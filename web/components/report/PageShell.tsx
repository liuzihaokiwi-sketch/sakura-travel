/**
 * web/components/report/PageShell.tsx — 页面外壳组件（L3-07）
 *
 * A4 纸张容器，支持 screen/print 双模式（F7）。
 * - screen: max-w-[210mm] mx-auto，允许 scroll
 * - print:  w-[210mm] h-[297mm]，break-before: always
 */

import React from "react"
import { Separator } from "@/components/ui/separator"
import { cn } from "@/lib/utils"

export interface PageShellProps {
  mode?: "screen" | "print"
  pageSize?: "full" | "half" | "dual-half"
  /** half 页专用：紧凑内边距 */
  compact?: boolean
  pageNumber?: number
  chapterTitle?: string
  /** 兼容 PageViewModel.footer 传入 */
  footer?: { page_number?: number; chapter_title?: string } | null
  className?: string
  children: React.ReactNode
}

export default function PageShell({
  mode = "screen",
  pageSize = "full",
  compact = false,
  pageNumber,
  chapterTitle,
  footer,
  className,
  children,
}: PageShellProps) {
  const resolvedPageNumber   = footer?.page_number   ?? pageNumber
  const resolvedChapterTitle = footer?.chapter_title ?? chapterTitle
  const isScreen = mode === "screen"
  const isHalf = pageSize === "half"

  return (
    <article
      className={cn(
        // ── 基础样式 ──────────────────────────────────────────────────────
        "relative bg-white font-sans",
        // ── 页面尺寸 ──────────────────────────────────────────────────────
        isScreen
          ? "max-w-[210mm] mx-auto shadow-xl rounded-sm"
          : "w-[210mm]",
        // 全页：完整 A4 高度；半页：约 A4 一半
        isScreen
          ? isHalf
            ? "min-h-[148.5mm]"
            : "min-h-[297mm]"
          : isHalf
          ? "h-[148.5mm]"
          : "h-[297mm]",
        // screen 模式增加垂直间距
        isScreen && "mb-8",
        // print 类（@media print 样式）
        "print-page",
        className,
      )}
    >
      {/* ── 页眉 ───────────────────────────────────────────────────────── */}
      {(resolvedChapterTitle || resolvedPageNumber !== undefined) && (
        <header className="flex items-center justify-between px-8 pt-5 pb-2">
          {resolvedChapterTitle ? (
            <span className="text-[10px] text-zinc-400 tracking-widest uppercase">
              {resolvedChapterTitle}
            </span>
          ) : (
            <span />
          )}
          {resolvedPageNumber !== undefined && (
            <span className="text-[10px] text-zinc-400">{resolvedPageNumber}</span>
          )}
        </header>
      )}

      {/* ── 内容区（安全区内边距，compact=half 页减小内边距） ─────────── */}
      <main className={cn("flex-1", compact ? "px-6 py-3" : "px-10 py-4")}>{children}</main>

      {/* ── 页脚 ───────────────────────────────────────────────────────── */}
      <footer className="flex items-center justify-between px-8 pb-5 pt-2 mt-auto">
        <span className="text-[9px] text-zinc-300 tracking-wider">
          Sakura Rush · AI 旅行规划
        </span>
        {resolvedPageNumber !== undefined && (
          <span className="text-[9px] text-zinc-300">{resolvedPageNumber}</span>
        )}
      </footer>

      {/* ── screen 模式分页线 ─────────────────────────────────────────── */}
      {isScreen && (
        <div
          aria-hidden
          className="absolute bottom-0 left-0 right-0 h-[1px] bg-zinc-100"
        />
      )}

      {/* ── print CSS ─────────────────────────────────────────────────── */}
      <style>{`
        @media print {
          .print-page {
            width: 210mm !important;
            height: ${isHalf ? "148.5mm" : "297mm"} !important;
            break-before: always;
            box-shadow: none !important;
            margin: 0 !important;
            overflow: hidden;
          }
          .print-page header,
          .print-page footer {
            display: flex !important;
          }
          /* 隐藏 screen 专用的交互元素 */
          .screen-only {
            display: none !important;
          }
        }
        @media screen {
          .print-only {
            display: none !important;
          }
        }
      `}</style>
    </article>
  )
}
