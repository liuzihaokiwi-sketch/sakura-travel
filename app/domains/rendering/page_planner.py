"""
page_planner.py — 页面规划器（L3-04）

输入：list[ChapterPlan] + ReportPayloadV2
输出：list[PagePlan]（持久化到 plan_metadata.page_plan）

生成规则（report/01 §6 §8）：
  固定前置页 → 章节主体（chapter_opener + day_execution + detail 页）→ 附录

条件页规则（F2）：booking_window / live_notice 等条件触发，数据不足直接跳过。
餐厅合并规则（F5）：主要餐厅 full，次要餐厅 dual-half 两两配对。
页数预算（F9）：超预算时按优先级裁剪。
持久化（F8）：plan_pages_and_persist() 将 page_plan 写入 plan_metadata。

依赖：
  chapter_planner.ChapterPlan
  page_type_registry.PAGE_TYPE_REGISTRY
  app.domains.planning.report_schema.ReportPayloadV2
  app.db.models.derived.ItineraryPlan（持久化用）
"""
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Optional

from app.domains.planning.report_schema import ReportPayloadV2
from app.domains.rendering.chapter_planner import ChapterPlan
from app.domains.rendering.page_type_registry import PAGE_TYPE_REGISTRY, get_page_type

logger = logging.getLogger(__name__)


# ── 页数预算 ──────────────────────────────────────────────────────────────────

MAX_PAGES_BY_DURATION: dict[tuple[int, int], int] = {
    (1, 3):  25,
    (4, 5):  35,
    (6, 8):  50,
    (9, 14): 70,
}


def _max_pages(total_days: int) -> int:
    for (lo, hi), cap in MAX_PAGES_BY_DURATION.items():
        if lo <= total_days <= hi:
            return cap
    return 70  # fallback


# ── 数据类 ────────────────────────────────────────────────────────────────────

@dataclass
class PageObjectRef:
    object_type: str        # "entity" / "cluster" / "day" / "chapter" / "trip"
    object_id: str
    role: str = ""          # "primary" / "secondary"


@dataclass
class PagePlan:
    page_id: str
    page_order: int
    chapter_id: str
    page_type: str
    page_size: str          # "full" / "half" / "dual-half"
    topic_family: str
    object_refs: list[PageObjectRef] = field(default_factory=list)
    required_slots: list[str] = field(default_factory=list)
    optional_slots: list[str] = field(default_factory=list)
    trigger_reason: Optional[str] = None
    merge_policy: Optional[str] = None
    overflow_policy: Optional[str] = None
    priority: int = 50
    day_index: Optional[int] = None


# ── 条件页触发规则（F2） ──────────────────────────────────────────────────────

def _has_booking_items(payload: ReportPayloadV2) -> bool:
    for d in payload.days:
        for slot in d.slots:
            if slot.booking_required:
                return True
    return len(payload.risk_watch_items) > 0


def _has_live_notice(payload: ReportPayloadV2) -> bool:
    return any(
        r.risk_type in ("weather", "seasonal")
        for r in payload.risk_watch_items
    )


def _has_photo_themes(payload: ReportPayloadV2) -> bool:
    return bool(getattr(payload, "photo_themes", None))


def _has_transfer_day(payload: ReportPayloadV2) -> bool:
    return any(
        getattr(d, "trigger_tags", []) and "transfer" in d.trigger_tags
        for d in payload.days
    )


def _has_supplemental(payload: ReportPayloadV2) -> bool:
    return bool(getattr(payload, "supplemental_items", None))


CONDITIONAL_PAGES: dict[str, bool | Callable[[ReportPayloadV2], bool]] = {
    "preference_fulfillment": lambda p: len(p.preference_fulfillment) > 0,
    "booking_window":         _has_booking_items,
    "departure_prep":         True,          # 始终生成
    "live_notice":            _has_live_notice,
    "photo_theme_detail":     _has_photo_themes,
    "transit_detail":         _has_transfer_day,
    "supplemental_spots":     _has_supplemental,
}


def _should_include(page_type: str, payload: ReportPayloadV2) -> bool:
    rule = CONDITIONAL_PAGES.get(page_type, True)
    if rule is True:
        return True
    if callable(rule):
        return rule(payload)
    return bool(rule)


# ── 餐厅分类（F5） ────────────────────────────────────────────────────────────

def _is_primary_restaurant(cond_section: dict) -> bool:
    """
    主要餐厅：meal_style = destination_meal 或 role = anchor
    次要餐厅：meal_style = route_meal / quick
    """
    meal_style = cond_section.get("meal_style", "")
    role = cond_section.get("role", "")
    return meal_style == "destination_meal" or role == "anchor"


# ── 辅助函数 ──────────────────────────────────────────────────────────────────

def _page_id(prefix: str, suffix: Any = "") -> str:
    return f"page_{prefix}_{suffix}".rstrip("_")


def _make_page(
    page_type: str,
    chapter_id: str,
    order: int,
    day_index: Optional[int] = None,
    object_refs: Optional[list[PageObjectRef]] = None,
    trigger_reason: Optional[str] = None,
    page_size: Optional[str] = None,
    merge_policy: Optional[str] = None,
    priority: int = 50,
    suffix: Any = "",
) -> PagePlan:
    defn = get_page_type(page_type)
    size = page_size or defn.default_size
    return PagePlan(
        page_id=_page_id(page_type, suffix),
        page_order=order,
        chapter_id=chapter_id,
        page_type=page_type,
        page_size=size,
        topic_family=defn.topic_family,
        object_refs=object_refs or [],
        required_slots=list(defn.required_slots),
        optional_slots=list(defn.optional_slots),
        trigger_reason=trigger_reason,
        merge_policy=merge_policy,
        day_index=day_index,
        priority=priority,
    )


# ── 核心规划函数 ──────────────────────────────────────────────────────────────

def plan_pages(
    chapters: list[ChapterPlan],
    payload: ReportPayloadV2,
) -> list[PagePlan]:
    """
    根据章节计划和 payload 生成有序 PagePlan 列表。

    分三阶段：
    1. 固定前置页
    2. 各章节主体页
    3. 附录页

    自动重排 page_order（跳过条件不满足的页后连续编号）。
    超预算时按优先级裁剪。
    """
    total_days = payload.meta.total_days
    pages: list[PagePlan] = []
    order = 0

    def next_order() -> int:
        nonlocal order
        order += 1
        return order

    # ── Phase A: 固定前置页（来自 ch_frontmatter） ────────────────────────
    fm_chapter = next((c for c in chapters if c.chapter_type == "frontmatter"), None)
    fm_id = fm_chapter.chapter_id if fm_chapter else "ch_frontmatter"

    # 1. 封面
    pages.append(_make_page("cover", fm_id, next_order(),
                             trigger_reason="固定前置", priority=100,
                             object_refs=[PageObjectRef("trip", payload.meta.trip_id, "primary")]))
    # 2. 目录
    pages.append(_make_page("toc", fm_id, next_order(),
                             trigger_reason="固定前置", priority=100))
    # 3. 偏好兑现（条件）
    if _should_include("preference_fulfillment", payload):
        pages.append(_make_page("preference_fulfillment", fm_id, next_order(),
                                 trigger_reason="payload.preference_fulfillment 非空", priority=90))
    # 4. 主要活动总表
    pages.append(_make_page("major_activity_overview", fm_id, next_order(),
                             trigger_reason="固定前置", priority=95))
    # 5. 大路线总览
    pages.append(_make_page("route_overview", fm_id, next_order(),
                             trigger_reason="固定前置", priority=95))
    # 6. 酒店策略
    pages.append(_make_page("hotel_strategy", fm_id, next_order(),
                             trigger_reason="固定前置", priority=90))
    # 7. 预约时间窗（条件）
    if _should_include("booking_window", payload):
        pages.append(_make_page("booking_window", fm_id, next_order(),
                                 trigger_reason="有必订项目或风险提醒", priority=85))
    # 8. 出发准备（始终）
    pages.append(_make_page("departure_prep", fm_id, next_order(),
                             trigger_reason="固定静态块", priority=80))
    # 9. 实时注意（条件）
    if _should_include("live_notice", payload):
        pages.append(_make_page("live_notice", fm_id, next_order(),
                                 trigger_reason="有天气/季节风险", priority=75))

    # ── Phase B: 各非 frontmatter / 非 appendix 章节 ─────────────────────
    body_chapters = [c for c in chapters
                     if c.chapter_type not in ("frontmatter", "appendix")]

    # 根据行程长度决定展开策略
    if total_days <= 5:
        expand_mode = "full"           # 3-5 天：展开型
    elif total_days <= 8:
        expand_mode = "balanced"       # 6-8 天：平衡型
    else:
        expand_mode = "chapter"        # 9-14 天：章节型

    # 用于追踪已分配 detail 页的 entity，防止重复（PAGE_004）
    assigned_detail_entity_ids: set[str] = set()

    for chapter in body_chapters:
        ch_id = chapter.chapter_id

        # 10. chapter_opener（仅 circle 类型章节）
        if chapter.chapter_type == "circle":
            pages.append(_make_page(
                "chapter_opener", ch_id, next_order(),
                trigger_reason=f"城市圈章节 {chapter.primary_circle_id}",
                priority=95,
                object_refs=[PageObjectRef("chapter", ch_id, "primary")],
                suffix=chapter.primary_circle_id or ch_id,
            ))

        # 11. 每天执行页
        day_map = {d.day_index: d for d in payload.days}
        for day_idx in sorted(chapter.covered_days):
            day_sec = day_map.get(day_idx)
            if not day_sec:
                continue
            pages.append(_make_page(
                "day_execution", ch_id, next_order(),
                day_index=day_idx,
                trigger_reason=f"Day {day_idx} 执行页",
                priority=100,
                object_refs=[PageObjectRef("day", str(day_idx), "primary")],
                suffix=day_idx,
            ))

        # 12. 主要活动 detail（S/A 级，每个 1 页）
        _add_major_activity_detail_pages(
            pages, payload, chapter, next_order,
            assigned_detail_entity_ids, expand_mode
        )

        # 13. 酒店 detail
        _add_hotel_detail_pages(
            pages, payload, chapter, next_order, assigned_detail_entity_ids
        )

        # 14. 餐厅 detail（F5 合并规则）
        _add_restaurant_detail_pages(
            pages, payload, chapter, next_order,
            assigned_detail_entity_ids, expand_mode
        )

        # 15. 拍摄主题（条件）
        if _should_include("photo_theme_detail", payload) and expand_mode != "chapter":
            pages.append(_make_page(
                "photo_theme_detail", ch_id, next_order(),
                trigger_reason="有拍摄主题数据", priority=40,
                suffix=ch_id,
            ))

        # 16. 交通详情（条件，仅复杂交通日）
        if _should_include("transit_detail", payload):
            for day_idx in sorted(chapter.covered_days):
                day_sec = day_map.get(day_idx)
                if day_sec and "transfer" in (day_sec.trigger_tags or []):
                    pages.append(_make_page(
                        "transit_detail", ch_id, next_order(),
                        day_index=day_idx,
                        trigger_reason=f"Day {day_idx} 含交通换乘",
                        priority=50,
                        suffix=day_idx,
                    ))

        # 17. 补充景点（条件，仅 full/balanced 模式）
        if _should_include("supplemental_spots", payload) and expand_mode == "full":
            pages.append(_make_page(
                "supplemental_spots", ch_id, next_order(),
                trigger_reason="有补充景点数据", priority=30,
                suffix=ch_id,
            ))

    # ── Phase C: 附录 ─────────────────────────────────────────────────────
    ap_chapter = next((c for c in chapters if c.chapter_type == "appendix"), None)
    ap_id = ap_chapter.chapter_id if ap_chapter else "ch_appendix"

    if _should_include("supplemental_spots", payload) and expand_mode == "chapter":
        pages.append(_make_page(
            "supplemental_spots", ap_id, next_order(),
            trigger_reason="章节型行程补充景点统一放附录", priority=30,
        ))

    # ── 页数预算裁剪（F9） ─────────────────────────────────────────────────
    pages = _trim_to_budget(pages, total_days)

    # ── 重新连续编号 ──────────────────────────────────────────────────────
    for i, p in enumerate(pages, start=1):
        p.page_order = i

    return pages


# ── Detail 页生成辅助 ─────────────────────────────────────────────────────────

def _add_major_activity_detail_pages(
    pages: list[PagePlan],
    payload: ReportPayloadV2,
    chapter: ChapterPlan,
    next_order_fn: Callable,
    assigned: set[str],
    expand_mode: str,
) -> None:
    """从 conditional_sections 找 type=poi 的 S/A 级活动，每个 1 页"""
    for sec in payload.conditional_sections:
        if sec.section_type not in ("hotel", "restaurant", "extra"):
            entity_id = sec.payload.get("entity_id", "")
            tier = sec.payload.get("data_tier", "")
            day_idx = sec.payload.get("day_index")

            # 只处理本章节的天
            if day_idx not in chapter.covered_days:
                continue
            if tier not in ("S", "A") and expand_mode == "chapter":
                continue
            if entity_id and entity_id in assigned:
                continue

            if entity_id:
                assigned.add(entity_id)
            name_slug = (sec.payload.get("name", entity_id) or entity_id).replace(" ", "_")[:20]
            pages.append(_make_page(
                "major_activity_detail",
                chapter.chapter_id,
                next_order_fn(),
                day_index=day_idx,
                trigger_reason=f"S/A 级活动 {name_slug}",
                priority=80,
                object_refs=[PageObjectRef("entity", entity_id, "primary")] if entity_id else [],
                suffix=entity_id or name_slug,
            ))


def _add_hotel_detail_pages(
    pages: list[PagePlan],
    payload: ReportPayloadV2,
    chapter: ChapterPlan,
    next_order_fn: Callable,
    assigned: set[str],
) -> None:
    """从 design_brief.hotel_base.bases 找本章节的主酒店，每个 1 页"""
    hotel_base = getattr(payload.design_brief, "hotel_base", None)
    if not hotel_base:
        return

    for base in hotel_base.bases:
        entity_id = base.get("entity_id", "")
        check_in = base.get("check_in_day")
        check_out = base.get("check_out_day")

        # 检查是否属于本章节
        if check_in not in chapter.covered_days and check_out not in chapter.covered_days:
            if not any(
                (check_in or 0) <= d <= (check_out or 0) and d in chapter.covered_days
                for d in chapter.covered_days
            ):
                continue

        if entity_id and entity_id in assigned:
            continue
        if entity_id:
            assigned.add(entity_id)

        name_slug = (base.get("area", entity_id) or entity_id).replace(" ", "_")[:20]
        pages.append(_make_page(
            "hotel_detail",
            chapter.chapter_id,
            next_order_fn(),
            trigger_reason=f"主酒店 {name_slug}",
            priority=85,
            object_refs=[PageObjectRef("entity", entity_id, "primary")] if entity_id else [],
            suffix=entity_id or name_slug,
        ))


def _add_restaurant_detail_pages(
    pages: list[PagePlan],
    payload: ReportPayloadV2,
    chapter: ChapterPlan,
    next_order_fn: Callable,
    assigned: set[str],
    expand_mode: str,
) -> None:
    """
    餐厅 detail 页（F5 合并规则）：
    - 主要餐厅 → full
    - 次要餐厅 → dual-half 两两配对
    - 奇数个次要餐厅最后一个 → half，与 supplemental_spots 合并
    """
    primary_rests = []
    secondary_rests = []

    for sec in payload.conditional_sections:
        if sec.section_type != "restaurant":
            continue
        day_idx = sec.payload.get("day_index")
        if day_idx not in chapter.covered_days:
            continue
        entity_id = sec.payload.get("entity_id", "")
        if entity_id and entity_id in assigned:
            continue

        if _is_primary_restaurant(sec.payload):
            primary_rests.append((entity_id, sec))
        else:
            secondary_rests.append((entity_id, sec))

    # 主要餐厅：full 页
    for entity_id, sec in primary_rests:
        if entity_id:
            assigned.add(entity_id)
        name_slug = (sec.payload.get("name", entity_id) or entity_id).replace(" ", "_")[:20]
        pages.append(_make_page(
            "restaurant_detail",
            chapter.chapter_id,
            next_order_fn(),
            day_index=sec.payload.get("day_index"),
            trigger_reason=f"目标餐厅 {name_slug}",
            priority=75,
            page_size="full",
            object_refs=[PageObjectRef("entity", entity_id, "primary")] if entity_id else [],
            suffix=entity_id or name_slug,
        ))

    # 次要餐厅（平衡/展开模式才展示）：dual-half 配对
    if expand_mode != "full" and len(secondary_rests) > 4:
        secondary_rests = secondary_rests[:4]  # 章节型模式限制数量

    pairs = list(zip(secondary_rests[::2], secondary_rests[1::2]))
    for (e1, s1), (e2, s2) in pairs:
        for eid in (e1, e2):
            if eid:
                assigned.add(eid)
        slug = f"{e1 or 'rest'}_{e2 or 'rest'}"
        pages.append(_make_page(
            "restaurant_detail",
            chapter.chapter_id,
            next_order_fn(),
            trigger_reason="次要餐厅 dual-half 配对",
            priority=60,
            page_size="dual-half",
            merge_policy="pair",
            suffix=slug[:20],
        ))

    # 奇数剩余
    if len(secondary_rests) % 2 == 1:
        last_eid, last_sec = secondary_rests[-1]
        if last_eid:
            assigned.add(last_eid)
        name_slug = (last_sec.payload.get("name", last_eid) or last_eid).replace(" ", "_")[:20]
        pages.append(_make_page(
            "restaurant_detail",
            chapter.chapter_id,
            next_order_fn(),
            trigger_reason="次要餐厅奇数尾 half",
            priority=55,
            page_size="half",
            merge_policy="merge_with_supplemental",
            suffix=last_eid or name_slug,
        ))


# ── 页数预算裁剪（F9） ────────────────────────────────────────────────────────

# 裁剪优先级（数字越小越先裁）
_TRIM_PRIORITY = {
    "supplemental_spots": 10,
    "transit_detail":     20,
    "restaurant_detail":  30,
    "photo_theme_detail": 40,
}
# 永不裁剪
_NEVER_TRIM = {"cover", "toc", "day_execution", "major_activity_detail"}


def _trim_to_budget(pages: list[PagePlan], total_days: int) -> list[PagePlan]:
    cap = _max_pages(total_days)
    if len(pages) <= cap:
        return pages

    logger.warning(
        "[PagePlanner] 页数 %d 超预算 %d，开始裁剪",
        len(pages), cap,
    )

    # 按裁剪优先级升序排 → 先裁优先级低的
    cuttable = [
        p for p in pages
        if p.page_type not in _NEVER_TRIM
    ]
    cuttable.sort(key=lambda p: (
        _TRIM_PRIORITY.get(p.page_type, 99),
        -p.priority,
    ))

    to_remove: set[str] = set()
    for p in cuttable:
        if len(pages) - len(to_remove) <= cap:
            break
        # dual-half 降级为 full（节省 1 页）
        if p.page_size == "dual-half" and p.page_type == "restaurant_detail":
            p.page_size = "full"
            logger.info("[PagePlanner] 降级 %s dual-half→full", p.page_id)
        else:
            to_remove.add(p.page_id)
            logger.info("[PagePlanner] 裁剪 %s (%s)", p.page_id, p.page_type)

    return [p for p in pages if p.page_id not in to_remove]


# ── 持久化（F8） ──────────────────────────────────────────────────────────────

async def plan_pages_and_persist(
    chapters: list[ChapterPlan],
    payload: ReportPayloadV2,
    session: Any,
    plan_id: str,
) -> list[PagePlan]:
    """
    规划页面并将结果持久化到 plan_metadata：
      - page_plan:   list[PagePlan]（供 PDF 渲染用）
      - chapters:    list[ChapterPlan]（供目录/章节 opener 用）
      - page_models: dict[page_id, PageViewModel]（供 Web 预览直接消费）

    后续渲染（Web/PDF）优先从 plan_metadata 读取，避免重算。
    """
    from app.db.models.derived import ItineraryPlan
    from app.domains.rendering.page_view_model import build_view_models
    from dataclasses import asdict as _asdict

    pages = plan_pages(chapters, payload)

    # 构建 view models（两遍构建，含 TOC 回填）
    try:
        view_models = build_view_models(pages, payload)
    except Exception as exc:
        logger.warning("[PagePlanner] build_view_models 失败（降级为空）: %s", exc)
        view_models = {}

    try:
        plan = await session.get(ItineraryPlan, plan_id)
        if plan:
            meta = plan.plan_metadata or {}
            # page_plan：序列化 PagePlan dataclass 列表
            meta["page_plan"] = [_asdict(p) for p in pages]
            meta["page_plan_version"] = "2"
            # chapters：序列化 ChapterPlan 列表
            meta["chapters"] = [_asdict(c) for c in chapters]
            # page_models：序列化 PageViewModel pydantic 模型字典
            meta["page_models"] = {
                pid: vm.dict() if hasattr(vm, "dict") else vars(vm)
                for pid, vm in view_models.items()
            }
            plan.plan_metadata = meta
            await session.flush()
            logger.info(
                "[PagePlanner] plan_metadata 已持久化到 plan %s: "
                "chapters=%d pages=%d view_models=%d",
                plan_id, len(chapters), len(pages), len(view_models),
            )
    except Exception as exc:
        logger.warning("[PagePlanner] 持久化失败（非致命）: %s", exc)

    return pages
