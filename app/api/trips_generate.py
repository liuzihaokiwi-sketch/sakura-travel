from __future__ import annotations

"""
鐞涘瞼鈻肩憴鍕灊娑撳骸顕遍崙?API閵?
娑撴槒顩﹂崗銉ュ經閿?- POST /trips/{id}/generate
- GET /trips/{id}/plan
- GET /trips/{id}/preview
- GET /trips/{id}/exports
- GET /trips/{id}/export
- POST /trips/{id}/page-overrides
- GET /trips/{id}/page-models
- GET /trips/{id}/page-render
"""

import uuid
from typing import Any, Dict, List, Optional

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.queue import enqueue_job
from app.db.models.business import TripRequest
from app.db.models.derived import ExportAsset, ExportJob, ItineraryDay, ItineraryItem, ItineraryPlan
from app.domains.rendering.page_editing import (
    apply_persisted_editor_overrides,
    build_page_render_payload,
    deserialize_page_models,
    merge_editor_overrides,
    sanitize_editor_overrides,
    serialize_page_models,
)
from app.db.session import get_db

router = APIRouter(prefix="/trips", tags=["trips-plan"])


# 閳光偓閳光偓 閸濆秴绨插Ο鈥崇€?閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓

class ItemOut(BaseModel):
    model_config = {"from_attributes": True}
    item_type: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_min: Optional[int] = None
    notes_zh: Optional[str] = None
    estimated_cost_jpy: Optional[int] = None
    is_optional: bool = False
    # 鐟欙絾鐎介崥搴ｆ畱鐎靛苯鐡у▓?    entity_name: Optional[str] = None
    copy_zh: Optional[str] = None
    tips_zh: Optional[str] = None
    area_name: Optional[str] = None
    google_rating: Optional[float] = None


class DayOut(BaseModel):
    day_number: int
    date: Optional[str]
    city_code: str
    day_theme: Optional[str]
    estimated_cost_jpy: Optional[int]
    items: List[ItemOut]


class PlanOut(BaseModel):
    plan_id: str
    trip_request_id: str
    status: str
    plan_metadata: Optional[Dict[str, Any]]
    days: List[DayOut]


class GenerateResponse(BaseModel):
    message: str
    trip_request_id: str
    job_queued: bool
    scene: Optional[str] = None


class PreviewResponse(BaseModel):
    trip_request_id: str
    plan_id: Optional[str]
    preview_url: Optional[str]
    status: str
    message: str


class ExportAssetOut(BaseModel):
    asset_id: int
    asset_type: str          # pdf / h5 / cover_image
    storage_url: str
    file_size_bytes: Optional[int]
    created_at: str


class ExportsResponse(BaseModel):
    trip_request_id: str
    plan_id: Optional[str]
    exports: List[ExportAssetOut]
    total: int


class PageOverrideSaveRequest(BaseModel):
    edits_by_page: Dict[str, Dict[str, Any]]


class PageOverrideSaveResponse(BaseModel):
    trip_request_id: str
    plan_id: str
    saved_pages: int
    editable_keys_saved: int


class PageModelsResponse(BaseModel):
    trip_request_id: str
    plan_id: str
    page_models: Dict[str, Dict[str, Any]]
    page_editor_overrides: Dict[str, Dict[str, Any]]
    page_asset_manifest: Optional[Dict[str, Any]] = None


class PageRenderResponse(BaseModel):
    trip_request_id: str
    plan_id: str
    mode: str
    render_payload: Dict[str, Any]


async def _load_latest_plan_for_trip(
    db: AsyncSession,
    req_uuid: uuid.UUID,
) -> ItineraryPlan | None:
    result = await db.execute(
        select(ItineraryPlan)
        .where(ItineraryPlan.trip_request_id == req_uuid)
        .order_by(ItineraryPlan.version.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


def _load_page_models_with_edits(plan: ItineraryPlan) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    meta = dict(plan.plan_metadata or {})
    raw_page_models = meta.get("page_models")
    base_models = deserialize_page_models(raw_page_models if isinstance(raw_page_models, dict) else {})
    overrides = _read_page_editor_overrides(meta)
    edited_models = apply_persisted_editor_overrides(base_models, overrides)
    serialized = serialize_page_models(edited_models)
    asset_manifest = meta.get("page_asset_manifest")
    asset_manifest = asset_manifest if isinstance(asset_manifest, dict) else None
    return serialized, overrides, meta, asset_manifest


def _read_page_editor_overrides(meta: dict[str, Any]) -> dict[str, dict[str, Any]]:
    overrides = meta.get("page_editor_overrides")
    if isinstance(overrides, dict):
        return overrides
    return {}


def _derive_generation_defaults(raw_input: dict[str, Any]) -> str:
    normalized_input = raw_input if isinstance(raw_input, dict) else {}
    party = str(normalized_input.get("party_type") or "").strip().lower()
    scene_map = {
        "couple": "couple",
        "solo": "solo",
        "family_child": "family",
        "family_no_child": "family",
        "group": "solo",
        "senior": "senior",
    }
    return scene_map.get(party, "couple")


async def _enqueue_generate_trip_job(
    trip_request_id: str,
    *,
    scene: str,
) -> bool:
    try:
        queued = await enqueue_job(
            "generate_trip",
            trip_request_id=trip_request_id,
            scene=scene,
        )
    except Exception:
        queued = None

    if queued:
        return True

    from app.workers.jobs.generate_trip import generate_trip as _generate_trip_job

    asyncio.ensure_future(
        _generate_trip_job(
            {},
            trip_request_id=trip_request_id,
            scene=scene,
        )
    )
    return False


# 閳光偓閳光偓 POST /trips/{id}/generate 閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓

@router.post("/{trip_request_id}/generate", response_model=GenerateResponse, status_code=202)
async def generate_trip(
    trip_request_id: str,
    scene: Optional[str] = Query(
        None,
        description="閸戦缚顢戦崷鐑樻珯閿涙瓭ouple / family / solo / senior",
        examples=["couple"],
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    鐟欙箑褰傜悰宀€鈻肩憴鍕灊 arq job閵?
    瑜版挸澧犳禒鍛暜閹镐礁鐓勭敮鍌氭箑娑撳鎽奸悽鐔稿灇閿涘奔绗夐崘宥呯磻閺€鐐＋濡剝婢橀悽鐔稿灇閸忋儱褰涢妴?
    鏉╂柨娲?202 閸氬函绱濋柅姘崇箖 `GET /trips/{id}/status` 鏉烆喛顕楅悩鑸碘偓渚婄礉
    鐎瑰本鍨氶崥搴ｆ暏 `GET /trips/{id}/preview` 閼惧嘲褰囨０鍕潔闁剧偓甯撮妴?    """
    try:
        req_uuid = uuid.UUID(trip_request_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid trip_request_id format")

    result = await db.execute(select(TripRequest).where(TripRequest.trip_request_id == req_uuid))
    trip_req = result.scalar_one_or_none()
    if trip_req is None:
        raise HTTPException(status_code=404, detail="TripRequest not found")

    # 閳光偓閳光偓 姒涙顓婚崗銉ュ經閿涙艾鐓勭敮鍌氭箑娑撳鎽?閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓
    if trip_req.status in ("assembling", "reviewing", "planning", "normalizing"):
        raise HTTPException(
            status_code=409,
            detail=f"Trip is already being processed (status={trip_req.status})",
        )

    raw_input = trip_req.raw_input if isinstance(trip_req.raw_input, dict) else {}
    if not raw_input:
        raise HTTPException(status_code=409, detail="TripRequest.raw_input is missing")

    resolved_scene = scene or _derive_generation_defaults(raw_input)

    trip_req.status = "normalizing"
    await db.commit()

    from app.workers.__main__ import normalize_trip_profile

    await normalize_trip_profile({}, trip_request_id)
    queued = await _enqueue_generate_trip_job(
        trip_request_id,
        scene=resolved_scene,
    )
    queue_text = "queued" if queued else "running"
    return GenerateResponse(
        message=f"city-circle generation {queue_text} (scene={resolved_scene})",
        trip_request_id=trip_request_id,
        job_queued=queued,
        scene=resolved_scene,
    )


# 閳光偓閳光偓 GET /trips/{id}/plan 閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓

@router.get("/{trip_request_id}/plan", response_model=PlanOut)
async def get_plan(trip_request_id: str, db: AsyncSession = Depends(get_db)):
    """閼惧嘲褰囧鑼晸閹存劗娈戠悰宀€鈻奸弬瑙勵攳"""
    try:
        req_uuid = uuid.UUID(trip_request_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid trip_request_id format")

    plan_result = await db.execute(
        select(ItineraryPlan)
        .where(ItineraryPlan.trip_request_id == req_uuid)
        .order_by(ItineraryPlan.version.desc()).limit(1)
    )
    plan = plan_result.scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail="No itinerary plan found")

    days_result = await db.execute(
        select(ItineraryDay).where(ItineraryDay.plan_id == plan.plan_id).order_by(ItineraryDay.day_number)
    )
    days = days_result.scalars().all()

    import json as _json
    from app.db.models.catalog import EntityBase

    days_out = []
    for day in days:
        items_result = await db.execute(
            select(ItineraryItem).where(ItineraryItem.day_id == day.day_id).order_by(ItineraryItem.sort_order)
        )
        items = items_result.scalars().all()
        rich_items = []
        for i in items:
            # 鐟欙絾鐎?notes_zh JSON
            notes = {}
            if i.notes_zh:
                try:
                    notes = _json.loads(i.notes_zh)
                except (ValueError, TypeError):
                    notes = {"copy_zh": i.notes_zh}
            # 閸忓疇浠?entity
            entity = await db.get(EntityBase, i.entity_id) if i.entity_id else None
            entity_name = notes.get("copy_zh") or (
                getattr(entity, "name_zh", None) or getattr(entity, "name_en", "") if entity else ""
            )
            rich_items.append(ItemOut(
                item_type=i.item_type,
                start_time=str(i.start_time) if i.start_time else None,
                end_time=str(i.end_time) if i.end_time else None,
                duration_min=i.duration_min,
                notes_zh=i.notes_zh,
                estimated_cost_jpy=i.estimated_cost_jpy,
                is_optional=i.is_optional or False,
                entity_name=entity_name,
                copy_zh=notes.get("copy_zh", ""),
                tips_zh=notes.get("tips_zh", ""),
                area_name=getattr(entity, "area_name", "") if entity else "",
                google_rating=float(entity.google_rating) if entity and getattr(entity, "google_rating", None) else None,
            ))
        days_out.append(DayOut(
            day_number=day.day_number, date=day.date, city_code=day.city_code,
            day_theme=day.day_theme, estimated_cost_jpy=day.estimated_cost_jpy,
            items=rich_items,
        ))

    return PlanOut(
        plan_id=str(plan.plan_id), trip_request_id=str(plan.trip_request_id),
        status=plan.status, plan_metadata=plan.plan_metadata, days=days_out,
    )


# 閳光偓閳光偓 GET /trips/{id}/export 閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓



@router.post("/{trip_request_id}/page-overrides", response_model=PageOverrideSaveResponse)
@router.post("/{trip_request_id}/page-edits", response_model=PageOverrideSaveResponse)
async def save_page_overrides(
    trip_request_id: str,
    req: PageOverrideSaveRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Persist editable-only page overrides into plan_metadata.
    System-owned fields (stable_inputs/internal_state) are ignored by design.
    """
    try:
        req_uuid = uuid.UUID(trip_request_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid trip_request_id format")

    plan = await _load_latest_plan_for_trip(db, req_uuid)
    if plan is None:
        raise HTTPException(status_code=404, detail="No itinerary plan found")

    meta = dict(plan.plan_metadata or {})
    base_page_models = deserialize_page_models(meta.get("page_models"))
    if not base_page_models:
        raise HTTPException(status_code=409, detail="plan_metadata.page_models is missing")

    sanitized_overrides = sanitize_editor_overrides(base_page_models, req.edits_by_page)
    existing_overrides = _read_page_editor_overrides(meta)
    merged_overrides = merge_editor_overrides(existing_overrides, sanitized_overrides)
    meta["page_editor_overrides"] = merged_overrides
    plan.plan_metadata = meta
    await db.flush()

    editable_key_count = sum(
        len((x.get("editable_content") or {}))
        for x in merged_overrides.values()
        if isinstance(x, dict)
    )
    return PageOverrideSaveResponse(
        trip_request_id=trip_request_id,
        plan_id=str(plan.plan_id),
        saved_pages=len(sanitized_overrides),
        editable_keys_saved=editable_key_count,
    )


save_page_edits = save_page_overrides
PageEditSaveRequest = PageOverrideSaveRequest
PageEditSaveResponse = PageOverrideSaveResponse


@router.get("/{trip_request_id}/page-models", response_model=PageModelsResponse)
async def get_page_models(
    trip_request_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Read page models with persisted editable overrides applied.
    """
    try:
        req_uuid = uuid.UUID(trip_request_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid trip_request_id format")

    plan = await _load_latest_plan_for_trip(db, req_uuid)
    if plan is None:
        raise HTTPException(status_code=404, detail="No itinerary plan found")

    meta = dict(plan.plan_metadata or {})
    base_page_models = deserialize_page_models(meta.get("page_models"))
    if not base_page_models:
        raise HTTPException(status_code=409, detail="plan_metadata.page_models is missing")

    persisted_overrides = _read_page_editor_overrides(meta)

    edited_models = apply_persisted_editor_overrides(base_page_models, persisted_overrides)
    return PageModelsResponse(
        trip_request_id=trip_request_id,
        plan_id=str(plan.plan_id),
        page_models=serialize_page_models(edited_models),
        page_editor_overrides=persisted_overrides,
        page_asset_manifest=meta.get("page_asset_manifest") if isinstance(meta.get("page_asset_manifest"), dict) else None,
    )


@router.get("/{trip_request_id}/page-render", response_model=PageRenderResponse)
async def get_page_render_payload(
    trip_request_id: str,
    mode: str = Query("preview", pattern="^(preview|render)$"),
    db: AsyncSession = Depends(get_db),
):
    """
    Build preview/render payload from edited page models on the same source data.
    """
    try:
        req_uuid = uuid.UUID(trip_request_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid trip_request_id format")

    plan = await _load_latest_plan_for_trip(db, req_uuid)
    if plan is None:
        raise HTTPException(status_code=404, detail="No itinerary plan found")

    meta = dict(plan.plan_metadata or {})
    base_page_models = deserialize_page_models(meta.get("page_models"))
    if not base_page_models:
        raise HTTPException(status_code=409, detail="plan_metadata.page_models is missing")

    persisted_overrides = _read_page_editor_overrides(meta)
    asset_manifest = meta.get("page_asset_manifest")
    asset_manifest = asset_manifest if isinstance(asset_manifest, dict) else None

    edited_models = apply_persisted_editor_overrides(base_page_models, persisted_overrides)
    payload = build_page_render_payload(edited_models, mode=mode, asset_manifest=asset_manifest)
    return PageRenderResponse(
        trip_request_id=trip_request_id,
        plan_id=str(plan.plan_id),
        mode=mode,
        render_payload=payload,
    )

@router.get("/{trip_request_id}/export")
async def export_plan(trip_request_id: str, fmt: str = "html", db: AsyncSession = Depends(get_db)):
    raise HTTPException(
        status_code=410,
        detail=(
            "Legacy export endpoint is retired from main flow. "
            "Use page-model export chain (/api/plan/{id}/pdf or shared_export_contract-based path)."
        ),
    )

# 閳光偓閳光偓 GET /trips/{id}/preview 閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓

@router.get("/{trip_request_id}/preview", response_model=PreviewResponse)
async def get_preview(
    trip_request_id: str,
    db: AsyncSession = Depends(get_db),
):
    del trip_request_id, db
    raise HTTPException(
        status_code=410,
        detail=(
            "Legacy H5 preview endpoint is retired from main flow. "
            "Use /trips/{id}/preview-data for page semantics preview."
        ),
    )

# GET /trips/{id}/exports 閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓閳光偓

@router.get("/{trip_request_id}/exports", response_model=ExportsResponse)
async def get_exports(
    trip_request_id: str,
    asset_type: Optional[str] = Query(
        None,
        description="legacy endpoint retired",
    ),
    db: AsyncSession = Depends(get_db),
):
    del trip_request_id, asset_type, db
    raise HTTPException(
        status_code=410,
        detail=(
            "Legacy exports listing endpoint is retired from main flow. "
            "Use /trips/{id}/preview-data for page semantics preview and /api/plan/{id}/pdf for handbook PDF."
        ),
    )


