"""
Trip V2 API — 新表单流程：4屏轻表单 → 方案确认 → 预算确认。

流程：
  POST /v2/trips          → 创建 + 触发预览生成
  GET  /v2/trips/{id}/plan-preview   → 获取预览方案
  POST /v2/trips/{id}/plan-actions   → 纠偏（action-based）
  POST /v2/trips/{id}/plan-confirm   → 确认方案
  GET  /v2/trips/{id}/budget-options → 获取预算选项
  POST /v2/trips/{id}/budget-confirm → 确认预算 → 触发最终生成
  GET  /v2/trips/{id}/status         → 状态查询
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queue import enqueue_job
from app.db.models.business import TripProfile, TripRequest, TripVersion
from app.db.session import get_db

router = APIRouter()


# ── Pydantic Schemas ──────────────────────────────────────────────────────────


class PreBookedItem(BaseModel):
    type: str = Field(..., examples=["hotel", "ticket", "restaurant", "transport"])
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    location: Optional[str] = None
    name: Optional[str] = None
    fixed: bool = True


class TripCreateV2Request(BaseModel):
    """POST /v2/trips 请求体 — 4屏表单数据"""

    # 屏1: 日期
    travel_start_date: str = Field(
        ..., pattern=r"^\d{4}-\d{2}-\d{2}$", examples=["2026-04-03"]
    )
    travel_end_date: str = Field(
        ..., pattern=r"^\d{4}-\d{2}-\d{2}$", examples=["2026-04-09"]
    )
    arrival_slot: str = Field("afternoon", examples=["morning", "afternoon", "evening"])
    departure_slot: str = Field("morning", examples=["morning", "afternoon", "evening"])

    # 屏2: 风格 + 人数
    trip_vibe: str = Field("classic", examples=["classic", "romantic", "photogenic", "family_fun"])
    adults: int = Field(2, ge=1, le=10)
    children: int = Field(0, ge=0, le=10)
    elders: int = Field(0, ge=0, le=10)

    # 屏3: 节奏
    density: str = Field("balanced", examples=["packed", "balanced", "relaxed"])

    # 屏4: 特殊情况（可选）
    pre_booked: list[PreBookedItem] = Field(default_factory=list)
    skip_entities: list[str] = Field(default_factory=list)
    skip_tags: list[str] = Field(default_factory=list)
    special_notes: Optional[str] = None


class TripCreateV2Response(BaseModel):
    trip_request_id: str
    status: str
    message: str


class DayPreview(BaseModel):
    day: int
    city: str
    title: str
    description: str


class ExperienceCard(BaseModel):
    id: str
    icon: str
    label: str
    description: str


class PlanPreviewResponse(BaseModel):
    trip_request_id: str
    plan_version: int
    status: str
    condition_summary: str
    decisions: list[str]
    daily_plans: list[DayPreview]
    addable_experiences: list[ExperienceCard]
    note: str


class PlanAction(BaseModel):
    op: str = Field(
        ...,
        examples=[
            "add_experience", "remove_experience",
            "set_density", "avoid_tag", "adjust_city", "free_text",
        ],
    )
    params: dict[str, Any] = Field(default_factory=dict)


class PlanActionRequest(BaseModel):
    actions: list[PlanAction]


class PlanConfirmRequest(BaseModel):
    confirmed: bool = True


class TierOption(BaseModel):
    id: str
    label: str
    price_range: str
    description: str


class BudgetEstimate(BaseModel):
    dining_total: int
    hotel_total: int
    transport: int
    tickets: int
    addons: int
    total_per_person: int
    currency: str = "CNY"


class BudgetOptionsResponse(BaseModel):
    dining_tiers: list[TierOption]
    hotel_tiers: list[TierOption]
    dining_preferences: list[dict[str, str]]
    hotel_preferences: list[dict[str, str]]
    comfort_addons: list[dict[str, Any]]
    default_estimate: BudgetEstimate


class BudgetConfirmRequest(BaseModel):
    dining_tier: str = Field(..., examples=["street", "local_good", "fine", "top"])
    dining_preference: Optional[str] = Field(None, examples=["taste_first", "comfort_first"])
    hotel_tier: str = Field(..., examples=["budget", "comfort", "premium", "luxury"])
    hotel_preferences: list[str] = Field(default_factory=list)
    comfort_addons: dict[str, bool] = Field(default_factory=dict)


class TripStatusV2Response(BaseModel):
    trip_request_id: str
    status: str
    plan_version: Optional[int] = None
    error_summary: Optional[str] = None


# ── Helper ───────────────────────────────────────────────────────────────────


async def _get_trip_or_404(trip_id: str, db: AsyncSession) -> TripRequest:
    trip = await db.get(TripRequest, uuid.UUID(trip_id))
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


async def _get_profile_or_404(trip_id: str, db: AsyncSession) -> TripProfile:
    result = await db.execute(
        select(TripProfile).where(
            TripProfile.trip_request_id == uuid.UUID(trip_id)
        )
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Trip profile not found")
    return profile


def _build_trip_constraints(body: TripCreateV2Request) -> dict[str, Any]:
    """从表单数据构建 trip_constraints 对象。"""
    return {
        "circle": "kansai",
        "version": "v2",
        "dates": {
            "start": body.travel_start_date,
            "end": body.travel_end_date,
            "arrival_slot": body.arrival_slot,
            "departure_slot": body.departure_slot,
        },
        "vibe": body.trip_vibe,
        "density": body.density,
        "party": {
            "adults": body.adults,
            "children": body.children,
            "elderly": body.elders,
        },
        "pre_booked": [item.model_dump() for item in body.pre_booked],
        "skip_entities": body.skip_entities,
        "skip_tags": body.skip_tags,
        "notes": body.special_notes or "",
    }


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=TripCreateV2Response)
async def create_trip_v2(
    body: TripCreateV2Request,
    db: AsyncSession = Depends(get_db),
) -> TripCreateV2Response:
    """
    创建行程请求（v2 新表单）。
    接收4屏表单数据，构建 trip_constraints，触发预览方案异步生成。
    """
    constraints = _build_trip_constraints(body)

    trip = TripRequest(
        raw_input=constraints,
        status="plan_generating",
    )
    db.add(trip)
    await db.flush()

    # 入队预览方案生成 job
    await enqueue_job("generate_plan_preview", str(trip.trip_request_id))

    return TripCreateV2Response(
        trip_request_id=str(trip.trip_request_id),
        status="plan_generating",
        message="方案生成中，请轮询 GET /v2/trips/{id}/status",
    )


@router.get("/{trip_id}/status", response_model=TripStatusV2Response)
async def get_trip_status_v2(
    trip_id: str,
    db: AsyncSession = Depends(get_db),
) -> TripStatusV2Response:
    """状态查询（轮询用）。"""
    trip = await _get_trip_or_404(trip_id, db)
    profile = await db.execute(
        select(TripProfile).where(
            TripProfile.trip_request_id == trip.trip_request_id
        )
    )
    p = profile.scalar_one_or_none()

    return TripStatusV2Response(
        trip_request_id=str(trip.trip_request_id),
        status=trip.status,
        plan_version=p.current_plan_version if p else None,
        error_summary=trip.last_job_error if "failed" in (trip.status or "") else None,
    )


@router.get("/{trip_id}/plan-preview", response_model=PlanPreviewResponse)
async def get_plan_preview(
    trip_id: str,
    db: AsyncSession = Depends(get_db),
) -> PlanPreviewResponse:
    """
    获取预览方案。
    前提：状态必须是 plan_preview 或 plan_confirmed。
    """
    trip = await _get_trip_or_404(trip_id, db)

    if trip.status not in ("plan_preview", "plan_confirmed"):
        raise HTTPException(
            status_code=409,
            detail=f"Plan not ready. Current status: {trip.status}",
        )

    # plan_version 存在 TripVersion 表
    version_result = await db.execute(
        select(TripVersion)
        .where(TripVersion.trip_request_id == trip.trip_request_id)
        .order_by(TripVersion.version_number.desc())
        .limit(1)
    )
    version = version_result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="No plan version found")

    # plan 数据从 TripVersion 或 TripRequest.raw_input 中提取
    # TODO: TemplatePlanner 生成的 plan_version 数据存在哪里需要定义
    # 暂时从 raw_input 的 plan_preview 字段读
    plan_data = trip.raw_input.get("plan_preview", {})

    return PlanPreviewResponse(
        trip_request_id=str(trip.trip_request_id),
        plan_version=version.version_number,
        status=trip.status,
        condition_summary=plan_data.get("condition_summary", ""),
        decisions=plan_data.get("decisions", []),
        daily_plans=[DayPreview(**d) for d in plan_data.get("daily_plans", [])],
        addable_experiences=[
            ExperienceCard(**e) for e in plan_data.get("addable_experiences", [])
        ],
        note=plan_data.get("note", ""),
    )


@router.post("/{trip_id}/plan-actions", response_model=PlanPreviewResponse)
async def apply_plan_actions(
    trip_id: str,
    body: PlanActionRequest,
    db: AsyncSession = Depends(get_db),
) -> PlanPreviewResponse:
    """
    纠偏：提交 action 列表，系统重新生成方案。
    返回新版 PlanPreviewResponse。
    """
    trip = await _get_trip_or_404(trip_id, db)

    if trip.status not in ("plan_preview",):
        raise HTTPException(
            status_code=409,
            detail=f"Plan actions only available in plan_preview state. Current: {trip.status}",
        )

    # 记录 actions 到 raw_input
    constraints = dict(trip.raw_input)
    action_log = constraints.get("action_history", [])
    action_log.append({
        "actions": [a.model_dump() for a in body.actions],
        "applied_at": datetime.utcnow().isoformat(),
    })
    constraints["action_history"] = action_log

    # TODO: 将 actions 应用到 trip_constraints（由 TemplatePlanner 处理）
    # 暂时直接存储，后续 TemplatePlanner 实现后补齐
    trip.raw_input = constraints
    trip.status = "plan_generating"
    await db.flush()

    # 重新生成预览
    await enqueue_job("generate_plan_preview", str(trip.trip_request_id))

    # 返回需要等待，实际应该 202，前端轮询
    # 这里先简化返回当前状态
    raise HTTPException(
        status_code=202,
        detail="Plan regenerating. Poll GET /v2/trips/{id}/status",
    )


@router.post("/{trip_id}/plan-confirm")
async def confirm_plan(
    trip_id: str,
    body: PlanConfirmRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """确认方案。锁定当前 plan_version。"""
    trip = await _get_trip_or_404(trip_id, db)

    if trip.status != "plan_preview":
        raise HTTPException(
            status_code=409,
            detail=f"Can only confirm in plan_preview state. Current: {trip.status}",
        )

    if not body.confirmed:
        return {"status": "not_confirmed"}

    trip.status = "plan_confirmed"

    # 更新 profile 的确认时间
    profile = await _get_profile_or_404(trip_id, db)
    profile.plan_confirmed_at = datetime.utcnow()

    return {"status": "plan_confirmed", "trip_request_id": str(trip.trip_request_id)}


@router.get("/{trip_id}/budget-options", response_model=BudgetOptionsResponse)
async def get_budget_options(
    trip_id: str,
    db: AsyncSession = Depends(get_db),
) -> BudgetOptionsResponse:
    """
    获取预算选项页数据。
    前提：方案已确认（plan_confirmed）。
    """
    trip = await _get_trip_or_404(trip_id, db)

    if trip.status not in ("plan_confirmed", "budget_confirmed"):
        raise HTTPException(
            status_code=409,
            detail=f"Budget options only available after plan confirmed. Current: {trip.status}",
        )

    # TODO: BudgetCalculator 根据方案计算费用预估
    # 暂时返回固定选项
    return BudgetOptionsResponse(
        dining_tiers=[
            TierOption(id="street", label="街头地道", price_range="￥40-60/顿", description="拉面·定食·乌冬·咖喱"),
            TierOption(id="local_good", label="本地好店", price_range="￥80-150/顿", description="居酒屋·名物老店·特色料理"),
            TierOption(id="fine", label="好好享受", price_range="￥200-350/顿", description="割烹·寿司吧台·铁板烧"),
            TierOption(id="top", label="顶级体验", price_range="￥500+/顿", description="怀石·omakase·米其林"),
        ],
        hotel_tiers=[
            TierOption(id="budget", label="干净方便", price_range="￥250-450/晚", description="商务酒店·交通便利"),
            TierOption(id="comfort", label="品质舒适", price_range="￥500-900/晚", description="品质酒店·可能有大浴场"),
            TierOption(id="premium", label="享受型", price_range="￥1,000-1,800/晚", description="温泉·景观·设计感"),
            TierOption(id="luxury", label="顶级", price_range="￥2,000+/晚", description="顶奢酒店·高端旅馆"),
        ],
        dining_preferences=[
            {"id": "taste_first", "label": "味道好最重要 — 哪怕环境一般、要排队也值得"},
            {"id": "comfort_first", "label": "体验舒服最重要 — 不排队、环境好、吃得从容"},
        ],
        hotel_preferences=[
            {"id": "stable", "label": "住得稳 — 干净、服务好、品牌靠谱不踩雷"},
            {"id": "experience", "label": "住出体验 — 温泉、景观、设计感"},
            {"id": "convenient", "label": "住得方便 — 车站近、位置好、搬行李不折腾"},
        ],
        comfort_addons=[
            {"id": "luggage_delivery", "label": "行李寄送", "price_range": "￥100-150/次", "description": "换城市不用拖行李"},
            {"id": "occasional_taxi", "label": "偶尔打车", "price_range": "￥300-500/全程", "description": "远离地铁或晚归时打车"},
        ],
        default_estimate=BudgetEstimate(
            dining_total=0, hotel_total=0, transport=0,
            tickets=0, addons=0, total_per_person=0,
        ),
    )


@router.post("/{trip_id}/budget-confirm")
async def confirm_budget(
    trip_id: str,
    body: BudgetConfirmRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    确认预算选择。
    状态改为 budget_confirmed → 自动触发最终手账本生成。
    """
    trip = await _get_trip_or_404(trip_id, db)

    if trip.status != "plan_confirmed":
        raise HTTPException(
            status_code=409,
            detail=f"Can only confirm budget in plan_confirmed state. Current: {trip.status}",
        )

    # 更新 profile
    profile = await _get_profile_or_404(trip_id, db)
    profile.dining_tier = body.dining_tier
    profile.dining_preference = body.dining_preference
    profile.hotel_tier = body.hotel_tier
    profile.hotel_preferences = body.hotel_preferences
    profile.comfort_addons = body.comfort_addons
    profile.budget_confirmed_at = datetime.utcnow()

    # 存 budget_profile 到 raw_input
    constraints = dict(trip.raw_input)
    constraints["budget_profile"] = body.model_dump()
    trip.raw_input = constraints
    trip.status = "budget_confirmed"

    await db.flush()

    # 触发最终手账本生成
    await enqueue_job("generate_handbook_final", str(trip.trip_request_id))

    return {
        "status": "budget_confirmed",
        "trip_request_id": str(trip.trip_request_id),
        "message": "预算已确认，开始生成你的专属手账本",
    }
