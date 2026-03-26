/**
 * DeparturePrepPage.tsx — 出行前注意事项页（departure_prep）
 *
 * 页型：frontmatter / full 页
 * 作用：汇总行程中所有需要提前准备的事项，包括预订提醒、签证/通关、行李、
 *       汇率/支付、健康注意事项等，让用户在出发前有明确的 checklist。
 */
"use client"

import { cn } from "@/lib/utils"
import type { PageViewModel, SectionVM } from "@/lib/report/types"
import PageShell from "../PageShell"

// ── 子组件 ─────────────────────────────────────────────────────────────────

interface CheckItem {
  id: string
  label: string
  detail?: string
  is_done?: boolean
  urgency?: "high" | "medium" | "low"
  deadline_days_before?: number   // 出发前 N 天需完成
}

interface CheckGroupContent {
  group_title: string
  icon?: string
  items: CheckItem[]
}

interface PrepHeroContent {
  image_url?: string
  image_alt?: string
  summary_text: string             // "您有 X 项待确认事项"
  urgent_count: number
  total_count: number
}

function UrgencyDot({ urgency }: { urgency?: "high" | "medium" | "low" }) {
  const cls = {
    high:   "bg-red-500",
    medium: "bg-amber-400",
    low:    "bg-emerald-400",
  }[urgency ?? "low"] ?? "bg-gray-300"
  return <span className={cn("inline-block w-2 h-2 rounded-full flex-shrink-0 mt-1.5", cls)} />
}

function CheckItemRow({ item }: { item: CheckItem }) {
  return (
    <li className="flex items-start gap-2.5 py-1.5 border-b border-gray-100 last:border-0">
      <UrgencyDot urgency={item.urgency} />
      <div className="flex-1 min-w-0">
        <p className={cn("text-sm font-medium leading-snug", item.is_done && "line-through text-gray-400")}>
          {item.label}
        </p>
        {item.detail && (
          <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">{item.detail}</p>
        )}
        {item.deadline_days_before != null && (
          <span className="inline-block mt-1 text-[11px] font-medium px-1.5 py-0.5 rounded bg-amber-50 text-amber-700">
            出发前 {item.deadline_days_before} 天内完成
          </span>
        )}
      </div>
    </li>
  )
}

function CheckGroup({ section }: { section: SectionVM }) {
  const content = section.content as unknown as CheckGroupContent | null
  if (!content) return null
  return (
    <div className="mb-5">
      <div className="flex items-center gap-2 mb-2">
        {content.icon && <span className="text-base">{content.icon}</span>}
        <h3 className="text-[13px] font-semibold text-gray-800 uppercase tracking-wide">
          {content.group_title}
        </h3>
      </div>
      <ul className="bg-white rounded-lg border border-gray-200 px-3 divide-y-0">
        {content.items.map((item) => (
          <CheckItemRow key={item.id} item={item} />
        ))}
      </ul>
    </div>
  )
}

function PrepHero({ section }: { section: SectionVM }) {
  const content = section.content as unknown as PrepHeroContent | null
  if (!content) return null

  const hasUrgent = content.urgent_count > 0

  return (
    <div
      className={cn(
        "rounded-xl p-4 mb-6 flex items-center justify-between gap-4",
        hasUrgent ? "bg-red-50 border border-red-200" : "bg-emerald-50 border border-emerald-200",
      )}
    >
      <div>
        <p className={cn("text-sm font-semibold", hasUrgent ? "text-red-800" : "text-emerald-800")}>
          {content.summary_text}
        </p>
        {hasUrgent && (
          <p className="text-xs text-red-600 mt-0.5">
            其中 {content.urgent_count} 项需要尽快处理
          </p>
        )}
      </div>
      <div className="text-right flex-shrink-0">
        <p className={cn("text-2xl font-bold", hasUrgent ? "text-red-600" : "text-emerald-600")}>
          {content.total_count}
        </p>
        <p className="text-xs text-gray-500">待确认事项</p>
      </div>
    </div>
  )
}

// ── 主组件 ─────────────────────────────────────────────────────────────────

interface DeparturePrepPageProps {
  vm: PageViewModel
  mode?: "screen" | "print"
}

export default function DeparturePrepPage(props: DeparturePrepPageProps) {
  const { vm, mode = "screen" } = props
  const { heading, hero, sections, footer } = vm

  const heroSection   = sections.find((s) => s.section_type === "prep_hero")
  const checkSections = sections.filter((s) => s.section_type === "check_group")
  const noteSection   = sections.find((s) => s.section_type === "text_block")

  return (
    <PageShell mode={mode} footer={footer}>
      {/* 页眉 */}
      <div className="flex items-start justify-between mb-5">
        <div>
          <h1 className="text-xl font-bold text-gray-900 leading-tight">
            {heading.title}
          </h1>
          {heading.subtitle && (
            <p className="text-sm text-gray-500 mt-1">{heading.subtitle}</p>
          )}
        </div>
        {/* 装饰性图标 */}
        <div className="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center flex-shrink-0">
          <svg
            className="w-6 h-6 text-blue-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.8}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806
                 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806
                 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946
                 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946
                 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806
                 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806
                 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946
                 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946
                 3.42 3.42 0 013.138-3.138z"
            />
          </svg>
        </div>
      </div>

      {/* Hero 主图（可选）*/}
      {hero?.image_url && (
        <div className="relative h-32 rounded-xl overflow-hidden mb-5">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={hero.image_url}
            alt={hero.image_alt ?? ""}
            className="w-full h-full object-cover"
          />
          {hero.caption && (
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 px-3 py-2">
              <p className="text-white text-xs">{hero.caption}</p>
            </div>
          )}
        </div>
      )}

      {/* 摘要横幅 */}
      {heroSection && <PrepHero section={heroSection} />}

      {/* 分组 Checklist */}
      <div className="space-y-0">
        {checkSections.map((s, i) => (
          <CheckGroup key={i} section={s} />
        ))}
      </div>

      {/* 底部备注 */}
      {noteSection && (
        <div className="mt-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-xs text-gray-600 leading-relaxed">
            {typeof noteSection.content === "string"
              ? noteSection.content
              : (noteSection.content as unknown as { text?: string })?.text ?? ""}
          </p>
        </div>
      )}
    </PageShell>
  )
}
