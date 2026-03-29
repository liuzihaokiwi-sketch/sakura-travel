"""
itinerary_fit_scorer.py — 日内适配评分器 (Layer 4)

骨架出来后才执行的评分层，衡量一个实体放进"今天这个位置"有多合适。
与 base_quality（Layer 2，实体固有品质）和 context_fit（Layer 3，旅行适配）不同，
这里考虑的是日内位置敏感信号。

4 层评分架构：
  Layer 1: eligibility_gate     — pass/fail 过滤（不打分）
  Layer 2: base_quality_score   — 实体固有品质（scorer.py）
  Layer 3: context_fit_score    — 旅行画像适配（scorer.compute_context_score）
  Layer 4: itinerary_fit_score  — 日内位置适配（本文件）

从 rules.py 中移出的维度在此消费：
  - theme_match   → 在 context_fit 层用（不在本文件）
  - area_efficiency → 在本文件的 corridor_alignment 维度中使用

评分维度（5 维，权重和 = 1.0）：
  1. corridor_alignment  — 实体是否在当天走廊上（替代旧 area_efficiency）
  2. sequence_fit        — 放在这个位置前后衔接是否顺
  3. time_window_fit     — 实体的最佳到达时间与当前 slot 的匹配
  4. backtrack_penalty   — 是否造成回头路
  5. day_rhythm_balance  — 节奏平衡（避免一天全是同类型）

接入补充：
  - route_matrix: sequence_fit / backtrack_penalty 可使用真实通勤时间（async 变体）
  - CorridorResolver: corridor_alignment 可使用标准化走廊匹配
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from app.domains.planning.corridor_resolver import CorridorResolver
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class SlotContext:
    """当前 slot 在日骨架中的上下文。"""
    day_index: int
    slot_index: int
    primary_corridor: str = ""
    secondary_corridor: str = ""
    prev_entity_area: str = ""
    next_entity_area: str = ""
    slot_time_hint: str = ""           # HH:MM
    day_capacity_remaining: float = 0.5
    same_type_count_today: int = 0     # 今天已经有几个同类型实体
    total_slots_today: int = 5
    transfer_budget_remaining: int = 60  # 剩余通勤分钟
    intensity: str = "balanced"         # light / balanced / dense


@dataclass
class EntityFitSignals:
    """实体在当前 slot 上下文中的适配信号。"""
    entity_id: Optional[str] = None     # entity_id（用于 route_matrix 查询）
    prev_entity_id: Optional[str] = None  # 前一个实体 ID（用于 route_matrix）
    entity_area: str = ""
    entity_type: str = "poi"
    entity_corridor_tags: list[str] = field(default_factory=list)  # 实体已标注的走廊
    best_arrival_time: str = ""         # HH:MM，实体最佳到达时间
    typical_duration_min: int = 60
    estimated_transit_min: int = 15     # 从上一个实体过来预估分钟
    real_transit_min: Optional[int] = None  # route_matrix 真实通勤时间（有则优先用）
    is_backtrack: bool = False          # 是否回头路
    theme_match_score: float = 50.0     # 从旧 context_fit 层传入
    area_efficiency_score: float = 50.0 # 从旧 scorer 传入


@dataclass
class ItineraryFitResult:
    """日内适配评分结果。"""
    entity_id: str = ""
    itinerary_fit_score: float = 50.0   # 0-100
    breakdown: dict[str, Any] = field(default_factory=dict)


# ── 权重配置 ──────────────────────────────────────────────────────────────────

_WEIGHTS = {
    "corridor_alignment": 0.30,
    "sequence_fit": 0.20,
    "time_window_fit": 0.15,
    "backtrack_penalty": 0.20,
    "day_rhythm_balance": 0.15,
}


# ── 主入口（纯函数，无 I/O）──────────────────────────────────────────────────

def compute_itinerary_fit(
    slot_ctx: SlotContext,
    entity_signals: EntityFitSignals,
) -> ItineraryFitResult:
    """
    计算实体在当前 slot 位置的日内适配分。

    纯函数，无 I/O，可并行调用。
    """
    result = ItineraryFitResult()
    bd: dict[str, Any] = {}

    # 1. corridor_alignment: 实体是否在当天走廊上
    bd["corridor_alignment"] = _score_corridor_alignment(slot_ctx, entity_signals)

    # 2. sequence_fit: 前后衔接
    bd["sequence_fit"] = _score_sequence_fit(slot_ctx, entity_signals)

    # 3. time_window_fit: 时间窗匹配
    bd["time_window_fit"] = _score_time_window_fit(slot_ctx, entity_signals)

    # 4. backtrack_penalty: 回头路惩罚
    bd["backtrack_penalty"] = _score_backtrack(slot_ctx, entity_signals)

    # 5. day_rhythm_balance: 节奏平衡
    bd["day_rhythm_balance"] = _score_rhythm_balance(slot_ctx, entity_signals)

    # 加权总分
    total = sum(bd[k] * _WEIGHTS[k] for k in _WEIGHTS)
    result.itinerary_fit_score = round(max(0.0, min(100.0, total)), 2)
    result.breakdown = bd
    return result


# ── 维度评分函数 ──────────────────────────────────────────────────────────────

def _score_corridor_alignment(ctx: SlotContext, sig: EntityFitSignals) -> float:
    """
    实体是否在当天走廊上。
    - 在 primary_corridor → 100
    - 在 secondary_corridor → 70
    - 都不在但 area_efficiency_score 高 → 按 area_efficiency 折算
    - 完全不在 → 20
    """
    entity_area = sig.entity_area.lower()
    primary = ctx.primary_corridor.lower()
    secondary = (ctx.secondary_corridor or "").lower()

    if primary and entity_area and primary in entity_area:
        return 100.0
    if secondary and entity_area and secondary in entity_area:
        return 70.0
    # fallback 到旧的 area_efficiency_score
    if sig.area_efficiency_score > 70:
        return sig.area_efficiency_score * 0.8
    return 20.0


def _score_sequence_fit(ctx: SlotContext, sig: EntityFitSignals) -> float:
    """
    前后衔接：前一个实体和后一个实体的区域与当前实体的关系。
    同区域 → 高分，跨区域但通勤 OK → 中分，通勤超预算 → 低分。
    """
    score = 60.0

    # 与前一个实体同区域
    if ctx.prev_entity_area and sig.entity_area:
        if ctx.prev_entity_area.lower() == sig.entity_area.lower():
            score += 25.0
        else:
            # 不同区域，看通勤预算
            if sig.estimated_transit_min <= 15:
                score += 10.0
            elif sig.estimated_transit_min <= 30:
                score -= 5.0
            else:
                score -= 20.0

    # 与后一个实体同区域
    if ctx.next_entity_area and sig.entity_area:
        if ctx.next_entity_area.lower() == sig.entity_area.lower():
            score += 15.0

    # 通勤预算检查
    if sig.estimated_transit_min > ctx.transfer_budget_remaining:
        score -= 30.0

    return max(0.0, min(100.0, score))


def _score_time_window_fit(ctx: SlotContext, sig: EntityFitSignals) -> float:
    """
    实体最佳到达时间与 slot 时间提示的匹配。
    完美匹配 → 100，差 1 小时 → 70，差 2 小时 → 40，无数据 → 60。
    """
    if not ctx.slot_time_hint or not sig.best_arrival_time:
        return 60.0  # 无数据，中性分

    try:
        slot_min = _parse_time_to_minutes(ctx.slot_time_hint)
        best_min = _parse_time_to_minutes(sig.best_arrival_time)
        diff = abs(slot_min - best_min)
        if diff <= 30:
            return 100.0
        elif diff <= 60:
            return 80.0
        elif diff <= 120:
            return 50.0
        else:
            return 30.0
    except (ValueError, TypeError):
        return 60.0


def _score_backtrack(ctx: SlotContext, sig: EntityFitSignals) -> float:
    """
    回头路惩罚。
    不回头 → 100，回头但距离短 → 50，明确回头 → 20。
    """
    if not sig.is_backtrack:
        return 100.0

    # 回头路但通勤短（< 10 min），可接受
    if sig.estimated_transit_min < 10:
        return 60.0

    return 20.0


def _score_rhythm_balance(ctx: SlotContext, sig: EntityFitSignals) -> float:
    """
    节奏平衡：避免一天全是同类型实体。
    同类型已有 0 个 → 100，1 个 → 80，2 个 → 60，3+ → 30。
    """
    same = ctx.same_type_count_today
    if same == 0:
        return 100.0
    elif same == 1:
        return 80.0
    elif same == 2:
        return 55.0
    else:
        return 30.0


# ── async 变体：接入 route_matrix + CorridorResolver ─────────────────────────

async def compute_itinerary_fit_async(
    slot_ctx: SlotContext,
    entity_signals: EntityFitSignals,
    session: "AsyncSession",
    corridor_resolver: Optional["CorridorResolver"] = None,
) -> ItineraryFitResult:
    """
    异步版本 — 用 route_matrix 获取真实通勤时间，用 CorridorResolver 做标准化走廊匹配。

    与 compute_itinerary_fit 相比：
      - real_transit_min 优先从 route_matrix 获取
      - corridor_alignment 优先使用 CorridorResolver
      - 其余逻辑完全一致
    """
    # 补充真实通勤时间
    if entity_signals.real_transit_min is None and entity_signals.entity_id and entity_signals.prev_entity_id:
        try:
            from app.domains.planning.route_matrix import get_travel_time
            result = await get_travel_time(
                session,
                uuid.UUID(entity_signals.prev_entity_id),
                uuid.UUID(entity_signals.entity_id),
                mode="transit",
            )
            entity_signals.real_transit_min = result["duration_min"]
            entity_signals.estimated_transit_min = result["duration_min"]
            logger.debug(
                "route_matrix: %s→%s = %d min (source=%s)",
                entity_signals.prev_entity_id[:8],
                entity_signals.entity_id[:8],
                result["duration_min"],
                result["source"],
            )
        except Exception as exc:
            logger.debug("route_matrix lookup failed: %s", exc)

    # 用 CorridorResolver 增强 corridor_alignment
    fit_result = ItineraryFitResult(entity_id=entity_signals.entity_id or "")
    bd: dict[str, Any] = {}

    bd["corridor_alignment"] = _score_corridor_alignment_v2(
        slot_ctx, entity_signals, corridor_resolver
    ) if corridor_resolver else _score_corridor_alignment(slot_ctx, entity_signals)

    transit = _effective_transit(entity_signals)
    bd["sequence_fit"] = _score_sequence_fit_v2(slot_ctx, entity_signals, transit)
    bd["time_window_fit"] = _score_time_window_fit(slot_ctx, entity_signals)
    bd["backtrack_penalty"] = _score_backtrack_v2(slot_ctx, entity_signals, transit)
    bd["day_rhythm_balance"] = _score_rhythm_balance(slot_ctx, entity_signals)

    total = sum(bd[k] * _WEIGHTS[k] for k in _WEIGHTS)
    fit_result.itinerary_fit_score = round(max(0.0, min(100.0, total)), 2)
    fit_result.breakdown = bd
    return fit_result


def _effective_transit(sig: EntityFitSignals) -> int:
    """优先使用真实通勤时间，fallback 到估算值。"""
    return sig.real_transit_min if sig.real_transit_min is not None else sig.estimated_transit_min


def _score_corridor_alignment_v2(
    ctx: SlotContext,
    sig: EntityFitSignals,
    resolver: "CorridorResolver",
) -> float:
    """CorridorResolver 增强版走廊对齐评分。"""
    entity_corridors = set(sig.entity_corridor_tags)
    if not entity_corridors and sig.entity_area:
        entity_corridors = set(resolver.resolve(sig.entity_area))

    if not entity_corridors:
        return 20.0

    primary_ids = set(resolver.resolve(ctx.primary_corridor)) if ctx.primary_corridor else set()
    secondary_ids = set(resolver.resolve(ctx.secondary_corridor)) if ctx.secondary_corridor else set()

    # 精确匹配主走廊
    if entity_corridors & primary_ids:
        return 100.0
    # 相邻主走廊
    if primary_ids and any(
        resolver.is_same_or_adjacent(ec, pc)
        for ec in entity_corridors for pc in primary_ids
    ):
        return 80.0
    # 精确匹配副走廊
    if entity_corridors & secondary_ids:
        return 70.0
    # 相邻副走廊
    if secondary_ids and any(
        resolver.is_same_or_adjacent(ec, sc)
        for ec in entity_corridors for sc in secondary_ids
    ):
        return 55.0
    # fallback
    if sig.area_efficiency_score > 70:
        return sig.area_efficiency_score * 0.8
    return 20.0


def _score_sequence_fit_v2(ctx: SlotContext, sig: EntityFitSignals, transit: int) -> float:
    """使用真实通勤时间的序列适配评分。"""
    score = 60.0

    if ctx.prev_entity_area and sig.entity_area:
        if ctx.prev_entity_area.lower() == sig.entity_area.lower():
            score += 25.0
        else:
            if transit <= 15:
                score += 10.0
            elif transit <= 30:
                score -= 5.0
            else:
                score -= 20.0

    if ctx.next_entity_area and sig.entity_area:
        if ctx.next_entity_area.lower() == sig.entity_area.lower():
            score += 15.0

    if transit > ctx.transfer_budget_remaining:
        score -= 30.0

    return max(0.0, min(100.0, score))


def _score_backtrack_v2(ctx: SlotContext, sig: EntityFitSignals, transit: int) -> float:
    """使用真实通勤时间的回头路惩罚。"""
    if not sig.is_backtrack:
        return 100.0
    if transit < 10:
        return 60.0
    if transit < 20:
        return 40.0
    return 20.0


# ── 辅助函数 ──────────────────────────────────────────────────────────────────

def _parse_time_to_minutes(time_str: str) -> int:
    """HH:MM → 总分钟数"""
    parts = time_str.strip().split(":")
    return int(parts[0]) * 60 + int(parts[1])


# ── E3: 小范围替换能力 ────────────────────────────────────────────────────────

# 替换触发阈值
SWAP_TRIGGER_THRESHOLD = 40.0      # itinerary_fit < 40 → 建议替换
MEAL_SWAP_TRIGGER_THRESHOLD = 35.0 # 餐厅 fit < 35 → 建议换餐厅

@dataclass
class SwapSuggestion:
    """替换建议。"""
    target_entity_id: str
    target_name: str
    reason: str                        # "backtrack_severe" / "corridor_mismatch" / "time_window_conflict"
    current_fit_score: float
    candidates: list[dict] = field(default_factory=list)  # [{entity_id, name, estimated_fit}]
    swap_type: str = "secondary"       # "secondary" / "meal"


async def suggest_swaps(
    slot_ctx: SlotContext,
    entity_signals_list: list[EntityFitSignals],
    candidate_pool: list[dict],
    session: "AsyncSession",
    corridor_resolver: Optional["CorridorResolver"] = None,
) -> list[SwapSuggestion]:
    """
    E3: 扫描当天所有次要活动，对 fit 分过低的建议 same_corridor 替换。

    复用 swap_engine 的 4 维评分逻辑，但触发点在 itinerary_fit 层。

    Args:
        slot_ctx: 当天的槽位上下文
        entity_signals_list: 当天所有实体的 fit signals
        candidate_pool: 可用候选实体池
        session: DB session (用于 route_matrix)
        corridor_resolver: 走廊解析器

    Returns:
        需要替换的建议列表
    """
    suggestions: list[SwapSuggestion] = []

    for sig in entity_signals_list:
        # 计算当前 fit
        fit = await compute_itinerary_fit_async(
            slot_ctx, sig, session, corridor_resolver
        )

        if fit.itinerary_fit_score >= SWAP_TRIGGER_THRESHOLD:
            continue  # 分数够高，不需要替换

        # 识别主要问题
        reason = _identify_swap_reason(fit)

        # 从候选池找 same_corridor 替代
        candidates = _find_corridor_candidates(
            sig, candidate_pool, slot_ctx, corridor_resolver, top_k=3
        )

        if candidates:
            suggestions.append(SwapSuggestion(
                target_entity_id=sig.entity_id or "",
                target_name=sig.entity_area,
                reason=reason,
                current_fit_score=fit.itinerary_fit_score,
                candidates=candidates,
                swap_type="secondary",
            ))

    return suggestions


async def suggest_meal_swaps(
    slot_ctx: SlotContext,
    meal_signals: list[EntityFitSignals],
    backup_restaurants: list[dict],
    session: "AsyncSession",
    corridor_resolver: Optional["CorridorResolver"] = None,
) -> list[SwapSuggestion]:
    """
    E3: 扫描当天餐厅，对 fit 分过低的建议 backup_meal 替换。
    """
    suggestions: list[SwapSuggestion] = []

    for sig in meal_signals:
        fit = await compute_itinerary_fit_async(
            slot_ctx, sig, session, corridor_resolver
        )

        if fit.itinerary_fit_score >= MEAL_SWAP_TRIGGER_THRESHOLD:
            continue

        reason = _identify_swap_reason(fit)
        candidates = _find_corridor_candidates(
            sig, backup_restaurants, slot_ctx, corridor_resolver, top_k=2
        )

        if candidates:
            suggestions.append(SwapSuggestion(
                target_entity_id=sig.entity_id or "",
                target_name=sig.entity_area,
                reason=reason,
                current_fit_score=fit.itinerary_fit_score,
                candidates=candidates,
                swap_type="meal",
            ))

    return suggestions


def _identify_swap_reason(fit: ItineraryFitResult) -> str:
    """从 fit breakdown 识别最严重的问题维度。"""
    bd = fit.breakdown
    worst_dim = min(bd, key=bd.get) if bd else "unknown"
    reasons_map = {
        "backtrack_penalty": "backtrack_severe",
        "corridor_alignment": "corridor_mismatch",
        "time_window_fit": "time_window_conflict",
        "sequence_fit": "sequence_poor",
        "day_rhythm_balance": "rhythm_imbalance",
    }
    return reasons_map.get(worst_dim, "low_overall_fit")


def _find_corridor_candidates(
    current_sig: EntityFitSignals,
    pool: list[dict],
    ctx: SlotContext,
    resolver: Optional["CorridorResolver"],
    top_k: int = 3,
) -> list[dict]:
    """
    从候选池中找 same_corridor 的替代实体。

    复用 swap_engine 的评分思路（context_fit + slot_compat + differentiation），
    但简化为走廊匹配 + 基础分排序。
    """
    current_id = current_sig.entity_id or ""
    current_area = current_sig.entity_area or ""

    scored: list[tuple[float, dict]] = []

    for ent in pool:
        eid = str(ent.get("entity_id", ""))
        if eid == current_id:
            continue  # 跳过自己

        # 走廊匹配
        corridor_score = 0.0
        ent_area = ent.get("area_name", "") or ""
        ent_corridor_tags = ent.get("corridor_tags") or []

        if resolver and ctx.primary_corridor:
            ent_corridors = set(ent_corridor_tags)
            if not ent_corridors and ent_area:
                ent_corridors = set(resolver.resolve(ent_area))
            primary_ids = set(resolver.resolve(ctx.primary_corridor))
            if ent_corridors & primary_ids:
                corridor_score = 10.0
            elif any(
                resolver.is_same_or_adjacent(ec, pc)
                for ec in ent_corridors for pc in primary_ids
            ):
                corridor_score = 7.0
        elif ctx.primary_corridor and ent_area:
            if ctx.primary_corridor.lower() in ent_area.lower():
                corridor_score = 10.0

        if corridor_score < 5.0:
            continue  # 不在走廊范围内的跳过

        # 基础分
        base = float(ent.get("final_score") or ent.get("base_score") or 50.0)

        # 差异化（避免推荐太相似的）
        diff_bonus = 2.0 if ent.get("sub_category") != current_sig.entity_type else 0.0

        total = corridor_score * 0.4 + (base / 10.0) * 0.4 + diff_bonus * 0.2
        scored.append((total, {
            "entity_id": eid,
            "name": ent.get("name_zh") or ent.get("name_en", ""),
            "estimated_fit": round(total * 10, 1),
            "area": ent_area,
            "corridor_score": corridor_score,
        }))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [s[1] for s in scored[:top_k]]


# ── 跨天节奏评分 ────────────────────────────────────────────────────────────

@dataclass
class RhythmScoreResult:
    """跨天节奏评分结果。"""
    rhythm_score: float = 80.0  # 0-100
    violations: list[str] = field(default_factory=list)
    breakdown: dict[str, float] = field(default_factory=dict)


def compute_rhythm_score(
    day_rhythms: list[dict[str, str]],
) -> RhythmScoreResult:
    """
    评估整个行程序列的节奏质量。

    Args:
        day_rhythms: 按天序的节奏属性列表，每个元素：
            {"experience_family": "shrine", "rhythm_role": "peak", "energy_level": "high"}
            空 dict 或 None 表示该天无主活动（到达日/离开日）

    Returns:
        RhythmScoreResult，含总分、违规列表、维度分拆

    评分维度（3 维，各 100 分，加权平均）：
      family_variety  (0.35) — experience_family 不连续 + 整体多样性
      peak_spacing    (0.35) — peak 间距合理、peak 数量适度
      energy_flow     (0.30) — high 后跟 low/medium、整体能量曲线合理
    """
    result = RhythmScoreResult()
    driven = [(i, d) for i, d in enumerate(day_rhythms) if d]

    if len(driven) < 2:
        result.rhythm_score = 80.0
        result.breakdown = {"family_variety": 80, "peak_spacing": 80, "energy_flow": 80}
        return result

    # ── family_variety ──
    family_score = 100.0
    families = [d.get("experience_family", "") for _, d in driven]
    families_valid = [f for f in families if f]

    # R1 检查：相邻同 family 每次 -20
    for i in range(len(families_valid) - 1):
        if families_valid[i] and families_valid[i] == families_valid[i + 1]:
            family_score -= 20.0
            result.violations.append(
                f"R1: day{driven[i][0]+1}-{driven[i+1][0]+1} same family '{families_valid[i]}'")

    # 多样性奖励：不同 family 种类越多越好
    unique_families = len(set(f for f in families_valid if f))
    if unique_families >= 4:
        family_score = min(100, family_score + 10)
    elif unique_families <= 2 and len(families_valid) >= 4:
        family_score -= 10

    family_score = max(0, min(100, family_score))

    # ── peak_spacing ──
    peak_score = 100.0
    roles = [d.get("rhythm_role", "") for _, d in driven]

    peak_indices = [i for i, r in enumerate(roles) if r == "peak"]
    peak_count = len(peak_indices)

    # R2 检查：连续 peak -25
    for i in range(len(peak_indices) - 1):
        gap = peak_indices[i + 1] - peak_indices[i]
        if gap == 1:
            peak_score -= 25.0
            result.violations.append(
                f"R2: consecutive peaks at positions {peak_indices[i]+1},{peak_indices[i+1]+1}")
        elif gap == 2:
            # 间隔只有 1 天，检查中间是否是 recovery/contrast
            mid_role = roles[peak_indices[i] + 1] if peak_indices[i] + 1 < len(roles) else ""
            if mid_role not in ("recovery", "contrast"):
                peak_score -= 10.0

    # peak 密度检查：每 7 天最多 3 个 peak
    total_days = len(driven)
    max_peaks = max(2, int(total_days * 3 / 7) + 1)
    if peak_count > max_peaks:
        peak_score -= 15.0 * (peak_count - max_peaks)
    elif peak_count == 0 and total_days >= 3:
        peak_score -= 15.0  # 完全没有 peak 也扣分

    peak_score = max(0, min(100, peak_score))

    # ── energy_flow ──
    energy_score = 100.0
    energies = [d.get("energy_level", "") for _, d in driven]

    # R3 检查：连续 high -20
    for i in range(len(energies) - 1):
        if energies[i] == "high" and energies[i + 1] == "high":
            energy_score -= 20.0
            result.violations.append(
                f"R3: consecutive high energy at positions {i+1},{i+2}")

    # 能量曲线：理想是波浪形（high→low→medium→high...）
    transitions = 0
    for i in range(len(energies) - 1):
        if energies[i] != energies[i + 1]:
            transitions += 1
    if len(energies) >= 3:
        transition_rate = transitions / (len(energies) - 1)
        if transition_rate >= 0.6:
            energy_score = min(100, energy_score + 5)  # 奖励变化多
        elif transition_rate <= 0.3:
            energy_score -= 10  # 太单调

    energy_score = max(0, min(100, energy_score))

    # ── 加权汇总 ──
    result.breakdown = {
        "family_variety": round(family_score, 1),
        "peak_spacing": round(peak_score, 1),
        "energy_flow": round(energy_score, 1),
    }
    result.rhythm_score = round(
        family_score * 0.35 + peak_score * 0.35 + energy_score * 0.30, 1
    )
    return result
