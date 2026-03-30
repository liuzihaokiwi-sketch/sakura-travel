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


async def _try_city_circle_pipeline(
    session: Any,
    trip: TripRequest,
    scene: str,
) -> tuple[bool, uuid.UUID | None, list | None, dict | None, dict | None]:
    """
    尝试走城市圈决策链路（带 trace）。
    Returns:
        (success, plan_id, day_frames_dicts, design_brief, runtime_context)
        success=False 表示主链失败，需要显式失败返回。    """
    from app.domains.planning.fallback_router import (
        FallbackLevel,
        evaluate_fallback,
    )
    from app.domains.planning.trace_writer import CircleTraceWriter
    from app.domains.planning.decision_writer import (
        write_decision, compute_profile_hash, invalidate_previous_decisions,
    )

    trace: CircleTraceWriter | None = None

    try:
        from app.db.models.business import TripProfile
        from sqlalchemy import select

        # 加载画像
        profile_q = await session.execute(
            select(TripProfile).where(TripProfile.trip_request_id == trip.trip_request_id)
        )
        profile = profile_q.scalar_one_or_none()
        if not profile:
            logger.info("no TripProfile, city-circle main chain failed")
            return False, None, None, None, None

        trip_id = trip.trip_request_id

        # E1: 作废旧决策 + 计算画像哈希
        await invalidate_previous_decisions(session, trip_id)
        canonical_input = build_layer2_profile_contract(profile)
        profile_snapshot = {
            "contract_version": canonical_input.get("contract_version"),
            "requested_city_circle": canonical_input.get("requested_city_circle"),
            "party_type": profile.party_type,
            "duration_days": profile.duration_days,
            "budget_level": profile.budget_level,
            "pace": getattr(profile, "pace", None),
            "arrival_day_shape": getattr(profile, "arrival_day_shape", None),
            "hotel_switch_tolerance": getattr(profile, "hotel_switch_tolerance", None),
            "layer2_canonical_input": canonical_input,
        }
        profile_hash = compute_profile_hash(canonical_input)

        # E1: normalized_profile 快照
        await write_decision(
            session, trip_request_id=trip_id, input_hash=profile_hash,
            stage="normalized_profile", key="profile_snapshot",
            value=profile_snapshot,
            reason="profile normalization completed",
        )
        await write_decision(
            session, trip_request_id=trip_id, input_hash=profile_hash,
            stage="normalized_profile", key="canonical_input",
            value=canonical_input,
            reason="Layer 2 canonical input contract frozen at main-chain entry",
        )

        # 初始化 trace writer
        trace = CircleTraceWriter(session, trip_id)
        await trace.start_run(profile_snapshot=profile_snapshot)

        # Step 1: 城市圈选择
        from app.domains.planning.city_circle_selector import select_city_circle
        async with trace.step("circle_selection") as s:
            circle_result = await select_city_circle(session, profile)
            s.set_output({"selected": circle_result.selected_circle_id})
            s.set_trace(circle_result.trace)

        if not circle_result.selected:
            logger.info("no matched city circle, main chain failed")
            await trace.finish_run(status="failed")
            return False, None, None, None, None

        circle_id = circle_result.selected_circle_id
        set_sentry_context(
            trip_id=str(trip_id), step="city_circle_pipeline", circle_id=circle_id,
        )
        logger.info("选中城市圈  %s (%s)", circle_id, circle_result.selected.name_zh)

        # E1: circle_selection 快照 + E4: explain
        await write_decision(
            session, trip_request_id=trip_id, input_hash=profile_hash,
            stage="circle_selection", key="selected_circle_id",
            value=circle_id,
            alternatives=[
                {"id": c.circle_id, "score": c.total_score,
                 "reason": c.reject_reason or "candidate"}
                for c in circle_result.candidates[:10]
            ],
            reason=(
                f"selected {circle_result.selected.name_zh}, "
                f"score={circle_result.selected.total_score:.3f}"
            ),
        )

        # Step 1a: 加载 ConfigResolver（运营配置中心）
        from app.domains.planning.config_resolver import ConfigResolver
        config_resolver = ConfigResolver(session)
        try:
            resolved_cfg = await config_resolver.resolve(
                circle_id=circle_id,
                segment=getattr(profile, "party_type", None),
            )
            logger.info(
                "[ConfigResolver] 已加载配置 circle=%s segment=%s sources=%d",
                circle_id,
                getattr(profile, "party_type", None),
                len(resolved_cfg.sources),
            )
        except Exception as exc:
            logger.warning("ConfigResolver 加载失败（降级为默认配置）:  %s", exc)
            from app.domains.planning.config_resolver import ResolvedConfig
            resolved_cfg = ResolvedConfig()

        from app.domains.planning.policy_resolver import resolve_policy_set
        resolved_policy = resolve_policy_set(
            circle_id,
            circle=None,
            resolved_config=resolved_cfg,
        )
        await write_decision(
            session,
            trip_request_id=trip_id,
            input_hash=profile_hash,
            stage="resolved_policy",
            key="policy_bundle",
            value=resolved_policy.to_dict(),
            reason="layer2 policy bundle resolved for front-half stages",
        )

        # 开关：是否启用运营干预
        _enable_override = resolved_cfg.switch("enable_operator_override", default=True)

        # Step 1b: 加载 OverrideResolver（L4-02）
        from app.domains.planning.override_resolver import OverrideResolver
        override_resolver = None
        if _enable_override:
            override_resolver = OverrideResolver(session)
            try:
                await override_resolver.load_active()
            except Exception as exc:
                logger.warning("OverrideResolver 加载失败（降级为无干预）: %s", exc)
                override_resolver = None

        # Step 2: 资格过滤
        from app.domains.planning.eligibility_gate import run_eligibility_gate, EligibilityContext
        from app.db.models.city_circles import CityCircle
        circle = await session.get(CityCircle, circle_id)
        resolved_policy = resolve_policy_set(circle_id, circle=circle, resolved_config=resolved_cfg)
        all_cities = list(set((circle.base_city_codes or []) + (circle.extension_city_codes or [])))

        travel_month = None
        travel_dates_raw = getattr(profile, "travel_dates", None) or {}
        if isinstance(travel_dates_raw, dict):
            start_str = travel_dates_raw.get("start", "")
            if start_str and len(start_str) >= 7:
                try:
                    travel_month = int(start_str[5:7])
                except ValueError:
                    pass

        eg_ctx = EligibilityContext(
            circle_id=circle_id,
            city_codes=all_cities,
            avoid_tags=profile.avoid_tags or [],
            party_type=profile.party_type or "couple",
            has_elderly=getattr(profile, "has_elderly", False) or False,
            has_children=getattr(profile, "has_children", False) or False,
            travel_month=travel_month,
        )
        eg_result = await run_eligibility_gate(session, eg_ctx, override_resolver=override_resolver)

        # E1: eligibility 快照
        await write_decision(
            session, trip_request_id=trip_id, input_hash=profile_hash,
            stage="eligibility", key="passed_entity_count",
            value=len(eg_result.passed_entity_ids),
            reason=(
                f"passed entities={len(eg_result.passed_entity_ids)}, "
                f"passed clusters={len(eg_result.passed_cluster_ids)}"
            ),
        )

        # Step 3: precheck gate
        from app.domains.planning.precheck_gate import run_precheck_gate
        from datetime import date, timedelta
        travel_start = None
        if isinstance(travel_dates_raw, dict) and travel_dates_raw.get("start"):
            try:
                from datetime import datetime as _dt
                travel_start = _dt.strptime(travel_dates_raw["start"], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                pass

        days_count = profile.duration_days or 5
        if travel_start:
            travel_date_list = [travel_start + timedelta(days=i) for i in range(days_count)]
        else:
            today = date.today()
            travel_date_list = [today + timedelta(days=30 + i) for i in range(days_count)]

        passed_entity_ids = list(eg_result.passed_entity_ids)
        async with trace.step("precheck_gate") as s:
            pc_result = await run_precheck_gate(session, passed_entity_ids, travel_date_list)
            s.set_output({"failed": len(pc_result.failed_ids), "warned": len(pc_result.warned_ids)})
            s.set_trace(pc_result.trace)

        # ── Step 3b: 缂栬瘧缁熶竴绾︽潫 ──
        from app.domains.planning.constraint_compiler import compile_constraints
        constraints = compile_constraints(profile, resolved_policy=resolved_policy)
        # 同源锁步：run_id 贯穿全链路
        _run_id = constraints.run_id
        logger.info("同源 run_id=%s plan 将绑定此 ID", _run_id[:8])

        # Step 4: 主要活动排序
        from app.domains.planning.major_activity_ranker import rank_major_activities
        async with trace.step("major_ranking") as s:
            ranking_result = await rank_major_activities(
                session=session,
                circle_id=circle_id,
                profile=profile,
                passed_cluster_ids=eg_result.passed_cluster_ids,
                precheck_failed_entity_ids=pc_result.failed_ids,
                override_resolver=override_resolver,
                constraints=constraints,
            )
            s.set_output({
                "selected": len(ranking_result.selected_majors),
                "capacity": f"{ranking_result.capacity_used}/{ranking_result.capacity_total}",
            })
            s.set_trace(ranking_result.trace)

        # E1: major_ranking 快照 + E4: explain (why_selected / why_not)
        await write_decision(
            session, trip_request_id=trip_id, input_hash=profile_hash,
            stage="major_activity_plan", key="selected_majors",
            value=[m.cluster_id for m in ranking_result.selected_majors],
            alternatives=[
                {"id": r.cluster_id, "score": r.major_score,
                 "selected": r.selected,
                 "reason": r.selection_reason,
                 "base_quality": r.base_quality_score,
                 "context_fit": r.context_fit_score}
                for r in ranking_result.all_ranked
            ],
            reason=f"选中 {len(ranking_result.selected_majors)} 个主活动, "
                   f"容量 {ranking_result.capacity_used:.1f}/{ranking_result.capacity_total:.1f}",
        )

        # E2: fallback evaluation
        fallback = evaluate_fallback(
            circle_found=True,
            cluster_count=len(eg_result.passed_cluster_ids),
            selected_major_count=len(ranking_result.selected_majors),
        )
        if getattr(ranking_result, "must_go_unresolved", None):
            unresolved = list(ranking_result.must_go_unresolved)
            if fallback.level == FallbackLevel.NONE:
                fallback.level = FallbackLevel.PAYLOAD_INCOMPATIBLE
            fallback.reasons.append(
                f"F-MUSTGO: unresolved must-go places={unresolved}"
            )
            await write_decision(
                session,
                trip_request_id=trip_id,
                input_hash=profile_hash,
                stage="fallback",
                key="must_go_unresolved",
                value=unresolved,
                reason="must-go items unresolved in current circle candidates; main chain must fail explicitly",
            )

        if fallback.level != FallbackLevel.NONE:
            logger.info("城市圈主链显式失败: level=%s reasons=%s", fallback.level, fallback.reasons)
            await write_decision(
                session, trip_request_id=trip_id, input_hash=profile_hash,
                stage="fallback", key="level",
                value=fallback.level.value,
                reason="; ".join(fallback.reasons) if fallback.reasons else "main_chain_explicit_failure",
            )
            await trace.finish_run(status="failed")
            return False, None, None, None, None

        # Step 5: 閰掑簵绛栫暐
        from app.domains.planning.hotel_base_builder import build_hotel_strategy
        selected_cluster_ids = [m.cluster_id for m in ranking_result.selected_majors]
        async with trace.step("hotel_strategy") as s:
            hotel_result = await build_hotel_strategy(
                session=session,
                circle_id=circle_id,
                profile=profile,
                selected_cluster_ids=selected_cluster_ids,
                resolved_policy=resolved_policy,
                constraints=constraints,
            )
            s.set_output({
                "preset": hotel_result.preset_name,
                "bases": len(hotel_result.bases),
                "last_night_safe": hotel_result.last_night_safe,
            })
            s.set_trace(hotel_result.trace)

        # E1: hotel_strategy 快照
        await write_decision(
            session, trip_request_id=trip_id, input_hash=profile_hash,
            stage="hotel_strategy", key="preset_name",
            value=hotel_result.preset_name,
            alternatives=[{
                "bases": len(hotel_result.bases),
                "switch_count": hotel_result.switch_count,
                "last_night_safe": hotel_result.last_night_safe,
                "airport_minutes": hotel_result.last_night_airport_minutes,
            }],
            reason=f"住法: {hotel_result.preset_name or '默认'}, "
                   f"{len(hotel_result.bases)} 鍩虹偣, "
                   f"last_night_safe={hotel_result.last_night_safe}",
        )

        # Step 6: 骨架构建
        from app.domains.planning.route_skeleton_builder import build_route_skeleton
        async with trace.step("skeleton_build") as s:
            skeleton = build_route_skeleton(
                duration_days=days_count,
                selected_majors=ranking_result.selected_majors,
                hotel_bases=hotel_result.bases,
                pace=profile.pace or "moderate",
                wake_up_time=profile.wake_up_time or "normal",
                constraints=constraints,
                resolved_policy=resolved_policy,
                booked_items=getattr(profile, "booked_items", None) or [],
            )
            s.set_output({"days": len(skeleton.frames)})
            s.set_trace(skeleton.trace)

        # E1: skeleton 快照
        await write_decision(
            session, trip_request_id=trip_id, input_hash=profile_hash,
            stage="day_frame", key="skeleton_summary",
            value={
                "days": len(skeleton.frames),
                "corridors": [f.primary_corridor for f in skeleton.frames],
                "drivers": [f.main_driver for f in skeleton.frames],
                "intensity": [f.intensity for f in skeleton.frames],
                "booking_alerts": skeleton.booking_alerts,
                "degraded_majors": skeleton.degraded_majors,
            },
            reason=f"楠ㄦ灦 {len(skeleton.frames)} 澶? "
                   f"pace={profile.pace or 'moderate'}",
        )

        # ── Step 6b: 初始化 CorridorResolver ──
        from app.domains.planning.corridor_resolver import CorridorResolver
        corridor_resolver = CorridorResolver(session)
        try:
            await corridor_resolver.load_cache()
        except Exception as exc:
            logger.warning("CorridorResolver 加载失败（降级为字符串匹配）: %s", exc)
            corridor_resolver = None

        # 提前构建 profile_dict（供 secondary_filler 和 meal_filler 共用）
        profile_dict = {
            "party_type": profile.party_type,
            "pace": profile.pace or "moderate",
            "budget_level": profile.budget_level,
        }

        # ── Step 7: 次要活动填充 ──
        from app.domains.planning.secondary_filler import fill_secondary_activities
        secondary_fills = []
        async with trace.step("secondary_fill") as s:
            try:
                # 构建候选池：circle_entity_roles + entity_base 直接补充
                from app.db.models.city_circles import CircleEntityRole
                from app.db.models.catalog import EntityBase, Poi
                # 1. 从 circle_entity_roles 拿有绑定的 POI
                role_q = await session.execute(
                    select(CircleEntityRole, EntityBase).join(
                        EntityBase, CircleEntityRole.entity_id == EntityBase.entity_id
                    ).where(
                        CircleEntityRole.circle_id == circle_id,
                        CircleEntityRole.entity_id.in_(eg_result.passed_entity_ids),
                        EntityBase.entity_type.in_(["poi", "activity"]),
                    )
                )
                candidate_pool = []
                _seen_poi_ids = set()
                for role, ent in role_q.all():
                    _seen_poi_ids.add(ent.entity_id)
                    candidate_pool.append({
                        "entity_id": str(ent.entity_id),
                        "name_zh": ent.name_zh,
                        "name_en": ent.name_en,
                        "entity_type": ent.entity_type,
                        "city_code": ent.city_code,
                        "lat": float(ent.lat) if ent.lat else None,
                        "lng": float(ent.lng) if ent.lng else None,
                        "area_name": ent.area_name,
                        "corridor_tags": ent.corridor_tags or [],
                        "final_score": getattr(ent, "google_rating", None) and float(ent.google_rating) * 20 or 50.0,
                        "base_score": getattr(ent, "google_rating", None) and float(ent.google_rating) * 20 or 50.0,
                        "data_tier": getattr(ent, "data_tier", "A"),
                        "sub_category": getattr(ent, "sub_category", None),
                        "typical_duration_min": getattr(ent, "typical_duration_min", 60),
                    })

                # 2. 如果候选池太小（<20），从 entity_base 按城市直接补充 POI
                if len(candidate_pool) < 20:
                    _circle_cities = set()
                    if circle and circle.base_city_codes:
                        _circle_cities.update(circle.base_city_codes)
                    if _circle_cities:
                        _extra_poi_q = await session.execute(
                            select(EntityBase, Poi).join(
                                Poi, Poi.entity_id == EntityBase.entity_id
                            ).where(
                                EntityBase.entity_type == "poi",
                                EntityBase.is_active == True,
                                EntityBase.city_code.in_(list(_circle_cities)),
                                EntityBase.entity_id.notin_(list(_seen_poi_ids)) if _seen_poi_ids else True,
                            ).order_by(Poi.google_rating.desc().nullslast())
                            .limit(50)
                        )
                        for ent, poi in _extra_poi_q.all():
                            candidate_pool.append({
                                "entity_id": str(ent.entity_id),
                                "name_zh": ent.name_zh,
                                "name_en": ent.name_en,
                                "entity_type": ent.entity_type,
                                "city_code": ent.city_code,
                                "lat": float(ent.lat) if ent.lat else None,
                                "lng": float(ent.lng) if ent.lng else None,
                                "area_name": ent.area_name,
                                "corridor_tags": ent.corridor_tags or [],
                                "final_score": float(poi.google_rating) * 20 if poi.google_rating else 50.0,
                                "data_tier": getattr(ent, "data_tier", "A"),
                                "sub_category": poi.poi_category,
                                "typical_duration_min": poi.typical_duration_min or 60,
                            })
                        logger.info("POI候选池补充: roles=%d + entity_base=%d = %d",
                                    len(_seen_poi_ids), len(candidate_pool) - len(_seen_poi_ids), len(candidate_pool))

                # 已被 major 占用的实体
                used_ids = set()
                for m in ranking_result.selected_majors:
                    for eid in m.anchor_entity_ids:
                        used_ids.add(str(eid))

                secondary_fills = fill_secondary_activities(
                    frames=skeleton.frames,
                    candidate_pool=candidate_pool,
                    trip_profile=profile_dict,
                    already_used_ids=used_ids,
                    corridor_resolver=corridor_resolver,
                    override_resolver=override_resolver,
                    constraints=constraints,
                )
                s.set_output({"days_filled": len(secondary_fills),
                              "total_items": sum(len(d.secondary_items) for d in secondary_fills)})
            except Exception as exc:
                logger.warning("secondary_filler 失败（继续）: %s", exc)
                s.set_output({"error": str(exc)})

        # ── Step 8: 餐厅填充 ──
        from app.domains.planning.meal_flex_filler import fill_meals
        meal_fills = []
        async with trace.step("meal_fill") as s:
            try:
                # 构建餐厅候选池
                # 1. 从 circle_entity_roles 拿有角色绑定的餐厅
                rest_q = await session.execute(
                    select(CircleEntityRole, EntityBase).join(
                        EntityBase, CircleEntityRole.entity_id == EntityBase.entity_id
                    ).where(
                        CircleEntityRole.circle_id == circle_id,
                        CircleEntityRole.entity_id.in_(eg_result.passed_entity_ids),
                        EntityBase.entity_type == "restaurant",
                    )
                )
                restaurant_pool = []
                _seen_rest_ids = set()
                for role, ent in rest_q.all():
                    _seen_rest_ids.add(ent.entity_id)
                    restaurant_pool.append({
                        "entity_id": str(ent.entity_id),
                        "name_zh": ent.name_zh,
                        "entity_type": "restaurant",
                        "city_code": ent.city_code,
                        "lat": float(ent.lat) if ent.lat else None,
                        "lng": float(ent.lng) if ent.lng else None,
                        "area_name": ent.area_name,
                        "corridor_tags": ent.corridor_tags or [],
                        "cuisine_type": getattr(ent, "cuisine_type", None),
                        "tabelog_score": getattr(ent, "tabelog_score", None),
                        "final_score": (getattr(ent, "tabelog_score", 3.5) or 3.5) * 20,
                        "price_band": getattr(ent, "price_band", None),
                        "meal_style": role.role_notes or "route_meal",
                        "role": role.role,
                        "is_active": True,
                    })

                # 2. 如果角色绑定的餐厅太少（<10），直接从 entity_base 按城市补充
                if len(restaurant_pool) < 10:
                    from app.db.models.catalog import Restaurant
                    _circle_cities = set()
                    for _f in skeleton.frames:
                        _sc = getattr(_f, 'sleep_base', '') or getattr(_f, 'primary_corridor', '') or ''
                        if _sc:
                            _circle_cities.add(_sc)
                    # 也从 circle 的 base_city_codes 拿
                    if circle and circle.base_city_codes:
                        for _cc in circle.base_city_codes:
                            _circle_cities.add(_cc)
                    if _circle_cities:
                        _extra_rest_q = await session.execute(
                            select(EntityBase, Restaurant).join(
                                Restaurant, Restaurant.entity_id == EntityBase.entity_id
                            ).where(
                                EntityBase.entity_type == "restaurant",
                                EntityBase.is_active == True,
                                EntityBase.city_code.in_(list(_circle_cities)),
                                EntityBase.entity_id.notin_(list(_seen_rest_ids)) if _seen_rest_ids else True,
                            ).order_by(Restaurant.tabelog_score.desc().nullslast())
                            .limit(50)
                        )
                        for ent, rest in _extra_rest_q.all():
                            restaurant_pool.append({
                                "entity_id": str(ent.entity_id),
                                "name_zh": ent.name_zh,
                                "entity_type": "restaurant",
                                "city_code": ent.city_code,
                                "lat": float(ent.lat) if ent.lat else None,
                                "lng": float(ent.lng) if ent.lng else None,
                                "area_name": ent.area_name,
                                "corridor_tags": ent.corridor_tags or [],
                                "cuisine_type": rest.cuisine_type,
                                "tabelog_score": float(rest.tabelog_score) if rest.tabelog_score else None,
                                "final_score": (float(rest.tabelog_score) if rest.tabelog_score else 3.5) * 20,
                                "is_active": True,
                            })
                        logger.info("餐厅候选池补充: circle_roles=%d + entity_base=%d = %d",
                                    len(_seen_rest_ids), len(restaurant_pool) - len(_seen_rest_ids), len(restaurant_pool))

                meal_fills = fill_meals(
                    frames=skeleton.frames,
                    restaurant_pool=restaurant_pool,
                    trip_profile=profile_dict,
                    corridor_resolver=corridor_resolver,
                    constraints=constraints,
                )
                s.set_output({"days_filled": len(meal_fills),
                              "total_meals": sum(len(d.meals) for d in meal_fills)})
            except Exception as exc:
                logger.warning("meal_filler 失败（继续）: %s", exc)
                s.set_output({"error": str(exc)})

        # ── Step 9: 日内适配评分 + 替换建议 ──
        from app.domains.planning.itinerary_fit_scorer import (
            compute_itinerary_fit_async, suggest_swaps,
            SlotContext, EntityFitSignals,
        )
        fit_scores = []
        swap_suggestions = []
        async with trace.step("itinerary_fit") as s:
            try:
                for frame in skeleton.frames:
                    slot_ctx = SlotContext(
                        day_index=frame.day_index,
                        slot_index=0,
                        primary_corridor=frame.primary_corridor,
                        secondary_corridor=frame.secondary_corridor or "",
                        slot_time_hint=("14:00" if frame.day_type == "arrival"
                                        else "08:30" if frame.day_type == "departure"
                                        else "09:30"),
                        transfer_budget_remaining=frame.transfer_budget_minutes,
                        prev_entity_area="",
                        next_entity_area="",
                    )

                    # 收集该天的 secondary 实体
                    day_sec = next((sf for sf in secondary_fills if sf.day_index == frame.day_index), None)
                    if day_sec:
                        day_signals = []
                        prev_eid = None
                        for ent in day_sec.secondary_items:
                            sig = EntityFitSignals(
                                entity_id=ent.get("entity_id"),
                                prev_entity_id=prev_eid,
                                entity_area=ent.get("area_name", ""),
                                entity_type=ent.get("entity_type", "poi"),
                                entity_corridor_tags=ent.get("corridor_tags", []),
                                estimated_transit_min=15,
                                typical_duration_min=ent.get("typical_duration_min", 60),
                            )
                            fit = await compute_itinerary_fit_async(
                                slot_ctx, sig, session, corridor_resolver
                            )
                            fit_scores.append(fit)
                            day_signals.append(sig)
                            prev_eid = ent.get("entity_id")

                        # 替换建议
                        if day_signals:
                            swaps = await suggest_swaps(
                                slot_ctx, day_signals, candidate_pool, session, corridor_resolver
                            )
                            swap_suggestions.extend(swaps)

                s.set_output({
                    "total_scored": len(fit_scores),
                    "swap_suggestions": len(swap_suggestions),
                    "avg_fit": round(sum(f.itinerary_fit_score for f in fit_scores) / max(1, len(fit_scores)), 1),
                })
            except Exception as exc:
                logger.warning("itinerary_fit 评分失败（继续）: %s", exc)
                s.set_output({"error": str(exc)})

        # E1: secondary + meal + fit 快照
        await write_decision(
            session, trip_request_id=trip_id, input_hash=profile_hash,
            stage="filler_summary", key="secondary_meal_fit",
            value={
                "secondary_items": sum(len(d.secondary_items) for d in secondary_fills),
                "meal_items": sum(len(d.meals) for d in meal_fills),
                "fit_scored": len(fit_scores),
                "swap_suggestions": len(swap_suggestions),
            },
            reason="填充+评分完成",
        )

        # 转换 day_frames 为 dict 列表
        import dataclasses
        frame_dicts = []
        for f in skeleton.frames:
            fd = dataclasses.asdict(f)
            frame_dicts.append(fd)

        # 构建 design_brief 从决策链结果
        design_brief = {
            "route_strategy": [
                f"城市圈: {circle_result.selected.name_zh}",
                f"主要活动: {', '.join(m.name_zh for m in ranking_result.selected_majors[:5])}",
            ],
            "tradeoffs": [t for t in ranking_result.trace if "capacity" in t.lower()],
            "stay_strategy": [
                f"hotel strategy: {hotel_result.preset_name or 'default'}",
            ],
            "budget_strategy": [f"预算档位: {profile.budget_level or 'mid'}"],
            "execution_principles": [
                f"节奏: {profile.pace or 'moderate'}",
                f"容量: {ranking_result.capacity_used:.1f}/{ranking_result.capacity_total:.1f}",
            ],
        }

        # ── E6b: 使用 timeline_filler 时间线填充 ──
        from app.domains.planning.itinerary_builder import CIRCLE_WRITE_MODE
        from app.domains.planning.timeline_filler import fill_and_write_timeline
        from app.db.models.derived import ItineraryPlan

        if CIRCLE_WRITE_MODE == "live":
            logger.info("E6b: timeline_filler 时间线填充")

            # 创建 plan 记录
            plan = ItineraryPlan(trip_request_id=trip_id, status="draft")
            session.add(plan)
            await session.flush()
            plan_id = plan.plan_id

            live_result = await fill_and_write_timeline(
                session=session,
                plan_id=plan_id,
                frames=skeleton.frames,
                poi_pool=candidate_pool,
                restaurant_pool=restaurant_pool,
                profile=profile_dict,
                ranking_result=ranking_result,
                hotel_result=hotel_result,
            )
            logger.info(
                "E6b timeline: plan=%s days=%s items=%s",
                plan_id, live_result.get("days_created"), live_result.get("items_created"),
            )

            # ── 推荐轮转：递增被选入行程的实体推荐计数 ──
            try:
                from app.domains.ranking.rotation import increment_recommendation
                from app.db.models.derived import (
                    ItineraryDay as _RotDay,
                    ItineraryItem as _RotItem,
                )

                _rot_items_q = await session.execute(
                    select(_RotItem)
                    .join(_RotDay, _RotItem.day_id == _RotDay.day_id)
                    .where(_RotDay.plan_id == plan_id)
                )
                _rotation_entity_ids = list({
                    item.entity_id
                    for item in _rot_items_q.scalars().all()
                    if item.entity_id
                })
                if _rotation_entity_ids:
                    await increment_recommendation(session, _rotation_entity_ids)
                    logger.info(
                        "推荐轮转计数更新: %d 个实体", len(_rotation_entity_ids),
                    )
            except Exception as _rot_exc:
                logger.warning("推荐轮转计数更新失败（非致命）: %s", _rot_exc)
        else:
            logger.warning("CIRCLE_WRITE_MODE=%s 非 live，按旧链清退策略显式失败", CIRCLE_WRITE_MODE)
            if trace:
                await trace.finish_run(status="failed")
            return False, None, None, None, None

        # E1: 回写 plan_id 到本次所有 decisions
        try:
            from sqlalchemy import update as _update
            from app.db.models.derived import GenerationDecision
            await session.execute(
                _update(GenerationDecision)
                .where(
                    GenerationDecision.trip_request_id == trip_id,
                    GenerationDecision.is_current == True,
                    GenerationDecision.plan_id.is_(None),
                )
                .values(plan_id=plan_id)
            )
            await session.flush()
        except Exception:
            pass

        # ── fit scorer 结果持久化 ──
        if fit_scores or swap_suggestions:
            try:
                from app.db.models.derived import ItineraryPlan
                _plan_obj = await session.get(ItineraryPlan, plan_id)
                if _plan_obj:
                    meta = _plan_obj.plan_metadata or {}
                    avg_fit = round(sum(f.itinerary_fit_score for f in fit_scores) / max(1, len(fit_scores)), 1) if fit_scores else 0
                    meta["fit_scoring"] = {
                        "avg_fit_score": avg_fit,
                        "total_scored": len(fit_scores),
                        "swap_suggestion_count": len(swap_suggestions),
                    }
                    _plan_obj.plan_metadata = meta
                    await session.flush()
            except Exception as _fit_exc:
                logger.warning("fit scorer 结果写入失败（非致命）: %s", _fit_exc)

        # ── constraint_trace finalize + evidence_bundle 钀藉簱 ──
        constraints.finalize_trace()

        _unconsumed_hard = constraints.hard_unconsumed()
        if _unconsumed_hard:
            logger.warning("鈿狅笍 unconsumed hard constraints: %s (run_id=%s)",
                           [u.constraint_name for u in _unconsumed_hard], _run_id[:8])

        try:
            from app.db.models.derived import ItineraryPlan as _IPlan
            _plan_for_trace = await session.get(_IPlan, plan_id)
            if _plan_for_trace:
                _meta = _plan_for_trace.plan_metadata or {}
                _meta["evidence_bundle"] = constraints.to_evidence_dict(
                    plan_id=str(plan_id),
                    request_id=str(trip_id),
                    input_contract=canonical_input,
                )
                _plan_for_trace.plan_metadata = _meta
                await session.flush()
                logger.info("evidence_bundle 钀藉簱: plan=%s run_id=%s items=%d unconsumed_hard=%d",
                            plan_id, _run_id[:8],
                            len(constraints.constraint_trace), len(_unconsumed_hard))
        except Exception as _exc:
            logger.warning("evidence_bundle 落库失败（非致命）:  %s", _exc)

        # 更新 trace 的 plan_id
        if trace._run:
            trace._run.plan_id = plan_id
        await trace.finish_run(status="completed")

        logger.info(
            "城市圈链路成功:  circle=%s majors=%d hotel=%s skeleton=%d days",
            circle_id, len(ranking_result.selected_majors),
            hotel_result.preset_name, len(skeleton.frames),
        )

        runtime_context = {
            "run_id": _run_id,
            "profile_hash": profile_hash,
            "travel_date_list": [d.isoformat() for d in travel_date_list],
            "enable_live_risk_monitor": bool(
                resolved_cfg.switch("enable_live_risk_monitor", default=True)
            ),
        }
        return True, plan_id, frame_dicts, design_brief, runtime_context

    except Exception as exc:
        logger.warning("城市圈链路异常，主链失败: %s", exc, exc_info=True)
        capture_exception_with_context(
            exc,
            trip_id=str(trip.trip_request_id),
            step="city_circle_pipeline",
            circle_id=locals().get("circle_id"),
        )
        if trace:
            try:
                await trace.finish_run(status="failed")
            except Exception:
                pass
        return False, None, None, None, None


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

        # ── I1: 尝试城市圈链路 ──
        plan_id = None
        day_frames = None
        design_brief = None
        runtime_context: dict[str, Any] = {}
        circle_path = False

        circle_path, plan_id, day_frames, design_brief, runtime_context = await _try_city_circle_pipeline(
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





