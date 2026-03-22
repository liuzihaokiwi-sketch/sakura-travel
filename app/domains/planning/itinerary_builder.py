"""
itinerary_builder.py — E6a: Layer 2 结果直写 itinerary records

将 skeleton frames + secondary fill + meal fill 的完整输出，
直接转换为 ItineraryPlan / ItineraryDay / ItineraryItem 记录。

当前为 shadow mode：
  - 写入 plan_artifacts 而不是替代旧 assembler
  - 同时产出 diff 报告到 plan_metadata
  - 通过 CIRCLE_WRITE_MODE 控制行为

CIRCLE_WRITE_MODE:
  "disabled" — 不执行（默认）
  "shadow"   — 写入 shadow plan + diff 对比（E6a）
  "live"     — 替代旧 assembler 直接写入主 plan（E6b）
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.derived import (
    ItineraryDay,
    ItineraryItem,
    ItineraryPlan,
    PlanArtifact,
    PlannerRun,
)

logger = logging.getLogger(__name__)

# Feature flag
CIRCLE_WRITE_MODE = "shadow"  # disabled / shadow / live


# ── 核心数据结构 ──────────────────────────────────────────────────────────────

def _time_for_slot(slot_index: int, day_type: str) -> str:
    """根据槽位序号估算 HH:MM 时间。"""
    if day_type == "arrival":
        base_hour = 14  # 到达日下午开始
    elif day_type == "departure":
        base_hour = 8   # 离开日早上开始
    else:
        base_hour = 9   # 普通日上午开始

    minutes = base_hour * 60 + slot_index * 75  # 每个槽位 ~75 分钟间隔
    h = min(22, minutes // 60)
    m = minutes % 60
    return f"{h:02d}:{m:02d}"


def _meal_time(meal_type: str) -> str:
    """餐厅的默认时间。"""
    return {"breakfast": "08:00", "lunch": "12:00", "dinner": "18:30"}.get(meal_type, "12:00")


# ── 主构建函数 ────────────────────────────────────────────────────────────────

async def build_itinerary_records(
    session: AsyncSession,
    *,
    trip_request_id: uuid.UUID,
    circle_id: str,
    skeleton_frames: list,
    secondary_fills: list,
    meal_fills: list,
    hotel_result: Any,
    ranking_result: Any,
    design_brief: dict,
    existing_plan_id: Optional[uuid.UUID] = None,
) -> dict:
    """
    从 Layer 2 完整输出构建 itinerary records。

    Args:
        skeleton_frames: list[DayFrame]
        secondary_fills: list[FilledDay]
        meal_fills: list[MealFillResult]
        hotel_result: HotelStrategyResult
        ranking_result: MajorRankingResult
        design_brief: dict (来自 circle pipeline)
        existing_plan_id: shadow mode 下用于对比的旧 plan_id

    Returns:
        {
            "plan_id": uuid,
            "mode": "shadow" | "live",
            "days_created": N,
            "items_created": M,
            "diff": {...}  (shadow mode)
        }
    """
    mode = CIRCLE_WRITE_MODE
    if mode == "disabled":
        return {"mode": "disabled", "skipped": True}

    # ── 1. 创建 PlannerRun ──
    planner_run = PlannerRun(
        trip_request_id=trip_request_id,
        status="running",
        algorithm_version="circle_v1",
        run_params={
            "circle_id": circle_id,
            "mode": mode,
            "majors": len(ranking_result.selected_majors) if ranking_result else 0,
            "hotel_preset": hotel_result.preset_name if hotel_result else "",
        },
        started_at=datetime.now(tz=timezone.utc),
    )
    session.add(planner_run)
    await session.flush()

    # ── 2. 创建 ItineraryPlan ──
    plan_metadata = {
        "circle_id": circle_id,
        "pipeline": "city_circle_v1",
        "write_mode": mode,
        "total_days": len(skeleton_frames),
        "design_brief": design_brief,
        "hotel_strategy": hotel_result.preset_name if hotel_result else "default",
        # L4-04: pipeline 版本跟踪
        "pipeline_versions": {
            "scorer": "base_quality_v2",
            "planner": "circle_v1",
            "report_schema": "v2",
            "review_pipeline": "6_agent_v1",
            "itinerary_builder": "shadow_v1" if mode == "shadow" else "live_v1",
        },
    }

    plan = ItineraryPlan(
        trip_request_id=trip_request_id,
        planner_run_id=planner_run.planner_run_id,
        status="draft" if mode == "live" else "shadow",
        plan_metadata=plan_metadata,
    )
    session.add(plan)
    await session.flush()

    plan_id = plan.plan_id
    total_items = 0

    # ── 索引 secondary / meal fills ──
    secondary_by_day: dict[int, Any] = {}
    for sf in (secondary_fills or []):
        secondary_by_day[sf.day_index] = sf

    meal_by_day: dict[int, Any] = {}
    for mf in (meal_fills or []):
        meal_by_day[mf.day_index] = mf

    # hotel entity 索引 (day_index → hotel entity_id)
    hotel_by_day: dict[int, Optional[uuid.UUID]] = {}
    if hotel_result and hotel_result.bases:
        for base in hotel_result.bases:
            for d in range(base.check_in_day, base.check_in_day + base.nights):
                hotel_by_day[d] = (
                    uuid.UUID(base.hotel_entity_id)
                    if base.hotel_entity_id else None
                )

    # ── 3. 逐天构建 ──
    for frame in skeleton_frames:
        day_idx = frame.day_index

        # 确定 city_code（从 sleep_base 或 corridor 推断）
        city_code = _infer_city_code(frame)

        itinerary_day = ItineraryDay(
            plan_id=plan_id,
            day_number=day_idx,
            city_code=city_code,
            day_theme=frame.title_hint or frame.main_driver_name or "",
            day_summary_zh=f"{frame.primary_corridor} · {frame.intensity}",
            hotel_entity_id=hotel_by_day.get(day_idx),
        )
        session.add(itinerary_day)
        await session.flush()

        sort_order = 0

        # ── 3a. 早餐 ──
        meal_data = meal_by_day.get(day_idx)
        if meal_data:
            for meal in meal_data.meals:
                if meal.meal_type == "breakfast":
                    item = _create_meal_item(
                        itinerary_day.day_id, sort_order, meal
                    )
                    session.add(item)
                    sort_order += 1
                    total_items += 1

        # ── 3b. 主活动 ──
        if frame.main_driver:
            # 找 anchor entity
            anchor_ids = _get_anchor_entities(frame, ranking_result)
            for eid in anchor_ids:
                item = ItineraryItem(
                    day_id=itinerary_day.day_id,
                    sort_order=sort_order,
                    item_type="poi",
                    entity_id=eid,
                    start_time=_time_for_slot(sort_order, frame.day_type),
                    duration_min=90,
                    notes_zh=None,  # AI copywriter 后续填充
                    is_optional=False,
                )
                session.add(item)
                sort_order += 1
                total_items += 1

        # ── 3c. 午餐 ──
        if meal_data:
            for meal in meal_data.meals:
                if meal.meal_type == "lunch":
                    item = _create_meal_item(
                        itinerary_day.day_id, sort_order, meal
                    )
                    session.add(item)
                    sort_order += 1
                    total_items += 1

        # ── 3d. 次要活动 ──
        secondary_data = secondary_by_day.get(day_idx)
        if secondary_data:
            for sec_ent in secondary_data.secondary_items:
                eid = sec_ent.get("entity_id")
                item = ItineraryItem(
                    day_id=itinerary_day.day_id,
                    sort_order=sort_order,
                    item_type=sec_ent.get("entity_type", "poi"),
                    entity_id=uuid.UUID(eid) if eid else None,
                    start_time=_time_for_slot(sort_order, frame.day_type),
                    duration_min=sec_ent.get("typical_duration_min", 60),
                    notes_zh=None,
                    is_optional=True,
                )
                session.add(item)
                sort_order += 1
                total_items += 1

        # ── 3e. 晚餐 ──
        if meal_data:
            for meal in meal_data.meals:
                if meal.meal_type == "dinner":
                    item = _create_meal_item(
                        itinerary_day.day_id, sort_order, meal
                    )
                    session.add(item)
                    sort_order += 1
                    total_items += 1

        # ── 3f. 酒店 check-in 标记 ──
        if hotel_by_day.get(day_idx):
            item = ItineraryItem(
                day_id=itinerary_day.day_id,
                sort_order=sort_order,
                item_type="hotel",
                entity_id=hotel_by_day[day_idx],
                start_time="21:00",
                notes_zh=None,
                is_optional=False,
            )
            session.add(item)
            sort_order += 1
            total_items += 1

    # ── 4. 完成 planner_run ──
    planner_run.status = "completed"
    planner_run.completed_at = datetime.now(tz=timezone.utc)
    await session.flush()

    # ── 5. Shadow mode: 对比 diff ──
    diff_result = {}
    if mode == "shadow" and existing_plan_id:
        diff_result = await _compute_shadow_diff(
            session, existing_plan_id, plan_id
        )
        # 写入 plan_metadata
        meta = plan.plan_metadata or {}
        meta["shadow_diff"] = diff_result
        plan.plan_metadata = meta

        logger.info(
            "E6a shadow write: new_plan=%s shadow_of=%s days=%d items=%d diff=%s",
            plan_id, existing_plan_id, len(skeleton_frames), total_items,
            {k: v for k, v in diff_result.items() if k != "day_details"},
        )

    # ── 6. 写入 plan_artifacts（shadow 模式作为 artifact 存储） ──
    if mode == "shadow":
        artifact = PlanArtifact(
            plan_id=plan_id,
            artifact_type="shadow_plan",
            delivery_url=None,
            is_delivered=False,
        )
        session.add(artifact)

    await session.flush()

    return {
        "plan_id": plan_id,
        "mode": mode,
        "days_created": len(skeleton_frames),
        "items_created": total_items,
        "diff": diff_result,
    }


# ── 辅助函数 ──────────────────────────────────────────────────────────────────

def _infer_city_code(frame) -> str:
    """从 DayFrame 推断 city_code。"""
    base = frame.sleep_base or ""
    # 从 corridor ID 推断城市 (kyo_higashiyama → kyoto)
    prefix_map = {
        "kyo": "kyoto", "osa": "osaka", "tyo": "tokyo",
        "nar": "nara", "kob": "kobe", "hak": "hakone",
        "kam": "kamakura", "nik": "nikko",
    }
    corridor = frame.primary_corridor or ""
    for prefix, city in prefix_map.items():
        if corridor.startswith(prefix + "_") or base.lower().startswith(prefix):
            return city
    # fallback
    if base:
        return base.split("_")[0] if "_" in base else base
    return "tokyo"


def _get_anchor_entities(frame, ranking_result) -> list[uuid.UUID]:
    """从 ranking_result 中找到当天 main_driver cluster 的 anchor entity IDs。"""
    if not frame.main_driver or not ranking_result:
        return []

    for major in ranking_result.selected_majors:
        if major.cluster_id == frame.main_driver:
            return [eid for eid in major.anchor_entity_ids[:3]]  # 最多 3 个

    # 如果 must_keep_ids 有内容
    result = []
    for mk in frame.must_keep_ids[:3]:
        try:
            result.append(uuid.UUID(mk))
        except (ValueError, TypeError):
            pass
    return result


def _create_meal_item(day_id: int, sort_order: int, meal) -> ItineraryItem:
    """从 MealSlot 创建 ItineraryItem。"""
    eid = meal.restaurant.get("entity_id") if isinstance(meal.restaurant, dict) else None
    return ItineraryItem(
        day_id=day_id,
        sort_order=sort_order,
        item_type="restaurant",
        entity_id=uuid.UUID(eid) if eid else None,
        start_time=_meal_time(meal.meal_type),
        duration_min=60 if meal.meal_type == "dinner" else 45,
        notes_zh=None,
        is_optional=False,
    )


async def _compute_shadow_diff(
    session: AsyncSession,
    old_plan_id: uuid.UUID,
    new_plan_id: uuid.UUID,
) -> dict:
    """
    对比旧 plan 和新 shadow plan 的差异。

    返回:
        {
            "old_day_count": N, "new_day_count": M,
            "old_item_count": N, "new_item_count": M,
            "entity_overlap_rate": 0.XX,
            "missing_in_new": [...entity_ids...],
            "extra_in_new": [...entity_ids...],
            "day_details": [...]
        }
    """
    old_days = await session.execute(
        select(ItineraryDay).where(ItineraryDay.plan_id == old_plan_id)
        .order_by(ItineraryDay.day_number)
    )
    old_day_list = old_days.scalars().all()

    new_days = await session.execute(
        select(ItineraryDay).where(ItineraryDay.plan_id == new_plan_id)
        .order_by(ItineraryDay.day_number)
    )
    new_day_list = new_days.scalars().all()

    # 收集所有 entity IDs
    old_entities: set[str] = set()
    new_entities: set[str] = set()
    old_item_count = 0
    new_item_count = 0

    for day in old_day_list:
        items_q = await session.execute(
            select(ItineraryItem).where(ItineraryItem.day_id == day.day_id)
        )
        for item in items_q.scalars().all():
            old_item_count += 1
            if item.entity_id:
                old_entities.add(str(item.entity_id))

    for day in new_day_list:
        items_q = await session.execute(
            select(ItineraryItem).where(ItineraryItem.day_id == day.day_id)
        )
        for item in items_q.scalars().all():
            new_item_count += 1
            if item.entity_id:
                new_entities.add(str(item.entity_id))

    overlap = old_entities & new_entities
    overlap_rate = len(overlap) / max(1, len(old_entities | new_entities))

    return {
        "old_day_count": len(old_day_list),
        "new_day_count": len(new_day_list),
        "old_item_count": old_item_count,
        "new_item_count": new_item_count,
        "old_entity_count": len(old_entities),
        "new_entity_count": len(new_entities),
        "entity_overlap_rate": round(overlap_rate, 4),
        "missing_in_new": sorted(old_entities - new_entities)[:20],
        "extra_in_new": sorted(new_entities - old_entities)[:20],
    }
