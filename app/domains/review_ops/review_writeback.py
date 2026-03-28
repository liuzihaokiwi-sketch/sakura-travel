"""
review_writeback.py — 评审结果回写机制

将 review_ops/pipeline 的评审 issues 回写到数据层，形成飞轮闭环：

回写规则：
  QA hard_fail(closed_entity)   → entity_temporal_profiles 标记 stale
  QA hard_fail(time_conflict)   → entity_temporal_profiles 校正
  Ops critical(reservation)     → entity_base.requires_advance_booking = True
  Ops critical(closed_day)      → entity_temporal_profiles 修正
  User Proxy complaints         → generation_decisions 追加 tradeoff
  Tuning Guard tunable          → plan_metadata.tunable_items 标记

同时把整个 PipelineResult 写入 generation_decisions 的 review 阶段快照。
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def writeback_review_issues(
    session: AsyncSession,
    plan_id: uuid.UUID,
    trip_request_id: uuid.UUID,
    pipeline_result: Any,
) -> dict:
    """
    将评审结果回写到数据层。

    Args:
        pipeline_result: review_ops.pipeline.PipelineResult

    Returns:
        {"entities_updated": N, "temporal_fixes": M, "decisions_written": K}
    """
    from app.domains.planning.decision_writer import write_decision, write_standard_decision

    stats = {"entities_updated": 0, "temporal_fixes": 0, "decisions_written": 0}

    # 1. 收集所有 issues
    all_issues = []
    for agent_result in [
        pipeline_result.qa_result,
        pipeline_result.ops_proxy_result,
        pipeline_result.user_proxy_result,
        pipeline_result.tuning_guard_result,
    ]:
        if agent_result and agent_result.issues:
            all_issues.extend(agent_result.issues)

    # 2. QA hard_fail → 实体回写
    for issue in all_issues:
        if issue.severity in ("hard_fail", "critical") and issue.entity_id:
            try:
                eid = uuid.UUID(issue.entity_id)
            except (ValueError, TypeError):
                continue

            if issue.category in ("closed_entity", "closed_day"):
                # 标记 entity_field_provenance stale
                await _mark_entity_stale(session, eid, issue.category, issue.description)
                stats["temporal_fixes"] += 1

            elif issue.category == "reservation_needed":
                # 更新 requires_advance_booking
                await _update_booking_flag(session, eid)
                stats["entities_updated"] += 1

    # 3. 写入 review 阶段 decision 快照
    verdict = (
        pipeline_result.final_verdict.value
        if hasattr(pipeline_result.final_verdict, "value")
        else str(pipeline_result.final_verdict)
    )
    status_bucket = "compatibility_residual" if any(
        i.category in {"legacy_fallback", "compatibility_residual"} for i in all_issues
    ) else ("operator_required" if verdict == "human" else ("main_chain_failed" if verdict == "rewrite" else "main_chain_ok"))
    await write_standard_decision(
        session,
        trip_request_id=trip_request_id,
        plan_id=plan_id,
        stage="review_writeback",
        verdict=verdict,
        reason=pipeline_result.final_reason,
        operator_action="manual_review" if verdict == "human" else None,
        status_bucket=status_bucket,
        payload={
            "qa_issue_count": len(pipeline_result.qa_result.issues) if pipeline_result.qa_result else 0,
            "ops_issue_count": len(pipeline_result.ops_proxy_result.issues) if pipeline_result.ops_proxy_result else 0,
            "user_proxy_score": pipeline_result.user_proxy_result.score if pipeline_result.user_proxy_result else None,
        },
        alternatives=[
            {
                "agent": "qa", "issues": len(pipeline_result.qa_result.issues) if pipeline_result.qa_result else 0,
            },
            {
                "agent": "user_proxy",
                "score": pipeline_result.user_proxy_result.score if pipeline_result.user_proxy_result else None,
            },
            {
                "agent": "ops",
                "issues": len(pipeline_result.ops_proxy_result.issues) if pipeline_result.ops_proxy_result else 0,
            },
        ],
    )
    stats["decisions_written"] += 1

    # 4. User Proxy highlights / complaints → decision 快照
    if pipeline_result.user_proxy_result and pipeline_result.user_proxy_result.raw_output:
        up_data = pipeline_result.user_proxy_result.raw_output
        if up_data.get("highlights"):
            await write_decision(
                session, trip_request_id=trip_request_id, plan_id=plan_id,
                stage="review_user_proxy", key="highlights",
                value=up_data["highlights"],
                reason="用户视角亮点",
            )
            stats["decisions_written"] += 1
        if up_data.get("complaints"):
            await write_decision(
                session, trip_request_id=trip_request_id, plan_id=plan_id,
                stage="review_user_proxy", key="complaints",
                value=[c.get("description", "") for c in up_data["complaints"]],
                reason="用户视角槽点",
            )
            stats["decisions_written"] += 1

    # 5. Tuning Guard → plan_metadata.tunable_items
    if pipeline_result.tuning_guard_result and pipeline_result.tuning_guard_result.raw_output:
        tg_data = pipeline_result.tuning_guard_result.raw_output
        tunable = tg_data.get("tunable_modules", [])
        locked = tg_data.get("locked_modules", [])
        if tunable or locked:
            from app.db.models.derived import ItineraryPlan
            plan = await session.get(ItineraryPlan, plan_id)
            if plan:
                meta = plan.plan_metadata or {}
                meta["tunable_items"] = tunable
                meta["locked_items"] = locked
                meta["tunable_count"] = tg_data.get("tunable_count", len(tunable))
                plan.plan_metadata = meta

    await session.flush()
    logger.info(
        "review_writeback: plan=%s entities=%d temporal=%d decisions=%d",
        plan_id, stats["entities_updated"], stats["temporal_fixes"], stats["decisions_written"],
    )
    return {
        **stats,
        "writeback": {
            "stage": "review_writeback",
            "verdict": verdict,
            "reason": pipeline_result.final_reason,
            "operator_action": "manual_review" if verdict == "human" else None,
            "status_bucket": status_bucket,
        },
    }


async def _mark_entity_stale(
    session: AsyncSession,
    entity_id: uuid.UUID,
    category: str,
    description: str,
) -> None:
    """将实体的 temporal/provenance 标记为 stale。"""
    try:
        from app.db.models.catalog import EntityFieldProvenance
        # 标记 opening_hours 相关字段为 stale
        target_fields = ["opening_hours_json"]
        if category == "closed_day":
            target_fields.append("regular_holiday")

        await session.execute(
            update(EntityFieldProvenance)
            .where(
                EntityFieldProvenance.entity_id == entity_id,
                EntityFieldProvenance.field_name.in_(target_fields),
                EntityFieldProvenance.review_status.in_(["unreviewed", "approved"]),
            )
            .values(review_status="stale")
        )
    except Exception as exc:
        logger.debug("mark_entity_stale failed: %s", exc)


async def _update_booking_flag(
    session: AsyncSession,
    entity_id: uuid.UUID,
) -> None:
    """更新实体的 requires_advance_booking 标记。"""
    try:
        from app.db.models.catalog import EntityBase
        await session.execute(
            update(EntityBase)
            .where(EntityBase.entity_id == entity_id)
            .values(requires_advance_booking=True)
        )
    except Exception as exc:
        logger.debug("update_booking_flag failed: %s", exc)
