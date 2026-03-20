#!/usr/bin/env python3
"""
酒店数据采集 CLI (Playwright)
==============================
四大平台一键采集：Booking.com / 携程 / Agoda / Jalan

用法:
  # 采集东京所有平台
  python scripts/hotel_crawl.py --city tokyo

  # 只用 Booking + 携程
  python scripts/hotel_crawl.py --city tokyo --platform booking ctrip

  # 采集多个城市
  python scripts/hotel_crawl.py --city tokyo osaka kyoto

  # 调整入住日期和住几晚
  python scripts/hotel_crawl.py --city tokyo --checkin-offset 45 --nights 3

  # 每个平台抓 3 页
  python scripts/hotel_crawl.py --city tokyo --pages 3

  # 显示浏览器（调试用）
  python scripts/hotel_crawl.py --city tokyo --headed

依赖:
  pip install playwright && python -m playwright install chromium

支持城市:
  tokyo, osaka, kyoto, nara, hakone, sapporo, fukuoka,
  okinawa, kamakura, kanazawa, kobe, nagoya
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)


async def main(args: argparse.Namespace) -> None:
    from scripts.crawlers.hotels import HotelCrawler, CITY_CONFIG

    if args.list:
        print("\n🏙️  支持的城市:")
        for code, cfg in CITY_CONFIG.items():
            print(f"  {code:12s}  {cfg['name_zh']} ({cfg['name_ja']})")
        print("\n🏨 支持的平台: booking, ctrip, agoda, jalan")
        return

    cities = args.city or ["tokyo"]
    platforms = args.platform if args.platform != ["all"] else ["booking", "ctrip", "agoda", "jalan"]

    async with HotelCrawler(
        platforms=platforms,
        check_in_offset_days=args.checkin_offset,
        nights=args.nights,
        output_dir=args.output_dir,
        headless=not args.headed,
        delay_range=tuple(args.delay),
        proxy=args.proxy or None,
    ) as crawler:
        for city in cities:
            if city not in CITY_CONFIG:
                print(f"❌ 未知城市: {city}，用 --list 查看")
                continue
            await crawler.crawl_city(city, max_pages=args.pages)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="多平台酒店数据采集（Playwright）",
    )
    parser.add_argument("--city", nargs="+", help="城市代码")
    parser.add_argument("--platform", nargs="+", default=["all"],
                        help="平台: booking / ctrip / agoda / jalan / all")
    parser.add_argument("--pages", type=int, default=2, help="每平台翻页数")
    parser.add_argument("--checkin-offset", type=int, default=30, help="入住日距今天数")
    parser.add_argument("--nights", type=int, default=2, help="住几晚")
    parser.add_argument("--delay", type=float, nargs=2, default=[2.0, 4.0])
    parser.add_argument("--output-dir", default="data/hotels_raw")
    parser.add_argument("--headed", action="store_true", help="显示浏览器窗口")
    parser.add_argument("--proxy", type=str, help="代理地址")
    parser.add_argument("--list", action="store_true", help="列出支持城市")
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    asyncio.run(main(args))
