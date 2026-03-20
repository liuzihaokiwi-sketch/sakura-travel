"""
app/api/ops/ranked.py
---------------------
运营端排名查询 API

端点：
  GET /ops/entities/ranked     按评分降序返回实体列表
  GET /ops/entities/score/{id} 查询单个实体的评分详情
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.domains.ranking.queries import get_entity_score, get_ranked_entities

router = APIRouter()


@router.get("/entities/ranked")
async def ranked_entities(
    city_code: Optional[str] = Query(None, description="城市代码，如 tokyo / osaka / kyoto"),
    entity_type: Optional[str] = Query(None, description="poi / hotel / restaurant"),
    score_profile: str = Query("general", description="评分 profile"),
    min_score: Optional[float] = Query(None, ge=0.0, le=100.0, description="最低分数过滤"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    按 final_score 降序返回实体排名列表。

    支持按城市、实体类型、评分 profile 过滤。
    结果包含 score_breakdown 可用于调试和解释。
    """
    items = await get_ranked_entities(
        session=db,
        city_code=city_code,
        entity_type=entity_type,
        score_profile=score_profile,
        limit=limit,
        offset=offset,
        min_score=min_score,
    )
    return {
        "total": len(items),
        "offset": offset,
        "limit": limit,
        "city_code": city_code,
        "entity_type": entity_type,
        "score_profile": score_profile,
        "items": items,
    }


@router.get("/entities/score/{entity_id}")
async def entity_score_detail(
    entity_id: str,
    score_profile: str = Query("general"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    查询单个实体的评分详情（含 score_breakdown 明细）。
    """
    from fastapi import HTTPException
    score = await get_entity_score(session=db, entity_id=entity_id, score_profile=score_profile)
    if score is None:
        raise HTTPException(status_code=404, detail=f"实体 {entity_id!r} 暂无评分记录")
    return score
