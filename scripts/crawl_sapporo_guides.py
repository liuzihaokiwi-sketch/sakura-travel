"""
B4: 攻略网站扫描 — 札幌
爬取 letsgojp.cn / gltjp.com / uu-hokkaido.in 的札幌页面
提取被提及的地点名称，存入 discovery_candidates 表

运行：python scripts/crawl_sapporo_guides.py [--dry-run]
"""
from __future__ import annotations

import asyncio
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.db.session import AsyncSessionLocal
from app.domains.catalog.crawlers.guide_scraper import (
    scrape_city_guides,
    upsert_discovery_candidates,
)


async def main(dry_run: bool = False) -> None:
    city_code = "sapporo"
    print(f"[B4] Guide scraper — city: {city_code}")

    source_results = await scrape_city_guides(city_code, delay=2.0)

    # Summary
    total = sum(len(names) for names in source_results.values())
    print(f"\nExtracted names by source:")
    for source, names in source_results.items():
        print(f"  {source}: {len(names)} names")
    print(f"  Total unique per source: {total}")

    if dry_run:
        # Show some samples
        for source, names in source_results.items():
            print(f"\n  {source} samples: {names[:10]}")
        print("\n[DRY RUN] No data stored")
        return

    async with AsyncSessionLocal() as session:
        new_count, updated_count = await upsert_discovery_candidates(
            session, city_code, source_results
        )

    print(f"\nDiscovery candidates: new={new_count}, updated={updated_count}")

    # Final count
    from sqlalchemy import text
    async with AsyncSessionLocal() as session:
        r = await session.execute(text("""
            SELECT source_count, COUNT(*) FROM discovery_candidates
            WHERE city_code = 'sapporo'
            GROUP BY source_count
            ORDER BY source_count DESC
        """))
        print("\nDiscovery candidates by source_count:")
        for row in r.fetchall():
            print(f"  source_count={row[0]}: {row[1]} places")

    print("\nB4 DONE")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
