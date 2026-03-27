from __future__ import annotations

from app.domains.rendering.chapter_planner import plan_chapters
from app.domains.rendering.layer2_handoff import (
    EDITABLE_PAGE_FIELDS,
    INTERNAL_ONLY_FIELDS,
    STABLE_HANDOFF_FIELDS,
    build_layer2_delivery_handoff,
)
from app.domains.rendering.page_planner import plan_pages
from app.domains.rendering.page_view_model import build_view_models


def _sample_report_content() -> dict:
    return {
        "schema_version": "v2",
        "version": "circle-v1",
        "generated_at": "2026-03-26T10:00:00+00:00",
        "design_brief": {
            "route_strategy": ["circle-based"],
            "tradeoffs": ["capacity-first"],
            "stay_strategy": ["double_base"],
            "budget_strategy": ["mid"],
            "execution_principles": ["balanced"],
        },
        "layer1_overview": {
            "booking_reminders": [
                {
                    "item": "Sagano Train",
                    "deadline": "7 days before",
                    "impact": "high queue risk",
                }
            ],
            "prep_checklist": {
                "title": "Departure checklist",
                "items": ["Passport", "eSIM", "Payment cards"],
            },
        },
        "layer2_daily": [
            {
                "day_number": 1,
                "city_code": "kyoto",
                "day_type": "arrival",
                "day_theme": "Higashiyama slow day",
                "primary_area": "higashiyama",
                "secondary_area": "gion",
                "day_goal": "Adapt with light pace",
                "must_keep": "Kiyomizu",
                "first_cut": "Night photo walk",
                "start_anchor": "Kyoto station",
                "end_anchor": "Gion",
                "route_integrity_score": 0.88,
                "intensity": "balanced",
                "sleep_base": "kyoto_station",
                "items": [
                    {
                        "sort": 1,
                        "type": "poi",
                        "duration": 90,
                        "entity_id": "kyo_kiyomizu",
                        "name": "Kiyomizu-dera",
                        "entity_type": "poi",
                        "area": "higashiyama",
                        "is_optional": False,
                    },
                    {
                        "sort": 2,
                        "type": "restaurant",
                        "duration": 70,
                        "entity_id": "kyo_tofu_dinner",
                        "name": "Tofu dinner",
                        "entity_type": "restaurant",
                        "area": "gion",
                        "is_optional": False,
                    },
                ],
                "report": {
                    "why_this_arrangement": ["Arrival day keeps low transfer cost"],
                    "highlights": [{"name": "Kiyomizu", "description": "Golden hour view"}],
                    "notes_and_planb": {
                        "weather_plan": "Switch to museum",
                        "energy_plan": "Skip night photo walk",
                    },
                    "execution_overview": {"top_expectation": "Kiyomizu sunset"},
                },
                "conditional_pages": ["booking_window"],
            }
        ],
        "preference_fulfillment": [],
        "skipped_options": [],
        "emotional_goals": [
            {"day_index": 1, "mood_keyword": "explore", "mood_sentence": "Easy first-day exploration."}
        ],
        "meta": {
            "total_days": 1,
            "destination": "kansai",
            "party_type": "couple",
            "budget_level": "mid",
            "pace": "moderate",
            "structure_warnings": [],
        },
    }


def _sample_plan_metadata() -> dict:
    return {
        "evidence_bundle": {
            "run_id": "run-123",
            "hard_unconsumed_count": 0,
            "compiled_constraints": {
                "must_go_clusters": ["kyo_kiyomizu"],
                "climate_risk_flags": ["rainy_season"],
            },
            "resolved_policy": {"circle_id": "kansai_classic_circle"},
            "input_contract": {
                "contract_version": "layer2_v1",
                "requested_city_circle": "kansai_classic_circle",
                "arrival_local_datetime": "2026-09-20T18:25",
                "departure_local_datetime": "2026-09-25T11:45",
                "companion_breakdown": {"party_type": "couple", "party_size": 2},
                "budget_range": {"budget_level": "mid", "currency": "CNY", "total": 18000},
                "booked_items": [{"type": "hotel", "city_code": "kyoto", "name": "Kyoto Stay"}],
                "do_not_go_places": ["osa_usj_themepark"],
                "visited_places": ["kyo_kiyomizu"],
            },
        }
    }


def test_layer2_delivery_handoff_builds_payload_and_boundary():
    payload, boundary = build_layer2_delivery_handoff(
        report_content=_sample_report_content(),
        plan_metadata=_sample_plan_metadata(),
        plan_id="plan-1",
    )

    assert payload.meta.trip_id == "plan-1"
    assert payload.meta.destination == "kansai"
    assert payload.profile_summary.party_type == "couple"
    assert payload.profile_summary.hotel_constraints
    assert payload.days[0].day_goal == "Adapt with light pace"
    assert payload.days[0].slots[0].entity_id == "kyo_kiyomizu"
    assert payload.day_circle_map[1] == "kansai_classic_circle"
    assert any(x.risk_type == "reservation_needed" for x in payload.risk_watch_items)
    assert any(x.risk_type == "seasonal" for x in payload.risk_watch_items)

    assert boundary["contract_version"] == "l2_to_delivery_v1"
    assert boundary["stable_fields"] == STABLE_HANDOFF_FIELDS
    assert boundary["internal_only_fields"] == INTERNAL_ONLY_FIELDS
    assert boundary["editable_page_fields"] == EDITABLE_PAGE_FIELDS


def test_handoff_fields_are_consumed_by_page_pipeline_minimal_loop():
    payload, _ = build_layer2_delivery_handoff(
        report_content=_sample_report_content(),
        plan_metadata=_sample_plan_metadata(),
        plan_id="plan-1",
    )

    chapters = plan_chapters(payload)
    pages = plan_pages(chapters, payload)
    view_models = build_view_models(pages, payload)

    booking_vm = next(vm for vm in view_models.values() if vm.page_type == "booking_window")
    prep_vm = next(vm for vm in view_models.values() if vm.page_type == "departure_prep")

    booking_timeline = next(s for s in booking_vm.sections if s.section_type == "booking_timeline")
    assert booking_timeline.content["items"], "booking_window should consume payload.booking_alerts"

    prep_text_blocks = [s for s in prep_vm.sections if s.section_type == "text_block"]
    assert any(getattr(s.content, "text", "") == "Departure checklist" for s in prep_text_blocks)


def test_page_models_define_stable_editable_internal_boundaries():
    payload, _ = build_layer2_delivery_handoff(
        report_content=_sample_report_content(),
        plan_metadata=_sample_plan_metadata(),
        plan_id="plan-1",
    )

    chapters = plan_chapters(payload)
    pages = plan_pages(chapters, payload)
    view_models = build_view_models(pages, payload)

    day_vm = next(vm for vm in view_models.values() if vm.page_type == "day_execution")

    assert day_vm.stable_inputs["day_index"] == 1
    assert day_vm.editable_content["day_intro_draft"] == "Adapt with light pace"
    assert day_vm.editable_content["timeline_note_draft"]
    assert "route_integrity_score" in day_vm.internal_state
    assert "slot_entity_ids" in day_vm.internal_state


def test_frontmatter_page_models_expose_editable_boundaries():
    payload, _ = build_layer2_delivery_handoff(
        report_content=_sample_report_content(),
        plan_metadata=_sample_plan_metadata(),
        plan_id="plan-1",
    )

    chapters = plan_chapters(payload)
    pages = plan_pages(chapters, payload)
    view_models = build_view_models(pages, payload)

    booking_vm = next(vm for vm in view_models.values() if vm.page_type == "booking_window")
    prep_vm = next(vm for vm in view_models.values() if vm.page_type == "departure_prep")

    assert booking_vm.editable_content["booking_copy_draft"]
    assert booking_vm.stable_inputs["booking_items_count"] >= 1
    assert prep_vm.editable_content["prep_intro_draft"] == "Departure checklist"
    assert prep_vm.stable_inputs["checklist_item_count"] == 3
