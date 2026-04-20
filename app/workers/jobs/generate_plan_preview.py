"""
arq Job: generate_plan_preview

v2 新流程第一步：接收 trip_request_id，调 Opus 装配（路线+日模板+酒店），
将结果写入 TripVersion.plan_data，状态改为 plan_preview。
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import date
from pathlib import Path
from typing import Any

from app.db.session import AsyncSessionLocal as async_session_factory
from app.db.models.business import TripRequest, TripVersion

logger = logging.getLogger(__name__)

_ASSEMBLY_RULES_PATH = Path(__file__).resolve().parents[3] / "content" / "kansai" / "assembly_rules.json"


async def generate_plan_preview(
    ctx: dict,
    *,
    trip_request_id: str,
) -> dict[str, Any]:
    """
    arq Job: 生成预览方案（v2 流程）。
    调用链：TripRequest → OpusAssembler.step1 → TripVersion.plan_data
    """
    trip_id = uuid.UUID(trip_request_id)
    logger.info("generate_plan_preview 开始 trip=%s", trip_id)

    async with async_session_factory() as session:
        trip = await session.get(TripRequest, trip_id)
        if trip is None:
            logger.error("trip_request_id=%s not found", trip_id)
            return {"status": "error", "reason": "trip not found"}

        constraints = dict(trip.raw_input or {})

        try:
            from app.domains.templates.loader import get_template_loader
            from app.domains.planning_v2.opus_assembler import assemble_route_and_hotels

            loader = get_template_loader()
            policy = loader.load_policy()

            assembly_rules = (
                json.loads(_ASSEMBLY_RULES_PATH.read_text(encoding="utf-8"))
                if _ASSEMBLY_RULES_PATH.exists()
                else {"rules": []}
            )

            cities = loader.list_cities()
            city_days_map: dict[str, dict] = {}
            city_hotels_map: dict[str, dict] = {}
            for city in cities:
                city_days_map[city] = loader.load_city_days(city)
                try:
                    city_hotels_map[city] = loader.load_city_hotels(city)
                except Exception:
                    city_hotels_map[city] = {}

            step1 = await assemble_route_and_hotels(
                constraints=constraints,
                policy=policy,
                assembly_rules=assembly_rules,
                city_days_map=city_days_map,
                city_hotels_map=city_hotels_map,
            )

            plan_data = {
                "type": "plan_preview",
                "total_days": _count_total_days(constraints),
                "effective_days": len(step1.get("daily_plans", [])),
                "city_allocation": step1.get("city_allocation", []),
                "hotel_selections": step1.get("hotel_selections", {}),
                "daily_plans": step1.get("daily_plans", []),
                "decisions": step1.get("decisions", []),
                "addable_experiences": step1.get("addable_experiences", []),
                "condition_summary": step1.get("condition_summary", ""),
                "note": (
                    "这是第一版主线。确认后手账本会补齐每天的餐厅推荐、店铺、"
                    "咖啡厅、拍照点和实用小技巧。下一步可以选择吃住的舒适度和预算。"
                ),
                "validation": {"hard_pass": True, "warnings": []},
                "assembled_by": "opus",
            }

            version = TripVersion(
                trip_request_id=trip_id,
                version_number=1,
                change_reason="initial",
                plan_data=plan_data,
            )
            session.add(version)

            trip.status = "plan_preview"
            await session.commit()

            logger.info(
                "generate_plan_preview 完成 trip=%s days=%d cities=%d",
                trip_id,
                len(plan_data["daily_plans"]),
                len(plan_data["city_allocation"]),
            )
            return {
                "status": "ok",
                "trip_request_id": trip_request_id,
                "days": len(plan_data["daily_plans"]),
            }

        except Exception as exc:
            logger.exception("generate_plan_preview 失败 trip=%s: %s", trip_id, exc)
            trip.status = "failed"
            trip.last_job_error = f"plan_preview_failed:{exc}"
            await session.commit()
            return {"status": "error", "reason": str(exc)}


def _count_total_days(constraints: dict) -> int:
    try:
        dates = constraints.get("dates", {})
        start = date.fromisoformat(dates["start"])
        end = date.fromisoformat(dates["end"])
        return (end - start).days + 1
    except Exception:
        return 0
