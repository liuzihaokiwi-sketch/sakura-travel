"""D40 JSON 批量改造脚本。

任务：
1. 删除 14 个冗余字段（实际存在 label/description/curators_notes/hotel_area_note）
   - curators_notes / hotel_area_note 有内容则并入 note
2. 按指定映射加 pace_type / pace_type_sub
3. 岚山 7 个模板回滚标签（time_sensitivity）
4. 清理过时文字（D38/D36/D37 章节引用 + index.md 引用 + fixed_early 无效旧句）
5. 精简 variant_label（只留白名单里的 10 个，其余删）

运行：
    python scripts/d40_transform.py
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_ROOT = REPO_ROOT / "japan/kansai/templates"

FIELDS_TO_DELETE = {
    "label", "description", "curators_notes", "hotel_area_note",
    "min_days", "selectable_tag", "day_type", "exclusive_with",
    "night_options", "template_kind", "downgrade_target",
    "core_experience", "audience_bonus", "execution_risk",
}

# pace_type 映射（template_id -> {pace_type, pace_type_sub?}）
PACE_TYPE_MAP = {
    "kyoto_arashiyama_5": {"pace_type": "fixed_early"},
    "kyoto_arashiyama_8": {"pace_type": "deep_stay", "pace_type_sub": "onsen"},
    "kyoto_arashiyama_9": {"pace_type": "deep_stay", "pace_type_sub": "deep_local"},
    "kyoto_arashiyama_10": {"pace_type": "deep_stay", "pace_type_sub": "deep_local"},
    "other_arima_1": {"pace_type": "deep_stay", "pace_type_sub": "onsen"},
    "other_arima_3": {"pace_type": "deep_stay", "pace_type_sub": "onsen"},
    "other_kinosaki_1": {"pace_type": "deep_stay", "pace_type_sub": "onsen"},
    "other_koyasan_1": {"pace_type": "deep_stay", "pace_type_sub": "deep_local"},
    "kyoto_takao_2": {"pace_type": "deep_stay", "pace_type_sub": "onsen"},
}

# time_sensitivity 映射（key = template_id）
# None = 归 adaptive，清掉已有的 time_sensitivity
TIME_SENSITIVITY_MAP = {
    "kyoto_arashiyama_2": None,
    "kyoto_arashiyama_3": {"time_sensitivity": "soft", "time_sensitivity_note": "樱花季 10:00 后人满，早到抢空景"},
    "kyoto_arashiyama_5": {"time_sensitivity": "hard"},  # fixed_early 标配
    "kyoto_arashiyama_6": {"time_sensitivity": "soft", "time_sensitivity_note": "红叶季早到抢空景"},
    "kyoto_arashiyama_7": {"time_sensitivity": "soft", "time_sensitivity_note": "嵯峨野小火车 1 小时一班，出门提前 20 分钟赶最近班次"},
    "kyoto_arashiyama_9": None,
    "kyoto_arashiyama_10": None,
    "kyoto_okazaki_tetsugaku_2": {"time_sensitivity": "soft", "time_sensitivity_note": "瑠璃光院抽签全天多场次每 20 分钟一场，按指定时刻反推出发"},
}

# variant_label 白名单（只保留这些 template_id 的 variant_label，且用新值覆盖）
VARIANT_LABEL_KEEP = {
    "kyoto_arashiyama_5": "晨光岚山·追光三站",
    "kyoto_arashiyama_7": "上山坐火车·下山坐船",
    "kyoto_arashiyama_8": "岚山温泉·住一夜",
    "kyoto_arashiyama_9": "岚山·夜枫与清晨",
    "kyoto_arashiyama_10": "岚山·夜樱与清晨",
    "other_koyasan_1": "宿坊早朝·奥之院",
}

# 过时文字片段（模板 note 里出现这些，要清除的句子前缀/关键词）
STALE_PHRASES = [
    "本模板 fixed_early·出门档无效（D38 §9.5）",
    "assembly/templates/index.md",
    "D36 §",
    "D37 §",
    "D38 §",
    "（D38 §",
    "（D36 §",
    "（D37 §",
]


def merge_into_note(note: str, hotel_area_note: str, curators_notes: list[str]) -> str:
    """把 hotel_area_note 和 curators_notes 并入 note。"""
    parts = [note.rstrip()] if note else []

    if hotel_area_note and hotel_area_note.strip():
        hn = hotel_area_note.strip()
        # 检查 note 里是否已经包含了大部分内容（避免重复）
        if hn[:20] not in note:
            parts.append("\n\n**住宿区域参考**：" + hn)

    if curators_notes:
        notes_list = [x.strip() for x in curators_notes if x and x.strip()]
        if notes_list:
            # 检查是否已并入
            first = notes_list[0][:15]
            if first not in note:
                cn_block = "\n\n**策展细节**：\n" + "\n".join(f"- {x}" for x in notes_list)
                parts.append(cn_block)

    return "".join(parts)


def clean_stale_phrases(text: str) -> str:
    """清理 note 里的过时文字（按句子粒度）。"""
    if not text:
        return text
    # 按行处理，删除包含过时引用的行
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        skip = False
        for phrase in STALE_PHRASES:
            if phrase in line:
                # 如果整行就是这个句子，删除；否则只删这个片段
                # 这里简单处理：把这些片段从行中移除
                line = line.replace(phrase, "").strip()
                if not line:
                    skip = True
                    break
        if not skip:
            cleaned.append(line)
    # 合并并清理多余空行
    result = "\n".join(cleaned)
    while "\n\n\n" in result:
        result = result.replace("\n\n\n", "\n\n")
    return result.strip()


def transform_template(path: Path) -> tuple[bool, str]:
    """改造单个模板 JSON。返回 (changed, template_id)。"""
    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
    except Exception as e:
        return False, f"ERROR loading {path}: {e}"

    if not isinstance(data, dict):
        return False, ""

    tid = data.get("template_id", "")
    changed = False

    # Step 1: 合并 curators_notes / hotel_area_note 到 note（如有）
    hotel_note = data.get("hotel_area_note", "")
    curator_notes = data.get("curators_notes", [])
    if isinstance(curator_notes, str):
        curator_notes = [curator_notes] if curator_notes else []
    old_note = data.get("note", "")
    new_note = merge_into_note(old_note, hotel_note, curator_notes)
    if new_note != old_note:
        data["note"] = new_note
        changed = True

    # Step 2: 清理过时文字
    note_clean = clean_stale_phrases(data.get("note", ""))
    if note_clean != data.get("note", ""):
        data["note"] = note_clean
        changed = True

    # Step 3: 删除冗余字段
    for f in FIELDS_TO_DELETE:
        if f in data:
            del data[f]
            changed = True

    # Step 4: pace_type
    if tid in PACE_TYPE_MAP:
        pt = PACE_TYPE_MAP[tid]
        for k, v in pt.items():
            if data.get(k) != v:
                data[k] = v
                changed = True
    else:
        # adaptive 是默认，不写
        for k in ("pace_type", "pace_type_sub"):
            if k in data:
                del data[k]
                changed = True

    # Step 5: time_sensitivity（只处理明确在映射里的模板）
    if tid in TIME_SENSITIVITY_MAP:
        ts_config = TIME_SENSITIVITY_MAP[tid]
        # 先清掉已有的
        for k in ("time_sensitivity", "time_sensitivity_note"):
            if k in data:
                del data[k]
                changed = True
        if ts_config:
            for k, v in ts_config.items():
                data[k] = v
                changed = True
    else:
        # 清掉错误贴上的（arashiyama 5 如果有旧的 time_sensitivity 先清，后面加 hard）
        pass

    # arashiyama_5: fixed_early 必须 time_sensitivity=hard
    if tid == "kyoto_arashiyama_5":
        if data.get("time_sensitivity") != "hard":
            data["time_sensitivity"] = "hard"
            changed = True
        if not data.get("time_sensitivity_note"):
            data["time_sensitivity_note"] = "三机位晨光轮转按绝对时刻走，起晚了看 contingencies.late_start"
            changed = True

    # Step 6: variant_label
    if tid in VARIANT_LABEL_KEEP:
        new_vl = VARIANT_LABEL_KEEP[tid]
        if data.get("variant_label") != new_vl:
            data["variant_label"] = new_vl
            changed = True
    else:
        # 删除
        if "variant_label" in data:
            del data["variant_label"]
            changed = True

    # Step 7: contingencies.late_start
    # fixed_early + time_sensitivity=hard 必须有 late_start
    if data.get("pace_type") == "fixed_early" or data.get("time_sensitivity") == "hard":
        if "contingencies" not in data:
            data["contingencies"] = {}
        if not isinstance(data["contingencies"], dict):
            data["contingencies"] = {}
        if "late_start" not in data["contingencies"]:
            if tid == "kyoto_arashiyama_5":
                data["contingencies"]["late_start"] = (
                    "若 7:00 之后才出门——渡月桥晨光+竹林光柱两个机位已错过，不追了。"
                    "直接去 % ARABICA 渡月桥店排队看桥，9:00 再走天龙寺曹源池（无开门即进的水面倒影但大方丈+法堂云龙图仍值得）。"
                    "下午按原计划嵯峨野民居樱漫步→奥嵯峨三寺→17:00 渡月桥 peak-end。出片体验打 6 折但岚山一日不崩。"
                )
            else:
                data["contingencies"]["late_start"] = "晚出发时按实际时刻从当前位置出发，跳过错过的时段，直接去最近景点。"
            changed = True

    if changed:
        # 保持字段顺序：必填在前，可选在后
        ORDER = ["template_id", "applicable_dates", "note", "slots",
                 "variant_label", "pace_type", "pace_type_sub",
                 "time_sensitivity", "time_sensitivity_note", "contingencies"]
        ordered = {}
        for k in ORDER:
            if k in data:
                ordered[k] = data[k]
        for k, v in data.items():
            if k not in ordered:
                ordered[k] = v
        path.write_text(json.dumps(ordered, ensure_ascii=False, indent=2), encoding="utf-8")

    return changed, tid


def main():
    templates = sorted([
        p for p in TEMPLATES_ROOT.rglob("*.json")
        if not any(part.startswith("_") for part in p.parts)
        and "entities" not in p.parts
        and not ("assembly" in p.parts and "data" in p.parts)
    ])

    changed_count = 0
    for path in templates:
        changed, tid = transform_template(path)
        if changed:
            changed_count += 1
            print(f"  改造: {path.relative_to(REPO_ROOT).as_posix()} [{tid}]")

    print(f"\n完成：{changed_count}/{len(templates)} 个文件已改造")


if __name__ == "__main__":
    main()
