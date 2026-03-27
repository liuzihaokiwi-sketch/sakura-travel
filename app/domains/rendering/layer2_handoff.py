from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.domains.planning.report_schema import ReportPayloadV2

STABLE_HANDOFF_FIELDS: list[str] = [
    "plan_metadata.evidence_bundle.run_id",
    "plan_metadata.evidence_bundle.input_contract.requested_city_circle",
    "plan_metadata.evidence_bundle.input_contract.arrival_local_datetime",
    "plan_metadata.evidence_bundle.input_contract.departure_local_datetime",
    "plan_metadata.evidence_bundle.input_contract.companion_breakdown",
    "plan_metadata.evidence_bundle.input_contract.budget_range",
    "plan_metadata.evidence_bundle.input_contract.booked_items",
    "plan_metadata.evidence_bundle.input_contract.visited_places",
    "plan_metadata.evidence_bundle.input_contract.do_not_go_places",
    "plan_metadata.evidence_bundle.compiled_constraints",
    "plan_metadata.evidence_bundle.resolved_policy",
    "report_content.layer2_daily.day_number",
    "report_content.layer2_daily.city_code",
    "report_content.layer2_daily.day_type",
    "report_content.layer2_daily.primary_area",
    "report_content.layer2_daily.day_goal",
    "report_content.layer2_daily.must_keep",
    "report_content.layer2_daily.first_cut",
    "report_content.layer2_daily.intensity",
    "report_content.layer2_daily.items",
    "report_content.layer1_overview.booking_reminders",
]

INTERNAL_ONLY_FIELDS: list[str] = [
    "report_content.layer2_daily.report",
    "report_content.layer2_daily.fragment_reuse",
    "report_content.meta.fragment_reuse_summary",
    "report_content.meta.structure_warnings",
]

EDITABLE_PAGE_FIELDS: list[str] = [
    "page_models.day_execution.editable_content.mood_sentence",
    "page_models.day_execution.editable_content.day_intro_draft",
    "page_models.day_execution.editable_content.timeline_note_draft",
    "page_models.booking_window.editable_content.booking_copy_draft",
    "page_models.departure_prep.editable_content.prep_intro_draft",
    "page_models.chapter_opener.editable_content.chapter_goal_draft",
]


def _normalize_intensity(value: Any) -> str:
    text = str(value or "").lower().strip()
    if text in {"light", "relaxed"}:
        return "light"
    if text in {"dense", "packed"}:
        return "dense"
    return "balanced"


def _intensity_label(value: str) -> str:
    return {"light": "轻松", "balanced": "均衡", "dense": "偏满"}.get(value, "均衡")


def _intensity_score(value: str) -> float:
    return {"light": 0.3, "balanced": 0.6, "dense": 0.85}.get(value, 0.6)


def _slot_kind(raw_type: Any) -> str:
    text = str(raw_type or "").lower()
    if "restaurant" in text:
        return "restaurant"
    if "hotel" in text or "checkin" in text or "checkout" in text:
        return "hotel"
    if "transit" in text or "transport" in text:
        return "transit"
    if "activity" in text:
        return "activity"
    return "poi"


def _risk_from_booking_reminders(reminders: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for r in reminders:
        item = str(r.get("item") or "").strip()
        if not item:
            continue
        items.append(
            {
                "risk_type": "reservation_needed",
                "description": item,
                "action_required": str(r.get("deadline") or ""),
            }
        )
    return items


def _hotel_constraints(booked_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    constraints: list[dict[str, Any]] = []
    for item in booked_items:
        if not isinstance(item, dict):
            continue
        if str(item.get("type") or "").lower() != "hotel":
            continue
        constraints.append(
            {
                "city": str(item.get("city_code") or ""),
                "check_in_day": None,
                "check_out_day": None,
                "hotel_name": str(item.get("name") or "") or None,
                "area": str(item.get("area") or "") or None,
                "is_fixed": bool(item.get("locked", True)),
            }
        )
    return constraints


def build_layer2_delivery_handoff(
    *,
    report_content: dict[str, Any],
    plan_metadata: dict[str, Any] | None,
    plan_id: str,
    language: str = "zh-CN",
    render_mode: str = "web",
) -> tuple[ReportPayloadV2, dict[str, Any]]:
    plan_metadata = plan_metadata or {}
    evidence_bundle = dict(plan_metadata.get("evidence_bundle") or {})
    input_contract = dict(evidence_bundle.get("input_contract") or {})
    compiled_constraints = dict(evidence_bundle.get("compiled_constraints") or {})
    resolved_policy = dict(evidence_bundle.get("resolved_policy") or {})

    report_meta = dict(report_content.get("meta") or {})
    layer1 = dict(report_content.get("layer1_overview") or {})
    layer2_daily = list(report_content.get("layer2_daily") or [])
    booking_reminders = list(layer1.get("booking_reminders") or [])

    companion_breakdown = dict(input_contract.get("companion_breakdown") or {})
    budget_range = dict(input_contract.get("budget_range") or {})
    booked_items = list(input_contract.get("booked_items") or [])
    requested_circle = (
        str(input_contract.get("requested_city_circle") or "").strip()
        or str(resolved_policy.get("circle_id") or "").strip()
    )

    route_summary = []
    intensity_map = []
    days = []
    selection_evidence: list[dict[str, Any]] = []
    day_circle_map: dict[int, str] = {}
    hotel_changes = []
    prev_sleep_base = ""

    for day in layer2_daily:
        day_index = int(day.get("day_number") or len(days) + 1)
        intensity = _normalize_intensity(day.get("intensity"))
        route_summary.append(
            {
                "day_index": day_index,
                "title": str(day.get("day_theme") or day.get("day_goal") or f"Day {day_index}"),
                "primary_area": str(day.get("primary_area") or ""),
                "intensity": intensity,
            }
        )
        intensity_map.append(
            {
                "day_index": day_index,
                "label": _intensity_label(intensity),
                "score": _intensity_score(intensity),
            }
        )
        if requested_circle:
            day_circle_map[day_index] = requested_circle

        sleep_base = str(day.get("sleep_base") or "")
        if prev_sleep_base and sleep_base and sleep_base != prev_sleep_base:
            hotel_changes.append(
                {
                    "day_index": day_index,
                    "from_area": prev_sleep_base,
                    "to_area": sleep_base,
                    "reason": "sleep_base_changed",
                }
            )
        if sleep_base:
            prev_sleep_base = sleep_base

        slots = []
        for idx, item in enumerate(list(day.get("items") or []), start=1):
            kind = _slot_kind(item.get("type"))
            entity_id = item.get("entity_id")
            slots.append(
                {
                    "slot_index": idx,
                    "kind": kind,
                    "entity_id": str(entity_id) if entity_id else None,
                    "title": str(item.get("name") or ""),
                    "area": str(item.get("area") or ""),
                    "start_time_hint": None,
                    "duration_mins": int(item.get("duration") or 0) or None,
                    "booking_required": False,
                    "weather_dependency": "low",
                    "replaceable": not bool(item.get("is_optional")),
                    "replacement_pool": [],
                }
            )
            if entity_id:
                selection_evidence.append(
                    {
                        "entity_id": str(entity_id),
                        "entity_type": kind,
                        "name": str(item.get("name") or ""),
                        "area": str(item.get("area") or ""),
                        "day_index": day_index,
                    }
                )

        day_report = dict(day.get("report") or {})
        execution = dict(day_report.get("execution_overview") or {})
        notes_planb = dict(day_report.get("notes_and_planb") or {})
        highlights = list(day_report.get("highlights") or [])

        days.append(
            {
                "day_index": day_index,
                "title": str(day.get("day_theme") or day.get("day_goal") or f"Day {day_index}"),
                "primary_area": str(day.get("primary_area") or ""),
                "secondary_area": str(day.get("secondary_area") or "") or None,
                "day_goal": str(day.get("day_goal") or ""),
                "intensity": intensity,
                "start_anchor": str(day.get("start_anchor") or ""),
                "end_anchor": str(day.get("end_anchor") or ""),
                "must_keep": str(day.get("must_keep") or ""),
                "first_cut": str(day.get("first_cut") or ""),
                "route_integrity_score": float(day.get("route_integrity_score") or 1.0),
                "risks": [
                    {
                        "risk_type": "booking",
                        "description": str(msg),
                        "mitigation": "",
                    }
                    for msg in notes_planb.get("risk_warnings", [])
                    if str(msg).strip()
                ],
                "slots": slots,
                "reasoning": [str(x) for x in (day_report.get("why_this_arrangement") or []) if str(x).strip()],
                "highlights": [
                    {
                        "name": str(h.get("name") or ""),
                        "description": str(h.get("description") or ""),
                        "photo_tip": str(h.get("photo_tip") or "") or None,
                        "nearby_bonus": str(h.get("nearby_bonus") or "") or None,
                    }
                    for h in highlights
                    if isinstance(h, dict)
                ],
                "execution_notes": {
                    "risk_warnings": [str(x) for x in notes_planb.get("risk_warnings", []) if str(x).strip()],
                    "weather_plan": str(notes_planb.get("weather_plan") or ""),
                    "energy_plan": str(notes_planb.get("energy_plan") or ""),
                    "clothing_tip": str(notes_planb.get("clothing_tip") or ""),
                },
                "plan_b": [
                    {"trigger": "weather", "alternative": str(notes_planb.get("weather_plan") or ""), "entity_ids": []}
                    if str(notes_planb.get("weather_plan") or "").strip()
                    else None,
                    {"trigger": "energy", "alternative": str(notes_planb.get("energy_plan") or ""), "entity_ids": []}
                    if str(notes_planb.get("energy_plan") or "").strip()
                    else None,
                ],
                "trigger_tags": [str(x) for x in (day.get("conditional_pages") or []) if str(x).strip()],
            }
        )
        days[-1]["plan_b"] = [x for x in days[-1]["plan_b"] if x]

        if execution.get("top_expectation"):
            selection_evidence.append(
                {
                    "evidence_type": "day_top_expectation",
                    "day_index": day_index,
                    "text": str(execution.get("top_expectation")),
                }
            )

    risk_watch_items = _risk_from_booking_reminders(booking_reminders)
    for risk in list(compiled_constraints.get("climate_risk_flags") or []):
        risk_watch_items.append(
            {
                "risk_type": "seasonal",
                "description": str(risk),
                "action_required": "",
                "day_index": None,
            }
        )

    hard_unconsumed_count = int(evidence_bundle.get("hard_unconsumed_count") or 0)
    if hard_unconsumed_count > 0:
        risk_watch_items.append(
            {
                "risk_type": "constraint",
                "description": f"hard_constraints_unconsumed={hard_unconsumed_count}",
                "action_required": "manual_review",
                "day_index": None,
            }
        )

    selection_evidence.append(
        {
            "evidence_type": "city_circle_selection",
            "circle_id": requested_circle,
            "resolved_policy": resolved_policy,
            "run_id": evidence_bundle.get("run_id"),
        }
    )
    selection_evidence.append(
        {
            "evidence_type": "input_contract_snapshot",
            "requested_city_circle": requested_circle,
            "arrival_local_datetime": input_contract.get("arrival_local_datetime"),
            "departure_local_datetime": input_contract.get("departure_local_datetime"),
            "companion_breakdown": companion_breakdown,
            "budget_range": budget_range,
            "booked_items": booked_items,
        }
    )

    payload_dict = {
        "meta": {
            "trip_id": plan_id,
            "destination": str(report_meta.get("destination") or ""),
            "total_days": int(report_meta.get("total_days") or len(days) or 1),
            "language": language,
            "render_mode": render_mode,
            "schema_version": "v2",
            "circle": {
                "circle_id": requested_circle or "unknown",
                "name_zh": requested_circle or "未命名城市圈",
                "base_city_codes": [],
                "extension_city_codes": [],
                "recommended_days_range": None,
                "selection_score": None,
                "selection_reasons": [],
            },
        },
        "profile_summary": {
            "party_type": str(companion_breakdown.get("party_type") or report_meta.get("party_type") or "couple"),
            "pace_preference": _normalize_intensity(report_meta.get("pace")),
            "budget_bias": str(budget_range.get("budget_level") or report_meta.get("budget_level") or ""),
            "trip_goals": [str(x) for x in list(compiled_constraints.get("must_go_clusters") or [])],
            "hard_constraints": [
                f"requested_city_circle={requested_circle}" if requested_circle else "",
                f"arrival={input_contract.get('arrival_local_datetime')}" if input_contract.get("arrival_local_datetime") else "",
                f"departure={input_contract.get('departure_local_datetime')}" if input_contract.get("departure_local_datetime") else "",
            ],
            "avoid_list": [str(x) for x in list(input_contract.get("do_not_go_places") or [])],
            "hotel_constraints": _hotel_constraints(booked_items),
        },
        "design_brief": dict(report_content.get("design_brief") or {}),
        "overview": {
            "route_summary": route_summary,
            "intensity_map": intensity_map,
            "anchor_events": [
                {
                    "day_index": int(d.get("day_number") or i + 1),
                    "label": str(d.get("must_keep") or ""),
                    "is_bookable": False,
                }
                for i, d in enumerate(layer2_daily)
                if str(d.get("must_keep") or "").strip()
            ],
            "hotel_changes": hotel_changes,
            "trip_highlights": [str(d.get("must_keep") or d.get("day_goal") or "") for d in layer2_daily][:5],
        },
        "booking_alerts": [
            {
                "entity_id": None,
                "label": str(item.get("item") or ""),
                "booking_level": "should_book",
                "deadline_hint": str(item.get("deadline") or ""),
                "impact_if_missed": str(item.get("impact") or ""),
                "fallback_label": None,
            }
            for item in booking_reminders
            if str(item.get("item") or "").strip()
        ],
        "prep_notes": dict(layer1.get("prep_checklist") or {}),
        "days": days,
        "conditional_sections": [],
        "quality_flags": {
            "warnings": [str(x) for x in list(report_meta.get("structure_warnings") or [])],
        },
        "versioning": {
            "generated_at": str(report_content.get("generated_at") or datetime.now(timezone.utc).isoformat()),
            "generator_version": str(report_content.get("version") or "circle-v1"),
            "profile_version": str(input_contract.get("contract_version") or ""),
        },
        "preference_fulfillment": list(report_content.get("preference_fulfillment") or []),
        "skipped_options": list(report_content.get("skipped_options") or []),
        "chapter_summaries": [],
        "emotional_goals": list(report_content.get("emotional_goals") or []),
        "risk_watch_items": risk_watch_items,
        "selection_evidence": selection_evidence,
        "photo_themes": [],
        "supplemental_items": [],
        "circles": [
            {
                "circle_id": requested_circle or "unknown",
                "name_zh": requested_circle or "未命名城市圈",
                "base_city_codes": [],
                "extension_city_codes": [],
                "recommended_days_range": None,
                "selection_score": None,
                "selection_reasons": [],
            }
        ]
        if requested_circle
        else [],
        "day_circle_map": day_circle_map,
    }

    # drop empty hard_constraints entries
    payload_dict["profile_summary"]["hard_constraints"] = [
        x for x in payload_dict["profile_summary"]["hard_constraints"] if x
    ]
    payload = ReportPayloadV2.model_validate(payload_dict)

    boundary = {
        "contract_version": "l2_to_delivery_v1",
        "source_report_schema": str(report_content.get("schema_version") or ""),
        "evidence_run_id": evidence_bundle.get("run_id"),
        "stable_fields": STABLE_HANDOFF_FIELDS,
        "internal_only_fields": INTERNAL_ONLY_FIELDS,
        "editable_page_fields": EDITABLE_PAGE_FIELDS,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    return payload, boundary
