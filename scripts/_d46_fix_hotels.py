"""修补 D46 迁移后的 201 家酒店：
1. 重新归档 tier（按平季中位 RMB 严格区间·不靠旧 budget_tier）
2. 补 near_attractions（按酒店 area → entity area 映射·挂 1-2 个代表 entity）
3. 补元数据数据来源（标 single_source 不变）
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
HOTELS = REPO / "japan/kansai/hotels/data/hotels__kansai.json"

# 酒店旧 area → entity area + 代表 entity_id（每 area 选 2-3 个最有名的）
# 旧酒店数据里的 area 是 D40 携程粒度·entity 用的是 D43 后的标准化粒度
HOTEL_AREA_MAP = {
    # 京都
    "shijo_kawaramachi": {"entity_area": "nakagyo", "entities": ["kyo_pontocho", "kyo_nishiki_market", "kyo_nijo_castle"]},
    "kyoto_station": {"entity_area": "京都站", "entities": ["kyo_railway_museum", "kyo_kyoto_aquarium"]},
    "gion_higashiyama": {"entity_area": "gion", "entities": ["kyo_yasaka_shrine", "kyo_kenninji", "kyo_maruyama_park"]},
    "arashiyama": {"entity_area": "arashiyama", "entities": ["kyo_togetsukyo", "kyo_arashiyama_bamboo", "kyo_tenryuji"]},
    "nijo_central": {"entity_area": "central_kyoto", "entities": ["kyo_nijo_castle"]},
    # 大阪
    "umeda_kita": {"entity_area": "osaka_kita", "entities": ["osk_nakanoshima", "osk_nakazakicho", "osk_mint_bureau"]},
    "namba_dotonbori": {"entity_area": "namba", "entities": ["osk_dotonbori", "osk_kuromon", "osk_hozenji_yokocho"]},
    "shinsaibashi": {"entity_area": "namba", "entities": ["osk_dotonbori", "osk_kuromon"]},
    "honmachi": {"entity_area": "osaka_central", "entities": ["osk_dotonbori"]},
    "tennoji_shinsekai": {"entity_area": "abeno_tennoji", "entities": ["osk_abeno_harukas", "osk_shitennoji"]},
    "bay_area": {"entity_area": "tempozan", "entities": ["osk_kaiyukan", "osk_tempozan_ferris"]},
    # 神户
    "sannomiya": {"entity_area": "kobe_central", "entities": ["kob_kitano_kyoryuchi", "kob_nankinmachi"]},
    "kitano_shinkobe": {"entity_area": "kobe_kitano", "entities": ["kob_kitano_kyoryuchi"]},
    "harborland_meriken": {"entity_area": "kobe_waterfront", "entities": ["kob_meriken_park", "kob_kobe_maritime"]},
    "motomachi_nankinmachi": {"entity_area": "kobe_central", "entities": ["kob_nankinmachi"]},
    # 奈良
    "nara_park_area": {"entity_area": "nara_park", "entities": ["nar_todaiji", "nar_nara_park", "nar_kasuga_taisha"]},
    # 温泉
    "arima_onsen": {"entity_area": "arima", "entities": ["arm_arima_onsen", "arm_kin_no_yu", "arm_ginnosyu"]},
    "kinosaki_onsen": {"entity_area": "kinosaki", "entities": ["kns_kinosaki"]},
    "koyasan_temple": {"entity_area": "koyasan", "entities": ["kya_kongobuji", "kya_okunoin"]},
    "shirahama": {"entity_area": "shirahama", "entities": ["shr_shirahama_beach", "shr_sakinoyu_onsen"]},
}

# tier 严格区间（按平季中位 RMB）
def tier_from_price(regular: int) -> str:
    if regular < 600:
        return "comfort"
    elif regular < 1700:
        return "quality"
    elif regular < 4000:
        return "luxury"
    else:
        return "top"


def fix_one(h: dict, entity_ids: set[str]) -> dict:
    pr = h.get("price_cny_per_night", [0, 0])
    regular = pr[0] if pr else 0

    # 1. 重新归档 tier（按平季中位）
    if regular > 0:
        h["tier"] = tier_from_price(regular)

    # 2. 补 near_attractions
    if not h.get("near_attractions"):
        area = h.get("area", "")
        mapping = HOTEL_AREA_MAP.get(area)
        if mapping:
            valid = [eid for eid in mapping["entities"] if eid in entity_ids]
            if valid:
                # 默认 walk_min=10·待精修
                h["near_attractions"] = [
                    {"entity_id": eid, "walk_min": 10}
                    for eid in valid[:2]
                ]
        # 如果 mapping 没匹配·near_attractions 留空·后续手动补

    return h


def main():
    # 加载 entity ids
    import glob
    entity_ids = set()
    for f in glob.glob(str(REPO / "japan/kansai/entities/*.json")):
        with open(f, encoding="utf-8") as fp:
            data = json.load(fp)
        if isinstance(data, dict):
            for k in data.keys():
                if not k.startswith("_"):
                    entity_ids.add(k)
    print(f"载入 entity: {len(entity_ids)}")

    # 加载酒店
    with open(HOTELS, encoding="utf-8") as f:
        pool = json.load(f)
    print(f"载入酒店: {len(pool)}")

    fixed_count = 0
    near_filled = 0
    tier_changed = 0
    for h in pool:
        old_tier = h.get("tier")
        old_near = bool(h.get("near_attractions"))
        h = fix_one(h, entity_ids)
        if h.get("tier") != old_tier:
            tier_changed += 1
        if not old_near and h.get("near_attractions"):
            near_filled += 1
        fixed_count += 1

    # 写回
    with open(HOTELS, "w", encoding="utf-8") as f:
        json.dump(pool, f, ensure_ascii=False, indent=2)

    print(f"✓ tier 重归: {tier_changed} 家")
    print(f"✓ near_attractions 补全: {near_filled} 家")
    print(f"✓ 总写回: {fixed_count} 家")

    # 重新统计
    from collections import Counter
    print("\n=== 修后 tier 分布 ===")
    for t, n in Counter(h["tier"] for h in pool).most_common():
        print(f"  {t}: {n}")

    print("\n=== 仍缺 near_attractions 的 area ===")
    missing = Counter(h["area"] for h in pool if not h.get("near_attractions"))
    for a, n in missing.most_common():
        print(f"  {a}: {n}")


if __name__ == "__main__":
    main()
