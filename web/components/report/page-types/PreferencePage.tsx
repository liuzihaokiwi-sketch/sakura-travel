/**
 * PreferencePage.tsx — 偏好兑现页（L3-08）
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

const FULFILLMENT_COLORS: Record<string, string> = {
  fully_met:     "bg-green-50 text-green-700 border-green-200",
  partially_met: "bg-yellow-50 text-yellow-700 border-yellow-200",
  traded_off:    "bg-orange-50 text-orange-700 border-orange-200",
  not_applicable:"bg-zinc-50 text-zinc-500 border-zinc-200",
}

const FULFILLMENT_LABEL: Record<string, string> = {
  fully_met:     "✅ 完全满足",
  partially_met: "🔶 部分满足",
  traded_off:    "🔄 做了取舍",
  not_applicable:"— 不适用",
}

export default function PreferencePage({ vm, mode = "screen" }: Props) {
  const fulfillmentContent = vm.sections.find((s) => s.section_type === "fulfillment_list")?.content as
    | { type: "fulfillment_list"; items: Array<{ preference_text: string; fulfillment_type: string; evidence: string; explanation: string }> }
    | undefined

  const items = fulfillmentContent?.items ?? []

  return (
    <PageShell mode={mode} pageSize="full" pageNumber={vm.heading.page_number} chapterTitle="行程概览">
      {/* ── Heading Zone ──────────────────────────────────────────────── */}
      <div className="mb-5">
        <h2 className="text-xl font-bold text-zinc-900">{vm.heading.title}</h2>
        {vm.heading.subtitle && (
          <p className="text-xs text-zinc-500 mt-1">{vm.heading.subtitle}</p>
        )}
        <Separator className="mt-3" />
      </div>

      {/* ── Fulfillment List ──────────────────────────────────────────── */}
      <div className="space-y-3">
        {items.map((item, idx) => (
          <Card key={idx} className={`border ${FULFILLMENT_COLORS[item.fulfillment_type] ?? "border-zinc-200"}`}>
            <CardContent className="p-4">
              <div className="flex items-start justify-between gap-3">
                <p className="text-sm font-medium text-zinc-800 flex-1">
                  {item.preference_text}
                </p>
                <Badge
                  variant="outline"
                  className={`shrink-0 text-[10px] ${FULFILLMENT_COLORS[item.fulfillment_type] ?? ""}`}
                >
                  {FULFILLMENT_LABEL[item.fulfillment_type] ?? item.fulfillment_type}
                </Badge>
              </div>
              {item.evidence && (
                <p className="mt-2 text-xs text-zinc-600 leading-relaxed">
                  <span className="text-zinc-400">兑现方式：</span>
                  {item.evidence}
                </p>
              )}
              {item.explanation && (
                <p className="mt-1 text-xs text-zinc-400 italic">{item.explanation}</p>
              )}
            </CardContent>
          </Card>
        ))}
        {items.length === 0 && (
          <p className="text-sm text-zinc-400">暂无偏好兑现数据</p>
        )}
      </div>
    </PageShell>
  )
}
