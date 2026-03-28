from __future__ import annotations

from typing import Any

from app.domains.rendering.page_editing import (
    apply_persisted_editor_overrides,
    build_page_render_payload,
    deserialize_page_models,
)


def build_shared_page_export_contract(
    plan_metadata: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """
    Build a minimal export-safe contract from persisted page models.

    This is intentionally narrow:
    - it reads the same page_models + page_editor_overrides used by the editor APIs
    - it resolves asset slots through the persisted manifest
    - it returns a template-friendly shape for handbook export adapters
    """
    meta = plan_metadata or {}
    raw_page_models = meta.get("page_models")
    if not isinstance(raw_page_models, dict):
        return None

    base_models = deserialize_page_models(raw_page_models)
    if not base_models:
        return None

    persisted_overrides = meta.get("page_editor_overrides")
    if not isinstance(persisted_overrides, dict):
        persisted_overrides = {}

    asset_manifest = meta.get("page_asset_manifest")
    asset_manifest = asset_manifest if isinstance(asset_manifest, dict) else None

    edited_models = apply_persisted_editor_overrides(base_models, persisted_overrides)
    payload = build_page_render_payload(
        edited_models,
        mode="export",
        asset_manifest=asset_manifest,
    )

    # D6: 从 page_plan 列表中建立 page_id → diy 字段索引
    diy_index: dict[str, dict] = {}
    raw_page_plan = meta.get("page_plan")
    if isinstance(raw_page_plan, list):
        for pp in raw_page_plan:
            if isinstance(pp, dict):
                pid = str(pp.get("page_id") or "")
                if pid:
                    diy_index[pid] = {
                        "sticker_zone": pp.get("sticker_zone"),
                        "freewrite_zone": pp.get("freewrite_zone"),
                    }

    pages = []
    for node in payload.get("nodes", []):
        if not isinstance(node, dict):
            continue
        asset_slots = node.get("asset_slots")
        asset_slots = asset_slots if isinstance(asset_slots, dict) else {}
        page_id = str(node.get("page_id") or "")
        diy = diy_index.get(page_id, {})
        pages.append(
            {
                "page_id": page_id,
                "page_type": str(node.get("page_type") or ""),
                "title": str(node.get("title") or ""),
                "subtitle": str(node.get("subtitle") or ""),
                "page_number": node.get("page_number"),
                "summary": str(node.get("summary") or ""),
                "hero_url": str(node.get("hero_url") or ""),
                "hero_fallback": str(node.get("hero_fallback") or "missing"),
                "hero_source": str(node.get("hero_source") or "none"),
                "asset_slots": _normalize_asset_slots(asset_slots),
                # D6: DIY 区域字段
                "sticker_zone": diy.get("sticker_zone"),
                "freewrite_zone": diy.get("freewrite_zone"),
            }
        )

    return {
        "source": "plan_metadata.page_models",
        "page_count": len(pages),
        "pages": pages,
        "asset_manifest_version": _manifest_version(asset_manifest),
        "asset_channels": list((asset_manifest or {}).get("channels") or (asset_manifest or {}).get("export_targets") or []),
        "has_persisted_edits": bool(persisted_overrides),
        "observation_chain": _normalize_observation_chain(meta),
    }


def _normalize_asset_slots(asset_slots: dict[str, Any]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for slot_name in sorted(asset_slots.keys(), key=str):
        slot_meta = asset_slots.get(slot_name)
        slot_meta = slot_meta if isinstance(slot_meta, dict) else {}
        resolved = slot_meta.get("resolved")
        resolved = resolved if isinstance(resolved, dict) else {}
        normalized.append(
            {
                "slot_name": str(slot_name),
                "slot_id": str(slot_meta.get("slot_id") or ""),
                "asset_id": str(slot_meta.get("asset_id") or ""),
                "asset_url": str(resolved.get("url") or ""),
                "asset_kind": str(resolved.get("kind") or ""),
                "asset_source": str(resolved.get("source") or ""),
                "asset_channel": list(resolved.get("channel") or []),
                "is_placeholder": str(resolved.get("source") or "").strip() == "repo_ui_placeholder",
            }
        )
    return normalized


def _manifest_version(asset_manifest: dict[str, Any] | None) -> str | None:
    if not isinstance(asset_manifest, dict):
        return None
    raw = asset_manifest.get("manifest_version") or asset_manifest.get("version")
    return str(raw) if raw else None


def _normalize_observation_chain(meta: dict[str, Any]) -> dict[str, Any]:
    evidence_bundle = meta.get("evidence_bundle")
    evidence_bundle = evidence_bundle if isinstance(evidence_bundle, dict) else {}
    chain = evidence_bundle.get("observation_chain")
    chain = chain if isinstance(chain, dict) else {}
    return {
        "run_id": chain.get("run_id"),
        "decision_surface": chain.get("decision_surface"),
        "handoff_surface": chain.get("handoff_surface"),
        "eval_surface": chain.get("eval_surface"),
        "regression_surface": chain.get("regression_surface"),
        "replay_surface": chain.get("replay_surface"),
    }



