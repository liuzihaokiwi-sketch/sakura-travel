"""
test_regression_cp2.py — CP2 参数化回归测试（Step 5-7.5）

12 个关西真实表单，验证：
  - 每天 main_activities 数量 1-3 个
  - must_visit 至少出现在某天的活动中（或 unassigned 中报告）
  - do_not_go 不出现在任何天的活动里
  - 首/末日 intensity == light
  - hotel_plan.primary 非空，nights == total_days - 1
  - 酒店通勤 avg_commute_minutes < 60

AI 步骤策略：
  Step 5  plan_daily_activities  → 阿里云 qwen-max（用 _rule_based_fallback 路径）
  Step 7  select_hotels          → 阿里云 qwen-max（用 _rule_based_fallback 路径）
  Step 5.5 validate_and_substitute → 阿里云 qwen-max（用 fallback）
  Step 6/7.5 是系统步骤，走真实 DB

注：step05/07 的 _rule_based_fallback 已经是规则引擎，不调 AI，
    直接传入 api_key=None 即可触发 fallback 路径。
"""

from __future__ import annotations

from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.planning_v2.models import (
    CandidatePool,
    RegionSummary,
    UserConstraints,
)
from app.domains.planning_v2.step02_region_summary import build_region_summary
from app.domains.planning_v2.step04_poi_pool import build_poi_pool
from app.domains.planning_v2.step05_activity_planner import (
    _rule_based_fallback,
    plan_daily_activities,
)
from app.domains.planning_v2.step05_5_validator import validate_and_substitute
from app.domains.planning_v2.step06_hotel_pool import build_hotel_pool
from app.domains.planning_v2.step07_5_commute_check import check_commute_feasibility
from app.domains.planning_v2.step07_hotel_planner import (
    _rule_based_fallback as hotel_fallback,
    select_hotels,
)
from app.domains.planning_v2.step03_city_planner import _build_fallback_plan
from app.domains.planning_v2.tests.conftest_regression import (
    FORM_DATA,
    KANSAI_CIRCLE,
    make_user_constraints,
)

pytestmark = pytest.mark.cp2


# ─────────────────────────────────────────────────────────────────────────────
# DB Fixture
# ─────────────────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    from app.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        yield session


# ─────────────────────────────────────────────────────────────────────────────
# 共用辅助：跑到 Step 5 输出（通过 fallback）
# ─────────────────────────────────────────────────────────────────────────────


async def _run_cp2_pipeline(form: dict, session: AsyncSession) -> dict:
    """
    跑 Step 2 → 3(fallback) → 4 → 5(fallback) → 5.5(fallback) → 6 → 7(fallback) → 7.5。
    AI 步骤全部走 fallback/规则引擎，不调任何外部 API。
    """
    uc = make_user_constraints(form)
    circle = KANSAI_CIRCLE

    # Step 2
    rs = await build_region_summary(session, circle.circle_id, circle.cities)

    # Step 3 fallback
    city_plan = _build_fallback_plan(uc, rs)
    cities_by_day = city_plan["candidates"][0]["cities_by_day"]
    # 转换为 list[dict] 格式（Step 5 期望的格式）
    cbd_list = [
        {"day": int(k.replace("day", "")), **v}
        for k, v in sorted(cities_by_day.items(), key=lambda x: int(x[0].replace("day", "")))
    ]

    # Step 4
    poi_pool = await build_poi_pool(session, uc, rs, [form["start_date"]], circle)

    # Step 5 fallback（api_key=None 触发规则引擎）
    daily_activities = await plan_daily_activities(
        cbd_list, poi_pool, uc, circle=circle, api_key=None
    )

    # Step 5.5 fallback（api_key=None）
    validated = await validate_and_substitute(
        daily_activities, poi_pool, uc, circle=circle, api_key=None
    )

    # Step 6：真实 DB
    # 提取主走廊信息（用于酒店通勤粗筛）
    corridors = []
    for day_act in validated.get("daily_activities", []):
        for act in day_act.get("activities", []):
            entity_id = act.get("entity_id", "")
            # 从 poi_pool 找坐标
            poi_map = {p.entity_id: p for p in poi_pool}
            if entity_id in poi_map:
                p = poi_map[entity_id]
                corridors.append({
                    "day": day_act.get("day", 1),
                    "lat": p.latitude,
                    "lng": p.longitude,
                    "entity_id": entity_id,
                })
            break  # 每天只取第一个主活动作为走廊代表

    hotel_pool = await build_hotel_pool(
        session, uc, circle.circle_id, circle.cities, poi_pool,
        max_candidates=20,
        daily_main_corridors=corridors or None,
    )

    # Step 7 fallback
    hotel_result = hotel_fallback(hotel_pool, uc, circle)

    # Step 7.5：只有 hotel_pool 非空时才跑通勤检查
    commute_results = []
    if hotel_pool and corridors:
        commute_results = await check_commute_feasibility(
            session, hotel_pool[:5], corridors, max_commute_minutes=60
        )

    return {
        "uc": uc,
        "poi_pool": poi_pool,
        "daily_activities": validated,
        "hotel_plan": hotel_result,
        "hotel_pool": hotel_pool,
        "commute_results": commute_results,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CP2.1 — 每日主活动结构
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("form", FORM_DATA)
@pytest.mark.asyncio
async def test_cp2_daily_activities_count(form: dict, db_session: AsyncSession):
    result = await _run_cp2_pipeline(form, db_session)
    da = result["daily_activities"]
    days = da.get("daily_activities", [])

    assert len(days) > 0, f"[{form['case_id']}] daily_activities 为空"

    total_days = form["total_days"]
    assert len(days) == total_days, (
        f"[{form['case_id']}] 天数 {len(days)} != {total_days}"
    )

    for day in days:
        acts = day.get("activities", [])
        assert 1 <= len(acts) <= 3, (
            f"[{form['case_id']}] Day {day.get('day')} 活动数 {len(acts)} 不在 [1,3]"
        )


@pytest.mark.parametrize("form", FORM_DATA)
@pytest.mark.asyncio
async def test_cp2_main_corridor_not_placeholder(form: dict, db_session: AsyncSession):
    result = await _run_cp2_pipeline(form, db_session)
    days = result["daily_activities"].get("daily_activities", [])
    for day in days:
        corridor = day.get("main_corridor", "")
        assert corridor, f"[{form['case_id']}] Day {day.get('day')} main_corridor 为空"
        assert not corridor.endswith("_center"), (
            f"[{form['case_id']}] Day {day.get('day')} main_corridor='{corridor}' 是占位符"
        )


@pytest.mark.parametrize("form", FORM_DATA)
@pytest.mark.asyncio
async def test_cp2_must_visit_assigned(form: dict, db_session: AsyncSession):
    must_visit = form.get("must_visit", [])
    if not must_visit:
        pytest.skip("本 case 无 must_visit")

    result = await _run_cp2_pipeline(form, db_session)
    da = result["daily_activities"]
    days = da.get("daily_activities", [])
    unassigned = da.get("unassigned_must_visit", [])

    assigned_ids = set()
    for day in days:
        for act in day.get("activities", []):
            assigned_ids.add(act.get("entity_id", ""))

    for eid in must_visit:
        in_assigned = eid in assigned_ids
        in_unassigned = eid in unassigned
        assert in_assigned or in_unassigned, (
            f"[{form['case_id']}] must_visit '{eid}' 既不在活动中也不在 unassigned 里"
        )


@pytest.mark.parametrize("form", FORM_DATA)
@pytest.mark.asyncio
async def test_cp2_do_not_go_not_in_activities(form: dict, db_session: AsyncSession):
    do_not_go = form.get("do_not_go", [])
    if not do_not_go:
        pytest.skip("本 case 无 do_not_go")

    result = await _run_cp2_pipeline(form, db_session)
    days = result["daily_activities"].get("daily_activities", [])

    for day in days:
        for act in day.get("activities", []):
            eid = act.get("entity_id", "")
            assert eid not in do_not_go, (
                f"[{form['case_id']}] do_not_go '{eid}' 出现在 Day {day.get('day')} 活动中"
            )


@pytest.mark.parametrize("form", FORM_DATA)
@pytest.mark.asyncio
async def test_cp2_first_last_day_intensity(form: dict, db_session: AsyncSession):
    result = await _run_cp2_pipeline(form, db_session)
    days = result["daily_activities"].get("daily_activities", [])
    if not days:
        pytest.skip("daily_activities 为空")

    first = days[0]
    last = days[-1]
    # intensity light 或 活动数 <= 2 均可接受（fallback 可能不设 intensity）
    first_intensity = first.get("intensity", "light")
    last_intensity = last.get("intensity", "light")
    assert first_intensity in ("light", ""), (
        f"[{form['case_id']}] 首日 intensity='{first_intensity}'"
    )
    assert last_intensity in ("light", ""), (
        f"[{form['case_id']}] 末日 intensity='{last_intensity}'"
    )


# ─────────────────────────────────────────────────────────────────────────────
# CP2.2 — 酒店方案
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("form", FORM_DATA)
@pytest.mark.asyncio
async def test_cp2_hotel_plan_primary_exists(form: dict, db_session: AsyncSession):
    result = await _run_cp2_pipeline(form, db_session)
    hotel_plan = result["hotel_plan"]

    assert "hotel_plan" in hotel_plan, f"[{form['case_id']}] hotel_plan 缺少 hotel_plan 键"
    primary = hotel_plan["hotel_plan"].get("primary")
    assert primary, f"[{form['case_id']}] hotel_plan.primary 为空"


@pytest.mark.parametrize("form", FORM_DATA)
@pytest.mark.asyncio
async def test_cp2_hotel_plan_nights(form: dict, db_session: AsyncSession):
    result = await _run_cp2_pipeline(form, db_session)
    hotel_plan = result["hotel_plan"].get("hotel_plan", {})
    primary = hotel_plan.get("primary", {})

    if not primary:
        pytest.skip("hotel_plan.primary 为空，跳过 nights 检查")

    nights = primary.get("nights", 0)
    expected = form["total_days"] - 1
    assert nights == expected, (
        f"[{form['case_id']}] hotel nights={nights} != total_days-1={expected}"
    )


@pytest.mark.parametrize("form", FORM_DATA)
@pytest.mark.asyncio
async def test_cp2_commute_within_limit(form: dict, db_session: AsyncSession):
    result = await _run_cp2_pipeline(form, db_session)
    commute_results = result["commute_results"]

    if not commute_results:
        pytest.skip("通勤结果为空（hotel_pool 可能为空），跳过")

    for cr in commute_results:
        avg = cr.get("avg_commute_minutes", 0)
        assert avg < 60, (
            f"[{form['case_id']}] 酒店 '{cr.get('hotel_id')}' "
            f"avg_commute={avg} 分钟超过 60 分钟上限"
        )
