/**
 * MajorActivityOverviewPage.tsx — 主要活动总表（L3-08）
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

export default function MajorActivityOverviewPage({ vm, mode = "screen" }: Props) {
  const entityCards = vm.sections
    .filter((s) => s.section_type === "entity_card")
    .map((s) => s.content as {
      type: "entity_card"
      entity_id: string; name: string; entity_type: string
      hero_image?: string; tagline: string
      stats: Array<{ label: string; value: string; unit: string }>
    })

  return (
    <PageShell mode={mode} pageSize="full" pageNumber={vm.heading.page_number} chapterTitle="行程概览">
      <div className="mb-5">
        <h2 className="text-xl font-bold text-zinc-900">{vm.heading.title}</h2>
        {vm.heading.subtitle && <p className="text-xs text-zinc-500 mt-1">{vm.heading.subtitle}</p>}
        <Separator className="mt-3" />
      </div>

      <div className="grid grid-cols-2 gap-3">
        {entityCards.map((card) => (
          <Card key={card.entity_id} className="border border-zinc-100 overflow-hidden">
            {card.hero_image ? (
              <div className="relative h-20 bg-zinc-100">
                <Image src={card.hero_image} alt={card.name} fill className="object-cover" />
              </div>
            ) : (
              <div className="h-20 bg-gradient-to-br from-pink-50 to-rose-100 flex items-center justify-center">
                <span className="text-2xl">{card.entity_type === "restaurant" ? "🍜" : "🏛️"}</span>
              </div>
            )}
            <CardContent className="p-3">
              <p className="font-semibold text-sm text-zinc-900 truncate">{card.name}</p>
              {card.tagline && <p className="text-xs text-zinc-500 mt-0.5 line-clamp-2">{card.tagline}</p>}
            </CardContent>
          </Card>
        ))}
        {entityCards.length === 0 && (
          <p className="text-sm text-zinc-400 col-span-2">暂无主要活动数据</p>
        )}
      </div>
    </PageShell>
  )
}
