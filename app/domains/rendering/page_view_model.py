from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional, Union

from app.domains.rendering.planning_output import PlanningOutput
from app.domains.rendering.page_planner import PagePlan

logger = logging.getLogger(__name__)


@dataclass
class TimelineItemVM:
    time: str = ""
    name: str = ""
    type_icon: str = ""
    duration: str = ""
    note: str = ""
    entity_id: Optional[str] = None


@dataclass
class TimelineContent:
    items: list[TimelineItemVM] = field(default_factory=list)


@dataclass
class KeyReasonsContent:
    reasons: list[str] = field(default_factory=list)


@dataclass
class StatStripContent:
    stats: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class EntityCardContent:
    entity_id: str = ""
    name: str = ""
    entity_type: str = ""
    hero_image: Optional[str] = None
    tagline: str = ""
    stats: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class RiskCardContent:
    risk_type: str = ""
    severity: str = "medium"
    description: str = ""
    action: Optional[str] = None


@dataclass
class TextBlockContent:
    text: str = ""
    items: list[str] = field(default_factory=list)


@dataclass
class DiyZoneContent:
    """Content model for sticker_zone and freewrite_zone DIY areas on printed handbook pages."""
    sticker_zone: Optional[str] = None     # "top_right" / "bottom_left" / "corner" / None
    freewrite_zone: Optional[str] = None   # "bottom_strip" / "side_margin" / "full_half" / None


@dataclass
class FulfillmentListContent:
    items: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class TocListContent:
    entries: list[dict[str, Any]] = field(default_factory=list)


SectionContent = Union[
    TimelineContent,
    KeyReasonsContent,
    StatStripContent,
    EntityCardContent,
    RiskCardContent,
    TextBlockContent,
    DiyZoneContent,
    FulfillmentListContent,
    TocListContent,
    dict[str, Any],
]


@dataclass
class HeadingVM:
    title: str
    subtitle: Optional[str] = None
    page_number: Optional[int] = None


@dataclass
class HeroVM:
    image_url: Optional[str] = None
    image_alt: str = ""
    orientation: str = "landscape"
    caption: Optional[str] = None


@dataclass
class SectionVM:
    section_type: str
    heading: Optional[str] = None
    content: SectionContent = field(default_factory=dict)


@dataclass
class FooterVM:
    page_number: Optional[int] = None
    chapter_title: Optional[str] = None


@dataclass
class PageViewModel:
    page_id: str
    page_type: str
    page_size: str
    heading: HeadingVM
    hero: Optional[HeroVM] = None
    sections: list[SectionVM] = field(default_factory=list)
    footer: Optional[FooterVM] = None
    day_index: Optional[int] = None
    chapter_id: Optional[str] = None
    stable_inputs: dict[str, Any] = field(default_factory=dict)
    editable_content: dict[str, Any] = field(default_factory=dict)
    internal_state: dict[str, Any] = field(default_factory=dict)


_PAGE_TYPE_PLACEHOLDERS = {
    "cover": "/assets/placeholders/cover_default.jpg",
    "chapter_opener": "/assets/placeholders/chapter_default.jpg",
    "major_activity_detail": "/assets/placeholders/activity_default.jpg",
    "hotel_detail": "/assets/placeholders/hotel_default.jpg",
    "restaurant_detail": "/assets/placeholders/restaurant_default.jpg",
    "photo_theme_detail": "/assets/placeholders/photo_default.jpg",
}


def _entity_id_from_page(page: PagePlan) -> str:
    return page.object_refs[0].object_id if page.object_refs else ""


def _resolve_hero_image(entity_id: Optional[str], page_type: str, payload: PlanningOutput) -> Optional[HeroVM]:
    if entity_id:
        for ev in payload.selection_evidence:
            if ev.get("entity_id") == entity_id and ev.get("hero_image_url"):
                return HeroVM(
                    image_url=str(ev.get("hero_image_url") or ""),
                    image_alt=str(ev.get("name") or ""),
                    orientation=str(ev.get("orientation") or "landscape"),
                )
    placeholder = _PAGE_TYPE_PLACEHOLDERS.get(page_type)
    return HeroVM(image_url=placeholder, image_alt=page_type) if placeholder else None


def _base_vm(page: PagePlan, page_number: int, title: str, subtitle: Optional[str] = None) -> PageViewModel:
    return PageViewModel(
        page_id=page.page_id,
        page_type=page.page_type,
        page_size=page.page_size,
        heading=HeadingVM(title=title, subtitle=subtitle, page_number=page_number),
        footer=FooterVM(page_number=page_number),
        day_index=page.day_index,
        chapter_id=page.chapter_id,
    )


def _inject_diy_zones(vm: PageViewModel, page: PagePlan) -> None:
    """Append a diy_zone section to the VM if the PagePlan has sticker/freewrite zones."""
    if page.sticker_zone or page.freewrite_zone:
        vm.sections.append(
            SectionVM(
                section_type="diy_zone",
                content=DiyZoneContent(
                    sticker_zone=page.sticker_zone,
                    freewrite_zone=page.freewrite_zone,
                ),
            )
        )


def _inject_day_boundaries(vm: PageViewModel, day: Any, mood_sentence: str) -> None:
    vm.stable_inputs = {
        "day_index": day.day_index,
        "title": day.title,
        "primary_area": day.primary_area,
        "slot_count": len(day.slots),
    }
    first_note = day.execution_notes.weather_plan or day.execution_notes.energy_plan
    if not first_note:
        first_note = day.reasoning[0] if day.reasoning else day.must_keep or day.first_cut
    vm.editable_content = {
        "mood_sentence": mood_sentence,
        "day_intro_draft": day.day_goal,
        "timeline_note_draft": first_note or "",
    }
    vm.internal_state = {
        "route_integrity_score": day.route_integrity_score,
        "slot_entity_ids": [slot.entity_id for slot in day.slots if slot.entity_id],
        "trigger_tags": list(day.trigger_tags or []),
        "plan_b_count": len(day.plan_b) if day.plan_b else 0,
    }


def _build_cover_vm(page: PagePlan, payload: PlanningOutput, page_number: int) -> PageViewModel:
    vm = _base_vm(page, page_number, f"{payload.meta.destination} {payload.meta.total_days}D", payload.profile_summary.budget_bias or None)
    vm.hero = _resolve_hero_image(None, "cover", payload)
    vm.sections.append(
        SectionVM(
            section_type="stat_strip",
            content=StatStripContent(
                stats=[
                    {"label": "destination", "value": payload.meta.destination, "unit": ""},
                    {"label": "days", "value": str(payload.meta.total_days), "unit": ""},
                    {"label": "party", "value": payload.profile_summary.party_type, "unit": ""},
                ]
            ),
        )
    )
    _inject_diy_zones(vm, page)
    return vm


def _build_toc_vm(page: PagePlan, payload: PlanningOutput, page_number: int, page_number_map: dict[str, int], all_pages: list[PagePlan]) -> PageViewModel:
    vm = _base_vm(page, page_number, "TOC")
    entries: list[dict[str, Any]] = []
    for p in all_pages:
        if p.page_id == page.page_id or p.page_type == "cover":
            continue
        title = f"Day {p.day_index}" if p.page_type == "day_execution" and p.day_index else p.page_type
        entries.append(
            {
                "title": title,
                "page_number": page_number_map.get(p.page_id, 0),
                "chapter_id": p.chapter_id,
                "page_type": p.page_type,
            }
        )
    vm.sections.append(SectionVM(section_type="toc_list", content=TocListContent(entries=entries)))
    return vm


def _build_preference_fulfillment_vm(page: PagePlan, payload: PlanningOutput, page_number: int) -> PageViewModel:
    vm = _base_vm(page, page_number, "Preference Fulfillment")
    items = [
        {
            "preference_text": x.preference_text,
            "fulfillment_type": x.fulfillment_type,
            "evidence": x.evidence,
            "explanation": x.explanation,
        }
        for x in payload.preference_fulfillment
    ]
    vm.sections.append(SectionVM(section_type="fulfillment_list", content=FulfillmentListContent(items=items)))
    return vm


def _build_day_execution_vm(page: PagePlan, payload: PlanningOutput, page_number: int) -> PageViewModel:
    day = next((d for d in payload.days if d.day_index == page.day_index), None)
    if not day:
        return _build_skeleton_vm(page, payload, page_number)

    vm = _base_vm(page, page_number, f"Day {day.day_index} {day.title}", f"{day.primary_area} | {day.intensity}")
    mood = next((g.mood_sentence for g in payload.emotional_goals if g.day_index == day.day_index), "")
    if mood:
        vm.sections.append(SectionVM(section_type="text_block", heading="Mood", content=TextBlockContent(text=mood)))

    timeline_items = [
        TimelineItemVM(
            time=slot.start_time_hint or "",
            name=slot.title,
            type_icon=slot.kind,
            duration=str(slot.duration_mins or ""),
            note=slot.area,
            entity_id=slot.entity_id,
        )
        for slot in day.slots
    ]
    vm.sections.append(SectionVM(section_type="timeline", content=TimelineContent(items=timeline_items)))

    for r in day.risks:
        vm.sections.append(
            SectionVM(
                section_type="risk_card",
                content=RiskCardContent(risk_type=r.risk_type, description=r.description, action=r.mitigation or None),
            )
        )

    # D3: Plan B alternatives (weather / low_energy / booking_fail)
    if day.plan_b:
        plan_b_items = [
            {
                "trigger": pb.trigger,
                "alternative": pb.alternative,
                "entity_ids": pb.entity_ids,
            }
            for pb in day.plan_b
        ]
        vm.sections.append(SectionVM(
            section_type="plan_b",
            heading="Plan B",
            content={"items": plan_b_items},
        ))

    _inject_day_boundaries(vm, day, mood)
    _inject_diy_zones(vm, page)
    return vm


def _build_major_activity_overview_vm(page: PagePlan, payload: PlanningOutput, page_number: int) -> PageViewModel:
    vm = _base_vm(page, page_number, "Major Activities")
    spots = [{"name": d.must_keep or d.title, "day_index": d.day_index, "area": d.primary_area} for d in payload.days]
    vm.sections.append(SectionVM(section_type="entity_card", content={"spots": spots}))
    return vm


def _build_route_overview_vm(page: PagePlan, payload: PlanningOutput, page_number: int) -> PageViewModel:
    vm = _base_vm(page, page_number, "Route Overview")
    timeline_items = [
        TimelineItemVM(time=f"Day {d.day_index}", name=d.title, type_icon="day", duration=d.intensity, note=d.primary_area)
        for d in payload.days
    ]
    vm.sections.append(SectionVM(section_type="timeline", content=TimelineContent(items=timeline_items)))
    return vm


def _build_hotel_strategy_vm(page: PagePlan, payload: PlanningOutput, page_number: int) -> PageViewModel:
    vm = _base_vm(page, page_number, "Hotel Strategy")
    hotels = []
    for hc in payload.profile_summary.hotel_constraints:
        hotels.append({"city": hc.city, "hotel_name": hc.hotel_name, "area": hc.area, "is_fixed": hc.is_fixed})
    vm.sections.append(SectionVM(section_type="entity_card", content={"spots": hotels}))
    return vm


def _build_booking_window_vm(page: PagePlan, payload: PlanningOutput, page_number: int) -> PageViewModel:
    vm = _base_vm(page, page_number, "Booking Window", "Reserve these early")
    items: list[dict[str, Any]] = []
    for alert in payload.booking_alerts:
        items.append(
            {
                "label": alert.label,
                "entity_id": alert.entity_id,
                "entity_name": alert.entity_name,
                "entity_type": alert.entity_type,
                "booking_level": alert.booking_level,
                "booking_method": alert.booking_method,
                "booking_url": alert.booking_url,
                "advance_booking_days": alert.advance_booking_days,
                "visit_day": alert.visit_day,
                "deadline_date": alert.deadline_date,
                "queue_wait_min": alert.queue_wait_min,
                "deadline_hint": alert.deadline_hint,
                "impact_if_missed": alert.impact_if_missed,
                "fallback_label": alert.fallback_label,
            }
        )

    # Sort by urgency: must_book first, then by deadline_date (earliest first)
    _LEVEL_ORDER = {"must_book": 0, "should_book": 1, "good_to_book": 2, "walkin_ok": 3}
    items.sort(key=lambda x: (
        _LEVEL_ORDER.get(x.get("booking_level", ""), 9),
        x.get("deadline_date") or "9999-99-99",
    ))

    must_book_count = sum(1 for i in items if i.get("booking_level") == "must_book")
    should_book_count = sum(1 for i in items if i.get("booking_level") == "should_book")

    vm.sections.append(SectionVM(
        section_type="stat_strip",
        content=StatStripContent(stats=[
            {"label": "必订", "value": str(must_book_count), "unit": "项"},
            {"label": "建议预订", "value": str(should_book_count), "unit": "项"},
            {"label": "总计", "value": str(len(items)), "unit": "项"},
        ]),
    ))
    vm.sections.append(SectionVM(
        section_type="booking_timeline",
        heading="Booking List",
        content={"items": items},
    ))
    vm.stable_inputs = {"booking_items_count": len(items)}
    vm.editable_content = {
        "booking_headline_draft": "Reserve these early",
        "booking_copy_draft": [
            {
                "label": item.get("label"),
                "entity_name": item.get("entity_name"),
                "booking_level": item.get("booking_level"),
                "deadline_hint": item.get("deadline_hint"),
                "deadline_date": item.get("deadline_date"),
                "impact_if_missed": item.get("impact_if_missed"),
            }
            for item in items
        ],
    }
    vm.internal_state = {"risk_types": sorted({r.risk_type for r in payload.risk_watch_items})}
    return vm


def _build_departure_prep_vm(page: PagePlan, payload: PlanningOutput, page_number: int) -> PageViewModel:
    title = str(payload.prep_notes.get("title") or "Departure Prep")
    vm = _base_vm(page, page_number, title, "Pre-departure checklist")

    # D1: 如果有结构化知识 sections，每个 section 独立渲染
    knowledge_sections = payload.prep_notes.get("knowledge_sections")
    if knowledge_sections:
        for ks in knowledge_sections:
            sec_title = ks.get("title", "")
            sec_items = [str(x) for x in ks.get("items", []) if str(x).strip()]
            sec_tips = [str(x) for x in ks.get("tips", []) if str(x).strip()]
            # items 作为主体内容
            vm.sections.append(SectionVM(
                section_type="text_block",
                heading=sec_title,
                content=TextBlockContent(text=sec_title, items=sec_items),
            ))
            # tips 作为该 section 的实用提示（非空时追加）
            if sec_tips:
                vm.sections.append(SectionVM(
                    section_type="text_block",
                    heading=f"{sec_title} — Tips",
                    content=TextBlockContent(text="", items=sec_tips),
                ))
    else:
        # fallback：旧的 flat list 渲染
        items = [str(x) for x in list(payload.prep_notes.get("items") or []) if str(x).strip()]
        vm.sections.append(SectionVM(section_type="text_block", content=TextBlockContent(text=title, items=items)))

    total_items = sum(
        len(ks.get("items", [])) + len(ks.get("tips", []))
        for ks in (knowledge_sections or [])
    ) if knowledge_sections else len(payload.prep_notes.get("items") or [])
    vm.stable_inputs = {"checklist_item_count": total_items}
    vm.editable_content = {"prep_intro_draft": title}
    vm.internal_state = {
        "risk_watch_count": len(payload.risk_watch_items),
        "has_knowledge_pack": bool(knowledge_sections),
    }
    _inject_diy_zones(vm, page)
    return vm


def _build_live_notice_vm(page: PagePlan, payload: PlanningOutput, page_number: int) -> PageViewModel:
    vm = _base_vm(page, page_number, "Live Notice")
    vm.sections.append(
        SectionVM(
            section_type="risk_card",
            content={
                "items": [
                    {
                        "risk_type": r.risk_type,
                        "description": r.description,
                        "action_required": r.action_required,
                        "day_index": r.day_index,
                    }
                    for r in payload.risk_watch_items
                ]
            },
        )
    )
    return vm


def _build_chapter_opener_vm(page: PagePlan, payload: PlanningOutput, page_number: int) -> PageViewModel:
    summary = next((c for c in payload.chapter_summaries if c.chapter_id == page.chapter_id), None)
    title = summary.title if summary else f"Chapter {page.chapter_id}"
    subtitle = summary.subtitle if summary else None
    goal = summary.goal if summary else ""
    mood = summary.mood if summary else ""

    vm = _base_vm(page, page_number, title, subtitle)
    vm.hero = _resolve_hero_image(None, "chapter_opener", payload)
    if goal:
        vm.sections.append(SectionVM(section_type="text_block", heading="Goal", content=TextBlockContent(text=goal)))
    if mood:
        vm.sections.append(SectionVM(section_type="text_block", heading="Mood", content=TextBlockContent(text=mood)))
    vm.stable_inputs = {"chapter_id": page.chapter_id}
    vm.editable_content = {"chapter_goal_draft": goal}
    vm.internal_state = {"covered_days": summary.covered_days if summary else []}
    _inject_diy_zones(vm, page)
    return vm


def _build_entity_detail_vm(page: PagePlan, payload: PlanningOutput, page_number: int, default_title: str) -> PageViewModel:
    entity_id = _entity_id_from_page(page)
    ev = next((x for x in payload.selection_evidence if x.get("entity_id") == entity_id), None)
    title = str((ev or {}).get("name") or default_title)
    vm = _base_vm(page, page_number, title)
    vm.hero = _resolve_hero_image(entity_id or None, page.page_type, payload)
    if ev and ev.get("why_selected"):
        vm.sections.append(SectionVM(section_type="key_reasons", content=KeyReasonsContent(reasons=[str(ev.get("why_selected"))])))
    _inject_diy_zones(vm, page)
    return vm


def _build_major_activity_detail_vm(page: PagePlan, payload: PlanningOutput, page_number: int) -> PageViewModel:
    return _build_entity_detail_vm(page, payload, page_number, "Major Activity")


def _build_hotel_detail_vm(page: PagePlan, payload: PlanningOutput, page_number: int) -> PageViewModel:
    return _build_entity_detail_vm(page, payload, page_number, "Hotel Detail")


def _build_restaurant_detail_vm(page: PagePlan, payload: PlanningOutput, page_number: int) -> PageViewModel:
    return _build_entity_detail_vm(page, payload, page_number, "Restaurant Detail")


def _build_photo_theme_detail_vm(page: PagePlan, payload: PlanningOutput, page_number: int) -> PageViewModel:
    vm = _build_entity_detail_vm(page, payload, page_number, "Photo Theme")
    vm.sections.append(SectionVM(section_type="photo_tips", content={"tips": []}))
    return vm


def _build_transit_detail_vm(page: PagePlan, payload: PlanningOutput, page_number: int) -> PageViewModel:
    vm = _base_vm(page, page_number, f"Transit Day {page.day_index}" if page.day_index else "Transit Detail")
    day = next((d for d in payload.days if d.day_index == page.day_index), None)
    steps = []
    if day:
        for idx, slot in enumerate(day.slots, start=1):
            if slot.kind == "transit":
                steps.append({"step": idx, "description": slot.title, "duration_mins": slot.duration_mins})
    vm.sections.append(SectionVM(section_type="transit_timeline", content={"steps": steps}))
    return vm


def _build_supplemental_spots_vm(page: PagePlan, payload: PlanningOutput, page_number: int) -> PageViewModel:
    vm = _base_vm(page, page_number, "Supplemental Spots")
    spots = [{"name": s.name, "entity_type": s.entity_type, "why_worth_it": s.would_fit_if or s.why_skipped} for s in payload.skipped_options[:8]]
    if spots:
        vm.sections.append(SectionVM(section_type="entity_card", content={"spots": spots}))
    else:
        vm.sections.append(SectionVM(section_type="text_block", content=TextBlockContent(text="No supplemental spots.")))
    return vm


def _build_skeleton_vm(page: PagePlan, payload: PlanningOutput, page_number: int) -> PageViewModel:
    return _base_vm(page, page_number, page.page_type)


_BUILDERS = {
    "cover": _build_cover_vm,
    "preference_fulfillment": _build_preference_fulfillment_vm,
    "day_execution": _build_day_execution_vm,
    "hotel_detail": _build_hotel_detail_vm,
    "restaurant_detail": _build_restaurant_detail_vm,
    "major_activity_overview": _build_major_activity_overview_vm,
    "route_overview": _build_route_overview_vm,
    "hotel_strategy": _build_hotel_strategy_vm,
    "booking_window": _build_booking_window_vm,
    "departure_prep": _build_departure_prep_vm,
    "live_notice": _build_live_notice_vm,
    "chapter_opener": _build_chapter_opener_vm,
    "major_activity_detail": _build_major_activity_detail_vm,
    "photo_theme_detail": _build_photo_theme_detail_vm,
    "transit_detail": _build_transit_detail_vm,
    "supplemental_spots": _build_supplemental_spots_vm,
}


def build_view_models(pages: list[PagePlan], payload: PlanningOutput) -> dict[str, PageViewModel]:
    result: dict[str, PageViewModel] = {}
    page_number_map: dict[str, int] = {}

    current_page = 1
    toc_pages: list[PagePlan] = []

    for page in sorted(pages, key=lambda p: p.page_order):
        page_number_map[page.page_id] = current_page
        current_page += 1

        if page.page_type == "toc":
            toc_pages.append(page)
            continue

        builder = _BUILDERS.get(page.page_type)
        if not builder:
            result[page.page_id] = _build_skeleton_vm(page, payload, page_number_map[page.page_id])
            continue

        try:
            result[page.page_id] = builder(page, payload, page_number_map[page.page_id])
        except Exception as exc:
            logger.warning("[ViewModelBuilder] %s failed: %s", page.page_id, exc)
            result[page.page_id] = _build_skeleton_vm(page, payload, page_number_map[page.page_id])

    for toc_page in toc_pages:
        try:
            result[toc_page.page_id] = _build_toc_vm(
                toc_page,
                payload,
                page_number_map.get(toc_page.page_id, 1),
                page_number_map,
                pages,
            )
        except Exception as exc:
            logger.warning("[ViewModelBuilder] toc failed: %s", exc)
            result[toc_page.page_id] = _build_skeleton_vm(toc_page, payload, page_number_map.get(toc_page.page_id, 1))

    return result
