"""
统计特征计算器（Stat Estimator）

从实体的结构化属性中计算部分软规则维度分。
不依赖 AI 调用，纯数值计算，速度快且确定性强。

负责的维度（source_type=STAT）：
  - smoothness          ← 基于区域/交通距离
  - recovery_friendliness ← 基于室内比例/步行量
  - weather_resilience_soft ← 基于室内/室外属性
  - preview_conversion_power ← 派生维度（从其他维度加权计算）
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domains.ranking.soft_rules.estimators.ai_estimator import DimensionEstimate


def compute_stat_dimensions(
    entity: dict[str, Any],
    existing_scores: dict[str, float] | None = None,
) -> dict[str, DimensionEstimate]:
    """
    从实体属性统计计算维度分。

    Args:
        entity: 实体数据字典
        existing_scores: 已有的其他维度分（用于计算派生维度 preview_conversion_power）

    Returns:
        {dimension_id: DimensionEstimate}，只包含 stat 类型的维度
    """
    results: dict[str, DimensionEstimate] = {}

    # ── smoothness（顺滑度） ───────────────────────────────────
    smoothness = _compute_smoothness(entity)
    results["smoothness"] = DimensionEstimate(
        dimension_id="smoothness",
        score=smoothness[0],
        reason=smoothness[1],
        confidence=0.8,
    )

    # ── recovery_friendliness（体力友好度） ─────────────────────
    recovery = _compute_recovery_friendliness(entity)
    results["recovery_friendliness"] = DimensionEstimate(
        dimension_id="recovery_friendliness",
        score=recovery[0],
        reason=recovery[1],
        confidence=0.8,
    )

    # ── weather_resilience_soft（天气适应性） ───────────────────
    weather = _compute_weather_resilience(entity)
    results["weather_resilience_soft"] = DimensionEstimate(
        dimension_id="weather_resilience_soft",
        score=weather[0],
        reason=weather[1],
        confidence=0.9,  # 室内/室外判断很确定
    )

    # ── preview_conversion_power（预览转化力）── 派生维度 ──────
    pcp = _compute_preview_conversion_power(entity, existing_scores)
    results["preview_conversion_power"] = DimensionEstimate(
        dimension_id="preview_conversion_power",
        score=pcp[0],
        reason=pcp[1],
        confidence=0.6,  # 依赖其他维度，置信度较低
    )

    return results


def _compute_smoothness(entity: dict[str, Any]) -> tuple[float, str]:
    """
    顺滑度计算：
    - 基于步行距离到最近车站
    - 基于交通便利度评分（如已有）
    """
    score = 5.0
    reasons = []

    # 步行距离
    walk_min = entity.get("walking_distance_station_min")
    if walk_min is not None:
        if walk_min <= 3:
            score = 9.0
            reasons.append("步行3分钟内到站")
        elif walk_min <= 5:
            score = 8.0
            reasons.append("步行5分钟内到站")
        elif walk_min <= 10:
            score = 7.0
            reasons.append("步行10分钟内到站")
        elif walk_min <= 15:
            score = 5.5
            reasons.append("步行15分钟到站")
        elif walk_min <= 20:
            score = 4.0
            reasons.append("步行20分钟到站，略远")
        else:
            score = 2.5
            reasons.append(f"步行{walk_min}分钟到站，交通不便")

    # 交通便利度评分（如有）
    transport_score = entity.get("transport_convenience_score")
    if transport_score is not None and walk_min is None:
        score = transport_score / 10.0  # 0-100 → 0-10
        reasons.append(f"交通便利度 {transport_score}")

    # 区域类型加成
    area_type = entity.get("area_type", "")
    if area_type in ("商业", "central", "downtown"):
        score = min(10.0, score + 0.5)
        reasons.append("位于核心商业区")

    reason = "；".join(reasons) if reasons else "基于默认评估"
    return round(max(0.0, min(10.0, score)), 1), reason


def _compute_recovery_friendliness(entity: dict[str, Any]) -> tuple[float, str]:
    """
    体力友好度计算：
    - 室内 → 高分
    - 有座位/休息区 → 加分
    - 预计步行量大 → 低分
    """
    score = 5.0
    reasons = []

    is_indoor = entity.get("is_indoor")
    entity_type = entity.get("entity_type", "poi")

    if entity_type == "restaurant":
        score = 8.0
        reasons.append("餐厅自带坐下休息")
    elif entity_type == "hotel":
        score = 9.0
        reasons.append("酒店是最好的休息场所")
    elif is_indoor is True:
        score = 7.5
        reasons.append("室内场所，体力消耗低")
    elif is_indoor is False:
        score = 4.0
        reasons.append("室外场所，需要走路")

    # 标签加成
    tags = set(entity.get("tags") or entity.get("types") or [])
    relaxing_tags = {"spa", "onsen", "温泉", "cafe", "museum", "博物馆", "美術館"}
    tiring_tags = {"hiking", "mountain", "garden", "park", "shrine_complex"}

    if tags & relaxing_tags:
        score = min(10.0, score + 1.5)
        reasons.append("有休闲/放松属性")
    if tags & tiring_tags:
        score = max(0.0, score - 1.5)
        reasons.append("需要较多步行/爬坡")

    # 预计停留时间（长停留 = 有坐下的时间）
    stay_min = entity.get("typical_stay_minutes")
    if stay_min and stay_min >= 90:
        score = min(10.0, score + 0.5)
        reasons.append(f"停留约{stay_min}分钟，有休息时间")

    reason = "；".join(reasons) if reasons else "基于默认评估"
    return round(max(0.0, min(10.0, score)), 1), reason


def _compute_weather_resilience(entity: dict[str, Any]) -> tuple[float, str]:
    """
    天气适应性计算：
    - 纯室内 → 10 分
    - 有遮蔽/室内备选 → 7 分
    - 纯室外 → 3 分
    """
    is_indoor = entity.get("is_indoor")
    entity_type = entity.get("entity_type", "poi")

    if entity_type in ("restaurant", "hotel"):
        return 9.5, "餐厅/酒店不受天气影响"

    if is_indoor is True:
        return 9.0, "室内场所，天气无影响"

    # 检查标签判断是否有遮蔽
    tags = set(entity.get("tags") or entity.get("types") or [])
    indoor_tags = {"museum", "shopping_mall", "department_store", "station",
                   "underground", "aquarium", "博物馆", "美術館", "商场"}
    partial_tags = {"shrine", "temple", "arcade", "covered_market"}

    if tags & indoor_tags:
        return 9.0, "室内类场所"
    if tags & partial_tags:
        return 6.5, "部分有遮蔽"

    if is_indoor is False:
        return 3.0, "纯室外场所，受天气影响大"

    # 无法判断时给中间分
    return 5.0, "天气适应性未知"


def _compute_preview_conversion_power(
    entity: dict[str, Any],
    existing_scores: dict[str, float] | None = None,
) -> tuple[float, str]:
    """
    预览转化力（派生维度）：
      = 0.4 × shareability + 0.3 × professional_judgement_feel + 0.3 × memory_point

    如果依赖的维度分还没算出来，使用实体属性估算。
    """
    if existing_scores:
        share = existing_scores.get("shareability", 5.0)
        prof = existing_scores.get("professional_judgement_feel", 5.0)
        memory = existing_scores.get("memory_point", 5.0)

        score = 0.4 * share + 0.3 * prof + 0.3 * memory
        return round(score, 1), f"派生：share={share} × 0.4 + prof={prof} × 0.3 + memory={memory} × 0.3"

    # Fallback：基于实体属性简单估算
    score = 5.0
    reasons = []

    # 有图片 → 视觉吸引力
    has_image = entity.get("image_url") or entity.get("photo_reference")
    if has_image:
        score += 1.5
        reasons.append("有图片")

    # 有评分数据 → 证据化
    google_rating = entity.get("google_rating")
    tabelog = entity.get("tabelog_score")
    if google_rating or tabelog:
        score += 1.0
        reasons.append("有评分证据")

    # 评论量多 → 知名度
    review_count = entity.get("google_review_count", 0)
    if review_count and review_count > 1000:
        score += 0.5
        reasons.append("评论量大")

    reason = "；".join(reasons) if reasons else "基于属性估算"
    return round(max(0.0, min(10.0, score)), 1), reason
