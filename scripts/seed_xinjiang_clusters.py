"""
seed_xinjiang_yili_circle_clusters.py — xinjiang_yili_circle 活动簇数据

从 mojor/ 目录转换生成。
幂等：cluster_id 已存在则 SKIP。

执行：
    python scripts/seed_xinjiang_clusters.py
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
        "cluster_id": "xj_sailimu_lake_loop_core",
        "circle_id": "xinjiang_yili_circle",
        "city_code": "sailimu",
        "name_zh": "北疆·赛里木湖环湖核心线",
        "name_en": "North Xinjiang Sayram Lake Full Loop",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "xj_sayram_lake_ringroad",
        "seasonality": [
            "all_year",
            "summer_flower",
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[\"06\",\"07\",\"08\",\"09\"]}",
        "profile_fit": [
            "self_drive",
            "photo",
            "couple",
            "nature"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 3,
        "default_selected": False,
        "notes": "赛里木湖官方就以环湖风光为核心分区，真正成立的玩法不是”到湖边拍一张”，而是完整环湖、自驾停靠、观景台与湖岸步行结合；命中夏季花海和初秋蓝湖时强度最高。",
        "experience_family": "sea",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "xj_yining_city_ili_valley",
        "circle_id": "xinjiang_yili_circle",
        "city_code": "yili",
        "name_zh": "伊宁·城市与伊犁河谷生活线",
        "name_en": "Yining City & Ili Valley Life Line",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "xj_yining_liuxingstreet_kazanqi_river",
        "seasonality": [
            "all_year",
            "summer"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "culture",
            "foodie",
            "self_drive",
            "slow_travel"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 3,
        "default_selected": False,
        "notes": "伊宁不是单纯中转站；六星街、喀赞其、伊犁河夜景与民族风情共同构成伊犁谷地的人文主簇，适合在草原和公路段之间作为完整停留日。",
        "experience_family": "locallife",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "xj_kalajun_grassland_core",
        "circle_id": "xinjiang_yili_circle",
        "city_code": "yili",
        "name_zh": "特克斯·喀拉峻草原核心线",
        "name_en": "Tekes Kalajun Grassland Core Line",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "xj_tekes_kalajun_koksu",
        "seasonality": [
            "summer_flower",
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[\"06\",\"07\",\"08\",\"09\"]}",
        "profile_fit": [
            "self_drive",
            "photo",
            "nature",
            "hiking"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "喀拉峻本身就是 5A 景区和”新疆天山”世界自然遗产组成部分，不是普通草原点位；草原、峡谷、雪山和鲜花台足够支撑一整天甚至过夜型安排。",
        "experience_family": "flower",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "xj_nalati_grassland_valley",
        "circle_id": "xinjiang_yili_circle",
        "city_code": "nalati",
        "name_zh": "那拉提·草原与河谷线",
        "name_en": "Nalati Grassland & Valley Line",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "xj_nalati_sky_grassland_valley",
        "seasonality": [
            "summer_flower",
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[\"06\",\"07\",\"08\",\"09\"]}",
        "profile_fit": [
            "self_drive",
            "family",
            "photo",
            "slow_travel"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "那拉提的标准玩法不是一个观景台，而是”空中草原 + 河谷草原 + 牧场风情”的组合；景区本身就按不同线路组织，天然适合作为整天草原主簇。",
        "experience_family": "flower",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "xj_duku_north_roadtrip",
        "circle_id": "xinjiang_yili_circle",
        "city_code": "nalati",
        "name_zh": "北疆·独库北段公路线",
        "name_en": "Northern Duku Highway Roadtrip Line",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "xj_duku_north_qiaorma_nalati",
        "seasonality": [
            "summer_open",
            "autumn_open"
        ],
        "upgrade_triggers": "{\"travel_months\":[\"06\",\"07\",\"08\",\"09\"]}",
        "profile_fit": [
            "self_drive",
            "roadtrip",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "独库北段本身就是目的地型景观公路，不只是交通段；雪墙、达坂、乔尔玛与高山草甸会直接决定行车节奏、出发时间与车辆限制。",
        "experience_family": "mountain",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "xj_yizhao_highway_conditional",
        "circle_id": "xinjiang_yili_circle",
        "city_code": "yili",
        "name_zh": "伊犁·伊昭公路线（条件性）",
        "name_en": "Ili Yizhao Highway Conditional Line",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "xj_yizhao_s237",
        "seasonality": [
            "summer_open",
            "autumn_open"
        ],
        "upgrade_triggers": "{\"travel_months\":[\"06\",\"07\",\"08\",\"09\",\"10\"]}",
        "profile_fit": [
            "self_drive",
            "roadtrip",
            "photo",
            "experienced_traveler"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "伊昭公路是明显的条件性主簇：通行窗口短、限行规则多、恶劣天气随时管制；一旦开放，它会成为伊犁最强的高颜值穿越公路之一。",
        "experience_family": "mountain",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "xj_qiongkushitai_wilderness",
        "circle_id": "xinjiang_yili_circle",
        "city_code": "yili",
        "name_zh": "特克斯·琼库什台深度自然线",
        "name_en": "Tekes Qiongkushitai Deep Wilderness Line",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "xj_qiongkushitai_wildscape",
        "seasonality": [
            "summer_flower",
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[\"06\",\"07\",\"08\",\"09\"]}",
        "profile_fit": [
            "self_drive",
            "hiking",
            "photo",
            "slow_travel"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "琼库什台不是”顺路看一眼”的村子，而是更偏深度自然、村落、轻徒步和山谷景观的独立主簇，尤其适合愿意牺牲效率换风景的客群。",
        "experience_family": "mountain",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "xj_kanas_hemu_dualcore",
        "circle_id": "xinjiang_yili_circle",
        "city_code": "kanas",
        "name_zh": "阿勒泰北线·喀纳斯湖禾木村双核线",
        "name_en": "Altay North Loop Kanas-Hemu Dual-Core",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "xj_burqin_kanas_hemu",
        "seasonality": [
            "summer_flower",
            "autumn",
            "winter_snow"
        ],
        "upgrade_triggers": "{\"travel_months\":[\"06\",\"07\",\"08\",\"09\",\"10\",\"12\",\"01\",\"02\"]}",
        "profile_fit": [
            "self_drive",
            "photo",
            "slow_travel",
            "family"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "喀纳斯湖与禾木应视为北疆扩展双核主簇，通常至少要按 2 天以上思路规划；秋色和冬雪都会显著提升其级别与停留意愿。",
        "experience_family": "sea",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "xj_guozigou_bridge_window",
        "circle_id": "xinjiang_yili_circle",
        "city_code": "yili",
        "name_zh": "伊犁·果子沟大桥沿线窗口线",
        "name_en": "Ili Guozigou Bridge View Window",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "xj_guozigou_bridge_view",
        "seasonality": [
            "all_year",
            "summer",
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "self_drive",
            "photo",
            "roadtrip"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "strong",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "果子沟大桥更像高价值”窗口线”而非单独整天簇，但它对赛里木湖进出段影响极大，必须单独保留。",
        "experience_family": "mountain",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "xj_lake_sunset_stargazing",
        "circle_id": "xinjiang_yili_circle",
        "city_code": "sailimu",
        "name_zh": "赛湖·湖边日落星空守候线",
        "name_en": "Sayram Lake Sunset & Stargazing Line",
        "level": "A",
        "default_duration": "quarter_day",
        "primary_corridor": "xj_sayram_lake_nightshore",
        "seasonality": [
            "all_year",
            "summer",
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[\"06\",\"07\",\"08\",\"09\"]}",
        "profile_fit": [
            "couple",
            "photo",
            "self_drive",
            "slow_travel"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "对赛里木湖来说，白天环湖和夜间守候是两种完全不同的体验；命中晴天和住湖边时，这条线经常直接升级为行程高光。",
        "experience_family": "sea",
        "rhythm_role": "recovery",
        "energy_level": "low"
    },
    {
        "cluster_id": "xj_grassland_horse_riding_light",
        "circle_id": "xinjiang_yili_circle",
        "city_code": "nalati",
        "name_zh": "草原·骑马轻体验线",
        "name_en": "Grassland Light Horse-Riding Experience",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "xj_grassland_horse_experience",
        "seasonality": [
            "summer_flower",
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[\"06\",\"07\",\"08\",\"09\"]}",
        "profile_fit": [
            "family",
            "photo",
            "slow_travel"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "骑马轻体验不是核心大线，但在那拉提、喀拉峻、禾木这类草原/村落场景里非常适合做半日型加挂。",
        "experience_family": "locallife",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "xj_herdsman_home_visit_meal",
        "circle_id": "xinjiang_yili_circle",
        "city_code": "yili",
        "name_zh": "草原·牧民家访与风味餐线",
        "name_en": "Grassland Herdsman Visit & Camp Meal",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "xj_nomad_visit_experience",
        "seasonality": [
            "summer_flower",
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[\"06\",\"07\",\"08\",\"09\"]}",
        "profile_fit": [
            "culture",
            "family",
            "slow_travel",
            "foodie"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "medium",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "牧民家访、奶茶、手抓肉、毡房风味餐非常适合放在草原主簇之下做体验型加挂，但单独不必抬得过高。",
        "experience_family": "food",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "xj_hemu_morningmist_night",
        "circle_id": "xinjiang_yili_circle",
        "city_code": "hemu",
        "name_zh": "禾木·晨雾炊烟与夜色线",
        "name_en": "Hemu Morning Mist & Night Scene Line",
        "level": "A",
        "default_duration": "quarter_day",
        "primary_corridor": "xj_hemu_viewplatform_village",
        "seasonality": [
            "summer_flower",
            "autumn",
            "winter_snow"
        ],
        "upgrade_triggers": "{\"travel_months\":[\"06\",\"07\",\"08\",\"09\",\"10\",\"12\",\"01\",\"02\"]}",
        "profile_fit": [
            "photo",
            "couple",
            "slow_travel"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "禾木的真正记忆点通常落在早晨观景台、晨雾炊烟和夜晚木屋灯光，因此值得从喀纳斯大簇中拆出独立强次级簇。",
        "experience_family": "locallife",
        "rhythm_role": "recovery",
        "energy_level": "low"
    },
    {
        "cluster_id": "xj_burqin_route_rest_supply",
        "circle_id": "xinjiang_yili_circle",
        "city_code": "burqin",
        "name_zh": "布尔津·北线补给与过夜缓冲线",
        "name_en": "Burqin North Loop Supply & Overnight Buffer",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "xj_burqin_gateway",
        "seasonality": [
            "all_year",
            "summer",
            "autumn",
            "winter"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "self_drive",
            "family",
            "buffer_stop"
        ],
        "trip_role": "buffer",
        "time_window_strength": "weak",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "布尔津本身未必是来北疆的理由，但在喀纳斯 / 禾木前后是极其重要的补给、过夜和体力恢复节点，路线价值很高。",
        "experience_family": "locallife",
        "rhythm_role": "utility",
        "energy_level": "low"
    },
    {
        "cluster_id": "xj_urumqi_arrival_departure_assembly",
        "circle_id": "xinjiang_yili_circle",
        "city_code": "urumqi",
        "name_zh": "乌鲁木齐·进出疆集散缓冲线",
        "name_en": "Urumqi Arrival-Departure Assembly Buffer",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "xj_urumqi_gateway",
        "seasonality": [
            "all_year"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "self_drive",
            "family",
            "buffer_stop"
        ],
        "trip_role": "buffer",
        "time_window_strength": "weak",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "对这类长线自驾圈，乌鲁木齐的核心价值在于提车、补给、休整和进出疆缓冲，而不是强行做城市观光主簇。",
        "experience_family": "locallife",
        "rhythm_role": "utility",
        "energy_level": "low"
    },
    {
        "cluster_id": "xj_ili_summer_flower_belt",
        "circle_id": "xinjiang_yili_circle",
        "city_code": "yili",
        "name_zh": "伊犁·6-8月花期总线",
        "name_en": "Ili Summer Flower Belt",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "xj_ili_flower_belt",
        "seasonality": [
            "summer_flower"
        ],
        "upgrade_triggers": "{\"travel_months\":[\"06\",\"07\",\"08\"]}",
        "profile_fit": [
            "photo",
            "self_drive",
            "couple",
            "nature"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "伊犁的花期不是单点事件，而是 6 月薰衣草、6 月底至 7 月油菜花、7 月向日葵等多点接力；命中月份时应视为整条路线的升级总线。",
        "experience_family": "flower",
        "rhythm_role": "peak",
        "energy_level": "medium"
    },
    {
        "cluster_id": "xj_northern_xinjiang_autumn_color",
        "circle_id": "xinjiang_yili_circle",
        "city_code": "altay",
        "name_zh": "北疆·9月秋色升级线",
        "name_en": "Northern Xinjiang Autumn Color Upgrade",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "xj_autumn_color_upgrade",
        "seasonality": [
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[\"09\",\"10\"]}",
        "profile_fit": [
            "photo",
            "self_drive",
            "slow_travel"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "9 月的喀纳斯、禾木、伊犁河谷和部分草原会整体进入秋色模式，若以摄影或深度自然为导向，秋色应视为整圈升级逻辑而不是附属标签。",
        "experience_family": "mountain",
        "rhythm_role": "peak",
        "energy_level": "medium"
    },
    {
        "cluster_id": "xj_hemu_kanas_winter_snowmode",
        "circle_id": "xinjiang_yili_circle",
        "city_code": "hemu",
        "name_zh": "阿勒泰北线·冬季雪国模式",
        "name_en": "Altay North Loop Winter Snow Mode",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "xj_hemu_kanas_winter",
        "seasonality": [
            "winter_snow"
        ],
        "upgrade_triggers": "{\"travel_months\":[\"12\",\"01\",\"02\"]}",
        "profile_fit": [
            "photo",
            "winter_travel",
            "slow_travel"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "冬季的禾木 / 喀纳斯不是夏秋的简单替代，而是完全不同的雪国线路；若命中冰雪偏好，可直接转为独立冬季玩法。",
        "experience_family": "mountain",
        "rhythm_role": "peak",
        "energy_level": "medium"
    },
    {
        "cluster_id": "xj_tuergen_apricot_blossom_valley",
        "circle_id": "xinjiang_yili_circle",
        "city_code": "yili",
        "name_zh": "伊犁·吐尔根杏花沟花期线",
        "name_en": "Ili Turgen Apricot Blossom Valley Route",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "xj_tuergen_xinyuan_apricot_valley",
        "seasonality": [
            "spring"
        ],
        "upgrade_triggers": "{\"travel_months\":[\"04\"]}",
        "profile_fit": [
            "photo",
            "self_drive",
            "couple",
            "nature"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "吐尔根杏花沟的价值不在”顺路看花”，而在 4 月前后极短花期内专门追花；命中花况时会直接影响伊宁 / 新源驻点与出发顺序。",
        "experience_family": "flower",
        "rhythm_role": "peak",
        "energy_level": "medium"
    },
    {
        "cluster_id": "xj_xiata_glacier_trail",
        "circle_id": "xinjiang_yili_circle",
        "city_code": "yili",
        "name_zh": "昭苏·夏塔古道雪山徒步线",
        "name_en": "Zhaosu Xiata Ancient Trail & Glacier Route",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "xj_zhaosu_xiata_glacier_valley",
        "seasonality": [
            "summer",
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[\"06\",\"07\",\"08\",\"09\"]}",
        "profile_fit": [
            "hiking",
            "photo",
            "self_drive",
            "nature"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "夏塔的成立方式是”昭苏进山 + 雪山峡谷轻徒步 / 观景车”的完整一天，强依赖早入园与天气窗口，常会把住宿拉到昭苏一侧。",
        "experience_family": "mountain",
        "rhythm_role": "peak",
        "energy_level": "high"
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
                     "xinjiang_yili_circle", new_count, skip_count, len(CLUSTERS))


if __name__ == "__main__":
    asyncio.run(seed())
