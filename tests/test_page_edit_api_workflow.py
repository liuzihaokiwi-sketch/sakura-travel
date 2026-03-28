from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api import trips_generate as tg
from app.domains.rendering.asset_manifest import hero_slot_id, page_slot_id
from app.domains.rendering.chapter_planner import plan_chapters
from app.domains.rendering.page_editing import serialize_page_models
from app.domains.rendering.page_planner import plan_pages
from app.domains.rendering.page_view_model import build_view_models
from tests.helpers.build_test_planning_output import build_test_planning_output


class _DummyDB:
    async def flush(self) -> None:
        return None


class _TripResult:
    def __init__(self, trip):
        self._trip = trip

    def scalar_one_or_none(self):
        return self._trip


class _TripDB:
    def __init__(self, trip):
        self.trip = trip
        self.commit_count = 0

    async def execute(self, _stmt):
        return _TripResult(self.trip)

    async def commit(self) -> None:
        self.commit_count += 1


def _build_page_models():
    payload = build_test_planning_output()
    chapters = plan_chapters(payload)
    pages = plan_pages(chapters, payload)
    return build_view_models(pages, payload)


@pytest.mark.asyncio
async def test_page_edit_persistence_and_api_reload_render_loop(monkeypatch):
    base_models = _build_page_models()
    day_vm = next(vm for vm in base_models.values() if vm.page_type == "day_execution")
    cover_vm = next(vm for vm in base_models.values() if vm.page_type == "cover")

    slot_id = hero_slot_id(cover_vm.page_id, cover_vm.page_type)
    manifest = {
        "version": "page-assets-v1",
        "slots": {slot_id: {"asset_id": "cover_hero_asset"}},
        "assets": {
            "cover_hero_asset": {
                "kind": "illustration",
                "url": "oss://travel-ai/cover-hero-001.jpg",
                "source": "object_storage",
                "license": "internal",
            }
        },
    }

    trip_id = uuid4()
    plan_obj = SimpleNamespace(
        plan_id=uuid4(),
        trip_request_id=trip_id,
        status="done",
        plan_metadata={
            "page_models": serialize_page_models(base_models),
            "page_asset_manifest": manifest,
        },
    )

    async def _fake_load(_db, req_uuid):
        return plan_obj if req_uuid == trip_id else None

    monkeypatch.setattr(tg, "_load_latest_plan_for_trip", _fake_load)

    stable_before = dict(day_vm.stable_inputs)
    internal_before = dict(day_vm.internal_state)

    save_resp = await tg.save_page_edits(
        str(trip_id),
        tg.PageOverrideSaveRequest(
            edits_by_page={
                day_vm.page_id: {
                    "stable_inputs": {"day_index": 999},
                    "internal_state": {"route_integrity_score": 0.01},
                    "editable_content": {
                        "mood_sentence": "Human mood persisted",
                        "day_intro_draft": "Human intro persisted",
                    },
                }
            }
        ),
        db=_DummyDB(),
    )

    assert save_resp.saved_pages == 1
    stored_patch = plan_obj.plan_metadata["page_editor_overrides"][day_vm.page_id]
    assert set(stored_patch.keys()) == {"editable_content"}
    assert "stable_inputs" not in stored_patch
    assert "internal_state" not in stored_patch

    models_resp = await tg.get_page_models(str(trip_id), db=_DummyDB())
    edited_day = models_resp.page_models[day_vm.page_id]
    assert edited_day["editable_content"]["mood_sentence"] == "Human mood persisted"
    assert edited_day["stable_inputs"] == stable_before
    assert edited_day["internal_state"] == internal_before

    render_resp = await tg.get_page_render_payload(str(trip_id), mode="preview", db=_DummyDB())
    day_node = next(n for n in render_resp.render_payload["nodes"] if n["page_id"] == day_vm.page_id)
    cover_node = next(n for n in render_resp.render_payload["nodes"] if n["page_id"] == cover_vm.page_id)

    assert "Human mood persisted" in day_node["summary"]
    assert cover_node["hero_fallback"] == "slot_asset"
    assert cover_node["hero_source"] == "object_storage"
    assert cover_node["asset_slots"]["hero"]["asset_id"] == "cover_hero_asset"
    assert cover_node["hero_url"] == "oss://travel-ai/cover-hero-001.jpg"


@pytest.mark.asyncio
async def test_page_edit_patch_and_asset_slot_coexist(monkeypatch):
    base_models = _build_page_models()
    booking_vm = next(vm for vm in base_models.values() if vm.page_type == "booking_window")

    badge_slot_id = page_slot_id(booking_vm.page_id, booking_vm.page_type, "badge")
    manifest = {
        "version": "page-assets-v1",
        "slots": {badge_slot_id: {"asset_id": "booking_badge_asset"}},
        "assets": {
            "booking_badge_asset": {
                "kind": "illustration",
                "url": "oss://travel-ai/booking-badge-002.png",
                "source": "object_storage",
                "license": "internal",
            }
        },
    }

    trip_id = uuid4()
    plan_obj = SimpleNamespace(
        plan_id=uuid4(),
        trip_request_id=trip_id,
        status="done",
        plan_metadata={
            "page_models": serialize_page_models(base_models),
            "page_asset_manifest": manifest,
            "page_editor_overrides": {
                booking_vm.page_id: {
                    "editable_content": {
                        "booking_headline_draft": "Booking headline patched",
                    }
                }
            },
        },
    )

    async def _fake_load(_db, req_uuid):
        return plan_obj if req_uuid == trip_id else None

    monkeypatch.setattr(tg, "_load_latest_plan_for_trip", _fake_load)

    render_resp = await tg.get_page_render_payload(str(trip_id), mode="render", db=_DummyDB())
    booking_node = next(n for n in render_resp.render_payload["nodes"] if n["page_id"] == booking_vm.page_id)

    assert booking_node["summary"] == "Booking headline patched"
    assert booking_node["asset_slots"]["badge"]["asset_id"] == "booking_badge_asset"


@pytest.mark.asyncio
async def test_page_model_endpoints_fail_explicitly_when_page_models_missing(monkeypatch):
    trip_id = uuid4()
    plan_obj = SimpleNamespace(
        plan_id=uuid4(),
        trip_request_id=trip_id,
        status="done",
        plan_metadata={
            # intentionally no page_models
            "page_editor_overrides": {},
        },
    )

    async def _fake_load(_db, req_uuid):
        return plan_obj if req_uuid == trip_id else None

    monkeypatch.setattr(tg, "_load_latest_plan_for_trip", _fake_load)

    with pytest.raises(HTTPException) as models_err:
        await tg.get_page_models(str(trip_id), db=_DummyDB())
    assert models_err.value.status_code == 409

    with pytest.raises(HTTPException) as edits_err:
        await tg.save_page_edits(
            str(trip_id),
            tg.PageOverrideSaveRequest(edits_by_page={"any-page": {"editable_content": {"k": "v"}}}),
            db=_DummyDB(),
        )
    assert edits_err.value.status_code == 409

    with pytest.raises(HTTPException) as render_err:
        await tg.get_page_render_payload(str(trip_id), mode="preview", db=_DummyDB())
    assert render_err.value.status_code == 409


@pytest.mark.asyncio
async def test_generate_endpoint_defaults_to_city_circle_worker_chain(monkeypatch):
    trip_id = uuid4()
    trip = SimpleNamespace(
        trip_request_id=trip_id,
        status="new",
        raw_input={
            "destination": "kansai",
            "cities": [{"city_code": "kyoto", "nights": 2}],
            "duration_days": 4,
            "party_type": "couple",
        },
    )
    db = _TripDB(trip)
    enqueued: list[dict[str, object]] = []
    normalized: list[str] = []

    async def _fake_enqueue(job_name, **kwargs):
        enqueued.append({"job_name": job_name, **kwargs})
        return True

    async def _fake_normalize(_ctx, trip_request_id: str):
        normalized.append(trip_request_id)
        return f"profiled:{trip_request_id}"

    monkeypatch.setattr(tg, "enqueue_job", _fake_enqueue)

    import app.workers.__main__ as workers_main

    monkeypatch.setattr(workers_main, "normalize_trip_profile", _fake_normalize)

    resp = await tg.generate_trip(str(trip_id), scene=None, db=db)

    assert normalized == [str(trip_id)]
    assert enqueued == [
        {
            "job_name": "generate_trip",
            "trip_request_id": str(trip_id),
            "scene": "couple",
        }
    ]
    assert resp.job_queued is True
    assert resp.scene == "couple"
