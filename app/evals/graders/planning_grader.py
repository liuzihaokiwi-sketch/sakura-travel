"""
Planning Grader — 规划层 grader (E2)

基于 trace 数据检查生成结果的规划质量：
  1. 顺路性 — 相邻景点地理距离/交通时间是否合理
  2. 节奏适配 — 每天景点数量是否匹配用户节奏偏好
  3. 到离时间一致性 — 首末日是否考虑航班到达/离开时间
  4. 预算偏向一致性 — 餐厅/住宿档次是否匹配预算级别
  5. 片段命中 vs 期望 — 片段复用是否符合预期
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.evals.engine import EvalCase, EvalLayer, EvalTrace, GraderOutput, Severity

logger = logging.getLogger(__name__)


class PlanningGrader:
    """规划层 grader — 基于 trace + output 的规则化检查"""

    @property
    def name(self) -> str:
        return "planning_grader"

    @property
    def layer(self) -> EvalLayer:
        return EvalLayer.PLANNING

    async def grade(
        self, case: EvalCase, trace: EvalTrace, output: Any
    ) -> GraderOutput:
        details: list[dict] = []
        total_score = 0.0
        max_score = 0.0

        # Dim 1: 顺路性 (20 分)
        d1 = self._check_route_coherence(case, trace, output)
        details.append(d1)
        total_score += d1["score"]
        max_score += d1["max"]

        # Dim 2: 节奏适配 (20 分)
        d2 = self._check_pace_fit(case, trace, output)
        details.append(d2)
        total_score += d2["score"]
        max_score += d2["max"]

        # Dim 3: 到离时间一致性 (20 分)
        d3 = self._check_arrival_departure(case, trace, output)
        details.append(d3)
        total_score += d3["score"]
        max_score += d3["max"]

        # Dim 4: 预算偏向一致性 (20 分)
        d4 = self._check_budget_alignment(case, trace, output)
        details.append(d4)
        total_score += d4["score"]
        max_score += d4["max"]

        # Dim 5: 片段命中 vs 期望 (20 分)
        d5 = self._check_fragment_hits(case, trace)
        details.append(d5)
        total_score += d5["score"]
        max_score += d5["max"]

        normalized = (total_score / max_score * 100) if max_score > 0 else 0

        if normalized >= 70:
            severity = Severity.PASS
        elif normalized >= 50:
            severity = Severity.WARNING
        else:
            severity = Severity.FAIL

        return GraderOutput(
            grader_name=self.name,
            layer=self.layer,
            score=round(normalized, 1),
            max_score=100.0,
            severity=severity,
            details=details,
        )

    def _check_route_coherence(self, case: EvalCase, trace: EvalTrace, output: Any) -> dict:
        """检查路线连贯性"""
        max_score = 20
        score = max_score  # 默认满分，扣分制
        issues = []

        if not output or not isinstance(output, dict):
            return {"dimension": "route_coherence", "score": 0, "max": max_score, "issues": ["no_output"]}

        days = output.get("days", [])
        if not days:
            return {"dimension": "route_coherence", "score": 0, "max": max_score, "issues": ["no_days"]}

        for i in range(len(days) - 1):
            curr_city = days[i].get("city", "")
            next_city = days[i + 1].get("city", "")
            # 不同城市间切换需要合理（非每天换城市）
            if curr_city != next_city:
                # 可以接受，但连续3天换3个城市则扣分
                if i + 2 < len(days) and days[i + 2].get("city", "") != next_city:
                    score -= 4
                    issues.append(f"day{i+1}-{i+3} 连续换城市")

        # 检查同一天内是否有太多景点（暗示路线不顺）
        for i, day in enumerate(days):
            items = day.get("items", [])
            if len(items) > 8:
                score -= 3
                issues.append(f"day{i+1} 景点过多({len(items)})")

        return {"dimension": "route_coherence", "score": max(score, 0), "max": max_score, "issues": issues}

    def _check_pace_fit(self, case: EvalCase, trace: EvalTrace, output: Any) -> dict:
        """检查节奏是否匹配用户偏好"""
        max_score = 20
        score = max_score
        issues = []

        pace = case.user_input.get("pace", "moderate")
        days = (output or {}).get("days", [])

        pace_limits = {"relaxed": 4, "moderate": 6, "packed": 9}
        limit = pace_limits.get(pace, 6)

        over_days = 0
        for i, day in enumerate(days):
            items = day.get("items", [])
            if len(items) > limit:
                over_days += 1
                issues.append(f"day{i+1}: {len(items)} items > {pace} limit {limit}")

        if days:
            over_ratio = over_days / len(days)
            if over_ratio > 0.5:
                score -= 10
            elif over_ratio > 0.2:
                score -= 5

        return {"dimension": "pace_fit", "score": max(score, 0), "max": max_score, "issues": issues}

    def _check_arrival_departure(self, case: EvalCase, trace: EvalTrace, output: Any) -> dict:
        """检查首末日是否考虑到达/离开时间"""
        max_score = 20
        score = max_score
        issues = []

        days = (output or {}).get("days", [])
        if not days:
            return {"dimension": "arrival_departure", "score": 0, "max": max_score, "issues": ["no_days"]}

        # 首日：如果到达时间很晚，不应该安排太多景点
        flight_info = case.user_input.get("flight_info", {})
        arrival = flight_info.get("outbound", {}).get("arrive", "")

        if arrival:
            try:
                hour = int(arrival.split(":")[0])
                first_day_items = days[0].get("items", [])
                if hour >= 18 and len(first_day_items) > 3:
                    score -= 8
                    issues.append(f"晚到({arrival})但首日安排{len(first_day_items)}个景点")
                elif hour >= 14 and len(first_day_items) > 5:
                    score -= 4
                    issues.append(f"下午到({arrival})但首日安排较多")
            except (ValueError, IndexError):
                pass

        # 末日：不应该安排太满，要留出去机场的时间
        last_day_items = days[-1].get("items", [])
        if len(last_day_items) > 4:
            score -= 4
            issues.append(f"末日安排{len(last_day_items)}个景点，可能赶不上航班")

        return {"dimension": "arrival_departure", "score": max(score, 0), "max": max_score, "issues": issues}

    def _check_budget_alignment(self, case: EvalCase, trace: EvalTrace, output: Any) -> dict:
        """检查预算偏向是否一致"""
        max_score = 20
        score = max_score
        issues = []

        budget_level = case.user_input.get("budget_level", "mid")
        budget_focus = case.user_input.get("budget_focus", "balanced")

        # 基于 trace 中的片段信息检查
        if trace.normalized_profile:
            prof_budget = trace.normalized_profile.get("budget_level")
            if prof_budget and prof_budget != budget_level:
                score -= 10
                issues.append(f"profile budget={prof_budget} != input budget={budget_level}")

        # 如果没有足够的 trace 数据，给基准分
        if not trace.fragments_hit and not trace.normalized_profile:
            score = int(max_score * 0.6)
            issues.append("insufficient_trace_data")

        return {"dimension": "budget_alignment", "score": max(score, 0), "max": max_score, "issues": issues}

    def _check_fragment_hits(self, case: EvalCase, trace: EvalTrace) -> dict:
        """检查片段命中是否符合期望"""
        max_score = 20
        score = max_score
        issues = []

        expected = case.fragment_hit_expectation
        if not expected:
            return {"dimension": "fragment_hits", "score": int(max_score * 0.7), "max": max_score, "issues": ["no_expectation_defined"]}

        # 检查应该命中的片段
        should_hit = expected.get("should_hit_fragments", [])
        actual_hit_ids = [f.get("fragment_id", "") for f in trace.fragments_hit]

        for frag_id in should_hit:
            if frag_id not in actual_hit_ids:
                score -= 4
                issues.append(f"expected_hit_miss: {frag_id}")

        # 检查应该避免的片段
        should_avoid = expected.get("should_avoid_fragments", [])
        for frag_id in should_avoid:
            if frag_id in actual_hit_ids:
                score -= 6
                issues.append(f"unexpected_hit: {frag_id}")

        return {"dimension": "fragment_hits", "score": max(score, 0), "max": max_score, "issues": issues}
