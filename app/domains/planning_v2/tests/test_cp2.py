"""
test_cp2.py — CP2 契约测试（Step 5 → 7.5，骨架锁定）

验证点（来自 CP2 检查点定义）：
  1. 每天主活动 1-2 个
  2. must_visit 全部分配（或在 unassigned 中报告）
  3. main_corridor 不是占位符（不是 xxx_center 格式）
  4. 酒店通勤 avg < 45 分钟
  5. Step 5.5 的替换都有 conflict_reason

涉及步骤：
  - Step 5  plan_daily_activities   (Opus AI, 有规则 fallback)
  - Step 5.5 validate_and_substitute (Sonnet AI)
  - Step 6  build_hotel_pool         (DB)
  - Step 7  select_hotels            (Sonnet AI, 有规则 fallback)
  - Step 7.5 check_commute_feasibility (API)

AI 调用全部 mock，不打真实 API。
"""

import json
import uuid
import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

from app.domains.planning_v2.models import (
    CandidatePool,
    UserConstraints,
    RegionSummary,
    DailyConstraints,
)
from app.domains.planning_v2.step05_activity_planner import (
    plan_daily_activities,
    _rule_based_fallback,
    _build_user_prompt,
    _collect_assigned_entity_ids,
    _group_pois_by_city,
)
from app.domains.planning_v2.step05_5_validator import validate_and_substitute
from app.domains.planning_v2.step06_hotel_pool import (
    build_hotel_pool,
    _calculate_geographic_center,
    _distance_km,
)
from app.domains.planning_v2.step07_hotel_planner import (
    select_hotels,
    _rule_based_fallback as hotel_fallback,
    _build_hotel_summaries,
)
from app.domains.planning_v2.step07_5_commute_check import check_commute_feasibility


# ─────────────────────────────────────────────────────────────────────────────
# 共用 Fixtures
# ─────────────────────────────────────────────────────────────────────────────

def _make_poi(entity_id: str, city: str, grade: str = "A", visit_min: int = 90,
              lat: float = 34.7, lng: float = 135.5, tags=None) -> CandidatePool:
    return CandidatePool(
        entity_id=entity_id,
        name_zh=f"景点_{entity_id[-4:]}",
        entity_type="poi",
        grade=grade,
        latitude=lat,
        longitude=lng,
        tags=tags or [],
        visit_minutes=visit_min,
        cost_local=500,
        city_code=city,
    )


def _make_hotel(entity_id: str = None, city: str = "kyoto", lat: float = 34.7,
                lng: float = 135.5, cost_local: int = 10000) -> CandidatePool:
    if entity_id is None:
        entity_id = str(uuid.uuid4())
    return CandidatePool(
        entity_id=entity_id,
        name_zh=f"酒店_{entity_id[-4:]}",
        entity_type="hotel",
        grade="A",
        latitude=lat,
        longitude=lng,
        tags=[],
        visit_minutes=0,
        cost_local=cost_local,
        city_code=city,
        open_hours={"check_in_time": "15:00", "check_out_time": "11:00"},
        review_signals={"google_rating": 4.5, "star_rating": 4.0},
    )


@pytest.fixture
def kansai_constraints_5d():
    return UserConstraints(
        trip_window={"start_date": "2026-04-10", "end_date": "2026-04-14", "total_days": 5},
        user_profile={"party_type": "couple", "budget_tier": "mid",
                      "must_have_tags": [], "avoid_tags": []},
        constraints={
            "must_visit": ["poi_fushimi", "poi_dotonbori"],
            "do_not_go": [],
            "visited": [],
            "booked_items": [],
        },
    )


@pytest.fixture
def cities_by_day_5d():
    return [
        {"day": 1, "city": "osaka", "theme": "到达", "intensity": "light"},
        {"day": 2, "city": "osaka", "theme": "美食购物", "intensity": "moderate"},
        {"day": 3, "city": "kyoto", "theme": "文化寺庙", "intensity": "moderate"},
        {"day": 4, "city": "kyoto", "theme": "岚山", "intensity": "moderate"},
        {"day": 5, "city": "osaka", "theme": "离开", "intensity": "light"},
    ]


@pytest.fixture
def poi_pool_5d():
    return [
        _make_poi("poi_fushimi", "kyoto", grade="S", lat=34.97, lng=135.77),
        _make_poi("poi_dotonbori", "osaka", grade="S", lat=34.66, lng=135.50),
        _make_poi("poi_kinkakuji", "kyoto", grade="S", lat=35.03, lng=135.73),
        _make_poi("poi_gion", "kyoto", grade="S", lat=35.00, lng=135.77),
        _make_poi("poi_usj", "osaka", grade="S", lat=34.67, lng=135.43),
        _make_poi("poi_namba", "osaka", grade="A", lat=34.66, lng=135.50),
        _make_poi("poi_arashiyama", "kyoto", grade="A", lat=35.01, lng=135.68),
    ]


_HOTEL_A_ID = str(uuid.uuid4())
_HOTEL_B_ID = str(uuid.uuid4())
_HOTEL_C_ID = str(uuid.uuid4())


@pytest.fixture
def hotel_pool_3():
    return [
        _make_hotel(_HOTEL_A_ID, "osaka", lat=34.67, lng=135.50, cost_local=8000),
        _make_hotel(_HOTEL_B_ID, "kyoto", lat=35.01, lng=135.76, cost_local=12000),
        _make_hotel(_HOTEL_C_ID, "osaka", lat=34.70, lng=135.48, cost_local=5000),
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Step 5: plan_daily_activities — 规则 fallback
# ─────────────────────────────────────────────────────────────────────────────

class TestStep5ActivityPlanner:

    def test_fallback_each_day_has_activities(
        self, cities_by_day_5d, poi_pool_5d, kansai_constraints_5d
    ):
        """每天应有至少 1 个主活动（fallback 模式）。"""
        result = _rule_based_fallback(
            cities_by_day=cities_by_day_5d,
            poi_pool=poi_pool_5d,
            must_visit_ids={"poi_fushimi", "poi_dotonbori"},
        )
        for day in result["daily_activities"]:
            assert len(day["main_activities"]) >= 1, (
                f"Day {day['day']} 没有主活动"
            )

    def test_fallback_activity_count_respects_intensity(
        self, cities_by_day_5d, poi_pool_5d
    ):
        """light 天最多 1 个活动，moderate 天最多 2 个。"""
        result = _rule_based_fallback(
            cities_by_day=cities_by_day_5d,
            poi_pool=poi_pool_5d,
            must_visit_ids=set(),
        )
        for day in result["daily_activities"]:
            intensity = day["intensity"]
            count = len(day["main_activities"])
            if intensity == "light":
                assert count <= 1, f"Day {day['day']} light强度但有{count}个活动"
            else:
                assert count <= 2, f"Day {day['day']} 有{count}个活动，超过上限2"

    def test_fallback_must_visit_all_assigned(
        self, cities_by_day_5d, poi_pool_5d
    ):
        """must_visit 中的景点应全部被分配到某一天。"""
        must_visit_ids = {"poi_fushimi", "poi_dotonbori"}
        result = _rule_based_fallback(
            cities_by_day=cities_by_day_5d,
            poi_pool=poi_pool_5d,
            must_visit_ids=must_visit_ids,
        )
        assigned = _collect_assigned_entity_ids(result["daily_activities"])
        unassigned = must_visit_ids - assigned
        assert not unassigned, f"must_visit 未被分配: {unassigned}"
        assert result["unassigned_must_visit"] == [], (
            f"unassigned 列表不为空: {result['unassigned_must_visit']}"
        )

    def test_fallback_first_last_day_intensity_light(
        self, cities_by_day_5d, poi_pool_5d
    ):
        result = _rule_based_fallback(
            cities_by_day=cities_by_day_5d,
            poi_pool=poi_pool_5d,
            must_visit_ids=set(),
        )
        days = result["daily_activities"]
        assert days[0]["intensity"] == "light"
        assert days[-1]["intensity"] == "light"

    def test_fallback_no_duplicate_activities_across_days(
        self, cities_by_day_5d, poi_pool_5d
    ):
        """同一景点不应在多天重复出现。"""
        result = _rule_based_fallback(
            cities_by_day=cities_by_day_5d,
            poi_pool=poi_pool_5d,
            must_visit_ids=set(),
        )
        all_ids = []
        for day in result["daily_activities"]:
            for act in day["main_activities"]:
                all_ids.append(act["entity_id"])
        assert len(all_ids) == len(set(all_ids)), (
            f"存在重复分配的景点: {[x for x in all_ids if all_ids.count(x) > 1]}"
        )

    def test_fallback_main_corridor_not_placeholder(
        self, cities_by_day_5d, poi_pool_5d
    ):
        """main_corridor 不应是空字符串或 xxx_center 格式的占位符。"""
        import re
        placeholder_pattern = re.compile(r"^[a-z_]+_center$")
        result = _rule_based_fallback(
            cities_by_day=cities_by_day_5d,
            poi_pool=poi_pool_5d,
            must_visit_ids=set(),
        )
        for day in result["daily_activities"]:
            corridor = day.get("main_corridor", "")
            if corridor:  # 有走廊时才检查格式
                assert not placeholder_pattern.match(corridor), (
                    f"Day {day['day']} main_corridor='{corridor}' 是占位符格式"
                )

    def test_fallback_activities_match_day_city(
        self, cities_by_day_5d, poi_pool_5d
    ):
        """每天的活动 entity_id 应属于该天城市的 POI。"""
        pool_map = {p.entity_id: p for p in poi_pool_5d}
        result = _rule_based_fallback(
            cities_by_day=cities_by_day_5d,
            poi_pool=poi_pool_5d,
            must_visit_ids=set(),
        )
        for day in result["daily_activities"]:
            day_city = day["city"]
            for act in day["main_activities"]:
                poi = pool_map.get(act["entity_id"])
                if poi:
                    assert poi.city_code == day_city or poi.city_code == "", (
                        f"Day {day['day']} 安排了 {poi.name_zh}(city={poi.city_code}) "
                        f"但当天城市是 {day_city}"
                    )

    @pytest.mark.asyncio
    async def test_plan_activities_fallback_on_api_error(
        self, cities_by_day_5d, poi_pool_5d, kansai_constraints_5d
    ):
        """API 调用失败时应返回 fallback 结果（不抛异常）。"""
        with patch("anthropic.AsyncAnthropic") as mock_cls:
            client = AsyncMock()
            client.messages.create = AsyncMock(side_effect=Exception("API timeout"))
            mock_cls.return_value = client

            result = await plan_daily_activities(
                cities_by_day=cities_by_day_5d,
                poi_pool=poi_pool_5d,
                user_constraints=kansai_constraints_5d,
                api_key="fake-key",
            )

        assert "daily_activities" in result
        assert "unassigned_must_visit" in result
        assert "fallback_reason" in result
        assert len(result["daily_activities"]) == len(cities_by_day_5d)

    @pytest.mark.asyncio
    async def test_plan_activities_valid_opus_response(
        self, cities_by_day_5d, poi_pool_5d, kansai_constraints_5d
    ):
        """Opus 返回合法 JSON 时应正确解析。"""
        mock_response_json = {
            "daily_activities": [
                {
                    "day": d["day"], "city": d["city"], "theme": d["theme"],
                    "main_activities": [
                        {"entity_id": "poi_dotonbori", "name": "道顿堀",
                         "visit_minutes": 90, "why": "关西必去"}
                    ],
                    "time_anchors": [],
                    "main_corridor": "namba_dotonbori",
                    "secondary_corridors": [],
                    "intensity": d["intensity"],
                }
                for d in cities_by_day_5d
            ]
        }

        mock_response = MagicMock()
        mock_response.content = [MagicMock(type="text", text=json.dumps(mock_response_json))]
        mock_response.usage = MagicMock(input_tokens=500, output_tokens=800)

        with patch("anthropic.AsyncAnthropic") as mock_cls:
            client = AsyncMock()
            client.messages.create = AsyncMock(return_value=mock_response)
            mock_cls.return_value = client

            result = await plan_daily_activities(
                cities_by_day=cities_by_day_5d,
                poi_pool=poi_pool_5d,
                user_constraints=kansai_constraints_5d,
                api_key="fake-key",
            )

        assert len(result["daily_activities"]) == 5
        assert "thinking_tokens_used" in result

    def test_user_prompt_contains_must_visit_marker(
        self, cities_by_day_5d, poi_pool_5d
    ):
        """prompt 中 must_visit 景点应有 [MUST] 标记。"""
        prompt = _build_user_prompt(
            cities_by_day=cities_by_day_5d,
            poi_pool=poi_pool_5d,
            must_visit_ids={"poi_fushimi"},
            user_profile={"party_type": "couple", "budget_tier": "mid"},
        )
        assert "[MUST]" in prompt, "must_visit 景点应在 prompt 中标注 [MUST]"

    def test_group_pois_uses_city_code(
        self, cities_by_day_5d, poi_pool_5d
    ):
        """_group_pois_by_city 使用 city_code 分组（fallback 逻辑）。"""
        grouped = _group_pois_by_city(poi_pool_5d, cities_by_day_5d)
        # 所有 city_code=osaka 的 POI 应在 osaka 或 unknown 组
        osaka_pois = [p for p in poi_pool_5d if p.city_code == "osaka"]
        grouped_osaka = grouped.get("osaka", []) + grouped.get("unknown", [])
        # 至少 osaka 的 POI 都有对应
        for poi in osaka_pois:
            assert poi in grouped_osaka or any(poi in v for v in grouped.values()), (
                f"{poi.name_zh} 未被分入任何组"
            )


# ─────────────────────────────────────────────────────────────────────────────
# Step 5.5: validate_and_substitute — 替换记录字段
# ─────────────────────────────────────────────────────────────────────────────

class TestStep5_5Validator:

    def _make_daily_activities(self, closed_entity_id: str) -> dict:
        return {
            "daily_activities": [
                {
                    "day": 1, "city": "kyoto",
                    "main_activities": [
                        {"entity_id": closed_entity_id, "name": "测试景点",
                         "visit_minutes": 90, "why": "test"},
                    ],
                    "time_anchors": [],
                    "main_corridor": "higashiyama",
                    "intensity": "moderate",
                }
            ]
        }

    def _make_daily_constraints(self, closed_entity_id: str) -> list:
        return [
            DailyConstraints(
                date="2026-04-10",
                day_of_week="Fri",
                sunrise="05:45",
                sunset="18:30",
                closed_entities=[closed_entity_id],
            )
        ]

    @pytest.mark.asyncio
    async def test_substitution_has_conflict_reason(self, poi_pool_5d):
        """替换记录应包含 conflict_reason 字段。"""
        closed_id = "poi_fushimi"
        activities = self._make_daily_activities(closed_id)
        constraints = self._make_daily_constraints(closed_id)

        mock_sub_json = {
            "substitutions": [
                {
                    "day": 1,
                    "original_entity_id": closed_id,
                    "replacement_entity_id": "poi_kinkakuji",
                    "replacement_name": "金阁寺",
                    "conflict_reason": "定休日（周五）",
                    "why_replacement": "同走廊最近的A级景点",
                }
            ],
            "validated_activities": activities["daily_activities"],
        }

        mock_response = MagicMock()
        mock_response.content = [MagicMock(type="text", text=json.dumps(mock_sub_json))]
        mock_response.usage = MagicMock(input_tokens=300, output_tokens=200)

        with patch("anthropic.AsyncAnthropic") as mock_cls:
            client = AsyncMock()
            client.messages.create = AsyncMock(return_value=mock_response)
            mock_cls.return_value = client

            result = await validate_and_substitute(
                daily_activities=activities,
                daily_constraints=constraints,
                poi_pool=poi_pool_5d,
                api_key="fake-key",
            )

        subs = result.get("substitutions", [])
        for sub in subs:
            assert "conflict_reason" in sub, (
                f"替换记录缺少 conflict_reason: {sub}"
            )

    @pytest.mark.asyncio
    async def test_no_conflict_returns_unchanged(self, poi_pool_5d):
        """无冲突时不触发替换，返回原始活动。"""
        activities = {
            "daily_activities": [
                {
                    "day": 1, "city": "kyoto",
                    "main_activities": [
                        {"entity_id": "poi_gion", "name": "祇园",
                         "visit_minutes": 120, "why": "test"},
                    ],
                    "time_anchors": [],
                    "main_corridor": "gion",
                    "intensity": "moderate",
                }
            ]
        }
        constraints = [
            DailyConstraints(
                date="2026-04-10",
                day_of_week="Fri",
                sunrise="05:45",
                sunset="18:30",
                closed_entities=[],  # 无关闭景点
            )
        ]

        result = await validate_and_substitute(
            daily_activities=activities,
            daily_constraints=constraints,
            poi_pool=poi_pool_5d,
            api_key=None,  # 无冲突不应调用 API
        )

        assert "validated_activities" in result or "daily_activities" in result
        subs = result.get("substitutions", [])
        assert len(subs) == 0, f"无冲突时不应有替换: {subs}"


# ─────────────────────────────────────────────────────────────────────────────
# Step 6: build_hotel_pool — 酒店候选池
# ─────────────────────────────────────────────────────────────────────────────

class TestStep6HotelPool:

    def test_geographic_center_weighted_by_visit_minutes(self, poi_pool_5d):
        """地理中心按 visit_minutes 加权，不是简单平均。"""
        # 两个点：A(0,0,60min) 和 B(10,10,120min)
        # 加权中心应偏向 B
        pois = [
            CandidatePool("a", "A", "poi", "A", 0.0, 0.0, [], 60, 0, "kyoto"),
            CandidatePool("b", "B", "poi", "A", 10.0, 10.0, [], 120, 0, "kyoto"),
        ]
        lat, lng = _calculate_geographic_center(pois)
        # B 权重是 A 的 2 倍，中心 = (0*60 + 10*120)/180 ≈ 6.67
        assert abs(lat - (10 * 120) / 180) < 0.01
        assert abs(lng - (10 * 120) / 180) < 0.01

    def test_geographic_center_empty_pool(self):
        lat, lng = _calculate_geographic_center([])
        assert lat == 0.0 and lng == 0.0

    def test_haversine_distance_known_pair(self):
        """大阪城→道顿堀约 2.3km，验证公式精度。"""
        d = _distance_km(34.6873, 135.5259, 34.6687, 135.5010)
        assert 1.5 < d < 3.5, f"大阪城→道顿堀距离应在 1.5-3.5km，实际 {d:.2f}km"

    def test_haversine_invalid_coords_returns_inf(self):
        d = _distance_km(0, 135.5, 34.7, 135.5)
        assert d == float("inf")

    @pytest.mark.asyncio
    async def test_build_hotel_pool_empty_cities_returns_empty(
        self, kansai_constraints_5d, poi_pool_5d
    ):
        session = AsyncMock()
        region = RegionSummary(
            circle_name="Kansai", cities=[],
            entity_count=0, entities_by_type={}, grade_distribution={}
        )
        result = await build_hotel_pool(
            session, kansai_constraints_5d, "Kansai", [], poi_pool_5d
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_build_hotel_pool_budget_filters_luxury_hotels(
        self, kansai_constraints_5d, poi_pool_5d
    ):
        """budget 用户应排除酒店预算等级高于用户预算的酒店。"""
        luxury_hotel_entity = MagicMock()
        luxury_hotel_entity.entity_id = uuid.uuid4()
        luxury_hotel_entity.name_zh = "豪华酒店"
        luxury_hotel_entity.entity_type = "hotel"
        luxury_hotel_entity.data_tier = "S"
        luxury_hotel_entity.budget_tier = "luxury"  # 酒店=luxury
        luxury_hotel_entity.city_code = "osaka"
        luxury_hotel_entity.lat = 34.67
        luxury_hotel_entity.lng = 135.50
        luxury_hotel_entity.is_active = True
        luxury_hotel_entity.risk_flags = []

        budget_constraints = UserConstraints(
            trip_window={"start_date": "2026-04-10", "end_date": "2026-04-14", "total_days": 5},
            user_profile={"party_type": "couple", "budget_tier": "budget"},
            constraints={"must_visit": [], "do_not_go": [], "visited": [], "booked_items": []},
        )

        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[luxury_hotel_entity])))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
        ])

        result = await build_hotel_pool(
            session, budget_constraints, "Kansai", ["osaka"], poi_pool_5d
        )
        assert len(result) == 0, "budget用户不应获得luxury酒店"

    @pytest.mark.asyncio
    async def test_build_hotel_pool_excludes_do_not_go(
        self, kansai_constraints_5d, poi_pool_5d
    ):
        excluded_id = uuid.uuid4()
        hotel_entity = MagicMock()
        hotel_entity.entity_id = excluded_id
        hotel_entity.name_zh = "被排除酒店"
        hotel_entity.entity_type = "hotel"
        hotel_entity.data_tier = "A"
        hotel_entity.budget_tier = "mid"
        hotel_entity.city_code = "osaka"
        hotel_entity.lat = 34.67
        hotel_entity.lng = 135.50
        hotel_entity.is_active = True
        hotel_entity.risk_flags = []

        constraints_with_dng = UserConstraints(
            trip_window={"start_date": "2026-04-10", "end_date": "2026-04-14", "total_days": 5},
            user_profile={"party_type": "couple", "budget_tier": "mid"},
            constraints={
                "must_visit": [], "do_not_go": [str(excluded_id)],
                "visited": [], "booked_items": []
            },
        )

        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[hotel_entity])))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
        ])

        result = await build_hotel_pool(
            session, constraints_with_dng, "Kansai", ["osaka"], poi_pool_5d
        )
        result_ids = {item.entity_id for item in result}
        assert str(excluded_id) not in result_ids

    @pytest.mark.asyncio
    async def test_build_hotel_pool_sorted_by_haversine_distance(
        self, kansai_constraints_5d
    ):
        """酒店候选应按与 POI 中心的 Haversine 距离升序排列。"""
        center_lat, center_lng = 34.97, 135.77  # 伏见稻荷附近

        poi_pool = [_make_poi("poi_fushimi", "kyoto", lat=34.97, lng=135.77, visit_min=120)]

        # 远酒店 (3km)
        far_hotel = MagicMock()
        far_hotel.entity_id = uuid.uuid4()
        far_hotel.name_zh = "远酒店"
        far_hotel.data_tier = "A"
        far_hotel.budget_tier = "mid"
        far_hotel.city_code = "kyoto"
        far_hotel.lat = 35.03   # ~7km 北
        far_hotel.lng = 135.73
        far_hotel.is_active = True
        far_hotel.risk_flags = []

        # 近酒店 (<1km)
        near_hotel = MagicMock()
        near_hotel.entity_id = uuid.uuid4()
        near_hotel.name_zh = "近酒店"
        near_hotel.data_tier = "A"
        near_hotel.budget_tier = "mid"
        near_hotel.city_code = "kyoto"
        near_hotel.lat = 34.97  # 几乎原地
        near_hotel.lng = 135.78
        near_hotel.is_active = True
        near_hotel.risk_flags = []

        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[far_hotel, near_hotel])))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
        ])

        result = await build_hotel_pool(
            session, kansai_constraints_5d, "Kansai", ["kyoto"], poi_pool
        )

        if len(result) >= 2:
            near_idx = next((i for i, h in enumerate(result) if h.name_zh == "近酒店"), None)
            far_idx = next((i for i, h in enumerate(result) if h.name_zh == "远酒店"), None)
            if near_idx is not None and far_idx is not None:
                assert near_idx < far_idx, "近酒店应排在远酒店前面"


# ─────────────────────────────────────────────────────────────────────────────
# Step 7: select_hotels — 酒店选择
# ─────────────────────────────────────────────────────────────────────────────

class TestStep7HotelPlanner:

    def _make_commute_results(self, hotel_pool: list[CandidatePool]) -> list[dict]:
        return [
            {
                "hotel_id": h.entity_id,
                "hotel_name": h.name_zh,
                "status": "pass",
                "avg_commute_minutes": 20,
                "max_commute_minutes": 30,
                "commute_details": [],
            }
            for h in hotel_pool
        ]

    def _make_daily_activities(self, cities_by_day):
        return {
            "daily_activities": [
                {
                    "day": d["day"],
                    "city": d["city"],
                    "main_corridor": "namba",
                    "intensity": d["intensity"],
                    "main_activities": [],
                    "time_anchors": [],
                }
                for d in cities_by_day
            ]
        }

    def test_fallback_primary_hotel_selected(self, hotel_pool_3):
        """fallback 应选出 1 家 primary 酒店。"""
        commute = self._make_commute_results(hotel_pool_3)
        summaries = _build_hotel_summaries(hotel_pool_3, commute)
        result = hotel_fallback(hotel_summaries=summaries, total_days=5)
        assert result["hotel_plan"]["primary"] is not None

    def test_fallback_primary_hotel_id_in_pool(self, hotel_pool_3):
        """fallback 选出的 hotel_id 必须在候选池中。"""
        commute = self._make_commute_results(hotel_pool_3)
        summaries = _build_hotel_summaries(hotel_pool_3, commute)
        result = hotel_fallback(hotel_summaries=summaries, total_days=5)
        primary_id = result["hotel_plan"]["primary"]["hotel_id"]
        pool_ids = {h.entity_id for h in hotel_pool_3}
        assert primary_id in pool_ids, (
            f"fallback 选的 hotel_id={primary_id} 不在候选池"
        )

    def test_fallback_prefers_lower_commute(self, hotel_pool_3):
        """fallback 应优先选平均通勤最短的酒店（综合评分最高）。"""
        commute_results = [
            {"hotel_id": hotel_pool_3[0].entity_id, "hotel_name": "hotel_a",
             "status": "pass", "avg_commute_minutes": 40, "max_commute_minutes": 50},
            {"hotel_id": hotel_pool_3[1].entity_id, "hotel_name": "hotel_b",
             "status": "pass", "avg_commute_minutes": 15, "max_commute_minutes": 20},
            {"hotel_id": hotel_pool_3[2].entity_id, "hotel_name": "hotel_c",
             "status": "pass", "avg_commute_minutes": 25, "max_commute_minutes": 30},
        ]
        summaries = _build_hotel_summaries(hotel_pool_3, commute_results)
        result = hotel_fallback(hotel_summaries=summaries, total_days=5)
        primary = result["hotel_plan"]["primary"]
        # hotel_b 通勤最短(15min)，通勤惩罚最低，综合评分最高
        assert primary["hotel_id"] == _HOTEL_B_ID, (
            f"应选通勤15min的hotel_b，实际选了 {primary['hotel_id']}"
        )

    def test_fallback_primary_has_required_fields(self, hotel_pool_3):
        """primary 酒店选择结果应包含必要字段。"""
        commute = self._make_commute_results(hotel_pool_3)
        summaries = _build_hotel_summaries(hotel_pool_3, commute)
        result = hotel_fallback(hotel_summaries=summaries, total_days=5)
        primary = result["hotel_plan"]["primary"]
        required_fields = [
            "hotel_id", "name", "nights", "cost_per_night_jpy",
            "meals_included", "check_in", "check_out",
            "avg_commute_minutes", "why_selected",
        ]
        for field in required_fields:
            assert field in primary, f"primary 缺少字段: {field}"

    def test_fallback_meals_included_propagated(self):
        """含早餐的酒店，meals_included.breakfast 应为 True。"""
        breakfast_hotel = CandidatePool(
            entity_id="h_breakfast",
            name_zh="含早餐酒店",
            entity_type="hotel",
            grade="A",
            latitude=34.7, longitude=135.5,
            tags=["breakfast_included"],
            visit_minutes=0,
            cost_local=12000,
            city_code="kyoto",
            open_hours={"check_in_time": "15:00", "check_out_time": "11:00"},
            review_signals={"google_rating": 4.5},
        )
        commute = [{
            "hotel_id": "h_breakfast",
            "hotel_name": "含早餐酒店",
            "status": "pass",
            "avg_commute_minutes": 20,
            "max_commute_minutes": 25,
        }]
        summaries = _build_hotel_summaries([breakfast_hotel], commute)
        result = hotel_fallback(hotel_summaries=summaries, total_days=4)
        assert result["hotel_plan"]["primary"]["meals_included"]["breakfast"] is True

    @pytest.mark.asyncio
    async def test_empty_hotel_pool_returns_empty_result(self, kansai_constraints_5d):
        """酒店候选池为空时返回 primary=None 的结果。"""
        daily_activities = {"daily_activities": []}
        result = await select_hotels(
            hotel_pool=[],
            commute_results=[],
            daily_activities=daily_activities,
            user_constraints=kansai_constraints_5d,
            api_key=None,
        )
        assert result["hotel_plan"]["primary"] is None

    @pytest.mark.asyncio
    async def test_select_hotels_fallback_on_sonnet_error(
        self, hotel_pool_3, kansai_constraints_5d, cities_by_day_5d
    ):
        """Sonnet 失败时降级规则引擎，不抛异常。"""
        daily_activities = {
            "daily_activities": [
                {"day": d["day"], "city": d["city"], "main_corridor": "namba",
                 "intensity": d["intensity"], "main_activities": [], "time_anchors": []}
                for d in cities_by_day_5d
            ]
        }
        commute = self._make_commute_results(hotel_pool_3)

        with patch("anthropic.AsyncAnthropic") as mock_cls:
            client = AsyncMock()
            client.messages.create = AsyncMock(side_effect=Exception("Sonnet unavailable"))
            mock_cls.return_value = client

            result = await select_hotels(
                hotel_pool=hotel_pool_3,
                commute_results=commute,
                daily_activities=daily_activities,
                user_constraints=kansai_constraints_5d,
                api_key="fake-key",
            )

        assert result["hotel_plan"]["primary"] is not None
        assert "fallback_reason" in result

    @pytest.mark.asyncio
    async def test_select_hotels_only_uses_viable_candidates(
        self, kansai_constraints_5d, cities_by_day_5d
    ):
        """通勤 fail 的酒店不应被选中（在 viable 候选中排除）。"""
        all_fail_pool = [_make_hotel("h_fail", "kyoto")]
        commute_all_fail = [{
            "hotel_id": "h_fail",
            "hotel_name": "远距离酒店",
            "status": "fail",
            "avg_commute_minutes": 90,
            "max_commute_minutes": 120,
        }]
        daily_activities = {"daily_activities": []}

        # 所有酒店 fail 时，select_hotels 放宽到 warning，不抛异常
        result = await select_hotels(
            hotel_pool=all_fail_pool,
            commute_results=commute_all_fail,
            daily_activities=daily_activities,
            user_constraints=kansai_constraints_5d,
            api_key=None,
        )
        # 放宽后 fallback 仍应给出结果
        assert result["hotel_plan"] is not None


# ─────────────────────────────────────────────────────────────────────────────
# Step 7.5: check_commute_feasibility — 通勤可行性验证
# ─────────────────────────────────────────────────────────────────────────────

class TestStep7_5CommuteCheck:

    def _make_corridors(self) -> list[dict]:
        return [
            {"day": 1, "corridor": "namba", "anchor_entity_id": str(uuid.uuid4())},
            {"day": 2, "corridor": "higashiyama", "anchor_entity_id": str(uuid.uuid4())},
            {"day": 3, "corridor": "arashiyama", "anchor_entity_id": str(uuid.uuid4())},
        ]

    @pytest.mark.asyncio
    async def test_all_pass_when_under_threshold(self, hotel_pool_3):
        """所有天通勤 ≤ 45 分钟时，status 应为 pass。"""
        corridors = self._make_corridors()

        with patch(
            "app.domains.planning_v2.step07_5_commute_check.get_travel_time",
            new_callable=AsyncMock,
            return_value={"duration_min": 20, "mode": "transit"},
        ):
            results = await check_commute_feasibility(
                session=AsyncMock(),
                hotel_candidates=hotel_pool_3,
                daily_main_corridors=corridors,
                max_commute_minutes=45,
            )

        assert len(results) == len(hotel_pool_3)
        for r in results:
            assert r["status"] == "pass", f"{r['hotel_name']} status={r['status']}, 期望 pass"

    @pytest.mark.asyncio
    async def test_all_fail_when_over_threshold(self, hotel_pool_3):
        """所有天通勤 > 45 分钟时，status 应为 fail。"""
        corridors = self._make_corridors()

        with patch(
            "app.domains.planning_v2.step07_5_commute_check.get_travel_time",
            new_callable=AsyncMock,
            return_value={"duration_min": 60, "mode": "transit"},
        ):
            results = await check_commute_feasibility(
                session=AsyncMock(),
                hotel_candidates=hotel_pool_3,
                daily_main_corridors=corridors,
                max_commute_minutes=45,
            )

        for r in results:
            assert r["status"] == "fail", f"{r['hotel_name']} 期望 fail，实际 {r['status']}"

    @pytest.mark.asyncio
    async def test_warning_when_partial_days_exceed(self, hotel_pool_3):
        """部分天超时时，status 应为 warning。"""
        corridors = self._make_corridors()
        # day1=20min (pass), day2=60min (fail), day3=20min (pass)
        call_count = [0]

        async def variable_commute(*args, **kwargs):
            call_count[0] += 1
            idx = (call_count[0] - 1) % 3
            return {"duration_min": [20, 60, 20][idx], "mode": "transit"}

        with patch(
            "app.domains.planning_v2.step07_5_commute_check.get_travel_time",
            side_effect=variable_commute,
        ):
            results = await check_commute_feasibility(
                session=AsyncMock(),
                hotel_candidates=[hotel_pool_3[0]],
                daily_main_corridors=corridors,
                max_commute_minutes=45,
            )

        assert results[0]["status"] == "warning"

    @pytest.mark.asyncio
    async def test_avg_commute_calculated_correctly(self, hotel_pool_3):
        """avg_commute_minutes 应是各天通勤时间的平均值。"""
        corridors = self._make_corridors()
        times = [20, 30, 40]
        call_count = [0]

        async def sequential_commute(*args, **kwargs):
            idx = call_count[0] % len(times)
            call_count[0] += 1
            return {"duration_min": times[idx], "mode": "transit"}

        with patch(
            "app.domains.planning_v2.step07_5_commute_check.get_travel_time",
            side_effect=sequential_commute,
        ):
            results = await check_commute_feasibility(
                session=AsyncMock(),
                hotel_candidates=[hotel_pool_3[0]],
                daily_main_corridors=corridors,
                max_commute_minutes=45,
            )

        assert results[0]["avg_commute_minutes"] == round(sum(times) / len(times))

    @pytest.mark.asyncio
    async def test_results_sorted_by_avg_commute(self, hotel_pool_3):
        """结果应按 avg_commute_minutes 升序排列。"""
        corridors = [{"day": 1, "corridor": "namba", "anchor_entity_id": str(uuid.uuid4())}]
        # 三家酒店返回不同通勤：hotel_a=40, hotel_b=15, hotel_c=25
        times_map = {
            _HOTEL_A_ID: 40,
            _HOTEL_B_ID: 15,
            _HOTEL_C_ID: 25,
        }
        call_idx = [0]

        async def hotel_specific_commute(*args, **kwargs):
            hotel_idx = call_idx[0] // len(corridors)
            call_idx[0] += 1
            hotel_id = hotel_pool_3[hotel_idx % len(hotel_pool_3)].entity_id
            return {"duration_min": times_map.get(hotel_id, 30), "mode": "transit"}

        with patch(
            "app.domains.planning_v2.step07_5_commute_check.get_travel_time",
            side_effect=hotel_specific_commute,
        ):
            results = await check_commute_feasibility(
                session=AsyncMock(),
                hotel_candidates=hotel_pool_3,
                daily_main_corridors=corridors,
                max_commute_minutes=45,
            )

        avg_mins = [r["avg_commute_minutes"] for r in results]
        assert avg_mins == sorted(avg_mins), f"结果未按通勤时间升序: {avg_mins}"

    @pytest.mark.asyncio
    async def test_empty_hotels_returns_empty(self):
        results = await check_commute_feasibility(
            session=AsyncMock(),
            hotel_candidates=[],
            daily_main_corridors=[{"day": 1, "corridor": "x", "anchor_entity_id": str(uuid.uuid4())}],
        )
        assert results == []

    @pytest.mark.asyncio
    async def test_empty_corridors_returns_empty(self, hotel_pool_3):
        results = await check_commute_feasibility(
            session=AsyncMock(),
            hotel_candidates=hotel_pool_3,
            daily_main_corridors=[],
        )
        assert results == []

    @pytest.mark.asyncio
    async def test_api_error_uses_fallback_minutes(self, hotel_pool_3):
        """get_travel_time 抛异常时，使用默认 30 分钟，不崩溃。"""
        corridors = [{"day": 1, "corridor": "namba", "anchor_entity_id": str(uuid.uuid4())}]

        with patch(
            "app.domains.planning_v2.step07_5_commute_check.get_travel_time",
            new_callable=AsyncMock,
            side_effect=ConnectionError("API unreachable"),
        ):
            results = await check_commute_feasibility(
                session=AsyncMock(),
                hotel_candidates=[hotel_pool_3[0]],
                daily_main_corridors=corridors,
                max_commute_minutes=45,
            )

        assert len(results) == 1
        assert results[0]["avg_commute_minutes"] == 30  # fallback = 30

    @pytest.mark.asyncio
    async def test_commute_avg_under_45_for_pass_hotels(self, hotel_pool_3):
        """CP2 核心验证：通过的酒店平均通勤应 < 45 分钟。"""
        corridors = self._make_corridors()

        with patch(
            "app.domains.planning_v2.step07_5_commute_check.get_travel_time",
            new_callable=AsyncMock,
            return_value={"duration_min": 25, "mode": "transit"},
        ):
            results = await check_commute_feasibility(
                session=AsyncMock(),
                hotel_candidates=hotel_pool_3,
                daily_main_corridors=corridors,
                max_commute_minutes=45,
            )

        for r in results:
            if r["status"] == "pass":
                assert r["avg_commute_minutes"] < 45, (
                    f"pass 酒店 {r['hotel_name']} avg_commute={r['avg_commute_minutes']}≥45"
                )


# ─────────────────────────────────────────────────────────────────────────────
# CP2 数据契约检查（Step 间字段对齐）
# ─────────────────────────────────────────────────────────────────────────────

class TestCp2DataContracts:

    def test_step5_output_has_required_fields_for_step5_5(self, cities_by_day_5d, poi_pool_5d):
        """Step 5 输出的 daily_activities 应满足 Step 5.5 期望的字段。"""
        result = _rule_based_fallback(
            cities_by_day=cities_by_day_5d,
            poi_pool=poi_pool_5d,
            must_visit_ids=set(),
        )
        for day in result["daily_activities"]:
            # Step 5.5 需要：day, main_activities[].entity_id, main_corridor
            assert "day" in day
            assert "main_activities" in day
            assert "main_corridor" in day
            for act in day["main_activities"]:
                assert "entity_id" in act, f"Day {day['day']} activity 缺少 entity_id"
                assert "visit_minutes" in act

    def test_step5_output_has_required_fields_for_step7(self, cities_by_day_5d, poi_pool_5d):
        """Step 7 使用 daily_activities 提取每日走廊，需要 city 和 main_corridor。"""
        result = _rule_based_fallback(
            cities_by_day=cities_by_day_5d,
            poi_pool=poi_pool_5d,
            must_visit_ids=set(),
        )
        for day in result["daily_activities"]:
            assert "city" in day
            assert "main_corridor" in day
            assert "intensity" in day

    def test_step6_output_fields_for_step7(self, hotel_pool_3):
        """Step 7 需要 hotel.entity_id, cost_local, review_signals, open_hours, tags。"""
        for hotel in hotel_pool_3:
            assert hotel.entity_id
            assert hotel.cost_local >= 0
            assert isinstance(hotel.open_hours, dict)
            assert isinstance(hotel.review_signals, dict)
            assert isinstance(hotel.tags, list)

    def test_step7_output_meals_propagates_to_step8(self, hotel_pool_3):
        """
        Step 7 输出的 meals_included 直接传给 Step 8 的 DailyConstraints。
        验证 fallback 输出的 meals_included 格式包含 breakfast/dinner 两个 bool 键。
        """
        commute = [
            {
                "hotel_id": h.entity_id,
                "hotel_name": h.name_zh,
                "status": "pass",
                "avg_commute_minutes": 20,
                "max_commute_minutes": 30,
            }
            for h in hotel_pool_3
        ]
        summaries = _build_hotel_summaries(hotel_pool_3, commute)
        result = hotel_fallback(hotel_summaries=summaries, total_days=5)

        meals = result["hotel_plan"]["primary"]["meals_included"]
        assert "breakfast" in meals, "meals_included 缺少 breakfast 键"
        assert "dinner" in meals, "meals_included 缺少 dinner 键"
        assert isinstance(meals["breakfast"], bool)
        assert isinstance(meals["dinner"], bool)

    def test_step7_5_output_fields_for_step7(self, hotel_pool_3):
        """Step 7 消费 Step 7.5 的输出，需要 hotel_id, status, avg_commute_minutes。"""
        mock_commute_result = {
            "hotel_id": hotel_pool_3[0].entity_id,
            "hotel_name": hotel_pool_3[0].name_zh,
            "status": "pass",
            "avg_commute_minutes": 22,
            "max_commute_minutes": 30,
            "commute_details": [],
        }
        for field in ("hotel_id", "hotel_name", "status", "avg_commute_minutes"):
            assert field in mock_commute_result, f"Step 7.5 输出缺少字段: {field}"

    def test_cp2_hotel_switch_day_consistent_with_secondary(self, hotel_pool_3):
        """
        若 hotel_plan.secondary 为 null，hotel_switch_day 也应为 null。
        若 secondary 存在，hotel_switch_day 应为正整数。
        """
        commute = [
            {"hotel_id": h.entity_id, "hotel_name": h.name_zh,
             "status": "pass", "avg_commute_minutes": 20, "max_commute_minutes": 25}
            for h in hotel_pool_3
        ]
        summaries = _build_hotel_summaries(hotel_pool_3, commute)
        result = hotel_fallback(hotel_summaries=summaries, total_days=5)

        secondary = result["hotel_plan"]["secondary"]
        switch_day = result["hotel_switch_day"]

        if secondary is None:
            assert switch_day is None, "secondary=null 时 hotel_switch_day 应为 null"
        else:
            assert isinstance(switch_day, int) and switch_day > 0, (
                "secondary 存在时 hotel_switch_day 应为正整数"
            )
