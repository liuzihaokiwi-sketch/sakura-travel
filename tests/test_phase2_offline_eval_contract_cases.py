from __future__ import annotations

from app.domains.evaluation.offline_eval import (
    build_eval_case_from_contract,
    load_contract_v2_eval_cases,
    run_eval,
)
from scripts.test_cases import CASE_PHASE2_KANSAI_FAMILY


def test_phase2_eval_cases_v2_file_is_contract_first():
    cases = load_contract_v2_eval_cases()

    assert len(cases) >= 3
    assert all(c.input_contract is not None for c in cases)
    assert all((c.input_contract or {}).get("contract_version") == "v2" for c in cases)
    assert any((c.input_contract or {}).get("booked_items") for c in cases)
    assert any((c.input_contract or {}).get("do_not_go_places") for c in cases)


def test_build_eval_case_from_contract_uses_trip_window_days_and_canonical_fields():
    eval_case = build_eval_case_from_contract(
        case_id=CASE_PHASE2_KANSAI_FAMILY["case_id"],
        description=CASE_PHASE2_KANSAI_FAMILY["case_desc"],
        contract=CASE_PHASE2_KANSAI_FAMILY,
    )

    assert eval_case.user_profile["days"] == 6
    assert eval_case.user_profile["segment"] == "family_child"
    assert eval_case.input_contract is not None
    assert eval_case.input_contract["requested_city_circle"] == "kansai_classic_circle"
    assert eval_case.input_contract["arrival_local_datetime"] == "2026-09-20T18:25"
    assert eval_case.input_contract["departure_local_datetime"] == "2026-09-25T11:45"


def _minimal_contract_plan(days: int) -> dict:
    return {
        "days": [
            {
                "day_index": idx + 1,
                "day_type": "arrival" if idx == 0 else ("departure" if idx == days - 1 else "main"),
                "intensity": "balanced",
                "items": [
                    {
                        "entity_id": f"poi_{idx}",
                        "entity_type": "poi",
                        "start_time": "10:00",
                        "area_code": "A1",
                        "reason": "test",
                    },
                    {
                        "entity_id": f"food_{idx}",
                        "entity_type": "restaurant",
                        "start_time": "13:00",
                        "area_code": "A1",
                        "reason": "test",
                    },
                ],
            }
            for idx in range(days)
        ]
    }


def test_contract_v2_cases_have_matrix_fields():
    cases = load_contract_v2_eval_cases()

    assert all(c.matrix_city_circle for c in cases)
    assert all(c.matrix_contract_semantics for c in cases)
    assert all(c.matrix_assertion_level in {"smoke", "strong"} for c in cases)


def test_run_eval_returns_contract_matrix_summary():
    cases = load_contract_v2_eval_cases()
    plans = [_minimal_contract_plan(c.user_profile["days"]) for c in cases]
    report = run_eval(plans, cases=cases, version="phase2_matrix_summary")

    assert report.matrix_summary["contract_cases"] == len(cases)
    assert len(report.matrix_summary["city_circle"]["covered"]) >= 6
    assert report.matrix_summary["city_circle"]["missing"] == []
    assert report.matrix_summary["scenario_type"]["rows"]
    assert report.matrix_summary["contract_semantics"]["rows"]
