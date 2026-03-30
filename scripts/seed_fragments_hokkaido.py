#!/usr/bin/env python3
"""
D2 Task: Seed day fragments for other Hokkaido cities

创建 15-20 个片段覆盖：
  小樽: 港町漫步半日、寿司美食
  函馆: 夜景全日、五棱郭+朝市
  富良野/美瑛: 花田自驾（夏）
  旭川: 旭山动物园+拉面村
  登别: 温泉一日
  洞爷湖: 火山温泉

每个城市 2-3 个片段，实体从 entity_base 查询。
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from typing import Any, Dict, List, Optional
from uuid import UUID

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


CITY_FRAGMENTS = [
    # 小樽
    {
        "city_code": "otaru",
        "theme": "Otaru Canal & Glass Town",
        "title_zh": "小樽运河·玻璃之城半日",
        "summary_zh": "运河散步 → 北一硝子馆 → 音乐盒堂 → 六花亭甜品",
        "fragment_type": "half_day",
        "num_items": 3,
        "best_season": ["spring", "summer", "fall"],
        "suitable_for": ["couple", "family"],
    },
    {
        "city_code": "otaru",
        "theme": "Otaru Sushi Street",
        "title_zh": "小樽寿司美食半日",
        "summary_zh": "寿司屋通午餐 → 三角市场海鲜 → 堺町商店街甜品",
        "fragment_type": "half_day",
        "num_items": 2,
        "best_season": ["any"],
        "suitable_for": ["couple", "foodie"],
    },
    # 函馆
    {
        "city_code": "hakodate",
        "theme": "Hakodate Night View & Bay Area",
        "title_zh": "函馆夜景·红砖仓库全日",
        "summary_zh": "金森红砖仓库 → 元町教堂群 → 函馆山缆车看夜景",
        "fragment_type": "full_day",
        "num_items": 3,
        "best_season": ["any"],
        "suitable_for": ["couple", "any"],
    },
    {
        "city_code": "hakodate",
        "theme": "Goryokaku & Morning Market",
        "title_zh": "五棱郭+函馆朝市半日",
        "summary_zh": "函馆朝市早餐 → 五棱郭塔展望 → 五棱郭公园散步",
        "fragment_type": "half_day",
        "num_items": 2,
        "best_season": ["spring", "summer"],
        "suitable_for": ["any"],
    },
    # 富良野
    {
        "city_code": "furano",
        "theme": "Furano Lavender Fields",
        "title_zh": "富良野薰衣草花田半日",
        "summary_zh": "富田农场薰衣草 → 中富良野花畑 → 薰衣草冰淇淋",
        "fragment_type": "half_day",
        "num_items": 2,
        "best_season": ["summer"],
        "weather_ok": ["prefer_clear"],
        "suitable_for": ["couple", "family"],
    },
    # 美瑛
    {
        "city_code": "biei",
        "theme": "Biei Patchwork Road Drive",
        "title_zh": "美瑛拼布之路自驾半日",
        "summary_zh": "青池 → 四季彩之丘 → 拼布之路展望台",
        "fragment_type": "half_day",
        "num_items": 2,
        "best_season": ["summer", "fall"],
        "weather_ok": ["prefer_clear"],
        "suitable_for": ["couple", "family"],
    },
    {
        "city_code": "biei",
        "theme": "Biei Blue Pond & Shirahige Falls",
        "title_zh": "美瑛青池·白须瀑布半日",
        "summary_zh": "青池湖畔散步 → 白须瀑布观赏 → 白金温泉足浴",
        "fragment_type": "half_day",
        "num_items": 2,
        "best_season": ["summer", "fall", "winter"],
        "suitable_for": ["any"],
    },
    # 旭川
    {
        "city_code": "asahikawa",
        "theme": "Asahiyama Zoo & Ramen Village",
        "title_zh": "旭山动物园+拉面村全日",
        "summary_zh": "旭山动物园企鹅散步 → 旭川拉面村午餐 → 雪之美术馆",
        "fragment_type": "full_day",
        "num_items": 2,
        "best_season": ["winter", "spring"],
        "suitable_for": ["family", "any"],
    },
    {
        "city_code": "asahikawa",
        "theme": "Asahikawa Food Tour",
        "title_zh": "旭川美食巡游半日",
        "summary_zh": "旭川拉面名店 → 买物公园散步 → 居酒屋体验",
        "fragment_type": "half_day",
        "num_items": 2,
        "best_season": ["any"],
        "suitable_for": ["foodie", "any"],
    },
    # 登别
    {
        "city_code": "noboribetsu",
        "theme": "Noboribetsu Onsen Day Trip",
        "title_zh": "登别温泉一日游",
        "summary_zh": "地狱谷 → 大汤沼足汤 → 登别温泉日归入浴",
        "fragment_type": "full_day",
        "num_items": 2,
        "best_season": ["any"],
        "suitable_for": ["couple", "any"],
    },
    {
        "city_code": "noboribetsu",
        "theme": "Noboribetsu Jigokudani Walk",
        "title_zh": "登别地狱谷散策半日",
        "summary_zh": "地狱谷木栈道 → 铁�的池 → 温泉街甜品",
        "fragment_type": "half_day",
        "num_items": 2,
        "best_season": ["any"],
        "suitable_for": ["any"],
    },
    # 洞爷湖
    {
        "city_code": "toya",
        "theme": "Lake Toya Volcano & Onsen",
        "title_zh": "洞爷湖火山温泉全日",
        "summary_zh": "有珠山缆车 → 洞爷湖游览船 → 温泉街日归入浴",
        "fragment_type": "full_day",
        "num_items": 2,
        "best_season": ["spring", "summer", "fall"],
        "suitable_for": ["couple", "family"],
    },
    # �的路
    {
        "city_code": "kushiro",
        "theme": "Kushiro Wetland & Seafood",
        "title_zh": "�的路湿原·海鲜半日",
        "summary_zh": "钏路湿原展望台 → 和商市场�的手丼 → 币舞桥夕阳",
        "fragment_type": "half_day",
        "num_items": 2,
        "best_season": ["summer", "fall"],
        "suitable_for": ["any"],
    },
    # 网走
    {
        "city_code": "abashiri",
        "theme": "Abashiri Prison Museum & Drift Ice",
        "title_zh": "网走监狱博物馆·流冰半日",
        "summary_zh": "网走监狱博物馆 → 流冰观光破冰船（冬季）/ �的荷网走湖散步（夏季）",
        "fragment_type": "half_day",
        "num_items": 2,
        "best_season": ["winter", "summer"],
        "suitable_for": ["any"],
    },
    # 二世古
    {
        "city_code": "niseko",
        "theme": "Niseko Outdoor & Onsen",
        "title_zh": "二世古户外·温泉半日",
        "summary_zh": "羊蹄山观景 → 户外体验（夏：漂流/冬：滑雪） → 温泉入浴",
        "fragment_type": "half_day",
        "num_items": 2,
        "best_season": ["winter", "summer"],
        "suitable_for": ["couple", "active"],
    },
]


async def main():
    """主流程"""
    from app.db.session import AsyncSessionLocal
    from app.db.models.fragments_v2 import DayFragment
    from sqlalchemy import text

    logger.info("=" * 60)
    logger.info("D2 Task: Seed fragments for other Hokkaido cities")
    logger.info("=" * 60)

    created_count = 0

    for frag_spec in CITY_FRAGMENTS:
        city = frag_spec["city_code"]

        # 获取该城市的随机实体
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("""
                    SELECT entity_id, entity_type, name_ja, name_zh
                    FROM entity_base
                    WHERE city_code = :city AND is_active = true
                    ORDER BY RANDOM()
                    LIMIT :limit
                """),
                {"city": city, "limit": frag_spec["num_items"]}
            )
            entities = result.fetchall()

        if not entities:
            logger.warning(f"  No entities found for {city}, skipping")
            continue

        items = []
        for row in entities:
            items.append({
                "entity_id": str(row[0]),
                "entity_name": row[3] or row[2],
                "type": row[1],
                "start": "09:00" if frag_spec["fragment_type"] == "full_day" else "14:00",
                "duration": 120 if frag_spec["fragment_type"] == "full_day" else 90,
                "note": f"Visit {row[2] or row[3]}",
            })

        fragment = DayFragment(
            city_code=city,
            fragment_type=frag_spec["fragment_type"],
            theme=frag_spec["theme"],
            items=items,
            total_duration=sum(i["duration"] for i in items),
            estimated_cost=3000,
            best_season=frag_spec.get("best_season", ["any"]),
            weather_ok=frag_spec.get("weather_ok", ["any"]),
            suitable_for=frag_spec.get("suitable_for", ["any"]),
            pace="moderate",
            energy_level="medium",
            title_zh=frag_spec["title_zh"],
            summary_zh=frag_spec["summary_zh"],
            practical_notes=f"{len(items)} activities",
            is_verified=False,
        )

        async with AsyncSessionLocal() as session:
            async with session.begin():
                session.add(fragment)

        created_count += 1
        logger.info(f"  Created: [{city}] {frag_spec['theme']} ({len(items)} items)")

    logger.info(f"\nResults: Created {created_count}/{len(CITY_FRAGMENTS)} fragments")

    # 验证
    logger.info("\nVerification...")
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("SELECT city_code, COUNT(*) FROM day_fragments GROUP BY city_code ORDER BY city_code")
        )
        rows = result.fetchall()
        logger.info("Fragments by city:")
        total = 0
        for city, cnt in rows:
            logger.info(f"  {city}: {cnt}")
            total += cnt
        logger.info(f"  TOTAL: {total}")

    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
