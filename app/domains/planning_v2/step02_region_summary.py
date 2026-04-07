"""
step02_region_summary.py — 地区摘要汇总

对 circle_cities 进行 SQL 聚合，按 city_code、entity_type、data_tier 分组统计。

输出 RegionSummary 包含：
  - circle_name
  - cities: list[str]
  - entity_count: 总数
  - entities_by_type: {poi: N, restaurant: N, hotel: N}
  - grade_distribution: {S: N, A: N, B: N, C: N}
"""

import logging
from typing import Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.catalog import EntityBase, Poi, Hotel, Restaurant
from app.domains.planning_v2.models import RegionSummary

logger = logging.getLogger(__name__)


async def build_region_summary(
    session: AsyncSession,
    circle_name: str,
    circle_cities: list[str]
) -> RegionSummary:
    """
    为 city_circle 构建地区摘要。

    逻辑：
      1. 按 city_code 过滤实体（WHERE city_code IN circle_cities）
      2. 按 entity_type 和 data_tier 分组统计
      3. 汇总为 RegionSummary

    Args:
        session: 数据库会话
        circle_name: 城市圈名称（如 'Kanto', 'Kansai', 'Hokkaido'）
        circle_cities: 该圈所属城市代码列表（如 ['tokyo', 'yokohama', 'kamakura']）

    Returns:
        RegionSummary: 地区统计摘要

    Raises:
        ValueError: 如果 circle_cities 为空或查询失败
    """

    if not circle_cities:
        raise ValueError(f"circle_cities 为空，无法构建 {circle_name} 的 RegionSummary")

    logger.info(
        f"Building region summary for {circle_name}: {len(circle_cities)} cities"
    )

    # 1. 统计总实体数（按 city_code 和 entity_type）
    entity_count_by_type = await _count_entities_by_type(
        session, circle_cities
    )

    # 2. 统计数据等级分布（按 data_tier）
    grade_distribution = await _count_entities_by_grade(
        session, circle_cities
    )

    # 3. 总实体数
    total_count = sum(entity_count_by_type.values())

    logger.info(
        f"Region summary for {circle_name}: "
        f"total={total_count}, "
        f"by_type={entity_count_by_type}, "
        f"grade_dist={grade_distribution}"
    )

    return RegionSummary(
        circle_name=circle_name,
        cities=circle_cities,
        entity_count=total_count,
        entities_by_type=entity_count_by_type,
        grade_distribution=grade_distribution
    )


async def _count_entities_by_type(
    session: AsyncSession,
    circle_cities: list[str]
) -> dict[str, int]:
    """
    按 entity_type 统计实体数量。

    Returns:
        {poi: N, restaurant: N, hotel: N, event: N, ...}
    """

    # SQL: SELECT entity_type, COUNT(*) FROM entity_base
    #      WHERE city_code IN ? AND is_active = true
    #      GROUP BY entity_type

    stmt = (
        select(
            EntityBase.entity_type,
            func.count(EntityBase.entity_id).label('count')
        )
        .where(
            and_(
                EntityBase.city_code.in_(circle_cities),
                EntityBase.is_active == True
            )
        )
        .group_by(EntityBase.entity_type)
    )

    result = await session.execute(stmt)
    rows = result.all()

    # 构造字典，缺少的类型填 0
    type_counts = {row[0]: row[1] for row in rows}

    # 确保常见类型存在
    for entity_type in ['poi', 'restaurant', 'hotel', 'event']:
        if entity_type not in type_counts:
            type_counts[entity_type] = 0

    return type_counts


async def _count_entities_by_grade(
    session: AsyncSession,
    circle_cities: list[str]
) -> dict[str, int]:
    """
    按 data_tier（等级）统计实体数量。

    data_tier 值通常为：S, A, B, C（但也可能有其他值）

    Returns:
        {S: N, A: N, B: N, C: N, ...}
    """

    # SQL: SELECT data_tier, COUNT(*) FROM entity_base
    #      WHERE city_code IN ? AND is_active = true
    #      GROUP BY data_tier

    stmt = (
        select(
            EntityBase.data_tier,
            func.count(EntityBase.entity_id).label('count')
        )
        .where(
            and_(
                EntityBase.city_code.in_(circle_cities),
                EntityBase.is_active == True
            )
        )
        .group_by(EntityBase.data_tier)
    )

    result = await session.execute(stmt)
    rows = result.all()

    # 构造字典
    grade_counts = {}
    for row in rows:
        tier = row[0] or 'unknown'
        grade_counts[tier] = row[1]

    # 确保标准等级存在（即使为 0）
    for tier in ['S', 'A', 'B', 'C']:
        if tier not in grade_counts:
            grade_counts[tier] = 0

    return grade_counts


async def _get_top_entities_by_type(
    session: AsyncSession,
    circle_cities: list[str],
    entity_type: str,
    limit: int = 10
) -> list[dict]:
    """
    获取该圈内评分最高的实体（特定类型）。

    用于调试和统计，不在 RegionSummary 输出中，但可用于补充信息。

    Args:
        session: 数据库会话
        circle_cities: 城市列表
        entity_type: 实体类型（poi/restaurant/hotel）
        limit: 返回数量限制

    Returns:
        list[dict]: 实体摘要列表
    """

    stmt = (
        select(
            EntityBase.entity_id,
            EntityBase.name_zh,
            EntityBase.data_tier,
            EntityBase.quality_tier
        )
        .where(
            and_(
                EntityBase.city_code.in_(circle_cities),
                EntityBase.entity_type == entity_type,
                EntityBase.is_active == True
            )
        )
        .order_by(EntityBase.data_tier.asc(), EntityBase.quality_tier.asc())
        .limit(limit)
    )

    result = await session.execute(stmt)
    rows = result.all()

    return [
        {
            'entity_id': str(row[0]),
            'name_zh': row[1],
            'data_tier': row[2],
            'quality_tier': row[3]
        }
        for row in rows
    ]
