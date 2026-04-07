"""
step06_hotel_pool.py — 酒店候选池构建与缩减

从 entity_base 读取酒店数据，按通勤时间+预算过滤。

逻辑（两阶段筛选）：
  1. 粗筛：Haversine 距离预筛 top 100（快速排除远距离酒店）
  2. 精排：调用 route_matrix 获取真实通勤时间，按通勤成本排序
  3. 目标函数：最小化 Σ(每日主走廊 → 酒店的通勤时间)
  4. 按 budget_level 过滤
  5. 排除 do_not_go_places / risk_flags
  6. 保留 top N（默认50）

注意：Haversine 仅做预筛，最终排序依据是门到门通勤时间。
京都/大阪等城市中"地图近但通勤远"的情况很常见（河流/铁路/山地隔断）。
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

# Haversine 粗筛上限（取 top N 进入精排）
_HAVERSINE_PREFILTER_LIMIT = 100

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
    daily_main_corridors: Optional[list[dict]] = None,
) -> list[CandidatePool]:
    """
    从 entity_base 读取候选酒店，按通勤时间和预算过滤。

    两阶段筛选：
      1. Haversine 粗筛 top 100（排除地理上明显不合理的）
      2. 如果提供 daily_main_corridors，调用 route_matrix 精排
         按 Σ(每日通勤时间) 排序，取 top N
      3. 如果未提供 daily_main_corridors，退化为 Haversine 排序

    Args:
        session: 数据库会话
        user_constraints: 用户约束
        circle_name: 城市圈名称
        circle_cities: 圈内城市列表
        candidate_poi_pool: POI 候选池（用于计算地理中心）
        max_candidates: 最多保留的候选酒店数
        daily_main_corridors: 每日主走廊的代表性POI坐标列表，
            格式 [{"day": 1, "lat": 35.0, "lng": 135.6, "entity_id": "..."}]
            用于计算真实通勤时间。不传则退化为 Haversine。

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

    # 6. 两阶段排序
    # Phase 1: Haversine 粗筛 top N（快速排除远距离）
    candidates_with_distance.sort(key=lambda x: x[1])
    haversine_top = candidates_with_distance[:_HAVERSINE_PREFILTER_LIMIT]
    trace_log.append(
        f"Phase 1 (Haversine prefilter): {len(candidates_with_distance)} -> "
        f"{len(haversine_top)} candidates"
    )

    # Phase 2: 通勤时间精排（如果有走廊数据和 route_matrix）
    if daily_main_corridors and haversine_top:
        try:
            haversine_top = await _rank_by_commute_time(
                session, haversine_top, daily_main_corridors, trace_log,
            )
        except Exception as e:
            logger.warning(
                "[酒店池] route_matrix 精排失败，退化为 Haversine: %s", e,
            )

    top_candidates = haversine_top[:max_candidates]

    count_after_filter = len(top_candidates)
    trace_log.append(f"Final selection: {count_after_filter} 家酒店")

    # 7. 转换为 CandidatePool
    candidate_pools = []

    for entity, distance_km, hotel, tags in top_candidates:
        eid = entity.entity_id

        # 访问时长（酒店通常不计，设为 0）
        visit_minutes = 0

        # 成本（参考价格）
        cost_local = 0
        if hotel and hotel.typical_price_min_jpy:
            cost_local = int(hotel.typical_price_min_jpy)

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
            cost_local=cost_local,
            city_code=entity.city_code or "",
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


async def _rank_by_commute_time(
    session: AsyncSession,
    candidates: list[tuple],  # (entity, distance_km, hotel, tags)
    daily_main_corridors: list[dict],
    trace_log: list[str],
) -> list[tuple]:
    """
    用 route_matrix 精排酒店候选，按实际通勤时间排序。

    目标函数：Σ(每日权重 × 门到门通勤分钟数)
    权重：所有天等权（未来可按行李日/check-in日加权）

    为避免 Google Routes API 元素上限（transit 模式 100 elements），
    采用串行查询：每个酒店候选 × 每日代表POI。

    Args:
        session: 数据库会话
        candidates: Haversine 粗筛后的候选列表
        daily_main_corridors: 每日主走廊代表性 POI 坐标
        trace_log: 日志追踪

    Returns:
        按通勤时间重排后的候选列表
    """
    from app.domains.planning.route_matrix import get_travel_time

    # 提取每日代表POI的 entity_id（需要是 DB 中的 UUID）
    corridor_eids = []
    for mc in daily_main_corridors:
        eid = mc.get("entity_id")
        if eid:
            try:
                corridor_eids.append(uuid.UUID(str(eid)))
            except (ValueError, AttributeError):
                pass

    if not corridor_eids:
        trace_log.append("Phase 2: 无有效走廊 entity_id，跳过通勤精排")
        return candidates

    scored: list[tuple[float, tuple]] = []

    for cand_tuple in candidates:
        entity, distance_km, hotel, tags = cand_tuple
        hotel_eid = entity.entity_id
        total_commute_mins = 0.0
        valid_queries = 0

        for corridor_eid in corridor_eids:
            try:
                result = await get_travel_time(
                    session=session,
                    origin_id=hotel_eid,
                    dest_id=corridor_eid,
                    mode="transit",
                )
                if result and result.get("duration_minutes"):
                    total_commute_mins += result["duration_minutes"]
                    valid_queries += 1
                else:
                    # route_matrix 无数据，用 Haversine 估算（15km/h 步行+公交）
                    total_commute_mins += distance_km * 4  # 粗略估算
                    valid_queries += 1
            except Exception:
                # 查询失败，降级到距离估算
                total_commute_mins += distance_km * 4
                valid_queries += 1

        avg_commute = total_commute_mins / max(valid_queries, 1)
        scored.append((avg_commute, cand_tuple))

    scored.sort(key=lambda x: x[0])

    trace_log.append(
        f"Phase 2 (commute rank): top3 avg_commute = "
        f"{', '.join(f'{s[0]:.0f}min' for s in scored[:3])}"
    )

    return [cand_tuple for _, cand_tuple in scored]
