from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

L2_MARKER = "l2_contract_blocker"
L3_MARKER = "l3_handbook_delivery_blocker"


def _paths_for_marker(marker: str) -> list[str]:
    if marker == L2_MARKER:
        phase2_files = sorted(str(p) for p in Path("tests").glob("test_phase2_*.py"))
        return [*phase2_files, "tests/e2e/test_full_pipeline.py"]
    if marker == L3_MARKER:
        return [
            "tests/test_layer2_delivery_handoff.py",
            "tests/test_shared_export_contract.py",
            "tests/test_handbook_delivery_acceptance.py",
            "tests/test_page_editing_workflow.py",
            "tests/test_page_edit_api_workflow.py",
        ]
    return []


def _run_marker(marker: str, passthrough: list[str]) -> int:
    paths = _paths_for_marker(marker)
    cmd = [sys.executable, "-m", "pytest", "-m", marker, *paths, *passthrough]
    print(f"[dual-track] running: {' '.join(cmd)}")
    completed = subprocess.run(cmd, check=False)
    print(f"[dual-track] marker={marker} exit_code={completed.returncode}")
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run layered tests with explicit policy: "
            "L2 and L3 are blocking."
        )
    )
    parser.add_argument(
        "--l2-only",
        action="store_true",
        help="Run only l2_contract_blocker (contract-first primary gate).",
    )
    parser.add_argument(
        "--l3-only",
        action="store_true",
        help="Run only l3_handbook_delivery_blocker (handbook delivery acceptance gate).",
    )
    parser.add_argument(
        "--blockers-only",
        action="store_true",
        help="Run L2 and L3 blockers only (both blocking).",
    )
    parser.add_argument(
        "--phase2-only",
        action="store_true",
        help=argparse.SUPPRESS,  # backward-compatible alias for --l2-only
    )
    parser.add_argument(
        "--legacy-only",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--strict-legacy",
        action="store_true",
        help=argparse.SUPPRESS,
    )

    args, passthrough = parser.parse_known_args()

    if args.phase2_only:
        args.l2_only = True

    enabled_primary_modes = [args.l2_only, args.l3_only, args.blockers_only]
    if sum(bool(x) for x in enabled_primary_modes) > 1:
        parser.error("--l2-only/--l3-only/--blockers-only cannot be combined")

    if args.l2_only:
        return _run_marker(L2_MARKER, passthrough)

    if args.l3_only:
        return _run_marker(L3_MARKER, passthrough)

    if args.blockers_only:
        l2_code = _run_marker(L2_MARKER, passthrough)
        if l2_code != 0:
            print("[dual-track] l2_contract_blocker failed: this is blocking.")
            return l2_code
        l3_code = _run_marker(L3_MARKER, passthrough)
        if l3_code != 0:
            print("[dual-track] l3_handbook_delivery_blocker failed: this is blocking.")
            return l3_code
        return 0

    l2_code = _run_marker(L2_MARKER, passthrough)
    if l2_code != 0:
        print("[dual-track] l2_contract_blocker failed: this is blocking.")
        return l2_code

    l3_code = _run_marker(L3_MARKER, passthrough)
    if l3_code != 0:
        print("[dual-track] l3_handbook_delivery_blocker failed: this is blocking.")
        return l3_code

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
