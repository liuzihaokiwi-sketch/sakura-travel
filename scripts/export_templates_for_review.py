"""
把所有日模板导出为三个 Markdown 文档供 GPT review：
- docs/review/templates_osaka.md
- docs/review/templates_kyoto.md
- docs/review/templates_other.md

每个模板格式：保留 Opus 需要的完整信息（description + slots + notes），
去掉纯系统字段（template_id 保留，assembly/condition/fit_audience 保留）
"""

import json
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent
CONTENT_DIR = ROOT / "content" / "kansai"
OUT_DIR = ROOT / "docs" / "review"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 城市分组
OSAKA_CITIES = ["osaka"]
KYOTO_CITIES = ["kyoto"]
OTHER_CITIES = ["nara", "uji", "kobe", "kinosaki", "koyasan"]

def load_templates(cities):
    templates = []
    for city in cities:
        days_dir = CONTENT_DIR / city / "days"
        if not days_dir.exists():
            continue
        for f in sorted(days_dir.glob("*.json")):
            if f.name.startswith("_"):
                continue
            with open(f, encoding="utf-8") as fp:
                data = json.load(fp)
            data["_city"] = city
            templates.append(data)
    return templates

def format_slot(slot):
    lines = []
    time = slot.get("time_range", "")
    slot_type = slot.get("type", "")
    area = slot.get("area", "")
    priority = slot.get("priority", "")
    duration = slot.get("duration_min", "")
    entity = slot.get("entity_hint", "")

    header_parts = [f"**[{time}]**" if time else ""]
    if priority:
        header_parts.append(f"`{priority}`")
    if slot_type:
        header_parts.append(slot_type)
    if entity:
        header_parts.append(f"— {entity}")
    if area:
        header_parts.append(f"| {area}")
    if duration:
        header_parts.append(f"| {duration}min")

    lines.append(" ".join(p for p in header_parts if p))
    note = slot.get("note", "")
    if note:
        lines.append(f"> {note}")
    return "\n".join(lines)

def format_template(t):
    tid = t.get("template_id", "")
    label = t.get("label", "")
    tags = t.get("tags", [])
    core = t.get("core_entities", [])
    fit = t.get("fit_audience", "all")
    weather = t.get("weather_sensitive", False)
    condition = t.get("condition", "")
    assembly = t.get("assembly", {})
    description = t.get("description", "")
    hotel_note = t.get("hotel_area_note", "")
    slots = t.get("slots") or []
    days = t.get("days")  # 两日模板

    lines = []
    lines.append(f"## {label}")
    lines.append(f"`{tid}`")
    lines.append("")

    meta_parts = []
    if tags:
        meta_parts.append(f"标签: {' / '.join(tags)}")
    if isinstance(fit, list):
        meta_parts.append(f"人群: {' / '.join(fit)}")
    elif fit != "all":
        meta_parts.append(f"人群: {fit}")
    if weather:
        meta_parts.append("⚠️ 天气敏感")
    if condition:
        meta_parts.append(f"触发条件: `{condition}`")
    phase = assembly.get("phase", "")
    pace = assembly.get("best_pace", "")
    if phase or pace:
        meta_parts.append(f"节奏: {phase} / {pace}")
    if core:
        meta_parts.append(f"核心实体: {' / '.join(core)}")

    if meta_parts:
        lines.append("  \n".join(meta_parts))
        lines.append("")

    if description:
        lines.append(f"**概述:** {description}")
        lines.append("")

    if hotel_note:
        lines.append(f"**交通/住宿:** {hotel_note}")
        lines.append("")

    if days:
        for i, day_slots in enumerate(days, 1):
            lines.append(f"### 第{i}天")
            for slot in day_slots:
                lines.append(format_slot(slot))
                lines.append("")
    elif slots:
        lines.append("### 行程")
        for slot in slots:
            lines.append(format_slot(slot))
            lines.append("")

    lines.append("---")
    lines.append("")
    return "\n".join(lines)

def write_doc(filepath, city_label, templates):
    count = len(templates)
    lines = [
        f"# 模板库 — {city_label}（{count} 个）",
        "",
        f"> 供 GPT review 用。共 {count} 个模板，包含完整描述和 slot note。",
        "",
        "---",
        "",
    ]
    for t in templates:
        lines.append(format_template(t))

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"写入 {filepath}（{count} 个模板）")

osaka = load_templates(OSAKA_CITIES)
kyoto = load_templates(KYOTO_CITIES)
other = load_templates(OTHER_CITIES)

write_doc(OUT_DIR / "templates_osaka.md", "大阪", osaka)
write_doc(OUT_DIR / "templates_kyoto.md", "京都", kyoto)
write_doc(OUT_DIR / "templates_other.md", "其他城市（奈良/宇治/神户/城崎/高野山）", other)

print(f"\n总计: 大阪 {len(osaka)} / 京都 {len(kyoto)} / 其他 {len(other)} = {len(osaka)+len(kyoto)+len(other)} 个")
