"""
conftest_regression.py — 12个关西真实表单 fixture，供 test_regression_cp*.py 使用。

使用方式：在 test_regression_cp*.py 中：
    from app.domains.planning_v2.tests.conftest_regression import FORM_DATA, make_user_constraints

entity_id 修正说明：
  - kob_arima_onsen → hyo_arima_kinsen（实际 id，见 hyogo.json）
  - kyo_gion / osa_shinsaibashi 在 visited（已访问，不在 poi_pool，不需要验证存在性）
"""

from __future__ import annotations

import pytest
from app.domains.planning_v2.models import CircleProfile, UserConstraints

KANSAI_CIRCLE = CircleProfile.from_registry("kansai")


def make_user_constraints(form: dict) -> UserConstraints:
    """从表单 dict 构造 UserConstraints。字段名与提示词定义对齐。"""
    return UserConstraints(
        trip_window={
            "start_date": form["start_date"],
            "end_date": form["end_date"],
            "total_days": form["total_days"],
        },
        user_profile={
            "party_type": form.get("party_type", "couple"),
            "party_size": form.get("party_size", 2),
            "budget_tier": form.get("budget_tier", "mid"),
            "children_ages": form.get("children_ages", []),
            "must_have_tags": form.get("must_have_tags", []),
            "nice_to_have_tags": form.get("nice_to_have_tags", []),
            "avoid_tags": form.get("avoid_tags", []),
            "special_requirements": form.get("special_requirements", {}),
        },
        constraints={
            "must_visit": form.get("must_visit", []),
            "do_not_go": form.get("do_not_go", []),
            "visited": form.get("visited", []),
            "booked_items": form.get("booked_items", []),
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# 12 个表单定义
# ─────────────────────────────────────────────────────────────────────────────

# 主力样本 1：基线
_FORM_7D_CLASSIC = {
    "case_id": "kansai_couple_7d_classic",
    "start_date": "2026-04-15",
    "end_date": "2026-04-21",
    "total_days": 7,
    "party_type": "couple",
    "budget_tier": "mid",
    "must_visit": [],
    "do_not_go": [],
    "visited": [],
    "booked_items": [],
    "must_have_tags": ["shrine", "garden"],
    "nice_to_have_tags": ["photo_spot", "cafe"],
}

# 主力样本 2：美食夜生活
_FORM_7D_FOOD = {
    "case_id": "kansai_friends_7d_food_citywalk",
    "start_date": "2026-05-01",
    "end_date": "2026-05-07",
    "total_days": 7,
    "party_type": "friends",
    "budget_tier": "mid",
    "must_visit": [],
    "do_not_go": [],
    "visited": [],
    "booked_items": [],
    "must_have_tags": ["food", "nightlife", "citywalk"],
    "nice_to_have_tags": ["bar", "izakaya"],
    "avoid_tags": ["temple", "shrine"],
}

# 主力样本 3：文化独行
_FORM_7D_CULTURE = {
    "case_id": "kansai_solo_7d_culture",
    "start_date": "2026-10-10",
    "end_date": "2026-10-16",
    "total_days": 7,
    "party_type": "solo",
    "budget_tier": "mid",
    "must_visit": [],
    "do_not_go": [],
    "visited": [],
    "booked_items": [],
    "must_have_tags": ["temple", "museum", "cultural"],
    "nice_to_have_tags": ["garden", "tea_house"],
}

# 主力样本 4：混合线（premium）
_FORM_8D_MIXED = {
    "case_id": "kansai_couple_8d_mixed",
    "start_date": "2026-04-01",
    "end_date": "2026-04-08",
    "total_days": 8,
    "party_type": "couple",
    "budget_tier": "premium",
    "must_visit": ["kyo_fushimi_inari", "nar_nara_park_deer"],
    "do_not_go": [],
    "visited": [],
    "booked_items": [],
    "must_have_tags": [],
    "nice_to_have_tags": ["onsen", "shopping"],
}

# 主力样本 5：拍照偏好（3人）
_FORM_8D_PHOTO = {
    "case_id": "kansai_friends_8d_photo_spots",
    "start_date": "2026-11-15",
    "end_date": "2026-11-22",
    "total_days": 8,
    "party_type": "friends",
    "party_size": 3,
    "budget_tier": "mid",
    "must_visit": [],
    "do_not_go": [],
    "visited": [],
    "booked_items": [],
    "must_have_tags": ["photo_spot", "night_view", "cafe"],
    "nice_to_have_tags": ["instagram", "scenic"],
}

# 主力样本 6：慢节奏
_FORM_9D_SLOW = {
    "case_id": "kansai_solo_9d_slow_pace",
    "start_date": "2026-06-10",
    "end_date": "2026-06-18",
    "total_days": 9,
    "party_type": "solo",
    "budget_tier": "mid",
    "must_visit": [],
    "do_not_go": [],
    "visited": [],
    "booked_items": [],
    "must_have_tags": ["garden", "tea_house", "onsen"],
    "nice_to_have_tags": ["bookshop", "craft"],
    "special_requirements": {"pace": "slow", "max_activities_per_day": 2},
}

# 主力样本 7（smoke）：多 must_visit
_FORM_9D_MUST_VISIT = {
    "case_id": "kansai_couple_9d_must_visit",
    "start_date": "2026-04-05",
    "end_date": "2026-04-13",
    "total_days": 9,
    "party_type": "couple",
    "budget_tier": "premium",
    "must_visit": [
        "kyo_fushimi_inari",
        "kyo_kinkakuji",
        "kyo_arashiyama_bamboo",
        "nar_nara_park_deer",
        "osa_dotonbori",
    ],
    "do_not_go": ["osa_usj"],
    "visited": ["kyo_gion"],
    "booked_items": [],
    "must_have_tags": ["shrine", "garden"],
    "nice_to_have_tags": ["onsen"],
}

# 主力样本 8：深度版（4人）
_FORM_10D_DEEP = {
    "case_id": "kansai_friends_10d_deep",
    "start_date": "2026-05-15",
    "end_date": "2026-05-24",
    "total_days": 10,
    "party_type": "friends",
    "party_size": 4,
    "budget_tier": "mid",
    "must_visit": ["kyo_fushimi_inari"],
    "do_not_go": [],
    "visited": [],
    "booked_items": [],
    "must_have_tags": [],
    "nice_to_have_tags": ["local_experience", "off_beaten_path"],
}

# 边界样本 9：最短目标单
_FORM_6D_SHORT = {
    "case_id": "kansai_couple_6d_short_dense",
    "start_date": "2026-09-20",
    "end_date": "2026-09-25",
    "total_days": 6,
    "party_type": "couple",
    "budget_tier": "mid",
    "must_visit": ["kyo_fushimi_inari", "kyo_kinkakuji"],
    "do_not_go": [],
    "visited": [],
    "booked_items": [],
    "must_have_tags": [],
    "nice_to_have_tags": [],
}

# 边界样本 10：低强度长线（有预订）
_FORM_11D_RELAXED = {
    "case_id": "kansai_couple_11d_relaxed",
    "start_date": "2026-03-25",
    "end_date": "2026-04-04",
    "total_days": 11,
    "party_type": "couple",
    "budget_tier": "premium",
    "must_visit": [],
    "do_not_go": [],
    "visited": ["kyo_fushimi_inari", "kyo_kinkakuji"],
    "booked_items": [
        {"type": "restaurant", "date": "2026-03-28", "time": "18:00", "name": "瓢亭"},
    ],
    "must_have_tags": ["onsen", "garden"],
    "nice_to_have_tags": ["cherry_blossom"],
    "special_requirements": {"pace": "relaxed"},
}

# 边界样本 11：带娃家庭
_FORM_8D_FAMILY = {
    "case_id": "kansai_parents_8d_family_kids",
    "start_date": "2026-07-20",
    "end_date": "2026-07-27",
    "total_days": 8,
    "party_type": "family_young",
    "budget_tier": "mid",
    "children_ages": [5, 8],
    "must_visit": ["osa_usj"],
    "do_not_go": [],
    "visited": [],
    "booked_items": [],
    "must_have_tags": ["family_friendly"],
    "nice_to_have_tags": ["aquarium", "park"],
    "avoid_tags": ["nightlife", "bar", "adults_only"],
}

# 边界样本 12（smoke）：最复杂边界单
_FORM_13D_COMPLEX = {
    "case_id": "kansai_couple_13d_complex_constraints",
    "start_date": "2026-04-10",
    "end_date": "2026-04-22",
    "total_days": 13,
    "party_type": "couple",
    "budget_tier": "premium",
    "must_visit": [
        "kyo_fushimi_inari",
        "kyo_kinkakuji",
        "kyo_arashiyama_bamboo",
        "nar_nara_park_deer",
        "nar_todaiji",
        "osa_dotonbori",
        "hyo_arima_kinsen",   # 原提示词 kob_arima_onsen，实际 id
    ],
    "do_not_go": ["osa_usj", "kyo_nijo_castle"],
    "visited": ["kyo_gion", "osa_shinsaibashi"],
    "booked_items": [
        {"type": "restaurant", "date": "2026-04-12", "time": "12:00", "name": "祢ざめ家"},
        {"type": "activity", "date": "2026-04-15", "time": "09:00", "name": "和服体验"},
    ],
    "must_have_tags": ["shrine", "onsen", "garden"],
    "nice_to_have_tags": ["tea_ceremony", "calligraphy"],
    "special_requirements": {
        "pace": "moderate",
        "hotel_preference": "ryokan_at_least_once",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# pytest.param 列表（含 smoke marker）
# ─────────────────────────────────────────────────────────────────────────────

FORM_DATA = [
    pytest.param(_FORM_7D_CLASSIC,    id="7d_classic",    marks=pytest.mark.smoke),
    pytest.param(_FORM_7D_FOOD,       id="7d_food_citywalk"),
    pytest.param(_FORM_7D_CULTURE,    id="7d_culture"),
    pytest.param(_FORM_8D_MIXED,      id="8d_mixed"),
    pytest.param(_FORM_8D_PHOTO,      id="8d_photo_spots"),
    pytest.param(_FORM_9D_SLOW,       id="9d_slow_pace"),
    pytest.param(_FORM_9D_MUST_VISIT, id="9d_must_visit", marks=pytest.mark.smoke),
    pytest.param(_FORM_10D_DEEP,      id="10d_deep"),
    pytest.param(_FORM_6D_SHORT,      id="6d_short_dense"),
    pytest.param(_FORM_11D_RELAXED,   id="11d_relaxed"),
    pytest.param(_FORM_8D_FAMILY,     id="8d_family_kids"),
    pytest.param(_FORM_13D_COMPLEX,   id="13d_complex",   marks=pytest.mark.smoke),
]


@pytest.fixture
def circle():
    return KANSAI_CIRCLE
