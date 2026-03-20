"""
app/api/ops/editorial.py
------------------------
运营端 Editorial Boost API

端点：
  POST   /ops/entities/{entity_type}/{entity_id}/editorial-score
  GET    /ops/entities/{entity_type}/{entity_id}/editorial-history
  PATCH  /ops/entities/{entity_id}/data-tier
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.catalog import EntityBase, EntityEditorNote
from app.db.session import get_db
from app.core.queue import enqueue_job

router = APIRouter()

VALID_ENTITY_TYPES = {"poi", "hotel", "restaurant"}
VALID_DATA_TIERS = {"S", "A", "B"}


# ── Pydantic 模型 ─────────────────────────────────────────────────────────────

class EditorialScoreRequest(BaseModel):
    boost_value: int = Field(..., ge=-8, le=8, description="编辑修正值（-8 ~ +8）")
    reason: Optional[str] = Field(None, max_length=500, description="修正原因备注（中文）")
    valid_until: Optional[datetime] = Field(None, description="有效截止时间（ISO 8601），None = 永久有效")
    created_by: Optional[str] = Field(None, max_length=100, description="操作人")


class DataTierUpdateRequest(BaseModel):
    data_tier: str = Field(..., description="数据层级：S / A / B")

    @field_validator("data_tier")
    @classmethod
    def validate_tier(cls, v: str) -> str:
        if v not in VALID_DATA_TIERS:
            raise ValueError(f"data_tier 必须是 S、A 或 B，收到: {v!r}")
        return v


# ── POST /ops/entities/{entity_type}/{entity_id}/editorial-score ──────────────

@router.post("/entities/{entity_type}/{entity_id}/editorial-score", status_code=201)
async def set_editorial_score(
    entity_type: str = Path(..., description="实体类型: poi / hotel / restaurant"),
    entity_id: str = Path(..., description="实体 UUID"),
    body: EditorialScoreRequest = ...,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    为实体添加 Editorial Boost 记录，然后自动触发重新评分。

    - boost_value 范围：-8 ~ +8
    - 写入 entity_editor_notes（note_type="editorial_boost"）
    - 自动入队 score_entities job 重新计算 final_score
    """
    if entity_type not in VALID_ENTITY_TYPES:
        raise HTTPException(status_code=422, detail=f"entity_type 无效: {entity_type!r}")

    import uuid as _uuid
    try:
        eid = _uuid.UUID(entity_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="entity_id 不是合法 UUID")

    # 校验实体存在
    stmt = select(EntityBase).where(
        EntityBase.entity_id == eid,
        EntityBase.entity_type == entity_type,
    )
    result = await db.execute(stmt)
    entity = result.scalar_one_or_none()
    if entity is None:
        raise HTTPException(
            status_code=404,
            detail=f"实体不存在: {entity_type}/{entity_id}",
        )

    # 写入 editorial_boost 记录
    note = EntityEditorNote(
        entity_id=eid,
        note_type="editorial_boost",
        boost_value=body.boost_value,
        content_zh=body.reason,
        valid_until=body.valid_until,
        created_by=body.created_by,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)

    # 异步触发重算
    try:
        await enqueue_job("score_entities", entity_type=entity_type, city_code=entity.city_code)
    except Exception:
        pass  # 入队失败不影响 API 响应

    return {
        "note_id": note.id,
        "entity_id": str(eid),
        "entity_type": entity_type,
        "boost_value": body.boost_value,
        "valid_until": body.valid_until.isoformat() if body.valid_until else None,
        "created_at": note.created_at.isoformat(),
        "message": "Editorial boost 已记录，评分将异步重新计算",
    }


# ── GET /ops/entities/{entity_type}/{entity_id}/editorial-history ─────────────

@router.get("/entities/{entity_type}/{entity_id}/editorial-history")
async def get_editorial_history(
    entity_type: str = Path(...),
    entity_id: str = Path(...),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    返回指定实体的 editorial_boost 历史记录，按 created_at 降序。
    """
    if entity_type not in VALID_ENTITY_TYPES:
        raise HTTPException(status_code=422, detail=f"entity_type 无效: {entity_type!r}")

    import uuid as _uuid
    try:
        eid = _uuid.UUID(entity_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="entity_id 不是合法 UUID")

    stmt = (
        select(EntityEditorNote)
        .where(
            EntityEditorNote.entity_id == eid,
            EntityEditorNote.note_type == "editorial_boost",
        )
        .order_by(EntityEditorNote.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    notes = result.scalars().all()

    now = datetime.now(tz=timezone.utc)

    return {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "total": len(notes),
        "items": [
            {
                "note_id": n.id,
                "boost_value": n.boost_value,
                "reason": n.content_zh,
                "created_by": n.created_by,
                "valid_until": n.valid_until.isoformat() if n.valid_until else None,
                "is_active": (
                    n.valid_until is None
                    or (
                        n.valid_until.replace(tzinfo=timezone.utc)
                        if n.valid_until.tzinfo is None
                        else n.valid_until
                    ) > now
                ),
                "created_at": n.created_at.isoformat(),
            }
            for n in notes
        ],
    }


# ── PATCH /ops/entities/{entity_id}/data-tier ────────────────────────────────

@router.patch("/entities/{entity_id}/data-tier")
async def update_data_tier(
    entity_id: str = Path(..., description="实体 UUID"),
    body: DataTierUpdateRequest = ...,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    更新实体的 data_tier（S/A/B）。
    更新后自动触发评分重算（data_tier 影响置信度折扣）。
    """
    import uuid as _uuid
    try:
        eid = _uuid.UUID(entity_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="entity_id 不是合法 UUID")

    stmt = select(EntityBase).where(EntityBase.entity_id == eid)
    result = await db.execute(stmt)
    entity = result.scalar_one_or_none()
    if entity is None:
        raise HTTPException(status_code=404, detail=f"实体不存在: {entity_id}")

    old_tier = entity.data_tier
    entity.data_tier = body.data_tier
    await db.commit()

    # 触发重算
    try:
        await enqueue_job("score_entities", city_code=entity.city_code, entity_type=entity.entity_type)
    except Exception:
        pass

    return {
        "entity_id": entity_id,
        "entity_type": entity.entity_type,
        "city_code": entity.city_code,
        "old_data_tier": old_tier,
        "new_data_tier": body.data_tier,
        "message": "data_tier 已更新，评分将异步重新计算",
    }
