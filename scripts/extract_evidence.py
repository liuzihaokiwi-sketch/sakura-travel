#!/usr/bin/env python
"""
Phase 2B: extract_evidence.py
规则化生成 quality_evidence（不调 AI，不做爬取）。
traveler_fit / execution 字段留 null，等真实爬取后回填。
同时修正 data_confidence。

输入:
  data/kansai_spots/phase2_ledger/*_ledger_phase2a.json

输出:
  data/kansai_spots/phase2_ledger/*_ledger_phase2b.json

运行:
  python scripts/extract_evidence.py
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = Path("data/kansai_spots/phase2_ledger")


def pct_label(pct: float) -> str:
    """percentile (0-1, 越高=排名越前) → 中文描述。
    pct=0.84 意味着超过了84%的组内竞品 → "前16%"。
    """
    rank = round((1 - pct) * 100)  # 转为"前X%"
    if rank <= 5:
        return "前5%"
    if rank <= 10:
        return "前10%"
    if rank <= 20:
        return "前20%"
    if rank <= 33:
        return "前1/3"
    if rank <= 50:
        return "前半段"
    return f"后{rank}%"


def city_cn(city_code: str) -> str:
    MAP = {
        "kyoto": "京都", "osaka": "大阪", "kobe": "神户", "nara": "奈良",
        "himeji": "姬路", "uji": "宇治", "otsu": "大津", "arima": "有马",
        "kinosaki": "城崎", "koyasan": "高野山", "ise": "伊势",
        "ise_shima": "伊势志摩", "akashi": "明石", "wakayama": "和歌山",
        "shirahama": "白滨",
    }
    return MAP.get(city_code, city_code)


def cuisine_cn(cuisine_normalized: str) -> str:
    MAP = {
        "nihon_ryori": "日本料理", "kaiseki": "怀石", "sushi": "寿司",
        "unagi": "鳗鱼", "tempura": "天妇罗", "tonkatsu": "炸猪排",
        "kushiage": "串炸", "yakitori": "烤鸡串", "yakiniku": "烧肉",
        "teppanyaki": "铁板烧", "wagyu": "和牛", "shabu_sukiyaki": "涮锅",
        "kani": "螃蟹", "fugu": "河豚", "soba": "荞麦面", "udon": "乌冬面",
        "ramen": "拉面", "okonomiyaki": "大阪烧", "takoyaki": "章鱼烧",
        "donburi": "丼饭", "tofu": "豆腐", "kamameshi": "釜饭",
        "obanzai": "おばんざい", "seafood": "海鲜", "akashiyaki": "明石焼",
        "yoshoku": "日式洋食", "izakaya": "居酒屋", "cafe": "咖啡",
        "matcha_sweets": "抹茶甜品", "wagashi": "和果子", "sweets": "甜品",
        "bakery": "面包", "street_food": "小吃", "french": "法餐",
        "italian": "意餐", "curry": "咖喱", "western": "西餐",
        "chinese": "中华料理", "local_cuisine": "当地特色", "other": "其他",
    }
    return MAP.get(cuisine_normalized, cuisine_normalized)


# ── 计算组内 tabelog percentile（用于 evidence 描述）────────────────────────────

def build_tabelog_percentiles(entries: list) -> dict:
    """name_ja|city_code → percentile (0-1)"""
    from collections import defaultdict
    groups: dict = defaultdict(list)
    for e in entries:
        if e.get("tabelog_score"):
            key = (e["city_code"], e.get("cuisine_normalized", ""), e.get("budget_tier", ""))
            groups[key].append(float(e["tabelog_score"]))

    result = {}
    for e in entries:
        tab = e.get("tabelog_score")
        if not tab:
            continue
        key = (e["city_code"], e.get("cuisine_normalized", ""), e.get("budget_tier", ""))
        vals = sorted(groups[key])
        pos = sum(1 for v in vals if v < float(tab))
        pct = pos / len(vals) if vals else 0.5
        result[e["name_ja"] + "|" + e["city_code"]] = pct
    return result


# ── 餐厅 quality_evidence ──────────────────────────────────────────────────────

def restaurant_quality_evidence(entry: dict, tab_pct: dict) -> str:
    city = city_cn(entry["city_code"])
    cuisine = cuisine_cn(entry.get("cuisine_normalized", ""))
    budget = entry.get("budget_tier", "")
    tab = entry.get("tabelog_score")
    mich = entry.get("michelin")

    parts = []
    if tab:
        pct = tab_pct.get(entry["name_ja"] + "|" + entry["city_code"])
        pct_str = f"，{city}×{cuisine}类组内{pct_label(pct)}" if pct is not None else ""
        parts.append(f"Tabelog {tab}{pct_str}")
    if mich:
        parts.append(str(mich))
    if not parts:
        src = entry.get("source", "")
        parts.append(f"来源: {src}，{budget}层候选" if src else f"{budget}层候选")

    return "，".join(parts)


# ── 酒店 quality_evidence ──────────────────────────────────────────────────────

def hotel_quality_evidence(entry: dict) -> str:
    mk = entry.get("michelin_keys")
    ota = entry.get("ota_rating")
    forbes = entry.get("raw_forbes_stars") or entry.get("forbes_stars")

    if mk and str(mk) not in ("", "0", "None"):
        return f"MICHELIN {mk} Keys"
    if ota and str(ota) not in ("", "0", "None"):
        ota_str = f"OTA ★{ota}"
        src = entry.get("source", "")
        return f"{ota_str}（{src}）" if src else ota_str
    if forbes and str(forbes) not in ("", "0", "None"):
        return f"Forbes {forbes} Stars"
    pl = entry.get("price_level", "")
    ht = entry.get("hotel_type", "")
    return f"{city_cn(entry['city_code'])} {ht} {pl}层候选"


# ── 景点 quality_evidence ──────────────────────────────────────────────────────

def spot_quality_evidence(entry: dict) -> str:
    level = entry.get("japan_guide_level", "")
    sub = entry.get("sub_type", "")
    level_cn = {"top": "强烈推荐", "recommended": "推荐", "featured": "特色介绍"}.get(level, level)
    return f"japan-guide {level_cn}，{sub}类"


# ── data_confidence 判定 ───────────────────────────────────────────────────────

def judge_data_confidence(entry: dict, category: str) -> str:
    if category == "restaurants":
        has_quality = bool(entry.get("tabelog_score") or entry.get("michelin"))
        has_traveler = bool(entry.get("traveler_fit_evidence"))
        has_execution = bool(entry.get("execution_evidence"))
    elif category == "hotels":
        has_quality = bool(entry.get("michelin_keys") or entry.get("ota_rating"))
        has_traveler = bool(entry.get("traveler_fit_evidence"))
        has_execution = bool(entry.get("execution_evidence"))
    else:  # spots
        has_quality = bool(entry.get("japan_guide_level"))
        has_traveler = bool(entry.get("traveler_fit_evidence"))
        has_execution = bool(entry.get("execution_evidence"))

    axis_count = sum([has_quality, has_traveler, has_execution])
    if axis_count >= 3:
        return "verified"
    if axis_count >= 2:
        return "cross_checked"
    if axis_count == 1:
        return "single_source"
    return "ai_generated"


# ── 主处理函数 ─────────────────────────────────────────────────────────────────

def process_restaurants():
    in_path = DATA_DIR / "restaurants_ledger_phase2a.json"
    out_path = DATA_DIR / "restaurants_ledger_phase2b.json"

    with open(in_path, encoding="utf-8") as f:
        entries = json.load(f)

    tab_pct = build_tabelog_percentiles(entries)
    updated = 0

    for e in entries:
        if e["selection_status"] not in ("selected", "borderline"):
            continue
        e["quality_evidence"] = restaurant_quality_evidence(e, tab_pct)
        e["data_confidence"] = judge_data_confidence(e, "restaurants")
        updated += 1

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    print(f"  [ok] restaurants: {updated} entries evidence extracted -> {out_path}")
    return entries


def process_hotels():
    in_path = DATA_DIR / "hotels_ledger_phase2a.json"
    out_path = DATA_DIR / "hotels_ledger_phase2b.json"

    with open(in_path, encoding="utf-8") as f:
        entries = json.load(f)

    updated = 0
    for e in entries:
        if e["selection_status"] not in ("selected", "borderline"):
            continue
        e["quality_evidence"] = hotel_quality_evidence(e)
        e["data_confidence"] = judge_data_confidence(e, "hotels")
        updated += 1

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    print(f"  [ok] hotels: {updated} entries evidence extracted -> {out_path}")
    return entries


def process_spots():
    in_path = DATA_DIR / "spots_ledger_phase2a.json"
    out_path = DATA_DIR / "spots_ledger_phase2b.json"

    with open(in_path, encoding="utf-8") as f:
        entries = json.load(f)

    updated = 0
    for e in entries:
        if e["selection_status"] not in ("selected", "borderline"):
            continue
        e["quality_evidence"] = spot_quality_evidence(e)
        e["data_confidence"] = judge_data_confidence(e, "spots")
        updated += 1

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    print(f"  [ok] spots: {updated} entries evidence extracted -> {out_path}")
    return entries


if __name__ == "__main__":
    print("Phase 2B: extract_evidence")
    print("=" * 60)
    process_restaurants()
    process_hotels()
    process_spots()
    print("\nDone. quality_evidence filled. traveler_fit/execution still null (pending real scraping).")
