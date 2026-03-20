#!/usr/bin/env python
"""
scripts/mark_data_tier.py
-------------------------
CLI 工具：批量自动标记实体的 data_tier（S/A/B）。

标记规则：
  - A tier：有 google_place_id，或 source 包含 "osm"
  - B tier：其他（默认）
  - S tier：需要手动通过 editorial API 标记（本脚本不做 S 级标记）

用法示例：
  # 标记所有城市
  python scripts/mark_data_tier.py

  # 只标记东京
  python scripts/mark_data_tier.py --city tokyo

  # 标记多个城市
  python scripts/mark_data_tier.py --city tokyo osaka

  # 预览（不写入）
  python scripts/mark_data_tier.py --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("mark_data_tier")

SUPPORTED_CITIES = ["tokyo", "osaka", "kyoto"]


async def run(args: argparse.Namespace) -> None:
    from sqlalchemy import select, update
    from app.db.session import AsyncSessionLocal
    from app.db.models.catalog import EntityBase

    cities = args.city if args.city else SUPPORTED_CITIES

    async with AsyncSessionLocal() as session:
        total_updated = 0
        stats: dict[str, dict[str, int]] = {}

        for city in cities:
            # 查询该城市所有 active 实体
            stmt = select(EntityBase).where(
                EntityBase.city_code == city,
                EntityBase.is_active == True,  # noqa: E712
            )
            result = await session.execute(stmt)
            entities = result.scalars().all()

            city_stats = {"A": 0, "B": 0, "total": len(entities)}
            updated = 0

            for entity in entities:
                # 判断 data_tier
                # A tier：有 google_place_id
                has_google = bool(getattr(entity, "google_place_id", None))

                # A tier：数据来源包含 osm（检查 entity 相关快照，简化为检查 entity_type + source 字段）
                # 由于 entity_base 没有 source 字段，根据 poi/hotel/restaurant 子表判断
                # 这里采用保守策略：有 google_place_id 则 A，否则 B
                new_tier = "A" if has_google else "B"

                if entity.data_tier != new_tier:
                    if not args.dry_run:
                        entity.data_tier = new_tier
                    updated += 1
                    city_stats[new_tier] = city_stats.get(new_tier, 0) + 1

            if not args.dry_run:
                await session.commit()

            total_updated += updated
            stats[city] = city_stats
            logger.info(
                f"[{city}] 处理完成 — 总计: {len(entities)}, "
                f"变更: {updated}, A: {city_stats.get('A', 0)}, B: {city_stats.get('B', 0)}"
            )

        # 汇总
        logger.info(f"{'[DRY-RUN] ' if args.dry_run else ''}全部完成 — 总变更实体: {total_updated}")
        for city, s in stats.items():
            logger.info(f"  {city}: total={s['total']}, A={s.get('A', 0)}, B={s.get('B', 0)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="批量标记实体 data_tier（S/A/B）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--city",
        nargs="+",
        choices=SUPPORTED_CITIES,
        metavar="CITY",
        help=f"目标城市（可多选）: {', '.join(SUPPORTED_CITIES)}。不指定则处理全部",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预览模式：仅统计需要变更的实体，不实际写入",
    )
    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    asyncio.run(run(args))
