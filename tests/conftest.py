from __future__ import annotations

from pathlib import Path

import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Auto-apply l2_contract_blocker to all test_phase2_* files."""
    for item in items:
        root = Path(str(item.config.rootpath))
        abs_path = Path(str(item.path))
        try:
            rel_path_obj = abs_path.relative_to(root)
        except ValueError:
            rel_path_obj = abs_path

        if (
            rel_path_obj.parent == Path("tests")
            and rel_path_obj.name.startswith("test_phase2_")
        ):
            item.add_marker(pytest.mark.l2_contract_blocker)
