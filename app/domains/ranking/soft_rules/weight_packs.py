"""
权重包管理模块（Weight Pack Manager）

管理客群权重包（segment_weight_packs）和阶段权重包（stage_weight_packs），
提供聚合计算接口，连接维度分和最终的 soft_rule_score。

核心函数：
  - get_segment_weight_pack(pack_id) → dict[str, float]
  - get_stage_weight_pack(pack_id) → dict[str, float]
  - merge_weight_packs(segment_pack, stage_pack) → dict[str, float]
  - aggregate_soft_rule_score(dimension_scores, merged_weights) → float

权重包合并逻辑：
  merged_weight[dim] = 0.6 × segment_weight[dim] + 0.4 × stage_weight[dim]
  然后 re-normalize 使总和 = 1.0

设计约定：
  - 权重包存储为 JSONB，结构是 {dimension_id: weight_float}
  - segment 包覆盖"对谁好"，stage 包覆盖"在什么场景下好"
  - 缺失时使用 DEFAULT_WEIGHTS 兜底
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from app.domains.ranking.soft_rules.dimensions import (
    DEFAULT_WEIGHTS,
    DIMENSION_IDS,
    validate_weights,
)


# ── 合并常量 ───────────────────────────────────────────────────────────────────

SEGMENT_MERGE_RATIO = 0.6   # 客群权重包占比
STAGE_MERGE_RATIO = 0.4     # 阶段权重包占比


# ── 内存缓存（进程级，非 Redis） ───────────────────────────────────────────────

_pack_cache: dict[str, dict[str, float]] = {}


def _cache_key(pack_type: str, pack_id: str) -> str:
    return f"{pack_type}:{pack_id}"


def invalidate_pack_cache(pack_type: str | None = None, pack_id: str | None = None) -> None:
    """
    清除权重包缓存。
    - 不传参数：清除所有缓存
    - 传 pack_type + pack_id：清除指定缓存
    """
    if pack_type is None:
        _pack_cache.clear()
    elif pack_id is not None:
        _pack_cache.pop(_cache_key(pack_type, pack_id), None)


# ── 数据库访问层（同步版本，async 版本后续添加） ────────────────────────────────

def get_segment_weight_pack(
    pack_id: str,
    db_session: Any = None,
) -> dict[str, float]:
    """
    获取客群权重包。

    Args:
        pack_id: 权重包 ID（如 "couple", "family_child", "first_time_fit"）
        db_session: SQLAlchemy session（传 None 时使用默认权重兜底）

    Returns:
        12 维度权重字典
    """
    ck = _cache_key("segment", pack_id)
    if ck in _pack_cache:
        return _pack_cache[ck]

    weights = _load_pack_from_db("segment", pack_id, db_session)
    _pack_cache[ck] = weights
    return weights


def get_stage_weight_pack(
    pack_id: str,
    db_session: Any = None,
) -> dict[str, float]:
    """
    获取阶段权重包。

    Args:
        pack_id: 权重包 ID（如 "preview_day1", "standard", "self_serve_tuning"）
        db_session: SQLAlchemy session（传 None 时使用默认权重兜底）

    Returns:
        12 维度权重字典
    """
    ck = _cache_key("stage", pack_id)
    if ck in _pack_cache:
        return _pack_cache[ck]

    weights = _load_pack_from_db("stage", pack_id, db_session)
    _pack_cache[ck] = weights
    return weights


def _load_pack_from_db(
    pack_type: str,
    pack_id: str,
    db_session: Any,
) -> dict[str, float]:
    """
    从数据库加载权重包。
    v1 阶段如果数据库不可用或找不到记录，fallback 到默认权重。
    后续 async 版本会替换这个实现。
    """
    if db_session is not None:
        try:
            if pack_type == "segment":
                from app.db.models.soft_rules import SegmentWeightPack
                result = db_session.query(SegmentWeightPack).filter_by(
                    pack_id=pack_id
                ).first()
            else:
                from app.db.models.soft_rules import StageWeightPack
                result = db_session.query(StageWeightPack).filter_by(
                    pack_id=pack_id
                ).first()

            if result is not None and result.weights:
                weights = result.weights
                is_valid, _ = validate_weights(weights)
                if is_valid:
                    return weights
        except Exception:
            pass  # DB 不可用时 fallback

    return dict(DEFAULT_WEIGHTS)


# ── 权重包合并 ─────────────────────────────────────────────────────────────────

def merge_weight_packs(
    segment_weights: dict[str, float],
    stage_weights: dict[str, float],
    segment_ratio: float = SEGMENT_MERGE_RATIO,
    stage_ratio: float = STAGE_MERGE_RATIO,
) -> dict[str, float]:
    """
    合并客群权重包和阶段权重包，生成最终权重。

    公式：
      raw_weight[dim] = segment_ratio × segment_weights[dim]
                      + stage_ratio × stage_weights[dim]
      merged_weight[dim] = raw_weight[dim] / sum(all raw_weights)  # re-normalize

    Args:
        segment_weights: 客群权重字典
        stage_weights: 阶段权重字典
        segment_ratio: 客群权重占比（默认 0.6）
        stage_ratio: 阶段权重占比（默认 0.4）

    Returns:
        re-normalized 后的 12 维度权重字典（求和 = 1.0）
    """
    raw: dict[str, float] = {}
    for dim_id in DIMENSION_IDS:
        seg_w = segment_weights.get(dim_id, DEFAULT_WEIGHTS[dim_id])
        stg_w = stage_weights.get(dim_id, DEFAULT_WEIGHTS[dim_id])
        raw[dim_id] = segment_ratio * seg_w + stage_ratio * stg_w

    # Re-normalize
    total = sum(raw.values())
    if total <= 0:
        return dict(DEFAULT_WEIGHTS)

    return {dim_id: round(w / total, 6) for dim_id, w in raw.items()}


# ── 聚合计算 ───────────────────────────────────────────────────────────────────

def aggregate_soft_rule_score(
    dimension_scores: dict[str, float],
    merged_weights: dict[str, float],
) -> float:
    """
    将 12 维度分聚合为 0-100 的 soft_rule_score。

    公式：
      raw = Σ (dimension_scores[dim] × merged_weights[dim])
      score = raw × 10   # 维度分 0-10，权重和 1.0 → raw 范围 0-10 → 乘 10 归一化到 0-100

    Args:
        dimension_scores: {dimension_id: score (0-10)} 实体在各维度的得分
        merged_weights: {dimension_id: weight} 合并后的权重（求和=1.0）

    Returns:
        soft_rule_score, 范围 0-100
    """
    raw = 0.0
    for dim_id in DIMENSION_IDS:
        score = dimension_scores.get(dim_id, 5.0)  # 缺失维度默认中间分
        weight = merged_weights.get(dim_id, DEFAULT_WEIGHTS[dim_id])
        raw += score * weight

    # raw 范围 0-10（维度分 0-10 × 权重和 1.0），乘 10 映射到 0-100
    return round(max(0.0, min(100.0, raw * 10.0)), 2)


def compute_soft_rule_score_simple(
    dimension_scores: dict[str, float],
    segment_pack_id: str = "default",
    stage_pack_id: str = "standard",
    db_session: Any = None,
) -> tuple[float, dict[str, float]]:
    """
    便捷函数：一次性完成 加载权重包 → 合并 → 聚合 计算。

    Args:
        dimension_scores: 实体 12 维度分
        segment_pack_id: 客群权重包 ID
        stage_pack_id: 阶段权重包 ID
        db_session: 数据库 session

    Returns:
        (soft_rule_score, merged_weights)
    """
    seg_w = get_segment_weight_pack(segment_pack_id, db_session)
    stg_w = get_stage_weight_pack(stage_pack_id, db_session)
    merged = merge_weight_packs(seg_w, stg_w)
    score = aggregate_soft_rule_score(dimension_scores, merged)
    return score, merged


# ── 预定义客群权重包种子数据 ────────────────────────────────────────────────────

SEGMENT_PACK_SEEDS: dict[str, dict[str, float]] = {
    "couple": {
        "emotional_value": 0.16,   # 情侣重情绪价值
        "shareability": 0.14,      # 重出片
        "relaxation_feel": 0.10,
        "memory_point": 0.12,      # 重独特记忆
        "localness": 0.06,
        "food_certainty": 0.08,
        "professional_judgement_feel": 0.06,
        "smoothness": 0.08,
        "night_completion": 0.10,  # 夜间安排很重要
        "recovery_friendliness": 0.04,
        "weather_resilience_soft": 0.03,
        "preview_conversion_power": 0.03,
    },
    "family_child": {
        "emotional_value": 0.08,
        "shareability": 0.06,
        "relaxation_feel": 0.14,   # 带娃需要松弛
        "memory_point": 0.08,
        "localness": 0.04,
        "food_certainty": 0.12,    # 餐饮不能出错
        "professional_judgement_feel": 0.06,
        "smoothness": 0.10,
        "night_completion": 0.04,  # 带娃夜间不重要
        "recovery_friendliness": 0.16, # 体力友好最重要
        "weather_resilience_soft": 0.08, # 需要雨天备案
        "preview_conversion_power": 0.04,
    },
    "besties": {
        "emotional_value": 0.12,
        "shareability": 0.16,      # 闺蜜最重出片
        "relaxation_feel": 0.08,
        "memory_point": 0.10,
        "localness": 0.08,
        "food_certainty": 0.10,
        "professional_judgement_feel": 0.06,
        "smoothness": 0.08,
        "night_completion": 0.10,
        "recovery_friendliness": 0.04,
        "weather_resilience_soft": 0.04,
        "preview_conversion_power": 0.04,
    },
    "first_time_fit": {
        "emotional_value": 0.10,
        "shareability": 0.10,
        "relaxation_feel": 0.08,
        "memory_point": 0.12,      # 初次游重经典记忆
        "localness": 0.04,         # 初次游不太在意在地感
        "food_certainty": 0.10,
        "professional_judgement_feel": 0.10, # 初次游很需要专业感
        "smoothness": 0.12,        # 不熟悉交通，顺畅很重要
        "night_completion": 0.06,
        "recovery_friendliness": 0.06,
        "weather_resilience_soft": 0.06,
        "preview_conversion_power": 0.06,
    },
    "repeat_fit": {
        "emotional_value": 0.10,
        "shareability": 0.08,
        "relaxation_feel": 0.10,
        "memory_point": 0.08,
        "localness": 0.16,         # 重游最在意在地感
        "food_certainty": 0.10,
        "professional_judgement_feel": 0.10,
        "smoothness": 0.08,
        "night_completion": 0.08,
        "recovery_friendliness": 0.04,
        "weather_resilience_soft": 0.04,
        "preview_conversion_power": 0.04,
    },
    "parents": {
        "emotional_value": 0.10,
        "shareability": 0.06,
        "relaxation_feel": 0.16,   # 带父母需要轻松
        "memory_point": 0.10,
        "localness": 0.06,
        "food_certainty": 0.12,
        "professional_judgement_feel": 0.06,
        "smoothness": 0.10,
        "night_completion": 0.02,  # 老人早睡
        "recovery_friendliness": 0.14, # 体力非常重要
        "weather_resilience_soft": 0.06,
        "preview_conversion_power": 0.02,
    },
    "friends_small_group": {
        "emotional_value": 0.12,
        "shareability": 0.12,
        "relaxation_feel": 0.08,
        "memory_point": 0.10,
        "localness": 0.08,
        "food_certainty": 0.10,
        "professional_judgement_feel": 0.06,
        "smoothness": 0.08,
        "night_completion": 0.12,  # 朋友出游夜间重要
        "recovery_friendliness": 0.04,
        "weather_resilience_soft": 0.04,
        "preview_conversion_power": 0.06,
    },
}


# ── 预定义阶段权重包种子数据 ────────────────────────────────────────────────────

STAGE_PACK_SEEDS: dict[str, dict[str, float]] = {
    "preview_day1": {
        "emotional_value": 0.14,
        "shareability": 0.14,       # 预览阶段最重出片+惊喜
        "relaxation_feel": 0.06,
        "memory_point": 0.12,
        "localness": 0.04,
        "food_certainty": 0.06,
        "professional_judgement_feel": 0.12, # 预览要体现专业
        "smoothness": 0.06,
        "night_completion": 0.04,
        "recovery_friendliness": 0.02,
        "weather_resilience_soft": 0.02,
        "preview_conversion_power": 0.18,   # 预览阶段转化力权重最高
    },
    "standard": {
        # 标准阶段 = 默认权重
        **DEFAULT_WEIGHTS,
    },
    "premium": {
        "emotional_value": 0.14,
        "shareability": 0.10,
        "relaxation_feel": 0.10,
        "memory_point": 0.12,
        "localness": 0.10,          # 高级版更重在地感
        "food_certainty": 0.10,
        "professional_judgement_feel": 0.10,
        "smoothness": 0.08,
        "night_completion": 0.06,
        "recovery_friendliness": 0.04,
        "weather_resilience_soft": 0.03,
        "preview_conversion_power": 0.03,
    },
    "self_serve_tuning": {
        "emotional_value": 0.08,
        "shareability": 0.08,
        "relaxation_feel": 0.12,     # 微调时松弛感更重要
        "memory_point": 0.06,
        "localness": 0.06,
        "food_certainty": 0.14,      # 微调时餐饮确定性很重要
        "professional_judgement_feel": 0.06,
        "smoothness": 0.16,          # 微调后交通顺畅最重要
        "night_completion": 0.06,
        "recovery_friendliness": 0.10,
        "weather_resilience_soft": 0.04,
        "preview_conversion_power": 0.04,
    },
}
