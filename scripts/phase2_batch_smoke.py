from __future__ import annotations

import asyncio
import json
import logging
import traceback

from app.db.session import AsyncSessionLocal
from scripts.run_regression import _build_case_trace, _expand_phase2_case, run_assertions, run_one_case
from scripts.test_cases import PHASE2_CASES


def _classify_fail(assert_results: list[dict], error_text: str) -> str:
    if error_text:
        t = error_text.lower()
        if "connectionrefusederror" in t or "winerror 1225" in t:
            return "db_connection_refused"
        if "does not exist" in t or "undefinedtable" in t:
            return "seed_or_schema_missing"
        return "runtime_exception"

    failed_names = [a.get("name", "") for a in assert_results if not a.get("passed")]
    if not failed_names:
        return "pass"
    if any("slot_lock_fixed_item_explicit_markers" in n for n in failed_names):
        return "fixed_item_lock_marker_missing"
    if any(n.startswith("phase2:") for n in failed_names):
        return "phase2_assertion_failed"
    return "general_assertion_failed"


async def main() -> int:
    logging.disable(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("regression").setLevel(logging.WARNING)
    logging.getLogger("app.domains.planning.constraint_compiler").setLevel(logging.WARNING)
    logging.getLogger("app.domains.planning.route_skeleton_builder").setLevel(logging.WARNING)
    logging.getLogger("app.domains.planning.meal_flex_filler").setLevel(logging.WARNING)

    print("phase2_batch_smoke: running PHASE2_CASES")
    print(f"case_count={len(PHASE2_CASES)}")
    print("-" * 72)

    rows = []
    async with AsyncSessionLocal() as session:
        for raw_case in PHASE2_CASES:
            case = _expand_phase2_case(raw_case)
            case_id = case.get("case_id", "<unknown>")
            error_text = ""
            try:
                case_data = await run_one_case(case, session)
                assert_results = run_assertions(case_data)
                passed = all(a.get("passed") for a in assert_results)
                failed = [a for a in assert_results if not a.get("passed")]
                case_trace = case_data.get("case_trace") or _build_case_trace(case)
            except Exception:
                passed = False
                failed = []
                error_text = traceback.format_exc(limit=20)
                assert_results = []
                case_trace = _build_case_trace(case)

            reason = _classify_fail(assert_results, error_text)
            fail_count = len(failed)
            first_fail = failed[0]["name"] if failed else ""
            rows.append(
                {
                    "case_id": case_id,
                    "passed": passed,
                    "fail_count": fail_count,
                    "first_fail": first_fail,
                    "reason_class": reason,
                    "proof_level": case_trace.get("proof_level", "unknown"),
                    "source_set": case_trace.get("source_set", "unknown"),
                    "entry_anchor": case_trace.get("entry_anchor", "unknown"),
                }
            )
            status = "PASS" if passed else "FAIL"
            trace_tail = f" | proof={case_trace.get('proof_level', 'unknown')}"
            tail = "" if passed else f" | reason={reason} | first_fail={first_fail or 'runtime_error'}"
            print(f"{status:4s} {case_id}{trace_tail}{tail}")

    print("-" * 72)
    pass_count = sum(1 for r in rows if r["passed"])
    fail_count = len(rows) - pass_count
    print(f"summary: PASS={pass_count} FAIL={fail_count}")

    print("summary_json:")
    print(json.dumps(rows, ensure_ascii=False, indent=2))

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
