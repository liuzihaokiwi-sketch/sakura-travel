"""
Ops API – 活动簇管理
供管理后台"活动簇"页面使用。
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.city_circles import ActivityCluster, CircleEntityRole
from app.db.models.catalog import EntityBase
from app.db.session import get_db

router = APIRouter()


def _serialize_cluster(c: ActivityCluster) -> dict:
    return {
        "cluster_id": c.cluster_id,
        "circle_id": c.circle_id,
        "city_code": c.city_code,
        "name_zh": c.name_zh,
        "name_en": c.name_en,
        "level": c.level,
        "default_duration": c.default_duration,
        "anchor_entities": c.anchor_entities or [],
        "anchor_count": len(c.anchor_entities) if c.anchor_entities else 0,
        "is_active": c.is_active,
        "trip_role": c.trip_role,
        "experience_family": c.experience_family,
        "energy_level": c.energy_level,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


@router.get("/clusters")
async def list_clusters(
    city_code: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """列出所有活动簇"""
    from sqlalchemy import func
    stmt = select(ActivityCluster)
    if city_code:
        stmt = stmt.where(ActivityCluster.city_code == city_code)
    if level:
        stmt = stmt.where(ActivityCluster.level == level)
    if is_active is not None:
        stmt = stmt.where(ActivityCluster.is_active == is_active)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.order_by(ActivityCluster.city_code, ActivityCluster.level, ActivityCluster.cluster_id)
    stmt = stmt.limit(limit).offset(offset)
    clusters = (await db.execute(stmt)).scalars().all()

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": [_serialize_cluster(c) for c in clusters],
    }


@router.get("/clusters/{cluster_id}")
async def get_cluster(cluster_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    """单个簇详情 + 关联的 circle_entity_roles"""
    cluster = await db.get(ActivityCluster, cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="cluster not found")

    # 关联实体角色
    roles_res = await db.execute(
        select(CircleEntityRole, EntityBase)
        .join(EntityBase, CircleEntityRole.entity_id == EntityBase.entity_id)
        .where(CircleEntityRole.cluster_id == cluster_id)
        .order_by(CircleEntityRole.sort_order)
    )
    entity_roles = []
    for role, entity in roles_res.all():
        entity_roles.append({
            "role_id": role.role_id,
            "entity_id": str(role.entity_id),
            "entity_name": entity.name_zh,
            "entity_type": entity.entity_type,
            "role": role.role,
            "sort_order": role.sort_order,
            "is_cluster_anchor": role.is_cluster_anchor,
        })

    data = _serialize_cluster(cluster)
    data["entity_roles"] = entity_roles
    data["notes"] = cluster.notes
    data["description_zh"] = cluster.description_zh
    return data


class ClusterUpdate(BaseModel):
    name_zh: Optional[str] = None
    level: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None
    default_duration: Optional[str] = None


@router.patch("/clusters/{cluster_id}")
async def update_cluster(
    cluster_id: str,
    body: ClusterUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """更新簇的基础字段"""
    cluster = await db.get(ActivityCluster, cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="cluster not found")

    for field in ("name_zh", "level", "is_active", "notes", "default_duration"):
        val = getattr(body, field, None)
        if val is not None:
            setattr(cluster, field, val)

    await db.commit()
    return {"cluster_id": cluster_id, "updated": True}
