"""
seed_huadong_circle_clusters.py — huadong_circle 活动簇数据

从 mojor/ 目录转换生成。
幂等：cluster_id 已存在则 SKIP。

执行：
    python scripts/seed_huadong_clusters.py
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
        "cluster_id": "sh_bund_architecture_nightview",
        "circle_id": "huadong_circle",
        "city_code": "shanghai",
        "name_zh": "上海·外滩万国建筑夜景线",
        "name_en": "Shanghai Bund Historic Skyline Night Line",
        "level": "S",
        "default_duration": "half_day",
        "primary_corridor": "sh_huangpu_bund_riverfront",
        "seasonality": [
            "all_year"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "first_timer",
            "couple",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "外滩与黄浦江夜景是上海最典型的城市封面，价值集中在日落后到夜间，可自然挂接黄浦江游船或南京路夜游。",
        "experience_family": "citynight",
        "rhythm_role": "peak",
        "energy_level": "low"
    },
    {
        "cluster_id": "sh_french_concession_plane_tree_walk",
        "circle_id": "huadong_circle",
        "city_code": "shanghai",
        "name_zh": "上海·法租界梧桐区漫步线",
        "name_en": "Shanghai Former French Concession Plane-Tree Walk",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "sh_hengfu_wukang_anfu",
        "seasonality": [
            "all_year",
            "spring",
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "couple",
            "photo",
            "coffee",
            "slow_travel"
        ],
        "trip_role": "anchor",
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 3,
        "default_selected": False,
        "notes": "武康路、安福路、永嘉路这一带适合做上海梧桐区 citywalk，对咖啡、海派建筑、街区生活方式画像尤其强。",
        "experience_family": "locallife",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "sh_yuyuan_oldcity_temple",
        "circle_id": "huadong_circle",
        "city_code": "shanghai",
        "name_zh": "上海·豫园城隍庙老城厢线",
        "name_en": "Shanghai Yuyuan & Old City God Temple Line",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "sh_yuyuan_oldcity",
        "seasonality": [
            "all_year"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "first_timer",
            "culture",
            "family",
            "foodie"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "豫园与城隍庙是最稳定的老城厢主线，既有古典园林，也有传统商业和小吃密度，适合首次来沪用户。",
        "experience_family": "shrine",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "sh_nanjingroad_shopping_strip",
        "circle_id": "huadong_circle",
        "city_code": "shanghai",
        "name_zh": "上海·南京路步行街购物线",
        "name_en": "Shanghai Nanjing Road Shopping Strip",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "sh_nanjingroad_core",
        "seasonality": [
            "all_year"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "shopping",
            "first_timer",
            "family"
        ],
        "trip_role": "buffer",
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "纯购物不是上海最强主轴，但南京路对首访用户仍是高兼容补位线，可和外滩、人民广场连排。",
        "experience_family": "locallife",
        "rhythm_role": "utility",
        "energy_level": "low"
    },
    {
        "cluster_id": "sh_xintiandi_tianzifang_haipai_life",
        "circle_id": "huadong_circle",
        "city_code": "shanghai",
        "name_zh": "上海·新天地田子坊海派生活线",
        "name_en": "Shanghai Xintiandi & Tianzifang Haipai Life Line",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "sh_xintiandi_tianzifang",
        "seasonality": [
            "all_year"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "couple",
            "photo",
            "shopping",
            "coffee"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 3,
        "default_selected": False,
        "notes": "新天地偏精致海派商业，田子坊偏巷弄与创意市集，组合后适合做”新旧上海生活方式”半天线。",
        "experience_family": "locallife",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "sh_lujiazui_skyline_observatory",
        "circle_id": "huadong_circle",
        "city_code": "shanghai",
        "name_zh": "上海·浦东陆家嘴都市天际线线",
        "name_en": "Shanghai Lujiazui Skyline Observatory Line",
        "level": "S",
        "default_duration": "half_day",
        "primary_corridor": "sh_lujiazui_skyscraper_cluster",
        "seasonality": [
            "all_year"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "first_timer",
            "couple",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "上海中心、东方明珠、滨江步道与黄浦江对望外滩，共同构成上海”现代都市感”最强主簇之一。",
        "experience_family": "citynight",
        "rhythm_role": "peak",
        "energy_level": "medium"
    },
    {
        "cluster_id": "sh_disney_resort_full_day",
        "circle_id": "huadong_circle",
        "city_code": "shanghai",
        "name_zh": "上海·迪士尼乐园全天线",
        "name_en": "Shanghai Disney Resort Full-Day Line",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "sh_shendi_disney",
        "seasonality": [
            "all_year",
            "summer",
            "winter"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "family",
            "couple",
            "first_timer"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "迪士尼天然就是整天型主活动，会明显影响住宿、排队策略和次日体力安排。",
        "experience_family": "themepark",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "sh_m50_westbund_contemporary_art",
        "circle_id": "huadong_circle",
        "city_code": "shanghai",
        "name_zh": "上海·M50西岸当代艺术线",
        "name_en": "Shanghai M50 & West Bund Contemporary Art Line",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "sh_suhe_xuhui_artbelt",
        "seasonality": [
            "all_year"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "art",
            "design",
            "photo",
            "couple"
        ],
        "trip_role": "anchor",
        "time_window_strength": "weak",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "M50和西岸都属于当代艺术与工业更新带，分开看各半天、合在一起正好能撑满一个完整艺术日。",
        "experience_family": "art",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "sh_zhujiajiao_water_town_daytrip",
        "circle_id": "huadong_circle",
        "city_code": "shanghai",
        "name_zh": "上海·朱家角古镇近郊线",
        "name_en": "Shanghai Zhujiajiao Water Town Day Trip",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "sh_qingpu_zhujiajiao",
        "seasonality": [
            "all_year",
            "spring",
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "slow_travel",
            "family",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "朱家角是上海周边最稳的古镇日归线之一，和中心城区体验差异足够大，适合单独占一天。",
        "experience_family": "locallife",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "sh_qibao_ancienttown_snack",
        "circle_id": "huadong_circle",
        "city_code": "shanghai",
        "name_zh": "上海·七宝古镇小吃线",
        "name_en": "Shanghai Qibao Ancient Town Snack Line",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "sh_minhang_qibao",
        "seasonality": [
            "all_year"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "foodie",
            "family",
            "buffer_stop"
        ],
        "trip_role": "buffer",
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "七宝更适合做轻量古镇+小吃补位，不一定值得整天，但很适合作为市区行程的半天缓冲。",
        "experience_family": "food",
        "rhythm_role": "utility",
        "energy_level": "low"
    },
    {
        "cluster_id": "sh_hengfu_cafe_citywalk",
        "circle_id": "huadong_circle",
        "city_code": "shanghai",
        "name_zh": "上海·衡复风貌区咖啡漫步线",
        "name_en": "Shanghai Hengfu Heritage Cafe Walk",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "sh_hengfu_cafes",
        "seasonality": [
            "all_year",
            "spring",
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "coffee",
            "couple",
            "photo",
            "slow_travel"
        ],
        "trip_role": "buffer",
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "衡复风貌区的咖啡密度和街区氛围都足够强，适合挂在法租界步行线之后延展成半天。",
        "experience_family": "locallife",
        "rhythm_role": "recovery",
        "energy_level": "low"
    },
    {
        "cluster_id": "sh_shanghai_nightlife_mixology",
        "circle_id": "huadong_circle",
        "city_code": "shanghai",
        "name_zh": "上海·夜生活调酒吧线",
        "name_en": "Shanghai Nightlife & Mixology Line",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "sh_xintiandi_hengshan_barbelt",
        "seasonality": [
            "all_year"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "nightlife",
            "couple",
            "luxury"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "衡山路、新天地和外滩高空酒吧是典型晚间体验，时间窗强，适合做都市线的夜间收口。",
        "experience_family": "citynight",
        "rhythm_role": "contrast",
        "energy_level": "low"
    },
    {
        "cluster_id": "sh_shengjian_xiaolongbao_foodcrawl",
        "circle_id": "huadong_circle",
        "city_code": "shanghai",
        "name_zh": "上海·生煎小笼本帮点心线",
        "name_en": "Shanghai Shengjian & Xiaolongbao Crawl",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "sh_local_snack_core",
        "seasonality": [
            "all_year"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "foodie",
            "first_timer",
            "local_life"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "生煎、小笼和本帮小吃在上海辨识度极高，足以构成明确的主题型吃喝线。",
        "experience_family": "food",
        "rhythm_role": "utility",
        "energy_level": "low"
    },
    {
        "cluster_id": "sh_gucun_cherry_blossom_season",
        "circle_id": "huadong_circle",
        "city_code": "shanghai",
        "name_zh": "上海·樱花季城市郊野线",
        "name_en": "Shanghai Cherry Blossom Season Line",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "sh_baoshan_gucun_sakura",
        "seasonality": [
            "sakura"
        ],
        "upgrade_triggers": "{\"travel_months\":[\"03\",\"04\"]}",
        "profile_fit": [
            "photo",
            "couple",
            "family"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "顾村公园樱花季是上海最明确的春季窗口之一，季节命中时可直接升级为一整天主簇。",
        "experience_family": "flower",
        "rhythm_role": "peak",
        "energy_level": "medium"
    },
    {
        "cluster_id": "hz_west_lake_classic",
        "circle_id": "huadong_circle",
        "city_code": "hangzhou",
        "name_zh": "杭州·西湖环湖经典线",
        "name_en": "Hangzhou West Lake Classic Loop",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "hz_westlake_ring",
        "seasonality": [
            "all_year",
            "spring",
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "first_timer",
            "couple",
            "photo",
            "family"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 3,
        "default_selected": False,
        "notes": "断桥、白堤/苏堤、雷峰塔、花港观鱼这些节点共同组成杭州最典型的全日型主线，没有西湖就谈不上杭州。",
        "experience_family": "sea",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "hz_lingyin_feilai_peak",
        "circle_id": "huadong_circle",
        "city_code": "hangzhou",
        "name_zh": "杭州·灵隐寺飞来峰线",
        "name_en": "Hangzhou Lingyin Temple & Feilai Peak Line",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "hz_lingyin_beigao",
        "seasonality": [
            "all_year",
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "culture",
            "family",
            "slow_travel",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "灵隐与飞来峰是杭州最稳的宗教与山林主簇之一，半天到一天都能成立。",
        "experience_family": "shrine",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "hz_longjing_tea_culture",
        "circle_id": "huadong_circle",
        "city_code": "hangzhou",
        "name_zh": "杭州·龙井茶文化线",
        "name_en": "Hangzhou Longjing Tea Culture Line",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "hz_longjing_meijiawu",
        "seasonality": [
            "all_year",
            "spring"
        ],
        "upgrade_triggers": "{\"travel_months\":[\"03\",\"04\",\"05\"]}",
        "profile_fit": [
            "foodie",
            "culture",
            "slow_travel",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "龙井村、梅家坞和中国茶叶博物馆共同构成茶文化主线；春茶季命中时体验强度显著上升。",
        "experience_family": "flower",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "hz_longjing_spring_tea_picking",
        "circle_id": "huadong_circle",
        "city_code": "hangzhou",
        "name_zh": "杭州·龙井春茶采茶线",
        "name_en": "Hangzhou Longjing Spring Tea Picking Route",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "hz_longjing_meijiawu_spring_tea",
        "seasonality": [
            "spring"
        ],
        "upgrade_triggers": "{\"travel_months\":[\"03\",\"04\"]}",
        "profile_fit": [
            "slow_travel",
            "culture",
            "foodie",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "春茶季的龙井不再只是泛化茶文化，而是围绕龙井村、梅家坞和茶山采摘窗口成立的半日主活动，会真实改变杭州春季排程与午后去向。",
        "experience_family": "flower",
        "rhythm_role": "peak",
        "energy_level": "medium"
    },
    {
        "cluster_id": "hz_songcheng_performance",
        "circle_id": "huadong_circle",
        "city_code": "hangzhou",
        "name_zh": "杭州·宋城千古情演出线",
        "name_en": "Hangzhou Songcheng Performance Line",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "hz_songcheng_themepark",
        "seasonality": [
            "all_year",
            "summer",
            "holiday"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "family",
            "first_timer",
            "performance"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "宋城的成立高度依赖用户是否接受主题演艺/大型秀场；画像命中时可升格为半天主簇。",
        "experience_family": "themepark",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "hz_xixi_wetland_ecology",
        "circle_id": "huadong_circle",
        "city_code": "hangzhou",
        "name_zh": "杭州·西溪湿地生态线",
        "name_en": "Hangzhou Xixi Wetland Ecology Line",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "hz_xixi_wetland",
        "seasonality": [
            "all_year",
            "spring",
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "family",
            "slow_travel",
            "nature",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "weak",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "西溪和西湖完全不是同一种杭州，适合做自然生态与慢节奏的一整天线路。",
        "experience_family": "locallife",
        "rhythm_role": "recovery",
        "energy_level": "medium"
    },
    {
        "cluster_id": "hz_qiantang_tide_viewing",
        "circle_id": "huadong_circle",
        "city_code": "hangzhou",
        "name_zh": "杭州·钱塘江观潮线",
        "name_en": "Hangzhou Qiantang Tidal Bore Viewing Line",
        "level": "S",
        "default_duration": "half_day",
        "primary_corridor": "hz_qiantang_tidebelt",
        "seasonality": [
            "tidal_bore"
        ],
        "upgrade_triggers": "{\"travel_months\":[\"09\",\"10\"]}",
        "profile_fit": [
            "photo",
            "festival",
            "first_timer"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "钱塘观潮是最典型的强时间窗季节型主簇之一，命中窗口时足以成为”来杭州的理由”。",
        "experience_family": "sea",
        "rhythm_role": "peak",
        "energy_level": "medium"
    },
    {
        "cluster_id": "hz_hefang_imperial_street",
        "circle_id": "huadong_circle",
        "city_code": "hangzhou",
        "name_zh": "杭州·南宋御街河坊街线",
        "name_en": "Hangzhou Southern Song Imperial Street & Hefang Street",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "hz_hefang_nansong",
        "seasonality": [
            "all_year"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "first_timer",
            "foodie",
            "culture"
        ],
        "trip_role": "buffer",
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "更适合做城市经典补位与晚间漫步，而非绝对主轴，但对首访用户仍有稳定价值。",
        "experience_family": "food",
        "rhythm_role": "utility",
        "energy_level": "low"
    },
    {
        "cluster_id": "hz_liangzhu_worldheritage",
        "circle_id": "huadong_circle",
        "city_code": "hangzhou",
        "name_zh": "杭州·良渚遗址世界遗产线",
        "name_en": "Hangzhou Liangzhu World Heritage Line",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "hz_liangzhu_heritage_park",
        "seasonality": [
            "all_year"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "history",
            "culture",
            "design",
            "family"
        ],
        "trip_role": "anchor",
        "time_window_strength": "weak",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "良渚是杭州最强的”文明起源叙事”节点之一，和西湖完全不同，值得单独建簇。",
        "experience_family": "shrine",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "hz_qianjiang_newtown_nightview",
        "circle_id": "huadong_circle",
        "city_code": "hangzhou",
        "name_zh": "杭州·钱江新城夜景线",
        "name_en": "Hangzhou Qianjiang New Town Night View",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "hz_qianjiang_newtown",
        "seasonality": [
            "all_year"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "couple",
            "photo",
            "urban"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "strong",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "杭州不只有古典气质，钱江新城夜景与江岸空间很适合做都市线夜间收口。",
        "experience_family": "citynight",
        "rhythm_role": "contrast",
        "energy_level": "low"
    },
    {
        "cluster_id": "hz_hangbang_food_night",
        "circle_id": "huadong_circle",
        "city_code": "hangzhou",
        "name_zh": "杭州·杭帮菜夜食线",
        "name_en": "Hangzhou Local Cuisine Night Line",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "hz_local_food_core",
        "seasonality": [
            "all_year"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "foodie",
            "couple",
            "local_life"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "medium",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "杭州夜间吃喝虽不是全国最强，但杭帮菜与湖鲜主题很适合做晚餐型补位簇。",
        "experience_family": "food",
        "rhythm_role": "utility",
        "energy_level": "low"
    },
    {
        "cluster_id": "sz_classical_gardens_dualcore",
        "circle_id": "huadong_circle",
        "city_code": "suzhou",
        "name_zh": "苏州·拙政园狮子林古典园林线",
        "name_en": "Suzhou Classical Gardens Dual-Core Line",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "sz_gusu_garden_core",
        "seasonality": [
            "all_year",
            "spring",
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "first_timer",
            "culture",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "拙政园和狮子林是”苏州园林”最稳定的入门双核，足够支撑整天主簇。",
        "experience_family": "shrine",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "sz_pingjiang_shantang_waterstreet",
        "circle_id": "huadong_circle",
        "city_code": "suzhou",
        "name_zh": "苏州·平江路山塘街水乡古街线",
        "name_en": "Suzhou Pingjiang & Shantang Water Street Line",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "sz_oldcity_canal_streets",
        "seasonality": [
            "all_year"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "couple",
            "photo",
            "slow_travel",
            "first_timer"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 3,
        "default_selected": False,
        "notes": "平江偏白天和生活感，山塘偏夜间和运河氛围，合起来很适合做”水巷古街”全日线。",
        "experience_family": "locallife",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "sz_tigerhill_hanshansi_culture",
        "circle_id": "huadong_circle",
        "city_code": "suzhou",
        "name_zh": "苏州·虎丘寒山寺文化线",
        "name_en": "Suzhou Tiger Hill & Hanshan Temple Culture Line",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "sz_tigerhill_hanshan",
        "seasonality": [
            "all_year",
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "culture",
            "history",
            "family"
        ],
        "trip_role": "anchor",
        "time_window_strength": "weak",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "虎丘与寒山寺是苏州更偏文化宗教向的经典线，适合和园林、水街错峰组合。",
        "experience_family": "shrine",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "sz_jinji_lake_modern_lakeside",
        "circle_id": "huadong_circle",
        "city_code": "suzhou",
        "name_zh": "苏州·金鸡湖现代都市线",
        "name_en": "Suzhou Jinji Lake Modern Lakeside Line",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "sz_sip_jinji_lake",
        "seasonality": [
            "all_year"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "couple",
            "urban",
            "shopping",
            "photo"
        ],
        "trip_role": "buffer",
        "time_window_strength": "medium",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "金鸡湖是苏州现代都市面的代表，适合与古城形成反差型补位。",
        "experience_family": "citynight",
        "rhythm_role": "utility",
        "energy_level": "low"
    },
    {
        "cluster_id": "sz_zhouzhuang_daytrip",
        "circle_id": "huadong_circle",
        "city_code": "suzhou",
        "name_zh": "苏州·周庄古镇日归线",
        "name_en": "Suzhou Zhouzhuang Water Town Day Trip",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "sz_kunshan_zhouzhuang",
        "seasonality": [
            "all_year",
            "spring",
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "photo",
            "slow_travel",
            "family"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "周庄是苏州系水乡中最有全国辨识度的一档，适合从苏州本城单独拉出一日。",
        "experience_family": "locallife",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "sz_tongli_daytrip",
        "circle_id": "huadong_circle",
        "city_code": "suzhou",
        "name_zh": "苏州·同里古镇日归线",
        "name_en": "Suzhou Tongli Water Town Day Trip",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "sz_wujiang_tongli",
        "seasonality": [
            "all_year",
            "spring",
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "slow_travel",
            "photo",
            "couple"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "同里比周庄更安静、更适合慢节奏和夜游，值得与周庄分开建簇。",
        "experience_family": "locallife",
        "rhythm_role": "recovery",
        "energy_level": "medium"
    },
    {
        "cluster_id": "sz_pingtan_teahouse_night",
        "circle_id": "huadong_circle",
        "city_code": "suzhou",
        "name_zh": "苏州·评弹茶馆夜听线",
        "name_en": "Suzhou Pingtan Teahouse Night Line",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "sz_oldcity_teahouse",
        "seasonality": [
            "all_year"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "culture",
            "couple",
            "slow_travel"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "strong",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "评弹是苏州在夜间最有地方感的文化补位之一，适合做古城线晚间收口。",
        "experience_family": "art",
        "rhythm_role": "contrast",
        "energy_level": "low"
    },
    {
        "cluster_id": "sz_yangcheng_lake_crab_autumn",
        "circle_id": "huadong_circle",
        "city_code": "suzhou",
        "name_zh": "苏州·阳澄湖大闸蟹秋季线",
        "name_en": "Suzhou Yangcheng Lake Hairy Crab Autumn Line",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "sz_yangcheng_lake_foodbelt",
        "seasonality": [
            "autumn_crab"
        ],
        "upgrade_triggers": "{\"travel_months\":[\"09\",\"10\",\"11\"]}",
        "profile_fit": [
            "foodie",
            "family",
            "local_life"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "大闸蟹季是华东秋季非常明确的时令升级项，命中月份时完全能从”餐”升级为”专门跑一趟的半日线”。",
        "experience_family": "food",
        "rhythm_role": "peak",
        "energy_level": "medium"
    },
    {
        "cluster_id": "nj_zhongshan_mingxiaoling",
        "circle_id": "huadong_circle",
        "city_code": "nanjing",
        "name_zh": "南京·中山陵明孝陵钟山线",
        "name_en": "Nanjing Zhongshan Scenic Area Line",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "nj_zhongshan_core",
        "seasonality": [
            "all_year",
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "first_timer",
            "history",
            "photo",
            "family"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "钟山风景区是南京最强的历史自然复合簇，中山陵和明孝陵已足够占满一天。",
        "experience_family": "shrine",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "nj_confucius_qinhuai_night",
        "circle_id": "huadong_circle",
        "city_code": "nanjing",
        "name_zh": "南京·夫子庙秦淮河夜游线",
        "name_en": "Nanjing Confucius Temple & Qinhuai Night Line",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "nj_qinhuai_confucius_core",
        "seasonality": [
            "all_year"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "first_timer",
            "couple",
            "photo",
            "family"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "夫子庙真正强的是傍晚到夜间的灯光与河面氛围，适合单独吃掉一个晚上。",
        "experience_family": "citynight",
        "rhythm_role": "contrast",
        "energy_level": "low"
    },
    {
        "cluster_id": "nj_presidential_republic_arch",
        "circle_id": "huadong_circle",
        "city_code": "nanjing",
        "name_zh": "南京·总统府民国建筑线",
        "name_en": "Nanjing Presidential Palace Republican Architecture Line",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "nj_changjiang_republic_axis",
        "seasonality": [
            "all_year"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "history",
            "architecture",
            "culture"
        ],
        "trip_role": "anchor",
        "time_window_strength": "weak",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "总统府和周边民国建筑线构成南京近现代史最强的城市叙事之一，半天完全成立。",
        "experience_family": "shrine",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "nj_citywall_loop",
        "circle_id": "huadong_circle",
        "city_code": "nanjing",
        "name_zh": "南京·明城墙环城线",
        "name_en": "Nanjing City Wall Loop",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "nj_citywall_nodes",
        "seasonality": [
            "all_year",
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "history",
            "photo",
            "walk"
        ],
        "trip_role": "anchor",
        "time_window_strength": "weak",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "中华门、玄武门等不同段落都可走，但作为”环城线”要重点强调节点式游法，而不是整圈暴走。",
        "experience_family": "shrine",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "nj_yihe_road_republic_villas",
        "circle_id": "huadong_circle",
        "city_code": "nanjing",
        "name_zh": "南京·颐和路民国别墅区线",
        "name_en": "Nanjing Yihe Road Republican Villa Line",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "nj_yihe_road",
        "seasonality": [
            "all_year",
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "architecture",
            "photo",
            "slow_travel",
            "coffee"
        ],
        "trip_role": "buffer",
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "颐和路更偏街区质感和别墅建筑，适合挂在民国线后做慢节奏加深。",
        "experience_family": "locallife",
        "rhythm_role": "recovery",
        "energy_level": "low"
    },
    {
        "cluster_id": "nj_memorial_hall_history_education",
        "circle_id": "huadong_circle",
        "city_code": "nanjing",
        "name_zh": "南京·大屠杀遇难同胞纪念馆历史教育线",
        "name_en": "Nanjing Memorial Hall History Education Line",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "nj_memorial_hall_core",
        "seasonality": [
            "all_year"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "history",
            "education",
            "serious_travel"
        ],
        "trip_role": "anchor",
        "time_window_strength": "weak",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 0,
        "default_selected": False,
        "notes": "这是情绪和教育属性都很强的独立簇，应避免与轻松娱乐型活动强行混排。",
        "experience_family": "art",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "nj_laomendong_nightwalk",
        "circle_id": "huadong_circle",
        "city_code": "nanjing",
        "name_zh": "南京·老门东夜走线",
        "name_en": "Nanjing Laomendong Night Walk",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "nj_laomendong_core",
        "seasonality": [
            "all_year"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "foodie",
            "photo",
            "couple"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "strong",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "老门东更适合放在夜间，与秦淮河线形成”传统街区+晚间吃喝”的双簇结构。",
        "experience_family": "food",
        "rhythm_role": "utility",
        "energy_level": "low"
    },
    {
        "cluster_id": "nj_plum_blossom_mountain",
        "circle_id": "huadong_circle",
        "city_code": "nanjing",
        "name_zh": "南京·梅花山赏梅线",
        "name_en": "Nanjing Plum Blossom Mountain Line",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "nj_meihuashan",
        "seasonality": [
            "plum_blossom"
        ],
        "upgrade_triggers": "{\"travel_months\":[\"02\",\"03\"]}",
        "profile_fit": [
            "photo",
            "couple",
            "family"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "南京的赏梅季辨识度很强，命中窗口时适合从钟山线中独立升级出来。",
        "experience_family": "flower",
        "rhythm_role": "peak",
        "energy_level": "medium"
    },
    {
        "cluster_id": "nj_qixia_redleaves",
        "circle_id": "huadong_circle",
        "city_code": "nanjing",
        "name_zh": "南京·栖霞山红叶线",
        "name_en": "Nanjing Qixia Mountain Red Leaves Line",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "nj_qixia_mountain",
        "seasonality": [
            "autumn_leaves"
        ],
        "upgrade_triggers": "{\"travel_months\":[\"11\"]}",
        "profile_fit": [
            "photo",
            "nature",
            "culture"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "栖霞山是南京秋季最稳的季节升级项之一，红叶窗口命中时有明显”专门去一趟”的能力。",
        "experience_family": "flower",
        "rhythm_role": "peak",
        "energy_level": "medium"
    },
    {
        "cluster_id": "wx_yuantouzhu_taihu_scenery",
        "circle_id": "huadong_circle",
        "city_code": "wuxi",
        "name_zh": "无锡·鼋头渚太湖风光线",
        "name_en": "Wuxi Yuantouzhu & Taihu Scenery Line",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "wx_taihu_yuantouzhu",
        "seasonality": [
            "all_year",
            "sakura"
        ],
        "upgrade_triggers": "{\"travel_months\":[\"03\",\"04\"]}",
        "profile_fit": [
            "photo",
            "couple",
            "family",
            "first_timer"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "鼋头渚本身就是无锡最强主簇之一，春季樱花命中时会进一步升级为全城级主活动。",
        "experience_family": "flower",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "wx_lingshan_nianhuawan_zen",
        "circle_id": "huadong_circle",
        "city_code": "wuxi",
        "name_zh": "无锡·灵山大佛拈花湾禅意线",
        "name_en": "Wuxi Lingshan & Nianhua Bay Zen Line",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "wx_mashan_zenbelt",
        "seasonality": [
            "all_year",
            "autumn",
            "winter"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "family",
            "couple",
            "slow_travel",
            "culture"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "灵山偏白天宗教景区，拈花湾偏傍晚到夜间禅意度假，组合后最容易撑满一个整天。",
        "experience_family": "shrine",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "wx_huishan_oldtown",
        "circle_id": "huadong_circle",
        "city_code": "wuxi",
        "name_zh": "无锡·惠山古镇线",
        "name_en": "Wuxi Huishan Old Town Line",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "wx_huishan_oldtown",
        "seasonality": [
            "all_year",
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "culture",
            "photo",
            "slow_travel"
        ],
        "trip_role": "anchor",
        "time_window_strength": "weak",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "惠山古镇属于典型”半天主簇”，既可以独立，也很适合和南长街拼成一日。",
        "experience_family": "locallife",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "wx_nanchang_canal_night",
        "circle_id": "huadong_circle",
        "city_code": "wuxi",
        "name_zh": "无锡·南长街运河夜游线",
        "name_en": "Wuxi Nanchang Street Canal Night Line",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "wx_nanchang_canal",
        "seasonality": [
            "all_year"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "couple",
            "foodie",
            "photo"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "strong",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "南长街在夜间更成立，适合与惠山古镇、鼋头渚错峰使用，作为无锡城市夜生活补位。",
        "experience_family": "citynight",
        "rhythm_role": "contrast",
        "energy_level": "low"
    },
    {
        "cluster_id": "wz_east_west_complete",
        "circle_id": "huadong_circle",
        "city_code": "wuzhen",
        "name_zh": "乌镇·东西栅完整线",
        "name_en": "Wuzhen East-West Scenic Line",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "wz_dongzha_xizha",
        "seasonality": [
            "all_year",
            "spring",
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "photo",
            "couple",
            "slow_travel",
            "family"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "乌镇真正强的不是单个入口，而是白天东西栅 + 夜间西栅的完整节奏，天然适合升级为住一晚。",
        "experience_family": "locallife",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "wz_xizha_nightwalk",
        "circle_id": "huadong_circle",
        "city_code": "wuzhen",
        "name_zh": "乌镇·西栅夜游线",
        "name_en": "Wuzhen Xizha Night Walk",
        "level": "A",
        "default_duration": "quarter_day",
        "primary_corridor": "wz_xizha_nightcore",
        "seasonality": [
            "all_year"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "couple",
            "photo",
            "slow_travel"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "如果用户不愿完整做东西栅，至少也应把西栅夜游作为独立强次级簇保留。",
        "experience_family": "citynight",
        "rhythm_role": "contrast",
        "energy_level": "low"
    },
    {
        "cluster_id": "xt_ancienttown_halfday",
        "circle_id": "huadong_circle",
        "city_code": "xitang",
        "name_zh": "西塘·古镇半日线",
        "name_en": "Xitang Ancient Town Half-Day Line",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "xt_oldtown_core",
        "seasonality": [
            "all_year",
            "spring",
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "photo",
            "couple",
            "slow_travel"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "西塘体量比乌镇小，更适合半日或一晚轻量古镇走法。",
        "experience_family": "locallife",
        "rhythm_role": "recovery",
        "energy_level": "medium"
    },
    {
        "cluster_id": "xt_night_corridor_walk",
        "circle_id": "huadong_circle",
        "city_code": "xitang",
        "name_zh": "西塘·廊棚夜走线",
        "name_en": "Xitang Covered Corridor Night Walk",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "xt_night_corridors",
        "seasonality": [
            "all_year"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "couple",
            "photo"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "strong",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "西塘的夜感比白天更强，适合作为轻量过夜或晚间补位簇。",
        "experience_family": "citynight",
        "rhythm_role": "contrast",
        "energy_level": "low"
    },
    {
        "cluster_id": "zs_putuoshan_pilgrimage_island",
        "circle_id": "huadong_circle",
        "city_code": "zhoushan",
        "name_zh": "舟山·普陀山朝圣海岛线",
        "name_en": "Zhoushan Putuoshan Pilgrimage Island Line",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "zs_putuoshan_core",
        "seasonality": [
            "all_year",
            "spring",
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "culture",
            "family",
            "slow_travel",
            "serious_travel"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "普陀山兼具宗教朝圣、山海景观和明显船班约束，是标准的过海型主活动簇，常常更适合安排一晚。",
        "experience_family": "shrine",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "zs_zhujiajian_coast_seafood",
        "circle_id": "huadong_circle",
        "city_code": "zhoushan",
        "name_zh": "舟山·朱家尖海岸海鲜线",
        "name_en": "Zhoushan Zhujiajian Coast & Seafood Line",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "zs_zhujiajian_coast",
        "seasonality": [
            "all_year",
            "summer",
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[\"06\",\"07\",\"08\",\"09\"]}",
        "profile_fit": [
            "family",
            "slow_travel",
            "seafood",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "对不走纯朝圣的人群，朱家尖的海岸放松+海鲜会是舟山更容易成交的主簇。",
        "experience_family": "sea",
        "rhythm_role": "recovery",
        "energy_level": "medium"
    },
    {
        "cluster_id": "zs_island_seafood_nightmarket",
        "circle_id": "huadong_circle",
        "city_code": "zhoushan",
        "name_zh": "舟山·海岛夜宵海鲜补位线",
        "name_en": "Zhoushan Island Seafood Night Fill-in",
        "level": "B",
        "default_duration": "quarter_day",
        "primary_corridor": "zs_harbor_seafood_night",
        "seasonality": [
            "all_year",
            "summer",
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "foodie",
            "local_life",
            "couple"
        ],
        "trip_role": "enrichment",
        "time_window_strength": "strong",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "作为海岛线的晚间补位，海鲜夜宵本身有明确存在价值。",
        "experience_family": "food",
        "rhythm_role": "utility",
        "energy_level": "low"
    },
    {
        "cluster_id": "zs_dongji_island_sunrise_stay",
        "circle_id": "huadong_circle",
        "city_code": "zhoushan",
        "name_zh": "舟山·东极岛日出过夜线",
        "name_en": "Zhoushan Dongji Island Sunrise Overnight Route",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "zs_dongji_qingbang_miaozihu",
        "seasonality": [
            "all_year",
            "summer"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "photo",
            "slow_travel",
            "couple",
            "nature"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "东极岛真正成立的方式是赶船进岛、守日出和至少住一晚；船班与天气窗口会直接改写舟山驻点，不应只当普陀山后的顺路海岛补充。",
        "experience_family": "sea",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "hs_mount_huangshan_summit_trek",
        "circle_id": "huadong_circle",
        "city_code": "huangshan",
        "name_zh": "黄山·世界遗产登山线",
        "name_en": "Huangshan World Heritage Summit Trek",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "hs_mountain_core",
        "seasonality": [
            "all_year",
            "autumn",
            "winter"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "nature",
            "photo",
            "hiking",
            "first_timer"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 0,
        "default_selected": False,
        "notes": "黄山是典型应考虑升级为 2 天 1 夜的主簇，日出、云海、索道和山顶住宿都会真实改写行程骨架。",
        "experience_family": "mountain",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "hs_hongcun_xidi_huizhou_village",
        "circle_id": "huadong_circle",
        "city_code": "huangshan",
        "name_zh": "黄山·宏村西递徽州古村线",
        "name_en": "Huangshan Hongcun-Xidi Huizhou Village Line",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "hs_huizhou_village_belt",
        "seasonality": [
            "all_year",
            "spring",
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "photo",
            "culture",
            "slow_travel"
        ],
        "trip_role": "anchor",
        "time_window_strength": "weak",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "黄山不该只剩”爬山”，徽州古村是完全不同的主体验，适合单独抽成一整天。",
        "experience_family": "locallife",
        "rhythm_role": "contrast",
        "energy_level": "medium"
    },
    {
        "cluster_id": "hs_winter_cloudsea_hotspring",
        "circle_id": "huadong_circle",
        "city_code": "huangshan",
        "name_zh": "黄山·冬季云海温泉线",
        "name_en": "Huangshan Winter Cloud Sea & Hot Spring Line",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "hs_winter_resort_zone",
        "seasonality": [
            "winter_cloudsea"
        ],
        "upgrade_triggers": "{\"travel_months\":[\"12\",\"01\",\"02\"]}",
        "profile_fit": [
            "couple",
            "slow_travel",
            "photo"
        ],
        "trip_role": "anchor",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "黄山冬季景观并非弱季，云海、雾凇、温泉命中时会显著改变玩法和住点。",
        "experience_family": "onsen",
        "rhythm_role": "peak",
        "energy_level": "medium"
    },
    {
        "cluster_id": "hs_tunxi_oldstreet_huizhou_snacks",
        "circle_id": "huadong_circle",
        "city_code": "huangshan",
        "name_zh": "黄山·屯溪老街徽味补位线",
        "name_en": "Huangshan Tunxi Old Street Hui Snacks Line",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "hs_tunxi_oldstreet",
        "seasonality": [
            "all_year"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "foodie",
            "culture",
            "buffer_stop"
        ],
        "trip_role": "buffer",
        "time_window_strength": "weak",
        "reservation_pressure": "none",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "屯溪老街更适合做黄山山上山下切换间的缓冲补位，不必抬得过高，但值得保留。",
        "experience_family": "food",
        "rhythm_role": "recovery",
        "energy_level": "low"
    },
    {
        "cluster_id": "mgs_bamboo_resort_hiking",
        "circle_id": "huadong_circle",
        "city_code": "moganshan",
        "name_zh": "莫干山·竹海度假徒步线",
        "name_en": "Moganshan Bamboo Resort & Hiking Line",
        "level": "S",
        "default_duration": "full_day",
        "primary_corridor": "mgs_bamboo_resort_core",
        "seasonality": [
            "all_year",
            "summer",
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "couple",
            "slow_travel",
            "hiking",
            "family"
        ],
        "trip_role": "anchor",
        "time_window_strength": "weak",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "莫干山对江浙沪周边客的核心卖点不是单点，而是”住民宿 + 竹林徒步 + 山中慢生活”的整包体验。",
        "experience_family": "mountain",
        "rhythm_role": "peak",
        "energy_level": "high"
    },
    {
        "cluster_id": "mgs_summer_minsu_escape",
        "circle_id": "huadong_circle",
        "city_code": "moganshan",
        "name_zh": "莫干山·避暑民宿度假线",
        "name_en": "Moganshan Summer Minsu Escape",
        "level": "A",
        "default_duration": "full_day",
        "primary_corridor": "mgs_summer_escape",
        "seasonality": [
            "summer_escape"
        ],
        "upgrade_triggers": "{\"travel_months\":[\"06\",\"07\",\"08\"]}",
        "profile_fit": [
            "couple",
            "family",
            "slow_travel",
            "luxury"
        ],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "high",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "夏季命中后，莫干山会从普通周边山地升级为强目的地，民宿库存和价格都会显著波动。",
        "experience_family": "mountain",
        "rhythm_role": "peak",
        "energy_level": "medium"
    },
    {
        "cluster_id": "mgs_yucun_cafe_slowlife",
        "circle_id": "huadong_circle",
        "city_code": "moganshan",
        "name_zh": "莫干山·庾村咖啡慢生活线",
        "name_en": "Moganshan Yucun Cafe Slow-Life Line",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "mgs_yucun_core",
        "seasonality": [
            "all_year",
            "spring",
            "autumn"
        ],
        "upgrade_triggers": "{\"travel_months\":[]}",
        "profile_fit": [
            "coffee",
            "couple",
            "slow_travel"
        ],
        "trip_role": "buffer",
        "time_window_strength": "weak",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": False,
        "notes": "庾村更适合做莫干山住宿型线路中的轻量缓冲与下午茶节点。",
        "experience_family": "locallife",
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
                     "huadong_circle", new_count, skip_count, len(CLUSTERS))


if __name__ == "__main__":
    asyncio.run(seed())
