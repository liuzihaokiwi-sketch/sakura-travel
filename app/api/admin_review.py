"""
Admin 数据审核 API

端点：
  GET  /admin/entities/review        列出待审核实体（trust_status != 'verified'）
  PATCH /admin/entities/{id}/trust   更新 trust_status
  GET  /admin/entities/stats         各 trust_status 数量统计
"""
from __future__ import annotations

import logging
from typing import Any, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.admin_auth import verify_admin_token
from app.db.models.catalog import EntityBase
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/entities", tags=["admin-review"])

TrustStatus = Literal["verified", "unverified", "ai_generated", "suspicious", "rejected"]


_auth_dep = Depends(verify_admin_token)


async def _get_session():
    async with AsyncSessionLocal() as session:
        yield session


# ── Schemas ───────────────────────────────────────────────────────────────────

class TrustUpdateRequest(BaseModel):
    trust_status: TrustStatus
    verified_by: Optional[str] = None
    trust_note: Optional[str] = None


class EntityReviewItem(BaseModel):
    entity_id: str
    name_zh: str
    name_ja: Optional[str]
    city_code: str
    entity_type: str
    data_tier: str
    trust_status: str
    lat: Optional[float]
    lng: Optional[float]
    verified_by: Optional[str]
    trust_note: Optional[str]

    class Config:
        from_attributes = True


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/review", response_model=list[EntityReviewItem])
async def list_review_entities(
    city_code: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    trust_status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(_get_session),
    _auth: Any = _auth_dep,
):
    """列出待审核实体。默认返回所有 trust_status != 'verified' 的记录。"""
    q = select(EntityBase)

    if trust_status:
        q = q.where(EntityBase.trust_status == trust_status)
    else:
        q = q.where(EntityBase.trust_status != "verified")

    if city_code:
        q = q.where(EntityBase.city_code == city_code)
    if entity_type:
        q = q.where(EntityBase.entity_type == entity_type)

    q = q.order_by(EntityBase.created_at.desc()).limit(limit).offset(offset)
    result = await session.execute(q)
    entities = result.scalars().all()

    return [
        EntityReviewItem(
            entity_id=str(e.entity_id),
            name_zh=e.name_zh,
            name_ja=e.name_ja,
            city_code=e.city_code,
            entity_type=e.entity_type,
            data_tier=e.data_tier,
            trust_status=e.trust_status,
            lat=float(e.lat) if e.lat is not None else None,
            lng=float(e.lng) if e.lng is not None else None,
            verified_by=e.verified_by,
            trust_note=e.trust_note,
        )
        for e in entities
    ]


@router.patch("/{entity_id}/trust")
async def update_trust_status(
    entity_id: UUID,
    body: TrustUpdateRequest,
    session: AsyncSession = Depends(_get_session),
    _auth: Any = _auth_dep,
):
    """更新实体 trust_status，可附带 verified_by 和 trust_note。"""
    entity = await session.get(EntityBase, entity_id)
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")

    entity.trust_status = body.trust_status
    if body.verified_by is not None:
        entity.verified_by = body.verified_by
    if body.trust_note is not None:
        entity.trust_note = body.trust_note

    if body.trust_status == "verified" and body.verified_by:
        from datetime import datetime, timezone
        entity.verified_at = datetime.now(timezone.utc)

    await session.commit()
    logger.info(
        "trust_status updated: entity=%s status=%s by=%s",
        entity_id, body.trust_status, body.verified_by,
    )
    return {"entity_id": str(entity_id), "trust_status": body.trust_status}


@router.get("/stats")
async def get_trust_stats(
    session: AsyncSession = Depends(_get_session),
    _auth: Any = _auth_dep,
):
    """各 trust_status 数量统计。"""
    result = await session.execute(
        select(EntityBase.trust_status, func.count(EntityBase.entity_id))
        .group_by(EntityBase.trust_status)
    )
    rows = result.all()
    return {row[0]: row[1] for row in rows}
