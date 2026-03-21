"""
Review API — 内部审核操作端点。

提供：
- GET    /admin/reviews/pending       — 待审核列表
- GET    /admin/reviews/{order_id}    — 审核详情
- PATCH  /admin/reviews/{order_id}    — 更新方案内容
- POST   /admin/reviews/{order_id}/publish  — 发布给用户
- POST   /admin/reviews/{order_id}/reject   — 打回重做
"""
from __future__ import annotations

import uuid
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.business import Order, TripRequest, ReviewJob, ReviewAction
from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/reviews", tags=["admin-reviews"])


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class ReviewOrderSummary(BaseModel):
    order_id: str
    status: str
    sku_id: str
    amount_cny: float
    created_at: str
    wechat_id: Optional[str] = None
    destination: Optional[str] = None
    duration_days: Optional[int] = None
    has_pending_modifications: bool = False


class ReviewListResponse(BaseModel):
    orders: list[ReviewOrderSummary]
    total: int


class ReviewUpdateRequest(BaseModel):
    """PATCH body: 更新方案内容"""
    itinerary_json: Optional[dict] = Field(None, description="修改后的行程 JSON")
    notes: Optional[str] = Field(None, description="审核备注")


class ReviewActionResponse(BaseModel):
    order_id: str
    new_status: str
    message: str


# ── Helper ────────────────────────────────────────────────────────────────────

async def _get_order_and_trip(
    order_id: str, db: AsyncSession
) -> tuple[Order, TripRequest | None]:
    order = await db.get(Order, uuid.UUID(order_id))
    if not order:
        raise HTTPException(404, "Order not found")

    tr_result = await db.execute(
        select(TripRequest).where(TripRequest.order_id == order.order_id)
    )
    trip = tr_result.scalar_one_or_none()
    return order, trip


async def _build_summary(
    order: Order, trip: TripRequest | None, db: AsyncSession
) -> ReviewOrderSummary:
    raw = (trip.raw_input if trip else {}) or {}

    # Check for pending modification jobs
    mod_count = await db.execute(
        select(func.count()).select_from(ReviewJob).where(
            ReviewJob.target_id == str(order.order_id),
            ReviewJob.target_type == "order",
            ReviewJob.job_type == "modification",
            ReviewJob.status == "pending",
        )
    )
    has_pending = (mod_count.scalar() or 0) > 0

    return ReviewOrderSummary(
        order_id=str(order.order_id),
        status=order.status,
        sku_id=order.sku_id,
        amount_cny=float(order.amount_cny),
        created_at=order.created_at.isoformat(),
        wechat_id=raw.get("wechat_id"),
        destination=raw.get("destination"),
        duration_days=raw.get("duration_days"),
        has_pending_modifications=has_pending,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/pending", response_model=ReviewListResponse)
async def list_pending_reviews(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> ReviewListResponse:
    """
    获取待审核订单列表。
    包括 status=review 的订单 + 有 pending modification 的订单。
    """
    # 查询 status=done 或 status=generating 的订单（待审核）
    q = (
        select(Order)
        .where(Order.status.in_(["done", "generating"]))
        .order_by(Order.created_at.asc())
        .limit(limit)
    )
    rows = (await db.execute(q)).scalars().all()

    summaries = []
    for order in rows:
        tr_result = await db.execute(
            select(TripRequest).where(TripRequest.order_id == order.order_id)
        )
        trip = tr_result.scalar_one_or_none()
        summaries.append(await _build_summary(order, trip, db))

    return ReviewListResponse(orders=summaries, total=len(summaries))


@router.get("/{order_id}", response_model=ReviewOrderSummary)
async def get_review_detail(
    order_id: str,
    db: AsyncSession = Depends(get_db),
) -> ReviewOrderSummary:
    """获取单个订单审核详情"""
    order, trip = await _get_order_and_trip(order_id, db)
    return await _build_summary(order, trip, db)


@router.patch("/{order_id}", response_model=ReviewActionResponse)
async def update_review_content(
    order_id: str,
    body: ReviewUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> ReviewActionResponse:
    """
    更新方案内容（保存草稿）。
    审核人员在工作台编辑后调用。
    """
    order, trip = await _get_order_and_trip(order_id, db)

    # 创建审核操作记录
    # 先查找或创建 plan_review job
    review_result = await db.execute(
        select(ReviewJob).where(
            ReviewJob.target_id == str(order.order_id),
            ReviewJob.target_type == "order",
            ReviewJob.job_type == "plan_review",
            ReviewJob.status.in_(["pending", "in_review"]),
        ).order_by(ReviewJob.created_at.desc()).limit(1)
    )
    review_job = review_result.scalar_one_or_none()

    if not review_job:
        review_job = ReviewJob(
            job_type="plan_review",
            target_id=str(order.order_id),
            target_type="order",
            status="in_review",
            priority=5,
        )
        db.add(review_job)
        await db.flush()

    # 记录编辑操作
    action = ReviewAction(
        review_job_id=review_job.review_job_id,
        action_type="edit_field",
        actor="admin",
        payload={
            "itinerary_json": body.itinerary_json,
        } if body.itinerary_json else None,
        comment=body.notes,
    )
    db.add(action)

    # 确保订单在 done 状态（审核中）
    if order.status == "generating":
        order.status = "done"

    await db.flush()

    logger.info(f"Review updated: order={order_id[:8]}")

    return ReviewActionResponse(
        order_id=order_id,
        new_status=order.status,
        message="方案已保存",
    )


@router.post("/{order_id}/publish", response_model=ReviewActionResponse)
async def publish_order(
    order_id: str,
    db: AsyncSession = Depends(get_db),
) -> ReviewActionResponse:
    """
    发布给用户（status → delivered）。
    """
    order, _ = await _get_order_and_trip(order_id, db)

    if order.status not in ("done", "generating"):
        raise HTTPException(
            400,
            f"当前状态 '{order.status}' 无法发布，需要 done 或 generating 状态",
        )

    order.status = "delivered"
    await db.flush()

    # 关闭相关的 review jobs
    jobs_result = await db.execute(
        select(ReviewJob).where(
            ReviewJob.target_id == str(order.order_id),
            ReviewJob.target_type == "order",
            ReviewJob.status.in_(["pending", "in_review"]),
        )
    )
    for job in jobs_result.scalars().all():
        job.status = "approved"
        action = ReviewAction(
            review_job_id=job.review_job_id,
            action_type="approve",
            actor="admin",
            comment="发布给用户",
        )
        db.add(action)

    await db.flush()

    logger.info(f"Order published: {order_id[:8]} → delivered")

    return ReviewActionResponse(
        order_id=order_id,
        new_status="delivered",
        message="方案已发布给用户",
    )


@router.post("/{order_id}/reject", response_model=ReviewActionResponse)
async def reject_order(
    order_id: str,
    reason: Optional[str] = Query(None, description="打回原因"),
    db: AsyncSession = Depends(get_db),
) -> ReviewActionResponse:
    """
    打回重做（status → generating）。
    """
    order, _ = await _get_order_and_trip(order_id, db)

    if order.status not in ("done",):
        raise HTTPException(
            400,
            f"当前状态 '{order.status}' 无法打回，需要 done 状态",
        )

    order.status = "generating"
    await db.flush()

    # 记录打回操作
    jobs_result = await db.execute(
        select(ReviewJob).where(
            ReviewJob.target_id == str(order.order_id),
            ReviewJob.target_type == "order",
            ReviewJob.status.in_(["pending", "in_review"]),
        )
    )
    for job in jobs_result.scalars().all():
        job.status = "rejected"
        action = ReviewAction(
            review_job_id=job.review_job_id,
            action_type="reject",
            actor="admin",
            comment=reason or "打回重新生成",
        )
        db.add(action)

    await db.flush()

    logger.info(f"Order rejected: {order_id[:8]} → generating (reason: {reason})")

    return ReviewActionResponse(
        order_id=order_id,
        new_status="generating",
        message="已打回重新生成",
    )
