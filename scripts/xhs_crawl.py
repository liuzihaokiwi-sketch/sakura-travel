#!/usr/bin/env python3
"""
小红书旅游攻略采集 CLI (Playwright)
用法:
  python scripts/xhs_crawl.py --city tokyo             # 采集东京攻略
  python scripts/xhs_crawl.py --city general            # 通用日本攻略
  python scripts/xhs_crawl.py --keyword "日本特价机票"   # 自定义关键词
  python scripts/xhs_crawl.py --city tokyo osaka kyoto  # 多城市
  python scripts/xhs_crawl.py --headed                   # 显示浏览器
"""
from __future__ import annotations
import argparse, asyncio, logging, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

async def main(args):
    from scripts.crawlers.xiaohongshu import XiaohongshuCrawler
    async with XiaohongshuCrawler(
        output_dir=args.output_dir,
        headless=not args.headed,
    ) as crawler:
        if args.keyword:
            for kw in args.keyword:
                await crawler.search_notes(kw, max_pages=args.pages)
        else:
            cities = args.city or ["general"]
            for city in cities:
                await crawler.crawl_by_city(city, max_pages=args.pages)

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="小红书攻略采集")
    p.add_argument("--city", nargs="+", help="城市: tokyo/osaka/kyoto/general")
    p.add_argument("--keyword", nargs="+", help="自定义搜索关键词")
    p.add_argument("--pages", type=int, default=2)
    p.add_argument("--output-dir", default="data/xhs_raw")
    p.add_argument("--headed", action="store_true")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()
    if args.verbose: logging.getLogger().setLevel(logging.DEBUG)
    asyncio.run(main(args))
