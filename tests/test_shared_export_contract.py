from __future__ import annotations

import uuid
from typing import AsyncGenerator

import pytest
from sqlalchemy import JSON, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql.sqltypes import Uuid as SA_Uuid

from app.db.models.business import TripRequest
from app.db.models.derived import ItineraryPlan
from app.db.session import Base
from app.domains.rendering.asset_manifest import hero_slot_id, page_slot_id
from app.domains.rendering.chapter_planner import plan_chapters
from app.domains.rendering.layer2_handoff import build_layer2_delivery_handoff
from app.domains.rendering.magazine.html_renderer import render_html
from app.domains.rendering.shared_export_contract import build_shared_page_export_contract
from app.domains.rendering.page_editing import serialize_page_models
from app.domains.rendering.page_planner import plan_pages
from app.domains.rendering.page_view_model import build_view_models


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    import sqlite3

    from app.db.models import (  # noqa: F401
        business,
        catalog,
        city_circles,
        config_center,
        corridors,
        derived,
        detail_forms,
        fragments,
        live_risk_rules,
        operator_overrides,
        page_assets,
        snapshots,
        soft_rules,
        temporal,
        trace,
    )

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    for table in Base.metadata.tables.values():
        for col in table.columns:
            if isinstance(col.type, JSONB):
                col.type = JSON()
            elif isinstance(col.type, (PG_UUID, SA_Uuid)):
                col.type = String(36)

    sqlite3.register_adapter(uuid.UUID, lambda value: str(value))

    original_bind_processor = SA_Uuid.bind_processor

    def _patched_bind_processor(self, dialect):
        if dialect.name == "sqlite":
            def process(value):
                if value is None:
                    return None
                return str(value)

            return process
        return original_bind_processor(self, dialect)

    SA_Uuid.bind_processor = _patched_bind_processor

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


def _report_content() -> dict:
    return {
        "schema_version": "v2",
        "version": "circle-v1",
        "generated_at": "2026-03-26T10:00:00+00:00",
        "layer1_overview": {
            "booking_reminders": [
                {"item": "Sagano Train", "deadline": "7 days before", "impact": "queue risk"}
            ],
            "prep_checklist": {"title": "Departure checklist", "items": ["Passport", "eSIM"]},
        },
        "layer2_daily": [
            {
                "day_number": 1,
                "city_code": "kyoto",
                "day_type": "arrival",
                "day_theme": "Higashiyama slow day",
                "primary_area": "higashiyama",
                "day_goal": "Adapt with light pace",
                "must_keep": "Kiyomizu",
                "first_cut": "Night photo walk",
                "start_anchor": "Kyoto station",
                "end_anchor": "Gion",
                "route_integrity_score": 0.88,
                "intensity": "balanced",
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
                    }
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


def _handoff_metadata() -> dict:
    return {
        "evidence_bundle": {
            "run_id": "run-123",
            "hard_unconsumed_count": 0,
            "compiled_constraints": {"must_go_clusters": ["kyo_kiyomizu"]},
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


def _build_page_models():
    payload, _ = build_layer2_delivery_handoff(
        report_content=_report_content(),
        plan_metadata=_handoff_metadata(),
        plan_id="plan-1",
    )
    chapters = plan_chapters(payload)
    pages = plan_pages(chapters, payload)
    return build_view_models(pages, payload)


def _build_plan_metadata(
    *,
    page_editor_overrides: dict | None = None,
    page_asset_manifest: dict | None = None,
) -> tuple[dict, dict[str, object]]:
    page_models = _build_page_models()
    return (
        {
            "scene": "general",
            "city_codes": ["kyoto"],
            "total_days": 1,
            "key_bookings": [],
            "pre_trip_checklist": [],
            "template_meta": {
                "title_zh": "测试共享导出合同",
                "tagline_zh": "验证编辑后的页面模型进入正式导出链",
            },
            "page_models": serialize_page_models(page_models),
            "page_editor_overrides": page_editor_overrides or {},
            "page_asset_manifest": page_asset_manifest or {},
        },
        page_models,
    )


async def _insert_plan(session: AsyncSession, plan_metadata: dict) -> uuid.UUID:
    trip_id = uuid.uuid4()
    plan_id = uuid.uuid4()

    session.add(
        TripRequest(
            trip_request_id=trip_id,
            raw_input={"wechat_id": "test-user"},
            status="reviewing",
        )
    )
    session.add(
        ItineraryPlan(
            plan_id=plan_id,
            trip_request_id=trip_id,
            version=1,
            status="reviewed",
            plan_metadata=plan_metadata,
            report_content=_report_content(),
        )
    )
    await session.commit()
    return plan_id


@pytest.mark.asyncio
async def test_unedited_page_models_enter_export_path(db_session: AsyncSession):
    plan_metadata, _ = _build_plan_metadata()
    plan_id = await _insert_plan(db_session, plan_metadata)

    html = await render_html(plan_id, db_session)

    assert "共享页面导出" in html
    assert "Easy first-day exploration. | Adapt with light pace" in html
    assert "Reserve these early" in html
    assert "Departure checklist" in html
    assert "hero_fallback=page_placeholder" in html


@pytest.mark.asyncio
async def test_edited_page_models_enter_export_path(db_session: AsyncSession):
    plan_metadata, page_models = _build_plan_metadata(
        page_editor_overrides={},
    )
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
    plan_id = await _insert_plan(db_session, plan_metadata)

    html = await render_html(plan_id, db_session)

    assert "Morning should stay slow and calm. | Human adjusted intro" in html
    assert "Human booking headline" in html
    assert "Bring meds and power bank." in html


@pytest.mark.asyncio
async def test_asset_slot_resolution_survives_export_path(db_session: AsyncSession):
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
    plan_id = await _insert_plan(db_session, plan_metadata)

    html = await render_html(plan_id, db_session)

    assert "page-assets-v1" in html
    assert "oss://travel-ai/day-hero-001.jpg" in html
    assert "booking_badge_asset" in html
    assert "oss://travel-ai/booking-badge-001.png" in html


@pytest.mark.asyncio
async def test_export_html_fails_explicitly_when_page_models_missing(db_session: AsyncSession):
    plan_metadata, _ = _build_plan_metadata()
    plan_metadata.pop("page_models", None)
    plan_id = await _insert_plan(db_session, plan_metadata)

    with pytest.raises(ValueError, match="page_models is missing"):
        await render_html(plan_id, db_session)



def test_export_contract_asset_slots_are_stably_sorted_by_slot_name():
    plan_metadata, page_models = _build_plan_metadata()
    booking_vm = next(vm for vm in page_models.values() if vm.page_type == "booking_window")

    zeta_slot = page_slot_id(
        page_id=booking_vm.page_id,
        page_type=booking_vm.page_type,
        slot_name="zeta",
    )
    alpha_slot = page_slot_id(
        page_id=booking_vm.page_id,
        page_type=booking_vm.page_type,
        slot_name="alpha",
    )

    plan_metadata["page_asset_manifest"] = {
        "version": "page-assets-v1",
        "slots": {
            zeta_slot: {"asset_id": "asset_zeta"},
            alpha_slot: {"asset_id": "asset_alpha"},
        },
        "assets": {
            "asset_zeta": {
                "kind": "illustration",
                "url": "oss://travel-ai/zeta.png",
                "source": "object_storage",
            },
            "asset_alpha": {
                "kind": "illustration",
                "url": "oss://travel-ai/alpha.png",
                "source": "object_storage",
            },
        },
    }

    contract = build_shared_page_export_contract(plan_metadata)
    assert contract is not None

    booking_page = next(page for page in contract["pages"] if page["page_type"] == "booking_window")
    slot_names = [slot["slot_name"] for slot in booking_page["asset_slots"]]
    assert slot_names == ["alpha", "zeta"]


