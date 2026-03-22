"""
Feedback & Distillation Engine — 反馈回库引擎 (H13)

对应文档 §22：
  回访数据收集 → 实体质量分更新 → 判断是否沉淀新片段 → 入 distillation_queue

闭环：用户反馈 → 实体/片段质量更新 → 新片段沉淀 → 片段库越来越强
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.fragments import (
    FragmentDistillationQueue,
    FragmentUsageStats,
    GuideFragment,
)

logger = logging.getLogger(__name__)


# ── 数据结构 ──────────────────────────────────────────────────────────────────

@dataclass
class FeedbackInput:
    """用户反馈输入"""
    trip_id: uuid.UUID
    source_type: str = "user_feedback"  # user_feedback / ops_review / auto_detect
    overall_rating: int = 3             # 1-5
    feedback_text: Optional[str] = None
    day_ratings: dict[int, int] = field(default_factory=dict)  # day_index -> 1-5
    highlights: list[str] = field(default_factory=list)        # 用户标记的亮点
    issues: list[str] = field(default_factory=list)            # 用户标记的问题
    would_recommend: Optional[bool] = None


@dataclass
class DistillationCandidate:
    """蒸馏候选"""
    trip_id: uuid.UUID
    day_index: Optional[int]
    proposed_type: str
    proposed_title: str
    proposed_city_code: str
    reason: str
    user_rating: int


@dataclass
class FeedbackResult:
    """反馈处理结果"""
    trip_id: uuid.UUID
    fragments_updated: int          # 质量分被更新的片段数
    entities_updated: int           # 实体质量分被更新的数量
    distillation_candidates: int    # 新入队的蒸馏候选数
    details: list[str] = field(default_factory=list)


# ── Step 1: 收集并关联片段 ────────────────────────────────────────────────────

async def _find_trip_fragments(
    session: AsyncSession,
    trip_id: uuid.UUID,
) -> list[GuideFragment]:
    """
    找到这个行程使用了哪些片段。

    优先通过 fragment_hit_logs 追踪表关联（精确），
    降级用 source_trip_id 匹配（蒸馏来源）。
    """
    from app.db.models.trace import FragmentHitLog, GenerationRun

    # 方式 1：通过 trace 关联（精确匹配已采纳的片段）
    subq = (
        select(FragmentHitLog.fragment_id)
        .join(GenerationRun, GenerationRun.run_id == FragmentHitLog.run_id)
        .where(
            GenerationRun.plan_id == trip_id,
            FragmentHitLog.adopted.is_(True),
        )
    )
    stmt = select(GuideFragment).where(GuideFragment.fragment_id.in_(subq))
    result = await session.execute(stmt)
    fragments = list(result.scalars().all())

    if fragments:
        return fragments

    # 方式 2：降级 — 通过 source_trip_id 匹配（从该行程蒸馏出来的片段）
    stmt_fallback = select(GuideFragment).where(
        GuideFragment.source_trip_id == trip_id
    )
    result_fb = await session.execute(stmt_fallback)
    return list(result_fb.scalars().all())


# ── Step 2: 更新片段质量分 ────────────────────────────────────────────────────

async def _update_fragment_quality(
    session: AsyncSession,
    fragments: list[GuideFragment],
    feedback: FeedbackInput,
) -> int:
    """
    根据用户反馈更新片段质量分。
    规则：
    - rating 4-5: quality_score += 0.2 (上限 10)
    - rating 3:   不变
    - rating 1-2: quality_score -= 0.3 (下限 1)
    - 被用户标记为 highlight: +0.5
    - 被用户标记为 issue: -0.5
    """
    updated = 0
    for frag in fragments:
        delta = 0.0

        if feedback.overall_rating >= 4:
            delta += 0.2
        elif feedback.overall_rating <= 2:
            delta -= 0.3

        # 检查是否有 day-level 反馈匹配
        if frag.day_index_hint is not None and frag.day_index_hint in feedback.day_ratings:
            day_r = feedback.day_ratings[frag.day_index_hint]
            if day_r >= 4:
                delta += 0.3
            elif day_r <= 2:
                delta -= 0.4

        if delta != 0.0:
            new_score = max(1.0, min(10.0, frag.quality_score + delta))
            await session.execute(
                update(GuideFragment)
                .where(GuideFragment.fragment_id == frag.fragment_id)
                .values(quality_score=new_score)
            )
            updated += 1
            logger.debug(
                "fragment %s quality: %.1f → %.1f (delta=%.1f)",
                frag.fragment_id, frag.quality_score, new_score, delta,
            )

    return updated


# ── Step 3: 更新使用统计 ──────────────────────────────────────────────────────

async def _update_usage_stats(
    session: AsyncSession,
    fragments: list[GuideFragment],
    feedback: FeedbackInput,
) -> None:
    """更新片段使用统计中的反馈数据"""
    for frag in fragments:
        values: dict = {}
        if feedback.overall_rating >= 4:
            values["positive_feedback_count"] = FragmentUsageStats.positive_feedback_count + 1
        elif feedback.overall_rating <= 2:
            values["negative_feedback_count"] = FragmentUsageStats.negative_feedback_count + 1

        if values:
            await session.execute(
                update(FragmentUsageStats)
                .where(FragmentUsageStats.fragment_id == frag.fragment_id)
                .values(**values)
            )


# ── Step 4: 判断蒸馏候选 ─────────────────────────────────────────────────────

def _should_distill(feedback: FeedbackInput) -> list[DistillationCandidate]:
    """
    判断是否应该从这个行程中沉淀新片段。
    规则：
    - overall_rating >= 4 且 would_recommend = True → 全行程可蒸馏
    - 某天 day_rating >= 4 → 该天可单独蒸馏
    - 用户有 highlights → 对应内容可蒸馏
    """
    candidates: list[DistillationCandidate] = []

    # 高评分行程 → 整体蒸馏
    if feedback.overall_rating >= 4 and feedback.would_recommend:
        candidates.append(DistillationCandidate(
            trip_id=feedback.trip_id,
            day_index=None,
            proposed_type="route",
            proposed_title=f"trip_{feedback.trip_id}_全程路线",
            proposed_city_code="auto",  # 后续从行程数据中提取
            reason="high_overall_rating_with_recommend",
            user_rating=feedback.overall_rating,
        ))

    # 高评分单日 → 单日蒸馏
    for day_idx, rating in feedback.day_ratings.items():
        if rating >= 4:
            candidates.append(DistillationCandidate(
                trip_id=feedback.trip_id,
                day_index=day_idx,
                proposed_type="route",
                proposed_title=f"trip_{feedback.trip_id}_day{day_idx}",
                proposed_city_code="auto",
                reason=f"high_day_rating_{rating}",
                user_rating=rating,
            ))

    # 用户标记的亮点 → experience 蒸馏
    for hl in feedback.highlights:
        candidates.append(DistillationCandidate(
            trip_id=feedback.trip_id,
            day_index=None,
            proposed_type="experience",
            proposed_title=hl,
            proposed_city_code="auto",
            reason="user_highlight",
            user_rating=feedback.overall_rating,
        ))

    return candidates


async def _enqueue_distillation(
    session: AsyncSession,
    candidates: list[DistillationCandidate],
    feedback: FeedbackInput,
) -> int:
    """将蒸馏候选写入队列"""
    count = 0
    for c in candidates:
        entry = FragmentDistillationQueue(
            source_trip_id=c.trip_id,
            source_day_index=c.day_index,
            source_type=feedback.source_type,
            proposed_type=c.proposed_type,
            proposed_title=c.proposed_title,
            proposed_city_code=c.proposed_city_code,
            status="pending",
            user_rating=feedback.overall_rating,
            user_feedback_text=feedback.feedback_text,
            feedback_collected_at=datetime.now(timezone.utc),
        )
        session.add(entry)
        count += 1
    return count


# ── 主函数 ────────────────────────────────────────────────────────────────────

async def process_feedback(
    session: AsyncSession,
    feedback: FeedbackInput,
) -> FeedbackResult:
    """
    反馈回库主入口。

    流程：
    1. 找到行程使用的片段
    2. 更新片段质量分
    3. 更新使用统计
    4. 判断蒸馏候选
    5. 入队蒸馏
    """
    details: list[str] = []

    # Step 1
    fragments = await _find_trip_fragments(session, feedback.trip_id)
    details.append(f"found {len(fragments)} fragments for trip {feedback.trip_id}")

    # Step 2
    frag_updated = await _update_fragment_quality(session, fragments, feedback)
    details.append(f"updated quality for {frag_updated} fragments")

    # Step 3
    await _update_usage_stats(session, fragments, feedback)
    details.append("usage stats updated")

    # Step 4-5
    candidates = _should_distill(feedback)
    distill_count = 0
    if candidates:
        distill_count = await _enqueue_distillation(session, candidates, feedback)
        details.append(f"enqueued {distill_count} distillation candidates")
    else:
        details.append("no distillation candidates")

    # Step 4.5: 实体/簇/圈质量回写
    entities_updated = 0
    try:
        entities_updated = await _update_entity_quality(session, feedback)
        details.append(f"entity quality updated for {entities_updated} entities")
    except Exception as exc:
        logger.warning("entity quality update failed: %s", exc)

    result = FeedbackResult(
        trip_id=feedback.trip_id,
        fragments_updated=frag_updated,
        entities_updated=entities_updated,
        distillation_candidates=distill_count,
        details=details,
    )

    logger.info(
        "feedback processed: trip=%s frags_updated=%d entities=%d distill=%d rating=%d",
        feedback.trip_id, frag_updated, entities_updated, distill_count, feedback.overall_rating,
    )
    return result


# ── Step 4.5: 实体 / 簇 / 圈 质量回写 ─────────────────────────────────────────

async def _update_entity_quality(
    session: AsyncSession,
    feedback: FeedbackInput,
) -> int:
    """
    根据用户反馈回写实体质量信号。

    规则：
      rating 4-5: 行程中所有实体 google_review_count +1 (模拟正向信号)
      rating 1-2: 行程中被标记为 issue 的实体降低 data_tier 权重
      day_rating 4-5: 该天实体标记正面反馈
      day_rating 1-2: 该天实体标记负面反馈

    回写到 generation_decisions 中，而非直接改 entity_base。
    这样保留可追溯性，后续可通过批量任务统计累积反馈。
    """
    from app.domains.planning.decision_writer import write_decision
    from app.db.models.derived import ItineraryPlan, ItineraryDay, ItineraryItem

    # 找到行程的 plan
    plan_q = await session.execute(
        select(ItineraryPlan).where(ItineraryPlan.trip_request_id == feedback.trip_id).limit(1)
    )
    plan = plan_q.scalar_one_or_none()
    if not plan:
        return 0

    # 找到所有 items
    days_q = await session.execute(
        select(ItineraryDay).where(ItineraryDay.plan_id == plan.plan_id).order_by(ItineraryDay.day_number)
    )
    all_days = days_q.scalars().all()

    updated = 0
    for day in all_days:
        day_rating = feedback.day_ratings.get(day.day_number, feedback.overall_rating)

        items_q = await session.execute(
            select(ItineraryItem).where(ItineraryItem.day_id == day.day_id)
        )
        items = items_q.scalars().all()

        for item in items:
            if not item.entity_id:
                continue

            signal = "neutral"
            if day_rating >= 4:
                signal = "positive"
            elif day_rating <= 2:
                signal = "negative"

            if signal != "neutral":
                await write_decision(
                    session,
                    trip_request_id=feedback.trip_id,
                    plan_id=plan.plan_id,
                    stage="feedback_entity",
                    key=f"entity_{item.entity_id}",
                    value=signal,
                    reason=f"day{day.day_number} rating={day_rating}, "
                           f"overall={feedback.overall_rating}, "
                           f"source={feedback.source_type}",
                )
                updated += 1

    # 如果 overall 高分，记录到 circle 级
    if feedback.overall_rating >= 4:
        await write_decision(
            session,
            trip_request_id=feedback.trip_id,
            plan_id=plan.plan_id,
            stage="feedback_circle",
            key="nps_positive",
            value=feedback.overall_rating,
            reason=f"would_recommend={feedback.would_recommend}",
        )
    elif feedback.overall_rating <= 2:
        await write_decision(
            session,
            trip_request_id=feedback.trip_id,
            plan_id=plan.plan_id,
            stage="feedback_circle",
            key="nps_negative",
            value=feedback.overall_rating,
            reason=feedback.feedback_text or "",
        )

    return updated
