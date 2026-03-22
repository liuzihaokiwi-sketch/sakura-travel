"""
seed_all_circles.py — T6: 6 个城市圈完整种子数据

包含：
  - 6 个 city_circles（关西/东京/冲绳/北海道/九州/中部）
  - 每圈 7-10 个 activity_clusters
  - 每圈 2-5 个 hotel_strategy_presets
  - 代表节点的 entity_aliases（日文名/英文名/罗马音）

SEED_META = {
    "schema_version": "v1",
    "seed_version": "2026-03-22",
    "source_doc_refs": ["major/02_关西城市圈系统结构表.md", ...]
}

执行方式：
    cd D:/projects/projects/travel-ai
    python scripts/seed_all_circles.py

幂等：circle_id / cluster_id 已存在则 SKIP，不重复写入。
"""
from __future__ import annotations

import asyncio
import logging
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db.models.city_circles import (
    ActivityCluster,
    CityCircle,
    HotelStrategyPreset,
)
from app.db.models.catalog import EntityAlias

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

SEED_META = {
    "schema_version": "v1",
    "seed_version": "2026-03-22",
    "source_doc_refs": [
        "major/02_关西城市圈系统结构表.md",
        "major/03_东京城市圈系统结构表.md",
        "major/04_冲绳城市圈系统结构表.md",
        "major/05_北海道城市圈系统结构表.md",
        "major/06_九州城市圈系统结构表.md",
        "major/07_中部城市圈系统结构表.md",
    ],
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6 个城市圈定义
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CIRCLES = [
    # ── 关西经典圈（关西 seed_kansai_circle.py 已有，这里做 UPSERT 兼容）──
    {
        "circle_id": "kansai_classic_circle",
        "name_zh": "关西经典圈",
        "name_en": "Kansai Classic Circle",
        "base_city_codes": ["kyoto", "osaka"],
        "extension_city_codes": ["nara", "kobe", "uji", "arima_onsen"],
        "min_days": 4, "max_days": 10,
        "recommended_days_range": "5-8",
        "tier": "hot",
        "fit_profiles": {"party_types": ["couple", "family_child", "solo", "friends"], "themes": ["temple", "food", "history", "nature"]},
        "friendly_airports": ["KIX", "ITM"],
        "season_strength": {"spring": 0.95, "summer": 0.65, "autumn": 0.95, "winter": 0.55},
        "notes": "日本旅游最核心圈。京都历史文化+大阪美食繁华，奈良半日游极强。",
        "is_active": True,
    },
    # ── 东京都市圈 ────────────────────────────────────────────────────────────
    {
        "circle_id": "tokyo_metropolitan_circle",
        "name_zh": "东京都市圈",
        "name_en": "Tokyo Metropolitan Circle",
        "base_city_codes": ["tokyo"],
        "extension_city_codes": ["hakone", "nikko", "kamakura", "yokohama", "kawaguchiko"],
        "min_days": 4, "max_days": 12,
        "recommended_days_range": "5-9",
        "tier": "hot",
        "fit_profiles": {"party_types": ["couple", "solo", "friends", "family_child"], "themes": ["shopping", "anime", "food", "nature", "history"]},
        "friendly_airports": ["NRT", "HND"],
        "season_strength": {"spring": 0.95, "summer": 0.70, "autumn": 0.85, "winter": 0.60},
        "notes": "全球最大都市圈之一。涩谷/新宿/浅草/秋叶原/银座各具特色，富士山/箱根日归极强。",
        "is_active": True,
    },
    # ── 冲绳海岛圈 ────────────────────────────────────────────────────────────
    {
        "circle_id": "okinawa_island_circle",
        "name_zh": "冲绳海岛圈",
        "name_en": "Okinawa Island Circle",
        "base_city_codes": ["naha"],
        "extension_city_codes": ["ishigaki", "miyako", "kerama"],
        "min_days": 3, "max_days": 8,
        "recommended_days_range": "4-6",
        "tier": "hot",
        "fit_profiles": {"party_types": ["couple", "friends", "family_child"], "themes": ["beach", "diving", "nature", "food"]},
        "friendly_airports": ["OKA"],
        "season_strength": {"spring": 0.80, "summer": 0.95, "autumn": 0.70, "winter": 0.40},
        "notes": "日本最南端度假胜地。珊瑚礁潜水/浮潜世界顶级，琉球文化独特，夏季为黄金期。",
        "is_active": True,
    },
    # ── 北海道自然圈 ──────────────────────────────────────────────────────────
    {
        "circle_id": "hokkaido_nature_circle",
        "name_zh": "北海道自然圈",
        "name_en": "Hokkaido Nature Circle",
        "base_city_codes": ["sapporo"],
        "extension_city_codes": ["furano", "biei", "niseko", "hakodate", "sounkyo"],
        "min_days": 4, "max_days": 10,
        "recommended_days_range": "5-8",
        "tier": "hot",
        "fit_profiles": {"party_types": ["couple", "family_child", "senior", "solo"], "themes": ["nature", "food", "skiing", "photography"]},
        "friendly_airports": ["CTS", "HKD"],
        "season_strength": {"spring": 0.75, "summer": 0.95, "autumn": 0.85, "winter": 0.90},
        "notes": "四季各异的自然圈。夏季薰衣草+美食，冬季粉雪滑雪+汤咖喱，差异化极高。",
        "is_active": True,
    },
    # ── 九州温泉食文化圈 ─────────────────────────────────────────────────────
    {
        "circle_id": "kyushu_onsen_circle",
        "name_zh": "九州温泉食文化圈",
        "name_en": "Kyushu Onsen & Culture Circle",
        "base_city_codes": ["fukuoka"],
        "extension_city_codes": ["beppu", "yufuin", "nagasaki", "kumamoto", "kagoshima"],
        "min_days": 4, "max_days": 10,
        "recommended_days_range": "5-8",
        "tier": "warm",
        "fit_profiles": {"party_types": ["couple", "senior", "solo"], "themes": ["onsen", "food", "history", "nature"]},
        "friendly_airports": ["FUK", "KOJ", "NGS"],
        "season_strength": {"spring": 0.85, "summer": 0.65, "autumn": 0.85, "winter": 0.70},
        "notes": "博多美食+别府/由布院温泉双雄。长崎历史独特，阿苏火山壮观，适合深度游者。",
        "is_active": True,
    },
    # ── 中部山岳圈（名古屋/中部） ──────────────────────────────────────────
    {
        "circle_id": "chubu_mountain_circle",
        "name_zh": "中部山岳圈",
        "name_en": "Chubu Mountain Circle",
        "base_city_codes": ["nagoya"],
        "extension_city_codes": ["takayama", "shirakawago", "kanazawa", "matsumoto"],
        "min_days": 3, "max_days": 8,
        "recommended_days_range": "4-6",
        "tier": "warm",
        "fit_profiles": {"party_types": ["couple", "senior", "family_child"], "themes": ["culture", "nature", "history", "food"]},
        "friendly_airports": ["NGO"],
        "season_strength": {"spring": 0.85, "summer": 0.65, "autumn": 0.90, "winter": 0.80},
        "notes": "日本心脏地带。高山古町+白川乡合掌村世界遗产，冬雪景极致，金泽被誉为'小京都'。",
        "is_active": True,
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 活动簇（按圈分组）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CLUSTERS: list[dict] = [
    # ────────────────── 关西（已在 seed_kansai_circle.py，这里补充一些缺失的）──
    {"cluster_id": "kyo_higashiyama_gion_classic", "circle_id": "kansai_classic_circle", "name_zh": "京都·东山祇园经典线", "name_en": "Kyoto Higashiyama & Gion Classic", "level": "S", "default_duration": "full_day", "primary_corridor": "higashiyama", "seasonality": ["all_year", "sakura", "autumn_leaves"], "profile_fit": ["first_timer", "couple", "photo", "culture"], "trip_role": "anchor", "time_window_strength": "medium", "reservation_pressure": "low", "secondary_attach_capacity": 2, "default_selected": True, "notes": "清水寺→二年坂→八坂神社→祇园白川。全年最受欢迎的京都线路。"},
    {"cluster_id": "kyo_arashiyama_sagano", "circle_id": "kansai_classic_circle", "name_zh": "京都·岚山嵯峨野线", "name_en": "Kyoto Arashiyama & Sagano", "level": "S", "default_duration": "full_day", "primary_corridor": "arashiyama", "seasonality": ["all_year", "sakura", "autumn_leaves"], "profile_fit": ["couple", "nature", "photo"], "trip_role": "anchor", "time_window_strength": "medium", "reservation_pressure": "medium", "secondary_attach_capacity": 2, "default_selected": True, "notes": "竹林→天龙寺→渡月桥。"},
    {"cluster_id": "kyo_fushimi_inari", "circle_id": "kansai_classic_circle", "name_zh": "京都·伏见稻荷", "name_en": "Kyoto Fushimi Inari", "level": "S", "default_duration": "half_day", "primary_corridor": "fushimi", "seasonality": ["all_year"], "profile_fit": ["first_timer", "photo", "couple"], "trip_role": "anchor", "time_window_strength": "strong", "reservation_pressure": "none", "secondary_attach_capacity": 1, "default_selected": True, "notes": "千本鸟居，建议 7-9 点前往。"},
    {"cluster_id": "osa_dotonbori_minami_food", "circle_id": "kansai_classic_circle", "name_zh": "大阪·道顿堀南区美食夜游", "name_en": "Osaka Dotonbori & Minami Food", "level": "S", "default_duration": "half_day", "primary_corridor": "namba", "seasonality": ["all_year"], "profile_fit": ["food", "couple", "friends"], "trip_role": "anchor", "time_window_strength": "weak", "reservation_pressure": "medium", "secondary_attach_capacity": 2, "default_selected": True, "notes": "章鱼烧→大阪烧→串炸，建议晚 18 点后进入。"},
    {"cluster_id": "osa_usj_themepark", "circle_id": "kansai_classic_circle", "name_zh": "大阪·USJ 环球影城", "name_en": "Osaka Universal Studios Japan", "level": "S", "default_duration": "full_day", "primary_corridor": "sakurajima", "seasonality": ["all_year"], "profile_fit": ["family_child", "friends", "theme_park"], "trip_role": "anchor", "time_window_strength": "strong", "reservation_pressure": "high", "secondary_attach_capacity": 0, "default_selected": False, "notes": "哈利波特+任天堂世界，必须提前购 express pass。"},

    # ────────────────── 东京 ────────────────────────────────────────────────
    {"cluster_id": "tok_shinjuku_shibuya_night", "circle_id": "tokyo_metropolitan_circle", "name_zh": "东京·新宿涩谷夜游线", "name_en": "Tokyo Shinjuku & Shibuya Night", "level": "S", "default_duration": "half_day", "primary_corridor": "shinjuku", "seasonality": ["all_year"], "profile_fit": ["first_timer", "friends", "nightlife"], "trip_role": "anchor", "time_window_strength": "weak", "reservation_pressure": "low", "secondary_attach_capacity": 2, "default_selected": True, "notes": "新宿歌舞伎町→涩谷十字路口。东京夜景入门首选。"},
    {"cluster_id": "tok_asakusa_senso_ji", "circle_id": "tokyo_metropolitan_circle", "name_zh": "东京·浅草寺仲见世线", "name_en": "Tokyo Asakusa Senso-ji", "level": "S", "default_duration": "half_day", "primary_corridor": "asakusa", "seasonality": ["all_year", "sakura"], "profile_fit": ["first_timer", "culture", "photo", "family_child"], "trip_role": "anchor", "time_window_strength": "medium", "reservation_pressure": "none", "secondary_attach_capacity": 2, "default_selected": True, "notes": "雷门→仲见世通→浅草寺本堂。建议上午 9 点前入场。"},
    {"cluster_id": "tok_akihabara_pop_culture", "circle_id": "tokyo_metropolitan_circle", "name_zh": "东京·秋叶原动漫文化圈", "name_en": "Tokyo Akihabara Anime & Pop Culture", "level": "A", "default_duration": "half_day", "primary_corridor": "akihabara", "seasonality": ["all_year"], "profile_fit": ["anime_fan", "solo", "friends", "shopping"], "trip_role": "enrichment", "time_window_strength": "weak", "reservation_pressure": "none", "secondary_attach_capacity": 2, "default_selected": False, "notes": "动漫/游戏/电子产品购物，女仆咖啡厅体验。"},
    {"cluster_id": "tok_hakone_fuji_day", "circle_id": "tokyo_metropolitan_circle", "name_zh": "箱根·富士山日归线", "name_en": "Hakone & Mt. Fuji Day Trip", "level": "S", "default_duration": "full_day", "primary_corridor": "hakone", "seasonality": ["all_year"], "profile_fit": ["couple", "nature", "photo", "first_timer"], "trip_role": "anchor", "time_window_strength": "medium", "reservation_pressure": "low", "secondary_attach_capacity": 1, "default_selected": False, "notes": "箱根温泉+大涌谷+富士山眺望。从新宿出发 90 分钟，推荐晴天前往。"},
    {"cluster_id": "tok_shibuya_harajuku_fashion", "circle_id": "tokyo_metropolitan_circle", "name_zh": "东京·涩谷原宿时尚线", "name_en": "Tokyo Shibuya & Harajuku Fashion", "level": "A", "default_duration": "half_day", "primary_corridor": "harajuku", "seasonality": ["all_year", "sakura"], "profile_fit": ["shopping", "couple", "young", "photo"], "trip_role": "anchor", "time_window_strength": "weak", "reservation_pressure": "low", "secondary_attach_capacity": 2, "default_selected": True, "notes": "竹下通→表参道→涩谷 Sky。时尚购物+咖啡文化。"},
    {"cluster_id": "tok_tsukiji_toyosu_food", "circle_id": "tokyo_metropolitan_circle", "name_zh": "东京·筑地/丰洲美食线", "name_en": "Tokyo Tsukiji & Toyosu Food", "level": "A", "default_duration": "quarter_day", "primary_corridor": "tsukiji", "seasonality": ["all_year"], "profile_fit": ["food", "sushi", "couple", "solo"], "trip_role": "enrichment", "time_window_strength": "strong", "reservation_pressure": "medium", "secondary_attach_capacity": 1, "default_selected": False, "notes": "筑地场外市场→丰洲市场（需提前预约参观）。建议早 7-9 点抵达。"},
    {"cluster_id": "tok_ueno_museum_park", "circle_id": "tokyo_metropolitan_circle", "name_zh": "东京·上野公园博物馆群", "name_en": "Tokyo Ueno Park & Museums", "level": "B", "default_duration": "half_day", "primary_corridor": "ueno", "seasonality": ["all_year", "sakura"], "profile_fit": ["culture", "family_child", "first_timer"], "trip_role": "buffer", "time_window_strength": "weak", "reservation_pressure": "none", "secondary_attach_capacity": 2, "default_selected": False, "notes": "东京国立博物馆/上野动物园/樱花大道。适合雨天或文化控。"},

    # ────────────────── 冲绳 ────────────────────────────────────────────────
    {"cluster_id": "oki_naha_kokusaidori", "circle_id": "okinawa_island_circle", "name_zh": "那霸·国际通购物文化线", "name_en": "Naha Kokusai-dori Street", "level": "A", "default_duration": "half_day", "primary_corridor": "naha_city", "seasonality": ["all_year"], "profile_fit": ["first_timer", "food", "shopping"], "trip_role": "anchor", "time_window_strength": "weak", "reservation_pressure": "none", "secondary_attach_capacity": 2, "default_selected": True, "notes": "那霸主购物街+首里城。到达/离开日首选。"},
    {"cluster_id": "oki_churaumi_aquarium", "circle_id": "okinawa_island_circle", "name_zh": "冲绳·美丽海水族馆", "name_en": "Okinawa Churaumi Aquarium", "level": "S", "default_duration": "full_day", "primary_corridor": "motobu", "seasonality": ["all_year"], "profile_fit": ["family_child", "couple", "nature"], "trip_role": "anchor", "time_window_strength": "medium", "reservation_pressure": "low", "secondary_attach_capacity": 2, "default_selected": True, "notes": "世界级水族馆+翡翠海滩。亲子游必到。"},
    {"cluster_id": "oki_kerama_snorkel", "circle_id": "okinawa_island_circle", "name_zh": "庆良间群岛·浮潜潜水", "name_en": "Kerama Islands Snorkeling & Diving", "level": "S", "default_duration": "full_day", "primary_corridor": "kerama", "seasonality": ["all_year"], "profile_fit": ["couple", "adventure", "diving", "nature"], "trip_role": "anchor", "time_window_strength": "medium", "reservation_pressure": "medium", "secondary_attach_capacity": 0, "default_selected": False, "notes": "世界顶级珊瑚礁，能见度极高。需提前预约潜水团。"},
    {"cluster_id": "oki_cape_manza_sunset", "circle_id": "okinawa_island_circle", "name_zh": "冲绳中部·万座毛夕阳线", "name_en": "Manza Cape Sunset Drive", "level": "B", "default_duration": "quarter_day", "primary_corridor": "manza", "seasonality": ["all_year"], "profile_fit": ["couple", "photo", "nature"], "trip_role": "buffer", "time_window_strength": "strong", "reservation_pressure": "none", "secondary_attach_capacity": 1, "default_selected": False, "notes": "珊瑚礁悬崖海景，日落约 18:30，绝佳拍照点。"},

    # ────────────────── 北海道 ────────────────────────────────────────────────
    {"cluster_id": "hok_sapporo_odori_susukino", "circle_id": "hokkaido_nature_circle", "name_zh": "札幌·大通公园薄野线", "name_en": "Sapporo Odori Park & Susukino", "level": "A", "default_duration": "half_day", "primary_corridor": "sapporo_city", "seasonality": ["all_year"], "profile_fit": ["first_timer", "food", "friends"], "trip_role": "anchor", "time_window_strength": "weak", "reservation_pressure": "low", "secondary_attach_capacity": 2, "default_selected": True, "notes": "大通公园→时计台→薄野拉面街。到达/离开日首选。"},
    {"cluster_id": "hok_furano_lavender", "circle_id": "hokkaido_nature_circle", "name_zh": "富良野·薰衣草花田", "name_en": "Furano Lavender Fields", "level": "S", "default_duration": "full_day", "primary_corridor": "furano", "seasonality": ["summer"], "profile_fit": ["couple", "photo", "nature", "family_child"], "trip_role": "anchor", "time_window_strength": "medium", "reservation_pressure": "low", "secondary_attach_capacity": 2, "default_selected": False, "upgrade_triggers": {"tags": ["lavender", "flower"], "travel_months": [6, 7, 8]}, "notes": "7月上旬为盛花期。Farm Tomita 免费入场，周边芝士工房值得一逛。"},
    {"cluster_id": "hok_biei_patchwork_road", "circle_id": "hokkaido_nature_circle", "name_zh": "美瑛·拼布之路丘陵", "name_en": "Biei Patchwork Road", "level": "A", "default_duration": "half_day", "primary_corridor": "biei", "seasonality": ["summer", "autumn"], "profile_fit": ["couple", "photo", "nature"], "trip_role": "enrichment", "time_window_strength": "weak", "reservation_pressure": "none", "secondary_attach_capacity": 1, "default_selected": False, "notes": "日本最美丘陵景观，租车或骑车自游，夏季绿黄红相间。"},
    {"cluster_id": "hok_niseko_skiing", "circle_id": "hokkaido_nature_circle", "name_zh": "二世谷·滑雪度假区", "name_en": "Niseko Skiing Resort", "level": "S", "default_duration": "full_day", "primary_corridor": "niseko", "seasonality": ["winter"], "profile_fit": ["ski", "couple", "friends", "adventure"], "trip_role": "anchor", "time_window_strength": "medium", "reservation_pressure": "high", "secondary_attach_capacity": 0, "default_selected": False, "upgrade_triggers": {"tags": ["ski", "snowboard"], "travel_months": [12, 1, 2, 3]}, "notes": "世界顶级粉雪，1月最佳。需提前订雪场住宿。"},
    {"cluster_id": "hok_hakodate_morning_market", "circle_id": "hokkaido_nature_circle", "name_zh": "函馆·朝市夜景线", "name_en": "Hakodate Morning Market & Night View", "level": "A", "default_duration": "full_day", "primary_corridor": "hakodate", "seasonality": ["all_year"], "profile_fit": ["couple", "food", "photo"], "trip_role": "anchor", "time_window_strength": "strong", "reservation_pressure": "low", "secondary_attach_capacity": 2, "default_selected": False, "notes": "凌晨 5 点海鲜朝市+函馆山夜景（世界三大夜景）。"},

    # ────────────────── 九州 ────────────────────────────────────────────────
    {"cluster_id": "kyu_fukuoka_hakata_food", "circle_id": "kyushu_onsen_circle", "name_zh": "福冈·博多美食天堂", "name_en": "Fukuoka Hakata Food Paradise", "level": "S", "default_duration": "half_day", "primary_corridor": "hakata", "seasonality": ["all_year"], "profile_fit": ["food", "first_timer", "couple", "friends"], "trip_role": "anchor", "time_window_strength": "weak", "reservation_pressure": "medium", "secondary_attach_capacity": 2, "default_selected": True, "notes": "博多拉面→水炊き→屋台文化。博多车站周边最集中。"},
    {"cluster_id": "kyu_beppu_onsen", "circle_id": "kyushu_onsen_circle", "name_zh": "别府·地狱温泉巡礼", "name_en": "Beppu Hell Onsen Tour", "level": "S", "default_duration": "full_day", "primary_corridor": "beppu", "seasonality": ["all_year"], "profile_fit": ["couple", "senior", "onsen", "photo"], "trip_role": "anchor", "time_window_strength": "medium", "reservation_pressure": "low", "secondary_attach_capacity": 2, "default_selected": False, "notes": "8 处地狱温泉观光+浸泡温泉。别府站 15 分钟车程。"},
    {"cluster_id": "kyu_yufuin_village", "circle_id": "kyushu_onsen_circle", "name_zh": "由布院·小镇温泉散步", "name_en": "Yufuin Onsen Village Walk", "level": "S", "default_duration": "full_day", "primary_corridor": "yufuin", "seasonality": ["all_year", "autumn"], "profile_fit": ["couple", "onsen", "photo", "relaxation"], "trip_role": "anchor", "time_window_strength": "medium", "reservation_pressure": "medium", "secondary_attach_capacity": 2, "default_selected": False, "notes": "湖畔温泉旅馆+金鳞湖晨雾+精品手工街。情侣必去。"},
    {"cluster_id": "kyu_nagasaki_history", "circle_id": "kyushu_onsen_circle", "name_zh": "长崎·和华兰历史文化线", "name_en": "Nagasaki History & Culture", "level": "A", "default_duration": "full_day", "primary_corridor": "nagasaki_city", "seasonality": ["all_year"], "profile_fit": ["history", "culture", "couple", "solo"], "trip_role": "anchor", "time_window_strength": "medium", "reservation_pressure": "none", "secondary_attach_capacity": 2, "default_selected": False, "notes": "出岛→大浦天主堂→稻佐山夜景。日本唯一和华兰三文化交融之地。"},
    {"cluster_id": "kyu_aso_volcano", "circle_id": "kyushu_onsen_circle", "name_zh": "阿苏·活火山壮观线", "name_en": "Aso Volcano Landscape", "level": "A", "default_duration": "full_day", "primary_corridor": "aso", "seasonality": ["spring", "autumn"], "profile_fit": ["nature", "adventure", "couple", "photo"], "trip_role": "anchor", "time_window_strength": "medium", "reservation_pressure": "none", "secondary_attach_capacity": 1, "default_selected": False, "notes": "世界最大级火山口+草原骑马。需确认火山活动状态再行程。"},

    # ────────────────── 中部 ────────────────────────────────────────────────
    {"cluster_id": "chu_takayama_old_town", "circle_id": "chubu_mountain_circle", "name_zh": "高山·古町老街文化线", "name_en": "Takayama Old Town Furukawa", "level": "S", "default_duration": "full_day", "primary_corridor": "takayama", "seasonality": ["all_year", "autumn", "winter"], "profile_fit": ["couple", "culture", "history", "photo"], "trip_role": "anchor", "time_window_strength": "medium", "reservation_pressure": "low", "secondary_attach_capacity": 2, "default_selected": True, "notes": "三町筋古街+朝市+飞弹民俗村。冬雪景极致，酒造一条街值得细逛。"},
    {"cluster_id": "chu_shirakawago_heritage", "circle_id": "chubu_mountain_circle", "name_zh": "白川乡·合掌村世界遗产", "name_en": "Shirakawa-go World Heritage", "level": "S", "default_duration": "half_day", "primary_corridor": "shirakawago", "seasonality": ["all_year", "winter"], "profile_fit": ["couple", "culture", "photo", "history"], "trip_role": "anchor", "time_window_strength": "medium", "reservation_pressure": "medium", "secondary_attach_capacity": 1, "default_selected": True, "notes": "UNESCO 世界遗产，冬季雪景为绝景。高山出发约 60 分钟。"},
    {"cluster_id": "chu_kanazawa_kenroku", "circle_id": "chubu_mountain_circle", "name_zh": "金泽·兼六园东茶屋街", "name_en": "Kanazawa Kenroku-en & Higashi Chaya", "level": "S", "default_duration": "full_day", "primary_corridor": "kanazawa", "seasonality": ["all_year", "spring", "autumn"], "profile_fit": ["culture", "food", "couple", "history"], "trip_role": "anchor", "time_window_strength": "medium", "reservation_pressure": "low", "secondary_attach_capacity": 2, "default_selected": False, "notes": "日本三大名园兼六园+东茶屋街金箔料理。近江市场新鲜海产午餐。"},
    {"cluster_id": "chu_matsumoto_castle", "circle_id": "chubu_mountain_circle", "name_zh": "松本·国宝天守阁线", "name_en": "Matsumoto Castle & Alps View", "level": "A", "default_duration": "half_day", "primary_corridor": "matsumoto", "seasonality": ["all_year"], "profile_fit": ["history", "culture", "photo", "nature"], "trip_role": "enrichment", "time_window_strength": "medium", "reservation_pressure": "none", "secondary_attach_capacity": 2, "default_selected": False, "notes": "日本现存12天守之一（国宝），日本阿尔卑斯眺望绝佳点。"},
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 酒店住法预设（每圈精选 2-3 个）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HOTEL_PRESETS: list[dict] = [
    # 关西
    {"circle_id": "kansai_classic_circle", "name_zh": "全程住京都（河原町/祇园）", "min_days": 4, "max_days": 7, "bases": [{"base_city": "kyoto", "area": "kawaramachi", "nights_range": "4-7", "served_cluster_ids": ["kyo_higashiyama_gion_classic", "kyo_arashiyama_sagano", "kyo_fushimi_inari", "osa_dotonbori_minami_food"]}], "fit_party_types": ["couple", "solo"], "fit_budget_levels": ["mid", "premium"], "switch_count": 0, "switch_cost_minutes": 0, "last_night_airport_minutes": 75, "priority": 10, "notes": "零换酒店，京都出行最便利。", "is_active": True},
    {"circle_id": "kansai_classic_circle", "name_zh": "京都前段+大阪后段（经典双基点）", "min_days": 5, "max_days": 9, "bases": [{"base_city": "kyoto", "area": "kawaramachi", "nights_range": "3-4"}, {"base_city": "osaka", "area": "namba", "nights_range": "2-3"}], "fit_party_types": ["couple", "family_child", "friends"], "fit_budget_levels": ["budget", "mid"], "switch_count": 1, "switch_cost_minutes": 45, "last_night_airport_minutes": 30, "priority": 20, "notes": "适合 5-9 天，换一次酒店性价比最高。", "is_active": True},
    # 东京
    {"circle_id": "tokyo_metropolitan_circle", "name_zh": "全程住新宿/涩谷", "min_days": 4, "max_days": 9, "bases": [{"base_city": "tokyo", "area": "shinjuku", "nights_range": "4-9", "served_cluster_ids": ["tok_shinjuku_shibuya_night", "tok_asakusa_senso_ji", "tok_akihabara_pop_culture", "tok_hakone_fuji_day"]}], "fit_party_types": ["couple", "solo", "friends"], "fit_budget_levels": ["mid", "premium"], "switch_count": 0, "switch_cost_minutes": 0, "last_night_airport_minutes": 90, "priority": 10, "notes": "零换酒店，新宿交通枢纽，去全东京都方便。", "is_active": True},
    {"circle_id": "tokyo_metropolitan_circle", "name_zh": "东京前段+箱根后段（松弛组合）", "min_days": 6, "max_days": 10, "bases": [{"base_city": "tokyo", "area": "shinjuku", "nights_range": "4-6"}, {"base_city": "hakone", "area": "hakone_en", "nights_range": "2-3"}], "fit_party_types": ["couple", "senior"], "fit_budget_levels": ["mid", "premium", "luxury"], "switch_count": 1, "switch_cost_minutes": 90, "last_night_airport_minutes": 120, "priority": 20, "notes": "东京逛完去箱根温泉放松。适合 6 天以上。", "is_active": True},
    # 冲绳
    {"circle_id": "okinawa_island_circle", "name_zh": "全程住那霸（南部基点）", "min_days": 3, "max_days": 6, "bases": [{"base_city": "naha", "area": "naha_city", "nights_range": "3-6", "served_cluster_ids": ["oki_naha_kokusaidori", "oki_churaumi_aquarium", "oki_cape_manza_sunset"]}], "fit_party_types": ["couple", "friends", "family_child"], "fit_budget_levels": ["budget", "mid"], "switch_count": 0, "switch_cost_minutes": 0, "last_night_airport_minutes": 20, "priority": 10, "notes": "那霸离机场最近，租车出行全岛通达。", "is_active": True},
    # 北海道
    {"circle_id": "hokkaido_nature_circle", "name_zh": "全程住札幌", "min_days": 4, "max_days": 7, "bases": [{"base_city": "sapporo", "area": "sapporo_city", "nights_range": "4-7", "served_cluster_ids": ["hok_sapporo_odori_susukino", "hok_furano_lavender", "hok_biei_patchwork_road"]}], "fit_party_types": ["couple", "family_child", "solo"], "fit_budget_levels": ["budget", "mid"], "switch_count": 0, "switch_cost_minutes": 0, "last_night_airport_minutes": 40, "priority": 10, "notes": "札幌交通枢纽，富良野/美瑛当天往返。", "is_active": True},
    {"circle_id": "hokkaido_nature_circle", "name_zh": "札幌+函馆双基点", "min_days": 6, "max_days": 10, "bases": [{"base_city": "sapporo", "area": "sapporo_city", "nights_range": "4-5"}, {"base_city": "hakodate", "area": "hakodate_city", "nights_range": "2-3"}], "fit_party_types": ["couple", "senior"], "fit_budget_levels": ["mid", "premium"], "switch_count": 1, "switch_cost_minutes": 120, "last_night_airport_minutes": 20, "priority": 20, "notes": "函馆朝市+夜景值得单独一站，搭新干线 70 分钟。", "is_active": True},
    # 九州
    {"circle_id": "kyushu_onsen_circle", "name_zh": "全程住福冈（博多基点）", "min_days": 4, "max_days": 7, "bases": [{"base_city": "fukuoka", "area": "hakata", "nights_range": "4-7", "served_cluster_ids": ["kyu_fukuoka_hakata_food", "kyu_beppu_onsen", "kyu_yufuin_village"]}], "fit_party_types": ["couple", "friends", "food_lover"], "fit_budget_levels": ["budget", "mid"], "switch_count": 0, "switch_cost_minutes": 0, "last_night_airport_minutes": 15, "priority": 10, "notes": "博多离机场极近（地铁 5 分钟），去别府/由布院轻松日归。", "is_active": True},
    # 中部
    {"circle_id": "chubu_mountain_circle", "name_zh": "全程住高山（古町基点）", "min_days": 3, "max_days": 6, "bases": [{"base_city": "takayama", "area": "sanmachi", "nights_range": "3-6", "served_cluster_ids": ["chu_takayama_old_town", "chu_shirakawago_heritage", "chu_matsumoto_castle"]}], "fit_party_types": ["couple", "senior", "culture_lover"], "fit_budget_levels": ["mid", "premium"], "switch_count": 0, "switch_cost_minutes": 0, "last_night_airport_minutes": 150, "priority": 10, "notes": "深度中部山岳游。白川乡当天往返，金泽可单独一站。", "is_active": True},
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 代表节点别名（T1 entity_aliases，用于 T7 实体映射管线）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 注：这里不指定 entity_id（UUID），因为 entity_base 可能尚未有对应记录。
# 使用 representative_name 作为"未匹配别名"占位，T7 管线会自动匹配。

CLUSTER_ALIASES: list[dict] = [
    # 关西
    {"cluster_id": "kyo_higashiyama_gion_classic", "aliases": [
        {"alias_text": "清水寺", "alias_lang": "zh", "alias_type": "official", "normalized_text": "清水寺"},
        {"alias_text": "kiyomizudera", "alias_lang": "romaji", "alias_type": "romaji", "normalized_text": "kiyomizudera"},
        {"alias_text": "清水寺・東山", "alias_lang": "ja", "alias_type": "official", "normalized_text": "清水寺 東山"},
        {"alias_text": "higashiyama", "alias_lang": "en", "alias_type": "common", "normalized_text": "higashiyama"},
    ]},
    {"cluster_id": "kyo_arashiyama_sagano", "aliases": [
        {"alias_text": "嵐山", "alias_lang": "ja", "alias_type": "official", "normalized_text": "嵐山"},
        {"alias_text": "arashiyama", "alias_lang": "romaji", "alias_type": "romaji", "normalized_text": "arashiyama"},
        {"alias_text": "岚山竹林", "alias_lang": "zh", "alias_type": "common", "normalized_text": "岚山竹林"},
    ]},
    {"cluster_id": "kyo_fushimi_inari", "aliases": [
        {"alias_text": "伏見稲荷大社", "alias_lang": "ja", "alias_type": "official", "normalized_text": "伏見稲荷大社"},
        {"alias_text": "千本鸟居", "alias_lang": "zh", "alias_type": "common", "normalized_text": "千本鸟居"},
        {"alias_text": "fushimi inari", "alias_lang": "en", "alias_type": "official", "normalized_text": "fushimi inari"},
    ]},
    {"cluster_id": "osa_usj_themepark", "aliases": [
        {"alias_text": "USJ", "alias_lang": "en", "alias_type": "short", "normalized_text": "usj"},
        {"alias_text": "环球影城", "alias_lang": "zh", "alias_type": "common", "normalized_text": "环球影城"},
        {"alias_text": "Universal Studios Japan", "alias_lang": "en", "alias_type": "official", "normalized_text": "universal studios japan"},
    ]},
    # 东京
    {"cluster_id": "tok_asakusa_senso_ji", "aliases": [
        {"alias_text": "浅草寺", "alias_lang": "zh", "alias_type": "official", "normalized_text": "浅草寺"},
        {"alias_text": "senso-ji", "alias_lang": "romaji", "alias_type": "official", "normalized_text": "sensoji"},
        {"alias_text": "雷门", "alias_lang": "zh", "alias_type": "common", "normalized_text": "雷门"},
    ]},
    {"cluster_id": "tok_hakone_fuji_day", "aliases": [
        {"alias_text": "富士山", "alias_lang": "zh", "alias_type": "official", "normalized_text": "富士山"},
        {"alias_text": "fujisan", "alias_lang": "romaji", "alias_type": "official", "normalized_text": "fujisan"},
        {"alias_text": "箱根", "alias_lang": "zh", "alias_type": "common", "normalized_text": "箱根"},
    ]},
    # 北海道
    {"cluster_id": "hok_furano_lavender", "aliases": [
        {"alias_text": "富良野", "alias_lang": "zh", "alias_type": "official", "normalized_text": "富良野"},
        {"alias_text": "薰衣草", "alias_lang": "zh", "alias_type": "common", "normalized_text": "薰衣草"},
        {"alias_text": "Farm Tomita", "alias_lang": "en", "alias_type": "common", "normalized_text": "farm tomita"},
    ]},
    # 中部
    {"cluster_id": "chu_shirakawago_heritage", "aliases": [
        {"alias_text": "白川郷", "alias_lang": "ja", "alias_type": "official", "normalized_text": "白川郷"},
        {"alias_text": "合掌村", "alias_lang": "zh", "alias_type": "common", "normalized_text": "合掌村"},
        {"alias_text": "shirakawa-go", "alias_lang": "en", "alias_type": "official", "normalized_text": "shirakawago"},
    ]},
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Seed 执行
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def seed():
    async with AsyncSessionLocal() as session:
        # 1. city_circles
        logger.info("=== Seeding city_circles (%d) ===", len(CIRCLES))
        for data in CIRCLES:
            existing = await session.get(CityCircle, data["circle_id"])
            if existing:
                logger.info("  SKIP: %s", data["circle_id"])
                continue
            session.add(CityCircle(**data))
            logger.info("  INSERT: %s", data["circle_id"])
        await session.flush()

        # 2. activity_clusters
        logger.info("=== Seeding activity_clusters (%d) ===", len(CLUSTERS))
        for data in CLUSTERS:
            existing = await session.get(ActivityCluster, data["cluster_id"])
            if existing:
                logger.info("  SKIP: %s", data["cluster_id"])
                continue
            session.add(ActivityCluster(**data))
            logger.info("  INSERT: %s", data["cluster_id"])
        await session.flush()

        # 3. hotel_strategy_presets
        logger.info("=== Seeding hotel_strategy_presets (%d) ===", len(HOTEL_PRESETS))
        for data in HOTEL_PRESETS:
            session.add(HotelStrategyPreset(**data))
            logger.info("  INSERT: %s", data["name_zh"])
        await session.flush()

        # 4. entity_aliases（无 entity_id 的占位别名，用于 T7 管线）
        logger.info("=== Seeding cluster_aliases ===")
        for cluster_aliases in CLUSTER_ALIASES:
            cluster_id = cluster_aliases["cluster_id"]
            for alias_data in cluster_aliases["aliases"]:
                # 不挂具体 entity，entity_id 为 None；T7 管线负责匹配后补填
                # 跳过已有的 normalized_text
                try:
                    session.add(EntityAlias(
                        entity_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),  # 占位 UUID，T7 替换
                        alias_text=alias_data["alias_text"],
                        alias_lang=alias_data.get("alias_lang"),
                        alias_type=alias_data.get("alias_type"),
                        normalized_text=alias_data.get("normalized_text"),
                    ))
                    logger.info("  ALIAS [%s] %s", cluster_id, alias_data["alias_text"])
                except Exception as e:
                    logger.debug("  alias skip: %s", e)
        await session.flush()

        await session.commit()
        logger.info("✅ 6 圈种子数据写入完成")
        logger.info("SEED_META: %s", SEED_META)

        # 汇总
        c_cnt = len((await session.execute(select(CityCircle))).scalars().all())
        cl_cnt = len((await session.execute(select(ActivityCluster))).scalars().all())
        h_cnt = len((await session.execute(select(HotelStrategyPreset))).scalars().all())
        logger.info(
            "当前数据：circles=%d  clusters=%d  hotel_presets=%d",
            c_cnt, cl_cnt, h_cnt,
        )


if __name__ == "__main__":
    asyncio.run(seed())
