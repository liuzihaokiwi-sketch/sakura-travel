"""
Evaluation Framework Core Engine (E1)

评测飞轮核心引擎 — 对照 docs-human/test.md

流程：读取 case YAML → 调用生成管线 → 收集 trace → 调用 grader → 输出结果 JSON
含 4 层评测钩子：输入理解 / 规划 / 交付 / 体验
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional, Protocol

import yaml

logger = logging.getLogger(__name__)

# ── 评测层定义 ────────────────────────────────────────────────────────────────

class EvalLayer(str, Enum):
    INPUT = "input"           # 输入理解层
    PLANNING = "planning"     # 规划层
    DELIVERY = "delivery"     # 交付层
    EXPERIENCE = "experience" # 体验层


class Severity(str, Enum):
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"
    ERROR = "error"


# ── 数据结构 ──────────────────────────────────────────────────────────────────

@dataclass
class EvalCase:
    """一个评测用例（对应 YAML 文件）"""
    case_id: str
    suite: str                          # standard / high_value / constrained / edge / regression
    title: str
    user_input: dict                    # 模拟的用户表单输入
    normalized_profile_expected: dict   # 期望的标准化画像
    hard_constraints_expected: list[str] # 期望触发的硬约束
    fragment_hit_expectation: dict      # 期望命中/不命中的片段
    output_requirements: list[str]      # 输出必须满足的条件
    grader_rubric: dict                 # 评分维度 + 权重
    known_risks: list[str]             # 已知风险
    tags: list[str] = field(default_factory=list)


@dataclass
class GraderOutput:
    """单个 grader 的输出"""
    grader_name: str
    layer: EvalLayer
    score: float                        # 0-100
    max_score: float = 100.0
    severity: Severity = Severity.PASS
    details: list[dict] = field(default_factory=list)  # 每个检查项
    notes: str = ""


@dataclass
class EvalTrace:
    """生成过程的 trace（供 grader 使用）"""
    normalized_profile: Optional[dict] = None
    fragments_hit: list[dict] = field(default_factory=list)
    fragments_rejected: list[dict] = field(default_factory=list)
    hard_rules_fired: list[dict] = field(default_factory=list)
    soft_rules_applied: list[dict] = field(default_factory=list)
    assembly_result: Optional[dict] = None
    output_structure: Optional[dict] = None
    raw_output: Optional[str] = None
    timings: dict = field(default_factory=dict)


@dataclass
class EvalResult:
    """单个 case 的评测结果"""
    case_id: str
    run_id: str
    timestamp: str
    layer_scores: dict[str, float]      # layer -> score
    overall_score: float
    severity: Severity
    grader_outputs: list[GraderOutput]
    failure_attribution: Optional[str] = None  # 归因到哪一层
    duration_ms: int = 0


@dataclass
class EvalRunSummary:
    """一次评测运行的汇总"""
    run_id: str
    suite: str
    started_at: str
    finished_at: str
    total_cases: int
    passed: int
    warned: int
    failed: int
    errored: int
    avg_score: float
    layer_avg_scores: dict[str, float]
    results: list[EvalResult]


# ── Grader Protocol ───────────────────────────────────────────────────────────

class Grader(Protocol):
    """Grader 接口 — 所有 grader 必须实现"""

    @property
    def name(self) -> str: ...

    @property
    def layer(self) -> EvalLayer: ...

    async def grade(
        self, case: EvalCase, trace: EvalTrace, output: Any
    ) -> GraderOutput: ...


# ── Case Loader ───────────────────────────────────────────────────────────────

CASES_DIR = Path("evals/cases")


def load_case(path: Path) -> EvalCase:
    """从 YAML 文件加载单个用例"""
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # E15: 兼容旧字段名 case_type（YAML 里写 case_type，engine 字段叫 suite）
    suite_val = data.get("suite") or data.get("case_type") or path.parent.name

    return EvalCase(
        case_id=data["case_id"],
        suite=suite_val,
        title=data.get("title", data["case_id"]),
        user_input=data["user_input"],
        normalized_profile_expected=data.get("normalized_profile_expected", {}),
        hard_constraints_expected=data.get("hard_constraints_expected", []),
        fragment_hit_expectation=data.get("fragment_hit_expectation", {}),
        output_requirements=data.get("output_requirements", []),
        grader_rubric=data.get("grader_rubric", {}),
        known_risks=data.get("known_risks", []),
        tags=data.get("tags", []),
    )


def load_suite(suite_name: str) -> list[EvalCase]:
    """加载整个 suite 的用例"""
    suite_dir = CASES_DIR / suite_name
    if not suite_dir.exists():
        logger.warning("suite %s not found at %s", suite_name, suite_dir)
        return []
    cases = []
    for f in sorted(suite_dir.glob("*.yaml")):
        try:
            cases.append(load_case(f))
        except Exception as e:
            logger.error("Failed to load case %s: %s", f, e)
    logger.info("Loaded %d cases from suite '%s'", len(cases), suite_name)
    return cases


def load_all_cases() -> list[EvalCase]:
    """加载所有 suite 的用例"""
    all_cases = []
    if not CASES_DIR.exists():
        return all_cases
    for suite_dir in sorted(CASES_DIR.iterdir()):
        if suite_dir.is_dir():
            all_cases.extend(load_suite(suite_dir.name))
    return all_cases


# ── Rubric Loader ─────────────────────────────────────────────────────────────

RUBRICS_DIR = Path("evals/rubrics")


def load_rubric(name: str) -> dict:
    """加载 rubric YAML"""
    path = RUBRICS_DIR / f"{name}.yaml"
    if not path.exists():
        logger.warning("rubric %s not found", name)
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ── Engine ────────────────────────────────────────────────────────────────────

class EvalEngine:
    """评测引擎 — 注册 grader、执行评测、汇总结果"""

    def __init__(self) -> None:
        self._graders: list[Grader] = []
        self._generate_fn: Optional[Callable] = None

    def register_grader(self, grader: Grader) -> None:
        self._graders.append(grader)
        logger.info("Registered grader: %s (layer=%s)", grader.name, grader.layer)

    def set_generate_fn(self, fn: Callable) -> None:
        """设置生成函数 — async fn(user_input: dict) -> (output, trace)"""
        self._generate_fn = fn

    async def run_case(self, case: EvalCase) -> EvalResult:
        """执行单个用例"""
        run_id = str(uuid.uuid4())[:8]
        start = time.time()
        trace = EvalTrace()
        output = None

        # Step 1: 调用生成管线
        if self._generate_fn:
            try:
                output, trace = await self._generate_fn(case.user_input)
            except Exception as e:
                logger.exception("Generate failed for case %s: %s", case.case_id, e)
                return EvalResult(
                    case_id=case.case_id,
                    run_id=run_id,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    layer_scores={},
                    overall_score=0.0,
                    severity=Severity.ERROR,
                    grader_outputs=[],
                    failure_attribution="generation_error",
                    duration_ms=int((time.time() - start) * 1000),
                )

        # Step 2: 执行所有 grader
        grader_outputs: list[GraderOutput] = []
        for grader in self._graders:
            try:
                result = await grader.grade(case, trace, output)
                grader_outputs.append(result)
            except Exception as e:
                logger.exception("Grader %s failed for case %s", grader.name, case.case_id)
                grader_outputs.append(GraderOutput(
                    grader_name=grader.name,
                    layer=grader.layer,
                    score=0.0,
                    severity=Severity.ERROR,
                    notes=str(e),
                ))

        # Step 3: 汇总分数
        layer_scores: dict[str, list[float]] = {}
        for go in grader_outputs:
            layer_scores.setdefault(go.layer.value, []).append(go.score / go.max_score * 100)

        layer_avg = {k: sum(v) / len(v) for k, v in layer_scores.items() if v}
        overall = sum(layer_avg.values()) / max(len(layer_avg), 1)

        # Severity
        worst = Severity.PASS
        for go in grader_outputs:
            if go.severity == Severity.ERROR:
                worst = Severity.ERROR
                break
            if go.severity == Severity.FAIL and worst != Severity.ERROR:
                worst = Severity.FAIL
            if go.severity == Severity.WARNING and worst == Severity.PASS:
                worst = Severity.WARNING

        # Failure attribution
        attribution = None
        if worst in (Severity.FAIL, Severity.ERROR):
            # 找到分最低的层
            if layer_avg:
                attribution = min(layer_avg, key=layer_avg.get)

        duration_ms = int((time.time() - start) * 1000)

        return EvalResult(
            case_id=case.case_id,
            run_id=run_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            layer_scores=layer_avg,
            overall_score=round(overall, 1),
            severity=worst,
            grader_outputs=grader_outputs,
            failure_attribution=attribution,
            duration_ms=duration_ms,
        )

    async def run_suite(self, suite_name: str) -> EvalRunSummary:
        """执行整个 suite"""
        cases = load_suite(suite_name)
        return await self._run_cases(cases, suite_name)

    async def run_all(self) -> EvalRunSummary:
        """执行所有用例"""
        cases = load_all_cases()
        return await self._run_cases(cases, "all")

    async def _run_cases(self, cases: list[EvalCase], suite: str) -> EvalRunSummary:
        run_id = str(uuid.uuid4())[:8]
        started = datetime.now(timezone.utc).isoformat()
        results: list[EvalResult] = []

        for case in cases:
            logger.info("Running eval case: %s", case.case_id)
            result = await self.run_case(case)
            results.append(result)

        finished = datetime.now(timezone.utc).isoformat()

        passed = sum(1 for r in results if r.severity == Severity.PASS)
        warned = sum(1 for r in results if r.severity == Severity.WARNING)
        failed = sum(1 for r in results if r.severity == Severity.FAIL)
        errored = sum(1 for r in results if r.severity == Severity.ERROR)
        avg_score = sum(r.overall_score for r in results) / max(len(results), 1)

        # Layer averages across all cases
        all_layer_scores: dict[str, list[float]] = {}
        for r in results:
            for layer, score in r.layer_scores.items():
                all_layer_scores.setdefault(layer, []).append(score)
        layer_avg = {k: round(sum(v) / len(v), 1) for k, v in all_layer_scores.items()}

        summary = EvalRunSummary(
            run_id=run_id,
            suite=suite,
            started_at=started,
            finished_at=finished,
            total_cases=len(results),
            passed=passed,
            warned=warned,
            failed=failed,
            errored=errored,
            avg_score=round(avg_score, 1),
            layer_avg_scores=layer_avg,
            results=results,
        )

        # 保存结果到 evals/runs/
        self._save_run(summary)

        logger.info(
            "Eval run %s complete: %d cases, pass=%d warn=%d fail=%d error=%d avg=%.1f",
            run_id, len(results), passed, warned, failed, errored, avg_score,
        )
        return summary

    # ── E16: 版本追踪 ─────────────────────────────────────────────────────────

    def set_versions(self, versions: dict[str, str]) -> None:
        """
        记录本次运行的 8 个版本号（对照文档 §9.1）。
        在 run_suite / run_all 之前调用。

        Parameters
        ----------
        versions : dict
            {
              "engine_version":       "v1.2.0",
              "fragment_lib_version": "v0.3.1",
              "soft_rules_version":   "v2.1.0",
              "hard_rules_version":   "v1.0.5",
              "template_version":     "v0.8.2",
              "prompt_version":       "v1.1.0",
              "grader_version":       "v0.2.0",
              "model_id":             "claude-sonnet-4-5",
            }
        """
        self._versions = versions
        logger.info("Eval version context set: %s", versions)

    def get_versions(self) -> dict[str, str]:
        return getattr(self, "_versions", {})

    # ── E17: 回归门槛检查 ─────────────────────────────────────────────────────

    # 文档 §9.4 定义的发布门槛（0-100 制，统一后）
    RELEASE_THRESHOLDS: dict[str, float] = {
        "input":      70.0,   # 输入理解层 ≥70
        "planning":   65.0,   # 规划层 ≥65
        "delivery":   70.0,   # 交付/结构层 ≥70
        "experience": 60.0,   # 体验/价值层 ≥60
    }

    def check_release_gate(
        self,
        summary: "EvalRunSummary",
        thresholds: Optional[dict[str, float]] = None,
    ) -> dict[str, Any]:
        """
        检查本次评测结果是否通过发布门槛（E17）。

        Parameters
        ----------
        summary : EvalRunSummary
        thresholds : dict, optional
            自定义门槛，不传时使用 RELEASE_THRESHOLDS

        Returns
        -------
        dict:
            {
              "passed": bool,
              "gates": [{"layer": str, "score": float, "threshold": float, "passed": bool}],
              "blocker_layers": [str],
              "recommendation": str,
            }
        """
        gates_config = thresholds or self.RELEASE_THRESHOLDS
        gates = []
        blockers = []

        for layer, threshold in gates_config.items():
            score = summary.layer_avg_scores.get(layer, 0.0)
            passed_gate = score >= threshold
            gates.append({
                "layer": layer,
                "score": score,
                "threshold": threshold,
                "passed": passed_gate,
                "delta": round(score - threshold, 1),
            })
            if not passed_gate:
                blockers.append(layer)

        overall_passed = len(blockers) == 0

        if overall_passed:
            recommendation = "✅ 所有层通过门槛，可以发布"
        elif len(blockers) == 1:
            recommendation = f"⚠️ {blockers[0]} 层未达门槛，建议修复后再发布"
        else:
            recommendation = f"🔴 {len(blockers)} 层未达门槛（{', '.join(blockers)}），不建议发布"

        logger.info(
            "Release gate check: passed=%s blockers=%s avg_score=%.1f",
            overall_passed, blockers, summary.avg_score,
        )

        return {
            "passed": overall_passed,
            "gates": gates,
            "blocker_layers": blockers,
            "recommendation": recommendation,
            "versions": self.get_versions(),
            "suite": summary.suite,
            "run_id": summary.run_id,
            "avg_score": summary.avg_score,
        }

    def _save_run(self, summary: "EvalRunSummary") -> None:
        """保存运行结果到 JSON"""
        runs_dir = Path("evals/runs")
        runs_dir.mkdir(parents=True, exist_ok=True)
        path = runs_dir / f"{summary.run_id}_{summary.suite}.json"

        # Convert dataclasses to dicts for serialization
        data = {
            "run_id": summary.run_id,
            "suite": summary.suite,
            "started_at": summary.started_at,
            "finished_at": summary.finished_at,
            "total_cases": summary.total_cases,
            "passed": summary.passed,
            "warned": summary.warned,
            "failed": summary.failed,
            "errored": summary.errored,
            "avg_score": summary.avg_score,
            "layer_avg_scores": summary.layer_avg_scores,
            "results": [
                {
                    "case_id": r.case_id,
                    "overall_score": r.overall_score,
                    "severity": r.severity.value,
                    "layer_scores": r.layer_scores,
                    "failure_attribution": r.failure_attribution,
                    "duration_ms": r.duration_ms,
                    "grader_count": len(r.grader_outputs),
                }
                for r in summary.results
            ],
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("Saved eval run to %s", path)
