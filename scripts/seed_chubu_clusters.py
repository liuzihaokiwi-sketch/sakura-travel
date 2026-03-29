"""
seed_chubu_mountain_circle_clusters.py — chubu_mountain_circle 活动簇数据

从 mojor/ 目录转换生成。
幂等：cluster_id 已存在则 SKIP。

执行：
    python scripts/seed_chubu_clusters.py
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
        "cluster_id": "chu_kanazawa_higashi_omicho_grand",
        "circle_id": "chubu_mountain_circle",
        "city_code": "kanazawa",
        "name_zh": "金泽·东茶屋街近江町完整版",
        "name_en": "Kanazawa Higashi Chaya and Omicho Grand Route",
        "level": "S",
        "default_duration": "half_day",
        "primary_corridor": "omicho_higashi_chaya_asanogawa",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "first_timer",
            "food",
            "culture",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": True,
        "notes": "以近江町市场的海鲜早餐或午餐接东茶屋街与浅野川一带，兼具老城气质与拍照价值，常占半天并明显影响金泽当日东线安排。",
        "experience_family": "food",
        "rhythm_role": "peak",
        "energy_level": "medium"
    },
    {
        "cluster_id": "chu_kanazawa_modern_garden_axis",
        "circle_id": "chubu_mountain_circle",
        "city_code": "kanazawa",
        "name_zh": "金泽·21世纪美术馆兼六园完整版",
        "name_en": "Kanazawa 21st Century Museum and Kenrokuen Axis",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "hirosaka_kenrokuen_castle_park",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "art",
            "design",
            "couple",
            "first_timer"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "把21世纪美术馆、兼六园与金泽城公园放在同一条步行轴线上，适合白天看展配园林收尾，展期与热门时段会抬高排队与入场压力。",
        "experience_family": "art",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "chu_kanazawa_samurai_craft_quiet",
        "circle_id": "chubu_mountain_circle",
        "city_code": "kanazawa",
        "name_zh": "金泽·武家屋敷工艺静线",
        "name_en": "Kanazawa Samurai District and Craft Quiet Route",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "nagamachi_dt_suzuki_hondanomori",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "culture",
            "design",
            "quiet",
            "couple"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "围绕长町武家屋敷、铃木大拙馆与本多之森一带展开，适合偏安静与工艺审美的用户单独留半天，不适合被当作顺路补点草草带过。",
        "experience_family": "locallife",
        "rhythm_role": "recovery",
        "energy_level": "low"
    },
    {
        "cluster_id": "chu_takayama_morning_market_sake",
        "circle_id": "chubu_mountain_circle",
        "city_code": "takayama",
        "name_zh": "高山·朝市酒造一条街完整线",
        "name_en": "Takayama Morning Market and Sake Brewery Route",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "miyagawa_jinya_sanmachi_breweries",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "food",
            "culture",
            "photo",
            "first_timer"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "以宫川朝市或阵屋前朝市起步，接三町古街与酒藏试饮，强依赖上午时段与步行节奏，适合把高山排成有明确晨间窗口的一天。",
        "experience_family": "food",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "chu_takayama_festival_seasonal",
        "circle_id": "chubu_mountain_circle",
        "city_code": "takayama",
        "name_zh": "高山·春秋祭季节线",
        "name_en": "Takayama Spring and Autumn Festival Route",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "old_town_hie_sakurayama_festival_axis",
        "seasonality": [
            "spring",
            "autumn"
        ],
        "profile_fit": [
            "festival",
            "culture",
            "photo",
            "first_timer"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "对应春祭4月14至15日与秋祭10月9至10日的山车与夜祭窗口，命中日期时会直接改变住宿与到达顺序，是高山最典型的强时窗活动簇。",
        "experience_family": "flower",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "chu_shirakawago_winter_lightup",
        "circle_id": "chubu_mountain_circle",
        "city_code": "shirakawago",
        "name_zh": "白川乡·冬季点灯线",
        "name_en": "Shirakawa-go Winter Light-Up Route",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "ogimachi_lightup_view_axis",
        "seasonality": [
            "winter"
        ],
        "profile_fit": [
            "photo",
            "seasonal",
            "culture",
            "couple"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "白川乡冬季点灯是极强日期型活动，通常需要围绕傍晚入场与返程交通专门排程；2026年活动继续严格预约制，临时到访不可行。",
        "experience_family": "flower",
        "rhythm_role": "peak",
        "energy_level": "medium"
    },
    {
        "cluster_id": "chu_shirakawago_gassho_village_full",
        "circle_id": "chubu_mountain_circle",
        "city_code": "shirakawago",
        "name_zh": "白川乡·合掌村完整线",
        "name_en": "Shirakawa-go Gassho Village Full Route",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "ogimachi_gassho_observatory_riverwalk",
        "seasonality": [
            "all_year",
            "winter",
            "autumn_leaves"
        ],
        "profile_fit": [
            "first_timer",
            "photo",
            "culture",
            "family"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "荻町合掌村、城山展望台与合掌造民宿本身就足以撑起完整一日甚至一晚，白天与傍晚景观差异明显，不应只在冬季点灯时才成立。",
        "experience_family": "shrine",
        "rhythm_role": "peak",
        "energy_level": "medium"
    },
    {
        "cluster_id": "chu_kamikochi_alps_hiking_day",
        "circle_id": "chubu_mountain_circle",
        "city_code": "matsumoto",
        "name_zh": "上高地·河童桥明神池徒步线",
        "name_en": "Kamikochi Kappabashi-Myojin Pond Hiking Route",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "kamikochi_taishoike_kappabashi_myojin",
        "seasonality": [
            "summer",
            "autumn_leaves"
        ],
        "profile_fit": [
            "nature",
            "hiking",
            "photo",
            "slow_travel"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "上高地是中部山岳最标准的整日型自然主活动之一，河童桥到明神池的步线强依赖开山季、公交换乘与早出发，常直接决定住平汤还是松本。",
        "experience_family": "mountain",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "chu_gero_onsen_river_stay",
        "circle_id": "chubu_mountain_circle",
        "city_code": "gero",
        "name_zh": "下吕·温泉河畔住宿线",
        "name_en": "Gero Onsen Riverside Stay Route",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "gero_station_hida_river_onsen_town",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "onsen",
            "couple",
            "relax",
            "senior"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "以下吕站、飞驒川沿岸与温泉街步行圈为核心，适合专门住一晚做泡汤与河畔散步，不再只是高山或名古屋之间的换乘补位。",
        "experience_family": "onsen",
        "rhythm_role": "recovery",
        "energy_level": "low"
    },
    {
        "cluster_id": "chu_okuhida_onsenkyo_alps_stay",
        "circle_id": "chubu_mountain_circle",
        "city_code": "takayama",
        "name_zh": "奥飞驒·温泉乡北阿尔卑斯住宿线",
        "name_en": "Okuhida Onsen Villages and Northern Alps Stay Route",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "hirayu_fukuchi_shinhotaka_okuhida",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "onsen",
            "nature",
            "photo",
            "couple"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "以平汤到新穗高为主轴串联奥飞驒温泉乡五大温泉地，常与缆车或山景露天风吕绑定，天然更适合住一晚而不是匆忙日归。",
        "experience_family": "onsen",
        "rhythm_role": "recovery",
        "energy_level": "medium"
    },
    {
        "cluster_id": "chu_tateyama_kurobe_alpine_route",
        "circle_id": "chubu_mountain_circle",
        "city_code": "regional",
        "name_zh": "中部山岳·立山黑部阿尔卑斯路线",
        "name_en": "Tateyama Kurobe Alpine Route",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "tateyama_murodo_kurobe_dam_ogizawa",
        "seasonality": [
            "spring",
            "summer",
            "autumn"
        ],
        "profile_fit": [
            "first_timer",
            "nature",
            "photo",
            "scenic"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "立山站至扇泽的多段交通穿越本身就是完整主活动，2026年运营期为4月15日至11月30日，强依赖早出发与开山季节窗口。",
        "experience_family": "mountain",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "chu_nagoya_miso_food_route",
        "circle_id": "chubu_mountain_circle",
        "city_code": "nagoya",
        "name_zh": "名古屋·味噌美食线",
        "name_en": "Nagoya Miso Food Route",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "nagoya_station_sakae_osu_food_axis",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "food",
            "first_timer",
            "local_life",
            "couple"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "围绕味噌炸猪排、味噌煮乌冬、土手煮等名古屋味噌系料理展开，常会主导午晚餐与区域选择，对重吃路线来说足以单独占半天。",
        "experience_family": "food",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "chu_nagoya_castle_atsuta_grand",
        "circle_id": "chubu_mountain_circle",
        "city_code": "nagoya",
        "name_zh": "名古屋·名古屋城热田神宫完整版",
        "name_en": "Nagoya Castle and Atsuta Jingu Grand Route",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "nagoya_castle_atsuta_jingu",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "first_timer",
            "history",
            "culture",
            "family"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": True,
        "notes": "以名古屋城与热田神宫两大历史锚点构成最稳的名古屋经典线，足以单独排满一天，并自然挂接蓬莱轩或荣一带晚餐。",
        "experience_family": "shrine",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "chu_matsumoto_art_town_life",
        "circle_id": "chubu_mountain_circle",
        "city_code": "matsumoto",
        "name_zh": "松本·美术馆城下町生活线",
        "name_en": "Matsumoto Museum of Art and Castle Town Life Route",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "matsumoto_art_museum_nakamachi_nawate",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "art",
            "design",
            "citywalk",
            "couple"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "weak",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "以松本市美术馆、仲町通与绳手通为核心，适合草间弥生或城下町生活感画像单独留半天，和城堡主簇形成互补而非重复。",
        "experience_family": "art",
        "rhythm_role": "recovery",
        "energy_level": "low"
    },
    {
        "cluster_id": "chu_nagoya_ghibli_park_full_day",
        "circle_id": "chubu_mountain_circle",
        "city_code": "nagoya",
        "name_zh": "名古屋·吉卜力公园全日线",
        "name_en": "Nagoya Ghibli Park Full-Day Route",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "nagoya_nagakute_ghibli_park",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "family",
            "design",
            "anime",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "吉卜力公园各展区需分批次预约，全天动线规划复杂，是名古屋最强主题目的地，对粉丝画像极强吸引力。",
        "experience_family": "themepark",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "chu_nakasendo_tsumago_magome_walk",
        "circle_id": "chubu_mountain_circle",
        "city_code": "regional",
        "name_zh": "中山道·妻笼马笼宿场步道线",
        "name_en": "Nakasendo Tsumago-Magome Post Town Walk",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "nakasendo_tsumago_magome",
        "seasonality": [
            "all_year",
            "autumn_leaves"
        ],
        "profile_fit": [
            "hiking",
            "history",
            "photo",
            "slow_travel"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "妻笼到马笼的8公里古道徒步是中山道最完整的步行体验，宿场建筑和林间古道景观足以独立占满全天。",
        "experience_family": "locallife",
        "rhythm_role": "contrast",
        "energy_level": "high"
    },
    {
        "cluster_id": "chu_kaga_onsen_ryokan_stay",
        "circle_id": "chubu_mountain_circle",
        "city_code": "regional",
        "name_zh": "加贺·温泉旅馆住宿线",
        "name_en": "Kaga Onsen Ryokan Stay Route",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "kaga_onsen_yamashiro_yamanaka",
        "seasonality": [
            "all_year",
            "autumn_leaves",
            "winter"
        ],
        "profile_fit": [
            "couple",
            "onsen",
            "luxury",
            "slow_travel"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "山代、山中、片山津三处加贺温泉乡各有特色，适合以旅馆过夜为核心建立与金泽区分的温泉住宿主线。",
        "experience_family": "onsen",
        "rhythm_role": "recovery",
        "energy_level": "low"
    },
    {
        "cluster_id": "chu_shinhotaka_ropeway_panorama",
        "circle_id": "chubu_mountain_circle",
        "city_code": "takayama",
        "name_zh": "奥飞驒·新穗高缆车全景线",
        "name_en": "Okuhida Shinhotaka Ropeway Panorama Route",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "shinhotaka_ropeway_panorama",
        "seasonality": [
            "all_year",
            "autumn_leaves",
            "winter"
        ],
        "profile_fit": [
            "photo",
            "nature",
            "couple",
            "first_timer"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "新穗高二阶缆车是北阿尔卑斯唯一双层缆车，秋叶与冬雪期全景视野极强，适合从高山城区拆出半日景观主线。",
        "experience_family": "mountain",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "chu_nakasendo_magome_tsumago",
        "circle_id": "chubu_mountain_circle",
        "city_code": "nagoya",
        "name_zh": "中部·中山道马笼妻笼宿场线",
        "name_en": "Chubu Nakasendo Magome-Tsumago Post Town Line",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "chu_kiso_nakasendo_magome_tsumago",
        "seasonality": [
            "all_year",
            "spring",
            "autumn"
        ],
        "profile_fit": [
            "history",
            "hiking",
            "photo",
            "slow_travel"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "马笼到妻笼是中部最典型的历史步道型主簇，宿场、古道和山村景观足以独立占满一天。",
        "experience_family": "locallife",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "chu_kanazawa_higashichaya_night",
        "circle_id": "chubu_mountain_circle",
        "city_code": "kanazawa",
        "name_zh": "金泽·东茶屋街夜走线",
        "name_en": "Chubu Kanazawa Higashi Chaya Night Walk",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "chu_kanazawa_higashichaya_night",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "couple",
            "photo",
            "slow_travel"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "strong",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "东茶屋街白天和夜晚氛围差异明显，夜走更适合作为金泽古都线的晚间收口。",
        "experience_family": "citynight",
        "rhythm_role": "contrast",
        "energy_level": "low"
    },
    {
        "cluster_id": "chu_kanazawa_omicho_food",
        "circle_id": "chubu_mountain_circle",
        "city_code": "kanazawa",
        "name_zh": "金泽·近江町市场美食线",
        "name_en": "Chubu Kanazawa Omicho Market Food Line",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "chu_kanazawa_omicho_food",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "foodie",
            "first_timer",
            "local_life"
        ],
        "trip_role": "buffer",
        "time_window_strength": "strong",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "近江町市场自成金泽海鲜早餐与午市主场，适合从大主线中拆出晨间美食补位。",
        "experience_family": "food",
        "rhythm_role": "utility",
        "energy_level": "medium"
    },
    {
        "cluster_id": "chu_gero_onsen_ryokan_stay",
        "circle_id": "chubu_mountain_circle",
        "city_code": "gero",
        "name_zh": "下吕·温泉旅馆体验线",
        "name_en": "Chubu Gero Onsen Ryokan Stay Line",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "chu_gero_onsen_ryokan",
        "seasonality": [
            "all_year",
            "winter"
        ],
        "profile_fit": [
            "couple",
            "onsen",
            "slow_travel"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "下吕真正强的是一泊二食旅馆体验，而不只是温泉街散步，应单独建为过夜主簇。",
        "experience_family": "onsen",
        "rhythm_role": "recovery",
        "energy_level": "low"
    },
    {
        "cluster_id": "chu_okuhida_shinhotaka_roten",
        "circle_id": "chubu_mountain_circle",
        "city_code": "takayama",
        "name_zh": "奥飞驒·新穗高露天温泉线",
        "name_en": "Chubu Okuhida Shinhotaka & Rotenburo Line",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "chu_okuhida_shinhotaka",
        "seasonality": [
            "all_year",
            "autumn",
            "winter"
        ],
        "profile_fit": [
            "nature",
            "onsen",
            "couple",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "新穗高缆车和奥飞驒露天风吕组合后形成明显的山岳温泉主线，和高山古城完全不同。",
        "experience_family": "onsen",
        "rhythm_role": "recovery",
        "energy_level": "medium"
    },
    {
        "cluster_id": "chu_nagoya_atsuta_osu",
        "circle_id": "chubu_mountain_circle",
        "city_code": "nagoya",
        "name_zh": "名古屋·热田神宫大须商店街线",
        "name_en": "Chubu Nagoya Atsuta Shrine & Osu Line",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "chu_nagoya_atsuta_osu",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "first_timer",
            "culture",
            "foodie",
            "shopping"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 3,
        "default_selected": False,
        "notes": "热田神宫和大须商店街组合后，能较完整地承接名古屋的宗教历史与庶民商业生活。",
        "experience_family": "shrine",
        "rhythm_role": "peak",
        "energy_level": "medium"
    },
    {
        "cluster_id": "chu_nagoya_hitsumabushi_tebasaki",
        "circle_id": "chubu_mountain_circle",
        "city_code": "nagoya",
        "name_zh": "名古屋·鳗鱼饭手羽先美食深度线",
        "name_en": "Chubu Nagoya Hitsumabushi & Tebasaki Food Depth Line",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "chu_nagoya_food_depth",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "foodie",
            "local_life",
            "first_timer"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "medium",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "与已有味噌系路线区分，这条线更强调鳗鱼饭、手羽先和名古屋夜间饮食场景。",
        "experience_family": "food",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "chu_takayama_hidabeef_food",
        "circle_id": "chubu_mountain_circle",
        "city_code": "takayama",
        "name_zh": "高山·飞驒牛美食线",
        "name_en": "Chubu Takayama Hida Beef Food Line",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "chu_takayama_hidabeef",
        "seasonality": [
            "all_year"
        ],
        "profile_fit": [
            "foodie",
            "couple",
            "first_timer"
        ],
        "trip_role": "buffer",
        "time_window_strength": "medium",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "飞驒牛本身足以形成高山的主题吃喝簇，适合作为古城和朝市线后的半日升级。",
        "experience_family": "food",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "chu_shirakawago_gassho_overnight",
        "circle_id": "chubu_mountain_circle",
        "city_code": "shirakawago",
        "name_zh": "白川乡·合掌造宿泊体验线",
        "name_en": "Chubu Shirakawago Gassho Overnight Line",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "chu_shirakawago_stay",
        "seasonality": [
            "all_year",
            "winter"
        ],
        "profile_fit": [
            "slow_travel",
            "photo",
            "culture"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "和日归簇区分，白川乡真正高级的玩法是住进合掌造并体验清晨和夜晚村落氛围。",
        "experience_family": "shrine",
        "rhythm_role": "peak",
        "energy_level": "medium"
    },
    {
        "cluster_id": "chu_tateyama_kurobe_autumn",
        "circle_id": "chubu_mountain_circle",
        "city_code": "matsumoto",
        "name_zh": "中部·立山黑部秋季红叶线",
        "name_en": "Chubu Tateyama Kurobe Autumn Foliage Line",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "chu_tateyama_kurobe_autumn",
        "seasonality": [
            "autumn_leaves"
        ],
        "profile_fit": [
            "photo",
            "nature",
            "first_timer"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "秋季立山黑部的红叶和高山交通窗口明显强于常规季节，命中时应独立升级建簇。",
        "experience_family": "flower",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "chu_takayama_festival_fullcycle",
        "circle_id": "chubu_mountain_circle",
        "city_code": "takayama",
        "name_zh": "高山·祭典完整线",
        "name_en": "Chubu Takayama Festival Full Cycle Line",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "chu_takayama_festival_full",
        "seasonality": [
            "festival"
        ],
        "profile_fit": [
            "culture",
            "photo",
            "festival"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "与已有seasonal不同，这条线强调春祭与秋祭的完整节奏、屋台巡行和过夜资源争夺。",
        "experience_family": "flower",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "chu_matsumoto_kaichi_soba",
        "circle_id": "chubu_mountain_circle",
        "city_code": "matsumoto",
        "name_zh": "松本·城学校荞麦街线",
        "name_en": "Chubu Matsumoto Castle Kaichi School & Soba Line",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "chu_matsumoto_castle_kaichi_soba",
        "seasonality": [
            "all_year",
            "autumn"
        ],
        "profile_fit": [
            "history",
            "foodie",
            "walk",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "weak",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "在已有松本城与艺文生活基础上，这条线补足旧开智学校和荞麦街的完整城市深度。",
        "experience_family": "locallife",
        "rhythm_role": "contrast",
        "energy_level": "medium"
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
                     "chubu_mountain_circle", new_count, skip_count, len(CLUSTERS))


if __name__ == "__main__":
    asyncio.run(seed())
