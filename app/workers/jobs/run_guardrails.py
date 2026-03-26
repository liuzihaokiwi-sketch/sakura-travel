"""
arq Job: run_guardrails
v2：调用 swap_safety.check_single_day_guardrails 进行完整 6 项检查，
保留原有 MIN_ITEMS + MAX_DUPLICATE 作为额外规则。
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.queue import enqueue_job
from app.db.models.business import TripRequest
from app.db.models.catalog import EntityBase
from app.db.models.derived import ItineraryDay, ItineraryItem, ItineraryPlan
from app.db.session import AsyncSessionLocal as async_session_factory
from app.domains.ranking.soft_rules.swap_safety import (
    GuardrailIssue,
    check_single_day_guardrails,
)

logger = logging.getLogger(__name__)

# hard_fail 阈值（原有规则保留）
MIN_ITEMS_PER_PLAN = 3          # 整个 plan 至少 3 个实体
MAX_DUPLICATE_RATIO = 0.2       # 重复实体比例上限 20%

# 星期映射
_WEEKDAY_MAP = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


async def _check_plan(session: AsyncSession, plan_id: uuid.UUID) -> tuple[list[str], list[dict]]:
    """
    返回 (hard_fail 错误列表, soft_fail 警告列表)。
    hard_fail 列表为空表示校验通过。
    """
    errors: list[str] = []
    warnings: list[dict] = []

    # 1. 查询所有 days + items
    days_q = await session.execute(
        select(ItineraryDay).where(ItineraryDay.plan_id == plan_id).order_by(ItineraryDay.day_number)
    )
    days = days_q.scalars().all()
    if not days:
        errors.append("行程无任何天数数据")
        return errors, warnings

    # 获取 plan 的 travel_dates（推算每天星期几）
    plan = await session.get(ItineraryPlan, plan_id)
    start_date: datetime | None = None
    if plan and plan.plan_metadata:
        dates = plan.plan_metadata.get("travel_dates") or {}
        start_str = dates.get("start")
        if start_str:
            try:
                start_date = datetime.strptime(start_str, "%Y-%m-%d")
            except (ValueError, TypeError):
                pass

    all_items: list[ItineraryItem] = []

    for day in days:
        items_q = await session.execute(
            select(ItineraryItem).where(ItineraryItem.day_id == day.day_id).order_by(ItineraryItem.sort_order)
        )
        items = items_q.scalars().all()
        all_items.extend(items)

        # 推算当天星期几
        day_of_week: str | None = None
        if start_date:
            actual_date = start_date + timedelta(days=day.day_number - 1)
            day_of_week = _WEEKDAY_MAP[actual_date.weekday()]

        # 将 ItineraryItem 转为 swap_safety 需要的 dict 格式
        day_item_dicts: list[dict] = []
        for item in items:
            if not item.entity_id:
                continue
            # 查询实体基本信息
            entity = await session.get(EntityBase, item.entity_id)
            day_item_dicts.append({
                "entity_id": str(item.entity_id),
                "entity_type": item.item_type or (entity.entity_type if entity else "poi"),
                "name": entity.name_zh if entity else "未知",
                "area_code": entity.area_code if entity and hasattr(entity, "area_code") else None,
                "area_name": entity.area_name if entity else None,
                "time": getattr(item, "start_time", None) or "",
                "time_slot": getattr(item, "slot_label", None) or "",
                "start_time": getattr(item, "start_time", None) or "",
            })

        # 调用 swap_safety 的完整 6 项检查
        if day_item_dicts:
            # 构建 operational_context：查询当天实体的营业事实
            op_context: dict = {}
            try:
                from app.db.models.soft_rules import EntityOperatingFact as _EOF
                day_entity_ids = [
                    itm.entity_id for itm in items
                    if getattr(itm, "entity_id", None)
                ]
                if day_entity_ids:
                    eof_q = await session.execute(
                        select(_EOF).where(_EOF.entity_id.in_(day_entity_ids))
                    )
                    for eof in eof_q.scalars().all():
                        key = str(eof.entity_id)
                        op_context.setdefault(key, {})[eof.fact_key] = eof.fact_value
            except Exception:
                pass

            issues = await check_single_day_guardrails(
                day_items=day_item_dicts,
                day_number=day.day_number,
                day_of_week=day_of_week,
                operational_context=op_context,
            )
            for issue in issues:
                if issue.severity == "hard_fail":
                    errors.append(f"Day{issue.day}: {issue.description}")
                else:
                    warnings.append({
                        "rule_id": issue.rule_id,
                        "severity": issue.severity,
                        "day": issue.day,
                        "description": issue.description,
                        "suggestion": issue.suggestion,
                        "entity_id": issue.entity_id,
                    })

    # 原有规则：实体总数检查
    if len(all_items) < MIN_ITEMS_PER_PLAN:
        errors.append(
            f"实体数量不足：{len(all_items)} < {MIN_ITEMS_PER_PLAN}"
        )

    # 原有规则：跨天重复实体比例检查
    entity_ids = [item.entity_id for item in all_items if item.entity_id is not None]
    if entity_ids:
        unique_count = len(set(entity_ids))
        dup_ratio = 1 - unique_count / len(entity_ids)
        if dup_ratio > MAX_DUPLICATE_RATIO:
            errors.append(
                f"重复实体比例过高：{dup_ratio:.0%} > {MAX_DUPLICATE_RATIO:.0%}"
            )

    return errors, warnings


async def _check_evidence_bundle(plan_meta: dict, run_id: str) -> list[dict]:
    """
    同源锁死 + 硬约束护栏。
    返回结构化 hard_fail 列表（code + detail）。
    """
    fails: list[dict] = []
    bundle = plan_meta.get("evidence_bundle")

    # Gate 1: evidence_bundle 必须存在
    if not bundle:
        fails.append({
            "code": "EVIDENCE_BUNDLE_MISSING",
            "detail": "plan_metadata 无 evidence_bundle 字段",
        })
        return fails  # 无 bundle 则后续检查无意义

    # Gate 2: 同源 run_id 校验
    if run_id and bundle.get("run_id") != run_id:
        fails.append({
            "code": "SOURCE_ID_MISMATCH",
            "detail": f"expect run_id={run_id[:8]}… got={str(bundle.get('run_id', ''))[:8]}…",
        })

    # Gate 3: constraint_trace 不允许 pending
    trace_items = bundle.get("constraint_trace", [])
    pending = [t for t in trace_items if t.get("final_status") == "pending"]
    if pending:
        names = [t["constraint_name"] for t in pending]
        fails.append({
            "code": "CONSTRAINT_TRACE_HAS_PENDING",
            "detail": f"pending constraints: {names}",
        })

    # Gate 4: hard constraint 不允许 unconsumed
    hard_unconsumed = [
        t for t in trace_items
        if t.get("strength") == "hard" and t.get("final_status") == "unconsumed"
    ]
    for t in hard_unconsumed:
        fails.append({
            "code": "HARD_CONSTRAINT_UNCONSUMED",
            "detail": f"{t['constraint_name']}: unconsumed, reason={t.get('ignored_reason', 'N/A')}",
            "constraint_name": t["constraint_name"],
        })

    return fails


async def run_guardrails(
    ctx: dict,
    *,
    plan_id: str,
    run_id: str = "",
) -> dict:
    """
    arq Job: 行程质量校验。
    通过后 enqueue render_export；失败则标记 trip_requests.status = 'failed'。

    v2: 新增 evidence_bundle 同源校验 + hard constraint 护栏。
    """
    pid = uuid.UUID(plan_id)
    logger.info("run_guardrails 开始 plan=%s run_id=%s", pid, run_id[:8] if run_id else "N/A")

    async with async_session_factory() as session:
        plan = await session.get(ItineraryPlan, pid)
        if plan is None:
            logger.error("plan_id=%s 不存在", pid)
            return {"status": "error", "reason": "plan not found"}

        # 更新 trip 状态为 reviewing
        trip = await session.get(TripRequest, plan.trip_request_id)
        if trip:
            trip.status = "reviewing"
            await session.commit()

        # ── 同源 + 约束护栏（优先于传统校验）──
        plan_meta = plan.plan_metadata or {}
        bundle_fails = await _check_evidence_bundle(plan_meta, run_id)

        # ── 传统校验（完整 6 项 + 原有 2 项）──
        errors, warnings = await _check_plan(session, pid)

        # 合并 bundle_fails 到 errors
        for bf in bundle_fails:
            errors.append(f"[{bf['code']}] {bf['detail']}")

        # 将结果写入 plan_metadata
        plan_meta["guardrail_warnings"] = warnings
        plan_meta["guardrail_errors"] = errors if errors else []
        plan_meta["guardrail_bundle_fails"] = bundle_fails
        plan_meta["guardrail_run_id"] = run_id
        plan.plan_metadata = plan_meta
        await session.commit()

        if errors:
            logger.warning("run_guardrails hard_fail plan=%s: %s", pid, errors)
            if trip:
                trip.status = "failed"
                await session.commit()
            return {
                "status": "failed",
                "plan_id": plan_id,
                "run_id": run_id,
                "errors": errors,
                "bundle_fails": bundle_fails,
                "warnings": warnings,
            }

    # 校验通过 → 触发渲染
    await enqueue_job("render_export", plan_id=plan_id, run_id=run_id)
    logger.info(
        "run_guardrails 通过 plan=%s run_id=%s（%d 条软警告），已入队 render_export",
        pid, run_id[:8] if run_id else "N/A", len(warnings),
    )

    return {"status": "ok", "plan_id": plan_id, "run_id": run_id, "warnings": warnings}
