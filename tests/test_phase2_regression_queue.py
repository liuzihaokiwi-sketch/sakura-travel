from __future__ import annotations

from scripts.run_regression import _expand_phase2_case, _select_run_cases, summarize_case_coverage
from scripts.test_cases import ALL_CASES, PHASE2_CASES


def test_phase2_batch_cases_cover_required_shapes():
    assert 3 <= len(PHASE2_CASES) <= 5

    has_must_and_dont = False
    has_booked_hotel_or_fixed = False
    has_arrival_departure_time = False
    has_companion_breakdown_inputs = False
    has_budget_range_inputs = False
    has_visited_places = False
    circle_ids = set()

    for case in PHASE2_CASES:
        assert case.get("contract_version") == "v2"

        must_go = list(case.get("must_visit_places") or [])
        dont_go = list(case.get("do_not_go_places") or [])
        booked = list(case.get("booked_items") or [])
        window = case.get("trip_window") or {}
        arrival = window.get("arrival") or {}
        departure = window.get("departure") or {}
        circle = case.get("city_circle_intent") or {}

        if must_go and dont_go:
            has_must_and_dont = True
        if any(i.get("type") == "hotel" for i in booked) or any(i.get("locked") for i in booked):
            has_booked_hotel_or_fixed = True
        if arrival.get("time") and departure.get("time"):
            has_arrival_departure_time = True
        if case.get("party_type") and (
            case.get("party_size") is not None or case.get("children_ages") or case.get("has_children")
        ):
            has_companion_breakdown_inputs = True
        if case.get("budget_level") and case.get("budget_total_cny") is not None:
            has_budget_range_inputs = True
        if case.get("visited_places"):
            has_visited_places = True
        if circle.get("circle_id"):
            circle_ids.add(circle["circle_id"])

    assert has_must_and_dont
    assert has_booked_hotel_or_fixed
    assert has_arrival_departure_time
    assert has_companion_breakdown_inputs
    assert has_budget_range_inputs
    assert has_visited_places
    assert len(circle_ids) >= 3


def test_phase2_cases_expand_to_same_execution_contract():
    for raw_case in PHASE2_CASES:
        expanded = _expand_phase2_case(raw_case)
        asserts = expanded.get("assertions", {})
        special = expanded.get("special_requirements", {})
        source = expanded.get("_phase2_contract_source", {})
        canonical = expanded.get("_phase2_canonical_input", {})

        assert expanded["case_id"] == raw_case["case_id"]
        assert asserts.get("phase2_contract_checks") is True
        assert asserts.get("phase2_slot_lock_checks") is True
        assert isinstance(special, dict)
        assert isinstance(canonical.get("booked_items"), list)
        assert canonical.get("requested_city_circle") == raw_case["city_circle_intent"]["circle_id"]
        assert canonical.get("visited_places") == raw_case.get("visited_places", [])
        assert source.get("contract_version") == "v2"
        assert expanded.get("_phase2_execution_mode") == "contract_first"
        assert expanded.get("proof_level") == "main_chain_proof"
        assert expanded.get("test_source_set") == "phase2_contract_cases"


def test_regression_case_id_filter_includes_phase2_cases():
    target = {"phase2_kansai_family"}
    selected = _select_run_cases(run_phase2=True, case_filter=target)
    selected_ids = {c["case_id"] for c in selected}

    assert selected_ids == target


def test_case_trace_metadata_classifies_main_vs_compatibility():
    for case in PHASE2_CASES:
        assert case["test_source_set"] == "phase2_contract_cases"
        assert case["proof_level"] == "main_chain_proof"
        assert "generate_trip._try_city_circle_pipeline" in case["entry_anchor"]

    for case in ALL_CASES:
        assert case["test_source_set"] == "legacy_profile_cases"
        assert case["proof_level"] == "compatibility_baseline"


def test_case_coverage_summary_keeps_main_vs_compatibility_split():
    all_case_data = [
        {
            "case": case,
            "case_trace": {
                "proof_level": case["proof_level"],
                "source_set": case["test_source_set"],
            },
        }
        for case in PHASE2_CASES + ALL_CASES
    ]

    coverage = summarize_case_coverage(all_case_data)

    assert coverage["proof_counts"]["main_chain_proof"] == len(PHASE2_CASES)
    assert coverage["proof_counts"]["compatibility_baseline"] == len(ALL_CASES)
    assert coverage["source_set_counts"]["phase2_contract_cases"] == len(PHASE2_CASES)
    assert coverage["source_set_counts"]["legacy_profile_cases"] == len(ALL_CASES)
    assert sorted(coverage["case_ids_by_proof"]["main_chain_proof"]) == sorted(c["case_id"] for c in PHASE2_CASES)
    assert sorted(coverage["case_ids_by_proof"]["compatibility_baseline"]) == sorted(c["case_id"] for c in ALL_CASES)

