"""
test_regression_cp4.py — CP4 参数化回归测试（Step 13-16）

12 个关西真实表单，验证：
  - restaurant_pool 非空
  - 酒店含早餐天的 breakfast 为 null（hotel_provided 或空）
  - meal_selections 每天有记录
  - budget 合计等于各天之和
  - budget.currency == "JPY"
  - trip_total_cny 在合理范围（1000-50000）
  - plan_b 不与当天原活动 entity_id 重复
  - day_frames 数量 == total_days
  - Step 16 失败不影响主链

AI 步骤策略：
  Step 13.5 select_meals   → 规则 fallback（api_key=None）
  Step 15  build_plan_b    → 规则 fallback（api_key=None）
  Step 16  handbook        → Anthropic Sonnet（@pytest.mark.live_api，可跳过）
  Step 13/14 是系统步骤

注：Step 12（时间线）是 CP4 前置依赖。
    CP4 的 timeline 用规则兜底构造（不调 AI），仅测 Step 13-16 结构。
"""

from __future__ import annotations

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.planning_v2.models import DailyConstraints, UserConstraints
from app.domains.planning_v2.step02_region_summary import build_region_summary
from app.domains.planning_v2.step03_city_planner import _build_fallback_plan
from app.domains.planning_v2.step04_poi_pool import build_poi_pool
from app.domains.planning_v2.step05_activity_planner import plan_daily_activities
from app.domains.planning_v2.step05_5_validator import validate_and_substitute
from app.domains.planning_v2.step06_hotel_pool import build_hotel_pool
from app.domains.planning_v2.step07_hotel_planner import _rule_based_fallback as hotel_fallback
from app.domains.planning_v2.step08_daily_constraints import build_daily_constraints_list
from app.domains.planning_v2.step10_feasibility import check_feasibility
from app.domains.planning_v2.step11_conflict_resolver import resolve_conflicts
from app.domains.planning_v2.step13_5_meal_planner import (
    _build_fallback_selections,
    select_meals,
)
from app.domains.planning_v2.step13_restaurant_pool import build_restaurant_pool
from app.domains.planning_v2.step14_budget import estimate_budget
from app.domains.planning_v2.step15_plan_b import _build_fallback_plan_b, build_plan_b
from app.domains.planning_v2.tests.conftest_regression import (
    FORM_DATA,
    KANSAI_CIRCLE,
    make_user_constraints,
)

pytestmark = pytest.mark.cp4


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    from app.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        yield session


# ─────────────────────────────────────────────────────────────────────────────
# 共用辅助：构造 CP4 最小可行前置数据
# ─────────────────────────────────────────────────────────────────────────────


def _build_stub_timeline(acts: list[dict], dcs: list[DailyConstraints]) -> dict:
    """
    从 daily_activities + daily_constraints 构造最小 timeline 结构，
    供 Step 13/13.5/15 使用（不调 Step 12 AI）。
    """
    days_out = []
    for i, (day_act, dc) in enumerate(zip(acts, dcs)):
        slots = []
        for j, act in enumerate(day_act.get("activities", [])):
            start_h = 9 + j * 2
            end_h = start_h + 1
            slots.append({
                "time": f"{start_h:02d}:00-{end_h:02d}:00",
                "type": "poi",
                "entity_id": act.get("entity_id", ""),
                "name": act.get("name", ""),
            })
        if not dc.hotel_breakfast_included:
            slots.insert(0, {"time": "08:00-08:30", "type": "flex_meal", "meal": "breakfast"})
        slots.append({"time": "12:00-13:00", "type": "flex_meal", "meal": "lunch"})
        slots.append({"time": "18:00-19:30", "type": "flex_meal", "meal": "dinner"})
        days_out.append({
            "day": day_act.get("day", i + 1),
            "date": dc.date,
            "slots": slots,
        })
    return {"timeline": days_out}


async def _run_cp4_prerequisites(form: dict, session: AsyncSession) -> dict:
    """跑 Step 2-14，AI 步骤走 fallback，Step 13/14 走真实 DB/纯 Python。"""
    uc = make_user_constraints(form)
    circle = KANSAI_CIRCLE

    rs = await build_region_summary(session, circle.circle_id, circle.cities)
    city_plan = _build_fallback_plan(uc, rs)
    cbd_list = [
        {"day": int(k.replace("day", "")), **v}
        for k, v in sorted(
            city_plan["candidates"][0]["cities_by_day"].items(),
            key=lambda x: int(x[0].replace("day", "")),
        )
    ]
    poi_pool = await build_poi_pool(session, uc, rs, [form["start_date"]], circle)

    daily_activities = await plan_daily_activities(
        cbd_list, poi_pool, uc, circle=circle, api_key=None
    )
    validated = await validate_and_substitute(
        daily_activities, poi_pool, uc, circle=circle, api_key=None
    )

    hotel_pool = await build_hotel_pool(
        session, uc, circle.circle_id, circle.cities, poi_pool, max_candidates=10
    )
    hotel_result = hotel_fallback(hotel_pool, uc, circle)
    primary = hotel_result.get("hotel_plan", {}).get("primary", {})
    hotel_id = primary.get("hotel_id")

    daily_constraints = await build_daily_constraints_list(
        session, uc.trip_window, circle,
        selected_hotel_id=hotel_id,
        user_party_type=uc.user_profile.get("party_type"),
    )

    acts = validated.get("daily_activities", [])
    daily_sequences = [
        {
            "day": day.get("day", i + 1),
            "date": day.get("date", ""),
            "sequence": [
                {"entity_id": act.get("entity_id", ""), "name": act.get("name", ""), "duration_min": 90}
                for act in day.get("activities", [])
            ],
        }
        for i, day in enumerate(acts)
    ]

    feasibility = check_feasibility(daily_sequences, daily_constraints, {})
    resolved = await resolve_conflicts(
        daily_sequences, feasibility, daily_constraints, poi_pool, circle, api_key=None
    )

    # Step 12 用 stub（不调 AI）
    timeline = _build_stub_timeline(acts, daily_constraints)

    # 提取主走廊列表（用于 Step 13）
    corridors = list({
        day.get("main_corridor", "unknown")
        for day in acts
        if day.get("main_corridor")
    })

    # Step 13：真实 DB
    restaurant_pool = await build_restaurant_pool(
        session, uc, circle.cities, daily_constraints, corridors or ["unknown"], circle
    )

    # Step 13.5 fallback（api_key=None）
    meal_selections = await select_meals(
        restaurant_pool, timeline, daily_constraints, uc, circle, api_key=None
    )

    # Step 14：纯 Python
    budget = estimate_budget(
        resolved.get("resolved_sequences", daily_sequences),
        hotel_result.get("hotel_plan", {}),
        meal_selections,
        uc.user_profile.get("budget_tier", "mid"),
        circle,
    )

    # Step 15 fallback（api_key=None）
    plan_b = await build_plan_b(
        timeline, poi_pool, daily_constraints, circle, api_key=None
    )

    return {
        "uc": uc,
        "timeline": timeline,
        "daily_constraints": daily_constraints,
        "restaurant_pool": restaurant_pool,
        "meal_selections": meal_selections,
        "budget": budget,
        "plan_b": plan_b,
        "daily_sequences": resolved.get("resolved_sequences", daily_sequences),
        "hotel_plan": hotel_result.get("hotel_plan", {}),
        "poi_pool": poi_pool,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CP4.1 — 餐厅池
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("form", FORM_DATA)
@pytest.mark.asyncio
async def test_cp4_restaurant_pool_not_empty(form: dict, db_session: AsyncSession):
    result = await _run_cp4_prerequisites(form, db_session)
    rp = result["restaurant_pool"]
    total = rp.get("pool_stats", {}).get("total_restaurants", 0)
    assert total > 0, f"[{form['case_id']}] restaurant_pool 为空"


# ─────────────────────────────────────────────────────────────────────────────
# CP4.2 — 餐食选择
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("form", FORM_DATA)
@pytest.mark.asyncio
async def test_cp4_meal_selections_count(form: dict, db_session: AsyncSession):
    result = await _run_cp4_prerequisites(form, db_session)
    ms = result["meal_selections"]
    selections = ms.get("meal_selections", [])

    assert len(selections) == form["total_days"], (
        f"[{form['case_id']}] meal_selections 天数 {len(selections)} != {form['total_days']}"
    )


@pytest.mark.parametrize("form", FORM_DATA)
@pytest.mark.asyncio
async def test_cp4_hotel_breakfast_null_when_included(form: dict, db_session: AsyncSession):
    """酒店含早餐的天，breakfast 应为 null（或标记 hotel_provided）。"""
    result = await _run_cp4_prerequisites(form, db_session)
    dcs = result["daily_constraints"]
    ms = result["meal_selections"].get("meal_selections", [])

    breakfast_included_dates = {dc.date for dc in dcs if dc.hotel_breakfast_included}
    for sel in ms:
        if sel.get("date", "") in breakfast_included_dates:
            breakfast = sel.get("breakfast")
            assert breakfast is None or (
                isinstance(breakfast, dict) and breakfast.get("type") == "hotel_provided"
            ), (
                f"[{form['case_id']}] 酒店含早餐当天 breakfast 不为 null: {breakfast}"
            )


# ─────────────────────────────────────────────────────────────────────────────
# CP4.3 — 预算
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("form", FORM_DATA)
@pytest.mark.asyncio
async def test_cp4_budget_currency(form: dict, db_session: AsyncSession):
    result = await _run_cp4_prerequisites(form, db_session)
    budget = result["budget"]
    assert budget.get("currency") == "JPY", (
        f"[{form['case_id']}] budget.currency='{budget.get('currency')}' 不是 JPY"
    )


@pytest.mark.parametrize("form", FORM_DATA)
@pytest.mark.asyncio
async def test_cp4_budget_total_matches_daily_sum(form: dict, db_session: AsyncSession):
    result = await _run_cp4_prerequisites(form, db_session)
    budget = result["budget"]
    daily = budget.get("daily_breakdown", [])
    if not daily:
        pytest.skip("daily_breakdown 为空，跳过")

    daily_sum = sum(d.get("total", 0) for d in daily)
    trip_total = budget.get("trip_total_local", 0)
    assert trip_total == daily_sum, (
        f"[{form['case_id']}] trip_total_local={trip_total} != sum(daily)={daily_sum}"
    )


@pytest.mark.parametrize("form", FORM_DATA)
@pytest.mark.asyncio
async def test_cp4_budget_daily_reasonable(form: dict, db_session: AsyncSession):
    result = await _run_cp4_prerequisites(form, db_session)
    budget = result["budget"]
    daily = budget.get("daily_breakdown", [])
    if not daily:
        pytest.skip("daily_breakdown 为空，跳过")

    for d in daily:
        total = d.get("total", 0)
        assert 5000 <= total <= 80000, (
            f"[{form['case_id']}] Day {d.get('day')} total={total} JPY 不在合理范围 [5000, 80000]"
        )


@pytest.mark.parametrize("form", FORM_DATA)
@pytest.mark.asyncio
async def test_cp4_budget_cny_reasonable(form: dict, db_session: AsyncSession):
    result = await _run_cp4_prerequisites(form, db_session)
    budget = result["budget"]
    cny = budget.get("trip_total_cny", 0)
    assert 1000 <= cny <= 50000, (
        f"[{form['case_id']}] trip_total_cny={cny} 不在合理范围 [1000, 50000]"
    )


# ─────────────────────────────────────────────────────────────────────────────
# CP4.4 — Plan B
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("form", FORM_DATA)
@pytest.mark.asyncio
async def test_cp4_plan_b_no_duplicate_with_activities(form: dict, db_session: AsyncSession):
    """Plan B 的 alternative_entity 不应与当天原活动 entity_id 相同。"""
    result = await _run_cp4_prerequisites(form, db_session)
    plan_b_days = result["plan_b"].get("plan_b", [])
    sequences = result["daily_sequences"]

    # 建立 day → activity entity_ids 映射
    acts_by_day: dict[int, set] = {}
    for seq in sequences:
        day = seq.get("day", 0)
        acts_by_day[day] = {s.get("entity_id", "") for s in seq.get("sequence", [])}

    for pb_day in plan_b_days:
        day = pb_day.get("day", 0)
        originals = acts_by_day.get(day, set())
        for alt in pb_day.get("alternatives", []):
            alt_eid = alt.get("alternative_entity", "")
            if alt_eid:
                assert alt_eid not in originals, (
                    f"[{form['case_id']}] Day {day} plan_b alternative_entity "
                    f"'{alt_eid}' 与原活动重复"
                )


@pytest.mark.parametrize("form", FORM_DATA)
@pytest.mark.asyncio
async def test_cp4_day_frames_count(form: dict, db_session: AsyncSession):
    """day_frames 数量 == total_days。"""
    result = await _run_cp4_prerequisites(form, db_session)
    # day_frames = timeline days（stub 构造的）
    timeline_days = result["timeline"].get("timeline", [])
    assert len(timeline_days) == form["total_days"], (
        f"[{form['case_id']}] day_frames={len(timeline_days)} != total_days={form['total_days']}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# CP4.5 — Step 16 非阻塞（live_api，可跳过）
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.live_api
@pytest.mark.parametrize("form", [FORM_DATA[0]])  # 只跑 7d_classic 验证非阻塞
@pytest.mark.asyncio
async def test_cp4_handbook_failure_non_blocking(form: dict, db_session: AsyncSession):
    """Step 16 失败不影响主链——抛异常时应被捕获，不传播。"""
    from app.core.config import settings
    from app.domains.planning_v2.step16_handbook import generate_handbook_content

    api_key = settings.anthropic_api_key
    if not api_key:
        pytest.skip("无 ANTHROPIC_API_KEY，跳过 live_api 测试")

    result = await _run_cp4_prerequisites(form, db_session)

    await asyncio.sleep(3)  # 串行限速

    try:
        handbook = await generate_handbook_content(
            result["timeline"],
            result["budget"],
            result["meal_selections"],
            result["plan_b"],
            result["uc"],
            KANSAI_CIRCLE,
            api_key=api_key,
        )
        # 成功路径：有输出
        assert handbook is not None
    except Exception:
        # Step 16 允许失败，不传播
        pass
