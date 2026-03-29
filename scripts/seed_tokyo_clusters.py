"""
seed_tokyo_metropolitan_circle_clusters.py — tokyo_metropolitan_circle 活动簇数据

从 mojor/ 目录转换生成。
幂等：cluster_id 已存在则 SKIP。

执行：
    python scripts/seed_tokyo_clusters.py
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
    {
        "cluster_id": "tok_eastside_classic_grand",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·东侧经典完整版",
        "name_en": "Tokyo Eastside Classic Grand Circuit",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "asakusa_ueno_marunouchi_ginza",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "first_timer",
            "culture",
            "citywalk",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 3,
        "default_selected": True,
        "notes": "覆盖浅草寺、上野公园、东京站丸之内与银座，适合第一次来东京用一整天完成传统街景到都会门面的完整切换。",
        "experience_family": "shrine",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "tok_westside_urban_grand",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·西侧都市完整版",
        "name_en": "Tokyo Westside Urban Grand Circuit",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "harajuku_shibuya_shinjuku",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "first_timer",
            "citywalk",
            "fashion",
            "nightview"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 3,
        "default_selected": True,
        "notes": "以原宿、涩谷、新宿为主轴串起神宫外缘与都市夜景，通常会自然拖到傍晚后，明显影响西东京驻点与步行强度。",
        "experience_family": "citynight",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "tok_roppongi_azabudai_art",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·六本木麻布台艺术线",
        "name_en": "Roppongi and Azabudai Art Skyline Route",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "roppongi_azabudai_toranomon",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "art",
            "couple",
            "photo",
            "design"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "以森美术馆、东京城市观景与麻布台艺术空间为核心，适合从白天展览一路排到夜景收尾，热门展与数字艺术常有时段票压力。",
        "experience_family": "art",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "tok_shimokitazawa_indie_vintage",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·下北泽独立潮流线",
        "name_en": "Shimokitazawa Indie Vintage Route",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "shimokitazawa_station_area",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "fashion",
            "music",
            "vintage",
            "youth"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "medium",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "围绕下北泽老铺中古店、唱片店与livehouse展开，建议下午后进入并接晚间小酒馆或演出，适合强风格用户单独占半天到一晚。",
        "experience_family": "locallife",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "tok_kichijoji_inokashira_life",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·吉祥寺井之头生活线",
        "name_en": "Kichijoji and Inokashira Local Life Route",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "kichijoji_inokashira_park",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "couple",
            "family",
            "citywalk",
            "local_life"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "以井之头公园、划船池与吉祥寺商店街为核心，更像东京本地生活样本，适合轻松半日并可自然接晚餐与小酒馆。",
        "experience_family": "locallife",
        "rhythm_role": "recovery",
        "energy_level": "low"
    },
    {
        "cluster_id": "tok_akiba_ikebukuro_otaku_depth",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·秋叶原池袋二次元深度线",
        "name_en": "Akihabara and Ikebukuro Otaku Deep Dive",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "akihabara_ikebukuro",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "anime",
            "gaming",
            "shopping",
            "youth"
        ],
        "trip_role": "anchor",
        "time_window_strength": "weak",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "把秋叶原电器街与池袋乙女路、Sunshine City一并处理，适合动漫游戏画像单独排满一天，明显影响采购预算与停留区域。",
        "experience_family": "themepark",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "tok_seasonal_flower_axis",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·季节花景线",
        "name_en": "Tokyo Seasonal Flower and Foliage Axis",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "chidorigafuchi_shinjuku_gyoen_jingu_gaien",
        "seasonality": [
            "sakura",
            "autumn_leaves"
        ],
        "profile_fit": [
            "couple",
            "photo",
            "citywalk",
            "seasonal"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "以千鸟渊、新宿御苑、神宫外苑等花景与银杏轴线为主，强依赖花期与光线窗口，命中季节时足以单独左右东京排程。",
        "experience_family": "flower",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "tok_night_observatory_axis",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·夜景展望台线",
        "name_en": "Tokyo Night Observatory Axis",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "shibuya_roppongi_shinjuku_observatories",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "couple",
            "photo",
            "nightview",
            "first_timer"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "围绕涩谷天空、六本木观景与都厅免费展望台做日落到夜景窗口，适合单独留出一个傍晚，热门时段常需提前锁票或排队。",
        "experience_family": "citynight",
        "rhythm_role": "contrast",
        "energy_level": "low"
    },
    {
        "cluster_id": "yok_port_city_classic",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "yokohama",
        "name_zh": "横滨·港城经典线",
        "name_en": "Yokohama Port City Classic Route",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "minato_mirai_red_brick_chinatown_yamashita",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "first_timer",
            "couple",
            "family",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 3,
        "default_selected": True,
        "notes": "把港未来、红砖仓库、中华街、山下公园与海边步道作为完整日归线处理，白天夜晚都成立，通常会自然拉长到夜景时段。",
        "experience_family": "sea",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "yok_harbor_night_views",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "yokohama",
        "name_zh": "横滨·海港夜景线",
        "name_en": "Yokohama Harbor Night View Route",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "osanbashi_red_brick_marine_tower",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "couple",
            "photo",
            "nightview"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "以大栈桥、红砖仓库、Marine Tower与海边步道夜景为核心，适合专门留出一晚并会直接影响是否在横滨住一晚。",
        "experience_family": "sea",
        "rhythm_role": "contrast",
        "energy_level": "low"
    },
    {
        "cluster_id": "hak_hakone_classic_loop",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "hakone",
        "name_zh": "箱根·温泉环线完整版",
        "name_en": "Hakone Classic Onsen Loop",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "yumoto_gora_owakudani_lake_ashi",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "first_timer",
            "nature",
            "onsen",
            "couple"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": True,
        "notes": "覆盖箱根汤本、强罗、大涌谷与芦之湖交通环线，强依赖缆车和海盗船运营时间，适合整天或拆成一晚两天处理。",
        "experience_family": "mountain",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "hak_luxury_ryokan_retreat",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "hakone",
        "name_zh": "箱根·豪华温泉酒店体验线",
        "name_en": "Hakone Luxury Ryokan Retreat",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "gora_miyanoshita_motohakone",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "couple",
            "luxury",
            "relax",
            "anniversary"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "以强罗、宫之下或元箱根一带高端旅馆为主角，核心是早晚餐、私汤与景观停留，本身就足以成立一晚住宿理由并显著改变预算。",
        "experience_family": "onsen",
        "rhythm_role": "recovery",
        "energy_level": "low"
    },
    {
        "cluster_id": "kam_temple_depth_route",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "kamakura",
        "name_zh": "镰仓·寺社深度线",
        "name_en": "Kamakura Temple Depth Route",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "tsurugaoka_hachimangu_kitakamakura_hase",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "culture",
            "history",
            "citywalk",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "区别于江之岛日归，这条线以鹤冈八幡宫、北镰仓寺社与长谷一带为核心，更偏古都寺社密集步行，适合完整占用一天。",
        "experience_family": "shrine",
        "rhythm_role": "contrast",
        "energy_level": "high"
    },
    {
        "cluster_id": "kam_kamakura_alps_hike",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "kamakura",
        "name_zh": "镰仓·阿尔卑斯步道寺社线",
        "name_en": "Kamakura Alps Hiking and Temple Route",
        "level": "B",
        "default_duration": "full_day",
        "primary_corridor": "kitakamakura_ten_en_hiking_hase",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "hiking",
            "nature",
            "culture",
            "active"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "strong",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "以天园或葛原冈到大佛步道串联寺社与山脊视野，强依赖白天体力与天气窗口，是命中徒步画像时会主导当天路线的活动簇。",
        "experience_family": "mountain",
        "rhythm_role": "contrast",
        "energy_level": "high"
    },
    {
        "cluster_id": "nik_okunikko_nature_onsen",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "nikko",
        "name_zh": "日光·奥日光自然温泉线",
        "name_en": "Okunikko Nature and Onsen Route",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "lake_chuzenji_kegon_senjogahara_yumoto",
        "seasonality": [
            "summer",
            "autumn"
        ],
        "profile_fit": [
            "nature",
            "onsen",
            "photo",
            "hiking"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "在世界遗产寺社之外，奥日光的中禅寺湖、华严瀑布、战场之原与温泉带本身就是独立主线，通常更适合整天甚至一晚。",
        "experience_family": "mountain",
        "rhythm_role": "contrast",
        "energy_level": "high"
    },
    {
        "cluster_id": "kaw_fuji_view_onsen_stay",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "kawaguchiko",
        "name_zh": "河口湖·富士景观温泉驻留线",
        "name_en": "Kawaguchiko Fuji View Onsen Stay",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "kawaguchiko_lakefront_mt_fuji_view",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "couple",
            "photo",
            "luxury",
            "relax"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "区别于单纯富士山打卡，这条线强调河口湖湖畔住一晚看日落日出与温泉景观，常会直接改变是否从东京外住一晚。",
        "experience_family": "mountain",
        "rhythm_role": "peak",
        "energy_level": "medium"
    },
    {
        "cluster_id": "kar_highland_retreat_day",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "karuizawa",
        "name_zh": "轻井泽·高原避暑日归线",
        "name_en": "Karuizawa Highland Retreat Day Trip",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "old_karuizawa_kumobaike_nakakaruizawa",
        "seasonality": [
            "summer",
            "autumn"
        ],
        "profile_fit": [
            "couple",
            "family",
            "nature",
            "shopping"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "以旧轻井泽银座、云场池与中轻井泽生活区为主轴，最适合夏季避暑与秋季高原漫游，适合从东京专门抽出一整天。",
        "experience_family": "locallife",
        "rhythm_role": "recovery",
        "energy_level": "medium"
    },
    {
        "cluster_id": "tok_winter_illumination_circuit",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·冬季灯饰巡游线",
        "name_en": "Tokyo Winter Illumination Circuit",
        "level": "S",
        "default_duration": "half_day",
        "primary_corridor": "marunouchi_roppongi_omotesando",
        "seasonality": [
            "winter"
        ],
        "profile_fit": [
            "couple",
            "photo",
            "festival"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "丸之内香槟金灯饰/六本木Hills蓝白光隧道/Midtown圣诞/惠比寿水晶吊灯，11月-2月限定，强夜间时间窗。",
        "experience_family": "citynight",
        "rhythm_role": "peak",
        "energy_level": "medium"
    },
    {
        "cluster_id": "tok_shitamachi_food_crawl",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·下町美食散步线",
        "name_en": "Tokyo Shitamachi Food Crawl",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "tsukishima_tsukiji_yanaka",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "foodie",
            "citywalk",
            "couple",
            "local_life"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "月岛文字烧街80家+筑地场外市场+谷中银座夕阳阶梯，串联东京最有庶民烟火气的美食散步线。",
        "experience_family": "food",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "tok_tsukishima_monja_bay",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·月岛文字烧湾岸线",
        "name_en": "Tokyo Tsukishima Monja & Bay Area",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "tsukishima_harumi",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "foodie",
            "local_life",
            "couple"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "月岛西仲通文字烧午餐+晴海埠头公园夕阳，半天下町美食收尾线。",
        "experience_family": "food",
        "rhythm_role": "utility",
        "energy_level": "low"
    },
    {
        "cluster_id": "tok_disney_resort_full_stay",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·迪士尼度假区全日线",
        "name_en": "Tokyo Disney Resort Full-Day Route",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "maihama_disney_resort",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "family",
            "couple",
            "first_timer",
            "festival"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "迪士尼乐园与迪士尼海洋需整天消化，预约、餐饮和园内路线都需要提前规划，是典型主题乐园型全日主簇。",
        "experience_family": "themepark",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "nik_toshogu_worldheritage_core",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "nikko",
        "name_zh": "日光·东照宫世界遗产核心线",
        "name_en": "Nikko Toshogu World Heritage Core Route",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "nikko_toshogu_rinnoji_futarasan",
        "seasonality": [
            "all_year",
            "autumn_leaves"
        ],
        "profile_fit": [
            "history",
            "culture",
            "photo",
            "first_timer"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "东照宫、轮王寺、二荒山神社共同构成日光核心文化轴，秋季红叶期与平日均可撑起整天深度游线。",
        "experience_family": "shrine",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "tok_mt_takao_hiking_escape",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·高尾山登山逃逸线",
        "name_en": "Tokyo Mount Takao Hiking Escape",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "mt_takao_cablecar_summit",
        "seasonality": [
            "all_year",
            "autumn_leaves"
        ],
        "profile_fit": [
            "hiking",
            "nature",
            "first_timer",
            "slow_travel"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "高尾山缆车与登山步道组合可适配不同体力，秋叶季与平日均能形成东京近郊半天到全天的自然逃逸线。",
        "experience_family": "mountain",
        "rhythm_role": "contrast",
        "energy_level": "high"
    },
    {
        "cluster_id": "kam_enoshima_shonan_sunset",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "kamakura",
        "name_zh": "镰仓·江之岛湘南夕阳线",
        "name_en": "Kamakura Enoshima Shonan Sunset Route",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "enoshima_shonan_coast",
        "seasonality": [
            "all_year",
            "summer"
        ],
        "profile_fit": [
            "couple",
            "photo",
            "coastal",
            "slow_travel"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "江之岛与湘南海岸在夕阳时段具有强视觉价值，适合从镰仓古都线延伸出来做海边下午收口。",
        "experience_family": "sea",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "tok_toyosu_tsukiji_sushi_morning",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·丰洲筑地寿司早市线",
        "name_en": "Tokyo Toyosu-Tsukiji Sushi Morning Route",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "toyosu_tsukiji_sushi_axis",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "foodie",
            "first_timer",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "清晨丰洲场内市场与筑地场外市场的寿司早餐是东京最稳定的美食晨间仪式，时间窗明确、强度适中。",
        "experience_family": "food",
        "rhythm_role": "contrast",
        "energy_level": "low"
    },
    {
        "cluster_id": "tok_meiji_yoyogi_sanctuary",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·明治神宫代代木公园线",
        "name_en": "Tokyo Meiji Jingu & Yoyogi Park Line",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "tok_harajuku_yoyogi_green",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "couple",
            "photo",
            "slow_travel",
            "first_timer"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "明治神宫从日出开放、代代木公园与原宿街区天然连排，适合清晨到午后的半日主线。",
        "experience_family": "shrine",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "tok_tokyo_tower_shiba_night",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·东京塔芝公园夜景线",
        "name_en": "Tokyo Tokyo Tower & Shiba Park Night Line",
        "level": "A",
        "default_duration": "quarter_day",
        "primary_corridor": "tok_shiba_tokyotower_night",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "couple",
            "photo",
            "first_timer"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "strong",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "和六本木高层展望不同，这条线强调东京塔近景、芝公园机位与夜间亮灯氛围。",
        "experience_family": "citynight",
        "rhythm_role": "utility",
        "energy_level": "low"
    },
    {
        "cluster_id": "tok_ryogoku_sumo_edo",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·两国相扑江户文化线",
        "name_en": "Tokyo Ryogoku Sumo & Edo Culture Line",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "tok_ryogoku_sumo_edo",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "culture",
            "history",
            "first_timer"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "两国国技馆、相扑博物馆、相扑部屋和江户工艺街区足以独立成半天到一天的文化主线。",
        "experience_family": "locallife",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "tok_jiyugaoka_nakameguro_life",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·自由之丘中目黑生活线",
        "name_en": "Tokyo Jiyugaoka & Nakameguro Lifestyle Line",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "tok_meguro_jiyugaoka_life",
        "seasonality": [
            "all_year",
            "sakura"
        ],
        "profile_fit": [
            "couple",
            "coffee",
            "photo",
            "slow_travel"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 3,
        "default_selected": False,
        "notes": "自由之丘杂货甜品和中目黑河岸街区很适合做生活方式型半日线，樱花季会明显升级。",
        "experience_family": "locallife",
        "rhythm_role": "recovery",
        "energy_level": "low"
    },
    {
        "cluster_id": "tok_ghibli_mitaka_forest",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·吉卜力美术馆三鹰之森线",
        "name_en": "Tokyo Ghibli Museum Mitaka Forest Line",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "tok_mitaka_inokashira_ghibli",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "couple",
            "family",
            "design",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "吉卜力美术馆需提前预约，和井之头公园、三鹰之森环境天然组合成预约型半日主线。",
        "experience_family": "art",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "tok_sanrio_puroland_family",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·三丽鸥乐园亲子线",
        "name_en": "Tokyo Sanrio Puroland Family Line",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "tok_tama_puroland",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "family",
            "couple",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "Sanrio Puroland是典型主题乐园型目的地，对亲子和角色粉丝画像能独立撑满全天。",
        "experience_family": "themepark",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "tok_ikebukuro_sunshine_aquarium",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·池袋Sunshine水族馆线",
        "name_en": "Tokyo Ikebukuro Sunshine Aquarium Line",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "tok_ikebukuro_sunshine",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "family",
            "couple",
            "photo"
        ],
        "trip_role": "buffer",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "Sunshine City和屋顶水族馆适合做东池袋的半日亲子与城市室内补位线。",
        "experience_family": "themepark",
        "rhythm_role": "utility",
        "energy_level": "medium"
    },
    {
        "cluster_id": "tok_sumida_fireworks_festival",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·隅田川花火大会线",
        "name_en": "Tokyo Sumida River Fireworks Festival Line",
        "level": "S",
        "default_duration": "half_day",
        "primary_corridor": "tok_sumida_river_fireworks",
        "seasonality": [
            "summer"
        ],
        "profile_fit": [
            "couple",
            "photo",
            "festival",
            "first_timer"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "隅田川花火大会是东京最强夏季夜间事件之一，酒店、机位和晚间路线都会被它重写。",
        "experience_family": "citynight",
        "rhythm_role": "peak",
        "energy_level": "medium"
    },
    {
        "cluster_id": "tok_shinjukugyoen_gaien_autumn",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·新宿御苑神宫外苑秋色线",
        "name_en": "Tokyo Shinjuku Gyoen & Jingu Gaien Autumn Line",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "tok_shinjuku_gaien_autumn",
        "seasonality": [
            "autumn_leaves"
        ],
        "profile_fit": [
            "couple",
            "photo",
            "slow_travel"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "新宿御苑秋色和神宫外苑银杏大道都是东京秋季高命中场景，11月前后可独立升级为半日主线。",
        "experience_family": "flower",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "tok_christmas_market_winter",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·圣诞市集冬季线",
        "name_en": "Tokyo Christmas Market Winter Line",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "tok_winter_market_axis",
        "seasonality": [
            "winter"
        ],
        "profile_fit": [
            "couple",
            "photo",
            "festival"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "圣诞市集属于明确冬季限时体验，最适合挂接夜景和灯饰簇形成冬季晚间线。",
        "experience_family": "citynight",
        "rhythm_role": "utility",
        "energy_level": "low"
    },
    {
        "cluster_id": "yok_chinatown_food_depth",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "yokohama",
        "name_zh": "横滨·中华街美食深度线",
        "name_en": "Yokohama Chinatown Food Depth Line",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "yok_chinatown_motomachi",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "foodie",
            "family",
            "first_timer"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "横滨中华街不是单次打卡点，足以作为独立半日到一日的中餐美食与街区体验线。",
        "experience_family": "food",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "yok_hakkeijima_seaparadise",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "yokohama",
        "name_zh": "横滨·八景岛海洋乐园亲子线",
        "name_en": "Yokohama Hakkeijima Sea Paradise Line",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "yok_hakkeijima_baypark",
        "seasonality": [
            "all_year",
            "summer"
        ],
        "profile_fit": [
            "family",
            "couple",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "海洋馆、游乐设施和海边空间足以独立占满全天，是横滨亲子线的强目的地。",
        "experience_family": "themepark",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "hak_museum_forest_axis",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "hakone",
        "name_zh": "箱根·美术馆群森林线",
        "name_en": "Hakone Museum Forest Axis",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "hak_gora_sengokuhara_museums",
        "seasonality": [
            "all_year",
            "autumn"
        ],
        "profile_fit": [
            "art",
            "couple",
            "photo",
            "slow_travel"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "POLA美术馆、玻璃之森等箱根美术馆群适合单独抽出一整天，与经典箱根环线区分明确。",
        "experience_family": "art",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "kam_hydrangea_temple_season",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "kamakura",
        "name_zh": "镰仓·绣球花寺院季线",
        "name_en": "Kamakura Hydrangea Temple Season Line",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "kam_hase_kitakamakura_hydrangea",
        "seasonality": [
            "hydrangea"
        ],
        "profile_fit": [
            "couple",
            "photo",
            "seasonal"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "长谷寺、明月院等在6月绣球花季有很强吸引力，命中季节时足以改写镰仓排程。",
        "experience_family": "flower",
        "rhythm_role": "peak",
        "energy_level": "medium"
    },
    {
        "cluster_id": "nik_toshogu_chuzenji_autumn",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "nikko",
        "name_zh": "日光·东照宫中禅寺湖秋色线",
        "name_en": "Nikko Toshogu & Lake Chuzenji Autumn Line",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "nik_toshogu_chuzenji_autumn",
        "seasonality": [
            "autumn_leaves"
        ],
        "profile_fit": [
            "photo",
            "nature",
            "history",
            "first_timer"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "秋季的东照宫与中禅寺湖组合明显强于常规日光线，适合命中红叶后独立升级。",
        "experience_family": "flower",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "tok_takao_mountain_hike",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·高尾山轻徒步线",
        "name_en": "Tokyo Mount Takao Light Hike",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "tok_west_takao_hike",
        "seasonality": [
            "all_year",
            "autumn_leaves"
        ],
        "profile_fit": [
            "nature",
            "hiking",
            "family",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "高尾山是东京近郊最稳定的轻徒步和季节山景选择，半天到一天都能成立。",
        "experience_family": "mountain",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "tok_jazz_livehouse_weekend",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·Jazz与音乐节夜线",
        "name_en": "Tokyo Jazz & Livehouse Night Line",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "tok_shibuya_roppongi_jazz",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "music",
            "couple",
            "nightlife"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "对音乐画像命中的用户，东京livehouse和jazz夜生活本身就是来东京的重要理由之一。",
        "experience_family": "citynight",
        "rhythm_role": "contrast",
        "energy_level": "low"
    },
    {
        "cluster_id": "tok_toyosu_ginza_morning_brunch",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·丰洲早市银座早午餐线",
        "name_en": "Tokyo Toyosu Morning Market & Ginza Brunch Line",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "tok_toyosu_ginza_morning",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "foodie",
            "couple",
            "first_timer"
        ],
        "trip_role": "buffer",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "清晨丰洲和银座早午餐形成明确时段价值，适合从常规筑地丰洲美食簇中再细分出晨间玩法。",
        "experience_family": "food",
        "rhythm_role": "utility",
        "energy_level": "low"
    },
    {
        "cluster_id": "tok_marunouchi_redbrick_station",
        "circle_id": "tokyo_metropolitan_circle",
        "city_code": "tokyo",
        "name_zh": "东京·丸之内红砖街区东京站线",
        "name_en": "Tokyo Marunouchi Red Brick Station District",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "tok_marunouchi_tokyostation",
        "seasonality": [
            "all_year",
            "winter"
        ],
        "profile_fit": [
            "photo",
            "shopping",
            "first_timer",
            "couple"
        ],
        "trip_role": "buffer",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "东京站红砖站舍、丸之内街区和KITTE适合组成半日城市建筑与购物补位线。",
        "experience_family": "locallife",
        "rhythm_role": "utility",
        "energy_level": "low"
    }
]


async def seed():
    async with AsyncSessionLocal() as session:
        new_count = skip_count = 0
        for data in CLUSTERS:
            existing = await session.get(ActivityCluster, data["cluster_id"])
            if existing:
                skip_count += 1
                continue
            # 只传 ActivityCluster 已知的字段
            known_fields = {c.key for c in ActivityCluster.__table__.columns}
            filtered = {k: v for k, v in data.items() if k in known_fields}
            cluster = ActivityCluster(**filtered)
            session.add(cluster)
            new_count += 1
            logger.info("  NEW: %s [%s] %s", data["cluster_id"], data.get("level", "?"), data.get("city_code", "?"))
        await session.commit()
        logger.info("=== %s 完成: 新增=%d 跳过=%d 总计=%d ===",
                     "tokyo_metropolitan_circle", new_count, skip_count, len(CLUSTERS))


if __name__ == "__main__":
    asyncio.run(seed())
