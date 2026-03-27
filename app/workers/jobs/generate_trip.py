"""
arq Job: generate_trip
瑙﹀彂琛岀▼瑁呴厤 鈫?AI 鏂囨娑﹁壊 鈫?澶氭ā鍨嬭瘎瀹?鈫?鍙戝竷/閲嶅啓/杞汉宸?
娴佺▼锛?    city-circle pipeline 鈫?enrich_itinerary_with_copy
    鈫?run_review_with_retry
        鈫?publish  鈫?鏍囪 delivered锛屽叆闃熸覆鏌?        鈫?rewrite  鈫?鑷姩閲嶅啓鍙楀奖鍝嶅ぉ锛堟渶澶?2 杞級
        鈫?human    鈫?鏍囪 review锛屽叆闃熶汉宸ュ鏍?"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from app.core.queue import enqueue_job
from app.db.models.business import TripRequest
from app.db.session import AsyncSessionLocal as async_session_factory
from app.domains.intake.layer2_contract import build_layer2_profile_contract
from app.domains.planning.assembler import enrich_itinerary_with_copy
from app.core.quality_gate import run_quality_gate, QualityGateResult

logger = logging.getLogger(__name__)

# Feature flags
REVIEW_PIPELINE_ENABLED = True
CITY_CIRCLE_ENABLED = True  # 鍩庡競鍦堥摼璺紑鍏筹紙False 鏃舵樉寮忓け璐ワ級


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
                "time": "",  # 浠?slot 鎺ㄦ柇
                "name": "鏈煡",
                "entity_type": item.item_type or "poi",
                "entity_id": str(item.entity_id) if item.entity_id else None,
            }
            if item.entity_id:
                entity = await session.get(EntityBase, item.entity_id)
                if entity:
                    item_dict["name"] = entity.name_local or entity.name or "鏈煡"
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
    """Build runtime review context from plan/profile/ops surfaces."""
    from sqlalchemy import select as _sel
    from datetime import datetime as _dt, timezone as _tz, timedelta as _td

    context: dict[str, Any] = {
        "segment": scene,
        "travel_date": "鏈煡",
    }

    # 鏃呰鏃ユ湡
    travel_start: Any = None
    if hasattr(trip, "travel_start_date") and trip.travel_start_date:
        travel_start = trip.travel_start_date
        context["travel_date"] = str(travel_start)

    # 1. entity_operating_facts
    try:
        from app.db.models.derived import ItineraryPlan, ItineraryItem
        from app.db.models.soft_rules import EntityOperatingFact

        # 鎵炬渶杩戠殑涓€涓?plan
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
                warnings = [
                    f"{f.fact_key}={f.fact_value} (entity={f.entity_id})"
                    for f in facts
                    if (f.fact_value or "").lower() in (
                        "permanently_closed", "long_term_closed",
                        "temporarily_closed", "limited_hours",
                    )
                ]
                context["operational_context"] = "; ".join(warnings) if warnings else "no_operational_alerts"
            else:
                context["operational_context"] = "no_entities"
        else:
            context["operational_context"] = "no_plan_data"
    except Exception as exc:
        logger.warning("_build_review_context: entity_operating_facts 鏌ヨ澶辫触: %s", exc)
        context["operational_context"] = "鏌ヨ澶辫触"

    # 2. seasonal_events锛氭媺鍙栨梾琛屾棩鏈熷墠鍚?30 澶╁唴鐨勫鑺傛椿鍔?    try:
        from app.db.models.soft_rules import SeasonalEvent

        if travel_start:
            # 鍏煎 date / datetime
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
        logger.warning("_build_review_context: seasonal_events 鏌ヨ澶辫触: %s", exc)
        context["seasonal_events"] = "鏌ヨ澶辫触"

    return context


async def _try_city_circle_pipeline(
    session: Any,
    trip: TripRequest,
    scene: str,
) -> tuple[bool, uuid.UUID | None, list | None, dict | None]:
    """
    灏濊瘯璧板煄甯傚湀鍐崇瓥閾捐矾锛堝甫 trace锛夈€?
    Returns:
        (success, plan_id, day_frames_dicts, design_brief)
        success=False 琛ㄧず涓婚摼澶辫触锛岄渶瑕佹樉寮忓け璐ヨ繑鍥炪€?    """
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

        # 鍔犺浇鐢诲儚
        profile_q = await session.execute(
            select(TripProfile).where(TripProfile.trip_request_id == trip.trip_request_id)
        )
        profile = profile_q.scalar_one_or_none()
        if not profile:
            logger.info("no TripProfile, city-circle main chain failed")
            return False, None, None, None

        trip_id = trip.trip_request_id

        # E1: 浣滃簾鏃у喅绛?+ 璁＄畻鐢诲儚鍝堝笇
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

        # E1: normalized_profile 蹇収
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

        # 鍒濆鍖?trace writer
        trace = CircleTraceWriter(session, trip_id)
        await trace.start_run(profile_snapshot=profile_snapshot)

        # Step 1: 鍩庡競鍦堥€夋嫨
        from app.domains.planning.city_circle_selector import select_city_circle
        async with trace.step("circle_selection") as s:
            circle_result = await select_city_circle(session, profile)
            s.set_output({"selected": circle_result.selected_circle_id})
            s.set_trace(circle_result.trace)

        if not circle_result.selected:
            logger.info("no matched city circle, main chain failed")
            await trace.finish_run(status="failed")
            return False, None, None, None

        circle_id = circle_result.selected_circle_id
        logger.info("閫変腑鍩庡競鍦? %s (%s)", circle_id, circle_result.selected.name_zh)

        # E1: circle_selection 蹇収 + E4: explain
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

        # Step 1a: 鍔犺浇 ConfigResolver锛堣繍钀ラ厤缃腑蹇冿級
        from app.domains.planning.config_resolver import ConfigResolver
        config_resolver = ConfigResolver(session)
        try:
            resolved_cfg = await config_resolver.resolve(
                circle_id=circle_id,
                segment=getattr(profile, "party_type", None),
            )
            logger.info(
                "[ConfigResolver] 宸插姞杞介厤缃?circle=%s segment=%s sources=%d",
                circle_id,
                getattr(profile, "party_type", None),
                len(resolved_cfg.sources),
            )
        except Exception as exc:
            logger.warning("ConfigResolver 鍔犺浇澶辫触锛堥檷绾т负榛樿閰嶇疆锛? %s", exc)
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

        # 寮€鍏筹細鏄惁鍚敤杩愯惀骞查
        _enable_override = resolved_cfg.switch("enable_operator_override", default=True)

        # Step 1b: 鍔犺浇 OverrideResolver锛圠4-02锛?        from app.domains.planning.override_resolver import OverrideResolver
        override_resolver = None
        if _enable_override:
            override_resolver = OverrideResolver(session)
            try:
                await override_resolver.load_active()
            except Exception as exc:
                logger.warning("OverrideResolver 鍔犺浇澶辫触锛堥檷绾т负鏃犲共棰勶級: %s", exc)
                override_resolver = None

        # Step 2: 璧勬牸杩囨护
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

        # E1: eligibility 蹇収
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

        # 鈹€鈹€ Step 3b: 缂栬瘧缁熶竴绾︽潫 鈹€鈹€
        from app.domains.planning.constraint_compiler import compile_constraints
        constraints = compile_constraints(profile, resolved_policy=resolved_policy)
        # 鍚屾簮閿佹锛歳un_id 璐┛鍏ㄩ摼璺?        _run_id = constraints.run_id
        logger.info("鍚屾簮 run_id=%s plan 灏嗙粦瀹氭 ID", _run_id[:8])

        # Step 4: 涓昏娲诲姩鎺掑簭
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

        # E1: major_ranking 蹇収 + E4: explain (why_selected / why_not)
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
            reason=f"閫変腑 {len(ranking_result.selected_majors)} 涓富娲诲姩, "
                   f"瀹归噺 {ranking_result.capacity_used:.1f}/{ranking_result.capacity_total:.1f}",
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
                fallback.level = FallbackLevel.SECTION_ADAPTER
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
            return False, None, None, None

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

        # E1: hotel_strategy 蹇収
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
            reason=f"浣忔硶: {hotel_result.preset_name or '榛樿'}, "
                   f"{len(hotel_result.bases)} 鍩虹偣, "
                   f"last_night_safe={hotel_result.last_night_safe}",
        )

        # Step 6: 楠ㄦ灦鏋勫缓
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

        # E1: skeleton 蹇収
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

        # 鈹€鈹€ Step 6b: 鍒濆鍖?CorridorResolver 鈹€鈹€
        from app.domains.planning.corridor_resolver import CorridorResolver
        corridor_resolver = CorridorResolver(session)
        try:
            await corridor_resolver.load_cache()
        except Exception as exc:
            logger.warning("CorridorResolver 鍔犺浇澶辫触锛堥檷绾т负瀛楃涓插尮閰嶏級: %s", exc)
            corridor_resolver = None

        # 鈹€鈹€ Step 7: 娆¤娲诲姩濉厖 鈹€鈹€
        from app.domains.planning.secondary_filler import fill_secondary_activities
        secondary_fills = []
        async with trace.step("secondary_fill") as s:
            try:
                # 鏋勫缓鍊欓€夋睜锛歝ircle 鍐呴€氳繃 eligibility 鐨?POI
                from app.db.models.city_circles import CircleEntityRole
                from app.db.models.catalog import EntityBase
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
                for role, ent in role_q.all():
                    candidate_pool.append({
                        "entity_id": str(ent.entity_id),
                        "name_zh": ent.name_zh,
                        "name_en": ent.name_en,
                        "entity_type": ent.entity_type,
                        "area_name": ent.area_name,
                        "corridor_tags": ent.corridor_tags or [],
                        "final_score": ent.google_rating * 20 if ent.google_rating else 50.0,
                        "base_score": ent.google_rating * 20 if ent.google_rating else 50.0,
                        "data_tier": getattr(ent, "data_tier", "A"),
                        "sub_category": ent.sub_category,
                        "typical_duration_min": getattr(ent, "typical_duration_min", 60),
                    })

                # 宸茶 major 鍗犵敤鐨勫疄浣?                used_ids = set()
                for m in ranking_result.selected_majors:
                    for eid in m.anchor_entity_ids:
                        used_ids.add(str(eid))

                profile_dict = {
                    "party_type": profile.party_type,
                    "pace": profile.pace or "moderate",
                    "budget_level": profile.budget_level,
                }

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
                logger.warning("secondary_filler 澶辫触锛堢户缁級: %s", exc)
                s.set_output({"error": str(exc)})

        # 鈹€鈹€ Step 8: 椁愬巺濉厖 鈹€鈹€
        from app.domains.planning.meal_flex_filler import fill_meals
        meal_fills = []
        async with trace.step("meal_fill") as s:
            try:
                # 鏋勫缓椁愬巺鍊欓€夋睜
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
                for role, ent in rest_q.all():
                    restaurant_pool.append({
                        "entity_id": str(ent.entity_id),
                        "name_zh": ent.name_zh,
                        "entity_type": "restaurant",
                        "area_name": ent.area_name,
                        "corridor_tags": ent.corridor_tags or [],
                        "cuisine_type": getattr(ent, "cuisine_type", None),
                        "tabelog_score": getattr(ent, "tabelog_score", None),
                        "final_score": (getattr(ent, "tabelog_score", 3.5) or 3.5) * 20,
                        "price_band": getattr(ent, "price_band", None),
                        "meal_style": role.role_notes or "route_meal",
                        "role": role.role,
                    })

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
                logger.warning("meal_filler 澶辫触锛堢户缁級: %s", exc)
                s.set_output({"error": str(exc)})

        # 鈹€鈹€ Step 9: 鏃ュ唴閫傞厤璇勫垎 + 鏇挎崲寤鸿 鈹€鈹€
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
                        current_time_hint=("14:00" if frame.day_type == "arrival"
                                           else "08:30" if frame.day_type == "departure"
                                           else "09:30"),
                        transfer_budget_remaining=frame.transfer_budget_minutes,
                        prev_entity_area="",
                        next_entity_area="",
                        day_entity_types_so_far=[],
                    )

                    # 鏀堕泦璇ュぉ鐨?secondary 瀹炰綋
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

                        # 鏇挎崲寤鸿
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
                logger.warning("itinerary_fit 璇勫垎澶辫触锛堢户缁級: %s", exc)
                s.set_output({"error": str(exc)})

        # E1: secondary + meal + fit 蹇収
        await write_decision(
            session, trip_request_id=trip_id, input_hash=profile_hash,
            stage="filler_summary", key="secondary_meal_fit",
            value={
                "secondary_items": sum(len(d.secondary_items) for d in secondary_fills),
                "meal_items": sum(len(d.meals) for d in meal_fills),
                "fit_scored": len(fit_scores),
                "swap_suggestions": len(swap_suggestions),
            },
            reason="濉厖+璇勫垎瀹屾垚",
        )

        # 杞崲 day_frames 涓?dict 鍒楄〃
        import dataclasses
        frame_dicts = []
        for f in skeleton.frames:
            fd = dataclasses.asdict(f)
            frame_dicts.append(fd)

        # 鏋勫缓 design_brief 浠庡喅绛栭摼缁撴灉
        design_brief = {
            "route_strategy": [
                f"鍩庡競鍦? {circle_result.selected.name_zh}",
                f"涓昏娲诲姩: {', '.join(m.name_zh for m in ranking_result.selected_majors[:5])}",
            ],
            "tradeoffs": [t for t in ranking_result.trace if "capacity" in t.lower()],
            "stay_strategy": [
                f"hotel strategy: {hotel_result.preset_name or 'default'}",
            ],
            "budget_strategy": [f"棰勭畻妗ｆ: {profile.budget_level or 'mid'}"],
            "execution_principles": [
                f"鑺傚: {profile.pace or 'moderate'}",
                f"瀹归噺: {ranking_result.capacity_used:.1f}/{ranking_result.capacity_total:.1f}",
            ],
        }

        # 鈹€鈹€ E6b: 鏍规嵁 CIRCLE_WRITE_MODE 鍐冲畾璧版棫 assembler 杩樻槸鏂?builder 鈹€鈹€
        from app.domains.planning.itinerary_builder import (
            build_itinerary_records, CIRCLE_WRITE_MODE,
        )

        if CIRCLE_WRITE_MODE == "live":
            # 鈹€鈹€ LIVE 妯″紡锛氭柊閾捐矾鐩村啓锛岃烦杩囨棫 assembler 鈹€鈹€
            logger.info("E6b live mode: 璺宠繃鏃?assembler锛屼娇鐢?itinerary_builder")
            live_result = await build_itinerary_records(
                session,
                trip_request_id=trip_id,
                circle_id=circle_id,
                skeleton_frames=skeleton.frames,
                secondary_fills=secondary_fills,
                meal_fills=meal_fills,
                hotel_result=hotel_result,
                ranking_result=ranking_result,
                design_brief=design_brief,
                existing_plan_id=None,
            )
            plan_id = live_result["plan_id"]
            logger.info(
                "E6b live write: plan=%s days=%s items=%s",
                plan_id, live_result.get("days_created"), live_result.get("items_created"),
            )
        else:
            logger.warning("CIRCLE_WRITE_MODE=%s 闈?live锛屾寜鏃ч摼娓呴€€绛栫暐鏄惧紡澶辫触", CIRCLE_WRITE_MODE)
            if trace:
                await trace.finish_run(status="failed")
            return False, None, None, None

        # E1: 鍥炲啓 plan_id 鍒版湰娆℃墍鏈?decisions
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

        # 鈹€鈹€ constraint_trace finalize + evidence_bundle 钀藉簱 鈹€鈹€
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
            logger.warning("evidence_bundle 钀藉簱澶辫触锛堥潪鑷村懡锛? %s", _exc)

        # 鏇存柊 trace 鐨?plan_id
        if trace._run:
            trace._run.plan_id = plan_id
        await trace.finish_run(status="completed")

        logger.info(
            "鍩庡競鍦堥摼璺垚鍔? circle=%s majors=%d hotel=%s skeleton=%d days",
            circle_id, len(ranking_result.selected_majors),
            hotel_result.preset_name, len(skeleton.frames),
        )

        return True, plan_id, frame_dicts, design_brief

    except Exception as exc:
        logger.warning("鍩庡競鍦堥摼璺紓甯革紝涓婚摼澶辫触: %s", exc, exc_info=True)
        if trace:
            try:
                await trace.finish_run(status="failed")
            except Exception:
                pass
        return False, None, None, None


async def generate_trip(
    ctx: dict,
    *,
    trip_request_id: str,
    template_code: str | None = None,
    scene: str = "general",
) -> dict:
    """
    arq Job: 瑙﹀彂琛岀▼瑁呴厤 + 璇勫銆?
    I1 鏀归€狅細浠呰蛋鍩庡競鍦堜富閾捐矾锛屽け璐ユ椂鏄惧紡澶辫触锛屼笉鍥為€€鏃фā鏉裤€?
    瀹屾暣娴佺▼锛?    1. [鏂癩 灏濊瘯鍩庡競鍦堥摼璺紙select_circle 鈫?rank_major 鈫?hotel 鈫?skeleton锛?       鈫?鎴愬姛: 鐢?itinerary_builder 瑁呴厤 + generate_report_v2
       鈫?澶辫触: 鏄惧紡澶辫触
    2. enrich_itinerary_with_copy 鈫?AI 鏂囨娑﹁壊
    3. run_review_with_retry 鈫?澶氭ā鍨嬭瘎瀹?    4. 鏍规嵁瑁佸喅锛歱ublish 鈫?娓叉煋 / rewrite 鈫?閲嶅啓 / human 鈫?浜哄伐闃熷垪
    """
    trip_id = uuid.UUID(trip_request_id)
    logger.info("generate_trip 寮€濮?trip=%s scene=%s", trip_id, scene)

    async with async_session_factory() as session:
        trip = await session.get(TripRequest, trip_id)
        if trip is None:
            logger.error("trip_request_id=%s not found", trip_id)
            return {"status": "error", "reason": "trip not found"}

        trip.status = "assembling"
        await session.commit()

        # 鈹€鈹€ 琛ㄥ崟绾у墠缃棬鎺э紙validation engine锛夆攢鈹€
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
                        "琛ㄥ崟鏍￠獙鏈€氳繃(red=%d): trip=%s",
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
                        "琛ㄥ崟鏍￠獙鏈?%d 涓粍鐏?鍙户缁?: trip=%s",
                        vr.yellow_count, trip_id,
                    )
        except Exception as exc:
            logger.warning("琛ㄥ崟鏍￠獙寮傚父(闈為樆濉?: %s", exc)

        # 鈹€鈹€ I1: 灏濊瘯鍩庡競鍦堥摼璺?鈹€鈹€
        plan_id = None
        day_frames = None
        design_brief = None
        circle_path = False

        if CITY_CIRCLE_ENABLED:
            circle_path, plan_id, day_frames, design_brief = await _try_city_circle_pipeline(
                session, trip, scene,
            )

        # 涓婚摼澶辫触鍗虫樉寮忓け璐ワ紝涓嶅洖閫€鏃фā鏉块摼璺?        if not circle_path:
            trip.status = "failed"
            await session.commit()
            return {"status": "error", "reason": "city_circle_pipeline_failed"}

        # Step 2: AI 鏂囨娑﹁壊
        try:
            await enrich_itinerary_with_copy(
                session=session,
                plan_id=plan_id,
                scene=scene,
            )
        except Exception as exc:
            logger.warning("鏂囨娑﹁壊澶辫触锛堥潪鑷村懡锛塼rip=%s: %s", trip_id, exc)

        # Step 2.2: 鎶ュ憡鐢熸垚锛堜富閾句粎 v2锛?        try:
            if day_frames:
                from app.domains.planning.report_generator import generate_report_v2
                # 閲嶆柊鍔犺浇 profile锛坃try_city_circle_pipeline 鍐呴儴鍙橀噺涓嶅湪姝や綔鐢ㄥ煙锛?                from app.db.models.business import TripProfile as _TP
                from sqlalchemy import select as _sel2
                _pq = await session.execute(
                    _sel2(_TP).where(_TP.trip_request_id == trip_id).limit(1)
                )
                _profile = _pq.scalar_one_or_none()
                user_ctx = {
                    "party_type": scene,
                    "styles": [],
                    "budget_level": getattr(_profile, "budget_level", "mid") or "mid" if _profile else "mid",
                    "pace": getattr(_profile, "pace", "moderate") or "moderate" if _profile else "moderate",
                    "trip_goals": (
                        (getattr(_profile, "must_have_tags", None) or [])
                        + (getattr(_profile, "nice_to_have_tags", None) or [])
                    ) if _profile else [],
                }
                report_v2 = await generate_report_v2(
                    session=session,
                    plan_id=plan_id,
                    day_frames=day_frames,
                    design_brief_override=design_brief,
                    user_context=user_ctx,
                )

                # 鈹€鈹€ Step 2.3: Layer 3 page pipeline 鈹€鈹€
                try:
                    from app.domains.rendering.chapter_planner import plan_chapters
                    from app.domains.rendering.layer2_handoff import build_layer2_delivery_handoff
                    from app.domains.rendering.page_planner import plan_pages_and_persist
                    from app.domains.rendering.page_view_model import build_view_models

                    chapters = []
                    pages = []
                    view_models = {}

                    # 鍏堝皢 Layer2 杈撳嚭閫傞厤涓轰氦浠樺眰绋冲畾 payload锛屽啀杩涘叆 L3 pipeline
                    if isinstance(report_v2, dict) and report_v2.get("schema_version") == "v2":
                        from app.db.models.derived import ItineraryPlan as _IP

                        _plan = await session.get(_IP, plan_id)
                        payload, handoff_boundary = build_layer2_delivery_handoff(
                            report_content=report_v2,
                            plan_metadata=(_plan.plan_metadata if _plan else {}) or {},
                            plan_id=str(plan_id),
                        )
                        chapters = plan_chapters(payload)
                        pages = await plan_pages_and_persist(chapters, payload, session, plan_id)
                        view_models = build_view_models(pages, payload)

                        # 鍐欏叆 plan_metadata
                        if _plan:
                            meta = _plan.plan_metadata or {}
                            meta["layer2_delivery_handoff"] = handoff_boundary
                            meta["page_pipeline"] = {
                                "chapters": len(chapters),
                                "pages": len(pages),
                                "view_models": len(view_models),
                            }
                            meta["observation_chain"] = {
                                "run_id": _run_id,
                                "decision_surface": "generation_decisions",
                                "handoff_surface": "layer2_delivery_handoff",
                                "eval_surface": "offline_eval",
                                "regression_surface": "scripts/run_regression.py",
                            }
                            _plan.plan_metadata = meta
                        await write_decision(
                            session,
                            trip_request_id=trip_id,
                            plan_id=plan_id,
                            input_hash=profile_hash,
                            stage="layer2_handoff",
                            key="handoff_boundary",
                            value={
                                "chapters": len(chapters),
                                "pages": len(pages),
                                "view_models": len(view_models),
                                "run_id": _run_id,
                            },
                            reason="layer2 handoff committed to page-model-first delivery boundary",
                        )

                    logger.info(
                        "L3 page pipeline: plan=%s chapters=%d pages=%d vms=%d",
                        plan_id, len(chapters), len(pages), len(view_models),
                    )
                except Exception as exc:
                    logger.warning("L3 page pipeline 澶辫触锛堥潪鑷村懡锛? %s", exc)

                # 鈹€鈹€ Step 2.4: LiveRiskMonitor 椋庨櫓鎵弿锛圠4-03锛夆攢鈹€
                if resolved_cfg.switch("enable_live_risk_monitor", default=True):
                    try:
                        from app.domains.planning.live_risk_monitor import LiveRiskMonitor
                        risk_monitor = LiveRiskMonitor(session)
                        await risk_monitor.load_rules()
                        risk_alerts = await risk_monitor.scan_plan(plan_id, travel_date_list)
                        if risk_alerts:
                            logger.info(
                                "LiveRiskMonitor: plan=%s 鐢熸垚 %d 鏉￠闄╄鎶?"
                                "(critical=%d warning=%d)",
                                plan_id,
                                len(risk_alerts),
                                sum(1 for a in risk_alerts if a.get("severity") == "critical"),
                                sum(1 for a in risk_alerts if a.get("severity") == "warning"),
                            )
                    except Exception as exc:
                        logger.warning("LiveRiskMonitor 鎵弿澶辫触锛堥潪鑷村懡锛? %s", exc)

                logger.info("鎶ュ憡 v2(circle) 鐢熸垚瀹屾垚 plan=%s", plan_id)
            else:
                raise RuntimeError("city_circle_pipeline_missing_day_frames")
        except Exception as exc:
            logger.warning("鎶ュ憡鐢熸垚澶辫触锛堥潪鑷村懡锛塼rip=%s: %s", trip_id, exc)

        # Step 2.3: 棰勮澶╂爣璁?        try:
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

            # 杞崲涓?select_preview_day 闇€瑕佺殑 list[list[dict]] 鏍煎紡
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
                        "name": (entity.name_local or entity.name or "鏈煡") if entity else "鏈煡",
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
                        "preview_day 鏍囪瀹屾垚 plan=%s day=%d needs_review=%s",
                        plan_id, preview_result.selected_day_index,
                        preview_result.needs_human_review,
                    )
        except Exception as exc:
            logger.warning("preview_day 鏍囪澶辫触锛堥潪鑷村懡锛塼rip=%s: %s", trip_id, exc)

        # Step 2.5: 璐ㄩ噺闂ㄦ帶鏍￠獙锛?1鏉?QTY 纭鍒欙級
        try:
            plan_json_for_gate = await _build_plan_json(session, plan_id)
            gate_result: QualityGateResult = await run_quality_gate(plan_json_for_gate, db=session)
            logger.info(
                "璐ㄩ噺闂ㄦ帶缁撴灉 trip=%s plan=%s %s",
                trip_id, plan_id, gate_result.summary(),
            )
            if not gate_result.passed:
                # Hard error 鈫?鐩存帴杞汉宸ワ紝闄勪笂閿欒淇℃伅
                trip.status = "review"
                await session.commit()
                error_summary = "; ".join(gate_result.errors[:5])
                logger.warning(
                    "璐ㄩ噺闂ㄦ帶鏈€氳繃锛岃浆浜哄伐瀹℃牳 trip=%s errors=%s",
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
            logger.warning("璐ㄩ噺闂ㄦ帶寮傚父锛堥潪鑷村懡锛岀户缁瘎瀹★級trip=%s: %s", trip_id, exc)

        # Step 2.6: 绂荤嚎璇勬祴锛坥ffline_eval锛夆€?鑷姩璇勫垎 + 鍥炲綊妫€娴?        eval_score_dict = None
        try:
            from app.domains.evaluation.offline_eval import score_plan, EvalCase
            plan_json_for_eval = plan_json_for_gate if "plan_json_for_gate" in locals() else await _build_plan_json(session, plan_id)

            # 鏋勫缓璇勬祴 case锛堜娇鐢ㄥ疄闄呯敾鍍忕害鏉燂級
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

            # 鍐欏叆 plan metadata
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
                    "run_id": _run_id,
                    "case_id": eval_case.case_id,
                },
                reason="offline eval attached to same observation chain",
            )

            logger.info(
                "offline_eval trip=%s overall=%.2f (completeness=%.1f feasibility=%.1f diversity=%.1f)",
                trip_id, eval_result.overall,
                eval_result.completeness, eval_result.feasibility, eval_result.diversity,
            )
        except Exception as exc:
            logger.warning("offline_eval 寮傚父锛堥潪鑷村懡锛塼rip=%s: %s", trip_id, exc)

        # Step 3: 澶氭ā鍨嬭瘎瀹?        if not REVIEW_PIPELINE_ENABLED:
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
                    "[T22-T25] 鍥涚淮璇勫瀹屾垚 plan=%s score=%.1f passed=%s",
                    plan_id, mmr_dict["overall_score"], mmr_dict["passed"],
                )
            except Exception as e:
                logger.warning("[T22-T25] 鍥涚淮璇勫澶辫触锛堥潪鑷村懡锛? %s", e)

            # 鎸佷箙鍖栨棫璇勫缁撴灉
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
                logger.warning("璇勫缁撴灉鎸佷箙鍖栧け璐ワ紙闈炶嚧鍛斤級: %s", e)

            # 璇勫鍥炲啓椋炶疆锛歩ssues 鈫?鏁版嵁灞備慨姝?            try:
                from app.domains.review_ops.review_writeback import writeback_review_issues
                wb_stats = await writeback_review_issues(
                    session, plan_id=plan_id,
                    trip_request_id=trip_id,
                    pipeline_result=result,
                )
                logger.info("review_writeback: %s", wb_stats)
            except Exception as e:
                logger.warning("review_writeback 澶辫触锛堥潪鑷村懡锛? %s", e)

            # 鏍规嵁瑁佸喅鍒嗘祦
            if result.final_verdict == Verdict.PUBLISH:
                trip.status = "reviewed"
                await session.commit()
                await enqueue_job("render_trip", plan_id=str(plan_id))
                logger.info(
                    "璇勫閫氳繃 plan=%s (tokens=%d, duration=%dms)",
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
                    "璇勫杞汉宸?plan=%s reason=%s",
                    plan_id, result.final_reason,
                )
                return {
                    "status": "ok",
                    "plan_id": str(plan_id),
                    "review": "human",
                    "reason": result.final_reason,
                }
            else:
                # REWRITE 宸茬粡鍦?run_review_with_retry 鍐呴儴澶勭悊浜?                # 鍒拌繖閲岃鏄庨噸鍐欏悗浠嶇劧鏄?human
                trip.status = "review"
                await session.commit()
                return {
                    "status": "ok",
                    "plan_id": str(plan_id),
                    "review": "human_after_rewrite",
                    "reason": result.final_reason,
                }

        except Exception as exc:
            logger.exception("璇勫娴佹按绾垮紓甯?trip=%s: %s", trip_id, exc)
            # review pipeline exception must fail explicitly
            trip.status = "failed"
            trip.last_job_error = f"review_pipeline_exception:{exc}"
            await session.commit()
            return {
                "status": "error",
                "plan_id": str(plan_id),
                "run_id": _run_id,
                "review": "failed",
                "error": str(exc),
            }


