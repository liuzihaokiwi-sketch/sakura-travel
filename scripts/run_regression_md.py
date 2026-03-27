"""
run_regression_md.py

Run regression cases and output a merged Markdown report instead of PDF.
"""
from __future__ import annotations

import asyncio
import os
import time
from datetime import datetime
from pathlib import Path

from app.db.session import AsyncSessionLocal
from scripts.run_regression import (
    _build_case_trace,
    _select_run_cases,
    _env_flag,
    summarize_case_coverage,
    logger,
    run_assertions,
    run_one_case,
)


def generate_regression_md(all_data: list[dict], output_path: str) -> None:
    lines: list[str] = []
    lines.append("# Travel AI Regression Report")
    lines.append("")
    lines.append(f"- Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"- Case count: {len(all_data)}")
    lines.append("")

    coverage = summarize_case_coverage(all_data)

    lines.append("## Coverage By Proof Level")
    lines.append("")
    for proof, count in sorted(coverage["proof_counts"].items()):
        lines.append(f"- {proof}: {count}")
    lines.append("")

    lines.append("## Coverage By Source Set")
    lines.append("")
    for source_set, count in sorted(coverage["source_set_counts"].items()):
        lines.append(f"- {source_set}: {count}")
    lines.append("")

    lines.append("## Case IDs By Proof Level")
    lines.append("")
    for proof, case_ids in sorted(coverage["case_ids_by_proof"].items()):
        lines.append(f"- {proof}: {', '.join(case_ids)}")
    lines.append("")

    total_pass = sum(
        1
        for cd in all_data
        for a in cd.get("_assert_results", [])
        if a.get("passed")
    )
    total_fail = sum(
        1
        for cd in all_data
        for a in cd.get("_assert_results", [])
        if not a.get("passed")
    )
    lines.append("## Assertions")
    lines.append("")
    lines.append(f"- PASS: {total_pass}")
    lines.append(f"- FAIL: {total_fail}")
    lines.append("")

    for cd in all_data:
        case = cd.get("case", {})
        trace = cd.get("case_trace") or _build_case_trace(case)
        days = cd.get("days", [])
        meta = cd.get("plan_meta", {})
        asserts = cd.get("_assert_results", [])

        lines.append(f"## {case.get('case_label', case.get('case_id', 'case'))}")
        lines.append("")
        lines.append(f"- case_id: `{case.get('case_id', '')}`")
        lines.append(f"- description: {case.get('case_desc', '')}")
        lines.append(f"- proof_level: `{trace.get('proof_level', 'unknown')}`")
        lines.append(f"- source_set: `{trace.get('source_set', 'unknown')}`")
        lines.append(f"- entry_anchor: `{trace.get('entry_anchor', 'unknown')}`")
        if trace.get("coverage_notes"):
            lines.append(f"- coverage_notes: {trace.get('coverage_notes')}")
        observation_chain = (cd.get("evidence_bundle") or {}).get("observation_chain", {})
        if observation_chain:
            lines.append(f"- observation_chain: `{observation_chain}`")
        lines.append(f"- day_count: {len(days)}")
        lines.append(f"- cities: {', '.join(meta.get('actual_cities', []) or [])}")
        lines.append(f"- hotel_cities: {', '.join(meta.get('hotel_cities', []) or [])}")
        lines.append("")

        lines.append("### Assertion Results")
        lines.append("")
        if not asserts:
            lines.append("- no assertions")
        else:
            for a in asserts:
                mark = "PASS" if a.get("passed") else "FAIL"
                detail = a.get("detail", "")
                if detail:
                    lines.append(f"- [{mark}] {a.get('name', '')}: {detail}")
                else:
                    lines.append(f"- [{mark}] {a.get('name', '')}")
        lines.append("")

        lines.append("### Itinerary Summary")
        lines.append("")
        if not days:
            lines.append("- no itinerary data")
        else:
            for d in days:
                lines.append(
                    f"- Day {d.get('day_number', '?')} | "
                    f"{d.get('city', '')} | {d.get('theme', '')} | {d.get('day_type', '')}"
                )
        lines.append("")

    Path(output_path).write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[OK] Markdown: {output_path}")


async def main() -> None:
    t0 = time.time()
    print("\n" + "=" * 70)
    print("  Travel AI - Regression (Markdown)")
    print("=" * 70 + "\n")

    all_data: list[dict] = []
    case_filter = {c.strip() for c in os.getenv("REGRESSION_CASE_IDS", "").split(",") if c.strip()}
    run_phase2 = _env_flag("REGRESSION_INCLUDE_PHASE2", default=False)
    run_cases = _select_run_cases(run_phase2=run_phase2, case_filter=case_filter)
    logger.info("cases selected: %d include_phase2=%s", len(run_cases), run_phase2)
    if not run_phase2:
        logger.warning("REGRESSION_INCLUDE_PHASE2 is off; markdown report covers compatibility baseline only by default")

    async with AsyncSessionLocal() as session:
        for case in run_cases:
            try:
                cd = await run_one_case(case, session)
                cd["_assert_results"] = run_assertions(cd)
                all_data.append(cd)
            except Exception as exc:
                logger.error("case %s failed: %s", case.get("case_id"), exc, exc_info=True)
                all_data.append(
                    {
                        "case": case,
                        "case_trace": _build_case_trace(case),
                        "profile_summary": case.get("profile_summary", {}),
                        "days": [],
                        "plan_meta": {},
                        "dates": case.get("travel_dates", {}),
                        "_assert_results": [{"name": "execute", "passed": False, "detail": str(exc)}],
                    }
                )

    ts = time.strftime("%H%M%S")
    output = str(Path(__file__).parent / f"regression_report_{ts}.md")
    generate_regression_md(all_data, output)

    elapsed = time.time() - t0
    total_pass = sum(1 for cd in all_data for a in cd.get("_assert_results", []) if a.get("passed"))
    total_fail = sum(1 for cd in all_data for a in cd.get("_assert_results", []) if not a.get("passed"))
    print(f"\n{'=' * 70}")
    print(f"  Total: {total_pass} PASS / {total_fail} FAIL ({elapsed:.1f}s)")
    if not run_phase2:
        print("  note: main_chain_proof coverage not included (set REGRESSION_INCLUDE_PHASE2=1)")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    asyncio.run(main())



