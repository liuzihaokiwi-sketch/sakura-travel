"""D44 category 迁移：33 英文 → 12 中文。dry-run 已确认全 113 条可映射。"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
MAP = {
    "temple": "寺社", "shrine": "寺社",
    "castle": "城",
    "garden": "庭园",
    "park": "自然", "natural_path": "自然", "riverside": "自然",
    "mountain": "自然", "lake": "自然", "natural_landmark": "自然",
    "view_spot": "展望", "observation_deck": "展望", "viewpoint": "展望",
    "museum": "博物馆",
    "aquarium": "水族动物",
    "theme_park": "主题乐园", "amusement_park": "主题乐园", "ferris_wheel": "主题乐园",
    "experience": "体验",
    "district": "街区", "neighborhood": "街区", "historic_area": "街区",
    "cultural_district": "街区", "area": "街区", "commercial_street": "街区",
    "shopping_street": "街区", "boulevard": "街区", "market": "街区",
    "department_store": "街区",
    "onsen": "温泉",
    "transport": "交通", "bridge": "交通",
}

VALID_NEW = set(MAP.values())

for city in ["kyoto", "osaka", "other"]:
    path = ROOT / f"japan/kansai/entities/{city}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    changed = 0
    for key, e in (data.items() if isinstance(data, dict) else enumerate(data)):
        if not isinstance(e, dict):
            continue
        old = e.get("category")
        if old in VALID_NEW:
            continue
        if old in MAP:
            e["category"] = MAP[old]
            changed += 1
        elif old:
            print(f"  [WARN] {city}/{key}: 未知 category={old}")
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"{city}.json: 迁移 {changed} 条")
