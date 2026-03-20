"""
Orders API — 订单管理端点（运营后台使用）。

核心状态机：
  quiz_submitted → preview_sent → paid → generating → review → delivered
                                                              → refunded

提供：
- POST   /orders              — 创建订单（关联 trip_request + sku）
- GET    /orders              — 按状态过滤查询订单列表
- GET    /orders/{id}         — 获取订单详情
- PATCH  /orders/{id}/status  — 推进订单状态（含状态校验）
"""
from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.business import Order, TripRequest, ProductSku
from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["orders"])


# ── 状态机定义 ────────────────────────────────────────────────────────────────

# 合法的状态流转
VALID_TRANSITIONS = {
    "quiz_submitted": ["preview_sent"],
    "preview_sent":   ["paid", "cancelled"],
    "paid":           ["generating", "refunded"],
    "generating":     ["review"],
    "review":         ["delivered", "generating"],  # review → generating = 打回重做
    "delivered":      ["refunded"],
    "cancelled":      [],
    "refunded":       [],
}

ALL_STATUSES = list(VALID_TRANSITIONS.keys())


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class OrderCreateRequest(BaseModel):
    trip_request_id: str = Field(..., description="关联的问卷提交 ID")
    sku_id: str = Field("standard_248", description="SKU ID")
    amount_cny: Optional[float] = Field(None, description="实际支付金额（不填则取 SKU 价格）")
    payment_channel: str = Field("wechat_manual", description="支付渠道")
    notes: Optional[str] = Field(None, description="运营备注")


class OrderStatusUpdate(BaseModel):
    new_status: str = Field(..., description="目标状态")
    reason: Optional[str] = Field(None, description="变更原因")


class OrderResponse(BaseModel):
    order_id: str
    trip_request_id: Optional[str]
    sku_id: str
    status: str
    amount_cny: float
    payment_channel: Optional[str]
    paid_at: Optional[str]
    created_at: str
    updated_at: str
    # 从 trip_request 带出的关键信息
    wechat_id: Optional[str] = None
    destination: Optional[str] = None
    duration_days: Optional[int] = None


class OrderListResponse(BaseModel):
    orders: list[OrderResponse]
    total: int


# ── Helper ────────────────────────────────────────────────────────────────────

def _order_to_response(order: Order, raw_input: dict | None = None) -> OrderResponse:
    raw = raw_input or {}
    return OrderResponse(
        order_id=str(order.order_id),
        trip_request_id=str(order.trip_request_id) if hasattr(order, "trip_request_id") and order.trip_request_id else None,
        sku_id=order.sku_id,
        status=order.status,
        amount_cny=float(order.amount_cny),
        payment_channel=order.payment_channel,
        paid_at=order.paid_at.isoformat() if order.paid_at else None,
        created_at=order.created_at.isoformat(),
        updated_at=order.updated_at.isoformat(),
        wechat_id=raw.get("wechat_id"),
        destination=raw.get("destination"),
        duration_days=raw.get("duration_days"),
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("", status_code=status.HTTP_201_CREATED, response_model=OrderResponse)
async def create_order(
    body: OrderCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    """创建订单（运营在微信确认用户意向后调用）"""
    # 校验 trip_request 存在
    trip = await db.get(TripRequest, uuid.UUID(body.trip_request_id))
    if not trip:
        raise HTTPException(404, f"TripRequest {body.trip_request_id} not found")

    # 校验 SKU 存在
    sku = await db.get(ProductSku, body.sku_id)
    if not sku:
        raise HTTPException(404, f"SKU {body.sku_id} not found")

    amount = body.amount_cny if body.amount_cny is not None else float(sku.price_cny)

    order = Order(
        sku_id=body.sku_id,
        status="quiz_submitted",
        amount_cny=amount,
        payment_channel=body.payment_channel,
    )
    # Order 表没有 trip_request_id 外键，通过 trip_request 的 order_id 关联
    db.add(order)
    await db.flush()

    # 双向绑定
    trip.order_id = order.order_id
    trip.sku_id = body.sku_id
    await db.flush()

    # 给 order 加上 trip_request_id 属性供响应用
    order.trip_request_id = trip.trip_request_id

    raw_input = trip.raw_input or {}
    return _order_to_response(order, raw_input)


@router.get("", response_model=OrderListResponse)
async def list_orders(
    status_filter: Optional[str] = Query(None, alias="status", description="按状态过滤"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> OrderListResponse:
    """查询订单列表（支持按状态过滤）"""
    # 总数
    count_q = select(func.count()).select_from(Order)
    if status_filter:
        count_q = count_q.where(Order.status == status_filter)
    total = (await db.execute(count_q)).scalar() or 0

    # 列表
    q = (
        select(Order)
        .order_by(Order.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if status_filter:
        q = q.where(Order.status == status_filter)
    rows = (await db.execute(q)).scalars().all()

    # 批量获取关联 trip_request 的 raw_input
    results = []
    for order in rows:
        raw_input = {}
        # 查找关联的 trip_request
        tr_result = await db.execute(
            select(TripRequest).where(TripRequest.order_id == order.order_id)
        )
        tr = tr_result.scalar_one_or_none()
        if tr:
            raw_input = tr.raw_input or {}
            order.trip_request_id = tr.trip_request_id
        results.append(_order_to_response(order, raw_input))

    return OrderListResponse(orders=results, total=total)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    """获取单个订单详情"""
    order = await db.get(Order, uuid.UUID(order_id))
    if not order:
        raise HTTPException(404, "Order not found")

    raw_input = {}
    tr_result = await db.execute(
        select(TripRequest).where(TripRequest.order_id == order.order_id)
    )
    tr = tr_result.scalar_one_or_none()
    if tr:
        raw_input = tr.raw_input or {}
        order.trip_request_id = tr.trip_request_id

    return _order_to_response(order, raw_input)


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: str,
    body: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    """
    推进订单状态。有状态机校验，不能跳步。

    状态流转:
    quiz_submitted → preview_sent → paid → generating → review → delivered
    """
    order = await db.get(Order, uuid.UUID(order_id))
    if not order:
        raise HTTPException(404, "Order not found")

    current = order.status
    target = body.new_status

    # 校验状态流转合法性
    if current not in VALID_TRANSITIONS:
        raise HTTPException(400, f"Unknown current status: {current}")

    if target not in VALID_TRANSITIONS[current]:
        allowed = VALID_TRANSITIONS[current]
        raise HTTPException(
            400,
            f"Cannot transition from '{current}' to '{target}'. "
            f"Allowed: {allowed}"
        )

    # 执行状态更新
    order.status = target

    # 特殊处理
    if target == "paid":
        order.paid_at = datetime.now(timezone.utc)

    await db.flush()

    logger.info(f"Order {order_id[:8]} status: {current} → {target} (reason: {body.reason})")

    # 查关联 trip_request
    raw_input = {}
    tr_result = await db.execute(
        select(TripRequest).where(TripRequest.order_id == order.order_id)
    )
    tr = tr_result.scalar_one_or_none()
    if tr:
        raw_input = tr.raw_input or {}
        order.trip_request_id = tr.trip_request_id
        # 同步更新 trip_request 状态
        if target in ("generating", "done", "delivered"):
            tr.status = target

    return _order_to_response(order, raw_input)
