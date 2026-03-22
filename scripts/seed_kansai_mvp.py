"""
seed_kansai_mvp.py — 一键执行关西 MVP 种子数据

按正确顺序执行：
  1. seed_kansai_circle     — 城市圈 + 活动簇 + 酒店住法预设
  2. seed_kansai_corridors  — 走廊 + 走廊别名
  3. seed_kansai_entities   — 实体 + 子表 + 角色映射

执行：
    cd D:/projects/projects/travel-ai
    python scripts/seed_kansai_mvp.py
"""
from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)


async def main():
    logger.info("=" * 60)
    logger.info("  关西 MVP 种子数据 — 一键执行")
    logger.info("=" * 60)

    # Step 1: 城市圈 + 活动簇 + 住法预设
    logger.info("\n▶ [1/3] 城市圈 / 活动簇 / 酒店住法预设")
    from scripts.seed_kansai_circle import seed as seed_circles
    await seed_circles()

    # Step 2: 走廊 + 走廊别名
    logger.info("\n▶ [2/3] 走廊 / 走廊别名")
    from scripts.seed_kansai_corridors import seed as seed_corridors
    await seed_corridors()

    # Step 3: 实体 + 子表 + 角色映射
    logger.info("\n▶ [3/3] 实体 / POI / 酒店 / 餐厅 / 角色映射")
    from scripts.seed_kansai_entities import seed as seed_entities
    await seed_entities()

    logger.info("\n" + "=" * 60)
    logger.info("  ✅ 关西 MVP 种子数据全部写入完成！")
    logger.info("=" * 60)
    logger.info("")
    logger.info("数据覆盖范围:")
    logger.info("  • 1 个城市圈 (kansai_classic_circle)")
    logger.info("  • 10 个活动簇 (S=4, A=4, B=2)")
    logger.info("  • 11 条走廊 (京都 6 + 大阪 4 + 奈良 1)")
    logger.info("  • ~24 个实体 (13 POI + 4 酒店 + 7 餐厅)")
    logger.info("  • 3 套酒店住法预设")
    logger.info("  • ~24 条角色映射 (circle_entity_roles)")
    logger.info("")
    logger.info("下一步: python scripts/prebuild_route_matrix.py --city kyoto osaka nara")


if __name__ == "__main__":
    asyncio.run(main())
