/**
 * RouteOverviewPage.tsx — 大路线总览（L3-08）
 */
import React from "react"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import PageShell from "../PageShell"
import type { PageViewModel } from "@/lib/report/types"

interface Props {
  vm: PageViewModel
  mode?: "screen" | "print"
}

const INTENSITY_STYLE: Record<string, string> = {
  light:    "bg-green-50 text-green-700 border-green-200",
  balanced: "bg-blue-50 text-blue-700 border-blue-200",
  dense:    "bg-orange-50 text-orange-700 border-orange-200",
}
const INTENSITY_LABEL: Record<string, string> = {
  light: "轻松", balanced: "均衡", dense: "偏满",
}

export default function RouteOverviewPage({ vm, mode = "screen" }: Props) {
  const timelineContent = vm.sections.find((s) => s.section_type === "timeline")?.content as
    | { type: "timeline"; items: Array<{ time: string; name: string; type_icon: string; duration: string; note: string }> }
    | undefined

  const items = timelineContent?.items ?? []

  return (
    <PageShell mode={mode} pageSize="full" pageNumber={vm.heading.page_number} chapterTitle="行程概览">
      <div className="mb-5">
        <h2 className="text-xl font-bold text-zinc-900">{vm.heading.title}</h2>
        {vm.heading.subtitle && <p className="text-xs text-zinc-500 mt-1">{vm.heading.subtitle}</p>}
        <Separator className="mt-3" />
      </div>

      {/* 路线 Timeline */}
      <ol className="space-y-2">
        {items.map((item, idx) => (
          <li key={idx} className="flex items-start gap-3">
            <div className="flex flex-col items-center">
              <div className="w-2 h-2 rounded-full bg-rose-400 mt-1.5 shrink-0" />
              {idx < items.length - 1 && (
                <div className="w-[1px] h-4 bg-zinc-200 mt-1" />
              )}
            </div>
            <div className="flex-1 pb-1">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-zinc-800">{item.name}</span>
                {item.note && (
                  <Badge variant="outline" className={`text-[10px] ${INTENSITY_STYLE[item.type_icon] ?? "border-zinc-200"}`}>
                    {INTENSITY_LABEL[item.type_icon] ?? item.note}
                  </Badge>
                )}
              </div>
              {item.time && (
                <span className="text-[10px] text-zinc-400">{item.time}</span>
              )}
            </div>
          </li>
        ))}
        {items.length === 0 && (
          <p className="text-sm text-zinc-400">路线数据加载中…</p>
        )}
      </ol>
    </PageShell>
  )
}
