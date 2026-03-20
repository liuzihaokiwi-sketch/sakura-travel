#!/usr/bin/env python3
"""
guide_crawl.py — 第四层攻略站统一采集入口
==========================================
聚合 letsgojp / matcha / xiaohongshu 三个爬虫，
统一 CLI 接口，输出标准 JSON 到 data/raw/{source}/

用法示例:
  # 单个来源 + 单城市
  python scripts/guide_crawl.py --source letsgojp --city tokyo --limit 20

  # 单个来源 + 多城市
  python scripts/guide_crawl.py --source matcha --city tokyo --city osaka

  # 小红书按关键词
  python scripts/guide_crawl.py --source xiaohongshu --keyword "东京攻略" --limit 10

  # 采集所有来源的所有城市
  python scripts/guide_crawl.py --source all --city all

  # 只保存不打印
  python scripts/guide_crawl.py --source letsgojp --city kyoto --quiet

输出路径:
  data/raw/letsgojp/letsgojp_{city}_{ts}.json
  data/raw/matcha/matcha_{city}_{ts}.json
  data/xhs_raw/xhs_{city}_{ts}.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── 日志 ─────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("guide_crawl")

# ── 支持的来源 ─────────────────────────────────────────────────────────────────

SOURCES = ["letsgojp", "matcha", "xiaohongshu", "all"]
CITIES = ["tokyo", "osaka", "kyoto", "all"]


# ── 采集函数 ──────────────────────────────────────────────────────────────────

async def run_letsgojp(
    cities: List[str],
    pages: int = 5,
    limit: Optional[int] = None,
    save_json: bool = True,
) -> List[dict]:
    """运行樂吃購爬虫"""
    from scripts.crawlers.letsgojp import LetsGoJPCrawler

    async with LetsGoJPCrawler() as crawler:
        all_articles = []
        for city in cities:
            articles = await crawler.crawl_category(city=city, pages=pages)
            if limit:
                articles = articles[:limit]
            all_articles.extend(articles)

        if save_json and all_articles:
            crawler._save_json(all_articles, "_".join(cities))

        if not all_articles:
            print("\n⚠️  樂吃購：未采集到数据（站点可能已更改结构，请手动检查选择器）")
        else:
            crawler._print_summary(all_articles)

        return all_articles


async def run_matcha(
    cities: List[str],
    limit: int = 50,
    save_json: bool = True,
) -> List[dict]:
    """运行 MATCHA 爬虫"""
    from scripts.crawlers.matcha import MATCHACrawler

    async with MATCHACrawler() as crawler:
        all_articles = []
        for city in cities:
            articles = await crawler.crawl_by_city(city=city, limit=limit, save_json=False)
            all_articles.extend(articles)

        if save_json and all_articles:
            crawler._save_json(all_articles, "_".join(cities))

        if not all_articles:
            print("\n⚠️  MATCHA：未采集到数据（API 可能需要认证或 URL 已更改）")

        return all_articles


async def run_xiaohongshu(
    keywords: Optional[List[str]] = None,
    cities: Optional[List[str]] = None,
    limit: int = 10,
    pages: int = 2,
    save_json: bool = True,
) -> List[dict]:
    """运行小红书爬虫"""
    from scripts.crawlers.xiaohongshu import XiaohongshuCrawler

    async with XiaohongshuCrawler() as crawler:
        all_notes = []

        if keywords:
            # 按关键词搜索
            for kw in keywords:
                notes = await crawler.search_notes(kw, max_pages=pages)
                all_notes.extend(notes)
        elif cities:
            # 按城市搜索
            for city in cities:
                if city == "all":
                    for c in ["tokyo", "osaka", "kyoto"]:
                        notes = await crawler.crawl_by_city(
                            city_code=c, max_pages=pages, save_json=False
                        )
                        all_notes.extend(notes)
                else:
                    notes = await crawler.crawl_by_city(
                        city_code=city, max_pages=pages, save_json=False
                    )
                    all_notes.extend(notes)
        else:
            # 默认：东京攻略
            notes = await crawler.search_notes("东京攻略", max_pages=pages)
            all_notes.extend(notes)

        # 去重 + 限制数量
        seen: set = set()
        unique = []
        for n in all_notes:
            if n["title"] not in seen:
                seen.add(n["title"])
                unique.append(n)

        unique = unique[:limit] if limit else unique

        if save_json and unique:
            from pathlib import Path
            from datetime import datetime
            out_dir = Path("data/xhs_raw")
            out_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            label = "_".join(keywords[:2]) if keywords else "_".join(cities or ["general"])
            fp = out_dir / f"xhs_{label[:30]}_{ts}.json"
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(
                    {"meta": {"total": len(unique), "source": "xiaohongshu"},
                     "notes": unique},
                    f, ensure_ascii=False, indent=2,
                )
            print(f"💾 小红书：已保存 {len(unique)} 条 → {fp}")

        if unique:
            print(f"\n📕 小红书: {len(unique)} 条笔记")
            for n in sorted(unique, key=lambda x: x.get("likes", 0), reverse=True)[:5]:
                print(f"  ❤️{n.get('likes',0):>5d}  {n['title'][:45]}")
        else:
            print("\n⚠️  小红书：未采集到数据（反爬较强，建议手动验证 Playwright 环境）")

        return unique


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="第四层攻略站采集工具（樂吃購 / MATCHA / 小红书）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--source", "-s",
        choices=SOURCES,
        default="letsgojp",
        help="数据来源 (default: letsgojp)",
    )
    parser.add_argument(
        "--city", "-c",
        action="append",
        dest="cities",
        default=None,
        metavar="CITY",
        help="城市代码，可多次指定 (tokyo/osaka/kyoto/all)",
    )
    parser.add_argument(
        "--keyword", "-k",
        action="append",
        dest="keywords",
        default=None,
        metavar="KEYWORD",
        help="搜索关键词（仅 xiaohongshu），可多次指定",
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=None,
        help="最多采集条数（默认不限）",
    )
    parser.add_argument(
        "--pages", "-p",
        type=int,
        default=3,
        help="每个分类/关键词的页数 (default: 3)",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="不保存 JSON 文件（只打印摘要）",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="减少输出",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="开启 DEBUG 日志",
    )

    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    cities = args.cities or ["tokyo"]
    save_json = not args.no_save
    limit = args.limit or 50

    source = args.source
    print(f"\n{'='*60}")
    print(f"  🗺️  攻略站采集 | source={source} | cities={cities}")
    print(f"{'='*60}\n")

    if source == "letsgojp":
        await run_letsgojp(
            cities=cities,
            pages=args.pages,
            limit=args.limit,
            save_json=save_json,
        )

    elif source == "matcha":
        await run_matcha(
            cities=cities,
            limit=limit,
            save_json=save_json,
        )

    elif source == "xiaohongshu":
        await run_xiaohongshu(
            keywords=args.keywords,
            cities=cities if not args.keywords else None,
            limit=limit,
            pages=args.pages,
            save_json=save_json,
        )

    elif source == "all":
        print("── 1/3 樂吃購 ──────────────────────────────")
        await run_letsgojp(cities=cities, pages=args.pages, save_json=save_json)

        print("\n── 2/3 MATCHA ──────────────────────────────")
        await run_matcha(cities=cities, limit=limit, save_json=save_json)

        print("\n── 3/3 小红书 ──────────────────────────────")
        await run_xiaohongshu(
            cities=cities, limit=limit, pages=args.pages, save_json=save_json
        )

    print(f"\n{'='*60}")
    print("  ✅ 采集完成")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
