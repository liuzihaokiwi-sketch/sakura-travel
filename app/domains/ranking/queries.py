"""
app/domains/ranking/queries.py
------------------------------
评分相关的数据库查询函数。

公开函数：
  - get_ranked_entities:  按评分排序返回实体列表（JOIN entity_base + entity_scores）
  - get_entity_score:     查询单个实体的评分详情
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.catalog import EntityBase
from app.db.models.derived import EntityScore


async def get_ranked_entities(
    session: AsyncSession,
    city_code: str | None = None,
    entity_type: str | None = None,
    score_profile: str = "general",
    limit: int = 50,
    offset: int = 0,
    min_score: float | None = None,
) -> list[dict[str, Any]]:
    """
    按 final_score 降序返回实体列表（JOIN entity_base + entity_scores）。

    Args:
        session:       AsyncSession
        city_code:     城市代码过滤（None = 不过滤）
        entity_type:   实体类型过滤 poi/hotel/restaurant（None = 不过滤）
        score_profile: 评分 profile（默认 "general"）
        limit:         返回条数上限（默认 50，最大 200）
        offset:        分页偏移量
        min_score:     最低 final_score 过滤（None = 不过滤）

    Returns:
        列表，每项为：
        {
            "entity_id": str,
            "entity_type": str,
            "name_zh": str | None,
            "name_ja": str | None,
            "city_code": str,
            "data_tier": str,
            "final_score": float,
            "base_score": float,
            "editorial_boost": int,
            "score_breakdown": dict,
            "computed_at": str,  # ISO 8601
        }
    """
    limit = min(limit, 200)  # 硬限制最大 200 条

    stmt = (
        select(EntityBase, EntityScore)
        .join(EntityScore, EntityBase.entity_id == EntityScore.entity_id)
        .where(
            EntityBase.is_active == True,  # noqa: E712
            EntityScore.score_profile == score_profile,
        )
        .order_by(EntityScore.final_score.desc())
        .offset(offset)
        .limit(limit)
    )

    if city_code:
        stmt = stmt.where(EntityBase.city_code == city_code)
    if entity_type:
        stmt = stmt.where(EntityBase.entity_type == entity_type)
    if min_score is not None:
        stmt = stmt.where(EntityScore.final_score >= min_score)

    result = await session.execute(stmt)
    rows = result.all()

    return [
        {
            "entity_id": str(entity.entity_id),
            "entity_type": entity.entity_type,
            "name_zh": entity.name_zh,
            "name_ja": entity.name_ja,
            "city_code": entity.city_code,
            "data_tier": entity.data_tier,
            "final_score": float(score.final_score),
            "base_score": float(score.base_score),
            "editorial_boost": int(score.editorial_boost or 0),
            "score_breakdown": score.score_breakdown or {},
            "computed_at": score.computed_at.isoformat() if score.computed_at else None,
        }
        for entity, score in rows
    ]


async def get_entity_score(
    session: AsyncSession,
    entity_id: str,
    score_profile: str = "general",
) -> dict[str, Any] | None:
    """
    查询单个实体的评分详情。

    Args:
        session:       AsyncSession
        entity_id:     实体 UUID 字符串
        score_profile: 评分 profile

    Returns:
        评分详情字典，或 None（实体不存在或无评分）
    """
    import uuid as _uuid
    try:
        eid = _uuid.UUID(entity_id)
    except ValueError:
        return None

    stmt = (
        select(EntityBase, EntityScore)
        .join(EntityScore, EntityBase.entity_id == EntityScore.entity_id)
        .where(
            EntityBase.entity_id == eid,
            EntityScore.score_profile == score_profile,
        )
    )
    result = await session.execute(stmt)
    row = result.one_or_none()
    if row is None:
        return None

    entity, score = row
    return {
        "entity_id": str(entity.entity_id),
        "entity_type": entity.entity_type,
        "name_zh": entity.name_zh,
        "name_ja": entity.name_ja,
        "city_code": entity.city_code,
        "data_tier": entity.data_tier,
        "final_score": float(score.final_score),
        "base_score": float(score.base_score),
        "editorial_boost": int(score.editorial_boost or 0),
        "score_breakdown": score.score_breakdown or {},
        "computed_at": score.computed_at.isoformat() if score.computed_at else None,
    }
