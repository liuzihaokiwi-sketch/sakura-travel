/**
 * BookingWindowPage.tsx — 预订时间窗口提醒页（booking_window）
 *
 * 页型：frontmatter / full 页
 * 作用：列出行程中需要提前预订的项目（热门景点门票、特色餐厅、新干线、酒店），
 *       并按"最迟需提前 N 天"排序，帮助用户合理安排预订节奏。
 */
"use client"

import { cn } from "@/lib/utils"
import type { PageViewModel, SectionVM } from "@/lib/report/types"
import PageShell from "../PageShell"

// ── 类型 ───────────────────────────────────────────────────────────────────

interface BookingItem {
  id: string
  name: string
  entity_type: "poi" | "restaurant" | "hotel" | "transport" | "activity"
  booking_channel: string          // "官网" / "OTA" / "电话" / "现场"
  booking_url?: string
  days_before_required: number     // 至少提前 N 天预订
  is_mandatory: boolean            // 不预订会无法进入/就坐
  notes?: string
  day_index?: number               // 对应行程第几天
}

interface BookingTimelineContent {
  items: BookingItem[]
}

interface BookingStatContent {
  mandatory_count: number
  recommended_count: number
  earliest_days_before: number     // 最早需要提前的天数
}

// ── 子组件 ─────────────────────────────────────────────────────────────────

const ENTITY_ICON: Record<string, string> = {
  poi:       "🏛️",
  restaurant:"🍽️",
  hotel:     "🏨",
  transport: "🚄",
  activity:  "🎭",
}

function BookingItemCard({ item }: { item: BookingItem }) {
  return (
    <div
      className={cn(
        "flex items-start gap-3 p-3 rounded-lg border mb-2.5",
        item.is_mandatory
          ? "border-red-200 bg-red-50"
          : "border-gray-200 bg-white",
      )}
    >
      {/* 图标 */}
      <span className="text-xl mt-0.5 flex-shrink-0">
        {ENTITY_ICON[item.entity_type] ?? "📌"}
      </span>

      {/* 内容 */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <p className="text-sm font-semibold text-gray-900 leading-snug">{item.name}</p>
          {item.day_index != null && (
            <span className="flex-shrink-0 text-[11px] font-medium px-1.5 py-0.5 rounded-full bg-gray-100 text-gray-600">
              第 {item.day_index} 天
            </span>
          )}
        </div>

        {/* 预订渠道 */}
        <p className="text-xs text-gray-500 mt-0.5">
          预订渠道：{item.booking_channel}
          {item.booking_url && (
            <>
              {" · "}
              <a
                href={item.booking_url}
                target="_blank"
                rel="noopener noreferrer"
                className="underline text-blue-500 hover:text-blue-700"
              >
                前往预订
              </a>
            </>
          )}
        </p>

        {/* 提前天数 */}
        <div className="flex items-center gap-2 mt-1.5">
          <span
            className={cn(
              "text-[11px] font-bold px-2 py-0.5 rounded-full",
              item.days_before_required >= 30
                ? "bg-red-100 text-red-700"
                : item.days_before_required >= 7
                ? "bg-amber-100 text-amber-700"
                : "bg-blue-50 text-blue-600",
            )}
          >
            提前 {item.days_before_required} 天
          </span>
          {item.is_mandatory && (
            <span className="text-[11px] font-semibold text-red-600">必须预订</span>
          )}
        </div>

        {item.notes && (
          <p className="text-xs text-gray-500 mt-1 leading-relaxed">{item.notes}</p>
        )}
      </div>
    </div>
  )
}

function BookingTimeline({ section }: { section: SectionVM }) {
  const content = section.content as BookingTimelineContent | null
  if (!content?.items?.length) return null

  // 按 days_before_required 降序排列（越早需要预订越靠前）
  const sorted = [...content.items].sort(
    (a, b) => b.days_before_required - a.days_before_required,
  )

  return (
    <div>
      {section.heading && (
        <h3 className="text-[13px] font-semibold text-gray-700 mb-3 uppercase tracking-wide">
          {section.heading}
        </h3>
      )}
      <div>
        {sorted.map((item) => (
          <BookingItemCard key={item.id} item={item} />
        ))}
      </div>
    </div>
  )
}

function BookingStatStrip({ section }: { section: SectionVM }) {
  const content = section.content as BookingStatContent | null
  if (!content) return null

  return (
    <div className="grid grid-cols-3 gap-3 mb-6">
      {/* 必须预订数 */}
      <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-center">
        <p className="text-2xl font-bold text-red-600">{content.mandatory_count}</p>
        <p className="text-xs text-red-700 mt-0.5">必须预订</p>
      </div>
      {/* 建议预订数 */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-center">
        <p className="text-2xl font-bold text-amber-600">{content.recommended_count}</p>
        <p className="text-xs text-amber-700 mt-0.5">建议预订</p>
      </div>
      {/* 最早提前天数 */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-center">
        <p className="text-2xl font-bold text-blue-600">{content.earliest_days_before}</p>
        <p className="text-xs text-blue-700 mt-0.5">最早提前天数</p>
      </div>
    </div>
  )
}

// ── 主组件 ─────────────────────────────────────────────────────────────────

interface BookingWindowPageProps extends PageViewModel {
  mode?: "screen" | "print"
}

export default function BookingWindowPage(props: BookingWindowPageProps) {
  const { heading, sections, footer, mode = "screen" } = props

  const statSection      = sections.find((s) => s.section_type === "stat_strip")
  const timelineSection  = sections.find((s) => s.section_type === "booking_timeline")
  const noteSection      = sections.find((s) => s.section_type === "text_block")

  return (
    <PageShell mode={mode} footer={footer}>
      {/* 标题区 */}
      <div className="mb-5">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-2xl">🗓️</span>
          <h1 className="text-xl font-bold text-gray-900">{heading.title}</h1>
        </div>
        {heading.subtitle && (
          <p className="text-sm text-gray-500 pl-9">{heading.subtitle}</p>
        )}
      </div>

      {/* 统计条 */}
      {statSection && <BookingStatStrip section={statSection} />}

      {/* 预订时间线 */}
      {timelineSection && <BookingTimeline section={timelineSection} />}

      {/* 备注 */}
      {noteSection && (
        <div className="mt-5 p-3 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-xs text-gray-600 leading-relaxed">
            {typeof noteSection.content === "string"
              ? noteSection.content
              : (noteSection.content as { text?: string })?.text ?? ""}
          </p>
        </div>
      )}
    </PageShell>
  )
}
