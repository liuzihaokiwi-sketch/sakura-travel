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


# submissions 使用统一状态机（13 状态）
# 生成完 → using（用户使用中，可微调）→ 旅程结束后 → archived（归档）
SUBMISSION_VALID_TRANSITIONS = {
    "new":              ["sample_viewed", "cancelled"],
    "sample_viewed":    ["paid", "cancelled"],
    "paid":             ["detail_filling", "refunded"],
    "detail_filling":   ["detail_submitted"],
    "detail_submitted": ["validating"],
    "validating":       ["needs_fix", "validated"],
    "needs_fix":        ["detail_filling"],
    "validated":        ["generating"],
    "generating":       ["generating_full", "done"],
    "generating_full":  ["done"],
    "done":             ["delivered"],
    "delivered":        ["using", "refunded"],
    "using":            ["archived"],
    "archived":         [],
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
    archived_at: Optional[str] = None
    travel_end_date: Optional[str] = None
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
    include_archived: bool = False,
    limit: int = 200,
    db: AsyncSession = Depends(get_db),
):
    sql = "SELECT * FROM quiz_submissions"
    conditions: list[str] = []
    params: dict = {}

    if status_filter:
        conditions.append("status = :status_filter")
        params["status_filter"] = status_filter
    if not include_archived:
        conditions.append("(archived_at IS NULL AND status != 'archived')")

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY created_at DESC LIMIT :limit"
    params["limit"] = limit

    result = await db.execute(text(sql), params)
    rows = result.mappings().all()

    return [_row_to_dict(r) for r in rows]


# ── POST /submissions/{id}/generate — 从 submission 触发攻略生成 ──────────────

@router.post("/{submission_id}/generate")
async def generate_from_submission(
    submission_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    从 quiz_submission + detail_form 数据创建 trip_request 并触发生成。

    1. 读 quiz_submission 拿 destination / duration_days / styles
    2. 读 detail_form 拿详细偏好（如果有）
    3. 在 trip_requests 表创建记录（如不存在）
    4. 自动匹配模板 + 调用 assemble_trip
    5. 更新 quiz_submission 状态为 generating
    """
    import asyncio
    import uuid as _uuid

    from app.db.models.business import TripRequest
    from app.db.models.detail_forms import DetailForm
    from sqlalchemy import select

    # 1. 读 submission
    sub_res = await db.execute(
        text("SELECT * FROM quiz_submissions WHERE id = :id"),
        {"id": submission_id},
    )
    sub = sub_res.mappings().first()
    if not sub:
        raise HTTPException(status_code=404, detail="提交记录不存在")

    destination = sub["destination"]
    duration = sub["duration_days"]
    party = sub.get("party_type") or "couple"
    styles = sub.get("styles") or []

    # 2. 读 detail_form（如果有）
    form_data = {}
    form_res = await db.execute(
        select(DetailForm).where(DetailForm.submission_id == submission_id)
    )
    form = form_res.scalar_one_or_none()
    if form:
        form_data = {
            "cities": form.cities,
            "party_type": form.party_type or party,
            "budget_level": form.budget_level,
            "must_have_tags": form.must_have_tags,
            "pace": form.pace,
            "free_text_wishes": form.free_text_wishes,
        }

    # 3. 创建 trip_request（幂等——通过 raw_input.submission_id 查重）
    existing_tr = await db.execute(
        text("SELECT trip_request_id FROM trip_requests WHERE raw_input->>'submission_id' = :sid"),
        {"sid": submission_id},
    )
    existing_row = existing_tr.fetchone()

    if existing_row:
        tr_id = existing_row[0]
    else:
        raw_input = {
            "submission_id": submission_id,
            "destination": destination,
            "duration_days": duration,
            "party_type": party,
            "styles": styles,
            **{k: v for k, v in form_data.items() if v},
        }
        tr_id = _uuid.uuid4()
        new_tr = TripRequest(
            trip_request_id=tr_id,
            raw_input=raw_input,
            status="assembling",
        )
        db.add(new_tr)
        await db.commit()
        await db.refresh(new_tr)

    # 4. 自动匹配模板
    dest_map = {
        "tokyo": "tokyo_classic",
        "osaka-kyoto": "kansai_classic",
        "tokyo-osaka-kyoto": "golden_route",
        "hokkaido": "hokkaido_classic",
        "okinawa": "okinawa_beach",
    }
    base_code = dest_map.get(destination, "tokyo_classic")
    template_code = f"{base_code}_{duration}d"

    scene_map = {
        "couple": "couple",
        "solo": "solo",
        "family": "family",
        "family_child": "family",
        "friends": "solo",
        "parents": "senior",
    }
    scene = scene_map.get(party, "couple")

    # 5. 更新 trip_request 状态 + 启动 inline 生成
    await db.execute(
        text("UPDATE trip_requests SET status='assembling' WHERE trip_request_id = :id"),
        {"id": str(tr_id)},
    )
    await db.commit()

    # Inline 执行（无 Redis 队列场景）
    from app.db.session import AsyncSessionLocal as _SF
    from app.domains.planning.assembler import assemble_trip, enrich_itinerary_with_copy
    from app.domains.planning.report_generator import generate_report

    async def _run():
        async with _SF() as _s:
            try:
                # Phase 1: 骨架装配（模板 + 实体填充）
                plan_id = await assemble_trip(
                    session=_s,
                    trip_request_id=_uuid.UUID(str(tr_id)),
                    template_code=template_code,
                    scene=scene,
                )
                # Phase 2: 逐实体文案润色
                await enrich_itinerary_with_copy(
                    session=_s, plan_id=plan_id, scene=scene,
                )
                # Phase 3: 3层报告生成（总纲 + 每日骨架 + 条件页 + 附录）
                user_ctx = {
                    "party_type": party,
                    "styles": styles if isinstance(styles, list) else [styles] if styles else [],
                    "budget_level": form_data.get("budget_level", "mid"),
                    "pace": form_data.get("pace", "moderate"),
                }
                # Phase 3: 3层报告生成（用独立 session，避免长 AI 调用导致 _s 超时）
                async with _SF() as _sr:
                    await generate_report(
                        session=_sr, plan_id=plan_id, user_context=user_ctx,
                    )
                # 更新 trip_request 状态 → done（generate_report 已经把 plan 设为 done）
                async with _SF() as _s2:
                    await _s2.execute(
                        text("UPDATE trip_requests SET status='done', updated_at=NOW() WHERE trip_request_id = :id"),
                        {"id": str(tr_id)},
                    )
                    await _s2.commit()
                # 更新 quiz_submission 状态为 done
                async with _SF() as _s3:
                    await _s3.execute(
                        text("UPDATE quiz_submissions SET status='done', updated_at=NOW() WHERE id = :id"),
                        {"id": submission_id},
                    )
                    await _s3.commit()
            except Exception as _exc:
                import logging as _log
                _log.getLogger(__name__).exception("generate_from_submission 失败: %s", _exc)
                async with _SF() as _s4:
                    _tr = await _s4.get(TripRequest, _uuid.UUID(str(tr_id)))
                    if _tr:
                        _tr.status = "failed"
                        await _s4.commit()

    asyncio.ensure_future(_run())

    return {
        "ok": True,
        "submission_id": submission_id,
        "trip_request_id": str(tr_id),
        "template_code": template_code,
        "scene": scene,
        "message": "攻略生成已启动，请稍候刷新查看",
    }


def _row_to_dict(r) -> dict:
    """Convert a quiz_submissions row mapping to API dict."""
    return {
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
        "archived_at": str(r["archived_at"]) if r.get("archived_at") else None,
        "travel_end_date": str(r["travel_end_date"]) if r.get("travel_end_date") else None,
        "created_at": str(r["created_at"]),
        "updated_at": str(r["updated_at"]),
    }


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

    # 查关联的 trip_request_id
    tr_result = await db.execute(
        text("SELECT trip_request_id FROM trip_requests WHERE raw_input->>'submission_id' = :sid"),
        {"sid": submission_id},
    )
    tr_row = tr_result.first()
    trip_request_id = str(tr_row[0]) if tr_row else None

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
        "trip_request_id": trip_request_id,
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


# ── POST /submissions/{id}/archive — 归档 ────────────────────────────────────

@router.post("/{submission_id}/archive")
async def archive_submission(
    submission_id: str,
    db: AsyncSession = Depends(get_db),
):
    """归档表单：设置 status=archived, archived_at=NOW()"""
    current = await db.execute(
        text("SELECT status FROM quiz_submissions WHERE id = :id"),
        {"id": submission_id},
    )
    row = current.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="提交记录不存在")

    cur_status = row[0]
    allowed = SUBMISSION_VALID_TRANSITIONS.get(cur_status, [])
    if "archived" not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"状态 '{cur_status}' 不能直接归档，需要先转到 'using'",
        )

    await db.execute(
        text(
            "UPDATE quiz_submissions SET status='archived', archived_at=NOW(), updated_at=NOW() "
            "WHERE id = :id"
        ),
        {"id": submission_id},
    )
    await db.commit()
    return {"ok": True, "id": submission_id, "status": "archived"}


# ── GET /submissions/archived — 归档历史列表 ──────────────────────────────────

@router.get("/archived/list")
async def list_archived_submissions(
    destination: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """查询已归档的表单，支持按目的地筛选。"""
    sql = "SELECT * FROM quiz_submissions WHERE (status = 'archived' OR archived_at IS NOT NULL)"
    params: dict = {"limit": limit, "offset": offset}

    if destination:
        sql += " AND destination ILIKE :dest"
        params["dest"] = f"%{destination}%"

    sql += " ORDER BY archived_at DESC NULLS LAST, updated_at DESC LIMIT :limit OFFSET :offset"

    result = await db.execute(text(sql), params)
    rows = result.mappings().all()
    return [_row_to_dict(r) for r in rows]
