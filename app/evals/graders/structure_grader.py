"""
Structure Grader — 结构层 grader (E5)

规则化检查攻略结构完整性，不依赖 LLM。
评分维度（对照 evals/rubrics/structure_rubric.yaml）：
  S1. 总纲页完整性         (20分)
  S2. 每日页骨架完整性     (30分)
  S3. 条件页触发正确性     (20分)
  S4. 版本边界清晰度       (15分)
  S5. 静态块覆盖           (15分)
"""
from __future__ import annotations

import logging
import re
from typing import Any, Optional

from app.evals.engine import EvalCase, EvalLayer, EvalTrace, GraderOutput, Severity

logger = logging.getLogger(__name__)

# ── 必须包含的静态块关键字 ───────────────────────────────────────────────────
REQUIRED_STATIC_BLOCKS = ["出发前", "安全须知", "eSIM"]

# ── 总纲页所需字段关键字 ──────────────────────────────────────────────────────
OVERVIEW_KEYWORDS = ["行程概览", "亮点", "适合", "预算"]

# ── 每日骨架所需元素 ──────────────────────────────────────────────────────────
DAY_SKELETON_PATTERNS = [
    r"\d{2}:\d{2}",          # 时间点 HH:MM
    r"交通|地铁|步行|乘坐",    # 交通说明
    r"¥\d+|预算|花费",        # 预算估算
    r"提示|Tips|tip|建议",    # 贴士
]

# ── 条件页触发关键字映射 ──────────────────────────────────────────────────────
CONDITIONAL_PAGE_TRIGGERS: dict[str, list[str]] = {
    "onsen_ryokan": ["温泉", "旅馆", "ryokan"],
    "family_with_kids": ["儿童", "亲子", "小朋友", "Kids"],
    "has_elderly": ["无障碍", "老人", "轮椅", "缓坡"],
    "halal": ["清真", "Halal", "halal", "不含猪"],
    "jr_pass": ["JR Pass", "JR通票", "新干线通票"],
    "transport_passes": ["通票", "Pass", "一日券"],
}

# ── 版本边界关键字 ────────────────────────────────────────────────────────────
VERSION_BOUNDARY_KEYWORDS = {
    "premium": ["尊享版", "premium", "专属", "升级"],
    "standard": ["标准版", "standard"],
}


class StructureGrader:
    """
    结构层 grader — 规则化，不调 LLM。
    输入：EvalCase + generated_content（str 或 dict）
    输出：GraderOutput（layer=PLANNING，含 S1-S5 维度明细）
    """

    layer = EvalLayer.PLANNING

    def grade(
        self,
        case: EvalCase,
        generated_content: str,
        trace: Optional[EvalTrace] = None,
    ) -> GraderOutput:
        """
        Parameters
        ----------
        case : EvalCase
            评测用例（含 output_requirements）
        generated_content : str
            攻略正文（HTML 或 Markdown 字符串）
        trace : EvalTrace, optional
            生成 trace（结构检查时较少用，预留）
        """
        text = generated_content or ""
        req = case.output_requirements or {}
        duration_days: int = case.user_input.get("duration_days", 0)

        dimension_scores: list[dict[str, Any]] = []

        # ── S1 总纲页完整性 ──────────────────────────────────────────────────
        s1_score, s1_issues = self._check_overview(text)
        dimension_scores.append({
            "id": "S1", "name": "总纲页完整性",
            "score": s1_score, "max": 20, "issues": s1_issues,
        })

        # ── S2 每日页骨架完整性 ──────────────────────────────────────────────
        s2_score, s2_issues = self._check_day_skeletons(text, duration_days)
        dimension_scores.append({
            "id": "S2", "name": "每日页骨架完整性",
            "score": s2_score, "max": 30, "issues": s2_issues,
        })

        # ── S3 条件页触发正确性 ──────────────────────────────────────────────
        s3_score, s3_issues = self._check_conditional_pages(text, case.user_input)
        dimension_scores.append({
            "id": "S3", "name": "条件页触发正确性",
            "score": s3_score, "max": 20, "issues": s3_issues,
        })

        # ── S4 版本边界清晰度 ────────────────────────────────────────────────
        expected_version = req.get("version", "standard")
        s4_score, s4_issues = self._check_version_boundary(text, expected_version)
        dimension_scores.append({
            "id": "S4", "name": "版本边界清晰度",
            "score": s4_score, "max": 15, "issues": s4_issues,
        })

        # ── S5 静态块覆盖 ────────────────────────────────────────────────────
        must_sections = req.get("must_include_sections", [])
        s5_score, s5_issues = self._check_static_blocks(text, must_sections)
        dimension_scores.append({
            "id": "S5", "name": "静态块覆盖",
            "score": s5_score, "max": 15, "issues": s5_issues,
        })

        total = sum(d["score"] for d in dimension_scores)
        all_issues = [i for d in dimension_scores for i in d["issues"]]

        # keyword 强制检查（must_mention / must_not_mention）
        kw_issues = self._check_keywords(text, req)
        all_issues.extend(kw_issues)
        if kw_issues:
            total = max(0, total - 5 * len(kw_issues))

        pass_threshold = 70
        if total >= pass_threshold:
            severity = Severity.OK
        elif total >= 50:
            severity = Severity.WARNING
        else:
            severity = Severity.ERROR

        return GraderOutput(
            layer=self.layer,
            grader_id="structure_grader_v1",
            score=total,
            max_score=100,
            passed=total >= pass_threshold,
            severity=severity,
            dimension_scores=dimension_scores,
            issues=all_issues,
            metadata={"pass_threshold": pass_threshold},
        )

    # ── 内部检查方法 ─────────────────────────────────────────────────────────

    def _check_overview(self, text: str) -> tuple[int, list[str]]:
        issues = []
        found = sum(1 for kw in OVERVIEW_KEYWORDS if kw in text)
        if found == 4:
            return 20, []
        if found >= 2:
            issues.append(f"总纲页缺少字段：{[kw for kw in OVERVIEW_KEYWORDS if kw not in text]}")
            return 12, issues
        if found >= 1:
            issues.append("总纲页内容极简，有效信息不足")
            return 5, issues
        issues.append("未检测到总纲页（缺少行程概览/亮点/适合/预算关键词）")
        return 0, issues

    def _check_day_skeletons(self, text: str, duration_days: int) -> tuple[int, list[str]]:
        if duration_days == 0:
            return 15, []  # 无法判断时给中间分

        issues = []
        # 统计有时间点的天数
        day_blocks = re.split(r"Day\s*\d+|第\s*\d+\s*[天日]", text, flags=re.IGNORECASE)
        if len(day_blocks) < 2:
            issues.append("无法识别每日分段（缺少 Day1/第1天 等标题）")
            return 10, issues

        content_days = day_blocks[1:]  # 跳过序言
        pass_count = 0
        for i, day_text in enumerate(content_days[:duration_days]):
            patterns_found = sum(
                1 for p in DAY_SKELETON_PATTERNS
                if re.search(p, day_text)
            )
            if patterns_found >= 3:
                pass_count += 1
            elif patterns_found >= 2:
                pass_count += 0.5
            else:
                issues.append(f"Day{i+1} 骨架不完整（仅找到 {patterns_found}/4 个骨架元素）")

        ratio = pass_count / max(duration_days, len(content_days), 1)
        if ratio >= 0.9:
            return 30, issues
        if ratio >= 0.7:
            return 20, issues
        if ratio >= 0.5:
            return 10, issues
        return 0, issues

    def _check_conditional_pages(
        self, text: str, user_input: dict[str, Any]
    ) -> tuple[int, list[str]]:
        issues = []
        should_trigger: list[str] = []

        # 判断应触发哪些条件页
        tags = user_input.get("must_have_tags", []) or []
        if "onsen_ryokan" in tags:
            should_trigger.append("onsen_ryokan")
        if user_input.get("has_children"):
            should_trigger.append("family_with_kids")
        if user_input.get("has_elderly"):
            should_trigger.append("has_elderly")
        if "halal" in (user_input.get("food_restrictions") or []):
            should_trigger.append("halal")
        if user_input.get("has_jr_pass"):
            should_trigger.append("jr_pass")

        if not should_trigger:
            return 20, []  # 无需条件页

        triggered = 0
        for trigger in should_trigger:
            keywords = CONDITIONAL_PAGE_TRIGGERS.get(trigger, [])
            if any(kw in text for kw in keywords):
                triggered += 1
            else:
                issues.append(f"条件页未触发：{trigger}（关键词 {keywords} 均未出现）")

        ratio = triggered / len(should_trigger)
        if ratio >= 1.0:
            return 20, issues
        if ratio >= 0.8:
            return 12, issues
        if ratio >= 0.5:
            return 5, issues
        return 0, issues

    def _check_version_boundary(
        self, text: str, expected_version: str
    ) -> tuple[int, list[str]]:
        if expected_version == "blocked":
            # 边界用例期望被拦截，无版本内容
            return 15, []

        issues = []
        has_standard = any(
            kw in text for kw in VERSION_BOUNDARY_KEYWORDS["standard"]
        )
        has_premium = any(
            kw in text for kw in VERSION_BOUNDARY_KEYWORDS["premium"]
        )

        if expected_version == "premium":
            if has_premium:
                return 15, []
            issues.append("尊享版攻略未明确标注尊享版内容边界")
            if has_standard:
                return 8, issues
            return 0, issues

        # standard
        if has_standard or (not has_premium):
            return 15, []
        issues.append("标准版攻略混入了尊享版内容标记，版本边界不清晰")
        return 8, issues

    def _check_static_blocks(
        self, text: str, must_sections: list[str]
    ) -> tuple[int, list[str]]:
        issues = []
        # 检查通用必要静态块
        found_required = sum(1 for kw in REQUIRED_STATIC_BLOCKS if kw in text)

        # 检查 case 指定的 must_include_sections
        section_map = {
            "pre_departure": "出发前",
            "esim_payment": "eSIM",
            "transport_guide": ["交通", "通票"],
            "transport_passes": "通票",
            "overview": ["行程概览", "总览"],
        }
        missing_sections = []
        for section in must_sections:
            kws = section_map.get(section, section)
            if isinstance(kws, str):
                kws = [kws]
            if not any(kw in text for kw in kws):
                missing_sections.append(section)

        if missing_sections:
            issues.append(f"指定 must_include_sections 未出现：{missing_sections}")

        if found_required == 3 and not missing_sections:
            return 15, issues
        if found_required >= 2 and not missing_sections:
            return 10, issues
        if found_required >= 1 or not missing_sections:
            return 5, issues
        issues.append(f"静态块严重缺失（找到 {found_required}/{len(REQUIRED_STATIC_BLOCKS)} 个必要块）")
        return 0, issues

    def _check_keywords(
        self, text: str, req: dict[str, Any]
    ) -> list[str]:
        issues = []
        for kw in req.get("must_mention_keywords", []):
            if kw not in text:
                issues.append(f"must_mention 关键词未出现：「{kw}」")
        for kw in req.get("must_not_mention_keywords", []):
            if kw in text:
                issues.append(f"must_not_mention 关键词出现了：「{kw}」")
        return issues
