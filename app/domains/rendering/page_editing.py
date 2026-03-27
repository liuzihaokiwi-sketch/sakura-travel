from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, is_dataclass
from typing import Any

from app.domains.rendering.asset_manifest import attach_asset_metadata_to_pages
from app.domains.rendering.page_view_model import (
    FooterVM,
    HeadingVM,
    HeroVM,
    PageViewModel,
    SectionVM,
    TextBlockContent,
    TimelineContent,
    TimelineItemVM,
)


def serialize_page_models(page_models: dict[str, PageViewModel]) -> dict[str, dict[str, Any]]:
    return {
        page_id: asdict(vm) if is_dataclass(vm) else dict(vm)
        for page_id, vm in page_models.items()
    }


def deserialize_page_models(raw_page_models: dict[str, Any] | None) -> dict[str, PageViewModel]:
    if not isinstance(raw_page_models, dict):
        return {}

    result: dict[str, PageViewModel] = {}
    for page_id, raw in raw_page_models.items():
        if isinstance(raw, PageViewModel):
            result[page_id] = raw
            continue
        if not isinstance(raw, dict):
            continue
        result[page_id] = _page_vm_from_dict(raw)
    return result


def sanitize_editor_overrides(
    page_models: dict[str, PageViewModel],
    edits_by_page: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Only keep editable_content keys declared by the page model itself."""
    sanitized: dict[str, dict[str, Any]] = {}
    for page_id, override_entry in (edits_by_page or {}).items():
        vm = page_models.get(page_id)
        if not vm or not isinstance(override_entry, dict):
            continue
        editable_override = override_entry.get("editable_content")
        if not isinstance(editable_override, dict):
            continue

        allowed_keys = set(vm.editable_content.keys())
        cleaned = {k: deepcopy(v) for k, v in editable_override.items() if k in allowed_keys}
        if cleaned:
            sanitized[page_id] = {"editable_content": cleaned}
    return sanitized


def merge_editor_overrides(
    existing: dict[str, dict[str, Any]] | None,
    incoming: dict[str, dict[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = deepcopy(existing) if isinstance(existing, dict) else {}
    for page_id, override_entry in (incoming or {}).items():
        if not isinstance(override_entry, dict):
            continue
        editable_override = override_entry.get("editable_content")
        if not isinstance(editable_override, dict):
            continue
        merged.setdefault(page_id, {}).setdefault("editable_content", {})
        merged[page_id]["editable_content"].update(deepcopy(editable_override))
    return merged


def apply_persisted_editor_overrides(
    page_models: dict[str, PageViewModel],
    persisted_overrides: dict[str, dict[str, Any]] | None,
) -> dict[str, PageViewModel]:
    if not isinstance(persisted_overrides, dict) or not persisted_overrides:
        return deepcopy(page_models)
    return apply_page_model_edits(page_models, persisted_overrides)


# Legacy compatibility aliases for one migration window.
sanitize_edit_patch = sanitize_editor_overrides
merge_edit_patches = merge_editor_overrides
apply_persisted_edit_patches = apply_persisted_editor_overrides


def apply_page_model_edits(
    page_models: dict[str, PageViewModel],
    edits_by_page: dict[str, dict[str, Any]],
) -> dict[str, PageViewModel]:
    """
    Apply human edits on top of AI draft page models.

    Rules:
    - only `editable_content` can be edited
    - `stable_inputs` and `internal_state` remain system-owned
    - for selected page types we sync edited drafts back into renderable sections
    """
    updated = deepcopy(page_models)

    for page_id, override_entry in edits_by_page.items():
        vm = updated.get(page_id)
        if not vm:
            continue

        editable_override = override_entry.get("editable_content") if isinstance(override_entry, dict) else None
        if not isinstance(editable_override, dict):
            continue

        allowed_keys = set(vm.editable_content.keys())
        for key, value in editable_override.items():
            if key in allowed_keys:
                vm.editable_content[key] = value

        _sync_editable_drafts_to_sections(vm)

    return updated


def build_page_render_payload(
    page_models: dict[str, PageViewModel],
    *,
    mode: str,
    asset_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build preview/render payload from the same page models.
    This keeps preview and render adapters on one data source.
    """
    effective_models = (
        attach_asset_metadata_to_pages(page_models, asset_manifest)
        if isinstance(asset_manifest, dict)
        else page_models
    )
    pages = sorted(effective_models.values(), key=lambda v: int(v.heading.page_number or 0))
    nodes = []

    for vm in pages:
        slot_map = deepcopy(vm.internal_state.get("asset_slots", {}))
        hero_state, hero_source = _resolve_hero_fallback(vm, slot_map)
        summary = ""
        if vm.page_type == "day_execution":
            mood = str(vm.editable_content.get("mood_sentence") or "").strip()
            intro = str(vm.editable_content.get("day_intro_draft") or "").strip()
            summary = " | ".join([x for x in [mood, intro] if x])
        elif vm.page_type == "booking_window":
            summary = str(vm.editable_content.get("booking_headline_draft") or "").strip()
        elif vm.page_type == "departure_prep":
            summary = str(vm.editable_content.get("prep_intro_draft") or "").strip()
        elif vm.sections:
            first = vm.sections[0]
            if isinstance(first.content, TextBlockContent):
                summary = first.content.text
            elif isinstance(first.content, dict):
                summary = str(first.content.get("summary_text") or "")

        nodes.append(
            {
                "page_id": vm.page_id,
                "page_type": vm.page_type,
                "mode": mode,
                "title": vm.heading.title,
                "subtitle": vm.heading.subtitle,
                "page_number": vm.heading.page_number,
                "summary": summary,
                "hero_url": vm.hero.image_url if vm.hero else None,
                "hero_fallback": hero_state,
                "hero_source": hero_source,
                "asset_slots": slot_map,
                "editable_content": deepcopy(vm.editable_content),
            }
        )

    return {
        "mode": mode,
        "count": len(nodes),
        "nodes": nodes,
    }


def _resolve_hero_fallback(vm: PageViewModel, slot_map: dict[str, Any]) -> tuple[str, str]:
    hero_url = (vm.hero.image_url if vm.hero else None) or ""
    hero_slot = slot_map.get("hero") if isinstance(slot_map, dict) else None
    hero_slot = hero_slot if isinstance(hero_slot, dict) else {}
    resolved = hero_slot.get("resolved")
    resolved = resolved if isinstance(resolved, dict) else {}
    resolved_url = str(resolved.get("url") or "").strip()

    if resolved_url:
        return "slot_asset", str(resolved.get("source") or "manifest_asset")
    if hero_url.startswith("/assets/placeholders/"):
        return "page_placeholder", "page_vm_default_placeholder"
    if hero_url:
        return "direct_url", "page_vm_or_entity_hero"
    return "missing", "none"


def _sync_editable_drafts_to_sections(vm: PageViewModel) -> None:
    if vm.page_type == "day_execution":
        mood = str(vm.editable_content.get("mood_sentence") or "").strip()
        intro = str(vm.editable_content.get("day_intro_draft") or "").strip()
        notes = vm.editable_content.get("timeline_note_draft")

        _upsert_text_block(vm.sections, heading="Mood", text=mood)
        _upsert_text_block(vm.sections, heading="Day Intro", text=intro)

        if isinstance(notes, list):
            _patch_timeline_notes(vm.sections, notes)
        return

    if vm.page_type == "booking_window":
        headline = str(vm.editable_content.get("booking_headline_draft") or "").strip()
        if headline:
            vm.heading.subtitle = headline
        booking_copy = vm.editable_content.get("booking_copy_draft")
        if isinstance(booking_copy, list):
            _patch_booking_timeline(vm.sections, booking_copy)
        elif isinstance(booking_copy, str):
            _upsert_text_block(vm.sections, heading="Booking Note", text=booking_copy.strip())
        return

    if vm.page_type == "departure_prep":
        intro = str(vm.editable_content.get("prep_intro_draft") or "").strip()
        _upsert_text_block(vm.sections, heading="Editor Note", text=intro)
        return


def _upsert_text_block(sections: list[SectionVM], *, heading: str, text: str) -> None:
    if not text:
        return
    for section in sections:
        if section.section_type == "text_block" and section.heading == heading and isinstance(section.content, TextBlockContent):
            section.content.text = text
            return
    sections.insert(0, SectionVM(section_type="text_block", heading=heading, content=TextBlockContent(text=text)))


def _patch_timeline_notes(sections: list[SectionVM], notes: list[dict[str, Any]]) -> None:
    timeline_section = next(
        (
            s
            for s in sections
            if s.section_type == "timeline" and isinstance(s.content, TimelineContent)
        ),
        None,
    )
    if not timeline_section:
        return

    note_by_slot = {
        int(item.get("slot_index")): str(item.get("note") or "")
        for item in notes
        if isinstance(item, dict) and item.get("slot_index") is not None
    }

    for idx, item in enumerate(timeline_section.content.items, start=1):
        if idx in note_by_slot:
            item.note = note_by_slot[idx]


def _patch_booking_timeline(sections: list[SectionVM], booking_copy: list[dict[str, Any]]) -> None:
    booking_section = next(
        (
            s
            for s in sections
            if s.section_type == "booking_timeline" and isinstance(s.content, dict)
        ),
        None,
    )
    if not booking_section:
        return

    items = booking_section.content.get("items")
    if not isinstance(items, list):
        return

    copy_by_label: dict[str, dict[str, Any]] = {}
    for entry in booking_copy:
        if not isinstance(entry, dict):
            continue
        label = str(entry.get("label") or "").strip()
        if label:
            copy_by_label[label] = entry

    for item in items:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or "").strip()
        override_entry = copy_by_label.get(label)
        if not override_entry:
            continue
        if "deadline_hint" in override_entry:
            item["deadline_hint"] = override_entry.get("deadline_hint")
        if "impact_if_missed" in override_entry:
            item["impact_if_missed"] = override_entry.get("impact_if_missed")


def _page_vm_from_dict(raw: dict[str, Any]) -> PageViewModel:
    heading_raw = raw.get("heading") if isinstance(raw.get("heading"), dict) else {}
    heading = HeadingVM(
        title=str(heading_raw.get("title") or ""),
        subtitle=heading_raw.get("subtitle"),
        page_number=heading_raw.get("page_number"),
    )

    hero_raw = raw.get("hero") if isinstance(raw.get("hero"), dict) else None
    hero = None
    if hero_raw:
        hero = HeroVM(
            image_url=hero_raw.get("image_url"),
            image_alt=str(hero_raw.get("image_alt") or ""),
            orientation=str(hero_raw.get("orientation") or "landscape"),
            caption=hero_raw.get("caption"),
        )

    footer_raw = raw.get("footer") if isinstance(raw.get("footer"), dict) else None
    footer = None
    if footer_raw:
        footer = FooterVM(
            page_number=footer_raw.get("page_number"),
            chapter_title=footer_raw.get("chapter_title"),
        )

    sections_raw = raw.get("sections") if isinstance(raw.get("sections"), list) else []
    sections: list[SectionVM] = []
    for section_raw in sections_raw:
        if not isinstance(section_raw, dict):
            continue
        section_type = str(section_raw.get("section_type") or "")
        heading_text = section_raw.get("heading")
        content_raw = section_raw.get("content")

        if section_type == "timeline" and isinstance(content_raw, dict):
            timeline_items = []
            for item_raw in content_raw.get("items", []):
                if not isinstance(item_raw, dict):
                    continue
                timeline_items.append(
                    TimelineItemVM(
                        time=str(item_raw.get("time") or ""),
                        name=str(item_raw.get("name") or ""),
                        type_icon=str(item_raw.get("type_icon") or ""),
                        duration=str(item_raw.get("duration") or ""),
                        note=str(item_raw.get("note") or ""),
                        entity_id=item_raw.get("entity_id"),
                    )
                )
            content = TimelineContent(items=timeline_items)
        elif section_type == "text_block" and isinstance(content_raw, dict):
            content = TextBlockContent(
                text=str(content_raw.get("text") or ""),
                items=[str(x) for x in list(content_raw.get("items") or [])],
            )
        else:
            content = content_raw if isinstance(content_raw, dict) else {}

        sections.append(SectionVM(section_type=section_type, heading=heading_text, content=content))

    return PageViewModel(
        page_id=str(raw.get("page_id") or ""),
        page_type=str(raw.get("page_type") or ""),
        page_size=str(raw.get("page_size") or "full"),
        heading=heading,
        hero=hero,
        sections=sections,
        footer=footer,
        day_index=raw.get("day_index"),
        chapter_id=raw.get("chapter_id"),
        stable_inputs=dict(raw.get("stable_inputs") or {}),
        editable_content=dict(raw.get("editable_content") or {}),
        internal_state=dict(raw.get("internal_state") or {}),
    )
