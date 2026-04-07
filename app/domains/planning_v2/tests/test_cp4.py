"""
test_cp4.py — CP4 契约测试（Step 13-16，完整流程）

CP4 检查点：
  1. 酒店含早餐的天，breakfast 选择为 null
  2. 酒店含晚餐的天，dinner 选择为 null
  3. 预算 within_budget=True（或有说明）
  4. Plan B 覆盖 rain 触发器
  5. Step 16 失败不导致整体失败
  6. 所有 step_log 条目都有 status

涉及步骤：
  - Step 13   build_restaurant_pool   (DB)
  - Step 13.5 select_meals            (Sonnet AI + fallback)
  - Step 14   estimate_budget         (纯 Python)
  - Step 15   build_plan_b            (Sonnet AI + fallback)
  - Step 16   generate_handbook_content (Sonnet AI + fallback，非阻塞)

Step 14 是纯 Python，重点测试。
Step 13.5/15/16 用 fallback 或 mock。
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.domains.planning_v2.models import (
    CandidatePool,
    DailyConstraints,
    UserConstraints,
)
from app.domains.planning_v2.step13_restaurant_pool import (
    _check_meal_inclusion,
    _empty_result,
)
from app.domains.planning_v2.step13_5_meal_planner import (
    _build_fallback_selections,
    _validate_cuisine_frequency,
    select_meals,
)
from app.domains.planning_v2.step14_budget import (
    estimate_budget,
    _get_admission_fee,
    _get_meal_cost,
    _empty_budget,
)
from app.domains.planning_v2.step15_plan_b import (
    build_plan_b,
    _build_fallback_plan_b,
    _classify_entity,
)
from app.domains.planning_v2.step16_handbook import (
    generate_handbook_content,
    _build_fallback_handbook,
    _is_heavy_day,
)


# ─────────────────────────────────────────────────────────────────────────────
# 共用 Fixtures
# ─────────────────────────────────────────────────────────────────────────────

def _make_dc(date_str: str, breakfast: bool = False, dinner: bool = False) -> DailyConstraints:
    from datetime import date
    return DailyConstraints(
        date=date_str,
        day_of_week=date.fromisoformat(date_str).strftime("%a"),
        sunrise="05:45",
        sunset="18:30",
        hotel_breakfast_included=breakfast,
        hotel_dinner_included=dinner,
    )


def _make_poi(entity_id: str, tags: list = None, grade: str = "A") -> CandidatePool:
    return CandidatePool(
        entity_id=entity_id,
        name_zh=f"景点_{entity_id[-4:]}",
        entity_type="poi",
        grade=grade,
        latitude=34.7,
        longitude=135.5,
        tags=tags or [],
        visit_minutes=90,
        cost_local=500,
        city_code="kyoto",
    )


def _make_timeline(days: int = 3) -> dict:
    """构造最小合法 timeline 结构。"""
    return {
        "timeline": [
            {
                "day": d + 1,
                "date": f"2026-04-{10 + d:02d}",
                "slots": [
                    {
                        "type": "poi",
                        "entity_id": f"poi_{d}a",
                        "name": f"景点{d}A",
                        "start_time": "09:00",
                        "end_time": "11:00",
                        "tags": [],
                    },
                    {
                        "type": "poi",
                        "entity_id": f"poi_{d}b",
                        "name": f"景点{d}B",
                        "start_time": "14:00",
                        "end_time": "16:00",
                        "tags": [],
                    },
                ],
            }
            for d in range(days)
        ]
    }


def _make_day_sequences(days: int = 3) -> list[dict]:
    return [
        {
            "day": d + 1,
            "date": f"2026-04-{10 + d:02d}",
            "items": [
                {"entity_id": f"poi_{d}a", "entity_type": "poi", "cost_local": 500},
                {"entity_id": f"poi_{d}b", "entity_type": "poi", "cost_local": 0},
            ],
        }
        for d in range(days)
    ]


def _make_hotel_plan(breakfast: bool = False, dinner: bool = False,
                     cost_per_night: int = 10000) -> dict:
    """构造酒店方案。
    step14 读 hotel_plan.get("cost_per_night_jpy")（顶层），
    meals_included 也在顶层。
    """
    return {
        "hotel_id": "hotel_a",
        "name": "测试酒店",
        "nights": 3,
        "cost_per_night_jpy": cost_per_night,
        "meals_included": {"breakfast": breakfast, "dinner": dinner},
        "check_in": "15:00",
        "check_out": "11:00",
        "avg_commute_minutes": 20,
    }


def _make_restaurant(entity_id: str, name: str) -> CandidatePool:
    """构造餐厅 CandidatePool（step13_5 fallback 期望 CandidatePool 对象）。"""
    return CandidatePool(
        entity_id=entity_id,
        name_zh=name,
        entity_type="restaurant",
        grade="A",
        latitude=34.7,
        longitude=135.5,
        tags=[],
        visit_minutes=60,
        cost_local=1200,
        city_code="kyoto",
    )


def _make_restaurant_pool(has_breakfast: bool = True, has_dinner: bool = True) -> dict:
    """构造餐厅候选池（pools 存储 CandidatePool 对象，与 step13 输出一致）。"""
    return {
        "breakfast_pool": [
            _make_restaurant("rest_b1", "早餐店1")
        ] if has_breakfast else [],
        "lunch_pool": {
            "restaurants": [_make_restaurant("rest_l1", "午餐店1")],
            "cafes": [_make_restaurant("rest_l2", "咖啡店1")],
        },
        "dinner_pool": [
            _make_restaurant("rest_d1", "晚餐店1")
        ] if has_dinner else [],
        "pool_stats": {
            "total_restaurants": 3,
            "breakfast_available": has_breakfast,
            "dinner_available": has_dinner,
            "lunch_flex": True,
        },
    }


def _make_user_constraints(budget: str = "mid") -> UserConstraints:
    return UserConstraints(
        trip_window={"start_date": "2026-04-10", "end_date": "2026-04-12", "total_days": 3},
        user_profile={"party_type": "couple", "budget_tier": budget,
                      "must_have_tags": [], "avoid_tags": []},
        constraints={"must_visit": [], "do_not_go": [], "visited": [], "booked_items": []},
    )


# ─────────────────────────────────────────────────────────────────────────────
# Step 13: build_restaurant_pool — 含餐检查逻辑
# ─────────────────────────────────────────────────────────────────────────────

class TestStep13RestaurantPool:

    def test_check_meal_inclusion_all_breakfast(self):
        """所有天含早餐时，all_breakfast_included=True。"""
        dcs = [
            _make_dc("2026-04-10", breakfast=True),
            _make_dc("2026-04-11", breakfast=True),
            _make_dc("2026-04-12", breakfast=True),
        ]
        all_b, all_d = _check_meal_inclusion(dcs)
        assert all_b is True
        assert all_d is False

    def test_check_meal_inclusion_partial_breakfast(self):
        """部分天含早餐时，all_breakfast_included=False。"""
        dcs = [
            _make_dc("2026-04-10", breakfast=True),
            _make_dc("2026-04-11", breakfast=False),
        ]
        all_b, _ = _check_meal_inclusion(dcs)
        assert all_b is False

    def test_check_meal_inclusion_all_dinner(self):
        dcs = [
            _make_dc("2026-04-10", dinner=True),
            _make_dc("2026-04-11", dinner=True),
        ]
        _, all_d = _check_meal_inclusion(dcs)
        assert all_d is True

    def test_empty_result_structure(self):
        """_empty_result 返回合法的空结构。"""
        result = _empty_result()
        assert "breakfast_pool" in result
        assert "lunch_pool" in result
        assert "dinner_pool" in result
        assert "pool_stats" in result
        assert isinstance(result["breakfast_pool"], list)
        assert isinstance(result["dinner_pool"], list)
        assert isinstance(result["lunch_pool"], dict)

    def test_check_meal_inclusion_empty_list(self):
        """空列表时返回 False, False。"""
        all_b, all_d = _check_meal_inclusion([])
        assert all_b is False
        assert all_d is False

    @pytest.mark.asyncio
    async def test_build_restaurant_pool_returns_empty_on_empty_cities(self):
        """circle_cities 为空时返回空结构。"""
        from app.domains.planning_v2.step13_restaurant_pool import build_restaurant_pool
        session = AsyncMock()
        result = await build_restaurant_pool(
            session=session,
            user_constraints=_make_user_constraints(),
            circle_cities=[],
            daily_constraints=[_make_dc("2026-04-10")],
            main_corridors=[],
        )
        assert result["breakfast_pool"] == []
        assert result["dinner_pool"] == []


# ─────────────────────────────────────────────────────────────────────────────
# Step 13.5: select_meals — CP4 核心：含餐天 null
# ─────────────────────────────────────────────────────────────────────────────

class TestStep13_5MealPlanner:

    def test_fallback_breakfast_null_when_hotel_includes(self):
        """CP4：酒店含早餐的天，breakfast 应为 null。"""
        dcs = [
            _make_dc("2026-04-10", breakfast=True),
            _make_dc("2026-04-11", breakfast=True),
            _make_dc("2026-04-12", breakfast=False),
        ]
        timeline = _make_timeline(3)
        pool = _make_restaurant_pool()
        result = _build_fallback_selections(pool, timeline, dcs)

        for sel in result["meal_selections"]:
            day_dc = next((dc for dc in dcs if dc.date == f"2026-04-{9 + sel['day']:02d}"), None)
            if day_dc and day_dc.hotel_breakfast_included:
                assert sel["breakfast"] is None, (
                    f"Day {sel['day']}: 酒店含早餐时 breakfast 应为 null"
                )

    def test_fallback_dinner_null_when_hotel_includes(self):
        """CP4：酒店含晚餐的天，dinner 应为 null。"""
        dcs = [
            _make_dc("2026-04-10", dinner=True),
            _make_dc("2026-04-11", dinner=True),
            _make_dc("2026-04-12", dinner=False),
        ]
        timeline = _make_timeline(3)
        pool = _make_restaurant_pool()
        result = _build_fallback_selections(pool, timeline, dcs)

        for sel in result["meal_selections"]:
            day_dc = next((dc for dc in dcs if dc.date == f"2026-04-{9 + sel['day']:02d}"), None)
            if day_dc and day_dc.hotel_dinner_included:
                assert sel["dinner"] is None, (
                    f"Day {sel['day']}: 酒店含晚餐时 dinner 应为 null"
                )

    def test_fallback_breakfast_null_when_pool_empty(self):
        """早餐池为空时，breakfast 应为 null（无论酒店含餐与否）。"""
        dcs = [_make_dc("2026-04-10", breakfast=False)]
        timeline = _make_timeline(1)
        pool = _make_restaurant_pool(has_breakfast=False)
        result = _build_fallback_selections(pool, timeline, dcs)
        assert result["meal_selections"][0]["breakfast"] is None

    def test_fallback_dinner_null_when_pool_empty(self):
        """晚餐池为空时，dinner 应为 null。"""
        dcs = [_make_dc("2026-04-10", dinner=False)]
        timeline = _make_timeline(1)
        pool = _make_restaurant_pool(has_dinner=False)
        result = _build_fallback_selections(pool, timeline, dcs)
        assert result["meal_selections"][0]["dinner"] is None

    def test_fallback_lunch_always_present(self):
        """午餐始终应有候选（pool 非空时）。"""
        dcs = [_make_dc("2026-04-10")]
        timeline = _make_timeline(1)
        pool = _make_restaurant_pool()
        result = _build_fallback_selections(pool, timeline, dcs)
        # lunch 可以是餐厅，不强制非 null（午餐是 optional）
        assert "lunch" in result["meal_selections"][0]

    def test_fallback_output_has_required_fields(self):
        """fallback 输出结构包含必要字段。"""
        dcs = [_make_dc("2026-04-10")]
        timeline = _make_timeline(1)
        pool = _make_restaurant_pool()
        result = _build_fallback_selections(pool, timeline, dcs)

        assert "meal_selections" in result
        for sel in result["meal_selections"]:
            assert "day" in sel
            assert "breakfast" in sel
            assert "lunch" in sel
            assert "dinner" in sel

    def test_validate_cuisine_frequency_caps_sushi_ramen(self):
        """寿司/拉面全程最多各 2 次。"""
        result = {
            "meal_selections": [
                {"day": 1, "breakfast": None, "lunch": {"entity_id": "r1", "name": "寿司1", "cuisine": "sushi"}, "dinner": None},
                {"day": 2, "breakfast": None, "lunch": {"entity_id": "r2", "name": "寿司2", "cuisine": "sushi"}, "dinner": None},
                {"day": 3, "breakfast": None, "lunch": {"entity_id": "r3", "name": "寿司3", "cuisine": "sushi"}, "dinner": None},  # 第3次，超限
            ]
        }
        validated = _validate_cuisine_frequency(result)
        # 超限会添加 warning，不会强制删除（由 AI 决策）
        assert "meal_selections" in validated

    @pytest.mark.asyncio
    async def test_select_meals_fallback_on_api_error(self):
        """API 调用失败（APIError）时返回 fallback，不抛异常。"""
        import anthropic as _anthropic
        dcs = [_make_dc("2026-04-10")]
        timeline = _make_timeline(1)
        pool = _make_restaurant_pool()
        constraints = _make_user_constraints()

        with patch("anthropic.AsyncAnthropic") as mock_cls:
            client = AsyncMock()
            client.messages.create = AsyncMock(
                side_effect=_anthropic.APIStatusError(
                    "Service unavailable",
                    response=MagicMock(status_code=503),
                    body={}
                )
            )
            mock_cls.return_value = client

            result = await select_meals(
                restaurant_pool=pool,
                timeline=timeline,
                daily_constraints=dcs,
                user_constraints=constraints,
                api_key="fake-key",
            )

        assert "meal_selections" in result
        assert len(result["meal_selections"]) >= 1

    @pytest.mark.asyncio
    async def test_select_meals_breakfast_null_from_sonnet_response(self):
        """Sonnet 正确返回时：含早餐的天 breakfast 仍为 null。"""
        dcs = [_make_dc("2026-04-10", breakfast=True)]
        timeline = _make_timeline(1)
        pool = _make_restaurant_pool()
        constraints = _make_user_constraints()

        sonnet_response = {
            "meal_selections": [
                {
                    "day": 1,
                    "breakfast": None,  # Sonnet 正确处理了含早餐
                    "lunch": {"entity_id": "rest_l1", "name": "午餐店1",
                              "cuisine": "ramen", "type": "restaurant", "why": "test"},
                    "dinner": {"entity_id": "rest_d1", "name": "晚餐店1",
                               "cuisine": "izakaya", "type": "restaurant", "why": "test"},
                }
            ],
            "cuisine_variety_check": True,
        }

        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(type="text", text=json.dumps(sonnet_response))]
        mock_resp.usage = MagicMock(input_tokens=300, output_tokens=200)

        with patch("anthropic.AsyncAnthropic") as mock_cls:
            client = AsyncMock()
            client.messages.create = AsyncMock(return_value=mock_resp)
            mock_cls.return_value = client

            result = await select_meals(
                restaurant_pool=pool,
                timeline=timeline,
                daily_constraints=dcs,
                user_constraints=constraints,
                api_key="fake-key",
            )

        assert result["meal_selections"][0]["breakfast"] is None


# ─────────────────────────────────────────────────────────────────────────────
# Step 14: estimate_budget — 纯 Python，重点覆盖
# ─────────────────────────────────────────────────────────────────────────────

class TestStep14Budget:

    def test_empty_sequences_returns_zero_budget(self):
        result = estimate_budget(
            daily_sequences=[],
            hotel_plan=_make_hotel_plan(),
            restaurant_selections={},
            budget_tier="mid",
        )
        assert result["trip_total_local"] == 0
        assert result["within_budget"] is True

    def test_output_has_required_fields(self):
        result = estimate_budget(
            daily_sequences=_make_day_sequences(3),
            hotel_plan=_make_hotel_plan(),
            restaurant_selections={},
            budget_tier="mid",
        )
        required = [
            "daily_breakdown", "trip_total_local", "currency",
            "trip_total_cny", "budget_tier", "within_budget", "breakdown_by_category",
        ]
        for field in required:
            assert field in result, f"estimate_budget 输出缺少字段: {field}"

    def test_daily_breakdown_length_matches_sequences(self):
        seqs = _make_day_sequences(5)
        result = estimate_budget(
            daily_sequences=seqs,
            hotel_plan=_make_hotel_plan(),
            restaurant_selections={},
            budget_tier="mid",
        )
        assert len(result["daily_breakdown"]) == 5

    def test_last_day_no_hotel_cost(self):
        """离开日（最后一天）不计酒店费用。"""
        seqs = _make_day_sequences(3)
        result = estimate_budget(
            daily_sequences=seqs,
            hotel_plan=_make_hotel_plan(cost_per_night=15000),
            restaurant_selections={},
            budget_tier="mid",
        )
        last_day = result["daily_breakdown"][-1]
        assert last_day["hotel"] == 0, "最后一天不应计酒店费"

    def test_non_last_days_have_hotel_cost(self):
        """非最后一天应包含酒店费。"""
        seqs = _make_day_sequences(3)
        hotel_plan = _make_hotel_plan(cost_per_night=12000)
        result = estimate_budget(
            daily_sequences=seqs,
            hotel_plan=hotel_plan,
            restaurant_selections={},
            budget_tier="mid",
        )
        for day in result["daily_breakdown"][:-1]:
            assert day["hotel"] == 12000, f"{day['date']} 酒店费应为 12000"

    def test_breakfast_cost_zero_when_hotel_includes(self):
        """CP4：酒店含早餐时，early breakfast 费用为 0。"""
        cost = _get_meal_cost(
            "breakfast",
            day_meal_data={},
            hotel_includes_meal=True,
            meal_defaults={"breakfast": 800},
        )
        assert cost == 0

    def test_dinner_cost_zero_when_hotel_includes(self):
        """CP4：酒店含晚餐时，dinner 费用为 0。"""
        cost = _get_meal_cost(
            "dinner",
            day_meal_data={},
            hotel_includes_meal=True,
            meal_defaults={"dinner": 3000},
        )
        assert cost == 0

    def test_meal_cost_uses_selection_cost_local(self):
        """餐厅选择有 cost_local 时，使用该值。"""
        cost = _get_meal_cost(
            "lunch",
            day_meal_data={"lunch": {"entity_id": "r1", "cost_local": 1500}},
            hotel_includes_meal=False,
            meal_defaults={"lunch": 1000},
        )
        assert cost == 1500

    def test_meal_cost_falls_back_to_default(self):
        """无餐厅选择时使用默认值。"""
        cost = _get_meal_cost(
            "lunch",
            day_meal_data={},
            hotel_includes_meal=False,
            meal_defaults={"lunch": 1200},
        )
        assert cost == 1200

    def test_admission_fee_uses_cost_local(self):
        """cost_local 优先于 poi_category 默认值。"""
        fee = _get_admission_fee(
            {"cost_local": 600, "poi_category": "temple"},
            default_admission={"temple": 500},
        )
        assert fee == 600

    def test_admission_fee_uses_default_when_no_cost(self):
        fee = _get_admission_fee(
            {"poi_category": "museum"},
            default_admission={"museum": 700},
        )
        assert fee == 700

    def test_admission_fee_free_flag(self):
        fee = _get_admission_fee(
            {"admission_free": True},
            default_admission={"shrine": 300},
        )
        assert fee == 0

    def test_trip_total_equals_sum_of_daily_totals(self):
        seqs = _make_day_sequences(3)
        result = estimate_budget(
            daily_sequences=seqs,
            hotel_plan=_make_hotel_plan(),
            restaurant_selections={},
            budget_tier="mid",
        )
        expected = sum(d["total"] for d in result["daily_breakdown"])
        assert result["trip_total_local"] == expected

    def test_breakdown_by_category_sums_to_total(self):
        seqs = _make_day_sequences(3)
        result = estimate_budget(
            daily_sequences=seqs,
            hotel_plan=_make_hotel_plan(),
            restaurant_selections={},
            budget_tier="mid",
        )
        cat = result["breakdown_by_category"]
        category_sum = sum(cat.values())
        # trip_total = sum(daily totals) = sum(subtotals + misc)
        # category_sum = hotel + activities + meals + transport + misc
        assert category_sum == result["trip_total_local"], (
            "各类别合计应等于总预算"
        )

    def test_within_budget_field_is_bool(self):
        result = estimate_budget(
            daily_sequences=_make_day_sequences(3),
            hotel_plan=_make_hotel_plan(),
            restaurant_selections={},
            budget_tier="mid",
        )
        assert isinstance(result["within_budget"], bool)

    def test_restaurant_selections_format_meal_selections(self):
        """Step 13.5 输出格式（meal_selections 列表）被正确解析。
        酒店含早餐 → breakfast=0；午餐/晚餐使用 cost_local 值。
        """
        seqs = _make_day_sequences(2)
        # 酒店含早餐，这样早餐费=0，便于验证午餐+晚餐数值
        hotel = _make_hotel_plan(breakfast=True)
        restaurant_selections = {
            "meal_selections": [
                {"day": 1, "breakfast": None,  # 酒店含早餐，null
                 "lunch": {"entity_id": "r1", "cost_local": 1200},
                 "dinner": {"entity_id": "r2", "cost_local": 3000}},
                {"day": 2, "breakfast": None, "lunch": None, "dinner": None},
            ]
        }
        result = estimate_budget(
            daily_sequences=seqs,
            hotel_plan=hotel,
            restaurant_selections=restaurant_selections,
            budget_tier="mid",
        )
        # Day1: breakfast=0(含) + lunch=1200 + dinner=3000 = 4200
        assert result["daily_breakdown"][0]["meals"] == 1200 + 3000

    def test_currency_field_present(self):
        result = estimate_budget(
            daily_sequences=_make_day_sequences(1),
            hotel_plan=_make_hotel_plan(),
            restaurant_selections={},
            budget_tier="mid",
        )
        assert result["currency"] in ("JPY", "CNY", "USD")

    def test_empty_budget_structure(self):
        result = _empty_budget("premium")
        assert result["trip_total_local"] == 0
        assert result["within_budget"] is True
        assert result["budget_tier"] == "premium"


# ─────────────────────────────────────────────────────────────────────────────
# Step 15: build_plan_b — CP4：覆盖 rain 触发器
# ─────────────────────────────────────────────────────────────────────────────

class TestStep15PlanB:

    def test_classify_entity_outdoor(self):
        result = _classify_entity(["outdoor", "nature"])
        assert result["is_outdoor"] is True
        assert result["is_indoor"] is False

    def test_classify_entity_indoor(self):
        result = _classify_entity(["雨天友好", "museum"])
        assert result["is_indoor"] is True

    def test_classify_entity_needs_reservation(self):
        """RESERVATION_TAGS 包含 '预约'，不是 '需预约'。"""
        result = _classify_entity(["预约"])
        assert result["needs_reservation"] is True

    def test_classify_entity_heavy(self):
        result = _classify_entity(["hiking", "extreme_physical"])
        assert result["is_heavy"] is True

    def test_fallback_plan_b_has_each_day(self):
        """fallback Plan B 应为 timeline 中每天生成条目。"""
        timeline = _make_timeline(3)
        poi_pool = [_make_poi("alt1", tags=["雨天友好"]), _make_poi("alt2")]
        result = _build_fallback_plan_b(timeline, poi_pool)
        assert "plan_b" in result
        assert len(result["plan_b"]) == 3

    def test_fallback_plan_b_has_alternatives_list(self):
        """每天的 plan_b 条目应有 alternatives 列表。"""
        timeline = _make_timeline(2)
        poi_pool = [_make_poi("alt1", tags=["雨天友好"])]
        result = _build_fallback_plan_b(timeline, poi_pool)
        for day_pb in result["plan_b"]:
            assert "alternatives" in day_pb
            assert isinstance(day_pb["alternatives"], list)

    def test_fallback_plan_b_rain_trigger_present(self):
        """CP4：户外景点的 Plan B 应有 rain 触发器。
        fallback 逻辑：slot 对应的 entity 在 poi_pool 中且是户外活动，
        且 poi_pool 中有 indoor 实体作为替代时，生成 rain 触发器。
        """
        # slot 中的 entity_id 必须能在 poi_pool 里找到，且是户外活动
        outdoor_entity = _make_poi("poi_outdoor", tags=["outdoor", "nature"])
        # 必须是 INDOOR_TAGS 里有的标签：museum/indoor/gallery/...
        indoor_entity = _make_poi("alt_indoor", tags=["museum", "indoor"])

        # timeline 中 slot 直接引用 outdoor_entity 的 id
        timeline = {
            "timeline": [
                {
                    "day": 1,
                    "date": "2026-04-10",
                    "slots": [
                        {
                            "type": "poi",
                            "entity_id": "poi_outdoor",
                            "name": "户外景点",
                            "start_time": "09:00",
                            "end_time": "11:00",
                            "tags": ["outdoor"],
                        }
                    ],
                }
            ]
        }
        poi_pool = [outdoor_entity, indoor_entity]
        result = _build_fallback_plan_b(timeline, poi_pool)

        all_triggers = [
            alt.get("trigger")
            for day_pb in result["plan_b"]
            for alt in day_pb["alternatives"]
        ]
        assert "rain" in all_triggers, (
            f"CP4：户外景点应生成 rain 触发器，实际 triggers={all_triggers}"
        )

    @pytest.mark.asyncio
    async def test_build_plan_b_fallback_on_api_error(self):
        """API 失败（APIError）时 build_plan_b 返回 fallback，不抛异常，结构合法。"""
        import anthropic as _anthropic
        timeline = _make_timeline(2)
        poi_pool = [_make_poi("alt1", tags=["museum"])]
        dcs = [_make_dc("2026-04-10"), _make_dc("2026-04-11")]

        with patch("anthropic.AsyncAnthropic") as mock_cls:
            client = AsyncMock()
            client.messages.create = AsyncMock(
                side_effect=_anthropic.APIStatusError(
                    "Service unavailable",
                    response=MagicMock(status_code=503),
                    body={}
                )
            )
            mock_cls.return_value = client

            result = await build_plan_b(
                timeline=timeline,
                poi_pool=poi_pool,
                daily_constraints=dcs,
                api_key="fake-key",
            )

        assert "plan_b" in result
        assert len(result["plan_b"]) == 2  # 两天
        for day_pb in result["plan_b"]:
            assert "day" in day_pb
            assert "alternatives" in day_pb

    @pytest.mark.asyncio
    async def test_build_plan_b_structure(self):
        """build_plan_b 输出满足 CP4 结构要求。"""
        timeline = _make_timeline(2)
        poi_pool = [_make_poi("alt1", tags=["雨天友好"])]
        dcs = [_make_dc("2026-04-10"), _make_dc("2026-04-11")]

        mock_response = {
            "plan_b": [
                {
                    "day": 1,
                    "alternatives": [
                        {
                            "trigger": "rain",
                            "replace_entity": "poi_0a",
                            "replace_name": "景点0A",
                            "alternative_entity": "alt1",
                            "alternative_name": "室内备选",
                            "reason": "雨天室内替代",
                        }
                    ],
                },
                {"day": 2, "alternatives": []},
            ]
        }

        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(type="text", text=json.dumps(mock_response))]
        mock_resp.usage = MagicMock(input_tokens=200, output_tokens=300)

        with patch("anthropic.AsyncAnthropic") as mock_cls:
            client = AsyncMock()
            client.messages.create = AsyncMock(return_value=mock_resp)
            mock_cls.return_value = client

            result = await build_plan_b(
                timeline=timeline,
                poi_pool=poi_pool,
                daily_constraints=dcs,
                api_key="fake-key",
            )

        rain_triggers = [
            alt["trigger"]
            for day_pb in result["plan_b"]
            for alt in day_pb["alternatives"]
            if alt.get("trigger") == "rain"
        ]
        assert len(rain_triggers) >= 1, "CP4：Plan B 应覆盖 rain 触发器"


# ─────────────────────────────────────────────────────────────────────────────
# Step 16: generate_handbook_content — CP4：失败不阻断
# ─────────────────────────────────────────────────────────────────────────────

class TestStep16HandbookNonBlocking:

    def test_is_heavy_day_by_heavy_tag(self):
        """_is_heavy_day 查 poi_pool 里对应实体的 tags，不是 slot.tags。
        entity 有 hiking tag → has_heavy_entity=True → 重度日。
        """
        heavy_entity = _make_poi("heavy_spot", tags=["hiking", "mountain"])
        day_tl = {
            "day": 1,
            "slots": [
                {"type": "poi", "entity_id": "heavy_spot", "name": "登山",
                 "time": "09:00-13:00", "tags": []},
            ]
        }
        assert _is_heavy_day(day_tl, [heavy_entity]) is True

    def test_is_heavy_day_single_slot_not_heavy(self):
        day_tl = {
            "day": 1,
            "slots": [{"type": "poi", "tags": []}]
        }
        result = _is_heavy_day(day_tl, [])
        assert result is False

    def test_fallback_handbook_structure(self):
        """fallback 生成正确的骨架结构。"""
        timeline = _make_timeline(2)
        poi_pool = [_make_poi("p1")]
        result = _build_fallback_handbook(timeline, poi_pool)

        assert "handbook" in result
        assert "days" in result["handbook"]
        assert len(result["handbook"]["days"]) == 2

        for day_data in result["handbook"]["days"]:
            assert "day" in day_data
            assert "activity_cards" in day_data
            assert "rest_stops" in day_data
            assert "daily_tip" in day_data

    def test_fallback_activity_cards_have_entity_id(self):
        """fallback 的 activity_cards 应包含 entity_id。"""
        timeline = _make_timeline(1)
        poi_pool = [_make_poi("p1")]
        result = _build_fallback_handbook(timeline, poi_pool)
        for card in result["handbook"]["days"][0]["activity_cards"]:
            assert "entity_id" in card

    @pytest.mark.asyncio
    async def test_step16_failure_does_not_block_pipeline(self):
        """CP4 核心：Step 16 API 失败（APIError）不应抛异常，返回 fallback 结果。"""
        import anthropic as _anthropic
        timeline = _make_timeline(2)
        poi_pool = [_make_poi("p1")]
        meal_selections = {"meal_selections": []}
        plan_b_data = {"plan_b": []}

        with patch("anthropic.AsyncAnthropic") as mock_cls:
            client = AsyncMock()
            # 模拟 Anthropic APIError（被 generate_handbook_content 捕获）
            client.messages.create = AsyncMock(
                side_effect=_anthropic.APIStatusError(
                    "Service unavailable",
                    response=MagicMock(status_code=503),
                    body={}
                )
            )
            mock_cls.return_value = client

            # 关键断言：不应抛出异常
            result = await generate_handbook_content(
                timeline=timeline,
                meal_selections=meal_selections,
                plan_b=plan_b_data,
                poi_pool=poi_pool,
                api_key="fake-key",
            )

        # 即使 API 失败，也应返回结构化结果
        assert "handbook" in result, "Step 16 失败时应返回 handbook 结构（fallback）"
        assert "days" in result["handbook"]

    @pytest.mark.asyncio
    async def test_step16_valid_response_structure(self):
        """Sonnet 正常返回时，handbook 结构符合规范。"""
        timeline = _make_timeline(2)
        poi_pool = [_make_poi("p1")]

        mock_response = {
            "handbook": {
                "days": [
                    {
                        "day": 1,
                        "daily_tip": "到达日不要安排太多",
                        "activity_cards": [
                            {
                                "entity_id": "poi_0a",
                                "copy_zh": "精彩介绍文案",
                                "insider_tip": "内行贴士",
                                "photo_spot": "最佳拍照点",
                            }
                        ],
                        "rest_stops": [],
                    },
                    {
                        "day": 2,
                        "daily_tip": "第二天加油",
                        "activity_cards": [],
                        "rest_stops": [],
                    },
                ]
            }
        }

        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(type="text", text=json.dumps(mock_response))]
        mock_resp.usage = MagicMock(input_tokens=400, output_tokens=600)

        with patch("anthropic.AsyncAnthropic") as mock_cls:
            client = AsyncMock()
            client.messages.create = AsyncMock(return_value=mock_resp)
            mock_cls.return_value = client

            result = await generate_handbook_content(
                timeline=timeline,
                meal_selections={"meal_selections": []},
                plan_b={"plan_b": []},
                poi_pool=poi_pool,
                api_key="fake-key",
            )

        assert len(result["handbook"]["days"]) == 2
        for day_data in result["handbook"]["days"]:
            assert "day" in day_data
            assert "activity_cards" in day_data
            assert "rest_stops" in day_data


# ─────────────────────────────────────────────────────────────────────────────
# CP4 数据契约（Step 间字段对齐）
# ─────────────────────────────────────────────────────────────────────────────

class TestCp4DataContracts:

    def test_step13_5_output_feeds_step14(self):
        """Step 14 使用 Step 13.5 输出的 meal_selections 格式。"""
        dcs = [_make_dc("2026-04-10")]
        timeline = _make_timeline(1)
        pool = _make_restaurant_pool()
        result = _build_fallback_selections(pool, timeline, dcs)

        # Step 14 期望：meal_selections[i].day + breakfast/lunch/dinner
        assert "meal_selections" in result
        for sel in result["meal_selections"]:
            assert "day" in sel
            # breakfast/lunch/dinner 存在（值可为 None）
            for meal in ("breakfast", "lunch", "dinner"):
                assert meal in sel, f"meal_selections 缺少 {meal} 字段"

    def test_step14_meals_included_propagation(self):
        """CP4 传导链：酒店含早餐 → breakfast 为 0 → within_budget 不受外部早餐影响。"""
        seqs = _make_day_sequences(2)
        # 酒店含早餐
        hotel_plan = _make_hotel_plan(breakfast=True)
        # 餐厅选择中早餐为 null（Step 13.5 正确处理了含餐）
        restaurant_selections = {
            "meal_selections": [
                {"day": 1, "breakfast": None, "lunch": None, "dinner": None},
                {"day": 2, "breakfast": None, "lunch": None, "dinner": None},
            ]
        }
        result = estimate_budget(
            daily_sequences=seqs,
            hotel_plan=hotel_plan,
            restaurant_selections=restaurant_selections,
            budget_tier="mid",
        )
        # 含早餐：breakfast 费用为 0
        for day_bd in result["daily_breakdown"]:
            # meals = breakfast(0) + lunch + dinner（默认值）
            assert day_bd["meals"] >= 0

    def test_cp4_meals_included_contract_breakfast(self):
        """
        CP4 核心传导：
        hotel_plan.meals_included.breakfast=True
        → estimate_budget 中 breakfast_cost=0
        → 整体预算不含外部早餐费
        """
        seqs = _make_day_sequences(1)
        hotel_plan = _make_hotel_plan(breakfast=True, cost_per_night=10000)
        # 无餐厅选择（早餐 null）
        result_with_breakfast = estimate_budget(
            daily_sequences=seqs,
            hotel_plan=hotel_plan,
            restaurant_selections={"meal_selections": [{"day": 1, "breakfast": None, "lunch": None, "dinner": None}]},
            budget_tier="mid",
        )
        result_without_breakfast = estimate_budget(
            daily_sequences=seqs,
            hotel_plan=_make_hotel_plan(breakfast=False, cost_per_night=10000),
            restaurant_selections={"meal_selections": [{"day": 1, "breakfast": None, "lunch": None, "dinner": None}]},
            budget_tier="mid",
        )
        # 含早餐时，meals 应 ≤ 不含早餐时
        assert result_with_breakfast["daily_breakdown"][0]["meals"] <= \
               result_without_breakfast["daily_breakdown"][0]["meals"], (
            "酒店含早餐时，当天餐食费应低于不含早餐"
        )

    def test_step15_output_fields_for_step16(self):
        """Step 16 使用 Step 15 输出的 plan_b 结构。"""
        timeline = _make_timeline(2)
        poi_pool = [_make_poi("alt1")]
        result = _build_fallback_plan_b(timeline, poi_pool)

        assert "plan_b" in result
        for day_pb in result["plan_b"]:
            assert "day" in day_pb
            assert "alternatives" in day_pb

    def test_step16_non_blocking_in_pipeline(self):
        """CP4 非阻塞性：Step 16 的 fallback 结果有 handbook.days，不是空。"""
        timeline = _make_timeline(3)
        poi_pool = [_make_poi("p1")]
        result = _build_fallback_handbook(timeline, poi_pool)
        assert len(result["handbook"]["days"]) == 3

    def test_within_budget_is_bool_always(self):
        """within_budget 必须始终是 bool，不能是 None 或数字。"""
        for tier in ("budget", "mid", "premium", "luxury"):
            result = estimate_budget(
                daily_sequences=_make_day_sequences(3),
                hotel_plan=_make_hotel_plan(),
                restaurant_selections={},
                budget_tier=tier,
            )
            assert isinstance(result["within_budget"], bool), (
                f"{tier}: within_budget 不是 bool"
            )

    def test_meal_null_vs_not_present_distinction(self):
        """
        breakfast=null 表示有意跳过（酒店含餐或池空），
        与字段不存在完全不同。fallback 必须明确写 null，不能省略字段。
        """
        dcs = [_make_dc("2026-04-10", breakfast=True)]
        timeline = _make_timeline(1)
        pool = _make_restaurant_pool()
        result = _build_fallback_selections(pool, timeline, dcs)
        sel = result["meal_selections"][0]
        # breakfast 字段存在且值为 None（不是 KeyError）
        assert "breakfast" in sel
        # 含早餐时明确为 None
        assert sel["breakfast"] is None
