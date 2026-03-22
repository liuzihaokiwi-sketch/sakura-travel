/**
 * ChapterOpenerPage.tsx — 章节 opener 页（L3-12）
 *
 * 城市圈名称 + 大图 hero + chapter goal + mood + covered_days 概览
 */
import React from "react"
import Image from "next/image"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import PageShell from "../PageShell"
import type { PageViewModel } from "@/lib/report/types"

interface Props {
  vm: PageViewModel
  mode?: "screen" | "print"
}

export default function ChapterOpenerPage({ vm, mode = "screen" }: Props) {
  const textBlock = vm.sections.find((s) => s.section_type === "text_block")?.content as
    | { type: "text_block"; text: string; items?: string[] } | undefined

  const highlights = vm.sections
    .filter((s) => s.section_type === "entity_card")
    .slice(0, 3)
    .map((s) => s.content as { type: "entity_card"; name: string; tagline: string })

  return (
    <PageShell mode={mode} pageSize="full" pageNumber={vm.heading.page_number}>
      {/* ── Hero Zone（大图，占页面约 55%）──────────────────────────── */}
      <div className="relative -mx-10 -mt-4 h-[65mm] overflow-hidden bg-zinc-100">
        {vm.hero?.image_url ? (
          <Image
            src={vm.hero.image_url}
            alt={vm.hero.image_alt || vm.heading.title}
            fill
            className="object-cover"
            priority
          />
        ) : (
          <div className="flex h-full items-center justify-center bg-gradient-to-br from-rose-50 to-pink-100">
            <span className="text-5xl">🗺️</span>
          </div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/10 to-transparent" />

        {/* 章节标题叠加在图片上 */}
        <div className="absolute bottom-4 left-6 right-6">
          <p className="text-[9px] text-white/60 uppercase tracking-widest mb-0.5">
            {vm.chapter_id?.replace("ch_", "").toUpperCase() ?? "CHAPTER"}
          </p>
          <h2 className="text-2xl font-bold text-white leading-tight">
            {vm.heading.title}
          </h2>
          {vm.heading.subtitle && (
            <p className="text-xs text-white/70 mt-0.5">{vm.heading.subtitle}</p>
          )}
        </div>
      </div>

      {/* ── Goal & Mood ───────────────────────────────────────────────── */}
      {textBlock?.text && (
        <div className="mt-4 mb-3">
          <p className="text-sm text-zinc-600 leading-relaxed italic">
            {textBlock.text}
          </p>
          {textBlock.items && textBlock.items.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {textBlock.items.map((kw, i) => (
                <Badge key={i} variant="secondary" className="text-[10px]">{kw}</Badge>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── 本章亮点预览 ──────────────────────────────────────────────── */}
      {highlights.length > 0 && (
        <>
          <Separator className="my-3" />
          <p className="text-[9px] text-zinc-400 uppercase tracking-wider mb-2">本章节亮点</p>
          <ul className="space-y-1.5">
            {highlights.map((h, i) => (
              <li key={i} className="flex gap-2 items-baseline">
                <span className="text-rose-400 text-xs shrink-0">★</span>
                <div>
                  <span className="text-sm font-medium text-zinc-800">{h.name}</span>
                  {h.tagline && (
                    <span className="text-xs text-zinc-500 ml-1.5">{h.tagline}</span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </>
      )}
    </PageShell>
  )
}
