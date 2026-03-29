"""
seed_tokyo_supplemental_clusters.py — 东京首都圈活动簇补全

新增 21 个活动簇：
  - 18 个来自原始数据（city_code 已修正为全名）
  - 3 个手工补充（冬季灯饰/下町美食/月岛文字烧）

数据来源：GPT-5.4 生成 + Opus 审核修正
幂等：cluster_id 已存在则 SKIP。

执行：
    python scripts/seed_tokyo_supplemental_clusters.py
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

CIRCLE = "tokyo_metropolitan_circle"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 活动簇数据
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CLUSTERS = [
    # ── 东京 ──────────────────────────────────────────────────────────────────
    {
        "cluster_id": "tok_eastside_classic_grand",
        "circle_id": CIRCLE, "city_code": "tokyo",
        "name_zh": "东京·东侧经典完整版",
        "name_en": "Tokyo Eastside Classic Grand Circuit",
        "level": "S", "default_duration": "full_day",
        "primary_corridor": "asakusa_ueno_marunouchi_ginza",
        "seasonality": ["all_year"],
        "profile_fit": ["first_timer", "culture", "citywalk", "photo"],
        "trip_role": "anchor",
        "time_window_strength": "medium", "reservation_pressure": "low",
        "secondary_attach_capacity": 3, "default_selected": True,
        "notes": "覆盖浅草寺、上野公园、东京站丸之内与银座，适合第一次来东京用一整天完成传统街景到都会门面的完整切换。",
    },
    {
        "cluster_id": "tok_westside_urban_grand",
        "circle_id": CIRCLE, "city_code": "tokyo",
        "name_zh": "东京·西侧都市完整版",
        "name_en": "Tokyo Westside Urban Grand Circuit",
        "level": "S", "default_duration": "full_day",
        "primary_corridor": "harajuku_shibuya_shinjuku",
        "seasonality": ["all_year"],
        "profile_fit": ["first_timer", "citywalk", "fashion", "nightview"],
        "trip_role": "anchor",
        "time_window_strength": "medium", "reservation_pressure": "low",
        "secondary_attach_capacity": 3, "default_selected": True,
        "notes": "以原宿、涩谷、新宿为主轴串起神宫外缘与都市夜景，通常会自然拖到傍晚后，明显影响西东京驻点与步行强度。",
    },
    {
        "cluster_id": "tok_roppongi_azabudai_art",
        "circle_id": CIRCLE, "city_code": "tokyo",
        "name_zh": "东京·六本木麻布台艺术线",
        "name_en": "Roppongi and Azabudai Art Skyline Route",
        "level": "A", "default_duration": "full_day",
        "primary_corridor": "roppongi_azabudai_toranomon",
        "seasonality": ["all_year"],
        "profile_fit": ["art", "couple", "photo", "design"],
        "trip_role": "anchor",
        "time_window_strength": "medium", "reservation_pressure": "medium",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "以森美术馆、东京城市观景与麻布台艺术空间为核心，适合从白天展览一路排到夜景收尾，热门展与数字艺术常有时段票压力。",
    },
    {
        "cluster_id": "tok_shimokitazawa_indie_vintage",
        "circle_id": CIRCLE, "city_code": "tokyo",
        "name_zh": "东京·下北泽独立潮流线",
        "name_en": "Shimokitazawa Indie Vintage Route",
        "level": "B", "default_duration": "half_day",
        "primary_corridor": "shimokitazawa_station_area",
        "seasonality": ["all_year"],
        "profile_fit": ["fashion", "music", "vintage", "youth"],
        "trip_role": "enrichment",
        "time_window_strength": "medium", "reservation_pressure": "none",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "围绕下北泽老铺中古店、唱片店与livehouse展开，建议下午后进入并接晚间小酒馆或演出，适合强风格用户单独占半天到一晚。",
    },
    {
        "cluster_id": "tok_kichijoji_inokashira_life",
        "circle_id": CIRCLE, "city_code": "tokyo",
        "name_zh": "东京·吉祥寺井之头生活线",
        "name_en": "Kichijoji and Inokashira Local Life Route",
        "level": "B", "default_duration": "half_day",
        "primary_corridor": "kichijoji_inokashira_park",
        "seasonality": ["all_year"],
        "profile_fit": ["couple", "family", "citywalk", "local_life"],
        "trip_role": "enrichment",
        "time_window_strength": "weak", "reservation_pressure": "none",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "以井之头公园、划船池与吉祥寺商店街为核心，更像东京本地生活样本，适合轻松半日并可自然接晚餐与小酒馆。",
    },
    {
        "cluster_id": "tok_akiba_ikebukuro_otaku_depth",
        "circle_id": CIRCLE, "city_code": "tokyo",
        "name_zh": "东京·秋叶原池袋二次元深度线",
        "name_en": "Akihabara and Ikebukuro Otaku Deep Dive",
        "level": "A", "default_duration": "full_day",
        "primary_corridor": "akihabara_ikebukuro",
        "seasonality": ["all_year"],
        "profile_fit": ["anime", "gaming", "shopping", "youth"],
        "trip_role": "anchor",
        "time_window_strength": "weak", "reservation_pressure": "low",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "把秋叶原电器街与池袋乙女路、Sunshine City一并处理，适合动漫游戏画像单独排满一天，明显影响采购预算与停留区域。",
    },
    {
        "cluster_id": "tok_seasonal_flower_axis",
        "circle_id": CIRCLE, "city_code": "tokyo",
        "name_zh": "东京·季节花景线",
        "name_en": "Tokyo Seasonal Flower and Foliage Axis",
        "level": "A", "default_duration": "full_day",
        "primary_corridor": "chidorigafuchi_shinjuku_gyoen_jingu_gaien",
        "seasonality": ["sakura", "autumn_leaves"],
        "profile_fit": ["couple", "photo", "citywalk", "seasonal"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "none",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "以千鸟渊、新宿御苑、神宫外苑等花景与银杏轴线为主，强依赖花期与光线窗口，命中季节时足以单独左右东京排程。",
    },
    {
        "cluster_id": "tok_night_observatory_axis",
        "circle_id": CIRCLE, "city_code": "tokyo",
        "name_zh": "东京·夜景展望台线",
        "name_en": "Tokyo Night Observatory Axis",
        "level": "A", "default_duration": "half_day",
        "primary_corridor": "shibuya_roppongi_shinjuku_observatories",
        "seasonality": ["all_year"],
        "profile_fit": ["couple", "photo", "nightview", "first_timer"],
        "trip_role": "enrichment",
        "time_window_strength": "strong", "reservation_pressure": "medium",
        "secondary_attach_capacity": 1, "default_selected": False,
        "notes": "围绕涩谷天空、六本木观景与都厅免费展望台做日落到夜景窗口，适合单独留出一个傍晚，热门时段常需提前锁票或排队。",
    },
    # ── 横滨 ──────────────────────────────────────────────────────────────────
    {
        "cluster_id": "yok_port_city_classic",
        "circle_id": CIRCLE, "city_code": "yokohama",
        "name_zh": "横滨·港城经典线",
        "name_en": "Yokohama Port City Classic Route",
        "level": "S", "default_duration": "full_day",
        "primary_corridor": "minato_mirai_red_brick_chinatown_yamashita",
        "seasonality": ["all_year"],
        "profile_fit": ["first_timer", "couple", "family", "photo"],
        "trip_role": "anchor",
        "time_window_strength": "medium", "reservation_pressure": "low",
        "secondary_attach_capacity": 3, "default_selected": True,
        "notes": "把港未来、红砖仓库、中华街、山下公园与海边步道作为完整日归线处理，白天夜晚都成立，通常会自然拉长到夜景时段。",
    },
    {
        "cluster_id": "yok_harbor_night_views",
        "circle_id": CIRCLE, "city_code": "yokohama",
        "name_zh": "横滨·海港夜景线",
        "name_en": "Yokohama Harbor Night View Route",
        "level": "A", "default_duration": "half_day",
        "primary_corridor": "osanbashi_red_brick_marine_tower",
        "seasonality": ["all_year"],
        "profile_fit": ["couple", "photo", "nightview"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "low",
        "secondary_attach_capacity": 1, "default_selected": False,
        "notes": "以大栈桥、红砖仓库、Marine Tower与海边步道夜景为核心，适合专门留出一晚并会直接影响是否在横滨住一晚。",
    },
    # ── 箱根 ──────────────────────────────────────────────────────────────────
    {
        "cluster_id": "hak_hakone_classic_loop",
        "circle_id": CIRCLE, "city_code": "hakone",
        "name_zh": "箱根·温泉环线完整版",
        "name_en": "Hakone Classic Onsen Loop",
        "level": "S", "default_duration": "full_day",
        "primary_corridor": "yumoto_gora_owakudani_lake_ashi",
        "seasonality": ["all_year"],
        "profile_fit": ["first_timer", "nature", "onsen", "couple"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "low",
        "secondary_attach_capacity": 2, "default_selected": True,
        "notes": "覆盖箱根汤本、强罗、大涌谷与芦之湖交通环线，强依赖缆车和海盗船运营时间，适合整天或拆成一晚两天处理。",
    },
    {
        "cluster_id": "hak_luxury_ryokan_retreat",
        "circle_id": CIRCLE, "city_code": "hakone",
        "name_zh": "箱根·豪华温泉酒店体验线",
        "name_en": "Hakone Luxury Ryokan Retreat",
        "level": "A", "default_duration": "full_day",
        "primary_corridor": "gora_miyanoshita_motohakone",
        "seasonality": ["all_year"],
        "profile_fit": ["couple", "luxury", "relax", "anniversary"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "high",
        "secondary_attach_capacity": 1, "default_selected": False,
        "notes": "以强罗、宫之下或元箱根一带高端旅馆为主角，核心是早晚餐、私汤与景观停留，本身就足以成立一晚住宿理由并显著改变预算。",
    },
    # ── 镰仓 ──────────────────────────────────────────────────────────────────
    {
        "cluster_id": "kam_temple_depth_route",
        "circle_id": CIRCLE, "city_code": "kamakura",
        "name_zh": "镰仓·寺社深度线",
        "name_en": "Kamakura Temple Depth Route",
        "level": "A", "default_duration": "full_day",
        "primary_corridor": "tsurugaoka_hachimangu_kitakamakura_hase",
        "seasonality": ["all_year"],
        "profile_fit": ["culture", "history", "citywalk", "photo"],
        "trip_role": "anchor",
        "time_window_strength": "medium", "reservation_pressure": "none",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "区别于江之岛日归，这条线以鹤冈八幡宫、北镰仓寺社与长谷一带为核心，更偏古都寺社密集步行，适合完整占用一天。",
    },
    {
        "cluster_id": "kam_kamakura_alps_hike",
        "circle_id": CIRCLE, "city_code": "kamakura",
        "name_zh": "镰仓·阿尔卑斯步道寺社线",
        "name_en": "Kamakura Alps Hiking and Temple Route",
        "level": "B", "default_duration": "full_day",
        "primary_corridor": "kitakamakura_ten_en_hiking_hase",
        "seasonality": ["all_year"],
        "profile_fit": ["hiking", "nature", "culture", "active"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "none",
        "secondary_attach_capacity": 1, "default_selected": False,
        "notes": "以天园或葛原冈到大佛步道串联寺社与山脊视野，强依赖白天体力与天气窗口，是命中徒步画像时会主导当天路线的活动簇。",
    },
    # ── 日光 ──────────────────────────────────────────────────────────────────
    {
        "cluster_id": "nik_okunikko_nature_onsen",
        "circle_id": CIRCLE, "city_code": "nikko",
        "name_zh": "日光·奥日光自然温泉线",
        "name_en": "Okunikko Nature and Onsen Route",
        "level": "A", "default_duration": "full_day",
        "primary_corridor": "lake_chuzenji_kegon_senjogahara_yumoto",
        "seasonality": ["summer", "autumn"],
        "profile_fit": ["nature", "onsen", "photo", "hiking"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "low",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "在世界遗产寺社之外，奥日光的中禅寺湖、华严瀑布、战场之原与温泉带本身就是独立主线，通常更适合整天甚至一晚。",
    },
    # ── 河口湖 ────────────────────────────────────────────────────────────────
    {
        "cluster_id": "kaw_fuji_view_onsen_stay",
        "circle_id": CIRCLE, "city_code": "kawaguchiko",
        "name_zh": "河口湖·富士景观温泉驻留线",
        "name_en": "Kawaguchiko Fuji View Onsen Stay",
        "level": "A", "default_duration": "full_day",
        "primary_corridor": "kawaguchiko_lakefront_mt_fuji_view",
        "seasonality": ["all_year"],
        "profile_fit": ["couple", "photo", "luxury", "relax"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "high",
        "secondary_attach_capacity": 1, "default_selected": False,
        "notes": "区别于单纯富士山打卡，这条线强调河口湖湖畔住一晚看日落日出与温泉景观，常会直接改变是否从东京外住一晚。",
    },
    # ── 轻井泽 ────────────────────────────────────────────────────────────────
    {
        "cluster_id": "kar_highland_retreat_day",
        "circle_id": CIRCLE, "city_code": "karuizawa",
        "name_zh": "轻井泽·高原避暑日归线",
        "name_en": "Karuizawa Highland Retreat Day Trip",
        "level": "A", "default_duration": "full_day",
        "primary_corridor": "old_karuizawa_kumobaike_nakakaruizawa",
        "seasonality": ["summer", "autumn"],
        "profile_fit": ["couple", "family", "nature", "shopping"],
        "trip_role": "anchor",
        "time_window_strength": "medium", "reservation_pressure": "low",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "以旧轻井泽银座、云场池与中轻井泽生活区为主轴，最适合夏季避暑与秋季高原漫游，适合从东京专门抽出一整天。",
    },
    # ── 补充：冬季灯饰 / 下町美食 / 月岛文字烧 ────────────────────────────────
    {
        "cluster_id": "tok_winter_illumination_circuit",
        "circle_id": CIRCLE, "city_code": "tokyo",
        "name_zh": "东京·冬季灯饰巡游线",
        "name_en": "Tokyo Winter Illumination Circuit",
        "level": "S", "default_duration": "half_day",
        "primary_corridor": "marunouchi_roppongi_omotesando",
        "seasonality": ["winter"],
        "profile_fit": ["couple", "photo", "festival"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "low",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "丸之内香槟金灯饰/六本木Hills蓝白光隧道/Midtown圣诞/惠比寿水晶吊灯，11月-2月限定，强夜间时间窗。",
    },
    {
        "cluster_id": "tok_shitamachi_food_crawl",
        "circle_id": CIRCLE, "city_code": "tokyo",
        "name_zh": "东京·下町美食散步线",
        "name_en": "Tokyo Shitamachi Food Crawl",
        "level": "A", "default_duration": "full_day",
        "primary_corridor": "tsukishima_tsukiji_yanaka",
        "seasonality": ["all_year"],
        "profile_fit": ["foodie", "citywalk", "couple", "local_life"],
        "trip_role": "anchor",
        "time_window_strength": "medium", "reservation_pressure": "low",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "月岛文字烧街80家+筑地场外市场+谷中银座夕阳阶梯，串联东京最有庶民烟火气的美食散步线。",
    },
    {
        "cluster_id": "tok_tsukishima_monja_bay",
        "circle_id": CIRCLE, "city_code": "tokyo",
        "name_zh": "东京·月岛文字烧湾岸线",
        "name_en": "Tokyo Tsukishima Monja & Bay Area",
        "level": "B", "default_duration": "half_day",
        "primary_corridor": "tsukishima_harumi",
        "seasonality": ["all_year"],
        "profile_fit": ["foodie", "local_life", "couple"],
        "trip_role": "enrichment",
        "time_window_strength": "medium", "reservation_pressure": "low",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "月岛西仲通文字烧午餐+晴海埠头公园夕阳，半天下町美食收尾线。",
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
        logger.info("东京首都圈活动簇补全完成: 新增=%d 跳过=%d 总计=%d", new_count, skip_count, len(CLUSTERS))


if __name__ == "__main__":
    asyncio.run(seed())
