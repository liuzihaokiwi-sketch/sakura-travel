"""
Modifications API — 用户端结构化修改请求。

核心逻辑：
- 用户通过 /plan/[id]/edit 页面提交结构化修改
- 校验精调次数（198 包 2 次，888 包不限次）
- 扣减次数 → 入队重新生成 → 返回 202
"""
from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.business import Order, TripRequest, ProductSku, ReviewJob, ReviewAction
from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["modifications"])


# ── SKU → max modifications mapping ──────────────────────────────────────────
SKU_MAX_MODIFICATIONS = {
    "standard_198": 2,
    "standard_248": 2,   # 旧 SKU 兼容
    "premium_888": -1,   # 不限次
    "basic_free": 0,
    "free_preview": 0,
}


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class ChangeItem(BaseModel):
    type: str = Field(
        ...,
        description="修改类型",
        examples=["replace_spot", "replace_restaurant", "adjust_pace", "remove_spot"],
    )
    target_entity_id: str = Field(..., description="要替换/删除的实体 ID")
    replacement_entity_id: Optional[str] = Field(None, description="替换目标实体 ID（remove 时为空）")


class ModifyRequest(BaseModel):
    day: int = Field(..., ge=1, le=30, description="修改的天数（Day N）")
    changes: list[ChangeItem] = Field(..., min_length=1, description="修改项列表")


class ModifyResponse(BaseModel):
    order_id: str
    modification_id: str
    remaining_modifications: int
    status: str
    message: str


class ModificationRecord(BaseModel):
    modification_id: str
    day: int
    changes: list[dict]
    created_at: str
    status: str


class ModificationListResponse(BaseModel):
    order_id: str
    total: int
    remaining_modifications: int
    modifications: list[ModificationRecord]


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_order_with_trip(
    order_id: str, db: AsyncSession
) -> tuple[Order, TripRequest | None]:
    """获取订单及其关联的 trip_request"""
    order = await db.get(Order, uuid.UUID(order_id))
    if not order:
        raise HTTPException(404, "Order not found")

    tr_result = await db.execute(
        select(TripRequest).where(TripRequest.order_id == order.order_id)
    )
    trip = tr_result.scalar_one_or_none()
    return order, trip


async def _count_modifications(order_id: uuid.UUID, db: AsyncSession) -> int:
    """统计已使用的修改次数"""
    result = await db.execute(
        select(func.count()).select_from(ReviewJob).where(
            ReviewJob.target_id == str(order_id),
            ReviewJob.target_type == "order",
            ReviewJob.job_type == "modification",
        )
    )
    return result.scalar() or 0


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/{order_id}/modify",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ModifyResponse,
)
async def submit_modification(
    order_id: str,
    body: ModifyRequest,
    db: AsyncSession = Depends(get_db),
) -> ModifyResponse:
    """
    提交结构化修改请求。

    - 校验订单存在且状态为 delivered
    - 校验精调次数未用完
    - 扣减次数，创建修改记录
    - 入队重新生成受影响的天
    """
    order, trip = await _get_order_with_trip(order_id, db)

    # 只有已交付的订单可以修改
    if order.status not in ("delivered", "done"):
        raise HTTPException(400, f"订单状态 '{order.status}' 不支持修改，需要已交付或已完成状态")

    # 获取 SKU 的最大修改次数
    max_mods = SKU_MAX_MODIFICATIONS.get(order.sku_id, 0)
    used_mods = await _count_modifications(order.order_id, db)

    if used_mods >= max_mods:
        raise HTTPException(
            403,
            f"精调次数已用完（{used_mods}/{max_mods}）。需要更多调整空间？升级管家版可享更多精调。",
        )

    # 创建修改记录（作为 ReviewJob）
    review_job = ReviewJob(
        job_type="modification",
        target_id=str(order.order_id),
        target_type="order",
        status="pending",
        priority=7,  # 修改请求优先级较高
    )
    db.add(review_job)
    await db.flush()

    # 记录修改详情
    action = ReviewAction(
        review_job_id=review_job.review_job_id,
        action_type="user_modify",
        payload={
            "day": body.day,
            "changes": [c.model_dump() for c in body.changes],
        },
        comment=f"用户修改 Day {body.day}，{len(body.changes)} 项变更",
    )
    db.add(action)

    # 更新订单状态为 generating（触发重新生成）
    order.status = "generating"
    await db.flush()

    remaining = max_mods - used_mods - 1

    logger.info(
        f"Modification submitted: order={order_id[:8]}, day={body.day}, "
        f"changes={len(body.changes)}, remaining={remaining}"
    )

    # TODO: enqueue generate_trip job for the affected day
    # await enqueue_job("generate_trip", trip_request_id=str(trip.trip_request_id), day=body.day)

    return ModifyResponse(
        order_id=order_id,
        modification_id=str(review_job.review_job_id),
        remaining_modifications=remaining,
        status="accepted",
        message=f"修改已提交，规划师将在2小时内更新你的行程。还剩 {remaining} 次精调机会。",
    )


@router.get(
    "/{order_id}/modifications",
    response_model=ModificationListResponse,
)
async def list_modifications(
    order_id: str,
    db: AsyncSession = Depends(get_db),
) -> ModificationListResponse:
    """查看订单的修改历史"""
    order, _ = await _get_order_with_trip(order_id, db)

    max_mods = SKU_MAX_MODIFICATIONS.get(order.sku_id, 0)

    # 查询所有修改记录
    jobs_result = await db.execute(
        select(ReviewJob)
        .where(
            ReviewJob.target_id == str(order.order_id),
            ReviewJob.target_type == "order",
            ReviewJob.job_type == "modification",
        )
        .order_by(ReviewJob.created_at.desc())
    )
    jobs = jobs_result.scalars().all()

    records = []
    for job in jobs:
        # 获取修改详情
        actions_result = await db.execute(
            select(ReviewAction)
            .where(
                ReviewAction.review_job_id == job.review_job_id,
                ReviewAction.action_type == "user_modify",
            )
            .order_by(ReviewAction.created_at.desc())
            .limit(1)
        )
        action = actions_result.scalar_one_or_none()

        payload = action.payload if action else {}
        records.append(
            ModificationRecord(
                modification_id=str(job.review_job_id),
                day=payload.get("day", 0),
                changes=payload.get("changes", []),
                created_at=job.created_at.isoformat(),
                status=job.status,
            )
        )

    return ModificationListResponse(
        order_id=order_id,
        total=len(records),
        remaining_modifications=max(0, max_mods - len(records)),
        modifications=records,
    )
