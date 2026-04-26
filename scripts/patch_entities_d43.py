#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_entities_d43.py
D43 entity 格式大瘦身：旧格式 → 新格式
处理 kyoto.json / osaka.json / other.json
"""

import json
import re
import sys
from pathlib import Path

# ── city 推断映射 ─────────────────────────────────────────────────────────────

CITY_MAP = {
    # 京都
    "arashiyama": "kyoto", "higashiyama": "kyoto", "kitayama": "kyoto",
    "okazaki": "kyoto", "tetsugaku_no_michi": "kyoto", "fushimi": "kyoto",
    "uji": "kyoto", "nijo": "kyoto", "kyoto_station": "kyoto",
    "gion": "kyoto", "kawaramachi": "kyoto", "kitano": "kyoto",
    "kurama": "kyoto", "kibune": "kyoto", "ohara": "kyoto",
    "sagano": "kyoto", "arashiyama_sagano": "kyoto", "kita": "kyoto",
    # 京都子区（entities 实际使用的 area 值补充）
    "nakagyo": "kyoto", "higashiyama_north": "kyoto", "sakyo": "kyoto",
    "south_kyoto": "kyoto", "kinkaku_nishiyama": "kyoto", "central_kyoto": "kyoto",
    "kyoto_center": "kyoto", "pontocho_kawaramachi": "kyoto", "karasuma_oike": "kyoto",
    "daigo": "kyoto", "takao": "kyoto", "nishikyo": "kyoto",
    "yase": "kyoto", "nagaokakyo": "kyoto", "yawata": "kyoto",
    # 大阪
    "namba": "osaka", "osaka_kita": "osaka", "tempozan": "osaka",
    "osaka_castle_park": "osaka", "abeno_tennoji": "osaka", "tennoji": "osaka",
    "shinsekai": "osaka", "sumiyoshi": "osaka", "suita_expo": "osaka",
    "osaka_nagai": "osaka", "osaka_bay": "osaka", "osaka_central": "osaka",
    "osaka_west": "osaka", "osakajo": "osaka", "osaka_ikeda": "osaka",
    "nara_ikoma": "osaka",
    # 奈良
    "nara_park": "nara", "nara_yoshino": "nara",
    # 神户
    "kobe_rokko": "kobe", "kobe_kita": "kobe", "kobe_kitano": "kobe",
    "kobe_waterfront": "kobe", "kobe_central": "kobe",
    # 有马
    "arima": "arima",
    # 姬路
    "himeji": "himeji",
    # 高野山
    "koyasan": "koyasan",
    # 城崎
    "kinosaki": "kinosaki",
    # 熊野
    "kumano": "kumano", "kumano_hongu": "kumano",
    # 天桥立/伊根
    "amanohashidate": "amanohashidate", "ine": "amanohashidate",
    # 滋贺
    "shiga": "other",
}

# ── depth 判断 ────────────────────────────────────────────────────────────────

def determine_depth(entity: dict) -> str:
    """full / verified / skeleton"""
    notes = entity.get("notes", "")
    has_notes_headers = isinstance(notes, str) and "## " in notes
    has_short_desc = bool(entity.get("short_desc"))

    if has_notes_headers:
        return "full"
    elif has_short_desc:
        return "verified"
    else:
        return "skeleton"

# ── notes 段落解析 ────────────────────────────────────────────────────────────

def parse_notes_sections(notes_text: str) -> dict:
    """
    把 markdown notes 按 ## 子标题拆解为 {标题: 内容} 字典。
    """
    if not notes_text or not isinstance(notes_text, str):
        return {}

    sections = {}
    current_heading = None
    current_lines = []

    for line in notes_text.split("\n"):
        m = re.match(r"^##\s+(.+)$", line)
        if m:
            if current_heading is not None:
                sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = m.group(1).strip()
            current_lines = []
        else:
            if current_heading is not None:
                current_lines.append(line)

    if current_heading is not None:
        sections[current_heading] = "\n".join(current_lines).strip()

    return sections

# ── admission → 自然语言 ───────────────────────────────────────────────────────

def admission_to_text(admission, entity_id: str = "") -> str:
    """
    把 admission 对象转为自然语言文本。
    """
    if admission is None:
        return "免费"

    if isinstance(admission, str):
        return admission

    if not isinstance(admission, dict):
        return str(admission)

    # 优先用 _note
    if admission.get("_note"):
        return admission["_note"]

    # 按 adult 字段
    adult = admission.get("adult")
    if adult is not None:
        if adult == 0:
            base = "免费"
        else:
            base = f"¥{adult}"
    else:
        # 有其他收费字段
        parts = []
        for key in ["adult_regular", "adult"]:
            val = admission.get(key)
            if val is not None:
                parts.append(f"成人 ¥{val}")
                break
        base = "；".join(parts) if parts else "免费"

    # 追加儿童价
    child_keys = [
        ("child", "儿童"),
        ("child_elementary", "小学生"),
        ("child_7_15", "儿童（7–15岁）"),
        ("child_small_school", "小学生"),
        ("child_preschool", "学龄前"),
        ("toddler", "幼儿"),
        ("toddler_3_6", "幼儿（3–6岁）"),
        ("toddler_4_5", "幼儿（4–5岁）"),
    ]
    child_parts = []
    for ckey, clabel in child_keys:
        val = admission.get(ckey)
        if val is not None:
            if val == 0:
                child_parts.append(f"{clabel}免费")
            elif str(val) != "未核实":
                child_parts.append(f"{clabel} ¥{val}")

    if child_parts:
        base = base + "；" + "；".join(child_parts)

    return base

# ── opening_hours → 自然语言 ──────────────────────────────────────────────────

SKIP_CLOSED = {"全年无休", "无休", "无定休", "全年无定休", "年中無休"}

def opening_hours_to_text(opening_hours, is_public_path: bool = False, closed_days: str = None) -> str:
    """
    把 opening_hours 对象转为自然语言。
    closed_days 用于 arm_ 系列特殊字段合并。
    """
    if is_public_path and not opening_hours:
        return "24h"

    if not opening_hours:
        if closed_days:
            return f"休：{closed_days}"
        return ""

    if isinstance(opening_hours, str):
        text = opening_hours
        if closed_days and closed_days not in text:
            text += f"，休：{closed_days}"
        return text

    if not isinstance(opening_hours, dict):
        return str(opening_hours)

    parts = []

    regular = opening_hours.get("regular", "")
    if regular:
        parts.append(regular)

    closed = opening_hours.get("closed") or closed_days
    if closed:
        # 过滤全年无休
        skip = any(s in str(closed) for s in SKIP_CLOSED)
        if not skip:
            parts.append(f"休：{closed}")

    last_entry = opening_hours.get("last_entry", "")
    if last_entry:
        parts.append(f"最终入场：{last_entry}")

    return "，".join(parts) if parts else ""

# ── templates_meta 提取 ───────────────────────────────────────────────────────

# notes 子标题 → templates_meta key 映射
SECTION_TO_META = {
    "拍照位置": "拍照位置",
    "冷知识": "冷知识",
    "顺路小店": "顺路小店",
    "衔接": "衔接",
    "避坑": "避坑",
    "季节": "季节看点",
    "特征": "亮点",
    "つぼ湯": "冷知识",   # 有马汤之峰温泉特殊
}

# 需要并入 note.票价 的段落
TICKET_SECTION = "票价指引"

# 需要并入 note.简介末段 的段落
DESC_APPEND_SECTIONS = {"当年临时", "排队"}

def extract_templates_meta(sections: dict) -> tuple:
    """
    返回 (templates_meta_dict, 需追加到简介末段的文本, 需追加到票价的文本)
    """
    meta = {}
    desc_appends = []
    ticket_appends = []

    for heading, content in sections.items():
        if not content:
            continue

        if heading in SECTION_TO_META:
            meta_key = SECTION_TO_META[heading]
            if meta_key in meta:
                meta[meta_key] = meta[meta_key] + "\n" + content
            else:
                meta[meta_key] = content

        elif heading == TICKET_SECTION:
            ticket_appends.append(content)

        elif heading in DESC_APPEND_SECTIONS:
            # 排队段落只保留重要提示（须预约等），其余略去
            if heading == "排队":
                # 只追加包含关键词的行
                key_lines = []
                for line in content.split("\n"):
                    if any(kw in line for kw in ["须提前", "需提前", "预约", "须购", "须排"]):
                        key_lines.append(line.strip("- ").strip())
                if key_lines:
                    desc_appends.append("；".join(key_lines))
            else:
                desc_appends.append(content)

    return meta, "；".join(desc_appends), "；".join(ticket_appends)

# ── seasonal_notes → 自然语言 ─────────────────────────────────────────────────

SEASON_LABEL = {"spring": "春", "summer": "夏", "autumn": "秋", "winter": "冬"}

def seasonal_notes_to_text(seasonal_notes) -> str:
    if not seasonal_notes or not isinstance(seasonal_notes, dict):
        return ""
    parts = []
    for season_key in ["spring", "summer", "autumn", "winter"]:
        val = seasonal_notes.get(season_key, "")
        if val:
            label = SEASON_LABEL.get(season_key, season_key)
            parts.append(f"【{label}】{val}")
    return "\n".join(parts)

# ── 单个 entity 转换 ──────────────────────────────────────────────────────────

def convert_entity(entity: dict, unknown_areas: set, warnings: list) -> dict:
    eid = entity.get("entity_id", "")

    # city 推断
    area = entity.get("area", "")
    city = CITY_MAP.get(area)
    if city is None and area:
        unknown_areas.add(area)
        city = "unknown"

    # depth
    depth = determine_depth(entity)

    # 店名合并
    name_zh = entity.get("name_zh", "")
    name_ja = entity.get("name_ja", "")
    name_en = entity.get("name_en", "")
    parts = [name_zh] if name_zh else []
    if name_ja and name_ja != name_zh:
        parts.append(name_ja)
    if name_en and name_en != name_zh:
        parts.append(name_en)
    shop_name = "（".join(parts[:1]) + ("（" + " / ".join(parts[1:]) + "）" if len(parts) > 1 else "")

    # 简介基础（short_desc）
    short_desc = entity.get("short_desc", "")

    # UNESCO 写进简介
    if entity.get("unesco"):
        if "UNESCO" not in short_desc:
            short_desc = short_desc.rstrip("。") + "。UNESCO世界文化遗产。" if short_desc else "UNESCO世界文化遗产。"

    # notes 段落解析
    notes_raw = entity.get("notes", "")
    sections = parse_notes_sections(notes_raw)

    # 提取 templates_meta
    templates_meta, desc_extra, ticket_extra = extract_templates_meta(sections)

    # seasonal_notes → templates_meta.季节看点（追加）
    sn_text = seasonal_notes_to_text(entity.get("seasonal_notes"))
    if sn_text:
        if "季节看点" in templates_meta:
            templates_meta["季节看点"] = templates_meta["季节看点"] + "\n" + sn_text
        else:
            templates_meta["季节看点"] = sn_text

    # photo 限制追加到简介
    desc_appends_photo = []
    if entity.get("photo_ok") is False:
        desc_appends_photo.append("禁止拍照")
    if entity.get("tripod_allowed") is False:
        # 仅当景点有拍照位置内容，才追加禁三脚架
        if "拍照位置" in templates_meta or entity.get("category") in (
            "natural_path", "garden", "temple", "shrine", "palace", "tower", "park"
        ):
            desc_appends_photo.append("禁三脚架")

    # reservation 追加
    if entity.get("reservation_required"):
        desc_appends_photo.append("需预约")
    reservation_note = entity.get("reservation_note", "")
    if reservation_note:
        desc_appends_photo.append(reservation_note)

    # 组装简介
    full_desc_parts = [short_desc] if short_desc else []
    if desc_extra:
        full_desc_parts.append(desc_extra)
    if desc_appends_photo:
        full_desc_parts.append("；".join(desc_appends_photo))
    full_desc = "；".join(filter(None, full_desc_parts)).strip()

    # 票价
    ticket_text = admission_to_text(entity.get("admission"), eid)
    # 特殊：kns_kinosaki external_baths 并入票价
    if "external_baths" in entity:
        eb = entity["external_baths"]
        if isinstance(eb, dict):
            note_str = eb.get("_note", "")
            if note_str:
                ticket_text = (ticket_text + "；" + note_str).lstrip("；")
            else:
                day_pass = eb.get("day_pass")
                single = eb.get("single_bath")
                if day_pass:
                    ticket_text = (ticket_text + f"；外汤一日券 ¥{day_pass}").lstrip("；")
                if single:
                    ticket_text += f"；单座约 ¥{single}"
    # 追加 ticket_extra（来自 ## 票价指引）
    if ticket_extra:
        ticket_text = (ticket_text + "；" + ticket_extra).lstrip("；")

    # 营业
    is_public = entity.get("is_public_path", False)
    closed_days = entity.get("closed_days")  # arm_ 特殊字段
    oh = entity.get("opening_hours")
    oh_note = entity.get("opening_hours_note")  # osk_kuromon 特殊字段

    # opening_hours_note 优先级高于 is_public_path 的"24h"默认值
    if oh_note and not oh:
        hours_text = oh_note
    elif oh or is_public or closed_days:
        hours_text = opening_hours_to_text(oh, is_public, closed_days)
    else:
        hours_text = ""

    # 怎么去
    access_text = entity.get("access", "")

    # ── 组装 note ─────────────────────────────────────────────────────────────
    note = {}
    note["店名"] = shop_name if shop_name else eid
    note["简介"] = full_desc
    if ticket_text:
        note["票价"] = ticket_text
    if hours_text:
        note["营业"] = hours_text
    if access_text:
        note["怎么去"] = access_text

    # ── 可信度 / 数据来源 / 最后核实 ──────────────────────────────────────────
    confidence = entity.get("data_confidence", "")
    sources = entity.get("data_sources", [])
    last_verified = entity.get("last_verified", "")

    # ── season_months（选填，来自原数据，若存在则保留）────────────────────────
    season_months = entity.get("season_months")

    # ── 组装新 entity ─────────────────────────────────────────────────────────
    new_entity = {}
    new_entity["entity_id"] = eid
    new_entity["city"] = city or "unknown"
    new_entity["area"] = area
    new_entity["category"] = entity.get("category", "")
    new_entity["depth"] = depth
    if season_months:
        new_entity["season_months"] = season_months

    new_entity["note"] = note

    if templates_meta:
        new_entity["templates_meta"] = templates_meta

    if confidence:
        new_entity["可信度"] = confidence
    if sources:
        new_entity["数据来源"] = sources
    if last_verified:
        new_entity["最后核实"] = last_verified

    return new_entity

# ── 处理单个文件 ──────────────────────────────────────────────────────────────

def process_file(file_path: Path, unknown_areas: set, warnings: list) -> int:
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    new_data = {}
    count = 0

    for key, value in data.items():
        if key.startswith("_"):
            # 保留 _meta 等元数据原样
            new_data[key] = value
            continue

        if not isinstance(value, dict):
            new_data[key] = value
            continue

        try:
            new_entity = convert_entity(value, unknown_areas, warnings)
            new_data[key] = new_entity
            count += 1
        except Exception as e:
            warnings.append(f"[{file_path.name}] {key} 转换异常：{e}")
            new_data[key] = value  # 保留原始以防丢数据

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)

    return count

# ── 主入口 ────────────────────────────────────────────────────────────────────

def main():
    base = Path("japan/kansai/entities")
    files = ["kyoto.json", "osaka.json", "other.json"]

    unknown_areas: set = set()
    warnings: list = []

    print("=== D43 Entity 格式转换 ===\n")

    for fname in files:
        fpath = base / fname
        if not fpath.exists():
            print(f"[跳过] {fpath} 不存在")
            continue
        count = process_file(fpath, unknown_areas, warnings)
        print(f"[完成] {fname}: {count} 个 entity 已转换")

    print()
    if unknown_areas:
        print(f"[未知 area，需手动补 CITY_MAP]:")
        for a in sorted(unknown_areas):
            print(f"  - {a}")
    else:
        print("[city 推断] 所有 area 均已识别，无缺口")

    print()
    if warnings:
        print(f"[异常/警告] {len(warnings)} 条:")
        for w in warnings:
            print(f"  {w}")
    else:
        print("[异常/警告] 无")

if __name__ == "__main__":
    # 允许从项目根目录运行
    import os
    os.chdir(Path(__file__).parent.parent)
    main()
