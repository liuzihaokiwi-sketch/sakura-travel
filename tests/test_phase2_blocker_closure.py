from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

import pytest

from app.db.models.city_circles import CityCircle, HotelStrategyPreset
from app.domains.intake.layer2_contract import build_layer2_canonical_input, unpack_canonical_values
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


def test_phase2_canonical_source_annotations():
    """P1-1 验收：build_layer2_canonical_input 返回带 source 标记的字段。"""
    raw = build_layer2_canonical_input({
        "requested_city_circle": "kansai_classic_circle",
        "arrival_date": "2026-09-20",
        "arrival_time": "14:00",
        "departure_date": "2026-09-25",
        "party_size": 2,
        "budget_level": "mid",
    })
    # 每个业务字段均包含 value + source
    assert raw["requested_city_circle"]["value"] == "kansai_classic_circle"
    assert raw["requested_city_circle"]["source"] == "explicit"
    # 有 arrival_time → explicit
    assert raw["arrival_local_datetime"]["source"] == "explicit"
    # 有 party_size → explicit
    assert raw["companion_breakdown"]["source"] == "explicit"
    # 有 budget_level → explicit
    assert raw["budget_range"]["source"] == "explicit"

    # 没填 requested_city_circle → inferred
    raw2 = build_layer2_canonical_input({"destination": "tokyo"})
    assert raw2["requested_city_circle"]["source"] == "inferred"
    assert raw2["requested_city_circle"]["value"] is None
    # 只有 travel_start_date 没有 arrival_time → inferred
    raw3 = build_layer2_canonical_input({"travel_start_date": "2026-09-20"})
    assert raw3["arrival_local_datetime"]["source"] == "inferred"


def test_phase2_contract_missing_requested_city_circle_is_explicit_none():
    canonical = unpack_canonical_values(build_layer2_canonical_input(
        {
            "destination": "unknown_destination",
            "arrival_date": "2026-09-20",
            "arrival_time": "18:25",
            "departure_date": "2026-09-25",
            "departure_time": "11:45",
        }
    ))
    assert canonical["requested_city_circle"] is None


def test_phase2_contract_does_not_infer_requested_city_circle_from_destination():
    canonical = unpack_canonical_values(build_layer2_canonical_input(
        {
            "destination": "kansai",
            "arrival_date": "2026-09-20",
            "departure_date": "2026-09-25",
        }
    ))
    assert canonical["requested_city_circle"] is None


def test_phase2_contract_does_not_infer_requested_city_circle_from_circle_intent():
    canonical = unpack_canonical_values(build_layer2_canonical_input(
        {
            "city_circle_intent": {"circle_id": "kansai_classic_circle"},
            "arrival_date": "2026-09-20",
            "departure_date": "2026-09-25",
        }
    ))
    assert canonical["requested_city_circle"] is None


def test_phase2_contract_datetime_and_boundary_normalization():
    canonical = unpack_canonical_values(build_layer2_canonical_input(
        {
            "requested_city_circle": "kansai_classic_circle",
            "arrival_date": "bad-date",
            "arrival_time": "25:88",
            "departure_date": "2026-09-25",
            "departure_time": "bad-time",
            "party_type": "family_child",
            "party_size": "not-a-number",
            "children_ages": ["5", "x"],
            "budget_level": "mid",
            "budget_total_cny": "invalid",
            "budget_currency": "cny",
        }
    ))

    assert canonical["arrival_local_datetime"] is None
    assert canonical["departure_local_datetime"] is None
    assert canonical["companion_breakdown"]["party_type"] == "family_child"
    assert canonical["companion_breakdown"]["party_size"] is None
    assert canonical["companion_breakdown"]["children_ages"] == [5]
    assert canonical["budget_range"]["budget_level"] == "mid"
    assert canonical["budget_range"]["currency"] == "CNY"
    assert canonical["budget_range"]["total"] is None


@pytest.mark.asyncio
async def test_phase2_minimal_chain_emits_required_l2_artifacts():
    canonical = unpack_canonical_values(build_layer2_canonical_input(
        {
            "requested_city_circle": "kansai_classic_circle",
            "arrival_date": "2026-09-20",
            "arrival_time": "18:25",
            "departure_date": "2026-09-25",
            "departure_time": "11:45",
            "party_type": "couple",
            "party_size": 2,
            "budget_level": "mid",
            "budget_total_cny": 12000,
            "must_visit_places": ["kyo_fushimi_inari"],
            "do_not_go_places": ["osa_usj_themepark"],
            "visited_places": ["kyo_kiyomizu"],
            "booked_items": [{"type": "hotel", "city_code": "kyoto", "name": "Kyoto Stay"}],
        }
    ))

    profile = SimpleNamespace(
        duration_days=6,
        cities=[{"city_code": "kyoto"}, {"city_code": "osaka"}],
        requested_city_circle=canonical["requested_city_circle"],
        must_have_tags=["culture", "food"],
        nice_to_have_tags=["photo"],
        avoid_tags=[],
        party_type="couple",
        budget_level="mid",
        arrival_airport="KIX",
        departure_airport="KIX",
        arrival_shape="same_city",
        pace="moderate",
        daytrip_tolerance="medium",
        hotel_switch_tolerance="low",
        travel_dates={"start": "2026-09-20"},
        must_visit_places=["kyo_fushimi_inari"],
        blocked_clusters=["osa_usj_themepark"],
        blocked_pois=[],
        do_not_go_places=canonical["do_not_go_places"],
        visited_places=canonical["visited_places"],
        booked_items=canonical["booked_items"],
        companion_breakdown=canonical["companion_breakdown"],
        budget_range=canonical["budget_range"],
        arrival_local_datetime=datetime.fromisoformat("2026-09-20T18:25"),
        departure_local_datetime=datetime.fromisoformat("2026-09-25T11:45"),
        departure_day_shape="airport_only",
        arrival_time="18:25",
        special_requirements={},
        must_stay_area=None,
        last_flight_time="11:45",
    )

    circles = [
        CityCircle(
            circle_id="kansai_classic_circle",
            name_zh="关西经典圈",
            base_city_codes=["kyoto", "osaka"],
            extension_city_codes=["nara"],
            min_days=4,
            max_days=8,
            recommended_days_range="5-7",
            tier="hot",
            fit_profiles={"party_types": ["couple"]},
            friendly_airports=["KIX"],
            season_strength={"spring": 0.9},
            is_active=True,
        )
    ]
    circle_result = await select_city_circle(_CircleSession(circles), profile)
    selected_circle = circle_result.selected_circle_id

    policy = resolve_policy_set(selected_circle)
    constraints = compile_constraints(profile, resolved_policy=policy)

    presets = [
        HotelStrategyPreset(
            circle_id="kansai_classic_circle",
            name_zh="关西双基点",
            min_days=4,
            max_days=8,
            bases=[
                {"base_city": "kyoto", "area": "kyoto_station", "nights": 3, "served_cluster_ids": ["kyo_fushimi_inari"]},
                {"base_city": "osaka", "area": "namba", "nights": 2, "served_cluster_ids": ["osa_dotonbori"]},
            ],
            fit_party_types=["couple"],
            fit_budget_levels=["mid"],
            switch_count=1,
            switch_cost_minutes=40,
            last_night_airport_minutes=55,
            priority=10,
            is_active=True,
        )
    ]
    hotel_result = await build_hotel_strategy(
        _PresetSession(presets),
        selected_circle,
        profile,
        ["kyo_fushimi_inari", "osa_dotonbori"],
        resolved_policy=policy,
        constraints=constraints,
    )

    selected_majors = [
        SimpleNamespace(
            cluster_id="kyo_fushimi_inari",
            name_zh="伏见稻荷",
            default_duration="half_day",
            primary_corridor="fushimi",
            activity_load_minutes=180,
            reservation_required=False,
            reservation_pressure="none",
            booking_hint="",
            anchor_entity_ids=[],
        ),
        SimpleNamespace(
            cluster_id="osa_dotonbori",
            name_zh="道顿堀",
            default_duration="half_day",
            primary_corridor="namba",
            activity_load_minutes=180,
            reservation_required=False,
            reservation_pressure="none",
            booking_hint="",
            anchor_entity_ids=[],
        ),
    ]
    skeleton = build_route_skeleton(
        duration_days=6,
        selected_majors=selected_majors,
        hotel_bases=hotel_result.bases,
        pace="moderate",
        constraints=constraints,
        resolved_policy=policy,
        booked_items=profile.booked_items,
    )

    constraints.finalize_trace()
    generation_decisions = [f"selected_major:{m.cluster_id}" for m in selected_majors]
    evidence_bundle = constraints.to_evidence_dict(
        plan_id="phase2_min_chain",
        request_id="phase2_blocker_closure",
        key_decisions=generation_decisions,
        input_contract=canonical,
    )

    assert selected_circle == "kansai_classic_circle"
    assert constraints.to_evidence_dict()["compiled_constraints"]
    assert hotel_result.preset_name == "关西双基点"
    assert skeleton.frames
    assert generation_decisions
    assert evidence_bundle["input_contract"]["requested_city_circle"] == "kansai_classic_circle"


def test_phase2_policy_bundle_covers_six_city_circles():
    expected_ids = {
        "kansai_classic_circle",
        "kanto_city_circle",
        "hokkaido_city_circle",
        "south_china_five_city_circle",
        "guangdong_city_circle",
        "northern_xinjiang_city_circle",
    }

    resolved = [resolve_policy_set(circle_id) for circle_id in sorted(expected_ids)]
    assert {r.circle_id for r in resolved} == expected_ids
    assert all(r.mobility_policy.primary_mode for r in resolved)
    assert all(r.routing_style_policy.routing_mode for r in resolved)
