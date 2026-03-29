"""
Ops API – Dashboard 数据统计
供管理后台"数据概览"页面使用。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.catalog import EntityBase
from app.db.models.city_circles import ActivityCluster
from app.db.session import get_db

router = APIRouter()


@router.get("/dashboard/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)) -> dict:
    """返回管理后台仪表板所需的汇总统计"""

    # ── 1. 按城市 + 类型的实体数量 ────────────────────────────────────────────
    city_type_res = await db.execute(
        select(
            EntityBase.city_code,
            EntityBase.entity_type,
            func.count().label("cnt"),
        )
        .where(EntityBase.is_active == True)  # noqa: E712
        .group_by(EntityBase.city_code, EntityBase.entity_type)
    )
    entity_counts: dict = {}
    for city_code, entity_type, cnt in city_type_res.all():
        if city_code not in entity_counts:
            entity_counts[city_code] = {"poi": 0, "hotel": 0, "restaurant": 0}
        entity_counts[city_code][entity_type] = cnt

    # ── 2. trust_status 分布 ──────────────────────────────────────────────────
    trust_res = await db.execute(
        select(
            EntityBase.trust_status,
            func.count().label("cnt"),
        )
        .group_by(EntityBase.trust_status)
    )
    trust_distribution: dict = {
        "verified": 0,
        "unverified": 0,
        "ai_generated": 0,
        "suspicious": 0,
        "rejected": 0,
    }
    for status, cnt in trust_res.all():
        if status in trust_distribution:
            trust_distribution[status] = cnt
        else:
            trust_distribution[status] = cnt

    # ── 3. 数据来源分布 ───────────────────────────────────────────────────────
    source_res = await db.execute(
        select(
            case(
                (EntityBase.google_place_id.isnot(None), "google"),
                else_="ai",
            ).label("source"),
            func.count().label("cnt"),
        )
        .group_by("source")
    )
    source_distribution: dict = {"google": 0, "ai": 0}
    for source, cnt in source_res.all():
        source_distribution[source] = cnt

    # ── 4. 活动簇统计 ─────────────────────────────────────────────────────────
    total_clusters_res = await db.execute(
        select(func.count()).select_from(ActivityCluster)
    )
    total_clusters = total_clusters_res.scalar() or 0

    active_clusters_res = await db.execute(
        select(func.count()).select_from(ActivityCluster).where(
            ActivityCluster.is_active == True  # noqa: E712
        )
    )
    active_clusters = active_clusters_res.scalar() or 0

    # 有 anchor_entities 的簇（非空 JSON）
    with_anchors_res = await db.execute(
        select(func.count()).select_from(ActivityCluster).where(
            ActivityCluster.anchor_entities.isnot(None)
        )
    )
    with_anchors = with_anchors_res.scalar() or 0

    # ── 5. 汇总数字卡片 ───────────────────────────────────────────────────────
    total_entities_res = await db.execute(
        select(func.count()).select_from(EntityBase).where(EntityBase.is_active == True)  # noqa: E712
    )
    total_entities = total_entities_res.scalar() or 0

    verified_res = await db.execute(
        select(func.count()).select_from(EntityBase).where(
            EntityBase.trust_status == "verified"
        )
    )
    verified_count = verified_res.scalar() or 0

    pending_review_res = await db.execute(
        select(func.count()).select_from(EntityBase).where(
            EntityBase.trust_status == "unverified"
        )
    )
    pending_review = pending_review_res.scalar() or 0

    # ── 6. 最近新增实体 ───────────────────────────────────────────────────────
    recent_res = await db.execute(
        select(EntityBase)
        .order_by(EntityBase.created_at.desc())
        .limit(10)
    )
    recent_entities = [
        {
            "entity_id": str(e.entity_id),
            "name_zh": e.name_zh,
            "entity_type": e.entity_type,
            "city_code": e.city_code,
            "trust_status": e.trust_status,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in recent_res.scalars().all()
    ]

    return {
        "summary": {
            "total_entities": total_entities,
            "verified_count": verified_count,
            "total_clusters": total_clusters,
            "pending_review": pending_review,
        },
        "entity_counts": entity_counts,
        "trust_distribution": trust_distribution,
        "source_distribution": source_distribution,
        "cluster_stats": {
            "total": total_clusters,
            "active": active_clusters,
            "with_anchors": with_anchors,
            "without_anchors": total_clusters - with_anchors,
        },
        "recent_entities": recent_entities,
    }
