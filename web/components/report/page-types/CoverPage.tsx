/**
 * CoverPage.tsx — 封面页（L3-08）
 *
 * 区域：hero_zone（大图）+ heading（行程标题）+ stat_strip（基本信息）
 * 数据源：PageViewModel props，不自行 fetch
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

export default function CoverPage({ vm, mode = "screen" }: Props) {
  const stats =
    vm.sections
      .find((s) => s.section_type === "stat_strip")
      ?.content as { type: "stat_strip"; stats: Array<{ label: string; value: string; unit: string }> } | undefined

  return (
    <PageShell
      mode={mode}
      pageSize="full"
      pageNumber={vm.heading.page_number}
    >
      {/* ── Hero Zone ──────────────────────────────────────────────────── */}
      <div className="relative -mx-10 -mt-4 h-[55mm] overflow-hidden bg-zinc-100">
        {vm.hero?.image_url ? (
          <Image
            src={vm.hero.image_url}
            alt={vm.hero.image_alt || vm.heading.title}
            fill
            className="object-cover"
            priority
          />
        ) : (
          <div className="flex h-full items-center justify-center bg-gradient-to-br from-pink-50 to-rose-100">
            <span className="text-4xl">🌸</span>
          </div>
        )}
        {/* 渐变遮罩 */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
        {/* 品牌标识 */}
        <span className="absolute top-4 left-6 text-xs text-white/70 tracking-widest uppercase">
          Sakura Rush
        </span>
      </div>

      {/* ── Heading Zone ──────────────────────────────────────────────── */}
      <div className="mt-6 space-y-1">
        <h1 className="text-3xl font-bold text-zinc-900 leading-tight">
          {vm.heading.title}
        </h1>
        {vm.heading.subtitle && (
          <p className="text-sm text-zinc-500">{vm.heading.subtitle}</p>
        )}
      </div>

      <Separator className="my-5" />

      {/* ── Stat Strip ────────────────────────────────────────────────── */}
      {stats?.stats && stats.stats.length > 0 && (
        <div className="flex flex-wrap gap-4">
          {stats.stats.map((s) => (
            <div key={s.label} className="flex flex-col">
              <span className="text-[10px] text-zinc-400 uppercase tracking-wider">
                {s.label}
              </span>
              <span className="text-base font-semibold text-zinc-800">
                {s.value}
                {s.unit && (
                  <span className="text-xs font-normal text-zinc-500 ml-0.5">
                    {s.unit}
                  </span>
                )}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* ── 底部装饰 ───────────────────────────────────────────────────── */}
      <div className="mt-auto pt-10 text-[9px] text-zinc-300 text-right">
        AI 生成 · 仅供参考，以官方信息为准
      </div>
    </PageShell>
  )
}
