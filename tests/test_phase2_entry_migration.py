from __future__ import annotations

import uuid
from datetime import datetime
from types import SimpleNamespace

import pytest

from app.api.submissions import _build_raw_input
from app.db.models.city_circles import ActivityCluster, CircleEntityRole
from app.domains.intake.layer2_contract import build_layer2_canonical_input, build_layer2_profile_contract
from app.domains.planning.constraint_compiler import compile_constraints
from app.domains.planning.major_activity_ranker import rank_major_activities
from app.workers.__main__ import _derive_circle_signals, derive_profile_tags
from scripts.test_cases import CASE_PHASE2_MIGRATED


class _ScalarResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return list(self._rows)


class _Result:
    def __init__(self, rows, scalar_mode: bool = True):
        self._rows = rows
        self._scalar_mode = scalar_mode

    def scalars(self):
        if not self._scalar_mode:
            raise AssertionError("scalars() called on non-scalar result")
        return _ScalarResult(self._rows)

    def all(self):
        return list(self._rows)


class _FakeSession:
    def __init__(self, clusters, roles, name_rows, alias_rows):
        self._clusters = clusters
        self._roles = roles
        self._name_rows = name_rows
        self._alias_rows = alias_rows

    async def execute(self, stmt):
        sql = str(stmt).lower()
        if "join entity_aliases" in sql:
            return _Result(self._alias_rows, scalar_mode=False)
        if "join entity_base" in sql:
            return _Result(self._name_rows, scalar_mode=False)
        if "from pois" in sql:
            # _load_booking_requirements expects (entity_id, requires_advance_booking)
            booking_rows = [(role.entity_id, False) for role in self._roles]
            return _Result(booking_rows, scalar_mode=False)
        if "from activity_clusters" in sql:
            return _Result(self._clusters)
        if "from circle_entity_roles" in sql:
            return _Result(self._roles)
        raise AssertionError(f"unexpected query: {sql}")


def _build_profile(case: dict) -> SimpleNamespace:
    intent = case["city_circle_intent"]
    tw = case["trip_window"]
    do_not_go = case["do_not_go_places"]
    booked_items = case["booked_items"]

    raw = {
        "requested_city_circle": intent["circle_id"],
        "party_type": "couple",
        "pace": "moderate",
        "duration_days": 5,
        "cities": [{"city_code": c, "nights": 2} for c in intent["destination_intent"]],
        "must_have_tags": ["culture", "food"],
        "nice_to_have_tags": ["photo"],
        "avoid_tags": ["sashimi"],
        "must_visit_places": case["must_visit_places"],
        "special_needs": {
            "do_not_go_places": do_not_go,
            "booked_items": booked_items,
            "locked_items": booked_items,
            **case.get("special_requirements", {}),
        },
        "travel_start_date": tw["start_date"],
        "travel_end_date": tw["end_date"],
        "arrival_date": tw["start_date"],
        "arrival_time": tw["arrival"]["time"],
        "departure_date": tw["end_date"],
        "departure_time": tw["departure"]["time"],
        "do_not_go_places": do_not_go,
        "booked_items": booked_items,
        "flight_info": {
            "outbound": {"airport": tw["arrival"]["airport"], "arrive_time": tw["arrival"]["time"]},
            "return": {"airport": tw["departure"]["airport"], "depart_time": tw["departure"]["time"]},
        },
        "arrival_airport": tw["arrival"]["airport"],
        "departure_airport": tw["departure"]["airport"],
    }
    tags = derive_profile_tags(raw)
    derived = _derive_circle_signals(raw, raw["cities"], raw["duration_days"], tags)
    canonical = build_layer2_canonical_input(raw)
    special_requirements = dict(derived["special_requirements"])

    return SimpleNamespace(
        duration_days=raw["duration_days"],
        party_type=raw["party_type"],
        pace=raw["pace"],
        cities=raw["cities"],
        must_have_tags=tags["must_have"],
        nice_to_have_tags=tags["nice_to_have"],
        avoid_tags=tags["avoid"],
        must_visit_places=raw["must_visit_places"],
        blocked_clusters=do_not_go,
        blocked_pois=[],
        must_stay_area=None,
        special_requirements=special_requirements,
        requested_city_circle=canonical["requested_city_circle"],
        arrival_local_datetime=datetime.fromisoformat(canonical["arrival_local_datetime"]),
        departure_local_datetime=datetime.fromisoformat(canonical["departure_local_datetime"]),
        visited_places=canonical["visited_places"],
        do_not_go_places=canonical["do_not_go_places"],
        booked_items=canonical["booked_items"],
        companion_breakdown=canonical["companion_breakdown"],
        budget_range=canonical["budget_range"],
        arrival_airport=derived["arrival_airport"],
        departure_airport=derived["departure_airport"],
        arrival_shape=derived["arrival_shape"],
        departure_shape=derived["departure_shape"],
        arrival_day_shape=derived["arrival_day_shape"],
        departure_day_shape=derived["departure_day_shape"],
        daytrip_tolerance=derived["daytrip_tolerance"],
        hotel_switch_tolerance=derived["hotel_switch_tolerance"],
        arrival_time=tw["arrival"]["time"],
    )


@pytest.mark.asyncio
async def test_phase2_build_raw_input_respects_explicit_requested_city_circle_from_detail_form():
    sub = {
        "destination": "kansai",
        "duration_days": 5,
        "party_type": "couple",
        "styles": [],
        "people_count": 2,
        "budget_focus": "balanced",
    }
    form = SimpleNamespace(
        cities=[{"city_code": "kyoto", "nights": 3}],
        duration_days=5,
        requested_city_circle="hokkaido_city_circle",
        special_needs={"requested_city_circle": "legacy_should_not_be_used"},
        travel_start_date="2026-10-01",
        travel_end_date="2026-10-05",
        booked_hotels=[],
    )

    raw_input = _build_raw_input("submission-1", sub, form)

    assert raw_input["requested_city_circle"] == "hokkaido_city_circle"


@pytest.mark.asyncio
async def test_phase2_migrated_contract_sample_assertions(monkeypatch):
    case = CASE_PHASE2_MIGRATED
    profile = _build_profile(case)
    constraints = compile_constraints(profile)

    must_go_cluster = "kyo_fushimi_inari"
    normal_cluster = "kyo_higashiyama_gion_classic"
    blocked_cluster = "osa_usj_themepark"
    circle_id = case["city_circle_intent"]["circle_id"]

    c1 = ActivityCluster(
        cluster_id=must_go_cluster,
        circle_id=circle_id,
        name_zh="fushimi_inari",
        level="B",
        default_duration="full_day",
        profile_fit=[],
        seasonality=[],
        is_active=True,
    )
    c2 = ActivityCluster(
        cluster_id=normal_cluster,
        circle_id=circle_id,
        name_zh="higashiyama_gion",
        level="S",
        default_duration="full_day",
        profile_fit=[],
        seasonality=[],
        is_active=True,
    )
    c3 = ActivityCluster(
        cluster_id=blocked_cluster,
        circle_id=circle_id,
        name_zh="usj_theme_park",
        level="S",
        default_duration="full_day",
        profile_fit=[],
        seasonality=[],
        is_active=True,
    )

    e1 = uuid.uuid4()
    e2 = uuid.uuid4()
    e3 = uuid.uuid4()
    roles = [
        CircleEntityRole(circle_id=circle_id, cluster_id=must_go_cluster, entity_id=e1, role="anchor_poi", is_cluster_anchor=True),
        CircleEntityRole(circle_id=circle_id, cluster_id=normal_cluster, entity_id=e2, role="anchor_poi", is_cluster_anchor=True),
        CircleEntityRole(circle_id=circle_id, cluster_id=blocked_cluster, entity_id=e3, role="anchor_poi", is_cluster_anchor=True),
    ]

    async def _fake_load_bq(_session, entity_ids):
        return {eid: 40.0 for eid in entity_ids}

    async def _fake_load_cf(_session, entity_ids, _profile):
        return {e1: 30.0, e2: 95.0, e3: 98.0}

    monkeypatch.setattr("app.domains.planning.major_activity_ranker._load_base_quality_scores", _fake_load_bq)
    monkeypatch.setattr("app.domains.planning.major_activity_ranker._load_context_fit_scores", _fake_load_cf)

    name_rows = [
        (must_go_cluster, "fushimi_inari_taisha", "Fushimi Inari Taisha"),
        (normal_cluster, "higashiyama_gion", "Higashiyama Gion"),
        (blocked_cluster, "usj_theme_park", "USJ"),
    ]
    alias_rows = [(must_go_cluster, "fushimi_inari", "fushimi_inari_taisha")]
    session = _FakeSession([c1, c2, c3], roles, name_rows=name_rows, alias_rows=alias_rows)

    result = await rank_major_activities(
        session=session,
        circle_id=circle_id,
        profile=profile,
        passed_cluster_ids={must_go_cluster, normal_cluster, blocked_cluster},
        precheck_failed_entity_ids=set(),
        constraints=constraints,
    )
    selected_ids = [m.cluster_id for m in result.selected_majors]

    assert must_go_cluster in selected_ids
    must_go_trace = next(t for t in constraints.constraint_trace if t.constraint_name == "must_go_clusters")
    assert any(e.get("module") == "ranker" for e in must_go_trace.consumption_events)

    assert blocked_cluster in constraints.blocked_clusters
    assert blocked_cluster not in selected_ids

    assert profile.special_requirements.get("booked_items")
    assert profile.special_requirements.get("locked_items")
    assert build_layer2_profile_contract(profile)["requested_city_circle"] == case["city_circle_intent"]["circle_id"]

    assert profile.arrival_day_shape == "evening_only"
    assert profile.departure_day_shape == "half_day_morning"

    constraints.finalize_trace()
    generation_decisions = [f"selected_major:{cid}" for cid in selected_ids]
    evidence = constraints.to_evidence_dict(
        plan_id="phase2-template-plan",
        request_id=case["case_id"],
        key_decisions=generation_decisions,
        input_contract=build_layer2_profile_contract(profile),
    )
    assert generation_decisions
    assert evidence.get("constraint_trace")
    assert evidence.get("key_decisions")
    assert evidence["input_contract"]["requested_city_circle"] == case["city_circle_intent"]["circle_id"]
