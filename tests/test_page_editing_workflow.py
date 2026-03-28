from __future__ import annotations

from app.domains.rendering.asset_manifest import (
    attach_asset_metadata_to_pages,
    hero_slot_id,
    page_slot_id,
    resolve_slot_asset,
)
from app.domains.rendering.chapter_planner import plan_chapters
from app.domains.rendering.page_editing import (
    apply_page_model_edits,
    build_page_render_payload,
)
from app.domains.rendering.page_planner import plan_pages
from app.domains.rendering.page_view_model import build_view_models
from tests.helpers.build_test_planning_output import build_test_planning_output


def _build_page_models():
    payload = build_test_planning_output()
    chapters = plan_chapters(payload)
    pages = plan_pages(chapters, payload)
    return build_view_models(pages, payload)


def test_handoff_to_edit_to_preview_render_pipeline():
    page_models = _build_page_models()
    day_vm = next(vm for vm in page_models.values() if vm.page_type == "day_execution")
    booking_vm = next(vm for vm in page_models.values() if vm.page_type == "booking_window")
    prep_vm = next(vm for vm in page_models.values() if vm.page_type == "departure_prep")
    cover_vm = next(vm for vm in page_models.values() if vm.page_type == "cover")

    stable_before = dict(day_vm.stable_inputs)
    internal_before = dict(day_vm.internal_state)
    booking_stable_before = dict(booking_vm.stable_inputs)
    booking_internal_before = dict(booking_vm.internal_state)
    prep_stable_before = dict(prep_vm.stable_inputs)
    prep_internal_before = dict(prep_vm.internal_state)

    edited_models = apply_page_model_edits(
        page_models,
        {
            day_vm.page_id: {
                "stable_inputs": {"day_index": 99},
                "internal_state": {"route_integrity_score": 0.01},
                "editable_content": {
                    "mood_sentence": "Morning should stay slow and calm.",
                    "day_intro_draft": "Human adjusted intro",
                    "timeline_note_draft": [{"slot_index": 1, "note": "Edited area note"}],
                },
            }
            ,
            booking_vm.page_id: {
                "stable_inputs": {"booking_alert_count": 999},
                "internal_state": {"source": "hacked"},
                "editable_content": {
                    "booking_headline_draft": "Human booking headline",
                    "booking_copy_draft": [
                        {
                            "label": "Sagano Train",
                            "deadline_hint": "5 days before",
                            "impact_if_missed": "Need backup scenic route",
                        }
                    ],
                },
            },
            prep_vm.page_id: {
                "stable_inputs": {"risk_watch_count": 999},
                "internal_state": {"prep_notes_keys": ["x"]},
                "editable_content": {
                    "prep_intro_draft": "Bring meds and power bank.",
                },
            },
        },
    )

    edited_day = edited_models[day_vm.page_id]
    edited_booking = edited_models[booking_vm.page_id]
    edited_prep = edited_models[prep_vm.page_id]
    assert edited_day.editable_content["mood_sentence"] == "Morning should stay slow and calm."
    assert edited_day.editable_content["day_intro_draft"] == "Human adjusted intro"
    assert edited_booking.editable_content["booking_headline_draft"] == "Human booking headline"
    assert edited_prep.editable_content["prep_intro_draft"] == "Bring meds and power bank."

    assert edited_day.stable_inputs == stable_before
    assert edited_day.internal_state == internal_before
    assert edited_booking.stable_inputs == booking_stable_before
    assert edited_booking.internal_state == booking_internal_before
    assert edited_prep.stable_inputs == prep_stable_before
    assert edited_prep.internal_state == prep_internal_before

    timeline_section = next(s for s in edited_day.sections if s.section_type == "timeline")
    assert timeline_section.content.items[0].note == "Edited area note"

    booking_section = next(s for s in edited_booking.sections if s.section_type == "booking_timeline")
    assert edited_booking.heading.subtitle == "Human booking headline"
    assert booking_section.content["items"][0]["deadline_hint"] == "5 days before"
    assert booking_section.content["items"][0]["impact_if_missed"] == "Need backup scenic route"

    prep_editor_note = next(
        s
        for s in edited_prep.sections
        if s.section_type == "text_block" and s.heading == "Editor Note"
    )
    assert prep_editor_note.content.text == "Bring meds and power bank."

    slot_id = hero_slot_id(cover_vm.page_id, cover_vm.page_type)
    booking_badge_slot = page_slot_id(
        page_id=booking_vm.page_id,
        page_type=booking_vm.page_type,
        slot_name="badge",
    )
    manifest = {
        "version": "page-assets-v1",
        "slots": {
            slot_id: {"asset_id": "day_hero_asset"},
            booking_badge_slot: {"asset_id": "booking_badge_asset"},
        },
        "assets": {
            "day_hero_asset": {
                "kind": "photo",
                "url": "oss://travel-ai/day-hero-001.jpg",
                "source": "object_storage",
                "license": "internal",
            },
            "booking_badge_asset": {
                "kind": "illustration",
                "url": "oss://travel-ai/booking-badge-001.png",
                "source": "object_storage",
                "license": "internal",
            },
        },
    }

    preview_payload = build_page_render_payload(edited_models, mode="preview", asset_manifest=manifest)
    render_payload = build_page_render_payload(edited_models, mode="render", asset_manifest=manifest)

    preview_node = next(n for n in preview_payload["nodes"] if n["page_id"] == day_vm.page_id)
    preview_booking_node = next(n for n in preview_payload["nodes"] if n["page_id"] == booking_vm.page_id)
    preview_prep_node = next(n for n in preview_payload["nodes"] if n["page_id"] == prep_vm.page_id)
    render_node = next(n for n in render_payload["nodes"] if n["page_id"] == day_vm.page_id)
    cover_node = next(n for n in preview_payload["nodes"] if n["page_id"] == cover_vm.page_id)

    assert "Morning should stay slow and calm." in preview_node["summary"]
    assert preview_booking_node["summary"] == "Human booking headline"
    assert preview_prep_node["summary"] == "Bring meds and power bank."
    assert cover_node["hero_fallback"] == "slot_asset"
    assert cover_node["hero_source"] == "object_storage"
    assert render_node["editable_content"]["day_intro_draft"] == "Human adjusted intro"
    assert cover_node["asset_slots"]["hero"]["asset_id"] == "day_hero_asset"
    assert cover_node["hero_url"] == "oss://travel-ai/day-hero-001.jpg"
    assert preview_booking_node["asset_slots"]["badge"]["asset_id"] == "booking_badge_asset"


def test_page_slot_asset_manifest_resolve():
    page_models = _build_page_models()
    cover_vm = next(vm for vm in page_models.values() if vm.page_type == "cover")
    booking_vm = next(vm for vm in page_models.values() if vm.page_type == "booking_window")

    slot_id = hero_slot_id(cover_vm.page_id, cover_vm.page_type)
    booking_badge_slot = page_slot_id(
        page_id=booking_vm.page_id,
        page_type=booking_vm.page_type,
        slot_name="badge",
    )
    manifest = {
        "version": "page-assets-v1",
        "slots": {
            slot_id: {"asset_id": "hero_cover_test"},
            booking_badge_slot: {"asset_id": "booking_badge_test"},
        },
        "assets": {
            "hero_cover_test": {
                "kind": "illustration",
                "url": "/assets/placeholders/cover_default.jpg",
                "source": "repo_ui_placeholder",
                "license": "internal",
            },
            "booking_badge_test": {
                "kind": "illustration",
                "url": "/assets/placeholders/booking_badge_default.png",
                "source": "repo_ui_placeholder",
                "license": "internal",
            },
        },
    }

    resolved = resolve_slot_asset(manifest, slot_id)
    resolved_booking_badge = resolve_slot_asset(manifest, booking_badge_slot)
    assert resolved is not None
    assert resolved_booking_badge is not None
    assert resolved["asset_id"] == "hero_cover_test"
    assert resolved_booking_badge["asset_id"] == "booking_badge_test"

    attached = attach_asset_metadata_to_pages(page_models, manifest)
    attached_cover = attached[cover_vm.page_id]
    attached_booking = attached[booking_vm.page_id]

    hero_slot = attached_cover.internal_state["asset_slots"]["hero"]
    badge_slot = attached_booking.internal_state["asset_slots"]["badge"]
    assert hero_slot["slot_id"] == slot_id
    assert hero_slot["asset_id"] == "hero_cover_test"
    assert badge_slot["slot_id"] == booking_badge_slot
    assert badge_slot["asset_id"] == "booking_badge_test"
    assert attached_cover.hero is not None
    assert attached_cover.hero.image_url == "/assets/placeholders/cover_default.jpg"
