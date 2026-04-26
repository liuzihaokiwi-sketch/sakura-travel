"""entity 字段校验脚本（D43 新版）。

每次改造 entity 数据后跑一次：
    python scripts/validate_entity.py japan/kansai/entities/kyoto.json

校验整个目录：
    python scripts/validate_entity.py japan/kansai/entities/

校验规则对应 docs/03_数据契约/字段权威.md §2.1（D43）。违规 exit code != 0。

设计原则：
- 字段白名单 + 必填 + 枚举三层校验
- AI 加新字段 = FAIL（防字段膨胀，铁律 1）
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent

# SCHEMA §2.1.1 系统字段（必填 5 + 选填 2）
REQUIRED_TOP = {"entity_id", "city", "area", "category", "depth", "可信度"}
OPTIONAL_TOP = {"season_months", "reservation"}
RESERVATION_ENUM = {"none", "recommended", "required", "hard"}

# area_registry 白名单（D44 加固·此前 validator 漏校验）
_REGISTRY_PATH = REPO_ROOT / "japan/kansai/area_registry.json"
try:
    AREA_REGISTRY = {r["area"] for r in json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))}
except Exception:
    AREA_REGISTRY = set()
# SCHEMA §2.1.4 元数据
META_TOP = {"数据来源", "最后核实"}
# note 块
NOTE_REQUIRED = {"店名", "简介"}
NOTE_OPTIONAL = {"票价", "营业", "怎么去"}
# templates_meta 块
TEMPLATES_META_KEYS = {"亮点", "拍照位置", "冷知识", "衔接", "季节看点", "顺路小店", "避坑"}

ALLOWED_TOP = REQUIRED_TOP | OPTIONAL_TOP | META_TOP | {"note", "templates_meta"}

# SCHEMA §2.1.5 category 枚举（D44 瘦身：33 英文 → 12 中文）
CATEGORY_ENUM = {
    "寺社", "城", "庭园", "自然", "展望", "博物馆",
    "水族动物", "主题乐园", "体验", "街区", "温泉", "交通",
}

DEPTH_ENUM = {"full", "verified", "skeleton"}

CONFIDENCE_ENUM = {"verified", "cross_checked", "single_source", "ai_generated"}

CITY_ENUM = {
    "kyoto", "osaka", "nara", "kobe", "arima", "himeji",
    "koyasan", "kinosaki", "kumano", "amanohashidate", "other",
}


def validate_entity(eid: str, data: dict, file: Path) -> list[str]:
    errors: list[str] = []

    if not isinstance(data, dict):
        errors.append(f"{file.name}::{eid} 不是 dict 对象")
        return errors

    # 1. 顶层字段白名单
    unknown = set(data.keys()) - ALLOWED_TOP
    if unknown:
        errors.append(f"{file.name}::{eid} 含未知顶层字段（防膨胀）: {sorted(unknown)}")

    # 2. 必填顶层字段
    missing = REQUIRED_TOP - set(data.keys())
    if missing:
        errors.append(f"{file.name}::{eid} 缺必填字段: {sorted(missing)}")

    # 3. entity_id 一致
    if "entity_id" in data and data["entity_id"] != eid:
        errors.append(f"{file.name}::{eid} entity_id 字段值 '{data['entity_id']}' 与 key 不一致")

    # 4. category 枚举
    if "category" in data and data["category"] not in CATEGORY_ENUM:
        errors.append(
            f"{file.name}::{eid} category='{data['category']}' 不在 SCHEMA §2.1.5 枚举内"
        )

    # 5. depth 枚举
    if "depth" in data and data["depth"] not in DEPTH_ENUM:
        errors.append(f"{file.name}::{eid} depth='{data['depth']}' 不在枚举 {DEPTH_ENUM}")

    # 6. city 枚举
    if "city" in data and data["city"] not in CITY_ENUM:
        errors.append(f"{file.name}::{eid} city='{data['city']}' 不在枚举 {CITY_ENUM}")

    # 7. 可信度枚举
    if "可信度" in data and data["可信度"] not in CONFIDENCE_ENUM:
        errors.append(f"{file.name}::{eid} 可信度='{data['可信度']}' 不在枚举 {CONFIDENCE_ENUM}")

    # 7b. reservation 枚举（D44）
    if "reservation" in data and data["reservation"] not in RESERVATION_ENUM:
        errors.append(
            f"{file.name}::{eid} reservation='{data['reservation']}' 不在枚举 {RESERVATION_ENUM}"
        )

    # 7c. area 必须在 area_registry（D44 加固）
    if "area" in data and AREA_REGISTRY and data["area"] not in AREA_REGISTRY:
        errors.append(
            f"{file.name}::{eid} area='{data['area']}' 不在 area_registry.json·"
            f"按 entity 规范铁律 4：不许自创·停下报告"
        )

    # 8. note 块校验
    if "note" in data:
        note = data["note"]
        if not isinstance(note, dict):
            errors.append(f"{file.name}::{eid} note 非 dict")
        else:
            unknown_note = set(note.keys()) - NOTE_REQUIRED - NOTE_OPTIONAL
            if unknown_note:
                errors.append(f"{file.name}::{eid} note 含未知 key: {sorted(unknown_note)}")
            missing_note = NOTE_REQUIRED - set(note.keys())
            if missing_note:
                errors.append(f"{file.name}::{eid} note 缺必填 key: {sorted(missing_note)}")
            for k in NOTE_REQUIRED | NOTE_OPTIONAL:
                if k in note and not isinstance(note[k], str):
                    errors.append(f"{file.name}::{eid} note.{k} 非字符串")
    else:
        # note 块本身必填
        errors.append(f"{file.name}::{eid} 缺 note 块")

    # 9. templates_meta 块校验（整块选填，有则校验 key）
    if "templates_meta" in data:
        tm = data["templates_meta"]
        if tm is not None:
            if not isinstance(tm, dict):
                errors.append(f"{file.name}::{eid} templates_meta 非 dict")
            else:
                unknown_tm = set(tm.keys()) - TEMPLATES_META_KEYS
                if unknown_tm:
                    errors.append(
                        f"{file.name}::{eid} templates_meta 含未知 key: {sorted(unknown_tm)}"
                    )
                for k in TEMPLATES_META_KEYS:
                    if k in tm and not isinstance(tm[k], str):
                        errors.append(f"{file.name}::{eid} templates_meta.{k} 非字符串")

    # 10. season_months 结构
    if "season_months" in data:
        sm = data["season_months"]
        if sm is not None:
            if not isinstance(sm, list):
                errors.append(f"{file.name}::{eid} season_months 非 list 也非 null")
            else:
                for m in sm:
                    if not isinstance(m, int) or m < 1 or m > 12:
                        errors.append(f"{file.name}::{eid} season_months 含非法月份值: {m}")

    # 11. 数据来源 结构
    if "数据来源" in data:
        ds = data["数据来源"]
        if ds is not None and not isinstance(ds, list):
            errors.append(f"{file.name}::{eid} 数据来源 非 list")

    return errors


def validate_file(file: Path) -> tuple[int, int, list[str]]:
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except Exception as e:
        return 0, 1, [f"{file.name} JSON 解析失败: {e}"]

    if not isinstance(data, dict):
        return 0, 1, [f"{file.name} 顶层非 dict"]

    errors: list[str] = []
    count = 0
    seen_ids: dict[str, str] = {}

    for eid, ent in data.items():
        if eid == "_meta":
            continue
        count += 1

        if eid in seen_ids:
            errors.append(f"{file.name}::{eid} 在同文件内重复")
        seen_ids[eid] = file.name

        errors.extend(validate_entity(eid, ent, file))

    return count, len(errors), errors


def collect_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target] if target.suffix == ".json" else []
    if target.is_dir():
        return sorted(p for p in target.rglob("*.json") if p.name != "_meta.json")
    return []


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("用法: python scripts/validate_entity.py <file_or_dir>")
        return 2

    target = Path(argv[1]).resolve()
    files = collect_files(target)
    if not files:
        print(f"未找到 JSON 文件: {target}")
        return 2

    total_entities = 0
    total_errors = 0
    all_msgs: list[str] = []
    file_results: list[tuple[str, int, int]] = []

    for f in files:
        cnt, errs, msgs = validate_file(f)
        total_entities += cnt
        total_errors += errs
        all_msgs.extend(msgs)
        file_results.append((str(f.relative_to(REPO_ROOT)), cnt, errs))

    print("=" * 60)
    print("entity 校验结果（D43 新版）")
    print("=" * 60)
    for path, cnt, errs in file_results:
        status = "PASS" if errs == 0 else "FAIL"
        print(f"  [{status}] {path}  ({cnt} entities, {errs} errors)")
    print("-" * 60)
    print(f"合计: {total_entities} entities, {total_errors} errors")

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
