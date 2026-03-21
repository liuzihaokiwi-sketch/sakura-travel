from __future__ import annotations

"""
对话式旅行规划 API
  POST /chat/start      → 用户发送第一条消息，AI 解析意图
  POST /chat/refine     → 用户追加澄清，更新意图
  POST /chat/confirm    → 用户确认，创建 TripRequest + TripProfile，触发规划
  GET  /chat/{id}/status → 查询规划状态
"""

import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.business import TripProfile, TripRequest
from app.db.session import get_db
from app.domains.intake.intent_parser import TripIntentResult, parse_trip_intent, refine_intent
from app.domains.trip_core.planner import generate_plan

router = APIRouter(prefix="/chat", tags=["chat"])


# ── 请求/响应模型 ─────────────────────────────────────────────────────────────

class ChatStartRequest(BaseModel):
    message: str
    session_id: Optional[str] = None   # 前端可传 session，方便追踪


class ChatRefineRequest(BaseModel):
    session_id: str
    clarification: str
    original_message: str
    previous_intent: Dict[str, Any]    # 上一轮 TripIntentResult 的 dict


class ChatConfirmRequest(BaseModel):
    intent: Dict[str, Any]             # TripIntentResult 的 dict
    user_id: Optional[str] = None


class IntentOut(BaseModel):
    cities: List[Dict[str, Any]]
    duration_days: int
    travel_dates: Dict[str, str]
    party_size: int
    party_composition: Dict[str, Any]
    budget_level: str
    must_have_tags: List[str]
    travel_style: str
    confidence: float
    clarification_needed: Optional[str]


class ChatStartResponse(BaseModel):
    session_id: str
    intent: IntentOut
    message: str                       # 给用户的友好回复
    needs_clarification: bool


class ChatConfirmResponse(BaseModel):
    trip_request_id: str
    message: str
    status: str


class TripStatusResponse(BaseModel):
    trip_request_id: str
    status: str
    plan_id: Optional[str]
    message: str


# ── 辅助函数 ──────────────────────────────────────────────────────────────────

def _intent_to_out(intent: TripIntentResult) -> IntentOut:
    return IntentOut(
        cities=intent.cities,
        duration_days=intent.duration_days,
        travel_dates=intent.travel_dates,
        party_size=intent.party_size,
        party_composition=intent.party_composition,
        budget_level=intent.budget_level,
        must_have_tags=intent.must_have_tags,
        travel_style=intent.travel_style,
        confidence=intent.confidence,
        clarification_needed=intent.clarification_needed,
    )


def _friendly_reply(intent: TripIntentResult) -> str:
    """根据解析结果生成友好的自然语言回复"""
    if intent.clarification_needed:
        return intent.clarification_needed

    cities_str = " → ".join(
        c.get("city_code", "").upper() for c in intent.cities
    )
    budget_map = {
        "budget": "经济", "mid": "中等", "premium": "高档", "luxury": "豪华"
    }
    budget_str = budget_map.get(intent.budget_level, intent.budget_level)
    tags_str = "、".join(intent.must_have_tags[:4]) if intent.must_have_tags else "综合体验"

    reply = (
        f"✅ 已为您解析行程需求！\n\n"
        f"🗾 路线：{cities_str}\n"
        f"📅 天数：{intent.duration_days} 天\n"
        f"👥 人数：{intent.party_size} 人\n"
        f"💰 预算：{budget_str}\n"
        f"🎯 偏好：{tags_str}\n\n"
        f"如果以上信息正确，请确认开始规划；如需调整请告诉我。"
    )
    return reply


# ── POST /chat/start ──────────────────────────────────────────────────────────

@router.post("/start", response_model=ChatStartResponse)
async def chat_start(req: ChatStartRequest):
    """
    用户发送第一条自然语言消息，AI 解析旅行意图。
    不需要数据库连接，纯 AI 解析。
    """
    if not req.message.strip():
        raise HTTPException(status_code=422, detail="消息不能为空")

    intent = await parse_trip_intent(req.message)
    session_id = req.session_id or str(uuid.uuid4())

    return ChatStartResponse(
        session_id=session_id,
        intent=_intent_to_out(intent),
        message=_friendly_reply(intent),
        needs_clarification=bool(intent.clarification_needed),
    )


# ── POST /chat/refine ─────────────────────────────────────────────────────────

@router.post("/refine", response_model=ChatStartResponse)
async def chat_refine(req: ChatRefineRequest):
    """用户追加澄清，重新解析意图（多轮对话）"""
    if not req.clarification.strip():
        raise HTTPException(status_code=422, detail="澄清内容不能为空")

    # 重建上一轮 TripIntentResult
    prev = TripIntentResult(
        cities=req.previous_intent.get("cities", []),
        duration_days=req.previous_intent.get("duration_days", 7),
        budget_level=req.previous_intent.get("budget_level", "mid"),
        must_have_tags=req.previous_intent.get("must_have_tags", []),
        travel_style=req.previous_intent.get("travel_style", "general"),
        raw_message=req.original_message,
    )

    intent = await refine_intent(
        original_message=req.original_message,
        clarification=req.clarification,
        previous_result=prev,
    )

    return ChatStartResponse(
        session_id=req.session_id,
        intent=_intent_to_out(intent),
        message=_friendly_reply(intent),
        needs_clarification=bool(intent.clarification_needed),
    )


# ── POST /chat/confirm ────────────────────────────────────────────────────────

@router.post("/confirm", response_model=ChatConfirmResponse)
async def chat_confirm(req: ChatConfirmRequest, db: AsyncSession = Depends(get_db)):
    """
    用户确认意图，创建 TripRequest + TripProfile，同步触发规划。
    （小型系统直接同步规划；大型系统可改为异步 job）
    """
    intent_data = req.intent

    # 创建 TripRequest
    trip_req = TripRequest(
        user_id=req.user_id,
        raw_input=intent_data.get("raw_message", ""),
        status="new",
        channel="chat_api",
    )
    db.add(trip_req)
    await db.flush()

    # 创建 TripProfile
    profile = TripProfile(
        trip_request_id=trip_req.trip_request_id,
        cities=intent_data.get("cities", []),
        duration_days=int(intent_data.get("duration_days", 7)),
        travel_dates=intent_data.get("travel_dates", {}),
        party_size=int(intent_data.get("party_size", 2)),
        party_composition=intent_data.get("party_composition", {"adults": 2}),
        budget_level=intent_data.get("budget_level", "mid"),
        must_have_tags=intent_data.get("must_have_tags", []),
        travel_style=intent_data.get("travel_style", "general"),
    )
    db.add(profile)
    await db.flush()

    # 更新状态为 profiled
    trip_req.status = "profiled"
    await db.flush()

    # 同步触发规划（如果数据库里有种子数据）
    try:
        plan = await generate_plan(db, str(trip_req.trip_request_id))
        await db.commit()
        return ChatConfirmResponse(
            trip_request_id=str(trip_req.trip_request_id),
            message=f"🎉 行程规划完成！共 {intent_data.get('duration_days', 7)} 天行程已生成。",
            status="done",
        )
    except Exception as e:
        await db.rollback()
        # 规划失败也保留 TripRequest，前端可以重试
        return ChatConfirmResponse(
            trip_request_id=str(trip_req.trip_request_id),
            message=f"⚠️ 需求已记录，但规划暂未完成（原因：{str(e)[:100]}）。数据库中景点数据可能不足，请先导入数据。",
            status="profiled",
        )


# ── GET /chat/{id}/status ─────────────────────────────────────────────────────

@router.get("/{trip_request_id}/status", response_model=TripStatusResponse)
async def get_trip_status(trip_request_id: str, db: AsyncSession = Depends(get_db)):
    """查询行程规划状态"""
    try:
        req_uuid = uuid.UUID(trip_request_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="无效的 trip_request_id")

    result = await db.execute(
        select(TripRequest).where(TripRequest.trip_request_id == req_uuid)
    )
    trip_req = result.scalar_one_or_none()
    if trip_req is None:
        raise HTTPException(status_code=404, detail="未找到该行程请求")

    status_messages = {
        "new":          "⏳ 需求已提交，等待处理",
        "sample_viewed": "� 预览已查看",
        "paid":         "💰 已付款，等待填写详情",
        "detail_filling": "📝 详情填写中",
        "validating":   "🔍 正在校验",
        "validated":    "✅ 校验通过，等待生成",
        "generating":   "🔄 正在生成行程...",
        "done":         "✅ 行程生成完成！",
        "delivered":    "📬 行程已送达",
        "failed":       "❌ 规划失败，请重试",
    }

    # 查询是否有 plan
    from app.db.models.derived import ItineraryPlan
    plan_result = await db.execute(
        select(ItineraryPlan)
        .where(ItineraryPlan.trip_request_id == req_uuid)
        .order_by(ItineraryPlan.version.desc())
        .limit(1)
    )
    plan = plan_result.scalar_one_or_none()

    return TripStatusResponse(
        trip_request_id=trip_request_id,
        status=trip_req.status,
        plan_id=str(plan.plan_id) if plan else None,
        message=status_messages.get(trip_req.status, trip_req.status),
    )
