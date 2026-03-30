"""
B3: Japan Guide 景点爬虫 — 北海道各城市
爬取景点名、JG评级（1-3）、用户评分、描述
与 entity_base 匹配，存入 entity_source_scores

运行：python scripts/crawl_japan_guide.py [--city sapporo] [--dry-run]
"""
from __future__ import annotations

import asyncio
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.db.session import AsyncSessionLocal
from app.domains.catalog.crawlers.japan_guide import (
    fetch_attractions,
    match_and_store_scores,
    JAPAN_GUIDE_PAGES,
)

# 可爬取的城市列表（排除 _hokkaido 概览页）
CRAWLABLE_CITIES = [c for c in JAPAN_GUIDE_PAGES if not c.startswith("_")]


async def crawl_city(session, city_code: str, dry_run: bool) -> tuple[int, int, int]:
    """爬取一个城市，返回 (fetched, matched, unmatched)"""
    attractions = await fetch_attractions(city_code, delay=2.0)
    print(f"  {city_code}: fetched {len(attractions)} attractions")

    if dry_run or not attractions:
        return len(attractions), 0, 0

    matched, unmatched = await match_and_store_scores(session, attractions, city_code)
    print(f"  {city_code}: matched={matched}, unmatched={unmatched}")
    return len(attractions), matched, unmatched


async def main(city: str = "sapporo", dry_run: bool = False) -> None:
    cities = CRAWLABLE_CITIES if city == "all" else [city]

    print(f"[B3] Japan Guide crawler — cities: {cities}")

    total_matched = 0
    total_unmatched = 0

    async with AsyncSessionLocal() as session:
        for city_code in cities:
            fetched, matched, unmatched = await crawl_city(session, city_code, dry_run)
            total_matched += matched
            total_unmatched += unmatched

    if dry_run:
        print(f"\n[DRY RUN] No data stored")
    else:
        print(f"\nB3 DONE: matched={total_matched}, unmatched={total_unmatched}")

    # Verify
    if not dry_run:
        async with AsyncSessionLocal() as session:
            from sqlalchemy import text
            r = await session.execute(text(
                "SELECT COUNT(*) FROM entity_source_scores WHERE source_name='japan_guide'"
            ))
            count = r.scalar()
            print(f"entity_source_scores[japan_guide] = {count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", default="sapporo",
                        help="City code or 'all' for all Hokkaido cities")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(city=args.city, dry_run=args.dry_run))
