from __future__ import annotations

import logging
import uuid as _uuid
from dataclasses import dataclass, field
from typing import Any

from app.domains.planning.policy_resolver import ResolvedPolicySet, resolve_policy_set

logger = logging.getLogger(__name__)

COMPILER_VERSION = "2.2.0"


@dataclass
class ConstraintTraceItem:
    constraint_name: str
    source_inputs: str
    compiled_value: str
    strength: str = "hard"
    intended_consumers: list[str] = field(default_factory=list)
    consumption_events: list[dict] = field(default_factory=list)
    final_status: str = "pending"
    ignored_reason: str = ""


@dataclass
class PlanningConstraints:
    blocked_tags: set[str] = field(default_factory=set)
    blocked_clusters: set[str] = field(default_factory=set)
    visited_clusters: set[str] = field(default_factory=set)
    must_go_clusters: set[str] = field(default_factory=set)
    avoid_cuisines: set[str] = field(default_factory=set)
    max_intensity: int = 2
    must_stay_cities: set[str] = field(default_factory=set)
    must_stay_area: str = ""
    city_strict_day_types: set[str] = field(default_factory=lambda: {"theme_park", "arrival", "departure"})
    party_block_tags: set[str] = field(default_factory=set)
    departure_day_no_poi: bool = True
    departure_meal_window: str = "breakfast_only"
    arrival_evening_only: bool = False
    preferred_tags_boost: dict[str, float] = field(default_factory=dict)
    party_fit_penalty: float = 0.0
    max_majors_per_day: int = 1
    max_transfer_minutes_per_day: int = 90
    max_cross_city_days: int = 3
    preferred_mobility_mode: str = "public_transit"
    routing_mode: str = "hub_and_spoke"
    climate_risk_flags: list[str] = field(default_factory=list)
    resolved_policy_snapshot: dict[str, Any] = field(default_factory=dict)
    constraint_trace: list[ConstraintTraceItem] = field(default_factory=list)
    compiler_version: str = COMPILER_VERSION
    run_id: str = field(default_factory=lambda: str(_uuid.uuid4()))

    def trace_summary(self) -> list[str]:
        lines = []
        for t in self.constraint_trace:
            consumers = ",".join(t.intended_consumers) if t.intended_consumers else "?"
            suffix = f" | ignored: {t.ignored_reason}" if t.ignored_reason else ""
            lines.append(
                f"[{t.strength}] {t.constraint_name}: {t.source_inputs} -> {t.compiled_value} "
                f"| consumers={consumers} | status={t.final_status}{suffix}"
            )
        return lines

    def record_consumption(
        self,
        constraint_name: str,
        module: str,
        action: str,
        effect_summary: str,
        reason: str = "",
    ) -> None:
        for t in self.constraint_trace:
            if t.constraint_name == constraint_name:
                t.consumption_events.append(
                    {
                        "module": module,
                        "action": action,
                        "effect_summary": effect_summary,
                        "reason": reason,
                    }
                )
                if t.final_status == "pending":
                    t.final_status = "partially_consumed"
                return
        self.constraint_trace.append(
            ConstraintTraceItem(
                constraint_name=constraint_name,
                source_inputs="(runtime)",
                compiled_value="(runtime)",
                intended_consumers=[module],
                consumption_events=[
                    {
                        "module": module,
                        "action": action,
                        "effect_summary": effect_summary,
                        "reason": reason,
                    }
                ],
                final_status="partially_consumed",
            )
        )

    def finalize_trace(self) -> None:
        for t in self.constraint_trace:
            if t.final_status == "pending":
                t.final_status = "unconsumed"
                if not t.ignored_reason:
                    t.ignored_reason = "no_consumption_event_recorded"
            elif t.final_status == "partially_consumed":
                hit_modules = {e["module"] for e in t.consumption_events}
                if t.intended_consumers and all(
                    any(expected in hit for hit in hit_modules) for expected in t.intended_consumers
                ):
                    t.final_status = "fully_consumed"
        logger.info(
            "[finalize_trace] run=%s %s",
            self.run_id[:8],
            " | ".join(f"{t.constraint_name}={t.final_status}" for t in self.constraint_trace),
        )

    def hard_unconsumed(self) -> list[ConstraintTraceItem]:
        return [t for t in self.constraint_trace if t.strength == "hard" and t.final_status == "unconsumed"]

    def has_pending(self) -> bool:
        return any(t.final_status == "pending" for t in self.constraint_trace)

    def to_evidence_dict(
        self,
        plan_id: str = "",
        request_id: str = "",
        key_decisions: list[str] | None = None,
        input_contract: dict | None = None,
    ) -> dict:
        from datetime import datetime, timezone

        return {
            "run_id": self.run_id,
            "plan_id": plan_id,
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "compiler_version": self.compiler_version,
            "compiled_constraints": {
                "blocked_tags": sorted(self.blocked_tags),
                "blocked_clusters": sorted(self.blocked_clusters),
                "visited_clusters": sorted(self.visited_clusters),
                "must_go_clusters": sorted(self.must_go_clusters),
                "avoid_cuisines": sorted(self.avoid_cuisines),
                "max_intensity": self.max_intensity,
                "preferred_tags_boost": self.preferred_tags_boost,
                "party_block_tags": sorted(self.party_block_tags),
                "max_majors_per_day": self.max_majors_per_day,
                "max_transfer_minutes_per_day": self.max_transfer_minutes_per_day,
                "max_cross_city_days": self.max_cross_city_days,
                "preferred_mobility_mode": self.preferred_mobility_mode,
                "routing_mode": self.routing_mode,
                "climate_risk_flags": self.climate_risk_flags,
            },
            "resolved_policy": self.resolved_policy_snapshot,
            "constraint_trace": [
                {
                    "constraint_name": t.constraint_name,
                    "strength": t.strength,
                    "source_inputs": t.source_inputs,
                    "compiled_value": t.compiled_value,
                    "intended_consumers": t.intended_consumers,
                    "consumption_events": t.consumption_events,
                    "final_status": t.final_status,
                    "ignored_reason": t.ignored_reason,
                }
                for t in self.constraint_trace
            ],
            "hard_unconsumed_count": len(self.hard_unconsumed()),
            "key_decisions": key_decisions or [],
            "input_contract": input_contract or {},
            "final_pdf_path": None,
            "final_html_path": None,
        }


_PACE_TO_MAX_INTENSITY: dict[str, int] = {
    "relaxed": 0,
    "moderate": 1,
    "packed": 2,
    "dense": 2,
}

_INTENSITY_LEVEL: dict[str, int] = {
    "light": 0,
    "relaxed": 0,
    "balanced": 1,
    "moderate": 1,
    "dense": 2,
}

_PARTY_RULES: dict[str, dict] = {
    "family_multi_gen": {"block_unless_must_go": {"theme_park"}, "penalty": 15.0, "max_intensity_override": 1},
    "senior": {"block_unless_must_go": {"theme_park"}, "penalty": 15.0, "max_intensity_override": 0},
    "family_child": {"block_unless_must_go": set(), "penalty": 5.0, "max_intensity_override": None},
}


def compile_constraints(profile, resolved_policy: ResolvedPolicySet | None = None) -> PlanningConstraints:
    c = PlanningConstraints()
    trace = c.constraint_trace
    must_tags = set(t.lower() for t in (getattr(profile, "must_have_tags", None) or []))
    special_requirements = getattr(profile, "special_requirements", None) or {}
    if isinstance(special_requirements, dict) and special_requirements:
        trace.append(
            ConstraintTraceItem(
                constraint_name="special_requirements_side_channel",
                source_inputs=f"profile.special_requirements.keys={sorted(special_requirements.keys())}",
                compiled_value="ignored_for_main_runtime_contract",
                strength="soft",
                intended_consumers=[],
                final_status="unconsumed",
                ignored_reason="compatibility_side_channel_only",
            )
        )

    if resolved_policy is None:
        requested_circle = getattr(profile, "requested_city_circle", None) or ""
        if requested_circle:
            resolved_policy = resolve_policy_set(requested_circle)

    if resolved_policy is not None:
        _apply_policy_constraints(c, resolved_policy, trace)

    avoid_tags = set(t.lower() for t in (getattr(profile, "avoid_tags", None) or []))
    c.blocked_tags = avoid_tags
    if avoid_tags:
        trace.append(
            ConstraintTraceItem(
                constraint_name="blocked_tags",
                source_inputs=f"profile.avoid_tags={sorted(avoid_tags)}",
                compiled_value=str(sorted(avoid_tags)),
                strength="hard",
                intended_consumers=["ranker", "skeleton"],
            )
        )

    blocked_clusters = set(getattr(profile, "blocked_clusters", None) or [])
    blocked_places = set(getattr(profile, "do_not_go_places", None) or [])
    blocked_pois = set(getattr(profile, "blocked_pois", None) or [])
    c.blocked_clusters = blocked_clusters | blocked_places | blocked_pois
    if c.blocked_clusters:
        trace.append(
            ConstraintTraceItem(
                constraint_name="blocked_clusters",
                source_inputs=(
                    f"profile.blocked_clusters={sorted(blocked_clusters)}, "
                    f"do_not_go_places={sorted(blocked_places)}, "
                    f"blocked_pois={sorted(blocked_pois)}"
                ),
                compiled_value=str(sorted(c.blocked_clusters)),
                strength="hard",
                intended_consumers=["ranker", "skeleton"],
            )
        )

    raw_must_go = (
        getattr(profile, "must_visit_places", None)
        or getattr(profile, "must_go_places", None)
        or []
    )

    must_go_clusters: set[str] = set()
    if isinstance(raw_must_go, (list, tuple, set)):
        for item in raw_must_go:
            if not isinstance(item, str):
                continue
            key = item.strip().lower().replace(" ", "_").replace("-", "_")
            if key:
                must_go_clusters.add(key)
    c.must_go_clusters = must_go_clusters
    if c.must_go_clusters:
        trace.append(
            ConstraintTraceItem(
                constraint_name="must_go_clusters",
                source_inputs=f"profile.must_visit_places={sorted(c.must_go_clusters)}",
                compiled_value=str(sorted(c.must_go_clusters)),
                strength="hard",
                intended_consumers=["ranker"],
            )
        )

    raw_visited_places = getattr(profile, "visited_places", None) or []
    visited_clusters: set[str] = set()
    if isinstance(raw_visited_places, (list, tuple, set)):
        for item in raw_visited_places:
            if not isinstance(item, str):
                continue
            key = item.strip().lower().replace(" ", "_").replace("-", "_")
            if key:
                visited_clusters.add(key)
    c.visited_clusters = visited_clusters
    if c.visited_clusters:
        trace.append(
            ConstraintTraceItem(
                constraint_name="visited_clusters",
                source_inputs=f"profile.visited_places={sorted(c.visited_clusters)}",
                compiled_value=str(sorted(c.visited_clusters)),
                strength="hard",
                intended_consumers=["ranker"],
            )
        )

    booked_items = getattr(profile, "booked_items", None) or []
    if booked_items:
        trace.append(
            ConstraintTraceItem(
                constraint_name="booked_items",
                source_inputs=f"profile.booked_items={len(booked_items)}",
                compiled_value=str(booked_items),
                strength="soft",
                intended_consumers=["hotel_base_builder", "skeleton"],
                ignored_reason="slot locking not fully wired yet",
            )
        )

    cuisine_tags = {
        "sushi", "sashimi", "raw", "yakiniku", "ramen", "tempura", "kushikatsu",
        "yakitori", "takoyaki", "okonomiyaki", "kaiseki", "udon", "tonkatsu",
    }
    cuisine_avoids = avoid_tags & cuisine_tags
    if "raw" in avoid_tags:
        cuisine_avoids |= {"sashimi", "sushi"}
    c.avoid_cuisines = cuisine_avoids
    if cuisine_avoids:
        trace.append(
            ConstraintTraceItem(
                constraint_name="avoid_cuisines",
                source_inputs=f"profile.avoid_tags={sorted(avoid_tags)}",
                compiled_value=str(sorted(cuisine_avoids)),
                strength="hard",
                intended_consumers=["filler"],
            )
        )

    pace = (getattr(profile, "pace", None) or "moderate").lower()
    c.max_intensity = min(c.max_intensity, _PACE_TO_MAX_INTENSITY.get(pace, 1))
    trace.append(
        ConstraintTraceItem(
            constraint_name="max_intensity",
            source_inputs=f"profile.pace='{pace}'",
            compiled_value=str(c.max_intensity),
            strength="hard",
            intended_consumers=["skeleton"],
        )
    )

    cities = getattr(profile, "cities", None) or []
    stay_cities = set()
    for city_spec in cities:
        if isinstance(city_spec, dict):
            city_code = city_spec.get("city_code", "")
            if city_code:
                stay_cities.add(city_code.lower())
        elif isinstance(city_spec, str):
            stay_cities.add(city_spec.lower())
    c.must_stay_cities = stay_cities

    c.must_stay_area = (getattr(profile, "must_stay_area", None) or "").lower()
    if c.must_stay_area:
        trace.append(
            ConstraintTraceItem(
                constraint_name="must_stay_area",
                source_inputs=f"profile.must_stay_area='{c.must_stay_area}'",
                compiled_value=f"area='{c.must_stay_area}'",
                strength="soft",
                intended_consumers=["hotel_base_builder"],
                ignored_reason="hotel_base_builder not yet wired",
            )
        )

    party = (getattr(profile, "party_type", None) or "").lower()
    rules = _PARTY_RULES.get(party)
    if rules:
        raw_blocks = rules.get("block_unless_must_go", set())
        effective_blocks = raw_blocks - must_tags
        if effective_blocks:
            c.party_block_tags = effective_blocks
            trace.append(
                ConstraintTraceItem(
                    constraint_name="party_block_tags",
                    source_inputs=f"party_type='{party}', must_have_tags={sorted(must_tags)}",
                    compiled_value=f"blocked={sorted(effective_blocks)}",
                    strength="hard",
                    intended_consumers=["ranker"],
                )
            )
        c.party_fit_penalty = rules.get("penalty", 0.0)
        if c.party_fit_penalty:
            trace.append(
                ConstraintTraceItem(
                    constraint_name="party_fit_penalty",
                    source_inputs=f"party_type='{party}'",
                    compiled_value=str(c.party_fit_penalty),
                    strength="soft",
                    intended_consumers=["ranker"],
                )
            )
        intensity_override = rules.get("max_intensity_override")
        if intensity_override is not None and intensity_override < c.max_intensity:
            old = c.max_intensity
            c.max_intensity = intensity_override
            trace.append(
                ConstraintTraceItem(
                    constraint_name="max_intensity_party_override",
                    source_inputs=f"party_type='{party}'",
                    compiled_value=f"{old}->{intensity_override}",
                    strength="hard",
                    intended_consumers=["skeleton"],
                )
            )
    else:
        trace.append(
            ConstraintTraceItem(
                constraint_name="party_rules",
                source_inputs=f"party_type='{party}'",
                compiled_value="no rules",
                strength="soft",
                intended_consumers=[],
                final_status="unconsumed",
                ignored_reason=f"no party rules for '{party}'",
            )
        )

    nice_tags = set(t.lower() for t in (getattr(profile, "nice_to_have_tags", None) or []))
    for tag in nice_tags:
        c.preferred_tags_boost[tag] = 10.0
    for tag in must_tags:
        c.preferred_tags_boost[tag] = max(c.preferred_tags_boost.get(tag, 0), 20.0)
    if c.preferred_tags_boost:
        trace.append(
            ConstraintTraceItem(
                constraint_name="preferred_tags_boost",
                source_inputs=f"must_have_tags={sorted(must_tags)}, nice_to_have={sorted(nice_tags)}",
                compiled_value=str({k: v for k, v in sorted(c.preferred_tags_boost.items())}),
                strength="soft",
                intended_consumers=["ranker"],
            )
        )

    departure_shape = (getattr(profile, "departure_day_shape", None) or "").lower()
    if departure_shape == "full_day":
        c.departure_day_no_poi = False
        c.departure_meal_window = "breakfast_lunch"
    elif departure_shape == "airport_only":
        c.departure_day_no_poi = True
        c.departure_meal_window = "none"
    else:
        c.departure_day_no_poi = True
        c.departure_meal_window = "breakfast_only"
    trace.append(
        ConstraintTraceItem(
            constraint_name="departure_constraints",
            source_inputs=f"departure_day_shape='{departure_shape}'",
            compiled_value=f"no_poi={c.departure_day_no_poi}, meals='{c.departure_meal_window}'",
            strength="hard",
            intended_consumers=["skeleton", "filler"],
        )
    )

    arrival_time = getattr(profile, "arrival_time", None) or ""
    if not arrival_time and getattr(profile, "arrival_local_datetime", None):
        arrival_time = profile.arrival_local_datetime.strftime("%H:%M")
    arrival_shape = (getattr(profile, "arrival_shape", None) or "").lower()
    if arrival_time:
        try:
            if int(arrival_time.split(":")[0]) >= 17:
                c.arrival_evening_only = True
        except (ValueError, IndexError):
            pass
    if arrival_shape == "evening_only":
        c.arrival_evening_only = True
    trace.append(
        ConstraintTraceItem(
            constraint_name="arrival_constraints",
            source_inputs=f"arrival_time='{arrival_time}', arrival_shape='{arrival_shape}'",
            compiled_value=f"evening_only={c.arrival_evening_only}",
            strength="hard",
            intended_consumers=["skeleton", "filler"],
        )
    )

    logger.info(
        "constraint_compiler v%s [%s]: %d constraints, %d trace items",
        COMPILER_VERSION,
        c.run_id,
        _count_active(c),
        len(trace),
    )
    for line in c.trace_summary():
        logger.debug("  %s", line)
    return c


def _apply_policy_constraints(
    constraints: PlanningConstraints,
    resolved_policy: ResolvedPolicySet,
    trace: list[ConstraintTraceItem],
) -> None:
    constraints.resolved_policy_snapshot = resolved_policy.to_dict()
    constraints.preferred_mobility_mode = resolved_policy.mobility_policy.primary_mode
    constraints.max_transfer_minutes_per_day = resolved_policy.mobility_policy.max_transfer_minutes_per_day
    constraints.max_cross_city_days = resolved_policy.routing_style_policy.max_cross_city_days
    constraints.max_majors_per_day = resolved_policy.routing_style_policy.max_majors_per_day
    constraints.routing_mode = resolved_policy.routing_style_policy.routing_mode
    constraints.climate_risk_flags = list(resolved_policy.climate_and_season_policy.explain_risks)
    constraints.max_intensity = max(
        0,
        min(2, constraints.max_intensity + resolved_policy.climate_and_season_policy.pace_cap_adjustment),
    )

    trace.append(
        ConstraintTraceItem(
            constraint_name="policy_city_circle_profile",
            source_inputs=f"policy.circle_id='{resolved_policy.circle_id}'",
            compiled_value=str(resolved_policy.city_circle_profile),
            strength="soft",
            intended_consumers=["selector", "explain"],
        )
    )
    trace.append(
        ConstraintTraceItem(
            constraint_name="policy_mobility",
            source_inputs=f"policy.circle_id='{resolved_policy.circle_id}'",
            compiled_value=(
                f"mode={constraints.preferred_mobility_mode}, "
                f"max_transfer_minutes_per_day={constraints.max_transfer_minutes_per_day}"
            ),
            strength="hard",
            intended_consumers=["skeleton", "explain"],
        )
    )
    trace.append(
        ConstraintTraceItem(
            constraint_name="policy_climate_and_season",
            source_inputs=f"policy.circle_id='{resolved_policy.circle_id}'",
            compiled_value=(
                f"pace_cap_adjustment={resolved_policy.climate_and_season_policy.pace_cap_adjustment}, "
                f"risk_flags={constraints.climate_risk_flags}"
            ),
            strength="hard",
            intended_consumers=["skeleton", "explain"],
        )
    )
    trace.append(
        ConstraintTraceItem(
            constraint_name="policy_routing_style",
            source_inputs=f"policy.circle_id='{resolved_policy.circle_id}'",
            compiled_value=(
                f"routing_mode={constraints.routing_mode}, "
                f"max_cross_city_days={constraints.max_cross_city_days}, "
                f"max_majors_per_day={constraints.max_majors_per_day}"
            ),
            strength="hard",
            intended_consumers=["skeleton", "explain"],
        )
    )
    trace.append(
        ConstraintTraceItem(
            constraint_name="policy_hotel_base",
            source_inputs=f"policy.circle_id='{resolved_policy.circle_id}'",
            compiled_value=(
                f"base_pattern_bias={resolved_policy.hotel_base_policy.base_pattern_bias}, "
                f"prefer_last_night_near_hub={resolved_policy.hotel_base_policy.prefer_last_night_near_hub}, "
                f"long_segment_base_preference={resolved_policy.hotel_base_policy.long_segment_base_preference}"
            ),
            strength="hard",
            intended_consumers=["hotel_base_builder", "explain"],
        )
    )
    trace.append(
        ConstraintTraceItem(
            constraint_name="policy_day_frame",
            source_inputs=f"policy.circle_id='{resolved_policy.circle_id}'",
            compiled_value=(
                f"arrival_ratio={resolved_policy.day_frame_policy.arrival_capacity_ratio}, "
                f"departure_ratio={resolved_policy.day_frame_policy.departure_capacity_ratio}, "
                f"transit_multiplier={resolved_policy.day_frame_policy.transit_budget_multiplier}"
            ),
            strength="hard",
            intended_consumers=["skeleton", "explain"],
        )
    )
    trace.append(
        ConstraintTraceItem(
            constraint_name="policy_booking_and_reservation",
            source_inputs=f"policy.circle_id='{resolved_policy.circle_id}'",
            compiled_value=(
                f"high_pressure_constraint={resolved_policy.booking_and_reservation_policy.high_pressure_constraint}, "
                f"unbooked_major_action={resolved_policy.booking_and_reservation_policy.unbooked_major_action}, "
                f"hold_back_edge_days={resolved_policy.booking_and_reservation_policy.hold_back_edge_days}"
            ),
            strength="hard",
            intended_consumers=["skeleton", "explain"],
        )
    )


def _count_active(c: PlanningConstraints) -> int:
    count = 0
    if c.blocked_tags:
        count += 1
    if c.blocked_clusters:
        count += 1
    if c.visited_clusters:
        count += 1
    if c.must_go_clusters:
        count += 1
    if c.avoid_cuisines:
        count += 1
    if c.max_intensity < 2:
        count += 1
    if c.must_stay_cities:
        count += 1
    if c.must_stay_area:
        count += 1
    if c.party_block_tags:
        count += 1
    if c.party_fit_penalty > 0:
        count += 1
    if c.preferred_tags_boost:
        count += 1
    if c.departure_day_no_poi:
        count += 1
    if c.arrival_evening_only:
        count += 1
    if c.resolved_policy_snapshot:
        count += 1
    return count


def intensity_name_to_level(name: str) -> int:
    return _INTENSITY_LEVEL.get(name.lower(), 1)


def is_intensity_allowed(intensity_name: str, constraints: PlanningConstraints) -> bool:
    return intensity_name_to_level(intensity_name) <= constraints.max_intensity


def max_allowed_intensity_name(constraints: PlanningConstraints) -> str:
    for name, level in [("dense", 2), ("balanced", 1), ("light", 0)]:
        if level <= constraints.max_intensity:
            return name
    return "light"
