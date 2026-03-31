"""
step06_hotel_pool.py — 酒店候选池构建与缩减

从 entity_base 读取酒店数据，计算地理中心，并按距离+预算过滤。

逻辑：
  1. 计算 candidate_poi_pool 的地理中心（加权平均，权重=visit_minutes）
  2. 从 entity_base WHERE entity_type='hotel' AND city_code IN circle_cities
  3. 按 distance_from_center 排序，保留前 N 个（N=50）
  4. 按 budget_level 过滤（用户预算↑ 可选更好的酒店）
  5. 排除 do_not_go_places 中的酒店
  6. 排除 risk_flags
"""

import logging
import math
import uuid
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.catalog import EntityBase, Hotel, EntityTag
from app.domains.planning_v2.models import (
    CandidatePool,
    UserConstraints,
    RegionSummary,
)

logger = logging.getLogger(__name__)

# 不同预算等级对应的酒店优先级（升序）
_BUDGET_TIER_PRIORITY: dict[str, int] = {
    "budget": 1,
    "mid": 2,
    "premium": 3,
    "luxury": 4,
}


def _calculate_geographic_center(
    poi_pools: list[CandidatePool],
) -> tuple[float, float]:
    """
    计算 POI 候选池的地理中心（加权平均）。

    权重 = visit_minutes（表示重要性）

    Args:
        poi_pools: POI 候选池列表

    Returns:
        (lat, lng) 元组
    """
    if not poi_pools:
        return (0.0, 0.0)

    total_weight = sum(p.visit_minutes for p in poi_pools)
    if total_weight == 0:
        # 无权重，使用简单平均
        avg_lat = sum(p.latitude for p in poi_pools) / len(poi_pools)
        avg_lng = sum(p.longitude for p in poi_pools) / len(poi_pools)
        return (avg_lat, avg_lng)

    weighted_lat = sum(p.latitude * p.visit_minutes for p in poi_pools) / total_weight
    weighted_lng = sum(p.longitude * p.visit_minutes for p in poi_pools) / total_weight

    return (weighted_lat, weighted_lng)


def _distance_km(
    lat1: float,
    lng1: float,
    lat2: float,
    lng2: float,
) -> float:
    """
    使用 Haversine 公式计算两个地理点之间的距离（公里）。
    """
    if lat1 == 0 or lng1 == 0 or lat2 == 0 or lng2 == 0:
        # 无效坐标
        return float("inf")

    # 地球半径（公里）
    R = 6371.0

    # 弧度转换
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)

    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    return R * c


async def build_hotel_pool(
    session: AsyncSession,
    user_constraints: UserConstraints,
    circle_name: str,
    circle_cities: list[str],
    candidate_poi_pool: list[CandidatePool],
    max_candidates: int = 50,
) -> list[CandidatePool]:
    """
    从 entity_base 读取候选酒店，按距离和预算过滤。

    Args:
        session: 数据库会话
        user_constraints: 用户约束
        circle_name: 城市圈名称
        circle_cities: 圈内城市列表
        candidate_poi_pool: POI 候选池（用于计算地理中心）
        max_candidates: 最多保留的候选酒店数

    Returns:
        list[CandidatePool]: 通过过滤的酒店候选池
    """
    trace_log = []

    # 0. 初始数据准备
    if not circle_cities:
        logger.warning(f"[酒店池] circle_cities 为空: circle={circle_name}")
        return []

    # 解析约束
    do_not_go_places = set(user_constraints.constraints.get("do_not_go", []))

    # 提取用户画像
    user_profile = user_constraints.user_profile or {}
    budget_tier = user_profile.get("budget_tier", "mid")  # budget/mid/premium/luxury

    trace_log.append(f"circle={circle_name}, cities={circle_cities}, budget_tier={budget_tier}")

    # 1. 计算 POI 池的地理中心
    center_lat, center_lng = _calculate_geographic_center(candidate_poi_pool)
    trace_log.append(f"POI地理中心: ({center_lat:.4f}, {center_lng:.4f})")

    if center_lat == 0 and center_lng == 0:
        logger.warning(f"[酒店池] POI池为空或无有效坐标，无法计算地理中心")
        # 降级：直接查询圈内所有酒店，不按距离排序
        pass

    # 2. 查询圈内所有酒店
    query = select(EntityBase).where(
        and_(
            EntityBase.entity_type == "hotel",
            EntityBase.city_code.in_(circle_cities),
            EntityBase.is_active == True,
        )
    )

    result = await session.execute(query)
    entities = result.scalars().all()
    count_total = len(entities)
    trace_log.append(f"Step 1: {count_total} 家酒店")

    if not entities:
        logger.info(f"[酒店池] 无符合条件的酒店: circle={circle_name}, cities={circle_cities}")
        return []

    entity_ids = [e.entity_id for e in entities]

    # 3. 批量加载 Hotel 扩展数据
    hotel_query = select(Hotel).where(Hotel.entity_id.in_(entity_ids))
    hotel_result = await session.execute(hotel_query)
    hotel_map: dict[uuid.UUID, Hotel] = {h.entity_id: h for h in hotel_result.scalars().all()}

    # 4. 批量加载标签
    tags_query = select(EntityTag).where(
        EntityTag.entity_id.in_(entity_ids)
    )
    tags_result = await session.execute(tags_query)
    entity_tags: dict[uuid.UUID, set[str]] = {}
    for tag in tags_result.scalars().all():
        entity_tags.setdefault(tag.entity_id, set()).add(
            tag.tag_value.lower() if tag.tag_value else ""
        )

    # 5. 执行过滤规则
    candidates_with_distance = []

    for entity in entities:
        eid = entity.entity_id
        hotel = hotel_map.get(eid)
        tags = entity_tags.get(eid, set())

        # Rule 1: 排除 do_not_go_places
        if str(eid) in do_not_go_places:
            continue

        # Rule 2: 排除 risk_flags
        if entity.risk_flags:
            skip_risk_flags = {"renovation", "construction", "unstable", "dangerous", "closed"}
            if any(flag in skip_risk_flags for flag in entity.risk_flags):
                continue

        # Rule 3: 按 budget_level 过滤
        # 用户预算等级低于酒店等级则过滤
        user_budget_priority = _BUDGET_TIER_PRIORITY.get(budget_tier, 2)
        hotel_budget_tier = entity.budget_tier or "mid"
        hotel_budget_priority = _BUDGET_TIER_PRIORITY.get(hotel_budget_tier, 2)

        # 用户预算等级 < 酒店预算等级时过滤（e.g., 用户预算，酒店奢华）
        if user_budget_priority < hotel_budget_priority:
            continue

        # 计算到地理中心的距离
        distance_km = _distance_km(
            center_lat, center_lng,
            float(entity.lat) if entity.lat else 0,
            float(entity.lng) if entity.lng else 0,
        )

        candidates_with_distance.append((entity, distance_km, hotel, tags))

    # 6. 按距离排序，保留前 N 个
    candidates_with_distance.sort(key=lambda x: x[1])
    top_candidates = candidates_with_distance[:max_candidates]

    count_after_filter = len(top_candidates)
    trace_log.append(f"Step 2-3 (filters + distance sort): {count_after_filter} 家酒店")

    # 7. 转换为 CandidatePool
    candidate_pools = []

    for entity, distance_km, hotel, tags in top_candidates:
        eid = entity.entity_id

        # 访问时长（酒店通常不计，设为 0）
        visit_minutes = 0

        # 成本（参考价格）
        cost_jpy = 0
        if hotel and hotel.typical_price_min_jpy:
            cost_jpy = int(hotel.typical_price_min_jpy)

        # 构建开放时间字典（酒店不适用，但保持字段兼容）
        open_hours = {
            "check_in_time": hotel.check_in_time if hotel and hotel.check_in_time else "15:00",
            "check_out_time": hotel.check_out_time if hotel and hotel.check_out_time else "11:00",
        }

        # 评分信号
        review_signals = {
            "distance_from_poi_center_km": round(distance_km, 2),
        }
        if hotel:
            if hotel.star_rating:
                review_signals["star_rating"] = float(hotel.star_rating)
            if hotel.google_rating:
                review_signals["google_rating"] = float(hotel.google_rating)
            if hotel.booking_score:
                review_signals["booking_score"] = float(hotel.booking_score)
            if hotel.amenities:
                review_signals["amenities"] = hotel.amenities

        # 创建 CandidatePool
        pool = CandidatePool(
            entity_id=str(eid),
            name_zh=entity.name_zh,
            entity_type="hotel",
            grade=entity.data_tier,
            latitude=float(entity.lat) if entity.lat else 0.0,
            longitude=float(entity.lng) if entity.lng else 0.0,
            tags=list(tags),
            visit_minutes=visit_minutes,
            cost_jpy=cost_jpy,
            open_hours=open_hours,
            review_signals=review_signals,
        )
        candidate_pools.append(pool)

    logger.info(
        f"[酒店池] 完成过滤: {count_total} -> {count_after_filter} -> {len(candidate_pools)} pools. "
        f"circle={circle_name}, center_distance_avg={sum(d[1] for d in top_candidates) / len(top_candidates) if top_candidates else 0:.2f}km"
    )
    for line in trace_log:
        logger.debug(f"  {line}")

    return candidate_pools
