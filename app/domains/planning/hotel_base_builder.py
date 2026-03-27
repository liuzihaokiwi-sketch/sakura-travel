from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.business import TripProfile
from app.db.models.city_circles import HotelStrategyPreset
from app.domains.planning.policy_resolver import ResolvedPolicySet

if TYPE_CHECKING:
    from app.domains.planning.constraint_compiler import PlanningConstraints

logger = logging.getLogger(__name__)


@dataclass
class HotelBase:
    base_city: str
    area: str = ""
    nights: int = 1
    served_cluster_ids: list[str] = field(default_factory=list)
    switch_cost_minutes: int = 0
    switch_reason_code: str = ""


@dataclass
class HotelExplain:
    why_selected: str = ""
    expected_tradeoff: str = ""
    fallback_hint: str = ""
    coverage_detail: str = ""


@dataclass
class HotelStrategyResult:
    preset_id: Optional[int] = None
    preset_name: str = ""
    bases: list[HotelBase] = field(default_factory=list)
    total_nights: int = 0
    switch_count: int = 0
    last_night_safe: bool = True
    last_night_airport_minutes: Optional[int] = None
    override_allowed: bool = True
    trace: list[str] = field(default_factory=list)
    explain: HotelExplain = field(default_factory=HotelExplain)
    policy_summary: dict[str, Any] = field(default_factory=dict)


async def build_hotel_strategy(
    session: AsyncSession,
    circle_id: str,
    profile: TripProfile,
    selected_cluster_ids: list[str],
    resolved_policy: ResolvedPolicySet | None = None,
    constraints: "PlanningConstraints | None" = None,
) -> HotelStrategyResult:
    result = HotelStrategyResult()
    days = profile.duration_days or 5
    result.policy_summary = _policy_summary(resolved_policy)

    q = await session.execute(
        select(HotelStrategyPreset).where(
            and_(
                HotelStrategyPreset.circle_id == circle_id,
                HotelStrategyPreset.is_active == True,
            )
        ).order_by(HotelStrategyPreset.priority)
    )
    presets = q.scalars().all()

    if not presets:
        result.trace.append(f"circle={circle_id} no preset, fallback to default single base")
        return _build_default_strategy(profile, result, resolved_policy=resolved_policy)

    best_score = -10_000.0
    best_preset: Optional[HotelStrategyPreset] = None
    for preset in presets:
        score = _score_preset(
            preset,
            profile,
            selected_cluster_ids,
            days,
            resolved_policy=resolved_policy,
            constraints=constraints,
        )
        result.trace.append(
            "preset="
            f"{preset.name_zh} score={score:.2f} days={preset.min_days}-{preset.max_days} "
            f"bases={len(preset.bases or [])} switches={preset.switch_count}"
        )
        if score > best_score:
            best_score = score
            best_preset = preset

    if best_preset is None:
        result.trace.append("no matching preset, fallback to default strategy")
        return _build_default_strategy(profile, result, resolved_policy=resolved_policy)

    result.preset_id = best_preset.preset_id
    result.preset_name = best_preset.name_zh
    result.switch_count = best_preset.switch_count
    result.last_night_airport_minutes = best_preset.last_night_airport_minutes
    result.bases = _allocate_bases(best_preset, days)
    result.total_nights = sum(base.nights for base in result.bases)
    result.last_night_safe = _check_last_night_safety(
        best_preset.last_night_airport_minutes,
        profile.last_flight_time,
        required_buffer_minutes=(
            resolved_policy.mobility_policy.last_night_airport_buffer_minutes
            if resolved_policy is not None
            else 180
        ),
    )

    for idx, base in enumerate(result.bases):
        if idx == 0:
            continue
        base.switch_reason_code = "area_change"
        base.switch_cost_minutes = best_preset.switch_cost_minutes // max(1, result.switch_count)

    result.trace.append(
        f"selected={result.preset_name} bases={len(result.bases)} "
        f"switches={result.switch_count} last_night_safe={result.last_night_safe}"
    )
    if result.policy_summary:
        result.trace.append(
            "policy_hotel_base="
            f"{result.policy_summary.get('base_pattern_bias')} "
            f"hub={result.policy_summary.get('prefer_last_night_near_hub')} "
            f"route_node={result.policy_summary.get('long_segment_base_preference')}"
        )

    _record_constraint_consumption(
        constraints=constraints,
        profile=profile,
        result=result,
    )

    base_summary = " -> ".join(f"{b.base_city}({b.nights}n)" for b in result.bases)
    result.explain = HotelExplain(
        why_selected=f"selected [{result.preset_name}]: {base_summary}",
        expected_tradeoff=(
            f"hotel switches {result.switch_count}"
            + (
                ""
                if result.last_night_safe
                else f", last night to airport {result.last_night_airport_minutes}min is tight"
            )
        ),
        coverage_detail=f"covers {sum(len(b.served_cluster_ids) for b in result.bases)} selected clusters",
        fallback_hint="manual override allowed" if result.override_allowed else "",
    )
    return result


def _allocate_bases(preset: HotelStrategyPreset, days: int) -> list[HotelBase]:
    total_nights = max(1, days - 1)
    raw_bases = preset.bases or []
    base_ranges: list[tuple[dict[str, Any], int, int]] = []
    for base_data in raw_bases:
        nights_range = base_data.get("nights_range", "")
        fixed_nights = base_data.get("nights")
        if isinstance(nights_range, str) and "-" in nights_range:
            lo, hi = nights_range.split("-", 1)
            base_ranges.append((base_data, int(lo), int(hi)))
        elif fixed_nights:
            fixed = int(fixed_nights)
            base_ranges.append((base_data, fixed, fixed))
        else:
            base_ranges.append((base_data, 1, total_nights))

    min_total = sum(lo for _, lo, _ in base_ranges)
    remainder = max(0, total_nights - min_total)
    bases: list[HotelBase] = []
    for base_data, lo, hi in base_ranges:
        extra = min(max(0, hi - lo), remainder)
        nights = lo + extra
        remainder -= extra
        bases.append(
            HotelBase(
                base_city=base_data.get("base_city", ""),
                area=base_data.get("area", ""),
                nights=nights,
                served_cluster_ids=list(base_data.get("served_cluster_ids", []) or []),
            )
        )

    if bases and sum(base.nights for base in bases) < total_nights:
        bases[-1].nights += total_nights - sum(base.nights for base in bases)
    return bases


def _score_preset(
    preset: HotelStrategyPreset,
    profile: TripProfile,
    selected_cluster_ids: list[str],
    days: int,
    *,
    resolved_policy: ResolvedPolicySet | None = None,
    constraints: "PlanningConstraints | None" = None,
) -> float:
    if days < preset.min_days or days > preset.max_days:
        return -100.0

    score = 0.0
    party = (profile.party_type or "").lower()
    budget = (profile.budget_level or "").lower()
    party_match = 1.0 if party in {str(x).lower() for x in (preset.fit_party_types or [])} else 0.3
    budget_match = 1.0 if budget in {str(x).lower() for x in (preset.fit_budget_levels or [])} else 0.4
    score += (party_match * 0.5 + budget_match * 0.5) * 30

    if selected_cluster_ids:
        all_served = set()
        for base_data in preset.bases or []:
            all_served.update(base_data.get("served_cluster_ids", []) or [])
        covered = len(set(selected_cluster_ids) & all_served)
        score += (covered / len(selected_cluster_ids)) * 40

    switch_tolerance = (profile.hotel_switch_tolerance or "medium").lower()
    switch_count = preset.switch_count or 0
    if switch_tolerance == "low":
        switch_score = max(0.0, 1.0 - switch_count * 0.5)
    elif switch_tolerance == "high":
        switch_score = 0.8
    else:
        switch_score = max(0.0, 1.0 - switch_count * 0.3)
    score += switch_score * 20

    profile_cities = {c.get("city_code", "").lower() for c in (getattr(profile, "cities", None) or []) if isinstance(c, dict)}
    preset_base_cities = {(b.get("base_city", "") or "").lower() for b in (preset.bases or [])}
    if len(profile_cities) >= 2:
        city_overlap = len(profile_cities & preset_base_cities) / max(1, len(profile_cities))
        score += city_overlap * 15
    elif len(preset_base_cities) == 1 and preset_base_cities & profile_cities:
        score += 15

    priority_bonus = max(0.0, (100 - (preset.priority or 50)) / 100)
    score += priority_bonus * 10

    if resolved_policy is not None:
        policy = resolved_policy.hotel_base_policy
        score += _score_base_pattern_bias(
            base_count=len(preset.bases or []),
            bias=policy.base_pattern_bias,
            switch_tolerance=switch_tolerance,
            city_count=len(profile_cities),
        )
        if policy.prefer_last_night_near_hub:
            airport_minutes = preset.last_night_airport_minutes or 999
            if airport_minutes <= policy.last_night_hub_max_minutes:
                score += 12
            else:
                score -= min(12.0, (airport_minutes - policy.last_night_hub_max_minutes) / 10)
        if policy.long_segment_base_preference == "route_node":
            score += _score_route_node_fit(preset) * max(0.0, policy.route_node_bias_weight) * 10

    if constraints and constraints.must_stay_area:
        target = constraints.must_stay_area.lower()
        if any((base.get("area", "") or "").lower() == target for base in (preset.bases or [])):
            score += 18
        else:
            score -= 4

    booked_items = getattr(profile, "booked_items", None) or []
    if booked_items:
        score += _score_booked_hotel_alignment(preset, booked_items)

    return score


def _score_base_pattern_bias(
    *,
    base_count: int,
    bias: str,
    switch_tolerance: str,
    city_count: int,
) -> float:
    if bias == "single_base":
        score = 10 if base_count == 1 else -6 * max(0, base_count - 1)
    elif bias == "double_base":
        score = 12 if base_count == 2 else 6 if base_count == 1 else 8 - abs(base_count - 2) * 4
    elif bias == "multi_base":
        score = 12 if base_count >= 3 else 8 if base_count == 2 else -8
    else:
        score = 0

    if switch_tolerance == "low" and base_count >= 3:
        score -= 6
    if city_count >= 3 and base_count >= 2:
        score += 4
    return score


def _score_route_node_fit(preset: HotelStrategyPreset) -> float:
    bases = preset.bases or []
    if not bases:
        return 0.0
    served_counts = [len(base.get("served_cluster_ids", []) or []) for base in bases]
    avg_served = sum(served_counts) / max(1, len(served_counts))
    if len(bases) >= 3:
        return 1.0 if avg_served <= 2.5 else 0.6
    if len(bases) == 2:
        return 0.6 if avg_served <= 3.0 else 0.2
    return -0.4


def _score_booked_hotel_alignment(preset: HotelStrategyPreset, booked_items: list[Any]) -> float:
    matched = 0
    preset_areas = {
        (base.get("area", "") or base.get("base_city", "") or "").lower()
        for base in (preset.bases or [])
    }
    preset_cities = {(base.get("base_city", "") or "").lower() for base in (preset.bases or [])}
    for item in booked_items:
        if not isinstance(item, dict):
            continue
        item_type = str(item.get("item_type") or item.get("type") or "").lower()
        if item_type and "hotel" not in item_type:
            continue
        item_area = str(item.get("area") or item.get("hotel_area") or "").lower()
        item_city = str(item.get("city_code") or item.get("city") or "").lower()
        if item_area and item_area in preset_areas:
            matched += 1
        elif item_city and item_city in preset_cities:
            matched += 1
    return matched * 8.0


def _record_constraint_consumption(
    *,
    constraints: "PlanningConstraints | None",
    profile: TripProfile,
    result: HotelStrategyResult,
) -> None:
    if constraints is None:
        return
    constraints.record_consumption(
        "policy_hotel_base",
        "hotel_base_builder",
        "preset_selected",
        f"selected={result.preset_name or 'default'} bases={len(result.bases)}",
    )
    if constraints.must_stay_area:
        constraints.record_consumption(
            "must_stay_area",
            "hotel_base_builder",
            "area_bias_applied",
            f"target={constraints.must_stay_area} selected={[b.area or b.base_city for b in result.bases]}",
        )
    booked_items = getattr(profile, "booked_items", None) or []
    if booked_items:
        constraints.record_consumption(
            "booked_items",
            "hotel_base_builder",
            "booked_items_checked",
            f"checked {len(booked_items)} booked items",
        )


def _check_last_night_safety(
    airport_minutes: Optional[int],
    flight_time: Optional[str],
    *,
    required_buffer_minutes: int = 180,
) -> bool:
    if not airport_minutes or not flight_time:
        return True

    try:
        parts = flight_time.split(":")
        flight_hour = int(parts[0])
        flight_min = int(parts[1]) if len(parts) > 1 else 0
        flight_total_min = flight_hour * 60 + flight_min
        needed_departure_min = flight_total_min - required_buffer_minutes
        departure_time_min = 8 * 60 + airport_minutes
        return departure_time_min <= needed_departure_min
    except (TypeError, ValueError):
        return True


def _build_default_strategy(
    profile: TripProfile,
    result: HotelStrategyResult,
    *,
    resolved_policy: ResolvedPolicySet | None = None,
) -> HotelStrategyResult:
    days = profile.duration_days or 5
    city_codes = [c.get("city_code", "") for c in (profile.cities or []) if isinstance(c, dict)]
    base_city = city_codes[0] if city_codes else "unknown"
    result.bases = [HotelBase(base_city=base_city, nights=max(1, days - 1))]
    result.total_nights = max(1, days - 1)
    result.switch_count = 0
    result.last_night_safe = True
    result.policy_summary = _policy_summary(resolved_policy)
    result.trace.append(f"default_single_base={base_city} nights={max(1, days - 1)}")
    result.explain = HotelExplain(
        why_selected=f"no preset matched, default single base {base_city} ({max(1, days - 1)} nights)",
        expected_tradeoff="single base strategy, no hotel switching",
    )
    return result


def _policy_summary(resolved_policy: ResolvedPolicySet | None) -> dict[str, Any]:
    if resolved_policy is None:
        return {}
    policy = resolved_policy.hotel_base_policy
    return {
        "base_pattern_bias": policy.base_pattern_bias,
        "prefer_last_night_near_hub": policy.prefer_last_night_near_hub,
        "long_segment_base_preference": policy.long_segment_base_preference,
        "route_node_bias_weight": policy.route_node_bias_weight,
    }
