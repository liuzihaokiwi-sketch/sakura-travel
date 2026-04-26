"""D49 Agent C — restaurants/stops/entities 的 area/city 中文 → 英文 slug.

读 area_city_mapping.json·扫 3 类数据池·按 area_mapping/city_mapping 替换。
未覆盖的 area 不自创·留待汇报。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAPPING_PATH = ROOT / "_archive/d49_naming_unification/area_city_mapping.json"

RESTAURANT_GLOB = "japan/kansai/restaurants/**/*.json"
STOPS_GLOB = "japan/kansai/stops/*.json"
ENTITIES_GLOB = "japan/kansai/entities/*.json"


def is_ascii(s: str) -> bool:
    try:
        s.encode("ascii")
        return True
    except UnicodeEncodeError:
        return False


def load_mapping():
    m = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))
    return m["city_mapping"], {
        k: v for k, v in m["area_mapping"].items() if not k.startswith("_")
    }


def rewrite_record(rec: dict, area_map, city_map, uncovered: set, *, has_city: bool):
    """Mutates record in place. Returns True if changed."""
    changed = False
    if "area" in rec and isinstance(rec["area"], str):
        old_area = rec["area"]
        # 中文 area 必须映射；ASCII 的 key（如 "USJ"）若在 mapping 中也走映射
        if old_area in area_map:
            new = area_map[old_area]
            if rec["area"] != new["area"]:
                rec["area"] = new["area"]
                changed = True
            if has_city and rec.get("city") != new["city"]:
                rec["city"] = new["city"]
                changed = True
        elif not is_ascii(old_area):
            uncovered.add(old_area)
    if has_city and "city" in rec and isinstance(rec["city"], str):
        old_city = rec["city"]
        if not is_ascii(old_city):
            if old_city in city_map:
                rec["city"] = city_map[old_city]
                changed = True
            else:
                uncovered.add(f"city:{old_city}")
    return changed


def process_list_file(path: Path, area_map, city_map, uncovered, has_city: bool):
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return 0
    n_changed = 0
    for rec in data:
        if isinstance(rec, dict):
            if rewrite_record(rec, area_map, city_map, uncovered, has_city=has_city):
                n_changed += 1
    if n_changed:
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return n_changed


def process_entity_file(path: Path, area_map, city_map, uncovered):
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return 0
    n_changed = 0
    for k, v in data.items():
        if k.startswith("_"):
            continue
        if isinstance(v, dict):
            if rewrite_record(v, area_map, city_map, uncovered, has_city=True):
                n_changed += 1
    if n_changed:
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return n_changed


def main():
    city_map, area_map = load_mapping()
    uncovered: set[str] = set()

    rest_total = 0
    rest_files = sorted(ROOT.glob(RESTAURANT_GLOB))
    for f in rest_files:
        rest_total += process_list_file(f, area_map, city_map, uncovered, has_city=False)

    stops_total = 0
    stops_files = sorted(ROOT.glob(STOPS_GLOB))
    for f in stops_files:
        stops_total += process_list_file(f, area_map, city_map, uncovered, has_city=False)

    ent_total = 0
    ent_files = sorted(ROOT.glob(ENTITIES_GLOB))
    for f in ent_files:
        ent_total += process_entity_file(f, area_map, city_map, uncovered)

    print(f"restaurants changed: {rest_total} records ({len(rest_files)} files)")
    print(f"stops       changed: {stops_total} records ({len(stops_files)} files)")
    print(f"entities    changed: {ent_total} records ({len(ent_files)} files)")
    if uncovered:
        print("\nUNCOVERED area/city (mapping has no entry):")
        for u in sorted(uncovered):
            print(f"  - {u}")
        sys.exit(2)
    print("\nAll Chinese area/city values mapped.")


if __name__ == "__main__":
    main()
