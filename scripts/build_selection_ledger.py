#!/usr/bin/env python
"""
Phase 2A: build_selection_ledger.py
- 计算 base_quality_score（组内 percentile）
- 计算 indie_support_score
- Slot 分组 + city-relative percentile + same-slot cap 3
- 标记候选状态: selected / borderline / excluded / needs_editorial

输出:
  data/kansai_spots/restaurants_ledger_phase2a.json
  data/kansai_spots/hotels_ledger_phase2a.json
  data/kansai_spots/spots_ledger_phase2a.json
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = Path("data/kansai_spots/phase2_ledger")


# ── 工具函数 ──────────────────────────────────────────────────────────────────

def percentile_rank(value, values):
    """value 在 values 中的 percentile rank (0.0~1.0)。values 必须非空。"""
    sorted_vals = sorted(v for v in values if v is not None)
    if not sorted_vals:
        return 0.5
    pos = sum(1 for v in sorted_vals if v < value)
    return pos / len(sorted_vals)


def map_percentile_to_score(pct):
    """percentile 0-1 → base_quality_score 2.5-5.0"""
    return 2.5 + pct * 2.5


def michelin_bonus(michelin_raw):
    """返回 Michelin 加分（已在 percentile 基础上叠加）"""
    if not michelin_raw:
        return 0.0
    s = str(michelin_raw).lower()
    if "3" in s or "三" in s:
        return 0.75
    if "2" in s or "二" in s:
        return 0.5
    if "bib" in s:
        return 0.2
    return 0.25  # 1 star


def indie_support(source, mention_count_raw):
    """计算 indie_support_score。来源越多，mention 越多越高。"""
    score = 0.0
    sources = [s.strip() for s in str(source).split(";") if s.strip() and s.strip() != "reference"]
    full_weight_used = 0
    for src in sources:
        if src in ("", "reference", "michelin", "trip.com", "hk01"):
            w = 0.10
        else:
            w = 0.10
        if full_weight_used < 2:
            score += w
            full_weight_used += 1
        else:
            score += w * 0.5
    # mention_count bonus
    try:
        mc = int(mention_count_raw or 0)
        if mc > 10:
            score += 0.10
        elif mc > 3:
            score += 0.05
    except (ValueError, TypeError):
        pass
    return min(score, 0.5)


def slot_key(*parts):
    return "_".join(str(p or "unknown") for p in parts)


# ── 餐厅处理 ──────────────────────────────────────────────────────────────────

def process_restaurants():
    print("\n[RESTAURANTS]")
    src = DATA_DIR / "restaurants_normalized.csv"
    with open(src, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"  Loaded {len(rows)} rows")

    # Step 1: 按 city × cuisine_normalized × budget_tier 分组，计算 tabelog percentile
    groups = defaultdict(list)
    for r in rows:
        key = (r["city_code"], r["cuisine_normalized"], r["budget_tier"])
        groups[key].append(r)

    # Step 2: 计算每行的 base_quality_score
    for r in rows:
        key = (r["city_code"], r["cuisine_normalized"], r["budget_tier"])
        group = groups[key]
        tabelog_vals = [float(x["tabelog_score"]) for x in group if x.get("tabelog_score")]
        has_tab = r.get("tabelog_score") and r["tabelog_score"] != ""
        has_mich = r.get("michelin") and r["michelin"] != ""

        if has_tab:
            pct = percentile_rank(float(r["tabelog_score"]), tabelog_vals)
            base = map_percentile_to_score(pct)
            bonus = michelin_bonus(r.get("michelin", "")) if has_mich else 0.0
            r["base_quality_score"] = round(min(base + bonus, 5.0), 3)
            r["score_basis"] = "tabelog_percentile"
        elif has_mich:
            # Michelin だが tabelog なし → group median + bonus
            median_base = 3.5
            bonus = michelin_bonus(r["michelin"])
            r["base_quality_score"] = round(min(median_base + bonus, 5.0), 3)
            r["score_basis"] = "michelin_only"
        else:
            # Neither: use group median
            if tabelog_vals:
                median_tab = sorted(tabelog_vals)[len(tabelog_vals) // 2]
                pct = percentile_rank(median_tab, tabelog_vals)
                r["base_quality_score"] = round(map_percentile_to_score(pct), 3)
            else:
                r["base_quality_score"] = 3.0
            r["score_basis"] = "group_median"

        r["indie_support_score"] = round(indie_support(r.get("source", ""), r.get("mention_count", "")), 3)
        tf = 0.0  # traveler_fit_modifier — Phase 2B 填充
        risk = 0.0  # risk_penalty — Phase 2B 填充
        r["house_score"] = round(r["base_quality_score"] + tf + r["indie_support_score"] + risk, 3)

    # Step 3: Slot 分组 + 城市相对 percentile + same-slot cap
    slots = defaultdict(list)
    for r in rows:
        corridor = r.get("corridor") or "no_corridor"
        s = slot_key(r["city_code"], corridor, r["cuisine_normalized"], r["budget_tier"])
        r["selection_slot"] = s
        slots[s].append(r)

    selected_count = 0
    for slot, slot_rows in slots.items():
        n = len(slot_rows)
        sorted_rows = sorted(slot_rows, key=lambda x: -x["house_score"])

        if n >= 15:
            top_n = max(1, int(n * 0.20))
            cutoff = sorted_rows[top_n - 1]["house_score"] if top_n <= len(sorted_rows) else 0
            for i, r in enumerate(sorted_rows):
                if i < top_n and i < 3:
                    r["selection_status"] = "selected"
                elif abs(r["house_score"] - cutoff) < 0.15 and i < 5:
                    r["selection_status"] = "borderline"
                else:
                    r["selection_status"] = "excluded"
        elif n >= 6:
            for i, r in enumerate(sorted_rows):
                if i < 3:
                    r["selection_status"] = "selected"
                elif i < 5:
                    r["selection_status"] = "borderline"
                else:
                    r["selection_status"] = "excluded"
        else:
            for r in slot_rows:
                r["selection_status"] = "needs_editorial"

        selected_count += sum(1 for r in slot_rows if r["selection_status"] in ("selected", "borderline"))

    # Step 4: 输出
    out = []
    for r in rows:
        out.append({
            "name_ja": r["name_ja"],
            "city_code": r["city_code"],
            "area": r.get("area", ""),
            "corridor": r.get("corridor"),
            "cuisine_type": r.get("cuisine_type", ""),
            "cuisine_normalized": r["cuisine_normalized"],
            "budget_tier": r["budget_tier"],
            "tabelog_score": r.get("tabelog_score") or None,
            "michelin": r.get("michelin") or None,
            "selection_slot": r["selection_slot"],
            "base_quality_score": r["base_quality_score"],
            "score_basis": r["score_basis"],
            "indie_support_score": r["indie_support_score"],
            "house_score": r["house_score"],
            "selection_status": r["selection_status"],
            # Phase 2B 填充
            "quality_evidence": None,
            "traveler_fit_modifier": None,
            "traveler_fit_evidence": None,
            "execution_penalty": None,
            "execution_evidence": None,
            "risk_watch": None,
            "risk_detail": None,
            "editorial_exclusion": None,
            "editorial_exclusion_reason": None,
            "one_line_editorial_note": None,
            "grade": None,
            "selection_tags": [],
            "opus_reviewed": False,
            "data_confidence": "single_source" if r.get("tabelog_score") else "ai_generated",
            "source": r.get("source", ""),
        })

    out_path = DATA_DIR / "restaurants_ledger_phase2a.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    # Stats
    status_dist = defaultdict(int)
    grade_dist = defaultdict(int)
    score_basis_dist = defaultdict(int)
    for r in out:
        status_dist[r["selection_status"]] += 1
        score_basis_dist[r["score_basis"]] += 1

    print(f"  [ok] {out_path} ({len(out)} entries)")
    print(f"\n  Selection status:")
    for k, v in sorted(status_dist.items(), key=lambda x: -x[1]):
        print(f"    {v:4d}  {k}")
    print(f"\n  Score basis:")
    for k, v in sorted(score_basis_dist.items(), key=lambda x: -x[1]):
        print(f"    {v:4d}  {k}")
    print(f"\n  Unique slots: {len(slots)}")
    print(f"  Slots by size: 1-5={sum(1 for s in slots.values() if len(s)<6)}, "
          f"6-14={sum(1 for s in slots.values() if 6<=len(s)<15)}, "
          f">=15={sum(1 for s in slots.values() if len(s)>=15)}")

    return out


# ── 酒店处理 ──────────────────────────────────────────────────────────────────

def process_hotels():
    print("\n[HOTELS]")
    src = DATA_DIR / "hotels_normalized.csv"
    with open(src, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"  Loaded {len(rows)} rows")

    for r in rows:
        # base_quality_score
        mk = r.get("michelin_keys", "")
        ota = r.get("ota_rating", "")
        forbes = r.get("forbes_stars", "")

        if mk and mk not in ("", "0"):
            k = int(mk)
            scores = {3: 5.0, 2: 4.5, 1: 4.0}
            base = scores.get(k, 4.0)
            r["score_basis"] = "michelin_keys"
        elif ota and ota not in ("", "0"):
            base = float(ota) / 5.0 * 2.5 + 2.5  # → 2.5-5.0
            r["score_basis"] = "ota_rating"
        elif forbes and forbes not in ("", "0"):
            stars = {5: 4.75, 4: 4.25, 3: 3.75}.get(int(forbes), 3.75)
            base = stars
            r["score_basis"] = "forbes_stars"
        else:
            # 组内 median（按 city × hotel_type × price_level）
            base = 3.0
            r["score_basis"] = "group_median"

        # 修正信号
        ht = r.get("hotel_type", "")
        if ht in ("ryokan", "boutique", "auberge", "luxury_resort"):
            base = min(base + 0.1, 5.0)
        kf = r.get("key_features", "")
        if kf and len(kf.split(";")) >= 3:
            base = min(base + 0.05, 5.0)

        r["base_quality_score"] = round(base, 3)
        r["indie_support_score"] = round(indie_support(r.get("source", ""), 0), 3)
        r["house_score"] = round(r["base_quality_score"] + r["indie_support_score"], 3)

    # Slot 分组
    slots = defaultdict(list)
    for r in rows:
        s = slot_key(r["city_code"], r.get("area", "unknown"), r.get("hotel_type", "unknown"), r["price_level"])
        r["selection_slot"] = s
        slots[s].append(r)

    for slot, slot_rows in slots.items():
        n = len(slot_rows)
        sorted_rows = sorted(slot_rows, key=lambda x: -x["house_score"])

        if n >= 15:
            top_n = max(1, int(n * 0.20))
            cutoff = sorted_rows[min(top_n - 1, len(sorted_rows) - 1)]["house_score"]
            for i, r in enumerate(sorted_rows):
                if i < top_n and i < 3:
                    r["selection_status"] = "selected"
                elif abs(r["house_score"] - cutoff) < 0.15:
                    r["selection_status"] = "borderline"
                else:
                    r["selection_status"] = "excluded"
        elif n >= 6:
            for i, r in enumerate(sorted_rows):
                if i < 3:
                    r["selection_status"] = "selected"
                elif i < 5:
                    r["selection_status"] = "borderline"
                else:
                    r["selection_status"] = "excluded"
        else:
            for r in slot_rows:
                r["selection_status"] = "needs_editorial"

    out = []
    for r in rows:
        out.append({
            "name_ja": r["name_ja"],
            "city_code": r["city_code"],
            "area": r.get("area", ""),
            "hotel_type": r.get("hotel_type", ""),
            "price_level": r["price_level"],
            "michelin_keys": r.get("michelin_keys") or None,
            "ota_rating": r.get("ota_rating") or None,
            "nightly_jpy_min": r.get("nightly_jpy_min") or None,
            "key_features": r.get("key_features", ""),
            "selection_slot": r["selection_slot"],
            "base_quality_score": r["base_quality_score"],
            "score_basis": r["score_basis"],
            "indie_support_score": r["indie_support_score"],
            "house_score": r["house_score"],
            "selection_status": r["selection_status"],
            "quality_evidence": None,
            "traveler_fit_modifier": None,
            "traveler_fit_evidence": None,
            "execution_penalty": None,
            "execution_evidence": None,
            "risk_watch": None,
            "editorial_exclusion": None,
            "editorial_exclusion_reason": None,
            "one_line_editorial_note": None,
            "grade": None,
            "selection_tags": [],
            "opus_reviewed": False,
            "data_confidence": "single_source" if r.get("michelin_keys") or r.get("ota_rating") else "ai_generated",
            "source": r.get("source", ""),
        })

    out_path = DATA_DIR / "hotels_ledger_phase2a.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    status_dist = defaultdict(int)
    score_basis_dist = defaultdict(int)
    for r in out:
        status_dist[r["selection_status"]] += 1
        score_basis_dist[r["score_basis"]] += 1

    print(f"  [ok] {out_path} ({len(out)} entries)")
    print(f"\n  Selection status:")
    for k, v in sorted(status_dist.items(), key=lambda x: -x[1]):
        print(f"    {v:4d}  {k}")
    print(f"\n  Score basis:")
    for k, v in sorted(score_basis_dist.items(), key=lambda x: -x[1]):
        print(f"    {v:4d}  {k}")
    print(f"\n  Unique slots: {len(slots)}")

    return out


# ── 景点处理 ──────────────────────────────────────────────────────────────────

def process_spots():
    print("\n[SPOTS]")
    src = DATA_DIR / "spots_candidate_pool.csv"
    with open(src, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"  Loaded {len(rows)} rows")

    # Japan-guide level 映射
    level_map = {"top": 4.0, "recommended": 3.5, "featured": 3.0}
    # 京都/奈良 history_religion 加成
    history_bonus_cities = {"kyoto", "nara", "koyasan"}

    for r in rows:
        base = level_map.get(r.get("japan_guide_level", ""), 3.0)
        if r.get("sub_type") == "history_religion" and r.get("city_code") in history_bonus_cities:
            base = min(base + 0.25, 5.0)
        r["base_quality_score"] = round(base, 3)
        r["score_basis"] = "guide_level"
        r["indie_support_score"] = 0.0
        r["house_score"] = round(base, 3)

    # Slot 分组
    slots = defaultdict(list)
    for r in rows:
        s = slot_key(r["city_code"], r.get("area", "unknown"), r.get("sub_type", "unknown"))
        r["selection_slot"] = s
        slots[s].append(r)

    for slot, slot_rows in slots.items():
        n = len(slot_rows)
        sorted_rows = sorted(slot_rows, key=lambda x: -x["house_score"])
        for i, r in enumerate(sorted_rows):
            if i < 3:
                r["selection_status"] = "selected"
            elif i < 5:
                r["selection_status"] = "borderline" if n >= 6 else "needs_editorial"
            else:
                r["selection_status"] = "excluded" if n >= 6 else "needs_editorial"

    out = []
    for r in rows:
        out.append({
            "name_en": r.get("name_en", ""),
            "name_ja": r.get("name_ja", ""),
            "city_code": r["city_code"],
            "area": r.get("area", ""),
            "main_type": r.get("main_type", ""),
            "sub_type": r.get("sub_type", ""),
            "japan_guide_level": r.get("japan_guide_level", ""),
            "japan_guide_url": r.get("japan_guide_url", ""),
            "selection_slot": r["selection_slot"],
            "base_quality_score": r["base_quality_score"],
            "score_basis": r["score_basis"],
            "indie_support_score": r["indie_support_score"],
            "house_score": r["house_score"],
            "selection_status": r["selection_status"],
            "quality_evidence": None,
            "traveler_fit_modifier": None,
            "traveler_fit_evidence": None,
            "execution_penalty": None,
            "execution_evidence": None,
            "risk_watch": None,
            "editorial_exclusion": None,
            "editorial_exclusion_reason": None,
            "one_line_editorial_note": None,
            "grade": None,
            "selection_tags": [],
            "opus_reviewed": False,
            "data_confidence": "cross_checked",
            "source": "japan-guide",
        })

    out_path = DATA_DIR / "spots_ledger_phase2a.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    status_dist = defaultdict(int)
    for r in out:
        status_dist[r["selection_status"]] += 1

    print(f"  [ok] {out_path} ({len(out)} entries)")
    print(f"\n  Selection status:")
    for k, v in sorted(status_dist.items(), key=lambda x: -x[1]):
        print(f"    {v:4d}  {k}")
    print(f"\n  Unique slots: {len(slots)}")

    return out


# ── 汇总 ─────────────────────────────────────────────────────────────────────

def print_summary(restaurants, hotels, spots):
    print("\n" + "=" * 70)
    print("PHASE 2A SUMMARY")
    print("=" * 70)

    for label, data in [("Restaurants", restaurants), ("Hotels", hotels), ("Spots", spots)]:
        sel = sum(1 for r in data if r["selection_status"] in ("selected", "borderline", "needs_editorial"))
        excl = sum(1 for r in data if r["selection_status"] == "excluded")
        print(f"\n{label}: {len(data)} total, {sel} for Phase 2B, {excl} excluded")
        for status in ("selected", "borderline", "needs_editorial", "excluded"):
            n = sum(1 for r in data if r["selection_status"] == status)
            print(f"  {n:4d}  {status}")

    total_for_2b = sum(
        sum(1 for r in data if r["selection_status"] in ("selected", "borderline", "needs_editorial"))
        for data in [restaurants, hotels, spots]
    )
    print(f"\nTotal candidates for Phase 2B (Sonnet evidence): {total_for_2b}")
    print("(Opus will review only S/A candidates + borderline + risk items)")


if __name__ == "__main__":
    print("=" * 70)
    print("PHASE 2A: BUILDING SELECTION LEDGER")
    print("=" * 70)
    restaurants = process_restaurants()
    hotels = process_hotels()
    spots = process_spots()
    print_summary(restaurants, hotels, spots)
