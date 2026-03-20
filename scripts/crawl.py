#!/usr/bin/env python3
"""
数据采集命令行工具

用法：
  # 采集单个城市（AI生成，立即可用）
  python scripts/crawl.py --city tokyo --force-ai

  # 采集单个城市（自动选择，有网用真实爬虫）
  python scripts/crawl.py --city tokyo

  # 只采集景点
  python scripts/crawl.py --city kyoto --pois-only --force-ai

  # 批量采集所有城市
  python scripts/crawl.py --all-cities --force-ai

  # 只测试不写库（dry-run）
  python scripts/crawl.py --city tokyo --dry-run --force-ai
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import os

# 把项目根目录加入 PATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


async def main(args: argparse.Namespace) -> None:
    from app.db.session import AsyncSessionLocal
    from app.domains.catalog.pipeline import (
        run_city_pipeline,
        run_all_cities,
        CITY_MAP,
    )
    from app.domains.catalog.ai_generator import (
        generate_pois, generate_restaurants, generate_hotels,
        POI_CATEGORIES, RESTAURANT_CUISINES,
    )

    # dry-run：只打印，不写库
    if args.dry_run:
        logger.info("=== DRY RUN 模式（只生成，不写入数据库）===")
        if args.city:
            if not args.restaurants_only and not args.hotels_only:
                for cat in list(POI_CATEGORIES.keys())[:2]:
                    pois = await generate_pois(args.city, cat, count=2)
                    print(f"\n--- {args.city} {cat} POIs ---")
                    print(json.dumps(pois, ensure_ascii=False, indent=2))
            if not args.pois_only and not args.hotels_only:
                cuisines = list(RESTAURANT_CUISINES.keys())[:2]
                for c in cuisines:
                    rests = await generate_restaurants(args.city, c, count=2)
                    print(f"\n--- {args.city} {c} Restaurants ---")
                    print(json.dumps(rests, ensure_ascii=False, indent=2))
        return

    # 正式写库
    async with AsyncSessionLocal() as session:
        try:
            if args.all_cities:
                cities = list(CITY_MAP.keys())
                logger.info(f"批量采集 {len(cities)} 个城市...")
                results = await run_all_cities(
                    session,
                    cities=cities,
                    sync_pois=not args.restaurants_only and not args.hotels_only,
                    sync_restaurants=not args.pois_only and not args.hotels_only,
                    sync_hotels=not args.pois_only and not args.restaurants_only,
                    force_ai=args.force_ai,
                    poi_count=args.poi_count,
                    restaurant_count=args.restaurant_count,
                    hotel_count=args.hotel_count,
                )
            else:
                city = args.city or "tokyo"
                logger.info(f"采集城市：{city}")
                results = [await run_city_pipeline(
                    session,
                    city_code=city,
                    sync_pois=not args.restaurants_only and not args.hotels_only,
                    sync_restaurants=not args.pois_only and not args.hotels_only,
                    sync_hotels=not args.pois_only and not args.restaurants_only,
                    force_ai=args.force_ai,
                    poi_count=args.poi_count,
                    restaurant_count=args.restaurant_count,
                    hotel_count=args.hotel_count,
                )]

            await session.commit()

            # 打印结果
            print("\n" + "="*50)
            print("采集完成！汇总：")
            for r in results:
                if "error" in r:
                    print(f"  ❌ {r.get('city', '?')}: {r['error']}")
                else:
                    print(
                        f"  ✅ {r['city']}"
                        f" [{r.get('mode','?')}]"
                        f" — 景点:{r['pois']}"
                        f" 餐厅:{r['restaurants']}"
                        f" 酒店:{r['hotels']}"
                    )
                    if r.get("errors"):
                        for e in r["errors"]:
                            print(f"     ⚠️  {e}")
            print("="*50)

        except Exception as e:
            await session.rollback()
            logger.error(f"采集失败: {e}")
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Japan Travel AI 数据采集工具")

    # 目标城市
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--city", type=str, help="城市代码，如 tokyo / osaka / kyoto")
    group.add_argument("--all-cities", action="store_true", help="采集所有城市")

    # 类型筛选
    type_group = parser.add_mutually_exclusive_group()
    type_group.add_argument("--pois-only", action="store_true", help="只采集景点")
    type_group.add_argument("--restaurants-only", action="store_true", help="只采集餐厅")
    type_group.add_argument("--hotels-only", action="store_true", help="只采集酒店")

    # 数量
    parser.add_argument("--poi-count", type=int, default=5, help="每类别景点数量（默认5）")
    parser.add_argument("--restaurant-count", type=int, default=5, help="每菜系餐厅数量（默认5）")
    parser.add_argument("--hotel-count", type=int, default=4, help="每档位酒店数量（默认4）")

    # 模式
    parser.add_argument("--force-ai", action="store_true", help="强制使用AI生成，跳过网络检查")
    parser.add_argument("--dry-run", action="store_true", help="只生成预览，不写入数据库")

    args = parser.parse_args()

    # 默认采集 tokyo
    if not args.city and not args.all_cities:
        args.city = "tokyo"

    asyncio.run(main(args))
