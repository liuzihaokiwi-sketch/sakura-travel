"""
page_type_registry.py — 17 种报告页型注册表（L3-02）

输入：无（纯静态注册表）
输出：PAGE_TYPE_REGISTRY dict + get_page_type() 查询函数

依赖：无外部依赖

设计参考：
  report/01_页型总表
  report/04_数据协议
  fix/TASK_L3_渲染层任务书_Sonnet46.md §L3-02
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PageTypeDefinition:
    """单个页型的完整规格描述"""
    page_type: str
    topic_family: str              # "frontmatter" / "chapter" / "daily" / "detail" / "special" / "appendix"
    default_size: str              # "full" / "half" / "dual-half"
    required_slots: list[str]      # 必须存在的 slot（对应 SectionVM.section_type）
    optional_slots: list[str]      # 可选 slot
    visual_priority: list[str]     # 渲染优先级（从上到下）
    mergeable_with: list[str]      # 可与之合并的页型
    print_constraints: list[str]   # 打印约束，如 ["break-before: always"]
    web_constraints: list[str]     # Web 约束（通常为空）
    primary_promise: str           # 这一页对读者的核心承诺


PAGE_TYPE_REGISTRY: dict[str, PageTypeDefinition] = {

    # ── 固定前置页（frontmatter） ─────────────────────────────────────────

    "cover": PageTypeDefinition(
        page_type="cover",
        topic_family="frontmatter",
        default_size="full",
        required_slots=["heading", "hero"],
        optional_slots=["stat_strip", "sticker_zone"],
        visual_priority=["hero", "heading", "stat_strip"],
        mergeable_with=[],
        print_constraints=["break-before: always"],
        web_constraints=[],
        primary_promise="第一眼告诉你这是谁的旅程",
    ),

    "toc": PageTypeDefinition(
        page_type="toc",
        topic_family="frontmatter",
        default_size="full",
        required_slots=["heading", "toc_list"],
        optional_slots=[],
        visual_priority=["heading", "toc_list"],
        mergeable_with=[],
        print_constraints=["break-before: always"],
        web_constraints=[],
        primary_promise="帮你快速定位想看的内容",
    ),

    "preference_fulfillment": PageTypeDefinition(
        page_type="preference_fulfillment",
        topic_family="frontmatter",
        default_size="full",
        required_slots=["heading", "fulfillment_list"],
        optional_slots=["evidence"],
        visual_priority=["heading", "fulfillment_list", "evidence"],
        mergeable_with=[],
        print_constraints=["break-before: always"],
        web_constraints=[],
        primary_promise="告诉你每个偏好是怎么被满足的",
    ),

    "major_activity_overview": PageTypeDefinition(
        page_type="major_activity_overview",
        topic_family="frontmatter",
        default_size="full",
        required_slots=["heading", "entity_card"],
        optional_slots=["stat_strip", "highlight"],
        visual_priority=["heading", "entity_card", "stat_strip"],
        mergeable_with=[],
        print_constraints=["break-before: always"],
        web_constraints=[],
        primary_promise="一眼看懂整趟行程的高光体验",
    ),

    "route_overview": PageTypeDefinition(
        page_type="route_overview",
        topic_family="frontmatter",
        default_size="full",
        required_slots=["heading", "timeline"],
        optional_slots=["stat_strip", "text_block"],
        visual_priority=["heading", "timeline", "stat_strip"],
        mergeable_with=[],
        print_constraints=["break-before: always"],
        web_constraints=[],
        primary_promise="一图看透整条路线的时间与空间逻辑",
    ),

    "hotel_strategy": PageTypeDefinition(
        page_type="hotel_strategy",
        topic_family="frontmatter",
        default_size="full",
        required_slots=["heading", "entity_card"],
        optional_slots=["text_block", "stat_strip"],
        visual_priority=["heading", "entity_card", "text_block"],
        mergeable_with=[],
        print_constraints=["break-before: always"],
        web_constraints=[],
        primary_promise="解释住哪里、为什么住这里、怎么安排换酒店",
    ),

    "booking_window": PageTypeDefinition(
        page_type="booking_window",
        topic_family="frontmatter",
        default_size="full",
        required_slots=["heading", "risk_card"],
        optional_slots=["text_block"],
        visual_priority=["heading", "risk_card", "text_block"],
        mergeable_with=["departure_prep"],
        print_constraints=["break-before: always"],
        web_constraints=[],
        primary_promise="告诉你什么必须提前订、不订会后悔",
    ),

    "departure_prep": PageTypeDefinition(
        page_type="departure_prep",
        topic_family="frontmatter",
        default_size="full",
        required_slots=["heading", "text_block"],
        optional_slots=["stat_strip", "freewrite_zone"],
        visual_priority=["heading", "text_block"],
        mergeable_with=["booking_window"],
        print_constraints=["break-before: always"],
        web_constraints=[],
        primary_promise="出发前不会漏掉的事项清单",
    ),

    "live_notice": PageTypeDefinition(
        page_type="live_notice",
        topic_family="frontmatter",
        default_size="full",
        required_slots=["heading", "risk_card"],
        optional_slots=[],
        visual_priority=["heading", "risk_card"],
        mergeable_with=[],
        print_constraints=["break-before: always"],
        web_constraints=[],
        primary_promise="实时注意事项：季节风险 / 天气 / 临时关闭",
    ),

    # ── 章节 opener ──────────────────────────────────────────────────────

    "chapter_opener": PageTypeDefinition(
        page_type="chapter_opener",
        topic_family="chapter",
        default_size="full",
        required_slots=["heading", "hero"],
        optional_slots=["text_block", "highlight", "sticker_zone", "freewrite_zone"],
        visual_priority=["hero", "heading", "text_block", "highlight", "sticker_zone", "freewrite_zone"],
        mergeable_with=[],
        print_constraints=["break-before: always"],
        web_constraints=[],
        primary_promise="进入新城市圈时的视觉与情绪切换",
    ),

    # ── 每日执行页 ───────────────────────────────────────────────────────

    "day_execution": PageTypeDefinition(
        page_type="day_execution",
        topic_family="daily",
        default_size="full",
        required_slots=["heading", "timeline"],
        optional_slots=["highlight", "risk_card", "text_block", "sticker_zone", "freewrite_zone"],
        visual_priority=["heading", "timeline", "highlight", "risk_card", "sticker_zone", "freewrite_zone"],
        mergeable_with=[],
        print_constraints=["break-before: always"],
        web_constraints=[],
        primary_promise="当天从早到晚的精确执行指南",
    ),

    # ── 详情页 ───────────────────────────────────────────────────────────

    "major_activity_detail": PageTypeDefinition(
        page_type="major_activity_detail",
        topic_family="detail",
        default_size="full",
        required_slots=["heading", "hero", "key_reasons"],
        optional_slots=["stat_strip", "text_block", "risk_card"],
        visual_priority=["hero", "heading", "key_reasons", "stat_strip", "text_block"],
        mergeable_with=[],
        print_constraints=["break-before: always"],
        web_constraints=[],
        primary_promise="深度解析这个体验为什么值得 + 怎么玩最好",
    ),

    "hotel_detail": PageTypeDefinition(
        page_type="hotel_detail",
        topic_family="detail",
        default_size="full",
        required_slots=["heading", "hero", "key_reasons"],
        optional_slots=["stat_strip", "text_block", "freewrite_zone"],
        visual_priority=["hero", "heading", "key_reasons", "stat_strip"],
        mergeable_with=[],
        print_constraints=["break-before: always"],
        web_constraints=[],
        primary_promise="解释为什么选这家酒店 + 入住注意事项",
    ),

    "restaurant_detail": PageTypeDefinition(
        page_type="restaurant_detail",
        topic_family="detail",
        default_size="full",
        required_slots=["heading", "hero", "key_reasons"],
        optional_slots=["stat_strip", "text_block", "risk_card", "sticker_zone", "freewrite_zone"],
        visual_priority=["hero", "heading", "key_reasons", "stat_strip"],
        mergeable_with=["restaurant_detail"],
        print_constraints=["break-before: always"],
        web_constraints=[],
        primary_promise="这家餐厅吃什么、为什么吃这家、怎么订",
    ),

    "photo_theme_detail": PageTypeDefinition(
        page_type="photo_theme_detail",
        topic_family="detail",
        default_size="half",
        required_slots=["heading", "hero"],
        optional_slots=["text_block", "sticker_zone"],
        visual_priority=["hero", "heading", "text_block"],
        mergeable_with=["supplemental_spots"],
        print_constraints=[],
        web_constraints=[],
        primary_promise="出片攻略：最佳机位、光线时机、构图建议",
    ),

    "transit_detail": PageTypeDefinition(
        page_type="transit_detail",
        topic_family="detail",
        default_size="half",
        required_slots=["heading", "timeline"],
        optional_slots=["text_block", "stat_strip"],
        visual_priority=["heading", "timeline", "text_block"],
        mergeable_with=["supplemental_spots"],
        print_constraints=[],
        web_constraints=[],
        primary_promise="复杂交通日的换乘指南和时间节点",
    ),

    "supplemental_spots": PageTypeDefinition(
        page_type="supplemental_spots",
        topic_family="appendix",
        default_size="half",
        required_slots=["heading", "entity_card"],
        optional_slots=["text_block"],
        visual_priority=["heading", "entity_card", "text_block"],
        mergeable_with=["photo_theme_detail", "transit_detail", "supplemental_spots"],
        print_constraints=[],
        web_constraints=[],
        primary_promise="补充备选景点和周边便利信息",
    ),
}


def get_page_type(name: str) -> PageTypeDefinition:
    """
    按 name 查询页型定义。

    Raises:
        KeyError: 如果 name 不在注册表中
    """
    if name not in PAGE_TYPE_REGISTRY:
        raise KeyError(
            f"页型 '{name}' 未注册。已知页型: {sorted(PAGE_TYPE_REGISTRY.keys())}"
        )
    return PAGE_TYPE_REGISTRY[name]


def list_page_types(topic_family: str | None = None) -> list[PageTypeDefinition]:
    """列出所有（或指定 family 的）页型定义"""
    result = list(PAGE_TYPE_REGISTRY.values())
    if topic_family:
        result = [p for p in result if p.topic_family == topic_family]
    return result
