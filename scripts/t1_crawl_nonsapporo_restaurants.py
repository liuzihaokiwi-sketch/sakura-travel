"""
T1: 非札幌城市餐厅数据补充
Google Places Nearby Search, type=restaurant, rating > 3.5
每城市拉 40 家，存入 entity_base + restaurants 表

运行: python scripts/t1_crawl_nonsapporo_restaurants.py [--dry-run]
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
from app.domains.catalog.crawlers.google_places import (
    _get_city_center, _nearby_search, _parse_restaurant, CITY_RADIUS, DEFAULT_RADIUS
)
from app.domains.catalog.upsert import upsert_entity

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# 需要补充餐厅的城市（排除已有足够数据的 sapporo/niseko）
TARGET_CITIES = [
    "hakodate",
    "otaru",
    "asahikawa",
    "furano",
    "biei",
    "kushiro",
    "toya",
    "abashiri",
    "noboribetsu",
]

LIMIT_PER_CITY = 40
MIN_RATING = 3.5


async def count_by_city(session) -> dict:
    r = await session.execute(text(
        "SELECT city_code, COUNT(*) FROM entity_base "
        "WHERE entity_type='restaurant' AND is_active=true "
        "GROUP BY city_code ORDER BY city_code"
    ))
    return {row[0]: row[1] for row in r.fetchall()}


async def crawl_city_restaurants(session, city_code: str, dry_run: bool) -> int:
    center = await _get_city_center(city_code)
    if not center:
        print(f"  [{city_code}] No center coords, skipping")
        return 0

    radius = CITY_RADIUS.get(city_code, DEFAULT_RADIUS)
    # 多关键词搜索提高覆盖
    keywords = ["", "ランチ 定食", "居酒屋 海鮮", "ラーメン そば", "カフェ スイーツ"]
    seen_place_ids: set[str] = set()
    all_results = []

    for keyword in keywords:
        if len(all_results) >= LIMIT_PER_CITY:
            break
        raw = await _nearby_search(
            center[0], center[1], radius,
            "restaurant", keyword=keyword, limit=LIMIT_PER_CITY,
        )
        for place in raw:
            pid = place.get("place_id", "")
            if pid in seen_place_ids:
                continue
            rating = place.get("rating", 0) or 0
            if rating < MIN_RATING and rating > 0:
                continue  # rating=0 means no ratings yet, keep them
            seen_place_ids.add(pid)
            parsed = _parse_restaurant(place, city_code)
            if parsed.get("lat") and parsed.get("lng"):
                all_results.append(parsed)
        await asyncio.sleep(1)

    print(f"  [{city_code}] Fetched {len(all_results)} restaurant candidates")

    if dry_run:
        return len(all_results)

    saved = skipped = 0
    for item in all_results:
        try:
            item["trust_status"] = "unverified"
            item["data_tier"] = "A"
            await upsert_entity(
                session, "restaurant", item,
                google_place_id=item.get("google_place_id"),
            )
            saved += 1
            if saved % 10 == 0:
                await session.flush()
        except Exception as e:
            skipped += 1
            logger.debug("Restaurant upsert failed: %s — %s", item.get("name_ja", "?"), e)

    await session.commit()
    print(f"  [{city_code}] Saved {saved}, skipped {skipped}")
    return saved


async def main(dry_run: bool = False) -> None:
    async with AsyncSessionLocal() as session:
        before = await count_by_city(session)
        print("=== Before ===")
        for city in TARGET_CITIES:
            print(f"  {city}: {before.get(city, 0)}")

        total_saved = 0
        for city in TARGET_CITIES:
            print(f"\n[T1] Processing {city}...")
            n = await crawl_city_restaurants(session, city, dry_run)
            total_saved += n

        if not dry_run:
            after = await count_by_city(session)
            print("\n=== After ===")
            for city in TARGET_CITIES:
                print(f"  {city}: {before.get(city, 0)} → {after.get(city, 0)}")
            print(f"\n[OK] T1 DONE: +{total_saved} restaurants total")
        else:
            print(f"\n[DRY RUN] Would save ~{total_saved} restaurants")

        # 验证
        print("\n=== Verification ===")
        after_check = await count_by_city(session)
        fails = [c for c in TARGET_CITIES if after_check.get(c, 0) < 20]
        if fails and not dry_run:
            print(f"[WARN] Cities with < 20 restaurants: {fails}")
        elif not dry_run:
            print("[OK] All target cities have >= 20 restaurants")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
