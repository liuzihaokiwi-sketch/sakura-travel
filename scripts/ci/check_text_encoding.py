#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

TEXT_EXTENSIONS = {
    ".md",
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".json",
    ".yml",
    ".yaml",
}

SCAN_ROOTS = [
    Path(".github/workflows"),
    Path("docs/architecture"),
    Path("docs/testing_layers.md"),
    Path("docs/encoding_guardrail.md"),
    Path("app/api/trips_generate.py"),
    Path("app/domains/planning/fusion_refinement.py"),
    Path("app/domains/rendering/page_editing.py"),
    Path("app/domains/rendering/shared_export_contract.py"),
    Path("web/app/api/plan/[id]/page-overrides/route.ts"),
    Path("web/app/plan/[id]/edit/page.tsx"),
    Path("scripts/ci/check_text_encoding.py"),
]

SKIP_PATHS = {
    Path("scripts/ci/check_text_encoding.py"),
}

MOJIBAKE_MARKERS = [
    "锘",
    "锟",
    "�",
    "涓",
    "鍙",
    "鏈",
    "鐨",
    "鎴",
    "妯",
    "璇",
    "闃",
    "绗",
    "閲",
]


def iter_targets() -> list[Path]:
    root = Path.cwd()
    targets: list[Path] = []

    for raw_path in SCAN_ROOTS:
        path = root / raw_path
        if not path.exists():
            continue
        if path.is_file():
            if path.suffix.lower() in TEXT_EXTENSIONS:
                targets.append(path)
            continue
        for child in path.rglob("*"):
            if child.is_file() and child.suffix.lower() in TEXT_EXTENSIONS:
                targets.append(child)

    deduped: list[Path] = []
    seen = set()
    for item in targets:
        rel = item.relative_to(root)
        if rel in SKIP_PATHS or rel in seen:
            continue
        seen.add(rel)
        deduped.append(item)
    return deduped


def main() -> int:
    root = Path.cwd()
    failures: list[str] = []

    for path in iter_targets():
        rel = path.relative_to(root)
        data = path.read_bytes()

        if data.startswith(b"\xef\xbb\xbf"):
            failures.append(f"BOM detected: {rel}")

        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            failures.append(f"Non-UTF-8 file: {rel} ({exc})")
            continue

        hit = next((marker for marker in MOJIBAKE_MARKERS if marker in text), None)
        if hit is not None:
            failures.append(f"Suspicious mojibake marker '{hit}' in: {rel}")

    if failures:
        print("Encoding check failed:", file=sys.stderr)
        for item in failures:
            print(f"- {item}", file=sys.stderr)
        return 1

    print("Encoding check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
