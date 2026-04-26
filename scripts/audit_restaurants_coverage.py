#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_restaurants_coverage.py
扫 japan/kansai/restaurants/ + stops/ 所有 JSON，
按区域类型对照"餐位需求分级"目标算缺口。
输出 japan/kansai/restaurants/audit_report.md
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
RESTAURANTS_DIR = ROOT / "japan/kansai/restaurants"
STOPS_DIR = ROOT / "japan/kansai/stops"
ASSEMBLY_DIR = ROOT / "japan/kansai/assembly/restaurants/data"
REPORT_OUT = ROOT / "japan/kansai/restaurants/audit_report.md"
AREA_REGISTRY_PATH = ROOT / "japan/kansai/area_registry.json"

# 从 area_registry.json 读取：{area: type}
_registry_raw = json.loads(AREA_REGISTRY_PATH.read_text(encoding="utf-8"))
AREA_TYPE_MAP: dict = {r["area"]: r["type"] for r in _registry_raw}

# 目标（full 池数量）
TARGETS = {
    "主场密集": {"showcase": None, "high": (4, 6), "mid": (8, 12), "economy": (4, 6)},
    "日归动线": {"showcase": None, "high": (1, 2), "mid": (3, 4), "economy": (2, 3)},
    "温泉宿坊": {"showcase": None, "high": (0, 0), "mid": (1, 2), "economy": (1, 1)},
    "景点单日": {"showcase": None, "high": (0, 0), "mid": (2, 2), "economy": (2, 2)},
}

def area_to_type(area_name):
    return AREA_TYPE_MAP.get(area_name, "未分类")


def load_json_list(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        print(f"  [WARN] 读取失败 {path}: {e}", file=sys.stderr)
        return []


def walk_score(entry):
    """随到随吃评分：must=0, queue_level=high=0.5, 其他=1"""
    res_diff = entry.get("reservation_difficulty", "none")
    queue = entry.get("queue_level", "mild")
    if res_diff == "must":
        return 0.0
    if queue == "high":
        return 0.5
    return 1.0


def collect_restaurants():
    """返回 {area: [entry, ...]}"""
    area_map = defaultdict(list)
    for json_file in sorted(RESTAURANTS_DIR.rglob("*.json")):
        entries = load_json_list(json_file)
        for e in entries:
            area = e.get("area", "未知")
            e["_source_file"] = str(json_file.relative_to(ROOT))
            area_map[area].append(e)
    return area_map


def collect_stops():
    """返回 {area: [entry, ...]}"""
    area_map = defaultdict(list)
    for json_file in sorted(STOPS_DIR.rglob("*.json")):
        entries = load_json_list(json_file)
        for e in entries:
            area = e.get("area", "未知")
            e["_source_file"] = str(json_file.relative_to(ROOT))
            area_map[area].append(e)
    return area_map


def count_assembly_candidates(area_name):
    """在 assembly 候选池里 grep 同 area（宽松匹配）"""
    counts = {}
    area_lower = area_name.lower()
    # 简单映射：用 area 字段匹配（assembly 用英文 area tag）
    # 同时做子串宽松匹配
    area_aliases = {
        "东山轴": ["gion", "higashiyama", "東山"],
        "河原町-先斗町": ["kawaramachi", "pontocho", "先斗町"],
        "烏丸御池": ["karasuma", "烏丸"],
        "京都站": ["kyoto_sta", "station", "京都駅"],
        "岚山": ["arashiyama", "嵐山"],
        "北区": ["kita", "kitaku"],
        "伏见": ["fushimi", "伏見"],
        "梅田": ["umeda"],
        "难波": ["namba", "难波"],
        "心斋桥": ["shinsaibashi"],
        "道顿堀": ["dotonbori", "道頓堀"],
        "天王寺-新世界": ["tennoji", "shinsekai"],
        "天满": ["tenjinbashisuji", "tenma"],
        "三宮-旧居留地": ["sannomiya", "kobe"],
        "北野-元町": ["kitano", "motomachi"],
        "奈良公园": ["nara"],
        "ならまち": ["naramachi"],
        "有马温泉": ["arima"],
        "城崎温泉": ["kinosaki"],
        "高野山": ["koyasan", "koya"],
        "吉野山": ["yoshino"],
    }
    keywords = area_aliases.get(area_name, [area_lower])

    for json_file in sorted(ASSEMBLY_DIR.glob("restaurants__*.json")):
        entries = load_json_list(json_file)
        matched = []
        for e in entries:
            e_area = str(e.get("area", "")).lower()
            if any(kw.lower() in e_area for kw in keywords):
                matched.append(e)
        if matched:
            counts[json_file.name] = len(matched)
    total = sum(counts.values())
    return total, counts


def build_matrix(entries):
    """
    返回：
      tier_counts: {tier: count_full}
      cuisine_set: {tier: set(cuisines)}
      meal_set: {tier: set(meals)}
      walk_score_by_tier: {tier: float}
      res_diff_counts: {tier: {diff: count}}
    """
    tier_counts = defaultdict(int)
    cuisine_set = defaultdict(set)
    meal_set = defaultdict(set)
    walk_scores = defaultdict(float)
    res_diff_counts = defaultdict(lambda: defaultdict(int))

    for e in entries:
        depth = e.get("depth", "skeleton")
        if depth != "full":
            continue
        tier = e.get("tier", "?")
        tier_counts[tier] += 1
        for c in e.get("cuisine", []):
            cuisine_set[tier].add(c)
        for rm in e.get("recommended_meals", []):
            meal_set[tier].add(rm.get("meal", "?"))
        walk_scores[tier] += walk_score(e)
        rd = e.get("reservation_difficulty", "none")
        res_diff_counts[tier][rd] += 1

    return tier_counts, cuisine_set, meal_set, walk_scores, res_diff_counts


def gap_line(tier, actual, target_range, walk_actual):
    if target_range is None:
        return None  # showcase 不做强目标
    lo, hi = target_range
    status = "✅" if actual >= lo else ("⚠️" if actual >= max(lo - 1, 0) else "❌")
    walk_str = f"{walk_actual:.1f}" if walk_actual else "0"
    return f"{status} {tier}: full={actual} (目标 {lo}~{hi})，随到随吃={walk_str}"


def render_area_section(area, atype, entries, stops_entries):
    lines = []
    lines.append(f"\n### {area}（{atype}）\n")

    tier_counts, cuisine_set, meal_set, walk_scores, res_diff_counts = build_matrix(entries)
    all_tiers = ["showcase", "high", "mid", "economy"]
    target = TARGETS.get(atype, {})

    # 矩阵
    lines.append("**正餐 full 矩阵**\n")
    lines.append("| tier | full数 | 菜系 | 用餐时段 | reservation_difficulty | 随到随吃加权 |")
    lines.append("|---|---|---|---|---|---|")
    for tier in all_tiers:
        cnt = tier_counts.get(tier, 0)
        cuisines = "、".join(sorted(cuisine_set.get(tier, []))) or "—"
        meals = "、".join(sorted(meal_set.get(tier, []))) or "—"
        rd_str = " ".join(f"{k}×{v}" for k, v in sorted(res_diff_counts.get(tier, {}).items())) or "—"
        ws = walk_scores.get(tier, 0.0)
        lines.append(f"| {tier} | {cnt} | {cuisines} | {meals} | {rd_str} | {ws:.1f} |")

    # stops 汇总
    stop_types = defaultdict(int)
    stop_full = 0
    for s in stops_entries:
        st = s.get("type", "?")
        stop_types[st] += 1
        if s.get("depth") == "full":
            stop_full += 1
    total_stops = len(stops_entries)
    if total_stops:
        types_str = "、".join(f"{t}×{c}" for t, c in sorted(stop_types.items()))
        lines.append(f"\n**停留池**：共 {total_stops} 条（full {stop_full}），类型：{types_str}\n")
    else:
        lines.append(f"\n**停留池**：0 条\n")

    # 缺口
    lines.append("**缺口分析**\n")
    for tier in ["high", "mid", "economy"]:
        trange = target.get(tier)
        actual = tier_counts.get(tier, 0)
        ws = walk_scores.get(tier, 0.0)
        g = gap_line(tier, actual, trange, ws)
        if g:
            lines.append(f"- {g}")

    # 候选池
    total_cand, cand_detail = count_assembly_candidates(area)
    cand_str = "、".join(f"{f}({c}条)" for f, c in sorted(cand_detail.items())) if cand_detail else "无匹配"
    lines.append(f"\n**assembly 候选池**：{total_cand} 条（{cand_str}）\n")

    return "\n".join(lines)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    print("扫描 restaurants/ + stops/...", file=sys.stderr)
    rest_map = collect_restaurants()
    stop_map = collect_stops()

    all_areas = set(rest_map.keys()) | set(stop_map.keys())
    # 按区域类型分组
    groups = {t: [] for t in ["主场密集", "日归动线", "温泉宿坊", "景点单日", "未分类"]}
    for area in sorted(all_areas):
        atype = area_to_type(area)
        groups[atype].append(area)

    lines = []
    lines.append("# 关西餐厅覆盖审计报告\n")
    lines.append(f"> 自动生成，勿手改。脚本：`scripts/audit_restaurants_coverage.py`\n")

    group_order = ["主场密集", "日归动线", "温泉宿坊", "景点单日", "未分类"]
    for gname in group_order:
        areas = sorted(groups.get(gname, []))
        if not areas:
            continue
        lines.append(f"\n## {gname}区\n")
        for area in areas:
            entries = rest_map.get(area, [])
            stops_entries = stop_map.get(area, [])
            section = render_area_section(area, gname, entries, stops_entries)
            lines.append(section)

    report = "\n".join(lines)
    REPORT_OUT.write_text(report, encoding="utf-8")
    print(f"报告已写入：{REPORT_OUT}", file=sys.stderr)
    print(report)


if __name__ == "__main__":
    main()
