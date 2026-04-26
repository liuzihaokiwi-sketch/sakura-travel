"""D49 Agent B: hotels city 中文 → 英文 slug 替换。

按 area_city_mapping.json 的 city_mapping 替换 3 个 hotels json 的 city 字段。
顺便统计每条 hotel 的 area·校验是否在 area_registry.json 白名单内·不在的报告出来不修。
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAPPING_PATH = ROOT / "_archive" / "d49_naming_unification" / "area_city_mapping.json"
REGISTRY_PATH = ROOT / "japan" / "kansai" / "area_registry.json"
HOTEL_FILES = [
    ROOT / "japan" / "kansai" / "hotels" / "kyoto.json",
    ROOT / "japan" / "kansai" / "hotels" / "osaka.json",
    ROOT / "japan" / "kansai" / "hotels" / "other.json",
]


def main():
    mapping = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))
    city_mapping = mapping["city_mapping"]

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    valid_areas = {entry["area"] for entry in registry}
    # (city, area) tuple set for stricter check
    valid_tuples = {(entry["city"], entry["area"]) for entry in registry}

    total_changed = 0
    total_hotels = 0
    unchanged_city_values = {}  # already english or unmapped
    area_issues = []  # area not in registry

    for hotel_path in HOTEL_FILES:
        data = json.loads(hotel_path.read_text(encoding="utf-8"))
        file_changed = 0
        for hotel in data:
            total_hotels += 1
            old_city = hotel.get("city")
            if old_city in city_mapping:
                hotel["city"] = city_mapping[old_city]
                file_changed += 1
            else:
                unchanged_city_values[old_city] = unchanged_city_values.get(old_city, 0) + 1

            area = hotel.get("area")
            new_city = hotel["city"]
            if area not in valid_areas:
                area_issues.append({
                    "file": hotel_path.name,
                    "hotel_id": hotel.get("id") or hotel.get("name"),
                    "city": new_city,
                    "area": area,
                    "issue": "area not in registry",
                })
            elif (new_city, area) not in valid_tuples:
                area_issues.append({
                    "file": hotel_path.name,
                    "hotel_id": hotel.get("id") or hotel.get("name"),
                    "city": new_city,
                    "area": area,
                    "issue": "(city,area) tuple not in registry",
                })

        hotel_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        total_changed += file_changed
        print(f"[{hotel_path.name}] hotels={len(data)} city_changed={file_changed}")

    print(f"\nTOTAL hotels={total_hotels} city_changed={total_changed}")
    print(f"Unchanged city values (already english or unmapped): {unchanged_city_values}")
    print(f"\nArea issues count: {len(area_issues)}")
    for issue in area_issues:
        print(f"  - {issue}")


if __name__ == "__main__":
    main()
