"""
5.6 节奏强度切换 API
GET  /trips/{trip_id}/intensity         — 查询当前节奏
POST /trips/{trip_id}/intensity         — 切换节奏（relaxed/moderate/intensive）

节奏定义：
  relaxed   — 每天 3-4 个景点，留出 2-3 小时自由时间
  moderate  — 每天 4-5 个景点（默认）
  intensive — 每天 5-6 个景点，紧凑日程

切换后：标记行程需要重装配，入队 generate_trip 任务
"""
from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.business import TripRequest
from app.core.queue import enqueue_job

router = APIRouter(prefix="/trips", tags=["trips-intensity"])

IntensityLevel = Literal["relaxed", "moderate", "intensive"]

INTENSITY_CONFIG: dict[str, dict] = {
    "relaxed": {
        "label": "轻松节奏",
        "description": "每天 3-4 个景点，留出充裕的自由时间，适合深度体验和休闲",
        "spots_per_day": (3, 4),
        "free_hours": 3,
        "icon": "🌿",
    },
    "moderate": {
        "label": "适中节奏",
        "description": "每天 4-5 个景点（默认），经典线路安排，兼顾效率与体验",
        "spots_per_day": (4, 5),
        "free_hours": 1.5,
        "icon": "⚖️",
    },
    "intensive": {
        "label": "紧凑节奏",
        "description": "每天 5-6 个景点，最大化覆盖率，适合打卡型旅行者",
        "spots_per_day": (5, 6),
        "free_hours": 0.5,
        "icon": "⚡",
    },
}


class IntensityResponse(BaseModel):
    trip_id: str
    current_intensity: str
    config: dict
    all_levels: list[dict]


class SetIntensityRequest(BaseModel):
    intensity: IntensityLevel


@router.get("/{trip_id}/intensity", response_model=IntensityResponse)
async def get_intensity(
    trip_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """查询当前行程的节奏设置。"""
    trip = await db.get(TripRequest, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="行程不存在")

    # 从 trip metadata 读取，默认 moderate
    meta = trip.quiz_answers or {}
    current = meta.get("pace_preference", "moderate")
    if current not in INTENSITY_CONFIG:
        current = "moderate"

    return IntensityResponse(
        trip_id=str(trip_id),
        current_intensity=current,
        config=INTENSITY_CONFIG[current],
        all_levels=[
            {"level": k, **v} for k, v in INTENSITY_CONFIG.items()
        ],
    )


@router.post("/{trip_id}/intensity")
async def set_intensity(
    trip_id: uuid.UUID,
    body: SetIntensityRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    切换行程节奏。

    - 更新 quiz_answers.pace_preference
    - 将行程状态设置为 pending（需重新生成）
    - 入队 generate_trip 任务
    """
    trip = await db.get(TripRequest, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="行程不存在")

    # 只有特定状态才允许切换节奏
    allowed_statuses = {"quiz_submitted", "preview_sent", "paid", "generating", "review", "delivered"}
    if trip.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"当前状态 '{trip.status}' 不支持切换节奏",
        )

    # 更新节奏偏好
    quiz_answers = dict(trip.quiz_answers or {})
    old_intensity = quiz_answers.get("pace_preference", "moderate")
    quiz_answers["pace_preference"] = body.intensity
    trip.quiz_answers = quiz_answers

    if old_intensity != body.intensity:
        # 节奏变化 → 需要重新生成
        trip.status = "pending"

    await db.commit()

    # 入队重新生成（如果状态已变为 pending）
    job_queued = False
    if old_intensity != body.intensity:
        try:
            template_code = (quiz_answers.get("cities") or [{}])[0]
            tc = "tokyo_classic_5d"  # 默认模板
            scene = quiz_answers.get("travel_style", "general")
            await enqueue_job(
                "generate_trip",
                trip_request_id=str(trip_id),
                template_code=tc,
                scene=scene,
            )
            job_queued = True
        except Exception:
            pass

    config = INTENSITY_CONFIG[body.intensity]
    return {
        "status": "ok",
        "trip_id": str(trip_id),
        "old_intensity": old_intensity,
        "new_intensity": body.intensity,
        "config": config,
        "regeneration_queued": job_queued,
        "message": f"节奏已切换为「{config['label']}」{'，行程将重新生成' if job_queued else ''}",
    }
