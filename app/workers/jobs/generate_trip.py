"""
arq Job: generate_trip
触发行程装配 → 写入 DB → enqueue run_guardrails
"""
from __future__ import annotations

import logging
import uuid

from app.core.queue import enqueue_job
from app.db.models.business import TripRequest
from app.db.session import AsyncSessionLocal as async_session_factory
from app.domains.planning.assembler import assemble_trip
from app.domains.planning.assembler import enrich_itinerary_with_copy

logger = logging.getLogger(__name__)


async def generate_trip(
    ctx: dict,
    *,
    trip_request_id: str,
    template_code: str,
    scene: str = "general",
) -> dict:
    """
    arq Job: 触发行程装配。

    Args:
        trip_request_id: 行程请求 UUID（字符串）
        template_code: 路线模板代码，如 "tokyo_classic_5d"
        scene: 出行场景，如 "couple" / "family" / "solo"
    """
    trip_id = uuid.UUID(trip_request_id)
    logger.info("generate_trip 开始 trip=%s template=%s scene=%s", trip_id, template_code, scene)

    async with async_session_factory() as session:
        # 更新状态为 assembling
        trip = await session.get(TripRequest, trip_id)
        if trip is None:
            logger.error("trip_request_id=%s 不存在", trip_id)
            return {"status": "error", "reason": "trip not found"}

        trip.status = "assembling"
        await session.commit()

        # 执行装配
        try:
            plan_id = await assemble_trip(
                session=session,
                trip_request_id=trip_id,
                template_code=template_code,
                scene=scene,
            )
            # AI 文案润色（装配后批量生成描述 + Tips）
            await enrich_itinerary_with_copy(
                session=session,
                plan_id=plan_id,
                scene=scene,
            )
        except Exception as exc:
            logger.exception("generate_trip 装配失败 trip=%s: %s", trip_id, exc)
            trip.status = "failed"
            await session.commit()
            return {"status": "error", "reason": str(exc)}

    # 装配成功 → 触发审核 job
    await enqueue_job("run_guardrails", plan_id=str(plan_id))
    logger.info("generate_trip 完成 plan=%s，已入队 run_guardrails", plan_id)

    return {"status": "ok", "plan_id": str(plan_id)}
