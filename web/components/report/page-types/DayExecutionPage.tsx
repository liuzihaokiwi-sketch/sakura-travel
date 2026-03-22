/**
 * DayExecutionPage.tsx — 每日执行页（L3-09）
 *
 * 展示：日期标签 + 情绪目标 + 时间轴 + 风险提示 + 强度标识
 */
import React from "react"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import PageShell from "../PageShell"
import type { PageViewModel } from "@/lib/report/types"

interface Props {
  vm: PageViewModel
  mode?: "screen" | "print"
}

const TYPE_ICON: Record<string, string> = {
  poi:        "🏛️",
  restaurant: "🍜",
  hotel:      "🏨",
  activity:   "🎯",
  transit:    "🚃",
  buffer:     "☕",
}

const INTENSITY_CONFIG: Record<string, { label: string; className: string }> = {
  light:    { label: "轻松", className: "bg-green-50 text-green-700 border-green-200" },
  balanced: { label: "均衡", className: "bg-blue-50 text-blue-700 border-blue-200" },
  dense:    { label: "偏满", className: "bg-orange-50 text-orange-700 border-orange-200" },
}

export default function DayExecutionPage({ vm, mode = "screen" }: Props) {
  const timelineContent = vm.sections.find((s) => s.section_type === "timeline")?.content as
    | { type: "timeline"; items: Array<{ time: string; name: string; type_icon: string; duration: string; note: string; entity_id?: string }> }
    | undefined

  const textBlock = vm.sections.find((s) => s.section_type === "text_block")?.content as
    | { type: "text_block"; text: string }
    | undefined

  const riskCards = vm.sections
    .filter((s) => s.section_type === "risk_card")
    .map((s) => s.content as { type: "risk_card"; risk_type: string; severity: string; description: string; action?: string })

  const intensityFromSubtitle = vm.heading.subtitle?.match(/节奏：(.+)/)?.[1] ?? "均衡"
  const intensityKey =
    intensityFromSubtitle === "轻松" ? "light"
    : intensityFromSubtitle === "偏满" ? "dense"
    : "balanced"
  const intensityCfg = INTENSITY_CONFIG[intensityKey]

  const timelineItems = timelineContent?.items ?? []

  return (
    <PageShell
      mode={mode}
      pageSize="full"
      pageNumber={vm.heading.page_number}
      chapterTitle={vm.chapter_id?.replace("ch_", "") ?? undefined}
    >
      {/* ── Heading Zone ──────────────────────────────────────────────── */}
      <div className="flex items-start justify-between mb-1">
        <div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-[10px] font-bold text-rose-600 border-rose-200 bg-rose-50">
              Day {vm.day_index}
            </Badge>
            <Badge variant="outline" className={`text-[10px] ${intensityCfg.className}`}>
              {intensityCfg.label}
            </Badge>
          </div>
          <h2 className="text-lg font-bold text-zinc-900 mt-1">{vm.heading.title}</h2>
          {vm.heading.subtitle && (
            <p className="text-xs text-zinc-500 mt-0.5">{vm.heading.subtitle}</p>
          )}
        </div>
      </div>

      {/* ── 情绪目标 ──────────────────────────────────────────────────── */}
      {textBlock?.text && (
        <p className="text-xs text-zinc-500 italic border-l-2 border-rose-200 pl-3 mb-3 mt-2">
          {textBlock.text}
        </p>
      )}

      <Separator className="mb-3" />

      {/* ── Timeline 时间轴 ───────────────────────────────────────────── */}
      <ol className="space-y-2.5">
        {timelineItems.map((item, idx) => (
          <li key={idx} className="flex gap-3">
            {/* 时间轴线 */}
            <div className="flex flex-col items-center w-4 shrink-0">
              <div className="w-2 h-2 rounded-full bg-rose-300 mt-1 shrink-0" />
              {idx < timelineItems.length - 1 && (
                <div className="w-[1px] flex-1 bg-zinc-100 mt-1" />
              )}
            </div>

            {/* 内容 */}
            <div className="flex-1 pb-1">
              <div className="flex items-start gap-1.5">
                <span className="text-sm" aria-hidden>
                  {TYPE_ICON[item.type_icon] ?? "📍"}
                </span>
                <div className="flex-1">
                  <div className="flex items-baseline justify-between">
                    <span className="text-sm font-medium text-zinc-800">{item.name}</span>
                    {item.time && (
                      <span className="text-[10px] text-zinc-400 tabular-nums shrink-0 ml-2">
                        {item.time}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 mt-0.5">
                    {item.duration && (
                      <span className="text-[10px] text-zinc-400">{item.duration}</span>
                    )}
                    {item.note && item.note !== item.name && (
                      <span className="text-[10px] text-zinc-400">{item.note}</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </li>
        ))}
        {timelineItems.length === 0 && (
          <li className="text-sm text-zinc-400">行程数据加载中…</li>
        )}
      </ol>

      {/* ── 风险提示 ──────────────────────────────────────────────────── */}
      {riskCards.length > 0 && (
        <div className="mt-4 space-y-2">
          <Separator />
          {riskCards.map((risk, i) => (
            <Card key={i} className="border-orange-100 bg-orange-50">
              <CardContent className="p-3">
                <p className="text-xs font-medium text-orange-700">
                  ⚠️ {risk.description}
                </p>
                {risk.action && (
                  <p className="text-[10px] text-orange-600 mt-0.5">{risk.action}</p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </PageShell>
  )
}
