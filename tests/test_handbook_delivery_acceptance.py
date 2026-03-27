from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.rendering.asset_manifest import hero_slot_id, page_slot_id
from app.domains.rendering.magazine.html_renderer import render_html
from app.domains.rendering.magazine.pdf_renderer import render_pdf
from app.domains.rendering.shared_export_contract import build_shared_page_export_contract
from tests.test_shared_export_contract import _build_plan_metadata, _insert_plan, db_session


def _page_by_type(contract: dict, page_type: str) -> dict:
    return next(page for page in contract["pages"] if page["page_type"] == page_type)


def test_handbook_delivery_contract_golden_baseline():
    plan_metadata, _ = _build_plan_metadata()

    contract = build_shared_page_export_contract(plan_metadata)

    assert contract is not None
    assert contract["source"] == "plan_metadata.page_models"
    assert contract["page_count"] >= 3
    assert contract["asset_manifest_version"] is None
    assert contract["has_persisted_edits"] is False

    page_types = {page["page_type"] for page in contract["pages"]}
    assert "cover" in page_types
    assert "day_execution" in page_types
    assert "booking_window" in page_types

    day_page = _page_by_type(contract, "day_execution")
    assert day_page["summary"] == "Easy first-day exploration. | Adapt with light pace"
    assert day_page["asset_slots"] == []
    assert _page_by_type(contract, "cover")["hero_fallback"] == "page_placeholder"


@pytest.mark.asyncio
async def test_handbook_delivery_html_accepts_persisted_edits(db_session: AsyncSession):
    plan_metadata, page_models = _build_plan_metadata(page_editor_overrides={})
    day_vm = next(vm for vm in page_models.values() if vm.page_type == "day_execution")
    booking_vm = next(vm for vm in page_models.values() if vm.page_type == "booking_window")
    prep_vm = next(vm for vm in page_models.values() if vm.page_type == "departure_prep")

    plan_metadata["page_editor_overrides"] = {
        day_vm.page_id: {
            "editable_content": {
                "mood_sentence": "Morning should stay slow and calm.",
                "day_intro_draft": "Human adjusted intro",
            }
        },
        booking_vm.page_id: {
            "editable_content": {
                "booking_headline_draft": "Human booking headline",
            }
        },
        prep_vm.page_id: {
            "editable_content": {
                "prep_intro_draft": "Bring meds and power bank.",
            }
        },
    }

    contract = build_shared_page_export_contract(plan_metadata)
    assert contract is not None
    assert contract["has_persisted_edits"] is True
    assert _page_by_type(contract, "day_execution")["summary"] == (
        "Morning should stay slow and calm. | Human adjusted intro"
    )
    assert _page_by_type(contract, "booking_window")["summary"] == "Human booking headline"
    assert _page_by_type(contract, "departure_prep")["summary"] == "Bring meds and power bank."

    plan_id = await _insert_plan(db_session, plan_metadata)
    html = await render_html(plan_id, db_session)

    assert "Morning should stay slow and calm. | Human adjusted intro" in html
    assert "Human booking headline" in html
    assert "Bring meds and power bank." in html


@pytest.mark.asyncio
async def test_handbook_delivery_assets_survive_formal_export_html(db_session: AsyncSession):
    plan_metadata, page_models = _build_plan_metadata()
    cover_vm = next(vm for vm in page_models.values() if vm.page_type == "cover")
    booking_vm = next(vm for vm in page_models.values() if vm.page_type == "booking_window")

    cover_slot = hero_slot_id(cover_vm.page_id, cover_vm.page_type)
    booking_badge_slot = page_slot_id(
        page_id=booking_vm.page_id,
        page_type=booking_vm.page_type,
        slot_name="badge",
    )
    plan_metadata["page_asset_manifest"] = {
        "version": "page-assets-v1",
        "slots": {
            cover_slot: {"asset_id": "day_hero_asset"},
            booking_badge_slot: {"asset_id": "booking_badge_asset"},
        },
        "assets": {
            "day_hero_asset": {
                "kind": "photo",
                "url": "oss://travel-ai/day-hero-001.jpg",
                "source": "object_storage",
            },
            "booking_badge_asset": {
                "kind": "illustration",
                "url": "oss://travel-ai/booking-badge-001.png",
                "source": "object_storage",
            },
        },
    }

    contract = build_shared_page_export_contract(plan_metadata)
    assert contract is not None
    assert contract["asset_manifest_version"] == "page-assets-v1"

    cover_page = _page_by_type(contract, "cover")
    booking_page = _page_by_type(contract, "booking_window")
    assert cover_page["hero_url"] == "oss://travel-ai/day-hero-001.jpg"
    assert cover_page["hero_fallback"] == "slot_asset"
    assert cover_page["hero_source"] == "object_storage"
    hero_slot = cover_page["asset_slots"][0]
    assert hero_slot["slot_name"] == "hero"
    assert hero_slot["slot_id"] == cover_slot
    assert hero_slot["asset_id"] == "day_hero_asset"
    assert hero_slot["asset_url"] == "oss://travel-ai/day-hero-001.jpg"
    assert hero_slot["asset_kind"] == "photo"
    assert hero_slot["asset_source"] == "object_storage"
    assert hero_slot["is_placeholder"] is False
    assert any(
        slot["slot_name"] == "badge"
        and slot["asset_id"] == "booking_badge_asset"
        and slot["asset_url"] == "oss://travel-ai/booking-badge-001.png"
        for slot in booking_page["asset_slots"]
    )

    plan_id = await _insert_plan(db_session, plan_metadata)
    html = await render_html(plan_id, db_session)

    assert "page-assets-v1" in html
    assert "oss://travel-ai/day-hero-001.jpg" in html
    assert "booking_badge_asset" in html
    assert "oss://travel-ai/booking-badge-001.png" in html


@pytest.mark.asyncio
async def test_handbook_delivery_pdf_smoke_uses_shared_export_bridge(db_session: AsyncSession):
    plan_metadata, page_models = _build_plan_metadata()
    cover_vm = next(vm for vm in page_models.values() if vm.page_type == "cover")
    cover_slot = hero_slot_id(cover_vm.page_id, cover_vm.page_type)
    plan_metadata["page_asset_manifest"] = {
        "version": "page-assets-v1",
        "slots": {
            cover_slot: {"asset_id": "day_hero_asset"},
        },
        "assets": {
            "day_hero_asset": {
                "kind": "photo",
                "url": "oss://travel-ai/day-hero-001.jpg",
                "source": "object_storage",
            },
        },
    }

    plan_id = await _insert_plan(db_session, plan_metadata)
    html = await render_html(plan_id, db_session)

    assert "共享页面导出" in html
    assert "page-assets-v1" in html

    try:
        pdf_bytes = await render_pdf(
            plan_id,
            db_session,
            watermark_text="acceptance-smoke-watermark",
        )
    except (ImportError, OSError) as exc:
        err = str(exc).lower()
        assert "weasyprint" in err or "libgobject" in err or "gtk" in err
    else:
        assert pdf_bytes.startswith(b"%PDF-")
        assert len(pdf_bytes) > 5_000

