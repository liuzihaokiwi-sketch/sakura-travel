"""
Fragment Reuse Engine — 片段复用引擎 (H9)

对应文档 §14-15：
  metadata filter → embedding 召回 → 硬规则 gate → 软规则 rerank
  → 4 档命中策略 (A/B/C/D) → 骨架装配

供 assembler.py / generate_trip.py 调用，返回可直接嵌入行程的片段列表。
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Sequence

from sqlalchemy import and_, select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.fragments import (
    FragmentCompatibility,
    FragmentEmbedding,
    FragmentUsageStats,
    GuideFragment,
)

logger = logging.getLogger(__name__)


# ── 数据结构 ──────────────────────────────────────────────────────────────────

class HitTier(str, Enum):
    """4 档命中策略"""
    A_STRONG = "A"   # 强命中：metadata + embedding + 硬规则 + 软规则 全通过，quality ≥ 7
    B_NORMAL = "B"   # 普通命中：通过硬规则，软规则分 ≥ 0.5
    C_WEAK = "C"     # 弱命中：通过硬规则，软规则分 < 0.5，但无替代
    D_MISS = "D"     # 未命中：需要 AI 全新生成


@dataclass
class FragmentCandidate:
    """片段候选"""
    fragment_id: uuid.UUID
    fragment_type: str
    title: str
    city_code: str
    day_index_hint: Optional[int]
    duration_slot: Optional[str]
    body_skeleton: dict
    body_prose: Optional[str]
    quality_score: float
    # 评分
    metadata_score: float = 0.0      # 0-1 metadata 匹配度
    semantic_score: float = 0.0      # 0-1 embedding 相似度
    hard_rule_pass: bool = True      # 硬规则是否通过
    hard_rule_reasons: list[str] = field(default_factory=list)
    soft_rule_score: float = 0.0     # 0-1 软规则加权分
    final_score: float = 0.0         # 综合分
    hit_tier: HitTier = HitTier.D_MISS

    def compute_final_score(self) -> float:
        """综合评分 = 0.2*metadata + 0.3*semantic + 0.3*soft_rule + 0.2*quality_norm"""
        quality_norm = min(self.quality_score / 10.0, 1.0)
        self.final_score = (
            0.2 * self.metadata_score
            + 0.3 * self.semantic_score
            + 0.3 * self.soft_rule_score
            + 0.2 * quality_norm
        )
        return self.final_score


@dataclass
class ReusePlan:
    """复用方案 — 引擎的最终输出"""
    request_summary: dict               # 查询条件快照
    candidates_evaluated: int           # 评估了多少候选
    fragments_adopted: list[FragmentCandidate]   # 采纳的片段
    fragments_rejected: list[FragmentCandidate]  # 被拒的片段
    gaps: list[dict]                    # 需要 AI 补充的空白时段
    stats: dict = field(default_factory=dict)    # hit_rate, tier_distribution 等


@dataclass
class ReuseRequest:
    """复用请求"""
    city_codes: list[str]
    theme_family: Optional[str] = None
    party_type: Optional[str] = None
    budget_level: Optional[str] = None
    season_tag: Optional[str] = None
    duration_days: int = 3
    fragment_types: list[str] = field(default_factory=lambda: ["route", "experience", "dining", "logistics", "tips"])
    # 可选：用户需求文本（用于 embedding 召回）
    user_wish_text: Optional[str] = None
    # 可选：已选定的片段 ID（避免重复）
    excluded_fragment_ids: list[uuid.UUID] = field(default_factory=list)


# ── Step 1: Metadata Filter ──────────────────────────────────────────────────

async def _metadata_filter(
    session: AsyncSession,
    req: ReuseRequest,
) -> list[GuideFragment]:
    """基于结构化字段过滤候选片段"""
    conditions = [
        GuideFragment.status == "active",
        GuideFragment.is_active.is_(True),
        GuideFragment.city_code.in_(req.city_codes),
    ]
    if req.fragment_types:
        conditions.append(GuideFragment.fragment_type.in_(req.fragment_types))
    if req.excluded_fragment_ids:
        conditions.append(GuideFragment.fragment_id.notin_(req.excluded_fragment_ids))

    stmt = select(GuideFragment).where(and_(*conditions)).order_by(
        GuideFragment.quality_score.desc()
    ).limit(100)  # 上限 100 候选

    result = await session.execute(stmt)
    fragments = list(result.scalars().all())
    logger.info("metadata_filter: %d 条候选 (cities=%s)", len(fragments), req.city_codes)
    return fragments


def _score_metadata(frag: GuideFragment, req: ReuseRequest) -> float:
    """计算 metadata 匹配度 0-1"""
    score = 0.0
    weights = {"theme": 0.3, "party": 0.25, "budget": 0.25, "season": 0.2}

    # theme_family 匹配
    if req.theme_family and frag.theme_families:
        if req.theme_family in frag.theme_families:
            score += weights["theme"]
        elif "all" in frag.theme_families:
            score += weights["theme"] * 0.5
    elif not req.theme_family:
        score += weights["theme"] * 0.5  # 无要求，给半分

    # party_type 匹配
    if req.party_type and frag.party_types:
        if req.party_type in frag.party_types:
            score += weights["party"]
        elif "all" in frag.party_types:
            score += weights["party"] * 0.5
    elif not req.party_type:
        score += weights["party"] * 0.5

    # budget_level 匹配
    if req.budget_level and frag.budget_levels:
        if req.budget_level in frag.budget_levels:
            score += weights["budget"]
    elif not req.budget_level:
        score += weights["budget"] * 0.5

    # season 匹配
    if req.season_tag and frag.season_tags:
        if req.season_tag in frag.season_tags or "all_year" in frag.season_tags:
            score += weights["season"]
    elif not req.season_tag:
        score += weights["season"] * 0.5

    return score


# ── Step 2: Embedding Recall (Optional) ──────────────────────────────────────

async def _embedding_recall(
    session: AsyncSession,
    candidates: list[GuideFragment],
    user_wish_text: Optional[str],
) -> dict[uuid.UUID, float]:
    """语义相似度评分（如果有 user_wish_text 和 embeddings）"""
    scores: dict[uuid.UUID, float] = {}

    if not user_wish_text or not candidates:
        # 无文本需求，所有候选给 0.5 中性分
        for c in candidates:
            scores[c.fragment_id] = 0.5
        return scores

    # 加载候选的 embeddings
    frag_ids = [c.fragment_id for c in candidates]
    stmt = select(FragmentEmbedding).where(
        FragmentEmbedding.fragment_id.in_(frag_ids)
    )
    result = await session.execute(stmt)
    embeddings = {e.fragment_id: e for e in result.scalars().all()}

    # 如果没有 embeddings 数据，给中性分
    for c in candidates:
        if c.fragment_id not in embeddings:
            scores[c.fragment_id] = 0.5
        else:
            # TODO: 接入实际 embedding API 计算 cosine similarity
            # 目前用质量分作为代理
            scores[c.fragment_id] = min(c.quality_score / 10.0, 1.0) * 0.7 + 0.3

    return scores


# ── Step 3: Hard Rule Gate ────────────────────────────────────────────────────

def _hard_rule_gate(frag: GuideFragment, req: ReuseRequest) -> tuple[bool, list[str]]:
    """硬规则过滤 — 不通过则直接淘汰"""
    reasons: list[str] = []

    # 规则 1：城市必须匹配
    if frag.city_code not in req.city_codes:
        reasons.append(f"city_mismatch: {frag.city_code} not in {req.city_codes}")

    # 规则 2：片段不能是 deprecated/archived
    if frag.status not in ("active", "draft"):
        reasons.append(f"status_invalid: {frag.status}")

    # 规则 3：day_index_hint 不能超过行程天数
    if frag.day_index_hint is not None and frag.day_index_hint >= req.duration_days:
        reasons.append(f"day_overflow: hint={frag.day_index_hint} >= days={req.duration_days}")

    # 规则 4：质量分 < 3 直接淘汰
    if frag.quality_score < 3.0:
        reasons.append(f"quality_too_low: {frag.quality_score}")

    return (len(reasons) == 0, reasons)


# ── Step 4: Soft Rule Rerank ──────────────────────────────────────────────────

def _soft_rule_score(frag: GuideFragment, req: ReuseRequest) -> float:
    """软规则加权评分 0-1"""
    score = 0.0
    dims = 0

    # 维度 1：质量分归一化
    score += min(frag.quality_score / 10.0, 1.0)
    dims += 1

    # 维度 2：day_index_hint 与行程天数的匹配度
    if frag.day_index_hint is not None:
        # 越靠前的片段越好（到达日优先）
        position_fit = 1.0 - (frag.day_index_hint / max(req.duration_days, 1))
        score += max(position_fit, 0.0)
        dims += 1

    # 维度 3：duration_slot 丰富度
    if frag.duration_slot:
        score += 0.7  # 有时段标注的片段更好
        dims += 1

    # 维度 4：body_prose 完整度
    if frag.body_prose and len(frag.body_prose) > 100:
        score += 1.0
    elif frag.body_prose:
        score += 0.5
    dims += 1

    return score / max(dims, 1)


# ── Step 5: Tier Classification ───────────────────────────────────────────────

def _classify_tier(candidate: FragmentCandidate) -> HitTier:
    """根据综合评分和硬规则结果判定命中档位"""
    if not candidate.hard_rule_pass:
        return HitTier.D_MISS
    if candidate.final_score >= 0.7 and candidate.quality_score >= 7.0:
        return HitTier.A_STRONG
    if candidate.final_score >= 0.4:
        return HitTier.B_NORMAL
    return HitTier.C_WEAK


# ── Step 6: Compatibility Check ───────────────────────────────────────────────

async def _check_compatibility(
    session: AsyncSession,
    adopted: list[FragmentCandidate],
    new_candidate: FragmentCandidate,
) -> tuple[bool, Optional[str]]:
    """检查新片段与已采纳片段的兼容性（双向查询）"""
    if not adopted:
        return True, None

    adopted_ids = [a.fragment_id for a in adopted]
    new_id = new_candidate.fragment_id

    # 双向查询：(adopted→new) OR (new→adopted)
    from sqlalchemy import or_
    stmt = select(FragmentCompatibility).where(
        and_(
            FragmentCompatibility.compatibility_type == "conflict",
            or_(
                and_(
                    FragmentCompatibility.fragment_a_id.in_(adopted_ids),
                    FragmentCompatibility.fragment_b_id == new_id,
                ),
                and_(
                    FragmentCompatibility.fragment_a_id == new_id,
                    FragmentCompatibility.fragment_b_id.in_(adopted_ids),
                ),
            ),
        )
    )
    result = await session.execute(stmt)
    conflicts = list(result.scalars().all())

    if conflicts:
        reasons = [c.reason or "conflict" for c in conflicts]
        return False, f"conflicts with adopted: {reasons}"
    return True, None


# ── 主函数 ────────────────────────────────────────────────────────────────────

async def find_reusable_fragments(
    session: AsyncSession,
    request: ReuseRequest,
) -> ReusePlan:
    """
    片段复用引擎主入口。

    流程：
    1. metadata filter — 从 DB 拉取候选
    2. embedding recall — 语义相似度（如有 user_wish_text）
    3. 对每个候选：metadata_score + semantic_score + hard_rule + soft_rule
    4. 排序 + tier 分类
    5. 兼容性检查 + 贪心选择
    6. 生成 gaps（需要 AI 补充的时段）
    """
    # Step 1: Metadata filter
    raw_fragments = await _metadata_filter(session, request)

    # Step 2: Embedding recall
    semantic_scores = await _embedding_recall(session, raw_fragments, request.user_wish_text)

    # Step 3-4: Score each candidate
    candidates: list[FragmentCandidate] = []
    for frag in raw_fragments:
        c = FragmentCandidate(
            fragment_id=frag.fragment_id,
            fragment_type=frag.fragment_type,
            title=frag.title,
            city_code=frag.city_code,
            day_index_hint=frag.day_index_hint,
            duration_slot=frag.duration_slot,
            body_skeleton=frag.body_skeleton or {},
            body_prose=frag.body_prose,
            quality_score=frag.quality_score,
        )
        c.metadata_score = _score_metadata(frag, request)
        c.semantic_score = semantic_scores.get(frag.fragment_id, 0.5)
        c.hard_rule_pass, c.hard_rule_reasons = _hard_rule_gate(frag, request)
        c.soft_rule_score = _soft_rule_score(frag, request) if c.hard_rule_pass else 0.0
        c.compute_final_score()
        c.hit_tier = _classify_tier(c)
        candidates.append(c)

    # Sort by final_score desc
    candidates.sort(key=lambda x: x.final_score, reverse=True)

    # Step 5: Greedy selection with compatibility check
    adopted: list[FragmentCandidate] = []
    rejected: list[FragmentCandidate] = []

    for c in candidates:
        if c.hit_tier == HitTier.D_MISS:
            rejected.append(c)
            continue

        compatible, reason = await _check_compatibility(session, adopted, c)
        if not compatible:
            c.hard_rule_reasons.append(reason or "compatibility_conflict")
            rejected.append(c)
            continue

        # 同一 day_index + duration_slot 不重复选
        slot_key = (c.day_index_hint, c.duration_slot)
        already_filled = any(
            (a.day_index_hint, a.duration_slot) == slot_key
            for a in adopted
            if slot_key != (None, None)
        )
        if already_filled:
            rejected.append(c)
            continue

        adopted.append(c)

    # Step 6: Identify gaps
    gaps = _identify_gaps(adopted, request.duration_days)

    # Stats
    tier_dist = {t.value: 0 for t in HitTier}
    for c in candidates:
        tier_dist[c.hit_tier.value] += 1

    plan = ReusePlan(
        request_summary={
            "city_codes": request.city_codes,
            "theme_family": request.theme_family,
            "party_type": request.party_type,
            "budget_level": request.budget_level,
            "duration_days": request.duration_days,
        },
        candidates_evaluated=len(candidates),
        fragments_adopted=adopted,
        fragments_rejected=rejected,
        gaps=gaps,
        stats={
            "hit_rate": len(adopted) / max(len(candidates), 1),
            "tier_distribution": tier_dist,
            "adopted_count": len(adopted),
            "rejected_count": len(rejected),
            "gap_count": len(gaps),
        },
    )

    logger.info(
        "fragment_reuse: evaluated=%d adopted=%d rejected=%d gaps=%d tiers=%s",
        plan.candidates_evaluated, len(adopted), len(rejected), len(gaps), tier_dist,
    )

    # Update last_used_at for adopted fragments
    if adopted:
        adopted_ids = [a.fragment_id for a in adopted]
        await session.execute(
            GuideFragment.__table__.update()
            .where(GuideFragment.fragment_id.in_(adopted_ids))
            .values(last_used_at=sa_func.now())
        )
        # Increment usage stats (upsert: INSERT if row missing, UPDATE if exists)
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        for a in adopted:
            insert_stmt = pg_insert(FragmentUsageStats.__table__).values(
                fragment_id=a.fragment_id,
                total_hits=1,
                total_adopted=1,
                total_rejected=0,
                total_replaced_by_human=0,
                positive_feedback_count=0,
                negative_feedback_count=0,
                last_hit_at=sa_func.now(),
            ).on_conflict_do_update(
                index_elements=["fragment_id"],
                set_={
                    "total_hits": FragmentUsageStats.__table__.c.total_hits + 1,
                    "total_adopted": FragmentUsageStats.__table__.c.total_adopted + 1,
                    "last_hit_at": sa_func.now(),
                },
            )
            await session.execute(insert_stmt)

    return plan


def _identify_gaps(adopted: list[FragmentCandidate], duration_days: int) -> list[dict]:
    """找出未被片段覆盖的时段"""
    covered_slots: set[tuple] = set()
    for a in adopted:
        if a.day_index_hint is not None and a.duration_slot:
            covered_slots.add((a.day_index_hint, a.duration_slot))

    all_slots = ["morning", "afternoon", "evening"]
    gaps = []
    for day in range(duration_days):
        for slot in all_slots:
            if (day, slot) not in covered_slots:
                gaps.append({
                    "day_index": day,
                    "duration_slot": slot,
                    "reason": "no_fragment_hit",
                    "suggested_action": "ai_generate",
                })

    return gaps
