"use client"
/**
 * /admin/config — 运营配置中心
 * 列出所有配置包，支持新建、筛选状态/类型，点击进入详情编辑。
 */
import { useState, useEffect, useCallback } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"

// ── 类型 ───────────────────────────────────────────────────────────────────

interface ConfigPack {
  pack_id: string
  name: string
  description?: string
  pack_type: string
  active_version_no: number | null
  status: string
  created_at: string
  updated_at: string
  config_scopes?: Array<{ scope_type: string; scope_value?: string; is_active: boolean }>
}

// ── 常量 ───────────────────────────────────────────────────────────────────

const STATUS_META: Record<string, { label: string; color: string }> = {
  draft:          { label: "草稿",    color: "bg-gray-100 text-gray-700" },
  pending_review: { label: "待审批",  color: "bg-amber-100 text-amber-700" },
  approved:       { label: "已审批",  color: "bg-blue-100 text-blue-700" },
  canary:         { label: "灰度中",  color: "bg-purple-100 text-purple-700" },
  active:         { label: "生效中",  color: "bg-green-100 text-green-700" },
  rolled_back:    { label: "已回滚",  color: "bg-red-100 text-red-700" },
  archived:       { label: "已归档",  color: "bg-slate-100 text-slate-500" },
}

const PACK_TYPE_META: Record<string, { label: string; icon: string }> = {
  weights:    { label: "权重",    icon: "⚖️" },
  thresholds: { label: "阈值",    icon: "📏" },
  switches:   { label: "开关",    icon: "🔀" },
  hard_rules: { label: "硬规则",  icon: "🔒" },
  segment:    { label: "客群包",  icon: "👥" },
  composite:  { label: "综合包",  icon: "📦" },
}

// ── 子组件 ─────────────────────────────────────────────────────────────────

function PackCard({ pack }: { pack: ConfigPack }) {
  const status = STATUS_META[pack.status] ?? { label: pack.status, color: "bg-gray-100 text-gray-600" }
  const type   = PACK_TYPE_META[pack.pack_type] ?? { label: pack.pack_type, icon: "📄" }

  const scopes = pack.config_scopes ?? []
  const activeScopes = scopes.filter((s) => s.is_active)

  const updatedAt = new Date(pack.updated_at)
  const timeStr = updatedAt.toLocaleString("zh-CN", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" })

  return (
    <Link href={`/admin/config/${pack.pack_id}`}>
      <div className="bg-white rounded-xl border border-slate-200 p-4 hover:shadow-md hover:border-slate-300 transition-all cursor-pointer">
        {/* 顶部行 */}
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex items-center gap-2">
            <span className="text-lg">{type.icon}</span>
            <div>
              <p className="text-sm font-semibold text-slate-900 leading-tight">{pack.name}</p>
              <p className="text-xs text-slate-400">{type.label} · v{pack.active_version_no ?? "—"}</p>
            </div>
          </div>
          <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full flex-shrink-0 ${status.color}`}>
            {status.label}
          </span>
        </div>

        {/* 描述 */}
        {pack.description && (
          <p className="text-xs text-slate-500 mb-2 leading-relaxed line-clamp-2">{pack.description}</p>
        )}

        {/* 作用域标签 */}
        {activeScopes.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-2">
            {activeScopes.slice(0, 3).map((s, i) => (
              <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-600 font-medium">
                {s.scope_type}{s.scope_value ? `: ${s.scope_value}` : ""}
              </span>
            ))}
            {activeScopes.length > 3 && (
              <span className="text-[10px] text-slate-400">+{activeScopes.length - 3}</span>
            )}
          </div>
        )}

        {/* 底部 */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-100">
          <span className="text-[10px] text-slate-400">{timeStr} 更新</span>
          <span className="text-[10px] text-indigo-500 font-medium">编辑 →</span>
        </div>
      </div>
    </Link>
  )
}

// ── 新建对话框 ──────────────────────────────────────────────────────────────

function CreatePackModal({ onClose, onCreate }: {
  onClose: () => void
  onCreate: (pack: ConfigPack) => void
}) {
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [packType, setPackType] = useState("weights")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const handleCreate = async () => {
    if (!name.trim()) { setError("名称不能为空"); return }
    setLoading(true)
    setError("")
    try {
      const res = await fetch("/api/admin/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, description, pack_type: packType }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || "创建失败")
      onCreate(data.pack)
      onClose()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "创建失败")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
        <h2 className="text-base font-semibold text-slate-900 mb-4">新建配置包</h2>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">名称 *</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="如：情侣审美路线增强 v1"
              className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">类型</label>
            <select
              value={packType}
              onChange={(e) => setPackType(e.target.value)}
              className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-300"
            >
              {Object.entries(PACK_TYPE_META).map(([k, v]) => (
                <option key={k} value={k}>{v.icon} {v.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">描述（可选）</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              placeholder="这套配置解决什么问题？"
              className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-300 resize-none"
            />
          </div>
        </div>

        {error && <p className="text-xs text-red-500 mt-2">{error}</p>}

        <div className="flex justify-end gap-2 mt-5">
          <button
            onClick={onClose}
            className="text-sm px-4 py-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50"
          >
            取消
          </button>
          <button
            onClick={handleCreate}
            disabled={loading}
            className="text-sm px-4 py-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading ? "创建中…" : "创建"}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── 主页面 ─────────────────────────────────────────────────────────────────

export default function ConfigCenterPage() {
  const [packs, setPacks]         = useState<ConfigPack[]>([])
  const [loading, setLoading]     = useState(true)
  const [filterStatus, setFilterStatus] = useState("")
  const [filterType, setFilterType]     = useState("")
  const [showCreate, setShowCreate]     = useState(false)
  const router = useRouter()

  const loadPacks = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filterStatus) params.set("status", filterStatus)
      if (filterType)   params.set("pack_type", filterType)
      const res = await fetch(`/api/admin/config?${params}`)
      const data = await res.json()
      setPacks(data.packs ?? [])
    } finally {
      setLoading(false)
    }
  }, [filterStatus, filterType])

  useEffect(() => { loadPacks() }, [loadPacks])

  const activePacks = packs.filter((p) => p.status === "active")
  const pendingPacks = packs.filter((p) => p.status === "pending_review")

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-3">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/admin" className="text-slate-400 hover:text-slate-600 text-sm">← 返回</Link>
            <div>
              <h1 className="text-sm font-semibold text-slate-900">⚙️ 运营配置中心</h1>
              <p className="text-xs text-slate-500">权重 · 阈值 · 开关 · 发布流程</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/admin/config/release" className="text-xs text-slate-500 hover:text-slate-900 flex items-center gap-1">
              🚀 发布中心
            </Link>
            <Link href="/admin/config/preview" className="text-xs text-slate-500 hover:text-slate-900 flex items-center gap-1">
              🔍 预览对比
            </Link>
            <button
              onClick={() => setShowCreate(true)}
              className="text-xs bg-indigo-600 text-white px-3 py-1.5 rounded-lg hover:bg-indigo-700"
            >
              + 新建配置包
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto p-6">
        {/* 概览条 */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          {[
            { label: "生效中", value: activePacks.length, color: "text-green-600" },
            { label: "待审批", value: pendingPacks.length, color: "text-amber-600" },
            { label: "全部",   value: packs.length,        color: "text-slate-700" },
            { label: "草稿",   value: packs.filter((p) => p.status === "draft").length, color: "text-gray-500" },
          ].map((item, i) => (
            <div key={i} className="bg-white rounded-xl border border-slate-200 p-4 text-center">
              <p className={`text-2xl font-bold ${item.color}`}>{item.value}</p>
              <p className="text-xs text-slate-500 mt-0.5">{item.label}</p>
            </div>
          ))}
        </div>

        {/* 筛选栏 */}
        <div className="flex items-center gap-3 mb-4">
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="text-sm border border-slate-200 rounded-lg px-3 py-1.5 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-300"
          >
            <option value="">全部状态</option>
            {Object.entries(STATUS_META).map(([k, v]) => (
              <option key={k} value={k}>{v.label}</option>
            ))}
          </select>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="text-sm border border-slate-200 rounded-lg px-3 py-1.5 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-300"
          >
            <option value="">全部类型</option>
            {Object.entries(PACK_TYPE_META).map(([k, v]) => (
              <option key={k} value={k}>{v.label}</option>
            ))}
          </select>
          <button
            onClick={loadPacks}
            className="text-xs text-slate-500 hover:text-slate-900 px-2 py-1.5"
          >
            🔄 刷新
          </button>
        </div>

        {/* 配置包列表 */}
        {loading ? (
          <div className="text-center text-sm text-slate-400 py-16">加载中…</div>
        ) : packs.length === 0 ? (
          <div className="text-center py-16">
            <p className="text-slate-400 text-sm mb-3">暂无配置包</p>
            <button
              onClick={() => setShowCreate(true)}
              className="text-sm text-indigo-600 hover:underline"
            >
              创建第一个配置包
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {packs.map((pack) => (
              <PackCard key={pack.pack_id} pack={pack} />
            ))}
          </div>
        )}
      </div>

      {showCreate && (
        <CreatePackModal
          onClose={() => setShowCreate(false)}
          onCreate={(pack) => {
            setPacks((prev) => [pack, ...prev])
            router.push(`/admin/config/${pack.pack_id}`)
          }}
        />
      )}
    </div>
  )
}
