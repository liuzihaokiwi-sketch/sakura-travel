"""
Detail Forms API — 付费后详细表单 CRUD 端点 (M1)

端点：
  POST   /detail-forms/{submission_id}   创建表单（付费后触发）
  GET    /detail-forms/{form_id}         获取表单完整数据
  PATCH  /detail-forms/{form_id}         更新表单字段（支持部分更新）
  POST   /detail-forms/{form_id}/steps/{step_number}  保存单步数据
  GET    /detail-forms/{form_id}/steps   获取所有步骤状态
  POST   /detail-forms/{form_id}/submit  提交表单（标记 is_complete=True）
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.detail_forms import DetailForm, DetailFormStep
from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/detail-forms", tags=["detail-forms"])


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class DetailFormCreate(BaseModel):
    """创建详细表单（付费后由后端触发，或前端调用）"""
    submission_id: str = Field(..., description="quiz_submissions.id")
    order_id: Optional[UUID] = None


class DetailFormPatch(BaseModel):
    """部分更新表单字段（前端每步保存调用）"""
    # Step 1 — 目的地与日期
    cities: Optional[list[dict]] = None
    travel_start_date: Optional[str] = None
    travel_end_date: Optional[str] = None
    duration_days: Optional[int] = None
    date_flexible: Optional[bool] = None

    # Step 2 — 同行人信息
    party_type: Optional[str] = None
    party_size: Optional[int] = None
    party_ages: Optional[list[int]] = None
    has_elderly: Optional[bool] = None
    has_children: Optional[bool] = None
    children_ages: Optional[list[int]] = None
    special_needs: Optional[str] = None

    # Step 3 — 预算与住宿（匹配 ORM: JSONB dict）
    budget_level: Optional[str] = None
    budget_total_cny: Optional[int] = None
    budget_focus: Optional[str] = None
    accommodation_pref: Optional[dict] = None

    # Step 4 — 兴趣偏好（匹配 ORM: JSONB list/dict）
    must_have_tags: Optional[list[str]] = None
    nice_to_have_tags: Optional[list[str]] = None
    avoid_tags: Optional[list[str]] = None
    food_preferences: Optional[dict] = None
    theme_family: Optional[str] = None

    # Step 5 — 行程节奏（匹配 ORM 字段名）
    pace: Optional[str] = None
    wake_up_time: Optional[str] = None
    must_visit_places: Optional[list[str]] = None
    free_text_wishes: Optional[str] = None

    # Step 6 — 航班与交通（匹配 ORM: JSONB dict）
    flight_info: Optional[dict] = None
    arrival_airport: Optional[str] = None
    departure_airport: Optional[str] = None
    has_jr_pass: Optional[bool] = None
    transport_pref: Optional[dict] = None

    # 当前步骤（用于进度追踪）
    current_step: Optional[int] = None

    model_config = {"extra": "ignore"}


class StepSave(BaseModel):
    """单步数据保存"""
    step_data: dict[str, Any] = Field(..., description="该步骤的完整数据")
    is_complete: bool = False


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _get_form_or_404(
    form_id: UUID, db: AsyncSession
) -> DetailForm:
    result = await db.execute(
        select(DetailForm).where(DetailForm.form_id == form_id)
    )
    form = result.scalar_one_or_none()
    if not form:
        raise HTTPException(status_code=404, detail=f"DetailForm {form_id} not found")
    return form


def _form_to_dict(form: DetailForm) -> dict:
    """将 ORM 对象序列化为 API 响应 — 字段严格匹配 ORM 模型"""
    return {
        "form_id": str(form.form_id),
        "submission_id": form.submission_id,
        "order_id": str(form.order_id) if form.order_id else None,
        "current_step": form.current_step,
        "is_complete": form.is_complete,
        # Step 1: 目的地与日期
        "cities": form.cities,
        "travel_start_date": form.travel_start_date,
        "travel_end_date": form.travel_end_date,
        "duration_days": form.duration_days,
        "date_flexible": form.date_flexible,
        # Step 2: 同行人信息
        "party_type": form.party_type,
        "party_size": form.party_size,
        "party_ages": form.party_ages,
        "has_elderly": form.has_elderly,
        "has_children": form.has_children,
        "children_ages": form.children_ages,
        "special_needs": form.special_needs,
        # Step 3: 预算与住宿
        "budget_level": form.budget_level,
        "budget_total_cny": form.budget_total_cny,
        "budget_focus": form.budget_focus,
        "accommodation_pref": form.accommodation_pref,
        # Step 4: 兴趣偏好
        "must_have_tags": form.must_have_tags,
        "nice_to_have_tags": form.nice_to_have_tags,
        "avoid_tags": form.avoid_tags,
        "food_preferences": form.food_preferences,
        "theme_family": form.theme_family,
        # Step 5: 行程节奏
        "pace": form.pace,
        "wake_up_time": form.wake_up_time,
        "must_visit_places": form.must_visit_places,
        "free_text_wishes": form.free_text_wishes,
        # Step 6: 航班与交通
        "flight_info": form.flight_info,
        "arrival_airport": form.arrival_airport,
        "departure_airport": form.departure_airport,
        "has_jr_pass": form.has_jr_pass,
        "transport_pref": form.transport_pref,
        # 时间戳
        "created_at": form.created_at.isoformat(),
        "updated_at": form.updated_at.isoformat(),
        "completed_at": form.completed_at.isoformat() if form.completed_at else None,
    }


# ── 端点 ─────────────────────────────────────────────────────────────────────

@router.post("/{submission_id}", status_code=status.HTTP_201_CREATED)
async def create_detail_form(
    submission_id: str,
    body: DetailFormCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    创建详细表单。
    付费成功后由 webhook 或管理员手动触发，也可由前端在付款确认页调用。
    同一 submission_id 只允许一个表单（unique 约束）。
    """
    # 检查是否已存在——如果有就返回现有的（幂等）
    existing = await db.execute(
        select(DetailForm).where(DetailForm.submission_id == submission_id)
    )
    existing_form = existing.scalar_one_or_none()
    if existing_form:
        return _form_to_dict(existing_form)

    form = DetailForm(
        form_id=uuid4(),
        submission_id=submission_id,
        order_id=body.order_id,
        current_step=1,
        is_complete=False,
    )
    db.add(form)
    await db.commit()
    await db.refresh(form)

    logger.info("DetailForm created: form_id=%s submission_id=%s", form.form_id, submission_id)
    return _form_to_dict(form)


@router.get("/{form_id}")
async def get_detail_form(
    form_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """获取表单完整数据。"""
    form = await _get_form_or_404(form_id, db)
    return _form_to_dict(form)


@router.get("/by-submission/{submission_id}")
async def get_form_by_submission(
    submission_id: str,
    db: AsyncSession = Depends(get_db),
):
    """通过 submission_id 获取表单（前端场景）。"""
    result = await db.execute(
        select(DetailForm).where(DetailForm.submission_id == submission_id)
    )
    form = result.scalar_one_or_none()
    if not form:
        raise HTTPException(status_code=404, detail=f"No form for submission {submission_id}")
    return _form_to_dict(form)


@router.patch("/{form_id}")
async def patch_detail_form(
    form_id: UUID,
    body: DetailFormPatch,
    db: AsyncSession = Depends(get_db),
):
    """
    部分更新表单字段（前端每步自动保存时调用）。
    只更新 body 中非 None 的字段，不强制整体替换。
    """
    form = await _get_form_or_404(form_id, db)

    patch_data = body.model_dump(exclude_none=True)
    if not patch_data:
        return _form_to_dict(form)

    for field_name, value in patch_data.items():
        if hasattr(form, field_name):
            setattr(form, field_name, value)

    form.updated_at = datetime.now(tz=timezone.utc)

    # 自动更新 current_step（取已有值和新值的最大值）
    if body.current_step and body.current_step > form.current_step:
        form.current_step = body.current_step

    await db.commit()
    await db.refresh(form)
    logger.info("DetailForm patched: form_id=%s fields=%s", form_id, list(patch_data.keys()))
    return _form_to_dict(form)


@router.post("/{form_id}/steps/{step_number}")
async def save_step(
    form_id: UUID,
    step_number: int,
    body: StepSave,
    db: AsyncSession = Depends(get_db),
):
    """
    保存单步数据快照到 detail_form_steps。
    同时同步到主表对应字段（双写保证一致性）。
    """
    if not (1 <= step_number <= 6):
        raise HTTPException(status_code=400, detail="step_number 必须在 1-6 之间")

    form = await _get_form_or_404(form_id, db)

    # upsert step 记录
    existing_step = await db.execute(
        select(DetailFormStep).where(
            DetailFormStep.form_id == form_id,
            DetailFormStep.step_number == step_number,
        )
    )
    step_obj = existing_step.scalar_one_or_none()
    now = datetime.now(tz=timezone.utc)

    if step_obj:
        step_obj.step_data = body.step_data
        step_obj.is_complete = body.is_complete
        step_obj.updated_at = now
        if body.is_complete and not step_obj.completed_at:
            step_obj.completed_at = now
    else:
        step_obj = DetailFormStep(
            form_id=form_id,
            step_number=step_number,
            step_data=body.step_data,
            is_complete=body.is_complete,
            completed_at=now if body.is_complete else None,
        )
        db.add(step_obj)

    # 更新主表 current_step
    if step_number > form.current_step:
        form.current_step = step_number
    form.updated_at = now

    await db.commit()
    return {
        "form_id": str(form_id),
        "step_number": step_number,
        "is_complete": body.is_complete,
        "current_step": form.current_step,
    }


@router.get("/{form_id}/steps")
async def get_steps(
    form_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """获取表单所有步骤的完成状态。"""
    await _get_form_or_404(form_id, db)

    result = await db.execute(
        select(DetailFormStep)
        .where(DetailFormStep.form_id == form_id)
        .order_by(DetailFormStep.step_number)
    )
    steps = result.scalars().all()

    # 构建 1-6 步的状态图
    step_map = {s.step_number: s for s in steps}
    return {
        "form_id": str(form_id),
        "steps": [
            {
                "step_number": i,
                "is_complete": step_map[i].is_complete if i in step_map else False,
                "completed_at": (
                    step_map[i].completed_at.isoformat()
                    if i in step_map and step_map[i].completed_at else None
                ),
                "has_data": i in step_map,
            }
            for i in range(1, 7)
        ],
    }


@router.post("/{form_id}/submit")
async def submit_detail_form(
    form_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    提交表单（用户点击「提交」按钮时调用）。
    标记 is_complete=True，记录 submitted_at。
    不做校验（校验由 POST /validate/{form_id} 完成）。
    """
    form = await _get_form_or_404(form_id, db)

    # 允许反复提交——每次提交都更新 completed_at
    now = datetime.now(tz=timezone.utc)
    form.is_complete = True
    form.completed_at = now
    form.updated_at = now

    await db.commit()
    logger.info("DetailForm submitted: form_id=%s", form_id)

    return {
        "form_id": str(form_id),
        "submitted": True,
        "submitted_at": now.isoformat(),
        "next": f"/validate/{form_id}",
    }


@router.post("/{form_id}/validate")
async def validate_detail_form(
    form_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    红黄绿校验端点（M5 管理后台调用）。
    读取表单的 merged_data，通过 ValidationEngine 逐条检查规则，
    返回结构化的红黄绿结果。
    """
    from app.domains.validation.engine import ValidationEngine

    form = await _get_form_or_404(form_id, db)

    # 合并各步骤数据为完整的 form_data 字典
    form_data: dict = {}
    if form.cities:           form_data["cities"] = form.cities
    if form.travel_start_date: form_data["travel_start_date"] = form.travel_start_date
    if form.travel_end_date:   form_data["travel_end_date"] = form.travel_end_date
    if form.duration_days:     form_data["duration_days"] = form.duration_days
    if form.date_flexible is not None: form_data["date_flexible"] = form.date_flexible
    if form.party_type:        form_data["party_type"] = form.party_type
    if form.party_size:        form_data["party_size"] = form.party_size
    if form.party_ages:        form_data["party_ages"] = form.party_ages
    if form.budget_level:      form_data["budget_level"] = form.budget_level
    if form.budget_total_cny:  form_data["budget_total_cny"] = form.budget_total_cny
    if form.accommodation_pref: form_data["accommodation_pref"] = form.accommodation_pref
    if form.must_have_tags:    form_data["must_have_tags"] = form.must_have_tags
    if form.nice_to_have_tags: form_data["nice_to_have_tags"] = form.nice_to_have_tags
    if form.avoid_tags:        form_data["avoid_tags"] = form.avoid_tags
    if form.food_preferences:  form_data["food_preferences"] = form.food_preferences
    if form.pace_preference:   form_data["pace_preference"] = form.pace_preference
    if form.arrival_date:      form_data["arrival_date"] = form.arrival_date
    if form.arrival_time:      form_data["arrival_time"] = form.arrival_time
    if form.arrival_place:     form_data["arrival_place"] = form.arrival_place
    if form.departure_date:    form_data["departure_date"] = form.departure_date
    if form.departure_time:    form_data["departure_time"] = form.departure_time
    if form.departure_place:   form_data["departure_place"] = form.departure_place
    if form.free_text_wishes:  form_data["free_text_wishes"] = form.free_text_wishes

    engine = ValidationEngine()
    result = engine.validate(form_data, form_id=str(form_id))

    # 缓存校验结果到表单（如果模型有该字段）
    try:
        if hasattr(form, "validation_result"):
            form.validation_result = result.to_dict()
            form.updated_at = datetime.now(tz=timezone.utc)
            await db.commit()
    except Exception:
        pass

    return result.to_dict()
