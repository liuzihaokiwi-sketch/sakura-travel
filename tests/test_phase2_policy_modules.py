from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.db.models.city_circles import CityCircle, HotelStrategyPreset
from app.domains.planning.city_circle_selector import select_city_circle
from app.domains.planning.constraint_compiler import compile_constraints
from app.domains.planning.hotel_base_builder import build_hotel_strategy
from app.domains.planning.policy_resolver import resolve_policy_set
from app.domains.planning.route_skeleton_builder import build_route_skeleton


class _ScalarResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return list(self._rows)


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return _ScalarResult(self._rows)


class _CircleSession:
    def __init__(self, circles):
        self._circles = circles

    async def execute(self, _stmt):
        return _Result(self._circles)


class _PresetSession:
    def __init__(self, presets):
        self._presets = presets

    async def execute(self, _stmt):
        return _Result(self._presets)


def _profile(**overrides):
    base = {
        "duration_days": 6,
        "cities": [{"city_code": "sapporo"}],
        "requested_city_circle": "hokkaido_city_circle",
        "must_have_tags": ["nature"],
        "nice_to_have_tags": ["photo"],
        "avoid_tags": [],
        "party_type": "couple",
        "budget_level": "mid",
        "arrival_airport": "CTS",
        "departure_airport": "CTS",
        "arrival_shape": "same_city",
        "pace": "moderate",
        "daytrip_tolerance": "low",
        "hotel_switch_tolerance": "low",
        "travel_dates": {"start": "2026-01-10"},
        "must_visit_places": ["otaru_canal"],
        "blocked_clusters": [],
        "blocked_pois": [],
        "do_not_go_places": [],
        "must_stay_area": None,
        "departure_day_shape": "airport_only",
        "arrival_time": "18:20",
        "booked_items": [],
        "special_requirements": {},
    }
    base.update(overrides)
    return SimpleNamespace(**base)


@pytest.mark.asyncio
async def test_phase2_selector_reads_policy_bundle():
    circles = [
        CityCircle(
            circle_id="hokkaido_city_circle",
            name_zh="北海道城市圈",
            base_city_codes=["sapporo"],
            extension_city_codes=["otaru", "noboribetsu"],
            min_days=4,
            max_days=8,
            recommended_days_range="5-7",
            tier="hot",
            fit_profiles={"party_types": ["couple"], "themes": ["nature"]},
            friendly_airports=["CTS"],
            season_strength={"winter": 0.95, "spring": 0.6, "summer": 0.8, "autumn": 0.7},
            is_active=True,
        ),
        CityCircle(
            circle_id="kanto_city_circle",
            name_zh="关东城市圈",
            base_city_codes=["tokyo"],
            extension_city_codes=["yokohama", "kamakura", "hakone"],
            min_days=4,
            max_days=8,
            recommended_days_range="5-7",
            tier="hot",
            fit_profiles={"party_types": ["couple"], "themes": ["shopping"]},
            friendly_airports=["HND", "NRT"],
            season_strength={"winter": 0.6, "spring": 0.9, "summer": 0.7, "autumn": 0.8},
            is_active=True,
        ),
    ]
    result = await select_city_circle(_CircleSession(circles), _profile())

    assert result.selected_circle_id == "hokkaido_city_circle"
    assert result.selected is not None
    assert result.selected.policy_summary["routing_mode"] == "low_density_blocks"
    assert any("mobility=self_drive_or_limited_transit" in item for item in result.trace)


def test_phase2_compiler_writes_resolved_policy_into_evidence():
    policy = resolve_policy_set("hokkaido_city_circle")
    constraints = compile_constraints(_profile(), resolved_policy=policy)
    constraints.finalize_trace()
    evidence = constraints.to_evidence_dict(
        plan_id="phase2-plan",
        request_id="phase2-policy",
        input_contract={"requested_city_circle": "hokkaido_city_circle"},
    )

    assert constraints.preferred_mobility_mode == "self_drive_or_limited_transit"
    assert constraints.max_transfer_minutes_per_day == 140
    assert constraints.routing_mode == "low_density_blocks"
    assert "snow" in constraints.climate_risk_flags
    assert evidence["resolved_policy"]["mobility_policy"]["primary_mode"] == "self_drive_or_limited_transit"
    assert any(item["constraint_name"] == "policy_routing_style" for item in evidence["constraint_trace"])
    assert any(item["constraint_name"] == "policy_hotel_base" for item in evidence["constraint_trace"])
    assert any(item["constraint_name"] == "policy_day_frame" for item in evidence["constraint_trace"])
    assert any(item["constraint_name"] == "policy_booking_and_reservation" for item in evidence["constraint_trace"])


@pytest.mark.asyncio
async def test_phase2_hotel_policy_pushes_long_segment_circle_to_multi_base():
    policy = resolve_policy_set("northern_xinjiang_city_circle")
    profile = _profile(
        requested_city_circle="northern_xinjiang_city_circle",
        cities=[
            {"city_code": "urumqi"},
            {"city_code": "altay"},
            {"city_code": "yining"},
        ],
        hotel_switch_tolerance="medium",
        last_flight_time="16:00",
        booked_items=[],
    )
    constraints = compile_constraints(profile, resolved_policy=policy)
    presets = [
        HotelStrategyPreset(
            circle_id="northern_xinjiang_city_circle",
            name_zh="单基地市区住法",
            min_days=5,
            max_days=8,
            bases=[
                {
                    "base_city": "urumqi",
                    "area": "downtown",
                    "nights": 5,
                    "served_cluster_ids": ["kanas", "sayram", "ili", "urumqi_city"],
                }
            ],
            fit_party_types=["couple"],
            fit_budget_levels=["mid"],
            switch_count=0,
            switch_cost_minutes=0,
            last_night_airport_minutes=180,
            priority=10,
            is_active=True,
        ),
        HotelStrategyPreset(
            circle_id="northern_xinjiang_city_circle",
            name_zh="路段多基地住法",
            min_days=5,
            max_days=8,
            bases=[
                {"base_city": "altay", "area": "kanas", "nights": 2, "served_cluster_ids": ["kanas"]},
                {"base_city": "yining", "area": "ili", "nights": 2, "served_cluster_ids": ["ili", "sayram"]},
                {"base_city": "urumqi", "area": "airport", "nights": 1, "served_cluster_ids": ["urumqi_city"]},
            ],
            fit_party_types=["couple"],
            fit_budget_levels=["mid"],
            switch_count=2,
            switch_cost_minutes=180,
            last_night_airport_minutes=35,
            priority=30,
            is_active=True,
        ),
    ]

    result = await build_hotel_strategy(
        _PresetSession(presets),
        "northern_xinjiang_city_circle",
        profile,
        ["kanas", "ili", "sayram"],
        resolved_policy=policy,
        constraints=constraints,
    )

    constraints.finalize_trace()
    assert result.preset_name == "路段多基地住法"
    assert len(result.bases) == 3
    assert any("policy_hotel_base" in line for line in result.trace)
    assert any(item.constraint_name == "policy_hotel_base" and item.final_status != "unconsumed" for item in constraints.constraint_trace)


def test_phase2_day_frame_and_booking_policy_change_skeleton_behavior():
    policy = resolve_policy_set("hokkaido_city_circle")
    profile = _profile(
        requested_city_circle="hokkaido_city_circle",
        cities=[{"city_code": "sapporo"}, {"city_code": "otaru"}],
        booked_items=[],
    )
    constraints = compile_constraints(profile, resolved_policy=policy)
    majors = [
        SimpleNamespace(
            cluster_id="otaru_canal",
            name_zh="小樽运河",
            default_duration="half_day",
            primary_corridor="otaru",
            activity_load_minutes=180,
            reservation_required=False,
            reservation_pressure="none",
            booking_hint="",
            anchor_entity_ids=[],
        ),
        SimpleNamespace(
            cluster_id="drift_ice_cruise",
            name_zh="流冰船",
            default_duration="full_day",
            primary_corridor="abashiri",
            activity_load_minutes=320,
            reservation_required=True,
            reservation_pressure="high",
            booking_hint="需提前预约，未预约只可降级",
            anchor_entity_ids=["anchor-1"],
        ),
    ]
    hotel_bases = [
        SimpleNamespace(base_city="sapporo", area="sapporo", nights=2, served_cluster_ids=["otaru_canal"]),
        SimpleNamespace(base_city="abashiri", area="abashiri", nights=3, served_cluster_ids=["drift_ice_cruise"]),
    ]

    skeleton = build_route_skeleton(
        duration_days=5,
        selected_majors=majors,
        hotel_bases=hotel_bases,
        pace="moderate",
        constraints=constraints,
        resolved_policy=policy,
        booked_items=[],
    )

    constraints.finalize_trace()
    arrival_frame = skeleton.frames[0]
    degraded_frames = [frame for frame in skeleton.frames if frame.booking_status == "degraded"]

    assert arrival_frame.daily_capacity_minutes < 300
    assert arrival_frame.transit_minutes > 90
    assert degraded_frames
    assert "drift_ice_cruise" in skeleton.degraded_majors
    assert any(alert["cluster_id"] == "drift_ice_cruise" for alert in skeleton.booking_alerts)
    assert any(item.constraint_name == "policy_day_frame" and item.final_status != "unconsumed" for item in constraints.constraint_trace)
    assert any(item.constraint_name == "policy_booking_and_reservation" and item.final_status != "unconsumed" for item in constraints.constraint_trace)
