"use client"
/**
 * /admin/config/preview — 预览对比中心
 * 展示所有配置包的预览运行记录，支持筛选/查看 diff。
 */
import { useState, useEffect, useCallback } from "react"
import Link from "next/link"

interface PreviewRun {
  run_id: string
  pack_id: string
  version_no: number
  subject_type: string
  subject_id: string
  status: string
  diff_summary: {
    major_changed?: string[]
    hotel_changed?: boolean
    score_delta?: number
    risk_delta?: number
  } | null
  created_at: string
  completed_at: string | null
}

const STATUS_COLOR: Record<string, string> = {
  pending: "bg-amber-100 text-amber-700",
  running: "bg-blue-100 text-blue-700",
  done:    "bg-green-100 text-green-700",
  failed:  "bg-red-100 text-red-700",
}

function DiffBadge({ diff }: { diff: PreviewRun["diff_summary"] }) {
  if (!diff) return <span className="text-[10px] text-slate-400">无差异数据</span>
  return (
    <div className="flex flex-wrap gap-1.5">
      {diff.score_delta !== undefined && (
        <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${diff.score_delta > 0 ? "bg-green-100 text-green-700" : diff.score_delta < 0 ? "bg-red-100 text-red-700" : "bg-gray-100 text-gray-500"}`}>
          分数 {diff.score_delta > 0 ? "+" : ""}{diff.score_delta?.toFixed(2)}
        </span>
      )}
      {diff.hotel_changed && (
        <span className="text-[11px] px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">酒店变化</span>
      )}
      {diff.major_changed && diff.major_changed.length > 0 && (
        <span className="text-[11px] px-2 py-0.5 rounded-full bg-purple-100 text-purple-700">
          {diff.major_changed.length} 项主活动变化
        </span>
      )}
      {diff.risk_delta !== undefined && diff.risk_delta !== 0 && (
        <span className={`text-[11px] px-2 py-0.5 rounded-full ${diff.risk_delta > 0 ? "bg-red-100 text-red-700" : "bg-green-100 text-green-700"}`}>
          风险 {diff.risk_delta > 0 ? "↑" : "↓"}
        </span>
      )}
    </div>
  )
}

export default function PreviewLabPage() {
  const [runs, setRuns] = useState<PreviewRun[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedRun, setSelectedRun] = useState<PreviewRun | null>(null)

  const loadRuns = useCallback(async () => {
    setLoading(true)
    try {
      // 查询最近所有 config pack 的预览运行（跨 pack 汇总）
      const res = await fetch("/api/admin/config/preview/all")
      const data = await res.json()
      setRuns(data.runs ?? [])
    } catch {
      setRuns([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { loadRuns() }, [loadRuns])

  const doneRuns    = runs.filter((r) => r.status === "done")
  const pendingRuns = runs.filter((r) => r.status === "pending" || r.status === "running")

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-3">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/admin/config" className="text-slate-400 hover:text-slate-600 text-sm">← 配置中心</Link>
            <div>
              <h1 className="text-sm font-semibold text-slate-900">🔍 预览对比中心</h1>
              <p className="text-xs text-slate-500">旧配置 vs 新配置对比结果</p>
            </div>
          </div>
          <button onClick={loadRuns} className="text-xs text-slate-500 hover:text-slate-900">🔄 刷新</button>
        </div>
      </header>

      <div className="max-w-5xl mx-auto p-6">
        {/* 概览 */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          {[
            { label: "全部", value: runs.length, color: "text-slate-700" },
            { label: "已完成", value: doneRuns.length, color: "text-green-600" },
            { label: "排队中", value: pendingRuns.length, color: "text-amber-600" },
          ].map((s, i) => (
            <div key={i} className="bg-white rounded-xl border border-slate-200 p-4 text-center">
              <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
              <p className="text-xs text-slate-500 mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>

        {/* 运行列表 */}
        {loading ? (
          <div className="text-center py-16 text-slate-400 text-sm">加载中…</div>
        ) : runs.length === 0 ? (
          <div className="text-center py-16">
            <p className="text-slate-400 text-sm mb-2">暂无预览运行</p>
            <p className="text-xs text-slate-400">进入配置包详情页，点击"预览对比"触发运行</p>
          </div>
        ) : (
          <div className="space-y-2">
            {runs.map((run) => (
              <div
                key={run.run_id}
                onClick={() => setSelectedRun(run)}
                className="bg-white rounded-xl border border-slate-200 p-4 hover:shadow-sm hover:border-slate-300 cursor-pointer transition-all"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full ${STATUS_COLOR[run.status] ?? "bg-gray-100 text-gray-600"}`}>
                        {run.status}
                      </span>
                      <span className="text-xs text-slate-600 font-medium">
                        {run.subject_type === "order" ? "📦 订单" : "📋 评测用例"} · {run.subject_id.slice(0, 12)}…
                      </span>
                      <span className="text-[10px] text-slate-400">pack: {run.pack_id.slice(0, 8)} v{run.version_no}</span>
                    </div>
                    {run.status === "done" && <DiffBadge diff={run.diff_summary} />}
                  </div>
                  <span className="text-[10px] text-slate-400 flex-shrink-0">
                    {new Date(run.created_at).toLocaleString("zh-CN", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 详情弹窗 */}
      {selectedRun && (
        <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4" onClick={() => setSelectedRun(null)}>
          <div
            className="bg-white rounded-2xl shadow-xl w-full max-w-2xl p-6 max-h-[80vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-slate-900">预览对比详情</h2>
              <button onClick={() => setSelectedRun(null)} className="text-slate-400 hover:text-slate-600 text-lg">×</button>
            </div>
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="bg-slate-50 rounded-lg p-3">
                  <p className="text-slate-500 mb-1">对象</p>
                  <p className="font-medium">{selectedRun.subject_type}: {selectedRun.subject_id}</p>
                </div>
                <div className="bg-slate-50 rounded-lg p-3">
                  <p className="text-slate-500 mb-1">配置版本</p>
                  <p className="font-medium">{selectedRun.pack_id.slice(0, 8)} v{selectedRun.version_no}</p>
                </div>
              </div>
              {selectedRun.diff_summary && (
                <div className="bg-slate-50 rounded-lg p-4">
                  <p className="text-xs font-semibold text-slate-700 mb-3">差异摘要</p>
                  <div className="space-y-2">
                    {selectedRun.diff_summary.score_delta !== undefined && (
                      <div className="flex justify-between text-xs">
                        <span className="text-slate-500">分数变化</span>
                        <span className={`font-bold ${selectedRun.diff_summary.score_delta >= 0 ? "text-green-600" : "text-red-600"}`}>
                          {selectedRun.diff_summary.score_delta >= 0 ? "+" : ""}{selectedRun.diff_summary.score_delta.toFixed(3)}
                        </span>
                      </div>
                    )}
                    {selectedRun.diff_summary.hotel_changed !== undefined && (
                      <div className="flex justify-between text-xs">
                        <span className="text-slate-500">酒店策略</span>
                        <span className={selectedRun.diff_summary.hotel_changed ? "text-amber-600 font-medium" : "text-green-600"}>
                          {selectedRun.diff_summary.hotel_changed ? "有变化" : "无变化"}
                        </span>
                      </div>
                    )}
                    {selectedRun.diff_summary.major_changed && selectedRun.diff_summary.major_changed.length > 0 && (
                      <div className="text-xs">
                        <span className="text-slate-500 block mb-1">主活动变化</span>
                        <ul className="space-y-0.5">
                          {selectedRun.diff_summary.major_changed.map((c, i) => (
                            <li key={i} className="text-purple-700">• {c}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
