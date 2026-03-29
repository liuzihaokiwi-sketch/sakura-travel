"""
seed_hokkaido_supplemental_clusters.py — 北海道自然圈活动簇补全

新增 15 个活动簇：
  - 来自原始数据（city_code 已修正为全名，hok 前缀按实际地理归属修正）

数据来源：GPT-5.4 生成 + Opus 审核修正
幂等：cluster_id 已存在则 SKIP。

执行：
    python scripts/seed_hokkaido_supplemental_clusters.py
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

CIRCLE = "hokkaido_nature_circle"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 活动簇数据
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CLUSTERS = [
    # ── 札幌 ──────────────────────────────────────────────────────────────────
    {
        "cluster_id": "sap_sapporo_food_crawl",
        "circle_id": CIRCLE, "city_code": "sapporo",
        "name_zh": "札幌·都市美食巡游线",
        "name_en": "Sapporo Urban Food Crawl",
        "level": "A", "default_duration": "half_day",
        "primary_corridor": "sapporo_central",
        "seasonality": ["all_year"],
        "profile_fit": ["food", "couple", "friends"],
        "trip_role": "anchor",
        "time_window_strength": "medium", "reservation_pressure": "medium",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "以札幌市中心为主轴，围绕汤咖喱、成吉思汗与回转寿司展开，晚餐与夜间时段表现最好，适合住札幌连吃一整段。",
    },
    {
        "cluster_id": "sap_sapporo_beer_heritage",
        "circle_id": CIRCLE, "city_code": "sapporo",
        "name_zh": "札幌·啤酒博物馆历史线",
        "name_en": "Sapporo Beer Heritage Route",
        "level": "B", "default_duration": "half_day",
        "primary_corridor": "sapporo_beer_east",
        "seasonality": ["all_year"],
        "profile_fit": ["food", "culture", "friends"],
        "trip_role": "enrichment",
        "time_window_strength": "medium", "reservation_pressure": "low",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "以札幌啤酒博物馆与啤酒园用餐为核心，是日本少见能把开拓史和啤酒体验合在一起的半日型主题线。",
    },
    {
        "cluster_id": "sap_sapporo_snow_festival",
        "circle_id": CIRCLE, "city_code": "sapporo",
        "name_zh": "札幌·雪祭冬季限定线",
        "name_en": "Sapporo Snow Festival Route",
        "level": "S", "default_duration": "full_day",
        "primary_corridor": "odori_susukino",
        "seasonality": ["winter"],
        "profile_fit": ["winter", "photo", "family"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "high",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "以大通会场为核心串联札幌雪祭多会场与夜间灯光，冬季限定且会显著抬高札幌住宿与行程预订压力。",
    },
    # ── 小樽 ──────────────────────────────────────────────────────────────────
    {
        "cluster_id": "ota_otaru_port_town_walk",
        "circle_id": CIRCLE, "city_code": "otaru",
        "name_zh": "小樽·港町经典完整线",
        "name_en": "Otaru Port Town Classic Loop",
        "level": "S", "default_duration": "full_day",
        "primary_corridor": "otaru_port",
        "seasonality": ["all_year"],
        "profile_fit": ["couple", "photo", "food"],
        "trip_role": "anchor",
        "time_window_strength": "medium", "reservation_pressure": "low",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "以小樽运河、堺町通与寿司街为核心，白天逛街看仓库街景，傍晚转入港城夜色与海鲜晚餐最顺。",
    },
    # ── 登别 ──────────────────────────────────────────────────────────────────
    {
        "cluster_id": "nob_noboribetsu_onsen_healing",
        "circle_id": CIRCLE, "city_code": "noboribetsu",
        "name_zh": "登别·温泉疗愈线",
        "name_en": "Noboribetsu Onsen Healing Stay",
        "level": "S", "default_duration": "full_day",
        "primary_corridor": "noboribetsu_onsen",
        "seasonality": ["all_year"],
        "profile_fit": ["relax", "couple", "family"],
        "trip_role": "anchor",
        "time_window_strength": "medium", "reservation_pressure": "low",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "以地狱谷、温泉街步行与旅馆泡汤为主，适合专门住一晚放慢节奏，和札幌或洞爷湖形成明显换驻点。",
    },
    # ── 洞爷湖 ────────────────────────────────────────────────────────────────
    {
        "cluster_id": "toy_lake_toya_volcano_onsen",
        "circle_id": CIRCLE, "city_code": "toya",
        "name_zh": "洞爷湖·火山温泉景观线",
        "name_en": "Lake Toya Volcano and Onsen Scenic Stay",
        "level": "S", "default_duration": "full_day",
        "primary_corridor": "toya_lakeside",
        "seasonality": ["all_year", "summer"],
        "profile_fit": ["couple", "photo", "relax"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "medium",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "围绕洞爷湖温泉街、火山地貌与湖景展开，4月下旬到10月底夜间烟火加成明显，常值得独立住一晚。",
    },
    # ── 函馆 ──────────────────────────────────────────────────────────────────
    {
        "cluster_id": "hak_hakodate_bay_nightview_full",
        "circle_id": CIRCLE, "city_code": "hakodate",
        "name_zh": "函馆·港城夜景完整版",
        "name_en": "Hakodate Bay and Night View Full Route",
        "level": "S", "default_duration": "full_day",
        "primary_corridor": "hakodate_bay",
        "seasonality": ["all_year"],
        "profile_fit": ["couple", "photo", "food"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "low",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "把朝市、元町坡道街景与函馆山夜景串成完整一天，晨间与日落后都有明确时间窗，通常会主导函馆住宿节奏。",
    },
    # ── 富良野 ────────────────────────────────────────────────────────────────
    {
        "cluster_id": "fur_furano_winter_snow_resort",
        "circle_id": CIRCLE, "city_code": "furano",
        "name_zh": "富良野·冬季雪场体验线",
        "name_en": "Furano Winter Snow Resort Experience",
        "level": "A", "default_duration": "full_day",
        "primary_corridor": "furano_ski",
        "seasonality": ["winter"],
        "profile_fit": ["snow", "family", "couple"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "high",
        "secondary_attach_capacity": 1, "default_selected": False,
        "notes": "以富良野滑雪场及周边雪上活动为核心，冬季限定且对住宿与进出路线影响很大，适合单独拿出完整雪场日。",
    },
    # ── 旭川 ──────────────────────────────────────────────────────────────────
    {
        "cluster_id": "asa_daisetsuzan_green_hiking",
        "circle_id": CIRCLE, "city_code": "asahikawa",
        "name_zh": "大雪山·绿季自然徒步线",
        "name_en": "Daisetsuzan Green Season Hiking Route",
        "level": "A", "default_duration": "full_day",
        "primary_corridor": "daisetsuzan_asahidake",
        "seasonality": ["summer", "autumn"],
        "profile_fit": ["nature", "hiking", "photo"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "medium",
        "secondary_attach_capacity": 1, "default_selected": False,
        "notes": "以旭岳或大雪山徒步为主，需要看天气、缆车与白天长度安排，通常会把旭川周边或山麓温泉住宿带进来。",
    },
    {
        "cluster_id": "asa_sounkyo_kurodake_onsen",
        "circle_id": CIRCLE, "city_code": "asahikawa",
        "name_zh": "层云峡·温泉峡谷大雪山线",
        "name_en": "Sounkyo Onsen and Kurodake Route",
        "level": "A", "default_duration": "full_day",
        "primary_corridor": "sounkyo_kurodake",
        "seasonality": ["summer", "autumn", "winter"],
        "profile_fit": ["nature", "photo", "relax"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "medium",
        "secondary_attach_capacity": 1, "default_selected": False,
        "notes": "以层云峡温泉、黑岳缆车与大雪山山景为核心，受缆车、红叶与雪季时窗影响明显，常值得专门住峡谷温泉区。",
    },
    {
        "cluster_id": "asa_kurodake_autumn_leaves",
        "circle_id": CIRCLE, "city_code": "asahikawa",
        "name_zh": "黑岳·红叶缆车线",
        "name_en": "Kurodake Autumn Foliage Ropeway Route",
        "level": "A", "default_duration": "half_day",
        "primary_corridor": "sounkyo_kurodake",
        "seasonality": ["autumn"],
        "profile_fit": ["photo", "nature", "couple"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "medium",
        "secondary_attach_capacity": 1, "default_selected": False,
        "notes": "以层云峡黑岳缆车看高山红叶为核心，北海道红叶启动早且窗口短，最适合和层云峡温泉住宿打包安排。",
    },
    # ── 二世谷（归属札幌） ────────────────────────────────────────────────────
    {
        "cluster_id": "hok_niseko_onsen_resort",
        "circle_id": CIRCLE, "city_code": "sapporo",
        "name_zh": "二世谷·温泉度假线",
        "name_en": "Niseko Onsen Resort Stay",
        "level": "A", "default_duration": "full_day",
        "primary_corridor": "niseko_resort",
        "seasonality": ["winter", "summer", "autumn"],
        "profile_fit": ["couple", "relax", "luxury"],
        "trip_role": "anchor",
        "time_window_strength": "medium", "reservation_pressure": "medium",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "以二世谷山景温泉酒店、度假村节奏与羊蹄山景观为核心，适合不只滑雪而是专门住进度假区放松一晚以上。",
    },
    # ── 支笏湖（归属札幌） ────────────────────────────────────────────────────
    {
        "cluster_id": "hok_shikotsu_lake_nature_escape",
        "circle_id": CIRCLE, "city_code": "sapporo",
        "name_zh": "支笏湖·自然避世线",
        "name_en": "Lake Shikotsu Nature Escape",
        "level": "A", "default_duration": "half_day",
        "primary_corridor": "shikotsu_lake",
        "seasonality": ["all_year", "winter"],
        "profile_fit": ["nature", "photo", "relax"],
        "trip_role": "anchor",
        "time_window_strength": "medium", "reservation_pressure": "low",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "以支笏湖湖岸风景、轻户外和湖畔温泉为主，冬季冰涛祭加成强，最适合从札幌或新千岁切出半天到一晚。",
    },
    # ── 余市（归属小樽） ──────────────────────────────────────────────────────
    {
        "cluster_id": "hok_yoichi_whisky_distillery",
        "circle_id": CIRCLE, "city_code": "otaru",
        "name_zh": "余市·威士忌蒸馏所线",
        "name_en": "Yoichi Whisky Distillery Route",
        "level": "B", "default_duration": "half_day",
        "primary_corridor": "yoichi_coast",
        "seasonality": ["all_year"],
        "profile_fit": ["food", "culture", "couple"],
        "trip_role": "enrichment",
        "time_window_strength": "strong", "reservation_pressure": "high",
        "secondary_attach_capacity": 1, "default_selected": False,
        "notes": "以余市蒸馏所导览、试饮与海边小镇停留为主，导览预约和开放时间会直接决定能否从小樽线顺利外挂。",
    },
]


async def seed():
    async with AsyncSessionLocal() as session:
        new_count = skip_count = 0
        for data in CLUSTERS:
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
        logger.info("北海道自然圈活动簇补全完成: 新增=%d 跳过=%d 总计=%d", new_count, skip_count, len(CLUSTERS))


if __name__ == "__main__":
    asyncio.run(seed())
