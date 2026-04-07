"""
orchestrator.py — 16步行程规划 Pipeline v2 编排器

串联所有16步，管理 state 传递和 decision/trace 记录。

步骤流程：
  Step  1: resolve_user_constraints       系统：解析用户约束
  Step  2: build_region_summary           系统：SQL聚合地区摘要
  Step  3: plan_city_combination          Opus：城市组合候选
  Step  4: build_poi_pool                 系统：缩POI候选池
  Step  5: plan_daily_activities          Opus：主活动+走廊
  Step  5.5: validate_and_substitute      Sonnet：可用性初筛
  Step  6: build_hotel_pool               系统：缩住宿候选池
  Step  7: select_hotels                  Sonnet：选酒店
  Step  7.5: check_commute_feasibility    系统：通勤矩阵
  Step  8: build_daily_constraints_list   系统：每日约束包
  Step  9: plan_daily_sequences           Opus：每日排序
  Step 10: check_feasibility              系统：可行性检查
  Step 11: resolve_conflicts              系统+Opus：冲突处理
  Step 12: build_timeline                 Sonnet：时间线骨架
  Step 13: build_restaurant_pool          系统：餐厅候选池
  Step 13.5: select_meals                 Sonnet：选餐厅
  Step 14: estimate_budget                系统：预算核算
  Step 15: build_plan_b                   Sonnet：Plan B
  Step 16: generate_handbook_content      Sonnet：手账本内容
"""

from __future__ import annotations

import logging
import time
import traceback
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.business import TripRequest
from app.domains.planning_v2.models import CircleProfile
from app.domains.planning_v2.step01_constraints import resolve_user_constraints
from app.domains.planning_v2.step02_region_summary import build_region_summary
from app.domains.planning_v2.step03_city_planner import plan_city_combination
from app.domains.planning_v2.step04_poi_pool import build_poi_pool
from app.domains.planning_v2.step05_5_validator import validate_and_substitute
from app.domains.planning_v2.step05_activity_planner import plan_daily_activities
from app.domains.planning_v2.step06_hotel_pool import build_hotel_pool
from app.domains.planning_v2.step07_5_commute_check import check_commute_feasibility
from app.domains.planning_v2.step07_hotel_planner import select_hotels
from app.domains.planning_v2.step08_daily_constraints import build_daily_constraints_list
from app.domains.planning_v2.step09_sequence_planner import plan_daily_sequences
from app.domains.planning_v2.step10_feasibility import check_feasibility
from app.domains.planning_v2.step11_conflict_resolver import resolve_conflicts
from app.domains.planning_v2.step12_timeline_builder import build_timeline
from app.domains.planning_v2.step13_5_meal_planner import select_meals
from app.domains.planning_v2.step13_restaurant_pool import build_restaurant_pool
from app.domains.planning_v2.step14_budget import estimate_budget
from app.domains.planning_v2.step15_plan_b import build_plan_b
from app.domains.planning_v2.step16_handbook import generate_handbook_content

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Step tracker
# ---------------------------------------------------------------------------


class PipelineState:
    """Pipeline 执行状态，跨步骤传递数据。"""

    def __init__(self, trip_request_id: str, scene: str):
        self.run_id = str(uuid.uuid4())
        self.trip_request_id = trip_request_id
        self.scene = scene
        self.started_at = time.time()

        # Circle context (set early in pipeline)
        self.circle: CircleProfile | None = None

        # Step outputs (populated as pipeline progresses)
        self.user_constraints = None
        self.region_summary = None
        self.city_plan = None
        self.poi_pool = None
        self.daily_activities = None
        self.validated_activities = None
        self.hotel_pool = None
        self.hotel_plan = None
        self.commute_results = None
        self.daily_constraints = None
        self.daily_sequences = None
        self.feasibility_result = None
        self.resolved_sequences = None
        self.timeline = None
        self.restaurant_pool = None
        self.meal_selections = None
        self.budget = None
        self.plan_b = None
        self.handbook = None

        # Tracking
        self.step_log: list[dict] = []
        self.total_thinking_tokens = 0
        self.api_key: str = settings.anthropic_api_key or ""

    def log_step(
        self,
        step_id: str,
        status: str,
        duration_ms: int,
        thinking_tokens: int = 0,
        error: str = "",
    ):
        entry = {
            "step": step_id,
            "status": status,
            "duration_ms": duration_ms,
            "thinking_tokens": thinking_tokens,
        }
        if error:
            entry["error"] = error
        self.step_log.append(entry)
        self.total_thinking_tokens += thinking_tokens

    def elapsed_sec(self) -> float:
        return time.time() - self.started_at


async def _run_step(
    state: PipelineState,
    step_id: str,
    step_fn,
    *args,
    **kwargs,
) -> Any:
    """通用步骤执行器：记录耗时、异常处理。"""
    logger.info("[v2] Step %s 开始", step_id)
    t0 = time.time()
    try:
        result = await step_fn(*args, **kwargs)
        duration_ms = int((time.time() - t0) * 1000)
        thinking = 0
        if isinstance(result, dict):
            thinking = result.get("thinking_tokens_used", 0)
        state.log_step(step_id, "ok", duration_ms, thinking)
        logger.info("[v2] Step %s 完成 (%d ms)", step_id, duration_ms)
        return result
    except Exception as e:
        duration_ms = int((time.time() - t0) * 1000)
        state.log_step(step_id, "error", duration_ms, error=str(e))
        logger.error("[v2] Step %s 失败 (%d ms): %s", step_id, duration_ms, e)
        raise


# ---------------------------------------------------------------------------
# City circle resolver (Step 2 needs circle info)
# ---------------------------------------------------------------------------


async def _resolve_circle(
    session: AsyncSession,
    trip_request_id: str,
) -> CircleProfile:
    """
    从 TripProfile 解析城市圈。

    主权威：TripProfile.circle_id（用户显式选择的圈）。
    兜底：从 TripProfile.cities 推断（仅当 circle_id 为空时）。
    两者都没有则直接报错，不静默降级。
    """
    from sqlalchemy import select

    from app.db.models.business import TripProfile

    trip_uuid = uuid.UUID(trip_request_id)
    stmt = select(TripProfile).where(TripProfile.trip_request_id == trip_uuid)
    result = await session.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        raise ValueError(f"TripProfile not found for {trip_request_id}")

    # 主权威：显式 circle_id
    circle_id = getattr(profile, "circle_id", None)
    if circle_id:
        return CircleProfile.from_registry(circle_id)

    # 兜底：从城市列表推断
    cities = profile.cities or []
    if not cities:
        raise ValueError(
            f"TripProfile {trip_request_id} 既没有 circle_id 也没有 cities，无法确定城市圈"
        )

    return CircleProfile.infer_from_cities(cities)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


async def run_planning_v2(
    session: AsyncSession,
    trip: TripRequest,
    scene: str,
) -> tuple[bool, uuid.UUID | None, list | None, dict | None, dict | None]:
    """
    规划管线主入口。

    Returns:
        (success, plan_id, day_frames, design_brief, runtime_context)

    Args:
        session: 数据库异步会话
        trip: TripRequest 实例
        scene: 场景名

    Returns:
        (success, plan_id, day_frames_dicts, design_brief, runtime_context)
    """
    trip_request_id = str(trip.trip_request_id)
    state = PipelineState(trip_request_id, scene)

    logger.info(
        "[v2] Pipeline 启动: trip=%s, scene=%s, run_id=%s",
        trip_request_id,
        scene,
        state.run_id,
    )

    try:
        # ── Step 1: 解析用户约束 ──────────────────────────────────
        state.user_constraints = await _run_step(
            state,
            "01_constraints",
            resolve_user_constraints,
            session,
            trip_request_id,
        )

        # ── 圈解析 + 配置校验 ─────────────────────────────────────
        state.circle = await _resolve_circle(session, trip_request_id)
        circle = state.circle
        config_issues = circle.validate()
        if config_issues:
            raise ValueError(
                f"圈 {circle.circle_id} 配置不完整，无法运行管线: " + "; ".join(config_issues)
            )

        # ── Step 2: 地区摘要 ─────────────────────────────────────
        state.region_summary = await _run_step(
            state,
            "02_region_summary",
            build_region_summary,
            session,
            circle.circle_id,
            circle.cities,
        )

        # ── Step 3: 城市组合（Opus）────────────────────────────────
        state.city_plan = await _run_step(
            state,
            "03_city_planner",
            plan_city_combination,
            state.user_constraints,
            state.region_summary,
            circle,
            state.api_key,
        )
        # 取第一个候选方案
        candidates = state.city_plan.get("candidates", [])
        if not candidates:
            raise ValueError("Step 3 未返回任何候选方案")
        cities_by_day = candidates[0].get("cities_by_day", {})
        if not cities_by_day:
            raise ValueError("Step 3 候选方案中 cities_by_day 为空")

        # ── Step 4: POI 候选池 ───────────────────────────────────
        travel_dates = state.user_constraints.trip_window
        state.poi_pool = await _run_step(
            state,
            "04_poi_pool",
            build_poi_pool,
            session,
            state.user_constraints,
            state.region_summary,
            travel_dates,
            circle,
        )

        # ── Step 5: 每日主活动（Opus）─────────────────────────────
        state.daily_activities = await _run_step(
            state,
            "05_activity_planner",
            plan_daily_activities,
            cities_by_day,
            state.poi_pool,
            state.user_constraints,
            circle=circle,
            api_key=state.api_key,
        )

        # ── Step 8: 每日约束包（先于 5.5 需要）─────────────────────
        trip_window = state.user_constraints.trip_window
        state.daily_constraints = await _run_step(
            state,
            "08_daily_constraints",
            build_daily_constraints_list,
            session,
            trip_window,
            circle,
        )

        # ── Step 5.5: 可用性校验（Sonnet）────────────────────────
        validation_result = await _run_step(
            state,
            "05.5_validator",
            validate_and_substitute,
            state.daily_activities,
            state.daily_constraints,
            state.poi_pool,
            circle,
            state.api_key,
        )
        state.validated_activities = validation_result.get(
            "validated_activities", state.daily_activities
        )

        # ── Step 6: 酒店候选池 ───────────────────────────────────
        # 提取每日主走廊代表POI用于通勤排序
        daily_corridors = _extract_corridor_pois(state.validated_activities, state.poi_pool)
        state.hotel_pool = await _run_step(
            state,
            "06_hotel_pool",
            build_hotel_pool,
            session,
            state.user_constraints,
            circle.circle_id,
            circle.cities,
            state.poi_pool,
            50,
            daily_corridors,
        )

        # ── Step 7.5: 通勤矩阵 ──────────────────────────────────
        main_corridors = _extract_main_corridors(state.validated_activities)
        state.commute_results = await _run_step(
            state,
            "07.5_commute_check",
            check_commute_feasibility,
            session,
            state.hotel_pool,
            main_corridors,
        )

        # ── Step 7: 选酒店（Sonnet）──────────────────────────────
        hotel_result = await _run_step(
            state,
            "07_hotel_planner",
            select_hotels,
            state.hotel_pool,
            state.commute_results,
            state.validated_activities,
            state.user_constraints,
            circle=circle,
            api_key=state.api_key,
        )
        state.hotel_plan = hotel_result.get("hotel_plan", {})

        # ── Step 8 补充: 用酒店餐信息更新每日约束 ─────────────────
        selected_hotel_id = state.hotel_plan.get("primary", {}).get("hotel_id")
        if selected_hotel_id:
            state.daily_constraints = await _run_step(
                state,
                "08_daily_constraints_update",
                build_daily_constraints_list,
                session,
                trip_window,
                circle,
                selected_hotel_id,
            )

        # ── Step 9: 每日排序（Opus）──────────────────────────────
        commute_data = _prepare_commute_data(state.commute_results)
        state.daily_sequences = await _run_step(
            state,
            "09_sequence_planner",
            plan_daily_sequences,
            state.validated_activities,
            state.daily_constraints,
            commute_data,
            circle=circle,
            api_key=state.api_key,
        )
        sequences = state.daily_sequences.get("daily_sequences", [])

        # ── Step 10: 可行性检查 ──────────────────────────────────
        state.feasibility_result = check_feasibility(sequences, state.daily_constraints)
        state.log_step("10_feasibility", state.feasibility_result.status, 0)
        logger.info(
            "[v2] Step 10 可行性: status=%s, violations=%d",
            state.feasibility_result.status,
            len(state.feasibility_result.violations),
        )

        # ── Step 11: 冲突处理 ────────────────────────────────────
        if state.feasibility_result.status != "pass":
            conflict_result = await _run_step(
                state,
                "11_conflict_resolver",
                resolve_conflicts,
                sequences,
                state.feasibility_result,
                state.daily_constraints,
                state.poi_pool,
                circle=circle,
                api_key=state.api_key,
            )
            state.resolved_sequences = conflict_result.get("resolved_sequences", sequences)
        else:
            state.resolved_sequences = sequences

        # ── Step 12: 时间线骨架（Sonnet）─────────────────────────
        timeline_result = await _run_step(
            state,
            "12_timeline_builder",
            build_timeline,
            state.resolved_sequences,
            state.daily_constraints,
            state.hotel_plan,
            circle=circle,
            api_key=state.api_key,
        )
        state.timeline = timeline_result

        # ── Step 13: 餐厅候选池 ──────────────────────────────────
        main_corridor_list = _extract_main_corridors(state.validated_activities)
        state.restaurant_pool = await _run_step(
            state,
            "13_restaurant_pool",
            build_restaurant_pool,
            session,
            state.user_constraints,
            circle.cities,
            state.daily_constraints,
            main_corridor_list,
            circle,
        )

        # ── Step 13.5: 选餐厅（Sonnet）───────────────────────────
        meal_result = await _run_step(
            state,
            "13.5_meal_planner",
            select_meals,
            state.restaurant_pool,
            state.timeline,
            state.daily_constraints,
            state.user_constraints,
            circle=circle,
            api_key=state.api_key,
        )
        state.meal_selections = meal_result

        # ── Step 14: 预算核算 ────────────────────────────────────
        budget_tier = (state.user_constraints.user_profile or {}).get("budget_tier", "mid")
        state.budget = estimate_budget(
            state.resolved_sequences,
            state.hotel_plan,
            state.meal_selections,
            budget_tier,
            circle,
        )
        state.log_step("14_budget", "ok", 0)

        # ── Step 15: Plan B（Sonnet）─────────────────────────────
        plan_b_result = await _run_step(
            state,
            "15_plan_b",
            build_plan_b,
            state.timeline,
            state.poi_pool,
            state.daily_constraints,
            circle=circle,
            api_key=state.api_key,
        )
        state.plan_b = plan_b_result

        # ── Step 16: 手账本内容（Sonnet）─────────────────────────
        # Step 16 失败不阻塞主流程
        try:
            handbook_result = await _run_step(
                state,
                "16_handbook",
                generate_handbook_content,
                state.timeline,
                state.meal_selections,
                state.plan_b,
                state.poi_pool,
                circle=circle,
                api_key=state.api_key,
            )
            state.handbook = handbook_result
        except Exception as e:
            logger.warning("[v2] Step 16 手账本失败（非阻塞）: %s", e)
            state.handbook = {}

        # ── 组装输出 ──────────────────────────────────────────────
        plan_id = uuid.uuid4()
        day_frames = _assemble_day_frames(state)
        design_brief = _build_design_brief(state)
        runtime_context = _build_runtime_context(state, plan_id)

        logger.info(
            "[v2] Pipeline 完成: trip=%s, plan=%s, elapsed=%.1fs, thinking_tokens=%d, steps=%d",
            trip_request_id,
            plan_id,
            state.elapsed_sec(),
            state.total_thinking_tokens,
            len(state.step_log),
        )

        return True, plan_id, day_frames, design_brief, runtime_context

    except Exception as e:
        logger.error(
            "[v2] Pipeline 失败: trip=%s, elapsed=%.1fs, error=%s\n%s",
            trip_request_id,
            state.elapsed_sec(),
            e,
            traceback.format_exc(),
        )
        runtime_context = _build_runtime_context(state, None)
        return False, None, None, None, runtime_context


# ---------------------------------------------------------------------------
# Helper: extract corridor info from daily_activities for Step 6/7.5
# ---------------------------------------------------------------------------


def _extract_corridor_pois(
    daily_activities: dict,
    poi_pool: list,
) -> list[dict]:
    """从每日活动中提取主走廊代表性POI坐标（供 Step 6 通勤排序）。"""
    pool_map = {p.entity_id: p for p in poi_pool}
    corridors = []

    for day_data in daily_activities.get("daily_activities", []):
        day_num = day_data.get("day", 0)
        acts = day_data.get("main_activities", [])
        if acts:
            first_eid = acts[0].get("entity_id")
            poi = pool_map.get(first_eid)
            if poi:
                corridors.append(
                    {
                        "day": day_num,
                        "lat": poi.latitude,
                        "lng": poi.longitude,
                        "entity_id": poi.entity_id,
                    }
                )
    return corridors


def _extract_main_corridors(daily_activities: dict) -> list[str]:
    """提取所有天的 main_corridor 列表。"""
    corridors = []
    for day_data in daily_activities.get("daily_activities", []):
        mc = day_data.get("main_corridor", "")
        if mc:
            corridors.append(mc)
    return corridors


def _prepare_commute_data(commute_results: list) -> dict:
    """将 Step 7.5 通勤结果转为 Step 9 需要的格式。"""
    if not commute_results:
        return {}
    # Step 9 期望 {hotel_id: {avg_commute: N, details: [...]}}
    data = {}
    for result in commute_results:
        hid = result.get("hotel_id", "")
        data[hid] = {
            "avg_commute_minutes": result.get("avg_commute_minutes", 30),
            "max_commute_minutes": result.get("max_commute_minutes", 45),
            "status": result.get("status", "pass"),
        }
    return data


# ---------------------------------------------------------------------------
# Output assembly
# ---------------------------------------------------------------------------


def _assemble_day_frames(state: PipelineState) -> list[dict]:
    """组装最终的日程框架（与 v1 pipeline 输出格式对齐）。"""
    timeline = state.timeline or {}
    meals = state.meal_selections or {}
    plan_b = state.plan_b or {}
    handbook = state.handbook or {}
    budget = state.budget or {}

    day_frames = []
    timeline_days = timeline.get("daily_timeline", [])
    meal_days = meals.get("meal_selections", [])
    plan_b_days = plan_b.get("plan_b_by_day", [])
    handbook_days = handbook.get("daily_content", [])

    # 按天索引组装
    meal_by_day = {m.get("day"): m for m in meal_days} if meal_days else {}
    planb_by_day = {p.get("day"): p for p in plan_b_days} if plan_b_days else {}
    handbook_by_day = {h.get("day"): h for h in handbook_days} if handbook_days else {}
    budget_daily = budget.get("daily_breakdown", [])
    budget_by_idx = {i: b for i, b in enumerate(budget_daily)}

    for idx, day_tl in enumerate(timeline_days):
        day_num = day_tl.get("day", idx + 1)
        frame = {
            "day": day_num,
            "date": day_tl.get("date", ""),
            "timeline": day_tl.get("slots", []),
            "meals": meal_by_day.get(day_num, {}),
            "plan_b": planb_by_day.get(day_num, {}),
            "handbook": handbook_by_day.get(day_num, {}),
            "budget": budget_by_idx.get(idx, {}),
        }
        day_frames.append(frame)

    return day_frames


def _build_design_brief(state: PipelineState) -> dict:
    """构建设计摘要（供评审和渲染使用）。"""
    uc = state.user_constraints
    return {
        "trip_window": uc.trip_window if uc else {},
        "user_profile": uc.user_profile if uc else {},
        "circle_name": state.region_summary.circle_name if state.region_summary else "",
        "city_plan": state.city_plan,
        "hotel_plan": state.hotel_plan,
        "budget_summary": {
            "total_local": (state.budget or {}).get("trip_total_local", 0),
            "currency": state.circle.currency,
            "total_cny": (state.budget or {}).get("trip_total_cny", 0),
            "within_budget": (state.budget or {}).get("within_budget", True),
        },
    }


def _build_runtime_context(state: PipelineState, plan_id: uuid.UUID | None) -> dict:
    """构建运行时上下文（供 decision_writer 使用）。"""
    return {
        "run_id": state.run_id,
        "pipeline_version": "v2",
        "plan_id": str(plan_id) if plan_id else None,
        "elapsed_sec": round(state.elapsed_sec(), 1),
        "total_thinking_tokens": state.total_thinking_tokens,
        "step_log": state.step_log,
        "scene": state.scene,
    }
