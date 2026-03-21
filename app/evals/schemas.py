"""
app/evals/schemas.py — 评测飞轮 Pydantic 数据模型

对应 E13。覆盖：
  EvalCase           — 评测用例（对应 evals/cases/**/*.yaml）
  EvalRun            — 一次评测运行（可包含多个 case）
  EvalResult         — 单个 case 的运行结果
  GraderOutput       — 单个 grader 的输出
  FailureAttribution — 失败归因
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ── 枚举 ─────────────────────────────────────────────────────────────────────


class CaseType(str, Enum):
    standard = "standard"
    high_value = "high_value"
    constrained = "constrained"
    edge = "edge"
    regression = "regression"


class Verdict(str, Enum):
    pass_ = "pass"
    fail = "fail"
    borderline = "borderline"
    error = "error"       # 生成管线异常
    skipped = "skipped"   # 依赖未满足，跳过


class FailureLayer(str, Enum):
    """失败归因的 7 层"""
    input_understanding = "input_understanding"   # 输入理解/profile normalization
    fragment_hit = "fragment_hit"                 # 片段命中
    hard_rule = "hard_rule"                       # 硬规则
    soft_rule = "soft_rule"                       # 软规则
    template_assembly = "template_assembly"        # 模板装配
    ai_explanation = "ai_explanation"             # AI 解释层
    render_delivery = "render_delivery"           # 渲染/交付


class GraderType(str, Enum):
    structure = "structure"           # E5 结构 grader
    planning = "planning"             # E2 规划 grader
    user_value = "user_value"         # E3 体验 grader（LLM-as-judge）
    input_understanding = "input"     # E6 输入理解 grader


# ── 用例 ─────────────────────────────────────────────────────────────────────


class FragmentHitExpectation(BaseModel):
    must_hit: list[str] = Field(
        default_factory=list,
        description="必须命中的片段城市/类型，如 ['tokyo:route', 'tokyo:logistics']"
    )
    should_hit: list[str] = Field(
        default_factory=list,
        description="期望命中但非必须"
    )
    must_not_hit: list[str] = Field(
        default_factory=list,
        description="明确不应命中的片段"
    )


class HardConstraintExpectation(BaseModel):
    """期望通过的硬规则 ID 列表（及期望触发 == fail 的）"""
    should_pass: list[str] = Field(default_factory=list, description="如 ['no_conflict_venues']")
    should_trigger: list[str] = Field(default_factory=list, description="期望触发的硬规则（如边界用例）")


class NormalizedProfileExpected(BaseModel):
    """期望的 normalized profile 字段值（用于 E6 输入理解 grader）"""
    city_codes: Optional[list[str]] = None
    trip_style: Optional[str] = None
    theme_family: Optional[str] = None
    budget_level: Optional[str] = None
    party_type: Optional[str] = None
    pace_preference: Optional[str] = None
    extra: dict[str, Any] = Field(default_factory=dict)


class OutputRequirement(BaseModel):
    """攻略输出的格式/内容要求"""
    min_days_covered: Optional[int] = None
    must_include_sections: list[str] = Field(
        default_factory=list,
        description="如 ['overview', 'day1', 'transport_pass_guide']"
    )
    must_mention_keywords: list[str] = Field(default_factory=list)
    must_not_mention_keywords: list[str] = Field(default_factory=list)
    version: Optional[str] = Field(None, description="standard / premium")


class EvalCase(BaseModel):
    """评测用例 — 对应 evals/cases/**/*.yaml 的反序列化结构"""
    case_id: str = Field(..., description="如 C001, H001, R001")
    case_type: CaseType
    title: str
    description: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    known_risks: list[str] = Field(default_factory=list, description="已知此 case 容易出错的点")

    # 输入
    user_input: dict[str, Any] = Field(
        ...,
        description="模拟 detail_forms 提交的完整用户输入 JSON"
    )

    # 期望
    normalized_profile_expected: Optional[NormalizedProfileExpected] = None
    hard_constraints_expected: Optional[HardConstraintExpectation] = None
    fragment_hit_expectation: Optional[FragmentHitExpectation] = None
    output_requirements: Optional[OutputRequirement] = None

    # grader 配置（可覆盖全局 rubric）
    grader_overrides: dict[str, Any] = Field(
        default_factory=dict,
        description="可覆盖某个 rubric 的特定维度权重或通过阈值"
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = "system"


# ── 运行 ─────────────────────────────────────────────────────────────────────


class EvalRun(BaseModel):
    """一次评测运行"""
    run_id: UUID = Field(default_factory=uuid4)
    run_name: str = Field(..., description="如 'regression-2026-03-22' 或 'fragment-engine-v2'")
    suite: Optional[str] = Field(None, description="如 'regression', 'standard', 'all'")
    case_ids: list[str] = Field(default_factory=list, description="本次运行的 case ID 列表")

    # 运行配置
    generation_config: dict[str, Any] = Field(
        default_factory=dict,
        description="覆盖生成管线参数（如 fragment_engine_version, llm_model）"
    )
    compare_with_run_id: Optional[UUID] = Field(None, description="对比的基线 run ID")

    # 状态
    status: str = "pending"  # pending / running / done / error
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    # 汇总
    total_cases: int = 0
    passed: int = 0
    failed: int = 0
    borderline: int = 0
    errored: int = 0
    avg_structure_score: Optional[float] = None
    avg_planning_score: Optional[float] = None
    avg_user_value_score: Optional[float] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)


# ── 结果 ─────────────────────────────────────────────────────────────────────


class GraderOutput(BaseModel):
    """单个 grader 的输出"""
    grader_type: GraderType
    score: float = Field(..., ge=0, le=100)
    max_score: float = 100
    verdict: Verdict
    dimension_scores: list[dict[str, Any]] = Field(
        default_factory=list,
        description="每个评分维度的得分明细"
    )
    key_issues: list[str] = Field(default_factory=list)
    highlight: Optional[str] = None
    raw_output: Optional[dict[str, Any]] = Field(None, description="LLM judge 的原始返回")
    graded_at: datetime = Field(default_factory=datetime.utcnow)
    grader_version: str = "1.0"


class EvalResult(BaseModel):
    """单个 case 的运行结果"""
    result_id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    case_id: str
    case_type: CaseType

    # 生成产物
    generated_trip_id: Optional[UUID] = None
    generation_trace_id: Optional[UUID] = Field(
        None,
        description="对应 generation_run.run_id，E9 接入后自动填充"
    )
    generation_duration_ms: Optional[int] = None

    # grader 输出
    grader_outputs: list[GraderOutput] = Field(default_factory=list)
    overall_verdict: Verdict = Verdict.skipped

    # 综合分
    composite_score: Optional[float] = Field(
        None,
        description="加权综合分：structure×0.3 + planning×0.4 + user_value×0.3"
    )

    # 错误
    error_message: Optional[str] = None
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)

    def compute_composite_score(self) -> float:
        """计算加权综合分"""
        weights = {
            GraderType.structure: 0.3,
            GraderType.planning: 0.4,
            GraderType.user_value: 0.3,
        }
        total_weight = 0.0
        weighted_sum = 0.0
        for output in self.grader_outputs:
            w = weights.get(output.grader_type, 0.0)
            if w > 0:
                weighted_sum += output.score * w
                total_weight += w
        if total_weight == 0:
            return 0.0
        return round(weighted_sum / total_weight, 2)


class FailureAttribution(BaseModel):
    """失败归因 — E8 失败归因器的输出"""
    attribution_id: UUID = Field(default_factory=uuid4)
    result_id: UUID
    run_id: UUID
    case_id: str

    # 归因结果
    primary_layer: FailureLayer = Field(..., description="主要失败层")
    secondary_layers: list[FailureLayer] = Field(default_factory=list)
    confidence: float = Field(..., ge=0, le=1, description="归因置信度")

    # 证据
    evidence: list[str] = Field(
        default_factory=list,
        description="支持归因的具体证据（如 '片段命中率仅 40%，低于阈值 80%'）"
    )
    suggested_fix: Optional[str] = Field(
        None,
        description="建议的修复方向（如 '检查 fragment_hit 阈值配置' 或 '增加该城市的片段种子数据'）"
    )

    attributed_at: datetime = Field(default_factory=datetime.utcnow)
    attributed_by: str = "e8_auto"  # e8_auto / human


# ── 便捷函数 ─────────────────────────────────────────────────────────────────

def load_case_from_yaml(yaml_path: str) -> EvalCase:
    """从 YAML 文件加载评测用例"""
    import yaml
    from pathlib import Path
    data = yaml.safe_load(Path(yaml_path).read_text(encoding="utf-8"))
    return EvalCase(**data)


def load_rubric(rubric_id: str) -> dict[str, Any]:
    """从 evals/rubrics/ 加载 rubric YAML"""
    import yaml
    from pathlib import Path
    rubric_path = Path(f"evals/rubrics/{rubric_id}.yaml")
    if not rubric_path.exists():
        raise FileNotFoundError(f"Rubric not found: {rubric_path}")
    return yaml.safe_load(rubric_path.read_text(encoding="utf-8"))
