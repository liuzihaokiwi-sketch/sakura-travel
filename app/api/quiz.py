"""
Quiz API — 轻问卷提交端点。

用户在前台 /quiz 填完 5 步问卷后，数据 POST 到此端点。
1. 写入 trip_requests 表 (status = quiz_submitted)
2. 触发企业微信 / 飞书 webhook 通知运营
3. 返回 trip_request_id 供前端跳转 /submitted
"""
from __future__ import annotations

import logging
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.business import TripRequest
from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class QuizSubmission(BaseModel):
    """前端 /quiz 页面提交的问卷数据"""

    # Step 1: 去哪里
    destination: str = Field(
        ...,
        description="目的地选择",
        examples=["tokyo", "osaka-kyoto", "tokyo-osaka-kyoto", "hokkaido", "okinawa", "other"],
    )

    # Step 2: 去几天
    duration_days: int = Field(
        ..., ge=3, le=30,
        description="旅行天数",
        examples=[5, 7],
    )

    # Step 3: 和谁去
    party_type: str = Field(
        ...,
        description="同行人类型",
        examples=["solo", "couple", "family", "friends", "parents"],
    )

    # Step 4: 旅行风格 (可选，最多3个)
    styles: list[str] = Field(
        default_factory=list,
        max_length=3,
        description="旅行风格偏好",
        examples=[["photo", "food", "culture"]],
    )

    # Step 5: 微信号 (关键！)
    wechat_id: str = Field(
        ..., min_length=1, max_length=100,
        description="用户微信号，用于发送方案",
    )

    # 可选：出发时间
    travel_time: Optional[str] = Field(
        None,
        description="大致出发时间",
        examples=["mar-late", "apr-early", "may"],
    )


class QuizResponse(BaseModel):
    trip_request_id: str
    status: str
    message: str


# ── Helper: 发送通知 ──────────────────────────────────────────────────────────

DESTINATION_LABELS = {
    "tokyo": "东京",
    "osaka-kyoto": "大阪+京都",
    "tokyo-osaka-kyoto": "东京+大阪+京都",
    "hokkaido": "北海道",
    "okinawa": "冲绳",
    "other": "其他",
}

PARTY_LABELS = {
    "solo": "独自一人",
    "couple": "情侣/夫妻",
    "family": "带孩子/家庭",
    "friends": "朋友/闺蜜",
    "parents": "带父母",
}

STYLE_LABELS = {
    "photo": "📸出片",
    "food": "🍣美食",
    "budget": "💰省钱",
    "culture": "🏛️文化",
    "kids": "👶亲子",
    "relax": "🧖放松",
}


async def _send_wecom_notification(data: QuizSubmission, trip_request_id: str) -> None:
    """发送企业微信机器人通知。静默失败，不影响主流程。"""
    webhook_url = settings.wecom_webhook_url
    if not webhook_url:
        logger.info("WECOM_WEBHOOK_URL 未配置，跳过通知")
        return

    dest = DESTINATION_LABELS.get(data.destination, data.destination)
    party = PARTY_LABELS.get(data.party_type, data.party_type)
    styles_str = "、".join(STYLE_LABELS.get(s, s) for s in data.styles) if data.styles else "未选择"
    travel_time = data.travel_time or "未指定"

    content = (
        f"📋 **新问卷提交**\n"
        f"> 订单ID: `{trip_request_id[:8]}...`\n"
        f"> 目的地: **{dest}**\n"
        f"> 天数: **{data.duration_days}天**\n"
        f"> 同行: {party}\n"
        f"> 风格: {styles_str}\n"
        f"> 出发: {travel_time}\n"
        f"> 微信: **{data.wechat_id}**\n"
        f"\n⏰ 请在 2 小时内联系用户并发送预览"
    )

    payload = {
        "msgtype": "markdown",
        "markdown": {"content": content},
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(webhook_url, json=payload)
            if resp.status_code == 200:
                logger.info(f"企微通知发送成功: trip={trip_request_id[:8]}")
            else:
                logger.warning(f"企微通知失败: status={resp.status_code}, body={resp.text}")
    except Exception as e:
        logger.warning(f"企微通知异常: {e}")


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post(
    "/quiz",
    status_code=status.HTTP_201_CREATED,
    response_model=QuizResponse,
    summary="提交轻问卷",
    description="用户在前台 /quiz 填完5步问卷后提交。写入 trip_requests 并通知运营。",
)
async def submit_quiz(
    body: QuizSubmission,
    db: AsyncSession = Depends(get_db),
) -> QuizResponse:
    # 1. 构建 raw_input (保留原始问卷数据，后续生成方案用)
    raw_input = {
        "source": "quiz_v1",
        "destination": body.destination,
        "duration_days": body.duration_days,
        "party_type": body.party_type,
        "styles": body.styles,
        "wechat_id": body.wechat_id,
        "travel_time": body.travel_time,
    }

    # 2. 写入 trip_requests
    trip = TripRequest(
        raw_input=raw_input,
        status="new",
    )
    db.add(trip)
    await db.flush()

    trip_id = str(trip.trip_request_id)

    # 3. 异步发送通知 (不阻塞响应)
    try:
        await _send_wecom_notification(body, trip_id)
    except Exception as e:
        logger.warning(f"通知发送失败，不影响主流程: {e}")

    return QuizResponse(
        trip_request_id=trip_id,
        status="new",
        message="已收到你的需求！规划师会在 2 小时内通过微信联系你。",
    )
