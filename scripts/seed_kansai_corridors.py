"""
seed_kansai_corridors.py — 关西经典圈走廊种子数据

写入 corridors + corridor_alias_map 表。
覆盖京都 5 条 + 大阪 4 条 + 奈良 1 条走廊。

执行：
    cd D:/projects/projects/travel-ai
    python scripts/seed_kansai_corridors.py
"""
from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.db.models.corridors import Corridor, CorridorAliasMap

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 走廊定义
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CORRIDORS = [
    # ── 京都 ──
    {
        "corridor_id": "kyo_higashiyama",
        "name_zh": "东山（清水寺-祇园）",
        "name_en": "Higashiyama (Kiyomizu-Gion)",
        "name_ja": "東山エリア",
        "city_code": "kyoto",
        "center_lat": 34.9948,
        "center_lng": 135.7850,
        "corridor_type": "line",
        "main_stations": ["清水五条", "祇園四条"],
        "adjacent_corridor_ids": [
            "kyo_gion", "kyo_okazaki"
        ],
        "typical_visit_hours": 4.0,
        "notes": "清水寺→二年坂→八坂神社，京都最经典步行线",
    },
    {
        "corridor_id": "kyo_gion",
        "name_zh": "祇园·花见小路",
        "name_en": "Gion & Hanamikoji",
        "name_ja": "祇園エリア",
        "city_code": "kyoto",
        "center_lat": 34.9985,
        "center_lng": 135.7754,
        "corridor_type": "area",
        "main_stations": ["祇園四条"],
        "adjacent_corridor_ids": [
            "kyo_higashiyama", "kyo_kawaramachi"
        ],
        "typical_visit_hours": 2.0,
        "notes": "艺伎街区+花见小路，傍晚最佳",
    },
    {
        "corridor_id": "kyo_arashiyama",
        "name_zh": "岚山·嵯峨野",
        "name_en": "Arashiyama & Sagano",
        "name_ja": "嵐山エリア",
        "city_code": "kyoto",
        "center_lat": 35.0094,
        "center_lng": 135.6722,
        "corridor_type": "area",
        "main_stations": ["嵐山(嵐電)", "嵯峨嵐山(JR)"],
        "adjacent_corridor_ids": [],
        "typical_visit_hours": 5.0,
        "notes": "竹林→天龙寺→渡月桥，独立片区",
    },
    {
        "corridor_id": "kyo_fushimi",
        "name_zh": "伏见（稻荷·酒藏）",
        "name_en": "Fushimi (Inari & Sake)",
        "name_ja": "伏見エリア",
        "city_code": "kyoto",
        "center_lat": 34.9671,
        "center_lng": 135.7727,
        "corridor_type": "area",
        "main_stations": ["稲荷(JR)", "伏見稲荷(京阪)"],
        "adjacent_corridor_ids": [],
        "typical_visit_hours": 3.0,
        "notes": "千本鸟居+伏见酒藏区",
    },
    {
        "corridor_id": "kyo_kawaramachi",
        "name_zh": "河原町·四条",
        "name_en": "Kawaramachi & Shijo",
        "name_ja": "河原町・四条エリア",
        "city_code": "kyoto",
        "center_lat": 35.0038,
        "center_lng": 135.7689,
        "corridor_type": "station_hub",
        "main_stations": ["河原町", "烏丸"],
        "adjacent_corridor_ids": [
            "kyo_gion", "kyo_higashiyama"
        ],
        "typical_visit_hours": 2.0,
        "notes": "京都最大商业区+酒店集中地",
    },
    {
        "corridor_id": "kyo_okazaki",
        "name_zh": "冈崎·哲学之道",
        "name_en": "Okazaki & Philosopher Path",
        "name_ja": "岡崎・哲学の道エリア",
        "city_code": "kyoto",
        "center_lat": 35.0116,
        "center_lng": 135.7862,
        "corridor_type": "line",
        "main_stations": ["蹴上"],
        "adjacent_corridor_ids": [
            "kyo_higashiyama"
        ],
        "typical_visit_hours": 3.0,
        "notes": "南禅寺→哲学之道→银阁寺",
    },
    # ── 大阪 ──
    {
        "corridor_id": "osa_namba",
        "name_zh": "难波·道顿堀·心斋桥",
        "name_en": "Namba, Dotonbori & Shinsaibashi",
        "name_ja": "なんば・道頓堀エリア",
        "city_code": "osaka",
        "center_lat": 34.6687,
        "center_lng": 135.5013,
        "corridor_type": "station_hub",
        "main_stations": ["なんば", "心斎橋"],
        "adjacent_corridor_ids": [
            "osa_shinsekai"
        ],
        "typical_visit_hours": 3.0,
        "notes": "大阪美食夜游核心区",
    },
    {
        "corridor_id": "osa_osakajo",
        "name_zh": "大阪城·天满桥",
        "name_en": "Osaka Castle & Tenmabashi",
        "name_ja": "大阪城エリア",
        "city_code": "osaka",
        "center_lat": 34.6873,
        "center_lng": 135.5262,
        "corridor_type": "area",
        "main_stations": ["大阪城公園", "天満橋"],
        "adjacent_corridor_ids": [],
        "typical_visit_hours": 2.5,
        "notes": "大阪城天守阁+西之丸庭园",
    },
    {
        "corridor_id": "osa_sakurajima",
        "name_zh": "此花·USJ",
        "name_en": "Sakurajima / USJ Area",
        "name_ja": "桜島(USJ)エリア",
        "city_code": "osaka",
        "center_lat": 34.6654,
        "center_lng": 135.4323,
        "corridor_type": "area",
        "main_stations": ["ユニバーサルシティ"],
        "adjacent_corridor_ids": [],
        "typical_visit_hours": 10.0,
        "notes": "USJ 环球影城专用",
    },
    {
        "corridor_id": "osa_shinsekai",
        "name_zh": "新世界·天王寺",
        "name_en": "Shinsekai & Tennoji",
        "name_ja": "新世界・天王寺エリア",
        "city_code": "osaka",
        "center_lat": 34.6525,
        "center_lng": 135.5063,
        "corridor_type": "area",
        "main_stations": ["天王寺", "新今宮"],
        "adjacent_corridor_ids": ["osa_namba"],
        "typical_visit_hours": 2.0,
        "notes": "通天阁+串炸名店街",
    },
    # ── 奈良 ──
    {
        "corridor_id": "nara_park",
        "name_zh": "奈良公园·东大寺",
        "name_en": "Nara Park & Todaiji",
        "name_ja": "奈良公園エリア",
        "city_code": "nara",
        "center_lat": 34.6851,
        "center_lng": 135.8398,
        "corridor_type": "area",
        "main_stations": ["近鉄奈良"],
        "adjacent_corridor_ids": [],
        "typical_visit_hours": 4.0,
        "notes": "鹿公园+东大寺+春日大社",
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 走廊别名
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ALIASES = [
    # kyo_higashiyama
    ("kyo_higashiyama", "东山", "zh", True),
    ("kyo_higashiyama", "東山", "ja", True),
    ("kyo_higashiyama", "higashiyama", "en", True),
    ("kyo_higashiyama", "清水寺周边", "zh", False),
    # kyo_gion
    ("kyo_gion", "祇园", "zh", True),
    ("kyo_gion", "祇園", "ja", True),
    ("kyo_gion", "gion", "en", True),
    ("kyo_gion", "花见小路", "zh", False),
    # kyo_arashiyama
    ("kyo_arashiyama", "岚山", "zh", True),
    ("kyo_arashiyama", "嵐山", "ja", True),
    ("kyo_arashiyama", "arashiyama", "en", True),
    ("kyo_arashiyama", "嵯峨野", "zh", False),
    # kyo_fushimi
    ("kyo_fushimi", "伏见", "zh", True),
    ("kyo_fushimi", "伏見", "ja", True),
    ("kyo_fushimi", "fushimi", "en", True),
    ("kyo_fushimi", "稻荷", "zh", False),
    # kyo_kawaramachi
    ("kyo_kawaramachi", "河原町", "zh", True),
    ("kyo_kawaramachi", "河原町通り", "ja", True),
    ("kyo_kawaramachi", "kawaramachi", "en", True),
    ("kyo_kawaramachi", "四条", "zh", False),
    # kyo_okazaki
    ("kyo_okazaki", "冈崎", "zh", True),
    ("kyo_okazaki", "岡崎", "ja", True),
    ("kyo_okazaki", "okazaki", "en", True),
    ("kyo_okazaki", "哲学之道", "zh", False),
    # osa_namba
    ("osa_namba", "难波", "zh", True),
    ("osa_namba", "なんば", "ja", True),
    ("osa_namba", "namba", "en", True),
    ("osa_namba", "道顿堀", "zh", False),
    ("osa_namba", "心斋桥", "zh", False),
    # osa_osakajo
    ("osa_osakajo", "大阪城", "zh", True),
    ("osa_osakajo", "大阪城公園", "ja", True),
    ("osa_osakajo", "osaka castle", "en", True),
    # osa_sakurajima
    ("osa_sakurajima", "USJ", "en", True),
    ("osa_sakurajima", "环球影城", "zh", False),
    # osa_shinsekai
    ("osa_shinsekai", "新世界", "zh", True),
    ("osa_shinsekai", "新世界エリア", "ja", True),
    ("osa_shinsekai", "shinsekai", "en", True),
    ("osa_shinsekai", "天王寺", "zh", False),
    # nara_park
    ("nara_park", "奈良公园", "zh", True),
    ("nara_park", "奈良公園", "ja", True),
    ("nara_park", "nara park", "en", True),
    ("nara_park", "东大寺", "zh", False),
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Seed 执行
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def seed():
    async with AsyncSessionLocal() as session:
        # 1. corridors
        logger.info("=== Seeding corridors (%d) ===", len(CORRIDORS))
        for data in CORRIDORS:
            existing = await session.get(
                Corridor, data["corridor_id"]
            )
            if existing:
                logger.info("  SKIP: %s", data["corridor_id"])
                continue
            session.add(Corridor(**data))
            logger.info("  INSERT: %s", data["corridor_id"])
        await session.flush()

        # 2. corridor_alias_map
        logger.info("=== Seeding corridor aliases (%d) ===", len(ALIASES))
        for cid, text, lang, is_primary in ALIASES:
            norm = text.lower().replace(" ", "")
            existing = await session.execute(
                select(CorridorAliasMap).where(
                    CorridorAliasMap.corridor_id == cid,
                    CorridorAliasMap.alias_text == text,
                )
            )
            if existing.scalar_one_or_none():
                continue
            session.add(CorridorAliasMap(
                corridor_id=cid,
                alias_text=text,
                alias_lang=lang,
                normalized_text=norm,
                is_primary=is_primary,
            ))
        await session.flush()

        await session.commit()

        c_cnt = len(
            (await session.execute(select(Corridor))).scalars().all()
        )
        a_cnt = len(
            (await session.execute(
                select(CorridorAliasMap)
            )).scalars().all()
        )
        logger.info(
            "✅ 走廊种子完成: corridors=%d aliases=%d",
            c_cnt, a_cnt,
        )


if __name__ == "__main__":
    asyncio.run(seed())
