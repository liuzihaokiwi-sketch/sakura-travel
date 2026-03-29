"""
seed_family_shopping_clusters.py — 亲子线 + 购物专线补充

覆盖 Task 8 的两个缺口：
1. 非乐园型亲子活动（动物园/水族馆/科技馆/手工体验）
2. 强购物专线（对购物型用户来说是 A/S 级）

跨东京、关西、广府三个圈。

执行：python scripts/seed_family_shopping_clusters.py
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
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 东京圈 亲子线
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {
        "cluster_id": "tok_ueno_zoo_museum_family",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·上野动物园+科博馆亲子线",
        "name_en": "Tokyo Ueno Zoo & Science Museum Family",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "ueno_park",
        "seasonality": ["all_year"],
        "profile_fit": ["family_child", "nature", "culture", "rainy_day_ok"],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "上野动物园（大熊猫）+国立科学博物馆+上野公园。全天亲子行程，雨天可在博物馆度过。",
        "experience_family": "locallife",
        "rhythm_role": "contrast",
        "energy_level": "medium",
        "upgrade_triggers": {"party_types": ["family_child"]},
    },
    {
        "cluster_id": "tok_sanrio_puroland_family",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·三丽鸥彩虹乐园亲子线",
        "name_en": "Tokyo Sanrio Puroland Family",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "tama",
        "seasonality": ["all_year"],
        "profile_fit": ["family_child", "couple", "rainy_day_ok"],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 0,
        "default_selected": False,
        "notes": "Hello Kitty 主题室内乐园，全室内不受天气影响。从新宿约40分钟。适合低龄儿童家庭。",
        "experience_family": "themepark",
        "rhythm_role": "peak",
        "energy_level": "medium",
        "upgrade_triggers": {"party_types": ["family_child"]},
    },
    {
        "cluster_id": "tok_odaiba_kidzania_family",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·台场KidZania职业体验亲子线",
        "name_en": "Tokyo Odaiba KidZania Family",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "odaiba",
        "seasonality": ["all_year"],
        "profile_fit": ["family_child", "rainy_day_ok"],
        "trip_role": "enrichment",
        "time_window_strength": "medium",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "KidZania东京（儿童职业体验）+DiverCity高达。全室内，适合雨天或亲子半日补位。",
        "experience_family": "locallife",
        "rhythm_role": "utility",
        "energy_level": "medium",
        "upgrade_triggers": {"party_types": ["family_child"]},
    },
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 东京圈 购物线
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {
        "cluster_id": "tok_ginza_omotesando_shopping",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·银座表参道奢侈品购物线",
        "name_en": "Tokyo Ginza & Omotesando Luxury Shopping",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "ginza_omotesando",
        "seasonality": ["all_year"],
        "profile_fit": ["shopping", "couple", "fashion"],
        "trip_role": "anchor",
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "银座和光+三越+GINZA SIX 上午，表参道 Hills+Laforet 下午。东京顶级购物一日线。",
        "experience_family": "locallife",
        "rhythm_role": "contrast",
        "energy_level": "medium",
        "upgrade_triggers": {"tags": ["shopping", "luxury", "fashion"]},
    },
    {
        "cluster_id": "tok_akihabara_otaku_shopping",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·秋叶原动漫周边购物线",
        "name_en": "Tokyo Akihabara Otaku Shopping",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "akihabara",
        "seasonality": ["all_year"],
        "profile_fit": ["anime", "shopping", "friends", "young", "rainy_day_ok"],
        "trip_role": "anchor",
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "电器街+Animate+Mandarake+中野百老汇。动漫/游戏/手办/古着购物天堂。室内为主。",
        "experience_family": "locallife",
        "rhythm_role": "utility",
        "energy_level": "medium",
        "upgrade_triggers": {"tags": ["anime", "otaku", "gaming"]},
    },
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 关西圈 亲子线
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {
        "cluster_id": "osa_kaiyukan_family_full",
        "circle_id": "kansai_classic_circle",
        "city_code": "osaka",
        "name_zh": "大阪·海游馆+天保山亲子线",
        "name_en": "Osaka Kaiyukan Aquarium & Tempozan Family",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "tempozan",
        "seasonality": ["all_year"],
        "profile_fit": ["family_child", "couple", "rainy_day_ok"],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "海游馆（世界最大级水族馆，鲸鲨）+天保山摩天轮+LEGOLAND Discovery Center。全天亲子行程。",
        "experience_family": "sea",
        "rhythm_role": "peak",
        "energy_level": "medium",
        "upgrade_triggers": {"party_types": ["family_child"]},
    },
    {
        "cluster_id": "kyo_wagashi_craft_family",
        "circle_id": "kansai_classic_circle",
        "city_code": "kyoto",
        "name_zh": "京都·和菓子制作+扎染体验亲子线",
        "name_en": "Kyoto Wagashi & Tie-dye Craft Family",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "kyo_downtown",
        "seasonality": ["all_year"],
        "profile_fit": ["family_child", "couple", "culture", "rainy_day_ok"],
        "trip_role": "enrichment",
        "time_window_strength": "medium",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "和菓子手作体验（约90分钟）+京友禅扎染体验。室内手工活动，雨天友好，适合亲子或情侣。",
        "experience_family": "art",
        "rhythm_role": "recovery",
        "energy_level": "low",
        "upgrade_triggers": {"party_types": ["family_child", "couple"]},
    },
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 关西圈 购物线
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {
        "cluster_id": "osa_shinsaibashi_full_shopping",
        "circle_id": "kansai_classic_circle",
        "city_code": "osaka",
        "name_zh": "大阪·心斋桥道顿堀全日购物线",
        "name_en": "Osaka Shinsaibashi & Dotonbori Full Day Shopping",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "shinsaibashi_dotonbori",
        "seasonality": ["all_year"],
        "profile_fit": ["shopping", "food", "friends", "first_timer"],
        "trip_role": "anchor",
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "心斋桥筋购物街+大丸百货+道顿堀美食+美国村潮牌+堀江家具杂货。购物型用户的大阪核心一天。",
        "experience_family": "locallife",
        "rhythm_role": "contrast",
        "energy_level": "medium",
        "upgrade_triggers": {"tags": ["shopping"]},
    },
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 广府圈 亲子线 + 购物线
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {
        "cluster_id": "gz_chimelong_family",
        "circle_id": "guangfu_circle",
        "city_code": "guangzhou",
        "name_zh": "广州·长隆野生动物世界亲子线",
        "name_en": "Guangzhou Chimelong Safari Park Family",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "gz_chimelong",
        "seasonality": ["all_year"],
        "profile_fit": ["family_child", "nature"],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 0,
        "default_selected": False,
        "notes": "亚洲最大野生动物园+自驾观赏区+考拉馆+长颈鹿喂食。全天亲子行程。晚上可看长隆国际大马戏。",
        "experience_family": "themepark",
        "rhythm_role": "peak",
        "energy_level": "high",
        "upgrade_triggers": {"party_types": ["family_child"]},
    },
    {
        "cluster_id": "hk_harbour_city_shopping",
        "circle_id": "guangfu_circle",
        "city_code": "hongkong",
        "name_zh": "香港·海港城+铜锣湾购物线",
        "name_en": "Hong Kong Harbour City & Causeway Bay Shopping",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "tsimshatsui_causewaybay",
        "seasonality": ["all_year"],
        "profile_fit": ["shopping", "couple", "fashion"],
        "trip_role": "anchor",
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "海港城（全港最大购物中心）上午+天星小轮过海+铜锣湾SOGO/时代广场下午。购物型用户的香港核心一天。",
        "experience_family": "locallife",
        "rhythm_role": "contrast",
        "energy_level": "medium",
        "upgrade_triggers": {"tags": ["shopping", "luxury"]},
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
        logger.info("=== 亲子/购物专线 完成: 新增=%d 跳过=%d 总计=%d ===",
                     new_count, skip_count, len(CLUSTERS))


if __name__ == "__main__":
    asyncio.run(seed())
