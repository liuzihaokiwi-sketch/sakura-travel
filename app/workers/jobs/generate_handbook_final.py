"""
arq Job: generate_handbook_final

v2 新流程第二步：budget_confirm 后触发，调 Opus 餐厅装配，
将完整方案写入新 TripVersion.plan_data，状态改为 handbook_ready。
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import select

from app.db.session import AsyncSessionLocal as async_session_factory
from app.db.models.business import TripProfile, TripRequest, TripVersion

logger = logging.getLogger(__name__)


async def generate_handbook_final(
    ctx: dict,
    *,
    trip_request_id: str,
) -> dict[str, Any]:
    """
    arq Job: 生成最终手账本（v2 流程）。
    调用链：TripVersion(plan_preview) + budget_profile → OpusAssembler.step2 → TripVersion(final)
    """
    trip_id = uuid.UUID(trip_request_id)
    logger.info("generate_handbook_final 开始 trip=%s", trip_id)

    async with async_session_factory() as session:
        trip = await session.get(TripRequest, trip_id)
        if trip is None:
            logger.error("trip_request_id=%s not found", trip_id)
            return {"status": "error", "reason": "trip not found"}

        if trip.status != "budget_confirmed":
            logger.warning(
                "generate_handbook_final: trip=%s 状态异常 status=%s",
                trip_id, trip.status,
            )
            return {"status": "error", "reason": f"unexpected status: {trip.status}"}

        # 从最新 TripVersion 读 plan_preview
        version_result = await session.execute(
            select(TripVersion)
            .where(TripVersion.trip_request_id == trip_id)
            .order_by(TripVersion.version_number.desc())
            .limit(1)
        )
        latest_version = version_result.scalar_one_or_none()

        if not latest_version or not latest_version.plan_data:
            logger.error("plan_preview TripVersion 缺失 trip=%s", trip_id)
            trip.status = "failed"
            trip.last_job_error = "plan_preview_version_missing"
            await session.commit()
            return {"status": "error", "reason": "plan_preview version missing"}

        plan_preview = latest_version.plan_data

        profile_result = await session.execute(
            select(TripProfile).where(TripProfile.trip_request_id == trip_id)
        )
        profile = profile_result.scalar_one_or_none()
        if not profile:
            logger.error("TripProfile 缺失 trip=%s", trip_id)
            trip.status = "failed"
            trip.last_job_error = "trip_profile_missing"
            await session.commit()
            return {"status": "error", "reason": "trip profile missing"}

        constraints = dict(trip.raw_input or {})

        try:
            from app.domains.templates.loader import get_template_loader
            from app.domains.planning_v2.opus_assembler import assemble_restaurants
            from app.domains.planning_v2.budget_calculator import calculate_budget

            loader = get_template_loader()
            policy = loader.load_policy()

            daily_plans = plan_preview.get("daily_plans", [])
            involved_cities = list({dp["city"] for dp in daily_plans if dp.get("city")})
            city_restaurants_map: dict[str, dict] = {}
            for city in involved_cities:
                try:
                    city_restaurants_map[city] = loader.load_city_restaurants(city)
                except Exception:
                    city_restaurants_map[city] = {}

            budget_profile = {
                "dining_tier": profile.dining_tier or "local_good",
                "dining_preference": profile.dining_preference,
                "hotel_tier": profile.hotel_tier or "comfort",
                "hotel_preferences": profile.hotel_preferences or [],
                "comfort_addons": profile.comfort_addons or {},
            }

            enriched_plans = await assemble_restaurants(
                daily_plans=daily_plans,
                constraints=constraints,
                city_restaurants_map=city_restaurants_map,
                budget_profile=budget_profile,
                policy=policy,
            )

            party = constraints.get("party", {"adults": 2, "children": 0, "elderly": 0})
            budget_estimate = calculate_budget(
                plan=plan_preview,
                dining_tier=budget_profile["dining_tier"],
                hotel_tier=budget_profile["hotel_tier"],
                party=party,
                comfort_addons=budget_profile["comfort_addons"],
            )

            final_plan_data = {
                **plan_preview,
                "type": "final_plan",
                "daily_plans": enriched_plans,
                "budget_estimate": budget_estimate,
                "assembled_by": "opus",
            }

            final_version = TripVersion(
                trip_request_id=trip_id,
                version_number=latest_version.version_number + 1,
                change_reason="budget_confirmed",
                plan_data=final_plan_data,
            )
            session.add(final_version)

            trip.status = "handbook_ready"
            await session.commit()

            logger.info(
                "generate_handbook_final 完成 trip=%s version=%d",
                trip_id, final_version.version_number,
            )
            return {
                "status": "ok",
                "trip_request_id": trip_request_id,
                "version": final_version.version_number,
                "budget_total": budget_estimate.get("total_per_person"),
            }

        except Exception as exc:
            logger.exception("generate_handbook_final 失败 trip=%s: %s", trip_id, exc)
            trip.status = "failed"
            trip.last_job_error = f"handbook_final_failed:{exc}"
            await session.commit()
            return {"status": "error", "reason": str(exc)}
