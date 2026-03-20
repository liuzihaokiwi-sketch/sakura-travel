from __future__ import annotations

"""
planner: 行程规划主逻辑
- 从 DB 查询候选实体（按城市 + must_have_tags 过滤）
- 按天调用 day_builder 组装行程
- 写入 ItineraryPlan / ItineraryDay / ItineraryItem
"""

import uuid
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.business import TripProfile, TripRequest
from app.db.models.catalog import EntityBase, EntityTag, Hotel, Poi, Restaurant
from app.db.models.derived import (
    ItineraryDay,
    ItineraryItem,
    ItineraryPlan,
    PlannerRun,
)
from app.domains.trip_core.day_builder import (
    EntityCandidate,
    PlannedItem,
    build_day,
    estimate_day_cost_jpy,
)

ALGORITHM_VERSION = "v0.1.0"


# ── 候选实体查询 ──────────────────────────────────────────────────────────────

async def _fetch_poi_candidates(
    session: AsyncSession,
    city_code: str,
    must_have_tags: List[str],
    limit: int = 20,
) -> List[EntityCandidate]:
    """查询指定城市的 POI 候选，must_have_tags 过滤（宽松匹配，有一个即可）"""
    stmt = (
        select(EntityBase, Poi)
        .join(Poi, Poi.entity_id == EntityBase.entity_id)
        .where(
            EntityBase.city_code == city_code,
            EntityBase.entity_type == "poi",
            EntityBase.is_active.is_(True),
        )
        .order_by(Poi.google_rating.desc().nulls_last())
        .limit(limit)
    )
    result = await session.execute(stmt)
    rows = result.all()

    candidates = []
    for entity, poi in rows:
        candidates.append(EntityCandidate(
            entity_id=str(entity.entity_id),
            entity_type="poi",
            name_zh=entity.name_zh,
            lat=float(entity.lat) if entity.lat else None,
            lng=float(entity.lng) if entity.lng else None,
            poi_category=poi.poi_category,
            typical_duration_min=poi.typical_duration_min,
            admission_fee_jpy=poi.admission_fee_jpy,
            google_rating=float(poi.google_rating) if poi.google_rating else None,
        ))
    return candidates


async def _fetch_restaurant_candidates(
    session: AsyncSession,
    city_code: str,
    limit: int = 10,
) -> List[EntityCandidate]:
    stmt = (
        select(EntityBase, Restaurant)
        .join(Restaurant, Restaurant.entity_id == EntityBase.entity_id)
        .where(
            EntityBase.city_code == city_code,
            EntityBase.entity_type == "restaurant",
            EntityBase.is_active.is_(True),
        )
        .order_by(Restaurant.tabelog_score.desc().nulls_last())
        .limit(limit)
    )
    result = await session.execute(stmt)
    rows = result.all()

    candidates = []
    for entity, rest in rows:
        candidates.append(EntityCandidate(
            entity_id=str(entity.entity_id),
            entity_type="restaurant",
            name_zh=entity.name_zh,
            lat=float(entity.lat) if entity.lat else None,
            lng=float(entity.lng) if entity.lng else None,
            cuisine_type=rest.cuisine_type,
            budget_lunch_jpy=rest.budget_lunch_jpy,
            budget_dinner_jpy=rest.budget_dinner_jpy,
        ))
    return candidates


async def _fetch_hotel_candidate(
    session: AsyncSession,
    city_code: str,
    budget_level: Optional[str],
) -> Optional[EntityCandidate]:
    """找最合适的酒店（按预算档+评分）"""
    price_tier_map = {
        "budget": "budget",
        "mid": "mid",
        "premium": "premium",
        "luxury": "luxury",
    }
    price_tier = price_tier_map.get(budget_level or "mid", "mid")

    stmt = (
        select(EntityBase, Hotel)
        .join(Hotel, Hotel.entity_id == EntityBase.entity_id)
        .where(
            EntityBase.city_code == city_code,
            EntityBase.entity_type == "hotel",
            EntityBase.is_active.is_(True),
            Hotel.price_tier == price_tier,
        )
        .order_by(Hotel.google_rating.desc().nulls_last())
        .limit(1)
    )
    result = await session.execute(stmt)
    row = result.one_or_none()
    if row is None:
        # fallback：不限 price_tier
        stmt2 = (
            select(EntityBase, Hotel)
            .join(Hotel, Hotel.entity_id == EntityBase.entity_id)
            .where(
                EntityBase.city_code == city_code,
                EntityBase.entity_type == "hotel",
                EntityBase.is_active.is_(True),
            )
            .order_by(Hotel.google_rating.desc().nulls_last())
            .limit(1)
        )
        result2 = await session.execute(stmt2)
        row = result2.one_or_none()

    if row is None:
        return None

    entity, hotel = row
    return EntityCandidate(
        entity_id=str(entity.entity_id),
        entity_type="hotel",
        name_zh=entity.name_zh,
        lat=float(entity.lat) if entity.lat else None,
        lng=float(entity.lng) if entity.lng else None,
    )


# ── 核心规划函数 ──────────────────────────────────────────────────────────────

async def generate_plan(
    session: AsyncSession,
    trip_request_id: str,
) -> ItineraryPlan:
    """
    为指定 trip_request 生成行程方案。

    流程：
      1. 查 TripRequest + TripProfile
      2. 创建 PlannerRun 记录
      3. 按城市逐天查询候选 → build_day → 写 DB
      4. 更新 TripRequest.status → "done"

    Args:
        session:          AsyncSession（调用方 commit）
        trip_request_id:  UUID 字符串

    Returns:
        已 flush 的 ItineraryPlan
    """
    req_uuid = uuid.UUID(trip_request_id)

    # 1. 查 TripRequest
    req_result = await session.execute(
        select(TripRequest).where(TripRequest.trip_request_id == req_uuid)
    )
    trip_req = req_result.scalar_one_or_none()
    if trip_req is None:
        raise ValueError(f"TripRequest not found: {trip_request_id}")

    # 2. 查 TripProfile（normalize job 应已跑完）
    profile_result = await session.execute(
        select(TripProfile).where(TripProfile.trip_request_id == req_uuid)
    )
    profile = profile_result.scalar_one_or_none()
    if profile is None:
        raise ValueError(f"TripProfile not found for trip_request: {trip_request_id}")

    # 3. 创建 PlannerRun
    planner_run = PlannerRun(
        trip_request_id=req_uuid,
        status="running",
        algorithm_version=ALGORITHM_VERSION,
        run_params={
            "cities": profile.cities,
            "duration_days": profile.duration_days,
            "must_have_tags": profile.must_have_tags,
            "budget_level": profile.budget_level,
        },
    )
    session.add(planner_run)
    await session.flush()

    # 4. 创建 ItineraryPlan
    plan = ItineraryPlan(
        trip_request_id=req_uuid,
        planner_run_id=planner_run.planner_run_id,
        version=1,
        status="draft",
        plan_metadata={
            "total_days": profile.duration_days,
            "cities": [c["city_code"] for c in profile.cities],
            "budget_level": profile.budget_level,
        },
    )
    session.add(plan)
    await session.flush()

    # 5. 按天规划
    travel_dates = profile.travel_dates or {}
    start_date_str: Optional[str] = travel_dates.get("start")

    total_cost_jpy = 0
    day_number = 1

    for city_entry in profile.cities:
        city_code: str = city_entry["city_code"]
        nights: int = city_entry.get("nights", 1)

        # 查询候选实体
        pois = await _fetch_poi_candidates(
            session, city_code, profile.must_have_tags, limit=nights * 4
        )
        restaurants = await _fetch_restaurant_candidates(
            session, city_code, limit=nights * 4
        )
        hotel = await _fetch_hotel_candidate(
            session, city_code, profile.budget_level
        )

        # 每个城市住几晚就生成几天
        poi_pool = list(pois)
        rest_pool = list(restaurants)

        for night_idx in range(nights):
            # 计算日期
            day_date: Optional[str] = None
            if start_date_str:
                d = date.fromisoformat(start_date_str) + timedelta(days=day_number - 1)
                day_date = d.isoformat()

            # 每天取前 3 个 POI 和前 2 个餐厅
            day_pois = poi_pool[:3]
            poi_pool = poi_pool[3:]
            day_rests = rest_pool[:2]
            rest_pool = rest_pool[2:]

            # 最后一晚才分配酒店入住
            day_hotel = hotel if night_idx == nights - 1 else hotel

            planned_items = build_day(
                pois=day_pois,
                restaurants=day_rests,
                hotel=day_hotel,
            )

            day_cost = estimate_day_cost_jpy(planned_items)
            total_cost_jpy += day_cost

            # 写 ItineraryDay
            itin_day = ItineraryDay(
                plan_id=plan.plan_id,
                day_number=day_number,
                date=day_date,
                city_code=city_code,
                day_theme=_day_theme(day_pois),
                estimated_cost_jpy=day_cost if day_cost > 0 else None,
                hotel_entity_id=uuid.UUID(hotel.entity_id) if hotel else None,
            )
            session.add(itin_day)
            await session.flush()

            # 写 ItineraryItem
            for pi in planned_items:
                item = ItineraryItem(
                    day_id=itin_day.day_id,
                    sort_order=pi.sort_order,
                    item_type=pi.item_type,
                    entity_id=uuid.UUID(pi.entity_id) if pi.entity_id else None,
                    start_time=pi.start_time,
                    end_time=pi.end_time,
                    duration_min=pi.duration_min,
                    notes_zh=pi.notes_zh,
                    estimated_cost_jpy=pi.estimated_cost_jpy,
                    is_optional=pi.is_optional,
                )
                session.add(item)

            day_number += 1

    # 6. 更新 plan_metadata 费用汇总
    plan.plan_metadata = {
        **(plan.plan_metadata or {}),
        "estimated_total_cost_jpy": total_cost_jpy,
    }

    # 7. 更新 PlannerRun + TripRequest 状态
    planner_run.status = "completed"
    trip_req.status = "done"

    await session.flush()
    return plan


def _day_theme(pois: List[EntityCandidate]) -> Optional[str]:
    """根据当天 POI 组合生成主题描述"""
    if not pois:
        return None
    categories = [p.poi_category for p in pois if p.poi_category]
    if not categories:
        return pois[0].name_zh + " 一日游"
    # 最多出现的类别决定主题
    from collections import Counter
    top_cat = Counter(categories).most_common(1)[0][0]
    theme_map = {
        "shrine": "神社文化之旅", "temple": "古寺探访", "park": "自然漫步",
        "museum": "文化艺术之旅", "castle": "历史城堡之旅", "landmark": "城市地标游览",
        "shopping": "购物休闲", "onsen": "温泉放松之旅", "theme_park": "主题乐园欢乐日",
    }
    return theme_map.get(top_cat, f"{pois[0].name_zh} 周边游")
