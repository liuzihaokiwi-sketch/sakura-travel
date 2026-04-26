"""D47 hotel tier remapping: 4 档 → 6 档 (b1-b6).

京都阈值（trip.com 京都 9 档压缩成 6）：
  b1: 0-500    b2: 500-950   b3: 950-1200
  b4: 1200-2000  b5: 2000-3500  b6: ≥3500

关西其他城市阈值（trip.com 关西 6 档 1:1）：
  b1: 0-400    b2: 400-600   b3: 600-850
  b4: 850-1250  b5: 1250-2050  b6: ≥2050

Run: python scripts/hotel_reband.py [--apply]
Default = dry-run.
"""
from __future__ import annotations

import io
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

DATA = Path("japan/kansai/hotels/data/hotels__kansai.json")

KYOTO_BANDS = [
    ("b1", 0, 500),
    ("b2", 500, 950),
    ("b3", 950, 1200),
    ("b4", 1200, 2000),
    ("b5", 2000, 3500),
    ("b6", 3500, 10**9),
]

OTHER_BANDS = [
    ("b1", 0, 400),
    ("b2", 400, 600),
    ("b3", 600, 850),
    ("b4", 850, 1250),
    ("b5", 1250, 2050),
    ("b6", 2050, 10**9),
]

TIER_NAMES = {"b1": "经济", "b2": "舒适", "b3": "品质",
              "b4": "高端", "b5": "奢华", "b6": "顶奢"}


def band_for(median: float, city: str) -> str:
    table = KYOTO_BANDS if city == "京都" else OTHER_BANDS
    for code, lo, hi in table:
        if lo <= median < hi:
            return code
    return table[-1][0]


def main() -> None:
    apply = "--apply" in sys.argv
    data = json.loads(DATA.read_text(encoding="utf-8"))

    changed = []
    for h in data:
        prices = h.get("price_cny_per_night")
        if not prices or len(prices) < 1:
            continue
        median = prices[0]
        city = h.get("city", "")
        old = h["tier"]
        new = band_for(median, city)
        if old != new:
            changed.append({
                "id": h["id"],
                "name": h["note"].get("店名", "")[:40],
                "city": city,
                "median": median,
                "old": old,
                "new": new,
                "new_name": TIER_NAMES.get(new, new),
            })
            if apply:
                h["tier"] = new

    print(f"total={len(data)} | changed={len(changed)}")
    print()
    print(f"{'old → new':25} count")
    move_counter = Counter((c["old"], c["new"]) for c in changed)
    for (old, new), n in sorted(move_counter.items(), key=lambda x: -x[1]):
        print(f"  {old:8} → {new:8}  {n}")
    print()

    print(f"分布（new tier × city）:")
    new_dist = Counter()
    for h in data:
        prices = h.get("price_cny_per_night")
        if not prices or len(prices) < 1:
            continue
        new = band_for(prices[0], h.get("city", ""))
        new_dist[(new, h.get("city", ""))] += 1
    for (tier, city), n in sorted(new_dist.items()):
        print(f"  {tier} {TIER_NAMES.get(tier, tier):4} {city:6} {n}")
    print()

    if changed:
        print("Sample (max 30):")
        print(f"  {'id':50} {'city':6} {'median':>6} {'old':6} {'new':6} {'name'}")
        for c in changed[:30]:
            print(f"  {c['id']:50} {c['city']:6} {c['median']:6} {c['old']:6} {c['new']:6} {c['name']}")
        if len(changed) > 30:
            print(f"  ... +{len(changed) - 30} more")

    if apply:
        DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[APPLIED] written to {DATA}")
    else:
        print("\n[DRY-RUN] no file change. add --apply to write.")


if __name__ == "__main__":
    main()
