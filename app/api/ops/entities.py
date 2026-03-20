from __future__ import annotations

from typing import Optional
"""
Ops API – Entity Search（运营端实体搜索）
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.catalog import EntityBase
from app.db.session import get_db

router = APIRouter()


@router.get("/entities/search")
async def search_entities(
    city: Optional[str] = Query(None, description="城市代码，如 tokyo / osaka"),
    entity_type: Optional[str] = Query(None, description="poi / hotel / restaurant"),
    data_tier: Optional[str] = Query(None, description="S / A / B"),
    is_active: bool = Query(True),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    按城市/类型/数据层级搜索实体（运营端使用）。
    """
    stmt = select(EntityBase)

    if city:
        stmt = stmt.where(EntityBase.city_code == city)
    if entity_type:
        stmt = stmt.where(EntityBase.entity_type == entity_type)
    if data_tier:
        stmt = stmt.where(EntityBase.data_tier == data_tier)

    stmt = stmt.where(EntityBase.is_active == is_active)
    stmt = stmt.order_by(EntityBase.created_at.desc())
    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    entities = result.scalars().all()

    return {
        "total": len(entities),
        "offset": offset,
        "limit": limit,
        "items": [
            {
                "entity_id": str(e.entity_id),
                "entity_type": e.entity_type,
                "name_zh": e.name_zh,
                "city_code": e.city_code,
                "area_name": e.area_name,
                "data_tier": e.data_tier,
                "lat": float(e.lat) if e.lat else None,
                "lng": float(e.lng) if e.lng else None,
            }
            for e in entities
        ],
    }
