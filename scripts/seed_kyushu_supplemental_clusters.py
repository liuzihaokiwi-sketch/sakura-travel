"""
seed_kyushu_supplemental_clusters.py — 九州温泉圈活动簇补全

新增 16 个活动簇：
  - 13 个主活动/anchor（含季节限定：灯笼祭、山笠等）
  - 3 个强次级/enrichment（温泉街散步、购物补位、美食补位）

数据来源：GPT-5.4 生成 + Opus 审核修正
幂等：cluster_id 已存在则 SKIP。

执行：
    python scripts/seed_kyushu_supplemental_clusters.py
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

CIRCLE = "kyushu_onsen_circle"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 主活动簇 (anchor)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ANCHOR_CLUSTERS = [
    # ── 福冈 ──────────────────────────────────────────────────────────────────
    {
        "cluster_id": "kyu_hakata_yatai_night_culture",
        "circle_id": CIRCLE, "city_code": "fukuoka",
        "name_zh": "福冈·博多屋台夜食文化线",
        "name_en": "Hakata Yatai Night Food Culture",
        "level": "A", "default_duration": "half_day",
        "primary_corridor": "hakata_nakasu_tenjin_night",
        "seasonality": ["all_year"],
        "profile_fit": ["food", "night", "friends"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "low",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "以中洲、天神与博多周边屋台为核心，夜间开摊时间窗非常明确，适合把晚餐、续摊与城市夜生活并成一整段体验。",
    },
    {
        "cluster_id": "kyu_dazaifu_tenmangu_culture",
        "circle_id": CIRCLE, "city_code": "fukuoka",
        "name_zh": "福冈·太宰府天满宫文化线",
        "name_en": "Dazaifu Tenmangu Cultural Route",
        "level": "A", "default_duration": "half_day",
        "primary_corridor": "dazaifu_tenmangu",
        "seasonality": ["all_year", "sakura", "autumn_leaves"],
        "profile_fit": ["culture", "family", "photo"],
        "trip_role": "anchor",
        "time_window_strength": "medium", "reservation_pressure": "low",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "以太宰府天满宫参拜表参道与周边文化设施为主，梅花季与考试季辨识度更强，是福冈最稳的半日至一日文化外挂机。",
    },
    {
        "cluster_id": "kyu_yanagawa_water_town_cruise",
        "circle_id": CIRCLE, "city_code": "fukuoka",
        "name_zh": "福冈·柳川水乡线",
        "name_en": "Yanagawa Water Town Cruise",
        "level": "A", "default_duration": "half_day",
        "primary_corridor": "yanagawa_canal",
        "seasonality": ["all_year", "sakura", "autumn_leaves", "winter"],
        "profile_fit": ["couple", "family", "photo"],
        "trip_role": "anchor",
        "time_window_strength": "medium", "reservation_pressure": "medium",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "以掘割游船和蒸笼鳗鱼为核心，船程本身就占去固定时段，春樱秋景和冬季暖桌船都会明显影响出发时间与日归节奏。",
    },
    {
        "cluster_id": "kyu_mojiko_retro_port_walk",
        "circle_id": CIRCLE, "city_code": "fukuoka",
        "name_zh": "福冈·门司港怀旧线",
        "name_en": "Mojiko Retro Port Walk",
        "level": "A", "default_duration": "half_day",
        "primary_corridor": "mojiko_retro",
        "seasonality": ["all_year"],
        "profile_fit": ["photo", "history", "couple"],
        "trip_role": "anchor",
        "time_window_strength": "medium", "reservation_pressure": "low",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "围绕门司港复古建筑群、关门海峡景观与港口散步展开，白天看建筑、傍晚看海峡灯光最顺，适合作为北九州独立半日主题线。",
    },
    {
        "cluster_id": "kyu_hakata_gion_yamakasa",
        "circle_id": CIRCLE, "city_code": "fukuoka",
        "name_zh": "福冈·博多祇园山笠线",
        "name_en": "Hakata Gion Yamakasa Festival Route",
        "level": "A", "default_duration": "full_day",
        "primary_corridor": "hakata_kushida_shrine_festival",
        "seasonality": ["summer"],
        "profile_fit": ["festival", "culture", "photo"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "high",
        "secondary_attach_capacity": 1, "default_selected": False,
        "notes": "以7月上半月的博多祇园山笠为核心，展示山笠与清晨追山时间点都很强，足以改变福冈城市住宿与观礼动线。",
    },
    # ── 别府 ──────────────────────────────────────────────────────────────────
    {
        "cluster_id": "kyu_beppu_jigoku_meguri_full",
        "circle_id": CIRCLE, "city_code": "beppu",
        "name_zh": "别府·地狱巡礼完整线",
        "name_en": "Beppu Jigoku Meguri Full Route",
        "level": "S", "default_duration": "full_day",
        "primary_corridor": "kannawa_shibaseki_jigoku",
        "seasonality": ["all_year"],
        "profile_fit": ["first_timer", "photo", "family"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "low",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "围绕海地狱等七大地狱展开，铁轮与柴石两片区分开且需要换乘或驾车衔接，通常会独立占掉别府完整观光日。",
    },
    # ── 由布院 ────────────────────────────────────────────────────────────────
    {
        "cluster_id": "kyu_yufuin_kinrin_onsen_stroll",
        "circle_id": CIRCLE, "city_code": "yufuin",
        "name_zh": "由布院·金鳞湖温泉街完整线",
        "name_en": "Yufuin Kinrin Lake and Onsen Town Route",
        "level": "S", "default_duration": "full_day",
        "primary_corridor": "yufuin_onsen_town",
        "seasonality": ["all_year", "autumn_leaves", "winter"],
        "profile_fit": ["couple", "photo", "relax"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "medium",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "以金鳞湖晨景、汤之坪街道步行与旅馆泡汤为主，早晨雾气和傍晚温泉节奏都很关键，常直接决定由布院是否住一晚。",
    },
    # ── 长崎 ──────────────────────────────────────────────────────────────────
    {
        "cluster_id": "kyu_nagasaki_bay_nightview_full",
        "circle_id": CIRCLE, "city_code": "nagasaki",
        "name_zh": "长崎·港城夜景完整版",
        "name_en": "Nagasaki Bay and Night View Full Route",
        "level": "S", "default_duration": "full_day",
        "primary_corridor": "dejima_oura_inasa",
        "seasonality": ["all_year"],
        "profile_fit": ["couple", "photo", "history"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "low",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "把出岛、大浦与山手片区串到稻佐山夜景收尾，白天看开港史、傍晚抢山顶视角，天然会主导长崎一整天与住宿节奏。",
    },
    {
        "cluster_id": "kyu_gunkanjima_cruise",
        "circle_id": CIRCLE, "city_code": "nagasaki",
        "name_zh": "长崎·军舰岛登陆航线",
        "name_en": "Gunkanjima Landing Cruise",
        "level": "A", "default_duration": "half_day",
        "primary_corridor": "nagasaki_port_gunkanjima",
        "seasonality": ["all_year", "summer"],
        "profile_fit": ["history", "photo", "industrial_heritage"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "high",
        "secondary_attach_capacity": 1, "default_selected": False,
        "notes": "以长崎港出发的军舰岛登陆巡航为核心，船班和海况决定成行率，通常需要提前预约并把前后半天都围绕它来排。",
    },
    {
        "cluster_id": "kyu_nagasaki_lantern_festival",
        "circle_id": CIRCLE, "city_code": "nagasaki",
        "name_zh": "长崎·灯笼祭线",
        "name_en": "Nagasaki Lantern Festival Route",
        "level": "A", "default_duration": "full_day",
        "primary_corridor": "shinchi_chinatown_central_nagasaki",
        "seasonality": ["winter"],
        "profile_fit": ["festival", "photo", "couple"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "high",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "农历新年前后全城灯会和夜间演出时间窗极强，会直接推高长崎住宿与晚间排程优先级，是典型季节限定主活动。",
    },
    # ── 熊本 ──────────────────────────────────────────────────────────────────
    {
        "cluster_id": "kyu_kumamoto_castle_suizenji_full",
        "circle_id": CIRCLE, "city_code": "kumamoto",
        "name_zh": "熊本·熊本城水前寺完整线",
        "name_en": "Kumamoto Castle and Suizenji Full Route",
        "level": "A", "default_duration": "full_day",
        "primary_corridor": "kumamoto_central_heritage",
        "seasonality": ["all_year", "sakura", "autumn_leaves"],
        "profile_fit": ["history", "family", "photo"],
        "trip_role": "anchor",
        "time_window_strength": "medium", "reservation_pressure": "low",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "以熊本城和水前寺成趣园组成城市文化主轴，城郭与回游庭园组合完整，适合拿出整天深挖熊本市内。",
    },
    {
        "cluster_id": "kyu_kurokawa_onsen_hideaway",
        "circle_id": CIRCLE, "city_code": "kumamoto",
        "name_zh": "熊本·黑川温泉隐世线",
        "name_en": "Kurokawa Onsen Hideaway Stay",
        "level": "S", "default_duration": "full_day",
        "primary_corridor": "kurokawa_onsen",
        "seasonality": ["all_year", "autumn_leaves", "winter"],
        "profile_fit": ["relax", "couple", "luxury"],
        "trip_role": "anchor",
        "time_window_strength": "medium", "reservation_pressure": "high",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "以山间温泉街散策、入汤手形外汤巡礼和旅馆住宿为核心，最适合专门住一晚放慢节奏，对自驾与驻点选择影响很大。",
    },
    # ── 鹿儿岛 ────────────────────────────────────────────────────────────────
    {
        "cluster_id": "kyu_ibusuki_sandbath_onsen",
        "circle_id": CIRCLE, "city_code": "kagoshima",
        "name_zh": "鹿儿岛·指宿砂蒸温泉线",
        "name_en": "Ibusuki Sand Bath Onsen Route",
        "level": "A", "default_duration": "half_day",
        "primary_corridor": "ibusuki_coastal_onsen",
        "seasonality": ["all_year"],
        "profile_fit": ["relax", "couple", "wellness"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "medium",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "以海滨砂蒸温泉为绝对主轴，再接常规温泉或海岸散步最顺，是鹿儿岛南下路线里辨识度最高的半日到一日型体验。",
    },
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 强次级/enrichment 簇
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ENRICHMENT_CLUSTERS = [
    {
        "cluster_id": "kyu_beppu_onsen_street_walk",
        "circle_id": CIRCLE, "city_code": "beppu",
        "name_zh": "别府·铁轮温泉街散步线",
        "name_en": "Beppu Kannawa Onsen Street Walk",
        "level": "B", "default_duration": "quarter_day",
        "primary_corridor": "kannawa_onsen_street",
        "seasonality": ["all_year"],
        "profile_fit": ["relax", "couple", "food"],
        "trip_role": "enrichment",
        "time_window_strength": "medium", "reservation_pressure": "none",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "铁轮温泉街蒸笼地狱蒸料理+足汤+温泉蒸气氛围，最适合挂在地狱巡礼后的松弛收口。",
    },
    {
        "cluster_id": "kyu_fukuoka_tenjin_shopping",
        "circle_id": CIRCLE, "city_code": "fukuoka",
        "name_zh": "福冈·天神地下街购物补位线",
        "name_en": "Fukuoka Tenjin Underground Shopping",
        "level": "B", "default_duration": "half_day",
        "primary_corridor": "tenjin_underground",
        "seasonality": ["all_year"],
        "profile_fit": ["shopping", "couple", "family"],
        "trip_role": "enrichment",
        "time_window_strength": "weak", "reservation_pressure": "none",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "天神地下街600米150+店铺+Canal City博多，适合雨天或到达/离开日的购物补位。",
    },
    {
        "cluster_id": "kyu_kagoshima_tenmonkan_food",
        "circle_id": CIRCLE, "city_code": "kagoshima",
        "name_zh": "鹿儿岛·天文馆通美食补位线",
        "name_en": "Kagoshima Tenmonkan Food Street",
        "level": "B", "default_duration": "quarter_day",
        "primary_corridor": "tenmonkan_arcade",
        "seasonality": ["all_year"],
        "profile_fit": ["foodie", "local_life"],
        "trip_role": "enrichment",
        "time_window_strength": "medium", "reservation_pressure": "none",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "黑猪涮涮锅/白熊刨冰/芋烧酒，鹿儿岛最集中的本地美食商店街。",
    },
]

ALL_CLUSTERS = ANCHOR_CLUSTERS + ENRICHMENT_CLUSTERS


async def seed():
    async with AsyncSessionLocal() as session:
        new_count = skip_count = 0
        for data in ALL_CLUSTERS:
            existing = await session.get(ActivityCluster, data["cluster_id"])
            if existing:
                skip_count += 1
                logger.info("  SKIP: %s", data["cluster_id"])
                continue
            cluster = ActivityCluster(**data)
            session.add(cluster)
            new_count += 1
            logger.info("  NEW:  %s (%s) [%s]", data["cluster_id"], data["city_code"], data["level"])
        await session.commit()
        logger.info("=" * 50)
        logger.info("九州温泉圈活动簇补全完成: 新增=%d 跳过=%d 总计=%d", new_count, skip_count, len(ALL_CLUSTERS))


if __name__ == "__main__":
    asyncio.run(seed())
