"""
单元测试：评分引擎 scorer.py

覆盖场景：
  1. POI 满分路径（S tier，高评分，无风险）
  2. POI 风险扣分（无营业时间 + 强季节性未标注）
  3. 酒店评分路径（Booking 评分折算 + 步行距离风险）
  4. 餐厅评分路径（Tabelog 评分 + 排队风险）
  5. editorial_boost 正向/负向 + 边界 clamp
  6. boost 越界自动 clamp（不抛异常）
  7. data_tier 折扣验证（S > A > B）
  8. 无信号默认值路径（全部使用默认值，应返回合理中间分）
  9. score_breakdown 结构完整性验证
  10. unsupported entity_type 应抛 ValueError
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta

from app.domains.ranking.scorer import (
    EntitySignals,
    ScoreResult,
    apply_editorial_boost,
    compute_base_score,
)
from app.domains.ranking.rules import (
    EDITORIAL_BOOST_MAX,
    EDITORIAL_BOOST_MIN,
    SCORE_MAX,
    SCORE_MIN,
    SCORE_VERSION,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _recent_ts() -> datetime:
    """返回 7 天前的 UTC 时间（新鲜度满分区间）"""
    return datetime.now(tz=timezone.utc) - timedelta(days=7)


def _stale_ts() -> datetime:
    """返回 400 天前的 UTC 时间（新鲜度最低分）"""
    return datetime.now(tz=timezone.utc) - timedelta(days=400)


# ─────────────────────────────────────────────────────────────────────────────
# 1. POI 满分路径
# ─────────────────────────────────────────────────────────────────────────────

def test_poi_high_quality_score_in_range():
    """高质量 POI（S tier, 高评分, 无风险）base_score 应在 70-100 之间。"""
    signals = EntitySignals(
        entity_type="poi",
        data_tier="S",
        google_rating=4.8,
        google_review_count=5000,
        has_opening_hours=True,
        best_season="all",
        city_popularity_score=90.0,
        area_efficiency_score=85.0,
        theme_match_score=80.0,
        updated_at=_recent_ts(),
    )
    result = compute_base_score(signals)

    assert isinstance(result, ScoreResult)
    assert SCORE_MIN <= result.base_score <= SCORE_MAX
    assert result.base_score >= 70.0, f"Expected >= 70, got {result.base_score}"


# ─────────────────────────────────────────────────────────────────────────────
# 2. POI 风险扣分路径
# ─────────────────────────────────────────────────────────────────────────────

def test_poi_risk_penalties_reduce_score():
    """无营业时间 + 强季节性未标注，应比同等无风险 POI 分数更低。"""
    base_signals = EntitySignals(
        entity_type="poi",
        data_tier="A",
        google_rating=4.5,
        google_review_count=1000,
        has_opening_hours=True,
        best_season="all",
        updated_at=_recent_ts(),
    )
    risky_signals = EntitySignals(
        entity_type="poi",
        data_tier="A",
        google_rating=4.5,
        google_review_count=1000,
        has_opening_hours=False,       # → unstable_hours risk (-20)
        best_season="spring",          # 强季节性
        has_seasonal_tags=False,        # 未标注 → seasonal_unlabeled risk (-10)
        updated_at=_recent_ts(),
    )
    result_base = compute_base_score(base_signals)
    result_risky = compute_base_score(risky_signals)

    assert result_risky.base_score < result_base.base_score, (
        f"Risk should reduce score: {result_risky.base_score} >= {result_base.base_score}"
    )


def test_poi_risk_breakdown_contains_triggered_risks():
    """score_breakdown 中 unstable_hours 应标记 triggered=True。"""
    signals = EntitySignals(
        entity_type="poi",
        data_tier="B",
        has_opening_hours=False,
        best_season="all",
        updated_at=_recent_ts(),
    )
    result = compute_base_score(signals)
    risk_details = result.score_breakdown["risk_details"]

    assert risk_details["unstable_hours"]["triggered"] is True
    assert risk_details["unstable_hours"]["penalty"] == 20.0


def test_poi_homogeneity_risk_triggered():
    """homogeneity_count >= 3 时应触发同质化风险。"""
    signals = EntitySignals(
        entity_type="poi",
        data_tier="B",
        homogeneity_count=3,
    )
    result = compute_base_score(signals)
    assert result.score_breakdown["risk_details"]["homogeneity"]["triggered"] is True


# ─────────────────────────────────────────────────────────────────────────────
# 3. 酒店评分路径
# ─────────────────────────────────────────────────────────────────────────────

def test_hotel_booking_score_fallback():
    """无 google_rating 时，酒店应使用 booking_score（0-10）折算。"""
    signals = EntitySignals(
        entity_type="hotel",
        data_tier="A",
        google_rating=None,
        booking_score=9.0,      # → 9/2 = 4.5 → 90 norm
        transport_convenience_score=80.0,
        value_for_money_score=75.0,
        amenity_coverage_score=70.0,
        booking_stability_score=80.0,
        updated_at=_recent_ts(),
    )
    result = compute_base_score(signals)

    assert SCORE_MIN <= result.base_score <= SCORE_MAX
    # platform_rating 维度应该较高
    platform_norm = result.score_breakdown["dimensions"]["platform_rating"]["norm"]
    assert platform_norm >= 85.0, f"Expected platform_norm >= 85, got {platform_norm}"


def test_hotel_poor_transport_risk():
    """步行时间 > 20 分钟应触发 poor_transport 风险。"""
    signals = EntitySignals(
        entity_type="hotel",
        data_tier="A",
        google_rating=4.0,
        walking_distance_station_min=25,   # > 20 → 触发
    )
    result = compute_base_score(signals)
    assert result.score_breakdown["risk_details"]["poor_transport"]["triggered"] is True
    assert result.score_breakdown["risk_details"]["poor_transport"]["penalty"] == 15.0


def test_hotel_transport_ok_no_risk():
    """步行时间 <= 20 分钟不应触发 poor_transport 风险。"""
    signals = EntitySignals(
        entity_type="hotel",
        data_tier="A",
        google_rating=4.0,
        walking_distance_station_min=10,   # <= 20 → 不触发
    )
    result = compute_base_score(signals)
    assert result.score_breakdown["risk_details"]["poor_transport"]["triggered"] is False


# ─────────────────────────────────────────────────────────────────────────────
# 4. 餐厅评分路径
# ─────────────────────────────────────────────────────────────────────────────

def test_restaurant_tabelog_rating():
    """餐厅使用 tabelog_score（0-5）时评分应正常归一化。"""
    signals = EntitySignals(
        entity_type="restaurant",
        data_tier="A",
        google_rating=None,
        tabelog_score=4.0,   # → 80 norm
        has_opening_hours=True,
        updated_at=_recent_ts(),
    )
    result = compute_base_score(signals)
    assert SCORE_MIN <= result.base_score <= SCORE_MAX


def test_restaurant_extreme_queue_risk():
    """has_extreme_queue=True 应触发 long_queue_no_alt 风险。"""
    signals = EntitySignals(
        entity_type="restaurant",
        data_tier="B",
        has_extreme_queue=True,
        has_opening_hours=True,
    )
    result = compute_base_score(signals)
    assert result.score_breakdown["risk_details"]["long_queue_no_alt"]["triggered"] is True


# ─────────────────────────────────────────────────────────────────────────────
# 5. editorial_boost 正向/负向
# ─────────────────────────────────────────────────────────────────────────────

def test_editorial_boost_positive():
    """正向 boost 应使 final_score > base_score。"""
    signals = EntitySignals(entity_type="poi", data_tier="A", editorial_boost=5)
    result = compute_base_score(signals)
    assert result.final_score == result.base_score + 5 or result.final_score == SCORE_MAX


def test_editorial_boost_negative():
    """负向 boost 应使 final_score < base_score（除非 base 已经是 0）。"""
    signals = EntitySignals(
        entity_type="poi",
        data_tier="A",
        google_rating=4.5,
        editorial_boost=-5,
        updated_at=_recent_ts(),
    )
    result = compute_base_score(signals)
    # final_score 应 <= base_score
    assert result.final_score <= result.base_score


def test_apply_editorial_boost_clamp_to_100():
    """base_score=98, boost=+5 → final_score 应 clamp 到 100。"""
    final = apply_editorial_boost(98.0, 5)
    assert final == 100.0


def test_apply_editorial_boost_clamp_to_0():
    """base_score=2, boost=-5 → final_score 应 clamp 到 0。"""
    final = apply_editorial_boost(2.0, -5)
    assert final == 0.0


def test_apply_editorial_boost_zero():
    """boost=0 时 final_score 应等于 base_score。"""
    for score in [0.0, 50.0, 100.0]:
        assert apply_editorial_boost(score, 0) == score


# ─────────────────────────────────────────────────────────────────────────────
# 6. boost 越界自动 clamp（不抛异常）
# ─────────────────────────────────────────────────────────────────────────────

def test_boost_out_of_range_clamped():
    """boost 超出 -8~+8 范围时应被 clamp 到边界，不抛异常。"""
    # 超大正值等价于 +8
    final_big = apply_editorial_boost(50.0, 100)
    final_max = apply_editorial_boost(50.0, EDITORIAL_BOOST_MAX)
    assert final_big == final_max

    # 超大负值等价于 -8
    final_neg = apply_editorial_boost(50.0, -100)
    final_min = apply_editorial_boost(50.0, EDITORIAL_BOOST_MIN)
    assert final_neg == final_min


# ─────────────────────────────────────────────────────────────────────────────
# 7. data_tier 折扣验证
# ─────────────────────────────────────────────────────────────────────────────

def test_data_tier_multiplier_s_greater_than_b():
    """相同信号下，S tier 的 base_score 应 >= A tier >= B tier。"""
    common = dict(
        entity_type="poi",
        google_rating=4.5,
        google_review_count=2000,
        has_opening_hours=True,
        best_season="all",
        city_popularity_score=70.0,
        area_efficiency_score=70.0,
        theme_match_score=70.0,
        updated_at=_recent_ts(),
    )
    result_s = compute_base_score(EntitySignals(**common, data_tier="S"))
    result_a = compute_base_score(EntitySignals(**common, data_tier="A"))
    result_b = compute_base_score(EntitySignals(**common, data_tier="B"))

    assert result_s.base_score >= result_a.base_score, (
        f"S({result_s.base_score}) should >= A({result_a.base_score})"
    )
    assert result_a.base_score >= result_b.base_score, (
        f"A({result_a.base_score}) should >= B({result_b.base_score})"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 8. 无信号默认值路径
# ─────────────────────────────────────────────────────────────────────────────

def test_default_signals_poi():
    """全默认 POI 信号应返回 0-100 之间的合理分数，不崩溃。"""
    result = compute_base_score(EntitySignals(entity_type="poi"))
    assert SCORE_MIN <= result.base_score <= SCORE_MAX


def test_default_signals_hotel():
    """全默认 Hotel 信号应正常计算。"""
    result = compute_base_score(EntitySignals(entity_type="hotel"))
    assert SCORE_MIN <= result.base_score <= SCORE_MAX


def test_default_signals_restaurant():
    """全默认 Restaurant 信号应正常计算。"""
    result = compute_base_score(EntitySignals(entity_type="restaurant"))
    assert SCORE_MIN <= result.base_score <= SCORE_MAX


# ─────────────────────────────────────────────────────────────────────────────
# 9. score_breakdown 结构完整性
# ─────────────────────────────────────────────────────────────────────────────

def test_score_breakdown_structure_poi():
    """POI score_breakdown 应包含 dimensions / risk_details / tier_multiplier / score_version 等键。"""
    result = compute_base_score(EntitySignals(entity_type="poi", data_tier="A"))
    bd = result.score_breakdown

    assert "dimensions" in bd
    assert "risk_details" in bd
    assert "tier_multiplier" in bd
    assert "system_score_raw" in bd
    assert "risk_penalty" in bd
    assert "score_version" in bd
    assert bd["score_version"] == SCORE_VERSION

    # 每个维度明细应有 raw / norm / weighted
    for dim_key, dim_val in bd["dimensions"].items():
        assert "raw" in dim_val, f"Dimension {dim_key} missing 'raw'"
        assert "norm" in dim_val, f"Dimension {dim_key} missing 'norm'"
        assert "weighted" in dim_val, f"Dimension {dim_key} missing 'weighted'"


def test_score_result_version():
    """ScoreResult.score_version 应等于 SCORE_VERSION 常量。"""
    result = compute_base_score(EntitySignals(entity_type="hotel"))
    assert result.score_version == SCORE_VERSION


# ─────────────────────────────────────────────────────────────────────────────
# 10. unsupported entity_type
# ─────────────────────────────────────────────────────────────────────────────

def test_unsupported_entity_type_raises():
    """不支持的 entity_type 应抛出 ValueError。"""
    signals = EntitySignals(entity_type="activity")  # 不存在的类型
    with pytest.raises(ValueError, match="Unsupported entity_type"):
        compute_base_score(signals)


# ─────────────────────────────────────────────────────────────────────────────
# 11. 新鲜度边界
# ─────────────────────────────────────────────────────────────────────────────

def test_stale_data_lower_score_than_fresh():
    """过时数据（400天前）的分数应低于新鲜数据（7天前）。"""
    fresh = EntitySignals(
        entity_type="poi",
        data_tier="A",
        google_rating=4.0,
        has_opening_hours=True,
        best_season="all",
        updated_at=_recent_ts(),
    )
    stale = EntitySignals(
        entity_type="poi",
        data_tier="A",
        google_rating=4.0,
        has_opening_hours=True,
        best_season="all",
        updated_at=_stale_ts(),
    )
    result_fresh = compute_base_score(fresh)
    result_stale = compute_base_score(stale)

    assert result_fresh.base_score > result_stale.base_score, (
        f"Fresh({result_fresh.base_score}) should > Stale({result_stale.base_score})"
    )
