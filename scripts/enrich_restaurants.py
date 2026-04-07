"""
Restaurant enrichment script.

Reads restaurants_selection_ledger.json, enriches with coordinates and prices
from a manually-curated enrichment data file, outputs restaurants_enriched.csv.

Usage:
    python scripts/enrich_restaurants.py                    # merge + output CSV
    python scripts/enrich_restaurants.py --search-urls      # search Tabelog URLs via OpenCLI
    python scripts/enrich_restaurants.py --audit-ai         # audit ai_generated entries
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LEDGER_PATH = BASE_DIR / "data" / "kansai_spots" / "restaurants_selection_ledger.json"
ENRICHMENT_PATH = BASE_DIR / "data" / "kansai_spots" / "discovery_pool" / "restaurants_enrichment_data.json"
OUTPUT_CSV = BASE_DIR / "data" / "kansai_spots" / "discovery_pool" / "restaurants_enriched.csv"
OPENCLI_DIR = BASE_DIR / "opencli-main"

CITY_TO_PREF = {
    "osaka": "osaka",
    "kyoto": "kyoto",
    "hyogo": "hyogo",
    "nara": "nara",
    "akashi": "hyogo",
    "kobe": "hyogo",
}


def load_ledger() -> list[dict]:
    with open(LEDGER_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["entries"]


def load_enrichment() -> dict:
    if ENRICHMENT_PATH.exists():
        with open(ENRICHMENT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_enrichment(data: dict) -> None:
    with open(ENRICHMENT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def search_tabelog_url(name_ja: str, city_code: str, cuisine: str) -> str | None:
    """Use OpenCLI to search for a restaurant's Tabelog URL."""
    pref = CITY_TO_PREF.get(city_code, city_code)
    query = f"{name_ja} {pref} tabelog"

    try:
        result = subprocess.run(
            f'npx opencli google search "{query}"',
            capture_output=True,
            text=True,
            cwd=str(OPENCLI_DIR),
            timeout=30,
            encoding="utf-8",
            shell=True,
        )
        output = result.stdout

        # Extract tabelog URLs from the output
        urls = re.findall(r"https?://(?:s\.)?tabelog\.com/\w+/A\d+/A\d+/(\d+)/", output)
        if urls:
            # Reconstruct the full URL using the first match
            # Find the full URL pattern
            full_urls = re.findall(
                r"https?://(?:s\.)?tabelog\.com/\w+/A\d+/A\d+/\d+/", output
            )
            if full_urls:
                url = full_urls[0]
                # Normalize to non-s. version
                url = url.replace("https://s.tabelog.com/", "https://tabelog.com/")
                return url
    except (subprocess.TimeoutExpired, Exception) as e:
        print(f"  Error searching for {name_ja}: {e}", file=sys.stderr)

    return None


def search_urls_mode(entries: list[dict], enrichment: dict, grades: list[str]) -> None:
    """Search Tabelog URLs for restaurants of specified grades."""
    targets = [e for e in entries if e.get("grade") in grades]
    print(f"Searching Tabelog URLs for {len(targets)} restaurants (grades: {grades})")

    found = 0
    skipped = 0
    for i, entry in enumerate(targets):
        name = entry["name_ja"]
        key = name  # use name_ja as key

        # Skip if already have a tabelog_url
        if key in enrichment and enrichment[key].get("tabelog_url"):
            skipped += 1
            continue

        print(f"[{i+1}/{len(targets)}] Searching: {name} ({entry['city_code']})...")
        url = search_tabelog_url(name, entry["city_code"], entry.get("cuisine_normalized", ""))

        if url:
            if key not in enrichment:
                enrichment[key] = {}
            enrichment[key]["tabelog_url"] = url
            enrichment[key]["name_ja"] = name
            enrichment[key]["city_code"] = entry["city_code"]
            enrichment[key]["grade"] = entry.get("grade")
            found += 1
            print(f"  Found: {url}")
        else:
            print(f"  Not found")

        # Rate limit
        time.sleep(2)

    save_enrichment(enrichment)
    print(f"\nDone. Found {found} new URLs, skipped {skipped} existing. Total in enrichment: {len(enrichment)}")


def audit_ai_generated(entries: list[dict]) -> None:
    """Audit ai_generated entries and produce downgrade recommendations."""
    ai_gen = [e for e in entries if e.get("data_confidence") == "ai_generated"]

    print(f"=== ai_generated Audit ({len(ai_gen)} entries) ===\n")

    downgrade_list = []
    keep_list = []

    for e in ai_gen:
        name = e["name_ja"]
        grade = e.get("grade", "?")
        tabelog = e.get("tabelog_score")
        source = e.get("source", "")

        if grade in ("A", "S") and not tabelog:
            # A-grade with no tabelog score AND ai_generated = must downgrade
            downgrade_list.append({
                "name_ja": name,
                "city_code": e["city_code"],
                "current_grade": grade,
                "recommended_grade": "C",
                "reason": f"A-grade ai_generated with no tabelog_score. Source: {source}",
            })
        elif tabelog:
            keep_list.append({
                "name_ja": name,
                "city_code": e["city_code"],
                "grade": grade,
                "tabelog_score": tabelog,
                "note": "Has tabelog_score, keep as single_source",
            })
        else:
            # B/C grade with no tabelog
            if source and ("tabelog.com" in source or "michelin" in source.lower()):
                keep_list.append({
                    "name_ja": name,
                    "city_code": e["city_code"],
                    "grade": grade,
                    "note": f"Source references authoritative site: {source}",
                })
            else:
                keep_list.append({
                    "name_ja": name,
                    "city_code": e["city_code"],
                    "grade": grade,
                    "note": f"B/C grade, acceptable as ai_generated. Source: {source}",
                })

    print("--- DOWNGRADE RECOMMENDATIONS (A-grade ai_generated, no tabelog) ---")
    for d in downgrade_list:
        print(f"  {d['name_ja']} ({d['city_code']}) : {d['current_grade']} -> {d['recommended_grade']}")
        print(f"    Reason: {d['reason']}")

    print(f"\n--- KEEP AS-IS ({len(keep_list)} entries) ---")
    for k in keep_list:
        print(f"  {k['name_ja']} ({k['city_code']}) grade={k['grade']} : {k.get('note', '')}")

    print(f"\nSummary: {len(downgrade_list)} to downgrade, {len(keep_list)} to keep")

    # Save downgrade list
    downgrade_path = BASE_DIR / "data" / "kansai_spots" / "discovery_pool" / "ai_generated_downgrade_list.json"
    with open(downgrade_path, "w", encoding="utf-8") as f:
        json.dump({"downgrades": downgrade_list, "keep": keep_list}, f, ensure_ascii=False, indent=2)
    print(f"Saved to: {downgrade_path}")


def merge_and_output(entries: list[dict], enrichment: dict) -> None:
    """Merge enrichment data into entries and output CSV."""
    output_fields = [
        "name_ja", "name_zh", "city_code", "area", "corridor",
        "cuisine_type", "cuisine_normalized", "budget_tier",
        "grade", "tabelog_score", "michelin", "data_confidence",
        "lat", "lng", "budget_lunch_jpy", "budget_dinner_jpy",
        "address", "tabelog_url",
        "house_score", "selection_status", "source",
    ]

    rows = []
    stats = {"total": 0, "has_coords": 0, "has_lunch_price": 0, "has_dinner_price": 0, "has_name_zh": 0}

    for entry in entries:
        name = entry["name_ja"]
        enrich = enrichment.get(name, {})

        row = {}
        for field in output_fields:
            if field in enrich and enrich[field] is not None:
                row[field] = enrich[field]
            elif field in entry and entry[field] is not None:
                row[field] = entry[field]
            else:
                row[field] = ""

        rows.append(row)
        stats["total"] += 1
        if row.get("lat"):
            stats["has_coords"] += 1
        if row.get("budget_lunch_jpy"):
            stats["has_lunch_price"] += 1
        if row.get("budget_dinner_jpy"):
            stats["has_dinner_price"] += 1
        if row.get("name_zh"):
            stats["has_name_zh"] += 1

    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=output_fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f"=== Enrichment Statistics ===")
    print(f"Total restaurants: {stats['total']}")
    print(f"With coordinates:  {stats['has_coords']} ({stats['has_coords']*100//stats['total']}%)")
    print(f"With lunch price:  {stats['has_lunch_price']} ({stats['has_lunch_price']*100//stats['total']}%)")
    print(f"With dinner price: {stats['has_dinner_price']} ({stats['has_dinner_price']*100//stats['total']}%)")
    print(f"With Chinese name: {stats['has_name_zh']} ({stats['has_name_zh']*100//stats['total']}%)")
    print(f"\nOutput: {OUTPUT_CSV}")


def main():
    parser = argparse.ArgumentParser(description="Enrich restaurant data")
    parser.add_argument("--search-urls", action="store_true", help="Search Tabelog URLs via OpenCLI")
    parser.add_argument("--grades", default="S,A", help="Comma-separated grades to search (default: S,A)")
    parser.add_argument("--audit-ai", action="store_true", help="Audit ai_generated entries")
    args = parser.parse_args()

    entries = load_ledger()
    enrichment = load_enrichment()

    if args.search_urls:
        grades = [g.strip() for g in args.grades.split(",")]
        search_urls_mode(entries, enrichment, grades)
    elif args.audit_ai:
        audit_ai_generated(entries)
    else:
        merge_and_output(entries, enrichment)


if __name__ == "__main__":
    main()
