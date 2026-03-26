/**
 * MajorActivityDetailPage.tsx — 主要活动详情页（major_activity_detail）
 *
 * 页型：detail / full 页
 * 作用：深度解析一个 S/A 级活动：为什么值得去、核心体验亮点、实用信息、
 *       拍摄建议、季节性风险。
 */
"use client"

import { cn } from "@/lib/utils"
import type { PageViewModel, SectionVM } from "@/lib/report/types"
import PageShell from "../PageShell"

// ── 类型 ───────────────────────────────────────────────────────────────────

interface KeyReason {
  icon?: string
  title: string
  body: string
}

interface KeyReasonsContent {
  reasons: KeyReason[]
}

interface StatItem {
  label: string
  value: string
  sub?: string
}

interface StatStripContent {
  stats: StatItem[]
}

// ── 子组件 ─────────────────────────────────────────────────────────────────

function KeyReasonCard({ reason }: { reason: KeyReason }) {
  return (
    <div className="flex items-start gap-2.5 p-2.5 rounded-lg bg-white border border-gray-200 mb-2">
      {reason.icon && <span className="text-lg flex-shrink-0">{reason.icon}</span>}
      <div>
        <p className="text-sm font-semibold text-gray-900">{reason.title}</p>
        <p className="text-xs text-gray-600 mt-0.5 leading-relaxed">{reason.body}</p>
      </div>
    </div>
  )
}

function KeyReasons({ section }: { section: SectionVM }) {
  const content = section.content as unknown as KeyReasonsContent | null
  if (!content?.reasons?.length) return null
  return (
    <div className="mb-4">
      {section.heading && (
        <h3 className="text-[13px] font-semibold text-gray-700 mb-2 uppercase tracking-wide">
          {section.heading}
        </h3>
      )}
      {content.reasons.map((r, i) => <KeyReasonCard key={i} reason={r} />)}
    </div>
  )
}

function StatStrip({ section }: { section: SectionVM }) {
  const content = section.content as unknown as StatStripContent | null
  if (!content?.stats?.length) return null
  return (
    <div className={cn("grid gap-2 mb-4", `grid-cols-${Math.min(content.stats.length, 4)}`)}>
      {content.stats.map((s, i) => (
        <div key={i} className="bg-gray-50 border border-gray-200 rounded-lg p-2.5 text-center">
          <p className="text-base font-bold text-gray-900">{s.value}</p>
          <p className="text-[11px] text-gray-500">{s.label}</p>
          {s.sub && <p className="text-[10px] text-gray-400">{s.sub}</p>}
        </div>
      ))}
    </div>
  )
}

// ── 主组件 ─────────────────────────────────────────────────────────────────

interface MajorActivityDetailPageProps {
  vm: PageViewModel
  mode?: "screen" | "print"
}

export default function MajorActivityDetailPage(props: MajorActivityDetailPageProps) {
  const { vm, mode = "screen" } = props
  const { heading, hero, sections, footer } = vm

  const statSection    = sections.find((s) => s.section_type === "stat_strip")
  const reasonSection  = sections.find((s) => s.section_type === "key_reasons")
  const textSection    = sections.find((s) => s.section_type === "text_block")
  const riskSection    = sections.find((s) => s.section_type === "risk_card")

  return (
    <PageShell mode={mode} footer={footer}>
      {/* Hero 图 */}
      {hero?.image_url && (
        <div className="relative h-48 rounded-xl overflow-hidden mb-4">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={hero.image_url} alt={hero.image_alt ?? ""} className="w-full h-full object-cover" />
          {hero.caption && (
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 px-3 py-2">
              <p className="text-white text-xs">{hero.caption}</p>
            </div>
          )}
        </div>
      )}

      {/* 标题 */}
      <div className="mb-4">
        <h1 className="text-xl font-bold text-gray-900 leading-tight">{heading.title}</h1>
        {heading.subtitle && <p className="text-sm text-gray-500 mt-1">{heading.subtitle}</p>}
      </div>

      {/* 统计条 */}
      {statSection && <StatStrip section={statSection} />}

      {/* 核心理由 */}
      {reasonSection && <KeyReasons section={reasonSection} />}

      {/* 正文 */}
      {textSection && (
        <div className="mb-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-xs text-gray-700 leading-relaxed">
            {typeof textSection.content === "string"
              ? textSection.content
              : (textSection.content as unknown as { text?: string })?.text ?? ""}
          </p>
        </div>
      )}

      {/* 风险提示 */}
      {riskSection && (
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
          <p className="text-xs font-semibold text-amber-800 mb-1">⚠️ 注意事项</p>
          <p className="text-xs text-amber-700 leading-relaxed">
            {typeof riskSection.content === "string"
              ? riskSection.content
              : (riskSection.content as unknown as { description?: string })?.description ?? ""}
          </p>
        </div>
      )}
    </PageShell>
  )
}
