"""正餐池 + 停留池字段校验脚本（全量数据层）。

校验 restaurants/{city}/*.json + stops/{city}/*.json：
    python scripts/validate_restaurants.py japan/kansai/restaurants/
    python scripts/validate_restaurants.py japan/kansai/stops/
    python scripts/validate_restaurants.py japan/kansai/   # 同时校验两个目录

校验规则：japan/餐厅规范.md §三（字段定稿）。违规 exit code != 0。

设计原则：
- 字段白名单 + 必填 + 枚举三层校验
- AI 加新字段 = FAIL（防字段膨胀）
- area 必须在 area_registry.json 白名单内
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent

# ---------- area 白名单（从 area_registry.json 读） ----------

def load_area_registry() -> set[str]:
    reg_path = REPO_ROOT / "japan/kansai/area_registry.json"
    if not reg_path.exists():
        return set()
    data = json.loads(reg_path.read_text(encoding="utf-8"))
    return {entry["area"] for entry in data if isinstance(entry, dict) and "area" in entry}

AREA_REGISTRY: set[str] = load_area_registry()

# ---------- 正餐池字段（restaurants/）按 §3.1 ----------

REST_REQUIRED = {"id", "area", "near_attractions", "tier", "cuisine", "recommended_meals", "closed_days"}
REST_OPTIONAL = {
    "reservation_difficulty", "queue_level", "season_months", "depth", "note",
}
REST_ALLOWED = REST_REQUIRED | REST_OPTIONAL

TIER_ENUM = {"showcase", "high", "mid", "economy"}
RESERVATION_DIFFICULTY_ENUM = {"none", "recommended", "must"}
QUEUE_LEVEL_ENUM = {"none", "mild", "high"}
DEPTH_ENUM = {"skeleton", "verified", "full"}

REST_NOTE_REQUIRED_FULL = {"店名", "简介", "亮点", "招牌菜", "地址", "营业", "预约"}
REST_NOTE_OPTIONAL = {"到店提醒", "Tabelog 分数"}
REST_NOTE_ALLOWED = REST_NOTE_REQUIRED_FULL | REST_NOTE_OPTIONAL

# ---------- 停留池字段（stops/）按 §3.2 ----------

STOP_REQUIRED = {"id", "area", "near_attractions", "type"}
STOP_OPTIONAL = {"depth", "note", "season_months"}
STOP_ALLOWED = STOP_REQUIRED | STOP_OPTIONAL

STOP_NOTE_REQUIRED_FULL = {"店名", "简介", "亮点", "地址", "营业"}
STOP_NOTE_OPTIONAL: set[str] = set()
STOP_NOTE_ALLOWED = STOP_NOTE_REQUIRED_FULL | STOP_NOTE_OPTIONAL

# stops type 开放枚举（§二）
STOP_TYPE_ENUM = {
    "咖啡", "甜品", "抹茶", "和菓子", "茶寮", "喫茶店", "刨冰",
    "古着", "古书", "书店", "书店咖啡", "杂货", "设计杂货",
    "文具", "古道具", "工艺品", "手工艺", "唱片", "御宅店", "当地土特产",
    "日本酒", "道具屋",
}


def _is_restaurants_dir(file: Path) -> bool:
    """判断文件是否在 restaurants/ 目录下（而非 stops/）。"""
    return "restaurants" in file.parts


def validate_item(item: dict, idx: int, file: Path, is_restaurant: bool) -> list[str]:
    errors: list[str] = []

    if not isinstance(item, dict):
        errors.append(f"{file.name}#{idx} 不是 dict")
        return errors

    rid = item.get("id", f"<no-id#{idx}>")
    label = f"{file.name}::{rid}"

    if is_restaurant:
        allowed = REST_ALLOWED
        required = REST_REQUIRED
    else:
        allowed = STOP_ALLOWED
        required = STOP_REQUIRED

    # 1. 字段白名单
    unknown = set(item.keys()) - allowed
    if unknown:
        errors.append(f"{label} 含未知字段（防膨胀）: {sorted(unknown)}")

    # 2. 必填字段
    missing = required - set(item.keys())
    if missing:
        errors.append(f"{label} 缺必填字段: {sorted(missing)}")

    # 3. area 白名单
    if "area" in item and AREA_REGISTRY:
        if item["area"] not in AREA_REGISTRY:
            errors.append(f"{label} area='{item['area']}' 不在 area_registry.json 白名单")

    # 4. near_attractions 结构
    if "near_attractions" in item:
        na = item["near_attractions"]
        if not isinstance(na, list) or len(na) == 0:
            errors.append(f"{label} near_attractions 必须是非空 list")
        else:
            for i, entry in enumerate(na):
                if not isinstance(entry, dict):
                    errors.append(f"{label} near_attractions[{i}] 非 dict")
                else:
                    if "entity_id" not in entry:
                        errors.append(f"{label} near_attractions[{i}] 缺 entity_id")
                    if "walk_min" not in entry:
                        errors.append(f"{label} near_attractions[{i}] 缺 walk_min")
                    elif not isinstance(entry["walk_min"], (int, float)):
                        errors.append(f"{label} near_attractions[{i}].walk_min 非数字")

    if is_restaurant:
        # 5. tier 枚举
        if "tier" in item and item["tier"] not in TIER_ENUM:
            errors.append(f"{label} tier='{item['tier']}' 不在枚举 {sorted(TIER_ENUM)}")

        # 6. cuisine 结构
        if "cuisine" in item:
            if not isinstance(item["cuisine"], list) or len(item["cuisine"]) == 0:
                errors.append(f"{label} cuisine 必须是非空 list")

        # 7. recommended_meals 结构
        if "recommended_meals" in item:
            rm = item["recommended_meals"]
            if not isinstance(rm, list) or len(rm) == 0:
                errors.append(f"{label} recommended_meals 必须是非空 list")
            else:
                for i, m in enumerate(rm):
                    if not isinstance(m, dict):
                        errors.append(f"{label} recommended_meals[{i}] 非 dict")
                    else:
                        if "meal" not in m:
                            errors.append(f"{label} recommended_meals[{i}] 缺 meal")
                        if "price_cny" not in m:
                            errors.append(f"{label} recommended_meals[{i}] 缺 price_cny")

        # 8. closed_days：list | null
        if "closed_days" in item:
            cd = item["closed_days"]
            if cd is not None and not isinstance(cd, list):
                errors.append(f"{label} closed_days 必须是 list 或 null")

        # 9. reservation_difficulty 枚举
        if "reservation_difficulty" in item and item["reservation_difficulty"] not in RESERVATION_DIFFICULTY_ENUM:
            errors.append(f"{label} reservation_difficulty='{item['reservation_difficulty']}' 不在枚举")

        # 10. queue_level 枚举
        if "queue_level" in item and item["queue_level"] not in QUEUE_LEVEL_ENUM:
            errors.append(f"{label} queue_level='{item['queue_level']}' 不在枚举")

        # 11. note 块（full 级必须含 7 个 key）
        if "note" in item and item["note"] is not None:
            note = item["note"]
            if not isinstance(note, dict):
                errors.append(f"{label} note 非 dict")
            else:
                unknown_note = set(note.keys()) - REST_NOTE_ALLOWED
                if unknown_note:
                    errors.append(f"{label} note 含未知 key: {sorted(unknown_note)}")
                depth = item.get("depth", "skeleton")
                if depth == "full":
                    missing_note = REST_NOTE_REQUIRED_FULL - set(note.keys())
                    if missing_note:
                        errors.append(f"{label} full 级 note 缺必填 key: {sorted(missing_note)}")

    else:
        # stops
        # 12. type 枚举
        if "type" in item and item["type"] not in STOP_TYPE_ENUM:
            errors.append(f"{label} type='{item['type']}' 不在 stops type 开放枚举")

        # 13. note 块（full 级必须含 5 个 key）
        if "note" in item and item["note"] is not None:
            note = item["note"]
            if not isinstance(note, dict):
                errors.append(f"{label} note 非 dict")
            else:
                unknown_note = set(note.keys()) - STOP_NOTE_ALLOWED
                if unknown_note:
                    errors.append(f"{label} note 含未知 key: {sorted(unknown_note)}")
                depth = item.get("depth", "skeleton")
                if depth == "full":
                    missing_note = STOP_NOTE_REQUIRED_FULL - set(note.keys())
                    if missing_note:
                        errors.append(f"{label} full 级 note 缺必填 key: {sorted(missing_note)}")

    # 14. depth 枚举（两池通用）
    if "depth" in item and item["depth"] not in DEPTH_ENUM:
        errors.append(f"{label} depth='{item['depth']}' 不在枚举 {sorted(DEPTH_ENUM)}")

    return errors


def validate_file(file: Path) -> tuple[int, int, list[str]]:
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except Exception as e:
        return 0, 1, [f"{file.name} JSON 解析失败: {e}"]

    if not isinstance(data, list):
        return 0, 1, [f"{file.name} 顶层非 list"]

    is_restaurant = _is_restaurants_dir(file)
    errors: list[str] = []
    seen_ids: set[str] = set()

    for i, item in enumerate(data):
        errors.extend(validate_item(item, i, file, is_restaurant))
        if isinstance(item, dict) and "id" in item:
            if item["id"] in seen_ids:
                errors.append(f"{file.name}::{item['id']} 重复 ID")
            seen_ids.add(item["id"])

    return len(data), len(errors), errors


def collect_files(target: Path) -> list[Path]:
    """收集 restaurants/ 和 stops/ 下的所有 JSON 文件。"""
    if target.is_file():
        return [target] if target.suffix == ".json" else []
    if target.is_dir():
        result = []
        for subdir in ("restaurants", "stops"):
            subpath = target / subdir
            if subpath.exists():
                result.extend(sorted(subpath.rglob("*.json")))
        # 如果直接传入的是 restaurants/ 或 stops/ 本身
        if not result:
            result = sorted(target.rglob("*.json"))
        return result
    return []


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("用法: python scripts/validate_restaurants.py <restaurants_or_stops_dir_or_file>")
        print("  例: python scripts/validate_restaurants.py japan/kansai/")
        print("  例: python scripts/validate_restaurants.py japan/kansai/restaurants/")
        print("  例: python scripts/validate_restaurants.py japan/kansai/stops/")
        return 2

    target = Path(argv[1]).resolve()
    files = collect_files(target)
    if not files:
        print(f"未找到 JSON 文件: {target}")
        return 2

    total = 0
    total_errors = 0
    all_msgs: list[str] = []
    file_results: list[tuple[str, int, int, str]] = []

    for f in files:
        is_r = _is_restaurants_dir(f)
        pool_type = "restaurants" if is_r else "stops"
        cnt, errs, msgs = validate_file(f)
        total += cnt
        total_errors += errs
        all_msgs.extend(msgs)
        file_results.append((str(f.relative_to(REPO_ROOT)), cnt, errs, pool_type))

    rest_count = sum(cnt for _, cnt, _, t in file_results if t == "restaurants")
    stop_count = sum(cnt for _, cnt, _, t in file_results if t == "stops")

    print("=" * 65)
    print("餐厅 + 停留点全量校验结果")
    print("=" * 65)
    cur_type = ""
    for path, cnt, errs, pool_type in file_results:
        if pool_type != cur_type:
            print(f"\n  --- {pool_type} ---")
            cur_type = pool_type
        status = "PASS" if errs == 0 else "FAIL"
        print(f"  [{status}] {path}  ({cnt} items, {errs} errors)")
    print("-" * 65)
    print(f"合计: {rest_count} restaurants + {stop_count} stops = {total} items, {total_errors} errors")

    if all_msgs:
        print()
        print("详细错误（前 300 条）:")
        for m in all_msgs[:300]:
            print(f"  - {m}")
        if len(all_msgs) > 300:
            print(f"  ... 还有 {len(all_msgs) - 300} 条未显示")

    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
