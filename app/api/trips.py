from __future__ import annotations

"""
Trip Core API router.
"""
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queue import enqueue_job
from app.db.models.business import TripProfile, TripRequest
from app.db.session import get_db

router = APIRouter()


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class CityInput(BaseModel):
    city_code: str = Field(..., examples=["tokyo", "osaka", "kyoto"])
    nights: int = Field(..., ge=1, le=30)


class TripCreateRequest(BaseModel):
    """POST /trips 请求体"""
    cities: list[CityInput] = Field(..., min_length=1)
    travel_start_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$", examples=["2025-04-01"])
    party_type: str = Field(
        "couple",
        examples=["solo", "couple", "family_child", "family_no_child", "group", "senior"],
    )
    party_size: int = Field(2, ge=1, le=20)
    budget_level: str = Field("mid", examples=["budget", "mid", "premium", "luxury"])
    interests: list[str] = Field(default_factory=list, examples=[["culture", "food"]])
    special_requirements: Optional[dict[str, Any]] = None


class TripCreateResponse(BaseModel):
    trip_request_id: str
    status: str
    message: str


class TripStatusResponse(BaseModel):
    trip_request_id: str
    status: str
    error_summary: Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=TripCreateResponse)
async def create_trip(
    body: TripCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> TripCreateResponse:
    """
    提交行程请求。
    返回 202 + trip_request_id，后台 Worker 异步处理。
    """
    trip = TripRequest(
        raw_input=body.model_dump(),
        status="new",
    )
    db.add(trip)
    await db.flush()  # 获取 trip_request_id（flush 不 commit，get_db 会在退出时 commit）

    # 入队 normalize_trip_profile job
    await enqueue_job("normalize_trip_profile", str(trip.trip_request_id))

    return TripCreateResponse(
        trip_request_id=str(trip.trip_request_id),
        status="new",
        message="Trip request accepted. Use GET /trips/{id}/status to poll.",
    )


@router.get("/{trip_id}", response_model=dict)
async def get_trip(
    trip_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """获取行程请求详情（含 profile，如已生成）"""
    trip = await db.get(TripRequest, uuid.UUID(trip_id))
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    result: dict = {
        "trip_request_id": str(trip.trip_request_id),
        "status": trip.status,
        "raw_input": trip.raw_input,
        "created_at": trip.created_at.isoformat(),
        "profile": None,
    }

    # 加载 profile（如已生成）
    profile_result = await db.execute(
        select(TripProfile).where(TripProfile.trip_request_id == trip.trip_request_id)
    )
    profile = profile_result.scalar_one_or_none()
    if profile:
        result["profile"] = {
            "cities": profile.cities,
            "duration_days": profile.duration_days,
            "party_type": profile.party_type,
            "party_size": profile.party_size,
            "budget_level": profile.budget_level,
            "must_have_tags": profile.must_have_tags,
            "nice_to_have_tags": profile.nice_to_have_tags,
            "avoid_tags": profile.avoid_tags,
        }

    return result


@router.get("/{trip_id}/status", response_model=TripStatusResponse)
async def get_trip_status(
    trip_id: str,
    db: AsyncSession = Depends(get_db),
) -> TripStatusResponse:
    """轻量状态查询（轮询用）"""
    trip = await db.get(TripRequest, uuid.UUID(trip_id))
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    return TripStatusResponse(
        trip_request_id=str(trip.trip_request_id),
        status=trip.status,
        error_summary=trip.last_job_error if trip.status == "failed" else None,
    )


# ── 问卷 & 推荐端点 ────────────────────────────────────────────────────────────

@router.get("/{trip_id}/profile-questions")
async def get_profile_questions(trip_id: str) -> dict:
    """
    返回5道偏好问卷题目（固定题目，不依赖 DB）。
    前端拿到后展示给用户，用户填写后提交到 POST /trips/{id}/questionnaire。
    """
    from app.domains.ranking.theme_weights import QUESTIONNAIRE_SIGNALS
    questions = [
        {
            "question_id": "q1",
            "question": "你这次最期待日本旅行的哪些体验？",
            "type": "multi_select",
            "options": list(QUESTIONNAIRE_SIGNALS["q1"].keys()),
        },
        {
            "question_id": "q2",
            "question": "这次同行人是谁？",
            "type": "single_select",
            "options": list(QUESTIONNAIRE_SIGNALS["q2"].keys()),
        },
        {
            "question_id": "q3",
            "question": "你是第一次去日本，还是已经去过？",
            "type": "single_select",
            "options": list(QUESTIONNAIRE_SIGNALS["q3"].keys()),
        },
        {
            "question_id": "q4",
            "question": "你更喜欢哪种节奏？",
            "type": "single_select",
            "options": list(QUESTIONNAIRE_SIGNALS["q4"].keys()),
        },
        {
            "question_id": "q5",
            "question": "你对以下项目有没有特别想安排的？",
            "type": "multi_select",
            "options": list(QUESTIONNAIRE_SIGNALS["q5"].keys()),
        },
    ]
    return {"trip_request_id": trip_id, "questions": questions}


class QuestionnaireSubmit(BaseModel):
    """POST /trips/{id}/questionnaire 请求体"""
    answers: dict[str, list[str]] = Field(
        ...,
        examples=[{
            "q1": ["美食探店", "拍照出片"],
            "q2": ["情侣/配偶"],
            "q3": ["第一次去"],
            "q5": ["樱花/红叶"],
        }]
    )
    is_repeat_visitor: bool = Field(False)
    travel_season: Optional[str] = Field(
        None,
        examples=["spring", "summer", "autumn", "winter"],
    )


@router.post("/{trip_id}/questionnaire")
async def submit_questionnaire(
    trip_id: str,
    body: QuestionnaireSubmit,
    db: AsyncSession = Depends(get_db),
) -> dict:
    del trip_id, body, db
    raise HTTPException(
        status_code=410,
        detail=(
            "Legacy questionnaire entry is retired. "
            "Use detail-form canonical input and city-circle main-chain generation."
        ),
    )


@router.get("/{trip_id}/recommendations")
async def get_recommendations(
    trip_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    del trip_id, db
    raise HTTPException(
        status_code=410,
        detail=(
            "Legacy recommendation read API is retired. "
            "Use page-model-first delivery endpoints."
        ),
    )
