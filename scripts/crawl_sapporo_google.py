"""
B2: Google Places 批量拉取 — 札幌
景点（shrine/temple/museum/park/landmark/onsen 各20）
酒店（budget/mid/premium/luxury 各15）
特色店（5类关键词各15）

写入 entity_base，trust_status='unverified', data_tier='A'
运行：python scripts/crawl_sapporo_google.py [--dry-run]
"""
from __future__ import annotations

import asyncio
import logging
import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from app.domains.catalog.crawlers.google_places import (
    fetch_pois_by_subcategory,
    fetch_hotels_by_tier,
    fetch_specialty_shops_sapporo,
)
from app.domains.catalog.upsert import upsert_entity

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

CITY_CODE = "sapporo"


async def count_current(session) -> dict:
    """统计当前札幌实体数量"""
    r = await session.execute(text(
        "SELECT entity_type, COUNT(*) FROM entity_base "
        "WHERE city_code = 'sapporo' AND is_active = true "
        "GROUP BY entity_type"
    ))
    return {row[0]: row[1] for row in r.fetchall()}


async def crawl_pois(session, dry_run: bool) -> int:
    """景点：按子分类批量搜索"""
    print("[B2] Fetching POIs by subcategory (shrine/temple/museum/park/landmark/onsen)...")
    pois = await fetch_pois_by_subcategory(CITY_CODE, limit_per_category=20)
    print(f"  Fetched {len(pois)} POI candidates")

    if dry_run or not pois:
        return len(pois)

    saved = 0
    skipped = 0
    for poi in pois:
        try:
            poi["trust_status"] = "unverified"
            poi["data_tier"] = "A"
            entity = await upsert_entity(
                session,
                entity_type="poi",
                data=poi,
                google_place_id=poi.get("google_place_id"),
            )
            saved += 1
            if saved % 10 == 0:
                await session.flush()
        except Exception as e:
            skipped += 1
            logger.debug("POI upsert failed: %s — %s", poi.get("name_ja", "?"), e)

    await session.commit()
    print(f"  Saved {saved} POIs, skipped {skipped}")
    return saved


async def crawl_hotels(session, dry_run: bool) -> int:
    """酒店：按价位档次搜索"""
    print("[B2] Fetching hotels by price tier (budget/mid/premium/luxury)...")
    hotels = await fetch_hotels_by_tier(CITY_CODE, limit_per_tier=15)
    print(f"  Fetched {len(hotels)} hotel candidates")

    if dry_run or not hotels:
        return len(hotels)

    saved = 0
    skipped = 0
    for hotel in hotels:
        try:
            hotel["trust_status"] = "unverified"
            hotel["data_tier"] = "A"
            entity = await upsert_entity(
                session,
                entity_type="hotel",
                data=hotel,
                google_place_id=hotel.get("google_place_id"),
            )
            saved += 1
            if saved % 10 == 0:
                await session.flush()
        except Exception as e:
            skipped += 1
            logger.debug("Hotel upsert failed: %s — %s", hotel.get("name_ja", "?"), e)

    await session.commit()
    print(f"  Saved {saved} hotels, skipped {skipped}")
    return saved


async def crawl_shops(session, dry_run: bool) -> int:
    """特色店：北海道相关关键词搜索"""
    print("[B2] Fetching specialty shops (Hokkaido keywords)...")
    shops = await fetch_specialty_shops_sapporo(CITY_CODE, limit_per_category=15)
    print(f"  Fetched {len(shops)} shop candidates")

    if dry_run or not shops:
        return len(shops)

    saved = 0
    skipped = 0
    for shop in shops:
        try:
            shop["trust_status"] = "unverified"
            shop["data_tier"] = "A"
            entity = await upsert_entity(
                session,
                entity_type="poi",
                data=shop,
                google_place_id=shop.get("google_place_id"),
            )
            saved += 1
            if saved % 10 == 0:
                await session.flush()
        except Exception as e:
            skipped += 1
            logger.debug("Shop upsert failed: %s — %s", shop.get("name_ja", "?"), e)

    await session.commit()
    print(f"  Saved {saved} shops, skipped {skipped}")
    return saved


async def update_coverage(session, entity_type: str, count: int) -> None:
    """更新 city_data_coverage 的 current_count"""
    await session.execute(text("""
        UPDATE city_data_coverage
        SET current_count = current_count + :count,
            last_updated = NOW(),
            sources_used = CASE
                WHEN NOT ('google_places' = ANY(coalesce(sources_used::text[], ARRAY[]::text[])))
                THEN COALESCE(sources_used::text[], '{}')::jsonb || '["google_places"]'::jsonb
                ELSE sources_used
            END
        WHERE city_code = 'sapporo' AND entity_type = :entity_type
    """), {"count": count, "entity_type": entity_type})
    await session.commit()


async def main(dry_run: bool = False) -> None:
    async with AsyncSessionLocal() as session:
        # 展示当前状态
        before = await count_current(session)
        print(f"\nBefore: {before}")

        poi_count = await crawl_pois(session, dry_run)
        hotel_count = await crawl_hotels(session, dry_run)
        shop_count = await crawl_shops(session, dry_run)

        if not dry_run:
            await update_coverage(session, "poi", poi_count)
            await update_coverage(session, "hotel", hotel_count)

            after = await count_current(session)
            print(f"\nAfter:  {after}")
            print(f"\nNew entities: poi+{after.get('poi',0)-before.get('poi',0)}, "
                  f"hotel+{after.get('hotel',0)-before.get('hotel',0)}")

    if dry_run:
        print(f"\n[DRY RUN] Would have fetched: POI={poi_count}, Hotel={hotel_count}, Shop={shop_count}")
    else:
        print("\nB2 DONE")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
