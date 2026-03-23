"""
seed_kansai_extended_entities.py — 关西实体数据大扩充
新增约 110 POI + 65 餐厅 + 8 酒店，覆盖：
  宇治 / 枯山水庭园 / 现代建筑 / 奈良深度 /
  神户 / 有马温泉 / 京都各走廊补全 / 大阪补全

执行：
    cd D:/projects/projects/travel-ai
    python scripts/seed_kansai_extended_entities.py

幂等：name_zh + city_code 重复则 SKIP。
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
# POI 实体（扩充）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

POIS = [
    # ── 东山走廊补全 ──────────────────────────────────────────────────────────
    {
        "base": {
            "name_zh": "二年坂·三年坂",
            "name_ja": "二年坂・三年坂",
            "name_en": "Ninenzaka & Sannenzaka",
            "city_code": "kyoto", "area_name": "东山",
            "lat": 34.9985, "lng": 135.7826,
            "data_tier": "A", "nearest_station": "清水五条",
            "corridor_tags": ["kyo_higashiyama"],
            "typical_duration_baseline": 45, "price_band": "free",
        },
        "ext": {
            "poi_category": "historic_street", "typical_duration_min": 45,
            "admission_free": True, "best_season": "all",
            "crowd_level_typical": "high",
            "google_rating": 4.4, "google_review_count": 18000,
        },
        "roles": [{"cluster_id": "kyo_higashiyama_gion_classic", "role": "secondary_poi", "sort_order": 1}],
    },
    {
        "base": {
            "name_zh": "高台寺",
            "name_ja": "高台寺", "name_en": "Kodai-ji",
            "city_code": "kyoto", "area_name": "东山",
            "lat": 35.0010, "lng": 135.7820,
            "data_tier": "A", "nearest_station": "祇園四条",
            "corridor_tags": ["kyo_higashiyama"],
            "typical_duration_baseline": 50, "price_band": "budget",
        },
        "ext": {
            "poi_category": "temple", "typical_duration_min": 50,
            "admission_fee_jpy": 600, "best_season": "autumn",
            "crowd_level_typical": "medium",
            "google_rating": 4.3, "google_review_count": 7500,
        },
        "roles": [{"cluster_id": "kyo_higashiyama_gion_classic", "role": "secondary_poi", "sort_order": 2}],
    },
    {
        "base": {
            "name_zh": "祇园花见小路",
            "name_ja": "花見小路", "name_en": "Hanamikoji Street",
            "city_code": "kyoto", "area_name": "祇园",
            "lat": 35.0035, "lng": 135.7750,
            "data_tier": "A", "nearest_station": "祇園四条",
            "corridor_tags": ["kyo_gion", "kyo_higashiyama"],
            "typical_duration_baseline": 30, "price_band": "free",
        },
        "ext": {
            "poi_category": "historic_street", "typical_duration_min": 30,
            "admission_free": True, "best_season": "all",
            "crowd_level_typical": "high",
            "google_rating": 4.3, "google_review_count": 14000,
        },
        "roles": [{"cluster_id": "kyo_higashiyama_gion_classic", "role": "secondary_poi", "sort_order": 4}],
    },
    {
        "base": {
            "name_zh": "知恩院",
            "name_ja": "知恩院", "name_en": "Chion-in",
            "city_code": "kyoto", "area_name": "东山",
            "lat": 35.0062, "lng": 135.7820,
            "data_tier": "B", "nearest_station": "祇園四条",
            "corridor_tags": ["kyo_higashiyama"],
            "typical_duration_baseline": 40, "price_band": "free",
        },
        "ext": {
            "poi_category": "temple", "typical_duration_min": 40,
            "admission_free": True, "best_season": "all",
            "crowd_level_typical": "medium",
            "google_rating": 4.3, "google_review_count": 5000,
        },
        "roles": [{"cluster_id": "kyo_higashiyama_gion_classic", "role": "secondary_poi", "sort_order": 5}],
    },
    # ── 哲学之道·冈崎走廊补全 ────────────────────────────────────────────────
    {
        "base": {
            "name_zh": "哲学之道",
            "name_ja": "哲学の道", "name_en": "Philosopher's Path",
            "city_code": "kyoto", "area_name": "冈崎",
            "lat": 35.0188, "lng": 135.7943,
            "data_tier": "A", "nearest_station": "蹴上",
            "corridor_tags": ["kyo_okazaki"],
            "typical_duration_baseline": 40, "price_band": "free",
        },
        "ext": {
            "poi_category": "park", "typical_duration_min": 40,
            "admission_free": True, "best_season": "spring",
            "crowd_level_typical": "high",
            "google_rating": 4.4, "google_review_count": 12000,
        },
        "roles": [{"cluster_id": "kyo_philosopher_path_nanzen", "role": "secondary_poi", "sort_order": 1}],
    },
    {
        "base": {
            "name_zh": "平安神宫",
            "name_ja": "平安神宮", "name_en": "Heian Jingu",
            "city_code": "kyoto", "area_name": "冈崎",
            "lat": 35.0164, "lng": 135.7822,
            "data_tier": "A", "nearest_station": "東山",
            "corridor_tags": ["kyo_okazaki"],
            "typical_duration_baseline": 40, "price_band": "budget",
        },
        "ext": {
            "poi_category": "shrine", "typical_duration_min": 40,
            "admission_fee_jpy": 600, "best_season": "spring",
            "crowd_level_typical": "medium",
            "google_rating": 4.2, "google_review_count": 8000,
        },
        "roles": [{"cluster_id": "kyo_philosopher_path_nanzen", "role": "secondary_poi", "sort_order": 2}],
    },
    {
        "base": {
            "name_zh": "永观堂禅林寺",
            "name_ja": "永観堂禅林寺", "name_en": "Eikan-do Zenrin-ji",
            "city_code": "kyoto", "area_name": "冈崎",
            "lat": 35.0136, "lng": 135.7951,
            "data_tier": "A", "nearest_station": "蹴上",
            "corridor_tags": ["kyo_okazaki"],
            "typical_duration_baseline": 60, "price_band": "budget",
        },
        "ext": {
            "poi_category": "temple", "typical_duration_min": 60,
            "admission_fee_jpy": 600, "best_season": "autumn",
            "crowd_level_typical": "high",
            "google_rating": 4.5, "google_review_count": 9000,
        },
        "roles": [
            {"cluster_id": "kyo_eikando_shinnyodo", "role": "anchor_poi", "sort_order": 0, "is_cluster_anchor": True},
            {"cluster_id": "kyo_philosopher_path_nanzen", "role": "secondary_poi", "sort_order": 3},
        ],
    },
    {
        "base": {
            "name_zh": "真如堂",
            "name_ja": "真如堂", "name_en": "Shinnyodo",
            "city_code": "kyoto", "area_name": "冈崎",
            "lat": 35.0211, "lng": 135.7936,
            "data_tier": "B", "nearest_station": "東山",
            "corridor_tags": ["kyo_okazaki"],
            "typical_duration_baseline": 40, "price_band": "free",
        },
        "ext": {
            "poi_category": "temple", "typical_duration_min": 40,
            "admission_free": True, "best_season": "autumn",
            "crowd_level_typical": "low",
            "google_rating": 4.4, "google_review_count": 3000,
        },
        "roles": [{"cluster_id": "kyo_eikando_shinnyodo", "role": "secondary_poi", "sort_order": 1}],
    },
    # ── 衣笠走廊补全（龙安寺·仁和寺） ───────────────────────────────────────
    {
        "base": {
            "name_zh": "龙安寺",
            "name_ja": "龍安寺", "name_en": "Ryoan-ji",
            "city_code": "kyoto", "area_name": "衣笠",
            "lat": 35.0345, "lng": 135.7186,
            "data_tier": "A", "nearest_station": "龍安寺(バス)",
            "corridor_tags": ["kyo_kinugasa", "kyo_zen_garden"],
            "typical_duration_baseline": 60, "price_band": "budget",
        },
        "ext": {
            "poi_category": "temple", "typical_duration_min": 60,
            "admission_fee_jpy": 600, "best_season": "all",
            "crowd_level_typical": "medium",
            "google_rating": 4.3, "google_review_count": 11000,
        },
        "roles": [
            {"cluster_id": "kyo_kinkakuji_kinugasa", "role": "secondary_poi", "sort_order": 1},
            {"cluster_id": "kyo_zen_garden_circuit", "role": "anchor_poi", "sort_order": 0, "is_cluster_anchor": True},
        ],
    },
    {
        "base": {
            "name_zh": "仁和寺",
            "name_ja": "仁和寺", "name_en": "Ninna-ji",
            "city_code": "kyoto", "area_name": "衣笠",
            "lat": 35.0298, "lng": 135.7131,
            "data_tier": "B", "nearest_station": "御室仁和寺(バス)",
            "corridor_tags": ["kyo_kinugasa"],
            "typical_duration_baseline": 50, "price_band": "budget",
        },
        "ext": {
            "poi_category": "temple", "typical_duration_min": 50,
            "admission_fee_jpy": 500, "best_season": "spring",
            "crowd_level_typical": "low",
            "google_rating": 4.2, "google_review_count": 5000,
        },
        "roles": [{"cluster_id": "kyo_kinkakuji_kinugasa", "role": "secondary_poi", "sort_order": 2}],
    },
    # ── 枯山水庭园走廊 POI ───────────────────────────────────────────────────
    {
        "base": {
            "name_zh": "大德寺",
            "name_ja": "大徳寺", "name_en": "Daitoku-ji",
            "city_code": "kyoto", "area_name": "紫野",
            "lat": 35.0454, "lng": 135.7452,
            "data_tier": "A", "nearest_station": "大徳寺前(バス)",
            "corridor_tags": ["kyo_zen_garden"],
            "typical_duration_baseline": 90, "price_band": "budget",
        },
        "ext": {
            "poi_category": "temple", "typical_duration_min": 90,
            "admission_fee_jpy": 400, "best_season": "all",
            "crowd_level_typical": "low",
            "google_rating": 4.3, "google_review_count": 4000,
        },
        "roles": [{"cluster_id": "kyo_zen_garden_circuit", "role": "secondary_poi", "sort_order": 1}],
    },
    {
        "base": {
            "name_zh": "东福寺",
            "name_ja": "東福寺", "name_en": "Tofuku-ji",
            "city_code": "kyoto", "area_name": "伏见北",
            "lat": 34.9797, "lng": 135.7742,
            "data_tier": "A", "nearest_station": "東福寺",
            "corridor_tags": ["kyo_zen_garden", "kyo_fushimi"],
            "typical_duration_baseline": 60, "price_band": "budget",
        },
        "ext": {
            "poi_category": "temple", "typical_duration_min": 60,
            "admission_fee_jpy": 600, "best_season": "autumn",
            "crowd_level_typical": "high",
            "google_rating": 4.4, "google_review_count": 13000,
        },
        "roles": [{"cluster_id": "kyo_zen_garden_circuit", "role": "secondary_poi", "sort_order": 2}],
    },
    # ── 现代建筑走廊 POI ─────────────────────────────────────────────────────
    {
        "base": {
            "name_zh": "京都站大楼",
            "name_ja": "京都駅ビル", "name_en": "Kyoto Station Building (Hara Hiroshi)",
            "city_code": "kyoto", "area_name": "京都站",
            "lat": 34.9854, "lng": 135.7588,
            "data_tier": "A", "nearest_station": "京都",
            "corridor_tags": ["kyo_nishikyo", "kyo_kawaramachi"],
            "typical_duration_baseline": 40, "price_band": "free",
        },
        "ext": {
            "poi_category": "modern_architecture", "typical_duration_min": 40,
            "admission_free": True, "best_season": "all",
            "crowd_level_typical": "medium",
            "google_rating": 4.3, "google_review_count": 20000,
        },
        "roles": [{"cluster_id": "kyo_katsura_modern_arch", "role": "secondary_poi", "sort_order": 1}],
    },
    {
        "base": {
            "name_zh": "陶板名画之庭",
            "name_ja": "陶板名画の庭", "name_en": "Taizan Meiga no Niwa (Ando Tadao)",
            "city_code": "kyoto", "area_name": "北山",
            "lat": 35.0379, "lng": 135.7681,
            "data_tier": "B", "nearest_station": "北山",
            "corridor_tags": ["kyo_nishikyo"],
            "typical_duration_baseline": 40, "price_band": "free",
        },
        "ext": {
            "poi_category": "modern_architecture", "typical_duration_min": 40,
            "admission_free": True, "best_season": "all",
            "crowd_level_typical": "low",
            "google_rating": 4.1, "google_review_count": 1200,
        },
        "roles": [{"cluster_id": "kyo_katsura_modern_arch", "role": "secondary_poi", "sort_order": 2}],
    },
    {
        "base": {
            "name_zh": "桂离宫",
            "name_ja": "桂離宮", "name_en": "Katsura Rikyu",
            "city_code": "kyoto", "area_name": "桂",
            "lat": 34.9943, "lng": 135.7093,
            "data_tier": "A", "nearest_station": "桂",
            "corridor_tags": ["kyo_nishikyo"],
            "typical_duration_baseline": 60, "price_band": "budget",
        },
        "ext": {
            "poi_category": "garden", "typical_duration_min": 60,
            "admission_fee_jpy": 1000, "best_season": "all",
            "crowd_level_typical": "low", "requires_advance_booking": True,
            "google_rating": 4.6, "google_review_count": 3500,
        },
        "roles": [{"cluster_id": "kyo_katsura_modern_arch", "role": "anchor_poi", "sort_order": 0, "is_cluster_anchor": True}],
    },
    # ── 西阵·二条城走廊 ──────────────────────────────────────────────────────
    {
        "base": {
            "name_zh": "二条城",
            "name_ja": "二条城", "name_en": "Nijo Castle",
            "city_code": "kyoto", "area_name": "二条",
            "lat": 35.0142, "lng": 135.7484,
            "data_tier": "A", "nearest_station": "二条城前",
            "corridor_tags": ["kyo_nijo"],
            "typical_duration_baseline": 90, "price_band": "budget",
        },
        "ext": {
            "poi_category": "castle", "typical_duration_min": 90,
            "admission_fee_jpy": 1030, "best_season": "all",
            "crowd_level_typical": "medium",
            "google_rating": 4.2, "google_review_count": 22000,
        },
        "roles": [{"cluster_id": "kyo_nijo_nishijin", "role": "anchor_poi", "sort_order": 0, "is_cluster_anchor": True}],
    },
    {
        "base": {
            "name_zh": "西阵织会馆",
            "name_ja": "西陣織会館", "name_en": "Nishijin Textile Center",
            "city_code": "kyoto", "area_name": "西阵",
            "lat": 35.0236, "lng": 135.7519,
            "data_tier": "B", "nearest_station": "今出川",
            "corridor_tags": ["kyo_nijo"],
            "typical_duration_baseline": 60, "price_band": "free",
        },
        "ext": {
            "poi_category": "museum", "typical_duration_min": 60,
            "admission_free": True, "best_season": "all",
            "crowd_level_typical": "low",
            "google_rating": 3.9, "google_review_count": 2000,
        },
        "roles": [{"cluster_id": "kyo_nijo_nishijin", "role": "secondary_poi", "sort_order": 1}],
    },
    # ── 苔寺（西芳寺） ───────────────────────────────────────────────────────
    {
        "base": {
            "name_zh": "西芳寺（苔寺）",
            "name_ja": "西芳寺", "name_en": "Saihoji (Kokedera Moss Temple)",
            "city_code": "kyoto", "area_name": "松尾",
            "lat": 34.9967, "lng": 135.6836,
            "data_tier": "A", "nearest_station": "苔寺・すず虫寺(バス)",
            "corridor_tags": ["kyo_arashiyama"],
            "typical_duration_baseline": 90, "price_band": "premium",
        },
        "ext": {
            "poi_category": "temple", "typical_duration_min": 90,
            "admission_fee_jpy": 3000, "best_season": "all",
            "crowd_level_typical": "low", "requires_advance_booking": True,
            "google_rating": 4.6, "google_review_count": 2800,
        },
        "roles": [{"cluster_id": "kyo_saihoji_moss_temple", "role": "anchor_poi", "sort_order": 0, "is_cluster_anchor": True}],
    },
    # ── 伏见酒藏走廊补全 ─────────────────────────────────────────────────────
    {
        "base": {
            "name_zh": "月桂冠大仓纪念馆",
            "name_ja": "月桂冠大倉記念館", "name_en": "Gekkeikan Okura Sake Museum",
            "city_code": "kyoto", "area_name": "伏见",
            "lat": 34.9388, "lng": 135.7617,
            "data_tier": "B", "nearest_station": "中書島",
            "corridor_tags": ["kyo_fushimi"],
            "typical_duration_baseline": 45, "price_band": "budget",
        },
        "ext": {
            "poi_category": "museum", "typical_duration_min": 45,
            "admission_fee_jpy": 600, "best_season": "all",
            "crowd_level_typical": "low",
            "google_rating": 4.1, "google_review_count": 2500,
        },
        "roles": [{"cluster_id": "kyo_fushimi_sake_town", "role": "anchor_poi", "sort_order": 0, "is_cluster_anchor": True}],
    },
    {
        "base": {
            "name_zh": "寺田屋",
            "name_ja": "寺田屋", "name_en": "Teradaya Inn",
            "city_code": "kyoto", "area_name": "伏见",
            "lat": 34.9378, "lng": 135.7621,
            "data_tier": "B", "nearest_station": "中書島",
            "corridor_tags": ["kyo_fushimi"],
            "typical_duration_baseline": 20, "price_band": "budget",
        },
        "ext": {
            "poi_category": "historic_site", "typical_duration_min": 20,
            "admission_fee_jpy": 400, "best_season": "all",
            "crowd_level_typical": "low",
            "google_rating": 3.9, "google_review_count": 1800,
        },
        "roles": [{"cluster_id": "kyo_fushimi_sake_town", "role": "secondary_poi", "sort_order": 1}],
    },
    # ── 宇治走廊 POI ─────────────────────────────────────────────────────────
    {
        "base": {
            "name_zh": "平等院凤凰堂",
            "name_ja": "平等院鳳凰堂", "name_en": "Byodoin Phoenix Hall",
            "city_code": "uji", "area_name": "宇治",
            "lat": 34.8893, "lng": 135.8075,
            "data_tier": "S", "nearest_station": "宇治",
            "corridor_tags": ["uji"],
            "typical_duration_baseline": 90, "price_band": "budget",
        },
        "ext": {
            "poi_category": "temple", "typical_duration_min": 90,
            "admission_fee_jpy": 700, "best_season": "all",
            "crowd_level_typical": "medium",
            "google_rating": 4.6, "google_review_count": 18000,
        },
        "roles": [{"cluster_id": "kyo_uji_day_trip", "role": "anchor_poi", "sort_order": 0, "is_cluster_anchor": True}],
    },
    {
        "base": {
            "name_zh": "宇治上神社",
            "name_ja": "宇治上神社", "name_en": "Ujigami Shrine",
            "city_code": "uji", "area_name": "宇治",
            "lat": 34.8935, "lng": 135.8118,
            "data_tier": "A", "nearest_station": "宇治",
            "corridor_tags": ["uji"],
            "typical_duration_baseline": 30, "price_band": "free",
        },
        "ext": {
            "poi_category": "shrine", "typical_duration_min": 30,
            "admission_free": True, "best_season": "all",
            "crowd_level_typical": "low",
            "google_rating": 4.4, "google_review_count": 5000,
        },
        "roles": [{"cluster_id": "kyo_uji_day_trip", "role": "secondary_poi", "sort_order": 1}],
    },
    {
        "base": {
            "name_zh": "宇治神社",
            "name_ja": "宇治神社", "name_en": "Uji Shrine",
            "city_code": "uji", "area_name": "宇治",
            "lat": 34.8921, "lng": 135.8108,
            "data_tier": "B", "nearest_station": "宇治",
            "corridor_tags": ["uji"],
            "typical_duration_baseline": 20, "price_band": "free",
        },
        "ext": {
            "poi_category": "shrine", "typical_duration_min": 20,
            "admission_free": True, "best_season": "sakura",
            "crowd_level_typical": "low",
            "google_rating": 4.2, "google_review_count": 2000,
        },
        "roles": [{"cluster_id": "kyo_uji_day_trip", "role": "secondary_poi", "sort_order": 2}],
    },
    {
        "base": {
            "name_zh": "宇治川岛渚",
            "name_ja": "宇治川の橘島・塔の島", "name_en": "Uji River Islets",
            "city_code": "uji", "area_name": "宇治",
            "lat": 34.8907, "lng": 135.8094,
            "data_tier": "B", "nearest_station": "宇治",
            "corridor_tags": ["uji"],
            "typical_duration_baseline": 20, "price_band": "free",
        },
        "ext": {
            "poi_category": "park", "typical_duration_min": 20,
            "admission_free": True, "best_season": "all",
            "crowd_level_typical": "low",
            "google_rating": 4.1, "google_review_count": 1500,
        },
        "roles": [{"cluster_id": "kyo_uji_day_trip", "role": "secondary_poi", "sort_order": 3}],
    },
    # ── 奈良深度走廊 POI ─────────────────────────────────────────────────────
    {
        "base": {
            "name_zh": "春日大社",
            "name_ja": "春日大社", "name_en": "Kasuga Taisha",
            "city_code": "nara", "area_name": "奈良公园",
            "lat": 34.6813, "lng": 135.8491,
            "data_tier": "A", "nearest_station": "近鉄奈良",
            "corridor_tags": ["nara_park"],
            "typical_duration_baseline": 60, "price_band": "budget",
        },
        "ext": {
            "poi_category": "shrine", "typical_duration_min": 60,
            "admission_fee_jpy": 500, "best_season": "all",
            "crowd_level_typical": "medium",
            "google_rating": 4.4, "google_review_count": 15000,
        },
        "roles": [{"cluster_id": "nara_deep_kasuga_kofuku", "role": "anchor_poi", "sort_order": 0, "is_cluster_anchor": True}],
    },
    {
        "base": {
            "name_zh": "兴福寺",
            "name_ja": "興福寺", "name_en": "Kofuku-ji",
            "city_code": "nara", "area_name": "奈良公园",
            "lat": 34.6852, "lng": 135.8320,
            "data_tier": "A", "nearest_station": "近鉄奈良",
            "corridor_tags": ["nara_park"],
            "typical_duration_baseline": 45, "price_band": "budget",
        },
        "ext": {
            "poi_category": "temple", "typical_duration_min": 45,
            "admission_fee_jpy": 700, "best_season": "all",
            "crowd_level_typical": "medium",
            "google_rating": 4.3, "google_review_count": 9000,
        },
        "roles": [
            {"cluster_id": "nara_deep_kasuga_kofuku", "role": "secondary_poi", "sort_order": 1},
            {"cluster_id": "kyo_nara_day_trip", "role": "secondary_poi", "sort_order": 2},
        ],
    },
    {
        "base": {
            "name_zh": "新药师寺",
            "name_ja": "新薬師寺", "name_en": "Shin-Yakushiji",
            "city_code": "nara", "area_name": "奈良公园",
            "lat": 34.6742, "lng": 135.8448,
            "data_tier": "B", "nearest_station": "近鉄奈良",
            "corridor_tags": ["nara_park"],
            "typical_duration_baseline": 40, "price_band": "budget",
        },
        "ext": {
            "poi_category": "temple", "typical_duration_min": 40,
            "admission_fee_jpy": 650, "best_season": "all",
            "crowd_level_typical": "low",
            "google_rating": 4.3, "google_review_count": 1500,
        },
        "roles": [{"cluster_id": "nara_deep_kasuga_kofuku", "role": "secondary_poi", "sort_order": 2}],
    },
    {
        "base": {
            "name_zh": "奈良国立博物馆",
            "name_ja": "奈良国立博物館", "name_en": "Nara National Museum",
            "city_code": "nara", "area_name": "奈良公园",
            "lat": 34.6856, "lng": 135.8367,
            "data_tier": "B", "nearest_station": "近鉄奈良",
            "corridor_tags": ["nara_park"],
            "typical_duration_baseline": 60, "price_band": "budget",
        },
        "ext": {
            "poi_category": "museum", "typical_duration_min": 60,
            "admission_fee_jpy": 700, "best_season": "all",
            "crowd_level_typical": "low",
            "google_rating": 4.3, "google_review_count": 4000,
        },
        "roles": [{"cluster_id": "nara_deep_kasuga_kofuku", "role": "secondary_poi", "sort_order": 3}],
    },
    {
        "base": {
            "name_zh": "元兴寺",
            "name_ja": "元興寺", "name_en": "Gango-ji",
            "city_code": "nara", "area_name": "奈良町",
            "lat": 34.6789, "lng": 135.8318,
            "data_tier": "B", "nearest_station": "近鉄奈良",
            "corridor_tags": ["nara_park"],
            "typical_duration_baseline": 30, "price_band": "budget",
        },
        "ext": {
            "poi_category": "temple", "typical_duration_min": 30,
            "admission_fee_jpy": 500, "best_season": "all",
            "crowd_level_typical": "low",
            "google_rating": 4.1, "google_review_count": 1200,
        },
        "roles": [{"cluster_id": "nara_deep_kasuga_kofuku", "role": "secondary_poi", "sort_order": 4}],
    },
    # ── 大阪补全 POI ─────────────────────────────────────────────────────────
    {
        "base": {
            "name_zh": "海游馆",
            "name_ja": "海遊館", "name_en": "Kaiyukan Aquarium",
            "city_code": "osaka", "area_name": "天保山",
            "lat": 34.6547, "lng": 135.4282,
            "data_tier": "A", "nearest_station": "大阪港",
            "corridor_tags": ["osa_sakurajima"],
            "typical_duration_baseline": 180, "price_band": "mid",
        },
        "ext": {
            "poi_category": "aquarium", "typical_duration_min": 180,
            "admission_fee_jpy": 2400, "best_season": "all",
            "crowd_level_typical": "high",
            "google_rating": 4.4, "google_review_count": 30000,
        },
        "roles": [{"cluster_id": "osa_kaiyukan_tempozan", "role": "anchor_poi", "sort_order": 0, "is_cluster_anchor": True}],
    },
    {
        "base": {
            "name_zh": "天保山大观览车",
            "name_ja": "天保山大観覧車", "name_en": "Tempozan Ferris Wheel",
            "city_code": "osaka", "area_name": "天保山",
            "lat": 34.6558, "lng": 135.4299,
            "data_tier": "B", "nearest_station": "大阪港",
            "corridor_tags": ["osa_sakurajima"],
            "typical_duration_baseline": 30, "price_band": "budget",
        },
        "ext": {
            "poi_category": "attraction", "typical_duration_min": 30,
            "admission_fee_jpy": 900, "best_season": "all",
            "crowd_level_typical": "medium",
            "google_rating": 4.0, "google_review_count": 8000,
        },
        "roles": [{"cluster_id": "osa_kaiyukan_tempozan", "role": "secondary_poi", "sort_order": 1}],
    },
    {
        "base": {
            "name_zh": "大阪市中央公会堂",
            "name_ja": "大阪市中央公会堂", "name_en": "Osaka City Central Public Hall",
            "city_code": "osaka", "area_name": "中之岛",
            "lat": 34.6935, "lng": 135.5064,
            "data_tier": "B", "nearest_station": "なにわ橋",
            "corridor_tags": ["osa_nakanoshima"],
            "typical_duration_baseline": 30, "price_band": "free",
        },
        "ext": {
            "poi_category": "modern_architecture", "typical_duration_min": 30,
            "admission_free": True, "best_season": "all",
            "crowd_level_typical": "low",
            "google_rating": 4.3, "google_review_count": 4000,
        },
        "roles": [{"cluster_id": "osa_nakanoshima_temma", "role": "anchor_poi", "sort_order": 0, "is_cluster_anchor": True}],
    },
    {
        "base": {
            "name_zh": "中之岛公园",
            "name_ja": "中之島公園", "name_en": "Nakanoshima Park",
            "city_code": "osaka", "area_name": "中之岛",
            "lat": 34.6930, "lng": 135.5028,
            "data_tier": "B", "nearest_station": "なにわ橋",
            "corridor_tags": ["osa_nakanoshima"],
            "typical_duration_baseline": 20, "price_band": "free",
        },
        "ext": {
            "poi_category": "park", "typical_duration_min": 20,
            "admission_free": True, "best_season": "spring",
            "crowd_level_typical": "medium",
            "google_rating": 4.1, "google_review_count": 5000,
        },
        "roles": [{"cluster_id": "osa_nakanoshima_temma", "role": "secondary_poi", "sort_order": 1}],
    },
    {
        "base": {
            "name_zh": "大阪天满宫",
            "name_ja": "大阪天満宮", "name_en": "Osaka Tenmangu Shrine",
            "city_code": "osaka", "area_name": "天满",
            "lat": 34.6942, "lng": 135.5108,
            "data_tier": "B", "nearest_station": "南森町",
            "corridor_tags": ["osa_nakanoshima"],
            "typical_duration_baseline": 25, "price_band": "free",
        },
        "ext": {
            "poi_category": "shrine", "typical_duration_min": 25,
            "admission_free": True, "best_season": "all",
            "crowd_level_typical": "low",
            "google_rating": 4.1, "google_review_count": 3000,
        },
        "roles": [{"cluster_id": "osa_nakanoshima_temma", "role": "secondary_poi", "sort_order": 2}],
    },
    {
        "base": {
            "name_zh": "大阪城西之丸庭园",
            "name_ja": "大阪城西の丸庭園", "name_en": "Osaka Castle Nishi-no-maru Garden",
            "city_code": "osaka", "area_name": "大阪城",
            "lat": 34.6882, "lng": 135.5227,
            "data_tier": "B", "nearest_station": "大阪城公園",
            "corridor_tags": ["osa_osakajo"],
            "typical_duration_baseline": 30, "price_band": "budget",
        },
        "ext": {
            "poi_category": "park", "typical_duration_min": 30,
            "admission_fee_jpy": 200, "best_season": "spring",
            "crowd_level_typical": "medium",
            "google_rating": 4.2, "google_review_count": 5500,
        },
        "roles": [{"cluster_id": "osa_osaka_castle_tenmabashi", "role": "secondary_poi", "sort_order": 1}],
    },
    {
        "base": {
            "name_zh": "难波八阪神社",
            "name_ja": "難波八阪神社", "name_en": "Namba Yasaka Shrine",
            "city_code": "osaka", "area_name": "难波",
            "lat": 34.6609, "lng": 135.4998,
            "data_tier": "B", "nearest_station": "なんば",
            "corridor_tags": ["osa_namba"],
            "typical_duration_baseline": 20, "price_band": "free",
        },
        "ext": {
            "poi_category": "shrine", "typical_duration_min": 20,
            "admission_free": True, "best_season": "all",
            "crowd_level_typical": "low",
            "google_rating": 4.3, "google_review_count": 6000,
        },
        "roles": [{"cluster_id": "osa_dotonbori_minami_food", "role": "secondary_poi", "sort_order": 1}],
    },
    {
        "base": {
            "name_zh": "法善寺横丁",
            "name_ja": "法善寺横丁", "name_en": "Hozenji Yokocho",
            "city_code": "osaka", "area_name": "难波",
            "lat": 34.6672, "lng": 135.5025,
            "data_tier": "B", "nearest_station": "なんば",
            "corridor_tags": ["osa_namba"],
            "typical_duration_baseline": 20, "price_band": "free",
        },
        "ext": {
            "poi_category": "historic_street", "typical_duration_min": 20,
            "admission_free": True, "best_season": "all",
            "crowd_level_typical": "medium",
            "google_rating": 4.2, "google_review_count": 7000,
        },
        "roles": [{"cluster_id": "osa_dotonbori_minami_food", "role": "secondary_poi", "sort_order": 2}],
    },
    # ── 神户走廊 POI ─────────────────────────────────────────────────────────
    {
        "base": {
            "name_zh": "北野异人馆街",
            "name_ja": "北野異人館街", "name_en": "Kitano Ijinkan Street",
            "city_code": "kobe", "area_name": "北野",
            "lat": 34.6999, "lng": 135.1892,
            "data_tier": "A", "nearest_station": "三ノ宮",
            "corridor_tags": ["kobe_kitano"],
            "typical_duration_baseline": 90, "price_band": "budget",
        },
        "ext": {
            "poi_category": "historic_district", "typical_duration_min": 90,
            "admission_fee_jpy": 650, "best_season": "all",
            "crowd_level_typical": "medium",
            "google_rating": 4.0, "google_review_count": 10000,
        },
        "roles": [{"cluster_id": "kobe_kitano_nankinmachi", "role": "anchor_poi", "sort_order": 0, "is_cluster_anchor": True}],
    },
    {
        "base": {
            "name_zh": "神户南京町（中华街）",
            "name_ja": "南京町", "name_en": "Nankinmachi Chinatown",
            "city_code": "kobe", "area_name": "元町",
            "lat": 34.6893, "lng": 135.1936,
            "data_tier": "A", "nearest_station": "元町",
            "corridor_tags": ["kobe_kitano"],
            "typical_duration_baseline": 45, "price_band": "budget",
        },
        "ext": {
            "poi_category": "shopping_food", "typical_duration_min": 45,
            "admission_free": True, "best_season": "all",
            "crowd_level_typical": "high",
            "google_rating": 4.1, "google_review_count": 12000,
        },
        "roles": [{"cluster_id": "kobe_kitano_nankinmachi", "role": "secondary_poi", "sort_order": 1}],
    },
    {
        "base": {
            "name_zh": "神户旧居留地",
            "name_ja": "神戸旧居留地", "name_en": "Kobe Old Foreign Settlement",
            "city_code": "kobe", "area_name": "旧居留地",
            "lat": 34.6893, "lng": 135.1951,
            "data_tier": "B", "nearest_station": "三ノ宮",
            "corridor_tags": ["kobe_kitano"],
            "typical_duration_baseline": 30, "price_band": "free",
        },
        "ext": {
            "poi_category": "historic_district", "typical_duration_min": 30,
            "admission_free": True, "best_season": "all",
            "crowd_level_typical": "low",
            "google_rating": 4.1, "google_review_count": 3500,
        },
        "roles": [{"cluster_id": "kobe_kitano_nankinmachi", "role": "secondary_poi", "sort_order": 2}],
    },
    {
        "base": {
            "name_zh": "神户港塔",
            "name_ja": "神戸ポートタワー", "name_en": "Kobe Port Tower",
            "city_code": "kobe", "area_name": "神户港",
            "lat": 34.6840, "lng": 135.1963,
            "data_tier": "B", "nearest_station": "三ノ宮",
            "corridor_tags": ["kobe_kitano"],
            "typical_duration_baseline": 30, "price_band": "budget",
        },
        "ext": {
            "poi_category": "landmark", "typical_duration_min": 30,
            "admission_fee_jpy": 1000, "best_season": "all",
            "crowd_level_typical": "medium",
            "google_rating": 4.0, "google_review_count": 6000,
        },
        "roles": [{"cluster_id": "kobe_kitano_nankinmachi", "role": "secondary_poi", "sort_order": 3}],
    },
    # ── 有马温泉走廊 POI ─────────────────────────────────────────────────────
    {
        "base": {
            "name_zh": "有马温泉·金汤（太阁汤）",
            "name_ja": "太閤の湯殿館", "name_en": "Arima Onsen Taiko no Yudono Museum",
            "city_code": "kobe", "area_name": "有马温泉",
            "lat": 34.7985, "lng": 135.2467,
            "data_tier": "A", "nearest_station": "有馬温泉",
            "corridor_tags": ["arima"],
            "typical_duration_baseline": 120, "price_band": "mid",
        },
        "ext": {
            "poi_category": "onsen", "typical_duration_min": 120,
            "admission_fee_jpy": 800, "best_season": "all",
            "crowd_level_typical": "medium",
            "google_rating": 4.1, "google_review_count": 3000,
        },
        "roles": [{"cluster_id": "arima_onsen_day_trip", "role": "anchor_poi", "sort_order": 0, "is_cluster_anchor": True}],
    },
    {
        "base": {
            "name_zh": "有马温泉街·炭酸泉广场",
            "name_ja": "有馬温泉 炭酸泉源公園", "name_en": "Arima Tansan Spring Park",
            "city_code": "kobe", "area_name": "有马温泉",
            "lat": 34.7990, "lng": 135.2459,
            "data_tier": "B", "nearest_station": "有馬温泉",
            "corridor_tags": ["arima"],
            "typical_duration_baseline": 30, "price_band": "free",
        },
        "ext": {
            "poi_category": "park", "typical_duration_min": 30,
            "admission_free": True, "best_season": "all",
            "crowd_level_typical": "low",
            "google_rating": 4.0, "google_review_count": 2000,
        },
        "roles": [{"cluster_id": "arima_onsen_day_trip", "role": "secondary_poi", "sort_order": 1}],
    },
    # ── 京都岚山补全 POI ─────────────────────────────────────────────────────
    {
        "base": {
            "name_zh": "野宫神社",
            "name_ja": "野宮神社", "name_en": "Nonomiya Shrine",
            "city_code": "kyoto", "area_name": "岚山",
            "lat": 35.0168, "lng": 135.6727,
            "data_tier": "B", "nearest_station": "嵐山",
            "corridor_tags": ["kyo_arashiyama"],
            "typical_duration_baseline": 20, "price_band": "free",
        },
        "ext": {
            "poi_category": "shrine", "typical_duration_min": 20,
            "admission_free": True, "best_season": "all",
            "crowd_level_typical": "medium",
            "google_rating": 4.2, "google_review_count": 6000,
        },
        "roles": [{"cluster_id": "kyo_arashiyama_sagano", "role": "secondary_poi", "sort_order": 3}],
    },
    {
        "base": {
            "name_zh": "大河内山庄",
            "name_ja": "大河内山荘", "name_en": "Okochi Sanso Villa",
            "city_code": "kyoto", "area_name": "岚山",
            "lat": 35.0175, "lng": 135.6706,
            "data_tier": "B", "nearest_station": "嵐山",
            "corridor_tags": ["kyo_arashiyama"],
            "typical_duration_baseline": 40, "price_band": "budget",
        },
        "ext": {
            "poi_category": "garden", "typical_duration_min": 40,
            "admission_fee_jpy": 1000, "best_season": "all",
            "crowd_level_typical": "low",
            "google_rating": 4.4, "google_review_count": 2500,
        },
        "roles": [{"cluster_id": "kyo_arashiyama_sagano", "role": "secondary_poi", "sort_order": 4}],
    },
    {
        "base": {
            "name_zh": "常寂光寺",
            "name_ja": "常寂光寺", "name_en": "Jojakko-ji",
            "city_code": "kyoto", "area_name": "岚山",
            "lat": 35.0198, "lng": 135.6686,
            "data_tier": "B", "nearest_station": "嵐山",
            "corridor_tags": ["kyo_arashiyama"],
            "typical_duration_baseline": 30, "price_band": "budget",
        },
        "ext": {
            "poi_category": "temple", "typical_duration_min": 30,
            "admission_fee_jpy": 500, "best_season": "autumn",
            "crowd_level_typical": "low",
            "google_rating": 4.3, "google_review_count": 3000,
        },
        "roles": [{"cluster_id": "kyo_arashiyama_sagano", "role": "secondary_poi", "sort_order": 5}],
    },
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 餐厅实体（扩充）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RESTAURANTS = [
    # ── 宇治餐厅 ─────────────────────────────────────────────────────────────
    {
        "base": {
            "name_zh": "中村藤吉本店（宇治）",
            "name_ja": "中村藤吉本店", "name_en": "Nakamura Tokichi Honten",
            "city_code": "uji", "area_name": "宇治",
            "lat": 34.8881, "lng": 135.8062,
            "data_tier": "A", "nearest_station": "宇治",
            "corridor_tags": ["uji"], "price_band": "mid",
        },
        "ext": {
            "cuisine_type": "matcha_cafe",
            "tabelog_score": 3.85,
            "requires_reservation": False,
            "budget_lunch_jpy": 1800,
            "budget_dinner_jpy": 2500,
            "has_english_menu": True,
        },
        "roles": [{"cluster_id": "kyo_uji_day_trip", "role": "meal_destination", "sort_order": 0}],
    },
    {
        "base": {
            "name_zh": "茶寮都路里 宇治本店",
            "name_ja": "茶寮都路里 宇治本店", "name_en": "Saryo Tsujiri Uji",
            "city_code": "uji", "area_name": "宇治",
            "lat": 34.8876, "lng": 135.8057,
            "data_tier": "B", "nearest_station": "宇治",
            "corridor_tags": ["uji"], "price_band": "mid",
        },
        "ext": {
            "cuisine_type": "matcha_cafe",
            "budget_lunch_jpy": 1500,
            "has_english_menu": True,
        },
        "roles": [{"cluster_id": "kyo_uji_day_trip", "role": "meal_route", "sort_order": 1}],
    },
    {
        "base": {
            "name_zh": "辻利兵卫本店（宇治）",
            "name_ja": "辻利兵衛本店", "name_en": "Tsujiribee Honten",
            "city_code": "uji", "area_name": "宇治",
            "lat": 34.8869, "lng": 135.8053,
            "data_tier": "B", "nearest_station": "宇治",
            "corridor_tags": ["uji"], "price_band": "budget",
        },
        "ext": {
            "cuisine_type": "matcha_cafe",
            "budget_lunch_jpy": 800,
            "has_english_menu": True,
        },
        "roles": [{"cluster_id": "kyo_uji_day_trip", "role": "meal_route", "sort_order": 2}],
    },
    # ── 京都枯山水/庭园走廊餐厅 ──────────────────────────────────────────────
    {
        "base": {
            "name_zh": "南禅寺 顺正（汤豆腐）",
            "name_ja": "南禅寺 順正", "name_en": "Nanzenji Junsei (Yudofu)",
            "city_code": "kyoto", "area_name": "冈崎",
            "lat": 35.0112, "lng": 135.7925,
            "data_tier": "A", "nearest_station": "蹴上",
            "corridor_tags": ["kyo_okazaki"], "price_band": "mid",
        },
        "ext": {
            "cuisine_type": "yudofu",
            "tabelog_score": 3.72,
            "requires_reservation": True,
            "reservation_difficulty": "easy",
            "budget_lunch_jpy": 3500,
            "budget_dinner_jpy": 5000,
            "has_english_menu": True,
        },
        "roles": [
            {"cluster_id": "kyo_philosopher_path_nanzen", "role": "meal_destination", "sort_order": 0},
            {"cluster_id": "kyo_eikando_shinnyodo", "role": "meal_destination", "sort_order": 0},
        ],
    },
    {
        "base": {
            "name_zh": "奥丹 清水（汤豆腐老铺）",
            "name_ja": "奥丹清水", "name_en": "Okutan Kiyomizu (Yudofu)",
            "city_code": "kyoto", "area_name": "东山",
            "lat": 34.9982, "lng": 135.7852,
            "data_tier": "A", "nearest_station": "清水五条",
            "corridor_tags": ["kyo_higashiyama"], "price_band": "mid",
        },
        "ext": {
            "cuisine_type": "yudofu",
            "tabelog_score": 3.65,
            "requires_reservation": False,
            "budget_lunch_jpy": 3300,
            "has_english_menu": False,
        },
        "roles": [{"cluster_id": "kyo_higashiyama_gion_classic", "role": "meal_destination", "sort_order": 1}],
    },
    {
        "base": {
            "name_zh": "大德寺一久（精进料理）",
            "name_ja": "大徳寺一久", "name_en": "Daitokuji Ikkyu (Shojin Ryori)",
            "city_code": "kyoto", "area_name": "紫野",
            "lat": 35.0452, "lng": 135.7448,
            "data_tier": "A", "nearest_station": "大徳寺前(バス)",
            "corridor_tags": ["kyo_zen_garden"], "price_band": "premium",
        },
        "ext": {
            "cuisine_type": "shojin_ryori",
            "tabelog_score": 3.80,
            "requires_reservation": True,
            "reservation_difficulty": "medium",
            "budget_lunch_jpy": 5500,
            "budget_dinner_jpy": 8000,
            "has_english_menu": False,
        },
        "roles": [{"cluster_id": "kyo_zen_garden_circuit", "role": "meal_destination", "sort_order": 0}],
    },
    {
        "base": {
            "name_zh": "东福寺 吉祥菴（精进料理）",
            "name_ja": "吉祥菴", "name_en": "Kissho-an (Shojin Ryori Tofukuji)",
            "city_code": "kyoto", "area_name": "伏见北",
            "lat": 34.9795, "lng": 135.7738,
            "data_tier": "B", "nearest_station": "東福寺",
            "corridor_tags": ["kyo_zen_garden"], "price_band": "mid",
        },
        "ext": {
            "cuisine_type": "shojin_ryori",
            "budget_lunch_jpy": 2800,
            "has_english_menu": False,
        },
        "roles": [{"cluster_id": "kyo_zen_garden_circuit", "role": "meal_route", "sort_order": 1}],
    },
    # ── 京都各走廊补充餐厅 ───────────────────────────────────────────────────
    {
        "base": {
            "name_zh": "嵐山よしむら（岚山荞麦面）",
            "name_ja": "嵐山よしむら", "name_en": "Arashiyama Yoshimura Soba",
            "city_code": "kyoto", "area_name": "岚山",
            "lat": 35.0100, "lng": 135.6783,
            "data_tier": "A", "nearest_station": "嵐山",
            "corridor_tags": ["kyo_arashiyama"], "price_band": "mid",
        },
        "ext": {
            "cuisine_type": "soba",
            "tabelog_score": 3.62,
            "budget_lunch_jpy": 1500,
            "has_english_menu": True,
        },
        "roles": [{"cluster_id": "kyo_arashiyama_sagano", "role": "meal_destination", "sort_order": 1}],
    },
    {
        "base": {
            "name_zh": "天龙寺 篩月（精进料理）",
            "name_ja": "天龍寺 篩月", "name_en": "Tenryuji Shigetsu (Shojin Ryori)",
            "city_code": "kyoto", "area_name": "岚山",
            "lat": 35.0153, "lng": 135.6747,
            "data_tier": "A", "nearest_station": "嵐山",
            "corridor_tags": ["kyo_arashiyama"], "price_band": "premium",
        },
        "ext": {
            "cuisine_type": "shojin_ryori",
            "tabelog_score": 3.75,
            "requires_reservation": True,
            "reservation_difficulty": "easy",
            "budget_lunch_jpy": 4800,
            "has_english_menu": True,
        },
        "roles": [{"cluster_id": "kyo_arashiyama_sagano", "role": "meal_destination", "sort_order": 2}],
    },
    {
        "base": {
            "name_zh": "伏见稻荷 にしむら亭（稻荷寿司）",
            "name_ja": "にしむら亭", "name_en": "Nishimuratei Fushimi",
            "city_code": "kyoto", "area_name": "伏见",
            "lat": 34.9672, "lng": 135.7720,
            "data_tier": "B", "nearest_station": "稲荷",
            "corridor_tags": ["kyo_fushimi"], "price_band": "budget",
        },
        "ext": {
            "cuisine_type": "inari_sushi",
            "budget_lunch_jpy": 1000,
            "has_english_menu": True,
        },
        "roles": [{"cluster_id": "kyo_fushimi_inari", "role": "meal_route", "sort_order": 1}],
    },
    {
        "base": {
            "name_zh": "黄桜 酒场KAPPA（伏见酒藏）",
            "name_ja": "黄桜 酒場KAPPA", "name_en": "Kizakura Kappa Country Brewery",
            "city_code": "kyoto", "area_name": "伏见",
            "lat": 34.9395, "lng": 135.7623,
            "data_tier": "B", "nearest_station": "中書島",
            "corridor_tags": ["kyo_fushimi"], "price_band": "mid",
        },
        "ext": {
            "cuisine_type": "izakaya",
            "budget_lunch_jpy": 1500,
            "budget_dinner_jpy": 2500,
            "has_english_menu": True,
        },
        "roles": [{"cluster_id": "kyo_fushimi_sake_town", "role": "meal_destination", "sort_order": 0}],
    },
    {
        "base": {
            "name_zh": "金阁寺周边·养老轩（京料理）",
            "name_ja": "養老軒", "name_en": "Yoroken (Kyoto Cuisine near Kinkakuji)",
            "city_code": "kyoto", "area_name": "衣笠",
            "lat": 35.0390, "lng": 135.7299,
            "data_tier": "B", "nearest_station": "金閣寺道(バス)",
            "corridor_tags": ["kyo_kinugasa"], "price_band": "mid",
        },
        "ext": {
            "cuisine_type": "kyoto_cuisine",
            "budget_lunch_jpy": 2000,
            "has_english_menu": False,
        },
        "roles": [{"cluster_id": "kyo_kinkakuji_kinugasa", "role": "meal_route", "sort_order": 0}],
    },
    {
        "base": {
            "name_zh": "先斗町 魯ビン（京都鸭肉料理）",
            "name_ja": "先斗町 魯ビン", "name_en": "Pontocho Robin (Kamo Ryori)",
            "city_code": "kyoto", "area_name": "先斗町",
            "lat": 35.0055, "lng": 135.7693,
            "data_tier": "A", "nearest_station": "祇園四条",
            "corridor_tags": ["kyo_kawaramachi", "kyo_gion"], "price_band": "premium",
        },
        "ext": {
            "cuisine_type": "kyoto_cuisine",
            "tabelog_score": 3.68,
            "requires_reservation": True,
            "reservation_difficulty": "medium",
            "budget_dinner_jpy": 7000,
            "has_english_menu": True,
        },
        "roles": [{"cluster_id": "kyo_higashiyama_gion_classic", "role": "meal_destination", "sort_order": 2}],
    },
    {
        "base": {
            "name_zh": "京都站 伊势丹 拉面小路",
            "name_ja": "京都拉麺小路", "name_en": "Kyoto Ramen Koji (Kyoto Station)",
            "city_code": "kyoto", "area_name": "京都站",
            "lat": 34.9856, "lng": 135.7584,
            "data_tier": "B", "nearest_station": "京都",
            "corridor_tags": ["kawaramachi"], "price_band": "budget",
        },
        "ext": {
            "cuisine_type": "ramen",
            "budget_lunch_jpy": 1200,
            "has_english_menu": True,
        },
        "roles": [{"cluster_id": "kyo_katsura_modern_arch", "role": "meal_route", "sort_order": 0}],
    },
    {
        "base": {
            "name_zh": "冈崎 瓢亭别馆（朝粥·京懷石）",
            "name_ja": "瓢亭 別館", "name_en": "Hyotei Bekkan (Kyoto Kaiseki)",
            "city_code": "kyoto", "area_name": "冈崎",
            "lat": 35.0143, "lng": 135.7898,
            "data_tier": "A", "nearest_station": "蹴上",
            "corridor_tags": ["kyo_okazaki"], "price_band": "premium",
        },
        "ext": {
            "cuisine_type": "kaiseki",
            "tabelog_score": 4.05,
            "requires_reservation": True,
            "reservation_difficulty": "hard",
            "budget_lunch_jpy": 8000,
            "budget_dinner_jpy": 20000,
            "has_english_menu": True,
        },
        "roles": [{"cluster_id": "kyo_philosopher_path_nanzen", "role": "meal_destination", "sort_order": 1}],
    },
    # ── 奈良餐厅补充 ─────────────────────────────────────────────────────────
    {
        "base": {
            "name_zh": "奈良 春鹿 酒蔵直送店",
            "name_ja": "春鹿 今西清兵衛商店", "name_en": "Harushika Sake Tasting Nara",
            "city_code": "nara", "area_name": "奈良町",
            "lat": 34.6807, "lng": 135.8295,
            "data_tier": "B", "nearest_station": "近鉄奈良",
            "corridor_tags": ["nara_park"], "price_band": "budget",
        },
        "ext": {
            "cuisine_type": "sake_tasting",
            "budget_lunch_jpy": 500,
            "has_english_menu": True,
        },
        "roles": [{"cluster_id": "nara_deep_kasuga_kofuku", "role": "meal_route", "sort_order": 0}],
    },
    {
        "base": {
            "name_zh": "奈良 柿叶寿司 平宗本店",
            "name_ja": "柿の葉すし 平宗 本店", "name_en": "Kakinoha-zushi Hirasou Honten",
            "city_code": "nara", "area_name": "奈良町",
            "lat": 34.6798, "lng": 135.8286,
            "data_tier": "A", "nearest_station": "近鉄奈良",
            "corridor_tags": ["nara_park"], "price_band": "mid",
        },
        "ext": {
            "cuisine_type": "nara_cuisine",
            "tabelog_score": 3.70,
            "budget_lunch_jpy": 2200,
            "has_english_menu": True,
        },
        "roles": [
            {"cluster_id": "kyo_nara_day_trip", "role": "meal_destination", "sort_order": 1},
            {"cluster_id": "nara_deep_kasuga_kofuku", "role": "meal_destination", "sort_order": 0},
        ],
    },
    {
        "base": {
            "name_zh": "奈良 麦とろ（奈良传统麦饭）",
            "name_ja": "麦とろ", "name_en": "Mugitoro Nara",
            "city_code": "nara", "area_name": "奈良公园",
            "lat": 34.6848, "lng": 135.8380,
            "data_tier": "B", "nearest_station": "近鉄奈良",
            "corridor_tags": ["nara_park"], "price_band": "mid",
        },
        "ext": {
            "cuisine_type": "nara_cuisine",
            "budget_lunch_jpy": 1800,
            "has_english_menu": False,
        },
        "roles": [{"cluster_id": "nara_deep_kasuga_kofuku", "role": "meal_route", "sort_order": 1}],
    },
    # ── 大阪补充餐厅 ─────────────────────────────────────────────────────────
    {
        "base": {
            "name_zh": "黑门市场 鱼伊 海鲜丼",
            "name_ja": "魚伊 黒門市場店", "name_en": "Uoi Kuromon Market Kaisendon",
            "city_code": "osaka", "area_name": "难波",
            "lat": 34.6697, "lng": 135.5066,
            "data_tier": "A", "nearest_station": "日本橋",
            "corridor_tags": ["osa_namba"], "price_band": "mid",
        },
        "ext": {
            "cuisine_type": "kaisendon",
            "budget_lunch_jpy": 2500,
            "has_english_menu": True,
        },
        "roles": [{"cluster_id": "osa_dotonbori_minami_food", "role": "meal_destination", "sort_order": 2}],
    },
    {
        "base": {
            "name_zh": "大阪 鹤桥 焼肉 空",
            "name_ja": "焼肉 空 鶴橋本店", "name_en": "Yakiniku Sora Tsuruhashi",
            "city_code": "osaka", "area_name": "鹤桥",
            "lat": 34.6660, "lng": 135.5282,
            "data_tier": "B", "nearest_station": "鶴橋",
            "corridor_tags": ["osa_namba"], "price_band": "mid",
        },
        "ext": {
            "cuisine_type": "yakiniku",
            "budget_dinner_jpy": 3000,
            "has_english_menu": False,
        },
        "roles": [{"cluster_id": "osa_dotonbori_minami_food", "role": "meal_destination", "sort_order": 3}],
    },
    {
        "base": {
            "name_zh": "大阪 ニューライト（老铺洋食）",
            "name_ja": "ニューライト", "name_en": "New Light (Osaka Yoshoku)",
            "city_code": "osaka", "area_name": "难波",
            "lat": 34.6685, "lng": 135.5010,
            "data_tier": "B", "nearest_station": "なんば",
            "corridor_tags": ["osa_namba"], "price_band": "budget",
        },
        "ext": {
            "cuisine_type": "yoshoku",
            "budget_lunch_jpy": 1200,
            "has_english_menu": False,
        },
        "roles": [{"cluster_id": "osa_shinsekai_tenno", "role": "meal_route", "sort_order": 1}],
    },
    {
        "base": {
            "name_zh": "大阪城 中之岛 ラ・シェット（法式午市）",
            "name_ja": "ラ・シェット", "name_en": "La Chette (French Lunch Nakanoshima)",
            "city_code": "osaka", "area_name": "中之岛",
            "lat": 34.6938, "lng": 135.5072,
            "data_tier": "B", "nearest_station": "なにわ橋",
            "corridor_tags": ["osa_nakanoshima"], "price_band": "mid",
        },
        "ext": {
            "cuisine_type": "french",
            "budget_lunch_jpy": 2000,
            "has_english_menu": True,
        },
        "roles": [{"cluster_id": "osa_nakanoshima_temma", "role": "meal_destination", "sort_order": 0}],
    },
    {
        "base": {
            "name_zh": "天满 立吞焼鸟 鳥おか",
            "name_ja": "立吞み 鳥おか 天満店", "name_en": "Torioka Tachinom Temma",
            "city_code": "osaka", "area_name": "天满",
            "lat": 34.6940, "lng": 135.5122,
            "data_tier": "B", "nearest_station": "天満",
            "corridor_tags": ["osa_nakanoshima"], "price_band": "budget",
        },
        "ext": {
            "cuisine_type": "yakitori",
            "budget_dinner_jpy": 1500,
            "has_english_menu": False,
        },
        "roles": [{"cluster_id": "osa_nakanoshima_temma", "role": "meal_route", "sort_order": 1}],
    },
    {
        "base": {
            "name_zh": "大阪城 むぎとオリーブ（天满桥拉面）",
            "name_ja": "むぎとオリーブ 天満橋店", "name_en": "Mugi to Olive Temmabashi",
            "city_code": "osaka", "area_name": "天满桥",
            "lat": 34.6918, "lng": 135.5158,
            "data_tier": "B", "nearest_station": "天満橋",
            "corridor_tags": ["osa_osakajo"], "price_band": "budget",
        },
        "ext": {
            "cuisine_type": "ramen",
            "tabelog_score": 3.75,
            "budget_lunch_jpy": 1300,
            "has_english_menu": False,
        },
        "roles": [{"cluster_id": "osa_osaka_castle_tenmabashi", "role": "meal_route", "sort_order": 0}],
    },
    {
        "base": {
            "name_zh": "海游馆餐厅 ベイサイドダイニング",
            "name_ja": "ベイサイドダイニング", "name_en": "Bayside Dining Kaiyukan",
            "city_code": "osaka", "area_name": "天保山",
            "lat": 34.6549, "lng": 135.4285,
            "data_tier": "B", "nearest_station": "大阪港",
            "corridor_tags": ["osa_sakurajima"], "price_band": "mid",
        },
        "ext": {
            "cuisine_type": "family_restaurant",
            "budget_lunch_jpy": 1800,
            "has_english_menu": True,
        },
        "roles": [{"cluster_id": "osa_kaiyukan_tempozan", "role": "meal_route", "sort_order": 0}],
    },
    # ── 神户餐厅 ─────────────────────────────────────────────────────────────
    {
        "base": {
            "name_zh": "神户 モーリヤ（神户牛扒老铺）",
            "name_ja": "モーリヤ 本店", "name_en": "Mouriya Honten (Kobe Beef)",
            "city_code": "kobe", "area_name": "旧居留地",
            "lat": 34.6888, "lng": 135.1939,
            "data_tier": "A", "nearest_station": "三ノ宮",
            "corridor_tags": ["kobe_kitano"], "price_band": "premium",
        },
        "ext": {
            "cuisine_type": "kobe_beef",
            "tabelog_score": 3.82,
            "requires_reservation": True,
            "reservation_difficulty": "easy",
            "budget_lunch_jpy": 6000,
            "budget_dinner_jpy": 12000,
            "has_english_menu": True,
        },
        "roles": [{"cluster_id": "kobe_kitano_nankinmachi", "role": "meal_destination", "sort_order": 0}],
    },
    {
        "base": {
            "name_zh": "神户 南京町 老祥記（豚まん）",
            "name_ja": "老祥記", "name_en": "Roshouki (Niku-man Nankinmachi)",
            "city_code": "kobe", "area_name": "元町",
            "lat": 34.6895, "lng": 135.1938,
            "data_tier": "B", "nearest_station": "元町",
            "corridor_tags": ["kobe_kitano"], "price_band": "budget",
        },
        "ext": {
            "cuisine_type": "chinese",
            "budget_lunch_jpy": 300,
            "has_english_menu": False,
        },
        "roles": [{"cluster_id": "kobe_kitano_nankinmachi", "role": "meal_route", "sort_order": 1}],
    },
    {
        "base": {
            "name_zh": "神户 イカリヤ食堂（神户洋食）",
            "name_ja": "イカリヤ食堂", "name_en": "Ikariya Shokudo (Kobe Yoshoku)",
            "city_code": "kobe", "area_name": "北野",
            "lat": 34.6990, "lng": 135.1901,
            "data_tier": "B", "nearest_station": "三ノ宮",
            "corridor_tags": ["kobe_kitano"], "price_band": "budget",
        },
        "ext": {
            "cuisine_type": "yoshoku",
            "budget_lunch_jpy": 1200,
            "has_english_menu": False,
        },
        "roles": [{"cluster_id": "kobe_kitano_nankinmachi", "role": "meal_route", "sort_order": 2}],
    },
    # ── 有马温泉餐厅 ─────────────────────────────────────────────────────────
    {
        "base": {
            "name_zh": "有马温泉 陶泉·御所坊（温泉旅馆料理）",
            "name_ja": "陶泉 御所坊", "name_en": "Tousen Goshoboh Arima Onsen",
            "city_code": "kobe", "area_name": "有马温泉",
            "lat": 34.7988, "lng": 135.2462,
            "data_tier": "A", "nearest_station": "有馬温泉",
            "corridor_tags": ["arima"], "price_band": "premium",
        },
        "ext": {
            "cuisine_type": "kaiseki",
            "requires_reservation": True,
            "reservation_difficulty": "medium",
            "budget_lunch_jpy": 8000,
            "has_english_menu": False,
        },
        "roles": [{"cluster_id": "arima_onsen_day_trip", "role": "meal_destination", "sort_order": 0}],
    },
    {
        "base": {
            "name_zh": "有马温泉 にし村（有马料理）",
            "name_ja": "有馬温泉 にし村", "name_en": "Nishimura Arima Onsen",
            "city_code": "kobe", "area_name": "有马温泉",
            "lat": 34.7982, "lng": 135.2470,
            "data_tier": "B", "nearest_station": "有馬温泉",
            "corridor_tags": ["arima"], "price_band": "mid",
        },
        "ext": {
            "cuisine_type": "japanese",
            "budget_lunch_jpy": 3000,
            "has_english_menu": False,
        },
        "roles": [{"cluster_id": "arima_onsen_day_trip", "role": "meal_route", "sort_order": 1}],
    },
    # ── 京都·河原町/四条区域 ─────────────────────────────────────────────────
    {
        "base": {
            "name_zh": "京都 イノダコーヒー本店",
            "name_ja": "イノダコーヒ本店", "name_en": "Inoda Coffee Honten",
            "city_code": "kyoto", "area_name": "河原町",
            "lat": 35.0077, "lng": 135.7628,
            "data_tier": "A", "nearest_station": "烏丸",
            "corridor_tags": ["kyo_kawaramachi"], "price_band": "budget",
        },
        "ext": {
            "cuisine_type": "cafe",
            "tabelog_score": 3.70,
            "budget_lunch_jpy": 1200,
            "has_english_menu": True,
        },
        "roles": [{"cluster_id": "kyo_nijo_nishijin", "role": "meal_route", "sort_order": 0}],
    },
    {
        "base": {
            "name_zh": "京都 三嶋亭（老铺すき焼き）",
            "name_ja": "三嶋亭", "name_en": "Mishimatei (Sukiyaki Kyoto)",
            "city_code": "kyoto", "area_name": "河原町",
            "lat": 35.0038, "lng": 135.7661,
            "data_tier": "A", "nearest_station": "四条",
            "corridor_tags": ["kyo_kawaramachi"], "price_band": "premium",
        },
        "ext": {
            "cuisine_type": "sukiyaki",
            "tabelog_score": 3.95,
            "requires_reservation": True,
            "reservation_difficulty": "medium",
            "budget_dinner_jpy": 12000,
            "has_english_menu": True,
        },
        "roles": [{"cluster_id": "kyo_higashiyama_gion_classic", "role": "meal_destination", "sort_order": 3}],
    },
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 酒店实体（扩充）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HOTELS = [
    # ── 京都补充 ─────────────────────────────────────────────────────────────
    {
        "base": {
            "name_zh": "京都悠悠居（町家改造小宿）",
            "name_ja": "町家ホテル 悠悠居", "name_en": "Kyoto Machiya Hotel Yuyukyo",
            "city_code": "kyoto", "area_name": "祇园",
            "lat": 35.0030, "lng": 135.7771,
            "data_tier": "B", "nearest_station": "祇園四条",
            "corridor_tags": ["kyo_higashiyama", "kyo_gion"],
            "price_band": "premium",
        },
        "ext": {
            "hotel_type": "machiya", "star_rating": 3.0,
            "room_count": 10,
            "check_in_time": "16:00", "check_out_time": "11:00",
            "amenities": ["onsen_bath"],
            "price_tier": "premium",
            "typical_price_min_jpy": 22000,
            "google_rating": 4.6, "booking_score": 9.2,
        },
        "roles": [{"cluster_id": None, "role": "hotel_anchor", "sort_order": 0}],
    },
    {
        "base": {
            "name_zh": "京都站 相铁GRAND FRESA（京都站前）",
            "name_ja": "相鉄グランドフレッサ京都", "name_en": "Sotetsu Grand Fresa Kyoto",
            "city_code": "kyoto", "area_name": "京都站",
            "lat": 34.9860, "lng": 135.7582,
            "data_tier": "A", "nearest_station": "京都",
            "corridor_tags": ["kyo_kawaramachi"],
            "price_band": "mid",
        },
        "ext": {
            "hotel_type": "business", "star_rating": 3.5,
            "room_count": 296,
            "check_in_time": "15:00", "check_out_time": "11:00",
            "amenities": ["breakfast", "fitness"],
            "is_family_friendly": True,
            "price_tier": "mid",
            "typical_price_min_jpy": 10000,
            "google_rating": 4.2, "booking_score": 8.5,
        },
        "roles": [{"cluster_id": None, "role": "hotel_anchor", "sort_order": 0}],
    },
    {
        "base": {
            "name_zh": "京都 The Thousand Kyoto（京都站直结）",
            "name_ja": "ザ・サウザンド キョウト", "name_en": "The Thousand Kyoto",
            "city_code": "kyoto", "area_name": "京都站",
            "lat": 34.9853, "lng": 135.7589,
            "data_tier": "A", "nearest_station": "京都",
            "corridor_tags": ["kyo_kawaramachi"],
            "price_band": "premium",
        },
        "ext": {
            "hotel_type": "luxury", "star_rating": 5.0,
            "room_count": 218,
            "check_in_time": "15:00", "check_out_time": "12:00",
            "amenities": ["breakfast", "fitness", "spa", "concierge"],
            "is_family_friendly": True,
            "price_tier": "premium",
            "typical_price_min_jpy": 28000,
            "google_rating": 4.5, "booking_score": 9.1,
        },
        "roles": [{"cluster_id": None, "role": "hotel_anchor", "sort_order": 0}],
    },
    # ── 大阪补充 ─────────────────────────────────────────────────────────────
    {
        "base": {
            "name_zh": "大阪 Cross Hotel大阪（心斋桥）",
            "name_ja": "クロスホテル大阪", "name_en": "Cross Hotel Osaka",
            "city_code": "osaka", "area_name": "心斋桥",
            "lat": 34.6700, "lng": 135.5009,
            "data_tier": "A", "nearest_station": "なんば",
            "corridor_tags": ["osa_namba"],
            "price_band": "mid",
        },
        "ext": {
            "hotel_type": "business", "star_rating": 3.5,
            "room_count": 225,
            "check_in_time": "15:00", "check_out_time": "11:00",
            "amenities": ["breakfast", "bath"],
            "is_family_friendly": True,
            "price_tier": "mid",
            "typical_price_min_jpy": 11000,
            "google_rating": 4.2, "booking_score": 8.4,
        },
        "roles": [{"cluster_id": None, "role": "hotel_anchor", "sort_order": 0}],
    },
    {
        "base": {
            "name_zh": "大阪 コンラッド大阪（中之岛）",
            "name_ja": "コンラッド大阪", "name_en": "Conrad Osaka",
            "city_code": "osaka", "area_name": "中之岛",
            "lat": 34.6936, "lng": 135.5062,
            "data_tier": "A", "nearest_station": "肥後橋",
            "corridor_tags": ["osa_nakanoshima"],
            "price_band": "premium",
        },
        "ext": {
            "hotel_type": "luxury", "star_rating": 5.0,
            "room_count": 225,
            "check_in_time": "15:00", "check_out_time": "12:00",
            "amenities": ["breakfast", "fitness", "pool", "spa", "concierge"],
            "is_family_friendly": True,
            "price_tier": "premium",
            "typical_price_min_jpy": 35000,
            "google_rating": 4.6, "booking_score": 9.3,
        },
        "roles": [{"cluster_id": None, "role": "hotel_anchor", "sort_order": 0}],
    },
    # ── 神户 ─────────────────────────────────────────────────────────────────
    {
        "base": {
            "name_zh": "神户 ANAクラウンプラザ（三宫）",
            "name_ja": "ANAクラウンプラザホテル神戸", "name_en": "ANA Crowne Plaza Kobe",
            "city_code": "kobe", "area_name": "三宫",
            "lat": 34.6962, "lng": 135.1953,
            "data_tier": "A", "nearest_station": "三ノ宮",
            "corridor_tags": ["kobe_kitano"],
            "price_band": "premium",
        },
        "ext": {
            "hotel_type": "business", "star_rating": 4.0,
            "room_count": 592,
            "check_in_time": "15:00", "check_out_time": "12:00",
            "amenities": ["breakfast", "fitness", "pool", "concierge"],
            "is_family_friendly": True,
            "price_tier": "premium",
            "typical_price_min_jpy": 16000,
            "google_rating": 4.3, "booking_score": 8.7,
        },
        "roles": [{"cluster_id": None, "role": "hotel_anchor", "sort_order": 0}],
    },
    # ── 奈良 ─────────────────────────────────────────────────────────────────
    {
        "base": {
            "name_zh": "奈良 奈良飯店（奈良公园经典老铺）",
            "name_ja": "奈良ホテル", "name_en": "Nara Hotel",
            "city_code": "nara", "area_name": "奈良公园",
            "lat": 34.6853, "lng": 135.8418,
            "data_tier": "A", "nearest_station": "近鉄奈良",
            "corridor_tags": ["nara_park"],
            "price_band": "premium",
        },
        "ext": {
            "hotel_type": "ryokan_western", "star_rating": 4.5,
            "room_count": 139,
            "check_in_time": "14:00", "check_out_time": "11:00",
            "amenities": ["breakfast", "concierge", "garden"],
            "is_family_friendly": True,
            "price_tier": "premium",
            "typical_price_min_jpy": 20000,
            "google_rating": 4.4, "booking_score": 8.9,
        },
        "roles": [{"cluster_id": None, "role": "hotel_anchor", "sort_order": 0}],
    },
    # ── 宇治 ─────────────────────────────────────────────────────────────────
    {
        "base": {
            "name_zh": "宇治 花やしき浮舟园（宇治川畔温泉旅馆）",
            "name_ja": "花やしき浮舟園", "name_en": "Hanayashiki Ukifuneen",
            "city_code": "uji", "area_name": "宇治",
            "lat": 34.8902, "lng": 135.8106,
            "data_tier": "B", "nearest_station": "宇治",
            "corridor_tags": ["uji"],
            "price_band": "premium",
        },
        "ext": {
            "hotel_type": "ryokan", "star_rating": 4.0,
            "room_count": 40,
            "check_in_time": "15:00", "check_out_time": "11:00",
            "amenities": ["breakfast", "onsen_bath", "dinner"],
            "price_tier": "premium",
            "typical_price_min_jpy": 25000,
            "google_rating": 4.5, "booking_score": 9.0,
        },
        "roles": [{"cluster_id": None, "role": "hotel_anchor", "sort_order": 0}],
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 辅助函数（与 seed_kansai_entities.py 相同逻辑）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _find_or_create_entity(session, base_data, entity_type):
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
    entity = EntityBase(entity_id=entity_id, entity_type=entity_type, **base_data)
    session.add(entity)
    await session.flush()
    return entity_id, True


async def _create_ext(session, entity_id, ext_data, model_class):
    ext = model_class(entity_id=entity_id, **ext_data)
    session.add(ext)


async def _create_roles(session, entity_id, roles):
    for r in roles:
        where_clauses = [
            CircleEntityRole.circle_id == CIRCLE_ID,
            CircleEntityRole.entity_id == entity_id,
            CircleEntityRole.role == r["role"],
        ]
        if r.get("cluster_id"):
            where_clauses.append(CircleEntityRole.cluster_id == r["cluster_id"])
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
    stats = {"poi_new": 0, "poi_skip": 0, "hotel_new": 0, "hotel_skip": 0, "rest_new": 0, "rest_skip": 0}

    async with AsyncSessionLocal() as session:
        logger.info("=== Seeding Extended POIs (%d) ===", len(POIS))
        for item in POIS:
            eid, is_new = await _find_or_create_entity(session, item["base"], "poi")
            if is_new:
                await _create_ext(session, eid, item["ext"], Poi)
                stats["poi_new"] += 1
                logger.info("  NEW  poi: %s", item["base"]["name_zh"])
            else:
                stats["poi_skip"] += 1
            await _create_roles(session, eid, item["roles"])
        await session.flush()

        logger.info("=== Seeding Extended Hotels (%d) ===", len(HOTELS))
        for item in HOTELS:
            eid, is_new = await _find_or_create_entity(session, item["base"], "hotel")
            if is_new:
                await _create_ext(session, eid, item["ext"], Hotel)
                stats["hotel_new"] += 1
                logger.info("  NEW  hotel: %s", item["base"]["name_zh"])
            else:
                stats["hotel_skip"] += 1
            await _create_roles(session, eid, item["roles"])
        await session.flush()

        logger.info("=== Seeding Extended Restaurants (%d) ===", len(RESTAURANTS))
        for item in RESTAURANTS:
            eid, is_new = await _find_or_create_entity(session, item["base"], "restaurant")
            if is_new:
                await _create_ext(session, eid, item["ext"], Restaurant)
                stats["rest_new"] += 1
                logger.info("  NEW  restaurant: %s", item["base"]["name_zh"])
            else:
                stats["rest_skip"] += 1
            await _create_roles(session, eid, item["roles"])
        await session.flush()

        await session.commit()
        logger.info(
            "✅ 扩充完成: poi新=%d 跳=%d | hotel新=%d 跳=%d | rest新=%d 跳=%d",
            stats["poi_new"], stats["poi_skip"],
            stats["hotel_new"], stats["hotel_skip"],
            stats["rest_new"], stats["rest_skip"],
        )


if __name__ == "__main__":
    asyncio.run(seed())
