#!/usr/bin/env python3
"""
C3 Task: Tag generation from dimension scores

从 entity_review_signals.dimension_scores 自动推断标签，存入 entity_tags。
纯规则映射，不需要 AI 调用。

映射规则：
  queue_risk=high → long_queue
  payment_method=cash_only → cash_only
  child_friendly=great → family_friendly
  language_friendliness=english_ok → english_friendly
  photo_value=iconic → instagrammable
  weather_sensitivity=rain_ruins → weather_dependent
  bath_quality=exceptional → great_onsen
  breakfast_quality=highlight → great_breakfast
  等等
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── 维度 → 标签映射规则 ─────────────────────────────────────────────────────

TAG_RULES: List[Dict[str, Any]] = [
    # Restaurant
    {"dimension": "queue_risk", "value": "high", "tag": "long_queue", "category": "caution"},
    {"dimension": "queue_risk", "value": "medium", "tag": "may_queue", "category": "caution"},
    {"dimension": "payment_method", "value": "cash_only", "tag": "cash_only", "category": "practical"},
    {"dimension": "reservation_difficulty", "value": "hard", "tag": "reservation_needed", "category": "practical"},
    {"dimension": "reservation_difficulty", "value": "impossible", "tag": "reservation_essential", "category": "practical"},
    {"dimension": "language_friendliness", "value": "english_ok", "tag": "english_friendly", "category": "practical"},
    {"dimension": "language_friendliness", "value": "japanese_only", "tag": "japanese_only", "category": "caution"},
    {"dimension": "signature_dish_clarity", "value": "clear", "tag": "must_try_dish", "category": "highlight"},
    {"dimension": "value_perception", "value": "above", "tag": "great_value", "category": "highlight"},
    {"dimension": "value_perception", "value": "below", "tag": "overpriced", "category": "caution"},

    # POI
    {"dimension": "child_friendly", "value": "great", "tag": "family_friendly", "category": "audience"},
    {"dimension": "child_friendly", "value": "not_suitable", "tag": "adults_only", "category": "audience"},
    {"dimension": "photo_value", "value": "iconic", "tag": "instagrammable", "category": "highlight"},
    {"dimension": "photo_value", "value": "high", "tag": "photogenic", "category": "highlight"},
    {"dimension": "weather_sensitivity", "value": "rain_ruins", "tag": "weather_dependent", "category": "caution"},
    {"dimension": "weather_sensitivity", "value": "any", "tag": "all_weather", "category": "practical"},
    {"dimension": "physical_demand", "value": "demanding", "tag": "physically_demanding", "category": "caution"},
    {"dimension": "physical_demand", "value": "easy", "tag": "easy_access", "category": "practical"},
    {"dimension": "season_dependency", "value": "specific_season", "tag": "seasonal", "category": "caution"},
    {"dimension": "duration_flexibility", "value": "flexible", "tag": "flexible_schedule", "category": "practical"},

    # Hotel
    {"dimension": "bath_quality", "value": "exceptional", "tag": "great_onsen", "category": "highlight"},
    {"dimension": "bath_quality", "value": "good", "tag": "has_onsen", "category": "highlight"},
    {"dimension": "breakfast_quality", "value": "highlight", "tag": "great_breakfast", "category": "highlight"},
    {"dimension": "soundproofing", "value": "poor", "tag": "noise_issue", "category": "caution"},
    {"dimension": "location_convenience", "value": "excellent", "tag": "great_location", "category": "highlight"},
    {"dimension": "room_condition", "value": "excellent", "tag": "luxury_room", "category": "highlight"},
    {"dimension": "room_condition", "value": "dated", "tag": "dated_room", "category": "caution"},
]


def derive_tags(dimension_scores: dict) -> List[Dict[str, str]]:
    """从维度评分推导标签"""
    tags = []
    seen = set()

    for rule in TAG_RULES:
        dim_value = dimension_scores.get(rule["dimension"])
        if dim_value == rule["value"]:
            tag = rule["tag"]
            if tag not in seen:
                tags.append({"tag": tag, "category": rule["category"]})
                seen.add(tag)

    # best_for (hotel) → audience tags
    best_for = dimension_scores.get("best_for", [])
    if isinstance(best_for, list):
        for audience in best_for:
            tag = f"best_for_{audience}"
            if tag not in seen:
                tags.append({"tag": tag, "category": "audience"})
                seen.add(tag)

    return tags


async def main():
    """主流程"""
    from app.db.session import AsyncSessionLocal
    from sqlalchemy import text

    logger.info("=" * 60)
    logger.info("C3 Task: Tag generation from dimension scores")
    logger.info("=" * 60)

    async with AsyncSessionLocal() as session:
        # 获取所有有 dimension_scores 的实体
        result = await session.execute(
            text("""
                SELECT ers.entity_id, ers.dimension_scores, eb.entity_type
                FROM entity_review_signals ers
                JOIN entity_base eb ON eb.entity_id = ers.entity_id
                WHERE ers.dimension_scores IS NOT NULL
                  AND ers.rating_source = 'ai_dimension'
            """)
        )
        rows = result.fetchall()
        logger.info(f"Found {len(rows)} entities with dimension scores")

    tags_created = 0
    entities_tagged = 0

    async with AsyncSessionLocal() as session:
        async with session.begin():
            for entity_id, dim_scores, entity_type in rows:
                if not dim_scores:
                    continue

                scores = dim_scores if isinstance(dim_scores, dict) else json.loads(dim_scores)
                tags = derive_tags(scores)

                if not tags:
                    continue

                for tag_info in tags:
                    # 检查是否已存在
                    existing = await session.execute(
                        text("""
                            SELECT id FROM entity_tags
                            WHERE entity_id = :eid AND tag_value = :tv
                        """),
                        {"eid": str(entity_id), "tv": tag_info["tag"]}
                    )
                    if existing.fetchone():
                        continue

                    await session.execute(
                        text("""
                            INSERT INTO entity_tags (entity_id, tag_namespace, tag_value, source)
                            VALUES (:eid, :cat, :tv, 'ai_dimension')
                        """),
                        {
                            "eid": str(entity_id),
                            "cat": tag_info["category"],
                            "tv": tag_info["tag"],
                        }
                    )
                    tags_created += 1

                entities_tagged += 1

    logger.info(f"\nResults: {entities_tagged} entities tagged, {tags_created} new tags created")

    # 验证
    logger.info("\nVerification...")
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("""
                SELECT tag_value, COUNT(*) as cnt
                FROM entity_tags
                GROUP BY tag_value
                ORDER BY cnt DESC
                LIMIT 20
            """)
        )
        rows = result.fetchall()
        logger.info("Top tags:")
        for tag, cnt in rows:
            logger.info(f"  {tag}: {cnt}")

    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
