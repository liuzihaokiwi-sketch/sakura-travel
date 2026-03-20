#!/usr/bin/env python3
"""
日本活动/节庆/樱花/红叶 数据采集 CLI
用法:
  python scripts/event_crawl.py                        # 未来6个月全量
  python scripts/event_crawl.py --months 3             # 未来3个月
  python scripts/event_crawl.py --sakura-only          # 只抓樱花
  python scripts/event_crawl.py --koyo-only            # 只抓红叶
"""
from __future__ import annotations
import argparse, asyncio, logging, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

async def main(args):
    from scripts.crawlers.events import EventCrawler
    async with EventCrawler(output_dir=args.output_dir) as crawler:
        if args.sakura_only:
            await crawler.crawl_sakura_forecast()
        elif args.koyo_only:
            await crawler.crawl_koyo_forecast()
        else:
            await crawler.crawl_all(months_ahead=args.months)

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="日本活动采集")
    p.add_argument("--months", type=int, default=6)
    p.add_argument("--sakura-only", action="store_true")
    p.add_argument("--koyo-only", action="store_true")
    p.add_argument("--output-dir", default="data/events_raw")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()
    if args.verbose: logging.getLogger().setLevel(logging.DEBUG)
    asyncio.run(main(args))
