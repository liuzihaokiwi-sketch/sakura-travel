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


# ── 城市圈决策层信号推导 ──────────────────────────────────────────────────────

_CELEBRATION_KEYWORDS = {
    "生日": "birthday", "birthday": "birthday",
    "纪念日": "anniversary", "anniversary": "anniversary",
    "求婚": "proposal", "proposal": "proposal",
    "蜜月": "honeymoon", "honeymoon": "honeymoon",
    "毕业": "graduation", "graduation": "graduation",
}


def _derive_circle_signals(
    raw: dict,
    cities: list[dict],
    duration_days: int,
    tags: dict,
) -> dict:
    """
    从 raw_input 推导城市圈决策链路所需的信号。

    返回一个 dict，包含一等字段值和 special_requirements 扩充。
    """
    result: dict[str, Any] = {}
    special = dict(raw.get("special_requirements") or {})
    must_visit_places = raw.get("must_visit_places") or []
    if isinstance(must_visit_places, list):
        special["must_visit_places"] = [
            str(x).strip() for x in must_visit_places if isinstance(x, str) and str(x).strip()
        ]
    raw_special_needs = raw.get("special_needs")
    if isinstance(raw_special_needs, dict):
        special.update(raw_special_needs)

    # ── 航班 / 机场 ──
    flight = raw.get("flight_info") or {}
    outbound = flight.get("outbound") or {}
    ret = flight.get("return") or {}

    result["arrival_airport"] = outbound.get("airport") or raw.get("arrival_airport", "")
    result["departure_airport"] = ret.get("airport") or raw.get("departure_airport", "")
    result["last_flight_time"] = ret.get("depart_time", "")

    # arrival_shape: 同城 vs 开口程
    arr_ap = result["arrival_airport"].upper()
    dep_ap = result["departure_airport"].upper()
    if arr_ap and dep_ap:
        result["arrival_shape"] = "same_city" if arr_ap == dep_ap else "open_jaw"
        result["departure_shape"] = result["arrival_shape"]
    else:
        result["arrival_shape"] = "same_city"
        result["departure_shape"] = "same_city"

    # arrival_day_shape: 根据到达时间
    arrive_time = outbound.get("arrive_time", outbound.get("arrive", ""))
    result["arrival_day_shape"] = _infer_day_shape_arrival(arrive_time)

    # departure_day_shape: 根据出发时间
    depart_time = ret.get("depart_time", ret.get("depart", ""))
    result["departure_day_shape"] = _infer_day_shape_departure(depart_time)

    # ── 容忍度推导 ──
    party_type = raw.get("party_type", "couple")
    pace = raw.get("pace", "moderate")
    has_elderly = raw.get("has_elderly", False) or bool(raw.get("special_needs", {}).get("wheelchair"))
    has_children = raw.get("has_children", False)
    children_ages = raw.get("children_ages", [])
    min_child_age = min(children_ages) if children_ages else 99

    # daytrip_tolerance
    if has_elderly or (has_children and min_child_age < 5):
        result["daytrip_tolerance"] = "low"
    elif pace == "packed" and party_type in ("solo", "friends"):
        result["daytrip_tolerance"] = "high"
    else:
        result["daytrip_tolerance"] = "medium"

    # hotel_switch_tolerance
    accom = raw.get("accommodation_pref") or {}
    if has_elderly or (has_children and min_child_age < 3):
        result["hotel_switch_tolerance"] = "low"
    elif accom.get("prefer_single_hotel"):
        result["hotel_switch_tolerance"] = "low"
    elif duration_days <= 3:
        result["hotel_switch_tolerance"] = "low"
    elif pace == "packed":
        result["hotel_switch_tolerance"] = "high"
    else:
        result["hotel_switch_tolerance"] = "medium"

    # ── celebration_flags（从 free_text_wishes 提取）──
    wishes = raw.get("free_text_wishes", "")
    celebrations = []
    if wishes:
        wishes_lower = wishes.lower()
        for keyword, flag in _CELEBRATION_KEYWORDS.items():
            if keyword in wishes_lower:
                celebrations.append(flag)
    if celebrations:
        special["celebration_flags"] = list(set(celebrations))

    # ── mobility_notes ──
    mobility = []
    if has_elderly:
        mobility.append("slow_pace")
    if has_children and min_child_age < 5:
        mobility.append("stroller_needed")
    if raw.get("special_needs", {}).get("wheelchair"):
        mobility.append("accessible_only")
    if mobility:
        special["mobility_notes"] = mobility

    # ── queue_tolerance ──
    if pace == "packed" and not has_elderly:
        special["queue_tolerance"] = "high"
    elif pace == "relaxed" or has_elderly:
        special["queue_tolerance"] = "low"
    else:
        special["queue_tolerance"] = "medium"

    # ── weather_risk_tolerance ──
    travel_month = None
    start = raw.get("travel_start_date", "")
    if start and len(start) >= 7:
        try:
            travel_month = int(start[5:7])
        except ValueError:
            pass
    rainy_months = {6, 7, 8, 9}
    if travel_month in rainy_months and (has_children or has_elderly):
        special["weather_risk_tolerance"] = "low"
    elif party_type == "solo" and pace == "packed":
        special["weather_risk_tolerance"] = "high"
    else:
        special["weather_risk_tolerance"] = "medium"

    # ── priority 推导（从 must_have_tags 计数）──
    must_tags = set(t.lower() for t in tags.get("must_have", []))
    food_tags = {"food", "foodie", "ramen", "sushi", "wagyu", "local_cuisine"}
    photo_tags = {"photo", "photo_spot", "scenic", "instagram"}
    shopping_tags = {"shopping", "market", "department_store"}
    if must_tags & food_tags:
        special["food_priority"] = "high"
    if must_tags & photo_tags:
        special["photo_priority"] = "high"
    if must_tags & shopping_tags:
        special["shopping_priority"] = "high"

    result["special_requirements"] = special
    return result


def _infer_day_shape_arrival(arrive_time: str) -> str:
    """从到达时间推断到达日形态。"""
    if not arrive_time:
        return "half_day_afternoon"
    try:
        hour = int(arrive_time.split(":")[0])
        if hour < 12:
            return "full_day"
        elif hour < 17:
            return "half_day_afternoon"
        elif hour < 22:
            return "evening_only"
        else:
            return "red_eye"
    except (ValueError, IndexError):
        return "half_day_afternoon"


def _infer_day_shape_departure(depart_time: str) -> str:
    """从离开航班时间推断离开日形态。"""
    if not depart_time:
        return "half_day_morning"
    try:
        hour = int(depart_time.split(":")[0])
        if hour >= 18:
            return "full_day"
        elif hour >= 12:
            return "half_day_morning"
        else:
            return "early_morning"
    except (ValueError, IndexError):
        return "half_day_morning"


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
        duration_days = int(raw.get("duration_days") or 0)
        if duration_days <= 0:
            duration_days = sum(c.get("nights", 1) for c in cities) + 1  # +1 for arrival day

        # 构建 travel_dates
        travel_dates = None
        if raw.get("travel_start_date"):
            travel_dates = {"start": raw["travel_start_date"]}
            if raw.get("travel_end_date"):
                travel_dates["end"] = raw["travel_end_date"]

        # ── 城市圈决策层新增推导 ──
        derived = _derive_circle_signals(raw, cities, duration_days, tags)

        profile_q = await session.execute(
            select(TripProfile).where(TripProfile.trip_request_id == uuid.UUID(trip_request_id))
        )
        profile = profile_q.scalar_one_or_none()
        if profile is None:
            profile = TripProfile(trip_request_id=uuid.UUID(trip_request_id))
            session.add(profile)

        profile.cities = [{"city_code": c["city_code"], "nights": c["nights"]} for c in cities]
        profile.travel_dates = travel_dates
        profile.duration_days = duration_days
        profile.party_type = raw.get("party_type", "couple")
        profile.party_size = raw.get("party_size", 2)
        profile.budget_level = raw.get("budget_level", "mid")
        profile.budget_total_cny = raw.get("budget_total_cny")
        profile.budget_focus = raw.get("budget_focus")
        profile.must_have_tags = tags["must_have"]
        profile.nice_to_have_tags = tags["nice_to_have"]
        profile.avoid_tags = tags["avoid"]
        profile.special_requirements = derived["special_requirements"]

        # 城市圈决策层一等字段
        profile.arrival_shape = derived.get("arrival_shape")
        profile.departure_shape = derived.get("departure_shape")
        profile.arrival_airport = derived.get("arrival_airport")
        profile.departure_airport = derived.get("departure_airport")
        profile.last_flight_time = derived.get("last_flight_time")
        profile.arrival_day_shape = derived.get("arrival_day_shape")
        profile.departure_day_shape = derived.get("departure_day_shape")
        profile.daytrip_tolerance = derived.get("daytrip_tolerance")
        profile.hotel_switch_tolerance = derived.get("hotel_switch_tolerance")
        profile.pace = raw.get("pace")
        profile.wake_up_time = raw.get("wake_up_time")
        profile.accommodation_pref = raw.get("accommodation_pref")
        profile.flight_info = raw.get("flight_info")

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
