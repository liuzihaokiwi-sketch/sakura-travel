"""
模板质量校验脚本。

读取城市模板目录下的 JSON 文件 + rules.json，逐条检查规则。
输出: PASS / WARNING / ERROR

用法:
    python scripts/validate_template.py --city osaka --circle kansai
    python scripts/validate_template.py --all
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ──────────────────────────────────────────────
# Data classes
# ──────────────────────────────────────────────

@dataclass
class Issue:
    level: str          # ERROR / WARNING
    file: str
    location: str       # e.g. "day1_dinner.mid.A"
    rule: str           # which rule violated
    detail: str

@dataclass
class Report:
    city: str
    circle: str
    issues: list[Issue] = field(default_factory=list)
    checks_run: int = 0

    def add(self, level: str, file: str, location: str, rule: str, detail: str):
        self.issues.append(Issue(level, file, location, rule, detail))

    def print_report(self):
        errors = [i for i in self.issues if i.level == "ERROR"]
        warnings = [i for i in self.issues if i.level == "WARNING"]
        print(f"\n{'='*60}")
        print(f"  Template validation: {self.circle}/{self.city}")
        print(f"  Checks run: {self.checks_run}")
        print(f"  Errors: {len(errors)}  Warnings: {len(warnings)}")
        print(f"{'='*60}")
        for i in sorted(self.issues, key=lambda x: (x.level != "ERROR", x.file)):
            tag = "[X]" if i.level == "ERROR" else "[!]"
            print(f"  {tag} [{i.level}] {i.file} > {i.location}")
            print(f"     Rule: {i.rule}")
            print(f"     Detail: {i.detail}")
            print()
        if not self.issues:
            print("  [OK] All checks passed.")
        return len(errors)


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def extract_meals(meals_data: dict) -> list[dict]:
    """Flatten all meal options (A/B/fallback) from meals.json."""
    results = []
    for meal_key, meal_val in meals_data.items():
        if not isinstance(meal_val, dict):
            continue
        # options_by_budget structure
        budgets = meal_val.get("options_by_budget", {})
        for tier, options in budgets.items():
            if tier.startswith("_"):
                continue
            if not isinstance(options, dict):
                continue
            for slot_label, slot_data in options.items():
                if not isinstance(slot_data, dict):
                    continue
                slot_data["_meal_key"] = meal_key
                slot_data["_tier"] = tier
                slot_data["_slot"] = slot_label
                results.append(slot_data)
        # audience_overrides
        overrides = meal_val.get("audience_overrides", {})
        for tier, audiences in overrides.items():
            if not isinstance(audiences, dict):
                continue
            for aud, aud_options in audiences.items():
                if not isinstance(aud_options, dict):
                    continue
                for slot_label, slot_data in aud_options.items():
                    if not isinstance(slot_data, dict):
                        continue
                    slot_data["_meal_key"] = meal_key
                    slot_data["_tier"] = tier
                    slot_data["_slot"] = f"{slot_label}(override:{aud})"
                    results.append(slot_data)
        # snacks items
        items = meal_val.get("items", [])
        for item in items:
            if isinstance(item, dict):
                item["_meal_key"] = meal_key
                item["_tier"] = "snack"
                item["_slot"] = "snack"
                results.append(item)
    return results


# ──────────────────────────────────────────────
# Checks
# ──────────────────────────────────────────────

def check_no_chinese(meals: list[dict], report: Report):
    """No Chinese cuisine recommended (except 551蓬莱)."""
    report.checks_run += 1
    for m in meals:
        cuisine = (m.get("cuisine") or "").lower()
        entity = m.get("entity_hint") or ""
        if any(k in cuisine for k in ["中华", "中国", "chinese"]):
            if "551" in entity or "蓬莱" in entity:
                continue
            loc = f"{m.get('_meal_key','?')}.{m.get('_tier','?')}.{m.get('_slot','?')}"
            report.add("ERROR", "meals.json", loc, "no_chinese",
                        f"中华料理不推荐: {entity} ({cuisine})")


def check_same_day_cuisine_dup(meals_data: dict, report: Report):
    """Lunch and dinner on same day shouldn't share cuisine."""
    report.checks_run += 1
    # Group by day (day1, day2, etc.)
    day_meals: dict[str, list] = {}
    for key, val in meals_data.items():
        if not isinstance(val, dict) or "options_by_budget" not in val:
            continue
        # Extract day number from key like "day1_lunch", "day2_dinner"
        m = re.match(r"(day\d+|umeda_day\d+)", key)
        if not m:
            continue
        day = m.group(1)
        if day not in day_meals:
            day_meals[day] = []
        budgets = val.get("options_by_budget", {})
        for tier, options in budgets.items():
            if tier.startswith("_") or not isinstance(options, dict):
                continue
            for slot, data in options.items():
                if isinstance(data, dict) and data.get("cuisine"):
                    day_meals[day].append({
                        "key": key, "tier": tier, "slot": slot,
                        "cuisine": data["cuisine"]
                    })

    for day, entries in day_meals.items():
        by_tier: dict[str, list] = {}
        for e in entries:
            by_tier.setdefault(e["tier"], []).append(e)
        for tier, tier_entries in by_tier.items():
            cuisines = [e["cuisine"] for e in tier_entries]
            seen = set()
            for i, c in enumerate(cuisines):
                if c in seen:
                    report.add("WARNING", "meals.json",
                               f"{day}.{tier}",
                               "same_day_cuisine_dup",
                               f"同天同档位出现重复菜系: {c}")
                seen.add(c)


def check_booking_blacklist(meals: list[dict], rules: dict, report: Report):
    """Restaurants in booking difficulty blacklist shouldn't appear."""
    report.checks_run += 1
    blacklist = rules.get("booking_difficulty_filter", {}).get("exclude", [])
    if not blacklist:
        return
    for m in meals:
        entity = m.get("entity_hint") or ""
        for banned in blacklist:
            # Extract shop name from blacklist entry like "尽誠（一见谢绝）"
            banned_name = banned.split("（")[0].split("(")[0].strip()
            if banned_name and banned_name in entity:
                loc = f"{m.get('_meal_key','?')}.{m.get('_tier','?')}.{m.get('_slot','?')}"
                report.add("ERROR", "meals.json", loc, "booking_blacklist",
                            f"预约极难店不应推荐: {entity} (黑名单: {banned})")


def check_entity_hint_present(meals: list[dict], report: Report):
    """All meal slots should have entity_hint."""
    report.checks_run += 1
    for m in meals:
        if m.get("_tier") == "snack":
            continue
        entity = m.get("entity_hint") or ""
        if not entity or entity == "_todo":
            loc = f"{m.get('_meal_key','?')}.{m.get('_tier','?')}.{m.get('_slot','?')}"
            report.add("WARNING", "meals.json", loc, "missing_entity_hint",
                        "缺少 entity_hint")


def check_cuisine_present(meals: list[dict], report: Report):
    """All non-snack meal slots should have cuisine field."""
    report.checks_run += 1
    for m in meals:
        if m.get("_tier") == "snack":
            continue
        cuisine = m.get("cuisine") or ""
        if not cuisine:
            entity = m.get("entity_hint") or "?"
            loc = f"{m.get('_meal_key','?')}.{m.get('_tier','?')}.{m.get('_slot','?')}"
            report.add("WARNING", "meals.json", loc, "missing_cuisine",
                        f"缺少 cuisine 字段: {entity}")


def check_ab_cuisine_diff(meals_data: dict, report: Report):
    """A and B in same budget tier should have different cuisine (preferably)."""
    report.checks_run += 1
    for key, val in meals_data.items():
        if not isinstance(val, dict):
            continue
        budgets = val.get("options_by_budget", {})
        for tier, options in budgets.items():
            if tier.startswith("_") or not isinstance(options, dict):
                continue
            a_cuisine = ""
            b_cuisine = ""
            if isinstance(options.get("A"), dict):
                a_cuisine = options["A"].get("cuisine", "")
            if isinstance(options.get("B"), dict):
                b_cuisine = options["B"].get("cuisine", "")
            if a_cuisine and b_cuisine and a_cuisine == b_cuisine:
                report.add("WARNING", "meals.json",
                           f"{key}.{tier}",
                           "ab_same_cuisine",
                           f"A和B菜系相同: A={a_cuisine}, B={b_cuisine}（应有体验差异）")


def check_cross_day_cuisine_dup(meals_data: dict, report: Report):
    """Track A-slot cuisines across days, warn on repeated cuisine."""
    report.checks_run += 1
    day_a_cuisines: dict[str, dict[str, str]] = {}  # {day: {tier: cuisine}}
    for key, val in meals_data.items():
        if not isinstance(val, dict) or "options_by_budget" not in val:
            continue
        m = re.match(r"(day\d+|umeda_day\d+)", key)
        if not m:
            continue
        day = m.group(1)
        budgets = val.get("options_by_budget", {})
        for tier, options in budgets.items():
            if tier.startswith("_") or not isinstance(options, dict):
                continue
            a_data = options.get("A")
            if isinstance(a_data, dict) and a_data.get("cuisine"):
                day_a_cuisines.setdefault(day, {})[f"{key}.{tier}"] = a_data["cuisine"]

    # Check across days
    all_cuisines: list[tuple[str, str, str]] = []  # (day, location, cuisine)
    for day in sorted(day_a_cuisines.keys()):
        for loc, cuisine in day_a_cuisines[day].items():
            all_cuisines.append((day, loc, cuisine))

    seen_cuisines: dict[str, list[str]] = {}  # cuisine -> [locations]
    for day, loc, cuisine in all_cuisines:
        if cuisine in seen_cuisines:
            prev = seen_cuisines[cuisine]
            if len(prev) >= 2:
                report.add("WARNING", "meals.json", loc,
                           "cross_day_cuisine_repeat",
                           f"A轨道菜系'{cuisine}'出现3次+: {prev + [loc]}")
            seen_cuisines[cuisine].append(loc)
        else:
            seen_cuisines[cuisine] = [loc]


def check_flour_consecutive(meals_data: dict, report: Report):
    """No two consecutive flour foods (ramen/udon/okonomiyaki/soba)."""
    report.checks_run += 1
    flour_types = {"拉面", "乌冬", "大阪烧", "荞麦", "うどん", "ラーメン", "お好み焼"}

    # Collect only A cuisines per meal (not per tier), in day order
    day_cuisines = []
    seen_keys = set()
    for key, val in sorted(meals_data.items()):
        if not isinstance(val, dict) or "options_by_budget" not in val:
            continue
        if key in seen_keys:
            continue
        seen_keys.add(key)
        budgets = val.get("options_by_budget", {})
        # Just check mid tier A as representative (most common)
        for tier in ["mid", "budget", "premium"]:
            options = budgets.get(tier)
            if isinstance(options, dict) and isinstance(options.get("A"), dict):
                c = options["A"].get("cuisine", "")
                if c:
                    day_cuisines.append((key, tier, c))
                    break

    for i in range(1, len(day_cuisines)):
        prev_key, prev_tier, prev_c = day_cuisines[i-1]
        cur_key, cur_tier, cur_c = day_cuisines[i]
        if any(f in prev_c for f in flour_types) and any(f in cur_c for f in flour_types):
            report.add("WARNING", "meals.json",
                       f"{cur_key}.{cur_tier}",
                       "consecutive_flour",
                       f"连续粉物: {prev_key}={prev_c} → {cur_key}={cur_c}")


def check_showcase_cap(meals_data: dict, rules: dict, report: Report):
    """Showcase meals per city should not exceed cap."""
    report.checks_run += 1
    caps = rules.get("dining_policy", {}).get("trip_caps", {}).get("showcase_caps", {})
    per_city = caps.get("per_city", 1)
    # Count premium+ audience_day meals (these are likely showcase)
    showcase_count = 0
    for key, val in meals_data.items():
        if "day5" in key or "audience" in key:
            budgets = val.get("options_by_budget", {}) if isinstance(val, dict) else {}
            if "premium" in budgets or "luxury" in budgets:
                showcase_count += 1
    if showcase_count > per_city:
        report.add("WARNING", "meals.json", "showcase_count",
                   "showcase_cap",
                   f"Showcase meals={showcase_count}, cap per city={per_city}")


def check_hotels_complete(hotels_data: dict, report: Report):
    """Check hotel data completeness."""
    report.checks_run += 1
    for area, area_data in hotels_data.items():
        if area.startswith("_"):
            continue
        if isinstance(area_data, dict) and "_todo" in str(area_data):
            report.add("WARNING", "hotels.json", area, "incomplete_data",
                       "酒店数据待补全")
            continue
        if not isinstance(area_data, dict):
            continue
        for tier, hotels in area_data.items():
            if not isinstance(hotels, list):
                continue
            for h in hotels:
                if not isinstance(h, dict):
                    continue
                if not h.get("name_zh"):
                    report.add("WARNING", "hotels.json",
                               f"{area}.{tier}",
                               "missing_name_zh",
                               f"酒店缺少中文名: {h.get('name_ja', '?')}")
                if not h.get("price_low"):
                    report.add("WARNING", "hotels.json",
                               f"{area}.{tier}",
                               "missing_price",
                               f"酒店缺少价格: {h.get('name_zh', '?')}")


def check_shops_todo(shops_data: dict, report: Report):
    """Check for _todo in shops."""
    report.checks_run += 1
    for key, val in shops_data.items():
        if isinstance(val, dict):
            defaults = val.get("defaults", [])
            if isinstance(defaults, str) and "待" in defaults:
                report.add("WARNING", "shops.json", key, "incomplete_data",
                           f"店铺数据待补全: {defaults}")
            elif isinstance(defaults, list):
                for d in defaults:
                    if isinstance(d, dict) and "_todo" in str(d):
                        report.add("WARNING", "shops.json", key, "incomplete_data",
                                   "店铺数据待补全")
                        break


def check_schedule_day_mood(schedule_data: dict, report: Report):
    """Each day should have day_mood."""
    report.checks_run += 1
    for variant in ["namba", "umeda"]:
        variant_data = schedule_data.get(variant, {})
        days = variant_data.get("days", [])
        for day in days:
            if not isinstance(day, dict):
                continue
            day_id = day.get("day_id", "?")
            if day_id in ("seasonal",):
                continue  # conditional day, ok to skip
            if not day.get("day_mood") and not day.get("day_mood_by_audience"):
                report.add("WARNING", "base_schedule.json",
                           f"{variant}.{day_id}",
                           "missing_day_mood",
                           "缺少 day_mood")


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def validate_city(circle: str, city: str, base_dir: Path) -> Report:
    template_dir = base_dir / "data" / f"{circle}_spots" / "templates" / city
    report = Report(city=city, circle=circle)

    if not template_dir.exists():
        report.add("ERROR", "", "", "directory_missing",
                   f"模板目录不存在: {template_dir}")
        return report

    rules = load_json(template_dir / "rules.json") or {}
    meals_data = load_json(template_dir / "meals.json") or {}
    hotels_data = load_json(template_dir / "hotels.json") or {}
    shops_data = load_json(template_dir / "shops.json") or {}
    schedule_data = load_json(template_dir / "base_schedule.json") or {}

    meals = extract_meals(meals_data)

    # Run checks
    check_no_chinese(meals, report)
    check_same_day_cuisine_dup(meals_data, report)
    check_booking_blacklist(meals, rules, report)
    check_entity_hint_present(meals, report)
    check_cuisine_present(meals, report)
    check_ab_cuisine_diff(meals_data, report)
    check_cross_day_cuisine_dup(meals_data, report)
    check_flour_consecutive(meals_data, report)
    check_showcase_cap(meals_data, rules, report)
    check_hotels_complete(hotels_data, report)
    check_shops_todo(shops_data, report)
    check_schedule_day_mood(schedule_data, report)

    return report


def main():
    parser = argparse.ArgumentParser(description="Validate template quality")
    parser.add_argument("--city", help="City name (e.g. osaka)")
    parser.add_argument("--circle", help="Circle name (e.g. kansai)")
    parser.add_argument("--all", action="store_true", help="Validate all cities")
    parser.add_argument("--base-dir", default=".", help="Project root directory")
    args = parser.parse_args()

    base_dir = Path(args.base_dir)

    if args.all:
        # Find all template directories
        templates_root = base_dir / "data"
        total_errors = 0
        for circle_dir in templates_root.glob("*_spots/templates"):
            for city_dir in circle_dir.iterdir():
                if city_dir.is_dir() and (city_dir / "manifest.json").exists():
                    circle = circle_dir.parent.name.replace("_spots", "")
                    report = validate_city(circle, city_dir.name, base_dir)
                    total_errors += report.print_report()
        sys.exit(1 if total_errors else 0)
    elif args.city and args.circle:
        report = validate_city(args.circle, args.city, base_dir)
        errors = report.print_report()
        sys.exit(1 if errors else 0)
    else:
        parser.error("Specify --city and --circle, or --all")


if __name__ == "__main__":
    main()
