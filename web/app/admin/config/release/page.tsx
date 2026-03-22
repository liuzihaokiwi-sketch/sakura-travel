"use client"
/**
 * /admin/config/release — 发布中心
 * 展示所有待审批 / 灰度中 / 可激活的配置包，集中管理发布流程。
 */
import { useState, useEffect, useCallback } from "react"
import Link from "next/link"

interface ConfigPack {
  pack_id: string
  name: string
  pack_type: string
  active_version_no: number | null
  status: string
  updated_at: string
  config_scopes?: Array<{ scope_type: string; scope_value?: string; rollout_pct: number }>
}

const STATUS_META: Record<string, { label: string; color: string; actionable?: boolean }> = {
  draft:          { label: "草稿",   color: "bg-gray-100 text-gray-700" },
  pending_review: { label: "待审批", color: "bg-amber-100 text-amber-800", actionable: true },
  approved:       { label: "已审批", color: "bg-blue-100 text-blue-800",   actionable: true },
  canary:         { label: "灰度中", color: "bg-purple-100 text-purple-800", actionable: true },
  active:         { label: "生效中", color: "bg-green-100 text-green-800" },
  rolled_back:    { label: "已回滚", color: "bg-red-100 text-red-700" },
  archived:       { label: "已归档", color: "bg-slate-100 text-slate-500" },
}

export default function ReleaseCenterPage() {
  const [packs, setPacks]   = useState<ConfigPack[]>([])
  const [loading, setLoading] = useState(true)
  const [opMsg, setOpMsg]   = useState<Record<string, string>>({})

  const loadPacks = useCallback(async () => {
    setLoading(true)
    try {
      // 加载待审批 + 灰度中 + 已审批的配置包
      const res = await fetch("/api/admin/config")
      const data = await res.json()
      const actionable = (data.packs ?? []).filter((p: ConfigPack) =>
        ["pending_review", "approved", "canary", "active"].includes(p.status)
      )
      setPacks(actionable)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { loadPacks() }, [loadPacks])

  const handleAction = async (packId: string, action: string, extra?: Record<string, unknown>) => {
    setOpMsg((prev) => ({ ...prev, [packId]: "处理中…" }))
    try {
      const res = await fetch(`/api/admin/config/${packId}/release`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, ...extra }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error)
      setOpMsg((prev) => ({ ...prev, [packId]: `✅ ${action} 成功` }))
      await loadPacks()
    } catch (e: unknown) {
      setOpMsg((prev) => ({ ...prev, [packId]: `❌ ${e instanceof Error ? e.message : "失败"}` }))
    }
  }

  const pendingReview = packs.filter((p) => p.status === "pending_review")
  const approved      = packs.filter((p) => p.status === "approved")
  const canary        = packs.filter((p) => p.status === "canary")
  const active        = packs.filter((p) => p.status === "active")

  function PackRow({ pack }: { pack: ConfigPack }) {
    const status = STATUS_META[pack.status] ?? { label: pack.status, color: "bg-gray-100 text-gray-600" }
    const scopes = pack.config_scopes ?? []

    return (
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <p className="text-sm font-semibold text-slate-900">{pack.name}</p>
              <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full ${status.color}`}>
                {status.label}
              </span>
              {pack.active_version_no && (
                <span className="text-[10px] text-slate-400">v{pack.active_version_no}</span>
              )}
            </div>
            {scopes.length > 0 && (
              <div className="flex flex-wrap gap-1 mb-2">
                {scopes.slice(0, 3).map((s, i) => (
                  <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                    {s.scope_type}{s.scope_value ? `: ${s.scope_value}` : ""} {s.rollout_pct < 1 ? `(${Math.round(s.rollout_pct * 100)}%)` : ""}
                  </span>
                ))}
              </div>
            )}
            {opMsg[pack.pack_id] && (
              <p className="text-xs text-slate-500 mt-1">{opMsg[pack.pack_id]}</p>
            )}
          </div>

          {/* 操作按钮 */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <Link
              href={`/admin/config/${pack.pack_id}`}
              className="text-xs text-indigo-600 hover:underline"
            >
              详情
            </Link>

            {pack.status === "pending_review" && (
              <>
                <button
                  onClick={() => handleAction(pack.pack_id, "approve")}
                  className="text-xs px-3 py-1.5 rounded-lg bg-blue-500 text-white hover:bg-blue-600"
                >
                  ✅ 审批通过
                </button>
                <button
                  onClick={() => handleAction(pack.pack_id, "reject")}
                  className="text-xs px-3 py-1.5 rounded-lg bg-red-100 text-red-700 hover:bg-red-200"
                >
                  ✗ 拒绝
                </button>
              </>
            )}

            {pack.status === "approved" && (
              <>
                <button
                  onClick={() => handleAction(pack.pack_id, "canary", { rollout_scope: { pct: 0.05 } })}
                  className="text-xs px-3 py-1.5 rounded-lg bg-purple-500 text-white hover:bg-purple-600"
                >
                  🔬 5% 灰度
                </button>
                <button
                  onClick={() => handleAction(pack.pack_id, "activate")}
                  className="text-xs px-3 py-1.5 rounded-lg bg-green-600 text-white hover:bg-green-700"
                >
                  🚀 全量激活
                </button>
              </>
            )}

            {pack.status === "canary" && (
              <>
                <button
                  onClick={() => handleAction(pack.pack_id, "activate")}
                  className="text-xs px-3 py-1.5 rounded-lg bg-green-600 text-white hover:bg-green-700"
                >
                  🚀 提升全量
                </button>
              </>
            )}

            {pack.status === "active" && (
              <button
                onClick={() => {
                  const reason = window.prompt("回滚原因：")
                  if (reason !== null) handleAction(pack.pack_id, "rollback", { rollback_reason: reason })
                }}
                className="text-xs px-3 py-1.5 rounded-lg bg-red-100 text-red-700 hover:bg-red-200"
              >
                ↩️ 回滚
              </button>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-3">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/admin/config" className="text-slate-400 hover:text-slate-600 text-sm">← 配置中心</Link>
            <div>
              <h1 className="text-sm font-semibold text-slate-900">🚀 发布中心</h1>
              <p className="text-xs text-slate-500">审批 · 灰度 · 激活 · 回滚</p>
            </div>
          </div>
          <button onClick={loadPacks} className="text-xs text-slate-500 hover:text-slate-900">🔄 刷新</button>
        </div>
      </header>

      <div className="max-w-5xl mx-auto p-6">
        {loading ? (
          <div className="text-center py-16 text-slate-400 text-sm">加载中…</div>
        ) : (
          <div className="space-y-8">
            {/* 待审批 */}
            {pendingReview.length > 0 && (
              <section>
                <h2 className="text-xs font-semibold text-amber-700 uppercase tracking-wide mb-3 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-amber-400 inline-block" />
                  待审批 ({pendingReview.length})
                </h2>
                <div className="space-y-2">
                  {pendingReview.map((p) => <PackRow key={p.pack_id} pack={p} />)}
                </div>
              </section>
            )}

            {/* 已审批，待激活 */}
            {approved.length > 0 && (
              <section>
                <h2 className="text-xs font-semibold text-blue-700 uppercase tracking-wide mb-3 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-blue-400 inline-block" />
                  已审批，待激活 ({approved.length})
                </h2>
                <div className="space-y-2">
                  {approved.map((p) => <PackRow key={p.pack_id} pack={p} />)}
                </div>
              </section>
            )}

            {/* 灰度中 */}
            {canary.length > 0 && (
              <section>
                <h2 className="text-xs font-semibold text-purple-700 uppercase tracking-wide mb-3 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-purple-400 inline-block" />
                  灰度中 ({canary.length})
                </h2>
                <div className="space-y-2">
                  {canary.map((p) => <PackRow key={p.pack_id} pack={p} />)}
                </div>
              </section>
            )}

            {/* 生效中（可回滚） */}
            {active.length > 0 && (
              <section>
                <h2 className="text-xs font-semibold text-green-700 uppercase tracking-wide mb-3 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-green-400 inline-block" />
                  生效中 ({active.length})
                </h2>
                <div className="space-y-2">
                  {active.map((p) => <PackRow key={p.pack_id} pack={p} />)}
                </div>
              </section>
            )}

            {packs.length === 0 && (
              <div className="text-center py-16">
                <p className="text-slate-400 text-sm">暂无待处理的配置包</p>
                <Link href="/admin/config" className="text-xs text-indigo-600 hover:underline mt-2 block">
                  前往配置中心创建
                </Link>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
