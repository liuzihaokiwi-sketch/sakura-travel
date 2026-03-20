#!/usr/bin/env python3
"""
预计算三城市 Top50 实体对的交通时间，写入 route_matrix_cache。

用法:
    python scripts/prebuild_route_matrix.py --cities tokyo osaka kyoto --top 50
    python scripts/prebuild_route_matrix.py --cities tokyo --top 30 --mode transit
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path

# 确保项目根目录在 path 中
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.db.models.catalog import EntityBase
from app.db.models.derived import EntityScore
from app.domains.planning.route_matrix import get_travel_time, TravelMode

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

DEFAULT_CITIES = ["tokyo", "osaka", "kyoto"]
DEFAULT_TOP = 50


async def get_top_entities(session, city_code: str, top_n: int) -> list:
    """获取城市评分最高的 top_n 个 POI 实体。"""
    stmt = (
        select(EntityBase)
        .join(EntityScore, EntityScore.entity_id == EntityBase.entity_id, isouter=True)
        .where(
            EntityBase.city_code == city_code,
            EntityBase.entity_type == "poi",
        )
        .order_by(EntityScore.final_score.desc().nulls_last())
        .limit(top_n)
    )
    rows = (await session.execute(stmt)).scalars().all()
    return rows


async def prebuild_city(
    session,
    city_code: str,
    top_n: int,
    mode: TravelMode,
) -> dict:
    """预计算单个城市的交通矩阵。"""
    entities = await get_top_entities(session, city_code, top_n)
    if not entities:
        logger.warning(f"[{city_code}] 未找到实体，跳过")
        return {"city": city_code, "entities": 0, "pairs": 0, "cached": 0, "failed": 0}

    entity_ids = [e.entity_id for e in entities]
    total_pairs = len(entity_ids) * (len(entity_ids) - 1) // 2
    logger.info(f"[{city_code}] {len(entity_ids)} 个实体，共 {total_pairs} 对，模式={mode}")

    cached = 0
    failed = 0

    for i, origin_id in enumerate(entity_ids):
        for dest_id in entity_ids[i + 1:]:
            try:
                result = await get_travel_time(session, origin_id, dest_id, mode)
                if result["source"] in ("db", "redis"):
                    cached += 1
                else:
                    cached += 1  # 新计算后已写入缓存
                    logger.debug(
                        f"  {origin_id} → {dest_id}: "
                        f"{result['duration_min']}min [{result['source']}]"
                    )
            except Exception as e:
                failed += 1
                logger.warning(f"  计算失败 {origin_id} → {dest_id}: {e}")

            # 避免 API 限速
            await asyncio.sleep(0.05)

        if (i + 1) % 10 == 0:
            await session.commit()
            logger.info(f"[{city_code}] 进度: {i + 1}/{len(entity_ids)} 起点已处理")

    await session.commit()

    return {
        "city": city_code,
        "entities": len(entity_ids),
        "pairs": total_pairs,
        "cached": cached,
        "failed": failed,
    }


async def main(cities: list[str], top_n: int, mode: TravelMode) -> None:
    t0 = time.time()

    summary = []
    async with AsyncSessionLocal() as session:
        for city in cities:
            logger.info(f"\n{'='*50}")
            logger.info(f"开始预计算城市: {city}")
            stats = await prebuild_city(session, city, top_n, mode)
            summary.append(stats)

    elapsed = time.time() - t0
    logger.info(f"\n{'='*50}")
    logger.info(f"预计算完成，耗时 {elapsed:.1f}s")
    logger.info(f"{'城市':<12} {'实体数':>6} {'对数':>8} {'成功':>6} {'失败':>6}")
    logger.info("-" * 45)
    for s in summary:
        logger.info(
            f"{s['city']:<12} {s['entities']:>6} {s['pairs']:>8} "
            f"{s['cached']:>6} {s['failed']:>6}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="预计算交通矩阵缓存")
    parser.add_argument(
        "--cities",
        nargs="+",
        default=DEFAULT_CITIES,
        help=f"城市代码列表，默认: {DEFAULT_CITIES}",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=DEFAULT_TOP,
        help=f"每城市取 Top N 实体，默认: {DEFAULT_TOP}",
    )
    parser.add_argument(
        "--mode",
        choices=["transit", "walking", "driving"],
        default="transit",
        help="交通模式，默认: transit",
    )
    args = parser.parse_args()
    asyncio.run(main(args.cities, args.top, args.mode))
