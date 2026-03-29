"""
planning_output.py — 决策链直出的页面数据源

替代原先 report_generator → layer2_handoff 的中间层。
从 ItineraryPlan/Day/Item + day_frames + evidence 直接构建，
供 chapter_planner / page_planner / page_view_model 消费。

数据结构复用 report_schema 中的嵌套类型（纯数据容器，无业务逻辑）。
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from app.domains.planning.report_schema import (
    BookingAlertItem,
    ChapterSummary,
    ConditionalSection,
    DayRisk,
    DaySection,
    DaySlot,
    DesignBrief,
    EmotionalGoal,
    ExecutionNotes,
    HotelBaseInfo,
    OverviewSection,
    PreferenceFulfillmentItem,
    ProfileSummary,
    QualityFlags,
    ReportMeta,
    RiskWatchItem,
    RouteSummaryCard,
    SelectedCircleInfo,
    SkippedOption,
)

logger = logging.getLogger(__name__)


# ── PlanningOutput: 页面管线的唯一数据源 ────────────────────────────────────


@dataclass
class PlanningOutput:
    """
    页面管线的顶层数据容器。

    属性名与 ReportPayloadV2 保持一致，以最小化下游改动。
    构建方式完全不同：直接从 DB + pipeline 结果组装，无 AI / 无 report 中间层。
    """

    meta: ReportMeta
    profile_summary: ProfileSummary
    design_brief: DesignBrief
    overview: OverviewSection
    days: list[DaySection]

    booking_alerts: list[BookingAlertItem] = field(default_factory=list)
    prep_notes: dict = field(default_factory=dict)
    conditional_sections: list[ConditionalSection] = field(default_factory=list)
    preference_fulfillment: list[PreferenceFulfillmentItem] = field(default_factory=list)
    skipped_options: list[SkippedOption] = field(default_factory=list)
    chapter_summaries: list[ChapterSummary] = field(default_factory=list)
    emotional_goals: list[EmotionalGoal] = field(default_factory=list)
    risk_watch_items: list[RiskWatchItem] = field(default_factory=list)
    selection_evidence: list[dict] = field(default_factory=list)
    photo_themes: list[dict] = field(default_factory=list)
    supplemental_items: list[dict] = field(default_factory=list)
    circles: list[SelectedCircleInfo] = field(default_factory=list)
    day_circle_map: dict[int, str] = field(default_factory=dict)
    quality_flags: QualityFlags = field(default_factory=QualityFlags)


# ── 构建函数 ─────────────────────────────────────────────────────────────────


async def build_planning_output(
    session: Any,
    *,
    plan_id: uuid.UUID,
    trip_request_id: uuid.UUID,
    day_frames: list[dict],
    design_brief: dict,
    circle_id: str,
    profile: Any,
    ranking_result: Any | None = None,
    hotel_result: Any | None = None,
    evidence_bundle: dict | None = None,
) -> PlanningOutput:
    """
    从 DB + pipeline 结果直接构建 PlanningOutput，跳过 report_generator。

    Args:
        session: AsyncSession
        plan_id: 当前 plan UUID
        trip_request_id: trip request UUID
        day_frames: skeleton.frames 序列化后的 dict 列表
        design_brief: 设计简报 dict（generate_trip 中已构建）
        circle_id: 选中的城市圈 ID
        profile: TripProfile ORM 对象
        ranking_result: major_activity_ranker 的结果（可选，用于构建 evidence）
        hotel_result: hotel_base_builder 的结果（可选）
        evidence_bundle: constraint_compiler 的证据包（可选）
    """
    from sqlalchemy import select
    from app.db.models.derived import ItineraryPlan, ItineraryDay, ItineraryItem
    from app.db.models.catalog import EntityBase

    # ── 1. 加载 DB 数据 ──────────────────────────────────────────────────────

    plan = await session.get(ItineraryPlan, plan_id)

    days_q = await session.execute(
        select(ItineraryDay)
        .where(ItineraryDay.plan_id == plan_id)
        .order_by(ItineraryDay.day_number)
    )
    db_days = days_q.scalars().all()

    # 批量加载所有 items
    all_items: dict[Any, list] = {}
    for day in db_days:
        items_q = await session.execute(
            select(ItineraryItem)
            .where(ItineraryItem.day_id == day.day_id)
            .order_by(ItineraryItem.sort_order)
        )
        all_items[day.day_id] = items_q.scalars().all()

    # 批量加载 entities
    entity_ids = set()
    for items in all_items.values():
        for item in items:
            if item.entity_id:
                entity_ids.add(item.entity_id)

    entities: dict[Any, Any] = {}
    if entity_ids:
        ent_q = await session.execute(
            select(EntityBase).where(EntityBase.entity_id.in_(entity_ids))
        )
        for ent in ent_q.scalars().all():
            entities[ent.entity_id] = ent

    # ── 2. frame index → frame dict 映射 ────────────────────────────────────

    frame_map: dict[int, dict] = {}
    for f in day_frames:
        frame_map[f.get("day_index", 0)] = f

    # ── 3. 构建 DaySection 列表 ──────────────────────────────────────────────

    day_sections: list[DaySection] = []
    all_conditional: list[ConditionalSection] = []
    all_booking_alerts: list[BookingAlertItem] = []
    all_risk_watch: list[RiskWatchItem] = []
    evidence_items: list[dict] = []

    for day in db_days:
        frame = frame_map.get(day.day_number, {})
        items = all_items.get(day.day_id, [])

        # 构建 slots
        slots: list[DaySlot] = []
        for idx, item in enumerate(items):
            ent = entities.get(item.entity_id)
            kind = _slot_kind(item.item_type or (ent.entity_type if ent else "poi"))
            name = (ent.name_zh or ent.name_en or ent.name or "未知") if ent else "未知"
            area = (ent.area_name or "") if ent else ""

            # 解析 notes_zh 获取额外信息
            notes = _parse_notes(item.notes_zh)

            slots.append(DaySlot(
                slot_index=idx,
                kind=kind,
                entity_id=str(item.entity_id) if item.entity_id else None,
                title=name,
                area=area,
                start_time_hint=item.start_time or _time_hint(idx, frame.get("day_type", "normal")),
                duration_mins=item.duration_min or 60,
                booking_required=notes.get("booking_required", False),
                weather_dependency="low",
                replaceable=True,
            ))

            # D4: 从 entity schema (A3) 读取预约信息，生成 BookingAlertItem
            if ent:
                booking_method = getattr(ent, "booking_method", None)
                risk_flags = getattr(ent, "risk_flags", None) or []
                requires_advance = (
                    booking_method in ("online_advance", "phone")
                    or "requires_reservation" in risk_flags
                )
                if requires_advance:
                    # 读子表预约字段（pois / restaurants）
                    from app.db.models.catalog import Poi, Restaurant
                    sub = None
                    if ent.entity_type == "poi":
                        sub = await session.get(Poi, ent.entity_id)
                    elif ent.entity_type == "restaurant":
                        sub = await session.get(Restaurant, ent.entity_id)

                    advance_days = getattr(sub, "advance_booking_days", None) if sub else None
                    booking_url = getattr(sub, "booking_url", None) if sub else None
                    queue_wait = getattr(sub, "queue_wait_typical_min", None) if sub else None

                    deadline_hint = ""
                    if advance_days and advance_days > 0:
                        deadline_hint = f"建议出发前 {advance_days} 天预约"
                    elif advance_days == 0:
                        deadline_hint = "可当天预约"

                    # D4: 计算实际截止日期 deadline_date
                    deadline_date = _compute_deadline_date(
                        profile, day.day_number, advance_days,
                    )

                    booking_level = (
                        "must_book" if booking_method == "online_advance"
                        else "should_book"
                    )
                    all_booking_alerts.append(BookingAlertItem(
                        entity_id=str(ent.entity_id),
                        entity_name=name,
                        entity_type=ent.entity_type or "",
                        label=f"{name}{'（预约链接）' if booking_url else ''}",
                        booking_level=booking_level,
                        booking_method=booking_method,
                        booking_url=booking_url,
                        advance_booking_days=advance_days,
                        visit_day=day.day_number,
                        deadline_date=deadline_date,
                        queue_wait_min=queue_wait,
                        deadline_hint=deadline_hint,
                        impact_if_missed="可能无法入场或排队时间超长",
                        fallback_label=booking_url,
                    ))

            # 构建 conditional_section（detail 页数据源）
            if ent and kind in ("poi", "activity"):
                all_conditional.append(ConditionalSection(
                    section_type="extra",
                    trigger_reason=f"Day {day.day_number} {kind}",
                    related_day_indexes=[day.day_number],
                    payload={
                        "entity_id": str(item.entity_id),
                        "name": name,
                        "entity_type": ent.entity_type,
                        "day_index": day.day_number,
                        "data_tier": getattr(ent, "data_tier", "A") or "A",
                        "area": area,
                        # D4: 预约信息透传给 detail 页渲染
                        "booking_method": getattr(ent, "booking_method", None),
                        "risk_flags": getattr(ent, "risk_flags", None) or [],
                    },
                ))
            elif ent and kind == "restaurant":
                meal_style = notes.get("meal_style", "route_meal")
                role = notes.get("role", "")
                all_conditional.append(ConditionalSection(
                    section_type="restaurant",
                    trigger_reason=f"Day {day.day_number} restaurant",
                    related_day_indexes=[day.day_number],
                    payload={
                        "entity_id": str(item.entity_id),
                        "name": name,
                        "day_index": day.day_number,
                        "meal_style": meal_style,
                        "role": role,
                    },
                ))

            # 构建 selection_evidence（E2: 自动查找本地成品图）
            if ent:
                hero_url = None
                try:
                    from app.domains.rendering.asset_loader import find_asset_url
                    cat = "food" if ent.entity_type == "restaurant" else (
                        "hotels" if ent.entity_type == "hotel" else "spots"
                    )
                    hero_url = find_asset_url(circle_id, name, category=cat)
                except Exception as _asset_err:
                    logger.warning("图片资源查找失败 entity=%s: %s", name, _asset_err)
                evidence_items.append({
                    "entity_id": str(item.entity_id),
                    "name": name,
                    "entity_type": ent.entity_type,
                    "area": area,
                    "hero_image_url": hero_url,
                    "orientation": "landscape",
                    "why_selected": notes.get("copy_zh", ""),
                })

        # 构建 risks
        risks: list[DayRisk] = []
        for alert in frame.get("booking_alerts", []):
            risks.append(DayRisk(
                risk_type=alert.get("type", "booking"),
                description=alert.get("message", ""),
                mitigation=alert.get("fallback", ""),
            ))

        # 构建 trigger_tags
        trigger_tags: list[str] = []
        if frame.get("day_type") == "arrival":
            trigger_tags.append("arrival")
        if frame.get("day_type") == "departure":
            trigger_tags.append("departure")
        if any(s.kind == "transit" for s in slots):
            trigger_tags.append("transfer")

        intensity = _normalize_intensity(frame.get("intensity", "balanced"))
        primary_area = frame.get("primary_corridor", day.city_code or "")

        # D3: 生成 Plan B 备用方案
        plan_b_dicts: list[dict] = []
        try:
            from app.domains.planning.plan_b_builder import build_plan_b_for_day
            budget_level = getattr(profile, "budget_level", "mid") or "mid"
            plan_b_dicts = await build_plan_b_for_day(
                session, slots, frame.get("primary_corridor") or day.city_code or "", budget_level
            )
        except Exception as _pb_err:
            logger.warning("Plan B 生成失败 day=%s: %s", day.day_number, _pb_err)

        from app.domains.planning.report_schema import PlanBOption
        plan_b = [
            PlanBOption(
                trigger=pb.get("trigger", ""),
                alternative=pb.get("alternative", ""),
                entity_ids=pb.get("entity_ids", []),
            )
            for pb in plan_b_dicts
        ]

        day_sections.append(DaySection(
            day_index=day.day_number,
            title=frame.get("title_hint", "") or day.day_theme or f"Day {day.day_number}",
            primary_area=primary_area,
            secondary_area=frame.get("secondary_corridor"),
            day_goal="",  # AI 文案后填
            intensity=intensity,
            start_anchor=slots[0].title if slots else "",
            end_anchor=slots[-1].title if slots else "",
            must_keep=frame.get("must_keep_ids", [""])[0] if frame.get("must_keep_ids") else "",
            first_cut=frame.get("cut_order", [""])[0] if frame.get("cut_order") else "",
            route_integrity_score=1.0,
            risks=risks,
            slots=slots,
            reasoning=[],
            highlights=[],
            execution_notes=ExecutionNotes(),
            plan_b=plan_b,
            trigger_tags=trigger_tags,
        ))

        # booking alerts → 顶层
        for alert in frame.get("booking_alerts", []):
            all_booking_alerts.append(BookingAlertItem(
                label=alert.get("message", ""),
                booking_level=alert.get("level", "good_to_book"),
                deadline_hint=alert.get("deadline", ""),
                impact_if_missed=alert.get("impact", ""),
            ))

        # risks → risk_watch_items
        for r in risks:
            all_risk_watch.append(RiskWatchItem(
                risk_type=r.risk_type,
                description=r.description,
                day_index=day.day_number,
            ))

    # ── 4. 构建 hotel conditional_sections ───────────────────────────────────

    hotel_base_info = None
    if hotel_result:
        bases = []
        for base in getattr(hotel_result, "bases", []):
            base_dict = {
                "city": getattr(base, "city", ""),
                "area": getattr(base, "area", ""),
                "nights": getattr(base, "nights", 1),
                "check_in_day": getattr(base, "check_in_day", None),
                "check_out_day": getattr(base, "check_out_day", None),
                "entity_id": str(getattr(base, "hotel_entity_id", "")) if getattr(base, "hotel_entity_id", None) else "",
            }
            bases.append(base_dict)

            if base_dict.get("entity_id"):
                all_conditional.append(ConditionalSection(
                    section_type="hotel",
                    trigger_reason=f"Hotel base {base_dict['area']}",
                    related_day_indexes=[base_dict.get("check_in_day", 1)],
                    payload=base_dict,
                ))

        hotel_base_info = HotelBaseInfo(
            strategy_name=getattr(hotel_result, "preset_name", "") or "",
            bases=bases,
            switch_count=getattr(hotel_result, "switch_count", 0),
            last_night_airport_minutes=getattr(hotel_result, "last_night_airport_minutes", None),
        )

    # ── 5. 构建 meta ────────────────────────────────────────────────────────

    destination = ""
    try:
        from app.db.models.city_circles import CityCircle
        circle = await session.get(CityCircle, circle_id)
        if circle:
            destination = circle.name_zh or circle_id
    except Exception:
        destination = circle_id

    meta = ReportMeta(
        trip_id=str(trip_request_id),
        destination=destination,
        total_days=len(db_days) or len(day_frames),
        language="zh-CN",
        render_mode="web",
        circle=SelectedCircleInfo(
            circle_id=circle_id,
            name_zh=destination,
        ) if circle_id else None,
    )

    # ── 6. 构建 profile_summary ──────────────────────────────────────────────

    profile_summary = ProfileSummary(
        party_type=getattr(profile, "party_type", "couple") or "couple",
        pace_preference=_normalize_intensity(getattr(profile, "pace", "moderate") or "moderate"),
        budget_bias=getattr(profile, "budget_level", "mid") or "mid",
        trip_goals=(getattr(profile, "must_have_tags", None) or [])
                   + (getattr(profile, "nice_to_have_tags", None) or []),
        hard_constraints=[],
        avoid_list=getattr(profile, "avoid_tags", None) or [],
        hotel_constraints=[],
    )

    # ── 7. 构建 design_brief ────────────────────────────────────────────────

    brief = DesignBrief(
        route_strategy=design_brief.get("route_strategy", []),
        tradeoffs=design_brief.get("tradeoffs", []),
        stay_strategy=design_brief.get("stay_strategy", []),
        budget_strategy=design_brief.get("budget_strategy", []),
        execution_principles=design_brief.get("execution_principles", []),
        hotel_base=hotel_base_info,
    )

    # ── 8. 构建 overview ────────────────────────────────────────────────────

    route_summary = [
        RouteSummaryCard(
            day_index=d.day_index,
            title=d.title,
            primary_area=d.primary_area,
            intensity=d.intensity,
        )
        for d in day_sections
    ]
    overview = OverviewSection(route_summary=route_summary)

    # ── 9. 构建 preference_fulfillment / skipped / emotional_goals ──────────

    preference_fulfillment = _build_preference_fulfillment(
        profile_summary.trip_goals,
        evidence_bundle.get("constraint_trace", []) if evidence_bundle else [],
    )

    skipped_options: list[SkippedOption] = []
    if ranking_result:
        for r in getattr(ranking_result, "all_ranked", []):
            if not getattr(r, "selected", False):
                skipped_options.append(SkippedOption(
                    name=getattr(r, "name_zh", "") or getattr(r, "cluster_id", ""),
                    entity_type="poi",
                    why_skipped=getattr(r, "selection_reason", "") or "capacity",
                    would_fit_if=None,
                ))

    emotional_goals = _build_emotional_goals(day_frames)

    # ── 10. prep_notes（静态） ───────────────────────────────────────────────

    prep_notes: dict = {"title": "出发准备", "items": [
        "确认护照/签证有效期",
        "确认机票/车票已预订",
        "必订餐厅/景点提前预约",
        "下载离线地图",
        "准备当地交通卡",
        "确认酒店入住信息",
    ]}

    # D1: 优先使用城市圈知识包（关西等有详细知识包时覆盖通用占位）
    try:
        from app.domains.planning.circle_knowledge import get_circle_knowledge
        knowledge = get_circle_knowledge(circle_id)
        if knowledge:
            sections = knowledge.get("sections", {})
            # 遍历所有知识 section，合并 items + tips 为 flat list（兼容旧渲染）
            _ALL_SECTION_KEYS = (
                "airport_transport", "ic_card", "communication",
                "luggage", "payment", "useful_apps", "emergency", "seasonal_tips",
            )
            combined_items: list[str] = []
            knowledge_sections: list[dict] = []
            for section_key in _ALL_SECTION_KEYS:
                sec = sections.get(section_key, {})
                if not sec:
                    continue
                title = sec.get("title", section_key)
                items = sec.get("items", [])
                tips = sec.get("tips", [])
                # flat list：section header + items + tips
                combined_items.append(f"【{title}】")
                combined_items.extend(items)
                if tips:
                    combined_items.extend(tips)
                # structured sections：供 view model 按 section 渲染
                knowledge_sections.append({
                    "key": section_key,
                    "title": title,
                    "items": items,
                    "tips": tips,
                })
            dest_name = destination or circle_id or "出行"
            if combined_items:
                prep_notes = {
                    "title": f"{dest_name}出行准备",
                    "items": combined_items,
                    "knowledge": knowledge,
                    "knowledge_sections": knowledge_sections,
                }
    except Exception:
        # fallback：尝试旧的 circle_content
        try:
            from app.domains.planning.circle_content.loader import load_circle_content
            cc = load_circle_content(circle_id)
            if cc and hasattr(cc, "static_prep") and cc.static_prep:
                prep_notes = cc.static_prep
        except Exception:
            pass

    # ── 11. circles + day_circle_map ─────────────────────────────────────────

    circles_list = [SelectedCircleInfo(circle_id=circle_id, name_zh=destination)]
    day_circle_map = {d.day_index: circle_id for d in day_sections}

    # ── 组装 ─────────────────────────────────────────────────────────────────

    output = PlanningOutput(
        meta=meta,
        profile_summary=profile_summary,
        design_brief=brief,
        overview=overview,
        days=day_sections,
        booking_alerts=all_booking_alerts,
        prep_notes=prep_notes,
        conditional_sections=all_conditional,
        preference_fulfillment=preference_fulfillment,
        skipped_options=skipped_options[:8],
        chapter_summaries=[],
        emotional_goals=emotional_goals,
        risk_watch_items=all_risk_watch,
        selection_evidence=evidence_items,
        circles=circles_list,
        day_circle_map=day_circle_map,
    )

    logger.info(
        "[PlanningOutput] built: days=%d slots=%d conditionals=%d evidence=%d",
        len(day_sections),
        sum(len(d.slots) for d in day_sections),
        len(all_conditional),
        len(evidence_items),
    )

    return output


# ── 纯规则辅助函数（从 report_generator 迁移） ──────────────────────────────


_INTENSITY_MAP = {
    "light": "light", "relaxed": "light",
    "balanced": "balanced", "moderate": "balanced",
    "dense": "dense", "packed": "dense",
}


def _normalize_intensity(value: str) -> str:
    return _INTENSITY_MAP.get(value, "balanced")


def _slot_kind(raw_type: str) -> str:
    mapping = {
        "restaurant": "restaurant",
        "hotel": "hotel",
        "transit": "transit",
        "transportation": "transit",
        "activity": "activity",
    }
    return mapping.get(raw_type, "poi")


def _time_hint(slot_index: int, day_type: str) -> str:
    if day_type == "arrival":
        times = ["14:00", "15:30", "17:00", "18:30", "20:00"]
    elif day_type == "departure":
        times = ["08:00", "09:30", "11:00"]
    else:
        times = ["09:00", "10:30", "12:00", "13:30", "15:00", "16:30", "18:00", "19:30"]
    return times[min(slot_index, len(times) - 1)]


def _parse_notes(notes_zh: Any) -> dict:
    if not notes_zh:
        return {}
    import json
    try:
        if isinstance(notes_zh, str):
            return json.loads(notes_zh)
        if isinstance(notes_zh, dict):
            return notes_zh
    except (json.JSONDecodeError, TypeError):
        pass
    return {}


def _compute_deadline_date(
    profile: Any,
    visit_day_number: int,
    advance_booking_days: int | None,
) -> str | None:
    """
    D4: 用 departure_date + visit_day + advance_booking_days 计算
    实际截止预约日期 (YYYY-MM-DD)。

    departure_date 来自 profile.travel_dates.start；
    visit_day_number 是行程的第几天（1-based）；
    advance_booking_days 是建议提前天数。

    返回 None 当信息不足时。
    """
    if advance_booking_days is None or advance_booking_days < 0:
        return None
    from datetime import datetime as _dt, timedelta as _td
    travel_dates = getattr(profile, "travel_dates", None) or {}
    if isinstance(travel_dates, dict):
        start_str = travel_dates.get("start", "")
    else:
        start_str = ""
    if not start_str:
        return None
    try:
        trip_start = _dt.strptime(str(start_str), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None
    # visit_date = trip_start + (visit_day_number - 1)
    visit_date = trip_start + _td(days=visit_day_number - 1)
    deadline = visit_date - _td(days=advance_booking_days)
    return deadline.isoformat()


_MOOD_MAP = {
    "arrival": ("期待", "旅程开始，放松享受第一天的节奏"),
    "departure": ("收获", "带着满满的回忆准备回程"),
    "normal": ("探索", "深度体验当地的魅力"),
}

_INTENSITY_MOOD = {
    "light": ("放松", "轻松的一天，不赶时间"),
    "balanced": ("探索", "节奏刚好的一天"),
    "dense": ("充实", "内容满满，精力充沛的一天"),
}


def _build_emotional_goals(day_frames: list[dict]) -> list[EmotionalGoal]:
    goals: list[EmotionalGoal] = []
    for f in day_frames:
        day_type = f.get("day_type", "normal")
        intensity = _normalize_intensity(f.get("intensity", "balanced"))

        if day_type in ("arrival", "departure"):
            keyword, sentence = _MOOD_MAP[day_type]
        else:
            keyword, sentence = _INTENSITY_MOOD.get(intensity, ("探索", ""))

        goals.append(EmotionalGoal(
            day_index=f.get("day_index", 0),
            mood_keyword=keyword,
            mood_sentence=sentence,
        ))
    return goals


def _build_preference_fulfillment(
    trip_goals: list[str],
    constraint_trace: list[dict],
) -> list[PreferenceFulfillmentItem]:
    items: list[PreferenceFulfillmentItem] = []
    consumed_names = {
        t.get("constraint_name", "")
        for t in constraint_trace
        if t.get("final_status") == "consumed"
    }

    for goal in trip_goals:
        if goal in consumed_names:
            items.append(PreferenceFulfillmentItem(
                preference_text=goal,
                fulfillment_type="fully_met",
                evidence=f"约束 '{goal}' 已在规划中被消费",
                explanation="",
            ))
        else:
            items.append(PreferenceFulfillmentItem(
                preference_text=goal,
                fulfillment_type="partially_met",
                evidence=f"偏好 '{goal}' 已纳入考虑",
                explanation="",
            ))
    return items
