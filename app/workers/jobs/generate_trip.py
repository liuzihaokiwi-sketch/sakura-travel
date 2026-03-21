"""
arq Job: generate_trip
触发行程装配 → AI 文案润色 → 多模型评审 → 发布/重写/转人工

流程：
    assemble_trip → enrich_itinerary_with_copy
    → run_review_with_retry
        → publish  → 标记 delivered，入队渲染
        → rewrite  → 自动重写受影响天（最多 2 轮）
        → human    → 标记 review，入队人工审核
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from app.core.queue import enqueue_job
from app.db.models.business import TripRequest
from app.db.session import AsyncSessionLocal as async_session_factory
from app.domains.planning.assembler import assemble_trip
from app.domains.planning.assembler import enrich_itinerary_with_copy
from app.core.quality_gate import run_quality_gate, QualityGateResult

logger = logging.getLogger(__name__)

# Feature flag: 评审流水线开关（关闭时走旧逻辑 run_guardrails）
REVIEW_PIPELINE_ENABLED = True


async def _build_plan_json(session: Any, plan_id: uuid.UUID) -> dict:
    """从 DB 构建评审流水线需要的 plan_json 结构。"""
    from sqlalchemy import select
    from app.db.models.derived import ItineraryPlan, ItineraryDay, ItineraryItem
    from app.db.models.catalog import EntityBase

    plan = await session.get(ItineraryPlan, plan_id)
    if not plan:
        return {"plan_id": str(plan_id), "days": []}

    days_result = await session.execute(
        select(ItineraryDay)
        .where(ItineraryDay.plan_id == plan_id)
        .order_by(ItineraryDay.day_number)
    )
    days = days_result.scalars().all()

    plan_json: dict[str, Any] = {
        "plan_id": str(plan_id),
        "metadata": plan.plan_metadata or {},
        "days": [],
    }

    for day in days:
        items_result = await session.execute(
            select(ItineraryItem)
            .where(ItineraryItem.day_id == day.day_id)
            .order_by(ItineraryItem.sort_order)
        )
        items = items_result.scalars().all()

        day_items = []
        for item in items:
            item_dict: dict[str, Any] = {
                "time": "",  # 从 slot 推断
                "name": "未知",
                "entity_type": item.item_type or "poi",
                "entity_id": str(item.entity_id) if item.entity_id else None,
            }
            if item.entity_id:
                entity = await session.get(EntityBase, item.entity_id)
                if entity:
                    item_dict["name"] = entity.name_local or entity.name or "未知"
                    item_dict["entity_type"] = entity.entity_type or "poi"
            if item.notes_zh:
                import json as _json
                try:
                    notes = _json.loads(item.notes_zh) if isinstance(item.notes_zh, str) else item.notes_zh
                    item_dict["recommendation_reason"] = notes.get("copy_zh", "")
                except Exception:
                    pass
            day_items.append(item_dict)

        plan_json["days"].append({
            "day_number": day.day_number,
            "city": day.city_code or "",
            "theme": day.day_theme or "",
            "items": day_items,
        })

    return plan_json


async def _build_review_context(session: Any, trip: TripRequest, scene: str) -> dict:
    """构建评审所需的上下文。"""
    context: dict[str, Any] = {
        "segment": scene,
        "travel_date": "未知",
    }

    # 尝试从 trip 中获取旅行日期
    if hasattr(trip, "travel_start_date") and trip.travel_start_date:
        context["travel_date"] = str(trip.travel_start_date)

    # entity_operating_facts / seasonal_events 表尚未创建（需 alembic migration）
    # 暂时使用占位数据，待表创建后再接入真实查询
    context["operational_context"] = "暂无营业限制数据"   # TODO: 接入 entity_operating_facts
    context["seasonal_events"] = "暂无季节活动数据"        # TODO: 接入 seasonal_events

    return context


async def generate_trip(
    ctx: dict,
    *,
    trip_request_id: str,
    template_code: str,
    scene: str = "general",
) -> dict:
    """
    arq Job: 触发行程装配 + 评审。

    完整流程：
    1. assemble_trip → 装配结构化行程
    2. enrich_itinerary_with_copy → AI 文案润色
    3. run_review_with_retry → 多模型评审（并行 4 agent + judge）
    4. 根据裁决：publish → 渲染 / rewrite → 重写 / human → 人工队列

    Args:
        trip_request_id: 行程请求 UUID（字符串）
        template_code: 路线模板代码，如 "tokyo_classic_5d"
        scene: 出行场景，如 "couple" / "family" / "solo"
    """
    trip_id = uuid.UUID(trip_request_id)
    logger.info("generate_trip 开始 trip=%s template=%s scene=%s", trip_id, template_code, scene)

    async with async_session_factory() as session:
        # 更新状态为 assembling
        trip = await session.get(TripRequest, trip_id)
        if trip is None:
            logger.error("trip_request_id=%s 不存在", trip_id)
            return {"status": "error", "reason": "trip not found"}

        trip.status = "assembling"
        await session.commit()

        # Step 1: 装配
        try:
            plan_id = await assemble_trip(
                session=session,
                trip_request_id=trip_id,
                template_code=template_code,
                scene=scene,
            )
        except Exception as exc:
            logger.exception("generate_trip 装配失败 trip=%s: %s", trip_id, exc)
            trip.status = "failed"
            await session.commit()
            return {"status": "error", "reason": f"assemble failed: {exc}"}

        # Step 2: AI 文案润色
        try:
            await enrich_itinerary_with_copy(
                session=session,
                plan_id=plan_id,
                scene=scene,
            )
        except Exception as exc:
            logger.warning("文案润色失败（非致命）trip=%s: %s", trip_id, exc)

        # Step 2.3: 预览天标记
        try:
            from app.domains.ranking.soft_rules.preview_engine import select_preview_day
            from sqlalchemy import select
            from app.db.models.derived import ItineraryPlan, ItineraryDay, ItineraryItem
            from app.db.models.catalog import EntityBase

            days_q = await session.execute(
                select(ItineraryDay)
                .where(ItineraryDay.plan_id == plan_id)
                .order_by(ItineraryDay.day_number)
            )
            all_days = days_q.scalars().all()

            # 转换为 select_preview_day 需要的 list[list[dict]] 格式
            itinerary_days_for_preview: list[list[dict]] = []
            for day in all_days:
                items_q = await session.execute(
                    select(ItineraryItem)
                    .where(ItineraryItem.day_id == day.day_id)
                    .order_by(ItineraryItem.sort_order)
                )
                items = items_q.scalars().all()
                day_items: list[dict] = []
                for item in items:
                    if not item.entity_id:
                        continue
                    entity = await session.get(EntityBase, item.entity_id)
                    day_items.append({
                        "entity_id": str(item.entity_id),
                        "entity_type": item.item_type or (entity.entity_type if entity else "poi"),
                        "name": (entity.name_local or entity.name or "未知") if entity else "未知",
                        "tags": [],  # tags 可后续补充
                    })
                itinerary_days_for_preview.append(day_items)

            if itinerary_days_for_preview:
                preview_result = select_preview_day(itinerary_days_for_preview)
                plan = await session.get(ItineraryPlan, plan_id)
                if plan:
                    meta = plan.plan_metadata or {}
                    meta["preview_day"] = preview_result.selected_day_index
                    meta["preview_needs_review"] = preview_result.needs_human_review
                    meta["preview_reason"] = preview_result.selection_reason
                    plan.plan_metadata = meta
                    await session.commit()
                    logger.info(
                        "preview_day 标记完成 plan=%s day=%d needs_review=%s",
                        plan_id, preview_result.selected_day_index,
                        preview_result.needs_human_review,
                    )
        except Exception as exc:
            logger.warning("preview_day 标记失败（非致命）trip=%s: %s", trip_id, exc)

        # Step 2.5: 质量门控校验（11条 QTY 硬规则）
        try:
            plan_json_for_gate = await _build_plan_json(session, plan_id)
            gate_result: QualityGateResult = await run_quality_gate(plan_json_for_gate, db=session)
            logger.info(
                "质量门控结果 trip=%s plan=%s %s",
                trip_id, plan_id, gate_result.summary(),
            )
            if not gate_result.passed:
                # Hard error → 直接转人工，附上错误信息
                trip.status = "review"
                await session.commit()
                error_summary = "; ".join(gate_result.errors[:5])
                logger.warning(
                    "质量门控未通过，转人工审核 trip=%s errors=%s",
                    trip_id, error_summary,
                )
                return {
                    "status": "ok",
                    "plan_id": str(plan_id),
                    "review": "human_quality_gate",
                    "quality_errors": gate_result.errors,
                    "quality_warnings": gate_result.warnings,
                    "quality_score": gate_result.score,
                }
        except Exception as exc:
            logger.warning("质量门控异常（非致命，继续评审）trip=%s: %s", trip_id, exc)

        # Step 3: 多模型评审
        if not REVIEW_PIPELINE_ENABLED:
            # 旧逻辑：直接触发 guardrails
            await enqueue_job("run_guardrails", plan_id=str(plan_id))
            logger.info("generate_trip 完成（旧流程）plan=%s", plan_id)
            return {"status": "ok", "plan_id": str(plan_id), "review": "skipped"}

        try:
            from app.domains.review_ops.pipeline import run_review_with_retry, Verdict

            plan_json = await _build_plan_json(session, plan_id)
            review_context = await _build_review_context(session, trip, scene)

            # 尝试获取 AI client
            ai_client = None
            try:
                from app.core.ai_client import get_openai_client
                ai_client = get_openai_client()
            except Exception:
                logger.warning("AI client 不可用，评审将使用规则引擎兜底")

            result = await run_review_with_retry(
                plan_json=plan_json,
                context=review_context,
                ai_client=ai_client,
            )

            # 持久化 T22-T25 四维评审报告（并行，不阻塞主流程）
            # NOTE: plan_review_reports 表尚未创建，需要 alembic migration。
            # 字段：plan_id, overall_score, passed, blocker_count, warning_count,
            #       summary, comments(jsonb), slot_boundaries(jsonb)
            # 表不存在时 try/except 会静默跳过，不影响主流程。
            try:
                from app.core.multi_model_review import (
                    run_multi_model_review, review_report_to_dict
                )
                import json as _json
                profile = review_context.get("profile", {})
                mmr = await run_multi_model_review(plan_json, profile, plan_id=str(plan_id))
                mmr_dict = review_report_to_dict(mmr)
                from sqlalchemy import text as _text
                await session.execute(_text("""
                    INSERT INTO plan_review_reports
                    (plan_id, overall_score, passed, blocker_count, warning_count,
                     summary, comments, slot_boundaries)
                    VALUES (:plan_id, :score, :passed, :blockers, :warnings,
                            :summary, :comments::jsonb, :boundaries::jsonb)
                    ON CONFLICT DO NOTHING
                """), {
                    "plan_id": str(plan_id),
                    "score": mmr_dict["overall_score"],
                    "passed": mmr_dict["passed"],
                    "blockers": mmr_dict["blocker_count"],
                    "warnings": mmr_dict["warning_count"],
                    "summary": mmr_dict["summary"],
                    "comments": _json.dumps(mmr_dict["comments"], ensure_ascii=False),
                    "boundaries": _json.dumps(mmr_dict["slot_boundaries"], ensure_ascii=False),
                })
                logger.info(
                    "[T22-T25] 四维评审完成 plan=%s score=%.1f passed=%s",
                    plan_id, mmr_dict["overall_score"], mmr_dict["passed"],
                )
            except Exception as e:
                logger.warning("[T22-T25] 四维评审失败（非致命）: %s", e)

            # 持久化旧评审结果
            try:
                from sqlalchemy import text
                await session.execute(text("""
                    INSERT INTO review_pipeline_runs
                    (plan_id, round, qa_result, user_proxy_result,
                     ops_proxy_result, tuning_guard_result,
                     final_verdict, final_reason, total_tokens, total_duration_ms)
                    VALUES (:plan_id, :round, :qa, :user, :ops, :tuning,
                            :verdict, :reason, :tokens, :duration)
                """), {
                    "plan_id": str(plan_id),
                    "round": result.round_number,
                    "qa": str(result.qa_result.raw_output),
                    "user": str(result.user_proxy_result.raw_output),
                    "ops": str(result.ops_proxy_result.raw_output),
                    "tuning": str(result.tuning_guard_result.raw_output),
                    "verdict": result.final_verdict.value,
                    "reason": result.final_reason,
                    "tokens": result.total_tokens,
                    "duration": result.total_duration_ms,
                })
                await session.commit()
            except Exception as e:
                logger.warning("评审结果持久化失败（非致命）: %s", e)

            # 根据裁决分流
            if result.final_verdict == Verdict.PUBLISH:
                trip.status = "reviewed"
                await session.commit()
                await enqueue_job("render_trip", plan_id=str(plan_id))
                logger.info(
                    "评审通过 plan=%s (tokens=%d, duration=%dms)",
                    plan_id, result.total_tokens, result.total_duration_ms,
                )
                return {
                    "status": "ok",
                    "plan_id": str(plan_id),
                    "review": "published",
                    "tokens": result.total_tokens,
                }
            elif result.final_verdict == Verdict.HUMAN:
                trip.status = "review"
                await session.commit()
                logger.info(
                    "评审转人工 plan=%s reason=%s",
                    plan_id, result.final_reason,
                )
                return {
                    "status": "ok",
                    "plan_id": str(plan_id),
                    "review": "human",
                    "reason": result.final_reason,
                }
            else:
                # REWRITE 已经在 run_review_with_retry 内部处理了
                # 到这里说明重写后仍然是 human
                trip.status = "review"
                await session.commit()
                return {
                    "status": "ok",
                    "plan_id": str(plan_id),
                    "review": "human_after_rewrite",
                    "reason": result.final_reason,
                }

        except Exception as exc:
            logger.exception("评审流水线异常 trip=%s: %s", trip_id, exc)
            # 评审失败不阻塞，降级到人工审核
            trip.status = "review"
            await session.commit()
            await enqueue_job("run_guardrails", plan_id=str(plan_id))
            return {
                "status": "ok",
                "plan_id": str(plan_id),
                "review": "fallback_guardrails",
                "error": str(exc),
            }
