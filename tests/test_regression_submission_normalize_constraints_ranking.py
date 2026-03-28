from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.api.submissions import _build_raw_input
from app.db.models.city_circles import ActivityCluster, CircleEntityRole
from app.domains.planning.constraint_compiler import compile_constraints
from app.domains.planning.major_activity_ranker import rank_major_activities
from app.workers.__main__ import normalize_trip_profile


class _ScalarResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return list(self._rows)

    def scalar_one_or_none(self):
        if not self._rows:
            return None
        return self._rows[0]


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

    def scalar_one_or_none(self):
        if not self._rows:
            return None
        return self._rows[0]


class _Store:
    def __init__(self):
        self.trip_request_id = uuid.uuid4()
        self.trip = SimpleNamespace(
            trip_request_id=self.trip_request_id,
            raw_input={},
            status="new",
            last_job_error=None,
        )
        self.profile = None


class _NormalizeSession:
    def __init__(self, store: _Store):
        self.store = store

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, model, key):
        if str(key) == str(self.store.trip_request_id):
            return self.store.trip
        return None

    async def execute(self, stmt):
        # normalize_trip_profile only needs scalar_one_or_none for existing profile query
        return _Result([self.store.profile] if self.store.profile is not None else [])

    def add(self, obj):
        # capture created TripProfile instance
        if getattr(obj, "__class__", None).__name__ == "TripProfile":
            self.store.profile = obj

    async def commit(self):
        return None


class _NormalizeSessionFactory:
    def __init__(self, store: _Store):
        self.store = store

    def __call__(self):
        return _NormalizeSession(self.store)


class _RankingSession:
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
            return _Result([], scalar_mode=False)
        if "from activity_clusters" in sql:
            return _Result(self._clusters)
        if "from circle_entity_roles" in sql:
            return _Result(self._roles)
        raise AssertionError(f"unexpected query: {sql}")


@pytest.mark.asyncio
async def test_regression_submission_normalize_constraints_ranking(monkeypatch):
    submission_id = "sub-reg-001"
    sub = {
        "destination": "kansai",
        "duration_days": 3,
        "party_type": "couple",
        "styles": [],
        "people_count": 2,
        "budget_focus": "balanced",
    }
    form = SimpleNamespace(
        cities=[{"city_code": "kyoto", "nights": 2}],
        requested_city_circle="kansai_classic_circle",
        duration_days=3,
        travel_start_date="2026-04-01",
        travel_end_date="2026-04-03",
        date_flexible=False,
        party_type="couple",
        party_size=2,
        has_elderly=False,
        has_children=False,
        children_ages=[],
        special_needs={},
        budget_level="mid",
        budget_total_cny=8000,
        budget_focus="balanced",
        accommodation_pref={},
        booked_items=[
            {
                "type": "hotel",
                "city_code": "kyoto",
                "name": "Kyoto Station Hotel",
                "area": "kyoto_station",
                "checkin": "2026-04-01",
                "checkout": "2026-04-03",
                "locked": True,
            }
        ],
        must_have_tags=[],
        nice_to_have_tags=[],
        avoid_tags=[],
        food_preferences={},
        pace_preference="balanced",
        wake_up_time="normal",
        must_visit_places=["伏见稻荷大社"],
        do_not_go_places=["osa_usj_themepark"],
        free_text_wishes="",
        flight_info={},
        arrival_airport="KIX",
        departure_airport="KIX",
        arrival_date="2026-04-01",
        arrival_time="18:10",
        departure_date="2026-04-03",
        departure_time="11:20",
        has_jr_pass=False,
        transport_pref={},
    )

    raw_input = _build_raw_input(submission_id, sub, form)
    assert raw_input["must_visit_places"] == ["伏见稻荷大社"]
    assert raw_input["do_not_go_places"] == ["osa_usj_themepark"]
    assert raw_input["requested_city_circle"] == "kansai_classic_circle"
    assert raw_input["arrival_local_datetime"] == "2026-04-01T18:10"
    assert raw_input["departure_local_datetime"] == "2026-04-03T11:20"
    assert raw_input["booked_items"]

    store = _Store()
    store.trip.raw_input = raw_input
    monkeypatch.setattr("app.workers.__main__.AsyncSessionLocal", _NormalizeSessionFactory(store))

    profiled = await normalize_trip_profile({}, str(store.trip_request_id))
    assert profiled.startswith("profiled:")
    assert store.profile is not None
    assert "must_visit_places" not in (store.profile.special_requirements or {})
    assert store.profile.requested_city_circle == "kansai_classic_circle"
    assert store.profile.do_not_go_places == ["osa_usj_themepark"]
    assert store.profile.booked_items
    assert store.profile.arrival_local_datetime.isoformat(timespec="minutes") == "2026-04-01T18:10"

    constraints = compile_constraints(store.profile)
    assert "伏见稻荷大社".lower() in constraints.must_go_clusters
    assert "osa_usj_themepark" in constraints.blocked_clusters

    must_go_cluster = "kyo_cluster_001"
    normal_cluster = "kyo_higashiyama_gion_classic"
    circle_id = "kansai_city_circle"
    c1 = ActivityCluster(
        cluster_id=must_go_cluster,
        circle_id=circle_id,
        name_zh="伏见稻荷",
        level="B",
        default_duration="full_day",
        profile_fit=[],
        seasonality=[],
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    c2 = ActivityCluster(
        cluster_id=normal_cluster,
        circle_id=circle_id,
        name_zh="东山祇园",
        level="S",
        default_duration="full_day",
        profile_fit=[],
        seasonality=[],
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    e1 = uuid.uuid4()
    e2 = uuid.uuid4()
    roles = [
        CircleEntityRole(
            circle_id=circle_id,
            cluster_id=must_go_cluster,
            entity_id=e1,
            role="anchor_poi",
            is_cluster_anchor=True,
        ),
        CircleEntityRole(
            circle_id=circle_id,
            cluster_id=normal_cluster,
            entity_id=e2,
            role="anchor_poi",
            is_cluster_anchor=True,
        ),
    ]
    name_rows = [
        (must_go_cluster, "伏见稻荷大社", "Fushimi Inari Taisha"),
        (normal_cluster, "东山祇园", "Higashiyama Gion"),
    ]
    alias_rows = [
        (must_go_cluster, "伏见稻荷", "伏见稻荷大社"),
    ]
    ranking_session = _RankingSession([c1, c2], roles, name_rows, alias_rows)

    async def _fake_load_bq(_session, entity_ids):
        return {eid: 40.0 for eid in entity_ids}

    async def _fake_load_cf(_session, entity_ids, _profile):
        return {e1: 30.0, e2: 95.0}

    monkeypatch.setattr(
        "app.domains.planning.major_activity_ranker._load_base_quality_scores",
        _fake_load_bq,
    )
    monkeypatch.setattr(
        "app.domains.planning.major_activity_ranker._load_context_fit_scores",
        _fake_load_cf,
    )

    result = await rank_major_activities(
        session=ranking_session,
        circle_id=circle_id,
        profile=store.profile,
        passed_cluster_ids={must_go_cluster, normal_cluster},
        precheck_failed_entity_ids=set(),
        constraints=constraints,
    )

    assert result.selected_majors
    assert result.selected_majors[0].cluster_id == must_go_cluster
    assert result.must_go_unresolved == []
