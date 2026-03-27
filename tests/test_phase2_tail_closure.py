from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.domains.planning.constraint_compiler import compile_constraints
from app.domains.planning.fallback_router import FallbackLevel, evaluate_fallback
from app.domains.planning.major_activity_ranker import rank_major_activities
from scripts.run_regression import run_assertions, run_one_case
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


class _RankerSession:
    def __init__(self, clusters, roles, names):
        self._clusters = clusters
        self._roles = roles
        self._names = names

    async def execute(self, stmt):
        sql = str(stmt).lower()
        if "join entity_aliases" in sql:
            return _Result([], scalar_mode=False)
        if "join entity_base" in sql:
            return _Result(self._names, scalar_mode=False)
        if "from pois" in sql:
            return _Result([(r.entity_id, False) for r in self._roles], scalar_mode=False)
        if "from activity_clusters" in sql:
            return _Result(self._clusters)
        if "from circle_entity_roles" in sql:
            return _Result(self._roles)
        raise AssertionError(f"unexpected query: {sql}")


@pytest.mark.asyncio
async def test_visited_places_are_consumed_by_main_chain_ranker(monkeypatch):
    from app.db.models.city_circles import ActivityCluster, CircleEntityRole

    profile = SimpleNamespace(
        requested_city_circle="kansai_classic_circle",
        avoid_tags=[],
        do_not_go_places=[],
        blocked_clusters=[],
        blocked_pois=[],
        must_visit_places=[],
        must_go_places=[],
        visited_places=["kyo_fushimi_inari"],
        duration_days=5,
        pace="moderate",
        party_type="couple",
        cities=[{"city_code": "kyoto"}],
        must_have_tags=[],
    )
    constraints = compile_constraints(profile)

    e1 = uuid4()
    e2 = uuid4()
    clusters = [
        ActivityCluster(
            cluster_id="kyo_fushimi_inari",
            circle_id="kansai_classic_circle",
            name_zh="伏见稻荷",
            level="S",
            default_duration="full_day",
            profile_fit=[],
            seasonality=[],
            is_active=True,
        ),
        ActivityCluster(
            cluster_id="kyo_higashiyama_gion_classic",
            circle_id="kansai_classic_circle",
            name_zh="东山祇园",
            level="S",
            default_duration="full_day",
            profile_fit=[],
            seasonality=[],
            is_active=True,
        ),
    ]
    roles = [
        CircleEntityRole(circle_id="kansai_classic_circle", cluster_id="kyo_fushimi_inari", entity_id=e1, role="anchor_poi", is_cluster_anchor=True),
        CircleEntityRole(circle_id="kansai_classic_circle", cluster_id="kyo_higashiyama_gion_classic", entity_id=e2, role="anchor_poi", is_cluster_anchor=True),
    ]

    async def _fake_load_bq(_session, entity_ids):
        return {eid: 80.0 for eid in entity_ids}

    async def _fake_load_cf(_session, entity_ids, _profile):
        return {eid: 80.0 for eid in entity_ids}

    monkeypatch.setattr("app.domains.planning.major_activity_ranker._load_base_quality_scores", _fake_load_bq)
    monkeypatch.setattr("app.domains.planning.major_activity_ranker._load_context_fit_scores", _fake_load_cf)

    session = _RankerSession(
        clusters=clusters,
        roles=roles,
        names=[
            ("kyo_fushimi_inari", "fushimi_inari", "Fushimi Inari"),
            ("kyo_higashiyama_gion_classic", "gion", "Gion"),
        ],
    )
    result = await rank_major_activities(
        session=session,
        circle_id="kansai_classic_circle",
        profile=profile,
        passed_cluster_ids={"kyo_fushimi_inari", "kyo_higashiyama_gion_classic"},
        constraints=constraints,
    )
    selected = {x.cluster_id for x in result.selected_majors}

    assert "kyo_higashiyama_gion_classic" in selected
    assert "kyo_fushimi_inari" not in selected
    visited_trace = next(t for t in constraints.constraint_trace if t.constraint_name == "visited_clusters")
    assert any(e.get("module") == "ranker" for e in visited_trace.consumption_events)


def test_special_requirements_no_longer_drive_main_constraint_compilation():
    profile = SimpleNamespace(
        must_visit_places=[],
        must_go_places=[],
        special_requirements={"must_visit_places": ["kyo_fushimi_inari"]},
        visited_places=[],
        do_not_go_places=[],
        blocked_clusters=[],
        blocked_pois=[],
        avoid_tags=[],
        pace="moderate",
        party_type="couple",
        cities=[],
        must_have_tags=[],
    )
    constraints = compile_constraints(profile)
    assert constraints.must_go_clusters == set()


def test_new_chain_fallback_levels_require_explicit_failure():
    decision = evaluate_fallback(circle_found=False, cluster_count=0, selected_major_count=0)
    assert decision.level == FallbackLevel.FULL_LEGACY
    assert decision.requires_explicit_failure is True
    assert decision.use_legacy_assembler is False
    assert decision.use_legacy_major_selection is False


def test_legacy_report_and_export_routes_are_retired():
    route_text = open("web/app/api/report/[planId]/route.ts", "r", encoding="utf-8").read()
    pages_route_text = open("web/app/api/report/[planId]/pages/route.ts", "r", encoding="utf-8").read()
    assert "status: 410" in route_text
    assert "status: 410" in pages_route_text


@pytest.mark.asyncio
async def test_observation_chain_links_run_decision_handoff_eval_regression():
    case = dict(CASE_PHASE2_MIGRATED)
    case["special_requirements"] = {}
    case_data = await run_one_case(case, session=None)
    chain = (case_data.get("evidence_bundle") or {}).get("observation_chain") or {}
    assert all(chain.get(k) for k in ("run_id", "decision_surface", "handoff_surface", "eval_surface", "regression_surface"))

    assert_results = run_assertions(case_data)
    by_name = {x["name"]: x for x in assert_results}
    assert by_name["phase2:observation_chain_linked"]["passed"] is True
