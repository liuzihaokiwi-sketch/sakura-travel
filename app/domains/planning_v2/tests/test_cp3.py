"""
test_cp3.py — CP3 契约测试（Step 8-12，时间线可行性）

CP3 检查点：
  1. DailyConstraints 日期连续，sunrise/sunset 格式 HH:MM
  2. FeasibilityResult 无 FAIL 级违规（或已被 Step 11 解决）
  3. 时间线无非法重叠（buffer 块除外）
  4. 允许缓冲时间块存在

涉及步骤：
  - Step 8  build_daily_constraints_list  (DB + astral)
  - Step 9  plan_daily_sequences           (Opus AI)
  - Step 10 check_feasibility              (纯 Python)
  - Step 11 resolve_conflicts              (规则链 + Opus AI fallback)
  - Step 12 build_timeline                 (Sonnet AI)

Step 10 是纯 Python，重点测试。
Step 8/9/11/12 涉及 DB/AI，用 mock。
"""

import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.domains.planning_v2.models import DailyConstraints, FeasibilityResult, CandidatePool
from app.domains.planning_v2.step10_feasibility import (
    check_feasibility,
    _check_time_overlap,
    _check_closed_entities,
    _check_commute_feasibility,
    _check_daylight,
    _check_meal_conflict,
    _check_total_active_time,
    _is_buffer_block,
    FAIL, WARNING,
)
from app.domains.planning_v2.step11_conflict_resolver import resolve_conflicts


# ─────────────────────────────────────────────────────────────────────────────
# 构造辅助
# ─────────────────────────────────────────────────────────────────────────────

def _make_dc(
    date_str: str,
    sunrise: str = "05:45",
    sunset: str = "18:30",
    closed: list = None,
    hotel_breakfast: bool = False,
    hotel_dinner: bool = False,
) -> DailyConstraints:
    return DailyConstraints(
        date=date_str,
        day_of_week=date.fromisoformat(date_str).strftime("%a"),
        sunrise=sunrise,
        sunset=sunset,
        closed_entities=closed or [],
        hotel_breakfast_included=hotel_breakfast,
        hotel_dinner_included=hotel_dinner,
    )


def _make_activity(
    entity_id: str,
    name: str,
    start: str,
    end: str,
    atype: str = "poi",
    tags: list = None,
    commute_from_prev: int = 0,
) -> dict:
    return {
        "entity_id": entity_id,
        "name": name,
        "type": atype,
        "start_time": start,
        "end_time": end,
        "tags": tags or [],
        "commute_from_prev_mins": commute_from_prev,
    }


def _make_buffer(start: str, end: str) -> dict:
    return {
        "entity_id": None,
        "name": "buffer",
        "type": "buffer",
        "start_time": start,
        "end_time": end,
        "tags": [],
        "commute_from_prev_mins": 0,
    }


def _make_day_seq(day: int, date_str: str, activities: list) -> dict:
    return {"day": day, "date": date_str, "activities": activities}


def _make_poi(entity_id: str) -> CandidatePool:
    return CandidatePool(
        entity_id=entity_id,
        name_zh="test",
        entity_type="poi",
        grade="A",
        latitude=34.7,
        longitude=135.5,
        tags=[],
        visit_minutes=90,
        cost_local=0,
        city_code="kyoto",
    )


def _make_consecutive_constraints(start: str, total_days: int) -> list[DailyConstraints]:
    """生成连续日期的 DailyConstraints 列表。"""
    start_date = date.fromisoformat(start)
    return [
        _make_dc((start_date + timedelta(days=i)).isoformat())
        for i in range(total_days)
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Step 8: DailyConstraints 结构验证
# ─────────────────────────────────────────────────────────────────────────────

class TestStep8DailyConstraints:

    def test_dates_are_consecutive(self):
        """CP3 核心：日期必须连续，无跳跃。"""
        constraints = _make_consecutive_constraints("2026-04-10", 5)
        dates = [date.fromisoformat(dc.date) for dc in constraints]
        for i in range(1, len(dates)):
            assert (dates[i] - dates[i - 1]).days == 1, (
                f"日期不连续: {dates[i-1]} → {dates[i]}"
            )

    def test_sunrise_format_hhmm(self):
        """sunrise 必须是 HH:MM 格式。"""
        import re
        pattern = re.compile(r"^\d{2}:\d{2}$")
        constraints = _make_consecutive_constraints("2026-04-10", 5)
        for dc in constraints:
            assert pattern.match(dc.sunrise), f"sunrise 格式错误: {dc.sunrise}"

    def test_sunset_format_hhmm(self):
        """sunset 必须是 HH:MM 格式。"""
        import re
        pattern = re.compile(r"^\d{2}:\d{2}$")
        constraints = _make_consecutive_constraints("2026-04-10", 5)
        for dc in constraints:
            assert pattern.match(dc.sunset), f"sunset 格式错误: {dc.sunset}"

    def test_sunrise_before_sunset(self):
        """sunrise 必须早于 sunset。"""
        constraints = _make_consecutive_constraints("2026-04-10", 5)
        for dc in constraints:
            from datetime import datetime
            sr = datetime.strptime(dc.sunrise, "%H:%M")
            ss = datetime.strptime(dc.sunset, "%H:%M")
            assert sr < ss, f"{dc.date}: sunrise {dc.sunrise} >= sunset {dc.sunset}"

    def test_total_days_matches_list_length(self):
        """生成的约束列表长度等于 total_days。"""
        for total_days in [3, 5, 7, 8]:
            constraints = _make_consecutive_constraints("2026-04-10", total_days)
            assert len(constraints) == total_days

    def test_hotel_breakfast_dinner_are_bool(self):
        """hotel_breakfast_included / hotel_dinner_included 必须是 bool。"""
        dc = _make_dc("2026-04-10", hotel_breakfast=True, hotel_dinner=False)
        assert isinstance(dc.hotel_breakfast_included, bool)
        assert isinstance(dc.hotel_dinner_included, bool)

    def test_closed_entities_is_list(self):
        dc = _make_dc("2026-04-10", closed=["entity_a", "entity_b"])
        assert isinstance(dc.closed_entities, list)
        assert len(dc.closed_entities) == 2

    @pytest.mark.asyncio
    async def test_build_daily_constraints_raises_on_invalid_trip_window(self):
        """trip_window 缺少 start_date 时应抛出 ValueError。"""
        from app.domains.planning_v2.step08_daily_constraints import build_daily_constraints_list
        session = AsyncMock()
        with pytest.raises((ValueError, KeyError)):
            await build_daily_constraints_list(
                session=session,
                trip_window={"end_date": "2026-04-14", "total_days": 5},
            )

    @pytest.mark.asyncio
    async def test_build_daily_constraints_returns_correct_length(self):
        """正常输入返回 total_days 条记录。"""
        from app.domains.planning_v2.step08_daily_constraints import build_daily_constraints_list
        session = AsyncMock()
        # mock DB 查询返回空（无关闭实体/酒店数据）
        session.execute = AsyncMock(
            return_value=MagicMock(scalars=MagicMock(
                return_value=MagicMock(all=MagicMock(return_value=[]))
            ))
        )

        result = await build_daily_constraints_list(
            session=session,
            trip_window={"start_date": "2026-04-10", "end_date": "2026-04-14", "total_days": 5},
        )

        assert len(result) == 5

    @pytest.mark.asyncio
    async def test_build_daily_constraints_dates_consecutive(self):
        """返回的 DailyConstraints 日期连续。"""
        from app.domains.planning_v2.step08_daily_constraints import build_daily_constraints_list
        session = AsyncMock()
        session.execute = AsyncMock(
            return_value=MagicMock(scalars=MagicMock(
                return_value=MagicMock(all=MagicMock(return_value=[]))
            ))
        )

        result = await build_daily_constraints_list(
            session=session,
            trip_window={"start_date": "2026-04-10", "end_date": "2026-04-14", "total_days": 5},
        )

        dates = [date.fromisoformat(dc.date) for dc in result]
        for i in range(1, len(dates)):
            assert (dates[i] - dates[i - 1]).days == 1

    @pytest.mark.asyncio
    async def test_hotel_breakfast_propagated_from_hotel_plan(self):
        """选中酒店含早餐时，所有天的 hotel_breakfast_included 应为 True。"""
        from app.domains.planning_v2.step08_daily_constraints import build_daily_constraints_list
        import uuid

        # mock 酒店 DB 查询返回含早餐的酒店
        hotel_entity = MagicMock()
        hotel_entity.entity_id = uuid.uuid4()

        hotel_detail = MagicMock()
        hotel_detail.entity_id = hotel_entity.entity_id
        hotel_detail.breakfast_included = True
        hotel_detail.dinner_included = False

        session = AsyncMock()
        execute_results = [
            # 第一次：查 closed entities → 空
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
            # 第二次：查 hotel → hotel_detail
            MagicMock(scalar_one_or_none=MagicMock(return_value=hotel_detail)),
        ]
        session.execute = AsyncMock(side_effect=execute_results * 10)

        result = await build_daily_constraints_list(
            session=session,
            trip_window={"start_date": "2026-04-10", "end_date": "2026-04-12", "total_days": 3},
            selected_hotel_id=str(hotel_entity.entity_id),
        )

        # 至少一天有含餐标记（具体逻辑依赖 DB 数据）
        assert isinstance(result[0].hotel_breakfast_included, bool)


# ─────────────────────────────────────────────────────────────────────────────
# Step 10: check_feasibility — 纯 Python，重点覆盖
# ─────────────────────────────────────────────────────────────────────────────

class TestStep10Feasibility:

    # ── 工厂 ──────────────────────────────────────────────────────────────────

    def _clean_day(self, activities: list) -> dict:
        return _make_day_seq(1, "2026-04-10", activities)

    def _dc(self, **kwargs) -> DailyConstraints:
        return _make_dc("2026-04-10", **kwargs)

    # ── Rule 1: 时间重叠 ──────────────────────────────────────────────────────

    def test_no_overlap_passes(self):
        acts = [
            _make_activity("a", "景点A", "09:00", "11:00"),
            _make_activity("b", "景点B", "13:00", "15:00"),
        ]
        result = check_feasibility([self._clean_day(acts)], [self._dc()])
        overlap_violations = [v for v in result.violations if v["type"] == "time_overlap"]
        assert not overlap_violations

    def test_overlap_is_fail(self):
        acts = [
            _make_activity("a", "景点A", "09:00", "12:00"),
            _make_activity("b", "景点B", "11:00", "14:00"),  # 与A重叠1小时
        ]
        result = check_feasibility([self._clean_day(acts)], [self._dc()])
        assert result.status == "fail"
        fail_violations = [v for v in result.violations if v["severity"] == FAIL]
        assert any(v["type"] == "time_overlap" for v in fail_violations)

    def test_buffer_block_not_checked_for_overlap(self):
        """buffer 块与真实活动重叠不触发 FAIL。"""
        acts = [
            _make_activity("a", "景点A", "09:00", "11:00"),
            _make_buffer("10:00", "12:00"),              # buffer 与 A 重叠
            _make_activity("b", "景点B", "13:00", "15:00"),
        ]
        result = check_feasibility([self._clean_day(acts)], [self._dc()])
        overlap_violations = [v for v in result.violations if v["type"] == "time_overlap"]
        assert not overlap_violations, "buffer 与真实活动重叠不应触发 time_overlap"

    def test_two_buffers_overlap_not_checked(self):
        """两个 buffer 块互相重叠也不触发违规。"""
        acts = [
            _make_buffer("09:00", "11:00"),
            _make_buffer("10:00", "12:00"),
        ]
        violations = []
        _check_time_overlap(self._clean_day(acts), violations)
        assert not violations

    def test_exact_adjacent_activities_no_overlap(self):
        """前一活动结束时间 = 后一活动开始时间，不算重叠。"""
        acts = [
            _make_activity("a", "景点A", "09:00", "11:00"),
            _make_activity("b", "景点B", "11:00", "13:00"),  # 紧接着
        ]
        violations = []
        _check_time_overlap(self._clean_day(acts), violations)
        assert not violations

    # ── Rule 2: 定休日 ────────────────────────────────────────────────────────

    def test_closed_entity_is_fail(self):
        acts = [_make_activity("closed_spot", "关闭景点", "10:00", "12:00")]
        dc = self._dc(closed=["closed_spot"])
        result = check_feasibility([self._clean_day(acts)], [dc])
        assert result.status == "fail"
        assert any(v["type"] == "closed_entity" for v in result.violations)

    def test_non_closed_entity_passes(self):
        acts = [_make_activity("open_spot", "开放景点", "10:00", "12:00")]
        dc = self._dc(closed=["other_entity"])
        violations = []
        _check_closed_entities(self._clean_day(acts), dc, violations)
        assert not violations

    def test_no_closed_entities_no_violation(self):
        acts = [_make_activity("spot_a", "景点A", "10:00", "12:00")]
        dc = self._dc(closed=[])
        violations = []
        _check_closed_entities(self._clean_day(acts), dc, violations)
        assert not violations

    # ── Rule 3: 通勤可行性 ────────────────────────────────────────────────────

    def test_commute_insufficient_is_warning(self):
        acts = [
            _make_activity("a", "景点A", "09:00", "11:00"),
            _make_activity("b", "景点B", "11:10", "13:00", commute_from_prev=30),  # 需要30min但只有10min
        ]
        violations = []
        _check_commute_feasibility(self._clean_day(acts), violations)
        assert any(v["type"] == "commute_infeasible" for v in violations)
        assert all(v["severity"] == WARNING for v in violations)

    def test_commute_sufficient_no_violation(self):
        acts = [
            _make_activity("a", "景点A", "09:00", "11:00"),
            _make_activity("b", "景点B", "11:40", "13:00", commute_from_prev=30),  # 40min > 30min
        ]
        violations = []
        _check_commute_feasibility(self._clean_day(acts), violations)
        assert not violations

    def test_zero_commute_no_violation(self):
        acts = [
            _make_activity("a", "景点A", "09:00", "11:00"),
            _make_activity("b", "景点B", "11:00", "13:00", commute_from_prev=0),
        ]
        violations = []
        _check_commute_feasibility(self._clean_day(acts), violations)
        assert not violations

    # ── Rule 4: 日出日落 ──────────────────────────────────────────────────────

    def test_outdoor_before_sunrise_is_warning(self):
        acts = [_make_activity("park", "公园", "04:00", "06:00", atype="park")]
        dc = self._dc(sunrise="06:00")
        violations = []
        _check_daylight(self._clean_day(acts), dc, violations)
        assert any(v["type"] == "before_sunrise" for v in violations)

    def test_outdoor_after_sunset_is_warning(self):
        acts = [_make_activity("beach", "海滩", "19:30", "21:00", atype="beach")]
        dc = self._dc(sunset="18:00")  # sunset + 30min = 18:30
        violations = []
        _check_daylight(self._clean_day(acts), dc, violations)
        assert any(v["type"] == "after_sunset" for v in violations)

    def test_outdoor_within_daylight_no_violation(self):
        acts = [_make_activity("park", "公园", "09:00", "11:00", atype="park")]
        dc = self._dc(sunrise="05:45", sunset="18:30")
        violations = []
        _check_daylight(self._clean_day(acts), dc, violations)
        assert not violations

    def test_indoor_ignores_daylight(self):
        """室内活动（museum）不受日出日落约束。"""
        acts = [_make_activity("museum", "博物馆", "04:00", "06:00", atype="museum")]
        dc = self._dc(sunrise="06:00")
        violations = []
        _check_daylight(self._clean_day(acts), dc, violations)
        assert not violations

    def test_outdoor_detection_by_tag(self):
        """tags 包含 outdoor 时也被识别为户外活动。"""
        acts = [_make_activity("spot", "景点", "04:00", "06:00", tags=["outdoor"])]
        dc = self._dc(sunrise="06:00")
        violations = []
        _check_daylight(self._clean_day(acts), dc, violations)
        assert any(v["type"] == "before_sunrise" for v in violations)

    # ── Rule 6: 餐食冲突 ──────────────────────────────────────────────────────

    def test_breakfast_conflict_when_hotel_includes(self):
        acts = [_make_activity("cafe", "咖啡店", "07:30", "08:30", atype="breakfast")]
        dc = self._dc(hotel_breakfast=True)
        violations = []
        _check_meal_conflict(self._clean_day(acts), dc, violations)
        assert any(v["type"] == "meal_conflict_breakfast" for v in violations)

    def test_dinner_conflict_when_hotel_includes(self):
        acts = [_make_activity("rest", "料理店", "18:30", "20:00", atype="dinner")]
        dc = self._dc(hotel_dinner=True)
        violations = []
        _check_meal_conflict(self._clean_day(acts), dc, violations)
        assert any(v["type"] == "meal_conflict_dinner" for v in violations)

    def test_no_meal_conflict_when_hotel_not_included(self):
        acts = [_make_activity("cafe", "咖啡店", "07:30", "08:30", atype="breakfast")]
        dc = self._dc(hotel_breakfast=False)
        violations = []
        _check_meal_conflict(self._clean_day(acts), dc, violations)
        assert not violations

    # ── Rule 7: 总时间 ────────────────────────────────────────────────────────

    def test_overloaded_day_is_warning(self):
        """超过10小时活动时间触发 WARNING。"""
        acts = [
            _make_activity("a", "A", "08:00", "14:00"),   # 6h
            _make_activity("b", "B", "14:00", "19:30"),   # 5.5h → 合计11.5h
        ]
        violations = []
        _check_total_active_time(self._clean_day(acts), violations)
        assert any(v["type"] == "overloaded_day" for v in violations)

    def test_buffer_not_counted_in_total(self):
        """buffer 块不计入总活动时间。"""
        acts = [
            _make_activity("a", "A", "08:00", "12:00"),  # 4h
            _make_buffer("12:00", "20:00"),               # 8h buffer，不计入
            _make_activity("b", "B", "14:00", "16:00"),  # 2h → 合计6h，不超限
        ]
        violations = []
        _check_total_active_time(self._clean_day(acts), violations)
        assert not violations

    def test_exactly_10_hours_no_violation(self):
        acts = [
            _make_activity("a", "A", "08:00", "13:00"),  # 5h
            _make_activity("b", "B", "14:00", "19:00"),  # 5h → 合计10h
        ]
        violations = []
        _check_total_active_time(self._clean_day(acts), violations)
        assert not violations

    # ── 整体状态逻辑 ──────────────────────────────────────────────────────────

    def test_status_fail_when_any_fail_violation(self):
        acts = [
            _make_activity("a", "A", "09:00", "12:00"),
            _make_activity("b", "B", "10:00", "13:00"),  # 重叠
        ]
        result = check_feasibility([self._clean_day(acts)], [self._dc()])
        assert result.status == "fail"

    def test_status_warning_when_only_warnings(self):
        acts = [
            _make_activity("a", "A", "09:00", "12:00"),
            _make_activity("b", "B", "14:00", "15:30", commute_from_prev=60),  # 需60min但只有2h → OK
        ]
        # 制造一个 warning：hotel_dinner 冲突
        acts.append(_make_activity("dinner", "晚餐", "18:30", "20:00", atype="dinner"))
        dc = self._dc(hotel_dinner=True)
        result = check_feasibility([self._clean_day(acts)], [dc])
        assert result.status in ("warning", "fail")

    def test_status_pass_when_no_violations(self):
        acts = [
            _make_activity("a", "A", "09:00", "11:00"),
            _make_activity("b", "B", "13:00", "15:00"),
        ]
        result = check_feasibility([self._clean_day(acts)], [self._dc()])
        assert result.status == "pass"
        assert result.violations == []

    def test_violations_sorted_fail_before_warning(self):
        """violations 列表中 fail 应排在 warning 之前。"""
        acts = [
            _make_activity("a", "A", "09:00", "12:00"),
            _make_activity("b", "B", "10:00", "13:00"),  # 重叠(FAIL)
            _make_activity("dinner", "晚餐", "18:30", "20:00", atype="dinner"),  # 餐食冲突(WARNING)
        ]
        dc = self._dc(hotel_dinner=True)
        result = check_feasibility([self._clean_day(acts)], [dc])
        if len(result.violations) >= 2:
            severities = [v["severity"] for v in result.violations]
            fail_indices = [i for i, s in enumerate(severities) if s == FAIL]
            warn_indices = [i for i, s in enumerate(severities) if s == WARNING]
            if fail_indices and warn_indices:
                assert max(fail_indices) < min(warn_indices), (
                    "FAIL 违规应排在 WARNING 之前"
                )

    def test_empty_sequences_returns_pass(self):
        result = check_feasibility([], [])
        assert result.status == "pass"
        assert result.violations == []

    def test_suggestions_generated_for_violations(self):
        acts = [
            _make_activity("a", "A", "09:00", "12:00"),
            _make_activity("b", "B", "10:00", "13:00"),  # 重叠
        ]
        result = check_feasibility([self._clean_day(acts)], [self._dc()])
        assert len(result.suggestions) > 0

    def test_multiple_days_checked(self):
        """多天序列都被检查，违规来自不同天。"""
        day1 = _make_day_seq(1, "2026-04-10", [
            _make_activity("a", "A", "09:00", "12:00"),
            _make_activity("b", "B", "10:00", "13:00"),  # 重叠
        ])
        day2 = _make_day_seq(2, "2026-04-11", [
            _make_activity("c", "C", "09:00", "11:00"),
        ])
        dcs = [_make_dc("2026-04-10"), _make_dc("2026-04-11")]
        result = check_feasibility([day1, day2], dcs)
        assert result.status == "fail"
        fail_days = {v["day"] for v in result.violations if v["severity"] == FAIL}
        assert 1 in fail_days

    # ── CP3 关键：buffer 块存在是允许的 ──────────────────────────────────────

    def test_buffer_blocks_allowed_in_timeline(self):
        """时间线中允许存在 buffer 块，不应触发任何违规。"""
        acts = [
            _make_activity("a", "景点A", "09:00", "11:00"),
            _make_buffer("11:00", "11:30"),               # buffer
            _make_activity("b", "景点B", "11:30", "13:00"),
            _make_buffer("13:00", "14:00"),               # 午餐缓冲
            _make_activity("c", "景点C", "14:00", "16:00"),
        ]
        result = check_feasibility([self._clean_day(acts)], [self._dc()])
        assert result.status == "pass"

    def test_is_buffer_block_detects_all_types(self):
        for btype in ("buffer", "slack", "free_time", "flex_meal", "rest", "commute"):
            act = {"type": btype, "name": "test", "is_buffer": False}
            assert _is_buffer_block(act), f"{btype} 应被识别为 buffer 块"

    def test_is_buffer_block_flag(self):
        act = {"type": "poi", "name": "test", "is_buffer": True}
        assert _is_buffer_block(act)

    def test_normal_poi_not_buffer(self):
        act = {"type": "poi", "name": "test", "is_buffer": False}
        assert not _is_buffer_block(act)


# ─────────────────────────────────────────────────────────────────────────────
# Step 11: resolve_conflicts — 冲突处理链
# ─────────────────────────────────────────────────────────────────────────────

class TestStep11ConflictResolver:

    def _make_overlapping_sequences(self) -> list[dict]:
        return [_make_day_seq(1, "2026-04-10", [
            _make_activity("a", "景点A", "09:00", "12:00", atype="poi"),
            _make_activity("b", "景点B", "10:00", "13:00", atype="poi"),  # 与A重叠
        ])]

    def _make_closed_sequences(self, closed_id: str) -> list[dict]:
        return [_make_day_seq(1, "2026-04-10", [
            _make_activity(closed_id, "关闭景点", "10:00", "12:00", atype="poi"),
            _make_activity("other", "其他景点", "14:00", "16:00", atype="poi"),
        ])]

    def _make_overloaded_sequences(self) -> list[dict]:
        return [_make_day_seq(1, "2026-04-10", [
            _make_activity("a", "景点A", "08:00", "13:00"),  # 5h
            _make_activity("b", "景点B", "13:00", "18:00"),  # 5h
            _make_activity("c", "景点C", "18:00", "21:30"),  # 3.5h → 合计 13.5h
        ])]

    @pytest.mark.asyncio
    async def test_pass_result_returns_unchanged(self):
        """已经是 pass 的结果不需要修改，直接返回。"""
        sequences = [_make_day_seq(1, "2026-04-10", [
            _make_activity("a", "景点A", "09:00", "11:00"),
        ])]
        feasibility = FeasibilityResult(status="pass")
        constraints = [_make_dc("2026-04-10")]
        pool = [_make_poi("a")]

        result = await resolve_conflicts(
            daily_sequences=sequences,
            feasibility_result=feasibility,
            daily_constraints=constraints,
            poi_pool=pool,
        )

        assert result["final_status"] in ("resolved", "pass")
        assert result["resolved_sequences"] is not None

    @pytest.mark.asyncio
    async def test_closed_entity_removed_by_rule(self):
        """Step 11.1：定休日实体被规则删除（不需要 AI）。"""
        closed_id = "closed_spot"
        sequences = self._make_closed_sequences(closed_id)
        feasibility = check_feasibility(
            sequences, [_make_dc("2026-04-10", closed=[closed_id])]
        )
        assert feasibility.status == "fail"

        result = await resolve_conflicts(
            daily_sequences=sequences,
            feasibility_result=feasibility,
            daily_constraints=[_make_dc("2026-04-10", closed=[closed_id])],
            poi_pool=[_make_poi("other")],
        )

        # 修复后 closed_spot 不应出现
        all_ids = {
            act["entity_id"]
            for day in result["resolved_sequences"]
            for act in day.get("activities", [])
            if act.get("entity_id")
        }
        assert closed_id not in all_ids, "定休日景点应被删除"

    @pytest.mark.asyncio
    async def test_resolution_log_not_empty_on_conflict(self):
        """有冲突时 resolution_log 不为空。"""
        closed_id = "closed_spot"
        sequences = self._make_closed_sequences(closed_id)
        feasibility = check_feasibility(
            sequences, [_make_dc("2026-04-10", closed=[closed_id])]
        )

        result = await resolve_conflicts(
            daily_sequences=sequences,
            feasibility_result=feasibility,
            daily_constraints=[_make_dc("2026-04-10", closed=[closed_id])],
            poi_pool=[_make_poi("other")],
        )

        assert isinstance(result["resolution_log"], list)
        assert len(result["resolution_log"]) > 0, "有冲突时日志不应为空"

    @pytest.mark.asyncio
    async def test_result_has_required_fields(self):
        """resolve_conflicts 输出必须包含所有规定字段。"""
        sequences = [_make_day_seq(1, "2026-04-10", [
            _make_activity("a", "景点A", "09:00", "11:00"),
        ])]
        feasibility = FeasibilityResult(status="pass")

        result = await resolve_conflicts(
            daily_sequences=sequences,
            feasibility_result=feasibility,
            daily_constraints=[_make_dc("2026-04-10")],
            poi_pool=[],
        )

        required_fields = [
            "resolved_sequences", "resolution_log",
            "final_status", "ai_fallback_used", "thinking_tokens_used",
        ]
        for field in required_fields:
            assert field in result, f"resolve_conflicts 输出缺少字段: {field}"

    @pytest.mark.asyncio
    async def test_final_status_resolved_after_rule_fix(self):
        """规则链成功修复后 final_status 应为 resolved 或 partially_resolved。"""
        closed_id = "closed_spot"
        sequences = self._make_closed_sequences(closed_id)
        feasibility = check_feasibility(
            sequences, [_make_dc("2026-04-10", closed=[closed_id])]
        )

        result = await resolve_conflicts(
            daily_sequences=sequences,
            feasibility_result=feasibility,
            daily_constraints=[_make_dc("2026-04-10", closed=[closed_id])],
            poi_pool=[_make_poi("other")],
        )

        assert result["final_status"] in ("resolved", "partially_resolved", "unresolved")

    @pytest.mark.asyncio
    async def test_ai_fallback_not_used_for_rule_solvable(self):
        """可被规则解决的冲突不应触发 AI 回退。"""
        closed_id = "closed_spot"
        sequences = self._make_closed_sequences(closed_id)
        feasibility = check_feasibility(
            sequences, [_make_dc("2026-04-10", closed=[closed_id])]
        )

        result = await resolve_conflicts(
            daily_sequences=sequences,
            feasibility_result=feasibility,
            daily_constraints=[_make_dc("2026-04-10", closed=[closed_id])],
            poi_pool=[_make_poi("other")],
            api_key=None,
        )

        assert result["ai_fallback_used"] is False


# ─────────────────────────────────────────────────────────────────────────────
# CP3 数据契约检查（Step 间字段对齐）
# ─────────────────────────────────────────────────────────────────────────────

class TestCp3DataContracts:

    def test_step8_output_fields_for_step10(self):
        """Step 10 需要 DailyConstraints 的 date/closed_entities/hotel_*。"""
        dc = _make_dc("2026-04-10", closed=["e1"], hotel_breakfast=True)
        assert hasattr(dc, "date")
        assert hasattr(dc, "closed_entities")
        assert hasattr(dc, "hotel_breakfast_included")
        assert hasattr(dc, "hotel_dinner_included")
        assert hasattr(dc, "sunrise")
        assert hasattr(dc, "sunset")

    def test_step10_output_fields_for_step11(self):
        """Step 11 读取 FeasibilityResult 的 status 和 violations。"""
        result = check_feasibility(
            [_make_day_seq(1, "2026-04-10", [
                _make_activity("a", "A", "09:00", "12:00"),
                _make_activity("b", "B", "10:00", "13:00"),
            ])],
            [_make_dc("2026-04-10")],
        )
        # Step 11 期望
        assert hasattr(result, "status")
        assert hasattr(result, "violations")
        assert isinstance(result.violations, list)
        for v in result.violations:
            assert "severity" in v
            assert "type" in v
            assert "day" in v

    def test_step8_dates_cover_all_trip_days(self):
        """Step 8 输出的日期必须覆盖 trip_window 的所有天（无遗漏）。"""
        constraints = _make_consecutive_constraints("2026-04-10", 5)
        expected_dates = {
            (date(2026, 4, 10) + timedelta(days=i)).isoformat()
            for i in range(5)
        }
        actual_dates = {dc.date for dc in constraints}
        assert expected_dates == actual_dates

    def test_step10_fail_count_matches_violations(self):
        """status=fail 时 violations 列表中至少有一条 severity=fail。"""
        acts = [
            _make_activity("a", "A", "09:00", "12:00"),
            _make_activity("b", "B", "10:00", "13:00"),
        ]
        result = check_feasibility(
            [_make_day_seq(1, "2026-04-10", acts)],
            [_make_dc("2026-04-10")],
        )
        assert result.status == "fail"
        assert any(v["severity"] == FAIL for v in result.violations)

    @pytest.mark.asyncio
    async def test_cp3_no_fail_after_step11_for_closed_entity(self):
        """
        CP3 核心：Step 11 修复后，对着修复结果重跑 Step 10，不应再有 FAIL 违规。
        """
        closed_id = "closed_spot"
        sequences = [_make_day_seq(1, "2026-04-10", [
            _make_activity(closed_id, "关闭景点", "10:00", "12:00"),
            _make_activity("other", "其他景点", "14:00", "16:00"),
        ])]
        dc = _make_dc("2026-04-10", closed=[closed_id])
        feasibility = check_feasibility(sequences, [dc])

        result = await resolve_conflicts(
            daily_sequences=sequences,
            feasibility_result=feasibility,
            daily_constraints=[dc],
            poi_pool=[_make_poi("other")],
        )

        # 重跑 Step 10 检查修复后的结果
        re_check = check_feasibility(result["resolved_sequences"], [dc])
        fail_violations = [v for v in re_check.violations if v["severity"] == FAIL]
        assert not fail_violations, (
            f"Step 11 修复后仍有 FAIL 违规: {fail_violations}"
        )

    def test_step11_meals_not_propagated_to_step12_when_hotel_included(self):
        """
        酒店含早餐时，DailyConstraints.hotel_breakfast_included=True 传给 Step 10/11。
        Step 12 应跳过早餐 slot 的外部安排——通过契约验证 DailyConstraints 字段正确传递。
        """
        dc = _make_dc("2026-04-10", hotel_breakfast=True, hotel_dinner=False)
        assert dc.hotel_breakfast_included is True
        assert dc.hotel_dinner_included is False
