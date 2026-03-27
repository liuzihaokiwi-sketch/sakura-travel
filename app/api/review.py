"""Admin review API with unified operator-surface semantics."""

from __future__ import annotations

import uuid
import logging
from dataclasses import dataclass
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.business import Order, TripRequest, ReviewJob, ReviewAction
from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/reviews", tags=["admin-reviews"])


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

    # Unified operator surface fields (P1-B3)
    operator_surface: str = "order_review_surface"
    operator_stage: str = "action_needed"
    operator_action_boundary: str = "compatibility_support"
    proof_lane: str = "compatibility_baseline"


class ReviewListResponse(BaseModel):
    orders: list[ReviewOrderSummary]
    total: int


class ReviewUpdateRequest(BaseModel):
    itinerary_json: Optional[dict] = Field(None, description="Updated itinerary payload")
    notes: Optional[str] = Field(None, description="Operator note")


class ReviewActionResponse(BaseModel):
    order_id: str
    new_status: str
    message: str

    operator_surface: str = "order_review_surface"
    operator_stage: str = "action_done"
    operator_action_boundary: str = "main_proof_flow"
    proof_lane: str = "main_chain_proof"


@dataclass
class OperatorSurfaceState:
    stage: str
    action_boundary: str
    proof_lane: str


def _derive_operator_surface_state(
    *,
    order_status: str,
    has_pending_modifications: bool,
    has_active_review_job: bool,
) -> OperatorSurfaceState:
    terminal_status = {"cancelled", "refunded", "archived"}
    main_flow_status = {"done", "delivered", "generating"}

    if order_status in terminal_status:
        return OperatorSurfaceState(
            stage="terminal",
            action_boundary="compatibility_support",
            proof_lane="compatibility_baseline",
        )

    if order_status in main_flow_status or has_active_review_job:
        stage = "action_needed" if has_pending_modifications or order_status in {"done", "generating"} else "read_ready"
        return OperatorSurfaceState(
            stage=stage,
            action_boundary="main_proof_flow",
            proof_lane="main_chain_proof",
        )

    return OperatorSurfaceState(
        stage="read_ready",
        action_boundary="compatibility_support",
        proof_lane="compatibility_baseline",
    )


async def _get_order_and_trip(order_id: str, db: AsyncSession) -> tuple[Order, TripRequest | None]:
    try:
        order_uuid = uuid.UUID(order_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid order_id format") from exc

    order = await db.get(Order, order_uuid)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    tr_result = await db.execute(
        select(TripRequest).where(TripRequest.order_id == order.order_id)
    )
    trip = tr_result.scalar_one_or_none()
    return order, trip


async def _count_pending_modifications(order: Order, db: AsyncSession) -> bool:
    mod_count = await db.execute(
        select(func.count()).select_from(ReviewJob).where(
            ReviewJob.target_id == str(order.order_id),
            ReviewJob.target_type == "order",
            ReviewJob.job_type == "modification",
            ReviewJob.status == "pending",
        )
    )
    return (mod_count.scalar() or 0) > 0


async def _has_active_review_job(order: Order, db: AsyncSession) -> bool:
    row = await db.execute(
        select(func.count()).select_from(ReviewJob).where(
            ReviewJob.target_id == str(order.order_id),
            ReviewJob.target_type == "order",
            ReviewJob.job_type.in_(["plan_review", "modification"]),
            ReviewJob.status.in_(["pending", "in_review"]),
        )
    )
    return (row.scalar() or 0) > 0


async def _build_summary(order: Order, trip: TripRequest | None, db: AsyncSession) -> ReviewOrderSummary:
    raw = (trip.raw_input if trip else {}) or {}
    has_pending = await _count_pending_modifications(order, db)
    has_active_job = await _has_active_review_job(order, db)
    state = _derive_operator_surface_state(
        order_status=order.status,
        has_pending_modifications=has_pending,
        has_active_review_job=has_active_job,
    )

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
        operator_surface="order_review_surface",
        operator_stage=state.stage,
        operator_action_boundary=state.action_boundary,
        proof_lane=state.proof_lane,
    )


@router.get("/pending", response_model=ReviewListResponse)
async def list_pending_reviews(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> ReviewListResponse:
    """List orders relevant for operator review surface."""
    q = (
        select(Order)
        .where(Order.status.in_(["done", "generating", "delivered"]))
        .order_by(Order.created_at.asc())
        .limit(limit)
    )
    rows = (await db.execute(q)).scalars().all()

    summaries: list[ReviewOrderSummary] = []
    for order in rows:
        tr_result = await db.execute(
            select(TripRequest).where(TripRequest.order_id == order.order_id)
        )
        trip = tr_result.scalar_one_or_none()
        summaries.append(await _build_summary(order, trip, db))

    return ReviewListResponse(orders=summaries, total=len(summaries))


@router.get("/{order_id}", response_model=ReviewOrderSummary)
async def get_review_detail(order_id: str, db: AsyncSession = Depends(get_db)) -> ReviewOrderSummary:
    order, trip = await _get_order_and_trip(order_id, db)
    return await _build_summary(order, trip, db)


@router.patch("/{order_id}", response_model=ReviewActionResponse)
async def update_review_content(
    order_id: str,
    body: ReviewUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> ReviewActionResponse:
    """Save operator edits as review actions; this is explicit edit boundary."""
    order, _ = await _get_order_and_trip(order_id, db)

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

    action = ReviewAction(
        review_job_id=review_job.review_job_id,
        action_type="edit_field",
        actor="admin",
        payload={"itinerary_json": body.itinerary_json} if body.itinerary_json else None,
        comment=body.notes,
    )
    db.add(action)

    if order.status == "generating":
        order.status = "done"

    await db.flush()

    return ReviewActionResponse(
        order_id=order_id,
        new_status=order.status,
        message="Review content saved",
        operator_surface="order_review_surface",
        operator_stage="action_done",
        operator_action_boundary="main_proof_flow",
        proof_lane="main_chain_proof",
    )


@router.post("/{order_id}/publish", response_model=ReviewActionResponse)
async def publish_order(order_id: str, db: AsyncSession = Depends(get_db)) -> ReviewActionResponse:
    """Publish reviewed order to user-facing delivered status."""
    order, _ = await _get_order_and_trip(order_id, db)

    if order.status not in ("done", "generating"):
        raise HTTPException(status_code=400, detail=f"Status '{order.status}' cannot be published")

    order.status = "delivered"
    await db.flush()

    jobs_result = await db.execute(
        select(ReviewJob).where(
            ReviewJob.target_id == str(order.order_id),
            ReviewJob.target_type == "order",
            ReviewJob.status.in_(["pending", "in_review"]),
        )
    )
    for job in jobs_result.scalars().all():
        job.status = "approved"
        db.add(
            ReviewAction(
                review_job_id=job.review_job_id,
                action_type="approve",
                actor="admin",
                comment="published",
            )
        )

    await db.flush()
    logger.info("Order published: %s", order_id)

    return ReviewActionResponse(
        order_id=order_id,
        new_status="delivered",
        message="Order published",
        operator_surface="order_review_surface",
        operator_stage="action_done",
        operator_action_boundary="main_proof_flow",
        proof_lane="main_chain_proof",
    )


@router.post("/{order_id}/reject", response_model=ReviewActionResponse)
async def reject_order(
    order_id: str,
    reason: Optional[str] = Query(None, description="reject reason"),
    db: AsyncSession = Depends(get_db),
) -> ReviewActionResponse:
    """Reject current output and move order back to generating."""
    order, _ = await _get_order_and_trip(order_id, db)

    if order.status not in ("done",):
        raise HTTPException(status_code=400, detail=f"Status '{order.status}' cannot be rejected")

    order.status = "generating"
    await db.flush()

    jobs_result = await db.execute(
        select(ReviewJob).where(
            ReviewJob.target_id == str(order.order_id),
            ReviewJob.target_type == "order",
            ReviewJob.status.in_(["pending", "in_review"]),
        )
    )
    for job in jobs_result.scalars().all():
        job.status = "rejected"
        db.add(
            ReviewAction(
                review_job_id=job.review_job_id,
                action_type="reject",
                actor="admin",
                comment=reason or "rejected for regeneration",
            )
        )

    await db.flush()
    logger.info("Order rejected: %s", order_id)

    return ReviewActionResponse(
        order_id=order_id,
        new_status="generating",
        message="Order rejected and moved back to generating",
        operator_surface="order_review_surface",
        operator_stage="action_done",
        operator_action_boundary="main_proof_flow",
        proof_lane="main_chain_proof",
    )
