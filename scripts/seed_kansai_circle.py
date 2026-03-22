"""
seed_kansai_circle.py — D5: 关西城市圈种子数据

向 city_circles / activity_clusters / hotel_strategy_presets 三张表写入
关西经典圈（kansai_classic_circle）的基础数据。

执行方式：
    cd D:/projects/projects/travel-ai
    python scripts/seed_kansai_circle.py

依赖：
    - app/db/session.py (Base, async_engine, AsyncSessionLocal)
    - app/db/models/city_circles.py
"""
from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

# 确保项目根在 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.session import AsyncSessionLocal
from app.db.models.city_circles import (
    ActivityCluster,
    CityCircle,
    HotelStrategyPreset,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 城市圈定义
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CIRCLES = [
    {
        "circle_id": "kansai_classic_circle",
        "name_zh": "关西经典圈",
        "name_en": "Kansai Classic Circle",
        "base_city_codes": ["kyoto", "osaka"],
        "extension_city_codes": ["nara", "kobe", "uji", "arima_onsen"],
        "min_days": 4,
        "max_days": 10,
        "recommended_days_range": "5-8",
        "tier": "hot",
        "fit_profiles": {
            "party_types": ["couple", "family_child", "solo", "friends"],
            "themes": ["temple", "food", "history", "nature"],
        },
        "friendly_airports": ["KIX", "ITM"],
        "season_strength": {
            "spring": 0.95,   # 樱花季极强
            "summer": 0.65,
            "autumn": 0.95,   # 红叶季极强
            "winter": 0.55,
        },
        "notes": "日本旅游最核心圈。京都历史文化+大阪美食繁华，奈良半日游极强，适合绝大多数旅行者。",
        "is_active": True,
    },
    {
        "circle_id": "osaka_day_base_circle",
        "name_zh": "大阪为基点圈",
        "name_en": "Osaka Day-Base Circle",
        "base_city_codes": ["osaka"],
        "extension_city_codes": ["kyoto", "kobe", "nara", "himeji"],
        "min_days": 3,
        "max_days": 6,
        "recommended_days_range": "3-5",
        "tier": "hot",
        "fit_profiles": {
            "party_types": ["couple", "solo", "friends"],
            "themes": ["food", "shopping", "day_trips"],
        },
        "friendly_airports": ["KIX", "ITM"],
        "season_strength": {
            "spring": 0.85,
            "summer": 0.70,
            "autumn": 0.80,
            "winter": 0.65,
        },
        "notes": "纯大阪为基点，京都/神户/奈良均可日归。适合天数少或以美食为主要目的的旅行者。",
        "is_active": True,
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 活动簇定义（属于 kansai_classic_circle）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CLUSTERS = [
    # ── 京都 ──────────────────────────────────────────────────────────────────
    {
        "cluster_id": "kyo_higashiyama_gion_classic",
        "circle_id": "kansai_classic_circle",
        "name_zh": "京都·东山祇园经典线",
        "name_en": "Kyoto Higashiyama & Gion Classic",
        "level": "S",
        "default_duration": "full_day",
        "duration_range_days": "0.8-1.0",
        "primary_corridor": "higashiyama",
        "seasonality": ["all_year", "sakura", "autumn_leaves"],
        "profile_fit": ["first_timer", "couple", "photo", "culture"],
        "trip_role": "anchor",
        "can_drive_hotel": False,
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": True,
        "notes": "清水寺→二年坂→八坂神社→祇园白川。全年最受欢迎的京都线路，首次来京必走。",
    },
    {
        "cluster_id": "kyo_arashiyama_sagano",
        "circle_id": "kansai_classic_circle",
        "name_zh": "京都·岚山嵯峨野线",
        "name_en": "Kyoto Arashiyama & Sagano",
        "level": "S",
        "default_duration": "full_day",
        "duration_range_days": "0.8-1.0",
        "primary_corridor": "arashiyama",
        "seasonality": ["all_year", "sakura", "autumn_leaves"],
        "profile_fit": ["couple", "nature", "photo", "culture"],
        "trip_role": "anchor",
        "can_drive_hotel": False,
        "time_window_strength": "medium",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": True,
        "notes": "竹林→天龙寺→渡月桥→保津川。适合偏自然系旅行者，春秋光线极佳。",
    },
    {
        "cluster_id": "kyo_fushimi_inari",
        "circle_id": "kansai_classic_circle",
        "name_zh": "京都·伏见稻荷",
        "name_en": "Kyoto Fushimi Inari",
        "level": "S",
        "default_duration": "half_day",
        "duration_range_days": "0.4-0.6",
        "primary_corridor": "fushimi",
        "seasonality": ["all_year"],
        "profile_fit": ["first_timer", "photo", "couple", "solo"],
        "trip_role": "anchor",
        "can_drive_hotel": False,
        "time_window_strength": "strong",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 1,
        "default_selected": True,
        "notes": "千本鸟居。建议清晨 7-9 点前往避开人流。可与伏见酒藏区搭配为半天线路。",
        "upgrade_triggers": {"tags": ["photo", "instagram"], "party_types": ["couple", "solo"]},
    },
    {
        "cluster_id": "kyo_kinkakuji_kinugasa",
        "circle_id": "kansai_classic_circle",
        "name_zh": "京都·金阁寺衣笠线",
        "name_en": "Kyoto Kinkakuji & Kinugasa",
        "level": "A",
        "default_duration": "half_day",
        "duration_range_days": "0.4-0.6",
        "primary_corridor": "kinugasa",
        "seasonality": ["all_year", "winter_snow"],
        "profile_fit": ["first_timer", "culture", "photo"],
        "trip_role": "anchor",
        "can_drive_hotel": False,
        "time_window_strength": "medium",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "金阁寺→龙安寺（枯山水）→仁和寺。文化密集，适合对禅意日本有兴趣的旅行者。",
    },
    {
        "cluster_id": "kyo_philosopher_path_nanzen",
        "circle_id": "kansai_classic_circle",
        "name_zh": "京都·哲学之道南禅寺线",
        "name_en": "Kyoto Philosopher's Path & Nanzenji",
        "level": "A",
        "default_duration": "half_day",
        "duration_range_days": "0.4-0.5",
        "primary_corridor": "okazaki",
        "seasonality": ["all_year", "sakura", "autumn_leaves"],
        "profile_fit": ["couple", "solo", "culture", "photo"],
        "trip_role": "enrichment",
        "can_drive_hotel": False,
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "哲学之道（春季樱花隧道）→南禅寺→平安神宫。轻松步行线，与东山东侧搭配效率高。",
    },
    {
        "cluster_id": "kyo_nara_day_trip",
        "circle_id": "kansai_classic_circle",
        "name_zh": "奈良日归（从京都/大阪）",
        "name_en": "Nara Day Trip",
        "level": "A",
        "default_duration": "full_day",
        "duration_range_days": "0.8-1.0",
        "primary_corridor": "nara_park",
        "seasonality": ["all_year"],
        "profile_fit": ["family_child", "couple", "first_timer", "nature"],
        "trip_role": "anchor",
        "can_drive_hotel": False,
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "奈良公园鹿+东大寺。从京都 45 分钟/大阪 40 分钟，强力日归选项。家庭游极推。",
        "upgrade_triggers": {"party_types": ["family_child"], "tags": ["kids", "nature"]},
    },
    # ── 大阪 ──────────────────────────────────────────────────────────────────
    {
        "cluster_id": "osa_dotonbori_minami_food",
        "circle_id": "kansai_classic_circle",
        "name_zh": "大阪·道顿堀南区美食夜游",
        "name_en": "Osaka Dotonbori & Minami Food Night",
        "level": "S",
        "default_duration": "half_day",
        "duration_range_days": "0.3-0.5",
        "primary_corridor": "namba",
        "seasonality": ["all_year"],
        "profile_fit": ["food", "couple", "friends", "first_timer"],
        "trip_role": "anchor",
        "can_drive_hotel": True,
        "time_window_strength": "weak",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": True,
        "notes": "章鱼烧→大阪烧→串炸。道顿堀至难波为大阪美食最密集区域，建议晚 18 点后进入。",
    },
    {
        "cluster_id": "osa_usj_themepark",
        "circle_id": "kansai_classic_circle",
        "name_zh": "大阪·USJ 环球影城",
        "name_en": "Osaka Universal Studios Japan",
        "level": "S",
        "default_duration": "full_day",
        "duration_range_days": "1.0-1.0",
        "primary_corridor": "sakurajima",
        "seasonality": ["all_year"],
        "profile_fit": ["family_child", "friends", "theme_park"],
        "trip_role": "anchor",
        "can_drive_hotel": False,
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 0,
        "default_selected": False,
        "notes": "哈利波特+任天堂世界。全天行程，必须提前购快速票/express pass，家庭/朋友游强烈推荐。",
        "upgrade_triggers": {"tags": ["theme_park", "nintendo", "harry_potter"], "party_types": ["family_child", "friends"]},
    },
    {
        "cluster_id": "osa_osaka_castle_tenmabashi",
        "circle_id": "kansai_classic_circle",
        "name_zh": "大阪·大阪城天满桥线",
        "name_en": "Osaka Castle & Tenmabashi",
        "level": "A",
        "default_duration": "half_day",
        "duration_range_days": "0.4-0.5",
        "primary_corridor": "osakajo",
        "seasonality": ["all_year", "sakura"],
        "profile_fit": ["history", "first_timer", "culture"],
        "trip_role": "enrichment",
        "can_drive_hotel": False,
        "time_window_strength": "medium",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "大阪城天守阁+护城河樱花。与中之岛、天满桥餐厅街搭配为上午线路。",
    },
    {
        "cluster_id": "osa_shinsekai_tenno",
        "circle_id": "kansai_classic_circle",
        "name_zh": "大阪·新世界天王寺线",
        "name_en": "Osaka Shinsekai & Tenoji",
        "level": "B",
        "default_duration": "quarter_day",
        "duration_range_days": "0.25-0.4",
        "primary_corridor": "shinsekai",
        "seasonality": ["all_year"],
        "profile_fit": ["solo", "friends", "food", "retro"],
        "trip_role": "buffer",
        "can_drive_hotel": False,
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "昭和复古风+串炸名店。通天阁周边气氛浓郁，可作为半天的补充或中转站。",
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 酒店住法预设（kansai_classic_circle）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HOTEL_PRESETS = [
    # ── 京都单基点 ─────────────────────────────────────────────────────────────
    {
        "circle_id": "kansai_classic_circle",
        "name_zh": "全程住京都（河原町/祇园）",
        "min_days": 4,
        "max_days": 7,
        "bases": [
            {
                "base_city": "kyoto",
                "area": "kawaramachi",
                "nights_range": "4-7",
                "served_cluster_ids": [
                    "kyo_higashiyama_gion_classic",
                    "kyo_arashiyama_sagano",
                    "kyo_fushimi_inari",
                    "kyo_kinkakuji_kinugasa",
                    "kyo_philosopher_path_nanzen",
                    "kyo_nara_day_trip",
                    "osa_dotonbori_minami_food",  # 大阪当天往返
                ],
            }
        ],
        "fit_party_types": ["couple", "solo", "culture_lover"],
        "fit_budget_levels": ["mid", "premium", "luxury"],
        "switch_count": 0,
        "switch_cost_minutes": 0,
        "last_night_airport_minutes": 75,  # 京都→KIX
        "priority": 10,
        "notes": "最推荐。零换酒店，京都出行最便利。大阪可日归（新干线 15 分）。",
        "is_active": True,
    },
    # ── 双基点（京都+大阪）──────────────────────────────────────────────────
    {
        "circle_id": "kansai_classic_circle",
        "name_zh": "京都前段 + 大阪后段（经典双基点）",
        "min_days": 5,
        "max_days": 9,
        "bases": [
            {
                "base_city": "kyoto",
                "area": "kawaramachi",
                "nights_range": "3-4",
                "served_cluster_ids": [
                    "kyo_higashiyama_gion_classic",
                    "kyo_arashiyama_sagano",
                    "kyo_fushimi_inari",
                    "kyo_nara_day_trip",
                ],
            },
            {
                "base_city": "osaka",
                "area": "namba",
                "nights_range": "2-3",
                "served_cluster_ids": [
                    "osa_dotonbori_minami_food",
                    "osa_usj_themepark",
                    "osa_osaka_castle_tenmabashi",
                ],
            },
        ],
        "fit_party_types": ["couple", "family_child", "friends"],
        "fit_budget_levels": ["budget", "mid", "premium"],
        "switch_count": 1,
        "switch_cost_minutes": 45,
        "last_night_airport_minutes": 30,  # 大阪难波→KIX
        "priority": 20,
        "notes": "适合 5-9 天行程，文化+美食均衡。换一次酒店（从京都移至大阪）性价比最高。",
        "is_active": True,
    },
    # ── 全程住大阪 ─────────────────────────────────────────────────────────────
    {
        "circle_id": "kansai_classic_circle",
        "name_zh": "全程住大阪（难波/心斋桥）",
        "min_days": 3,
        "max_days": 6,
        "bases": [
            {
                "base_city": "osaka",
                "area": "namba",
                "nights_range": "3-6",
                "served_cluster_ids": [
                    "osa_dotonbori_minami_food",
                    "osa_osaka_castle_tenmabashi",
                    "osa_shinsekai_tenno",
                    "kyo_higashiyama_gion_classic",  # 日归
                    "kyo_arashiyama_sagano",          # 日归
                    "kyo_nara_day_trip",               # 日归
                ],
            }
        ],
        "fit_party_types": ["friends", "solo", "food_lover"],
        "fit_budget_levels": ["budget", "mid"],
        "switch_count": 0,
        "switch_cost_minutes": 0,
        "last_night_airport_minutes": 30,
        "priority": 30,
        "notes": "天数少或以大阪为核心的旅行者。京都/奈良均可当天往返，离 KIX 机场最方便。",
        "is_active": True,
    },
    # ── 大阪单基点圈（第二圈）──────────────────────────────────────────────
    {
        "circle_id": "osaka_day_base_circle",
        "name_zh": "全程住大阪（短途圈）",
        "min_days": 3,
        "max_days": 5,
        "bases": [
            {
                "base_city": "osaka",
                "area": "namba",
                "nights_range": "3-5",
                "served_cluster_ids": [
                    "osa_dotonbori_minami_food",
                    "osa_osaka_castle_tenmabashi",
                ],
            }
        ],
        "fit_party_types": ["friends", "solo", "couple"],
        "fit_budget_levels": ["budget", "mid"],
        "switch_count": 0,
        "switch_cost_minutes": 0,
        "last_night_airport_minutes": 30,
        "priority": 10,
        "notes": "大阪为基点短途圈。适合天数少（3-5天）或以购物/美食为主的旅行者。",
        "is_active": True,
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 执行 seed
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def seed():
    async with AsyncSessionLocal() as session:
        # ── 1. city_circles ─────────────────────────────────────────────────
        logger.info("Seeding city_circles ...")
        for data in CIRCLES:
            existing = await session.get(CityCircle, data["circle_id"])
            if existing:
                logger.info("  SKIP (exists): %s", data["circle_id"])
                continue
            session.add(CityCircle(**data))
            logger.info("  INSERT: %s", data["circle_id"])
        await session.flush()

        # ── 2. activity_clusters ────────────────────────────────────────────
        logger.info("Seeding activity_clusters ...")
        for data in CLUSTERS:
            existing = await session.get(ActivityCluster, data["cluster_id"])
            if existing:
                logger.info("  SKIP (exists): %s", data["cluster_id"])
                continue
            session.add(ActivityCluster(**data))
            logger.info("  INSERT: %s", data["cluster_id"])
        await session.flush()

        # ── 3. hotel_strategy_presets ───────────────────────────────────────
        logger.info("Seeding hotel_strategy_presets ...")
        for data in HOTEL_PRESETS:
            session.add(HotelStrategyPreset(**data))
            logger.info("  INSERT: %s", data["name_zh"])
        await session.flush()

        await session.commit()
        logger.info("✅ 关西城市圈种子数据写入完成")

        # ── 汇总 ─────────────────────────────────────────────────────────────
        c_count = len((await session.execute(select(CityCircle))).scalars().all())
        cl_count = len((await session.execute(select(ActivityCluster))).scalars().all())
        h_count = len((await session.execute(select(HotelStrategyPreset))).scalars().all())
        logger.info(
            "当前数据：city_circles=%d  activity_clusters=%d  hotel_presets=%d",
            c_count, cl_count, h_count,
        )


if __name__ == "__main__":
    asyncio.run(seed())
