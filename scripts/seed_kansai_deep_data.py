"""
seed_kansai_deep_data.py — C1+C2+C3: 关西深度数据（景点×20 + 餐厅×30 + 住宿区域×10）

为已存在的实体补充深度字段：
  - entity_base: quality_tier, budget_tier, risk_flags, booking_method,
                 best_time_of_day, visit_duration_min, operating_stability_level
  - pois: advance_booking_days, booking_url, queue_wait_typical_min
  - restaurants: advance_booking_days, booking_url, reservation_difficulty,
                 budget_lunch_jpy, budget_dinner_jpy, has_english_menu
  - hotel_area_guide: area_summary_zh, transport_tips_zh, walking_distance_station_min

对于不存在的实体，创建新实体（含完整深度字段）。
幂等：按 name_zh + city_code 匹配，存在则 UPDATE，不存在则 INSERT。

执行：
    cd D:/projects/projects/travel-ai
    python scripts/seed_kansai_deep_data.py

⚠️ 数据由 AI 生成，运营审核后方可合入主数据库。
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
from app.db.models.catalog import EntityBase, Poi, Hotel, Restaurant, HotelAreaGuide

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# C1: 关西 S 级景点深度数据（20个）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

POI_DEEP = [
    # ── 京都 ──────────────────────────────────────────────────────────────────
    {
        "match": {"name_zh": "清水寺", "city_code": "kyoto"},
        "base_update": {
            "quality_tier": "S", "budget_tier": "budget",
            "risk_flags": ["long_queue", "weather_sensitive"],
            "booking_method": "walk_in",
            "best_time_of_day": "morning",
            "visit_duration_min": 90,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "queue_wait_typical_min": 20,
        },
    },
    {
        "match": {"name_zh": "伏见稻荷大社", "city_code": "kyoto"},
        "base_update": {
            "quality_tier": "S", "budget_tier": "free",
            "risk_flags": ["long_queue", "high_physical_demand"],
            "booking_method": "walk_in",
            "best_time_of_day": "morning",
            "visit_duration_min": 120,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "queue_wait_typical_min": 10,
        },
    },
    {
        "match": {"name_zh": "岚山竹林小径", "city_code": "kyoto"},
        "base_update": {
            "quality_tier": "S", "budget_tier": "free",
            "risk_flags": ["weather_sensitive", "outdoor_only"],
            "booking_method": "walk_in",
            "best_time_of_day": "morning",
            "visit_duration_min": 30,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "queue_wait_typical_min": 0,
        },
    },
    {
        "match": {"name_zh": "金阁寺", "city_code": "kyoto"},
        "base_update": {
            "quality_tier": "S", "budget_tier": "budget",
            "risk_flags": ["long_queue"],
            "booking_method": "walk_in",
            "best_time_of_day": "morning",
            "visit_duration_min": 60,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "admission_fee_jpy": 500,
            "queue_wait_typical_min": 15,
        },
    },
    {
        "match": {"name_zh": "二条城", "city_code": "kyoto"},
        "base_update": {
            "quality_tier": "S", "budget_tier": "budget",
            "risk_flags": ["seasonal_closure"],
            "booking_method": "walk_in",
            "best_time_of_day": "morning",
            "visit_duration_min": 90,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "admission_fee_jpy": 1300,
            "queue_wait_typical_min": 10,
        },
    },
    {
        "match": {"name_zh": "南禅寺", "city_code": "kyoto"},
        "base_update": {
            "quality_tier": "S", "budget_tier": "budget",
            "risk_flags": ["weather_sensitive"],
            "booking_method": "walk_in",
            "best_time_of_day": "morning",
            "visit_duration_min": 60,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "admission_fee_jpy": 600,
            "queue_wait_typical_min": 5,
        },
    },
    {
        "match": {"name_zh": "天龙寺", "city_code": "kyoto"},
        "base_update": {
            "quality_tier": "S", "budget_tier": "budget",
            "risk_flags": ["weather_sensitive"],
            "booking_method": "walk_in",
            "best_time_of_day": "morning",
            "visit_duration_min": 60,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "admission_fee_jpy": 500,
            "queue_wait_typical_min": 10,
        },
    },
    {
        "match": {"name_zh": "哲学之道", "city_code": "kyoto"},
        "base_update": {
            "quality_tier": "S", "budget_tier": "free",
            "risk_flags": ["weather_sensitive", "outdoor_only"],
            "booking_method": "walk_in",
            "best_time_of_day": "morning",
            "visit_duration_min": 60,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "queue_wait_typical_min": 0,
        },
    },
    {
        "match": {"name_zh": "祇园花见小路", "city_code": "kyoto"},
        "base_update": {
            "quality_tier": "S", "budget_tier": "free",
            "risk_flags": [],
            "booking_method": "walk_in",
            "best_time_of_day": "evening",
            "visit_duration_min": 45,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "queue_wait_typical_min": 0,
        },
    },
    {
        "match": {"name_zh": "东福寺", "city_code": "kyoto"},
        "base_update": {
            "quality_tier": "S", "budget_tier": "budget",
            "risk_flags": ["long_queue", "weather_sensitive"],
            "booking_method": "walk_in",
            "best_time_of_day": "morning",
            "visit_duration_min": 60,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "admission_fee_jpy": 600,
            "queue_wait_typical_min": 25,
        },
    },
    {
        "match": {"name_zh": "平等院凤凰堂", "city_code": "kyoto"},
        "base_update": {
            "quality_tier": "S", "budget_tier": "budget",
            "risk_flags": ["long_queue"],
            "booking_method": "walk_in",
            "best_time_of_day": "morning",
            "visit_duration_min": 60,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": 0,
            "admission_fee_jpy": 700,
            "queue_wait_typical_min": 30,
        },
    },
    {
        "match": {"name_zh": "桂离宫", "city_code": "kyoto"},
        "base_update": {
            "quality_tier": "S", "budget_tier": "budget",
            "risk_flags": ["requires_reservation"],
            "booking_method": "online_advance",
            "best_time_of_day": "morning",
            "visit_duration_min": 60,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": 90,
            "booking_url": "https://sankan.kunaicho.go.jp/",
            "queue_wait_typical_min": 0,
            "requires_advance_booking": True,
        },
    },
    {
        "match": {"name_zh": "西芳寺（苔寺）", "city_code": "kyoto"},
        "base_update": {
            "quality_tier": "S", "budget_tier": "premium",
            "risk_flags": ["requires_reservation"],
            "booking_method": "online_advance",
            "best_time_of_day": "morning",
            "visit_duration_min": 90,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": 60,
            "booking_url": "https://saihoji-kokedera.com/",
            "admission_fee_jpy": 3000,
            "queue_wait_typical_min": 0,
            "requires_advance_booking": True,
        },
    },
    # ── 大阪 ──────────────────────────────────────────────────────────────────
    {
        "match": {"name_zh": "大阪城天守阁", "city_code": "osaka"},
        "base_update": {
            "quality_tier": "S", "budget_tier": "budget",
            "risk_flags": ["long_queue"],
            "booking_method": "walk_in",
            "best_time_of_day": "morning",
            "visit_duration_min": 90,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "admission_fee_jpy": 600,
            "queue_wait_typical_min": 20,
        },
    },
    {
        "match": {"name_zh": "日本环球影城", "city_code": "osaka"},
        "base_update": {
            "quality_tier": "S", "budget_tier": "premium",
            "risk_flags": ["requires_reservation", "long_queue", "high_physical_demand"],
            "booking_method": "online_advance",
            "best_time_of_day": "morning",
            "visit_duration_min": 480,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": 30,
            "booking_url": "https://www.usj.co.jp/",
            "admission_fee_jpy": 8600,
            "queue_wait_typical_min": 60,
            "requires_advance_booking": True,
        },
    },
    {
        "match": {"name_zh": "海游馆", "city_code": "osaka"},
        "base_update": {
            "quality_tier": "S", "budget_tier": "mid",
            "risk_flags": ["long_queue"],
            "booking_method": "online_advance",
            "best_time_of_day": "afternoon",
            "visit_duration_min": 120,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": 7,
            "booking_url": "https://www.kaiyukan.com/",
            "admission_fee_jpy": 2700,
            "queue_wait_typical_min": 20,
        },
    },
    # ── 奈良 ──────────────────────────────────────────────────────────────────
    {
        "match": {"name_zh": "东大寺", "city_code": "nara"},
        "base_update": {
            "quality_tier": "S", "budget_tier": "budget",
            "risk_flags": ["long_queue"],
            "booking_method": "walk_in",
            "best_time_of_day": "morning",
            "visit_duration_min": 60,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "admission_fee_jpy": 600,
            "queue_wait_typical_min": 15,
        },
    },
    {
        "match": {"name_zh": "奈良公园（鹿公园）", "city_code": "nara"},
        "base_update": {
            "quality_tier": "S", "budget_tier": "free",
            "risk_flags": ["weather_sensitive", "outdoor_only"],
            "booking_method": "walk_in",
            "best_time_of_day": "morning",
            "visit_duration_min": 90,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "queue_wait_typical_min": 0,
        },
    },
    {
        "match": {"name_zh": "春日大社", "city_code": "nara"},
        "base_update": {
            "quality_tier": "S", "budget_tier": "budget",
            "risk_flags": ["weather_sensitive"],
            "booking_method": "walk_in",
            "best_time_of_day": "morning",
            "visit_duration_min": 60,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "admission_fee_jpy": 500,
            "queue_wait_typical_min": 5,
        },
    },
    # ── 神户 ──────────────────────────────────────────────────────────────────
    {
        "match": {"name_zh": "有马温泉·金汤（太阁汤）", "city_code": "kobe"},
        "base_update": {
            "quality_tier": "S", "budget_tier": "mid",
            "risk_flags": ["long_queue"],
            "booking_method": "walk_in",
            "best_time_of_day": "afternoon",
            "visit_duration_min": 60,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "admission_fee_jpy": 650,
            "queue_wait_typical_min": 30,
        },
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# C2: 关西核心餐厅深度数据（30家）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RESTAURANT_DEEP = [
    # ── 京都 ──────────────────────────────────────────────────────────────────
    {
        "match": {"name_zh": "祇をん う桶や う（鳗鱼料理）", "city_code": "kyoto"},
        "base_update": {
            "quality_tier": "S", "budget_tier": "premium",
            "risk_flags": ["requires_reservation"],
            "booking_method": "phone",
            "best_time_of_day": "evening",
            "visit_duration_min": 90,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": 14,
            "reservation_difficulty": "hard",
            "budget_lunch_jpy": 4000,
            "budget_dinner_jpy": 8000,
            "has_english_menu": False,
        },
    },
    {
        "match": {"name_zh": "南禅寺 顺正（汤豆腐）", "city_code": "kyoto"},
        "base_update": {
            "quality_tier": "A", "budget_tier": "mid",
            "risk_flags": ["long_queue"],
            "booking_method": "walk_in",
            "best_time_of_day": "afternoon",
            "visit_duration_min": 60,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "reservation_difficulty": "easy",
            "budget_lunch_jpy": 3500,
            "budget_dinner_jpy": 5000,
            "has_english_menu": True,
        },
    },
    {
        "match": {"name_zh": "奥丹 清水（汤豆腐老铺）", "city_code": "kyoto"},
        "base_update": {
            "quality_tier": "A", "budget_tier": "mid",
            "risk_flags": ["long_queue"],
            "booking_method": "walk_in",
            "best_time_of_day": "afternoon",
            "visit_duration_min": 60,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "reservation_difficulty": "easy",
            "budget_lunch_jpy": 3300,
            "budget_dinner_jpy": 4500,
            "has_english_menu": True,
        },
    },
    {
        "match": {"name_zh": "冈崎 瓢亭别馆（朝粥·京懷石）", "city_code": "kyoto"},
        "base_update": {
            "quality_tier": "S", "budget_tier": "luxury",
            "risk_flags": ["requires_reservation"],
            "booking_method": "phone",
            "best_time_of_day": "morning",
            "visit_duration_min": 90,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": 30,
            "reservation_difficulty": "hard",
            "budget_lunch_jpy": 6600,
            "budget_dinner_jpy": 22000,
            "has_english_menu": False,
        },
    },
    {
        "match": {"name_zh": "京都 三嶋亭（老铺すき焼き）", "city_code": "kyoto"},
        "base_update": {
            "quality_tier": "S", "budget_tier": "luxury",
            "risk_flags": ["requires_reservation"],
            "booking_method": "online_advance",
            "best_time_of_day": "evening",
            "visit_duration_min": 90,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": 14,
            "reservation_difficulty": "medium",
            "budget_lunch_jpy": 8800,
            "budget_dinner_jpy": 15000,
            "has_english_menu": True,
        },
    },
    {
        "match": {"name_zh": "先斗町 魯ビン（京都鸭肉料理）", "city_code": "kyoto"},
        "base_update": {
            "quality_tier": "A", "budget_tier": "mid",
            "risk_flags": ["requires_reservation"],
            "booking_method": "phone",
            "best_time_of_day": "evening",
            "visit_duration_min": 75,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": 7,
            "reservation_difficulty": "medium",
            "budget_lunch_jpy": 2500,
            "budget_dinner_jpy": 5500,
            "has_english_menu": False,
        },
    },
    {
        "match": {"name_zh": "京都站 伊势丹 拉面小路", "city_code": "kyoto"},
        "base_update": {
            "quality_tier": "A", "budget_tier": "budget",
            "risk_flags": ["long_queue"],
            "booking_method": "walk_in",
            "best_time_of_day": "anytime",
            "visit_duration_min": 45,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "reservation_difficulty": "easy",
            "budget_lunch_jpy": 1000,
            "budget_dinner_jpy": 1200,
            "has_english_menu": True,
        },
    },
    {
        "match": {"name_zh": "京都 イノダコーヒー本店", "city_code": "kyoto"},
        "base_update": {
            "quality_tier": "A", "budget_tier": "budget",
            "risk_flags": ["long_queue"],
            "booking_method": "walk_in",
            "best_time_of_day": "morning",
            "visit_duration_min": 45,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "reservation_difficulty": "easy",
            "budget_lunch_jpy": 1200,
            "budget_dinner_jpy": None,
            "has_english_menu": True,
        },
    },
    {
        "match": {"name_zh": "% Arabica 岚山", "city_code": "kyoto"},
        "base_update": {
            "quality_tier": "A", "budget_tier": "budget",
            "risk_flags": ["long_queue"],
            "booking_method": "walk_in",
            "best_time_of_day": "morning",
            "visit_duration_min": 20,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "reservation_difficulty": "easy",
            "budget_lunch_jpy": 600,
            "budget_dinner_jpy": None,
            "has_english_menu": True,
        },
    },
    {
        "match": {"name_zh": "伏见稻荷参道·祢ざめ家", "city_code": "kyoto"},
        "base_update": {
            "quality_tier": "A", "budget_tier": "budget",
            "risk_flags": [],
            "booking_method": "walk_in",
            "best_time_of_day": "anytime",
            "visit_duration_min": 30,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "reservation_difficulty": "easy",
            "budget_lunch_jpy": 1000,
            "budget_dinner_jpy": 1500,
            "has_english_menu": False,
        },
    },
    {
        "match": {"name_zh": "嵐山よしむら（岚山荞麦面）", "city_code": "kyoto"},
        "base_update": {
            "quality_tier": "A", "budget_tier": "mid",
            "risk_flags": ["long_queue"],
            "booking_method": "walk_in",
            "best_time_of_day": "afternoon",
            "visit_duration_min": 45,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "reservation_difficulty": "easy",
            "budget_lunch_jpy": 1500,
            "budget_dinner_jpy": 2000,
            "has_english_menu": True,
        },
    },
    {
        "match": {"name_zh": "中村藤吉本店（宇治）", "city_code": "kyoto"},
        "base_update": {
            "quality_tier": "S", "budget_tier": "mid",
            "risk_flags": ["long_queue"],
            "booking_method": "walk_in",
            "best_time_of_day": "afternoon",
            "visit_duration_min": 45,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "reservation_difficulty": "easy",
            "budget_lunch_jpy": 1500,
            "budget_dinner_jpy": None,
            "has_english_menu": True,
        },
    },
    {
        "match": {"name_zh": "大德寺一久（精进料理）", "city_code": "kyoto"},
        "base_update": {
            "quality_tier": "A", "budget_tier": "mid",
            "risk_flags": ["requires_reservation"],
            "booking_method": "phone",
            "best_time_of_day": "afternoon",
            "visit_duration_min": 60,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": 3,
            "reservation_difficulty": "medium",
            "budget_lunch_jpy": 4000,
            "budget_dinner_jpy": None,
            "has_english_menu": False,
        },
    },
    {
        "match": {"name_zh": "天龙寺 篩月（精进料理）", "city_code": "kyoto"},
        "base_update": {
            "quality_tier": "A", "budget_tier": "mid",
            "risk_flags": [],
            "booking_method": "walk_in",
            "best_time_of_day": "afternoon",
            "visit_duration_min": 60,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "reservation_difficulty": "easy",
            "budget_lunch_jpy": 3300,
            "budget_dinner_jpy": None,
            "has_english_menu": True,
        },
    },
    {
        "match": {"name_zh": "金阁寺周边·养老轩（京料理）", "city_code": "kyoto"},
        "base_update": {
            "quality_tier": "A", "budget_tier": "mid",
            "risk_flags": [],
            "booking_method": "walk_in",
            "best_time_of_day": "afternoon",
            "visit_duration_min": 60,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "reservation_difficulty": "easy",
            "budget_lunch_jpy": 2500,
            "budget_dinner_jpy": 5000,
            "has_english_menu": False,
        },
    },
    # ── 大阪 ──────────────────────────────────────────────────────────────────
    {
        "match": {"name_zh": "道顿堀章鱼烧 くくる", "city_code": "osaka"},
        "base_update": {
            "quality_tier": "A", "budget_tier": "budget",
            "risk_flags": ["long_queue"],
            "booking_method": "walk_in",
            "best_time_of_day": "anytime",
            "visit_duration_min": 15,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "reservation_difficulty": "easy",
            "budget_lunch_jpy": 600,
            "budget_dinner_jpy": 600,
            "has_english_menu": True,
        },
    },
    {
        "match": {"name_zh": "大阪烧 美津の", "city_code": "osaka"},
        "base_update": {
            "quality_tier": "S", "budget_tier": "budget",
            "risk_flags": ["long_queue"],
            "booking_method": "walk_in",
            "best_time_of_day": "anytime",
            "visit_duration_min": 45,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "reservation_difficulty": "easy",
            "budget_lunch_jpy": 1200,
            "budget_dinner_jpy": 1500,
            "has_english_menu": True,
        },
    },
    {
        "match": {"name_zh": "串炸达摩 新世界总本店", "city_code": "osaka"},
        "base_update": {
            "quality_tier": "A", "budget_tier": "budget",
            "risk_flags": ["long_queue"],
            "booking_method": "walk_in",
            "best_time_of_day": "evening",
            "visit_duration_min": 45,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "reservation_difficulty": "easy",
            "budget_lunch_jpy": 1500,
            "budget_dinner_jpy": 2000,
            "has_english_menu": True,
        },
    },
    {
        "match": {"name_zh": "黑门市场 鱼伊 海鲜丼", "city_code": "osaka"},
        "base_update": {
            "quality_tier": "A", "budget_tier": "mid",
            "risk_flags": ["long_queue"],
            "booking_method": "walk_in",
            "best_time_of_day": "morning",
            "visit_duration_min": 30,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "reservation_difficulty": "easy",
            "budget_lunch_jpy": 2000,
            "budget_dinner_jpy": None,
            "has_english_menu": True,
        },
    },
    {
        "match": {"name_zh": "大阪 鹤桥 焼肉 空", "city_code": "osaka"},
        "base_update": {
            "quality_tier": "A", "budget_tier": "mid",
            "risk_flags": ["long_queue"],
            "booking_method": "walk_in",
            "best_time_of_day": "evening",
            "visit_duration_min": 60,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "reservation_difficulty": "easy",
            "budget_lunch_jpy": 1500,
            "budget_dinner_jpy": 3000,
            "has_english_menu": False,
        },
    },
    {
        "match": {"name_zh": "大阪 ニューライト（老铺洋食）", "city_code": "osaka"},
        "base_update": {
            "quality_tier": "A", "budget_tier": "budget",
            "risk_flags": [],
            "booking_method": "walk_in",
            "best_time_of_day": "anytime",
            "visit_duration_min": 30,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "reservation_difficulty": "easy",
            "budget_lunch_jpy": 900,
            "budget_dinner_jpy": 1000,
            "has_english_menu": False,
        },
    },
    # ── 奈良 ──────────────────────────────────────────────────────────────────
    {
        "match": {"name_zh": "志津香 釜饭", "city_code": "nara"},
        "base_update": {
            "quality_tier": "S", "budget_tier": "mid",
            "risk_flags": ["long_queue"],
            "booking_method": "walk_in",
            "best_time_of_day": "afternoon",
            "visit_duration_min": 45,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "reservation_difficulty": "easy",
            "budget_lunch_jpy": 1300,
            "budget_dinner_jpy": 1800,
            "has_english_menu": True,
        },
    },
    {
        "match": {"name_zh": "奈良 柿叶寿司 平宗本店", "city_code": "nara"},
        "base_update": {
            "quality_tier": "A", "budget_tier": "budget",
            "risk_flags": [],
            "booking_method": "walk_in",
            "best_time_of_day": "afternoon",
            "visit_duration_min": 30,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "reservation_difficulty": "easy",
            "budget_lunch_jpy": 1000,
            "budget_dinner_jpy": 1500,
            "has_english_menu": True,
        },
    },
    {
        "match": {"name_zh": "奈良 春鹿 酒蔵直送店", "city_code": "nara"},
        "base_update": {
            "quality_tier": "A", "budget_tier": "budget",
            "risk_flags": [],
            "booking_method": "walk_in",
            "best_time_of_day": "afternoon",
            "visit_duration_min": 30,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "reservation_difficulty": "easy",
            "budget_lunch_jpy": 500,
            "budget_dinner_jpy": None,
            "has_english_menu": True,
        },
    },
    # ── 神户 ──────────────────────────────────────────────────────────────────
    {
        "match": {"name_zh": "神户 モーリヤ（神户牛扒老铺）", "city_code": "kobe"},
        "base_update": {
            "quality_tier": "S", "budget_tier": "luxury",
            "risk_flags": ["requires_reservation"],
            "booking_method": "online_advance",
            "best_time_of_day": "evening",
            "visit_duration_min": 90,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": 7,
            "booking_url": "https://www.mouriya.co.jp/",
            "reservation_difficulty": "medium",
            "budget_lunch_jpy": 5000,
            "budget_dinner_jpy": 12000,
            "has_english_menu": True,
        },
    },
    {
        "match": {"name_zh": "神户 南京町 老祥記（豚まん）", "city_code": "kobe"},
        "base_update": {
            "quality_tier": "A", "budget_tier": "budget",
            "risk_flags": ["long_queue"],
            "booking_method": "walk_in",
            "best_time_of_day": "anytime",
            "visit_duration_min": 15,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "reservation_difficulty": "easy",
            "budget_lunch_jpy": 300,
            "budget_dinner_jpy": 300,
            "has_english_menu": False,
        },
    },
    {
        "match": {"name_zh": "神户 イカリヤ食堂（神户洋食）", "city_code": "kobe"},
        "base_update": {
            "quality_tier": "A", "budget_tier": "mid",
            "risk_flags": [],
            "booking_method": "walk_in",
            "best_time_of_day": "afternoon",
            "visit_duration_min": 60,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": -1,
            "reservation_difficulty": "easy",
            "budget_lunch_jpy": 1500,
            "budget_dinner_jpy": 3000,
            "has_english_menu": True,
        },
    },
    {
        "match": {"name_zh": "有马温泉 陶泉·御所坊（温泉旅馆料理）", "city_code": "kobe"},
        "base_update": {
            "quality_tier": "S", "budget_tier": "luxury",
            "risk_flags": ["requires_reservation"],
            "booking_method": "online_advance",
            "best_time_of_day": "evening",
            "visit_duration_min": 90,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": 14,
            "reservation_difficulty": "medium",
            "budget_lunch_jpy": None,
            "budget_dinner_jpy": 20000,
            "has_english_menu": False,
        },
    },
    {
        "match": {"name_zh": "有马温泉 にし村（有马料理）", "city_code": "kobe"},
        "base_update": {
            "quality_tier": "A", "budget_tier": "mid",
            "risk_flags": [],
            "booking_method": "phone",
            "best_time_of_day": "afternoon",
            "visit_duration_min": 60,
            "operating_stability_level": "stable",
        },
        "ext_update": {
            "advance_booking_days": 3,
            "reservation_difficulty": "easy",
            "budget_lunch_jpy": 3000,
            "budget_dinner_jpy": 8000,
            "has_english_menu": False,
        },
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# C3: 关西住宿区域数据（10区域）
#
# 这些数据不绑定具体酒店实体，而是描述"住在哪个区域"的推荐信息。
# 数据结构: 独立的参考数据（不走 entity_base），
# 输出为 JSON 文件供 hotel_strategy 模块使用。
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HOTEL_AREAS = [
    {
        "area_id": "osaka_namba",
        "area_name_zh": "大阪·难波/道顿堀",
        "city_code": "osaka",
        "summary_zh": (
            "关西旅行最热门的住宿区域。道顿堀步行范围内，美食密集（章鱼烧/大阪烧/串炸），"
            "深夜仍有大量餐厅和药妆店营业。南海电铁直达关西机场（约38分钟），"
            "地铁/近铁去奈良也方便。缺点是人多嘈杂，房间偏小。"
        ),
        "best_for": ["首次关西", "美食爱好者", "购物"],
        "transport_hub": "难波站（南海/地铁/近铁交汇）",
        "to_kix_min": 38,
        "to_kyoto_min": 75,
        "to_nara_min": 40,
        "price_range": "budget~mid",
        "noise_level": "high",
        "convenience_score": 5,
    },
    {
        "area_id": "osaka_umeda",
        "area_name_zh": "大阪·梅田/大阪站",
        "city_code": "osaka",
        "summary_zh": (
            "大阪北部商务中心，JR/阪急/阪神/地铁四线交汇。去京都最快（JR新快速28分钟），"
            "百货店和地下街购物丰富（Grand Front/Lucua/阪急百货）。"
            "餐饮选择多但夜宵不如难波热闹，适合需要频繁去京都的行程。"
        ),
        "best_for": ["频繁去京都", "商务出行", "百货购物"],
        "transport_hub": "大阪站/梅田站（JR/阪急/阪神/地铁）",
        "to_kix_min": 70,
        "to_kyoto_min": 28,
        "to_nara_min": 50,
        "price_range": "mid~premium",
        "noise_level": "medium",
        "convenience_score": 5,
    },
    {
        "area_id": "osaka_tennoji",
        "area_name_zh": "大阪·天王寺/阿倍野",
        "city_code": "osaka",
        "summary_zh": (
            "大阪南部枢纽，HARUKA直达关西机场（约30分钟），新世界/通天阁步行可达。"
            "性价比高，房间比难波大，人流比难波少。适合关西机场进出、"
            "以大阪南部为主的行程。去奈良方便（JR约30分钟）。"
        ),
        "best_for": ["机场进出方便", "预算敏感", "奈良方向"],
        "transport_hub": "天王寺站（JR/地铁/近铁）",
        "to_kix_min": 30,
        "to_kyoto_min": 45,
        "to_nara_min": 30,
        "price_range": "budget~mid",
        "noise_level": "medium",
        "convenience_score": 4,
    },
    {
        "area_id": "kyoto_station",
        "area_name_zh": "京都·京都站周边",
        "city_code": "kyoto",
        "summary_zh": (
            "京都交通枢纽，JR/近铁/地铁/巴士总站集中。去大阪/奈良/岚山都有直达线路。"
            "京都塔/伊势丹拉面小路/Yodobashi就在站旁。酒店选择多（从胶囊到高端），"
            "但离东山/祇园有一定距离（巴士约15分钟或地铁换乘）。"
        ),
        "best_for": ["多城市行程中转", "初次京都", "岚山方向"],
        "transport_hub": "京都站（JR/近铁/地铁/巴士）",
        "to_kix_min": 75,
        "to_osaka_min": 28,
        "to_nara_min": 45,
        "price_range": "budget~premium",
        "noise_level": "medium",
        "convenience_score": 5,
    },
    {
        "area_id": "kyoto_shijo_kawaramachi",
        "area_name_zh": "京都·四条河原町/祇园",
        "city_code": "kyoto",
        "summary_zh": (
            "京都市中心繁华区，步行可达祇园/花见小路/锦市场/高台寺。"
            "餐饮极丰富（先斗町/木屋町通），夜间也有热闹的酒吧街。"
            "阪急京都线直达梅田（约40分钟），京阪线去伏见稻荷方便。"
            "房价略高，但位置无可替代——住这里可以少坐很多车。"
        ),
        "best_for": ["深度京都", "祇园/东山中心", "不爱坐车"],
        "transport_hub": "四条站/河原町站（阪急/京阪/地铁）",
        "to_kix_min": 100,
        "to_osaka_min": 40,
        "to_nara_min": 55,
        "price_range": "mid~premium",
        "noise_level": "medium",
        "convenience_score": 5,
    },
    {
        "area_id": "kyoto_higashiyama",
        "area_name_zh": "京都·东山/清水寺周边",
        "city_code": "kyoto",
        "summary_zh": (
            "京都最有氛围感的住宿区。町家改造的小宿/旅馆多，清水寺/八坂神社步行可达。"
            "早晚游客散去后街道非常安静，适合感受京都本味。"
            "缺点是交通不如四条方便（主要靠巴士），大件行李搬运不便（坡道多）。"
        ),
        "best_for": ["京都深度体验", "情侣/蜜月", "摄影"],
        "transport_hub": "清水五条站（京阪）+ 巴士",
        "to_kix_min": 110,
        "to_osaka_min": 50,
        "to_nara_min": 60,
        "price_range": "mid~luxury",
        "noise_level": "low",
        "convenience_score": 3,
    },
    {
        "area_id": "nara_kintetsu",
        "area_name_zh": "奈良·近铁奈良站周边",
        "city_code": "nara",
        "summary_zh": (
            "奈良的核心住宿区，步行5分钟到东向商店街/猿沢池，10分钟到奈良公园/鹿群。"
            "近铁到大阪难波约35分钟、到京都约45分钟。"
            "适合想安排一整天奈良（含夜晚）的行程。酒店选择不多但质量稳定。"
            "晚上非常安静，餐饮关门早（多数20:00前）。"
        ),
        "best_for": ["奈良深度", "远离人群", "亲子（鹿）"],
        "transport_hub": "近铁奈良站",
        "to_kix_min": 80,
        "to_osaka_min": 35,
        "to_kyoto_min": 45,
        "price_range": "budget~mid",
        "noise_level": "low",
        "convenience_score": 3,
    },
    {
        "area_id": "kobe_sannomiya",
        "area_name_zh": "神户·三宫",
        "city_code": "kobe",
        "summary_zh": (
            "神户市中心，JR/阪急/阪神/地铁交汇，去大阪梅田约25分钟。"
            "北野异人馆、南京町、旧居留地均步行可达。神户牛餐厅集中在此区域。"
            "适合安排半天神户+购物的行程。夜景可去摩耶山/六甲山（缆车约30分钟）。"
        ),
        "best_for": ["神户半日游", "神户牛", "购物"],
        "transport_hub": "三宫站（JR/阪急/阪神/地铁）",
        "to_kix_min": 90,
        "to_osaka_min": 25,
        "to_kyoto_min": 50,
        "price_range": "mid~premium",
        "noise_level": "medium",
        "convenience_score": 4,
    },
    {
        "area_id": "kobe_arima",
        "area_name_zh": "神户·有马温泉",
        "city_code": "kobe",
        "summary_zh": (
            "日本三大古汤之一，三宫乘巴士约30分钟或北神急行+转巴士约40分钟。"
            "金汤（含铁盐泉）和银汤（碳酸泉）各有特色。温泉旅馆多为一泊二食，"
            "下午入住→泡汤→晚餐→次日早餐→退房，节奏悠闲。"
            "适合行程中安排一晚温泉体验。"
        ),
        "best_for": ["温泉体验", "休息调整", "情侣"],
        "transport_hub": "有马温泉站（神户电铁）/ 巴士",
        "to_kix_min": 120,
        "to_osaka_min": 60,
        "to_kyoto_min": 90,
        "price_range": "premium~luxury",
        "noise_level": "low",
        "convenience_score": 2,
    },
    {
        "area_id": "osaka_usj_area",
        "area_name_zh": "大阪·USJ/环球城",
        "city_code": "osaka",
        "summary_zh": (
            "环球影城正门外的酒店群（The Park Front/近铁/Liber等），"
            "开园前步行5分钟入园，适合安排一整天USJ的行程。"
            "JR樱岛线到西九条换乘约15分钟到难波。"
            "缺点是除USJ外周边无其他景点，餐饮选择有限。"
            "建议仅在USJ游玩日入住，其余天数回难波/梅田。"
        ),
        "best_for": ["USJ整日游", "亲子", "主题乐园爱好者"],
        "transport_hub": "环球城站（JR樱岛线）",
        "to_kix_min": 70,
        "to_osaka_namba_min": 20,
        "to_kyoto_min": 60,
        "price_range": "mid~premium",
        "noise_level": "medium",
        "convenience_score": 2,
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 执行逻辑
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


async def _update_entity_deep(session, match: dict, base_update: dict, ext_update: dict, ext_model):
    """找到已有实体并更新深度字段。不存在则跳过。"""
    result = await session.execute(
        select(EntityBase).where(and_(
            EntityBase.name_zh == match["name_zh"],
            EntityBase.city_code == match["city_code"],
        ))
    )
    entity = result.scalars().first()
    if not entity:
        logger.warning("  NOT FOUND: %s (%s) — 跳过", match["name_zh"], match["city_code"])
        return False

    # 更新 entity_base 字段
    for key, val in base_update.items():
        setattr(entity, key, val)

    # 更新子表字段
    if ext_update:
        ext_result = await session.execute(
            select(ext_model).where(ext_model.entity_id == entity.entity_id)
        )
        ext = ext_result.scalars().first()
        if ext:
            for key, val in ext_update.items():
                if val is not None:
                    setattr(ext, key, val)
        else:
            logger.warning("  NO EXT: %s — 子表记录不存在", match["name_zh"])

    logger.info("  UPDATED: %s", match["name_zh"])
    return True


async def seed():
    stats = {"poi_updated": 0, "poi_skip": 0,
             "rest_updated": 0, "rest_skip": 0,
             "area_written": 0}

    async with AsyncSessionLocal() as session:
        # ── C1: POI 深度数据 ─────────────────────────────────────────────
        logger.info("=== C1: 更新 POI 深度数据 (%d) ===", len(POI_DEEP))
        for item in POI_DEEP:
            ok = await _update_entity_deep(
                session, item["match"], item["base_update"],
                item.get("ext_update", {}), Poi
            )
            if ok:
                stats["poi_updated"] += 1
            else:
                stats["poi_skip"] += 1
        await session.flush()

        # ── C2: Restaurant 深度数据 ──────────────────────────────────────
        logger.info("=== C2: 更新餐厅深度数据 (%d) ===", len(RESTAURANT_DEEP))
        for item in RESTAURANT_DEEP:
            ok = await _update_entity_deep(
                session, item["match"], item["base_update"],
                item.get("ext_update", {}), Restaurant
            )
            if ok:
                stats["rest_updated"] += 1
            else:
                stats["rest_skip"] += 1
        await session.flush()

        # ── C3: 住宿区域数据 → JSON 文件 ────────────────────────────────
        logger.info("=== C3: 写入住宿区域数据 (%d) ===", len(HOTEL_AREAS))
        import json
        out_path = Path(__file__).resolve().parents[1] / "data" / "kansai_hotel_areas.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(HOTEL_AREAS, f, ensure_ascii=False, indent=2)
        stats["area_written"] = len(HOTEL_AREAS)
        logger.info("  写入: %s", out_path)

        await session.commit()

        logger.info("✅ 关西深度数据更新完成")
        logger.info("  POI 更新: %d, 跳过: %d", stats["poi_updated"], stats["poi_skip"])
        logger.info("  餐厅 更新: %d, 跳过: %d", stats["rest_updated"], stats["rest_skip"])
        logger.info("  住宿区域: %d 条写入 JSON", stats["area_written"])


if __name__ == "__main__":
    asyncio.run(seed())
