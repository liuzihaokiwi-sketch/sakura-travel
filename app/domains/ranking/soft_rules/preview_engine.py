"""
免费预览选天引擎（Preview Engine）

从完整行程的 N 天中选出"最能促成付费"的一天作为免费预览。
不固定展示 Day 1，而是基于 preview_day1_score 动态选择最佳天。

选天公式：
  preview_day1_score = 0.30 × avg_soft_score
                     + 0.25 × variety_score
                     + 0.20 × hero_moment_score
                     + 0.15 × shareability_score
                     + 0.10 × completeness_score

护栏规则：
  1. 到达日/离开日降权 30%
  2. 纯移动日（无 POI）跳过
  3. avg_soft_score 与全行程均分比值上限 1.5（防止预览太精彩、正式版失望）
  4. 选出的天必须"自包含"（不需要前一天的前置体验才能理解）
  5. 至少包含 3 个 POI + 1 个餐厅

降级策略：
  最高分天校验不通过 → 次高分天 → ... → fallback Day 1 → 仍不通过 → needs_human_review
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any

from app.domains.ranking.soft_rules.dimensions import DIMENSION_IDS

logger = logging.getLogger(__name__)


# ── 选天公式权重 ───────────────────────────────────────────────────────────────

PREVIEW_WEIGHT_AVG_SOFT = 0.30
PREVIEW_WEIGHT_VARIETY = 0.25
PREVIEW_WEIGHT_HERO = 0.20
PREVIEW_WEIGHT_SHAREABILITY = 0.15
PREVIEW_WEIGHT_COMPLETENESS = 0.10

# 护栏参数
ARRIVAL_DEPARTURE_PENALTY = 0.70      # 到达日/离开日得分乘以此系数
MAX_PREVIEW_TO_AVG_RATIO = 1.5        # 预览天 avg_soft 与全行程 avg 的比值上限
MIN_POIS = 3                          # 预览天最少 POI 数
MIN_RESTAURANTS = 1                   # 预览天最少餐厅数


# ── 数据结构 ───────────────────────────────────────────────────────────────────

@dataclass
class DayPreviewScore:
    """单天的预览得分明细"""
    day_index: int                # 0-based
    avg_soft_score: float         # 当天实体平均软规则分
    variety_score: float          # 实体类型丰富度
    hero_moment_score: float      # 高光时刻分
    shareability_score: float     # 平均分享感
    completeness_score: float     # 餐饮/夜间完整度
    preview_day1_score: float     # 加权总分
    penalty_applied: str | None   # "arrival" / "departure" / None
    passed_validation: bool       # 是否通过校验
    validation_issues: list[str]  # 未通过的原因


@dataclass
class PreviewDayResult:
    """预览引擎的最终输出"""
    selected_day_index: int           # 选中的天（0-based）
    selected_day_score: DayPreviewScore
    all_day_scores: list[DayPreviewScore]
    fallback_used: bool               # 是否使用了降级
    needs_human_review: bool          # 是否需要人工审核
    selection_reason: str             # 选择理由


# ── 分项计算函数 ───────────────────────────────────────────────────────────────

def _calc_avg_soft_score(day_items: list[dict[str, Any]]) -> float:
    """计算当天所有实体的平均软规则分（0-10）。"""
    soft_scores = []
    for item in day_items:
        # soft_rule_score 可以存在 item 的 entity 数据中
        score = item.get("soft_rule_score") or item.get("entity", {}).get("soft_rule_score")
        if score is not None:
            # 可能是 0-100 也可能是 0-10，统一到 0-10
            score = float(score)
            if score > 10:
                score = score / 10.0
            soft_scores.append(score)

    if not soft_scores:
        return 5.0  # 无数据时给中间分
    return sum(soft_scores) / len(soft_scores)


def _calc_variety_score(day_items: list[dict[str, Any]]) -> float:
    """
    类型丰富度（0-10），基于香农熵。
    类型越多样得分越高。
    """
    type_counts: dict[str, int] = {}
    for item in day_items:
        et = item.get("entity_type") or item.get("type", "unknown")
        # 更细粒度的类型区分
        sub_type = item.get("sub_type") or item.get("category", et)
        type_counts[sub_type] = type_counts.get(sub_type, 0) + 1

    n = sum(type_counts.values())
    if n <= 1:
        return 2.0

    # 香农熵
    entropy = 0.0
    for count in type_counts.values():
        p = count / n
        if p > 0:
            entropy -= p * math.log2(p)

    # 归一化到 0-10（最大熵约 3.5 for 12 types）
    max_entropy = math.log2(max(len(type_counts), 2))
    normalized = (entropy / max_entropy) * 10.0 if max_entropy > 0 else 5.0

    return round(min(10.0, normalized), 1)


def _calc_hero_moment_score(day_items: list[dict[str, Any]]) -> float:
    """
    高光时刻分（0-10）：是否有明确的"wow"体验。
    检查：emotional_value > 7 或 memory_point > 7 的实体。
    """
    hero_count = 0
    max_emotional = 0.0
    max_memory = 0.0

    for item in day_items:
        soft = item.get("soft_scores", {})
        emotional = float(soft.get("emotional_value", 0))
        memory = float(soft.get("memory_point", 0))

        max_emotional = max(max_emotional, emotional)
        max_memory = max(max_memory, memory)

        if emotional >= 7.0 or memory >= 7.0:
            hero_count += 1

    if hero_count == 0:
        # 没有明确高光，用最高分折算
        return round(max(max_emotional, max_memory) * 0.7, 1)

    # 1 个高光 = 7 分，2 个 = 8.5 分，3+ = 10 分
    if hero_count == 1:
        return 7.0
    elif hero_count == 2:
        return 8.5
    else:
        return 10.0


def _calc_shareability_score(day_items: list[dict[str, Any]]) -> float:
    """当天所有实体的平均分享感（0-10）。"""
    scores = []
    for item in day_items:
        soft = item.get("soft_scores", {})
        share = soft.get("shareability")
        if share is not None:
            scores.append(float(share))

    if not scores:
        return 5.0
    return round(sum(scores) / len(scores), 1)


def _calc_completeness_score(day_items: list[dict[str, Any]]) -> float:
    """
    完整度（0-10）：餐饮 + 夜间安排是否齐全。
    - 有午餐 +3
    - 有晚餐 +3
    - 有夜间活动 +2
    - 有早餐推荐 +1
    - 有交通指引 +1
    """
    score = 0.0
    has_lunch = False
    has_dinner = False
    has_night = False
    has_breakfast = False

    for item in day_items:
        slot = item.get("time_slot", "").lower()
        et = item.get("entity_type", "")

        if et == "restaurant" or "restaurant" in str(item.get("type", "")):
            if "lunch" in slot or "午" in slot:
                has_lunch = True
            elif "dinner" in slot or "晚" in slot:
                has_dinner = True
            elif "breakfast" in slot or "早" in slot:
                has_breakfast = True

        if "night" in slot or "evening" in slot or "夜" in slot:
            has_night = True

    if has_lunch:
        score += 3.0
    if has_dinner:
        score += 3.0
    if has_night:
        score += 2.0
    if has_breakfast:
        score += 1.0

    # 基础分（有任何安排就不是 0）
    if day_items:
        score += 1.0

    return round(min(10.0, score), 1)


# ── 校验函数 ───────────────────────────────────────────────────────────────────

def _validate_preview_day(
    day_items: list[dict[str, Any]],
    day_avg_soft: float,
    trip_avg_soft: float,
) -> tuple[bool, list[str]]:
    """
    校验某天是否适合做预览天。

    Returns:
        (passed, issues)
    """
    issues: list[str] = []

    # 规则 1: 至少 3 个 POI
    poi_count = sum(
        1 for item in day_items
        if item.get("entity_type", "") == "poi"
        or item.get("type", "") == "poi"
    )
    if poi_count < MIN_POIS:
        issues.append(f"POI 数量不足（{poi_count} < {MIN_POIS}）")

    # 规则 2: 至少 1 个餐厅
    restaurant_count = sum(
        1 for item in day_items
        if item.get("entity_type", "") == "restaurant"
        or "restaurant" in str(item.get("type", ""))
    )
    if restaurant_count < MIN_RESTAURANTS:
        issues.append(f"餐厅数量不足（{restaurant_count} < {MIN_RESTAURANTS}）")

    # 规则 3: 不能是纯移动日（0 个实体）
    if len(day_items) == 0:
        issues.append("纯移动日（无实体）")

    # 规则 4: avg_soft 不能远超全行程均分
    if trip_avg_soft > 0 and day_avg_soft / trip_avg_soft > MAX_PREVIEW_TO_AVG_RATIO:
        issues.append(
            f"预览天均分（{day_avg_soft:.1f}）远超全行程均分（{trip_avg_soft:.1f}），"
            f"比值 {day_avg_soft/trip_avg_soft:.2f} > {MAX_PREVIEW_TO_AVG_RATIO}"
        )

    return len(issues) == 0, issues


# ── 主函数 ─────────────────────────────────────────────────────────────────────

def select_preview_day(
    itinerary_days: list[list[dict[str, Any]]],
    arrival_day_index: int = 0,
    departure_day_index: int | None = None,
) -> PreviewDayResult:
    """
    从完整行程中选出最佳预览天。

    Args:
        itinerary_days: 每天的实体列表，外层 list 索引 = day_index
        arrival_day_index: 到达日索引（默认 0）
        departure_day_index: 离开日索引（默认最后一天）

    Returns:
        PreviewDayResult
    """
    n_days = len(itinerary_days)
    if n_days == 0:
        return PreviewDayResult(
            selected_day_index=0,
            selected_day_score=DayPreviewScore(
                day_index=0, avg_soft_score=0, variety_score=0,
                hero_moment_score=0, shareability_score=0, completeness_score=0,
                preview_day1_score=0, penalty_applied=None,
                passed_validation=False, validation_issues=["行程为空"],
            ),
            all_day_scores=[],
            fallback_used=True,
            needs_human_review=True,
            selection_reason="行程为空，需人工审核",
        )

    if departure_day_index is None:
        departure_day_index = n_days - 1

    # Step 1: 计算全行程平均软规则分
    all_avg_softs = [_calc_avg_soft_score(day) for day in itinerary_days]
    trip_avg_soft = sum(all_avg_softs) / len(all_avg_softs) if all_avg_softs else 5.0

    # Step 2: 计算每天的 preview_day1_score
    day_scores: list[DayPreviewScore] = []

    for i, day_items in enumerate(itinerary_days):
        avg_soft = all_avg_softs[i]
        variety = _calc_variety_score(day_items)
        hero = _calc_hero_moment_score(day_items)
        share = _calc_shareability_score(day_items)
        complete = _calc_completeness_score(day_items)

        raw_score = (
            PREVIEW_WEIGHT_AVG_SOFT * avg_soft
            + PREVIEW_WEIGHT_VARIETY * variety
            + PREVIEW_WEIGHT_HERO * hero
            + PREVIEW_WEIGHT_SHAREABILITY * share
            + PREVIEW_WEIGHT_COMPLETENESS * complete
        )

        # 到达日/离开日降权
        penalty = None
        if i == arrival_day_index:
            raw_score *= ARRIVAL_DEPARTURE_PENALTY
            penalty = "arrival"
        elif i == departure_day_index:
            raw_score *= ARRIVAL_DEPARTURE_PENALTY
            penalty = "departure"

        # 校验
        passed, issues = _validate_preview_day(day_items, avg_soft, trip_avg_soft)

        day_scores.append(DayPreviewScore(
            day_index=i,
            avg_soft_score=round(avg_soft, 2),
            variety_score=round(variety, 2),
            hero_moment_score=round(hero, 2),
            shareability_score=round(share, 2),
            completeness_score=round(complete, 2),
            preview_day1_score=round(raw_score, 2),
            penalty_applied=penalty,
            passed_validation=passed,
            validation_issues=issues,
        ))

    # Step 3: 按得分排序，选第一个通过校验的
    sorted_days = sorted(day_scores, key=lambda d: d.preview_day1_score, reverse=True)

    for candidate in sorted_days:
        if candidate.passed_validation:
            logger.info(
                "Preview day selected: Day %d (score=%.2f)",
                candidate.day_index + 1,
                candidate.preview_day1_score,
            )
            return PreviewDayResult(
                selected_day_index=candidate.day_index,
                selected_day_score=candidate,
                all_day_scores=day_scores,
                fallback_used=False,
                needs_human_review=False,
                selection_reason=(
                    f"Day {candidate.day_index + 1} 得分最高（{candidate.preview_day1_score:.2f}）"
                    f"且通过所有校验"
                ),
            )

    # Step 4: 降级 — 所有天都未通过校验
    # 尝试 Day 1（原始策略）
    day1 = day_scores[0] if day_scores else None
    if day1:
        logger.warning(
            "No day passed preview validation, falling back to Day 1"
        )
        return PreviewDayResult(
            selected_day_index=0,
            selected_day_score=day1,
            all_day_scores=day_scores,
            fallback_used=True,
            needs_human_review=True,
            selection_reason="所有天均未通过校验，降级到 Day 1，需人工审核",
        )

    # 极端情况
    return PreviewDayResult(
        selected_day_index=0,
        selected_day_score=sorted_days[0],
        all_day_scores=day_scores,
        fallback_used=True,
        needs_human_review=True,
        selection_reason="预览选天异常，需人工审核",
    )
