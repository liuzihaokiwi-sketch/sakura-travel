"""
Input Understanding Grader — 输入理解层 grader (E6)

规则化对比 normalized_profile（实际）vs expected（用例期望）。
评测维度：
  I1. 目的地映射正确性     (25分)
  I2. 行程风格判断         (20分)
  I3. 主题家族归类         (20分)
  I4. 预算层级映射         (20分)
  I5. 同行结构识别         (15分)
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from app.evals.engine import EvalCase, EvalLayer, EvalTrace, GraderOutput, Severity

logger = logging.getLogger(__name__)


class InputUnderstandingGrader:
    """
    输入理解层 grader — 规则化，不依赖 LLM。
    比较 normalized_profile（从 trace 或生成结果中提取）
    与 case.normalized_profile_expected 之间的差异。
    """

    layer = EvalLayer.INPUT

    def grade(
        self,
        case: EvalCase,
        normalized_profile: dict[str, Any],
        trace: Optional[EvalTrace] = None,
    ) -> GraderOutput:
        """
        Parameters
        ----------
        case : EvalCase
            评测用例（含 normalized_profile_expected）
        normalized_profile : dict
            生成管线实际产出的 normalized profile
        trace : EvalTrace, optional
            预留，trace 接入后可从中自动提取 profile
        """
        expected = case.normalized_profile_expected or {}
        actual = normalized_profile or {}
        dimension_scores: list[dict[str, Any]] = []

        # ── I1 目的地映射正确性 ──────────────────────────────────────────────
        i1_score, i1_issues = self._check_city_codes(
            actual.get("city_codes", []),
            expected.get("city_codes", []),
            case.user_input,
        )
        dimension_scores.append({
            "id": "I1", "name": "目的地映射正确性",
            "score": i1_score, "max": 25, "issues": i1_issues,
        })

        # ── I2 行程风格判断 ──────────────────────────────────────────────────
        i2_score, i2_issues = self._check_trip_style(
            actual.get("trip_style"),
            expected.get("trip_style"),
            case.user_input,
        )
        dimension_scores.append({
            "id": "I2", "name": "行程风格判断",
            "score": i2_score, "max": 20, "issues": i2_issues,
        })

        # ── I3 主题家族归类 ──────────────────────────────────────────────────
        i3_score, i3_issues = self._check_theme_family(
            actual.get("theme_family"),
            expected.get("theme_family"),
        )
        dimension_scores.append({
            "id": "I3", "name": "主题家族归类",
            "score": i3_score, "max": 20, "issues": i3_issues,
        })

        # ── I4 预算层级映射 ──────────────────────────────────────────────────
        i4_score, i4_issues = self._check_budget_level(
            actual.get("budget_level"),
            expected.get("budget_level"),
            case.user_input,
        )
        dimension_scores.append({
            "id": "I4", "name": "预算层级映射",
            "score": i4_score, "max": 20, "issues": i4_issues,
        })

        # ── I5 同行结构识别 ──────────────────────────────────────────────────
        i5_score, i5_issues = self._check_party_type(
            actual.get("party_type"),
            expected.get("party_type"),
            case.user_input,
        )
        dimension_scores.append({
            "id": "I5", "name": "同行结构识别",
            "score": i5_score, "max": 15, "issues": i5_issues,
        })

        total = sum(d["score"] for d in dimension_scores)
        all_issues = [i for d in dimension_scores for i in d["issues"]]

        pass_threshold = 80  # 输入理解要求更严
        if total >= pass_threshold:
            severity = Severity.OK
        elif total >= 60:
            severity = Severity.WARNING
        else:
            severity = Severity.ERROR

        return GraderOutput(
            layer=self.layer,
            grader_id="input_understanding_grader_v1",
            score=total,
            max_score=100,
            passed=total >= pass_threshold,
            severity=severity,
            dimension_scores=dimension_scores,
            issues=all_issues,
            metadata={
                "expected": expected,
                "actual": actual,
                "pass_threshold": pass_threshold,
            },
        )

    # ── 内部检查方法 ─────────────────────────────────────────────────────────

    def _check_city_codes(
        self,
        actual: list[str],
        expected: list[str],
        user_input: dict[str, Any],
    ) -> tuple[int, list[str]]:
        issues = []
        if not expected:
            # 从 user_input 推断期望
            cities = user_input.get("cities", [])
            expected = [c.get("city_code", "") for c in cities if isinstance(c, dict)]

        if not expected:
            return 25, []  # 无期望，跳过

        actual_set = set(c.lower() for c in actual)
        expected_set = set(c.lower() for c in expected)

        missing = expected_set - actual_set
        extra = actual_set - expected_set

        if not missing and not extra:
            return 25, []

        if missing:
            issues.append(f"城市映射缺失：{list(missing)}")
        if extra:
            issues.append(f"城市映射多余：{list(extra)}（用户未填写）")

        match_ratio = len(actual_set & expected_set) / max(len(expected_set), 1)
        if match_ratio >= 0.9:
            return 20, issues
        if match_ratio >= 0.7:
            return 12, issues
        if match_ratio >= 0.5:
            return 6, issues
        return 0, issues

    def _check_trip_style(
        self,
        actual: Optional[str],
        expected: Optional[str],
        user_input: dict[str, Any],
    ) -> tuple[int, list[str]]:
        issues = []
        if not expected:
            # 从 user_input 推断
            expected = user_input.get("trip_style")

        if not expected:
            return 20, []

        if actual == expected:
            return 20, []

        # 检查是否是合理的推断差异
        city_count = len(user_input.get("cities", []) or [])
        if city_count >= 2 and expected == "multi_city" and actual == "one_city":
            issues.append(f"行程风格误判：用户有 {city_count} 个城市，应为 multi_city，实际映射为 {actual}")
            return 5, issues
        if city_count == 1 and expected == "one_city" and actual == "multi_city":
            issues.append(f"行程风格误判：用户仅 1 城，应为 one_city，实际映射为 {actual}")
            return 5, issues

        issues.append(f"行程风格不符：期望 {expected}，实际 {actual}")
        return 10, issues

    def _check_theme_family(
        self,
        actual: Optional[str],
        expected: Optional[str],
    ) -> tuple[int, list[str]]:
        if not expected:
            return 20, []  # 无期望，跳过

        if actual == expected:
            return 20, []

        # 相近主题族（可接受的误差）
        SIMILAR_FAMILIES: dict[str, set[str]] = {
            "classic_first": {"culture_deep", "shopping_first"},
            "nature_onsen": {"relaxed_scenic"},
            "gourmet_focus": {"classic_first"},
        }
        if actual in SIMILAR_FAMILIES.get(expected, set()):
            return 12, [f"主题家族近似但不完全匹配：期望 {expected}，实际 {actual}"]

        return 5, [f"主题家族明显不符：期望 {expected}，实际 {actual}"]

    def _check_budget_level(
        self,
        actual: Optional[str],
        expected: Optional[str],
        user_input: dict[str, Any],
    ) -> tuple[int, list[str]]:
        issues = []
        if not expected:
            expected = user_input.get("budget_level")

        if not expected:
            return 20, []

        BUDGET_ORDER = ["budget", "mid", "premium", "luxury"]

        if actual == expected:
            return 20, []

        try:
            diff = abs(BUDGET_ORDER.index(actual) - BUDGET_ORDER.index(expected))
        except ValueError:
            issues.append(f"预算层级映射异常值：期望 {expected}，实际 {actual}")
            return 0, issues

        if diff == 1:
            issues.append(f"预算层级偏差一级：期望 {expected}，实际 {actual}")
            return 10, issues

        issues.append(f"预算层级严重偏差（{diff}级）：期望 {expected}，实际 {actual}")
        return 0, issues

    def _check_party_type(
        self,
        actual: Optional[str],
        expected: Optional[str],
        user_input: dict[str, Any],
    ) -> tuple[int, list[str]]:
        if not expected:
            expected = user_input.get("party_type")

        if not expected:
            return 15, []

        if actual == expected:
            return 15, []

        # 近似可接受
        SIMILAR: dict[str, set[str]] = {
            "family_no_kids": {"family_with_kids"},
            "family_with_kids": {"family_no_kids"},
            "couple": {"solo"},
        }
        if actual in SIMILAR.get(expected, set()):
            return 8, [f"同行结构近似不符：期望 {expected}，实际 {actual}"]

        return 0, [f"同行结构完全不符：期望 {expected}，实际 {actual}"]
