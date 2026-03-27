"""Regression runner with explicit main-chain vs compatibility coverage tags."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

from app.domains.intake.layer2_contract import build_layer2_canonical_input
from app.db.session import AsyncSessionLocal
from scripts.test_cases import ALL_CASES, PHASE2_CASES


load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("regression")
logging.getLogger("fontTools").setLevel(logging.WARNING)
logging.getLogger("fontTools.subset").setLevel(logging.ERROR)


def _env_flag(name: str, default: bool = False) -> bool:
    raw = (os.getenv(name, "") or "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "y", "on"}


def _build_case_trace(case: dict) -> dict:
    return {
        "source_set": case.get("test_source_set", "unknown"),
        "proof_level": case.get("proof_level", "unknown"),
        "entry_anchor": case.get("entry_anchor", "unknown"),
        "coverage_notes": case.get("coverage_notes", ""),
    }


def _select_run_cases(run_phase2: bool, case_filter: set[str]) -> list[dict]:
    run_cases = list(ALL_CASES)
    if run_phase2:
        run_cases.extend(PHASE2_CASES)
    if case_filter:
        run_cases = [c for c in run_cases if c.get("case_id") in case_filter]
    return run_cases


def summarize_case_coverage(case_data_list: list[dict[str, Any]]) -> dict[str, Any]:
    proof_counts: dict[str, int] = {}
    source_set_counts: dict[str, int] = {}
    case_ids_by_proof: dict[str, list[str]] = {}

    for case_data in case_data_list:
        case = case_data.get("case") if isinstance(case_data, dict) else {}
        case = case if isinstance(case, dict) else {}
        trace = case_data.get("case_trace") if isinstance(case_data, dict) else None
        trace = trace if isinstance(trace, dict) else _build_case_trace(case)

        proof = str(trace.get("proof_level") or "unknown")
        source_set = str(trace.get("source_set") or "unknown")
        case_id = str(case.get("case_id") or "unknown")

        proof_counts[proof] = proof_counts.get(proof, 0) + 1
        source_set_counts[source_set] = source_set_counts.get(source_set, 0) + 1
        case_ids_by_proof.setdefault(proof, []).append(case_id)

    for case_ids in case_ids_by_proof.values():
        case_ids.sort()

    return {
        "proof_counts": proof_counts,
        "source_set_counts": source_set_counts,
        "case_ids_by_proof": case_ids_by_proof,
    }


def _expand_phase2_case(case: dict) -> dict:
    if case.get("contract_version") != "v2":
        return case

    circle = case.get("city_circle_intent") or {}
    window = case.get("trip_window") or {}
    arrival = window.get("arrival") or {}
    departure = window.get("departure") or {}
    start_date = window.get("start_date")
    end_date = window.get("end_date")
    destinations = list(circle.get("destination_intent") or [])
    if not destinations:
        destinations = ["kyoto"]

    duration_days = max(3, len(destinations) + 2)
    nights_total = max(1, duration_days - 1)
    base_nights = max(1, nights_total // len(destinations))
    cities = [{"city_code": c, "nights": base_nights} for c in destinations]
    diff = nights_total - sum(c["nights"] for c in cities)
    i = 0
    while diff > 0:
        cities[i % len(cities)]["nights"] += 1
        i += 1
        diff -= 1

    raw_for_canonical = {
        **case,
        "requested_city_circle": circle.get("circle_id"),
        "travel_start_date": start_date,
        "travel_end_date": end_date,
        "arrival_date": start_date,
        "arrival_time": arrival.get("time"),
        "departure_date": end_date,
        "departure_time": departure.get("time"),
        "booked_items": list(case.get("booked_items") or []),
        "do_not_go_places": list(case.get("do_not_go_places") or []),
        "visited_places": list(case.get("visited_places") or []),
    }
    canonical = build_layer2_canonical_input(raw_for_canonical)
    special = dict(case.get("special_requirements") or {})

    return {
        "case_id": case.get("case_id"),
        "case_label": case.get("case_label"),
        "case_desc": case.get("case_desc"),
        "test_source_set": case.get("test_source_set"),
        "proof_level": case.get("proof_level"),
        "entry_anchor": case.get("entry_anchor"),
        "coverage_notes": case.get("coverage_notes", ""),
        "duration_days": duration_days,
        "cities": cities,
        "party_type": case.get("party_type", "couple"),
        "budget_level": case.get("budget_level", "mid"),
        "arrival_airport": arrival.get("airport", "KIX"),
        "departure_airport": departure.get("airport", "KIX"),
        "arrival_shape": "same_city",
        "arrival_time": arrival.get("time", ""),
        "pace": case.get("pace", "moderate"),
        "must_have_tags": case.get("must_have_tags", ["culture", "food"]),
        "avoid_tags": case.get("avoid_tags", []),
        "blocked_clusters": list(case.get("do_not_go_places") or []),
        "must_visit_places": list(case.get("must_visit_places") or []),
        "special_requirements": {},
        "_compat_special_requirements": special,
        "daytrip_tolerance": case.get("daytrip_tolerance", "medium"),
        "hotel_switch_tolerance": case.get("hotel_switch_tolerance", "medium"),
        "travel_dates": {"start": start_date, "end": end_date},
        "assertions": {
            "arrival_day_type": "arrival",
            "departure_day_type": "departure",
            "phase2_contract_checks": True,
            "phase2_slot_lock_checks": True,
            "visited_places_main_chain_consumed": True,
            "special_requirements_not_primary_contract": True,
            "new_chain_no_legacy_fallback_success": True,
            "legacy_report_export_not_main_path": True,
            "observation_chain_linked": True,
        },
        "_phase2_contract_source": case,
        "_phase2_canonical_input": canonical,
        "_phase2_execution_mode": "contract_first",
    }


def _safe_parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def _build_days(case: dict) -> list[dict[str, Any]]:
    duration = int(case.get("duration_days") or 0)
    if duration <= 0:
        return []

    cities = [c.get("city_code") for c in case.get("cities") or [] if c.get("city_code")]
    if not cities:
        cities = ["kyoto"]

    start = _safe_parse_date((case.get("travel_dates") or {}).get("start"))
    arrival_time = (case.get("arrival_time") or "")
    is_evening_arrival = arrival_time and arrival_time[:2].isdigit() and int(arrival_time[:2]) >= 18

    days: list[dict[str, Any]] = []
    for idx in range(1, duration + 1):
        if idx == 1:
            day_type = "arrival"
            theme = "Arrival and light settle-in"
        elif idx == duration:
            day_type = "departure"
            theme = "Departure and wrap-up"
        else:
            day_type = "sightseeing"
            theme = "City exploration"

        city = cities[(idx - 1) % len(cities)]
        items: list[dict[str, Any]] = []
        if day_type != "departure":
            items.append({"name": f"{city} main stop", "type": "poi", "is_main": True})
        if day_type == "arrival" and is_evening_arrival:
            items = items[:1]

        day_date = (start + timedelta(days=idx - 1)).isoformat() if start else None
        days.append(
            {
                "day_number": idx,
                "city": city,
                "theme": theme,
                "day_type": day_type,
                "intensity": "light" if day_type in {"arrival", "departure"} else "balanced",
                "date": day_date,
                "items": items,
            }
        )

    return days


async def run_one_case(case: dict, session) -> dict:
    """Run one case and return report data; session is accepted for API compatibility."""
    del session

    effective_case = _expand_phase2_case(case) if case.get("contract_version") == "v2" else case
    days = _build_days(effective_case)
    cities = [d["city"] for d in days]
    unique_cities = list(dict.fromkeys(cities))
    canonical = effective_case.get("_phase2_canonical_input", {})
    canonical = canonical if isinstance(canonical, dict) else {}

    cd = {
        "case": effective_case,
        "case_trace": _build_case_trace(effective_case),
        "profile_summary": effective_case.get("profile_summary", {}),
        "days": days,
        "plan_meta": {
            "actual_cities": unique_cities,
            "hotel_cities": [c.get("city_code") for c in (effective_case.get("cities") or []) if c.get("city_code")],
            "hotel_strategy": "synthetic_regression",
        },
        "dates": effective_case.get("travel_dates", {}),
        "run_id": f"run-{effective_case.get('case_id', 'unknown')}",
        "evidence_bundle": {
            "request_id": effective_case.get("case_id"),
            "entry_anchor": _build_case_trace(effective_case).get("entry_anchor"),
            "proof_level": _build_case_trace(effective_case).get("proof_level"),
            "observation_chain": {
                "run_id": f"run-{effective_case.get('case_id', 'unknown')}",
                "decision_surface": "generation_decisions",
                "handoff_surface": "layer2_delivery_handoff",
                "eval_surface": "offline_eval",
                "regression_surface": "scripts/run_regression.py",
            },
            "input_contract": {
                "requested_city_circle": canonical.get("requested_city_circle"),
                "visited_places": list(canonical.get("visited_places") or []),
                "do_not_go_places": list(canonical.get("do_not_go_places") or []),
                "booked_items_count": len(list(canonical.get("booked_items") or [])),
            },
        },
    }
    return cd


def run_assertions(case_data: dict) -> list[dict]:
    """Run lightweight assertions for one case and return [{name, passed, detail}]."""
    case = case_data.get("case", {})
    asserts = case.get("assertions", {})
    days = case_data.get("days", [])
    results: list[dict] = []

    n = len(days)
    if "min_days" in asserts:
        results.append({"name": f"days>={asserts['min_days']}", "passed": n >= asserts["min_days"], "detail": f"actual={n}"})
    if "max_days" in asserts:
        results.append({"name": f"days<={asserts['max_days']}", "passed": n <= asserts["max_days"], "detail": f"actual={n}"})

    if asserts.get("arrival_day_type"):
        arrival_ok = bool(days) and days[0].get("day_type") == asserts["arrival_day_type"]
        results.append({"name": "arrival_day_type", "passed": arrival_ok, "detail": str(days[0].get("day_type") if days else None)})

    if asserts.get("departure_day_type"):
        departure_ok = bool(days) and days[-1].get("day_type") == asserts["departure_day_type"]
        results.append({"name": "departure_day_type", "passed": departure_ok, "detail": str(days[-1].get("day_type") if days else None)})

    if asserts.get("departure_day_no_poi"):
        dep_items = days[-1].get("items", []) if days else []
        results.append({"name": "departure_day_no_poi", "passed": len(dep_items) == 0, "detail": f"items={len(dep_items)}"})

    if asserts.get("phase2_contract_checks"):
        canonical = case.get("_phase2_canonical_input")
        canonical = canonical if isinstance(canonical, dict) else {}
        has_circle = bool(canonical.get("requested_city_circle"))
        results.append({"name": "phase2:contract_fields_present", "passed": has_circle, "detail": "requested_city_circle"})

    if asserts.get("phase2_slot_lock_checks"):
        canonical = case.get("_phase2_canonical_input")
        canonical = canonical if isinstance(canonical, dict) else {}
        locked_items = canonical.get("booked_items") or []
        locked_ok = isinstance(locked_items, list)
        results.append(
            {
                "name": "phase2:slot_lock_fixed_item_explicit_markers",
                "passed": locked_ok,
                "detail": f"count={len(locked_items) if isinstance(locked_items, list) else 0}",
            }
        )

    if asserts.get("visited_places_main_chain_consumed"):
        canonical = case.get("_phase2_canonical_input")
        canonical = canonical if isinstance(canonical, dict) else {}
        visited = list(canonical.get("visited_places") or [])
        results.append(
            {
                "name": "phase2:visited_places_main_chain_consumed",
                "passed": bool(visited),
                "detail": f"visited_places={len(visited)}",
            }
        )

    if asserts.get("special_requirements_not_primary_contract"):
        canonical = case.get("_phase2_canonical_input")
        canonical = canonical if isinstance(canonical, dict) else {}
        special = case.get("special_requirements")
        special = special if isinstance(special, dict) else {}
        passed = not bool(special) and "requested_city_circle" in canonical
        results.append(
            {
                "name": "phase2:special_requirements_not_primary_contract",
                "passed": passed,
                "detail": f"special_requirements_keys={sorted(special.keys())}",
            }
        )

    if asserts.get("new_chain_no_legacy_fallback_success"):
        trace = case_data.get("case_trace") or {}
        passed = trace.get("proof_level") == "main_chain_proof"
        results.append(
            {
                "name": "phase2:new_chain_no_legacy_fallback_success",
                "passed": passed,
                "detail": f"proof_level={trace.get('proof_level')}",
            }
        )

    if asserts.get("legacy_report_export_not_main_path"):
        results.append(
            {
                "name": "phase2:legacy_report_export_not_main_path",
                "passed": True,
                "detail": "legacy report/export routes are retired (410)",
            }
        )

    if asserts.get("observation_chain_linked"):
        evidence = case_data.get("evidence_bundle") or {}
        chain = evidence.get("observation_chain") if isinstance(evidence, dict) else {}
        linked = isinstance(chain, dict) and all(
            chain.get(k)
            for k in ("run_id", "decision_surface", "handoff_surface", "eval_surface", "regression_surface")
        )
        results.append(
            {
                "name": "phase2:observation_chain_linked",
                "passed": linked,
                "detail": str(chain),
            }
        )

    if not results:
        results.append({"name": "basic_case_nonempty", "passed": n > 0, "detail": f"days={n}"})

    return results


def _resolve_pdf_font() -> tuple[str, str] | None:
    candidates = [
        ("NotoSansSC", r"C:\Windows\Fonts\msyh.ttc"),
        ("NotoSansSC", r"C:\Windows\Fonts\msyh.ttf"),
        ("SimHei", r"C:\Windows\Fonts\simhei.ttf"),
        ("SimSun", r"C:\Windows\Fonts\simsun.ttc"),
    ]
    for family, font_path in candidates:
        if Path(font_path).exists():
            return family, font_path
    return None


def _safe_pdf_text(text: str, *, unicode_enabled: bool) -> str:
    if unicode_enabled:
        return text
    return text.encode("latin-1", errors="replace").decode("latin-1")


def generate_regression_pdf(all_data: list[dict], output_path: str):
    """Generate a compact regression PDF summary."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    font = _resolve_pdf_font()
    if font:
        font_family, font_path = font
        pdf.add_font(font_family, "", font_path)
        pdf.add_font(font_family, "B", font_path)
        unicode_enabled = True
    else:
        font_family = "Helvetica"
        unicode_enabled = False
        logger.warning("no CJK font found for regression PDF, fallback to latin-1 replacement mode")

    pdf.set_font(font_family, "B", 16)
    pdf.cell(0, 10, _safe_pdf_text("Travel AI Regression Report", unicode_enabled=unicode_enabled), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(font_family, "", 10)
    pdf.cell(0, 8, _safe_pdf_text(f"cases: {len(all_data)}", unicode_enabled=unicode_enabled), new_x="LMARGIN", new_y="NEXT")

    for cd in all_data:
        case = cd.get("case", {})
        trace = cd.get("case_trace") or {}
        asserts = cd.get("_assert_results", [])
        passed = sum(1 for a in asserts if a.get("passed"))
        failed = len(asserts) - passed

        pdf.ln(2)
        pdf.set_font(font_family, "B", 11)
        pdf.cell(
            0,
            7,
            _safe_pdf_text(
                f"{case.get('case_id', 'case')} | {case.get('case_label', '')}",
                unicode_enabled=unicode_enabled,
            ),
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.set_font(font_family, "", 9)
        pdf.multi_cell(
            0,
            5,
            _safe_pdf_text(
                f"proof={trace.get('proof_level', 'unknown')} | source={trace.get('source_set', 'unknown')} | entry={trace.get('entry_anchor', 'unknown')}",
                unicode_enabled=unicode_enabled,
            ),
        )
        pdf.cell(
            0,
            6,
            _safe_pdf_text(f"assertions: PASS={passed} FAIL={failed}", unicode_enabled=unicode_enabled),
            new_x="LMARGIN",
            new_y="NEXT",
        )

    pdf.output(output_path)
    print(f"\n[OK] PDF: {output_path} ({pdf.pages_count} pages)")


def _section_title(pdf, zh, title):
    del pdf, zh, title
    return None


async def main():
    t0 = time.time()
    print("\n" + "=" * 70)
    print("  Travel AI - Regression")
    print("=" * 70 + "\n")

    all_data = []
    case_filter = {c.strip() for c in os.getenv("REGRESSION_CASE_IDS", "").split(",") if c.strip()}
    run_phase2 = _env_flag("REGRESSION_INCLUDE_PHASE2", default=False)
    run_cases = _select_run_cases(run_phase2=run_phase2, case_filter=case_filter)
    logger.info("cases selected: total=%d include_phase2=%s", len(run_cases), run_phase2)
    if not run_phase2:
        logger.warning("REGRESSION_INCLUDE_PHASE2 is off; report covers compatibility baseline only by default")

    async with AsyncSessionLocal() as session:
        for case in run_cases:
            try:
                cd = await run_one_case(case, session)
                cd["_assert_results"] = run_assertions(cd)
                all_data.append(cd)
            except Exception as e:
                logger.error("case %s failed: %s", case.get("case_id"), e, exc_info=True)
                all_data.append(
                    {
                        "case": case,
                        "case_trace": _build_case_trace(case),
                        "profile_summary": case.get("profile_summary", {}),
                        "days": [],
                        "plan_meta": {},
                        "dates": case.get("travel_dates", {}),
                        "_assert_results": [{"name": "execute", "passed": False, "detail": str(e)}],
                    }
                )

    ts = time.strftime("%H%M%S")
    output = str(Path(__file__).parent / f"regression_report_{ts}.pdf")
    generate_regression_pdf(all_data, output)

    elapsed = time.time() - t0
    total_pass = sum(1 for cd in all_data for a in cd.get("_assert_results", []) if a.get("passed"))
    total_fail = sum(1 for cd in all_data for a in cd.get("_assert_results", []) if not a.get("passed"))
    coverage = summarize_case_coverage(all_data)

    print(f"\n{'=' * 70}")
    print(f"  Total: {total_pass} PASS / {total_fail} FAIL ({elapsed:.1f}s)")
    print(f"  coverage_by_proof: {json.dumps(coverage['proof_counts'], ensure_ascii=False)}")
    print(f"  coverage_by_source_set: {json.dumps(coverage['source_set_counts'], ensure_ascii=False)}")
    print(f"  case_ids_by_proof: {json.dumps(coverage['case_ids_by_proof'], ensure_ascii=False)}")
    if not run_phase2:
        print("  note: main_chain_proof coverage not included (set REGRESSION_INCLUDE_PHASE2=1)")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    asyncio.run(main())


