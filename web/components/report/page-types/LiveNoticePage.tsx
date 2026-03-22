/**
 * LiveNoticePage.tsx — 动态注意事项页（live_notice）
 *
 * 页型：frontmatter / full 页
 * 作用：基于 RiskWatchItem 和 LiveRiskMonitor 的输出，展示行程期间的
 *       实时/动态风险提醒（关闭日、极端天气、节假日拥挤、交通停运等）。
 *       每次报告生成时动态注入，区别于静态的 departure_prep。
 */
"use client"

import { cn } from "@/lib/utils"
import type { PageViewModel, SectionVM } from "@/lib/report/types"
import PageShell from "../PageShell"

// ── 类型 ───────────────────────────────────────────────────────────────────

type Severity = "critical" | "warning" | "info"

interface RiskCardContent {
  risk_id: string
  risk_type: string              // "closed_day" | "crowd_alert" | "weather_risk" | "reservation_needed"
  severity: Severity
  title: string
  description: string
  action_required?: string
  entity_name?: string
  day_index?: number
  affected_date?: string         // YYYY-MM-DD
}

interface LiveSummaryContent {
  critical_count: number
  warning_count: number
  info_count: number
  generated_at: string           // ISO datetime
  is_fresh: boolean              // 是否最近 24h 内生成
}

// ── 子组件 ─────────────────────────────────────────────────────────────────

const SEVERITY_STYLE: Record<Severity, { bg: string; border: string; badge: string; icon: string }> = {
  critical: {
    bg:     "bg-red-50",
    border: "border-red-300",
    badge:  "bg-red-100 text-red-700",
    icon:   "🚨",
  },
  warning: {
    bg:     "bg-amber-50",
    border: "border-amber-300",
    badge:  "bg-amber-100 text-amber-700",
    icon:   "⚠️",
  },
  info: {
    bg:     "bg-blue-50",
    border: "border-blue-200",
    badge:  "bg-blue-100 text-blue-600",
    icon:   "ℹ️",
  },
}

const RISK_TYPE_LABEL: Record<string, string> = {
  closed_day:          "关闭日提醒",
  crowd_alert:         "拥挤预警",
  weather_risk:        "天气提示",
  reservation_needed:  "预订提醒",
  seasonal:            "季节性注意",
  transport:           "交通异常",
}

function RiskCard({ content }: { content: RiskCardContent }) {
  const style = SEVERITY_STYLE[content.severity] ?? SEVERITY_STYLE.info
  const typeLabel = RISK_TYPE_LABEL[content.risk_type] ?? content.risk_type

  return (
    <div className={cn("rounded-lg border p-3 mb-3", style.bg, style.border)}>
      {/* 顶部行 */}
      <div className="flex items-start justify-between gap-2 mb-1.5">
        <div className="flex items-center gap-1.5">
          <span className="text-base">{style.icon}</span>
          <p className="text-sm font-semibold text-gray-900 leading-snug">{content.title}</p>
        </div>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          {content.day_index != null && (
            <span className="text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-white/80 text-gray-600 border border-gray-200">
              第 {content.day_index} 天
            </span>
          )}
          <span className={cn("text-[10px] font-bold px-1.5 py-0.5 rounded-full", style.badge)}>
            {typeLabel}
          </span>
        </div>
      </div>

      {/* 实体名 */}
      {content.entity_name && (
        <p className="text-xs text-gray-600 mb-1">
          涉及：<span className="font-medium">{content.entity_name}</span>
          {content.affected_date && (
            <span className="ml-2 text-gray-400">（{content.affected_date}）</span>
          )}
        </p>
      )}

      {/* 描述 */}
      <p className="text-xs text-gray-700 leading-relaxed">{content.description}</p>

      {/* 建议操作 */}
      {content.action_required && (
        <div className="mt-2 flex items-start gap-1.5">
          <span className="text-xs text-gray-400 flex-shrink-0 mt-0.5">→</span>
          <p className="text-xs font-medium text-gray-800">{content.action_required}</p>
        </div>
      )}
    </div>
  )
}

function LiveSummaryBanner({ section }: { section: SectionVM }) {
  const content = section.content as LiveSummaryContent | null
  if (!content) return null

  const total = content.critical_count + content.warning_count + content.info_count
  const hasCritical = content.critical_count > 0

  return (
    <div
      className={cn(
        "rounded-xl p-4 mb-5 border",
        hasCritical
          ? "bg-red-50 border-red-200"
          : content.warning_count > 0
          ? "bg-amber-50 border-amber-200"
          : "bg-emerald-50 border-emerald-200",
      )}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className={cn(
            "text-sm font-bold",
            hasCritical ? "text-red-800" : content.warning_count > 0 ? "text-amber-800" : "text-emerald-800",
          )}>
            {total === 0
              ? "✅ 行程期间暂无风险提示"
              : `共 ${total} 条动态提醒`}
          </p>
          <p className="text-xs text-gray-500 mt-0.5">
            更新于 {content.generated_at}
            {content.is_fresh && (
              <span className="ml-1.5 text-emerald-600 font-medium">· 最新</span>
            )}
          </p>
        </div>
        {total > 0 && (
          <div className="flex items-center gap-2">
            {content.critical_count > 0 && (
              <span className="text-xs font-bold px-2 py-1 rounded-full bg-red-100 text-red-700">
                🚨 {content.critical_count}
              </span>
            )}
            {content.warning_count > 0 && (
              <span className="text-xs font-bold px-2 py-1 rounded-full bg-amber-100 text-amber-700">
                ⚠️ {content.warning_count}
              </span>
            )}
            {content.info_count > 0 && (
              <span className="text-xs font-bold px-2 py-1 rounded-full bg-blue-100 text-blue-600">
                ℹ️ {content.info_count}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function RiskCardList({ section }: { section: SectionVM }) {
  const items = section.content as RiskCardContent[] | null
  if (!items?.length) return null

  // 按 severity 排序：critical > warning > info
  const order: Record<Severity, number> = { critical: 0, warning: 1, info: 2 }
  const sorted = [...items].sort((a, b) => order[a.severity] - order[b.severity])

  return (
    <div>
      {section.heading && (
        <h3 className="text-[13px] font-semibold text-gray-700 mb-3 uppercase tracking-wide">
          {section.heading}
        </h3>
      )}
      {sorted.map((item) => (
        <RiskCard key={item.risk_id} content={item} />
      ))}
    </div>
  )
}

// ── 主组件 ─────────────────────────────────────────────────────────────────

interface LiveNoticePageProps extends PageViewModel {
  mode?: "screen" | "print"
}

export default function LiveNoticePage(props: LiveNoticePageProps) {
  const { heading, sections, footer, mode = "screen" } = props

  const summarySection = sections.find((s) => s.section_type === "live_summary")
  const riskSections   = sections.filter((s) => s.section_type === "risk_card")
  const noteSection    = sections.find((s) => s.section_type === "text_block")

  return (
    <PageShell mode={mode} footer={footer}>
      {/* 标题区 */}
      <div className="flex items-center gap-2 mb-5">
        <span className="text-2xl">📡</span>
        <div>
          <h1 className="text-xl font-bold text-gray-900 leading-tight">{heading.title}</h1>
          {heading.subtitle && (
            <p className="text-sm text-gray-500 mt-0.5">{heading.subtitle}</p>
          )}
        </div>
      </div>

      {/* 摘要横幅 */}
      {summarySection && <LiveSummaryBanner section={summarySection} />}

      {/* 风险卡片列表 */}
      {riskSections.length > 0 ? (
        riskSections.map((s, i) => <RiskCardList key={i} section={s} />)
      ) : (
        <div className="text-center py-10 text-gray-400">
          <p className="text-4xl mb-2">✅</p>
          <p className="text-sm">行程期间暂无风险事项</p>
        </div>
      )}

      {/* 备注 */}
      {noteSection && (
        <div className="mt-5 p-3 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-xs text-gray-600 leading-relaxed">
            {typeof noteSection.content === "string"
              ? noteSection.content
              : (noteSection.content as { text?: string })?.text ?? ""}
          </p>
        </div>
      )}
    </PageShell>
  )
}
