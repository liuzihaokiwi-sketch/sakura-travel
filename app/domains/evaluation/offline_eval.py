"""
离线评测框架（Offline Evaluation）

用于验证行程生成质量，包含：
1. 评测用例集（从 JSON 加载）
2. 6 维自动评分器
3. 回归检测（新版本 vs 旧版本对比）

评分维度：
  - completeness: 行程完整度（是否覆盖必要元素）
  - feasibility: 可行性（时间/交通/营业时间是否合理）
  - diversity: 多样性（类型/区域/体验是否丰富）
  - preference_match: 偏好匹配度（与用户画像的契合）
  - quality: 内容质量（推荐理由/文案质量）
  - safety: 安全性（无 hard_fail 问题）
"""
from __future__ import annotations

import json
import logging
from datetime import date
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from app.domains.intake.layer2_contract import build_layer2_canonical_input, unpack_canonical_values

logger = logging.getLogger(__name__)

EVAL_CASES_DIR = Path(__file__).resolve().parents[3] / "data" / "eval"
EXPECTED_CITY_CIRCLES = {
    "kansai_classic_circle",
    "kanto_city_circle",
    "hokkaido_city_circle",
    "south_china_five_city_circle",
    "northern_xinjiang_city_circle",
    "guangdong_city_circle",
}


# ── 数据结构 ───────────────────────────────────────────────────────────────────

@dataclass
class EvalScore:
    completeness: float = 0.0        # 0-10（现有）
    feasibility: float = 0.0         # 0-10（现有）
    diversity: float = 0.0           # 0-10（现有）
    preference_match: float = 0.0    # 0-10（现有）
    quality: float = 0.0             # 0-10（现有）
    safety: float = 0.0              # 0-10（现有）
    factual_reliability: float = 0.0 # 0-10（L4-05 新增）
    pacing_quality: float = 0.0      # 0-10（L4-05 新增）

    @property
    def overall(self) -> float:
        # 权重总和 = 0.15+0.20+0.10+0.15+0.10+0.10+0.10+0.10 = 1.00
        weights = [0.15, 0.20, 0.10, 0.15, 0.10, 0.10, 0.10, 0.10]
        dims = [self.completeness, self.feasibility, self.diversity,
                self.preference_match, self.quality, self.safety,
                self.factual_reliability, self.pacing_quality]
        return round(sum(w * d for w, d in zip(weights, dims)), 2)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["overall"] = self.overall
        return d


@dataclass
class EvalCase:
    case_id: str
    description: str
    user_profile: dict[str, Any]
    expected_constraints: dict[str, Any]  # 必须满足的约束
    input_contract: dict[str, Any] | None = None
    matrix_city_circle: str | None = None
    matrix_scenario_types: list[str] = field(default_factory=list)
    matrix_contract_semantics: list[str] = field(default_factory=list)
    matrix_assertion_level: str = "smoke"
    plan_json: dict[str, Any] | None = None  # 待评测的行程
    score: EvalScore | None = None
    issues: list[str] = field(default_factory=list)


@dataclass
class EvalReport:
    version: str
    total_cases: int
    passed: int
    failed: int
    avg_score: float
    dimension_avgs: dict[str, float]
    regressions: list[dict[str, Any]]
    cases: list[dict[str, Any]]
    matrix_summary: dict[str, Any] = field(default_factory=dict)


# ── 评测用例加载 ──────────────────────────────────────────────────────────────

def load_eval_cases(cases_file: str = "eval_cases_v1.json") -> list[EvalCase]:
    fp = EVAL_CASES_DIR / cases_file
    if not fp.exists():
        logger.warning("Eval cases file not found: %s, using built-in cases", fp)
        return _builtin_cases()
    with open(fp, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return [
        EvalCase(
            case_id=c["case_id"],
            description=c["description"],
            user_profile=c["user_profile"],
            expected_constraints=c.get("expected_constraints", {}),
        )
        for c in raw
    ]


def build_eval_case_from_contract(
    *,
    case_id: str,
    description: str,
    contract: dict[str, Any],
    expected_constraints: dict[str, Any] | None = None,
    matrix: dict[str, Any] | None = None,
) -> EvalCase:
    """Build a contract-first eval case from v2 contract payload."""
    trip_window = contract.get("trip_window") or {}
    start_date = str(trip_window.get("start_date") or "").strip()
    end_date = str(trip_window.get("end_date") or "").strip()
    duration_days = int(contract.get("duration_days") or 0)
    if duration_days <= 0 and start_date and end_date:
        try:
            duration_days = (date.fromisoformat(end_date) - date.fromisoformat(start_date)).days + 1
        except ValueError:
            duration_days = 0
    if duration_days <= 0:
        duration_days = max(1, len(list((contract.get("city_circle_intent") or {}).get("destination_intent") or [])))

    raw_for_canonical = {
        **contract,
        "requested_city_circle": (contract.get("city_circle_intent") or {}).get("circle_id"),
        "travel_start_date": start_date,
        "travel_end_date": end_date,
        "arrival_date": start_date,
        "arrival_time": ((trip_window.get("arrival") or {}).get("time")),
        "departure_date": end_date,
        "departure_time": ((trip_window.get("departure") or {}).get("time")),
    }
    canonical = unpack_canonical_values(build_layer2_canonical_input(raw_for_canonical))
    canonical["contract_version"] = str(contract.get("contract_version") or "v2")

    matrix_data = matrix or {}
    circle_id = str(canonical.get("requested_city_circle") or "")

    constraints = dict(expected_constraints or {})
    constraints.setdefault("min_days", duration_days)
    constraints.setdefault("max_poi_per_day", 6)
    constraints.setdefault("must_include_types", ["poi", "restaurant"])

    profile = {
        "segment": str(contract.get("party_type") or "unknown"),
        "days": duration_days,
        "pace": str(contract.get("pace") or "moderate"),
        "city_circle": circle_id,
        "budget": str(contract.get("budget_level") or "mid"),
    }

    contract_semantics = list(matrix_data.get("contract_semantics") or [])
    if not contract_semantics:
        contract_semantics = [
            "requested_city_circle",
            "trip_window",
            "booked_items",
            "do_not_go_places",
            "must_visit_places",
            "visited_places",
            "companion_breakdown",
            "budget_range",
        ]

    return EvalCase(
        case_id=case_id,
        description=description,
        user_profile=profile,
        expected_constraints=constraints,
        input_contract=canonical,
        matrix_city_circle=circle_id or None,
        matrix_scenario_types=list(matrix_data.get("scenario_types") or []),
        matrix_contract_semantics=contract_semantics,
        matrix_assertion_level=str(matrix_data.get("assertion_level") or "smoke"),
    )


def load_contract_v2_eval_cases(cases_file: str = "eval_cases_v2_contract.json") -> list[EvalCase]:
    fp = EVAL_CASES_DIR / cases_file
    if not fp.exists():
        logger.warning("Contract-v2 eval cases file not found: %s", fp)
        return []
    with open(fp, "r", encoding="utf-8") as f:
        raw = json.load(f)

    cases: list[EvalCase] = []
    for item in raw:
        contract = item.get("contract")
        if not isinstance(contract, dict):
            continue
        cases.append(
            build_eval_case_from_contract(
                case_id=str(item.get("case_id") or contract.get("case_id") or "unknown"),
                description=str(item.get("description") or ""),
                contract=contract,
                expected_constraints=item.get("expected_constraints"),
                matrix=item.get("matrix"),
            )
        )
    return cases


def _builtin_cases() -> list[EvalCase]:
    """内置的最小评测用例集。"""
    return [
        EvalCase(
            case_id="couple_tokyo_5d",
            description="情侣东京5日游",
            user_profile={"segment": "couple", "city": "tokyo", "days": 5, "budget": "medium"},
            expected_constraints={
                "min_days": 5, "must_have_dinner": True, "max_poi_per_day": 6,
                "must_include_types": ["poi", "restaurant"],
            },
        ),
        EvalCase(
            case_id="family_kansai_7d",
            description="家庭关西7日游",
            user_profile={"segment": "family", "city": "osaka", "days": 7, "budget": "medium", "has_children": True},
            expected_constraints={
                "min_days": 7, "must_have_dinner": True, "max_poi_per_day": 5,
                "no_late_night": True,
            },
        ),
        EvalCase(
            case_id="solo_tokyo_3d",
            description="独行侠东京3日快闪",
            user_profile={"segment": "solo", "city": "tokyo", "days": 3, "budget": "low"},
            expected_constraints={
                "min_days": 3, "max_poi_per_day": 7,
            },
        ),
        EvalCase(
            case_id="senior_kyoto_4d",
            description="银发族京都4日慢游",
            user_profile={"segment": "senior", "city": "kyoto", "days": 4, "budget": "high", "pace": "relaxed"},
            expected_constraints={
                "min_days": 4, "max_poi_per_day": 4, "must_have_rest_time": True,
            },
        ),
    ]


# ── 6 维自动评分器 ────────────────────────────────────────────────────────────

def score_plan(plan: dict[str, Any], case: EvalCase) -> EvalScore:
    """对单个行程方案进行 6 维自动评分。"""
    days = plan.get("days", [])
    constraints = case.expected_constraints
    issues: list[str] = []

    # 1. Completeness（完整度）
    completeness = 10.0
    if len(days) < constraints.get("min_days", 1):
        completeness -= 5.0
        issues.append(f"天数不足: {len(days)} < {constraints['min_days']}")
    for i, day in enumerate(days):
        items = day.get("items", [])
        if not items:
            completeness -= 2.0
            issues.append(f"Day {i+1} 没有任何安排")
        types = {it.get("entity_type") or it.get("type") for it in items}
        for must_type in constraints.get("must_include_types", []):
            if must_type not in types:
                completeness -= 0.5

    # 2. Feasibility（可行性）
    feasibility = 10.0
    for i, day in enumerate(days):
        items = day.get("items", [])
        poi_count = sum(1 for it in items if it.get("entity_type") in ("poi", "attraction"))
        max_poi = constraints.get("max_poi_per_day", 7)
        if poi_count > max_poi:
            feasibility -= 1.5
            issues.append(f"Day {i+1} 景点过多: {poi_count}")
        # 简单时间线检查
        times = [it.get("start_time", "") for it in items if it.get("start_time")]
        if times and times != sorted(times):
            feasibility -= 2.0
            issues.append(f"Day {i+1} 时间线乱序")

    # 3. Diversity（多样性）
    diversity = 10.0
    all_types = set()
    all_areas = set()
    for day in days:
        for it in day.get("items", []):
            all_types.add(it.get("entity_type"))
            all_areas.add(it.get("area_code") or it.get("area_name"))
    if len(all_types) < 2:
        diversity -= 3.0
    if len(all_areas) < 3 and len(days) > 2:
        diversity -= 2.0

    # 4. Preference Match（偏好匹配）
    pref_match = 7.0  # 默认中等，需要更复杂的逻辑
    segment = case.user_profile.get("segment", "")
    if segment == "family" and constraints.get("no_late_night"):
        for day in days:
            for it in day.get("items", []):
                t = it.get("start_time", "")
                if t and t > "21:00":
                    pref_match -= 1.0
                    issues.append("家庭行程不应有深夜安排")
    if segment == "senior" and constraints.get("must_have_rest_time"):
        pref_match += 1.0  # 有意识地安排了慢节奏

    # 5. Quality（内容质量）
    quality = 7.0
    items_with_reason = 0
    total_items = 0
    for day in days:
        for it in day.get("items", []):
            total_items += 1
            if it.get("reason") or it.get("notes_zh"):
                items_with_reason += 1
    if total_items > 0:
        reason_ratio = items_with_reason / total_items
        quality = 5.0 + reason_ratio * 5.0

    # 6. Safety（安全性）
    safety = 10.0
    # 简单检查：有无重复实体
    all_entity_ids = []
    for day in days:
        day_ids = set()
        for it in day.get("items", []):
            eid = it.get("entity_id")
            if eid and eid in day_ids:
                safety -= 2.0
                issues.append(f"同天重复实体: {eid}")
            if eid:
                day_ids.add(eid)
                all_entity_ids.append(eid)

    # Observation consistency checks are only enforced for contract-first cases.
    observation_issues = _validate_observation_chain(plan, case)
    if observation_issues:
        safety -= min(3.0, float(len(observation_issues)))
        issues.extend(observation_issues)

    # 7. Factual Reliability（L4-05）
    factual_reliability = _score_factual_reliability(plan, case)

    # 8. Pacing Quality（L4-05）
    pacing_quality = _score_pacing_quality(plan, case)

    score = EvalScore(
        completeness=max(0, min(10, completeness)),
        feasibility=max(0, min(10, feasibility)),
        diversity=max(0, min(10, diversity)),
        preference_match=max(0, min(10, pref_match)),
        quality=max(0, min(10, quality)),
        safety=max(0, min(10, safety)),
        factual_reliability=factual_reliability,
        pacing_quality=pacing_quality,
    )
    case.score = score
    case.issues = issues
    return score


# ── L4-05 新增评分函数 ────────────────────────────────────────────────────────

def _score_factual_reliability(plan: dict, case: EvalCase) -> float:
    """
    事实可靠性评分（L4-05）。检查：
    - 实体是否有 google_rating（有 = 加分，说明来源可靠）
    - 实体是否有 opening_hours_json（有 = 加分）
    - 餐厅是否有 tabelog_score（有 = 加分）
    - data_tier A 比 B 加分
    - 有 field_provenance 且非 stale = 加分

    纯规则统计，不调 API。
    """
    days = plan.get("days", [])
    total_items = 0
    score_sum = 0.0

    for day in days:
        for it in day.get("items", []):
            total_items += 1
            item_score = 5.0  # 基础分

            # google_rating 存在且合理
            gr = it.get("google_rating")
            if gr:
                try:
                    gr_f = float(gr)
                    if 1.0 <= gr_f <= 5.0:
                        item_score += 1.5
                except (ValueError, TypeError):
                    pass

            # 营业时间有记录
            if it.get("opening_hours_json") or it.get("opening_hours"):
                item_score += 1.0

            # tabelog 评分（餐厅）
            ts = it.get("tabelog_score")
            if ts:
                try:
                    if float(ts) >= 3.0:
                        item_score += 1.0
                except (ValueError, TypeError):
                    pass

            # data_tier
            tier = it.get("data_tier", "")
            if tier == "S":
                item_score += 1.5
            elif tier == "A":
                item_score += 1.0
            elif tier == "B":
                item_score += 0.5

            # field_provenance 且非 stale
            if it.get("field_provenance") and not it.get("is_stale"):
                item_score += 0.5

            score_sum += min(10.0, item_score)

    if total_items == 0:
        return 5.0  # 无数据时给中间分
    return round(score_sum / total_items, 2)


def _score_pacing_quality(plan: dict, case: EvalCase) -> float:
    """
    节奏质量评分（L4-05）。检查：
    - 每天 item 数量方差（低 = 好）
    - intensity 分布是否有"先松后紧"或"张弛有度"
    - 是否有连续 2 天都是 dense
    - arrival day 是否 light / balanced
    - departure day 是否 light

    纯规则统计，不调 API。
    """
    days = plan.get("days", [])
    if not days:
        return 5.0

    score = 10.0
    item_counts = []

    intensities = []
    for i, day in enumerate(days):
        items = day.get("items", [])
        item_counts.append(len(items))
        intensities.append(day.get("intensity", "balanced"))

        # arrival day 应该轻松
        if day.get("day_type") == "arrival" and day.get("intensity") == "dense":
            score -= 1.5

        # departure day 应该轻松
        if day.get("day_type") == "departure" and day.get("intensity") == "dense":
            score -= 1.5

    # 连续 2 天 dense 扣分
    for i in range(len(intensities) - 1):
        if intensities[i] == "dense" and intensities[i + 1] == "dense":
            score -= 1.0

    # item 数量方差（越低越稳定）
    if len(item_counts) > 1:
        mean = sum(item_counts) / len(item_counts)
        variance = sum((x - mean) ** 2 for x in item_counts) / len(item_counts)
        # 方差 > 9（标准差 > 3 个 item）开始扣分
        if variance > 9:
            score -= min(2.0, (variance - 9) * 0.2)

    # 首天和末天轻松加分
    if intensities and intensities[0] in ("light", "balanced"):
        score += 0.5
    if len(intensities) > 1 and intensities[-1] == "light":
        score += 0.5

    return round(max(0.0, min(10.0, score)), 2)


# ── 回归检测 ──────────────────────────────────────────────────────────────────

def detect_regressions(
    current_scores: list[EvalScore],
    baseline_scores: list[EvalScore],
    threshold: float = 0.5,
) -> list[dict[str, Any]]:
    """
    对比当前版本与基线版本的分数，找出回归。

    Args:
        threshold: 分数下降超过此值视为回归
    """
    regressions = []
    dims = [
        "completeness", "feasibility", "diversity", "preference_match",
        "quality", "safety", "factual_reliability", "pacing_quality",  # L4-05
    ]

    for dim in dims:
        curr_avg = sum(getattr(s, dim) for s in current_scores) / len(current_scores) if current_scores else 0
        base_avg = sum(getattr(s, dim) for s in baseline_scores) / len(baseline_scores) if baseline_scores else 0
        drop = base_avg - curr_avg
        if drop > threshold:
            regressions.append({
                "dimension": dim,
                "baseline_avg": round(base_avg, 2),
                "current_avg": round(curr_avg, 2),
                "drop": round(drop, 2),
                "severity": "critical" if drop > 1.5 else "warning",
            })

    # Overall
    curr_overall = sum(s.overall for s in current_scores) / len(current_scores) if current_scores else 0
    base_overall = sum(s.overall for s in baseline_scores) / len(baseline_scores) if baseline_scores else 0
    if base_overall - curr_overall > threshold:
        regressions.append({
            "dimension": "overall",
            "baseline_avg": round(base_overall, 2),
            "current_avg": round(curr_overall, 2),
            "drop": round(base_overall - curr_overall, 2),
            "severity": "critical",
        })

    return regressions


# ── 主入口 ────────────────────────────────────────────────────────────────────

def run_eval(
    plans: list[dict[str, Any]],
    cases: list[EvalCase] | None = None,
    baseline_file: str | None = None,
    version: str = "dev",
) -> EvalReport:
    """
    运行完整评测。

    Args:
        plans: 待评测的行程列表（与 cases 一一对应）
        cases: 评测用例，默认使用内置用例
        baseline_file: 基线分数文件路径（用于回归检测）
        version: 当前版本标识
    """
    if cases is None:
        cases = load_eval_cases()

    scores: list[EvalScore] = []
    case_results: list[dict[str, Any]] = []
    passed = 0

    for i, case in enumerate(cases):
        plan = plans[i] if i < len(plans) else {"days": []}
        case.plan_json = plan
        score = score_plan(plan, case)
        scores.append(score)

        is_pass = score.overall >= 6.0 and score.safety >= 7.0
        if is_pass:
            passed += 1

        case_results.append({
            "case_id": case.case_id,
            "description": case.description,
            "passed": is_pass,
            "score": score.to_dict(),
            "issues": case.issues,
        })

    # 回归检测
    regressions = []
    if baseline_file:
        bp = EVAL_CASES_DIR / baseline_file
        if bp.exists():
            with open(bp, "r") as f:
                baseline_data = json.load(f)
            baseline_scores = [
                EvalScore(**bs) for bs in baseline_data.get("scores", [])
            ]
            regressions = detect_regressions(scores, baseline_scores)

    # 维度均值
    dim_avgs = {}
    dims = [
        "completeness", "feasibility", "diversity", "preference_match",
        "quality", "safety", "factual_reliability", "pacing_quality",  # L4-05
    ]
    for dim in dims:
        vals = [getattr(s, dim) for s in scores]
        dim_avgs[dim] = round(sum(vals) / len(vals), 2) if vals else 0

    avg_overall = round(sum(s.overall for s in scores) / len(scores), 2) if scores else 0
    matrix_summary = _build_matrix_summary(cases)

    report = EvalReport(
        version=version,
        total_cases=len(cases),
        passed=passed,
        failed=len(cases) - passed,
        avg_score=avg_overall,
        dimension_avgs=dim_avgs,
        regressions=regressions,
        cases=case_results,
        matrix_summary=matrix_summary,
    )

    # 输出摘要
    logger.info(
        "Eval complete: v=%s, %d/%d passed, avg=%.2f, regressions=%d",
        version, passed, len(cases), avg_overall, len(regressions),
    )
    if regressions:
        for r in regressions:
            logger.warning("REGRESSION: %s dropped %.2f (%.2f → %.2f)", r["dimension"], r["drop"], r["baseline_avg"], r["current_avg"])

    return report


def save_baseline(scores: list[EvalScore], filename: str = "baseline_latest.json"):
    """保存当前分数作为基线。"""
    EVAL_CASES_DIR.mkdir(parents=True, exist_ok=True)
    fp = EVAL_CASES_DIR / filename
    data = {"scores": [asdict(s) for s in scores]}
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info("Baseline saved: %s", fp)


def _build_matrix_summary(cases: list[EvalCase]) -> dict[str, Any]:
    contract_cases = [c for c in cases if isinstance(c.input_contract, dict)]
    circles = sorted({c.matrix_city_circle for c in contract_cases if c.matrix_city_circle})
    missing = sorted(EXPECTED_CITY_CIRCLES.difference(circles))

    scenario_counts: dict[str, int] = {}
    semantics_counts: dict[str, int] = {}
    assertion_counts: dict[str, int] = {}
    for case in contract_cases:
        if case.matrix_assertion_level:
            assertion_counts[case.matrix_assertion_level] = assertion_counts.get(case.matrix_assertion_level, 0) + 1
        for scenario in case.matrix_scenario_types:
            if scenario:
                scenario_counts[scenario] = scenario_counts.get(scenario, 0) + 1
        for semantic in case.matrix_contract_semantics:
            if semantic:
                semantics_counts[semantic] = semantics_counts.get(semantic, 0) + 1

    scenario_rows = [
        {"key": k, "count": scenario_counts[k]}
        for k in sorted(scenario_counts.keys())
    ]
    semantics_rows = [
        {"key": k, "count": semantics_counts[k]}
        for k in sorted(semantics_counts.keys())
    ]

    return {
        "contract_cases": len(contract_cases),
        "city_circle": {
            "covered": circles,
            "missing": missing,
        },
        "scenario_type": {
            "rows": scenario_rows,
        },
        "contract_semantics": {
            "rows": semantics_rows,
        },
        "assertion_level": {
            "rows": [
                {"key": k, "count": assertion_counts[k]}
                for k in sorted(assertion_counts.keys())
            ],
        },
    }


def _validate_observation_chain(plan: dict[str, Any], case: EvalCase) -> list[str]:
    issues: list[str] = []
    if not isinstance(case.input_contract, dict):
        return issues

    meta = plan.get("metadata")
    if not isinstance(meta, dict):
        return ["missing_plan_metadata_for_observation_chain"]

    chain = meta.get("observation_chain")
    if not isinstance(chain, dict):
        return ["missing_observation_chain"]

    required_surfaces = (
        "run_id",
        "decision_surface",
        "handoff_surface",
        "eval_surface",
        "regression_surface",
        "replay_surface",
    )
    for key in required_surfaces:
        if not chain.get(key):
            issues.append(f"observation_chain_missing:{key}")

    if chain.get("legacy_fallback_used") is True:
        issues.append("observation_chain_legacy_fallback_used")

    evidence = meta.get("evidence_bundle")
    if isinstance(evidence, dict):
        input_contract = evidence.get("input_contract")
        if isinstance(input_contract, dict):
            expected_visited = list(case.input_contract.get("visited_places") or [])
            actual_visited = list(input_contract.get("visited_places") or [])
            if expected_visited and actual_visited != expected_visited:
                issues.append("visited_places_not_aligned_with_contract")
    return issues


