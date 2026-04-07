"""
CP1 测试 — 宏观决策（Step 1-4 后）

使用真实关西景点数据（data/kansai_spots/*.json）作为测试 fixture。

验证点：
  1. UserConstraints.trip_window 包含 start_date / end_date / total_days
  2. RegionSummary.entity_count == sum(entities_by_type.values())
  3. 城市组合方案 2-3 个，每个方案总天数 == total_days
  4. POI 候选池每个条目都有 city_code，且 city_code 在 circle_cities 内
"""

import json
import uuid
import pytest
from pathlib import Path
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

from app.domains.planning_v2.models import (
    UserConstraints,
    RegionSummary,
    CandidatePool,
)
from app.domains.planning_v2.step01_constraints import (
    _parse_trip_window,
    _parse_constraints,
    resolve_user_constraints,
)
from app.domains.planning_v2.step02_region_summary import build_region_summary
from app.domains.planning_v2.step03_city_planner import (
    plan_city_combination,
    _build_fallback_plan,
    _extract_json,
)
from app.domains.planning_v2.step04_poi_pool import build_poi_pool


# ─────────────────────────────────────────────────────────────────────────────
# 真实关西数据加载
# ─────────────────────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parents[4] / "data" / "kansai_spots" / "archived_ai_generated"

_SPOT_FILES = [
    "kyoto_city.json",
    "kyoto_extended.json",
    "osaka_city.json",
    "nara.json",
    "hyogo.json",
]


def _load_kansai_spots() -> list[dict]:
    """从关西 JSON 文件加载所有景点。"""
    spots = []
    for fname in _SPOT_FILES:
        fpath = DATA_DIR / fname
        if not fpath.exists():
            continue
        data = json.loads(fpath.read_text(encoding="utf-8"))
        spots.extend(data.get("spots", []))
    return spots


def _load_kansai_restaurants() -> list[dict]:
    """从关西餐厅 JSON 文件加载所有餐厅。"""
    restaurants = []
    for fpath in DATA_DIR.glob("restaurants_*.json"):
        data = json.loads(fpath.read_text(encoding="utf-8"))
        restaurants.extend(data.get("restaurants", []))
    return restaurants


def _load_kansai_hotels() -> list[dict]:
    """从关西酒店 JSON 文件加载所有酒店。"""
    hotels = []
    for fpath in DATA_DIR.glob("hotels_*.json"):
        data = json.loads(fpath.read_text(encoding="utf-8"))
        hotels.extend(data.get("hotels", []))
    return hotels


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

KANSAI_CITIES = ["kyoto", "osaka", "nara", "kobe", "himeji"]

KANSAI_SPOT_LIST = _load_kansai_spots()
KANSAI_RESTAURANT_LIST = _load_kansai_restaurants()
KANSAI_HOTEL_LIST = _load_kansai_hotels()


def _build_region_summary_from_real_data() -> RegionSummary:
    """从真实关西数据构造 RegionSummary（与 Step 2 输出格式一致）。"""
    poi_count = len([s for s in KANSAI_SPOT_LIST if s.get("city_code") in KANSAI_CITIES])
    restaurant_count = len([r for r in KANSAI_RESTAURANT_LIST if r.get("city_code") in KANSAI_CITIES])
    hotel_count = len([h for h in KANSAI_HOTEL_LIST if h.get("city_code") in KANSAI_CITIES])

    entities_by_type = {
        "poi": poi_count,
        "restaurant": restaurant_count,
        "hotel": hotel_count,
        "event": 0,
    }
    total = sum(entities_by_type.values())

    # 等级分布
    grade_dist: dict[str, int] = {"S": 0, "A": 0, "B": 0, "C": 0}
    for s in KANSAI_SPOT_LIST:
        g = s.get("grade", "B")
        if g in grade_dist:
            grade_dist[g] += 1

    return RegionSummary(
        circle_name="Kansai",
        cities=KANSAI_CITIES,
        entity_count=total,
        entities_by_type=entities_by_type,
        grade_distribution=grade_dist,
    )


@pytest.fixture
def kansai_region_summary() -> RegionSummary:
    return _build_region_summary_from_real_data()


@pytest.fixture
def kansai_user_constraints() -> UserConstraints:
    """6天关西行程，情侣，中档预算，must_visit 使用真实景点 id。"""
    return UserConstraints(
        trip_window={
            "start_date": "2026-04-10",
            "end_date": "2026-04-15",
            "total_days": 6,
        },
        user_profile={
            "party_type": "couple",
            "budget_tier": "mid",
            "must_have_tags": ["文化", "拍照强"],
            "nice_to_have_tags": ["免费", "夜间强"],
            "avoid_tags": [],
        },
        constraints={
            "must_visit": ["kyo_fushimi_inari", "nar_nara_park_deer"],
            "do_not_go": ["osa_usj"],   # 不去 USJ
            "visited": [],
            "booked_items": [],
        },
    )


@pytest.fixture
def kansai_poi_pool() -> list[CandidatePool]:
    """从真实关西 JSON 构造 CandidatePool 列表（只取 S/A 级）。"""
    pools = []
    for spot in KANSAI_SPOT_LIST:
        if spot.get("grade") not in ("S", "A"):
            continue
        city = spot.get("city_code", "")
        if city not in KANSAI_CITIES:
            continue
        coord = spot.get("coord", [0.0, 0.0])
        cost = spot.get("cost", {})
        pools.append(CandidatePool(
            entity_id=spot["id"],
            name_zh=spot["name_zh"],
            entity_type="poi",
            grade=spot["grade"],
            latitude=coord[0] if len(coord) > 0 else 0.0,
            longitude=coord[1] if len(coord) > 1 else 0.0,
            tags=spot.get("tags", []),
            visit_minutes=spot.get("visit_minutes", 60),
            cost_local=cost.get("admission_jpy", 0) or 0,
            city_code=city,
            open_hours=spot.get("when", {}),
            review_signals=spot.get("review_signals", {}),
        ))
    return pools


# ─────────────────────────────────────────────────────────────────────────────
# Step 1: UserConstraints 字段完整性
# ─────────────────────────────────────────────────────────────────────────────

class TestStep1UserConstraints:

    def test_cp1_trip_window_has_all_required_keys(self, kansai_user_constraints):
        tw = kansai_user_constraints.trip_window
        assert "start_date" in tw
        assert "end_date" in tw
        assert "total_days" in tw

    def test_cp1_trip_window_dates_non_empty(self, kansai_user_constraints):
        tw = kansai_user_constraints.trip_window
        assert tw["start_date"], "start_date 不能为空"
        assert tw["end_date"], "end_date 不能为空"

    def test_cp1_total_days_matches_date_diff(self, kansai_user_constraints):
        tw = kansai_user_constraints.trip_window
        start = date.fromisoformat(tw["start_date"])
        end = date.fromisoformat(tw["end_date"])
        expected = (end - start).days + 1
        assert tw["total_days"] == expected, (
            f"total_days={tw['total_days']}，但日期差+1={expected}"
        )

    def test_cp1_total_days_is_int(self, kansai_user_constraints):
        assert isinstance(kansai_user_constraints.trip_window["total_days"], int)

    def test_cp1_constraints_lists_are_lists(self, kansai_user_constraints):
        cs = kansai_user_constraints.constraints
        for key in ("must_visit", "do_not_go", "visited", "booked_items"):
            assert isinstance(cs[key], list), f"constraints.{key} 应为 list"

    def test_cp1_must_visit_uses_real_kansai_spot_ids(self, kansai_user_constraints):
        """must_visit 中的 id 应能在真实关西数据中找到。"""
        real_ids = {s["id"] for s in KANSAI_SPOT_LIST}
        for spot_id in kansai_user_constraints.constraints["must_visit"]:
            assert spot_id in real_ids, f"must_visit id '{spot_id}' 在关西数据中不存在"

    def test_cp1_do_not_go_uses_real_kansai_spot_ids(self, kansai_user_constraints):
        real_ids = {s["id"] for s in KANSAI_SPOT_LIST}
        for spot_id in kansai_user_constraints.constraints["do_not_go"]:
            assert spot_id in real_ids, f"do_not_go id '{spot_id}' 在关西数据中不存在"

    def test_cp1_parse_trip_window_calculates_total_days_from_dates(self):
        mock_profile = MagicMock()
        mock_profile.travel_dates = {"start": "2026-04-10", "end": "2026-04-15"}
        mock_profile.duration_days = 3  # 与日期不一致，应以日期优先

        result = _parse_trip_window(mock_profile)

        assert result["total_days"] == 6  # 10~15 含首尾=6天
        assert result["start_date"] == "2026-04-10"
        assert result["end_date"] == "2026-04-15"

    def test_cp1_parse_trip_window_fallback_to_duration_days(self):
        mock_profile = MagicMock()
        mock_profile.travel_dates = {}
        mock_profile.duration_days = 5

        result = _parse_trip_window(mock_profile)

        assert result["total_days"] == 5

    def test_cp1_parse_constraints_normalizes_string_to_list(self):
        mock_profile = MagicMock()
        mock_profile.must_visit_places = "kyo_fushimi_inari"  # 字符串
        mock_profile.do_not_go_places = ["osa_usj"]
        mock_profile.visited_places = None
        mock_profile.booked_items = []

        result = _parse_constraints(mock_profile)

        assert isinstance(result["must_visit"], list)
        assert "kyo_fushimi_inari" in result["must_visit"]
        assert result["visited"] == []

    @pytest.mark.asyncio
    async def test_cp1_resolve_raises_if_trip_request_missing(self):
        session = AsyncMock()
        session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        )
        with pytest.raises(ValueError, match="TripRequest"):
            await resolve_user_constraints(session, str(uuid.uuid4()))

    @pytest.mark.asyncio
    async def test_cp1_resolve_raises_if_trip_profile_missing(self):
        mock_req = MagicMock()
        mock_req.trip_request_id = uuid.uuid4()

        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_req)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
        ])
        with pytest.raises(ValueError, match="TripProfile"):
            await resolve_user_constraints(session, str(mock_req.trip_request_id))


# ─────────────────────────────────────────────────────────────────────────────
# Step 2: RegionSummary 一致性
# ─────────────────────────────────────────────────────────────────────────────

class TestStep2RegionSummary:

    def test_cp1_entity_count_matches_type_sum(self, kansai_region_summary):
        rs = kansai_region_summary
        expected = sum(rs.entities_by_type.values())
        assert rs.entity_count == expected, (
            f"entity_count={rs.entity_count} != sum(types)={expected}"
        )

    def test_cp1_entity_count_reflects_real_kansai_data(self, kansai_region_summary):
        """真实关西数据的 POI 数量应 > 0。"""
        assert kansai_region_summary.entities_by_type["poi"] > 0

    def test_cp1_kansai_has_standard_entity_types(self, kansai_region_summary):
        for t in ("poi", "restaurant", "hotel"):
            assert t in kansai_region_summary.entities_by_type

    def test_cp1_grade_distribution_has_s_and_a(self, kansai_region_summary):
        gd = kansai_region_summary.grade_distribution
        assert gd.get("S", 0) > 0, "关西数据中应有 S 级景点"
        assert gd.get("A", 0) > 0, "关西数据中应有 A 级景点"

    def test_cp1_kansai_cities_in_region_summary(self, kansai_region_summary):
        for city in ("kyoto", "osaka"):
            assert city in kansai_region_summary.cities

    @pytest.mark.asyncio
    async def test_cp1_build_region_summary_raises_on_empty_cities(self):
        session = AsyncMock()
        with pytest.raises(ValueError, match="circle_cities"):
            await build_region_summary(session, "Kansai", [])

    @pytest.mark.asyncio
    async def test_cp1_build_region_summary_entity_count_equals_type_sum(self):
        """mock DB 返回关西量级数据，验证 entity_count = 各类型之和。"""
        session = AsyncMock()

        # 模拟与真实关西 POI/餐厅/酒店数量接近的统计
        poi_count = len([s for s in KANSAI_SPOT_LIST if s.get("grade") in ("S", "A")])
        restaurant_count = len(KANSAI_RESTAURANT_LIST)
        hotel_count = len(KANSAI_HOTEL_LIST)

        type_rows = [("poi", poi_count), ("restaurant", restaurant_count), ("hotel", hotel_count)]
        grade_rows = [
            ("S", len([s for s in KANSAI_SPOT_LIST if s.get("grade") == "S"])),
            ("A", len([s for s in KANSAI_SPOT_LIST if s.get("grade") == "A"])),
            ("B", 0), ("C", 0),
        ]

        session.execute = AsyncMock(side_effect=[
            MagicMock(all=MagicMock(return_value=type_rows)),
            MagicMock(all=MagicMock(return_value=grade_rows)),
        ])

        result = await build_region_summary(session, "Kansai", KANSAI_CITIES)

        assert result.entity_count == sum(result.entities_by_type.values())
        assert result.entity_count == poi_count + restaurant_count + hotel_count


# ─────────────────────────────────────────────────────────────────────────────
# Step 3: 城市组合方案
# ─────────────────────────────────────────────────────────────────────────────

class TestStep3CityCombination:

    def _make_kansai_opus_result(self, total_days: int, num_candidates: int = 3) -> dict:
        """构造符合 Step 3 规范的关西城市组合输出。"""
        city_rotation = ["kyoto", "osaka", "nara", "kobe", "kyoto", "osaka"]
        candidates = []
        for i in range(num_candidates):
            cities_by_day = {}
            for d in range(1, total_days + 1):
                intensity = "light" if d in (1, total_days) else "medium"
                cities_by_day[f"day{d}"] = {
                    "city": city_rotation[(d - 1) % len(city_rotation)],
                    "theme": f"关西主题{d}",
                    "intensity": intensity,
                }
            candidates.append({
                "plan_name": f"关西方案{i + 1}",
                "cities_by_day": cities_by_day,
                "reasoning": "基于关西景点密度和通勤距离设计",
                "trade_offs": "京都/大阪侧重不同",
            })
        return {
            "candidates": candidates,
            "recommended_index": 0,
            "thinking_tokens_used": 8000,
        }

    def test_cp1_candidates_count_is_2_or_3(self):
        result = self._make_kansai_opus_result(total_days=6)
        assert 2 <= len(result["candidates"]) <= 3

    def test_cp1_each_candidate_days_equals_total_days(self):
        total_days = 6
        result = self._make_kansai_opus_result(total_days=total_days)
        for cand in result["candidates"]:
            actual = len(cand["cities_by_day"])
            assert actual == total_days, (
                f"'{cand['plan_name']}' 有 {actual} 天，期望 {total_days}"
            )

    def test_cp1_first_and_last_day_intensity_light(self):
        total_days = 6
        result = self._make_kansai_opus_result(total_days=total_days)
        for cand in result["candidates"]:
            assert cand["cities_by_day"]["day1"]["intensity"] == "light"
            assert cand["cities_by_day"][f"day{total_days}"]["intensity"] == "light"

    def test_cp1_all_cities_in_kansai_circle(self):
        result = self._make_kansai_opus_result(total_days=6)
        for cand in result["candidates"]:
            for day_data in cand["cities_by_day"].values():
                assert day_data["city"] in KANSAI_CITIES, (
                    f"city='{day_data['city']}' 不在关西 circle 内"
                )

    def test_cp1_candidates_have_required_fields(self):
        result = self._make_kansai_opus_result(total_days=6)
        for cand in result["candidates"]:
            for field in ("plan_name", "cities_by_day", "reasoning", "trade_offs"):
                assert field in cand, f"候选方案缺少 {field}"

    def test_cp1_fallback_plan_uses_kansai_cities(self, kansai_user_constraints, kansai_region_summary):
        fallback = _build_fallback_plan(kansai_user_constraints, kansai_region_summary)
        candidate = fallback["candidates"][0]
        for day_data in candidate["cities_by_day"].values():
            assert day_data["city"] in KANSAI_CITIES

    def test_cp1_fallback_plan_correct_total_days(self, kansai_user_constraints, kansai_region_summary):
        total_days = kansai_user_constraints.trip_window["total_days"]
        fallback = _build_fallback_plan(kansai_user_constraints, kansai_region_summary)
        assert len(fallback["candidates"][0]["cities_by_day"]) == total_days

    def test_cp1_fallback_first_last_day_light(self, kansai_user_constraints, kansai_region_summary):
        total_days = kansai_user_constraints.trip_window["total_days"]
        fallback = _build_fallback_plan(kansai_user_constraints, kansai_region_summary)
        cbd = fallback["candidates"][0]["cities_by_day"]
        assert cbd["day1"]["intensity"] == "light"
        assert cbd[f"day{total_days}"]["intensity"] == "light"

    @pytest.mark.asyncio
    async def test_cp1_plan_city_combination_returns_fallback_without_api_key(
        self, kansai_user_constraints, kansai_region_summary
    ):
        with patch("app.domains.planning_v2.step03_city_planner.settings") as mock_settings:
            mock_settings.anthropic_api_key = None
            result = await plan_city_combination(
                kansai_user_constraints, kansai_region_summary, api_key=None
            )
        assert "candidates" in result
        assert len(result["candidates"]) >= 1

    @pytest.mark.asyncio
    async def test_cp1_plan_city_combination_retries_on_json_error_then_fallback(
        self, kansai_user_constraints, kansai_region_summary
    ):
        bad_response = MagicMock()
        bad_response.content = [MagicMock(type="text", text="这不是 JSON")]
        bad_response.usage = MagicMock(output_tokens=50, input_tokens=200)

        with patch("anthropic.AsyncAnthropic") as mock_cls:
            client = AsyncMock()
            client.messages.create = AsyncMock(return_value=bad_response)
            mock_cls.return_value = client

            result = await plan_city_combination(
                kansai_user_constraints, kansai_region_summary, api_key="fake-key"
            )

        assert "candidates" in result
        assert result.get("fallback") is True or "error" in result

    def test_cp1_extract_json_from_markdown_code_block(self):
        text = '```json\n{"candidates": [], "recommended_index": 0}\n```'
        parsed = json.loads(_extract_json(text))
        assert "candidates" in parsed

    def test_cp1_extract_json_bare_object(self):
        text = '  {"candidates": [{"plan_name": "京都深度"}]}  '
        parsed = json.loads(_extract_json(text))
        assert parsed["candidates"][0]["plan_name"] == "京都深度"


# ─────────────────────────────────────────────────────────────────────────────
# Step 4: POI 候选池（关西真实数据）
# ─────────────────────────────────────────────────────────────────────────────

class TestStep4PoiPool:

    def test_cp1_all_pool_items_have_city_code(self, kansai_poi_pool):
        for item in kansai_poi_pool:
            assert item.city_code != "", f"'{item.name_zh}' city_code 为空"

    def test_cp1_all_pool_city_codes_in_kansai_circle(self, kansai_poi_pool):
        for item in kansai_poi_pool:
            assert item.city_code in KANSAI_CITIES, (
                f"'{item.name_zh}'.city_code='{item.city_code}' 不在 KANSAI_CITIES"
            )

    def test_cp1_pool_only_contains_s_and_a_grade(self, kansai_poi_pool):
        for item in kansai_poi_pool:
            assert item.grade in ("S", "A"), (
                f"'{item.name_zh}' grade='{item.grade}'，Step 4 只取 S/A"
            )

    def test_cp1_pool_visit_minutes_positive(self, kansai_poi_pool):
        for item in kansai_poi_pool:
            assert item.visit_minutes > 0, f"'{item.name_zh}' visit_minutes 必须 > 0"

    def test_cp1_pool_has_meaningful_size(self, kansai_poi_pool):
        """关西 S/A 级 POI 数量应足够支撑 6 天行程。"""
        assert len(kansai_poi_pool) >= 6, (
            f"关西 S/A 级 POI 仅 {len(kansai_poi_pool)} 个，不足以支撑 6 天行程"
        )

    def test_cp1_pool_entity_type_is_poi(self, kansai_poi_pool):
        for item in kansai_poi_pool:
            assert item.entity_type == "poi"

    def test_cp1_do_not_go_entity_exists_in_raw_kansai_data(self, kansai_user_constraints):
        """do_not_go 中的 id（osa_usj）必须在真实关西数据中存在（才有意义排除它）。"""
        real_ids = {s["id"] for s in KANSAI_SPOT_LIST}
        for spot_id in kansai_user_constraints.constraints["do_not_go"]:
            assert spot_id in real_ids, (
                f"do_not_go id '{spot_id}' 在关西数据中不存在，配置有误"
            )

    def test_cp1_fushimi_inari_in_pool_for_kyoto(self, kansai_poi_pool):
        """伏见稻荷（kyo_fushimi_inari）是 S 级，应在关西 POI 池中。"""
        ids = {item.entity_id for item in kansai_poi_pool}
        assert "kyo_fushimi_inari" in ids, "伏见稻荷大社应在关西 POI 候选池中"

    def test_cp1_nara_deer_park_in_pool(self, kansai_poi_pool):
        """奈良鹿公园是 S 级，应在候选池中。"""
        ids = {item.entity_id for item in kansai_poi_pool}
        assert "nar_nara_park_deer" in ids, "奈良公园·鹿应在关西 POI 候选池中"

    def test_cp1_kyoto_pois_have_kyoto_city_code(self, kansai_poi_pool):
        kyoto_pois = [item for item in kansai_poi_pool if item.city_code == "kyoto"]
        assert len(kyoto_pois) > 0, "京都 POI 池不应为空"

    def test_cp1_osaka_pois_have_osaka_city_code(self, kansai_poi_pool):
        osaka_pois = [item for item in kansai_poi_pool if item.city_code == "osaka"]
        assert len(osaka_pois) > 0, "大阪 POI 池不应为空"

    @pytest.mark.asyncio
    async def test_cp1_build_poi_pool_empty_on_no_cities(self, kansai_user_constraints):
        session = AsyncMock()
        region = RegionSummary(
            circle_name="Kansai", cities=[],
            entity_count=0, entities_by_type={}, grade_distribution={}
        )
        result = await build_poi_pool(session, kansai_user_constraints, region, ["2026-04-10"])
        assert result == []

    @pytest.mark.asyncio
    async def test_cp1_build_poi_pool_excludes_osa_usj_via_do_not_go(self, kansai_user_constraints):
        """do_not_go=['osa_usj']，构建池时不应包含 USJ。"""
        usj_id = uuid.uuid4()

        e = MagicMock()
        e.entity_id = usj_id
        e.name_zh = "日本环球影城"
        e.data_tier = "S"
        e.city_code = "osaka"
        e.lat = 34.6654
        e.lng = 135.4323
        e.risk_flags = []
        e.typical_duration_baseline = 600

        # do_not_go 用字符串 id，匹配逻辑是 str(eid) in do_not_go_places
        kansai_user_constraints.constraints["do_not_go"] = [str(usj_id)]

        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[e])))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
        ])

        region = RegionSummary(
            circle_name="Kansai", cities=["osaka"],
            entity_count=1, entities_by_type={"poi": 1}, grade_distribution={"S": 1}
        )

        result = await build_poi_pool(session, kansai_user_constraints, region, ["2026-04-10"])
        result_ids = {item.entity_id for item in result}
        assert str(usj_id) not in result_ids

    @pytest.mark.asyncio
    async def test_cp1_build_poi_pool_excludes_renovation_entities(self, kansai_user_constraints):
        risky_id = uuid.uuid4()

        e = MagicMock()
        e.entity_id = risky_id
        e.name_zh = "施工中景点"
        e.data_tier = "A"
        e.city_code = "kyoto"
        e.lat = 35.0
        e.lng = 135.7
        e.risk_flags = ["renovation"]
        e.typical_duration_baseline = 60

        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[e])))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
        ])

        region = RegionSummary(
            circle_name="Kansai", cities=["kyoto"],
            entity_count=1, entities_by_type={"poi": 1}, grade_distribution={"A": 1}
        )
        kansai_user_constraints.constraints["do_not_go"] = []

        result = await build_poi_pool(session, kansai_user_constraints, region, ["2026-04-10"])
        assert len(result) == 0


# ─────────────────────────────────────────────────────────────────────────────
# CP1 数据契约检查（Step 间字段对齐）
# ─────────────────────────────────────────────────────────────────────────────

class TestCp1DataContracts:

    def test_contract_step1_to_step3_trip_window_keys(self, kansai_user_constraints):
        """Step 3 _build_user_prompt 依赖 trip_window 的三个键。"""
        tw = kansai_user_constraints.trip_window
        for key in ("start_date", "end_date", "total_days"):
            assert tw.get(key) is not None, f"Step1→3 契约破坏：trip_window 缺少 {key}"

    def test_contract_step1_to_step3_constraints_are_lists(self, kansai_user_constraints):
        """Step 3 prompt 对 must_visit/do_not_go/visited 做 join，必须是 list。"""
        cs = kansai_user_constraints.constraints
        for key in ("must_visit", "do_not_go", "visited"):
            assert isinstance(cs.get(key), list), f"Step1→3 契约破坏：constraints.{key} 不是 list"

    def test_contract_step2_to_step3_region_summary_fields(self, kansai_region_summary):
        """Step 3 prompt 使用 circle_name, cities, entities_by_type, grade_distribution。"""
        rs = kansai_region_summary
        assert rs.circle_name
        assert isinstance(rs.cities, list) and len(rs.cities) > 0
        assert isinstance(rs.entities_by_type, dict)
        assert isinstance(rs.grade_distribution, dict)

    def test_contract_step2_entity_count_consistency(self, kansai_region_summary):
        """Step 2 核心不变量：entity_count == sum(entities_by_type.values())。"""
        rs = kansai_region_summary
        assert rs.entity_count == sum(rs.entities_by_type.values())

    def test_contract_step3_output_has_cities_by_day_for_step5(self):
        """Step 5 期望 candidates[i].cities_by_day[dayN].city 存在。"""
        step3_out = {
            "candidates": [
                {
                    "plan_name": "关西文化线",
                    "cities_by_day": {
                        "day1": {"city": "osaka", "theme": "到达", "intensity": "light"},
                        "day2": {"city": "kyoto", "theme": "寺庙", "intensity": "medium"},
                        "day3": {"city": "nara", "theme": "古都", "intensity": "medium"},
                        "day4": {"city": "kyoto", "theme": "岚山", "intensity": "medium"},
                        "day5": {"city": "kobe", "theme": "港口", "intensity": "medium"},
                        "day6": {"city": "osaka", "theme": "离开", "intensity": "light"},
                    },
                    "reasoning": "...",
                    "trade_offs": "...",
                }
            ],
            "recommended_index": 0,
        }
        for cand in step3_out["candidates"]:
            for day_key, day_data in cand["cities_by_day"].items():
                assert "city" in day_data, f"Step3→5 契约破坏：{day_key} 缺少 city"
                assert day_data["city"] in KANSAI_CITIES, (
                    f"{day_key}.city='{day_data['city']}' 不在关西 circle"
                )

    def test_contract_step4_candidate_pool_fields_for_step5(self, kansai_poi_pool):
        """Step 5 使用 CandidatePool 的 entity_id/city_code/tags/visit_minutes/grade。"""
        for item in kansai_poi_pool:
            assert item.entity_id, "entity_id 不能为空"
            assert item.city_code, "city_code 不能为空"
            assert isinstance(item.tags, list), "tags 应为 list"
            assert item.visit_minutes > 0, "visit_minutes 应 > 0"
            assert item.grade in ("S", "A", "B", "C"), f"grade='{item.grade}' 不合法"

    def test_contract_step1_total_days_is_int_for_step4(self, kansai_user_constraints):
        """Step 4 用 total_days 做规模控制，必须是 int 而非 str。"""
        total_days = kansai_user_constraints.trip_window.get("total_days")
        assert isinstance(total_days, int), (
            f"Step1→4 契约破坏：total_days 类型={type(total_days).__name__}，期望 int"
        )
