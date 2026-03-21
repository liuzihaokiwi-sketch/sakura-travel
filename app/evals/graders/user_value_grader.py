"""
User Value Grader — 体验层 grader (E3)

LLM-as-judge 方式，按 rubric 评测用户感知价值。

评分维度（对照 docs-human/test.md §1 第四层）：
  1. personalization  — 是否像为这个人写的
  2. flow             — 是否顺（逻辑/交通/节奏）
  3. pitfall_avoidance — 是否少踩坑
  4. worth_paying     — 是否值得付费
  5. memorability     — 是否有记忆点
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from app.evals.engine import EvalCase, EvalLayer, EvalTrace, GraderOutput, Severity

logger = logging.getLogger(__name__)

# ── Rubric 默认权重 ──────────────────────────────────────────────────────────

DEFAULT_RUBRIC = {
    "personalization": {
        "weight": 0.25,
        "max": 20,
        "criteria": "攻略是否体现了用户的具体偏好（同行人类型、预算偏向、兴趣标签、节奏）",
    },
    "flow": {
        "weight": 0.25,
        "max": 20,
        "criteria": "路线是否顺畅、交通衔接是否合理、每天节奏是否适配",
    },
    "pitfall_avoidance": {
        "weight": 0.20,
        "max": 20,
        "criteria": "是否主动避开常见坑（定休日、高峰拥堵、季节不适、骗局等）",
    },
    "worth_paying": {
        "weight": 0.15,
        "max": 20,
        "criteria": "内容是否超出用户自己搜索能获得的信息，是否有专业价值感",
    },
    "memorability": {
        "weight": 0.15,
        "max": 20,
        "criteria": "是否有 1-2 个让用户'眼前一亮'的亮点推荐（隐藏好店、绝佳时机、独特体验）",
    },
}


# ── Prompt 构建 ───────────────────────────────────────────────────────────────

def _build_judge_prompt(case: EvalCase, output: Any, rubric: dict) -> str:
    """构建 LLM 评审 prompt"""

    user_profile = json.dumps(case.user_input, ensure_ascii=False, indent=2)
    output_text = output if isinstance(output, str) else json.dumps(output, ensure_ascii=False, indent=2)

    rubric_text = ""
    for dim, spec in rubric.items():
        rubric_text += f"\n### {dim}（满分 {spec['max']} 分，权重 {spec['weight']:.0%}）\n"
        rubric_text += f"评判标准：{spec['criteria']}\n"

    return f"""你是一位资深旅行攻略评审专家。请根据以下评分维度，对生成的攻略进行打分。

## 用户画像
```json
{user_profile}
```

## 生成的攻略内容
```
{output_text[:3000]}
```

## 评分维度
{rubric_text}

## 输出要求
请用以下 JSON 格式输出评分结果，每个维度给 0-{list(rubric.values())[0]['max']} 的整数分，并给出一句话理由：

```json
{{
  "scores": {{
    "personalization": {{"score": 0, "reason": "..."}},
    "flow": {{"score": 0, "reason": "..."}},
    "pitfall_avoidance": {{"score": 0, "reason": "..."}},
    "worth_paying": {{"score": 0, "reason": "..."}},
    "memorability": {{"score": 0, "reason": "..."}}
  }},
  "overall_comment": "一句话总评",
  "top_highlight": "最大亮点",
  "biggest_issue": "最大问题"
}}
```

只输出 JSON，不要其他内容。"""


def _parse_judge_response(response_text: str, rubric: dict) -> tuple[dict, str]:
    """解析 LLM 返回的 JSON"""
    # 尝试提取 JSON
    text = response_text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Failed to parse judge response as JSON")
        return {dim: 0 for dim in rubric}, "parse_error"

    scores = {}
    for dim in rubric:
        dim_data = data.get("scores", {}).get(dim, {})
        if isinstance(dim_data, dict):
            scores[dim] = dim_data.get("score", 0)
        elif isinstance(dim_data, (int, float)):
            scores[dim] = dim_data
        else:
            scores[dim] = 0

    comment = data.get("overall_comment", "")
    return scores, comment


# ── Grader 实现 ───────────────────────────────────────────────────────────────

class UserValueGrader:
    """体验层 LLM-as-judge grader"""

    def __init__(self, llm_fn=None, rubric: Optional[dict] = None):
        """
        Args:
            llm_fn: async fn(prompt: str) -> str — LLM 调用函数
                    如果不提供，使用规则化 fallback
            rubric: 自定义评分维度，默认用 DEFAULT_RUBRIC
        """
        self._llm_fn = llm_fn
        self._rubric = rubric or DEFAULT_RUBRIC

    @property
    def name(self) -> str:
        return "user_value_grader"

    @property
    def layer(self) -> EvalLayer:
        return EvalLayer.EXPERIENCE

    async def grade(
        self, case: EvalCase, trace: EvalTrace, output: Any
    ) -> GraderOutput:
        """执行评分"""
        details: list[dict] = []
        rubric = {**self._rubric, **case.grader_rubric} if case.grader_rubric else self._rubric

        if self._llm_fn and output:
            # LLM-as-judge 路径
            scores, comment = await self._grade_with_llm(case, output, rubric)
        else:
            # 规则化 fallback 路径
            scores, comment = self._grade_with_rules(case, trace, rubric)

        # 计算加权总分
        total = 0.0
        max_total = 0.0
        for dim, spec in rubric.items():
            dim_score = scores.get(dim, 0)
            dim_max = spec["max"]
            weight = spec["weight"]
            weighted = dim_score * weight
            total += weighted
            max_total += dim_max * weight

            passed = dim_score >= dim_max * 0.6
            details.append({
                "dimension": dim,
                "score": dim_score,
                "max": dim_max,
                "weight": weight,
                "weighted_score": round(weighted, 1),
                "passed": passed,
                "criteria": spec["criteria"],
            })

        # 归一化到 0-100
        normalized = (total / max_total * 100) if max_total > 0 else 0

        # 严重度
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
            notes=comment,
        )

    async def _grade_with_llm(
        self, case: EvalCase, output: Any, rubric: dict
    ) -> tuple[dict, str]:
        """使用 LLM 评分"""
        prompt = _build_judge_prompt(case, output, rubric)
        try:
            response = await self._llm_fn(prompt)
            return _parse_judge_response(response, rubric)
        except Exception as e:
            logger.exception("LLM judge failed: %s", e)
            return {dim: 0 for dim in rubric}, f"llm_error: {e}"

    def _grade_with_rules(
        self, case: EvalCase, trace: EvalTrace, rubric: dict
    ) -> tuple[dict, str]:
        """规则化 fallback — 无 LLM 时基于 trace 数据估算"""
        scores: dict[str, int] = {}

        for dim, spec in rubric.items():
            max_score = spec["max"]

            if dim == "personalization":
                # 检查 trace 中是否有用户画像匹配信息
                if trace.normalized_profile:
                    scores[dim] = int(max_score * 0.6)
                else:
                    scores[dim] = int(max_score * 0.3)

            elif dim == "flow":
                # 检查片段命中和路线装配
                hit_count = len(trace.fragments_hit)
                if hit_count >= 3:
                    scores[dim] = int(max_score * 0.7)
                elif hit_count >= 1:
                    scores[dim] = int(max_score * 0.5)
                else:
                    scores[dim] = int(max_score * 0.3)

            elif dim == "pitfall_avoidance":
                # 检查硬规则是否触发
                rules_fired = len(trace.hard_rules_fired)
                if rules_fired >= 2:
                    scores[dim] = int(max_score * 0.7)
                elif rules_fired >= 1:
                    scores[dim] = int(max_score * 0.5)
                else:
                    scores[dim] = int(max_score * 0.4)

            elif dim == "worth_paying":
                # 基于片段复用率估算
                total = len(trace.fragments_hit) + len(trace.fragments_rejected)
                if total > 0:
                    hit_rate = len(trace.fragments_hit) / total
                    scores[dim] = int(max_score * min(hit_rate + 0.3, 1.0))
                else:
                    scores[dim] = int(max_score * 0.4)

            elif dim == "memorability":
                # 如果有高质量片段，可能有记忆点
                if any(f.get("quality_score", 0) >= 8 for f in trace.fragments_hit):
                    scores[dim] = int(max_score * 0.7)
                else:
                    scores[dim] = int(max_score * 0.4)

            else:
                scores[dim] = int(max_score * 0.5)

        return scores, "rule_based_fallback"
