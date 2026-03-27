from __future__ import annotations

from pathlib import Path

import pytest


PHASE2_FILE_PREFIX = "test_phase2_"
PHASE2_E2E_FILE = Path("tests/e2e/test_full_pipeline.py")
PHASE2_E2E_NODE_PREFIX = "test_phase2_"
L3_BLOCKER_FILES = {
    Path("tests/test_layer2_delivery_handoff.py"),
    Path("tests/test_shared_export_contract.py"),
    Path("tests/test_handbook_delivery_acceptance.py"),
    Path("tests/test_page_editing_workflow.py"),
    Path("tests/test_page_edit_api_workflow.py"),
}
LEGACY_BASELINE_FILES = {
    Path("tests/test_regression_submission_normalize_constraints_ranking.py"),
    Path("tests/test_pdf_watermark.py"),
}


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        root = Path(str(item.config.rootpath))
        abs_path = Path(str(item.path))
        try:
            rel_path_obj = abs_path.relative_to(root)
        except ValueError:
            rel_path_obj = abs_path
        node_name = item.name

        is_phase2_file = (
            rel_path_obj.parent == Path("tests")
            and rel_path_obj.name.startswith(PHASE2_FILE_PREFIX)
        )
        is_phase2_e2e_node = (
            rel_path_obj == PHASE2_E2E_FILE and node_name.startswith(PHASE2_E2E_NODE_PREFIX)
        )
        is_l3_blocker_file = rel_path_obj in L3_BLOCKER_FILES

        if is_phase2_file or is_phase2_e2e_node:
            item.add_marker(pytest.mark.l2_contract_blocker)
            # Backward-compatible alias while commands migrate to explicit l2/l3 markers.
            item.add_marker(pytest.mark.phase2_acceptance)
            continue

        if is_l3_blocker_file:
            item.add_marker(pytest.mark.l3_handbook_delivery_blocker)
            continue

        if rel_path_obj == PHASE2_E2E_FILE or rel_path_obj in LEGACY_BASELINE_FILES:
            item.add_marker(pytest.mark.legacy_compatibility)
