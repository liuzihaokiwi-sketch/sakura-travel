"""
FIX-4: Google Places 批量拉取 — 北海道其他 9 个城市
（跳过已有充足数据的 sapporo）

目标：
  中型城市（hakodate/otaru/asahikawa）：80-120 个实体
  小城市（furano/biei/noboribetsu/toya/abashiri/kushiro/niseko）：30-50 个

策略：
  POI: shrine/temple/museum/park/landmark/onsen
  酒店: budget/mid/premium/luxury
  特色店（仅中型城市）

Google Places 每日 200 次限制。本脚本约需 120-150 次 API 调用，一天内可完成。

运行: python scripts/crawl_hokkaido_all.py [--city otaru] [--dry-run]
     python scripts/crawl_hokkaido_all.py  # 跑全部
"""
from __future__ import annotations

import asyncio, argparse, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from app.domains.catalog.crawlers.google_places import (
    fetch_pois_by_subcategory,
    fetch_hotels_by_tier,
    fetch_specialty_shops_sapporo,
)
from app.domains.catalog.upsert import upsert_entity

# 城市配置：(limit_per_poi_category, limit_per_hotel_tier, do_shops)
CITY_CONFIG = {
    # 中型城市
    "hakodate":    (15, 12, True),
    "otaru":       (15, 12, True),
    "asahikawa":   (15, 10, False),
    # 小城市
    "furano":      (8,  8,  False),
    "biei":        (8,  6,  False),
    "noboribetsu": (8,  8,  False),
    "toya":        (8,  8,  False),
    "abashiri":    (8,  6,  False),
    "kushiro":     (8,  8,  False),
    "niseko":      (8,  10, False),
}


async def crawl_city(session, city_code: str, poi_limit: int, hotel_limit: int,
                     do_shops: bool, dry_run: bool) -> dict:
    """爬取一个城市，返回统计"""
    stats = {"poi": 0, "hotel": 0, "shop": 0, "error": 0}

    # POI
    try:
        pois = await fetch_pois_by_subcategory(city_code, limit_per_category=poi_limit)
        if not dry_run:
            for poi in pois:
                try:
                    poi["trust_status"] = "unverified"
                    poi["data_tier"] = "A"
                    await upsert_entity(session, "poi", poi,
                                        google_place_id=poi.get("google_place_id"))
                    stats["poi"] += 1
                except Exception:
                    stats["error"] += 1
            await session.commit()
        else:
            stats["poi"] = len(pois)
    except Exception as e:
        print(f"  [{city_code}] POI fetch error: {e}")

    # Hotels
    try:
        hotels = await fetch_hotels_by_tier(city_code, limit_per_tier=hotel_limit)
        if not dry_run:
            for hotel in hotels:
                try:
                    hotel["trust_status"] = "unverified"
                    hotel["data_tier"] = "A"
                    await upsert_entity(session, "hotel", hotel,
                                        google_place_id=hotel.get("google_place_id"))
                    stats["hotel"] += 1
                except Exception:
                    stats["error"] += 1
            await session.commit()
        else:
            stats["hotel"] = len(hotels)
    except Exception as e:
        print(f"  [{city_code}] Hotel fetch error: {e}")

    # Specialty shops (only for medium cities)
    if do_shops:
        try:
            shops = await fetch_specialty_shops_sapporo(city_code, limit_per_category=10)
            if not dry_run:
                for shop in shops:
                    try:
                        shop["trust_status"] = "unverified"
                        shop["data_tier"] = "A"
                        await upsert_entity(session, "poi", shop,
                                            google_place_id=shop.get("google_place_id"))
                        stats["shop"] += 1
                    except Exception:
                        stats["error"] += 1
                await session.commit()
            else:
                stats["shop"] = len(shops)
        except Exception as e:
            print(f"  [{city_code}] Shop fetch error: {e}")

    return stats


async def get_current_counts(session) -> dict:
    """获取当前各城市实体数量"""
    r = await session.execute(text("""
        SELECT city_code, COUNT(*) FROM entity_base
        WHERE is_active=true AND city_code != 'sapporo'
        GROUP BY city_code ORDER BY city_code
    """))
    return {row[0]: row[1] for row in r.fetchall()}


async def main(target_cities: list, dry_run: bool = False) -> None:
    print(f"[FIX-4] Crawling {len(target_cities)} cities: {target_cities}")
    if dry_run:
        print("  [DRY RUN mode]")

    async with AsyncSessionLocal() as session:
        before = await get_current_counts(session)
        print(f"\nBefore: {before}")

        total_new = {"poi": 0, "hotel": 0, "shop": 0, "error": 0}

        for city_code in target_cities:
            if city_code not in CITY_CONFIG:
                print(f"  [{city_code}] Not in config, skipping")
                continue

            poi_limit, hotel_limit, do_shops = CITY_CONFIG[city_code]
            print(f"\n  [{city_code}] poi_limit={poi_limit}, hotel_limit={hotel_limit}, shops={do_shops}")

            stats = await crawl_city(session, city_code, poi_limit, hotel_limit,
                                     do_shops, dry_run)
            print(f"    -> poi={stats['poi']}, hotel={stats['hotel']}, shop={stats['shop']}, err={stats['error']}")

            for k in total_new:
                total_new[k] += stats[k]

            # 每城市之间休息 2 秒避免 API 限速
            await asyncio.sleep(2)

        if not dry_run:
            after = await get_current_counts(session)
            print(f"\nAfter:  {after}")

            # 更新 coverage counts
            print("\nUpdating coverage counts...")
            from scripts.fix_coverage_counts import main as update_coverage
            # 直接执行 SQL 更新（避免重新导入复杂度）
            await session.execute(text("""
                UPDATE city_data_coverage cdc
                SET current_count = (
                    SELECT COUNT(*) FROM entity_base e
                    WHERE e.city_code = cdc.city_code
                      AND e.entity_type = cdc.entity_type
                      AND e.is_active = true
                ),
                last_updated = NOW()
                WHERE sub_category = 'general'
            """))
            await session.commit()
            print("  Coverage counts updated for 'general' sub_category rows")

    if dry_run:
        print(f"\n[DRY RUN] Would have saved: poi={total_new['poi']}, hotel={total_new['hotel']}, shop={total_new['shop']}")
    else:
        print(f"\nFIX-4 DONE: poi={total_new['poi']}, hotel={total_new['hotel']}, shop={total_new['shop']}, errors={total_new['error']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", help="Single city or comma-separated list (default: all)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.city:
        cities = [c.strip() for c in args.city.split(",")]
    else:
        cities = list(CITY_CONFIG.keys())

    asyncio.run(main(cities, dry_run=args.dry_run))
