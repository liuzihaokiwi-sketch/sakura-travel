"""
Three-Layer Content Structure — 攻略正文 3 层结构 (H11)

对应文档 §17：总纲 + 每日固定骨架 + 条件页按需触发

3 层结构：
  Layer 1: 总纲（Overview）— 旅行概况、核心亮点、预算概览、注意事项
  Layer 2: 每日骨架（Daily Skeleton）— 4 页固定：路线/餐饮/交通/提醒
  Layer 3: 条件页（Conditional Pages）— 按需触发：出发准备/通票/出片/避坑/附录

供渲染引擎（PDF/H5）使用，从 FragmentAwareContext + ItineraryPlan 生成结构化内容树。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ── 内容节点 ──────────────────────────────────────────────────────────────────

@dataclass
class ContentBlock:
    """最小内容单元"""
    block_id: str
    block_type: str           # "static" | "rule_based" | "ai_generated" | "fragment"
    source_id: Optional[str] = None  # fragment_id / static_block_id / prompt_id
    title: str = ""
    body: str = ""
    body_html: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class DailyPage:
    """每日的一个固定页"""
    page_type: str   # "route" | "dining" | "transport" | "tips"
    title: str
    blocks: list[ContentBlock] = field(default_factory=list)


@dataclass
class DailySection:
    """每日骨架 — 4 页固定"""
    day_index: int
    city_code: str
    day_theme: str
    pages: list[DailyPage] = field(default_factory=list)
    conditional_pages: list["ConditionalPage"] = field(default_factory=list)


@dataclass
class ConditionalPage:
    """条件页 — 按需触发"""
    page_type: str   # "departure_prep" | "transport_pass" | "photo_guide" | "avoid_traps" | "appendix"
    trigger_condition: str   # 触发条件描述
    triggered: bool = False
    title: str = ""
    blocks: list[ContentBlock] = field(default_factory=list)


@dataclass
class OverviewSection:
    """Layer 1: 总纲"""
    trip_summary: ContentBlock = field(default_factory=lambda: ContentBlock(
        block_id="overview_summary", block_type="ai_generated", title="旅行概况"
    ))
    highlights: ContentBlock = field(default_factory=lambda: ContentBlock(
        block_id="overview_highlights", block_type="ai_generated", title="核心亮点"
    ))
    budget_overview: ContentBlock = field(default_factory=lambda: ContentBlock(
        block_id="overview_budget", block_type="rule_based", title="预算概览"
    ))
    important_notes: ContentBlock = field(default_factory=lambda: ContentBlock(
        block_id="overview_notes", block_type="rule_based", title="重要提醒"
    ))


@dataclass
class ContentTree:
    """完整的攻略内容树"""
    overview: OverviewSection
    daily_sections: list[DailySection]
    global_conditionals: list[ConditionalPage]  # 全局条件页（非某天专属）
    metadata: dict = field(default_factory=dict)


# ── 条件页触发规则 ────────────────────────────────────────────────────────────

CONDITIONAL_PAGE_RULES: list[dict] = [
    {
        "page_type": "departure_prep",
        "title": "出发前准备清单",
        "trigger": lambda ctx: True,  # 所有行程都需要
        "static_block": "departure_prep",
    },
    {
        "page_type": "transport_pass",
        "title": "交通通票攻略",
        "trigger": lambda ctx: (
            ctx.get("duration_days", 0) >= 5
            or ctx.get("has_jr_pass")
            or len(ctx.get("city_codes", [])) > 1
        ),
        "static_block": "transport_passes",
    },
    {
        "page_type": "photo_guide",
        "title": "出片指南",
        "trigger": lambda ctx: ctx.get("theme_family") in (
            "couple_aesthetic", "culture_deep"
        ),
        "static_block": "photo_guide",
    },
    {
        "page_type": "avoid_traps",
        "title": "避坑指南",
        "trigger": lambda ctx: True,  # 所有行程都需要
        "static_block": "avoid_traps",
    },
    {
        "page_type": "esim_wifi",
        "title": "网络与通讯",
        "trigger": lambda ctx: True,
        "static_block": "esim_guide",
    },
    {
        "page_type": "safety",
        "title": "安全与紧急联系",
        "trigger": lambda ctx: True,
        "static_block": "safety_info",
    },
]


# ── Layer 2: 每日骨架构建 ─────────────────────────────────────────────────────

def _build_daily_pages(
    day_index: int,
    day_data: dict,
    skeleton_hints: Optional[dict] = None,
) -> list[DailyPage]:
    """为每天构建 4 页固定骨架"""
    day_hints = skeleton_hints or {}
    fragments = day_hints.get("fragments", [])

    # Page 1: 路线页
    route_blocks = []
    route_frags = [f for f in fragments if f.get("fragment_type") in ("route", "experience")]
    if route_frags:
        for rf in route_frags:
            route_blocks.append(ContentBlock(
                block_id=f"day{day_index}_route_{rf['fragment_id'][:8]}",
                block_type="fragment",
                source_id=rf["fragment_id"],
                title=rf.get("title", ""),
                body=rf.get("body_prose", "") or "",
                metadata={"hit_tier": rf.get("hit_tier"), "score": rf.get("final_score")},
            ))
    else:
        route_blocks.append(ContentBlock(
            block_id=f"day{day_index}_route_gen",
            block_type="ai_generated",
            title=f"Day {day_index + 1} 路线",
            body="",  # 待 AI 生成
        ))

    route_page = DailyPage(page_type="route", title=f"Day {day_index + 1} 路线", blocks=route_blocks)

    # Page 2: 餐饮页
    dining_blocks = []
    dining_frags = [f for f in fragments if f.get("fragment_type") == "dining"]
    if dining_frags:
        for df in dining_frags:
            dining_blocks.append(ContentBlock(
                block_id=f"day{day_index}_dining_{df['fragment_id'][:8]}",
                block_type="fragment",
                source_id=df["fragment_id"],
                title=df.get("title", ""),
                body=df.get("body_prose", "") or "",
            ))
    else:
        dining_blocks.append(ContentBlock(
            block_id=f"day{day_index}_dining_gen",
            block_type="ai_generated",
            title="餐饮推荐",
        ))

    dining_page = DailyPage(page_type="dining", title="餐饮推荐", blocks=dining_blocks)

    # Page 3: 交通页
    transport_blocks = []
    logistics_frags = [f for f in fragments if f.get("fragment_type") == "logistics"]
    if logistics_frags:
        for lf in logistics_frags:
            transport_blocks.append(ContentBlock(
                block_id=f"day{day_index}_transport_{lf['fragment_id'][:8]}",
                block_type="fragment",
                source_id=lf["fragment_id"],
                title=lf.get("title", ""),
                body=lf.get("body_prose", "") or "",
            ))
    else:
        transport_blocks.append(ContentBlock(
            block_id=f"day{day_index}_transport_gen",
            block_type="ai_generated",
            title="交通指南",
        ))

    transport_page = DailyPage(page_type="transport", title="交通指南", blocks=transport_blocks)

    # Page 4: 提醒页
    tips_blocks = []
    tips_frags = [f for f in fragments if f.get("fragment_type") == "tips"]
    if tips_frags:
        for tf in tips_frags:
            tips_blocks.append(ContentBlock(
                block_id=f"day{day_index}_tips_{tf['fragment_id'][:8]}",
                block_type="fragment",
                source_id=tf["fragment_id"],
                title=tf.get("title", ""),
                body=tf.get("body_prose", "") or "",
            ))
    else:
        tips_blocks.append(ContentBlock(
            block_id=f"day{day_index}_tips_gen",
            block_type="ai_generated",
            title="今日提醒",
        ))

    tips_page = DailyPage(page_type="tips", title="今日提醒", blocks=tips_blocks)

    return [route_page, dining_page, transport_page, tips_page]


# ── Layer 3: 条件页触发 ───────────────────────────────────────────────────────

def _evaluate_conditionals(profile_ctx: dict) -> list[ConditionalPage]:
    """评估全局条件页触发"""
    pages = []
    for rule in CONDITIONAL_PAGE_RULES:
        triggered = rule["trigger"](profile_ctx)
        page = ConditionalPage(
            page_type=rule["page_type"],
            trigger_condition=str(rule["trigger"]),
            triggered=triggered,
            title=rule["title"],
        )
        if triggered:
            page.blocks.append(ContentBlock(
                block_id=f"cond_{rule['page_type']}",
                block_type="static",
                source_id=rule.get("static_block"),
                title=rule["title"],
                body="",  # 从 static_blocks 渲染
            ))
        pages.append(page)
    return pages


# ── 主函数 ────────────────────────────────────────────────────────────────────

def build_content_tree(
    plan_data: dict,
    skeleton_hints: dict[int, dict],
    profile_ctx: dict,
) -> ContentTree:
    """
    构建完整的 3 层内容树。

    Args:
        plan_data: 行程计划数据 {"days": [{"day_number": 1, "city": "tokyo", ...}]}
        skeleton_hints: 片段复用引擎输出 {day_index: {"fragments": [...], "slots_filled": [...]}}
        profile_ctx: 用户画像上下文 {"city_codes": [...], "theme_family": "...", ...}

    Returns:
        ContentTree: 可供渲染引擎消费的结构化内容树
    """
    # Layer 1: 总纲
    overview = OverviewSection()
    overview.trip_summary.metadata = {
        "city_codes": profile_ctx.get("city_codes", []),
        "duration_days": profile_ctx.get("duration_days", 0),
        "party_type": profile_ctx.get("party_type"),
        "theme_family": profile_ctx.get("theme_family"),
    }

    # Layer 2: 每日骨架
    daily_sections = []
    days = plan_data.get("days", [])
    for i, day in enumerate(days):
        day_hints = skeleton_hints.get(i, {})
        pages = _build_daily_pages(i, day, day_hints)

        section = DailySection(
            day_index=i,
            city_code=day.get("city", ""),
            day_theme=day.get("theme", ""),
            pages=pages,
        )
        daily_sections.append(section)

    # Layer 3: 条件页
    global_conditionals = _evaluate_conditionals(profile_ctx)
    triggered_count = sum(1 for p in global_conditionals if p.triggered)

    # 统计
    total_blocks = sum(
        len(p.blocks) for s in daily_sections for p in s.pages
    )
    fragment_blocks = sum(
        1 for s in daily_sections for p in s.pages for b in p.blocks if b.block_type == "fragment"
    )
    ai_blocks = sum(
        1 for s in daily_sections for p in s.pages for b in p.blocks if b.block_type == "ai_generated"
    )
    static_blocks = total_blocks - fragment_blocks - ai_blocks

    metadata = {
        "total_days": len(daily_sections),
        "total_blocks": total_blocks,
        "fragment_blocks": fragment_blocks,
        "ai_blocks": ai_blocks,
        "static_blocks": static_blocks,
        "fragment_ratio": round(fragment_blocks / max(total_blocks, 1), 2),
        "conditional_pages_triggered": triggered_count,
        "conditional_pages_total": len(global_conditionals),
    }

    logger.info(
        "content_tree: days=%d blocks=%d (frag=%d ai=%d) conditionals=%d/%d",
        len(daily_sections), total_blocks, fragment_blocks, ai_blocks,
        triggered_count, len(global_conditionals),
    )

    return ContentTree(
        overview=overview,
        daily_sections=daily_sections,
        global_conditionals=global_conditionals,
        metadata=metadata,
    )
