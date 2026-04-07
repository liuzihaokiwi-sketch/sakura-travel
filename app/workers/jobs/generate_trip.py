"""
arq Job: generate_trip

流程：
    city-circle pipeline → build_planning_output → page pipeline
    → copy enrichment → quality gate → review pipeline
        → publish  → 渲染交付
        → rewrite  → 自动重写（最多 2 轮）
        → human    → 人工审核队列
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from app.core.queue import enqueue_job
from app.db.models.business import TripRequest
from app.db.session import AsyncSessionLocal as async_session_factory
from app.domains.intake.layer2_contract import build_layer2_profile_contract
from app.core.quality_gate import run_quality_gate, QualityGateResult
from app.core.sentry import set_sentry_context, capture_exception_with_context

logger = logging.getLogger(__name__)

# Feature flags（从 env 读取，支持运行时关闭）
import os as _os
REVIEW_PIPELINE_ENABLED: bool = _os.environ.get("REVIEW_PIPELINE_ENABLED", "true").lower() != "false"


def _plan_json_from_planning_output(planning_output: Any, plan_id: Any) -> dict:
    """
    从已构建的 PlanningOutput 直接组装 plan_json，跳过 DB 二次查询。

    用于 quality gate 和 offline_eval——这两处在 planning_output 已可用时调用，
    无需重新从 DB 读 ItineraryDay/ItineraryItem。

    字段需与 quality_gate.py 中 QTY 规则消费的字段对齐：
      item_type, entity_name, start_time, end_time, duration_min,
      copy_zh, entity_id, day_theme, transport_note
    """
    # 构建 entity_id → why_selected 映射，供 QTY-08 推荐理由检查
    evidence_map: dict[str, str] = {}
    for ev in getattr(planning_output, "selection_evidence", []) or []:
        eid = ev.get("entity_id", "")
        why = ev.get("why_selected", "")
        if eid and why:
            evidence_map[eid] = why

    days = []
    for day in planning_output.days:
        items = []
        for slot in day.slots:
            # 计算 end_time（用于 QTY-04 时间冲突检查）
            end_time = None
            if slot.start_time_hint and slot.duration_mins:
                try:
                    parts = slot.start_time_hint.split(":")
                    start_min = int(parts[0]) * 60 + int(parts[1])
                    end_min = start_min + slot.duration_mins
                    end_time = f"{end_min // 60:02d}:{end_min % 60:02d}"
                except (ValueError, IndexError):
                    pass

            entity_id = slot.entity_id or ""
            copy_zh = evidence_map.get(entity_id, "")

            items.append({
                "time": slot.start_time_hint or "",
                "name": slot.title or "未知",
                "entity_type": slot.kind or "poi",
                "item_type": slot.kind or "poi",
                "entity_id": entity_id,
                "entity_name": slot.title or "未知",
                "start_time": slot.start_time_hint or "",
                "end_time": end_time or "",
                "duration_min": slot.duration_mins or 60,
                "copy_zh": copy_zh,
            })
        days.append({
            "day_number": day.day_index,
            "city": day.primary_area or "",
            "theme": day.title or "",
            "day_theme": day.title or "",
            "items": items,
        })
    return {
        "plan_id": str(plan_id),
        "days": days,
    }


async def _build_plan_json(session: Any, plan_id: uuid.UUID) -> dict:
    """Build the plan_json payload for downstream review/eval."""
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

    # 批量拉取所有 items，避免 N+1
    all_items_result = await session.execute(
        select(ItineraryItem)
        .join(ItineraryDay, ItineraryItem.day_id == ItineraryDay.day_id)
        .where(ItineraryDay.plan_id == plan_id)
        .order_by(ItineraryDay.day_number, ItineraryItem.sort_order)
    )
    all_items = all_items_result.scalars().all()

    # 批量拉取所有 entity_ids 对应的 EntityBase，避免循环 N+1
    entity_ids = list({item.entity_id for item in all_items if item.entity_id})
    entity_map: dict[Any, EntityBase] = {}
    if entity_ids:
        ents_result = await session.execute(
            select(EntityBase).where(EntityBase.entity_id.in_(entity_ids))
        )
        for ent in ents_result.scalars().all():
            entity_map[ent.entity_id] = ent

    # 按 day_id 分组
    from collections import defaultdict
    items_by_day: dict[Any, list] = defaultdict(list)
    for item in all_items:
        items_by_day[item.day_id].append(item)

    for day in days:
        items = items_by_day.get(day.day_id, [])

        day_items = []
        for item in items:
            entity_name = "未知"
            entity_type = item.item_type or "poi"
            if item.entity_id:
                entity = entity_map.get(item.entity_id)
                if entity:
                    entity_name = getattr(entity, "name_local", None) or getattr(entity, "name", None) or entity.name_zh or "未知"
                    entity_type = entity.entity_type or "poi"

            copy_zh = ""
            if item.notes_zh:
                import json as _json
                try:
                    notes = _json.loads(item.notes_zh) if isinstance(item.notes_zh, str) else item.notes_zh
                    copy_zh = notes.get("copy_zh", "")
                except Exception as _exc:
                    logger.warning("notes_zh parse failed for item %s: %s", item.item_id, _exc)

            item_dict: dict[str, Any] = {
                "time": item.start_time or "",
                "name": entity_name,
                "entity_type": entity_type,
                "item_type": entity_type,
                "entity_id": str(item.entity_id) if item.entity_id else None,
                "entity_name": entity_name,
                "start_time": item.start_time or "",
                "end_time": item.end_time or "",
                "duration_min": item.duration_min or 60,
                "copy_zh": copy_zh,
            }
            day_items.append(item_dict)

        plan_json["days"].append({
            "day_number": day.day_number,
            "city": day.city_code or "",
            "theme": day.day_theme or "",
            "day_theme": day.day_theme or "",
            "items": day_items,
        })

    return plan_json


async def _build_review_context(session: Any, trip: TripRequest, scene: str) -> dict:
    """Build runtime review context from plan/profile/ops surfaces."""
    from sqlalchemy import select as _sel
    from datetime import datetime as _dt, timezone as _tz, timedelta as _td

    context: dict[str, Any] = {
        "segment": scene,
        "travel_date": "未知",
    }

    # 旅行日期
    travel_start: Any = None
    if hasattr(trip, "travel_start_date") and trip.travel_start_date:
        travel_start = trip.travel_start_date
        context["travel_date"] = str(travel_start)

    # 1. entity_operating_facts
    try:
        from app.db.models.derived import ItineraryPlan, ItineraryItem
        from app.db.models.soft_rules import EntityOperatingFact

        # 找最近的一个 plan
        plan_q = await session.execute(
            _sel(ItineraryPlan)
            .where(ItineraryPlan.trip_request_id == trip.trip_request_id)
            .order_by(ItineraryPlan.created_at.desc())
            .limit(1)
        )
        plan = plan_q.scalar_one_or_none()
        if plan:
            items_q = await session.execute(
                _sel(ItineraryItem).where(ItineraryItem.plan_id == plan.plan_id)
            )
            entity_ids = list({
                item.entity_id for item in items_q.scalars().all()
                if item.entity_id
            })
            if entity_ids:
                facts_q = await session.execute(
                    _sel(EntityOperatingFact)
                    .where(EntityOperatingFact.entity_id.in_(entity_ids))
                )
                facts = facts_q.scalars().all()
                # EntityOperatingFact 存储营业时段；检查 holiday_schedule 中的关闭标记
                warnings = []
                for f in facts:
                    hs = f.holiday_schedule or {}
                    status = str(hs.get("status", "")).lower()
                    if status in ("permanently_closed", "long_term_closed",
                                  "temporarily_closed", "limited_hours"):
                        warnings.append(
                            f"status={status} day={f.day_of_week} (entity={f.entity_id})"
                        )
                context["operational_context"] = "; ".join(warnings) if warnings else "no_operational_alerts"
            else:
                context["operational_context"] = "no_entities"
        else:
            context["operational_context"] = "no_plan_data"
    except Exception as exc:
        logger.warning("_build_review_context: entity_operating_facts 查询失败: %s", exc)
        context["operational_context"] = "查询失败"

    # 2. seasonal_events：拉取旅行日期前后30天内的季节活动    try:
        from app.db.models.soft_rules import SeasonalEvent

        if travel_start:
            # 兼容 date / datetime
            if hasattr(travel_start, "year"):
                window_start = _dt.combine(travel_start, _dt.min.time()).replace(tzinfo=_tz.utc) \
                    if not hasattr(travel_start, "tzinfo") else travel_start
            else:
                window_start = _dt.now(_tz.utc)
            window_end = window_start + _td(days=30)

            events_q = await session.execute(
                _sel(SeasonalEvent)
                .where(
                    SeasonalEvent.start_date <= window_end,
                    SeasonalEvent.end_date >= window_start,
                )
                .order_by(SeasonalEvent.crowd_impact.desc())
                .limit(10)
            )
            events = events_q.scalars().all()
            if events:
                context["seasonal_events"] = "; ".join(
                    f"{e.event_name}({e.city_code}, crowd={e.crowd_impact})"
                    for e in events
                )
            else:
                context["seasonal_events"] = "no_seasonal_events"
        else:
            context["seasonal_events"] = "no_travel_date"
    except Exception as exc:
        logger.warning("_build_review_context: seasonal_events 查询失败: %s", exc)
        context["seasonal_events"] = "查询失败"

    return context



async def generate_trip(
    ctx: dict,
    *,
    trip_request_id: str,
    scene: str = "general",
) -> dict:
    """
    arq Job: 触发行程装配 + 评审。
    I1 改造：仅走城市圈主链路，失败时显式失败，不回退旧模板。
    完整流程：        1. [新] 尝试城市圈链路（select_circle → rank_major → hotel → skeleton）              → 成功: 用 itinerary_builder 装配 + generate_report_v2
              → 失败: 显式失败
    2. enrich_itinerary_with_copy 鈫?AI 鏂囨娑﹁壊
        3. run_review_with_retry → 多模型评审        4. 根据裁决：publish → 渲染 / rewrite → 重写 / human → 人工队列
    """
    trip_id = uuid.UUID(trip_request_id)
    logger.info("generate_trip 寮€濮?trip=%s scene=%s", trip_id, scene)

    # Set Sentry transaction name and trip_id tag for all errors in this job
    set_sentry_context(
        transaction_name="generate_trip",
        trip_id=trip_request_id,
        step="init",
    )

    async with async_session_factory() as session:
        from app.domains.planning.decision_writer import write_decision

        trip = await session.get(TripRequest, trip_id)
        if trip is None:
            logger.error("trip_request_id=%s not found", trip_id)
            return {"status": "error", "reason": "trip not found"}

        trip.status = "assembling"
        await session.commit()

        # ── 表单级前置门控（validation engine）──
        form_validation_ok = True
        try:
            from app.domains.validation.engine import ValidationEngine
            from sqlalchemy import select as _sel
            from app.db.models.detail_forms import DetailForm

            form_q = await session.execute(
                _sel(DetailForm).where(DetailForm.trip_request_id == trip_id).limit(1)
            )
            form = form_q.scalar_one_or_none()
            if form and form.form_data:
                engine = ValidationEngine()
                vr = engine.validate(form.form_data, form_id=str(form.form_id))
                if not vr.can_generate():
                    logger.warning(
                        "表单校验未通过(red=%d): trip=%s",
                        vr.red_count, trip_id,
                    )
                    trip.status = "validation_failed"
                    await session.commit()
                    return {
                        "status": "validation_failed",
                        "red_count": vr.red_count,
                        "issues": vr.to_dict().get("results", []),
                    }
                elif vr.yellow_count > 0:
                    logger.info(
                        "表单校验有 %d 个黄灯（可继续）: trip=%s",
                        vr.yellow_count, trip_id,
                    )
        except Exception as exc:
            logger.warning("表单校验异常(非阻塞): %s", exc)

        # ── I1: 行程规划管线 ──
        from app.domains.planning_v2.orchestrator import run_planning_v2

        circle_path, plan_id, day_frames, design_brief, runtime_context = await run_planning_v2(
            session, trip, scene,
        )

        # 主链失败即显式失败，不回退旧模板链路
        if not circle_path:
            trip.status = "failed"
            trip.last_job_error = "city_circle_pipeline_failed"
            await session.commit()
            # WeChat Work notification: generation failed (non-blocking)
            try:
                from app.core.wechat_notify import notify_generation_failed
                await notify_generation_failed(
                    trip_id=str(trip_id),
                    error="city_circle_pipeline_failed",
                    step="city_circle_pipeline",
                )
            except Exception:
                pass
            return {"status": "error", "reason": "city_circle_pipeline_failed"}

        run_id = str(runtime_context.get("run_id") or "")
        profile_hash = runtime_context.get("profile_hash")
        enable_live_risk_monitor = bool(runtime_context.get("enable_live_risk_monitor", True))
        travel_date_list: list[Any] = []
        for iso_day in runtime_context.get("travel_date_list") or []:
            try:
                from datetime import date as _date

                travel_date_list.append(_date.fromisoformat(str(iso_day)))
            except Exception:
                continue

        planning_output = None  # 供 step 2.5 / 2.6 使用，避免 step 2 失败时未定义

        # ── Step 2: PlanningOutput → page pipeline（直通，无 report 中间层） ──
        try:
            if not day_frames:
                raise RuntimeError("city_circle_pipeline_missing_day_frames")

            from app.db.models.business import TripProfile as _TP
            from sqlalchemy import select as _sel2
            from app.domains.rendering.planning_output import build_planning_output
            from app.domains.rendering.chapter_planner import plan_chapters
            from app.domains.rendering.page_planner import plan_pages_and_persist
            from app.domains.rendering.page_view_model import build_view_models
            from app.domains.rendering.copy_enrichment import enrich_page_copy
            from app.db.models.derived import ItineraryPlan as _IP

            _pq = await session.execute(
                _sel2(_TP).where(_TP.trip_request_id == trip_id).limit(1)
            )
            _profile = _pq.scalar_one_or_none()

            # 从 pipeline 上下文取 circle_id
            _plan_obj = await session.get(_IP, plan_id)
            _evidence = (_plan_obj.plan_metadata or {}).get("evidence_bundle") if _plan_obj else None
            _circle_id_for_output = (
                (_evidence or {}).get("circle_id")
                or (design_brief.get("route_strategy", [""])[0].split()[-1] if design_brief.get("route_strategy") else "")
            )
            # 从 decisions 表取 circle_id（更可靠）
            try:
                from app.db.models.derived import GenerationDecision
                _cd_q = await session.execute(
                    _sel2(GenerationDecision).where(
                        GenerationDecision.trip_request_id == trip_id,
                        GenerationDecision.stage == "circle_selection",
                        GenerationDecision.key == "selected_circle_id",
                        GenerationDecision.is_current == True,
                    ).limit(1)
                )
                _cd = _cd_q.scalar_one_or_none()
                if _cd and _cd.value:
                    import json as _json
                    _raw = _cd.value
                    if isinstance(_raw, str):
                        try:
                            _raw = _json.loads(_raw)
                        except Exception:
                            pass
                    _circle_id_for_output = str(_raw) if _raw else _circle_id_for_output
            except Exception:
                pass

            # 构建 PlanningOutput（直接从 DB + pipeline 结果，无 AI / 无 report）
            planning_output = await build_planning_output(
                session,
                plan_id=plan_id,
                trip_request_id=trip_id,
                day_frames=day_frames,
                design_brief=design_brief or {},
                circle_id=_circle_id_for_output,
                profile=_profile,
                evidence_bundle=_evidence,
            )

            # Chapter → Page → ViewModel pipeline
            chapters = plan_chapters(planning_output)
            pages = await plan_pages_and_persist(chapters, planning_output, session, plan_id)
            view_models = build_view_models(pages, planning_output)
            if not pages or not view_models:
                raise RuntimeError("page_pipeline_empty")

            # AI 文案填充（可选，失败不阻塞）
            try:
                from app.domains.rendering.page_editing import serialize_page_models
                serialized_vms = serialize_page_models(view_models)
                await enrich_page_copy(serialized_vms, planning_output, session)
                # 回写到 plan_metadata
                if _plan_obj:
                    meta = _plan_obj.plan_metadata or {}
                    meta["page_models"] = serialized_vms
                    _plan_obj.plan_metadata = meta
                    await session.flush()
            except Exception as exc:
                logger.warning("copy enrichment 失败（非致命）: %s", exc)

            # D5: 每日预算估算写入 plan_metadata
            try:
                from app.domains.planning.budget_estimator import attach_budget_to_plan
                _budget_level = getattr(_profile, "budget_level", "mid") or "mid"
                _budget_result = await attach_budget_to_plan(session, plan_id, _budget_level)
                logger.info(
                    "D5 预算估算: plan=%s total_jpy=%s total_cny=%s",
                    plan_id,
                    _budget_result.get("total_jpy"),
                    _budget_result.get("total_cny"),
                )
            except Exception as exc:
                logger.warning("每日预算估算失败（非致命）: %s", exc)

            # 写入 plan_metadata
            if _plan_obj:
                meta = _plan_obj.plan_metadata or {}
                meta["page_pipeline"] = {
                    "chapters": len(chapters),
                    "pages": len(pages),
                    "view_models": len(view_models),
                    "source": "planning_output_direct",
                }
                meta["observation_chain"] = {
                    "run_id": run_id,
                    "decision_surface": "generation_decisions",
                    "handoff_surface": "planning_output_direct",
                    "eval_surface": "offline_eval",
                    "regression_surface": "scripts/run_regression.py",
                    "replay_surface": "scripts/run_regression_md.py",
                    "new_chain_success": True,
                    "legacy_fallback_used": False,
                }
                _plan_obj.plan_metadata = meta
            await write_decision(
                session,
                trip_request_id=trip_id,
                plan_id=plan_id,
                input_hash=profile_hash,
                stage="page_pipeline",
                key="pipeline_result",
                value={
                    "chapters": len(chapters),
                    "pages": len(pages),
                    "view_models": len(view_models),
                    "run_id": run_id,
                    "source": "planning_output_direct",
                },
                reason="page pipeline built from PlanningOutput (no report intermediate)",
            )

            logger.info(
                "L3 page pipeline: plan=%s chapters=%d pages=%d vms=%d (direct)",
                plan_id, len(chapters), len(pages), len(view_models),
            )

            # LiveRiskMonitor 风险扫描
            if enable_live_risk_monitor:
                try:
                    from app.domains.planning.live_risk_monitor import LiveRiskMonitor
                    risk_monitor = LiveRiskMonitor(session)
                    await risk_monitor.load_rules()
                    await risk_monitor.load_rules()
                    risk_alerts = await risk_monitor.evaluate_plan(plan_id, travel_date_list)
                    if risk_alerts:
                        logger.info(
                            "LiveRiskMonitor: plan=%s alerts=%d",
                            plan_id, len(risk_alerts),
                        )
                except Exception as exc:
                    logger.warning("LiveRiskMonitor 扫描失败（非致命）: %s", exc)

            logger.info("page pipeline 完成 plan=%s", plan_id)
        except Exception as exc:
            logger.warning("delivery pipeline 失败，转 failed：trip=%s: %s", trip_id, exc)
            capture_exception_with_context(
                exc, trip_id=trip_request_id, step="delivery_pipeline",
            )
            trip.status = "failed"
            trip.last_job_error = f"delivery_pipeline_failed:{exc}"
            await session.commit()
            # WeChat Work notification: delivery pipeline failed (non-blocking)
            try:
                from app.core.wechat_notify import notify_generation_failed
                await notify_generation_failed(
                    trip_id=str(trip_id),
                    error=str(exc)[:300],
                    step="delivery_pipeline",
                )
            except Exception:
                pass
            return {
                "status": "error",
                "plan_id": str(plan_id) if plan_id else None,
                "run_id": run_id,
                "reason": "delivery_pipeline_failed",
                "error": str(exc),
            }

        # Step 2.3: 预览天标记        try:
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
                        "tags": [],
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

        # Step 2.5: 质量门控（11 条 QTY 硬规则）
        try:
            # 优先从 planning_output 直接构建，避免重新查库
            if planning_output is not None:
                plan_json_for_gate = _plan_json_from_planning_output(planning_output, plan_id)
            else:
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
                # 通知运营
                try:
                    from app.core.wecom_notify import notify_review_required
                    await notify_review_required(
                        trip_request_id=str(trip_id),
                        score=gate_result.score,
                        reason=error_summary[:200],
                    )
                except Exception:
                    pass
                # WeChat Work notification: review needed (non-blocking)
                try:
                    from app.core.wechat_notify import notify_review_needed
                    await notify_review_needed(
                        trip_id=str(trip_id),
                        reason=error_summary[:200],
                        score=gate_result.score,
                    )
                except Exception:
                    pass
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

        # Step 2.6: 离线评测（offline_eval）— 自动评分 + 回归检测
        eval_score_dict = None
        try:
            from app.domains.evaluation.offline_eval import score_plan, EvalCase
            plan_json_for_eval = (
                plan_json_for_gate
                if "plan_json_for_gate" in locals()
                else (_plan_json_from_planning_output(planning_output, plan_id) if planning_output is not None
                      else await _build_plan_json(session, plan_id))
            )

            # 构建评测 case（使用实际画像约束）
            eval_case = EvalCase(
                case_id=f"live_{trip_id}",
                description="live generation",
                user_profile={"scene": scene},
                expected_constraints={
                    "min_days": 1,
                    "max_days": 30,
                },
                plan_json=plan_json_for_eval,
            )
            eval_result = score_plan(plan_json_for_eval, eval_case)
            eval_score_dict = eval_result.to_dict()

            # 写入 plan metadata
            from app.db.models.derived import ItineraryPlan
            plan_obj = await session.get(ItineraryPlan, plan_id)
            if plan_obj:
                meta = plan_obj.plan_metadata or {}
                meta["offline_eval"] = eval_score_dict
                meta["offline_eval_overall"] = eval_result.overall
                observation_chain = dict(meta.get("observation_chain") or {})
                observation_chain["offline_eval_overall"] = eval_result.overall
                observation_chain["offline_eval_case_id"] = eval_case.case_id
                meta["observation_chain"] = observation_chain
                plan_obj.plan_metadata = meta
            await write_decision(
                session,
                trip_request_id=trip_id,
                plan_id=plan_id,
                input_hash=profile_hash,
                stage="offline_eval",
                key="overall",
                value={
                    "overall": eval_result.overall,
                    "run_id": run_id,
                    "case_id": eval_case.case_id,
                },
                reason="offline eval attached to same observation chain",
            )

            logger.info(
                "offline_eval trip=%s overall=%.2f (completeness=%.1f feasibility=%.1f diversity=%.1f)",
                trip_id, eval_result.overall,
                eval_result.completeness, eval_result.feasibility, eval_result.diversity,
            )

            # 离线评分阈值检查：低于 0.70 标记需人工审核
            EVAL_THRESHOLD = 0.70
            if eval_result.overall < EVAL_THRESHOLD:
                logger.warning(
                    "offline_eval 低于阈值 trip=%s overall=%.2f < %.2f，标记需人工审核",
                    trip_id, eval_result.overall, EVAL_THRESHOLD,
                )
                if plan_obj:
                    meta = plan_obj.plan_metadata or {}
                    meta["needs_human_review"] = True
                    meta["low_eval_reason"] = (
                        f"overall={eval_result.overall:.2f} "
                        f"completeness={eval_result.completeness:.1f} "
                        f"feasibility={eval_result.feasibility:.1f} "
                        f"diversity={eval_result.diversity:.1f}"
                    )
                    plan_obj.plan_metadata = meta
        except Exception as exc:
            logger.warning("offline_eval 异常（非致命）trip=%s: %s", trip_id, exc)

        # Step 3: 多模型评审
        if not REVIEW_PIPELINE_ENABLED:
            trip.status = "failed"
            trip.last_job_error = "review_pipeline_disabled"
            await session.commit()
            return {"status": "error", "plan_id": str(plan_id), "reason": "review_pipeline_disabled"}

        try:
            from app.domains.review_ops.pipeline import run_review_with_retry, Verdict

            plan_json = await _build_plan_json(session, plan_id)
            review_context = await _build_review_context(session, trip, scene)

            # 灏濊瘯鑾峰彇 AI client
            ai_client = None
            try:
                from app.core.ai_client import get_openai_client
                ai_client = get_openai_client()
            except Exception:
                logger.warning("AI client unavailable, using rules-only review fallback")

            result = await run_review_with_retry(
                plan_json=plan_json,
                context=review_context,
                ai_client=ai_client,
            )

            # Persist multi-model review report (best effort).
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
                logger.warning("[T22-T25] 四维评审失败（非致命）:  %s", e)

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

            # 评审回写飞轮：issues → 数据层修正            try:
                from app.domains.review_ops.review_writeback import writeback_review_issues
                wb_stats = await writeback_review_issues(
                    session, plan_id=plan_id,
                    trip_request_id=trip_id,
                    pipeline_result=result,
                )
                logger.info("review_writeback: %s", wb_stats)
            except Exception as e:
                logger.warning("review_writeback 失败（非致命）:  %s", e)

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
                # WeChat Work notification: review needed (non-blocking)
                try:
                    from app.core.wechat_notify import notify_review_needed
                    await notify_review_needed(
                        trip_id=str(trip_id),
                        reason=result.final_reason or "review_verdict_human",
                        score=0.0,
                    )
                except Exception:
                    pass
                return {
                    "status": "ok",
                    "plan_id": str(plan_id),
                    "review": "human",
                    "reason": result.final_reason,
                }
            else:
                # REWRITE 已经在 run_review_with_retry 内部处理了                # 到这里说明重写后仍然是 human
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
            capture_exception_with_context(
                exc, trip_id=trip_request_id, step="review_pipeline",
            )
            # review pipeline exception must fail explicitly
            trip.status = "failed"
            trip.last_job_error = f"review_pipeline_exception:{exc}"
            await session.commit()
            # WeChat Work notification: review pipeline failed (non-blocking)
            try:
                from app.core.wechat_notify import notify_generation_failed
                await notify_generation_failed(
                    trip_id=str(trip_id),
                    error=str(exc)[:300],
                    step="review_pipeline",
                )
            except Exception:
                pass
            return {
                "status": "error",
                "plan_id": str(plan_id),
                "run_id": run_id,
                "review": "failed",
                "error": str(exc),
            }





