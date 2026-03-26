/**
 * PhotoThemeDetailPage.tsx — 拍摄主题详情页（photo_theme_detail）
 *
 * 页型：detail / half 页（可与 supplemental_spots 合并为 dual-half）
 * 作用：针对一个拍摄地点，提供最佳机位、光线时机、构图建议。
 */
"use client"

import type { PageViewModel, SectionVM } from "@/lib/report/types"
import PageShell from "../PageShell"

interface PhotoTip {
  icon?: string
  label: string
  tip: string
}

interface PhotoTipsContent {
  tips: PhotoTip[]
}

function PhotoTipRow({ tip }: { tip: PhotoTip }) {
  return (
    <div className="flex items-start gap-2 py-1.5 border-b border-gray-100 last:border-0">
      <span className="text-base flex-shrink-0">{tip.icon ?? "📷"}</span>
      <div>
        <p className="text-xs font-semibold text-gray-800">{tip.label}</p>
        <p className="text-xs text-gray-500 leading-relaxed">{tip.tip}</p>
      </div>
    </div>
  )
}

interface PhotoThemeDetailPageProps {
  vm: PageViewModel
  mode?: "screen" | "print"
}

export default function PhotoThemeDetailPage(props: PhotoThemeDetailPageProps) {
  const { vm, mode = "screen" } = props
  const { heading, hero, sections, footer } = vm
  const tipsSection = sections.find((s) => s.section_type === "photo_tips" || s.section_type === "key_reasons")
  const textSection = sections.find((s) => s.section_type === "text_block")

  return (
    <PageShell mode={mode} footer={footer} compact>
      {/* Hero */}
      {hero?.image_url && (
        <div className="relative h-36 rounded-xl overflow-hidden mb-3">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={hero.image_url} alt={hero.image_alt ?? ""} className="w-full h-full object-cover" />
          <div className="absolute top-2 left-2">
            <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-black/60 text-white">📸 出片圣地</span>
          </div>
        </div>
      )}

      <h2 className="text-base font-bold text-gray-900 mb-1">{heading.title}</h2>
      {heading.subtitle && <p className="text-xs text-gray-500 mb-3">{heading.subtitle}</p>}

      {tipsSection && (
        <div className="bg-white rounded-lg border border-gray-200 px-3 mb-3">
          {(tipsSection.content as unknown as PhotoTipsContent)?.tips?.map((t, i) => (
            <PhotoTipRow key={i} tip={t} />
          ))}
        </div>
      )}

      {textSection && (
        <p className="text-xs text-gray-600 leading-relaxed">
          {typeof textSection.content === "string"
            ? textSection.content
            : (textSection.content as unknown as { text?: string })?.text ?? ""}
        </p>
      )}
    </PageShell>
  )
}
