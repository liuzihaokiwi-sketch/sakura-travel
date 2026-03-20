"""
arq Job: run_guardrails
简版 v1：校验行程质量，通过后触发 render_export
"""
from __future__ import annotations

import logging
import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queue import enqueue_job
from app.db.models.business import TripRequest
from app.db.models.derived import ItineraryDay, ItineraryItem, ItineraryPlan
from app.db.session import AsyncSessionLocal as async_session_factory

logger = logging.getLogger(__name__)

# hard_fail 阈值
MIN_ITEMS_PER_PLAN = 3          # 整个 plan 至少 3 个实体
MAX_DUPLICATE_RATIO = 0.2       # 重复实体比例上限 20%


async def _check_plan(session: AsyncSession, plan_id: uuid.UUID) -> list[str]:
    """
    返回 hard_fail 错误列表。列表为空表示校验通过。
    """
    errors: list[str] = []

    # 1. 查询所有 items（通过 day_id join）
    days_q = await session.execute(
        select(ItineraryDay).where(ItineraryDay.plan_id == plan_id)
    )
    day_ids = [d.day_id for d in days_q.scalars().all()]
    if not day_ids:
        items = []
    else:
        items_q = await session.execute(
            select(ItineraryItem).where(ItineraryItem.day_id.in_(day_ids))
        )
        items = items_q.scalars().all()

    if len(items) < MIN_ITEMS_PER_PLAN:
        errors.append(
            f"实体数量不足：{len(items)} < {MIN_ITEMS_PER_PLAN}"
        )

    # 2. 检查重复实体
    entity_ids = [item.entity_id for item in items if item.entity_id is not None]
    if entity_ids:
        unique_count = len(set(entity_ids))
        dup_ratio = 1 - unique_count / len(entity_ids)
        if dup_ratio > MAX_DUPLICATE_RATIO:
            errors.append(
                f"重复实体比例过高：{dup_ratio:.0%} > {MAX_DUPLICATE_RATIO:.0%}"
            )

    return errors


async def run_guardrails(
    ctx: dict,
    *,
    plan_id: str,
) -> dict:
    """
    arq Job: 行程质量校验。
    通过后 enqueue render_export；失败则标记 trip_requests.status = 'failed'。
    """
    pid = uuid.UUID(plan_id)
    logger.info("run_guardrails 开始 plan=%s", pid)

    async with async_session_factory() as session:
        plan = await session.get(ItineraryPlan, pid)
        if plan is None:
            logger.error("plan_id=%s 不存在", pid)
            return {"status": "error", "reason": "plan not found"}

        # 更新 trip 状态为 reviewing
        trip = await session.get(TripRequest, plan.trip_request_id)
        if trip:
            trip.status = "reviewing"
            await session.commit()

        # 执行校验
        errors = await _check_plan(session, pid)

        if errors:
            logger.warning("run_guardrails hard_fail plan=%s: %s", pid, errors)
            if trip:
                trip.status = "failed"
                await session.commit()
            return {"status": "failed", "errors": errors}

    # 校验通过 → 触发渲染
    await enqueue_job("render_export", plan_id=plan_id)
    logger.info("run_guardrails 通过 plan=%s，已入队 render_export", pid)

    return {"status": "ok", "plan_id": plan_id}
