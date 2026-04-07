"""
Compile final selection_ledger.json and GUIDE_*.md from phase2b ledger files.
Usage: python scripts/compile_selection_ledger.py
"""
import json
import re
from collections import Counter, defaultdict
from datetime import datetime

BASE = "data/kansai_spots"
PHASE2B = f"{BASE}/phase2_ledger"
GENERATED_AT = "2026-04-01T00:00:00+09:00"


def load_phase2b(name: str) -> list[dict]:
    path = f"{PHASE2B}/{name}_ledger_phase2b.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("entries", data) if isinstance(data, dict) else data


def effective_grade(entry: dict) -> str | None:
    g = entry.get("grade")
    if g:
        return g
    return entry.get("grade_suggestion")


def is_selected(entry: dict) -> bool:
    return (
        entry.get("selection_status") in ("selected", "borderline")
        and entry.get("editorial_exclusion") is not True
    )


def build_summary(all_entries: list[dict], selected: list[dict]) -> dict:
    by_grade: Counter = Counter()
    by_city: Counter = Counter()
    for e in selected:
        g = effective_grade(e) or "unknown"
        by_grade[g] += 1
        c = e.get("city_code") or "unknown"
        by_city[c] += 1

    return {
        "total_candidates": len(all_entries),
        "selected": len(selected),
        "excluded": len(all_entries) - len(selected),
        "by_grade": dict(sorted(by_grade.items())),
        "by_city": dict(sorted(by_city.items())),
    }


def write_selection_ledger(name: str) -> None:
    all_entries = load_phase2b(name)
    selected = [e for e in all_entries if is_selected(e)]

    # Inject effective_grade into each entry for convenience
    for e in selected:
        if not e.get("grade"):
            gs = e.get("grade_suggestion")
            if gs:
                e["grade"] = gs

    output = {
        "version": "2.0",
        "generated_at": GENERATED_AT,
        "city_circle": "kansai",
        "summary": build_summary(all_entries, selected),
        "entries": selected,
    }

    out_path = f"{BASE}/{name}_selection_ledger.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    s = output["summary"]
    print(
        f"[{name}] total={s['total_candidates']}  selected={s['selected']}  "
        f"excluded={s['excluded']}  by_grade={s['by_grade']}"
    )
    return selected


# ---------------------------------------------------------------------------
# GUIDE_RESTAURANTS.md
# ---------------------------------------------------------------------------

BUDGET_ORDER = ["luxury", "premium", "mid", "budget", "unknown"]
CITY_ORDER = ["kyoto", "osaka", "kobe", "nara", "hyogo", "akashi", "other"]


def _city_key(city: str) -> int:
    try:
        return CITY_ORDER.index(city)
    except ValueError:
        return len(CITY_ORDER)


def _budget_key(tier: str) -> int:
    t = (tier or "unknown").lower()
    try:
        return BUDGET_ORDER.index(t)
    except ValueError:
        return len(BUDGET_ORDER)


def write_guide_restaurants(selected: list[dict]) -> None:
    # Only S/A/B/C — all grades go into guide for restaurants (C included per spec)
    entries = [e for e in selected]

    # Group by city → corridor/area → budget_tier
    tree: dict = defaultdict(lambda: defaultdict(list))
    for e in entries:
        city = e.get("city_code") or "unknown"
        corridor = e.get("corridor") or e.get("area") or "その他"
        tree[city][corridor].append(e)

    lines = ["# GUIDE_RESTAURANTS — 関西レストラン編集ガイド", ""]
    lines.append(f"> 生成日: {GENERATED_AT}  |  入選数: {len(entries)}")
    lines.append("")

    for city in sorted(tree.keys(), key=_city_key):
        lines.append(f"## {city.upper()}")
        lines.append("")

        corridors = tree[city]
        for corridor in sorted(corridors.keys()):
            lines.append(f"### {corridor}")
            lines.append("")

            # Group by budget tier within corridor
            budget_map: dict[str, list] = defaultdict(list)
            for e in corridors[corridor]:
                tier = (e.get("budget_tier") or "unknown").lower()
                budget_map[tier].append(e)

            for tier in sorted(budget_map.keys(), key=_budget_key):
                lines.append(f"#### {tier}")
                lines.append("")
                for e in sorted(
                    budget_map[tier],
                    key=lambda x: (-({"S": 4, "A": 3, "B": 2, "C": 1}.get(effective_grade(x) or "C", 1))),
                ):
                    grade = effective_grade(e) or "?"
                    name_ja = e.get("name_ja") or ""
                    tags = " ".join(e.get("selection_tags") or [])
                    qe = e.get("quality_evidence") or ""
                    note = e.get("one_line_editorial_note") or ""
                    lines.append(f"**{name_ja}** `{grade}` {tags}")
                    if qe:
                        lines.append(f"> {qe}")
                    if note:
                        lines.append(f"> {note}")
                    lines.append("")

    out_path = f"{BASE}/GUIDE_RESTAURANTS.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    grade_dist = Counter(effective_grade(e) or "?" for e in entries)
    print(
        f"[GUIDE_RESTAURANTS] entries={len(entries)}  grades={dict(sorted(grade_dist.items()))}"
    )


# ---------------------------------------------------------------------------
# GUIDE_HOTELS.md
# ---------------------------------------------------------------------------

PRICE_ORDER = ["luxury", "premium", "upper_mid", "mid", "budget", "unknown"]


def _price_key(level: str) -> int:
    l = (level or "unknown").lower()
    try:
        return PRICE_ORDER.index(l)
    except ValueError:
        return len(PRICE_ORDER)


def write_guide_hotels(selected: list[dict]) -> None:
    # S/A/B/C all go into guide
    entries = [e for e in selected]

    tree: dict = defaultdict(list)
    for e in entries:
        city = e.get("city_code") or "unknown"
        tree[city].append(e)

    lines = ["# GUIDE_HOTELS — 関西ホテル編集ガイド", ""]
    lines.append(f"> 生成日: {GENERATED_AT}  |  入選数: {len(entries)}")
    lines.append("")

    for city in sorted(tree.keys(), key=_city_key):
        lines.append(f"## {city.upper()}")
        lines.append("")

        # Group by price_level
        price_map: dict[str, list] = defaultdict(list)
        for e in tree[city]:
            pl = (e.get("price_level") or "unknown").lower()
            price_map[pl].append(e)

        for pl in sorted(price_map.keys(), key=_price_key):
            lines.append(f"### {pl}")
            lines.append("")
            for e in sorted(
                price_map[pl],
                key=lambda x: (-({"S": 4, "A": 3, "B": 2, "C": 1}.get(effective_grade(x) or "C", 1))),
            ):
                grade = effective_grade(e) or "?"
                name_ja = e.get("name_ja") or ""
                hotel_type = e.get("hotel_type") or ""
                price_level = e.get("price_level") or ""
                tags = " ".join(e.get("selection_tags") or [])
                qe = e.get("quality_evidence") or ""
                note = e.get("one_line_editorial_note") or ""
                lines.append(f"**{name_ja}** `{grade}` {hotel_type} {price_level} {tags}".rstrip())
                if qe:
                    lines.append(f"> {qe}")
                if note:
                    lines.append(f"> {note}")
                lines.append("")

    out_path = f"{BASE}/GUIDE_HOTELS.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    grade_dist = Counter(effective_grade(e) or "?" for e in entries)
    print(
        f"[GUIDE_HOTELS] entries={len(entries)}  grades={dict(sorted(grade_dist.items()))}"
    )


# ---------------------------------------------------------------------------
# GUIDE_SPOTS.md
# ---------------------------------------------------------------------------

MAIN_TYPE_ORDER = [
    "temple", "shrine", "castle", "garden", "museum", "nature",
    "onsen", "cultural_experience", "shopping", "entertainment", "other",
]


def _type_key(t: str) -> int:
    try:
        return MAIN_TYPE_ORDER.index(t)
    except ValueError:
        return len(MAIN_TYPE_ORDER)


def write_guide_spots(selected: list[dict]) -> None:
    # Only S/A/B (no C)
    entries = [e for e in selected if effective_grade(e) in ("S", "A", "B")]

    tree: dict = defaultdict(lambda: defaultdict(list))
    for e in entries:
        city = e.get("city_code") or "unknown"
        main_type = (e.get("main_type") or "other").lower()
        tree[city][main_type].append(e)

    lines = ["# GUIDE_SPOTS — 関西観光スポット編集ガイド", ""]
    lines.append(f"> 生成日: {GENERATED_AT}  |  入選数(S/A/B): {len(entries)}")
    lines.append("")

    for city in sorted(tree.keys(), key=_city_key):
        lines.append(f"## {city.upper()}")
        lines.append("")

        for main_type in sorted(tree[city].keys(), key=_type_key):
            lines.append(f"### {main_type}")
            lines.append("")
            for e in sorted(
                tree[city][main_type],
                key=lambda x: (-({"S": 4, "A": 3, "B": 2, "C": 1}.get(effective_grade(x) or "C", 1))),
            ):
                grade = effective_grade(e) or "?"
                name_ja = e.get("name_ja") or ""
                name_en = e.get("name_en") or ""
                display_name = f"{name_ja}/{name_en}" if name_en and name_ja else (name_ja or name_en)
                sub_type = e.get("sub_type") or ""
                tags = " ".join(e.get("selection_tags") or [])
                qe = e.get("quality_evidence") or ""
                note = e.get("one_line_editorial_note") or ""
                lines.append(f"**{display_name}** `{grade}` {sub_type} {tags}".rstrip())
                if qe:
                    lines.append(f"> {qe}")
                if note:
                    lines.append(f"> {note}")
                lines.append("")

    out_path = f"{BASE}/GUIDE_SPOTS.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    grade_dist = Counter(effective_grade(e) or "?" for e in entries)
    print(
        f"[GUIDE_SPOTS] entries={len(entries)}  grades={dict(sorted(grade_dist.items()))}"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Compiling selection ledgers ===")
    sel_restaurants = write_selection_ledger("restaurants")
    sel_hotels = write_selection_ledger("hotels")
    sel_spots = write_selection_ledger("spots")

    print()
    print("=== Generating GUIDE files ===")

    # Re-load from written files to use effective grade already injected
    def load_sel(name: str) -> list[dict]:
        with open(f"{BASE}/{name}_selection_ledger.json", encoding="utf-8") as f:
            return json.load(f)["entries"]

    write_guide_restaurants(load_sel("restaurants"))
    write_guide_hotels(load_sel("hotels"))
    write_guide_spots(load_sel("spots"))

    print()
    print("Done.")
