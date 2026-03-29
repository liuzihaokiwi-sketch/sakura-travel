"""
seed_chaoshan_clusters.py — 潮汕文化圈活动簇

潮汕圈覆盖：潮州、汕头、揭阳，以美食和传统文化为核心卖点。
定位：中国国内深度美食文化旅行目的地，2-4 天行程。

执行：python scripts/seed_chaoshan_clusters.py
"""
from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import AsyncSessionLocal
from app.db.models.city_circles import CityCircle, ActivityCluster

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

CIRCLE = "chaoshan_culture_circle"

CIRCLE_DEF = {
    "circle_id": CIRCLE,
    "name_zh": "潮汕文化圈",
    "name_en": "Chaoshan Culture Circle",
    "base_city_codes": ["chaozhou", "shantou"],
    "extension_city_codes": ["meizhou", "jieyang"],
    "min_days": 2,
    "max_days": 5,
    "recommended_days_range": "3-4",
    "tier": "niche",
    "fit_profiles": {"party_types": ["couple", "friends", "foodie", "solo"], "themes": ["food", "culture", "history"]},
    "friendly_airports": ["SWA"],  # 揭阳潮汕国际机场
    "season_strength": {"spring": 0.85, "summer": 0.70, "autumn": 0.90, "winter": 0.80},
    "notes": "中国最被低估的美食目的地。功夫茶文化、牛肉火锅、潮汕小吃、古城建筑、工夫茶道。",
    "is_active": True,
}

CLUSTERS = [
    # ── 潮州 ────────────────────────────────────────────────────────────────
    {
        "cluster_id": "cs_chaozhou_old_city_core",
        "circle_id": CIRCLE,
        "city_code": "chaozhou",
        "name_zh": "潮州·古城核心文化线",
        "name_en": "Chaozhou Old City Core Culture",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "chaozhou_old_city",
        "seasonality": ["all_year"],
        "profile_fit": ["culture", "history", "photo", "first_timer"],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": True,
        "notes": "广济桥（中国四大古桥）+广济门城楼+开元寺+牌坊街。潮州古城精华一日线，晚上广济桥灯光秀。",
        "experience_family": "shrine",
        "rhythm_role": "peak",
        "energy_level": "high",
    },
    {
        "cluster_id": "cs_chaozhou_food_crawl",
        "circle_id": CIRCLE,
        "city_code": "chaozhou",
        "name_zh": "潮州·牌坊街美食扫街线",
        "name_en": "Chaozhou Paifang Street Food Crawl",
        "level": "S",
        "default_duration": "half_day",
        "primary_corridor": "chaozhou_paifang",
        "seasonality": ["all_year"],
        "profile_fit": ["foodie", "first_timer", "friends"],
        "trip_role": "anchor",
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": True,
        "notes": "牌坊街+西马路小吃集中区：春卷、粿条、腐乳饼、鸭母捻、蚝烙。潮州美食精华，步行可达。",
        "experience_family": "food",
        "rhythm_role": "peak",
        "energy_level": "low",
    },
    {
        "cluster_id": "cs_chaozhou_gongfu_tea",
        "circle_id": CIRCLE,
        "city_code": "chaozhou",
        "name_zh": "潮州·功夫茶文化体验线",
        "name_en": "Chaozhou Gongfu Tea Culture",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "chaozhou_tea_area",
        "seasonality": ["all_year"],
        "profile_fit": ["culture", "couple", "slow_travel"],
        "trip_role": "enrichment",
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "凤凰单丛茶发源地，古城内茶馆功夫茶道体验+中山路茶叶街选购。潮州最独特的慢旅行体验。",
        "experience_family": "locallife",
        "rhythm_role": "recovery",
        "energy_level": "low",
    },
    {
        "cluster_id": "cs_chaozhou_ceramics",
        "circle_id": CIRCLE,
        "city_code": "chaozhou",
        "name_zh": "潮州·陶瓷之都手工艺线",
        "name_en": "Chaozhou Ceramics Capital",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "chaozhou_fengxi",
        "seasonality": ["all_year"],
        "profile_fit": ["culture", "couple", "rainy_day_ok"],
        "trip_role": "enrichment",
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "枫溪陶瓷工业区+潮州陶瓷博物馆。中国瓷都，可现场参观制作过程。",
        "experience_family": "art",
        "rhythm_role": "utility",
        "energy_level": "low",
    },
    # ── 汕头 ────────────────────────────────────────────────────────────────
    {
        "cluster_id": "cs_shantou_xiaogongyuan_food",
        "circle_id": CIRCLE,
        "city_code": "shantou",
        "name_zh": "汕头·小公园骑楼美食线",
        "name_en": "Shantou Xiaogongyuan Arcade Food Line",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "shantou_xiaogongyuan",
        "seasonality": ["all_year"],
        "profile_fit": ["foodie", "culture", "photo", "first_timer"],
        "trip_role": "anchor",
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": True,
        "notes": "小公园开埠区骑楼建筑群+西天巷蚝烙+老妈宫粽球+汕头牛肉火锅。汕头美食核心区域。",
        "experience_family": "food",
        "rhythm_role": "peak",
        "energy_level": "medium",
    },
    {
        "cluster_id": "cs_shantou_beef_hotpot",
        "circle_id": CIRCLE,
        "city_code": "shantou",
        "name_zh": "汕头·牛肉火锅朝圣线",
        "name_en": "Shantou Beef Hotpot Pilgrimage",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "shantou_beef_area",
        "seasonality": ["all_year"],
        "profile_fit": ["foodie", "friends", "couple"],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "汕头牛肉火锅是中国火锅届的天花板——2小时内现宰现切，部位讲究到极致。八合里/金厝柴/海记等名店需排队。",
        "experience_family": "food",
        "rhythm_role": "contrast",
        "energy_level": "low",
    },
    {
        "cluster_id": "cs_shantou_nanao_island",
        "circle_id": CIRCLE,
        "city_code": "shantou",
        "name_zh": "汕头·南澳岛海岛一日线",
        "name_en": "Shantou Nan'ao Island Day Trip",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "nanao_island",
        "seasonality": ["all_year", "summer"],
        "profile_fit": ["couple", "nature", "photo", "beach"],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "南澳大桥跨海+青澳湾海滩+风车群+海鲜大排档。广东最美海岛之一，需自驾或包车。",
        "experience_family": "sea",
        "rhythm_role": "peak",
        "energy_level": "high",
    },
    {
        "cluster_id": "cs_shantou_laojie_night",
        "circle_id": CIRCLE,
        "city_code": "shantou",
        "name_zh": "汕头·老街夜食补位线",
        "name_en": "Shantou Old Street Night Food",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "shantou_xiaogongyuan",
        "seasonality": ["all_year"],
        "profile_fit": ["foodie", "nightlife", "friends", "arrival_friendly"],
        "trip_role": "enrichment",
        "time_window_strength": "strong",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "国平路+长平路夜宵一条街：白糜配杂咸、肠粉、宵夜糜档。到达日晚间最佳补位。",
        "experience_family": "food",
        "rhythm_role": "utility",
        "energy_level": "low",
    },
    # ── 跨城 ────────────────────────────────────────────────────────────────
    {
        "cluster_id": "cs_fenghuang_shan_tea",
        "circle_id": CIRCLE,
        "city_code": "chaozhou",
        "name_zh": "潮州·凤凰山茶乡一日线",
        "name_en": "Phoenix Mountain Tea Plantation Day Trip",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "fenghuang_mountain",
        "seasonality": ["all_year", "spring"],
        "profile_fit": ["nature", "culture", "couple", "slow_travel"],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "凤凰山是单丛茶核心产区，乌岽山顶古茶树+茶农家访+天池。春季采茶季体验最佳。需包车。",
        "experience_family": "mountain",
        "rhythm_role": "contrast",
        "energy_level": "medium",
    },
    {
        "cluster_id": "cs_chaoshan_temple_circuit",
        "circle_id": CIRCLE,
        "city_code": "chaozhou",
        "name_zh": "潮汕·宗祠庙宇文化线",
        "name_en": "Chaoshan Ancestral Temple Circuit",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "chaozhou_old_city",
        "seasonality": ["all_year"],
        "profile_fit": ["culture", "history", "photo", "rainy_day_ok"],
        "trip_role": "enrichment",
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "己略黄公祠（国宝级木雕）+从熙公祠+韩文公祠。潮汕宗祠是中国最精致的民间建筑群之一。",
        "experience_family": "shrine",
        "rhythm_role": "contrast",
        "energy_level": "medium",
    },
    {
        "cluster_id": "cs_shantou_market_morning",
        "circle_id": CIRCLE,
        "city_code": "shantou",
        "name_zh": "汕头·早市粿条糜早线",
        "name_en": "Shantou Morning Market Breakfast",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "shantou_xiaogongyuan",
        "seasonality": ["all_year"],
        "profile_fit": ["foodie", "first_timer", "arrival_friendly"],
        "trip_role": "enrichment",
        "time_window_strength": "strong",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "潮汕早餐精华：猪血汤+粿条+白糜配杂咸+蚝烙。6:00-9:00最佳，之后关门。",
        "experience_family": "food",
        "rhythm_role": "utility",
        "energy_level": "low",
    },
]


async def seed():
    async with AsyncSessionLocal() as session:
        # 1. 城市圈
        existing_circle = await session.get(CityCircle, CIRCLE)
        if not existing_circle:
            known_fields = {c.key for c in CityCircle.__table__.columns}
            filtered = {k: v for k, v in CIRCLE_DEF.items() if k in known_fields}
            session.add(CityCircle(**filtered))
            logger.info("NEW circle: %s", CIRCLE)
        else:
            logger.info("SKIP circle: %s (exists)", CIRCLE)

        # 2. 活动簇
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
        logger.info("=== %s 完成: 新增=%d 跳过=%d 总计=%d ===",
                     CIRCLE, new_count, skip_count, len(CLUSTERS))


if __name__ == "__main__":
    asyncio.run(seed())
