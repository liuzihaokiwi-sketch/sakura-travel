/**
 * HotelDetailPage.tsx — 酒店详情页（L3-10）
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

export default function HotelDetailPage({ vm, mode = "screen" }: Props) {
  const keyReasons = vm.sections.find((s) => s.section_type === "key_reasons")?.content as
    | { type: "key_reasons"; reasons: string[] } | undefined

  const statStrip = vm.sections.find((s) => s.section_type === "stat_strip")?.content as
    | { type: "stat_strip"; stats: Array<{ label: string; value: string; unit: string }> } | undefined

  return (
    <PageShell mode={mode} pageSize="full" pageNumber={vm.heading.page_number} chapterTitle="酒店">
      {/* ── Hero Zone ──────────────────────────────────────────────────── */}
      <div className="relative -mx-10 -mt-4 h-[40mm] overflow-hidden bg-zinc-100">
        {vm.hero?.image_url ? (
          <Image src={vm.hero.image_url} alt={vm.hero.image_alt || vm.heading.title} fill className="object-cover" />
        ) : (
          <div className="flex h-full items-center justify-center bg-gradient-to-br from-amber-50 to-orange-100">
            <span className="text-4xl">🏨</span>
          </div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
      </div>

      {/* ── Heading ───────────────────────────────────────────────────── */}
      <div className="mt-4 mb-3">
        <h2 className="text-xl font-bold text-zinc-900">{vm.heading.title}</h2>
        {vm.heading.subtitle && <p className="text-xs text-zinc-500 mt-0.5">{vm.heading.subtitle}</p>}
      </div>

      <Separator className="mb-4" />

      {/* ── Why Selected ──────────────────────────────────────────────── */}
      {keyReasons && keyReasons.reasons.length > 0 && (
        <div className="mb-4">
          <p className="text-[10px] text-zinc-400 uppercase tracking-wider mb-2">为什么选这里</p>
          <ul className="space-y-1">
            {keyReasons.reasons.map((r, i) => (
              <li key={i} className="flex gap-2 text-sm text-zinc-700">
                <span className="text-amber-400 shrink-0">◆</span>
                {r}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ── Stat Strip ────────────────────────────────────────────────── */}
      {statStrip && statStrip.stats.length > 0 && (
        <div className="grid grid-cols-2 gap-3">
          {statStrip.stats.map((s) => (
            <div key={s.label} className="bg-zinc-50 rounded p-2.5">
              <p className="text-[9px] text-zinc-400 uppercase tracking-wider">{s.label}</p>
              <p className="text-sm font-semibold text-zinc-800 mt-0.5">
                {s.value}
                {s.unit && <span className="text-xs font-normal text-zinc-500 ml-0.5">{s.unit}</span>}
              </p>
            </div>
          ))}
        </div>
      )}
    </PageShell>
  )
}
