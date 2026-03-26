#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = REPO_ROOT / "ci" / "ruff_ewf_baseline.json"
RUFF_ARGS = [
    "check",
    "app/",
    "scripts/",
    "--select",
    "E,F,W",
    "--ignore",
    "E501",
    "--output-format",
    "json",
]


def _normalize_path(path: str) -> str:
    p = Path(path)
    if not p.is_absolute():
        p = (REPO_ROOT / p).resolve()
    try:
        rel = p.relative_to(REPO_ROOT)
    except ValueError:
        rel = p
    return rel.as_posix()


def _run_ruff() -> list[dict[str, Any]]:
    proc = subprocess.run(
        [sys.executable, "-m", "ruff", *RUFF_ARGS],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    raw = (proc.stdout or "").strip()
    if not raw:
        if proc.returncode == 0:
            return []
        print(proc.stderr or "ruff returned non-zero without JSON output", file=sys.stderr)
        raise SystemExit(proc.returncode or 1)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print("Failed to parse ruff JSON output:", exc, file=sys.stderr)
        print(raw[:1000], file=sys.stderr)
        raise SystemExit(2) from exc
    if not isinstance(data, list):
        print("Unexpected ruff JSON payload type", file=sys.stderr)
        raise SystemExit(2)
    return data


def _to_keys(items: list[dict[str, Any]]) -> list[str]:
    keys: list[str] = []
    for item in items:
        filename = _normalize_path(str(item.get("filename", "")))
        code = str(item.get("code", ""))
        location = item.get("location") or {}
        row = int(location.get("row", 0))
        column = int(location.get("column", 0))
        keys.append(f"{filename}:{row}:{column}:{code}")
    return sorted(set(keys))


def _load_baseline() -> set[str]:
    if not BASELINE_PATH.exists():
        print(f"Baseline missing: {BASELINE_PATH}", file=sys.stderr)
        print(
            "Run `python scripts/ci/check_ruff_baseline.py --write-baseline` to create one.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    data = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        print("Baseline must be a JSON array", file=sys.stderr)
        raise SystemExit(2)
    return set(str(i) for i in data)


def _write_baseline(keys: list[str]) -> None:
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_PATH.write_text(json.dumps(keys, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote baseline: {BASELINE_PATH} ({len(keys)} entries)")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write-baseline",
        action="store_true",
        help="Update baseline to current ruff findings.",
    )
    args = parser.parse_args()

    findings = _run_ruff()
    keys = _to_keys(findings)

    if args.write_baseline:
        _write_baseline(keys)
        return 0

    baseline = _load_baseline()
    current = set(keys)
    new_issues = sorted(current - baseline)
    resolved = sorted(baseline - current)

    print(
        f"Ruff findings: current={len(current)} baseline={len(baseline)} "
        f"new={len(new_issues)} resolved={len(resolved)}"
    )

    if resolved:
        print("Resolved baseline issues detected (consider refreshing baseline):")
        for item in resolved[:20]:
            print(f"  - {item}")
        if len(resolved) > 20:
            print(f"  ... and {len(resolved) - 20} more")

    if new_issues:
        print("New lint issues (must be fixed or added to baseline intentionally):")
        for item in new_issues[:50]:
            print(f"  - {item}")
        if len(new_issues) > 50:
            print(f"  ... and {len(new_issues) - 50} more")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
