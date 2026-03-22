"""
评分规则配置（Scoring Rules Config）

定义各 entity_type 的评分维度权重、风险扣分规则，以及编辑 boost 的合法范围。
所有权重之和 = 1.0，风险扣分为负值，最终分数归一化到 0-100。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


# ── 常量 ───────────────────────────────────────────────────────────────────────

SCORE_VERSION = "v1.0"

EDITORIAL_BOOST_MIN = -8
EDITORIAL_BOOST_MAX = 8

SCORE_MIN = 0.0
SCORE_MAX = 100.0

EntityType = Literal["poi", "hotel", "restaurant"]

# 候选分公式权重（二维退化公式）
CANDIDATE_SYSTEM_WEIGHT = 0.60
CANDIDATE_CONTEXT_WEIGHT = 0.40

# 候选分公式权重（三维公式 — 启用 soft_rule_score 时）
CANDIDATE_SYSTEM_WEIGHT_3D = 0.45
CANDIDATE_CONTEXT_WEIGHT_3D = 0.30
CANDIDATE_SOFT_RULE_WEIGHT_3D = 0.25


# ── 数据类：评分维度 ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ScoreDimension:
    """单个评分维度定义"""
    key: str          # 唯一标识，写入 score_breakdown
    label: str        # 可读名称
    weight: float     # 权重（0-1），同 entity_type 下所有维度之和 = 1.0
    max_raw: float    # 该维度原始值的最大值（用于归一化）


@dataclass(frozen=True)
class RiskRule:
    """风险扣分规则"""
    key: str          # 风险标识，写入 score_breakdown
    label: str        # 可读名称
    penalty: float    # 扣分值（正数，实际使用时取负）
    condition: str    # 触发条件说明（文档用）


# ── POI 评分维度 ──────────────────────────────────────────────────────────────

POI_DIMENSIONS: list[ScoreDimension] = [
    ScoreDimension(
        key="platform_rating",
        label="平台评分与口碑",
        weight=0.30,
        max_raw=5.0,  # Google rating 0-5
    ),
    ScoreDimension(
        key="review_confidence",
        label="评论量置信度",
        weight=0.20,
        max_raw=10000.0,  # review_count，10000 条视为满分
    ),
    ScoreDimension(
        key="city_popularity",
        label="城市代表性/热度",
        weight=0.20,
        max_raw=100.0,  # 归一化热度分 0-100
    ),
    # R2: theme_match (原 0.20) 和 area_efficiency (原 0.15) 已从 base_quality
    # 移至 context_fit 层（itinerary_fit_scorer.py），不再参与实体固有品质评分。
    # 新增 operational_stability 替代，确保权重和 = 1.0。
    ScoreDimension(
        key="operational_stability",
        label="运营稳定度",
        weight=0.15,
        max_raw=100.0,  # 综合营业稳定性、投诉率、状态变更频率
    ),
    ScoreDimension(
        key="data_freshness",
        label="信息新鲜度",
        weight=0.15,
        max_raw=100.0,
    ),
]

# R2: 已移出到 context_fit 层的维度（保留定义供 itinerary_fit_scorer 使用）
POI_CONTEXT_DIMENSIONS: list[ScoreDimension] = [
    ScoreDimension(
        key="theme_match",
        label="与用户主题匹配度（context_fit 层）",
        weight=0.55,
        max_raw=100.0,
    ),
    ScoreDimension(
        key="area_efficiency",
        label="区域串联效率（itinerary_fit 层）",
        weight=0.45,
        max_raw=100.0,
    ),
]

POI_RISK_RULES: list[RiskRule] = [
    RiskRule(
        key="unstable_hours",
        label="闭馆/营业时间不稳定",
        penalty=20.0,
        condition="opening_hours_json 为空 or 标注 unstable",
    ),
    RiskRule(
        key="high_transport_cost",
        label="交通代价过高",
        penalty=15.0,
        condition="到市中心距离 > 60 min",
    ),
    RiskRule(
        key="seasonal_unlabeled",
        label="强季节性未提示",
        penalty=10.0,
        condition="best_season != 'all' 且无季节提示标签",
    ),
    RiskRule(
        key="homogeneity",
        label="过度同质化",
        penalty=5.0,
        condition="同城市同类型 entity 已推荐 3 个以上",
    ),
]


# ── 酒店评分维度 ──────────────────────────────────────────────────────────────

HOTEL_DIMENSIONS: list[ScoreDimension] = [
    ScoreDimension(
        key="platform_rating",
        label="公共评分与口碑",
        weight=0.20,
        max_raw=5.0,
    ),
    ScoreDimension(
        key="review_confidence",
        label="评论量置信度",
        weight=0.10,
        max_raw=5000.0,
    ),
    ScoreDimension(
        key="transport_convenience",
        label="交通便利度",
        weight=0.20,
        max_raw=100.0,
    ),
    ScoreDimension(
        key="value_for_money",
        label="性价比",
        weight=0.20,
        max_raw=100.0,
    ),
    ScoreDimension(
        key="amenity_coverage",
        label="房型与设施完整度",
        weight=0.15,
        max_raw=100.0,
    ),
    ScoreDimension(
        key="booking_stability",
        label="取消政策/可订稳定性",
        weight=0.15,
        max_raw=100.0,
    ),
]

HOTEL_RISK_RULES: list[RiskRule] = [
    RiskRule(
        key="price_volatility",
        label="动态价格波动大",
        penalty=15.0,
        condition="price_variance_ratio > 0.5",
    ),
    RiskRule(
        key="poor_transport",
        label="交通不便",
        penalty=15.0,
        condition="walking_distance_station_min > 20",
    ),
    RiskRule(
        key="hygiene_noise_complaints",
        label="差评集中于卫生/噪音",
        penalty=20.0,
        condition="负面标签 hygiene_issue 或 noise_issue",
    ),
    RiskRule(
        key="bad_cancellation",
        label="取消政策差",
        penalty=10.0,
        condition="cancellation_policy = 'non_refundable'",
    ),
]


# ── 餐厅评分维度 ──────────────────────────────────────────────────────────────

RESTAURANT_DIMENSIONS: list[ScoreDimension] = [
    ScoreDimension(
        key="platform_rating",
        label="公共评分与口碑",
        weight=0.25,
        max_raw=5.0,
    ),
    ScoreDimension(
        key="review_confidence",
        label="评论量置信度",
        weight=0.10,
        max_raw=3000.0,
    ),
    ScoreDimension(
        key="timeslot_route_fit",
        label="与时段/路线适配度",
        weight=0.20,
        max_raw=100.0,
    ),
    ScoreDimension(
        key="price_match",
        label="价格带匹配",
        weight=0.15,
        max_raw=100.0,
    ),
    ScoreDimension(
        key="reservation_feasibility",
        label="预约/排队可执行性",
        weight=0.15,
        max_raw=100.0,
    ),
    ScoreDimension(
        key="cuisine_diversity",
        label="菜系差异化",
        weight=0.15,
        max_raw=100.0,
    ),
]

RESTAURANT_RISK_RULES: list[RiskRule] = [
    RiskRule(
        key="long_queue_no_alt",
        label="超长排队且无替代",
        penalty=15.0,
        condition="queue_risk = 'extreme' 且无附近同类餐厅",
    ),
    RiskRule(
        key="meal_slot_mismatch",
        label="时段不匹配",
        penalty=10.0,
        condition="推荐早餐时段但仅营业晚市",
    ),
    RiskRule(
        key="price_inflated",
        label="价格虚高",
        penalty=10.0,
        condition="价格带高于用户预算 2 个档次",
    ),
    RiskRule(
        key="unstable_hours",
        label="营业信息不稳",
        penalty=15.0,
        condition="opening_hours_json 为空 or 标注 unstable",
    ),
]


# ── 索引映射：entity_type → 规则 ─────────────────────────────────────────────

DIMENSIONS_BY_TYPE: dict[str, list[ScoreDimension]] = {
    "poi": POI_DIMENSIONS,
    "hotel": HOTEL_DIMENSIONS,
    "restaurant": RESTAURANT_DIMENSIONS,
}

RISK_RULES_BY_TYPE: dict[str, list[RiskRule]] = {
    "poi": POI_RISK_RULES,
    "hotel": HOTEL_RISK_RULES,
    "restaurant": RESTAURANT_RISK_RULES,
}


# ── 数据层加权系数（data_tier 影响置信度） ────────────────────────────────────

DATA_TIER_MULTIPLIER: dict[str, float] = {
    "S": 1.0,   # 顶级数据，满权重
    "A": 0.90,  # 良好数据，轻微折扣
    "B": 0.75,  # 基础数据，信号弱折扣更大
}
