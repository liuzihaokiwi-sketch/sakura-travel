"""
自助微调候选排序引擎（Swap Engine）

当用户点击"换一个"时，为目标实体推荐 3-5 个替换候选。
候选排序基于 swap_score，考虑四个维度：
  - context_fit（场景适配度）
  - soft_rule_score（软规则分）
  - slot_compatibility（时间/位置/类型兼容性）
  - differentiation（与被替换实体的差异度）

核心原则：
  1. 替换后整体行程不能"变差"——itinerary_soft_score 跌幅 < 15%
  2. 候选必须满足硬约束（营业时间/区域/类型）
  3. 推荐有差异化的选项（不推荐太相似的）
  4. 保底机制：如果候选池不足 3 个，放宽约束（跨区域）
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.domains.ranking.soft_rules.dimensions import DIMENSION_IDS

logger = logging.getLogger(__name__)


# ── Swap Score 公式权重 ────────────────────────────────────────────────────────

SWAP_WEIGHT_CONTEXT_FIT = 0.40
SWAP_WEIGHT_SOFT_RULE = 0.25
SWAP_WEIGHT_SLOT_COMPAT = 0.20
SWAP_WEIGHT_DIFFERENTIATION = 0.15

# 跌幅阈值
IMPACT_THRESHOLD_SAFE = 0.05       # < 5% → green，无提示
IMPACT_THRESHOLD_WARNING = 0.15    # 5-15% → yellow，提示但允许
IMPACT_THRESHOLD_BLOCK = 0.25      # > 25% → red，不推荐（但不强制阻止）

# 候选池参数
MIN_CANDIDATES = 3
MAX_CANDIDATES = 5
RELAXED_AREA_SEARCH = True  # 候选不足时是否跨区域搜索


# ── 数据结构 ───────────────────────────────────────────────────────────────────

@dataclass
class SwapCandidate:
    """单个替换候选"""
    entity_id: str
    entity_type: str
    name: str
    name_zh: str | None
    area_name: str | None
    swap_score: float               # 0-10
    context_fit: float              # 0-10
    soft_rule_score: float          # 0-10（实体级软规则均分）
    slot_compatibility: float       # 0-10
    differentiation: float          # 0-10
    swap_reason: str                # 一句话推荐理由
    impact_level: str               # "green" / "yellow" / "red"
    estimated_score_change: float   # 替换后行程分预估变化百分比


@dataclass
class SwapResult:
    """Swap Engine 的输出"""
    target_entity_id: str           # 被替换的实体 ID
    candidates: list[SwapCandidate]
    pool_size: int                  # 原始候选池大小
    relaxed_search: bool            # 是否启用了放宽搜索
    message: str                    # 面向用户的提示


@dataclass
class SwapImpact:
    """替换影响评估"""
    original_score: float           # 替换前行程当天分
    new_score: float                # 替换后行程当天分
    change_pct: float               # 变化百分比（正=变好，负=变差）
    impact_level: str               # "green" / "yellow" / "red"
    affected_dimensions: list[str]  # 受影响最大的维度
    message: str                    # 面向用户的提示


# ── 分项计算 ───────────────────────────────────────────────────────────────────

def _calc_context_fit(
    candidate: dict[str, Any],
    original: dict[str, Any],
    time_slot: str,
) -> tuple[float, str]:
    """
    场景适配度：候选实体和原实体在同一使用场景下的匹配度。
    """
    score = 5.0
    reasons = []

    # 同类型加分
    if candidate.get("entity_type") == original.get("entity_type"):
        score += 2.0
        reasons.append("同类型")

    # 同区域加分
    if candidate.get("area_code") == original.get("area_code"):
        score += 1.5
        reasons.append("同区域")
    elif candidate.get("city_code") == original.get("city_code"):
        score += 0.5
        reasons.append("同城市")

    # 价格带匹配
    c_price = candidate.get("price_level", 2)
    o_price = original.get("price_level", 2)
    if c_price and o_price:
        diff = abs(int(c_price) - int(o_price))
        if diff == 0:
            score += 1.0
            reasons.append("价格带一致")
        elif diff == 1:
            score += 0.5

    # 时段匹配
    c_slots = set(candidate.get("valid_time_slots", []))
    if time_slot and (time_slot in c_slots or not c_slots):
        score += 0.5
        reasons.append(f"适合{time_slot}时段")

    reason = "；".join(reasons) if reasons else "基于基础匹配"
    return round(max(0.0, min(10.0, score)), 1), reason


def _calc_slot_compatibility(
    candidate: dict[str, Any],
    time_slot: str,
    prev_item_area: str | None,
    next_item_area: str | None,
) -> tuple[float, str]:
    """
    时间/位置/类型兼容性。
    """
    score = 5.0
    reasons = []

    # 营业时间兼容
    c_slots = set(candidate.get("valid_time_slots", []))
    if c_slots and time_slot:
        if time_slot in c_slots:
            score += 2.0
            reasons.append("营业时间匹配")
        else:
            score -= 3.0
            reasons.append("营业时间不匹配")

    # 与前后行程的区域连贯性
    c_area = candidate.get("area_code", "")
    if prev_item_area and c_area == prev_item_area:
        score += 1.5
        reasons.append("与前项同区域")
    if next_item_area and c_area == next_item_area:
        score += 1.5
        reasons.append("与后项同区域")

    # 步行距离到最近车站
    walk = candidate.get("walking_distance_station_min")
    if walk is not None and walk <= 5:
        score += 0.5
        reasons.append("交通便利")

    reason = "；".join(reasons) if reasons else "基于基础兼容性"
    return round(max(0.0, min(10.0, score)), 1), reason


def _calc_differentiation(
    candidate: dict[str, Any],
    original: dict[str, Any],
) -> tuple[float, str]:
    """
    差异度：候选和被替换实体的差异有多大。
    差异太小 → 换了等于没换；差异太大 → 可能不合适。
    最佳差异度在 4-7 分。
    """
    # 标签重合度
    c_tags = set(candidate.get("tags") or [])
    o_tags = set(original.get("tags") or [])

    if c_tags and o_tags:
        overlap = len(c_tags & o_tags) / len(c_tags | o_tags)
        # overlap 越低 → 差异越大
        diff_score = (1 - overlap) * 10.0
    else:
        diff_score = 5.0

    # 极端差异惩罚（太不同了可能不合适）
    if diff_score > 8.0:
        diff_score = 8.0 - (diff_score - 8.0) * 0.5

    reason = f"标签差异度 {diff_score:.1f}"
    return round(max(0.0, min(10.0, diff_score)), 1), reason


# ── 主函数 ─────────────────────────────────────────────────────────────────────

def rank_swap_candidates(
    target_entity: dict[str, Any],
    candidate_pool: list[dict[str, Any]],
    time_slot: str = "",
    prev_item_area: str | None = None,
    next_item_area: str | None = None,
    day_items: list[dict[str, Any]] | None = None,
    max_results: int = MAX_CANDIDATES,
) -> SwapResult:
    """
    为目标实体推荐替换候选。

    Args:
        target_entity: 被替换的实体数据
        candidate_pool: 候选实体列表（已通过硬约束筛选）
        time_slot: 目标时段（morning/afternoon/evening/night）
        prev_item_area: 前一个行程项的区域
        next_item_area: 后一个行程项的区域
        day_items: 当天所有行程项（用于计算影响）
        max_results: 最多返回候选数

    Returns:
        SwapResult
    """
    target_id = str(target_entity.get("id", "unknown"))

    # 排除自身和当天已出现的实体
    existing_ids = set()
    if day_items:
        existing_ids = {str(item.get("entity_id", "")) for item in day_items}
    existing_ids.add(target_id)

    filtered = [c for c in candidate_pool if str(c.get("id", "")) not in existing_ids]

    if len(filtered) < MIN_CANDIDATES:
        logger.warning(
            "Candidate pool too small for %s: %d entities after filter",
            target_id, len(filtered),
        )

    # 计算每个候选的 swap_score
    scored: list[SwapCandidate] = []

    for cand in filtered:
        # 四维分项
        ctx_fit, ctx_reason = _calc_context_fit(cand, target_entity, time_slot)

        # soft_rule_score（从候选实体数据中读取，0-100 → 0-10）
        raw_soft = cand.get("soft_rule_score", 50.0)
        soft_score = raw_soft / 10.0 if raw_soft > 10 else raw_soft

        slot_compat, slot_reason = _calc_slot_compatibility(
            cand, time_slot, prev_item_area, next_item_area,
        )

        diff, diff_reason = _calc_differentiation(cand, target_entity)

        # 综合 swap_score
        swap_score = (
            SWAP_WEIGHT_CONTEXT_FIT * ctx_fit
            + SWAP_WEIGHT_SOFT_RULE * soft_score
            + SWAP_WEIGHT_SLOT_COMPAT * slot_compat
            + SWAP_WEIGHT_DIFFERENTIATION * diff
        )

        # 预估影响
        impact = _estimate_quick_impact(target_entity, cand, day_items)

        scored.append(SwapCandidate(
            entity_id=str(cand.get("id", "")),
            entity_type=cand.get("entity_type", "poi"),
            name=cand.get("name_local") or cand.get("name", ""),
            name_zh=cand.get("name_zh"),
            area_name=cand.get("area_name"),
            swap_score=round(swap_score, 2),
            context_fit=ctx_fit,
            soft_rule_score=round(soft_score, 1),
            slot_compatibility=slot_compat,
            differentiation=diff,
            swap_reason=f"{ctx_reason}；{slot_reason}",
            impact_level=impact[0],
            estimated_score_change=impact[1],
        ))

    # 按 swap_score 降序排序
    scored.sort(key=lambda c: c.swap_score, reverse=True)
    top = scored[:max_results]

    # 生成用户提示
    if not top:
        msg = "暂无合适的替换选项"
    elif top[0].impact_level == "green":
        msg = "以下选项都不错，随意替换"
    elif top[0].impact_level == "yellow":
        msg = "替换后行程体验略有变化，但仍然很好"
    else:
        msg = "替换可能影响当天行程的整体体验，建议先看看其他选项"

    return SwapResult(
        target_entity_id=target_id,
        candidates=top,
        pool_size=len(filtered),
        relaxed_search=len(filtered) < MIN_CANDIDATES,
        message=msg,
    )


def _estimate_quick_impact(
    original: dict[str, Any],
    replacement: dict[str, Any],
    day_items: list[dict[str, Any]] | None,
) -> tuple[str, float]:
    """
    快速预估替换影响（不做完整重算，只用分数差异估算）。

    Returns:
        (impact_level, change_pct)
    """
    o_score = float(original.get("soft_rule_score", 50))
    r_score = float(replacement.get("soft_rule_score", 50))

    if o_score <= 0:
        return "green", 0.0

    change_pct = (r_score - o_score) / o_score

    if change_pct >= -IMPACT_THRESHOLD_SAFE:
        return "green", round(change_pct * 100, 1)
    elif change_pct >= -IMPACT_THRESHOLD_WARNING:
        return "yellow", round(change_pct * 100, 1)
    else:
        return "red", round(change_pct * 100, 1)


# ── 完整影响评估（用于用户确认替换后） ─────────────────────────────────────────

def validate_swap_impact(
    day_items: list[dict[str, Any]],
    target_index: int,
    replacement_entity: dict[str, Any],
) -> SwapImpact:
    """
    完整的替换影响评估。
    在用户选择了具体候选后、实际执行替换前调用。

    Args:
        day_items: 当天所有行程项
        target_index: 被替换项在 day_items 中的索引
        replacement_entity: 替换实体数据

    Returns:
        SwapImpact
    """
    # 计算替换前当天总分
    original_scores = []
    for item in day_items:
        s = float(item.get("soft_rule_score", 50))
        if s > 10:
            s = s / 10.0
        original_scores.append(s)

    original_avg = sum(original_scores) / len(original_scores) if original_scores else 5.0

    # 计算替换后当天总分
    new_scores = list(original_scores)
    r_score = float(replacement_entity.get("soft_rule_score", 50))
    if r_score > 10:
        r_score = r_score / 10.0
    if 0 <= target_index < len(new_scores):
        new_scores[target_index] = r_score

    new_avg = sum(new_scores) / len(new_scores) if new_scores else 5.0

    # 计算变化
    change_pct = (new_avg - original_avg) / original_avg if original_avg > 0 else 0.0

    # 判断影响等级
    if change_pct >= -IMPACT_THRESHOLD_SAFE:
        level = "green"
        msg = "替换后行程体验几乎不变，放心替换！"
    elif change_pct >= -IMPACT_THRESHOLD_WARNING:
        level = "yellow"
        msg = f"替换后当天体验会略有下降（约{abs(change_pct)*100:.0f}%），但仍然不错。"
    elif change_pct >= -IMPACT_THRESHOLD_BLOCK:
        level = "red"
        msg = f"替换后当天体验会明显下降（约{abs(change_pct)*100:.0f}%），建议考虑其他选项。"
    else:
        level = "red"
        msg = f"替换会显著影响当天行程体验（降低约{abs(change_pct)*100:.0f}%），强烈建议选择其他选项。"

    # 找出受影响最大的维度
    affected_dims = _find_affected_dimensions(
        day_items[target_index] if target_index < len(day_items) else {},
        replacement_entity,
    )

    return SwapImpact(
        original_score=round(original_avg, 2),
        new_score=round(new_avg, 2),
        change_pct=round(change_pct * 100, 1),
        impact_level=level,
        affected_dimensions=affected_dims,
        message=msg,
    )


def _find_affected_dimensions(
    original: dict[str, Any],
    replacement: dict[str, Any],
) -> list[str]:
    """找出替换后变化最大的维度。"""
    o_soft = original.get("soft_scores", {})
    r_soft = replacement.get("soft_scores", {})

    changes = []
    for dim_id in DIMENSION_IDS:
        o_val = float(o_soft.get(dim_id, 5.0))
        r_val = float(r_soft.get(dim_id, 5.0))
        diff = abs(r_val - o_val)
        if diff > 1.5:
            direction = "↑" if r_val > o_val else "↓"
            changes.append((dim_id, diff, direction))

    changes.sort(key=lambda x: x[1], reverse=True)
    return [f"{dim_id}{direction}" for dim_id, _, direction in changes[:3]]
