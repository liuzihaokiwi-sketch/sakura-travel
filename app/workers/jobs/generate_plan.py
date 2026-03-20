"""
arq Job：generate_itinerary_plan

触发方式：
  - POST /trips/{id}/generate  调用后入队
  - 手动：await enqueue_job("generate_itinerary_plan", trip_request_id="...")

流程：
  1. 查 TripRequest + TripProfile（若无 profile 则先 normalize）
  2. 调用 planner.generate_plan(session, trip_request_id)
  3. 更新 TripRequest.status = "done"
  4. 返回摘要
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import select

from app.db.models.business import TripProfile, TripRequest
from app.db.session import AsyncSessionLocal
from app.domains.trip_core.planner import generate_plan

logger = logging.getLogger(__name__)


async def generate_itinerary_plan(
    ctx: dict,
    trip_request_id: str,
) -> dict[str, Any]:
    """
    arq Job：为指定行程生成详细行程方案。

    Args:
        ctx:              arq context
        trip_request_id:  UUID 字符串

    Returns:
        {
            "trip_request_id": str,
            "plan_id": str,
            "total_days": int,
            "status": "done" | "failed",
            "error": str | None,
        }
    """
    job_id = ctx.get("job_id", "manual")
    logger.info("generate_itinerary_plan START | job_id=%s trip=%s", job_id, trip_request_id)

    try:
        req_uuid = uuid.UUID(trip_request_id)
    except ValueError as exc:
        logger.error("Invalid trip_request_id: %s", trip_request_id)
        return {"trip_request_id": trip_request_id, "status": "failed", "error": str(exc)}

    async with AsyncSessionLocal() as session:
        try:
            # ── 校验 TripRequest 状态 ─────────────────────────────────────────
            req_result = await session.execute(
                select(TripRequest).where(TripRequest.trip_request_id == req_uuid)
            )
            trip_req = req_result.scalar_one_or_none()
            if trip_req is None:
                raise ValueError(f"TripRequest not found: {trip_request_id}")

            # ── 若缺少 TripProfile，先做 normalize ──────────────────────────
            profile_result = await session.execute(
                select(TripProfile).where(TripProfile.trip_request_id == req_uuid)
            )
            profile = profile_result.scalar_one_or_none()

            if profile is None:
                logger.info("No TripProfile found, running normalize inline ...")
                from app.domains.intake.intent_parser import normalize_trip_profile
                profile = await normalize_trip_profile(session, trip_request_id)
                if profile is None:
                    raise ValueError("normalize_trip_profile returned None")

            # ── 生成行程方案 ──────────────────────────────────────────────────
            plan = await generate_plan(session, trip_request_id)
            await session.commit()

            total_days = plan.plan_metadata.get("total_days", 0) if plan.plan_metadata else 0
            logger.info(
                "generate_itinerary_plan DONE | trip=%s plan_id=%s days=%d",
                trip_request_id, plan.plan_id, total_days,
            )
            return {
                "trip_request_id": trip_request_id,
                "plan_id": str(plan.plan_id),
                "total_days": total_days,
                "status": "done",
                "error": None,
            }

        except Exception as exc:
            await session.rollback()
            logger.exception("generate_itinerary_plan FAILED | trip=%s error=%s", trip_request_id, exc)
            # 将 TripRequest 标记为 failed
            try:
                async with AsyncSessionLocal() as err_session:
                    r = await err_session.execute(
                        select(TripRequest).where(TripRequest.trip_request_id == req_uuid)
                    )
                    t = r.scalar_one_or_none()
                    if t:
                        t.status = "failed"
                        await err_session.commit()
            except Exception:
                pass

            return {
                "trip_request_id": trip_request_id,
                "plan_id": None,
                "total_days": 0,
                "status": "failed",
                "error": str(exc),
            }
