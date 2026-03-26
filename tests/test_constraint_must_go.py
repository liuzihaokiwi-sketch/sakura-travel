from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

from app.db.models.city_circles import ActivityCluster, CircleEntityRole
from app.domains.planning.constraint_compiler import compile_constraints
from app.domains.planning.major_activity_ranker import rank_major_activities


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


class _FakeSession:
    def __init__(self, clusters, roles):
        self._clusters = clusters
        self._roles = roles

    async def execute(self, stmt):
        sql = str(stmt).lower()
        if "from activity_clusters" in sql:
            return _Result(self._clusters)
        if "from circle_entity_roles" in sql:
            return _Result(self._roles)
        raise AssertionError(f"unexpected query: {sql}")


@pytest.mark.asyncio
async def test_must_visit_places_compiled_and_consumed_by_ranker(monkeypatch):
    must_go_cluster = "kyo_fushimi_inari"
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

    profile = SimpleNamespace(
        duration_days=1,
        must_visit_places=["Fushimi Inari"],
        must_have_tags=[],
        nice_to_have_tags=[],
        avoid_tags=[],
        blocked_clusters=[],
        blocked_pois=[],
        special_requirements={},
        pace="moderate",
        cities=[],
        must_stay_area=None,
        party_type="couple",
        departure_day_shape=None,
        last_flight_time=None,
        arrival_day_shape=None,
        arrival_shape=None,
    )

    constraints = compile_constraints(profile)
    assert "fushimi_inari" in constraints.must_go_clusters

    async def _fake_load_bq(_session, entity_ids):
        return {eid: 40.0 for eid in entity_ids}

    async def _fake_load_cf(_session, entity_ids, _profile):
        if not entity_ids:
            return {}
        # 非 must-go 的分更高，用来验证 must-go 优先级覆盖分数
        return {
            e1: 30.0,
            e2: 95.0,
        }

    monkeypatch.setattr(
        "app.domains.planning.major_activity_ranker._load_base_quality_scores",
        _fake_load_bq,
    )
    monkeypatch.setattr(
        "app.domains.planning.major_activity_ranker._load_context_fit_scores",
        _fake_load_cf,
    )

    session = _FakeSession([c1, c2], roles)
    result = await rank_major_activities(
        session=session,
        circle_id=circle_id,
        profile=profile,
        passed_cluster_ids={must_go_cluster, normal_cluster},
        precheck_failed_entity_ids=set(),
        constraints=constraints,
    )

    assert result.selected_majors
    assert result.selected_majors[0].cluster_id == must_go_cluster

    must_go_trace = next(
        t for t in constraints.constraint_trace if t.constraint_name == "must_go_clusters"
    )
    assert any(e.get("module") == "ranker" for e in must_go_trace.consumption_events)
