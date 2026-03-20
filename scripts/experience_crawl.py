#!/usr/bin/env python3
"""
experience_crawl.py — 活动体验爬虫 CLI 入口
============================================
用法示例：

  # 爬取东京 KKday (快速测试)
  python scripts/experience_crawl.py --city tokyo --source kkday --limit 10

  # 爬取所有平台、所有城市
  python scripts/experience_crawl.py --all

  # 只爬特定平台
  python scripts/experience_crawl.py --city osaka --source klook --pages 2

  # 多城市 + 多平台
  python scripts/experience_crawl.py --city tokyo,osaka --source kkday,klook
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# 确保项目根目录在 PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.crawlers.experiences import ExperienceCrawler

# ── 日志配置 ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("experience_crawl")

# ── 输出目录 ──────────────────────────────────────────────────────────────────

OUTPUT_DIR = Path("data/experiences_raw")


def _save_results(results: list, tag: str) -> Path:
    """保存爬取结果到 JSON 文件"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = OUTPUT_DIR / f"experiences_{tag}_{ts}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return filename


def _print_summary(results: list) -> None:
    """打印结果摘要"""
    if not results:
        print("⚠️  没有采集到任何数据")
        return

    # 按平台统计
    by_source: dict = {}
    by_city: dict = {}
    for item in results:
        src = item.get("source", "unknown")
        city = item.get("city", "unknown")
        by_source[src] = by_source.get(src, 0) + 1
        by_city[city] = by_city.get(city, 0) + 1

    print(f"\n{'='*50}")
    print(f"📊 采集结果汇总  共 {len(results)} 条")
    print(f"{'='*50}")

    print("\n按平台:")
    for src, cnt in sorted(by_source.items()):
        print(f"  {src:12s}: {cnt} 条")

    print("\n按城市:")
    for city, cnt in sorted(by_city.items()):
        print(f"  {city:12s}: {cnt} 条")

    # 展示前几条样本
    print(f"\n📝 样本数据 (前 3 条):")
    for item in results[:3]:
        price = f"¥{item['price_cny']:.0f}" if item.get("price_cny") else "价格未知"
        rating = f"⭐{item['rating']}" if item.get("rating") else ""
        print(f"  [{item['source']}] {item['name'][:40]} | {price} {rating}")
    print()


# ── 主逻辑 ────────────────────────────────────────────────────────────────────

async def run(args: argparse.Namespace) -> None:
    async with ExperienceCrawler(
        delay_range=(1.0, 2.5) if args.fast else (1.5, 3.5),
        max_retries=2 if args.fast else 3,
    ) as crawler:

        # 解析参数
        if args.all:
            cities = ["tokyo", "osaka", "kyoto"]
            sources = ["kkday", "klook", "veltra", "rakuten"]
        else:
            cities = [c.strip() for c in args.city.split(",")]
            sources = [s.strip() for s in args.source.split(",")]

        pages = args.pages

        logger.info(f"目标城市: {cities}")
        logger.info(f"目标平台: {sources}")
        logger.info(f"每平台页数: {pages}")

        # 爬取
        results = await crawler.crawl_all(
            cities=cities,
            sources=sources,
            pages=pages,
        )

        # 限制条数（用于测试）
        if args.limit and args.limit > 0:
            results = results[: args.limit]
            logger.info(f"--limit {args.limit}: 截取前 {len(results)} 条")

        # 打印统计
        _print_summary(results)

        # 保存文件
        if results and not args.dry_run:
            tag = "_".join(cities) if len(cities) <= 3 else "multi"
            output_path = _save_results(results, tag)
            print(f"💾 已保存到: {output_path}")
        elif args.dry_run:
            print("🔍 dry-run 模式，不保存文件")

        # 打印爬虫统计
        print(crawler.stats.summary())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="活动体验爬虫 — 爬取 KKday / Klook / VELTRA / Rakuten",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--city",
        default="tokyo",
        help="城市，逗号分隔，如 tokyo,osaka,kyoto (默认: tokyo)",
    )
    parser.add_argument(
        "--source",
        default="kkday,klook,veltra,rakuten",
        help="平台，逗号分隔: kkday,klook,veltra,rakuten (默认: 全部)",
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=3,
        help="每个城市+平台最多爬取的页数 (默认: 3)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="限制最终输出条数，0=不限 (用于快速测试)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="爬取所有平台、所有城市",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="快速模式（减少请求延迟，适合测试）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只爬取，不保存文件",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细日志",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    asyncio.run(run(args))


if __name__ == "__main__":
    main()
