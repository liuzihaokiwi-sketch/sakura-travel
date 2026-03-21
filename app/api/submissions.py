"""
Quiz Submissions API — 问卷提交的 CRUD 端点。

前端 quiz 页面提交 → POST /submissions
管理后台读取列表 → GET /submissions
管理后台更新状态 → PATCH /submissions/{id}
"""
from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/submissions", tags=["submissions"])


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class SubmissionCreate(BaseModel):
    """前端 /quiz 页面提交的问卷数据（免费阶段只收 dest+style）"""
    name: Optional[str] = None
    destination: str
    styles: list[str] = Field(default_factory=list)
    # 免费阶段以下字段均为可选，默认值保证兼容
    duration_days: int = Field(ge=1, le=30, default=7)
    people_count: Optional[int] = None
    party_type: str = "unknown"
    japan_experience: Optional[str] = None
    play_mode: Optional[str] = None
    budget_focus: Optional[str] = None
    wechat_id: Optional[str] = None


# submissions 使用与 orders 相同的统一 11 状态
SUBMISSION_VALID_TRANSITIONS = {
    "new":              ["sample_viewed", "cancelled"],
    "sample_viewed":    ["paid", "cancelled"],
    "paid":             ["detail_filling", "refunded"],
    "detail_filling":   ["detail_submitted"],
    "detail_submitted": ["validating"],
    "validating":       ["needs_fix", "validated"],
    "needs_fix":        ["detail_filling"],
    "validated":        ["generating"],
    "generating":       ["done"],
    "done":             ["delivered"],
    "delivered":        ["refunded"],
    "cancelled":        [],
    "refunded":         [],
}


class SubmissionUpdate(BaseModel):
    """管理后台更新状态"""
    status: Optional[str] = None
    notes: Optional[str] = None


class SubmissionOut(BaseModel):
    id: str
    name: Optional[str] = None
    destination: str
    duration_days: int
    people_count: Optional[int] = None
    party_type: str
    japan_experience: Optional[str] = None
    play_mode: Optional[str] = None
    budget_focus: Optional[str] = None
    styles: list[str] = []
    wechat_id: Optional[str] = None
    status: str
    notes: Optional[str] = None
    created_at: str
    updated_at: str


# ── POST /submissions — 提交问卷 ─────────────────────────────────────────────

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_submission(
    body: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            INSERT INTO quiz_submissions
                (name, destination, duration_days, people_count, party_type,
                 japan_experience, play_mode, budget_focus, styles, wechat_id, status)
            VALUES
                (:name, :destination, :duration_days, :people_count, :party_type,
                 :japan_experience, :play_mode, :budget_focus, :styles, :wechat_id, 'new')
            RETURNING id, created_at
        """),
        {
            "name": body.name,
            "destination": body.destination,
            "duration_days": body.duration_days,
            "people_count": body.people_count,
            "party_type": body.party_type,
            "japan_experience": body.japan_experience,
            "play_mode": body.play_mode,
            "budget_focus": body.budget_focus,
            "styles": body.styles,
            "wechat_id": body.wechat_id,
        },
    )
    row = result.fetchone()
    await db.commit()

    return {
        "id": str(row.id),
        "status": "new",
        "message": "已收到你的需求！规划师会在 2 小时内通过微信联系你。",
    }


# ── GET /submissions — 列表（管理后台用） ─────────────────────────────────────

@router.get("")
async def list_submissions(
    status_filter: Optional[str] = None,
    limit: int = 200,
    db: AsyncSession = Depends(get_db),
):
    sql = "SELECT * FROM quiz_submissions"
    params: dict = {}
    if status_filter:
        sql += " WHERE status = :status_filter"
        params["status_filter"] = status_filter
    sql += " ORDER BY created_at DESC LIMIT :limit"
    params["limit"] = limit

    result = await db.execute(text(sql), params)
    rows = result.mappings().all()

    return [
        {
            "id": str(r["id"]),
            "name": r.get("name"),
            "destination": r["destination"],
            "duration_days": r["duration_days"],
            "people_count": r.get("people_count"),
            "party_type": r["party_type"],
            "japan_experience": r.get("japan_experience"),
            "play_mode": r.get("play_mode"),
            "budget_focus": r.get("budget_focus"),
            "styles": r.get("styles") or [],
            "wechat_id": r.get("wechat_id"),
            "status": r["status"],
            "notes": r.get("notes"),
            "created_at": str(r["created_at"]),
            "updated_at": str(r["updated_at"]),
        }
        for r in rows
    ]


# ── GET /submissions/{id} — 单条详情 ─────────────────────────────────────────

@router.get("/{submission_id}")
async def get_submission(
    submission_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("SELECT * FROM quiz_submissions WHERE id = :id"),
        {"id": submission_id},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="提交记录不存在")

    return {
        "id": str(row["id"]),
        "name": row.get("name"),
        "destination": row["destination"],
        "duration_days": row["duration_days"],
        "people_count": row.get("people_count"),
        "party_type": row["party_type"],
        "japan_experience": row.get("japan_experience"),
        "play_mode": row.get("play_mode"),
        "budget_focus": row.get("budget_focus"),
        "styles": row.get("styles") or [],
        "wechat_id": row.get("wechat_id"),
        "status": row["status"],
        "notes": row.get("notes"),
        "created_at": str(row["created_at"]),
        "updated_at": str(row["updated_at"]),
    }


# ── PATCH /submissions/{id} — 更新状态（管理后台用） ──────────────────────────

@router.patch("/{submission_id}")
async def update_submission(
    submission_id: str,
    body: SubmissionUpdate,
    db: AsyncSession = Depends(get_db),
):
    updates = []
    params: dict = {"id": submission_id}

    if body.status is not None:
        # 校验状态流转合法性
        current_result = await db.execute(
            text("SELECT status FROM quiz_submissions WHERE id = :id"),
            {"id": submission_id},
        )
        current_row = current_result.fetchone()
        if not current_row:
            raise HTTPException(status_code=404, detail="提交记录不存在")

        current_status = current_row[0]
        target_status = body.status
        allowed = SUBMISSION_VALID_TRANSITIONS.get(current_status, [])
        if target_status not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"无法从 '{current_status}' 转到 '{target_status}'，允许: {allowed}",
            )

        updates.append("status = :new_status")
        params["new_status"] = target_status
    if body.notes is not None:
        updates.append("notes = :notes")
        params["notes"] = body.notes

    updates.append("updated_at = NOW()")

    if not updates:
        raise HTTPException(status_code=400, detail="没有需要更新的字段")

    sql = f"UPDATE quiz_submissions SET {', '.join(updates)} WHERE id = :id RETURNING id"
    result = await db.execute(text(sql), params)
    row = result.fetchone()
    await db.commit()

    if not row:
        raise HTTPException(status_code=404, detail="提交记录不存在")

    return {"ok": True, "id": str(row.id)}