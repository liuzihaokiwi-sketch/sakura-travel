/**
 * HotelStrategyPage.tsx — 酒店策略总览（L3-08）
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

export default function HotelStrategyPage({ vm, mode = "screen" }: Props) {
  const entityCards = vm.sections
    .filter((s) => s.section_type === "entity_card")
    .map((s) => s.content as {
      type: "entity_card"
      entity_id: string; name: string; entity_type: string
      hero_image?: string; tagline: string
      stats: Array<{ label: string; value: string; unit: string }>
    })

  const textBlock = vm.sections.find((s) => s.section_type === "text_block")?.content as
    | { type: "text_block"; text: string; items?: string[] }
    | undefined

  return (
    <PageShell mode={mode} pageSize="full" pageNumber={vm.heading.page_number} chapterTitle="行程概览">
      <div className="mb-5">
        <h2 className="text-xl font-bold text-zinc-900">{vm.heading.title}</h2>
        {vm.heading.subtitle && <p className="text-xs text-zinc-500 mt-1">{vm.heading.subtitle}</p>}
        <Separator className="mt-3" />
      </div>

      {/* 策略说明 */}
      {textBlock?.text && (
        <p className="text-sm text-zinc-600 mb-4 leading-relaxed">{textBlock.text}</p>
      )}
      {textBlock?.items && textBlock.items.length > 0 && (
        <ul className="mb-4 space-y-1">
          {textBlock.items.map((item, i) => (
            <li key={i} className="flex gap-2 text-sm text-zinc-700">
              <span className="text-rose-400 shrink-0">·</span>
              {item}
            </li>
          ))}
        </ul>
      )}

      {/* 酒店卡片 */}
      <div className="space-y-3">
        {entityCards.map((card) => (
          <Card key={card.entity_id} className="border border-zinc-100">
            <CardContent className="p-3 flex gap-3">
              {card.hero_image ? (
                <div className="relative w-16 h-16 rounded overflow-hidden shrink-0 bg-zinc-100">
                  <Image src={card.hero_image} alt={card.name} fill className="object-cover" />
                </div>
              ) : (
                <div className="w-16 h-16 rounded bg-gradient-to-br from-amber-50 to-orange-100 flex items-center justify-center shrink-0">
                  <span className="text-xl">🏨</span>
                </div>
              )}
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-sm text-zinc-900 truncate">{card.name}</p>
                {card.tagline && (
                  <p className="text-xs text-zinc-500 mt-0.5 line-clamp-2">{card.tagline}</p>
                )}
                {card.stats.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap gap-2">
                    {card.stats.slice(0, 3).map((s) => (
                      <Badge key={s.label} variant="outline" className="text-[9px] text-zinc-500 border-zinc-200">
                        {s.label}: {s.value}{s.unit}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
        {entityCards.length === 0 && (
          <p className="text-sm text-zinc-400">酒店策略数据生成中…</p>
        )}
      </div>
    </PageShell>
  )
}
