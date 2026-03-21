from __future__ import annotations

"""
arq Worker entry point.

启动方式：
    python -m app.workers

arq 会从 WorkerSettings 读取 functions、redis_settings 等配置。
"""
import uuid
from typing import Any

from arq.connections import RedisSettings
from arq import cron
from sqlalchemy import select

from app.core.config import settings
from app.db.models.business import TripProfile, TripRequest
from app.db.session import AsyncSessionLocal
from app.workers.jobs.score_entities import score_entities
from app.workers.jobs.generate_plan import generate_itinerary_plan
from app.workers.jobs.generate_trip import generate_trip
from app.workers.jobs.run_guardrails import run_guardrails
from app.workers.jobs.render_export import render_export
from app.workers.jobs.scan_flight_prices import scan_flight_prices


# ── Job 推导规则 ───────────────────────────────────────────────────────────────

PARTY_TYPE_TAG_RULES: dict[str, dict[str, list[str]]] = {
    "family_child": {
        "must_have": ["family_friendly"],
        "avoid": ["crowded_narrow", "alcohol_focused"],
    },
    "senior": {
        "must_have": ["accessible", "low_physical_demand"],
        "avoid": ["extreme_activity"],
    },
    "solo": {
        "nice_to_have": ["budget_friendly", "solo_friendly"],
    },
    "couple": {
        "nice_to_have": ["romantic", "scenic"],
    },
}

BUDGET_TAG_RULES: dict[str, dict[str, list[str]]] = {
    "budget": {"must_have": ["budget_friendly"], "avoid": ["luxury_only"]},
    "luxury": {"nice_to_have": ["luxury", "premium_experience"]},
}

INTEREST_TAG_MAP: dict[str, list[str]] = {
    "culture": ["shrine", "temple", "museum", "traditional"],
    "food": ["foodie", "local_cuisine", "restaurant_dense"],
    "nature": ["park", "mountain", "garden", "scenic"],
    "shopping": ["shopping", "department_store", "market"],
    "anime": ["otaku", "anime", "akihabara_style"],
    "onsen": ["onsen", "hot_spring", "ryokan"],
    "nightlife": ["bar", "izakaya", "late_night"],
}


def derive_profile_tags(raw_input: dict) -> dict:
    """
    根据 raw_input 推导出标准化标签集合。
    返回 {must_have, nice_to_have, avoid} 三个列表。
    """
    must_have: list[str] = list(raw_input.get("must_have_tags", []))
    nice_to_have: list[str] = list(raw_input.get("nice_to_have_tags", []))
    avoid: list[str] = list(raw_input.get("avoid_tags", []))

    # 从 party_type 推导
    party_type = raw_input.get("party_type", "")
    if party_type in PARTY_TYPE_TAG_RULES:
        rules = PARTY_TYPE_TAG_RULES[party_type]
        must_have.extend(rules.get("must_have", []))
        nice_to_have.extend(rules.get("nice_to_have", []))
        avoid.extend(rules.get("avoid", []))

    # 从 budget_level 推导
    budget_level = raw_input.get("budget_level", "mid")
    if budget_level in BUDGET_TAG_RULES:
        rules = BUDGET_TAG_RULES[budget_level]
        must_have.extend(rules.get("must_have", []))
        nice_to_have.extend(rules.get("nice_to_have", []))
        avoid.extend(rules.get("avoid", []))

    # 从 interests 推导 nice_to_have
    for interest in raw_input.get("interests", []):
        if interest in INTEREST_TAG_MAP:
            nice_to_have.extend(INTEREST_TAG_MAP[interest])

    # 去重
    return {
        "must_have": list(dict.fromkeys(must_have)),
        "nice_to_have": list(dict.fromkeys(nice_to_have)),
        "avoid": list(dict.fromkeys(avoid)),
    }


# ── Job: normalize_trip_profile ────────────────────────────────────────────────

async def normalize_trip_profile(ctx: dict, trip_request_id: str) -> str:
    """
    从 trip_requests 读取 raw_input，标准化为 trip_profiles 并写库。
    状态流转：pending → normalizing → profiled（或 failed）
    """
    async with AsyncSessionLocal() as session:
        trip = await session.get(TripRequest, uuid.UUID(trip_request_id))
        if not trip:
            raise ValueError(f"TripRequest {trip_request_id} not found")

        # 更新状态为 normalizing
        trip.status = "normalizing"
        await session.commit()

    async with AsyncSessionLocal() as session:
        trip = await session.get(TripRequest, uuid.UUID(trip_request_id))

        raw = trip.raw_input
        tags = derive_profile_tags(raw)

        # 计算总天数
        cities = raw.get("cities", [])
        duration_days = sum(c.get("nights", 1) for c in cities) + 1  # +1 for arrival day

        # 构建 travel_dates
        travel_dates = None
        if raw.get("travel_start_date"):
            travel_dates = {"start": raw["travel_start_date"]}

        profile = TripProfile(
            trip_request_id=uuid.UUID(trip_request_id),
            cities=[{"city_code": c["city_code"], "nights": c["nights"]} for c in cities],
            travel_dates=travel_dates,
            duration_days=duration_days,
            party_type=raw.get("party_type", "couple"),
            party_size=raw.get("party_size", 2),
            budget_level=raw.get("budget_level", "mid"),
            must_have_tags=tags["must_have"],
            nice_to_have_tags=tags["nice_to_have"],
            avoid_tags=tags["avoid"],
            special_requirements=raw.get("special_requirements"),
        )
        session.add(profile)

        trip.status = "profiled"
        trip.last_job_error = None
        await session.commit()

    return f"profiled:{trip_request_id}"


# ── Worker Settings ────────────────────────────────────────────────────────────

class WorkerSettings:
    """arq Worker 配置入口。"""

    functions = [
        normalize_trip_profile,
        score_entities,
        generate_itinerary_plan,
        generate_trip,
        run_guardrails,
        render_export,
        scan_flight_prices,
    ]

    # 定时任务：每6小时扫描一次机票特价（6/12/18/0点）
    cron_jobs = [
        cron(scan_flight_prices, hour={0, 6, 12, 18}, minute=0, timeout=600),
    ]

    redis_settings = RedisSettings.from_dsn(settings.redis_url)

    # 最大并发 job 数
    max_jobs = settings.worker_max_jobs

    # 失败重试策略
    retry_jobs = True
    max_tries = settings.job_retry_max

    # 健康检查间隔（秒）
    health_check_interval = 30

    # 启动/关闭钩子（可扩展）
    on_startup = None
    on_shutdown = None


if __name__ == "__main__":
    import asyncio
    from arq import run_worker

    # Python 3.14+ 不再自动创建 event loop，需要手动设置
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    run_worker(WorkerSettings)
