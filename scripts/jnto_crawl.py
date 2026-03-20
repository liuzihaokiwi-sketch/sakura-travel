#!/usr/bin/env python3
"""
JNTO / GO TOKYO 官方旅游数据采集 CLI
=====================================

用法:
  # 全量采集 (目的地+景点+活动+指南)
  python scripts/jnto_crawl.py

  # 只抓目的地骨架
  python scripts/jnto_crawl.py --only destinations

  # 只抓景点 (限制10个)
  python scripts/jnto_crawl.py --only spots --limit 10

  # 只抓活动
  python scripts/jnto_crawl.py --only events

  # 只抓季节指南
  python scripts/jnto_crawl.py --only guides
"""

import argparse
import asyncio
import logging
import sys

sys.path.insert(0, ".")

from scripts.crawlers.jnto import JNTOCrawler


def main():
    parser = argparse.ArgumentParser(description="JNTO / GO TOKYO 官方数据采集")
    parser.add_argument(
        "--only",
        choices=["destinations", "spots", "events", "guides"],
        help="只抓取指定类型",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="景点最大数量 (默认 50)",
    )
    parser.add_argument(
        "--output",
        default="data/raw/official",
        help="输出目录",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="显示调试日志",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(message)s",
    )

    async def run():
        async with JNTOCrawler(output_dir=args.output) as crawler:
            if args.only == "destinations":
                await crawler.crawl_jnto_destinations()
            elif args.only == "spots":
                await crawler.crawl_gotokyo_spots(limit=args.limit)
            elif args.only == "events":
                await crawler.crawl_gotokyo_events()
            elif args.only == "guides":
                await crawler.crawl_gotokyo_guides()
            else:
                await crawler.crawl_all(spots_limit=args.limit)

    asyncio.run(run())


if __name__ == "__main__":
    main()
