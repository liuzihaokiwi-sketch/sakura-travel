from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.domains.intake.layer2_contract import build_layer2_canonical_input
from app.domains.planning.constraint_compiler import compile_constraints
from app.workers.__main__ import _derive_circle_signals, derive_profile_tags
from scripts.test_cases import PHASE2_CASES


def _build_raw(case: dict) -> dict:
    window = case["trip_window"]
    return {
        "party_type": case.get("party_type"),
        "party_size": case.get("party_size"),
        "has_children": case.get("has_children", False),
        "children_ages": case.get("children_ages", []),
        "budget_level": case.get("budget_level"),
        "budget_total_cny": case.get("budget_total_cny"),
        "budget_currency": case.get("budget_currency"),
        "budget_focus": case.get("budget_focus"),
        "pace": case.get("pace", "moderate"),
        "requested_city_circle": (case.get("city_circle_intent") or {}).get("circle_id"),
        "city_circle_intent": case.get("city_circle_intent"),
        "travel_start_date": window.get("start_date"),
        "travel_end_date": window.get("end_date"),
        "arrival_date": window.get("start_date"),
        "arrival_time": (window.get("arrival") or {}).get("time"),
        "departure_date": window.get("end_date"),
        "departure_time": (window.get("departure") or {}).get("time"),
        "arrival_airport": (window.get("arrival") or {}).get("airport"),
        "departure_airport": (window.get("departure") or {}).get("airport"),
        "must_visit_places": case.get("must_visit_places", []),
        "do_not_go_places": case.get("do_not_go_places", []),
        "visited_places": case.get("visited_places", []),
        "booked_items": case.get("booked_items", []),
        "special_requirements": case.get("special_requirements", {}),
        "flight_info": {
            "outbound": {
                "airport": (window.get("arrival") or {}).get("airport"),
                "arrive_time": (window.get("arrival") or {}).get("time"),
            },
            "return": {
                "airport": (window.get("departure") or {}).get("airport"),
                "depart_time": (window.get("departure") or {}).get("time"),
            },
        },
    }


def _departure_no_poi_expected(departure_time: str) -> bool:
    try:
        return int((departure_time or "00:00").split(":")[0]) < 18
    except (ValueError, IndexError):
        return True


@pytest.mark.parametrize("case", PHASE2_CASES, ids=[c["case_id"] for c in PHASE2_CASES])
def test_phase2_quick_contract_fields_preserved(case: dict):
    raw = _build_raw(case)
    canonical = build_layer2_canonical_input(raw)

    assert canonical["contract_version"] == "layer2_v1"
    assert canonical["requested_city_circle"] == case["city_circle_intent"]["circle_id"]
    assert canonical["do_not_go_places"] == case.get("do_not_go_places", [])
    assert canonical["visited_places"] == case.get("visited_places", [])
    assert canonical["booked_items"] == case.get("booked_items", [])
    assert canonical["companion_breakdown"]["party_type"] == case.get("party_type")
    assert canonical["budget_range"]["budget_level"] == case.get("budget_level")
    assert canonical["budget_range"]["total"] == case.get("budget_total_cny")


@pytest.mark.parametrize("case", PHASE2_CASES, ids=[c["case_id"] for c in PHASE2_CASES])
def test_phase2_quick_constraints_and_semantics(case: dict):
    raw = _build_raw(case)
    tags = derive_profile_tags(raw)
    derived = _derive_circle_signals(
        raw=raw,
        cities=[{"city_code": c, "nights": 2} for c in case["city_circle_intent"]["destination_intent"]],
        duration_days=5,
        tags=tags,
    )

    profile = SimpleNamespace(
        must_visit_places=case.get("must_visit_places", []),
        must_have_tags=tags.get("must_have", []),
        nice_to_have_tags=tags.get("nice_to_have", []),
        avoid_tags=tags.get("avoid", []),
        blocked_clusters=case.get("do_not_go_places", []),
        blocked_pois=[],
        pace=case.get("pace", "moderate"),
        cities=[{"city_code": c, "nights": 2} for c in case["city_circle_intent"]["destination_intent"]],
        must_stay_area=None,
        party_type=case.get("party_type", "couple"),
        arrival_time=(case["trip_window"]["arrival"] or {}).get("time"),
        arrival_shape=derived.get("arrival_shape"),
        departure_day_shape=derived.get("departure_day_shape"),
        special_requirements=derived.get("special_requirements", {}),
        requested_city_circle=case["city_circle_intent"]["circle_id"],
        do_not_go_places=case.get("do_not_go_places", []),
        booked_items=case.get("booked_items", []),
        visited_places=case.get("visited_places", []),
    )

    constraints = compile_constraints(profile)

    if case.get("must_visit_places"):
        must_go_norm = {s.lower().replace(" ", "_").replace("-", "_") for s in case["must_visit_places"]}
        assert must_go_norm.issubset(constraints.must_go_clusters)
    assert set(case.get("do_not_go_places", [])).issubset(constraints.blocked_clusters)

    arrival_hour = int(case["trip_window"]["arrival"]["time"].split(":")[0])
    assert constraints.arrival_evening_only is (arrival_hour >= 17)
    assert constraints.departure_day_no_poi is _departure_no_poi_expected(
        case["trip_window"]["departure"]["time"]
    )

    special = profile.special_requirements
    assert special.get("requested_city_circle") == case["city_circle_intent"]["circle_id"]
    assert special.get("visited_places") == case.get("visited_places", [])
    assert special.get("do_not_go_places") == case.get("do_not_go_places", [])
    assert special.get("booked_items") == case.get("booked_items", [])
