from __future__ import annotations

from app.api.review import _derive_operator_surface_state


def test_operator_surface_state_main_flow_for_done_order():
    state = _derive_operator_surface_state(
        order_status="done",
        has_pending_modifications=False,
        has_active_review_job=False,
    )
    assert state.stage in {"action_needed", "read_ready"}
    assert state.action_boundary == "main_proof_flow"
    assert state.proof_lane == "main_chain_proof"


def test_operator_surface_state_terminal_for_cancelled():
    state = _derive_operator_surface_state(
        order_status="cancelled",
        has_pending_modifications=False,
        has_active_review_job=False,
    )
    assert state.stage == "terminal"
    assert state.action_boundary == "compatibility_support"
    assert state.proof_lane == "compatibility_baseline"


def test_operator_surface_state_pending_modification_marks_action_needed():
    state = _derive_operator_surface_state(
        order_status="delivered",
        has_pending_modifications=True,
        has_active_review_job=True,
    )
    assert state.stage == "action_needed"
    assert state.action_boundary == "main_proof_flow"
    assert state.proof_lane == "main_chain_proof"
