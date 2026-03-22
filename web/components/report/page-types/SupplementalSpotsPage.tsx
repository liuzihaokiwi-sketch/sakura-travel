/**
 * SupplementalSpotsPage.tsx — 补充景点页（supplemental_spots）
 *
 * 页型：appendix / half 页（可与 photo_theme_detail / transit_detail 合并）
 * 作用：展示行程中未列入主线的备选景点和周边便利信息（便利店/药店/超市）。
 */
"use client"

import { cn } from "@/lib/utils"
import type { PageViewModel } from "@/lib/report/types"
import PageShell from "../PageShell"

interface SpotCard {
  entity_id?: string
  name: string
  entity_type: string       // "poi" | "shop" | "convenience"
  area?: string
  distance_from_hotel?: string
  why_worth_it?: string
  tags?: string[]
  rating?: number
}

interface EntityCardContent {
  spots: SpotCard[]
}

const TYPE_ICON: Record<string, string> = {
  poi:         "🏛️",
  shop:        "🛍️",
  convenience: "🏪",
  cafe:        "☕",
  park:        "🌿",
}

function SpotRow({ spot }: { spot: SpotCard }) {
  return (
    <div className="flex items-start gap-2.5 py-2 border-b border-gray-100 last:border-0">
      <span className="text-base flex-shrink-0 mt-0.5">
        {TYPE_ICON[spot.entity_type] ?? "📍"}
      </span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 flex-wrap">
          <p className="text-xs font-semibold text-gray-900">{spot.name}</p>
          {spot.area && (
            <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-gray-100 text-gray-500">
              {spot.area}
            </span>
          )}
          {spot.rating != null && (
            <span className="text-[10px] text-amber-500 font-medium">★ {spot.rating}</span>
          )}
        </div>
        {spot.distance_from_hotel && (
          <p className="text-[11px] text-gray-400 mt-0.5">距酒店 {spot.distance_from_hotel}</p>
        )}
        {spot.why_worth_it && (
          <p className="text-[11px] text-gray-600 mt-0.5 leading-snug">{spot.why_worth_it}</p>
        )}
        {spot.tags && spot.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1">
            {spot.tags.map((tag, i) => (
              <span key={i} className="text-[10px] px-1 py-0.5 rounded bg-blue-50 text-blue-600">
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

interface SupplementalSpotsPageProps extends PageViewModel {
  mode?: "screen" | "print"
}

export default function SupplementalSpotsPage(props: SupplementalSpotsPageProps) {
  const { heading, sections, footer, mode = "screen" } = props
  const entitySection = sections.find((s) => s.section_type === "entity_card")
  const textSection   = sections.find((s) => s.section_type === "text_block")

  const spots = (entitySection?.content as EntityCardContent)?.spots ?? []

  return (
    <PageShell mode={mode} footer={footer} compact>
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xl">📌</span>
        <div>
          <h2 className="text-base font-bold text-gray-900">{heading.title}</h2>
          {heading.subtitle && <p className="text-xs text-gray-500">{heading.subtitle}</p>}
        </div>
      </div>

      {spots.length > 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 px-3">
          {spots.map((spot, i) => (
            <SpotRow key={spot.entity_id ?? i} spot={spot} />
          ))}
        </div>
      ) : (
        <p className="text-xs text-gray-400 text-center py-6">暂无补充景点</p>
      )}

      {textSection && (
        <div className="mt-3 p-2.5 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-xs text-gray-600 leading-relaxed">
            {typeof textSection.content === "string"
              ? textSection.content
              : (textSection.content as { text?: string })?.text ?? ""}
          </p>
        </div>
      )}
    </PageShell>
  )
}
