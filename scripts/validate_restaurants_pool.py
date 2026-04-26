"""餐厅池字段校验脚本。

每次改造餐厅数据后跑一次：
    python scripts/validate_restaurants.py japan/kansai/assembly/restaurants/data/restaurants__kyoto.json

校验整个目录：
    python scripts/validate_restaurants.py japan/kansai/assembly/restaurants/data/

校验规则参考 docs/03_数据契约/字段权威.md §2.2 + japan/餐厅规范.md。违规 exit code != 0。

设计原则（_沉淀盘点.md 决策）：
- 字段白名单 + 必填 + 枚举三层校验
- AI 加新字段 = FAIL（防字段膨胀，铁律 1）
- 字段以现实数据为准（D36 后字段名实际是 cuisine_tag/budget_tier/ab_role/meal_role）
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent

# 必填（按现实数据 + japan/餐厅规范.md §三）
REQUIRED = {
    "id", "name_ja", "name_zh", "area",
    "cuisine_tag", "budget_tier", "ab_role",
}
OPTIONAL = {
    "vibe_tags", "price_lunch_jpy", "price_dinner_jpy",
    "score", "meal_role", "editor_note", "reservation_required",
    "notes",
    "facility_tags", "risk_flags", "last_verified",
    "opening_hours", "near_attractions", "queue_level",
    "closed_days", "season_months", "depth",
    "meal_type_fit", "reservation_difficulty",
}
ALLOWED = REQUIRED | OPTIONAL

BUDGET_TIER_ENUM = {"economy", "mid", "high", "showcase"}
AB_ROLE_ENUM = {"A_safe", "B_surprise"}
MEAL_ROLE_ENUM = {
    "affordable_local", "audience_day_showcase",
    "core_local_experience", "everyday_good",
    "light", "showcase",
}
RESERVATION_DIFFICULTY_ENUM = {"none", "recommended", "must"}
QUEUE_LEVEL_ENUM = {"none", "mild", "high"}
DEPTH_ENUM = {"skeleton", "verified", "full"}


def validate_item(it: dict, idx: int, file: Path) -> list[str]:
    errors: list[str] = []

    if not isinstance(it, dict):
        errors.append(f"{file.name}#{idx} 不是 dict")
        return errors

    rid = it.get("id", f"<no-id#{idx}>")

    unknown = set(it.keys()) - ALLOWED
    if unknown:
        errors.append(f"{file.name}::{rid} 含未知字段（防膨胀）: {sorted(unknown)}")

    missing = REQUIRED - set(it.keys())
    if missing:
        errors.append(f"{file.name}::{rid} 缺必填: {sorted(missing)}")

    if "budget_tier" in it and it["budget_tier"] not in BUDGET_TIER_ENUM:
        errors.append(
            f"{file.name}::{rid} budget_tier='{it['budget_tier']}' 不在枚举: {sorted(BUDGET_TIER_ENUM)}"
        )

    if "ab_role" in it and it["ab_role"] not in AB_ROLE_ENUM:
        errors.append(
            f"{file.name}::{rid} ab_role='{it['ab_role']}' 不在枚举: {sorted(AB_ROLE_ENUM)}"
        )

    if "meal_role" in it and it["meal_role"] not in MEAL_ROLE_ENUM:
        errors.append(
            f"{file.name}::{rid} meal_role='{it['meal_role']}' 不在枚举: {sorted(MEAL_ROLE_ENUM)}"
        )

    if "reservation_difficulty" in it and it["reservation_difficulty"] not in RESERVATION_DIFFICULTY_ENUM:
        errors.append(
            f"{file.name}::{rid} reservation_difficulty='{it['reservation_difficulty']}' 不在枚举"
        )

    if "queue_level" in it and it["queue_level"] not in QUEUE_LEVEL_ENUM:
        errors.append(f"{file.name}::{rid} queue_level='{it['queue_level']}' 不在枚举")

    if "depth" in it and it["depth"] not in DEPTH_ENUM:
        errors.append(f"{file.name}::{rid} depth='{it['depth']}' 不在枚举")

    for pk in ("price_lunch_jpy", "price_dinner_jpy"):
        if pk in it and it[pk] is not None and not isinstance(it[pk], (int, float)):
            errors.append(f"{file.name}::{rid} {pk} 非数字（或 null）")

    for lk in ("vibe_tags", "facility_tags", "risk_flags"):
        if lk in it and not isinstance(it[lk], list):
            errors.append(f"{file.name}::{rid} {lk} 非 list")

    if "notes" in it and not isinstance(it["notes"], str):
        errors.append(f"{file.name}::{rid} notes 非字符串")

    return errors


def validate_file(file: Path) -> tuple[int, int, list[str]]:
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except Exception as e:
        return 0, 1, [f"{file.name} JSON 解析失败: {e}"]

    if not isinstance(data, list):
        return 0, 1, [f"{file.name} 顶层非 list（餐厅池约定 list of dict）"]

    errors: list[str] = []
    seen_ids: set[str] = set()

    for i, it in enumerate(data):
        errors.extend(validate_item(it, i, file))
        if isinstance(it, dict) and "id" in it:
            if it["id"] in seen_ids:
                errors.append(f"{file.name}::{it['id']} 重复 ID")
            seen_ids.add(it["id"])

    return len(data), len(errors), errors


def collect_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target] if target.suffix == ".json" else []
    if target.is_dir():
        return sorted(target.rglob("restaurants__*.json"))
    return []


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("用法: python scripts/validate_restaurants.py <file_or_dir>")
        return 2

    target = Path(argv[1]).resolve()
    files = collect_files(target)
    if not files:
        print(f"未找到餐厅 JSON 文件: {target}")
        return 2

    total = 0
    total_errors = 0
    all_msgs: list[str] = []
    file_results = []

    for f in files:
        cnt, errs, msgs = validate_file(f)
        total += cnt
        total_errors += errs
        all_msgs.extend(msgs)
        file_results.append((str(f.relative_to(REPO_ROOT)), cnt, errs))

    print("=" * 60)
    print("餐厅池校验结果")
    print("=" * 60)
    for path, cnt, errs in file_results:
        status = "PASS" if errs == 0 else "FAIL"
        print(f"  [{status}] {path}  ({cnt} restaurants, {errs} errors)")
    print("-" * 60)
    print(f"合计: {total} restaurants, {total_errors} errors")

    if all_msgs:
        print()
        print("详细错误（前 200 条）:")
        for m in all_msgs[:200]:
            print(f"  - {m}")
        if len(all_msgs) > 200:
            print(f"  ... 还有 {len(all_msgs) - 200} 条未显示")

    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
