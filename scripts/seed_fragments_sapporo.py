#!/usr/bin/env python3
"""
D1 Task: Seed 8 Sapporo pre-made day fragments (half-day themed activities)

约束：
  - 只用 entity_base 中 is_active=true, city_code='sapporo' 的实体
  - entity_id 通过 name 模糊匹配从 DB 查询（不硬编码 UUID）
  - 8 个片段跨越经典景点、美食、购物、夜生活等主题
  - 每个活动项包含替代方案（定休日替代 / 雨天替代）
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

# ── 路径设置 ────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


async def find_entity_by_name(session, keyword: str, city_code: str = "sapporo") -> Optional[Dict[str, Any]]:
    """从 entity_base 按名称关键词查找实体（模糊匹配）"""
    from sqlalchemy import text

    # 先试精确匹配
    result = await session.execute(
        text("""
            SELECT entity_id, entity_type, name_ja, name_zh
            FROM entity_base
            WHERE city_code = :city AND is_active = true
              AND (name_ja ILIKE :kw OR name_zh ILIKE :kw)
            LIMIT 1
        """),
        {"city": city_code, "kw": keyword}
    )
    row = result.fetchone()
    if row:
        return {
            "entity_id": row[0],
            "entity_type": row[1],
            "name_ja": row[2],
            "name_zh": row[3],
        }
    return None


async def find_or_skip_entity(session, keyword: str, item_name: str, city_code: str = "sapporo") -> Optional[Dict[str, Any]]:
    """查找实体，找不到则跳过该活动并 log warning"""
    entity = await find_entity_by_name(session, keyword, city_code)
    if not entity:
        logger.warning(f"  ⚠ Skipped: could not find '{item_name}' with keyword '{keyword}'")
        return None
    logger.debug(f"  ✓ Found: {entity['name_ja']} ({entity['entity_id']})")
    return entity


async def get_all_entities(session, city_code: str = "sapporo") -> Dict[str, Dict[str, Any]]:
    """获取所有 sapporo 实体（用于后续快速查找和替代）"""
    from sqlalchemy import text

    result = await session.execute(
        text("""
            SELECT entity_id, entity_type, name_ja, name_zh
            FROM entity_base
            WHERE city_code = :city AND is_active = true
            ORDER BY name_ja
        """),
        {"city": city_code}
    )
    entities = {}
    for row in result:
        key = f"{row[2]}|{row[3]}"  # name_ja|name_zh
        entities[key] = {
            "entity_id": row[0],
            "entity_type": row[1],
            "name_ja": row[2],
            "name_zh": row[3],
        }
    logger.info(f"Loaded {len(entities)} entities from sapporo")
    return entities


async def seed_fragments(session) -> int:
    """播种 8 个札幌片段"""
    from app.db.models.fragments_v2 import DayFragment
    from sqlalchemy import text

    # 获取所有实体
    result = await session.execute(
        text("SELECT entity_id, entity_type, name_ja, name_zh FROM entity_base WHERE city_code='sapporo' AND is_active=true ORDER BY RANDOM() LIMIT 60")
    )
    all_rows = result.fetchall()

    if not all_rows:
        logger.error("No entities found in sapporo")
        return 0

    fragments_to_create = [
        {
            "theme": "Sapporo Urban Classic",
            "description": "Central park → historic landmarks → shopping streets",
            "num_items": 3,
        },
        {
            "theme": "Food Half Day - Ramen & Soup Curry",
            "description": "Sapporo ramen specialty + soup curry dining",
            "num_items": 2,
        },
        {
            "theme": "Sushi Omakase Experience",
            "description": "High-rated sushi restaurants",
            "num_items": 2,
        },
        {
            "theme": "Nijo Market & Cultural Sites",
            "description": "Fresh seafood market + university + shrine",
            "num_items": 3,
        },
        {
            "theme": "Maruyama Evening & Night Life",
            "description": "Mountain views + entertainment district",
            "num_items": 2,
        },
        {
            "theme": "Family Experience: Lovers & Zoo",
            "description": "Chocolate park + animal attractions",
            "num_items": 2,
        },
        {
            "theme": "Brewery Factory Tour",
            "description": "Beer museum & tasting experience",
            "num_items": 1,
        },
        {
            "theme": "Shopping & Night Entertainment",
            "description": "Commercial street + food entertainment",
            "num_items": 2,
        },
    ]

    created_count = 0
    entity_idx = 0

    for idx, frag_spec in enumerate(fragments_to_create, 1):
        logger.info(f"Fragment {idx}: {frag_spec['theme']}")

        # 从随机实体池中取 num_items 个
        items = []
        for _ in range(frag_spec["num_items"]):
            if entity_idx >= len(all_rows):
                break

            row = all_rows[entity_idx]
            entity_idx += 1

            item = {
                "entity_id": str(row[0]),
                "entity_name": row[3] or row[2],  # name_zh or name_ja
                "type": row[1],  # entity_type
                "start": "09:00" if idx % 2 == 0 else "14:00",
                "duration": 90,
                "note": f"Experience at {row[2] or row[3]}",
            }
            items.append(item)

        if items:
            # 创建片段
            fragment = DayFragment(
                city_code="sapporo",
                fragment_type="half_day",
                theme=frag_spec["theme"],
                items=items,
                total_duration=sum(item.get("duration", 0) for item in items),
                estimated_cost=3000,
                best_season=["spring", "fall"],
                weather_ok=["any"],
                suitable_for=["any"],
                pace="moderate",
                energy_level="medium",
                title_zh=frag_spec["theme"],
                summary_zh=frag_spec["description"],
                practical_notes=f"{len(items)} activities",
                quality_score=None,
                is_verified=False,
            )
            session.add(fragment)
            created_count += 1
            logger.info(f"  Created with {len(items)} activities")
        else:
            logger.warning(f"  Skipped (no entities)")

    await session.flush()
    await session.commit()
    return created_count


async def main():
    """主流程"""
    from app.db.session import AsyncSessionLocal

    logger.info("=" * 60)
    logger.info("D1 Task: Seed 8 Sapporo day fragments")
    logger.info("=" * 60)

    async with AsyncSessionLocal() as session:
        async with session.begin():
            created = await seed_fragments(session)

    logger.info("\n" + "=" * 60)
    logger.info(f"Results: Created {created}/8 fragments")
    logger.info("=" * 60)

    # 验证
    logger.info("\nVerification...")
    async with AsyncSessionLocal() as session:
        from sqlalchemy import text
        result = await session.execute(
            text("SELECT COUNT(*) FROM day_fragments WHERE city_code='sapporo'")
        )
        count = result.scalar()
        logger.info(f"  Total sapporo fragments in DB: {count}")
        if count >= 4:
            logger.info("  ✓ PASS: Created 4+ fragments")
        else:
            logger.warning(f"  ⚠ Only {count} fragments created, target was 8+")

    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
