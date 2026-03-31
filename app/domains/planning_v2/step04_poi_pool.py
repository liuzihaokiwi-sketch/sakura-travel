"""
step04_poi_pool.py — POI 候选池构建与缩减

从 entity_base 读取 POI 数据并按 10 条规则顺序过滤，
生成最终的候选景点池。

过滤规则（顺序执行）：
  1. 必须在 circle 的城市范围内（city_code in region_summary.cities）
  2. 必须 is_active=true
  3. 必须 data_tier in [S, A]
  4. 按 party_type 过滤（小孩不宜场景等）
  5. 按 budget_level 过滤（高预算可含高端体验）
  6. 按 season 过滤（best_season + travel dates）
  7. 排除 do_not_go_places
  8. 排除 visited_places
  9. 定休日初筛（reading entity_operating_fact）
  10. 排除 risk_flags（施工中、不稳定等）
"""

import logging
import uuid
from datetime import datetime, date
from typing import Optional

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.catalog import EntityBase, Poi, EntityTag
from app.db.models.soft_rules import EntityOperatingFact
from app.domains.planning_v2.models import (
    CandidatePool,
    UserConstraints,
    RegionSummary,
)

logger = logging.getLogger(__name__)

# 月份到季节的映射
_MONTH_TO_SEASON: dict[int, str] = {
    1: "winter", 2: "winter", 3: "spring", 4: "spring",
    5: "spring", 6: "summer", 7: "summer", 8: "summer",
    9: "autumn", 10: "autumn", 11: "autumn", 12: "winter",
}


def _parse_best_season(best_season_str: Optional[str]) -> set[str]:
    """将 best_season 字符串解析为季节集合。

    格式: "all", "all_year", "全年" 或 "spring,summer" 或 "spring" 等
    """
    if not best_season_str:
        return {"all"}

    bs = best_season_str.lower().strip()
    if bs in ("all", "all_year", "全年", ""):
        return {"all"}

    # 逗号分隔的季节列表
    seasons = {s.strip() for s in bs.split(",")}
    seasons = {s for s in seasons if s}  # 去空字符串

    return seasons if seasons else {"all"}


async def build_poi_pool(
    session: AsyncSession,
    user_constraints: UserConstraints,
    region_summary: RegionSummary,
    travel_dates: list[str],  # [YYYY-MM-DD, ...]
) -> list[CandidatePool]:
    """
    从 entity_base 读取并按规则缩减 POI 候选池。

    Args:
        session: 数据库会话
        user_constraints: 用户约束（包含 trip_window, user_profile, constraints）
        region_summary: 地区摘要（包含 circle_name, cities）
        travel_dates: 旅行日期列表 YYYY-MM-DD 格式

    Returns:
        list[CandidatePool]: 通过过滤的 POI 候选池
    """
    trace_log = []

    # 0. 初始数据准备
    circle_cities = region_summary.cities or []
    if not circle_cities:
        logger.warning("region_summary.cities 为空")
        return []

    # 解析约束
    do_not_go_places = set(user_constraints.constraints.get("do_not_go", []))
    visited_places = set(user_constraints.constraints.get("visited", []))
    must_visit = set(user_constraints.constraints.get("must_visit", []))

    # 提取用户画像
    user_profile = user_constraints.user_profile or {}
    party_type = user_profile.get("party_type", "couple")  # couple/family_young/family_teen/solo/group
    has_children = party_type in ("family_young", "family_teen")
    children_ages = user_profile.get("children_ages", [])
    has_elderly = user_profile.get("has_elderly", False)

    budget_tier = user_profile.get("budget_tier", "mid")  # budget/mid/premium/luxury
    avoid_tags = user_profile.get("avoid_tags", [])

    # 旅行月份（用于季节检查）
    travel_month = None
    if travel_dates:
        try:
            first_date = datetime.strptime(travel_dates[0], "%Y-%m-%d")
            travel_month = first_date.month
        except (ValueError, IndexError):
            logger.warning("无法解析旅行日期")

    travel_season = _MONTH_TO_SEASON.get(travel_month) if travel_month else None

    trace_log.append(f"circle_cities={circle_cities}, travel_month={travel_month}, season={travel_season}")
    trace_log.append(f"party_type={party_type}, budget_tier={budget_tier}")

    # 1. 查询基础 POI（entity_type='poi'）
    query = select(EntityBase).where(
        and_(
            EntityBase.entity_type == "poi",
            EntityBase.city_code.in_(circle_cities),
            EntityBase.is_active == True,
            EntityBase.data_tier.in_(["S", "A"]),
        )
    ).order_by(EntityBase.entity_id)

    result = await session.execute(query)
    entities = result.scalars().all()
    count_after_base = len(entities)
    trace_log.append(f"Step 1 (base filter): {count_after_base} POI")

    if not entities:
        logger.info(f"[POI池] 无符合条件的 POI: cities={circle_cities}, tier=S/A")
        return []

    entity_ids = [e.entity_id for e in entities]

    # 2. 批量加载 Poi 扩展数据
    poi_query = select(Poi).where(Poi.entity_id.in_(entity_ids))
    poi_result = await session.execute(poi_query)
    poi_map: dict[uuid.UUID, Poi] = {p.entity_id: p for p in poi_result.scalars().all()}

    # 3. 批量加载标签
    tags_query = select(EntityTag).where(
        EntityTag.entity_id.in_(entity_ids)
    )
    tags_result = await session.execute(tags_query)
    entity_tags: dict[uuid.UUID, set[str]] = {}
    for tag in tags_result.scalars().all():
        entity_tags.setdefault(tag.entity_id, set()).add(
            tag.tag_value.lower() if tag.tag_value else ""
        )

    # 4. 批量加载运营事实（用于定休日和风险检查）
    facts_query = select(EntityOperatingFact).where(
        EntityOperatingFact.entity_id.in_(entity_ids)
    )
    facts_result = await session.execute(facts_query)
    entity_facts: dict[uuid.UUID, list[EntityOperatingFact]] = {}
    for fact in facts_result.scalars().all():
        entity_facts.setdefault(fact.entity_id, []).append(fact)

    # 5. 执行过滤规则
    filtered_entities = []

    for entity in entities:
        eid = entity.entity_id
        poi = poi_map.get(eid)
        tags = entity_tags.get(eid, set())
        facts = entity_facts.get(eid, [])

        # Rule 4: 按 party_type 过滤
        if has_children and children_ages:
            min_age = min(children_ages)
            if "adults_only" in tags or "bar" in tags or "nightclub" in tags:
                if min_age < 18:
                    continue  # 过滤掉

        if has_elderly and "extreme_physical" in tags:
            continue  # 过滤掉

        # Rule 5: 按 budget_level 过滤
        # 仅在高端体验标签且用户低预算时过滤
        if budget_tier in ("budget", "mid"):
            if "luxury_only" in tags or "vip_only" in tags:
                continue

        # Rule 6: 按 season 过滤
        if travel_season and poi:
            best_season = poi.best_season
            if best_season:
                valid_seasons = _parse_best_season(best_season)
                if "all" not in valid_seasons and travel_season not in valid_seasons:
                    continue

        # Rule 7: 排除 do_not_go_places
        if str(eid) in do_not_go_places:
            continue

        # Rule 8: 排除 visited_places
        if str(eid) in visited_places:
            continue

        # Rule 9: 定休日初筛
        if facts:
            is_permanently_closed = False
            for fact in facts:
                fact_key = (fact.fact_key or "").lower()
                fact_value = (fact.fact_value or "").lower()
                if fact_key == "status" and fact_value in ("permanently_closed", "long_term_closed"):
                    is_permanently_closed = True
                    break
            if is_permanently_closed:
                continue

        # Rule 10: 排除 risk_flags
        if entity.risk_flags:
            # risk_flags 包含 施工中、不稳定等风险标签
            skip_risk_flags = {"renovation", "construction", "unstable", "dangerous"}
            if any(flag in skip_risk_flags for flag in entity.risk_flags):
                continue

        # Rule 6 补充：用户 avoid_tags
        if avoid_tags:
            avoid_set = {t.lower() for t in avoid_tags}
            if tags & avoid_set:
                continue

        # 通过所有过滤规则
        filtered_entities.append(entity)

    count_after_filter = len(filtered_entities)
    trace_log.append(f"Step 2-10 (all filters): {count_after_filter} POI")

    # 6. 转换为 CandidatePool
    candidate_pools = []
    for entity in filtered_entities:
        eid = entity.entity_id
        poi = poi_map.get(eid)
        tags = entity_tags.get(eid, set())

        # 提取 cost_jpy
        cost_jpy = 0
        if poi and poi.admission_fee_jpy:
            cost_jpy = int(poi.admission_fee_jpy)

        # 提取 visit_minutes
        visit_minutes = 60  # 默认
        if poi and poi.typical_duration_min:
            visit_minutes = int(poi.typical_duration_min)
        elif entity.typical_duration_baseline:
            visit_minutes = int(entity.typical_duration_baseline)

        # 获取 best_season 用于展示
        best_season = None
        if poi and poi.best_season:
            best_season = poi.best_season

        # 构建开放时间字典
        open_hours = {}
        if poi and poi.opening_hours_json:
            open_hours = poi.opening_hours_json

        # 构建评分信号
        review_signals = {}
        if poi:
            if poi.google_rating:
                review_signals["google_rating"] = float(poi.google_rating)
            if poi.google_review_count:
                review_signals["google_review_count"] = int(poi.google_review_count)

        # 创建 CandidatePool
        pool = CandidatePool(
            entity_id=str(eid),
            name_zh=entity.name_zh,
            entity_type="poi",
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
        f"[POI池] 完成过滤: {count_after_base} -> {count_after_filter} -> {len(candidate_pools)} pools. "
        f"circle={region_summary.circle_name}, season={travel_season}"
    )
    for line in trace_log:
        logger.debug(f"  {line}")

    return candidate_pools
