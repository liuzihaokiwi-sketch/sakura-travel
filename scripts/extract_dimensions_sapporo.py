#!/usr/bin/env python3
"""
C2 Task: Dimension extraction + summary generation from Google Places reviews

从 source_snapshots 读取评论原文，用 AI 按实体类型提取维度评分，
生成 why_go / practical_tip / skip_if 一句话摘要。

结果存入：
  - entity_review_signals.dimension_scores (JSONB)
  - entity_descriptions (多行，不同 description_type)

使用阿里云 DashScope API (deepseek-v3.2)，低并发逐条处理。
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── 维度定义 ─────────────────────────────────────────────────────────────────

RESTAURANT_DIMENSIONS = {
    "signature_dish_clarity": {
        "desc": "Is there a must-order signature dish?",
        "values": ["clear", "vague", "none"],
    },
    "queue_risk": {
        "desc": "How likely is queuing?",
        "values": ["none", "low", "medium", "high"],
    },
    "reservation_difficulty": {
        "desc": "How hard to get a seat?",
        "values": ["walk_in", "easy", "hard", "impossible"],
    },
    "language_friendliness": {
        "desc": "How friendly for non-Japanese speakers?",
        "values": ["japanese_only", "menu_ok", "english_ok"],
    },
    "payment_method": {
        "desc": "Payment options",
        "values": ["cash_only", "card_ok"],
    },
    "value_perception": {
        "desc": "Is it worth the price?",
        "values": ["below", "fair", "above"],
    },
}

POI_DIMENSIONS = {
    "best_timing": {
        "desc": "Best time of day to visit (free text, e.g. 'morning 8-9am')",
        "values": "free_text",
    },
    "weather_sensitivity": {
        "desc": "How much does weather affect the experience?",
        "values": ["any", "prefer_clear", "rain_ruins"],
    },
    "physical_demand": {
        "desc": "Physical effort required",
        "values": ["easy", "moderate", "demanding"],
    },
    "photo_value": {
        "desc": "How photogenic is it?",
        "values": ["low", "medium", "high", "iconic"],
    },
    "crowd_pattern": {
        "desc": "Crowd pattern (free text, e.g. 'tour groups 10-14')",
        "values": "free_text",
    },
    "duration_flexibility": {
        "desc": "Can you adjust visit time?",
        "values": ["fixed", "flexible"],
    },
    "child_friendly": {
        "desc": "Suitable for children?",
        "values": ["not_suitable", "ok", "great"],
    },
    "season_dependency": {
        "desc": "Does it depend on specific season?",
        "values": ["any_season", "specific_season"],
    },
}

HOTEL_DIMENSIONS = {
    "location_convenience": {
        "desc": "How convenient is the location?",
        "values": ["remote", "ok", "convenient", "excellent"],
    },
    "room_condition": {
        "desc": "Room quality",
        "values": ["dated", "acceptable", "good", "excellent"],
    },
    "bath_quality": {
        "desc": "Onsen/bath quality",
        "values": ["none", "basic", "good", "exceptional"],
    },
    "breakfast_quality": {
        "desc": "Breakfast quality",
        "values": ["none", "basic", "good", "highlight"],
    },
    "soundproofing": {
        "desc": "Noise insulation",
        "values": ["poor", "acceptable", "good"],
    },
    "value_perception": {
        "desc": "Value for money",
        "values": ["below", "fair", "above"],
    },
    "best_for": {
        "desc": "Best suited traveler types (list)",
        "values": "list",
    },
}


def get_dimensions_for_type(entity_type: str) -> dict:
    if entity_type == "restaurant":
        return RESTAURANT_DIMENSIONS
    elif entity_type == "poi":
        return POI_DIMENSIONS
    elif entity_type == "hotel":
        return HOTEL_DIMENSIONS
    return {}


def build_extraction_prompt(entity_name: str, entity_type: str, reviews: List[dict]) -> str:
    """构建维度提取 prompt"""
    dims = get_dimensions_for_type(entity_type)
    if not dims:
        return ""

    # 拼接评论文本
    review_texts = []
    for i, r in enumerate(reviews[:5], 1):
        text = r.get("text", "").strip()
        rating = r.get("rating", "?")
        if len(text) < 5:
            continue
        review_texts.append(f"Review {i} (rating: {rating}/5): {text[:500]}")

    if not review_texts:
        return ""

    reviews_block = "\n".join(review_texts)

    # 构建维度说明
    dim_lines = []
    for key, info in dims.items():
        if info["values"] == "free_text":
            dim_lines.append(f'  "{key}": "<short text>",  // {info["desc"]}')
        elif info["values"] == "list":
            dim_lines.append(f'  "{key}": ["<item>", ...],  // {info["desc"]}')
        else:
            vals = " | ".join(info["values"])
            dim_lines.append(f'  "{key}": "<{vals}>",  // {info["desc"]}')

    dims_block = "\n".join(dim_lines)

    return f"""You are analyzing Google reviews for a Japanese {entity_type} named "{entity_name}".

REVIEWS:
{reviews_block}

Based ONLY on the reviews above, extract dimension scores and generate summaries.
If a dimension cannot be determined from the reviews, use "unknown".
Filter out reviews shorter than 5 characters or pure emotional reactions.
Negative observations need 2+ people mentioning to be reliable.

Respond in JSON format ONLY (no markdown, no explanation):
{{
  "dimensions": {{
{dims_block}
  }},
  "summaries": {{
    "why_go": "<One sentence in Chinese: why visit this place, based on reviews>",
    "practical_tip": "<One sentence in Chinese: practical tip from reviews>",
    "skip_if": "<One sentence in Chinese: skip this if...>"
  }}
}}"""


async def call_ai_extract(prompt: str) -> Optional[dict]:
    """调用 AI 提取维度"""
    try:
        from app.core.ai_cache import cached_ai_call
        from app.core.config import settings

        model = getattr(settings, "ai_model", None) or os.getenv("AI_MODEL", "deepseek-v3.2")

        result = await cached_ai_call(
            prompt=prompt,
            model=model,
            system_prompt="You are a structured data extractor. Output valid JSON only.",
            temperature=0.1,
            max_tokens=1500,
            response_format={"type": "json_object"},
        )

        if not result:
            return None

        # 清理可能的 markdown 包装
        text = result.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse error: {e}")
        return None
    except Exception as e:
        logger.error(f"AI call error: {e}")
        return None


async def save_dimension_scores(session, entity_id, entity_type: str, dimensions: dict):
    """保存维度到 entity_review_signals"""
    from sqlalchemy import text

    # upsert: 查找已有记录或创建新的
    result = await session.execute(
        text("""
            SELECT id FROM entity_review_signals
            WHERE entity_id = :eid AND rating_source = 'ai_dimension'
        """),
        {"eid": str(entity_id)}
    )
    existing = result.fetchone()

    if existing:
        await session.execute(
            text("""
                UPDATE entity_review_signals
                SET dimension_scores = :dims, updated_at = NOW()
                WHERE id = :rid
            """),
            {"dims": json.dumps(dimensions), "rid": existing[0]}
        )
    else:
        await session.execute(
            text("""
                INSERT INTO entity_review_signals
                    (entity_id, rating_source, dimension_scores, confidence_score)
                VALUES (:eid, 'ai_dimension', :dims, 0.70)
            """),
            {"eid": str(entity_id), "dims": json.dumps(dimensions)}
        )


async def save_summaries(session, entity_id, summaries: dict):
    """保存摘要到 entity_descriptions"""
    from sqlalchemy import text

    type_map = {
        "why_go": "review_why_go",
        "practical_tip": "review_practical_tip",
        "skip_if": "review_skip_if",
    }

    for key, desc_type in type_map.items():
        content = summaries.get(key, "").strip()
        if not content or content == "unknown":
            continue

        # 检查是否已有
        result = await session.execute(
            text("""
                SELECT id FROM entity_descriptions
                WHERE entity_id = :eid AND description_type = :dtype AND source_kind = 'ai_generated'
            """),
            {"eid": str(entity_id), "dtype": desc_type}
        )
        existing = result.fetchone()

        if existing:
            await session.execute(
                text("""
                    UPDATE entity_descriptions
                    SET content = :content, updated_at = NOW()
                    WHERE id = :did
                """),
                {"content": content, "did": existing[0]}
            )
        else:
            await session.execute(
                text("""
                    INSERT INTO entity_descriptions
                        (entity_id, source_kind, description_type, content, language, confidence_score, needs_review, is_active)
                    VALUES (:eid, 'ai_generated', :dtype, :content, 'zh', 0.70, true, true)
                """),
                {"eid": str(entity_id), "dtype": desc_type, "content": content}
            )


async def main():
    """主流程"""
    from app.db.session import AsyncSessionLocal
    from sqlalchemy import text

    logger.info("=" * 60)
    logger.info("C2 Task: Dimension extraction + summary generation")
    logger.info("=" * 60)

    async with AsyncSessionLocal() as session:
        # 获取所有 review_batch 快照
        result = await session.execute(
            text("""
                SELECT ss.object_id, ss.raw_payload,
                       eb.entity_type, eb.name_ja, eb.name_zh
                FROM source_snapshots ss
                JOIN entity_base eb ON eb.entity_id = ss.object_id::uuid
                WHERE ss.source_name = 'google_reviews'
                  AND ss.object_type = 'review_batch'
                  AND eb.is_active = true
                ORDER BY eb.entity_type, eb.name_ja
            """)
        )
        snapshots = result.fetchall()
        logger.info(f"Found {len(snapshots)} review snapshots to process")

    # 逐条处理（低并发，避免限速）
    processed = 0
    errors = 0

    for i, row in enumerate(snapshots):
        entity_id = row[0]
        raw_payload = row[1] if isinstance(row[1], dict) else json.loads(row[1])
        entity_type = row[2]
        entity_name = row[3] or row[4] or "Unknown"

        reviews = raw_payload.get("reviews", [])
        if not reviews:
            logger.warning(f"  [{i+1}] No reviews for {entity_name}, skipping")
            continue

        # 构建 prompt
        prompt = build_extraction_prompt(entity_name, entity_type, reviews)
        if not prompt:
            continue

        logger.info(f"  [{i+1}/{len(snapshots)}] Processing {entity_type}: {entity_name}")

        # 调用 AI
        result = await call_ai_extract(prompt)
        if not result:
            errors += 1
            logger.warning(f"  ✗ AI extraction failed for {entity_name}")
            continue

        dimensions = result.get("dimensions", {})
        summaries = result.get("summaries", {})

        # 保存到数据库
        async with AsyncSessionLocal() as session:
            async with session.begin():
                await save_dimension_scores(session, entity_id, entity_type, dimensions)
                await save_summaries(session, entity_id, summaries)

        processed += 1

        if (i + 1) % 10 == 0:
            logger.info(f"  Progress: {i+1}/{len(snapshots)} ({processed} OK, {errors} errors)")

        # 限速：每次调用间隔 1 秒
        await asyncio.sleep(1)

    logger.info("\n" + "=" * 60)
    logger.info(f"Results: {processed} entities processed, {errors} errors")
    logger.info("=" * 60)

    # 验证
    logger.info("\nVerification...")
    async with AsyncSessionLocal() as session:
        r1 = await session.execute(
            text("SELECT COUNT(*) FROM entity_review_signals WHERE dimension_scores IS NOT NULL")
        )
        dim_count = r1.scalar()

        r2 = await session.execute(
            text("SELECT description_type, COUNT(*) FROM entity_descriptions WHERE source_kind='ai_generated' GROUP BY description_type")
        )
        desc_rows = r2.fetchall()

        logger.info(f"  Entities with dimension scores: {dim_count}")
        for dtype, cnt in desc_rows:
            logger.info(f"  {dtype}: {cnt} descriptions")

    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
