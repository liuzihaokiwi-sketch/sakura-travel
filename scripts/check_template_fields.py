"""检查所有日模板的字段完整性，输出缺失/异常报告。"""
import json
import sys
from pathlib import Path

CONTENT_DIR = Path(__file__).resolve().parent.parent / "content" / "kansai"

REQUIRED_TOP = ["template_id", "label", "tags", "core_entities", "fit_audience",
                "weather_sensitive", "assembly", "description"]
REQUIRED_ASM = ["phase", "best_pace"]
REQUIRED_SLOT = ["slot_id", "type"]
# slot 非 transport/shop_info 时需要的字段
REQUIRED_SLOT_POI = ["area", "priority", "duration_min", "note"]
# 这些 type 不要求 area 和 duration_min（位置/时长不固定）
EXEMPT_AREA_TYPES = {"rest", "cafe_info", "photo_spots"}
EXEMPT_DURATION_TYPES = {"rest", "cafe_info", "photo_spots"}

VALID_PHASES = {"arrival", "departure", "transfer", "sightseeing"}
VALID_BEST_PACE = {"compact", "standard", "relaxed", "locked"}
VALID_SLOT_PRIORITIES = {"P1", "P2", "P3"}
VALID_FIT = {"all", "couple", "friends", "family", "default", "elderly"}

issues: list[str] = []


def check_template(path: Path, tmpl: dict) -> None:
    tid = tmpl.get("template_id", path.stem)
    prefix = f"{path.relative_to(CONTENT_DIR)}::{tid}"

    # 顶层必填
    for f in REQUIRED_TOP:
        if f not in tmpl or tmpl[f] is None:
            if f == "core_entities":
                continue  # 允许空列表
            issues.append(f"[缺字段] {prefix}: 缺 {f}")

    # description 里有 day_mood
    desc = tmpl.get("description", "")
    if "day_mood" not in desc:
        issues.append(f"[缺day_mood] {prefix}: description 中没有 day_mood")

    # assembly
    asm = tmpl.get("assembly", {})
    for f in REQUIRED_ASM:
        if f not in asm:
            issues.append(f"[缺assembly] {prefix}: assembly 缺 {f}")
    if asm.get("phase") and asm["phase"] not in VALID_PHASES:
        issues.append(f"[无效值] {prefix}: assembly.phase={asm['phase']} 不在合法值中")
    if asm.get("best_pace") and asm["best_pace"] not in VALID_BEST_PACE:
        issues.append(f"[无效值] {prefix}: assembly.best_pace={asm['best_pace']} 不在合法值中")
    # 旧字段残留检查
    for old_field in ("role", "priority", "fatigue"):
        if old_field in asm:
            issues.append(f"[旧字段残留] {prefix}: assembly 仍有已废弃的 {old_field}")

    # fit_audience
    fit = tmpl.get("fit_audience", "all")
    if isinstance(fit, str):
        if fit not in VALID_FIT:
            issues.append(f"[无效值] {prefix}: fit_audience={fit}")
    elif isinstance(fit, list):
        for a in fit:
            if a not in VALID_FIT:
                issues.append(f"[无效值] {prefix}: fit_audience 含无效值 {a}")

    # hotel_area_note（非 departure 模板应有）
    phase = asm.get("phase", "")
    if phase != "departure" and not tmpl.get("hotel_area_note"):
        issues.append(f"[缺字段] {prefix}: 缺 hotel_area_note")

    # slots
    slots = tmpl.get("slots", [])
    days = tmpl.get("days")
    if days:
        # 多日模板
        for i, day_slots in enumerate(days):
            _check_slots(prefix, f"D{i+1}", day_slots)
    elif slots:
        _check_slots(prefix, "", slots)
    else:
        issues.append(f"[缺slots] {prefix}: 没有 slots 也没有 days")

    # P1 至少一个（游玩日应有灵魂景点）
    all_slots = slots if not days else [s for d in days for s in d]
    p1_count = sum(1 for s in all_slots if s.get("priority") == "P1")
    has_core = bool(tmpl.get("core_entities"))
    if p1_count == 0 and phase == "sightseeing" and has_core and asm.get("best_pace") not in ("relaxed", "locked"):
        issues.append(f"[无P1] {prefix}: 没有 P1 级别的 slot")

    # P4/P5 残留（应已清理）
    for s in all_slots:
        p = s.get("priority", "")
        if p in ("P4", "P5") and s.get("type") != "shop_info":
            issues.append(f"[P4/P5残留] {prefix}: slot {s.get('slot_id')} 仍有 {p}")


def _check_slots(prefix: str, day_label: str, slots: list[dict]) -> None:
    day_str = f" {day_label}" if day_label else ""
    for s in slots:
        sid = s.get("slot_id", "?")
        sp = f"{prefix}{day_str}::{sid}"
        for f in REQUIRED_SLOT:
            if f not in s:
                issues.append(f"[缺slot字段] {sp}: 缺 {f}")

        stype = s.get("type", "")
        if stype not in ("transport", "shop_info", "evening_auto"):
            for f in REQUIRED_SLOT_POI:
                if f not in s or s[f] is None:
                    # note 允许为空字符串但不允许缺
                    if f == "note" and s.get(f) == "":
                        continue
                    # rest/cafe_info/photo_spots 不要求 area 和 duration_min
                    if f == "area" and stype in EXEMPT_AREA_TYPES:
                        continue
                    if f == "duration_min" and stype in EXEMPT_DURATION_TYPES:
                        continue
                    # "白天照常"类占位 optional_poi 不要求 duration_min
                    if f == "duration_min" and stype == "optional_poi":
                        note = s.get("note", "")
                        if "白天照常" in note or "白天は通常" in note:
                            continue
                    issues.append(f"[缺slot字段] {sp}: 缺 {f}")

        # slot priority 合法性
        pri = s.get("priority", "")
        if pri and pri not in VALID_SLOT_PRIORITIES and stype != "shop_info":
            issues.append(f"[无效值] {sp}: priority={pri}")

        # note 太短（< 10字可能是占位）
        note = s.get("note", "")
        if stype not in ("transport", "shop_info") and note and len(note) < 10:
            issues.append(f"[note太短] {sp}: note 只有 {len(note)} 字")


def main() -> None:
    template_count = 0
    for city_dir in sorted(CONTENT_DIR.iterdir()):
        days_dir = city_dir / "days"
        if not days_dir.is_dir():
            continue
        for f in sorted(days_dir.glob("*.json")):
            if f.name.startswith("_"):
                continue
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                issues.append(f"[JSON错误] {f.relative_to(CONTENT_DIR)}: {e}")
                continue
            check_template(f, data)
            template_count += 1

    print(f"\n检查完成：{template_count} 个模板\n")
    if issues:
        print(f"发现 {len(issues)} 个问题：\n")
        for issue in issues:
            print(f"  {issue}")
        sys.exit(1)
    else:
        print("全部通过！")
        sys.exit(0)


if __name__ == "__main__":
    main()
