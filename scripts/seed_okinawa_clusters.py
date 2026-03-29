"""
seed_okinawa_clusters.py — 冲绳海岛圈活动簇补全

现有 7 个基础簇（在 seed_all_circles.py），本文件新增 11 个，总计 18 个。
覆盖：那霸市区、北部、中部、南部、离岛、季节活动。

执行：python scripts/seed_okinawa_clusters.py
"""
from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import AsyncSessionLocal
from app.db.models.city_circles import ActivityCluster

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

CLUSTERS = [
    # ── 那霸市区 ────────────────────────────────────────────────────────────
    {
        "cluster_id": "oki_naha_tsuboya_pottery",
        "circle_id": "okinawa_island_circle",
        "city_code": "naha",
        "name_zh": "那霸·壶屋通陶器手工艺线",
        "name_en": "Naha Tsuboya Pottery Street",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "naha_tsuboya",
        "seasonality": ["all_year"],
        "profile_fit": ["culture", "couple", "slow_travel", "arrival_friendly", "rainy_day_ok"],
        "trip_role": "enrichment",
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "壶屋やちむん通是冲绳传统陶器工房街区，步行可达国际通，适合到达日或离开日的轻量补位。",
        "experience_family": "locallife",
        "rhythm_role": "utility",
        "energy_level": "low",
    },
    {
        "cluster_id": "oki_naha_makishi_market",
        "circle_id": "okinawa_island_circle",
        "city_code": "naha",
        "name_zh": "那霸·牧志公设市场美食线",
        "name_en": "Naha Makishi Public Market Food Line",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "naha_city",
        "seasonality": ["all_year"],
        "profile_fit": ["foodie", "first_timer", "arrival_friendly", "rainy_day_ok"],
        "trip_role": "enrichment",
        "time_window_strength": "medium",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "牧志公设市场1楼选海鲜、2楼加工现吃，冲绳本地美食入门体验，室内不受天气影响。",
        "experience_family": "food",
        "rhythm_role": "utility",
        "energy_level": "low",
    },
    # ── 南部 ────────────────────────────────────────────────────────────────
    {
        "cluster_id": "oki_nanbu_peace_seifa",
        "circle_id": "okinawa_island_circle",
        "city_code": "naha",
        "name_zh": "冲绳南部·和平公园斋场御嶽线",
        "name_en": "Southern Okinawa Peace Park & Seifa Utaki",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "nanbu_itoman_nanjou",
        "seasonality": ["all_year"],
        "profile_fit": ["culture", "history", "couple", "photo"],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "平和祈念公园+姬百合之塔+斋场御嶽（世界遗产，琉球最高圣地）+知念岬。冲绳历史文化核心线路。",
        "experience_family": "shrine",
        "rhythm_role": "contrast",
        "energy_level": "medium",
    },
    {
        "cluster_id": "oki_nanbu_cave_cliff",
        "circle_id": "okinawa_island_circle",
        "city_code": "naha",
        "name_zh": "冲绳南部·玉泉洞王国村线",
        "name_en": "Southern Okinawa Gyokusendo Cave & Village",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "nanbu_itoman_nanjou",
        "seasonality": ["all_year"],
        "profile_fit": ["family_child", "culture", "nature", "rainy_day_ok"],
        "trip_role": "enrichment",
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "玉泉洞（30万年钟乳石洞）+冲绳世界文化王国（琉球传统工艺体验）。室内为主，雨天友好。",
        "experience_family": "mountain",
        "rhythm_role": "contrast",
        "energy_level": "medium",
    },
    # ── 中部 ────────────────────────────────────────────────────────────────
    {
        "cluster_id": "oki_zanpa_cape_sunset",
        "circle_id": "okinawa_island_circle",
        "city_code": "naha",
        "name_zh": "冲绳中部·残波岬灯台夕阳线",
        "name_en": "Cape Zanpa Lighthouse Sunset",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "yomitan",
        "seasonality": ["all_year"],
        "profile_fit": ["couple", "photo", "nature"],
        "trip_role": "buffer",
        "time_window_strength": "strong",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "残波岬白色灯台+珊瑚礁断崖夕阳，读谷村陶器街可顺路。适合下午到傍晚。",
        "experience_family": "sea",
        "rhythm_role": "recovery",
        "energy_level": "low",
    },
    # ── 北部 ────────────────────────────────────────────────────────────────
    {
        "cluster_id": "oki_yanbaru_nature",
        "circle_id": "okinawa_island_circle",
        "city_code": "naha",
        "name_zh": "冲绳北部·山原亚热带森林线",
        "name_en": "Yanbaru Subtropical Forest Trek",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "yanbaru",
        "seasonality": ["all_year"],
        "profile_fit": ["nature", "adventure", "couple"],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "山原国立公园（世界自然遗产候选）+大石林山+比地大瀑布。冲绳唯一的亚热带原始森林体验，需租车。",
        "experience_family": "mountain",
        "rhythm_role": "peak",
        "energy_level": "high",
    },
    # ── 离岛 ────────────────────────────────────────────────────────────────
    {
        "cluster_id": "oki_zamami_whale_watch",
        "circle_id": "okinawa_island_circle",
        "city_code": "naha",
        "name_zh": "座间味·冬季赏鲸+浮潜线",
        "name_en": "Zamami Whale Watching & Snorkeling",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "kerama",
        "seasonality": ["winter"],
        "profile_fit": ["couple", "adventure", "nature", "photo"],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 0,
        "default_selected": False,
        "notes": "1-3月座头鲸回游庆良间海域，赏鲸船+浮潜一日游。泊港出发约50分钟，需提前预约。",
        "experience_family": "sea",
        "rhythm_role": "peak",
        "energy_level": "medium",
        "upgrade_triggers": {"travel_months": [1, 2, 3]},
    },
    {
        "cluster_id": "oki_tokashiki_beach",
        "circle_id": "okinawa_island_circle",
        "city_code": "naha",
        "name_zh": "渡嘉敷岛·阿波连海滩一日线",
        "name_en": "Tokashiki Island Aharen Beach Day Trip",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "kerama",
        "seasonality": ["all_year"],
        "profile_fit": ["couple", "diving", "nature", "beach"],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 0,
        "default_selected": False,
        "notes": "庆良间群岛最大岛，阿波连海滩被评为日本最美海滩之一。泊港高速船35分钟，需预约回程船。",
        "experience_family": "sea",
        "rhythm_role": "peak",
        "energy_level": "medium",
    },
    # ── 季节活动 ────────────────────────────────────────────────────────────
    {
        "cluster_id": "oki_umi_biraki_spring",
        "circle_id": "okinawa_island_circle",
        "city_code": "naha",
        "name_zh": "冲绳·海开季海滩开幕线",
        "name_en": "Okinawa Umi-Biraki Beach Opening",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "beaches",
        "seasonality": ["spring"],
        "profile_fit": ["beach", "family_child", "friends"],
        "trip_role": "enrichment",
        "time_window_strength": "strong",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "冲绳3月底-4月初海开，全日本最早可下水。万座海滩/残波海滩/翡翠海滩三选一。",
        "experience_family": "sea",
        "rhythm_role": "utility",
        "energy_level": "medium",
        "upgrade_triggers": {"travel_months": [3, 4]},
    },
    # ── 夜间/美食补位 ────────────────────────────────────────────────────────
    {
        "cluster_id": "oki_naha_sakaemachi_night",
        "circle_id": "okinawa_island_circle",
        "city_code": "naha",
        "name_zh": "那霸·荣町市场夜间美食线",
        "name_en": "Naha Sakaemachi Night Food Market",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "naha_city",
        "seasonality": ["all_year"],
        "profile_fit": ["foodie", "nightlife", "friends"],
        "trip_role": "enrichment",
        "time_window_strength": "strong",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "荣町市场夜间变身居酒屋街，泡盛+冲绳料理（海葡萄/苦瓜炒蛋/猪脚）。比国际通更本地。",
        "experience_family": "food",
        "rhythm_role": "utility",
        "energy_level": "low",
    },
    {
        "cluster_id": "oki_resort_hotel_rest",
        "circle_id": "okinawa_island_circle",
        "city_code": "naha",
        "name_zh": "冲绳·度假酒店海滩休息线",
        "name_en": "Okinawa Resort Hotel Beach Day",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "resort_area",
        "seasonality": ["all_year"],
        "profile_fit": ["couple", "family_child", "slow_travel"],
        "trip_role": "enrichment",
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 0,
        "default_selected": False,
        "notes": "度假酒店泳池+私人海滩+spa半日休息。不安排外出活动，让用户享受酒店本身。中部恩纳/北谷区域度假酒店密集。",
        "experience_family": "onsen",
        "rhythm_role": "recovery",
        "energy_level": "low",
    },
]


async def seed():
    async with AsyncSessionLocal() as session:
        new_count = skip_count = 0
        for data in CLUSTERS:
            existing = await session.get(ActivityCluster, data["cluster_id"])
            if existing:
                skip_count += 1
                continue
            known_fields = {c.key for c in ActivityCluster.__table__.columns}
            filtered = {k: v for k, v in data.items() if k in known_fields}
            cluster = ActivityCluster(**filtered)
            session.add(cluster)
            new_count += 1
            logger.info("  NEW: %s [%s] %s", data["cluster_id"], data.get("level", "?"), data.get("city_code", "?"))
        await session.commit()
        logger.info("=== okinawa_island_circle 完成: 新增=%d 跳过=%d 总计=%d ===",
                     new_count, skip_count, len(CLUSTERS))


if __name__ == "__main__":
    asyncio.run(seed())
