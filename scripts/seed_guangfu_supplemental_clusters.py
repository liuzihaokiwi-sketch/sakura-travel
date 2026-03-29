"""
seed_guangfu_supplemental_clusters.py — 广府圈活动簇补全

新增 35 个活动簇：
  - 广州 11 个（含季节限定：花市、荔枝季）
  - 佛山 4 个
  - 顺德 3 个（注意：shunde 需确认已加入 CITY_MAP）
  - 香港 6 个
  - 澳门 5 个
  - 深圳 5 个（新增）

数据来源：GPT-5.4 生成 + Opus 审核修正
幂等：cluster_id 已存在则 SKIP。

执行：
    python scripts/seed_guangfu_supplemental_clusters.py
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

CIRCLE = "guangfu_circle"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 主活动簇 (anchor)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ANCHOR_CLUSTERS = [
    # ── 广州 ──────────────────────────────────────────────────────────────────
    {
        "cluster_id": "gz_old_town_guangfu_life",
        "circle_id": CIRCLE, "city_code": "guangzhou",
        "name_zh": "广州·老城广府生活线",
        "name_en": "Guangzhou Old Town Guangfu Life Line",
        "level": "S", "default_duration": "full_day",
        "primary_corridor": "gz_liwan_yuexiu_oldcore",
        "seasonality": ["all_year"],
        "profile_fit": ["first_timer", "culture", "foodie", "photo"],
        "trip_role": "anchor",
        "time_window_strength": "medium", "reservation_pressure": "none",
        "secondary_attach_capacity": 3, "default_selected": False,
        "notes": "永庆坊/西关、上下九、沙面、北京路组成广州最完整的广府城市生活主线，足够独立占满一天，也会真实影响酒店是否落在荔湾或越秀。",
    },
    {
        "cluster_id": "gz_canton_tower_pearl_river_nightview",
        "circle_id": CIRCLE, "city_code": "guangzhou",
        "name_zh": "广州·广州塔珠江夜景都市线",
        "name_en": "Guangzhou Canton Tower & Pearl River Night View Line",
        "level": "A", "default_duration": "half_day",
        "primary_corridor": "gz_haizhu_zhujiang_riverfront",
        "seasonality": ["all_year"],
        "profile_fit": ["couple", "photo", "first_timer"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "medium",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "广州塔+珠江夜游是典型夜间都市主簇，价值集中在日落到夜间，适合单独吃掉一个傍晚。",
    },
    {
        "cluster_id": "gz_dimsum_culture_experience",
        "circle_id": CIRCLE, "city_code": "guangzhou",
        "name_zh": "广州·早茶文化体验线",
        "name_en": "Guangzhou Dim Sum Culture Experience",
        "level": "A", "default_duration": "half_day",
        "primary_corridor": "gz_xiguan_old_teahouse",
        "seasonality": ["all_year"],
        "profile_fit": ["foodie", "culture", "family", "first_timer"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "medium",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "广州早茶不是普通餐饮补位，而是强时间窗的生活方式体验，老字号和老城动线能自然组成半天主线。",
    },
    {
        "cluster_id": "gz_museum_lingnan_culture_dualcore",
        "circle_id": CIRCLE, "city_code": "guangzhou",
        "name_zh": "广州·博物馆岭南文化双核线",
        "name_en": "Guangzhou Museum & Lingnan Heritage Dual-Core",
        "level": "A", "default_duration": "half_day",
        "primary_corridor": "gz_tianhe_liwan_museum_axis",
        "seasonality": ["all_year"],
        "profile_fit": ["culture", "history", "photo"],
        "trip_role": "anchor",
        "time_window_strength": "medium", "reservation_pressure": "low",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "广东省博+陈家祠分别对应现代广东叙事与传统岭南工艺建筑，组合后足够成立半天到一天文化线。",
    },
    {
        "cluster_id": "gz_chimelong_family_themepark",
        "circle_id": CIRCLE, "city_code": "guangzhou",
        "name_zh": "广州·长隆主题乐园亲子线",
        "name_en": "Guangzhou Chimelong Family Theme Park Line",
        "level": "S", "default_duration": "full_day",
        "primary_corridor": "gz_panyu_chimelong",
        "seasonality": ["all_year", "summer", "winter"],
        "profile_fit": ["family", "first_timer"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "high",
        "secondary_attach_capacity": 1, "default_selected": False,
        "notes": "长隆是标准整天型主活动，且会直接影响住番禺还是市区、是否预留连续两天给亲子项目。",
    },
    {
        "cluster_id": "gz_huacheng_square_cbd_urban",
        "circle_id": CIRCLE, "city_code": "guangzhou",
        "name_zh": "广州·花城广场商圈都市线",
        "name_en": "Guangzhou Huacheng Square CBD Urban Line",
        "level": "A", "default_duration": "half_day",
        "primary_corridor": "gz_zhujiang_new_town",
        "seasonality": ["all_year"],
        "profile_fit": ["photo", "shopping", "couple", "first_timer"],
        "trip_role": "anchor",
        "time_window_strength": "medium", "reservation_pressure": "low",
        "secondary_attach_capacity": 3, "default_selected": False,
        "notes": "花城广场、花城汇、剧院和看塔视角天然连成现代广州城市中轴，适合半天都市体验。",
    },
    {
        "cluster_id": "gz_flower_market_cny",
        "circle_id": CIRCLE, "city_code": "guangzhou",
        "name_zh": "广州·迎春花市年味线",
        "name_en": "Guangzhou Lunar New Year Flower Market Line",
        "level": "S", "default_duration": "half_day",
        "primary_corridor": "gz_cny_flower_market",
        "seasonality": ["spring"],
        "profile_fit": ["family", "culture", "photo", "first_timer"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "medium",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "广州花市是极强的春节季节簇，到了窗口就是独立来广州的理由之一。",
    },
    {
        "cluster_id": "gz_lychee_season_orchard",
        "circle_id": CIRCLE, "city_code": "guangzhou",
        "name_zh": "广州·荔枝季尝鲜线",
        "name_en": "Guangzhou Lychee Season Tasting Line",
        "level": "A", "default_duration": "half_day",
        "primary_corridor": "gz_suburban_lychee_season",
        "seasonality": ["summer"],
        "profile_fit": ["foodie", "family", "slow_travel"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "low",
        "secondary_attach_capacity": 1, "default_selected": False,
        "notes": "荔枝季有明确时间窗，对时令吃喝画像很强，适合作为夏季限定补强簇。",
    },
    # ── 佛山 ──────────────────────────────────────────────────────────────────
    {
        "cluster_id": "fs_lingnan_kungfu_culture",
        "circle_id": CIRCLE, "city_code": "foshan",
        "name_zh": "佛山·岭南文化功夫线",
        "name_en": "Foshan Lingnan Culture & Kung Fu Line",
        "level": "A", "default_duration": "full_day",
        "primary_corridor": "fs_chancheng_heritage_core",
        "seasonality": ["all_year"],
        "profile_fit": ["culture", "history", "first_timer", "photo"],
        "trip_role": "anchor",
        "time_window_strength": "medium", "reservation_pressure": "low",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "祖庙、岭南天地、南风古灶组合后是佛山最完整的文化主线，足够独立一整天。",
    },
    {
        "cluster_id": "fs_foshan_food_depth",
        "circle_id": CIRCLE, "city_code": "foshan",
        "name_zh": "佛山·禅城南海美食深度线",
        "name_en": "Foshan Chancheng-Nanhai Food Depth Line",
        "level": "A", "default_duration": "full_day",
        "primary_corridor": "fs_chancheng_nanhai_foodbelt",
        "seasonality": ["all_year"],
        "profile_fit": ["foodie", "slow_travel", "local_life"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "low",
        "secondary_attach_capacity": 3, "default_selected": False,
        "notes": "佛山本地饮食体系足够独立成一条主簇，不应只当作顺德美食的外延补充。",
    },
    # ── 顺德 ──────────────────────────────────────────────────────────────────
    # 注意：shunde 需确认已加入 CITY_MAP
    {
        "cluster_id": "sd_shunde_world_food_classic",
        "circle_id": CIRCLE, "city_code": "shunde",
        "name_zh": "顺德·世界美食经典线",
        "name_en": "Shunde UNESCO Food Capital Classic Line",
        "level": "S", "default_duration": "full_day",
        "primary_corridor": "sd_daliang_food_core",
        "seasonality": ["all_year"],
        "profile_fit": ["foodie", "first_timer", "family"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "medium",
        "secondary_attach_capacity": 3, "default_selected": False,
        "notes": "清晖园、华盖路、金榜、伦教可自然形成完整一日线，顺德本身就足以作为"为吃而来"的主目的地。",
    },
    {
        "cluster_id": "sd_water_town_garden_slowline",
        "circle_id": CIRCLE, "city_code": "shunde",
        "name_zh": "顺德·园林水乡松弛线",
        "name_en": "Shunde Garden & Water Town Slow Line",
        "level": "A", "default_duration": "full_day",
        "primary_corridor": "sd_fengjian_slowtravel",
        "seasonality": ["all_year", "spring", "autumn"],
        "profile_fit": ["couple", "photo", "slow_travel", "family"],
        "trip_role": "anchor",
        "time_window_strength": "weak", "reservation_pressure": "low",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "逢简水乡配合清晖园或容桂河岸活化节点，很适合做顺德慢节奏的一整天。",
    },
    # ── 香港 ──────────────────────────────────────────────────────────────────
    {
        "cluster_id": "hk_harbour_skyline_classic",
        "circle_id": CIRCLE, "city_code": "hongkong",
        "name_zh": "香港·维港天际线经典线",
        "name_en": "Hong Kong Victoria Harbour Skyline Classic",
        "level": "S", "default_duration": "full_day",
        "primary_corridor": "hk_tst_central_harbour",
        "seasonality": ["all_year"],
        "profile_fit": ["first_timer", "couple", "photo"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "medium",
        "secondary_attach_capacity": 3, "default_selected": False,
        "notes": "天星小轮、中环/尖沙咀两岸天际线、海滨步道和夜景是香港最具标志性的首访主线，几乎总能独立占满一天。",
    },
    {
        "cluster_id": "hk_peak_central_heritage",
        "circle_id": CIRCLE, "city_code": "hongkong",
        "name_zh": "香港·太平山顶中环经典线",
        "name_en": "Hong Kong Peak & Central Heritage Line",
        "level": "S", "default_duration": "full_day",
        "primary_corridor": "hk_central_peak_axis",
        "seasonality": ["all_year"],
        "profile_fit": ["first_timer", "photo", "couple"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "medium",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "Peak Tram+The Peak+Central老城区是非常成熟的首访动线，既有明确的日落窗口，也会影响住港岛还是九龙。",
    },
    {
        "cluster_id": "hk_westkowloon_art_harbour",
        "circle_id": CIRCLE, "city_code": "hongkong",
        "name_zh": "香港·西九文化海滨线",
        "name_en": "Hong Kong West Kowloon Art & Harbour Line",
        "level": "A", "default_duration": "half_day",
        "primary_corridor": "hk_westkowloon_cultural_district",
        "seasonality": ["all_year"],
        "profile_fit": ["culture", "photo", "couple"],
        "trip_role": "anchor",
        "time_window_strength": "medium", "reservation_pressure": "low",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "M+、西九文化区海滨、草坪与黄昏看海景天然适合组成半天以上艺术与海港簇。",
    },
    {
        "cluster_id": "hk_disney_family_themepark",
        "circle_id": CIRCLE, "city_code": "hongkong",
        "name_zh": "香港·迪士尼亲子线",
        "name_en": "Hong Kong Disneyland Family Line",
        "level": "S", "default_duration": "full_day",
        "primary_corridor": "hk_lantau_disney",
        "seasonality": ["all_year", "summer", "winter"],
        "profile_fit": ["family", "first_timer"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "high",
        "secondary_attach_capacity": 1, "default_selected": False,
        "notes": "迪士尼是标准整天型主活动，且往往直接决定是否住欣澳/迪士尼周边或压缩市区行程。",
    },
    # ── 澳门 ──────────────────────────────────────────────────────────────────
    {
        "cluster_id": "mo_historic_centre_worldheritage",
        "circle_id": CIRCLE, "city_code": "macau",
        "name_zh": "澳门·历史城区世界遗产线",
        "name_en": "Macao Historic Centre World Heritage Line",
        "level": "S", "default_duration": "full_day",
        "primary_corridor": "mo_senado_stpaul_heritage",
        "seasonality": ["all_year"],
        "profile_fit": ["first_timer", "history", "photo", "culture"],
        "trip_role": "anchor",
        "time_window_strength": "medium", "reservation_pressure": "low",
        "secondary_attach_capacity": 3, "default_selected": False,
        "notes": "大三巴、议事亭前地、玫瑰堂、炮台山一带足够形成完整世界遗产主线，是澳门首访最稳定的整天簇。",
    },
    {
        "cluster_id": "mo_taipa_village_food_heritage",
        "circle_id": CIRCLE, "city_code": "macau",
        "name_zh": "澳门·氹仔村风味文化线",
        "name_en": "Macao Taipa Village Food & Heritage Line",
        "level": "A", "default_duration": "half_day",
        "primary_corridor": "mo_taipa_village_core",
        "seasonality": ["all_year"],
        "profile_fit": ["foodie", "couple", "photo"],
        "trip_role": "anchor",
        "time_window_strength": "medium", "reservation_pressure": "low",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "官也街、氹仔旧城区与葡式街景天然组成半天以上的风味簇，适合与路环或Cotai串联。",
    },
    {
        "cluster_id": "mo_cotai_resort_show_entertainment",
        "circle_id": CIRCLE, "city_code": "macau",
        "name_zh": "澳门·路氹综合度假娱乐线",
        "name_en": "Macao Cotai Resort Entertainment Line",
        "level": "A", "default_duration": "half_day",
        "primary_corridor": "mo_cotai_integrated_resort",
        "seasonality": ["all_year"],
        "profile_fit": ["couple", "luxury", "shopping", "show"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "medium",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "路氹的综合度假村、演出、购物与夜景不是简单酒店区，而是能独立占掉一个晚上甚至半天的娱乐型主簇。",
    },
    # ── 深圳 ──────────────────────────────────────────────────────────────────
    {
        "cluster_id": "sz_oct_loft_culture",
        "circle_id": CIRCLE, "city_code": "shenzhen",
        "name_zh": "深圳·华侨城创意文化线",
        "name_en": "Shenzhen OCT-LOFT Creative Culture Line",
        "level": "A", "default_duration": "half_day",
        "primary_corridor": "nanshan_oct_loft",
        "seasonality": ["all_year"],
        "profile_fit": ["art", "photo", "couple", "culture"],
        "trip_role": "anchor",
        "time_window_strength": "medium", "reservation_pressure": "low",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "OCT-LOFT创意园区/何香凝美术馆/OCAT深圳馆，深圳最成熟的当代艺术与设计聚集地。",
    },
    {
        "cluster_id": "sz_shenzhen_bay_coastal",
        "circle_id": CIRCLE, "city_code": "shenzhen",
        "name_zh": "深圳·深圳湾海滨线",
        "name_en": "Shenzhen Bay Coastal Walk Line",
        "level": "A", "default_duration": "half_day",
        "primary_corridor": "nanshan_futian_bay",
        "seasonality": ["all_year", "winter"],
        "profile_fit": ["couple", "nature", "photo", "relax"],
        "trip_role": "anchor",
        "time_window_strength": "strong", "reservation_pressure": "none",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "深圳湾公园6.6km滨海步道/红树林候鸟保护区/日落观鸟，冬季候鸟季最佳。",
    },
    {
        "cluster_id": "sz_east_coast_beach",
        "circle_id": CIRCLE, "city_code": "shenzhen",
        "name_zh": "深圳·东部海岸线",
        "name_en": "Shenzhen East Coast Beach Line",
        "level": "A", "default_duration": "full_day",
        "primary_corridor": "yantian_dameisha_coast",
        "seasonality": ["all_year", "summer"],
        "profile_fit": ["nature", "family", "couple", "active"],
        "trip_role": "anchor",
        "time_window_strength": "medium", "reservation_pressure": "medium",
        "secondary_attach_capacity": 1, "default_selected": False,
        "notes": "大梅沙海滨/较场尾古村/杨梅坑骑行/盐田海滨栈道19.5km，夏季旺季需预约通行。",
    },
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 强次级/enrichment 簇
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ENRICHMENT_CLUSTERS = [
    # ── 广州 ──────────────────────────────────────────────────────────────────
    {
        "cluster_id": "gz_wenminglu_dessert_crawl",
        "circle_id": CIRCLE, "city_code": "guangzhou",
        "name_zh": "广州·文明路糖水甜品线",
        "name_en": "Guangzhou Wenming Road Dessert Crawl",
        "level": "B", "default_duration": "quarter_day",
        "primary_corridor": "gz_yuexiu_dessert_lane",
        "seasonality": ["all_year", "summer"],
        "profile_fit": ["foodie", "photo", "couple"],
        "trip_role": "enrichment",
        "time_window_strength": "medium", "reservation_pressure": "low",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "文明路糖水线适合挂在北京路或越秀老城线之后，作为广州本地甜品主题补位。",
    },
    {
        "cluster_id": "gz_party_pier_nightlife",
        "circle_id": CIRCLE, "city_code": "guangzhou",
        "name_zh": "广州·琶醍江边夜生活线",
        "name_en": "Guangzhou Party Pier Riverside Nightlife",
        "level": "B", "default_duration": "quarter_day",
        "primary_corridor": "gz_party_pier_riverfront",
        "seasonality": ["all_year", "summer"],
        "profile_fit": ["couple", "nightlife", "photo"],
        "trip_role": "enrichment",
        "time_window_strength": "strong", "reservation_pressure": "medium",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "琶醍适合作为广州塔/珠江夜景簇后的夜间续接，强化都市夜生活感。",
    },
    {
        "cluster_id": "gz_tianhe_luxury_shopping",
        "circle_id": CIRCLE, "city_code": "guangzhou",
        "name_zh": "广州·天河高端购物补位线",
        "name_en": "Guangzhou Tianhe Luxury Shopping Fill-in",
        "level": "B", "default_duration": "half_day",
        "primary_corridor": "gz_tianhe_luxury_core",
        "seasonality": ["all_year"],
        "profile_fit": ["shopping", "luxury", "couple"],
        "trip_role": "enrichment",
        "time_window_strength": "weak", "reservation_pressure": "none",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "天河高端商圈对消费型画像很强，会影响酒店落点与下午档安排。",
    },
    # ── 佛山 ──────────────────────────────────────────────────────────────────
    {
        "cluster_id": "fs_lingnan_tiandi_nightwalk",
        "circle_id": CIRCLE, "city_code": "foshan",
        "name_zh": "佛山·岭南天地夜走线",
        "name_en": "Foshan Lingnan Tiandi Night Walk",
        "level": "B", "default_duration": "quarter_day",
        "primary_corridor": "fs_lingnan_tiandi_core",
        "seasonality": ["all_year"],
        "profile_fit": ["couple", "photo", "culture"],
        "trip_role": "enrichment",
        "time_window_strength": "strong", "reservation_pressure": "low",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "岭南天地夜间氛围比白天更强，适合挂在祖庙文化线之后。",
    },
    {
        "cluster_id": "fs_chancheng_night_snack",
        "circle_id": CIRCLE, "city_code": "foshan",
        "name_zh": "佛山·禅城夜宵补位线",
        "name_en": "Foshan Chancheng Night Snack Fill-in",
        "level": "B", "default_duration": "quarter_day",
        "primary_corridor": "fs_chancheng_nightfood",
        "seasonality": ["all_year"],
        "profile_fit": ["foodie", "nightlife", "local_life"],
        "trip_role": "enrichment",
        "time_window_strength": "strong", "reservation_pressure": "none",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "从早茶延续到夜宵，是佛山本地生活感最自然的收口方式。",
    },
    # ── 顺德 ──────────────────────────────────────────────────────────────────
    {
        "cluster_id": "sd_double_skin_milk_dessert",
        "circle_id": CIRCLE, "city_code": "shunde",
        "name_zh": "顺德·双皮奶牛乳甜品线",
        "name_en": "Shunde Double-Skin Milk Dessert Line",
        "level": "B", "default_duration": "quarter_day",
        "primary_corridor": "sd_daliang_milk_dessert",
        "seasonality": ["all_year", "summer"],
        "profile_fit": ["foodie", "family", "photo"],
        "trip_role": "enrichment",
        "time_window_strength": "medium", "reservation_pressure": "low",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "双皮奶、姜撞奶、伦教糕与金榜牛乳足够形成独立下午茶甜品簇。",
    },
    # ── 香港 ──────────────────────────────────────────────────────────────────
    {
        "cluster_id": "hk_tsimshatsui_nightwalk",
        "circle_id": CIRCLE, "city_code": "hongkong",
        "name_zh": "香港·尖沙咀夜走线",
        "name_en": "Hong Kong Tsim Sha Tsui Night Walk",
        "level": "B", "default_duration": "quarter_day",
        "primary_corridor": "hk_tst_nightcore",
        "seasonality": ["all_year"],
        "profile_fit": ["couple", "photo", "shopping"],
        "trip_role": "enrichment",
        "time_window_strength": "strong", "reservation_pressure": "none",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "尖沙咀夜景、码头、海滨步道与商场很适合作为维港线后的晚间补位。",
    },
    {
        "cluster_id": "hk_temple_street_local_night",
        "circle_id": CIRCLE, "city_code": "hongkong",
        "name_zh": "香港·庙街本地夜市线",
        "name_en": "Hong Kong Temple Street Local Night Line",
        "level": "B", "default_duration": "quarter_day",
        "primary_corridor": "hk_yaumatei_temple_street",
        "seasonality": ["all_year"],
        "profile_fit": ["local_life", "foodie", "nightlife"],
        "trip_role": "enrichment",
        "time_window_strength": "strong", "reservation_pressure": "none",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "庙街更偏市井生活与夜间氛围，适合做香港城市感的本地补位簇。",
    },
    # ── 澳门 ──────────────────────────────────────────────────────────────────
    {
        "cluster_id": "mo_macau_tower_waterfront_night",
        "circle_id": CIRCLE, "city_code": "macau",
        "name_zh": "澳门·澳门塔南湾夜景线",
        "name_en": "Macao Tower & Praia Grande Night Line",
        "level": "B", "default_duration": "quarter_day",
        "primary_corridor": "mo_macau_tower_waterfront",
        "seasonality": ["all_year"],
        "profile_fit": ["couple", "photo"],
        "trip_role": "enrichment",
        "time_window_strength": "strong", "reservation_pressure": "low",
        "secondary_attach_capacity": 1, "default_selected": False,
        "notes": "澳门塔与南湾夜景很适合做世界遗产主线后的夜景收口。",
    },
    {
        "cluster_id": "mo_portuguese_snack_crawl",
        "circle_id": CIRCLE, "city_code": "macau",
        "name_zh": "澳门·葡式小吃甜品线",
        "name_en": "Macao Portuguese Snack & Dessert Crawl",
        "level": "B", "default_duration": "quarter_day",
        "primary_corridor": "mo_snack_crawl_core",
        "seasonality": ["all_year"],
        "profile_fit": ["foodie", "photo", "couple"],
        "trip_role": "enrichment",
        "time_window_strength": "medium", "reservation_pressure": "none",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "葡挞、杏仁饼、猪扒包与葡式点心足够形成澳门高辨识度的轻量吃喝簇。",
    },
    # ── 深圳 ──────────────────────────────────────────────────────────────────
    {
        "cluster_id": "sz_nantou_shekou_heritage",
        "circle_id": CIRCLE, "city_code": "shenzhen",
        "name_zh": "深圳·南头古城蛇口线",
        "name_en": "Shenzhen Nantou Ancient Town & Shekou Line",
        "level": "B", "default_duration": "half_day",
        "primary_corridor": "nanshan_nantou_shekou",
        "seasonality": ["all_year"],
        "profile_fit": ["culture", "photo", "foodie", "couple"],
        "trip_role": "enrichment",
        "time_window_strength": "medium", "reservation_pressure": "none",
        "secondary_attach_capacity": 2, "default_selected": False,
        "notes": "南头古城活化改造+蛇口海上世界，新旧碰撞的半天文化散步线。",
    },
    {
        "cluster_id": "sz_lianhuashan_lightshow",
        "circle_id": CIRCLE, "city_code": "shenzhen",
        "name_zh": "深圳·莲花山灯光秀夜景线",
        "name_en": "Shenzhen Lianhua Mountain Light Show Night Line",
        "level": "B", "default_duration": "quarter_day",
        "primary_corridor": "futian_lianhuashan",
        "seasonality": ["all_year"],
        "profile_fit": ["couple", "photo", "first_timer"],
        "trip_role": "enrichment",
        "time_window_strength": "strong", "reservation_pressure": "none",
        "secondary_attach_capacity": 1, "default_selected": False,
        "notes": "莲花山山顶邓小平雕像+市民中心灯光秀，深圳最具代表性的夜景收口线。",
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
        logger.info("广府圈活动簇补全完成: 新增=%d 跳过=%d 总计=%d", new_count, skip_count, len(ALL_CLUSTERS))


if __name__ == "__main__":
    asyncio.run(seed())
