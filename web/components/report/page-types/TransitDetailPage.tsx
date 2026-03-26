/**
 * TransitDetailPage.tsx — 交通详情页（transit_detail）
 *
 * 页型：detail / half 页（可与 supplemental_spots 合并为 dual-half）
 * 作用：复杂交通日的换乘指南，包括乘车节点、时刻表关键点、票种建议。
 */
"use client"

import type { PageViewModel } from "@/lib/report/types"
import PageShell from "../PageShell"

interface TransitStep {
  step: number
  time?: string
  mode: string        // "train" | "bus" | "walk" | "taxi" | "subway"
  description: string
  notes?: string
  duration_mins?: number
}

interface TransitTimelineContent {
  steps: TransitStep[]
  total_duration_mins?: number
}

interface StatItem { label: string; value: string }
interface StatStripContent { stats: StatItem[] }

const MODE_ICON: Record<string, string> = {
  train:  "🚄",
  subway: "🚇",
  bus:    "🚌",
  walk:   "🚶",
  taxi:   "🚕",
  ferry:  "⛴️",
}

function TransitStep({ step }: { step: TransitStep }) {
  return (
    <div className="flex items-start gap-2.5 relative">
      {/* 连接线 */}
      <div className="flex flex-col items-center">
        <div className="w-7 h-7 rounded-full bg-blue-100 border-2 border-blue-300 flex items-center justify-center text-sm flex-shrink-0 z-10">
          {MODE_ICON[step.mode] ?? "📍"}
        </div>
      </div>
      <div className="flex-1 pb-3">
        <div className="flex items-center gap-2">
          {step.time && <span className="text-[11px] font-bold text-blue-600">{step.time}</span>}
          <p className="text-xs font-semibold text-gray-900">{step.description}</p>
          {step.duration_mins && (
            <span className="ml-auto text-[10px] text-gray-400">{step.duration_mins}min</span>
          )}
        </div>
        {step.notes && <p className="text-[11px] text-gray-500 mt-0.5">{step.notes}</p>}
      </div>
    </div>
  )
}

interface TransitDetailPageProps {
  vm: PageViewModel
  mode?: "screen" | "print"
}

export default function TransitDetailPage(props: TransitDetailPageProps) {
  const { vm, mode = "screen" } = props
  const { heading, sections, footer } = vm
  const timelineSection = sections.find((s) => s.section_type === "transit_timeline" || s.section_type === "timeline")
  const statSection     = sections.find((s) => s.section_type === "stat_strip")
  const textSection     = sections.find((s) => s.section_type === "text_block")

  const timeline = timelineSection?.content as unknown as TransitTimelineContent | null
  const stats    = (statSection?.content as unknown as StatStripContent)?.stats ?? []

  return (
    <PageShell mode={mode} footer={footer} compact>
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xl">🚄</span>
        <div>
          <h2 className="text-base font-bold text-gray-900">{heading.title}</h2>
          {heading.subtitle && <p className="text-xs text-gray-500">{heading.subtitle}</p>}
        </div>
      </div>

      {/* 统计条 */}
      {stats.length > 0 && (
        <div className="grid grid-cols-3 gap-2 mb-3">
          {stats.map((s, i) => (
            <div key={i} className="bg-blue-50 rounded-lg p-2 text-center border border-blue-100">
              <p className="text-sm font-bold text-blue-700">{s.value}</p>
              <p className="text-[10px] text-blue-500">{s.label}</p>
            </div>
          ))}
        </div>
      )}

      {/* 换乘步骤 */}
      {timeline?.steps && (
        <div className="relative">
          {/* 竖线 */}
          <div className="absolute left-3.5 top-7 bottom-3 w-0.5 bg-blue-100" />
          <div className="space-y-0">
            {timeline.steps.map((step) => (
              <TransitStep key={step.step} step={step} />
            ))}
          </div>
          {timeline.total_duration_mins && (
            <p className="text-xs text-gray-400 mt-1 pl-9">
              全程约 {timeline.total_duration_mins} 分钟
            </p>
          )}
        </div>
      )}

      {textSection && (
        <div className="mt-3 p-2.5 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-xs text-gray-600 leading-relaxed">
            {typeof textSection.content === "string"
              ? textSection.content
              : (textSection.content as unknown as { text?: string })?.text ?? ""}
          </p>
        </div>
      )}
    </PageShell>
  )
}
