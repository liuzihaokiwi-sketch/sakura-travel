/**
 * TocPage.tsx — 目录页（L3-08）
 *
 * screen 模式支持 anchor 跳转；print 模式仅显示文字页码。
 */
import React from "react"
import { Separator } from "@/components/ui/separator"
import PageShell from "../PageShell"
import type { PageViewModel } from "@/lib/report/types"

interface Props {
  vm: PageViewModel
  mode?: "screen" | "print"
}

const FAMILY_LABEL: Record<string, string> = {
  frontmatter: "概览",
  chapter: "章节",
  daily: "行程",
  detail: "详情",
  appendix: "附录",
}

export default function TocPage({ vm, mode = "screen" }: Props) {
  const tocContent = vm.sections.find((s) => s.section_type === "toc_list")?.content as
    | { type: "toc_list"; entries: Array<{ title: string; page_number: number; chapter_id: string; page_type: string }> }
    | undefined

  const entries = tocContent?.entries ?? []

  // 按 chapter_id 分组
  const grouped: Record<string, typeof entries> = {}
  entries.forEach((e) => {
    const key = e.chapter_id ?? "other"
    if (!grouped[key]) grouped[key] = []
    grouped[key].push(e)
  })

  return (
    <PageShell mode={mode} pageSize="full" pageNumber={vm.heading.page_number}>
      {/* ── Heading Zone ──────────────────────────────────────────────── */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-zinc-900">{vm.heading.title}</h2>
        <Separator className="mt-3" />
      </div>

      {/* ── TOC 列表 ──────────────────────────────────────────────────── */}
      <div className="space-y-5">
        {Object.entries(grouped).map(([chapterId, items]) => (
          <div key={chapterId}>
            <p className="text-[9px] text-zinc-400 uppercase tracking-widest mb-1">
              {chapterId.replace("ch_", "").replace(/_/g, " ")}
            </p>
            <ul className="space-y-1">
              {items.map((entry) => (
                <li key={`${entry.page_type}-${entry.page_number}`}>
                  {mode === "screen" ? (
                    <a
                      href={`#${entry.chapter_id}`}
                      className="screen-only flex items-baseline justify-between hover:text-rose-500 transition-colors group"
                    >
                      <span className="text-sm text-zinc-700 group-hover:text-rose-500">
                        {entry.title}
                      </span>
                      <span className="ml-2 shrink-0 text-xs text-zinc-400 tabular-nums">
                        {entry.page_number}
                      </span>
                    </a>
                  ) : (
                    <div className="flex items-baseline justify-between">
                      <span className="text-sm text-zinc-700">{entry.title}</span>
                      <span className="ml-2 text-xs text-zinc-400 tabular-nums">
                        {entry.page_number}
                      </span>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          </div>
        ))}
        {entries.length === 0 && (
          <p className="text-sm text-zinc-400">目录正在生成…</p>
        )}
      </div>
    </PageShell>
  )
}
