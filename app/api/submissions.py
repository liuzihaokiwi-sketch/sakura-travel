"""
Quiz Submissions API — 问卷提交的 CRUD 端点。

前端 quiz 页面提交 → POST /submissions
管理后台读取列表 → GET /submissions
管理后台更新状态 → PATCH /submissions/{id}
"""
from __future__ import annotations

import logging
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/submissions", tags=["submissions"])


_DESTINATION_CITY_MAP: dict[str, list[str]] = {
    "tokyo": ["tokyo"],
    "osaka-kyoto": ["osaka", "kyoto"],
    "tokyo-osaka-kyoto": ["tokyo", "osaka", "kyoto"],
    "hokkaido": ["sapporo"],
    "okinawa": ["naha"],
    "kansai": ["osaka", "kyoto", "nara", "kobe"],
    "kanto": ["tokyo", "yokohama", "kamakura"],
    "south_china_five_city": ["guangzhou", "shenzhen", "foshan", "zhuhai", "dongguan"],
    "northern_xinjiang": ["urumqi", "yining", "kuitun"],
    "guangdong": ["guangzhou", "shenzhen", "foshan", "zhuhai"],
}

_CITY_ALIAS_MAP: dict[str, str] = {
    "\u4e1c\u4eac": "tokyo",
    "\u5927\u962a": "osaka",
    "\u4eac\u90fd": "kyoto",
    "\u5948\u826f": "nara",
    "\u795e\u6237": "kobe",
    "\u672d\u5e4c": "sapporo",
    "\u51b2\u7ef3": "naha",
    "\u90a3\u9738": "naha",
    "\u6a2a\u6ee8": "yokohama",
    "\u9570\u4ed3": "kamakura",
    "\u4e4c\u9c81\u6728\u9f50": "urumqi",
    "\u4f0a\u5b81": "yining",
    "\u594e\u5c6f": "kuitun",
    "\u5e7f\u5dde": "guangzhou",
    "\u6df1\u5733": "shenzhen",
    "\u4f5b\u5c71": "foshan",
    "\u73e0\u6d77": "zhuhai",
    "\u4e1c\u839e": "dongguan",
}


def _normalize_party_type(raw: Optional[str]) -> str:
    mapping = {
        "family_with_kids": "family_child",
        "family_no_kids": "family_no_child",
        "family": "family_child",
        "friends": "group",
        "besties": "group",
        "parents": "senior",
        "business": "group",
    }
    party = (raw or "couple").strip().lower()
    return mapping.get(party, party or "couple")


def _normalize_pace(raw: Optional[str]) -> str:
    mapping = {
        "balanced": "moderate",
        "intensive": "packed",
        "light": "relaxed",
        "dense": "packed",
    }
    pace = (raw or "moderate").strip().lower()
    return mapping.get(pace, pace or "moderate")


def _normalize_wake_up_time(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    val = str(raw).strip().lower()
    if val in {"early", "normal", "late"}:
        return val
    if ":" in val:
        try:
            hour = int(val.split(":", 1)[0])
        except ValueError:
            return None
        if hour <= 6:
            return "early"
        if hour <= 9:
            return "normal"
        return "late"
    return None


def _extract_city_code(city: dict[str, Any]) -> str:
    for key in ("city_code", "place_id", "code"):
        val = city.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip().lower()

    for key in ("name_zh", "city_name", "name"):
        val = city.get(key)
        if isinstance(val, str) and val.strip():
            text = val.strip()
            if text in _CITY_ALIAS_MAP:
                return _CITY_ALIAS_MAP[text]
            return text.lower().replace(" ", "_")
    return ""


def _normalize_cities(
    raw_cities: Optional[list[Any]],
    destination: str,
    duration_days: int,
) -> list[dict[str, Any]]:
    cities: list[dict[str, Any]] = []
    if isinstance(raw_cities, list):
        for c in raw_cities:
            if not isinstance(c, dict):
                continue
            code = _extract_city_code(c)
            if not code:
                continue
            nights_raw = c.get("nights")
            try:
                nights = int(nights_raw) if nights_raw is not None else 0
            except (TypeError, ValueError):
                nights = 0
            if nights <= 0:
                nights = 1
            cities.append({"city_code": code, "nights": nights})

    if cities:
        return cities

    fallback_codes = _DESTINATION_CITY_MAP.get(destination, ["tokyo"])
    per_city_days = max(1, duration_days // max(1, len(fallback_codes)))
    return [{"city_code": code, "nights": per_city_days} for code in fallback_codes]


def _build_raw_input(
    submission_id: str,
    sub: dict[str, Any],
    form: Any | None,
) -> dict[str, Any]:
    destination = (sub.get("destination") or "").strip().lower()
    duration = int(sub.get("duration_days") or 5)
    party = _normalize_party_type(sub.get("party_type") or "couple")
    styles = sub.get("styles") or []

    if not form:
        return {
            "submission_id": submission_id,
            "destination": destination,
            "duration_days": duration,
            "party_type": party,
            "party_size": sub.get("people_count") or 2,
            "styles": styles,
            "budget_focus": sub.get("budget_focus"),
        }

    special_needs = getattr(form, "special_needs", None)
    if isinstance(special_needs, str) and special_needs.strip():
        special_needs = {"notes": special_needs.strip()}
    elif not isinstance(special_needs, dict):
        special_needs = {}

    budget_total_cny = getattr(form, "budget_total_cny", None)

    return {
        "submission_id": submission_id,
        "destination": destination,
        "cities": _normalize_cities(getattr(form, "cities", None), destination, duration),
        "duration_days": int(getattr(form, "duration_days", None) or duration),
        "travel_start_date": getattr(form, "travel_start_date", None),
        "travel_end_date": getattr(form, "travel_end_date", None),
        "date_flexible": bool(getattr(form, "date_flexible", False)),
        "party_type": _normalize_party_type(getattr(form, "party_type", None) or party),
        "party_size": getattr(form, "party_size", None) or sub.get("people_count") or 2,
        "has_elderly": bool(getattr(form, "has_elderly", False)),
        "has_children": bool(getattr(form, "has_children", False)),
        "children_ages": getattr(form, "children_ages", None) or [],
        "special_needs": special_needs,
        "budget_level": getattr(form, "budget_level", None) or "mid",
        "budget_total_cny": int(budget_total_cny) if budget_total_cny else None,
        "budget_focus": getattr(form, "budget_focus", None) or sub.get("budget_focus"),
        "accommodation_pref": getattr(form, "accommodation_pref", None) or {},
        "must_have_tags": getattr(form, "must_have_tags", None) or [],
        "nice_to_have_tags": getattr(form, "nice_to_have_tags", None) or [],
        "avoid_tags": getattr(form, "avoid_tags", None) or [],
        "food_preferences": getattr(form, "food_preferences", None) or {},
        "pace": _normalize_pace(getattr(form, "pace", None)),
        "wake_up_time": _normalize_wake_up_time(getattr(form, "wake_up_time", None)),
        "must_visit_places": getattr(form, "must_visit_places", None) or [],
        "free_text_wishes": getattr(form, "free_text_wishes", None) or "",
        "flight_info": getattr(form, "flight_info", None) or {},
        "arrival_airport": getattr(form, "arrival_airport", None) or "",
        "departure_airport": getattr(form, "departure_airport", None) or "",
        "has_jr_pass": bool(getattr(form, "has_jr_pass", False)),
        "transport_pref": getattr(form, "transport_pref", None) or {},
        "styles": styles,
    }


def _legacy_template_and_scene(raw_input: dict[str, Any]) -> tuple[str, str]:
    cities = raw_input.get("cities") or []
    first_city = ""
    if isinstance(cities, list) and cities and isinstance(cities[0], dict):
        first_city = (cities[0].get("city_code") or "").lower()
    days = int(raw_input.get("duration_days") or 5)

    base_code = "kansai_classic" if first_city in {"osaka", "kyoto", "nara", "kobe", "uji"} else "tokyo_classic"
    template_code = f"{base_code}_{days}d"

    party = _normalize_party_type(raw_input.get("party_type"))
    scene_map = {
        "couple": "couple",
        "solo": "solo",
        "family_child": "family",
        "family_no_child": "family",
        "group": "solo",
        "senior": "senior",
    }
    scene = scene_map.get(party, "couple")
    return template_code, scene


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

    1. 构建统一 raw_input
    2. upsert trip_requests（按 submission_id 幂等）
    3. 先执行 normalize_trip_profile
    4. 触发 generate_trip（城市圈优先，旧模板 fallback）
    5. 更新 quiz_submission 状态为 generating
    """
    import asyncio
    import uuid as _uuid

    from app.core.queue import enqueue_job
    from app.db.models.business import TripRequest
    from app.db.models.detail_forms import DetailForm
    from sqlalchemy import select

    sub_res = await db.execute(
        text("SELECT * FROM quiz_submissions WHERE id = :id"),
        {"id": submission_id},
    )
    sub = sub_res.mappings().first()
    if not sub:
        raise HTTPException(status_code=404, detail="提交记录不存在")

    form_res = await db.execute(
        select(DetailForm).where(DetailForm.submission_id == submission_id)
    )
    form = form_res.scalar_one_or_none()
    raw_input = _build_raw_input(submission_id, sub, form)

    existing_tr = await db.execute(
        text("SELECT trip_request_id FROM trip_requests WHERE raw_input->>'submission_id' = :sid"),
        {"sid": submission_id},
    )
    existing_row = existing_tr.fetchone()

    if existing_row:
        tr_id = existing_row[0]
        await db.execute(
            text(
                "UPDATE trip_requests "
                "SET raw_input = :raw_input, status = 'new', updated_at = NOW() "
                "WHERE trip_request_id = :id"
            ),
            {"id": str(tr_id), "raw_input": raw_input},
        )
        await db.commit()
    else:
        tr_id = _uuid.uuid4()
        new_tr = TripRequest(
            trip_request_id=tr_id,
            raw_input=raw_input,
            status="new",
        )
        db.add(new_tr)
        await db.commit()
        await db.refresh(new_tr)

    template_code, scene = _legacy_template_and_scene(raw_input)

    await db.execute(
        text("UPDATE trip_requests SET status='normalizing', updated_at=NOW() WHERE trip_request_id = :id"),
        {"id": str(tr_id)},
    )
    await db.execute(
        text("UPDATE quiz_submissions SET status='generating', updated_at=NOW() WHERE id = :id"),
        {"id": submission_id},
    )
    await db.commit()

    from app.workers.__main__ import normalize_trip_profile
    await normalize_trip_profile({}, str(tr_id))

    queued = None
    try:
        queued = await enqueue_job(
            "generate_trip",
            trip_request_id=str(tr_id),
            template_code=template_code,
            scene=scene,
        )
    except Exception:
        queued = None

    if not queued:
        from app.workers.jobs.generate_trip import generate_trip as _generate_trip_job

        async def _run_inline() -> None:
            try:
                await _generate_trip_job(
                    {},
                    trip_request_id=str(tr_id),
                    template_code=template_code,
                    scene=scene,
                )
            except Exception as _exc:
                import logging as _log
                _log.getLogger(__name__).exception("generate_from_submission fallback failed: %s", _exc)

        asyncio.ensure_future(_run_inline())

    return {
        "ok": True,
        "submission_id": submission_id,
        "trip_request_id": str(tr_id),
        "template_code": template_code,
        "scene": scene,
        "job_queued": bool(queued),
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
