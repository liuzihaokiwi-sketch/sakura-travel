"""
seed_kyushu_onsen_circle_clusters.py — kyushu_onsen_circle 活动簇数据

从 mojor/ 目录转换生成。
幂等：cluster_id 已存在则 SKIP。

执行：
    python scripts/seed_kyushu_clusters.py
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
        "cluster_id": "kyu_hakata_yatai_night_culture",
        "circle_id": "kyushu_onsen_circle",
        "city_code": "fukuoka",
        "name_zh": "福冈·博多屋台夜食文化线",
        "name_en": "Hakata Yatai Night Food Culture",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "hakata_nakasu_tenjin_night",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "food",
            "night",
            "friends"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "以中洲、天神与博多周边屋台为核心，夜间开摊时间窗非常明确，适合把晚餐、续摊与城市夜生活并成一整段体验。",
        "experience_family": "food",
        "rhythm_role": "recovery",
        "energy_level": "low"
    },
    {
        "cluster_id": "kyu_dazaifu_tenmangu_culture",
        "circle_id": "kyushu_onsen_circle",
        "city_code": "fukuoka",
        "name_zh": "福冈·太宰府天满宫文化线",
        "name_en": "Dazaifu Tenmangu Cultural Route",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "dazaifu_tenmangu",
        "seasonality": [
            "all_year",
            "sakura",
            "autumn_leaves"
        ],
        "profile_fit": [
            "culture",
            "family",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "以太宰府天满宫参拜表参道与周边文化设施为主，梅花季与考试季辨识度更强，是福冈最稳的半日至一日文化外挂机。",
        "experience_family": "shrine",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "kyu_beppu_jigoku_meguri_full",
        "circle_id": "kyushu_onsen_circle",
        "city_code": "beppu",
        "name_zh": "别府·地狱巡礼完整线",
        "name_en": "Beppu Jigoku Meguri Full Route",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "kannawa_shibaseki_jigoku",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "first_timer",
            "photo",
            "family"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "围绕海地狱等七大地狱展开，铁轮与柴石两片区分开且需要换乘或驾车衔接，通常会独立占掉别府完整观光日。",
        "experience_family": "mountain",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "kyu_yufuin_kinrin_onsen_stroll",
        "circle_id": "kyushu_onsen_circle",
        "city_code": "yufuin",
        "name_zh": "由布院·金鳞湖温泉街完整线",
        "name_en": "Yufuin Kinrin Lake and Onsen Town Route",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "yufuin_onsen_town",
        "seasonality": [
            "all_year",
            "autumn_leaves",
            "winter"
        ],
        "profile_fit": [
            "couple",
            "photo",
            "relax"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "以金鳞湖晨景、汤之坪街道步行与旅馆泡汤为主，早晨雾气和傍晚温泉节奏都很关键，常直接决定由布院是否住一晚。",
        "experience_family": "onsen",
        "rhythm_role": "recovery",
        "energy_level": "low"
    },
    {
        "cluster_id": "kyu_nagasaki_bay_nightview_full",
        "circle_id": "kyushu_onsen_circle",
        "city_code": "nagasaki",
        "name_zh": "长崎·港城夜景完整版",
        "name_en": "Nagasaki Bay and Night View Full Route",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "dejima_oura_inasa",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "couple",
            "photo",
            "history"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "把出岛、大浦与山手片区串到稻佐山夜景收尾，白天看开港史、傍晚抢山顶视角，天然会主导长崎一整天与住宿节奏。",
        "experience_family": "citynight",
        "rhythm_role": "peak",
        "energy_level": "medium"
    },
    {
        "cluster_id": "kyu_gunkanjima_cruise",
        "circle_id": "kyushu_onsen_circle",
        "city_code": "nagasaki",
        "name_zh": "长崎·军舰岛登陆航线",
        "name_en": "Gunkanjima Landing Cruise",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "nagasaki_port_gunkanjima",
        "seasonality": [
            "all_year",
            "summer"
        ],
        "profile_fit": [
            "history",
            "photo",
            "industrial_heritage"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "以长崎港出发的军舰岛登陆巡航为核心，船班和海况决定成行率，通常需要提前预约并把前后半天都围绕它来排。",
        "experience_family": "sea",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "kyu_kumamoto_castle_suizenji_full",
        "circle_id": "kyushu_onsen_circle",
        "city_code": "kumamoto",
        "name_zh": "熊本·熊本城水前寺完整线",
        "name_en": "Kumamoto Castle and Suizenji Full Route",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "kumamoto_central_heritage",
        "seasonality": [
            "all_year",
            "sakura",
            "autumn_leaves"
        ],
        "profile_fit": [
            "history",
            "family",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "以熊本城和水前寺成趣园组成城市文化主轴，城郭与回游庭园组合完整，适合拿出整天深挖熊本市内。",
        "experience_family": "shrine",
        "rhythm_role": "contrast",
        "energy_level": "high"
    },
    {
        "cluster_id": "kyu_kurokawa_onsen_hideaway",
        "circle_id": "kyushu_onsen_circle",
        "city_code": "kumamoto",
        "name_zh": "熊本·黑川温泉隐世线",
        "name_en": "Kurokawa Onsen Hideaway Stay",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "kurokawa_onsen",
        "seasonality": [
            "all_year",
            "autumn_leaves",
            "winter"
        ],
        "profile_fit": [
            "relax",
            "couple",
            "luxury"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "以山间温泉街散策、入汤手形外汤巡礼和旅馆住宿为核心，最适合专门住一晚放慢节奏，对自驾与驻点选择影响很大。",
        "experience_family": "onsen",
        "rhythm_role": "recovery",
        "energy_level": "low"
    },
    {
        "cluster_id": "kyu_aso_caldera_grassland_drive",
        "circle_id": "kyushu_onsen_circle",
        "city_code": "aso",
        "name_zh": "阿苏·火山口草千里完整线",
        "name_en": "Aso Crater and Kusasenri Grassland Route",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "aso_crater_kusasenri_daikanbo",
        "seasonality": [
            "all_year",
            "summer",
            "autumn_leaves"
        ],
        "profile_fit": [
            "nature",
            "photo",
            "roadtrip",
            "first_timer"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "阿苏的成立方式是围绕火山口、草千里与大观峰展开一整天；开放管制、天气和自驾节奏都会真实改变熊本 / 黑川的住宿与进出顺序。",
        "experience_family": "mountain",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "kyu_kagoshima_sakurajima_bay",
        "circle_id": "kyushu_onsen_circle",
        "city_code": "kagoshima",
        "name_zh": "鹿儿岛·樱岛海湾完整线",
        "name_en": "Kagoshima Sakurajima Bay Full Route",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "sakurajima_ferry_yunohira_bay",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "first_timer",
            "photo",
            "nature",
            "roadtrip"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "樱岛不是鹿儿岛港口远眺的背景板，而是坐 ferry 上岛、看展望台和火山海湾的一整天主活动，常直接决定鹿儿岛是否外住或加租车。",
        "experience_family": "mountain",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "kyu_ibusuki_sandbath_onsen",
        "circle_id": "kyushu_onsen_circle",
        "city_code": "kagoshima",
        "name_zh": "鹿儿岛·指宿砂蒸温泉线",
        "name_en": "Ibusuki Sand Bath Onsen Route",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "ibusuki_coastal_onsen",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "relax",
            "couple",
            "wellness"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "以海滨砂蒸温泉为绝对主轴，再接常规温泉或海岸散步最顺，是鹿儿岛南下路线里辨识度最高的半日到一日型体验。",
        "experience_family": "onsen",
        "rhythm_role": "recovery",
        "energy_level": "low"
    },
    {
        "cluster_id": "kyu_yanagawa_water_town_cruise",
        "circle_id": "kyushu_onsen_circle",
        "city_code": "fukuoka",
        "name_zh": "福冈·柳川水乡线",
        "name_en": "Yanagawa Water Town Cruise",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "yanagawa_canal",
        "seasonality": [
            "all_year",
            "sakura",
            "autumn_leaves",
            "winter"
        ],
        "profile_fit": [
            "couple",
            "family",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "以掘割游船和蒸笼鳗鱼为核心，船程本身就占去固定时段，春樱秋景和冬季暖桌船都会明显影响出发时间与日归节奏。",
        "experience_family": "locallife",
        "rhythm_role": "contrast",
        "energy_level": "low"
    },
    {
        "cluster_id": "kyu_mojiko_retro_port_walk",
        "circle_id": "kyushu_onsen_circle",
        "city_code": "fukuoka",
        "name_zh": "福冈·门司港怀旧线",
        "name_en": "Mojiko Retro Port Walk",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "mojiko_retro",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "photo",
            "history",
            "couple"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "围绕门司港复古建筑群、关门海峡景观与港口散步展开，白天看建筑、傍晚看海峡灯光最顺，适合作为北九州独立半日主题线。",
        "experience_family": "sea",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "kyu_nagasaki_lantern_festival",
        "circle_id": "kyushu_onsen_circle",
        "city_code": "nagasaki",
        "name_zh": "长崎·灯笼祭线",
        "name_en": "Nagasaki Lantern Festival Route",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "shinchi_chinatown_central_nagasaki",
        "seasonality": [
            "winter"
        ],
        "profile_fit": [
            "festival",
            "photo",
            "couple"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "农历新年前后全城灯会和夜间演出时间窗极强，会直接推高长崎住宿与晚间排程优先级，是典型季节限定主活动。",
        "experience_family": "citynight",
        "rhythm_role": "peak",
        "energy_level": "medium"
    },
    {
        "cluster_id": "kyu_hakata_gion_yamakasa",
        "circle_id": "kyushu_onsen_circle",
        "city_code": "fukuoka",
        "name_zh": "福冈·博多祇园山笠线",
        "name_en": "Hakata Gion Yamakasa Festival Route",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "hakata_kushida_shrine_festival",
        "seasonality": [
            "summer"
        ],
        "profile_fit": [
            "festival",
            "culture",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "以7月上半月的博多祇园山笠为核心，展示山笠与清晨追山时间点都很强，足以改变福冈城市住宿与观礼动线。",
        "experience_family": "shrine",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "kyu_takachiho_gorge_myth_route",
        "circle_id": "kyushu_onsen_circle",
        "city_code": "kumamoto",
        "name_zh": "高千穗·峡谷神话路线",
        "name_en": "Takachiho Gorge and Mythic Route",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "takachiho_gorge_amanoiwato_shrine",
        "seasonality": [
            "all_year",
            "autumn_leaves"
        ],
        "profile_fit": [
            "photo",
            "nature",
            "culture",
            "roadtrip"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "高千穗峡谷划船、天岩户神社和夜神乐共同构成九州最强神话文化体验线，自驾全天为佳。",
        "experience_family": "shrine",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "kyu_unzen_jigoku_onsen_stay",
        "circle_id": "kyushu_onsen_circle",
        "city_code": "nagasaki",
        "name_zh": "云仙·地狱温泉住宿线",
        "name_en": "Unzen Jigoku Onsen Stay",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "unzen_jigoku_onsen_town",
        "seasonality": [
            "all_year",
            "autumn_leaves",
            "winter"
        ],
        "profile_fit": [
            "onsen",
            "nature",
            "slow_travel",
            "couple"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "云仙地狱是长崎县最具个性的温泉区，硫磺气场和秋叶季景观突出，适合做过夜深度住宿线。",
        "experience_family": "onsen",
        "rhythm_role": "recovery",
        "energy_level": "low"
    },
    {
        "cluster_id": "kyu_kirishima_jingu_onsen_drive",
        "circle_id": "kyushu_onsen_circle",
        "city_code": "kagoshima",
        "name_zh": "霾岛·神宫高原温泉自驾线",
        "name_en": "Kirishima Jingu and Highland Onsen Drive",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "kirishima_jingu_ebino_onsen",
        "seasonality": [
            "all_year",
            "autumn_leaves"
        ],
        "profile_fit": [
            "roadtrip",
            "nature",
            "onsen",
            "couple"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "霾岛神宫、御池和栗野岳温泉形成完整高原温泉自驾主线，秋叶期景观最佳，与鹿儿岛城区明确区分。",
        "experience_family": "shrine",
        "rhythm_role": "contrast",
        "energy_level": "high"
    },
    {
        "cluster_id": "kyu_beppu_onsen_street_walk",
        "circle_id": "kyushu_onsen_circle",
        "city_code": "beppu",
        "name_zh": "别府·铁轮温泉街漫步线",
        "name_en": "Beppu Kannawa Onsen Street Walk",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "kannawa_onsen_street",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "relax",
            "couple",
            "food"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "medium",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "铁轮温泉街的足蒸温泉、地狱蒸料理和玉手箱汤等适合从地狱巡游拆出短时体验补位线。",
        "experience_family": "onsen",
        "rhythm_role": "utility",
        "energy_level": "low"
    },
    {
        "cluster_id": "kyu_fukuoka_tenjin_shopping",
        "circle_id": "kyushu_onsen_circle",
        "city_code": "fukuoka",
        "name_zh": "福冈·天神地下街购物线",
        "name_en": "Fukuoka Tenjin Underground Shopping",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "tenjin_underground",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "shopping",
            "couple",
            "family"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "天神地下街和大名区域是福冈最完整的购物商圈，适合雨天或到离境日作为城市补位半日线。",
        "experience_family": "locallife",
        "rhythm_role": "utility",
        "energy_level": "low"
    },
    {
        "cluster_id": "kyu_kagoshima_tenmonkan_food",
        "circle_id": "kyushu_onsen_circle",
        "city_code": "kagoshima",
        "name_zh": "鹿儿岛·天文馆通美食街线",
        "name_en": "Kagoshima Tenmonkan Food Street",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "tenmonkan_arcade",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "foodie",
            "local_life"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "medium",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "天文馆通是鹿儿岛市内最集中的美食与商业街区，适合做樱岛线后的城市晚间补位。",
        "experience_family": "food",
        "rhythm_role": "utility",
        "energy_level": "low"
    },
    # ── 补充 B 级 buffer（3→8）──────────────────────────────────────────────
    {
        "cluster_id": "yuf_yunotsubo_craft_sweets",
        "circle_id": "kyushu_onsen_circle",
        "city_code": "oita",
        "name_zh": "由布院·汤之坪手工艺甜品街线",
        "name_en": "Yufuin Yunotsubo Street Craft & Sweets",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "yunotsubo_kaido",
        "seasonality": ["all_year"],
        "profile_fit": ["couple", "photo", "slow_travel", "arrival_friendly", "rainy_day_ok"],
        "trip_role": "enrichment",
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "汤之坪街道集中了手工玻璃、甜品店、猫头鹰森林等小店，步行即可，适合由布院金鳞湖线之后的下午补位。",
        "experience_family": "locallife",
        "rhythm_role": "recovery",
        "energy_level": "low"
    },
    {
        "cluster_id": "nag_shinchi_chinatown",
        "circle_id": "kyushu_onsen_circle",
        "city_code": "nagasaki",
        "name_zh": "长崎·新地中华街美食补位线",
        "name_en": "Nagasaki Shinchi Chinatown Food Line",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "shinchi_chinatown",
        "seasonality": ["all_year"],
        "profile_fit": ["foodie", "first_timer", "arrival_friendly", "rainy_day_ok"],
        "trip_role": "enrichment",
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "日本三大中华街之一，强棒面和角煮馒头是必尝，规模小走20分钟逛完，适合做哥拉巴园线之后的午餐或傍晚补位。",
        "experience_family": "food",
        "rhythm_role": "utility",
        "energy_level": "low"
    },
    {
        "cluster_id": "fuk_nakasu_yatai_night",
        "circle_id": "kyushu_onsen_circle",
        "city_code": "fukuoka",
        "name_zh": "福冈·中洲屋台夜宵线",
        "name_en": "Fukuoka Nakasu Yatai Night Stalls",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "nakasu_riverside",
        "seasonality": ["all_year"],
        "profile_fit": ["foodie", "nightlife", "friends"],
        "trip_role": "enrichment",
        "time_window_strength": "strong",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "中洲川端沿河屋台群是博多夜生活标志，18:00后出摊，拉面+关东煮+烧�的+天妇罗，适合任何白天线路之后的晚间补位。",
        "experience_family": "food",
        "rhythm_role": "utility",
        "energy_level": "low"
    },
    {
        "cluster_id": "fuk_canal_city_shopping",
        "circle_id": "kyushu_onsen_circle",
        "city_code": "fukuoka",
        "name_zh": "福冈·博多运河城购物线",
        "name_en": "Fukuoka Canal City Shopping",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "hakata_canal_city",
        "seasonality": ["all_year"],
        "profile_fit": ["shopping", "family", "arrival_friendly", "rainy_day_ok"],
        "trip_role": "enrichment",
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "博多运河城是全室内大型商业设施，含拉面竞技场和喷泉秀，雨天和购物需求的理想补位。",
        "experience_family": "locallife",
        "rhythm_role": "utility",
        "energy_level": "low"
    },
    {
        "cluster_id": "bep_jigoku_mushi_food",
        "circle_id": "kyushu_onsen_circle",
        "city_code": "beppu",
        "name_zh": "别府·地狱蒸し工房美食线",
        "name_en": "Beppu Jigoku Mushi Steam Cooking",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "kannawa_onsen_street",
        "seasonality": ["all_year"],
        "profile_fit": ["foodie", "couple", "culture"],
        "trip_role": "enrichment",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "铁轮温泉地狱蒸し工房用天然温泉蒸汽蒸食材，体验独特，适合地狱巡礼线之后的午餐补位。",
        "experience_family": "food",
        "rhythm_role": "recovery",
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
                     "kyushu_onsen_circle", new_count, skip_count, len(CLUSTERS))


if __name__ == "__main__":
    asyncio.run(seed())
