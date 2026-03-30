#!/usr/bin/env python3
"""
C1 Task: 为札幌 top 100 实体采集 Google Places 评论原文

目标：
  - 从 entity_base 中查出 city_code='sapporo' 的 top 100 实体（按评分排序）
  - 每个实体通过 Google Places Place Details API 获取评论（最多 5 条）
  - 存入 source_snapshots 表（source_name='google_reviews', object_type='review_batch'）
  - 验证：SELECT COUNT(DISTINCT object_id) FROM source_snapshots WHERE object_type='review_batch' → 80+

数据来源：
  - Google Places Place Details API（需要 google_place_id）
  - Tabelog 用 tabelog_score 作为餐厅评分

约束：
  - 1 秒/请求间隔
  - 每日上限 100 条（脚本级）
  - 无 AI 生成内容
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

# ── 路径设置（必须在任何 app 导入前） ──────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# 脚本级速率控制
SCRIPT_DAILY_LIMIT = 100
REQUEST_DELAY_SEC = 1.0


async def get_top_entities(session) -> List[Dict[str, Any]]:
    """
    从 entity_base 查出 sapporo 的 top 100 实体（跨类型按评分排序）。
    优先级：pois.google_rating DESC，hotels.google_rating DESC，
    restaurants.tabelog_score DESC。
    """
    from sqlalchemy import text

    query = text("""
        WITH poi_ranked AS (
            SELECT
                e.entity_id, e.entity_type, e.name_ja, e.name_zh, e.google_place_id,
                p.google_rating as score,
                1 as type_order
            FROM entity_base e
            JOIN pois p ON p.entity_id = e.entity_id
            WHERE e.city_code = 'sapporo'
              AND e.is_active = true
              AND e.trust_status != 'rejected'
              AND e.google_place_id IS NOT NULL
              AND p.google_rating IS NOT NULL
        ),
        hotel_ranked AS (
            SELECT
                e.entity_id, e.entity_type, e.name_ja, e.name_zh, e.google_place_id,
                h.google_rating as score,
                2 as type_order
            FROM entity_base e
            JOIN hotels h ON h.entity_id = e.entity_id
            WHERE e.city_code = 'sapporo'
              AND e.is_active = true
              AND e.trust_status != 'rejected'
              AND e.google_place_id IS NOT NULL
              AND h.google_rating IS NOT NULL
        ),
        restaurant_ranked AS (
            SELECT
                e.entity_id, e.entity_type, e.name_ja, e.name_zh, e.google_place_id,
                COALESCE(r.tabelog_score, 0) as score,
                3 as type_order
            FROM entity_base e
            LEFT JOIN restaurants r ON r.entity_id = e.entity_id
            WHERE e.city_code = 'sapporo'
              AND e.is_active = true
              AND e.trust_status != 'rejected'
              AND e.google_place_id IS NOT NULL
        )
        SELECT entity_id, entity_type, name_ja, name_zh, google_place_id, score, type_order
        FROM (
            SELECT * FROM poi_ranked
            UNION ALL
            SELECT * FROM hotel_ranked
            UNION ALL
            SELECT * FROM restaurant_ranked
        ) AS combined
        ORDER BY type_order, score DESC, entity_id
        LIMIT 100
    """)

    result = await session.execute(query)
    rows = result.fetchall()

    entities = []
    for row in rows:
        entities.append({
            "entity_id": row[0],
            "entity_type": row[1],
            "name_ja": row[2],
            "name_zh": row[3],
            "google_place_id": row[4],
            "score": row[5],
        })

    return entities


async def check_snapshot_exists(session, entity_id: UUID) -> bool:
    """检查是否已有 google_reviews 快照"""
    from sqlalchemy import select, text

    query = text("""
        SELECT 1 FROM source_snapshots
        WHERE source_name = 'google_reviews'
          AND object_type = 'review_batch'
          AND object_id = :object_id
        LIMIT 1
    """)

    result = await session.execute(query, {"object_id": str(entity_id)})
    return result.scalar() is not None


async def collect_and_save_reviews(
    session, entity: Dict[str, Any], api_call_count: List[int]
) -> int:
    """
    为一个实体调 Place Details API，保存评论到 source_snapshots。
    返回采集到的评论数。
    """
    from app.domains.catalog.crawlers.google_places import fetch_place_details
    from app.core.snapshots import record_snapshot

    entity_id = entity["entity_id"]
    place_id = entity["google_place_id"]

    # 防重
    if await check_snapshot_exists(session, entity_id):
        logger.debug("Snapshot already exists for entity_id=%s", entity_id)
        return 0

    # API 调用
    if api_call_count[0] >= SCRIPT_DAILY_LIMIT:
        logger.warning("Daily limit (%d) reached, stopping", SCRIPT_DAILY_LIMIT)
        return -1

    logger.debug("Fetching reviews for %s (place_id=%s)", entity["name_ja"], place_id)
    try:
        place_details = await fetch_place_details(place_id)
    except Exception as e:
        logger.warning("fetch_place_details failed for %s: %s", entity["name_ja"], e)
        return 0

    api_call_count[0] += 1

    if not place_details:
        logger.debug("No place details returned for %s", entity["name_ja"])
        return 0

    reviews = place_details.get("reviews", [])
    if not reviews:
        logger.debug("No reviews for %s", entity["name_ja"])
        return 0

    # 构建 raw_payload
    raw_payload = {
        "entity_id": str(entity_id),
        "entity_name": entity.get("name_zh") or entity.get("name_ja"),
        "entity_type": entity["entity_type"],
        "place_id": place_id,
        "reviews_count": len(reviews),
        "reviews": [
            {
                "author_name": r.get("author_name"),
                "text": r.get("text"),
                "rating": r.get("rating"),
                "time": r.get("time"),
                "relative_time_description": r.get("relative_time_description"),
                "language": r.get("language"),
            }
            for r in reviews
        ],
        "fetched_at": datetime.utcnow().isoformat(),
    }

    # 写入 source_snapshots
    try:
        await record_snapshot(
            session=session,
            source_name="google_reviews",
            object_type="review_batch",
            object_id=str(entity_id),
            raw_payload=raw_payload,
            expires_in_days=90,
        )
        await session.flush()
        logger.info(
            "✓ Saved %d reviews for %s",
            len(reviews),
            entity.get("name_zh") or entity.get("name_ja"),
        )
        return len(reviews)
    except Exception as e:
        logger.error("Error saving snapshot for entity_id=%s: %s", entity_id, e)
        return 0


async def main():
    """主流程"""
    from app.db.session import AsyncSessionLocal

    logger.info("=" * 60)
    logger.info("C1 Task: Collect Google Places reviews for Sapporo top 100")
    logger.info("=" * 60)

    api_call_count = [0]
    reviews_collected = 0
    entities_succeeded = 0
    entities_failed = []

    async with AsyncSessionLocal() as session:
        try:
            # 步骤 1: 查询 top 100 实体
            async with session.begin():
                logger.info("Step 1: Fetching top 100 entities from sapporo...")
                entities = await get_top_entities(session)
                logger.info("Found %d entities", len(entities))

            if not entities:
                logger.error("No entities found!")
                return

            # 步骤 2: 逐个采集评论
            logger.info("Step 2: Collecting reviews...")
            for i, entity in enumerate(entities):
                if api_call_count[0] >= SCRIPT_DAILY_LIMIT:
                    logger.warning("Daily limit reached, stopping at entity %d/%d", i, len(entities))
                    break

                async with session.begin():
                    result = await collect_and_save_reviews(session, entity, api_call_count)
                    if result > 0:
                        reviews_collected += result
                        entities_succeeded += 1
                    elif result < 0:
                        break
                    else:
                        entities_failed.append(entity["entity_id"])

                    # 每 10 条 log 一次
                    if (i + 1) % 10 == 0:
                        logger.info("Checkpoint: processed entity %d/%d", i + 1, len(entities))

                # 请求间隔
                if i < len(entities) - 1:
                    await asyncio.sleep(REQUEST_DELAY_SEC)

        except Exception as e:
            logger.error("Fatal error: %s", e, exc_info=True)
            raise

    # 统计和验证
    logger.info("\n" + "=" * 60)
    logger.info("Results Summary:")
    logger.info("  API calls made: %d/%d", api_call_count[0], SCRIPT_DAILY_LIMIT)
    logger.info("  Reviews collected: %d", reviews_collected)
    logger.info("  Entities with reviews: %d", entities_succeeded)
    logger.info("  Entities without reviews: %d", len(entities_failed))

    # 验证
    logger.info("\nStep 3: Verification...")
    from sqlalchemy import text
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text(
                "SELECT COUNT(DISTINCT object_id) FROM source_snapshots "
                "WHERE object_type='review_batch' AND source_name='google_reviews'"
            )
        )
        distinct_count = result.scalar()
        logger.info(f"  Distinct entities with review snapshots: {distinct_count}")

        if distinct_count >= 80:
            logger.info("✅ PASS: Collected from 80+ entities (threshold met)")
        else:
            logger.warning(f"⚠️  WARNING: Only {distinct_count} entities, target is 80+")

    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
