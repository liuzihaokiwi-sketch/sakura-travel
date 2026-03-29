"""
seed_guangfu_circle_clusters.py — guangfu_circle 活动簇数据

从 mojor/ 目录转换生成。
幂等：cluster_id 已存在则 SKIP。

执行：
    python scripts/seed_guangfu_clusters.py
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
        "cluster_id": "gz_old_town_guangfu_life",
        "circle_id": "guangfu_circle",
        "city_code": "guangzhou",
        "name_zh": "广州·老城广府生活线",
        "name_en": "Guangzhou Old Town Guangfu Life Line",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "gz_liwan_yuexiu_oldcore",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "first_timer",
            "culture",
            "foodie",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 3,
        "default_selected": False,
        "notes": "永庆坊 / 西关、上下九、沙面、北京路组成广州最完整的广府城市生活主线，足够独立占满一天，也会真实影响酒店是否落在荔湾或越秀。",
        "experience_family": "locallife",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "gz_canton_tower_pearl_river_nightview",
        "circle_id": "guangfu_circle",
        "city_code": "guangzhou",
        "name_zh": "广州·广州塔珠江夜景都市线",
        "name_en": "Guangzhou Canton Tower & Pearl River Night View Line",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "gz_haizhu_zhujiang_riverfront",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "couple",
            "photo",
            "first_timer"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "广州塔 + 珠江夜游是典型夜间都市主簇，价值集中在日落到夜间，适合单独吃掉一个傍晚。",
        "experience_family": "citynight",
        "rhythm_role": "peak",
        "energy_level": "medium"
    },
    {
        "cluster_id": "gz_dimsum_culture_experience",
        "circle_id": "guangfu_circle",
        "city_code": "guangzhou",
        "name_zh": "广州·早茶文化体验线",
        "name_en": "Guangzhou Dim Sum Culture Experience",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "gz_xiguan_old_teahouse",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "foodie",
            "culture",
            "family",
            "first_timer"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "广州早茶不是普通餐饮补位，而是强时间窗的生活方式体验，老字号和老城动线能自然组成半天主线。",
        "experience_family": "food",
        "rhythm_role": "contrast",
        "energy_level": "low"
    },
    {
        "cluster_id": "gz_museum_lingnan_culture_dualcore",
        "circle_id": "guangfu_circle",
        "city_code": "guangzhou",
        "name_zh": "广州·博物馆岭南文化双核线",
        "name_en": "Guangzhou Museum & Lingnan Heritage Dual-Core",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "gz_tianhe_liwan_museum_axis",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "culture",
            "history",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "广东省博 + 陈家祠分别对应现代广东叙事与传统岭南工艺建筑，组合后足够成立半天到一天文化线。",
        "experience_family": "art",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "gz_chimelong_family_themepark",
        "circle_id": "guangfu_circle",
        "city_code": "guangzhou",
        "name_zh": "广州·长隆主题乐园亲子线",
        "name_en": "Guangzhou Chimelong Family Theme Park Line",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "gz_panyu_chimelong",
        "seasonality": [
            "all_year",
            "summer",
            "winter"
        ],
        "profile_fit": [
            "family",
            "first_timer"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "长隆是标准整天型主活动，且会直接影响住番禺还是市区、是否预留连续两天给亲子项目。",
        "experience_family": "themepark",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "gz_huacheng_square_cbd_urban",
        "circle_id": "guangfu_circle",
        "city_code": "guangzhou",
        "name_zh": "广州·花城广场商圈都市线",
        "name_en": "Guangzhou Huacheng Square CBD Urban Line",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "gz_zhujiang_new_town",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "photo",
            "shopping",
            "couple",
            "first_timer"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 3,
        "default_selected": False,
        "notes": "花城广场、花城汇、剧院和看塔视角天然连成现代广州城市中轴，适合半天都市体验。",
        "experience_family": "citynight",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "gz_wenminglu_dessert_crawl",
        "circle_id": "guangfu_circle",
        "city_code": "guangzhou",
        "name_zh": "广州·文明路糖水甜品线",
        "name_en": "Guangzhou Wenming Road Dessert Crawl",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "gz_yuexiu_dessert_lane",
        "seasonality": [
            "all_year",
            "summer"
        ],
        "profile_fit": [
            "foodie",
            "photo",
            "couple"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "文明路糖水线适合挂在北京路或越秀老城线之后，作为广州本地甜品主题补位。",
        "experience_family": "food",
        "rhythm_role": "utility",
        "energy_level": "low"
    },
    {
        "cluster_id": "gz_party_pier_nightlife",
        "circle_id": "guangfu_circle",
        "city_code": "guangzhou",
        "name_zh": "广州·琶醍江边夜生活线",
        "name_en": "Guangzhou Party Pier Riverside Nightlife",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "gz_party_pier_riverfront",
        "seasonality": [
            "all_year",
            "summer"
        ],
        "profile_fit": [
            "couple",
            "nightlife",
            "photo"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "琶醍适合作为广州塔/珠江夜景簇后的夜间续接，强化都市夜生活感。",
        "experience_family": "citynight",
        "rhythm_role": "utility",
        "energy_level": "low"
    },
    {
        "cluster_id": "gz_tianhe_luxury_shopping",
        "circle_id": "guangfu_circle",
        "city_code": "guangzhou",
        "name_zh": "广州·天河高端购物补位线",
        "name_en": "Guangzhou Tianhe Luxury Shopping Fill-in",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "gz_tianhe_luxury_core",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "shopping",
            "luxury",
            "couple"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "天河高端商圈对消费型画像很强，会影响酒店落点与下午档安排。",
        "experience_family": "locallife",
        "rhythm_role": "utility",
        "energy_level": "low"
    },
    {
        "cluster_id": "gz_flower_market_cny",
        "circle_id": "guangfu_circle",
        "city_code": "guangzhou",
        "name_zh": "广州·迎春花市年味线",
        "name_en": "Guangzhou Lunar New Year Flower Market Line",
        "level": "S",
        "default_duration": "half_day",
        "primary_corridor": "gz_cny_flower_market",
        "seasonality": [
            "spring"
        ],
        "profile_fit": [
            "family",
            "culture",
            "photo",
            "first_timer"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "广州花市是极强的春节季节簇，到了窗口就是独立来广州的理由之一。",
        "experience_family": "flower",
        "rhythm_role": "peak",
        "energy_level": "medium"
    },
    {
        "cluster_id": "gz_lychee_season_orchard",
        "circle_id": "guangfu_circle",
        "city_code": "guangzhou",
        "name_zh": "广州·荔枝季尝鲜线",
        "name_en": "Guangzhou Lychee Season Tasting Line",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "gz_suburban_lychee_season",
        "seasonality": [
            "summer"
        ],
        "profile_fit": [
            "foodie",
            "family",
            "slow_travel"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "荔枝季有明确时间窗，对时令吃喝画像很强，适合作为夏季限定补强簇。",
        "experience_family": "food",
        "rhythm_role": "contrast",
        "energy_level": "low"
    },
    {
        "cluster_id": "fs_lingnan_kungfu_culture",
        "circle_id": "guangfu_circle",
        "city_code": "foshan",
        "name_zh": "佛山·岭南文化功夫线",
        "name_en": "Foshan Lingnan Culture & Kung Fu Line",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "fs_chancheng_heritage_core",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "culture",
            "history",
            "first_timer",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "祖庙、岭南天地、南风古灶组合后是佛山最完整的文化主线，足够独立一整天。",
        "experience_family": "shrine",
        "rhythm_role": "contrast",
        "energy_level": "high"
    },
    {
        "cluster_id": "fs_foshan_food_depth",
        "circle_id": "guangfu_circle",
        "city_code": "foshan",
        "name_zh": "佛山·禅城南海美食深度线",
        "name_en": "Foshan Chancheng-Nanhai Food Depth Line",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "fs_chancheng_nanhai_foodbelt",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "foodie",
            "slow_travel",
            "local_life"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 3,
        "default_selected": False,
        "notes": "佛山本地饮食体系足够独立成一条主簇，不应只当作顺德美食的外延补充。",
        "experience_family": "food",
        "rhythm_role": "recovery",
        "energy_level": "medium"
    },
    {
        "cluster_id": "fs_xiqiao_mountain_lingnan_retreat",
        "circle_id": "guangfu_circle",
        "city_code": "foshan",
        "name_zh": "佛山·西樵山岭南山水线",
        "name_en": "Foshan Xiqiao Mountain Lingnan Scenic Retreat",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "fs_xiqiao_mountain_baofeng_lake",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "nature",
            "culture",
            "photo",
            "slow_travel"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "西樵山不是佛山的小补点，而是能独立占满半天到一天的山水文化主线；命中自然 / 岭南宗教画像时，会明显影响佛山还是顺德驻点。",
        "experience_family": "mountain",
        "rhythm_role": "contrast",
        "energy_level": "high"
    },
    {
        "cluster_id": "fs_lingnan_tiandi_nightwalk",
        "circle_id": "guangfu_circle",
        "city_code": "foshan",
        "name_zh": "佛山·岭南天地夜走线",
        "name_en": "Foshan Lingnan Tiandi Night Walk",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "fs_lingnan_tiandi_core",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "couple",
            "photo",
            "culture"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "strong",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "岭南天地夜间氛围比白天更强，适合挂在祖庙文化线之后。",
        "experience_family": "citynight",
        "rhythm_role": "contrast",
        "energy_level": "low"
    },
    {
        "cluster_id": "fs_chancheng_night_snack",
        "circle_id": "guangfu_circle",
        "city_code": "foshan",
        "name_zh": "佛山·禅城夜宵补位线",
        "name_en": "Foshan Chancheng Night Snack Fill-in",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "fs_chancheng_nightfood",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "foodie",
            "nightlife",
            "local_life"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "strong",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "从早茶延续到夜宵，是佛山本地生活感最自然的收口方式。",
        "experience_family": "food",
        "rhythm_role": "utility",
        "energy_level": "low"
    },
    {
        "cluster_id": "sd_shunde_world_food_classic",
        "circle_id": "guangfu_circle",
        "city_code": "shunde",
        "name_zh": "顺德·世界美食经典线",
        "name_en": "Shunde UNESCO Food Capital Classic Line",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "sd_daliang_food_core",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "foodie",
            "first_timer",
            "family"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 3,
        "default_selected": False,
        "notes": "清晖园、华盖路、金榜、伦教可自然形成完整一日线，顺德本身就足以作为\"为吃而来\"的主目的地。",
        "experience_family": "food",
        "rhythm_role": "peak",
        "energy_level": "medium"
    },
    {
        "cluster_id": "sd_water_town_garden_slowline",
        "circle_id": "guangfu_circle",
        "city_code": "shunde",
        "name_zh": "顺德·园林水乡松弛线",
        "name_en": "Shunde Garden & Water Town Slow Line",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "sd_fengjian_slowtravel",
        "seasonality": [
            "all_year",
            "spring",
            "autumn"
        ],
        "profile_fit": [
            "couple",
            "photo",
            "slow_travel",
            "family"
        ],
        "trip_role": "anchor",
        "time_window_strength": "weak",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "逢简水乡配合清晖园或容桂河岸活化节点，很适合做顺德慢节奏的一整天。",
        "experience_family": "locallife",
        "rhythm_role": "recovery",
        "energy_level": "medium"
    },
    {
        "cluster_id": "sd_double_skin_milk_dessert",
        "circle_id": "guangfu_circle",
        "city_code": "shunde",
        "name_zh": "顺德·双皮奶牛乳甜品线",
        "name_en": "Shunde Double-Skin Milk Dessert Line",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "sd_daliang_milk_dessert",
        "seasonality": [
            "all_year",
            "summer"
        ],
        "profile_fit": [
            "foodie",
            "family",
            "photo"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "双皮奶、姜撞奶、伦教糕与金榜牛乳足够形成独立下午茶甜品簇。",
        "experience_family": "food",
        "rhythm_role": "utility",
        "energy_level": "low"
    },
    {
        "cluster_id": "hk_harbour_skyline_classic",
        "circle_id": "guangfu_circle",
        "city_code": "hong_kong",
        "name_zh": "香港·维港天际线经典线",
        "name_en": "Hong Kong Victoria Harbour Skyline Classic",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "hk_tst_central_harbour",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "first_timer",
            "couple",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 3,
        "default_selected": False,
        "notes": "天星小轮、中环/尖沙咀两岸天际线、海滨步道和夜景是香港最具标志性的首访主线，几乎总能独立占满一天。",
        "experience_family": "sea",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "hk_peak_central_heritage",
        "circle_id": "guangfu_circle",
        "city_code": "hong_kong",
        "name_zh": "香港·太平山顶中环经典线",
        "name_en": "Hong Kong Peak & Central Heritage Line",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "hk_central_peak_axis",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "first_timer",
            "photo",
            "couple"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "Peak Tram + The Peak + Central 老城区是非常成熟的首访动线，既有明确的日落窗口，也会影响住港岛还是九龙。",
        "experience_family": "citynight",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "hk_westkowloon_art_harbour",
        "circle_id": "guangfu_circle",
        "city_code": "hong_kong",
        "name_zh": "香港·西九文化海滨线",
        "name_en": "Hong Kong West Kowloon Art & Harbour Line",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "hk_westkowloon_cultural_district",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "culture",
            "photo",
            "couple"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "M+、西九文化区海滨、草坪与黄昏看海景天然适合组成半天以上艺术与海港簇。",
        "experience_family": "art",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "hk_lantau_ngongping_bigbuddha",
        "circle_id": "guangfu_circle",
        "city_code": "hong_kong",
        "name_zh": "香港·大屿山昂坪天坛大佛线",
        "name_en": "Hong Kong Lantau Ngong Ping Big Buddha Line",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "hk_lantau_tungchung_ngongping_tai_o",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "first_timer",
            "family",
            "photo",
            "culture"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "东涌缆车、昂坪、大佛与大澳天然连成一整天，大屿山不是普通离岛补位；它会直接改变香港是否安排离岛日和住九龙还是机场线附近。",
        "experience_family": "shrine",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "hk_disney_family_themepark",
        "circle_id": "guangfu_circle",
        "city_code": "hong_kong",
        "name_zh": "香港·迪士尼亲子线",
        "name_en": "Hong Kong Disneyland Family Line",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "hk_lantau_disney",
        "seasonality": [
            "all_year",
            "summer",
            "winter"
        ],
        "profile_fit": [
            "family",
            "first_timer"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "迪士尼是标准整天型主活动，且往往直接决定是否住欣澳/迪士尼周边或压缩市区行程。",
        "experience_family": "themepark",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "hk_tsimshatsui_nightwalk",
        "circle_id": "guangfu_circle",
        "city_code": "hong_kong",
        "name_zh": "香港·尖沙咀夜走线",
        "name_en": "Hong Kong Tsim Sha Tsui Night Walk",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "hk_tst_nightcore",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "couple",
            "photo",
            "shopping"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "strong",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "尖沙咀夜景、码头、海滨步道与商场很适合作为维港线后的晚间补位。",
        "experience_family": "citynight",
        "rhythm_role": "utility",
        "energy_level": "low"
    },
    {
        "cluster_id": "hk_temple_street_local_night",
        "circle_id": "guangfu_circle",
        "city_code": "hong_kong",
        "name_zh": "香港·庙街本地夜市线",
        "name_en": "Hong Kong Temple Street Local Night Line",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "hk_yaumatei_temple_street",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "local_life",
            "foodie",
            "nightlife"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "strong",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "庙街更偏市井生活与夜间氛围，适合做香港城市感的本地补位簇。",
        "experience_family": "locallife",
        "rhythm_role": "contrast",
        "energy_level": "low"
    },
    {
        "cluster_id": "mo_historic_centre_worldheritage",
        "circle_id": "guangfu_circle",
        "city_code": "macau",
        "name_zh": "澳门·历史城区世界遗产线",
        "name_en": "Macao Historic Centre World Heritage Line",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "mo_senado_stpaul_heritage",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "first_timer",
            "history",
            "photo",
            "culture"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 3,
        "default_selected": False,
        "notes": "大三巴、议事亭前地、玫瑰堂、炮台山一带足够形成完整世界遗产主线，是澳门首访最稳定的整天簇。",
        "experience_family": "shrine",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "mo_taipa_village_food_heritage",
        "circle_id": "guangfu_circle",
        "city_code": "macau",
        "name_zh": "澳门·氹仔村风味文化线",
        "name_en": "Macao Taipa Village Food & Heritage Line",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "mo_taipa_village_core",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "foodie",
            "couple",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "官也街、氹仔旧城区与葡式街景天然组成半天以上的风味簇，适合与路环或 Cotai 串联。",
        "experience_family": "food",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "mo_cotai_resort_show_entertainment",
        "circle_id": "guangfu_circle",
        "city_code": "macau",
        "name_zh": "澳门·路氹综合度假娱乐线",
        "name_en": "Macao Cotai Resort Entertainment Line",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "mo_cotai_integrated_resort",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "couple",
            "luxury",
            "shopping",
            "show"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "路氹的综合度假村、演出、购物与夜景不是简单酒店区，而是能独立占掉一个晚上甚至半天的娱乐型主簇。",
        "experience_family": "citynight",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "mo_macau_tower_waterfront_night",
        "circle_id": "guangfu_circle",
        "city_code": "macau",
        "name_zh": "澳门·澳门塔南湾夜景线",
        "name_en": "Macao Tower & Praia Grande Night Line",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "mo_macau_tower_waterfront",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "couple",
            "photo"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "strong",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "澳门塔与南湾夜景很适合做世界遗产主线后的夜景收口。",
        "experience_family": "citynight",
        "rhythm_role": "utility",
        "energy_level": "low"
    },
    {
        "cluster_id": "mo_portuguese_snack_crawl",
        "circle_id": "guangfu_circle",
        "city_code": "macau",
        "name_zh": "澳门·葡式小吃甜品线",
        "name_en": "Macao Portuguese Snack & Dessert Crawl",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "mo_snack_crawl_core",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "foodie",
            "photo",
            "couple"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "medium",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "葡挞、杏仁饼、猪扒包与葡式点心足够形成澳门高辨识度的轻量吃喝簇。",
        "experience_family": "food",
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
                     "guangfu_circle", new_count, skip_count, len(CLUSTERS))


if __name__ == "__main__":
    asyncio.run(seed())
