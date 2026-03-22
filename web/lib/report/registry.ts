/**
 * web/lib/report/registry.ts — 页型注册表 TS 版本 + 组件映射（L3-06）
 *
 * 对应 Python 端：app/domains/rendering/page_type_registry.py
 */

import type { ComponentType } from "react"
import type { PageTypeDefinition, PageViewModel } from "./types"

// ── 页型注册表 ────────────────────────────────────────────────────────────────

export const PAGE_TYPE_REGISTRY: Record<string, PageTypeDefinition> = {
  cover: {
    page_type: "cover",
    topic_family: "frontmatter",
    default_size: "full",
    required_slots: ["heading", "hero"],
    optional_slots: ["stat_strip"],
    visual_priority: ["hero", "heading", "stat_strip"],
    mergeable_with: [],
    print_constraints: ["break-before: always"],
    web_constraints: [],
    primary_promise: "第一眼告诉你这是谁的旅程",
  },
  toc: {
    page_type: "toc",
    topic_family: "frontmatter",
    default_size: "full",
    required_slots: ["heading", "toc_list"],
    optional_slots: [],
    visual_priority: ["heading", "toc_list"],
    mergeable_with: [],
    print_constraints: ["break-before: always"],
    web_constraints: [],
    primary_promise: "帮你快速定位想看的内容",
  },
  preference_fulfillment: {
    page_type: "preference_fulfillment",
    topic_family: "frontmatter",
    default_size: "full",
    required_slots: ["heading", "fulfillment_list"],
    optional_slots: ["evidence"],
    visual_priority: ["heading", "fulfillment_list", "evidence"],
    mergeable_with: [],
    print_constraints: ["break-before: always"],
    web_constraints: [],
    primary_promise: "告诉你每个偏好是怎么被满足的",
  },
  major_activity_overview: {
    page_type: "major_activity_overview",
    topic_family: "frontmatter",
    default_size: "full",
    required_slots: ["heading", "entity_card"],
    optional_slots: ["stat_strip", "highlight"],
    visual_priority: ["heading", "entity_card", "stat_strip"],
    mergeable_with: [],
    print_constraints: ["break-before: always"],
    web_constraints: [],
    primary_promise: "一眼看懂整趟行程的高光体验",
  },
  route_overview: {
    page_type: "route_overview",
    topic_family: "frontmatter",
    default_size: "full",
    required_slots: ["heading", "timeline"],
    optional_slots: ["stat_strip", "text_block"],
    visual_priority: ["heading", "timeline", "stat_strip"],
    mergeable_with: [],
    print_constraints: ["break-before: always"],
    web_constraints: [],
    primary_promise: "一图看透整条路线的时间与空间逻辑",
  },
  hotel_strategy: {
    page_type: "hotel_strategy",
    topic_family: "frontmatter",
    default_size: "full",
    required_slots: ["heading", "entity_card"],
    optional_slots: ["text_block", "stat_strip"],
    visual_priority: ["heading", "entity_card", "text_block"],
    mergeable_with: [],
    print_constraints: ["break-before: always"],
    web_constraints: [],
    primary_promise: "解释住哪里、为什么住这里、怎么安排换酒店",
  },
  booking_window: {
    page_type: "booking_window",
    topic_family: "frontmatter",
    default_size: "full",
    required_slots: ["heading", "risk_card"],
    optional_slots: ["text_block"],
    visual_priority: ["heading", "risk_card", "text_block"],
    mergeable_with: ["departure_prep"],
    print_constraints: ["break-before: always"],
    web_constraints: [],
    primary_promise: "告诉你什么必须提前订、不订会后悔",
  },
  departure_prep: {
    page_type: "departure_prep",
    topic_family: "frontmatter",
    default_size: "full",
    required_slots: ["heading", "text_block"],
    optional_slots: ["stat_strip"],
    visual_priority: ["heading", "text_block"],
    mergeable_with: ["booking_window"],
    print_constraints: ["break-before: always"],
    web_constraints: [],
    primary_promise: "出发前不会漏掉的事项清单",
  },
  live_notice: {
    page_type: "live_notice",
    topic_family: "frontmatter",
    default_size: "full",
    required_slots: ["heading", "risk_card"],
    optional_slots: [],
    visual_priority: ["heading", "risk_card"],
    mergeable_with: [],
    print_constraints: ["break-before: always"],
    web_constraints: [],
    primary_promise: "实时注意事项：季节风险 / 天气 / 临时关闭",
  },
  chapter_opener: {
    page_type: "chapter_opener",
    topic_family: "chapter",
    default_size: "full",
    required_slots: ["heading", "hero"],
    optional_slots: ["text_block", "highlight"],
    visual_priority: ["hero", "heading", "text_block", "highlight"],
    mergeable_with: [],
    print_constraints: ["break-before: always"],
    web_constraints: [],
    primary_promise: "进入新城市圈时的视觉与情绪切换",
  },
  day_execution: {
    page_type: "day_execution",
    topic_family: "daily",
    default_size: "full",
    required_slots: ["heading", "timeline"],
    optional_slots: ["highlight", "risk_card", "text_block"],
    visual_priority: ["heading", "timeline", "highlight", "risk_card"],
    mergeable_with: [],
    print_constraints: ["break-before: always"],
    web_constraints: [],
    primary_promise: "当天从早到晚的精确执行指南",
  },
  major_activity_detail: {
    page_type: "major_activity_detail",
    topic_family: "detail",
    default_size: "full",
    required_slots: ["heading", "hero", "key_reasons"],
    optional_slots: ["stat_strip", "text_block", "risk_card"],
    visual_priority: ["hero", "heading", "key_reasons", "stat_strip", "text_block"],
    mergeable_with: [],
    print_constraints: ["break-before: always"],
    web_constraints: [],
    primary_promise: "深度解析这个体验为什么值得 + 怎么玩最好",
  },
  hotel_detail: {
    page_type: "hotel_detail",
    topic_family: "detail",
    default_size: "full",
    required_slots: ["heading", "hero", "key_reasons"],
    optional_slots: ["stat_strip", "text_block"],
    visual_priority: ["hero", "heading", "key_reasons", "stat_strip"],
    mergeable_with: [],
    print_constraints: ["break-before: always"],
    web_constraints: [],
    primary_promise: "解释为什么选这家酒店 + 入住注意事项",
  },
  restaurant_detail: {
    page_type: "restaurant_detail",
    topic_family: "detail",
    default_size: "full",
    required_slots: ["heading", "hero", "key_reasons"],
    optional_slots: ["stat_strip", "text_block", "risk_card"],
    visual_priority: ["hero", "heading", "key_reasons", "stat_strip"],
    mergeable_with: ["restaurant_detail"],
    print_constraints: ["break-before: always"],
    web_constraints: [],
    primary_promise: "这家餐厅吃什么、为什么吃这家、怎么订",
  },
  photo_theme_detail: {
    page_type: "photo_theme_detail",
    topic_family: "detail",
    default_size: "half",
    required_slots: ["heading", "hero"],
    optional_slots: ["text_block"],
    visual_priority: ["hero", "heading", "text_block"],
    mergeable_with: ["supplemental_spots"],
    print_constraints: [],
    web_constraints: [],
    primary_promise: "出片攻略：最佳机位、光线时机、构图建议",
  },
  transit_detail: {
    page_type: "transit_detail",
    topic_family: "detail",
    default_size: "half",
    required_slots: ["heading", "timeline"],
    optional_slots: ["text_block", "stat_strip"],
    visual_priority: ["heading", "timeline", "text_block"],
    mergeable_with: ["supplemental_spots"],
    print_constraints: [],
    web_constraints: [],
    primary_promise: "复杂交通日的换乘指南和时间节点",
  },
  supplemental_spots: {
    page_type: "supplemental_spots",
    topic_family: "appendix",
    default_size: "half",
    required_slots: ["heading", "entity_card"],
    optional_slots: ["text_block"],
    visual_priority: ["heading", "entity_card", "text_block"],
    mergeable_with: ["photo_theme_detail", "transit_detail", "supplemental_spots"],
    print_constraints: [],
    web_constraints: [],
    primary_promise: "补充备选景点和周边便利信息",
  },
}

export function getPageTypeDef(pageType: string): PageTypeDefinition | undefined {
  return PAGE_TYPE_REGISTRY[pageType]
}

// ── 组件映射（懒加载，避免 SSR 问题） ─────────────────────────────────────────

const componentImports: Record<string, () => Promise<{ default: ComponentType<{ vm: PageViewModel; mode?: "screen" | "print" }> }>> = {
  // ── 固定前置页（frontmatter）─────────────────────────────────────────────
  cover:                   () => import("@/components/report/page-types/CoverPage"),
  toc:                     () => import("@/components/report/page-types/TocPage"),
  preference_fulfillment:  () => import("@/components/report/page-types/PreferencePage"),
  major_activity_overview: () => import("@/components/report/page-types/MajorActivityOverviewPage"),
  route_overview:          () => import("@/components/report/page-types/RouteOverviewPage"),
  hotel_strategy:          () => import("@/components/report/page-types/HotelStrategyPage"),
  booking_window:          () => import("@/components/report/page-types/BookingWindowPage"),
  departure_prep:          () => import("@/components/report/page-types/DeparturePrepPage"),
  live_notice:             () => import("@/components/report/page-types/LiveNoticePage"),
  // ── 章节 / 每日页 ──────────────────────────────────────────────────────
  chapter_opener:          () => import("@/components/report/page-types/ChapterOpenerPage"),
  day_execution:           () => import("@/components/report/page-types/DayExecutionPage"),
  // ── 详情页（detail）────────────────────────────────────────────────────
  major_activity_detail:   () => import("@/components/report/page-types/MajorActivityDetailPage"),
  hotel_detail:            () => import("@/components/report/page-types/HotelDetailPage"),
  restaurant_detail:       () => import("@/components/report/page-types/RestaurantDetailPage"),
  photo_theme_detail:      () => import("@/components/report/page-types/PhotoThemeDetailPage"),
  transit_detail:          () => import("@/components/report/page-types/TransitDetailPage"),
  // ── 附录页（appendix）──────────────────────────────────────────────────
  supplemental_spots:      () => import("@/components/report/page-types/SupplementalSpotsPage"),
}

/** 是否有对应的具体组件实现 */
export function hasPageComponent(pageType: string): boolean {
  return pageType in componentImports
}

/** 动态加载页型组件（返回 Promise） */
export function loadPageComponent(
  pageType: string
): (() => Promise<{ default: ComponentType<{ vm: PageViewModel; mode?: "screen" | "print" }> }>) | null {
  return componentImports[pageType] ?? null
}
