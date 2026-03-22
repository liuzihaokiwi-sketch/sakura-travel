/**
 * RestaurantDetailPage.tsx — 餐厅详情页（L3-11）
 */
import React from "react"
import Image from "next/image"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import PageShell from "../PageShell"
import type { PageViewModel } from "@/lib/report/types"

interface Props {
  vm: PageViewModel
  mode?: "screen" | "print"
}

export default function RestaurantDetailPage({ vm, mode = "screen" }: Props) {
  const keyReasons = vm.sections.find((s) => s.section_type === "key_reasons")?.content as
    | { type: "key_reasons"; reasons: string[] } | undefined

  const statStrip = vm.sections.find((s) => s.section_type === "stat_strip")?.content as
    | { type: "stat_strip"; stats: Array<{ label: string; value: string; unit: string }> } | undefined

  const riskCard = vm.sections.find((s) => s.section_type === "risk_card")?.content as
    | { type: "risk_card"; risk_type: string; severity: string; description: string; action?: string } | undefined

  const pageSize = vm.page_size

  return (
    <PageShell
      mode={mode}
      pageSize={pageSize}
      pageNumber={vm.heading.page_number}
      chapterTitle="餐厅"
    >
      {/* ── Hero Zone ──────────────────────────────────────────────────── */}
      <div className={`relative -mx-10 -mt-4 overflow-hidden bg-zinc-100 ${pageSize === "full" ? "h-[35mm]" : "h-[20mm]"}`}>
        {vm.hero?.image_url ? (
          <Image src={vm.hero.image_url} alt={vm.hero.image_alt || vm.heading.title} fill className="object-cover" />
        ) : (
          <div className="flex h-full items-center justify-center bg-gradient-to-br from-red-50 to-orange-100">
            <span className="text-4xl">🍜</span>
          </div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
      </div>

      {/* ── Heading ───────────────────────────────────────────────────── */}
      <div className="mt-3 mb-2">
        <h2 className={`font-bold text-zinc-900 ${pageSize === "full" ? "text-xl" : "text-base"}`}>
          {vm.heading.title}
        </h2>
      </div>

      {pageSize === "full" && <Separator className="mb-3" />}

      {/* ── Stat Strip ────────────────────────────────────────────────── */}
      {statStrip && statStrip.stats.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3">
          {statStrip.stats.map((s) => (
            <Badge key={s.label} variant="outline" className="text-[10px] text-zinc-600 border-zinc-200">
              {s.label}：{s.value}{s.unit}
            </Badge>
          ))}
        </div>
      )}

      {/* ── Why Selected ──────────────────────────────────────────────── */}
      {keyReasons && keyReasons.reasons.length > 0 && (
        <div className="mb-3">
          {pageSize === "full" && (
            <p className="text-[10px] text-zinc-400 uppercase tracking-wider mb-1">为什么推荐</p>
          )}
          <ul className="space-y-1">
            {keyReasons.reasons.slice(0, pageSize === "full" ? 5 : 2).map((r, i) => (
              <li key={i} className="flex gap-1.5 text-xs text-zinc-700">
                <span className="text-rose-400 shrink-0">·</span>
                {r}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ── 预约提示 ──────────────────────────────────────────────────── */}
      {riskCard && (
        <Card className="border-orange-100 bg-orange-50 mt-2">
          <CardContent className="p-2.5">
            <p className="text-xs font-medium text-orange-700">
              📅 {riskCard.description}
            </p>
          </CardContent>
        </Card>
      )}
    </PageShell>
  )
}
