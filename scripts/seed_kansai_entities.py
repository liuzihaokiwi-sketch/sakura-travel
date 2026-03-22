"""
seed_kansai_entities.py — P1-H1: 关西经典圈 MVP 实体种子数据

写入:
  - entity_base (30+ 实体)
  - pois / hotels / restaurants (子表)
  - circle_entity_roles (角色映射)

执行：
    cd D:/projects/projects/travel-ai
    python scripts/seed_kansai_entities.py

幂等：按 name_zh + city_code 检查重复，已存在则 SKIP。
"""
from __future__ import annotations

import asyncio
import logging
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select, and_
from app.db.session import AsyncSessionLocal
from app.db.models.catalog import EntityBase, Poi, Hotel, Restaurant
from app.db.models.city_circles import CircleEntityRole

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

CIRCLE_ID = "kansai_classic_circle"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# POI 实体
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

POIS = [
    {
        "base": {
            "name_zh": "清水寺",
            "name_ja": "清水寺",
            "name_en": "Kiyomizu-dera",
            "city_code": "kyoto",
            "area_name": "东山",
            "lat": 34.9948, "lng": 135.7850,
            "data_tier": "S",
            "nearest_station": "清水五条",
            "corridor_tags": ["kyo_higashiyama"],
            "typical_duration_baseline": 90,
            "price_band": "budget",
        },
        "ext": {
            "poi_category": "temple",
            "typical_duration_min": 90,
            "admission_fee_jpy": 400,
            "best_season": "all",
            "crowd_level_typical": "high",
            "google_rating": 4.5,
            "google_review_count": 45000,
        },
        "roles": [
            {"cluster_id": "kyo_higashiyama_gion_classic",
             "role": "anchor_poi", "sort_order": 0,
             "is_cluster_anchor": True},
        ],
    },
    {
        "base": {
            "name_zh": "八坂神社",
            "name_ja": "八坂神社",
            "name_en": "Yasaka Shrine",
            "city_code": "kyoto",
            "area_name": "祇园",
            "lat": 35.0036, "lng": 135.7785,
            "data_tier": "A",
            "nearest_station": "祇園四条",
            "corridor_tags": ["kyo_higashiyama", "kyo_gion"],
            "typical_duration_baseline": 30,
            "price_band": "free",
        },
        "ext": {
            "poi_category": "shrine",
            "typical_duration_min": 30,
            "admission_free": True,
            "best_season": "all",
            "crowd_level_typical": "medium",
            "google_rating": 4.4,
            "google_review_count": 22000,
        },
        "roles": [
            {"cluster_id": "kyo_higashiyama_gion_classic",
             "role": "secondary_poi", "sort_order": 3},
        ],
    },
    {
        "base": {
            "name_zh": "伏见稻荷大社",
            "name_ja": "伏見稲荷大社",
            "name_en": "Fushimi Inari Taisha",
            "city_code": "kyoto",
            "area_name": "伏见",
            "lat": 34.9671, "lng": 135.7727,
            "data_tier": "S",
            "nearest_station": "稲荷",
            "corridor_tags": ["kyo_fushimi"],
            "typical_duration_baseline": 120,
            "price_band": "free",
        },
        "ext": {
            "poi_category": "shrine",
            "typical_duration_min": 120,
            "admission_free": True,
            "best_season": "all",
            "crowd_level_typical": "high",
            "google_rating": 4.6,
            "google_review_count": 68000,
        },
        "roles": [
            {"cluster_id": "kyo_fushimi_inari",
             "role": "anchor_poi", "sort_order": 0,
             "is_cluster_anchor": True},
        ],
    },
    {
        "base": {
            "name_zh": "岚山竹林小径",
            "name_ja": "竹林の小径",
            "name_en": "Arashiyama Bamboo Grove",
            "city_code": "kyoto",
            "area_name": "岚山",
            "lat": 35.0170, "lng": 135.6713,
            "data_tier": "S",
            "nearest_station": "嵐山",
            "corridor_tags": ["kyo_arashiyama"],
            "typical_duration_baseline": 30,
            "price_band": "free",
        },
        "ext": {
            "poi_category": "park",
            "typical_duration_min": 30,
            "admission_free": True,
            "best_season": "all",
            "crowd_level_typical": "high",
            "google_rating": 4.4,
            "google_review_count": 35000,
        },
        "roles": [
            {"cluster_id": "kyo_arashiyama_sagano",
             "role": "anchor_poi", "sort_order": 0,
             "is_cluster_anchor": True},
        ],
    },
    {
        "base": {
            "name_zh": "天龙寺",
            "name_ja": "天龍寺",
            "name_en": "Tenryu-ji",
            "city_code": "kyoto",
            "area_name": "岚山",
            "lat": 35.0156, "lng": 135.6745,
            "data_tier": "A",
            "nearest_station": "嵐山",
            "corridor_tags": ["kyo_arashiyama"],
            "typical_duration_baseline": 60,
            "price_band": "budget",
        },
        "ext": {
            "poi_category": "temple",
            "typical_duration_min": 60,
            "admission_fee_jpy": 500,
            "best_season": "autumn",
            "crowd_level_typical": "medium",
            "google_rating": 4.5,
            "google_review_count": 12000,
        },
        "roles": [
            {"cluster_id": "kyo_arashiyama_sagano",
             "role": "secondary_poi", "sort_order": 1},
        ],
    },
    {
        "base": {
            "name_zh": "渡月桥",
            "name_ja": "渡月橋",
            "name_en": "Togetsukyo Bridge",
            "city_code": "kyoto",
            "area_name": "岚山",
            "lat": 35.0101, "lng": 135.6779,
            "data_tier": "A",
            "nearest_station": "嵐山",
            "corridor_tags": ["kyo_arashiyama"],
            "typical_duration_baseline": 20,
            "price_band": "free",
        },
        "ext": {
            "poi_category": "landmark",
            "typical_duration_min": 20,
            "admission_free": True,
            "best_season": "autumn",
            "crowd_level_typical": "medium",
            "google_rating": 4.3,
        },
        "roles": [
            {"cluster_id": "kyo_arashiyama_sagano",
             "role": "secondary_poi", "sort_order": 2},
        ],
    },
    {
        "base": {
            "name_zh": "金阁寺",
            "name_ja": "金閣寺",
            "name_en": "Kinkaku-ji",
            "city_code": "kyoto",
            "area_name": "衣笠",
            "lat": 35.0394, "lng": 135.7292,
            "data_tier": "S",
            "nearest_station": "金閣寺道(バス)",
            "corridor_tags": ["kyo_kinugasa"],
            "typical_duration_baseline": 60,
            "price_band": "budget",
        },
        "ext": {
            "poi_category": "temple",
            "typical_duration_min": 60,
            "admission_fee_jpy": 500,
            "best_season": "winter",
            "crowd_level_typical": "high",
            "google_rating": 4.6,
            "google_review_count": 42000,
        },
        "roles": [
            {"cluster_id": "kyo_kinkakuji_kinugasa",
             "role": "anchor_poi", "sort_order": 0,
             "is_cluster_anchor": True},
        ],
    },
    {
        "base": {
            "name_zh": "南禅寺",
            "name_ja": "南禅寺",
            "name_en": "Nanzen-ji",
            "city_code": "kyoto",
            "area_name": "冈崎",
            "lat": 35.0112, "lng": 135.7933,
            "data_tier": "A",
            "nearest_station": "蹴上",
            "corridor_tags": ["kyo_okazaki"],
            "typical_duration_baseline": 60,
            "price_band": "budget",
        },
        "ext": {
            "poi_category": "temple",
            "typical_duration_min": 60,
            "admission_fee_jpy": 600,
            "best_season": "autumn",
            "crowd_level_typical": "medium",
            "google_rating": 4.5,
            "google_review_count": 8000,
        },
        "roles": [
            {"cluster_id": "kyo_philosopher_path_nanzen",
             "role": "anchor_poi", "sort_order": 0,
             "is_cluster_anchor": True},
        ],
    },
    # ── 大阪 POI ──
    {
        "base": {
            "name_zh": "大阪城天守阁",
            "name_ja": "大阪城天守閣",
            "name_en": "Osaka Castle",
            "city_code": "osaka",
            "area_name": "大阪城",
            "lat": 34.6873, "lng": 135.5262,
            "data_tier": "A",
            "nearest_station": "大阪城公園",
            "corridor_tags": ["osa_osakajo"],
            "typical_duration_baseline": 90,
            "price_band": "budget",
        },
        "ext": {
            "poi_category": "castle",
            "typical_duration_min": 90,
            "admission_fee_jpy": 600,
            "best_season": "spring",
            "crowd_level_typical": "high",
            "google_rating": 4.3,
            "google_review_count": 38000,
        },
        "roles": [
            {"cluster_id": "osa_osaka_castle_tenmabashi",
             "role": "anchor_poi", "sort_order": 0,
             "is_cluster_anchor": True},
        ],
    },
    {
        "base": {
            "name_zh": "日本环球影城",
            "name_ja": "ユニバーサル・スタジオ・ジャパン",
            "name_en": "Universal Studios Japan",
            "city_code": "osaka",
            "area_name": "此花",
            "lat": 34.6654, "lng": 135.4323,
            "data_tier": "S",
            "nearest_station": "ユニバーサルシティ",
            "corridor_tags": ["osa_sakurajima"],
            "typical_duration_baseline": 600,
            "price_band": "premium",
        },
        "ext": {
            "poi_category": "theme_park",
            "typical_duration_min": 600,
            "admission_fee_jpy": 8600,
            "best_season": "all",
            "crowd_level_typical": "high",
            "requires_advance_booking": True,
            "google_rating": 4.4,
            "google_review_count": 85000,
        },
        "roles": [
            {"cluster_id": "osa_usj_themepark",
             "role": "anchor_poi", "sort_order": 0,
             "is_cluster_anchor": True},
        ],
    },
    {
        "base": {
            "name_zh": "通天阁",
            "name_ja": "通天閣",
            "name_en": "Tsutenkaku Tower",
            "city_code": "osaka",
            "area_name": "新世界",
            "lat": 34.6525, "lng": 135.5063,
            "data_tier": "B",
            "nearest_station": "新今宮",
            "corridor_tags": ["osa_shinsekai"],
            "typical_duration_baseline": 45,
            "price_band": "budget",
        },
        "ext": {
            "poi_category": "landmark",
            "typical_duration_min": 45,
            "admission_fee_jpy": 900,
            "best_season": "all",
            "crowd_level_typical": "medium",
            "google_rating": 3.9,
        },
        "roles": [
            {"cluster_id": "osa_shinsekai_tenno",
             "role": "anchor_poi", "sort_order": 0,
             "is_cluster_anchor": True},
        ],
    },
    # ── 奈良 POI ──
    {
        "base": {
            "name_zh": "东大寺",
            "name_ja": "東大寺",
            "name_en": "Todai-ji",
            "city_code": "nara",
            "area_name": "奈良公园",
            "lat": 34.6890, "lng": 135.8399,
            "data_tier": "S",
            "nearest_station": "近鉄奈良",
            "corridor_tags": ["nara_park"],
            "typical_duration_baseline": 60,
            "price_band": "budget",
        },
        "ext": {
            "poi_category": "temple",
            "typical_duration_min": 60,
            "admission_fee_jpy": 600,
            "best_season": "all",
            "crowd_level_typical": "high",
            "google_rating": 4.6,
            "google_review_count": 25000,
        },
        "roles": [
            {"cluster_id": "kyo_nara_day_trip",
             "role": "anchor_poi", "sort_order": 0,
             "is_cluster_anchor": True},
        ],
    },
    {
        "base": {
            "name_zh": "奈良公园（鹿公园）",
            "name_ja": "奈良公園",
            "name_en": "Nara Park",
            "city_code": "nara",
            "area_name": "奈良公园",
            "lat": 34.6851, "lng": 135.8398,
            "data_tier": "A",
            "nearest_station": "近鉄奈良",
            "corridor_tags": ["nara_park"],
            "typical_duration_baseline": 90,
            "price_band": "free",
        },
        "ext": {
            "poi_category": "park",
            "typical_duration_min": 90,
            "admission_free": True,
            "best_season": "all",
            "crowd_level_typical": "medium",
            "google_rating": 4.5,
            "google_review_count": 30000,
        },
        "roles": [
            {"cluster_id": "kyo_nara_day_trip",
             "role": "secondary_poi", "sort_order": 1},
        ],
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 酒店实体
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HOTELS = [
    {
        "base": {
            "name_zh": "京都世纪酒店",
            "name_ja": "ホテルグランヴィア京都",
            "name_en": "Hotel Granvia Kyoto",
            "city_code": "kyoto",
            "area_name": "京都站",
            "lat": 34.9854, "lng": 135.7589,
            "data_tier": "A",
            "nearest_station": "京都",
            "corridor_tags": ["kyo_kawaramachi"],
            "price_band": "premium",
        },
        "ext": {
            "hotel_type": "business",
            "star_rating": 4.5,
            "room_count": 537,
            "check_in_time": "14:00",
            "check_out_time": "11:00",
            "amenities": ["breakfast", "fitness", "concierge"],
            "is_family_friendly": True,
            "price_tier": "premium",
            "typical_price_min_jpy": 18000,
            "google_rating": 4.4,
            "booking_score": 8.7,
        },
        "roles": [
            {"cluster_id": None,
             "role": "hotel_anchor", "sort_order": 0},
        ],
    },
    {
        "base": {
            "name_zh": "京都四条三井花园酒店",
            "name_ja": "三井ガーデンホテル京都四条",
            "name_en": "Mitsui Garden Hotel Kyoto Shijo",
            "city_code": "kyoto",
            "area_name": "四条烏丸",
            "lat": 35.0020, "lng": 135.7610,
            "data_tier": "A",
            "nearest_station": "四条",
            "corridor_tags": ["kyo_kawaramachi"],
            "price_band": "mid",
        },
        "ext": {
            "hotel_type": "business",
            "star_rating": 3.5,
            "room_count": 272,
            "check_in_time": "15:00",
            "check_out_time": "11:00",
            "amenities": ["breakfast", "bath"],
            "is_family_friendly": True,
            "price_tier": "mid",
            "typical_price_min_jpy": 12000,
            "google_rating": 4.2,
            "booking_score": 8.3,
        },
        "roles": [
            {"cluster_id": None,
             "role": "hotel_anchor", "sort_order": 0},
        ],
    },
    {
        "base": {
            "name_zh": "大阪难波道顿堀相铁FRESA INN",
            "name_ja": "相鉄フレッサイン大阪なんば駅前",
            "name_en": "Sotetsu Fresa Inn Osaka Namba",
            "city_code": "osaka",
            "area_name": "难波",
            "lat": 34.6645, "lng": 135.5022,
            "data_tier": "A",
            "nearest_station": "なんば",
            "corridor_tags": ["osa_namba"],
            "price_band": "mid",
        },
        "ext": {
            "hotel_type": "business",
            "star_rating": 3.0,
            "room_count": 352,
            "check_in_time": "15:00",
            "check_out_time": "10:00",
            "amenities": ["breakfast"],
            "price_tier": "mid",
            "typical_price_min_jpy": 8000,
            "google_rating": 4.0,
            "booking_score": 8.0,
        },
        "roles": [
            {"cluster_id": None,
             "role": "hotel_anchor", "sort_order": 0},
        ],
    },
    {
        "base": {
            "name_zh": "大阪瑞士南海酒店",
            "name_ja": "スイスホテル南海大阪",
            "name_en": "Swissotel Nankai Osaka",
            "city_code": "osaka",
            "area_name": "难波",
            "lat": 34.6657, "lng": 135.5020,
            "data_tier": "A",
            "nearest_station": "なんば",
            "corridor_tags": ["osa_namba"],
            "price_band": "premium",
        },
        "ext": {
            "hotel_type": "business",
            "star_rating": 5.0,
            "room_count": 546,
            "check_in_time": "15:00",
            "check_out_time": "11:00",
            "amenities": ["breakfast", "fitness", "pool", "concierge", "spa"],
            "is_family_friendly": True,
            "price_tier": "premium",
            "typical_price_min_jpy": 25000,
            "google_rating": 4.4,
            "booking_score": 8.8,
        },
        "roles": [
            {"cluster_id": None,
             "role": "hotel_anchor", "sort_order": 0},
        ],
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 餐厅实体
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RESTAURANTS = [
    # ── 京都 ──
    {
        "base": {
            "name_zh": "祇园 う桶や う",
            "name_ja": "祇をん う桶や う",
            "name_en": "Gion Uokeyau",
            "city_code": "kyoto",
            "area_name": "祇园",
            "lat": 35.0041, "lng": 135.7759,
            "data_tier": "A",
            "nearest_station": "祇園四条",
            "corridor_tags": ["kyo_gion", "kyo_higashiyama"],
            "price_band": "premium",
        },
        "ext": {
            "cuisine_type": "kaiseki",
            "tabelog_score": 3.58,
            "requires_reservation": True,
            "reservation_difficulty": "medium",
            "budget_lunch_jpy": 3500,
            "budget_dinner_jpy": 8000,
            "has_english_menu": True,
        },
        "roles": [
            {"cluster_id": "kyo_higashiyama_gion_classic",
             "role": "meal_destination", "sort_order": 0},
        ],
    },
    {
        "base": {
            "name_zh": "% Arabica 岚山",
            "name_ja": "% アラビカ 京都 嵐山",
            "name_en": "% Arabica Arashiyama",
            "city_code": "kyoto",
            "area_name": "岚山",
            "lat": 35.0112, "lng": 135.6777,
            "data_tier": "B",
            "nearest_station": "嵐山",
            "corridor_tags": ["kyo_arashiyama"],
            "price_band": "budget",
        },
        "ext": {
            "cuisine_type": "cafe",
            "budget_lunch_jpy": 600,
            "has_english_menu": True,
        },
        "roles": [
            {"cluster_id": "kyo_arashiyama_sagano",
             "role": "meal_route", "sort_order": 0},
        ],
    },
    {
        "base": {
            "name_zh": "伏见稻荷参道·祢ざめ家",
            "name_ja": "祢ざめ家",
            "name_en": "Nezameya (Fushimi Inari)",
            "city_code": "kyoto",
            "area_name": "伏见",
            "lat": 34.9676, "lng": 135.7718,
            "data_tier": "B",
            "nearest_station": "稲荷",
            "corridor_tags": ["kyo_fushimi"],
            "price_band": "budget",
        },
        "ext": {
            "cuisine_type": "inari_sushi",
            "budget_lunch_jpy": 1200,
            "has_english_menu": True,
        },
        "roles": [
            {"cluster_id": "kyo_fushimi_inari",
             "role": "meal_route", "sort_order": 0},
        ],
    },
    # ── 大阪 ──
    {
        "base": {
            "name_zh": "道顿堀章鱼烧 くくる",
            "name_ja": "たこ焼き道楽 わなか 道頓堀店",
            "name_en": "Takoyaki Wanaka Dotonbori",
            "city_code": "osaka",
            "area_name": "道顿堀",
            "lat": 34.6688, "lng": 135.5014,
            "data_tier": "A",
            "nearest_station": "なんば",
            "corridor_tags": ["osa_namba"],
            "price_band": "budget",
        },
        "ext": {
            "cuisine_type": "takoyaki",
            "budget_lunch_jpy": 500,
            "has_english_menu": True,
        },
        "roles": [
            {"cluster_id": "osa_dotonbori_minami_food",
             "role": "meal_destination", "sort_order": 0},
        ],
    },
    {
        "base": {
            "name_zh": "大阪烧 美津の",
            "name_ja": "美津の",
            "name_en": "Mizuno Okonomiyaki",
            "city_code": "osaka",
            "area_name": "道顿堀",
            "lat": 34.6690, "lng": 135.5018,
            "data_tier": "A",
            "nearest_station": "なんば",
            "corridor_tags": ["osa_namba"],
            "price_band": "mid",
        },
        "ext": {
            "cuisine_type": "okonomiyaki",
            "tabelog_score": 3.72,
            "budget_lunch_jpy": 1500,
            "budget_dinner_jpy": 2000,
            "has_english_menu": True,
        },
        "roles": [
            {"cluster_id": "osa_dotonbori_minami_food",
             "role": "meal_destination", "sort_order": 1},
        ],
    },
    {
        "base": {
            "name_zh": "串炸达摩 新世界总本店",
            "name_ja": "串かつだるま 新世界総本店",
            "name_en": "Kushikatsu Daruma Shinsekai",
            "city_code": "osaka",
            "area_name": "新世界",
            "lat": 34.6523, "lng": 135.5064,
            "data_tier": "A",
            "nearest_station": "新今宮",
            "corridor_tags": ["osa_shinsekai"],
            "price_band": "budget",
        },
        "ext": {
            "cuisine_type": "kushikatsu",
            "budget_lunch_jpy": 1000,
            "budget_dinner_jpy": 1500,
            "has_english_menu": True,
        },
        "roles": [
            {"cluster_id": "osa_shinsekai_tenno",
             "role": "meal_destination", "sort_order": 0},
        ],
    },
    # ── 奈良 ──
    {
        "base": {
            "name_zh": "志津香 釜饭",
            "name_ja": "志津香",
            "name_en": "Shizuka Kamameshi",
            "city_code": "nara",
            "area_name": "奈良公园",
            "lat": 34.6840, "lng": 135.8371,
            "data_tier": "B",
            "nearest_station": "近鉄奈良",
            "corridor_tags": ["nara_park"],
            "price_band": "mid",
        },
        "ext": {
            "cuisine_type": "kamameshi",
            "budget_lunch_jpy": 1500,
            "has_english_menu": True,
        },
        "roles": [
            {"cluster_id": "kyo_nara_day_trip",
             "role": "meal_route", "sort_order": 0},
        ],
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 辅助函数
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _find_or_create_entity(
    session,
    base_data: dict,
    entity_type: str,
) -> tuple[uuid.UUID, bool]:
    """
    按 name_zh + city_code 查找实体，不存在则创建。
    返回 (entity_id, is_new)。
    """
    result = await session.execute(
        select(EntityBase).where(and_(
            EntityBase.name_zh == base_data["name_zh"],
            EntityBase.city_code == base_data["city_code"],
        ))
    )
    existing = result.scalars().first()
    if existing:
        return existing.entity_id, False

    entity_id = uuid.uuid4()
    entity = EntityBase(
        entity_id=entity_id,
        entity_type=entity_type,
        **base_data,
    )
    session.add(entity)
    await session.flush()
    return entity_id, True


async def _create_ext(session, entity_id, ext_data, model_class):
    """创建子表记录"""
    ext = model_class(entity_id=entity_id, **ext_data)
    session.add(ext)


async def _create_roles(session, entity_id, roles):
    """创建实体角色映射"""
    for r in roles:
        # 检查重复
        where_clauses = [
            CircleEntityRole.circle_id == CIRCLE_ID,
            CircleEntityRole.entity_id == entity_id,
            CircleEntityRole.role == r["role"],
        ]
        if r.get("cluster_id"):
            where_clauses.append(
                CircleEntityRole.cluster_id == r["cluster_id"]
            )
        existing = await session.execute(
            select(CircleEntityRole).where(and_(*where_clauses))
        )
        if existing.scalar_one_or_none():
            continue
        role = CircleEntityRole(
            circle_id=CIRCLE_ID,
            cluster_id=r.get("cluster_id"),
            entity_id=entity_id,
            role=r["role"],
            sort_order=r.get("sort_order", 0),
            is_cluster_anchor=r.get("is_cluster_anchor", False),
        )
        session.add(role)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Seed 执行
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def seed():
    stats = {"poi_new": 0, "poi_skip": 0,
             "hotel_new": 0, "hotel_skip": 0,
             "rest_new": 0, "rest_skip": 0,
             "roles": 0}

    async with AsyncSessionLocal() as session:
        # ── POIs ──────────────────────────────────────────────────────────
        logger.info("=== Seeding POIs (%d) ===", len(POIS))
        for item in POIS:
            eid, is_new = await _find_or_create_entity(
                session, item["base"], "poi"
            )
            if is_new:
                await _create_ext(session, eid, item["ext"], Poi)
                stats["poi_new"] += 1
                logger.info("  NEW  poi: %s", item["base"]["name_zh"])
            else:
                stats["poi_skip"] += 1
                logger.info("  SKIP poi: %s", item["base"]["name_zh"])
            await _create_roles(session, eid, item["roles"])
        await session.flush()

        # ── Hotels ────────────────────────────────────────────────────────
        logger.info("=== Seeding Hotels (%d) ===", len(HOTELS))
        for item in HOTELS:
            eid, is_new = await _find_or_create_entity(
                session, item["base"], "hotel"
            )
            if is_new:
                await _create_ext(session, eid, item["ext"], Hotel)
                stats["hotel_new"] += 1
                logger.info("  NEW  hotel: %s", item["base"]["name_zh"])
            else:
                stats["hotel_skip"] += 1
                logger.info("  SKIP hotel: %s", item["base"]["name_zh"])
            await _create_roles(session, eid, item["roles"])
        await session.flush()

        # ── Restaurants ───────────────────────────────────────────────────
        logger.info("=== Seeding Restaurants (%d) ===", len(RESTAURANTS))
        for item in RESTAURANTS:
            eid, is_new = await _find_or_create_entity(
                session, item["base"], "restaurant"
            )
            if is_new:
                await _create_ext(session, eid, item["ext"], Restaurant)
                stats["rest_new"] += 1
                logger.info("  NEW  restaurant: %s", item["base"]["name_zh"])
            else:
                stats["rest_skip"] += 1
                logger.info("  SKIP restaurant: %s", item["base"]["name_zh"])
            await _create_roles(session, eid, item["roles"])
        await session.flush()

        await session.commit()

        # ── 统计 ──────────────────────────────────────────────────────────
        total_e = len((await session.execute(select(EntityBase))).scalars().all())
        total_r = len((await session.execute(select(CircleEntityRole))).scalars().all())
        logger.info("✅ 关西实体种子完成")
        logger.info(
            "  新建: poi=%d hotel=%d restaurant=%d",
            stats["poi_new"], stats["hotel_new"], stats["rest_new"],
        )
        logger.info(
            "  跳过: poi=%d hotel=%d restaurant=%d",
            stats["poi_skip"], stats["hotel_skip"], stats["rest_skip"],
        )
        logger.info("  entity_base 总计: %d", total_e)
        logger.info("  circle_entity_roles 总计: %d", total_r)


if __name__ == "__main__":
    asyncio.run(seed())
