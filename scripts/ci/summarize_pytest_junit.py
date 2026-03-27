from __future__ import annotations

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET


def _read_root(path: Path) -> ET.Element:
    tree = ET.parse(path)
    return tree.getroot()


def _suite_list(root: ET.Element) -> list[ET.Element]:
    if root.tag == "testsuite":
        return [root]
    return [suite for suite in root.findall("testsuite")]


def _to_int(value: str | None) -> int:
    if not value:
        return 0
    try:
        return int(value)
    except ValueError:
        return 0


def _to_float(value: str | None) -> float:
    if not value:
        return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def _collect_failed_cases(root: ET.Element) -> list[str]:
    cases: list[str] = []
    for testcase in root.iter("testcase"):
        failure = testcase.find("failure")
        error = testcase.find("error")
        if failure is None and error is None:
            continue
        classname = testcase.attrib.get("classname", "")
        name = testcase.attrib.get("name", "")
        detail = failure if failure is not None else error
        detail_message = (detail.attrib.get("message", "") if detail is not None else "").strip()
        first_line = detail_message.splitlines()[0] if detail_message else ""
        identifier = f"{classname}.{name}" if classname else name
        if first_line:
            cases.append(f"{identifier} :: {first_line}")
        else:
            cases.append(identifier)
    return cases


def _build_summary_markdown(
    *,
    tests: int,
    failures: int,
    errors: int,
    skipped: int,
    duration: float,
    failed_cases: list[str],
) -> str:
    lines = [
        "## Legacy Compatibility Nightly",
        "",
        f"- tests: `{tests}`",
        f"- failures: `{failures}`",
        f"- errors: `{errors}`",
        f"- skipped: `{skipped}`",
        f"- duration_seconds: `{duration:.2f}`",
    ]
    if failed_cases:
        lines.append("- failed_cases:")
        lines.extend([f"  - `{case}`" for case in failed_cases])
    else:
        lines.append("- failed_cases: `none`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize pytest JUnit XML for legacy nightly monitoring.")
    parser.add_argument("--junit", required=True, help="Path to junit.xml file.")
    parser.add_argument("--summary-md", required=True, help="Output markdown summary path.")
    parser.add_argument("--failed-list", required=True, help="Output failed test list path.")
    args = parser.parse_args()

    junit_path = Path(args.junit)
    summary_path = Path(args.summary_md)
    failed_path = Path(args.failed_list)

    root = _read_root(junit_path)
    suites = _suite_list(root)
    tests = sum(_to_int(suite.attrib.get("tests")) for suite in suites)
    failures = sum(_to_int(suite.attrib.get("failures")) for suite in suites)
    errors = sum(_to_int(suite.attrib.get("errors")) for suite in suites)
    skipped = sum(_to_int(suite.attrib.get("skipped")) for suite in suites)
    duration = sum(_to_float(suite.attrib.get("time")) for suite in suites)
    failed_cases = _collect_failed_cases(root)

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    failed_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        _build_summary_markdown(
            tests=tests,
            failures=failures,
            errors=errors,
            skipped=skipped,
            duration=duration,
            failed_cases=failed_cases,
        ),
        encoding="utf-8",
    )
    if failed_cases:
        failed_path.write_text("\n".join(failed_cases) + "\n", encoding="utf-8")
    else:
        failed_path.write_text("none\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
