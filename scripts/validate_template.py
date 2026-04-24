"""D40 模板字段校验脚本。

每次改造模板后跑一次：
    python scripts/validate_template.py japan/kansai/templates/kyoto/arashiyama/1.json

校验整个目录：
    python scripts/validate_template.py japan/kansai/templates/kyoto/arashiyama/

校验规则对应 docs/03_数据契约/SCHEMA.md §4.4 + D40 新字段契约。违规 exit code != 0。
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_ROOT = REPO_ROOT / "japan/kansai/templates"
ENTITIES_ROOT = REPO_ROOT / "japan/kansai/entities"

# D40 新白名单：必填 4 个 + 可选 6 个
REQUIRED_TOP = {"template_id", "applicable_dates", "note", "slots"}
OPTIONAL_TOP = {
    "variant_label", "pace_type", "pace_type_sub",
    "time_sensitivity", "time_sensitivity_note", "contingencies",
}
# 已删字段 — 出现即报错
BANNED_TOP = {
    "label", "description", "curators_notes", "hotel_area_note",
    "min_days", "selectable_tag", "day_type", "exclusive_with",
    "night_options", "template_kind", "downgrade_target",
    "core_experience", "audience_bonus", "execution_risk",
}

SLOT_TYPES = {"poi", "meal", "hotel", "transport", "free_time"}
CONTINGENCIES_ALLOWED = {"rain_light", "rain_heavy", "crowd", "indoor_backup", "late_start"}
CONTINGENCIES_BANNED = {"swap_candidates", "minimum_viable"}

PACE_TYPE_VALUES = {"adaptive", "fixed_early", "deep_stay"}
PACE_TYPE_SUB_VALUES = {"onsen", "deep_local"}
TIME_SENSITIVITY_VALUES = {"flexible", "soft", "hard"}

VARIANT_LABEL_BANNED_SUBSTRINGS = {"fixed_early", "adaptive", "deep_stay", "9 点档"}


def load_entity_ids() -> set[str]:
    ids: set[str] = set()
    if not ENTITIES_ROOT.exists():
        return ids
    for p in ENTITIES_ROOT.glob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict):
            for k in data.keys():
                if not k.startswith("_"):
                    ids.add(k)
    return ids


def _parse_time(t: str):
    try:
        hh, mm = t.split("-", 1)[0].split(":")
        return int(hh) * 60 + int(mm)
    except Exception:
        return None


def validate_template(path: Path, entity_ids: set[str]) -> list[str]:
    errors: list[str] = []
    rel = path.relative_to(REPO_ROOT).as_posix()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return [f"{rel}: JSON 解析失败: {e}"]

    if not isinstance(data, dict):
        return [f"{rel}: 顶层不是对象"]

    for k in REQUIRED_TOP:
        if k not in data:
            errors.append(f"{rel}: 顶层缺必填字段 `{k}`")

    # D40: 已删字段不允许出现
    for k in BANNED_TOP:
        if k in data:
            errors.append(f"{rel}: 顶层有已删字段 `{k}`（D40 已删，需移除）")

    unknown = set(data.keys()) - REQUIRED_TOP - OPTIONAL_TOP - BANNED_TOP
    for k in unknown:
        errors.append(f"{rel}: 顶层有未知字段 `{k}`（已砍或应挪装配层）")

    # D40: pace_type 枚举校验
    pt = data.get("pace_type")
    if pt is not None and pt not in PACE_TYPE_VALUES:
        errors.append(f"{rel}: pace_type=`{pt}` 不合法，合法值 {PACE_TYPE_VALUES}")
    pts = data.get("pace_type_sub")
    if pts is not None:
        if pt != "deep_stay":
            errors.append(f"{rel}: pace_type_sub 只在 pace_type=deep_stay 时可写")
        elif pts not in PACE_TYPE_SUB_VALUES:
            errors.append(f"{rel}: pace_type_sub=`{pts}` 不合法，合法值 {PACE_TYPE_SUB_VALUES}")
    if pt == "deep_stay" and not pts:
        errors.append(f"{rel}: pace_type=deep_stay 必须有 pace_type_sub")

    # D40: time_sensitivity 枚举校验 + time_sensitivity_note 必填
    ts = data.get("time_sensitivity")
    if ts is not None and ts not in TIME_SENSITIVITY_VALUES:
        errors.append(f"{rel}: time_sensitivity=`{ts}` 不合法，合法值 {TIME_SENSITIVITY_VALUES}")
    if ts in ("soft", "hard") and not data.get("time_sensitivity_note"):
        errors.append(f"{rel}: time_sensitivity={ts} 时必须有 time_sensitivity_note")

    # D40: fixed_early / time_sensitivity=hard 必须有 contingencies.late_start
    needs_late_start = (pt == "fixed_early") or (ts == "hard")
    cg = data.get("contingencies")
    if needs_late_start:
        if not isinstance(cg, dict) or not cg.get("late_start"):
            errors.append(f"{rel}: pace_type=fixed_early 或 time_sensitivity=hard 时 contingencies.late_start 必填")

    # D40: variant_label 不含技术术语，长度 ≤ 20
    vl = data.get("variant_label")
    if vl is not None:
        if len(vl) > 20:
            errors.append(f"{rel}: variant_label 长度 {len(vl)} > 20 字")
        for banned in VARIANT_LABEL_BANNED_SUBSTRINGS:
            if banned in vl:
                errors.append(f"{rel}: variant_label 含禁用词 `{banned}`")

    ad = data.get("applicable_dates", [])
    if not isinstance(ad, list):
        errors.append(f"{rel}: applicable_dates 不是数组")
    else:
        for i, e in enumerate(ad):
            if not isinstance(e, dict):
                errors.append(f"{rel}: applicable_dates[{i}] 不是对象")
                continue
            for k in ("start", "end", "label"):
                if k not in e:
                    errors.append(f"{rel}: applicable_dates[{i}] 缺 `{k}`")
            for k in ("start", "end"):
                v = e.get(k, "")
                if v and not (len(v) == 5 and v[2] == "-"):
                    errors.append(f"{rel}: applicable_dates[{i}].{k}=`{v}` 格式错（应 MM-DD）")

    if cg is not None:
        if not isinstance(cg, dict):
            errors.append(f"{rel}: contingencies 不是对象")
        else:
            for k in cg.keys():
                if k in CONTINGENCIES_BANNED:
                    errors.append(f"{rel}: contingencies.{k} 已砍不允许")
                elif k not in CONTINGENCIES_ALLOWED:
                    errors.append(f"{rel}: contingencies.{k} 不在合法子项 {CONTINGENCIES_ALLOWED}")

    slots = data.get("slots")
    if not isinstance(slots, list):
        errors.append(f"{rel}: slots 不是数组")
        return errors

    entity_occur: dict[str, list] = {}
    last_min = None
    for si, seg in enumerate(slots):
        if not isinstance(seg, dict):
            errors.append(f"{rel}: slots[{si}] 不是对象")
            continue
        t = seg.get("time")
        if not t:
            errors.append(f"{rel}: slots[{si}] 缺 time")
        cur = _parse_time(t) if t else None
        if cur is not None and last_min is not None and cur < last_min:
            errors.append(f"{rel}: slots[{si}] time={t} 早于前一段")
        if cur is not None:
            last_min = cur

        main = seg.get("main")
        if not isinstance(main, list) or len(main) == 0:
            errors.append(f"{rel}: slots[{si}] main 必须 ≥1，不能空")
            main = []

        for bucket, slots_list in (("main", main), ("optional", seg.get("optional", []) or [])):
            if not isinstance(slots_list, list):
                errors.append(f"{rel}: slots[{si}].{bucket} 不是数组")
                continue
            for sj, slot in enumerate(slots_list):
                if not isinstance(slot, dict):
                    errors.append(f"{rel}: slots[{si}].{bucket}[{sj}] 不是对象")
                    continue
                tp = slot.get("type")
                if tp not in SLOT_TYPES:
                    errors.append(f"{rel}: slots[{si}].{bucket}[{sj}].type=`{tp}` 不合法")

                if tp == "poi":
                    ent = slot.get("entity")
                    if not ent:
                        errors.append(f"{rel}: slots[{si}].{bucket}[{sj}] poi 缺 entity")
                    else:
                        if entity_ids and ent not in entity_ids:
                            errors.append(f"{rel}: slots[{si}].{bucket}[{sj}].entity=`{ent}` 在 entities/ 不存在")
                        entity_occur.setdefault(ent, []).append((si, bucket, sj, slot))
                elif tp == "meal":
                    if "entity" in slot:
                        errors.append(f"{rel}: slots[{si}].{bucket}[{sj}] meal 不允许写 entity")
                    for k in ("meal_type", "meal_area"):
                        if not slot.get(k):
                            errors.append(f"{rel}: slots[{si}].{bucket}[{sj}] meal 缺 `{k}`")
                elif tp == "hotel":
                    if "entity" in slot:
                        errors.append(f"{rel}: slots[{si}].{bucket}[{sj}] hotel 不允许写 entity")
                    if not slot.get("hotel_area"):
                        errors.append(f"{rel}: slots[{si}].{bucket}[{sj}] hotel 缺 hotel_area")
                elif tp == "free_time":
                    if "entity" in slot:
                        errors.append(f"{rel}: slots[{si}].{bucket}[{sj}] free_time 不允许挂 entity")
                    for k in ("theme", "options_note"):
                        if not slot.get(k):
                            errors.append(f"{rel}: slots[{si}].{bucket}[{sj}] free_time 缺 `{k}`")

    for ent, occ in entity_occur.items():
        if len(occ) >= 2:
            for si, bucket, sj, slot in occ:
                if not slot.get("note"):
                    errors.append(
                        f"{rel}: entity `{ent}` 出现 {len(occ)} 次，slots[{si}].{bucket}[{sj}] 必须写 note 区分用途"
                    )

    return errors


def validate_route_folder(folder: Path) -> list[str]:
    errors: list[str] = []
    rel = folder.relative_to(REPO_ROOT).as_posix()
    is_pool = folder.name in {"half_day", "arrivals", "departures", "special_dates", "special_events", "niche_spots"}

    if not is_pool:
        # D40: index.md 已统一改名为 动线说明.md（兼容旧 index.md）
        has_linedesc = (folder / "动线说明.md").exists() or (folder / "index.md").exists()
        if not has_linedesc:
            errors.append(f"{rel}: 动线文件夹缺 动线说明.md（或 index.md）")
        if not (folder / "transport.md").exists():
            errors.append(f"{rel}: 动线文件夹缺 transport.md")

        json_files = sorted(
            [p for p in folder.glob("*.json") if p.stem.isdigit()],
            key=lambda p: int(p.stem),
        )
        if json_files:
            nums = [int(p.stem) for p in json_files]
            expected = list(range(1, max(nums) + 1))
            missing = set(expected) - set(nums)
            if missing:
                errors.append(f"{rel}: 编号不连续，缺 {sorted(missing)}")

    return errors


def main():
    args = sys.argv[1:]
    target = Path(args[0]) if args else TEMPLATES_ROOT
    if not target.is_absolute():
        target = REPO_ROOT / target

    entity_ids = load_entity_ids()
    if not entity_ids:
        print("[WARN] entities/ 未找到或为空，entity 引用校验跳过")

    all_errors: list[str] = []

    if target.is_file():
        all_errors.extend(validate_template(target, entity_ids))
    elif target.is_dir():
        for p in sorted(target.rglob("*.json")):
            if any(part.startswith("_") for part in p.parts):
                continue
            if "entities" in p.parts or ("assembly" in p.parts and "data" in p.parts):
                continue
            all_errors.extend(validate_template(p, entity_ids))

        for sub in sorted(target.rglob("*")):
            if not sub.is_dir():
                continue
            if any(part.startswith("_") for part in sub.parts):
                continue
            try:
                relparts = sub.relative_to(TEMPLATES_ROOT).parts
            except ValueError:
                continue
            if len(relparts) == 2:
                all_errors.extend(validate_route_folder(sub))
    else:
        print(f"[ERROR] 路径不存在: {target}")
        sys.exit(2)

    if all_errors:
        print(f"\n[FAIL] 发现 {len(all_errors)} 处违规:\n")
        for e in all_errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("[OK] 所有校验通过")
        sys.exit(0)


if __name__ == "__main__":
    main()
