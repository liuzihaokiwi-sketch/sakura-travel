#!/usr/bin/env python3
"""
Tabelog 餐厅数据采集 CLI
========================

用法：
  # 采集东京的寿司店（列表页+详情页，前3页）
  python scripts/tabelog_crawl.py --city tokyo --cuisine sushi --pages 3

  # 只采集列表页（更快，不抓详情）
  python scripts/tabelog_crawl.py --city tokyo --cuisine sushi --no-detail

  # 采集大阪所有菜系（默认每种3页）
  python scripts/tabelog_crawl.py --city osaka

  # 采集多种菜系
  python scripts/tabelog_crawl.py --city kyoto --cuisine sushi ramen kaiseki

  # 批量采集多个城市
  python scripts/tabelog_crawl.py --city tokyo osaka kyoto --cuisine sushi ramen

  # 导出 CSV（默认同时输出 JSON）
  python scripts/tabelog_crawl.py --city tokyo --cuisine sushi --csv

  # 使用代理
  python scripts/tabelog_crawl.py --city tokyo --proxy http://user:pass@host:port

  # 调整延迟和页数
  python scripts/tabelog_crawl.py --city tokyo --delay 3 8 --pages 5

  # 导入到数据库（需要配置 .env）
  python scripts/tabelog_crawl.py --city tokyo --cuisine sushi --write-db

支持的城市：
  tokyo, osaka, kyoto, nara, sapporo, fukuoka, hiroshima,
  naha, kanazawa, hakone, kamakura, kobe, nagoya, yokohama, sendai

支持的菜系：
  sushi, ramen, kaiseki, tempura, yakitori, wagyu, izakaya,
  udon, soba, seafood, tonkatsu, curry, unagi, okonomiyaki, cafe
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys

# 把项目根目录加入 PATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


async def main(args: argparse.Namespace) -> None:
    from scripts.crawlers.tabelog import (
        TabelogCrawler,
        TABELOG_AREA_MAP,
        TABELOG_CUISINE_MAP,
    )

    # 列出支持的城市/菜系
    if args.list:
        print("\n🏙️  支持的城市:")
        for code, info in TABELOG_AREA_MAP.items():
            print(f"  {code:12s}  {info['name_ja']}")
        print("\n🍽️  支持的菜系:")
        for code, info in TABELOG_CUISINE_MAP.items():
            print(f"  {code:14s}  {info['name_zh']} ({info['name_ja']})")
        return

    # 准备参数
    cities = args.city or ["tokyo"]
    cuisines = args.cuisine or None  # None = 全部菜系
    proxies = [args.proxy] if args.proxy else []

    # 创建爬虫实例
    crawler_kwargs = {
        "fetch_detail": not args.no_detail,
        "sort_by": args.sort,
        "output_dir": args.output_dir,
        "delay_range": tuple(args.delay),
        "max_retries": args.retries,
        "max_concurrent": 1,
        "proxies": proxies,
    }

    total_restaurants = []

    async with TabelogCrawler(**crawler_kwargs) as crawler:
        for city in cities:
            if city not in TABELOG_AREA_MAP:
                logger.error(f"❌ 未知城市: {city}，用 --list 查看支持的城市")
                continue

            restaurants = await crawler.crawl_city(
                city_code=city,
                cuisines=cuisines,
                max_pages=args.pages,
                max_items_per_cuisine=args.max_items,
                save_json=True,
            )
            total_restaurants.extend(restaurants)

            # 导出 CSV
            if args.csv and restaurants:
                from scripts.crawlers.tabelog import TabelogCrawler as TC
                csv_path = os.path.join(args.output_dir, f"tabelog_{city}.csv")
                TC.save_csv(restaurants, csv_path)

    # 可选：写入数据库
    if args.write_db and total_restaurants:
        await _write_to_db(total_restaurants)

    # 打印总结
    print("\n" + "=" * 60)
    print(f"🎉 采集完成！总计 {len(total_restaurants)} 家餐厅")
    print(f"📊 {crawler.stats.summary()}")
    print("=" * 60)


async def _write_to_db(restaurants: list) -> None:
    """将采集数据写入项目数据库"""
    try:
        from app.db.session import AsyncSessionLocal
        from app.domains.catalog.pipeline import _write_restaurant

        logger.info(f"📝 正在写入数据库... ({len(restaurants)} 条)")
        written = 0
        async with AsyncSessionLocal() as session:
            for item in restaurants:
                # 转换字段名以匹配 pipeline 期望
                db_item = {
                    "name_ja": item.get("name_ja", ""),
                    "name_zh": item.get("name_zh", ""),
                    "name_en": item.get("name_en", ""),
                    "city_code": item.get("city_code", ""),
                    "tabelog_id": item.get("tabelog_id"),
                    "tabelog_url": item.get("tabelog_url"),
                    "tabelog_score": item.get("tabelog_score"),
                    "tabelog_review_count": item.get("tabelog_review_count"),
                    "price_lunch_jpy": item.get("price_lunch_jpy"),
                    "price_dinner_jpy": item.get("price_dinner_jpy"),
                    "cuisine_type": item.get("cuisine_query") or item.get("cuisine_raw"),
                    "cuisine_raw": item.get("cuisine_raw"),
                    "district": item.get("district"),
                    "lat": item.get("lat"),
                    "lng": item.get("lng"),
                    "address_ja": item.get("address_ja"),
                    "opening_hours_json": item.get("opening_hours_json"),
                    "seating_count": item.get("seating_count"),
                    "requires_reservation": item.get("requires_reservation", False),
                    "has_english_menu": item.get("has_english_menu", False),
                    "source": "tabelog",
                }
                eid = await _write_restaurant(session, db_item)
                if eid:
                    written += 1

            await session.commit()
            logger.info(f"✅ 数据库写入完成: {written}/{len(restaurants)} 条")

    except ImportError:
        logger.error("❌ 无法导入数据库模块，请确认 .env 已配置且依赖已安装")
    except Exception as e:
        logger.error(f"❌ 数据库写入失败: {e}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tabelog 餐厅数据采集工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # 目标
    parser.add_argument(
        "--city", nargs="+", type=str,
        help="城市代码，可指定多个（默认 tokyo）",
    )
    parser.add_argument(
        "--cuisine", nargs="+", type=str,
        help="菜系代码，可指定多个（默认全部）",
    )

    # 爬取参数
    parser.add_argument(
        "--pages", type=int, default=3,
        help="每种菜系最大翻页数（默认 3）",
    )
    parser.add_argument(
        "--max-items", type=int, default=60,
        help="每种菜系最大采集数（默认 60）",
    )
    parser.add_argument(
        "--no-detail", action="store_true",
        help="不抓取详情页（更快但数据不完整）",
    )
    parser.add_argument(
        "--sort", type=str, default="score",
        choices=["score", "review", "new"],
        help="排序方式（默认 score）",
    )

    # 反爬参数
    parser.add_argument(
        "--delay", type=float, nargs=2, default=[2.0, 5.0],
        metavar=("MIN", "MAX"),
        help="请求间随机延迟范围/秒（默认 2.0 5.0）",
    )
    parser.add_argument(
        "--retries", type=int, default=3,
        help="请求失败重试次数（默认 3）",
    )
    parser.add_argument(
        "--proxy", type=str, default="",
        help="HTTP 代理地址，如 http://user:pass@host:port",
    )

    # 输出
    parser.add_argument(
        "--output-dir", type=str, default="data/tabelog_raw",
        help="输出目录（默认 data/tabelog_raw）",
    )
    parser.add_argument(
        "--csv", action="store_true",
        help="同时导出 CSV 文件",
    )
    parser.add_argument(
        "--write-db", action="store_true",
        help="写入项目数据库（需要 .env 配置）",
    )

    # 工具
    parser.add_argument(
        "--list", action="store_true",
        help="列出支持的城市和菜系",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="详细日志输出",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    asyncio.run(main(args))
