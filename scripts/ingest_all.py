#!/usr/bin/env python3
"""
D3.1  Phase 0 收尾 + 数据入库 一键脚本
用法: python scripts/ingest_all.py [--hotels] [--tabelog] [--jnto] [--events] [--experiences] [--all]

功能:
  1. 调用 pipeline.py 中的 ingest_* 函数批量写入 DB
  2. 可单独指定类型，默认 --all
  3. 打印汇总结果
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import AsyncSessionLocal
from app.domains.catalog.pipeline import (
    ingest_hotel_crawl,
    ingest_tabelog_crawl,
    ingest_jnto_spots,
    ingest_events,
    ingest_experiences,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def run(args: argparse.Namespace) -> None:
    do_all = args.all or not any([
        args.hotels, args.tabelog, args.jnto, args.events, args.experiences
    ])

    results = {}

    async with AsyncSessionLocal() as session:
        async with session.begin():

            if do_all or args.hotels:
                logger.info("=== D1.1 酒店数据入库 ===")
                stats = await ingest_hotel_crawl(session)
                results["hotels"] = stats

            if do_all or args.tabelog:
                logger.info("=== D1.2 Tabelog 餐厅入库 ===")
                stats = await ingest_tabelog_crawl(session)
                results["tabelog"] = stats

            if do_all or args.jnto:
                logger.info("=== D1.3 JNTO/GO TOKYO 景点入库 ===")
                stats = await ingest_jnto_spots(session)
                results["jnto"] = stats

            if do_all or args.events:
                logger.info("=== D1.4a Events 入库 ===")
                stats = await ingest_events(session)
                results["events"] = stats

            if do_all or args.experiences:
                logger.info("=== D1.4b Experiences 入库 ===")
                stats = await ingest_experiences(session)
                results["experiences"] = stats

    # 汇总
    print("\n" + "=" * 50)
    print("📊 入库汇总结果")
    print("=" * 50)
    total_inserted = 0
    total_skipped = 0
    for name, stats in results.items():
        inserted = stats.get("inserted", 0)
        skipped = stats.get("skipped", 0)
        errors = stats.get("errors", [])
        total_inserted += inserted
        total_skipped += skipped
        status = "✅" if not errors else "⚠️"
        print(f"{status} {name:15s}: 写入 {inserted:4d} 条  跳过 {skipped:4d} 条  错误 {len(errors)} 条")
        if errors:
            for e in errors[:3]:
                print(f"    ❌ {e}")

    print("-" * 50)
    print(f"   总计: 写入 {total_inserted} 条  跳过 {total_skipped} 条")
    print("=" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="批量写入爬虫原始数据到 DB")
    parser.add_argument("--all",          action="store_true", help="写入所有类型（默认）")
    parser.add_argument("--hotels",       action="store_true", help="仅写入酒店")
    parser.add_argument("--tabelog",      action="store_true", help="仅写入 Tabelog 餐厅")
    parser.add_argument("--jnto",         action="store_true", help="仅写入 JNTO 景点")
    parser.add_argument("--events",       action="store_true", help="仅写入活动/节日")
    parser.add_argument("--experiences",  action="store_true", help="仅写入体验活动")
    args = parser.parse_args()
    asyncio.run(run(args))
