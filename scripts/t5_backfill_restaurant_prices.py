"""
T5: 餐厅价格信息补充
1. 有 google_place_id → Google Places Details 拉 price_level
2. 无 google_place_id → 按 cuisine_type 默认价格带
3. cuisine_type 也没有 → 按 tabelog_score 估算

运行: python scripts/t5_backfill_restaurant_prices.py [--dry-run] [--limit 200]
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from app.domains.catalog.crawlers.google_places import fetch_place_details

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

CALL_INTERVAL = 0.15

# Google price_level → (min_jpy, max_jpy)
PRICE_LEVEL_MAP = {
    0: (300, 500),
    1: (500, 1500),
    2: (1500, 3500),
    3: (3500, 8000),
    4: (8000, 30000),
}

# cuisine_type → (min_jpy, max_jpy)
CUISINE_PRICE_MAP = {
    "ramen":        (800, 1200),
    "soba":         (800, 1500),
    "udon":         (800, 1200),
    "tempura":      (1500, 4000),
    "sushi":        (2000, 5000),
    "sushi_premium": (5000, 20000),
    "kaiseki":      (8000, 20000),
    "kappo":        (8000, 20000),
    "izakaya":      (3000, 5000),
    "yakitori":     (2000, 4000),
    "yakiniku":     (3000, 6000),
    "teppanyaki":   (3000, 7000),
    "cafe":         (500, 1500),
    "coffee":       (500, 1000),
    "sweets":       (500, 1200),
    "bakery":       (500, 1000),
    "curry":        (800, 1500),
    "gyoza":        (800, 1500),
    "tonkatsu":     (1000, 2000),
    "seafood":      (2000, 4000),
    "crab":         (3000, 8000),
    "soup_curry":   (1000, 2000),
    "fast_food":    (500, 1000),
    "chinese":      (1000, 3000),
    "italian":      (1500, 4000),
    "french":       (3000, 10000),
    "steak":        (3000, 8000),
    "bbq":          (2000, 5000),
    "buffet":       (1500, 3500),
    "set_meal":     (800, 1500),
    "hokkaido_seafood": (2000, 5000),
    "jingisukan":   (2000, 4000),   # 成吉思汗烤肉
    "soup":         (800, 1500),
    "noodle":       (800, 1500),
    "donburi":      (800, 1500),
    "bento":        (500, 1000),
    "other":        (1000, 2500),
}

# tabelog_score 段 → 价格推算（无 cuisine 时兜底）
def score_to_price(score: float | None) -> tuple[int, int]:
    if score is None:
        return (1000, 3000)
    if score >= 4.0:
        return (3000, 8000)
    if score >= 3.5:
        return (1500, 4000)
    if score >= 3.0:
        return (800, 2000)
    return (700, 1500)


async def main(dry_run: bool = False, limit: int = 300) -> None:
    async with AsyncSessionLocal() as session:
        r_before = await session.execute(text("""
            SELECT
                COUNT(CASE WHEN r.price_range_min_jpy IS NOT NULL THEN 1 END) AS has_price,
                COUNT(*) AS total
            FROM restaurants r
            JOIN entity_base eb ON eb.entity_id = r.entity_id
            WHERE eb.is_active = true
        """))
        row = r_before.fetchone()
        print(f"Before: {row[0]}/{row[1]} restaurants have price ({row[0]/max(row[1],1)*100:.1f}%)")

        # 拉所有没有价格的餐厅
        r_rests = await session.execute(text("""
            SELECT
                r.entity_id::text,
                eb.google_place_id,
                r.cuisine_type,
                r.tabelog_score
            FROM restaurants r
            JOIN entity_base eb ON eb.entity_id = r.entity_id
            WHERE eb.is_active = true
              AND r.price_range_min_jpy IS NULL
            LIMIT :limit
        """), {"limit": limit})
        restaurants = r_rests.fetchall()
        print(f"Restaurants without price: {len(restaurants)}")

        # 分两组
        with_place_id = [(eid, pid, ct, ts) for eid, pid, ct, ts in restaurants if pid]
        without_place_id = [(eid, pid, ct, ts) for eid, pid, ct, ts in restaurants if not pid]
        print(f"  With place_id: {len(with_place_id)}, Without: {len(without_place_id)}")

        updated_api = updated_rule = 0

        # ── Group 1: Google Places Details ───────────────────────────────────
        print(f"\nFetching price from Google Places for {len(with_place_id)} restaurants...")
        for entity_id, place_id, cuisine_type, tabelog_score in with_place_id:
            try:
                details = await fetch_place_details(place_id)
                await asyncio.sleep(CALL_INTERVAL)

                if details and details.get("price_level") is not None:
                    level = details["price_level"]
                    lo, hi = PRICE_LEVEL_MAP.get(level, (1000, 3000))
                else:
                    # fallback to cuisine type
                    lo, hi = CUISINE_PRICE_MAP.get(cuisine_type or "other", (1000, 3000))

                if not dry_run:
                    await session.execute(text("""
                        UPDATE restaurants
                        SET price_range_min_jpy = :lo, price_range_max_jpy = :hi
                        WHERE entity_id = CAST(:eid AS uuid)
                    """), {"lo": lo, "hi": hi, "eid": entity_id})
                updated_api += 1
                if not dry_run and updated_api % 20 == 0:
                    await session.flush()
            except Exception as e:
                logger.debug("API price failed %s: %s", entity_id, e)

        # ── Group 2: cuisine_type / tabelog_score ────────────────────────────
        print(f"\nApplying rule-based prices for {len(without_place_id)} restaurants...")
        for entity_id, _, cuisine_type, tabelog_score in without_place_id:
            if cuisine_type and cuisine_type in CUISINE_PRICE_MAP:
                lo, hi = CUISINE_PRICE_MAP[cuisine_type]
            else:
                lo, hi = score_to_price(float(tabelog_score) if tabelog_score else None)

            if not dry_run:
                await session.execute(text("""
                    UPDATE restaurants
                    SET price_range_min_jpy = :lo, price_range_max_jpy = :hi
                    WHERE entity_id = CAST(:eid AS uuid)
                """), {"lo": lo, "hi": hi, "eid": entity_id})
            updated_rule += 1

        if not dry_run:
            await session.commit()

        print(f"\nResult: api_updated={updated_api}, rule_updated={updated_rule}")

        if not dry_run:
            r_after = await session.execute(text("""
                SELECT
                    COUNT(CASE WHEN r.price_range_min_jpy IS NOT NULL THEN 1 END),
                    COUNT(*)
                FROM restaurants r
                JOIN entity_base eb ON eb.entity_id = r.entity_id
                WHERE eb.is_active = true
            """))
            row_a = r_after.fetchone()
            pct = row_a[0] / max(row_a[1], 1) * 100
            print(f"After: {row_a[0]}/{row_a[1]} restaurants have price ({pct:.1f}%)")
            if pct >= 80:
                print("[PASS] Verification: > 80% have price")
            else:
                print(f"[WARN] Verification: {pct:.1f}% < 80% target")

        print("\n[OK] T5 DONE")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=300)
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run, limit=args.limit))
