"""
失败归因器 — Failure Analyzer (E8)

对每个失败的 eval case，自动归因到 7 层中的一层（或多层），
并生成标准化的归因标签（对照文档 §9.3 的 8 个固定标签）。

归因逻辑：
  1. 先检查 InputUnderstandingGrader 分数 → I 层问题
  2. 检查 StructureGrader → T 层问题（模板装配）
  3. 检查 fragment_hit 期望 vs 实际 → F 层问题
  4. 检查硬规则 / 软规则 → H / S 层
  5. 检查 user_value_grader → A 层（AI 解释）
  6. 其余 → R 层（渲染交付）

标准化标签（8 个，对照 §9.3）：
  I-BAD_CITY_MAP     输入理解-城市映射错误
  I-BAD_STYLE        输入理解-风格误判
  F-MISS             片段命中-必须命中但未命中
  H-VIOLATION        硬规则-违规
  S-LOW_SCORE        软规则-综合分偏低
  T-MISSING_SECTION  模板装配-缺少必要章节
  A-LOW_VALUE        AI解释-用户价值低
  R-EXPORT_FAIL      渲染/交付-导出失败
"""
from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── 标准化归因标签 ─────────────────────────────────────────────────────────────

LABEL_I_BAD_CITY_MAP    = "I-BAD_CITY_MAP"
LABEL_I_BAD_STYLE       = "I-BAD_STYLE"
LABEL_F_MISS            = "F-MISS"
LABEL_H_VIOLATION       = "H-VIOLATION"
LABEL_S_LOW_SCORE       = "S-LOW_SCORE"
LABEL_T_MISSING_SECTION = "T-MISSING_SECTION"
LABEL_A_LOW_VALUE       = "A-LOW_VALUE"
LABEL_R_EXPORT_FAIL     = "R-EXPORT_FAIL"

ALL_LABELS = [
    LABEL_I_BAD_CITY_MAP, LABEL_I_BAD_STYLE,
    LABEL_F_MISS, LABEL_H_VIOLATION, LABEL_S_LOW_SCORE,
    LABEL_T_MISSING_SECTION, LABEL_A_LOW_VALUE, LABEL_R_EXPORT_FAIL,
]


# ── E18: layer 内部名 → 标准 8 归因标签前缀映射 ────────────────────────────────

LAYER_TO_STANDARD_PREFIX: dict[str, str] = {
    "input_understanding": "I",   # I-BAD_CITY_MAP / I-BAD_STYLE
    "fragment_hit":        "F",   # F-MISS
    "hard_rules":          "H",   # H-VIOLATION
    "soft_rules":          "S",   # S-LOW_SCORE
    "structure":           "T",   # T-MISSING_SECTION
    "template":            "T",
    "user_value":          "A",   # A-LOW_VALUE
    "experience":          "A",
    "delivery":            "R",   # R-EXPORT_FAIL
    "render":              "R",
}

STANDARD_LAYER_NAMES: dict[str, str] = {
    "I": "输入理解层",
    "F": "片段命中层",
    "H": "硬规则层",
    "S": "软规则层",
    "T": "模板装配层",
    "A": "AI价值层",
    "R": "渲染交付层",
}


# ── 归因结果结构 ──────────────────────────────────────────────────────────────

class Attribution:
    """单个 case 的归因结果"""

    def __init__(self, case_id: str):
        self.case_id = case_id
        self.labels: list[str] = []
        self.primary_layer: str = ""   # 内部层名
        self.details: list[dict[str, Any]] = []
        self.confidence: float = 0.0   # 0-1

    def add(self, label: str, layer: str, reason: str, conf: float = 0.8) -> None:
        if label not in self.labels:
            self.labels.append(label)
        self.details.append({"label": label, "layer": layer, "reason": reason})
        if conf > self.confidence:
            self.confidence = conf
            self.primary_layer = layer

    @property
    def primary_label_prefix(self) -> str:
        """E18: 将 primary_layer 映射到标准 8 归因标签的前缀（I/F/H/S/T/A/R）"""
        return LAYER_TO_STANDARD_PREFIX.get(self.primary_layer, "R")

    @property
    def primary_label_name(self) -> str:
        """标准层名（中文）"""
        return STANDARD_LAYER_NAMES.get(self.primary_label_prefix, "未知层")

    def to_dict(self) -> dict[str, Any]:
        prefix = self.primary_label_prefix
        return {
            "case_id": self.case_id,
            "labels": self.labels,
            "primary_layer": self.primary_layer,
            # E18: 标准化层标识
            "primary_label_prefix": prefix,
            "primary_label_name": self.primary_label_name,
            "confidence": round(self.confidence, 2),
            "details": self.details,
        }


# ── 主归因器 ──────────────────────────────────────────────────────────────────

class FailureAnalyzer:
    """
    接收 EvalResult（来自 engine.py）或原始 grader 输出字典，
    输出标准化归因标签 + 主归因层。

    Usage:
        analyzer = FailureAnalyzer()
        attribution = analyzer.analyze(case_id="C011", grader_outputs={...})
        print(attribution.to_dict())
    """

    # 各层 pass threshold
    INPUT_PASS  = 80
    STRUCT_PASS = 70
    VALUE_PASS  = 60

    def analyze(
        self,
        case_id: str,
        grader_outputs: dict[str, Any],
        fragment_hit_result: Optional[dict] = None,
        trace_summary: Optional[dict] = None,
    ) -> Attribution:
        """
        Parameters
        ----------
        case_id : str
        grader_outputs : dict
            {
              "input":     GraderOutput.dict(),
              "structure": GraderOutput.dict(),
              "user_value": GraderOutput.dict(),
              "planning":  GraderOutput.dict(),   # optional
            }
        fragment_hit_result : dict, optional
            {
              "must_hit": [...],
              "actually_hit": [...],
              "missed": [...],
            }
        trace_summary : dict, optional
            来自 generation_runs 表的汇总（rule_fail_count 等）
        """
        attr = Attribution(case_id)

        input_out  = grader_outputs.get("input", {})
        struct_out = grader_outputs.get("structure", {})
        value_out  = grader_outputs.get("user_value", {})
        plan_out   = grader_outputs.get("planning", {})

        # ── I 层：输入理解 ─────────────────────────────────────────────────────
        if input_out:
            input_score = input_out.get("score", 100)
            dims = {d["id"]: d for d in input_out.get("dimension_scores", [])}

            if input_score < self.INPUT_PASS:
                i1 = dims.get("I1", {})
                if i1.get("score", 25) < 15:
                    attr.add(
                        LABEL_I_BAD_CITY_MAP, "input_understanding",
                        f"城市映射得分 {i1.get('score', 0)}/25，低于阈值",
                        conf=0.9,
                    )
                i2 = dims.get("I2", {})
                if i2.get("score", 20) < 12:
                    attr.add(
                        LABEL_I_BAD_STYLE, "input_understanding",
                        f"行程风格判断得分 {i2.get('score', 0)}/20，可能误判",
                        conf=0.85,
                    )

        # ── F 层：片段命中 ─────────────────────────────────────────────────────
        if fragment_hit_result:
            missed = fragment_hit_result.get("missed", [])
            if missed:
                attr.add(
                    LABEL_F_MISS, "fragment_hit",
                    f"必须命中的片段未命中：{missed[:3]}",
                    conf=0.88,
                )

        # ── H 层：硬规则（通过 trace 判断）────────────────────────────────────
        if trace_summary:
            rule_fail = trace_summary.get("rule_fail_count", 0)
            if rule_fail > 0:
                attr.add(
                    LABEL_H_VIOLATION, "hard_rule",
                    f"硬规则违规 {rule_fail} 条",
                    conf=0.95,
                )

        # ── S 层：软规则 ───────────────────────────────────────────────────────
        if plan_out:
            plan_score = plan_out.get("score", 100)
            if plan_score < 65:
                attr.add(
                    LABEL_S_LOW_SCORE, "soft_rule",
                    f"规划层综合分 {plan_score}/100，软规则整体偏低",
                    conf=0.82,
                )

        # ── T 层：模板装配 ─────────────────────────────────────────────────────
        if struct_out:
            struct_score = struct_out.get("score", 100)
            dims = {d["id"]: d for d in struct_out.get("dimension_scores", [])}
            if struct_score < self.STRUCT_PASS:
                s1 = dims.get("S1", {})
                s2 = dims.get("S2", {})
                if s1.get("score", 20) < 12 or s2.get("score", 30) < 18:
                    attr.add(
                        LABEL_T_MISSING_SECTION, "template_assembly",
                        f"总纲({s1.get('score', 0)}/20) 或骨架({s2.get('score', 0)}/30) 分低，"
                        "可能缺少必要章节",
                        conf=0.87,
                    )

        # ── A 层：AI 解释/用户价值 ─────────────────────────────────────────────
        if value_out:
            value_score = value_out.get("score", 100)
            if value_score < self.VALUE_PASS:
                attr.add(
                    LABEL_A_LOW_VALUE, "ai_explanation",
                    f"用户价值层得分 {value_score}/100，内容个性化或可读性不足",
                    conf=0.80,
                )

        # ── R 层：无任何命中时降级到渲染层 ────────────────────────────────────
        if not attr.labels:
            attr.add(
                LABEL_R_EXPORT_FAIL, "render_delivery",
                "未发现明确的上层归因，可能为渲染/交付问题或未知错误",
                conf=0.40,
            )

        return attr

    def analyze_batch(
        self,
        results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        批量分析评测结果列表（来自 engine run output）。
        只分析 passed=False 的 case。

        返回：归因报告列表，包含 label 频次统计。
        """
        attributions = []
        label_counts: dict[str, int] = {lbl: 0 for lbl in ALL_LABELS}

        for r in results:
            if r.get("passed"):
                continue
            case_id = r.get("case_id", "unknown")
            grader_outputs = r.get("grader_outputs", {})
            frag = r.get("fragment_hit_result")
            trace = r.get("trace_summary")

            attr = self.analyze(case_id, grader_outputs, frag, trace)
            for lbl in attr.labels:
                label_counts[lbl] = label_counts.get(lbl, 0) + 1
            attributions.append(attr.to_dict())

        return {
            "attributions": attributions,
            "label_frequency": {
                k: v for k, v in sorted(
                    label_counts.items(), key=lambda x: -x[1]
                ) if v > 0
            },
            "total_failed": len(attributions),
        }
