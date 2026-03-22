"""
page_view_model.py — 页面 ViewModel 构建器（L3-05）

输入：list[PagePlan] + ReportPayloadV2 + fragment outputs
输出：dict[str, PageViewModel]  (page_id → view model)

两遍构建模式（F1）：
  Pass 1：构建非 toc 页的 VM，同时分配页码
  Pass 2：用已确定的页码回填 toc VM

Hero 图片优先级（F4）：
  1. page_hero_registry 表配置
  2. entity_media hero
  3. sort_order 最小图片
  4. 页型默认 placeholder
  5. None

SectionVM.content 使用具体类型（F10）。

依赖：
  page_planner.PagePlan
  page_type_registry.get_page_type
  app.domains.planning.report_schema.ReportPayloadV2
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional, Union

from app.domains.planning.report_schema import ReportPayloadV2
from app.domains.rendering.page_planner import PagePlan

logger = logging.getLogger(__name__)


# ── Section Content 具体类型（F10） ───────────────────────────────────────────

@dataclass
class TimelineItemVM:
    time: str = ""
    name: str = ""
    type_icon: str = ""       # "poi" / "restaurant" / "hotel" / "transit" / "buffer"
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
    stats: list[dict] = field(default_factory=list)   # [{label, value, unit}]


@dataclass
class EntityCardContent:
    entity_id: str = ""
    name: str = ""
    entity_type: str = ""
    hero_image: Optional[str] = None
    tagline: str = ""
    stats: list[dict] = field(default_factory=list)


@dataclass
class RiskCardContent:
    risk_type: str = ""
    severity: str = "medium"
    description: str = ""
    action: Optional[str] = None


@dataclass
class TextBlockContent:
    text: str = ""
    items: list[str] = field(default_factory=list)   # bullet list


@dataclass
class FulfillmentListContent:
    items: list[dict] = field(default_factory=list)  # [{preference_text, fulfillment_type, evidence}]


@dataclass
class TocListContent:
    entries: list[dict] = field(default_factory=list)  # [{title, page_number, chapter_id}]


# Union type
SectionContent = Union[
    TimelineContent, KeyReasonsContent, StatStripContent,
    EntityCardContent, RiskCardContent, TextBlockContent,
    FulfillmentListContent, TocListContent, dict,
]


# ── View Model 数据类 ─────────────────────────────────────────────────────────

@dataclass
class HeadingVM:
    title: str
    subtitle: Optional[str] = None
    page_number: Optional[int] = None


@dataclass
class HeroVM:
    image_url: Optional[str] = None
    image_alt: str = ""
    orientation: str = "landscape"    # landscape / portrait / square
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


# ── Hero 图片解析（F4） ────────────────────────────────────────────────────────

_PAGE_TYPE_PLACEHOLDERS = {
    "cover":                "/assets/placeholders/cover_default.jpg",
    "chapter_opener":       "/assets/placeholders/chapter_default.jpg",
    "major_activity_detail":"/assets/placeholders/activity_default.jpg",
    "hotel_detail":         "/assets/placeholders/hotel_default.jpg",
    "restaurant_detail":    "/assets/placeholders/restaurant_default.jpg",
    "photo_theme_detail":   "/assets/placeholders/photo_default.jpg",
}


def _resolve_hero_image(
    entity_id: Optional[str],
    entity_type: str,
    page_type: str,
    payload: ReportPayloadV2,
) -> Optional[HeroVM]:
    """
    Hero 图片解析优先级：
    1. page_hero_registry（payload.selection_evidence 中找 hero_image_url）
    2. entity_media 中 media_type=hero
    3. entity_media 中 sort_order 最小
    4. 页型默认 placeholder
    5. None（前端自行处理无图状态）
    """
    # 1. 从 selection_evidence 找 hero_image_url
    if entity_id:
        for ev in payload.selection_evidence:
            if ev.get("entity_id") == entity_id and ev.get("hero_image_url"):
                return HeroVM(
                    image_url=ev["hero_image_url"],
                    image_alt=ev.get("name", ""),
                    orientation=ev.get("orientation", "landscape"),
                )

    # 4. 页型 placeholder
    placeholder = _PAGE_TYPE_PLACEHOLDERS.get(page_type)
    if placeholder:
        return HeroVM(image_url=placeholder, image_alt=page_type)

    # 5. None
    return None


# ── 各页型 Builder 函数 ───────────────────────────────────────────────────────

def _build_cover_vm(page: PagePlan, payload: ReportPayloadV2, page_number: int) -> PageViewModel:
    meta = payload.meta
    profile = payload.profile_summary
    hero = _resolve_hero_image(None, "trip", "cover", payload)

    stats = [
        {"label": "目的地", "value": meta.destination, "unit": ""},
        {"label": "天数", "value": str(meta.total_days), "unit": "天"},
        {"label": "同行", "value": profile.party_type, "unit": ""},
    ]

    return PageViewModel(
        page_id=page.page_id,
        page_type="cover",
        page_size=page.page_size,
        heading=HeadingVM(
            title=f"{meta.destination} {meta.total_days}天行程",
            subtitle=profile.budget_bias or None,
            page_number=page_number,
        ),
        hero=hero,
        sections=[
            SectionVM(
                section_type="stat_strip",
                content=StatStripContent(stats=stats),
            )
        ],
        footer=FooterVM(page_number=page_number),
        chapter_id=page.chapter_id,
    )


def _build_toc_vm(
    page: PagePlan,
    payload: ReportPayloadV2,
    page_number: int,
    page_number_map: dict[str, int],
    all_pages: list[PagePlan],
) -> PageViewModel:
    """两遍构建：用 page_number_map 回填目录"""
    entries = []
    seen_chapters: set[str] = set()

    for p in all_pages:
        if p.page_id == page.page_id:
            continue
        if p.chapter_id not in seen_chapters:
            seen_chapters.add(p.chapter_id)

        # 只放 chapter_opener、day_execution 和 frontmatter 固定页进目录
        if p.page_type in ("cover", "toc"):
            continue
        if p.page_type in (
            "chapter_opener", "major_activity_overview", "route_overview",
            "hotel_strategy", "preference_fulfillment",
        ):
            entries.append({
                "title": _page_title_hint(p, payload),
                "page_number": page_number_map.get(p.page_id, 0),
                "chapter_id": p.chapter_id,
                "page_type": p.page_type,
            })
        elif p.page_type == "day_execution" and p.day_index is not None:
            day_sec = next((d for d in payload.days if d.day_index == p.day_index), None)
            entries.append({
                "title": f"Day {p.day_index}" + (f" · {day_sec.title}" if day_sec else ""),
                "page_number": page_number_map.get(p.page_id, 0),
                "chapter_id": p.chapter_id,
                "page_type": "day_execution",
            })

    return PageViewModel(
        page_id=page.page_id,
        page_type="toc",
        page_size=page.page_size,
        heading=HeadingVM(title="目录", page_number=page_number),
        sections=[
            SectionVM(section_type="toc_list", content=TocListContent(entries=entries))
        ],
        footer=FooterVM(page_number=page_number),
        chapter_id=page.chapter_id,
    )


def _page_title_hint(page: PagePlan, payload: ReportPayloadV2) -> str:
    """为目录条目生成可读标题"""
    hints = {
        "major_activity_overview": "主要体验一览",
        "route_overview":          "路线总览",
        "hotel_strategy":          "酒店策略",
        "preference_fulfillment":  "偏好兑现",
        "booking_window":          "预约时间窗",
        "departure_prep":          "出发准备",
        "live_notice":             "实时注意事项",
        "chapter_opener":          "章节开篇",
        "supplemental_spots":      "补充景点",
    }
    return hints.get(page.page_type, page.page_type)


def _build_preference_fulfillment_vm(
    page: PagePlan, payload: ReportPayloadV2, page_number: int
) -> PageViewModel:
    items = [
        {
            "preference_text": item.preference_text,
            "fulfillment_type": item.fulfillment_type,
            "evidence": item.evidence,
            "explanation": item.explanation,
        }
        for item in payload.preference_fulfillment
    ]
    return PageViewModel(
        page_id=page.page_id,
        page_type="preference_fulfillment",
        page_size=page.page_size,
        heading=HeadingVM(title="你的偏好，这样被满足了", page_number=page_number),
        sections=[
            SectionVM(
                section_type="fulfillment_list",
                heading="偏好兑现清单",
                content=FulfillmentListContent(items=items),
            )
        ],
        footer=FooterVM(page_number=page_number),
        chapter_id=page.chapter_id,
    )


def _build_day_execution_vm(
    page: PagePlan, payload: ReportPayloadV2, page_number: int
) -> PageViewModel:
    day_sec = next((d for d in payload.days if d.day_index == page.day_index), None)
    if not day_sec:
        return _build_skeleton_vm(page, payload, page_number)

    # 情绪目标
    eg = next(
        (g for g in payload.emotional_goals if g.day_index == page.day_index), None
    )
    mood_sentence = eg.mood_sentence if eg else ""

    # Timeline items
    timeline_items = []
    for slot in day_sec.slots:
        timeline_items.append(TimelineItemVM(
            time=slot.start_time_hint or "",
            name=slot.title,
            type_icon=slot.kind,
            duration=f"{slot.duration_mins}分钟" if slot.duration_mins else "",
            note=slot.area,
            entity_id=slot.entity_id,
        ))

    sections = [
        SectionVM(
            section_type="timeline",
            heading=f"Day {day_sec.day_index} · {day_sec.title}",
            content=TimelineContent(items=timeline_items),
        )
    ]

    if mood_sentence:
        sections.insert(0, SectionVM(
            section_type="text_block",
            heading="今日基调",
            content=TextBlockContent(text=mood_sentence),
        ))

    if day_sec.risks:
        risk_items = [
            RiskCardContent(
                risk_type=r.risk_type,
                description=r.description,
                action=r.mitigation or None,
            )
            for r in day_sec.risks
        ]
        for rc in risk_items:
            sections.append(SectionVM(section_type="risk_card", content=rc))

    intensity_label = {"light": "轻松", "balanced": "均衡", "dense": "偏满"}.get(
        day_sec.intensity, day_sec.intensity
    )

    return PageViewModel(
        page_id=page.page_id,
        page_type="day_execution",
        page_size=page.page_size,
        heading=HeadingVM(
            title=f"Day {day_sec.day_index} · {day_sec.title}",
            subtitle=f"{day_sec.primary_area}  ·  节奏：{intensity_label}",
            page_number=page_number,
        ),
        sections=sections,
        footer=FooterVM(page_number=page_number, chapter_title=day_sec.primary_area),
        day_index=day_sec.day_index,
        chapter_id=page.chapter_id,
    )


def _build_hotel_detail_vm(
    page: PagePlan, payload: ReportPayloadV2, page_number: int
) -> PageViewModel:
    # 从 conditional_sections 找酒店数据
    entity_id = (page.object_refs[0].object_id if page.object_refs else "") or ""
    hotel_data = _find_entity_data(entity_id, "hotel", payload)
    name = hotel_data.get("name", "酒店详情") if hotel_data else "酒店详情"
    hero = _resolve_hero_image(entity_id or None, "hotel", "hotel_detail", payload)

    sections = []
    why_selected = hotel_data.get("why_selected", "") if hotel_data else ""
    if why_selected:
        sections.append(SectionVM(
            section_type="key_reasons",
            heading="为什么选这里",
            content=KeyReasonsContent(reasons=[why_selected]),
        ))

    stats = []
    if hotel_data:
        if hotel_data.get("area"):
            stats.append({"label": "区域", "value": hotel_data["area"], "unit": ""})
        if hotel_data.get("price_band"):
            stats.append({"label": "价格带", "value": hotel_data["price_band"], "unit": ""})
        if hotel_data.get("nearest_station"):
            stats.append({"label": "最近车站", "value": hotel_data["nearest_station"], "unit": ""})
        served_days = hotel_data.get("served_days", [])
        if served_days:
            stats.append({"label": "入住天数", "value": str(len(served_days)), "unit": "晚"})

    if stats:
        sections.append(SectionVM(
            section_type="stat_strip",
            content=StatStripContent(stats=stats),
        ))

    return PageViewModel(
        page_id=page.page_id,
        page_type="hotel_detail",
        page_size=page.page_size,
        heading=HeadingVM(title=name, page_number=page_number),
        hero=hero,
        sections=sections,
        footer=FooterVM(page_number=page_number),
        chapter_id=page.chapter_id,
    )


def _build_restaurant_detail_vm(
    page: PagePlan, payload: ReportPayloadV2, page_number: int
) -> PageViewModel:
    entity_id = (page.object_refs[0].object_id if page.object_refs else "") or ""
    rest_data = _find_entity_data(entity_id, "restaurant", payload)
    name = rest_data.get("name", "餐厅详情") if rest_data else "餐厅详情"
    hero = _resolve_hero_image(entity_id or None, "restaurant", "restaurant_detail", payload)

    sections = []
    why_selected = rest_data.get("why_selected", "") if rest_data else ""
    if why_selected:
        sections.append(SectionVM(
            section_type="key_reasons",
            heading="为什么推荐",
            content=KeyReasonsContent(reasons=[why_selected]),
        ))

    stats = []
    if rest_data:
        if rest_data.get("cuisine_type"):
            stats.append({"label": "料理", "value": rest_data["cuisine_type"], "unit": ""})
        if rest_data.get("price_band"):
            stats.append({"label": "价格带", "value": rest_data["price_band"], "unit": ""})
        if rest_data.get("tabelog_score"):
            stats.append({"label": "Tabelog", "value": str(rest_data["tabelog_score"]), "unit": "分"})
        day_idx = rest_data.get("day_index")
        meal_type = rest_data.get("meal_type", "")
        if day_idx is not None:
            stats.append({"label": "安排", "value": f"Day {day_idx} {meal_type}", "unit": ""})

    if stats:
        sections.append(SectionVM(
            section_type="stat_strip",
            content=StatStripContent(stats=stats),
        ))

    booking_note = rest_data.get("booking_note", "") if rest_data else ""
    requires_booking = rest_data.get("requires_advance_booking", False) if rest_data else False
    if requires_booking:
        sections.append(SectionVM(
            section_type="risk_card",
            heading="预约提示",
            content=RiskCardContent(
                risk_type="reservation_needed",
                description=booking_note or "需要提前预约",
                severity="high",
            ),
        ))

    return PageViewModel(
        page_id=page.page_id,
        page_type="restaurant_detail",
        page_size=page.page_size,
        heading=HeadingVM(title=name, page_number=page_number),
        hero=hero,
        sections=sections,
        footer=FooterVM(page_number=page_number),
        chapter_id=page.chapter_id,
    )


def _find_entity_data(
    entity_id: str, entity_type: str, payload: ReportPayloadV2
) -> Optional[dict]:
    """从 conditional_sections 或 selection_evidence 中查找实体数据"""
    for sec in payload.conditional_sections:
        if sec.payload.get("entity_id") == entity_id:
            return sec.payload
    for ev in payload.selection_evidence:
        if ev.get("entity_id") == entity_id:
            return ev
    return None


def _build_skeleton_vm(
    page: PagePlan, payload: ReportPayloadV2, page_number: int
) -> PageViewModel:
    """骨架 VM：给尚未完整实现的页型返回带 heading 的空 VM"""
    from app.domains.rendering.page_type_registry import get_page_type
    try:
        defn = get_page_type(page.page_type)
        title = defn.primary_promise
    except KeyError:
        title = page.page_type

    return PageViewModel(
        page_id=page.page_id,
        page_type=page.page_type,
        page_size=page.page_size,
        heading=HeadingVM(title=title, page_number=page_number),
        sections=[],
        footer=FooterVM(page_number=page_number),
        day_index=page.day_index,
        chapter_id=page.chapter_id,
    )


# ── 补充 builder 函数 ─────────────────────────────────────────────────────────

def _build_major_activity_overview_vm(
    page: PagePlan, payload: ReportPayloadV2, page_number: int
) -> PageViewModel:
    """主要体验一览页 VM"""
    major_items = []
    for ev in payload.selection_evidence:
        if ev.get("entity_type") in ("poi", "activity") and ev.get("tier") in ("S", "A"):
            major_items.append({
                "name": ev.get("name", ""),
                "area": ev.get("area", ""),
                "tier": ev.get("tier", "A"),
                "why_selected": ev.get("why_selected", ""),
                "day_index": ev.get("day_index"),
                "entity_id": ev.get("entity_id"),
            })
    # 去重
    seen = set()
    deduped = []
    for item in major_items:
        if item["entity_id"] not in seen:
            seen.add(item["entity_id"])
            deduped.append(item)

    stats = [
        {"label": "主要体验", "value": str(len(deduped)), "unit": "处"},
        {"label": "S级景点", "value": str(sum(1 for i in deduped if i["tier"] == "S")), "unit": "处"},
        {"label": "A级景点", "value": str(sum(1 for i in deduped if i["tier"] == "A")), "unit": "处"},
    ]
    return PageViewModel(
        page_id=page.page_id,
        page_type="major_activity_overview",
        page_size=page.page_size,
        heading=HeadingVM(title="主要体验一览", subtitle="行程高光时刻", page_number=page_number),
        sections=[
            SectionVM(section_type="entity_card", heading="核心体验", content={"spots": deduped}),
            SectionVM(section_type="stat_strip", content=StatStripContent(stats=stats)),
        ],
        footer=FooterVM(page_number=page_number),
        chapter_id=page.chapter_id,
    )


def _build_route_overview_vm(
    page: PagePlan, payload: ReportPayloadV2, page_number: int
) -> PageViewModel:
    """路线总览页 VM — 按天构建时间线"""
    meta = payload.meta
    timeline_items = []
    for day in sorted(payload.days, key=lambda d: d.day_index):
        timeline_items.append(TimelineItemVM(
            time=f"Day {day.day_index}",
            name=day.title,
            type_icon="day",
            duration=day.intensity,
            note=day.primary_area,
        ))

    stats = [
        {"label": "总天数", "value": str(meta.total_days), "unit": "天"},
        {"label": "城市", "value": str(len({d.primary_area for d in payload.days if d.primary_area})), "unit": "座"},
    ]
    return PageViewModel(
        page_id=page.page_id,
        page_type="route_overview",
        page_size=page.page_size,
        heading=HeadingVM(title="路线总览", subtitle=f"{meta.destination} · {meta.total_days}天", page_number=page_number),
        sections=[
            SectionVM(section_type="timeline", heading="行程时间线", content=TimelineContent(items=timeline_items)),
            SectionVM(section_type="stat_strip", content=StatStripContent(stats=stats)),
        ],
        footer=FooterVM(page_number=page_number),
        chapter_id=page.chapter_id,
    )


def _build_hotel_strategy_vm(
    page: PagePlan, payload: ReportPayloadV2, page_number: int
) -> PageViewModel:
    """酒店策略页 VM"""
    hotels = [ev for ev in payload.selection_evidence if ev.get("entity_type") == "hotel"]
    seen = set()
    deduped_hotels = []
    for h in hotels:
        if h.get("entity_id") not in seen:
            seen.add(h.get("entity_id"))
            deduped_hotels.append(h)

    stats = [
        {"label": "住宿城市", "value": str(len({h.get("area", "") for h in deduped_hotels})), "unit": "座"},
        {"label": "换酒店次数", "value": str(max(0, len(deduped_hotels) - 1)), "unit": "次"},
    ]
    return PageViewModel(
        page_id=page.page_id,
        page_type="hotel_strategy",
        page_size=page.page_size,
        heading=HeadingVM(title="住宿策略", subtitle="为什么这样安排酒店", page_number=page_number),
        sections=[
            SectionVM(section_type="entity_card", heading="住宿安排", content={"spots": deduped_hotels}),
            SectionVM(section_type="stat_strip", content=StatStripContent(stats=stats)),
        ],
        footer=FooterVM(page_number=page_number),
        chapter_id=page.chapter_id,
    )


def _build_booking_window_vm(
    page: PagePlan, payload: ReportPayloadV2, page_number: int
) -> PageViewModel:
    """预订时间窗口页 VM"""
    booking_items = []
    for sec in payload.conditional_sections:
        if sec.section_type == "booking_alert":
            booking_items.append(sec.payload)

    mandatory = [b for b in booking_items if b.get("is_mandatory")]
    stats = [
        {"label": "必须预订", "value": str(len(mandatory)), "unit": "项"},
        {"label": "建议预订", "value": str(len(booking_items) - len(mandatory)), "unit": "项"},
        {"label": "最早提前", "value": str(max((b.get("days_before_required", 0) for b in booking_items), default=0)), "unit": "天"},
    ]
    return PageViewModel(
        page_id=page.page_id,
        page_type="booking_window",
        page_size=page.page_size,
        heading=HeadingVM(title="预订时间窗口", subtitle="这些必须提前安排", page_number=page_number),
        sections=[
            SectionVM(section_type="stat_strip", content=StatStripContent(stats=stats)),
            SectionVM(section_type="booking_timeline", heading="预订清单", content={"items": booking_items}),
        ],
        footer=FooterVM(page_number=page_number),
        chapter_id=page.chapter_id,
    )


def _build_departure_prep_vm(
    page: PagePlan, payload: ReportPayloadV2, page_number: int
) -> PageViewModel:
    """出行前注意事项页 VM"""
    meta = payload.meta
    risk_items = payload.risk_watch_items or []

    # 按类型分组为 check_group
    groups: dict[str, list] = {}
    DEFAULT_GROUPS = [
        ("booking", "📅", "预订事项"),
        ("visa", "🛂", "签证 / 通关"),
        ("packing", "🧳", "行李 / 打包"),
        ("payment", "💴", "支付 / 汇率"),
        ("health", "💊", "健康 / 药品"),
    ]
    group_map = {g[0]: {"group_title": g[2], "icon": g[1], "items": []} for g in DEFAULT_GROUPS}
    other_items = []

    for r in risk_items:
        check_item = {
            "id": r.entity_id or r.risk_type,
            "label": r.description,
            "urgency": "high" if r.risk_type in ("closed_day", "reservation_needed") else "medium",
            "detail": r.action_required or None,
        }
        if r.risk_type == "reservation_needed":
            group_map["booking"]["items"].append(check_item)
        else:
            other_items.append(check_item)

    if other_items:
        group_map["other"] = {"group_title": "其他注意事项", "icon": "📌", "items": other_items}

    urgent = sum(
        1 for r in risk_items
        if r.risk_type in ("closed_day", "reservation_needed")
    )
    sections = [
        SectionVM(section_type="prep_hero", content={
            "summary_text": f"共 {len(risk_items)} 项出行前确认事项",
            "urgent_count": urgent,
            "total_count": len(risk_items),
        })
    ]
    for grp in group_map.values():
        if grp["items"]:
            sections.append(SectionVM(section_type="check_group", content=grp))

    return PageViewModel(
        page_id=page.page_id,
        page_type="departure_prep",
        page_size=page.page_size,
        heading=HeadingVM(title="出行前注意事项", subtitle="出发前请逐一确认", page_number=page_number),
        sections=sections,
        footer=FooterVM(page_number=page_number),
        chapter_id=page.chapter_id,
    )


def _build_live_notice_vm(
    page: PagePlan, payload: ReportPayloadV2, page_number: int
) -> PageViewModel:
    """动态注意事项页 VM — 从 risk_watch_items 构建"""
    from datetime import datetime
    risk_items = payload.risk_watch_items or []

    critical = [r for r in risk_items if r.risk_type in ("closed_day",)]
    warning_  = [r for r in risk_items if r.risk_type in ("crowd_alert", "reservation_needed")]
    info_     = [r for r in risk_items if r.risk_type not in ("closed_day", "crowd_alert", "reservation_needed")]

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    summary = SectionVM(section_type="live_summary", content={
        "critical_count": len(critical),
        "warning_count":  len(warning_),
        "info_count":     len(info_),
        "generated_at":   generated_at,
        "is_fresh": True,
    })

    risk_cards = [
        SectionVM(
            section_type="risk_card",
            content=[{
                "risk_id":       r.entity_id or r.risk_type,
                "risk_type":     r.risk_type,
                "severity":      "critical" if r.risk_type == "closed_day" else "warning",
                "title":         r.description[:40],
                "description":   r.description,
                "action_required": r.action_required,
                "day_index":     r.day_index,
            } for r in risk_items]
        )
    ] if risk_items else []

    return PageViewModel(
        page_id=page.page_id,
        page_type="live_notice",
        page_size=page.page_size,
        heading=HeadingVM(title="动态注意事项", subtitle=f"基于 {generated_at} 数据生成", page_number=page_number),
        sections=[summary] + risk_cards,
        footer=FooterVM(page_number=page_number),
        chapter_id=page.chapter_id,
    )


def _build_chapter_opener_vm(
    page: PagePlan, payload: ReportPayloadV2, page_number: int
) -> PageViewModel:
    """章节开篇页 VM"""
    # 从 chapter_summaries 找对应章节
    ch_summary = next(
        (c for c in payload.chapter_summaries if c.chapter_id == page.chapter_id),
        None,
    )
    title    = ch_summary.title    if ch_summary else f"章节 {page.chapter_id}"
    subtitle = ch_summary.subtitle if ch_summary else None
    goal     = ch_summary.goal     if ch_summary else ""
    mood     = ch_summary.mood     if ch_summary else ""

    hero = _resolve_hero_image(None, "circle", "chapter_opener", payload)

    sections = []
    if goal:
        sections.append(SectionVM(section_type="text_block", heading="本章目标", content=TextBlockContent(text=goal)))
    if mood:
        sections.append(SectionVM(section_type="text_block", heading="旅行氛围", content=TextBlockContent(text=mood)))

    return PageViewModel(
        page_id=page.page_id,
        page_type="chapter_opener",
        page_size=page.page_size,
        heading=HeadingVM(title=title, subtitle=subtitle, page_number=page_number),
        hero=hero,
        sections=sections,
        footer=FooterVM(page_number=page_number),
        chapter_id=page.chapter_id,
    )


def _build_major_activity_detail_vm(
    page: PagePlan, payload: ReportPayloadV2, page_number: int
) -> PageViewModel:
    """主要活动详情页 VM"""
    entity_id = (page.object_refs[0].object_id if page.object_refs else "") or ""
    ev = _find_entity_data(entity_id, "poi", payload) or _find_entity_data(entity_id, "activity", payload)
    name = ev.get("name", "活动详情") if ev else "活动详情"
    hero = _resolve_hero_image(entity_id or None, "poi", "major_activity_detail", payload)

    sections = []
    if ev:
        why = ev.get("why_selected", "")
        if why:
            sections.append(SectionVM(
                section_type="key_reasons",
                heading="为什么值得去",
                content=KeyReasonsContent(reasons=[{"title": "核心理由", "body": why}]),
            ))
        stats = []
        if ev.get("area"):        stats.append({"label": "区域", "value": ev["area"], "unit": ""})
        if ev.get("duration_mins"): stats.append({"label": "建议时长", "value": str(ev["duration_mins"]), "unit": "分钟"})
        if ev.get("google_rating"): stats.append({"label": "评分", "value": str(ev["google_rating"]), "unit": "⭐"})
        if ev.get("tier"):          stats.append({"label": "等级", "value": ev["tier"], "unit": ""})
        if stats:
            sections.append(SectionVM(section_type="stat_strip", content=StatStripContent(stats=stats)))

    return PageViewModel(
        page_id=page.page_id,
        page_type="major_activity_detail",
        page_size=page.page_size,
        heading=HeadingVM(title=name, page_number=page_number),
        hero=hero,
        sections=sections,
        footer=FooterVM(page_number=page_number),
        chapter_id=page.chapter_id,
    )


def _build_photo_theme_detail_vm(
    page: PagePlan, payload: ReportPayloadV2, page_number: int
) -> PageViewModel:
    """拍摄主题详情页 VM"""
    entity_id = (page.object_refs[0].object_id if page.object_refs else "") or ""
    ev = _find_entity_data(entity_id, "photo_spot", payload)
    name = ev.get("name", "拍摄地点") if ev else "拍摄地点"
    hero = _resolve_hero_image(entity_id or None, "photo_spot", "photo_theme_detail", payload)

    tips = []
    if ev:
        if ev.get("best_time"):    tips.append({"icon": "🌅", "label": "最佳时间", "tip": ev["best_time"]})
        if ev.get("best_angle"):   tips.append({"icon": "📐", "label": "推荐机位", "tip": ev["best_angle"]})
        if ev.get("lens_suggest"): tips.append({"icon": "🔭", "label": "镜头建议", "tip": ev["lens_suggest"]})

    sections = []
    if tips:
        sections.append(SectionVM(section_type="photo_tips", content={"tips": tips}))

    return PageViewModel(
        page_id=page.page_id,
        page_type="photo_theme_detail",
        page_size=page.page_size,
        heading=HeadingVM(title=name, subtitle="出片攻略", page_number=page_number),
        hero=hero,
        sections=sections,
        footer=FooterVM(page_number=page_number),
        chapter_id=page.chapter_id,
    )


def _build_transit_detail_vm(
    page: PagePlan, payload: ReportPayloadV2, page_number: int
) -> PageViewModel:
    """交通详情页 VM"""
    day_index = page.day_index
    day_sec = next((d for d in payload.days if d.day_index == day_index), None)

    transit_steps = []
    if day_sec:
        for i, slot in enumerate(day_sec.slots):
            if slot.kind in ("transit", "train", "bus", "walk"):
                transit_steps.append({
                    "step": i + 1,
                    "time": slot.start_time_hint or "",
                    "mode": slot.kind,
                    "description": slot.title,
                    "notes": slot.area,
                    "duration_mins": slot.duration_mins,
                })

    sections = []
    if transit_steps:
        sections.append(SectionVM(
            section_type="transit_timeline",
            content={"steps": transit_steps, "total_duration_mins": sum(s.get("duration_mins", 0) or 0 for s in transit_steps)},
        ))

    return PageViewModel(
        page_id=page.page_id,
        page_type="transit_detail",
        page_size=page.page_size,
        heading=HeadingVM(
            title=f"Day {day_index} 交通指南" if day_index else "交通详情",
            page_number=page_number,
        ),
        sections=sections,
        footer=FooterVM(page_number=page_number),
        chapter_id=page.chapter_id,
    )


def _build_supplemental_spots_vm(
    page: PagePlan, payload: ReportPayloadV2, page_number: int
) -> PageViewModel:
    """补充景点页 VM"""
    skipped = payload.skipped_options or []
    spots = [
        {
            "name": s.name,
            "entity_type": s.entity_type,
            "why_worth_it": s.would_fit_if or s.why_skipped,
            "tags": [],
        }
        for s in skipped[:8]
    ]
    return PageViewModel(
        page_id=page.page_id,
        page_type="supplemental_spots",
        page_size=page.page_size,
        heading=HeadingVM(title="补充景点 & 备选", subtitle="更多选择", page_number=page_number),
        sections=[
            SectionVM(section_type="entity_card", content={"spots": spots}),
        ] if spots else [
            SectionVM(section_type="text_block", content=TextBlockContent(text="本行程已充分覆盖目的地精华，暂无补充推荐。")),
        ],
        footer=FooterVM(page_number=page_number),
        chapter_id=page.chapter_id,
    )


# ── 页型分发表 ────────────────────────────────────────────────────────────────

_BUILDERS = {
    "cover":                  _build_cover_vm,
    "preference_fulfillment": _build_preference_fulfillment_vm,
    "day_execution":          _build_day_execution_vm,
    "hotel_detail":           _build_hotel_detail_vm,
    "restaurant_detail":      _build_restaurant_detail_vm,
    # 补充 builder（L3 收尾）
    "major_activity_overview": _build_major_activity_overview_vm,
    "route_overview":          _build_route_overview_vm,
    "hotel_strategy":          _build_hotel_strategy_vm,
    "booking_window":          _build_booking_window_vm,
    "departure_prep":          _build_departure_prep_vm,
    "live_notice":             _build_live_notice_vm,
    "chapter_opener":          _build_chapter_opener_vm,
    "major_activity_detail":   _build_major_activity_detail_vm,
    "photo_theme_detail":      _build_photo_theme_detail_vm,
    "transit_detail":          _build_transit_detail_vm,
    "supplemental_spots":      _build_supplemental_spots_vm,
}


# ── 主函数（两遍构建，F1） ─────────────────────────────────────────────────────

def build_view_models(
    pages: list[PagePlan],
    payload: ReportPayloadV2,
) -> dict[str, PageViewModel]:
    """
    两遍构建：
    Pass 1：非 toc 页分配页码并构建 VM
    Pass 2：toc 页用 page_number_map 回填
    """
    result: dict[str, PageViewModel] = {}
    page_number_map: dict[str, int] = {}

    # ── Pass 1：非 toc 页 ────────────────────────────────────────────────
    current_page = 1
    toc_pages = []

    for page in sorted(pages, key=lambda p: p.page_order):
        page_number_map[page.page_id] = current_page
        # dual-half 占同一页，视为 0.5 页，但实际页码仍递增
        if page.page_size == "dual-half":
            # 每对 dual-half 共用一个页码（偶数时与前一页共用）
            pass
        current_page += 1

        if page.page_type == "toc":
            toc_pages.append(page)
            continue

        builder = _BUILDERS.get(page.page_type)
        if builder:
            try:
                vm = builder(page, payload, page_number_map[page.page_id])
                result[page.page_id] = vm
            except Exception as exc:
                logger.warning("[ViewModelBuilder] %s 构建失败: %s", page.page_id, exc)
                result[page.page_id] = _build_skeleton_vm(
                    page, payload, page_number_map[page.page_id]
                )
        else:
            result[page.page_id] = _build_skeleton_vm(
                page, payload, page_number_map[page.page_id]
            )

    # ── Pass 2：toc 页回填 ────────────────────────────────────────────────
    for toc_page in toc_pages:
        try:
            vm = _build_toc_vm(
                toc_page, payload,
                page_number_map.get(toc_page.page_id, 2),
                page_number_map,
                pages,
            )
            result[toc_page.page_id] = vm
        except Exception as exc:
            logger.warning("[ViewModelBuilder] toc 构建失败: %s", exc)
            result[toc_page.page_id] = _build_skeleton_vm(
                toc_page, payload, page_number_map.get(toc_page.page_id, 2)
            )

    return result
