"""D47 hotel tier remapping.

Old D46 boundaries: 300/600/1700/4000
New D47 boundaries (trip.com Kansai 6 tiers): 600/1250/2050

Run: python scripts/hotel_retier.py [--apply]
Default = dry-run (only show diff). --apply writes the file.
"""

import json
import sys
from collections import Counter
from pathlib import Path

DATA = Path("japan/kansai/hotels/data/hotels__kansai.json")


def new_tier(median_cny: int) -> str:
    if median_cny < 600:
        return "comfort"
    if median_cny < 1250:
        return "quality"
    if median_cny < 2050:
        return "luxury"
    return "top"


def main() -> None:
    apply = "--apply" in sys.argv
    data = json.loads(DATA.read_text(encoding="utf-8"))

    changed = []
    for h in data:
        prices = h.get("price_cny_per_night")
        if not prices or len(prices) < 1:
            continue
        median = prices[0]
        old = h["tier"]
        new = new_tier(median)
        if old != new:
            changed.append({
                "id": h["id"],
                "name": h["note"].get("店名", "")[:40],
                "city": h.get("city"),
                "median": median,
                "old_tier": old,
                "new_tier": new,
            })
            if apply:
                h["tier"] = new

    print(f"total={len(data)} | changed={len(changed)}")
    print()
    print(f"{'old → new':25} count")
    move_counter = Counter((c["old_tier"], c["new_tier"]) for c in changed)
    for (old, new), n in sorted(move_counter.items(), key=lambda x: -x[1]):
        print(f"  {old:8} → {new:8}  {n}")
    print()

    print("Sample (max 30):")
    print(f"{'id':50} {'city':6} {'median':>6} {'old':8} {'new':8} {'name'}")
    for c in changed[:30]:
        print(f"  {c['id']:50} {c['city']:6} {c['median']:6} {c['old_tier']:8} {c['new_tier']:8} {c['name']}")
    if len(changed) > 30:
        print(f"  ... +{len(changed)-30} more")

    if apply:
        DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[APPLIED] written to {DATA}")
    else:
        print("\n[DRY-RUN] no file change. add --apply to write.")


if __name__ == "__main__":
    main()
