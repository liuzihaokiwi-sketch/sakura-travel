"""
评分引擎核心（Scorer）

两个公开函数：
  - compute_base_score(entity, signals) → ScoreResult
      给单个实体计算系统基础分（归一化 0-100），附带分项明细。
  - apply_editorial_boost(base_score, boost) → float
      叠加编辑 boost（-8 ~ +8），结果 clamp 到 0-100。

设计约定：
  1. 所有计算为纯函数（无 I/O）——方便单元测试、可离线重放。
  2. score_breakdown 字典格式：{dimension_key: {"raw": x, "norm": y, "weighted": z}}
  3. 风险明细格式：{risk_key: {"triggered": bool, "penalty": p}}
  4. 实际 DB 写入由上层（score_entities job）负责。
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.domains.ranking.rules import (
    CANDIDATE_CONTEXT_WEIGHT,
    CANDIDATE_SYSTEM_WEIGHT,
    DATA_TIER_MULTIPLIER,
    DIMENSIONS_BY_TYPE,
    EDITORIAL_BOOST_MAX,
    EDITORIAL_BOOST_MIN,
    RISK_RULES_BY_TYPE,
    SCORE_MAX,
    SCORE_MIN,
    SCORE_VERSION,
)

# ── 三维公式权重（启用 soft_rule_score 时） ────────────────────────────────────
# 退化公式（无 soft_rule_score）：0.60 × system + 0.40 × context
# 三维公式：0.45 × system + 0.30 × context + 0.25 × soft_rule
CANDIDATE_SYSTEM_WEIGHT_3D = 0.45
CANDIDATE_CONTEXT_WEIGHT_3D = 0.30
CANDIDATE_SOFT_RULE_WEIGHT_3D = 0.25


# ── 输入信号 DataClass ─────────────────────────────────────────────────────────

@dataclass
class EntitySignals:
    """
    传入 scorer 的原始信号集合。
    调用方从 ORM 实体 + 快照中提取后传入。
    所有字段可选，缺失时使用合理默认值（不中断计算）。
    """
    entity_type: str = "poi"          # poi | hotel | restaurant
    data_tier: str = "B"              # S | A | B

    # ── 通用评分信号 ──────────────────────────────────────────────────────────
    google_rating: float | None = None        # 0-5
    google_review_count: int | None = None
    booking_score: float | None = None        # 酒店用，0-10
    tabelog_score: float | None = None        # 餐厅用，0-5

    # ── 数据新鲜度 ────────────────────────────────────────────────────────────
    updated_at: datetime | None = None        # 最近更新时间，None → 扣半分

    # ── POI 专用信号 ──────────────────────────────────────────────────────────
    has_opening_hours: bool = True            # opening_hours_json 非空
    best_season: str | None = None            # spring/summer/autumn/winter/all/None
    city_popularity_score: float = 50.0       # 外部传入热度分，默认 50
    area_efficiency_score: float = 50.0       # 区域串联效率，默认 50
    theme_match_score: float = 50.0           # 与用户主题匹配，默认 50
    has_seasonal_tags: bool = False           # 是否有季节提示标签

    # ── 酒店专用信号 ──────────────────────────────────────────────────────────
    walking_distance_station_min: int | None = None   # 步行到地铁分钟数
    transport_convenience_score: float = 50.0
    value_for_money_score: float = 50.0
    amenity_coverage_score: float = 50.0
    booking_stability_score: float = 50.0
    has_price_volatility: bool = False
    has_hygiene_noise_complaints: bool = False
    has_bad_cancellation: bool = False

    # ── 餐厅专用信号 ──────────────────────────────────────────────────────────
    timeslot_route_fit_score: float = 50.0
    price_match_score: float = 50.0
    reservation_feasibility_score: float = 50.0
    cuisine_diversity_score: float = 50.0
    has_extreme_queue: bool = False
    has_meal_slot_mismatch: bool = False
    has_price_inflated: bool = False

    # ── 通用风险 ──────────────────────────────────────────────────────────────
    homogeneity_count: int = 0     # 同城市同类型已推荐数量（景点同质化判断）

    # ── 编辑 boost（来自 entity_editor_notes） ────────────────────────────────
    editorial_boost: int = 0       # -8 ~ +8


# ── 输出结果 DataClass ─────────────────────────────────────────────────────────

@dataclass
class ScoreResult:
    """
    单次评分结果，包含所有层级的分数和可解释明细。
    对应 entity_scores 表中的字段。
    """
    entity_type: str
    score_profile: str                         # "general" 或传入的 profile 名
    base_score: float                          # 系统基础分 0-100（写 base_score 列）
    editorial_boost: int                       # 编辑修正 -8~+8
    final_score: float                         # clamp(base_score + editorial_boost, 0, 100)
    score_breakdown: dict[str, Any]            # 分项明细（写 score_breakdown 列）
    score_version: str = SCORE_VERSION


# ── 内部工具函数 ───────────────────────────────────────────────────────────────

def _clamp(value: float, lo: float = SCORE_MIN, hi: float = SCORE_MAX) -> float:
    """将 value 限制在 [lo, hi] 区间。"""
    return max(lo, min(hi, value))


def _normalize(raw: float, max_raw: float) -> float:
    """将 raw 归一化到 0-100。max_raw <= 0 时返回 0。"""
    if max_raw <= 0:
        return 0.0
    return _clamp(raw / max_raw * 100.0)


def _review_count_norm(count: int | None, max_count: float) -> float:
    """
    评论量置信度：使用对数缩放而非线性，避免超大平台把小众景点全压死。
    norm = log(count+1) / log(max_count+1) × 100
    """
    if not count or count <= 0:
        return 0.0
    return _clamp(math.log(count + 1) / math.log(max_count + 1) * 100.0)


def _freshness_score(updated_at: datetime | None) -> float:
    """
    数据新鲜度分（0-100）：
    - 30 天内：100
    - 90 天内：75
    - 180 天内：50
    - 365 天内：25
    - 超过一年或为 None：10
    """
    if updated_at is None:
        return 10.0
    now = datetime.now(tz=timezone.utc)
    # 确保 updated_at 有时区信息
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)
    days = (now - updated_at).days
    if days <= 30:
        return 100.0
    elif days <= 90:
        return 75.0
    elif days <= 180:
        return 50.0
    elif days <= 365:
        return 25.0
    else:
        return 10.0


def _platform_rating_norm(signals: EntitySignals) -> float:
    """
    统一处理 platform_rating（Google/Booking/Tabelog）→ 归一化到 0-100。
    优先 Google rating，酒店次选 Booking，餐厅次选 Tabelog。
    """
    rating: float | None = signals.google_rating

    if rating is None and signals.entity_type == "hotel":
        # Booking 评分 0-10 → 先折算成 0-5
        rating = signals.booking_score / 2.0 if signals.booking_score is not None else None

    if rating is None and signals.entity_type == "restaurant":
        rating = signals.tabelog_score  # Tabelog 0-5

    if rating is None:
        return 40.0  # 无评分数据时给中低默认分

    return _clamp((rating / 5.0) * 100.0)


# ── POI 系统分计算 ─────────────────────────────────────────────────────────────

def _compute_poi_system_score(signals: EntitySignals) -> tuple[float, dict]:
    """
    计算 POI system_score（0-100）和分项明细。
    返回 (score, breakdown_partial_dict)
    """
    dims = DIMENSIONS_BY_TYPE["poi"]
    breakdown: dict[str, Any] = {}
    weighted_sum = 0.0

    for dim in dims:
        if dim.key == "platform_rating":
            raw = _platform_rating_norm(signals)
            norm = raw  # 已经是 0-100
        elif dim.key == "review_confidence":
            raw = float(signals.google_review_count or 0)
            norm = _review_count_norm(signals.google_review_count, dim.max_raw)
        elif dim.key == "city_popularity":
            raw = signals.city_popularity_score
            norm = _normalize(raw, dim.max_raw)
        elif dim.key == "theme_match":
            raw = signals.theme_match_score
            norm = _normalize(raw, dim.max_raw)
        elif dim.key == "area_efficiency":
            raw = signals.area_efficiency_score
            norm = _normalize(raw, dim.max_raw)
        elif dim.key == "data_freshness":
            raw = _freshness_score(signals.updated_at)
            norm = raw
        else:
            raw = 0.0
            norm = 0.0

        weighted = norm * dim.weight
        weighted_sum += weighted
        breakdown[dim.key] = {"raw": round(raw, 2), "norm": round(norm, 2), "weighted": round(weighted, 2)}

    return _clamp(weighted_sum), breakdown


# ── 酒店系统分计算 ────────────────────────────────────────────────────────────

def _compute_hotel_system_score(signals: EntitySignals) -> tuple[float, dict]:
    """计算酒店 system_score（0-100）和分项明细。"""
    dims = DIMENSIONS_BY_TYPE["hotel"]
    breakdown: dict[str, Any] = {}
    weighted_sum = 0.0

    for dim in dims:
        if dim.key == "platform_rating":
            raw = _platform_rating_norm(signals)
            norm = raw
        elif dim.key == "review_confidence":
            raw = float(signals.google_review_count or 0)
            norm = _review_count_norm(signals.google_review_count, dim.max_raw)
        elif dim.key == "transport_convenience":
            raw = signals.transport_convenience_score
            norm = _normalize(raw, dim.max_raw)
        elif dim.key == "value_for_money":
            raw = signals.value_for_money_score
            norm = _normalize(raw, dim.max_raw)
        elif dim.key == "amenity_coverage":
            raw = signals.amenity_coverage_score
            norm = _normalize(raw, dim.max_raw)
        elif dim.key == "booking_stability":
            raw = signals.booking_stability_score
            norm = _normalize(raw, dim.max_raw)
        else:
            raw = 0.0
            norm = 0.0

        weighted = norm * dim.weight
        weighted_sum += weighted
        breakdown[dim.key] = {"raw": round(raw, 2), "norm": round(norm, 2), "weighted": round(weighted, 2)}

    return _clamp(weighted_sum), breakdown


# ── 餐厅系统分计算 ────────────────────────────────────────────────────────────

def _compute_restaurant_system_score(signals: EntitySignals) -> tuple[float, dict]:
    """计算餐厅 system_score（0-100）和分项明细。"""
    dims = DIMENSIONS_BY_TYPE["restaurant"]
    breakdown: dict[str, Any] = {}
    weighted_sum = 0.0

    for dim in dims:
        if dim.key == "platform_rating":
            raw = _platform_rating_norm(signals)
            norm = raw
        elif dim.key == "review_confidence":
            raw = float(signals.google_review_count or 0)
            norm = _review_count_norm(signals.google_review_count, dim.max_raw)
        elif dim.key == "timeslot_route_fit":
            raw = signals.timeslot_route_fit_score
            norm = _normalize(raw, dim.max_raw)
        elif dim.key == "price_match":
            raw = signals.price_match_score
            norm = _normalize(raw, dim.max_raw)
        elif dim.key == "reservation_feasibility":
            raw = signals.reservation_feasibility_score
            norm = _normalize(raw, dim.max_raw)
        elif dim.key == "cuisine_diversity":
            raw = signals.cuisine_diversity_score
            norm = _normalize(raw, dim.max_raw)
        else:
            raw = 0.0
            norm = 0.0

        weighted = norm * dim.weight
        weighted_sum += weighted
        breakdown[dim.key] = {"raw": round(raw, 2), "norm": round(norm, 2), "weighted": round(weighted, 2)}

    return _clamp(weighted_sum), breakdown


# ── 风险扣分计算 ──────────────────────────────────────────────────────────────

def _compute_risk_penalty(signals: EntitySignals) -> tuple[float, dict]:
    """
    根据 signals 计算总风险扣分和明细。
    返回 (total_penalty, risk_breakdown)
    total_penalty 为正数，使用时取负。
    """
    entity_type = signals.entity_type
    risk_rules = RISK_RULES_BY_TYPE.get(entity_type, [])
    risk_breakdown: dict[str, Any] = {}
    total_penalty = 0.0

    for rule in risk_rules:
        triggered = False

        # POI 风险触发判断
        if entity_type == "poi":
            if rule.key == "unstable_hours":
                triggered = not signals.has_opening_hours
            elif rule.key == "high_transport_cost":
                triggered = False  # 需要外部路线数据，默认不触发
            elif rule.key == "seasonal_unlabeled":
                triggered = (
                    signals.best_season not in (None, "all")
                    and not signals.has_seasonal_tags
                )
            elif rule.key == "homogeneity":
                triggered = signals.homogeneity_count >= 3

        # 酒店风险触发判断
        elif entity_type == "hotel":
            if rule.key == "price_volatility":
                triggered = signals.has_price_volatility
            elif rule.key == "poor_transport":
                triggered = (
                    signals.walking_distance_station_min is not None
                    and signals.walking_distance_station_min > 20
                )
            elif rule.key == "hygiene_noise_complaints":
                triggered = signals.has_hygiene_noise_complaints
            elif rule.key == "bad_cancellation":
                triggered = signals.has_bad_cancellation

        # 餐厅风险触发判断
        elif entity_type == "restaurant":
            if rule.key == "long_queue_no_alt":
                triggered = signals.has_extreme_queue
            elif rule.key == "meal_slot_mismatch":
                triggered = signals.has_meal_slot_mismatch
            elif rule.key == "price_inflated":
                triggered = signals.has_price_inflated
            elif rule.key == "unstable_hours":
                triggered = not signals.has_opening_hours

        penalty_applied = rule.penalty if triggered else 0.0
        total_penalty += penalty_applied
        risk_breakdown[rule.key] = {
            "triggered": triggered,
            "penalty": penalty_applied,
            "label": rule.label,
        }

    return total_penalty, risk_breakdown


# ── 主公开函数 ────────────────────────────────────────────────────────────────

def compute_base_score(
    signals: EntitySignals,
    score_profile: str = "general",
) -> ScoreResult:
    """
    计算实体基础评分（纯函数，无 I/O）。

    步骤：
    1. 按 entity_type 计算 system_score（维度加权求和）
    2. 按 data_tier 应用置信度折扣
    3. 减去风险扣分
    4. clamp 到 0-100 → base_score

    不叠加 editorial_boost，让调用方决定是否调用 apply_editorial_boost。

    Args:
        signals: 从 ORM 实体 + 快照中提取的原始信号集合
        score_profile: 评分 profile 名称（general / family / culture / ...）

    Returns:
        ScoreResult，包含 base_score、final_score（已含 boost）和分项明细
    """
    entity_type = signals.entity_type

    # Step 1: 计算 system_score
    if entity_type == "poi":
        system_score, dim_breakdown = _compute_poi_system_score(signals)
    elif entity_type == "hotel":
        system_score, dim_breakdown = _compute_hotel_system_score(signals)
    elif entity_type == "restaurant":
        system_score, dim_breakdown = _compute_restaurant_system_score(signals)
    else:
        raise ValueError(f"Unsupported entity_type: {entity_type!r}")

    # Step 2: data_tier 置信度折扣
    tier_multiplier = DATA_TIER_MULTIPLIER.get(signals.data_tier, 0.75)
    system_score_adjusted = system_score * tier_multiplier

    # Step 3: 风险扣分
    risk_penalty, risk_breakdown = _compute_risk_penalty(signals)
    raw_base = system_score_adjusted - risk_penalty

    # Step 4: clamp
    base_score = round(_clamp(raw_base), 2)

    # Step 5: 合并 breakdown
    breakdown = {
        "dimensions": dim_breakdown,
        "system_score_raw": round(system_score, 2),
        "tier_multiplier": tier_multiplier,
        "system_score_adjusted": round(system_score_adjusted, 2),
        "risk_penalty": round(risk_penalty, 2),
        "risk_details": risk_breakdown,
        "score_version": SCORE_VERSION,
    }

    # Step 6: 叠加 boost 得到 final_score（boost 在 base 上直接加）
    final_score = apply_editorial_boost(base_score, signals.editorial_boost)

    return ScoreResult(
        entity_type=entity_type,
        score_profile=score_profile,
        base_score=base_score,
        editorial_boost=signals.editorial_boost,
        final_score=final_score,
        score_breakdown=breakdown,
    )


# ── Context Score（主观偏好适配分）────────────────────────────────────────────

# 合法的主题维度 key（与 context_score_design.json 对齐）
THEME_KEYS = frozenset([
    "shopping",
    "food",
    "culture_history",
    "onsen_relaxation",
    "nature_outdoors",
    "anime_pop_culture",
    "family_kids",
    "nightlife_entertainment",
    "photography_scenic",
])


def compute_context_score(
    user_weights: dict[str, float],
    entity_affinity: dict[str, int],
) -> tuple[float, dict]:
    """
    计算 context_score（主观偏好适配分，0-100），纯函数，无 I/O。

    设计原则（来自 context_score_design.json）：
      - 只衡量主观偏好适配度，不重复计算 system_score 的客观信号
      - raw = Σ(user_weight_i × entity_affinity_i)
      - normalized = raw × (100 / (5 × Σ(user_weight_i)))
      - 若权重和为 0，返回 0.0

    Args:
        user_weights:   {theme_key: weight (0.0-1.0)}，用户画像中各主题权重
        entity_affinity: {theme_key: affinity (0-5)}，实体在各主题上的匹配度

    Returns:
        (context_score, breakdown)
        breakdown 格式：{theme_key: {"weight": w, "affinity": a, "contribution": w*a}}
    """
    weights_sum = sum(user_weights.values())
    if weights_sum == 0:
        return 0.0, {}

    breakdown: dict[str, Any] = {}
    raw = 0.0
    for key, weight in user_weights.items():
        if weight <= 0:
            continue
        affinity = float(entity_affinity.get(key, 0))
        contribution = weight * affinity
        raw += contribution
        breakdown[key] = {
            "weight": round(weight, 4),
            "affinity": int(affinity),
            "contribution": round(contribution, 4),
        }

    score = raw * (100.0 / (5.0 * weights_sum))
    return round(_clamp(score), 2), breakdown


def apply_editorial_boost(base_score: float, boost: int) -> float:
    """
    将编辑 boost 叠加到 base_score 上，结果 clamp 到 0-100。

    boost 合法范围为 EDITORIAL_BOOST_MIN ~ EDITORIAL_BOOST_MAX（-8 ~ +8）。
    超出范围时自动 clamp boost 值，不抛异常（宽容接受，避免 job 崩溃）。

    Args:
        base_score: compute_base_score 产出的系统基础分（0-100）
        boost: 编辑修正值（-8 ~ +8）

    Returns:
        final_score: clamp 后的最终分（0-100）
    """
    clamped_boost = max(EDITORIAL_BOOST_MIN, min(EDITORIAL_BOOST_MAX, boost))
    return round(_clamp(base_score + clamped_boost), 2)


# ── Candidate Score（候选排序分 — 三维公式） ──────────────────────────────────

@dataclass
class CandidateScoreResult:
    """
    候选排序分结果，包含三维公式的分项明细。

    三维公式（启用软规则时）：
      candidate_score = 0.45 × system_score + 0.30 × context_score
                      + 0.25 × soft_rule_score - risk_penalty
      final = candidate_score + editorial_boost

    退化公式（无软规则分时）：
      candidate_score = 0.60 × system_score + 0.40 × context_score
                      - risk_penalty
      final = candidate_score + editorial_boost
    """
    entity_id: str
    entity_type: str
    system_score: float          # 0-100
    context_score: float         # 0-100
    soft_rule_score: float | None  # 0-100，None 表示未启用
    risk_penalty: float          # >= 0
    editorial_boost: int         # -8 ~ +8
    candidate_score: float       # 加权后 0-100
    final_score: float           # candidate + boost, 0-100
    formula_used: str            # "3d" | "2d"
    breakdown: dict[str, Any]    # 完整明细


def compute_candidate_score(
    signals: EntitySignals,
    user_weights: dict[str, float] | None = None,
    entity_affinity: dict[str, int] | None = None,
    soft_rule_score: float | None = None,
    segment_pack_id: str | None = None,
    stage_pack_id: str | None = None,
    score_profile: str = "general",
) -> CandidateScoreResult:
    """
    计算候选排序分（三维公式 / 退化二维公式）。

    这是对外暴露的主计算接口，统一了 system_score + context_score + soft_rule_score。

    Args:
        signals: 实体原始信号
        user_weights: 用户主题偏好权重（计算 context_score 用）
        entity_affinity: 实体主题亲和度（计算 context_score 用）
        soft_rule_score: 软规则分 0-100（传 None 退化到二维公式）
        segment_pack_id: 客群权重包 ID（记录在 breakdown 中）
        stage_pack_id: 阶段权重包 ID（记录在 breakdown 中）
        score_profile: 评分 profile 名称

    Returns:
        CandidateScoreResult 完整结果
    """
    entity_type = signals.entity_type

    # Step 1: system_score（复用已有逻辑）
    score_result = compute_base_score(signals, score_profile)
    system_score = score_result.base_score  # 已含 tier_multiplier 和 risk_penalty

    # 但我们需要分离 system_score（不含 risk）和 risk_penalty
    raw_system = score_result.score_breakdown.get("system_score_adjusted", system_score)
    risk_penalty = score_result.score_breakdown.get("risk_penalty", 0.0)

    # Step 2: context_score
    ctx_score = 0.0
    ctx_breakdown: dict[str, Any] = {}
    if user_weights and entity_affinity:
        ctx_score, ctx_breakdown = compute_context_score(user_weights, entity_affinity)

    # Step 3: 选择公式
    if soft_rule_score is not None:
        # 三维公式
        formula = "3d"
        candidate = (
            CANDIDATE_SYSTEM_WEIGHT_3D * raw_system
            + CANDIDATE_CONTEXT_WEIGHT_3D * ctx_score
            + CANDIDATE_SOFT_RULE_WEIGHT_3D * soft_rule_score
            - risk_penalty
        )
    else:
        # 退化二维公式
        formula = "2d"
        candidate = (
            CANDIDATE_SYSTEM_WEIGHT * raw_system
            + CANDIDATE_CONTEXT_WEIGHT * ctx_score
            - risk_penalty
        )

    candidate = round(_clamp(candidate), 2)

    # Step 4: editorial boost
    final = apply_editorial_boost(candidate, signals.editorial_boost)

    # Step 5: breakdown
    breakdown = {
        "system_score_raw": round(raw_system, 2),
        "system_score_breakdown": score_result.score_breakdown.get("dimensions", {}),
        "tier_multiplier": score_result.score_breakdown.get("tier_multiplier", 1.0),
        "context_score": round(ctx_score, 2),
        "context_score_breakdown": ctx_breakdown,
        "soft_rule_score": round(soft_rule_score, 2) if soft_rule_score is not None else None,
        "segment_pack_id": segment_pack_id,
        "stage_pack_id": stage_pack_id,
        "risk_penalty": round(risk_penalty, 2),
        "risk_details": score_result.score_breakdown.get("risk_details", {}),
        "editorial_boost": signals.editorial_boost,
        "formula": formula,
        "weights": {
            "system": CANDIDATE_SYSTEM_WEIGHT_3D if formula == "3d" else CANDIDATE_SYSTEM_WEIGHT,
            "context": CANDIDATE_CONTEXT_WEIGHT_3D if formula == "3d" else CANDIDATE_CONTEXT_WEIGHT,
            "soft_rule": CANDIDATE_SOFT_RULE_WEIGHT_3D if formula == "3d" else 0.0,
        },
        "score_version": SCORE_VERSION,
    }

    return CandidateScoreResult(
        entity_id=str(getattr(signals, "entity_id", "unknown")),
        entity_type=entity_type,
        system_score=round(raw_system, 2),
        context_score=round(ctx_score, 2),
        soft_rule_score=round(soft_rule_score, 2) if soft_rule_score is not None else None,
        risk_penalty=round(risk_penalty, 2),
        editorial_boost=signals.editorial_boost,
        candidate_score=candidate,
        final_score=final,
        formula_used=formula,
        breakdown=breakdown,
    )
