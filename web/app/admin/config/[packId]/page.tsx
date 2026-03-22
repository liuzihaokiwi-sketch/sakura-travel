"use client"
/**
 * /admin/config/[packId] — 配置包详情与编辑页
 * 支持：基本信息 / 作用域 / 权重组 / 阈值组 / 开关组 / 影响预估 / 保存草稿 / 送审
 */
import { useState, useEffect, useCallback } from "react"
import Link from "next/link"
import { useParams, useRouter } from "next/navigation"

// ── 类型 ───────────────────────────────────────────────────────────────────

interface ConfigVersion {
  version_id: string
  version_no: number
  weights: Record<string, number> | null
  thresholds: Record<string, unknown> | null
  switches: Record<string, boolean> | null
  hard_rules: unknown[] | null
  change_summary: string | null
  reason: string | null
  created_at: string
}

interface ConfigScope {
  scope_id: string
  scope_type: string
  scope_value: string | null
  rollout_pct: number
  is_active: boolean
}

interface ReleaseRecord {
  record_id: string
  version_no: number
  action: string
  notes: string | null
  created_at: string
}

interface PackDetail {
  pack_id: string
  name: string
  description: string | null
  pack_type: string
  active_version_no: number | null
  status: string
  updated_at: string
}

// ── 权重定义（含建议范围和说明）──────────────────────────────────────────────

const WEIGHT_DEFINITIONS: Record<string, {
  group: string
  label: string
  hint: string
  min: number
  max: number
  default: number
  danger?: boolean
}> = {
  // 活动权重
  major_activity_base_weight:    { group: "activity", label: "主活动基础权重",  hint: "影响主要活动整体选取倾向", min: 0.5, max: 2.0, default: 1.0 },
  secondary_activity_base_weight:{ group: "activity", label: "次活动基础权重",  hint: "影响次要活动整体选取倾向", min: 0.3, max: 1.5, default: 0.7 },
  photo_bias:                    { group: "activity", label: "拍照偏好加成",    hint: "调高→更多出片地点", min: -0.5, max: 1.0, default: 0.0 },
  food_bias:                     { group: "activity", label: "美食偏好加成",    hint: "调高→更多美食体验", min: -0.5, max: 1.0, default: 0.0 },
  shopping_bias:                 { group: "activity", label: "购物偏好加成",    hint: "调高→更多购物行程", min: -0.5, max: 1.0, default: 0.0 },
  recovery_bias:                 { group: "activity", label: "休闲恢复加成",    hint: "调高→更轻松节奏", min: -0.5, max: 1.0, default: 0.0 },
  season_bias:                   { group: "activity", label: "季节活动加成",    hint: "调高→优先当季特色活动", min: -0.3, max: 0.8, default: 0.0 },
  // 酒店权重
  hotel_quality_weight:          { group: "hotel", label: "酒店品质权重",      hint: "评分高的酒店更受优先", min: 0.2, max: 0.9, default: 0.55 },
  hotel_location_weight:         { group: "hotel", label: "酒店位置权重",      hint: "靠近景区的酒店更受优先", min: 0.1, max: 0.6, default: 0.25 },
  hotel_experience_weight:       { group: "hotel", label: "特色住宿权重",      hint: "温泉/设计酒店等", min: 0.0, max: 0.3, default: 0.05 },
  hotel_switch_penalty_weight:   { group: "hotel", label: "换酒店惩罚",        hint: "负值=换酒店越多越扣分", min: -0.5, max: 0.0, default: -0.1, danger: true },
  hotel_last_night_safe_weight:  { group: "hotel", label: "末夜安全策略权重",  hint: "保证最后一夜接近机场", min: 0.0, max: 0.2, default: 0.05 },
  // 餐厅权重
  dining_quality_weight:         { group: "dining", label: "餐厅品质权重",     hint: "评分高的餐厅更受优先", min: 0.2, max: 0.9, default: 0.6 },
  dining_queue_penalty_weight:   { group: "dining", label: "排队惩罚",         hint: "负值=需排队越多越扣分", min: -0.5, max: 0.0, default: -0.15 },
  destination_dining_bonus:      { group: "dining", label: "目的地特色餐加成", hint: "当地名菜/网红餐厅加分", min: 0.0, max: 0.3, default: 0.1 },
  backup_meal_bonus:             { group: "dining", label: "备选餐加成",        hint: "提供备选餐厅的行程加分", min: 0.0, max: 0.2, default: 0.05 },
  // 节奏
  dense_day_penalty:             { group: "rhythm", label: "高密度日惩罚",     hint: "负值=连续安排太多扣分", min: -0.5, max: 0.0, default: -0.15 },
  backtrack_penalty:             { group: "rhythm", label: "折返惩罚",         hint: "负值=来回折返越多越扣分", min: -0.5, max: 0.0, default: -0.2, danger: true },
  long_transfer_penalty:         { group: "rhythm", label: "长途转移惩罚",     hint: "超过阈值的交通时间扣分", min: -0.4, max: 0.0, default: -0.15 },
  same_corridor_bonus:           { group: "rhythm", label: "同走廊奖励",        hint: "同一走廊内活动加分", min: 0.0, max: 0.4, default: 0.15 },
}

const THRESHOLD_DEFINITIONS: Record<string, {
  label: string
  hint: string
  min: number
  max: number
  default: number
  unit?: string
  danger?: boolean
}> = {
  max_secondary_per_day:         { label: "每天最多次活动数", hint: "超过此数量次活动不再加入", min: 1, max: 6, default: 3, unit: "个" },
  max_hotel_switches:            { label: "最多换酒店次数",   hint: "超过将触发审查", min: 0, max: 5, default: 2, unit: "次" },
  max_transfer_minutes_per_day:  { label: "每天最大交通时间", hint: "超过将触发路线优化", min: 30, max: 180, default: 90, unit: "分钟" },
  max_walk_minutes_per_day:      { label: "每天最大步行时间", hint: "父母团需降低此值", min: 15, max: 90, default: 40, unit: "分钟" },
  strong_risk_redline:           { label: "强风险红线",       hint: "超过此分数不纳入主活动", min: 0.5, max: 1.0, default: 0.8, danger: true },
  low_match_review_threshold:    { label: "低匹配度审查阈值", hint: "低于此分数触发人工审查", min: 0.2, max: 0.8, default: 0.5 },
}

const SWITCH_DEFINITIONS: Record<string, { label: string; hint: string; danger?: boolean }> = {
  enable_city_circle_pipeline:       { label: "启用城市圈流水线",   hint: "关闭→降级到旧模板", danger: true },
  enable_fragment_first:             { label: "优先复用内容片段",   hint: "关闭→全量重新生成" },
  enable_hotel_base_strategy:        { label: "启用住宿策略预设",   hint: "关闭→随机分配酒店" },
  enable_conditional_pages:          { label: "启用条件页触发",     hint: "关闭→不生成动态页" },
  enable_shadow_write:               { label: "启用 Shadow 对比",  hint: "开启→新旧并行运行，消耗双倍算力" },
  enable_live_risk_monitor:          { label: "启用实时风险监控",   hint: "关闭→不扫描关闭日/极端天气" },
  enable_operator_override:          { label: "启用运营干预",        hint: "关闭→忽略所有 block/boost 设置", danger: true },
  enable_review_required_for_low_hit:{ label: "低命中率触发审查",   hint: "关闭→低匹配度行程不再强制审查" },
}

// ── 常量 ───────────────────────────────────────────────────────────────────

const STATUS_META: Record<string, { label: string; color: string }> = {
  draft:          { label: "草稿",   color: "bg-gray-100 text-gray-700" },
  pending_review: { label: "待审批", color: "bg-amber-100 text-amber-700" },
  approved:       { label: "已审批", color: "bg-blue-100 text-blue-700" },
  canary:         { label: "灰度中", color: "bg-purple-100 text-purple-700" },
  active:         { label: "生效中", color: "bg-green-100 text-green-700" },
  rolled_back:    { label: "已回滚", color: "bg-red-100 text-red-700" },
  archived:       { label: "已归档", color: "bg-slate-100 text-slate-500" },
}

const ACTION_RECORD_LABELS: Record<string, string> = {
  draft_saved:      "保存草稿",
  submitted_review: "送审",
  approved:         "审批通过",
  rejected:         "审批拒绝",
  canary_start:     "开始灰度",
  canary_promote:   "全量灰度",
  activated:        "正式激活",
  rolled_back:      "已回滚",
  archived:         "归档",
}

// ── 子组件 ─────────────────────────────────────────────────────────────────

function WeightSlider({
  defKey,
  value,
  onChange,
}: {
  defKey: string
  value: number
  onChange: (v: number) => void
}) {
  const def = WEIGHT_DEFINITIONS[defKey]
  if (!def) return null
  const pct = ((value - def.min) / (def.max - def.min)) * 100

  return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-1.5">
          {def.danger && <span className="text-red-500 text-xs font-bold">!</span>}
          <span className="text-xs font-medium text-slate-700">{def.label}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-slate-400">默认: {def.default}</span>
          <input
            type="number"
            value={value}
            step={0.05}
            min={def.min}
            max={def.max}
            onChange={(e) => onChange(Number(e.target.value))}
            className="w-16 text-xs border border-slate-200 rounded px-1.5 py-0.5 text-right"
          />
        </div>
      </div>
      <input
        type="range"
        min={def.min}
        max={def.max}
        step={0.05}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-1.5 rounded-full appearance-none cursor-pointer"
        style={{
          background: `linear-gradient(to right, #6366f1 0%, #6366f1 ${pct}%, #e2e8f0 ${pct}%, #e2e8f0 100%)`,
        }}
      />
      <div className="flex justify-between text-[10px] text-slate-400 mt-0.5">
        <span>{def.min}</span>
        <span className="text-slate-500 text-center flex-1">{def.hint}</span>
        <span>{def.max}</span>
      </div>
    </div>
  )
}

function SwitchToggle({
  defKey,
  value,
  onChange,
}: {
  defKey: string
  value: boolean
  onChange: (v: boolean) => void
}) {
  const def = SWITCH_DEFINITIONS[defKey]
  if (!def) return null

  return (
    <div className={`flex items-center justify-between p-3 rounded-lg border mb-2 ${value ? "border-indigo-200 bg-indigo-50" : "border-slate-200 bg-white"}`}>
      <div className="flex items-center gap-2">
        {def.danger && <span className="text-red-500 text-xs font-bold">⚠️</span>}
        <div>
          <p className="text-xs font-medium text-slate-800">{def.label}</p>
          <p className="text-[10px] text-slate-500">{def.hint}</p>
        </div>
      </div>
      <button
        onClick={() => onChange(!value)}
        className={`w-10 h-5 rounded-full relative transition-colors ${value ? "bg-indigo-500" : "bg-slate-300"}`}
      >
        <span className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${value ? "translate-x-5" : "translate-x-0.5"}`} />
      </button>
    </div>
  )
}

// ── 主页面 ─────────────────────────────────────────────────────────────────

export default function ConfigPackDetailPage() {
  const { packId } = useParams() as { packId: string }
  const router = useRouter()

  const [pack, setPack]         = useState<PackDetail | null>(null)
  const [versions, setVersions] = useState<ConfigVersion[]>([])
  const [scopes, setScopes]     = useState<ConfigScope[]>([])
  const [releases, setReleases] = useState<ReleaseRecord[]>([])
  const [loading, setLoading]   = useState(true)

  // 编辑态
  const [activeTab, setActiveTab]   = useState<"weights" | "thresholds" | "switches" | "scopes" | "history">("weights")
  const [editWeights, setEditWeights]       = useState<Record<string, number>>({})
  const [editThresholds, setEditThresholds] = useState<Record<string, number>>({})
  const [editSwitches, setEditSwitches]     = useState<Record<string, boolean>>({})
  const [changeSummary, setChangeSummary]   = useState("")
  const [reason, setReason]                 = useState("")
  const [saving, setSaving]   = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [actionMsg, setActionMsg]   = useState("")

  const loadDetail = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`/api/admin/config/${packId}`)
      const data = await res.json()
      setPack(data.pack)
      setVersions(data.versions ?? [])
      setScopes(data.scopes ?? [])
      setReleases(data.releases ?? [])

      // 初始化编辑态：从最新版本加载
      const latest = data.versions?.[0]
      const wDef: Record<string, number> = {}
      Object.keys(WEIGHT_DEFINITIONS).forEach((k) => {
        wDef[k] = (latest?.weights?.[k] as number) ?? WEIGHT_DEFINITIONS[k].default
      })
      setEditWeights(wDef)

      const tDef: Record<string, number> = {}
      Object.keys(THRESHOLD_DEFINITIONS).forEach((k) => {
        tDef[k] = (latest?.thresholds?.[k] as number) ?? THRESHOLD_DEFINITIONS[k].default
      })
      setEditThresholds(tDef)

      const swDef: Record<string, boolean> = {}
      Object.keys(SWITCH_DEFINITIONS).forEach((k) => {
        swDef[k] = (latest?.switches?.[k] as boolean) ?? false
      })
      setEditSwitches(swDef)
    } finally {
      setLoading(false)
    }
  }, [packId])

  useEffect(() => { loadDetail() }, [loadDetail])

  const handleSaveDraft = async () => {
    setSaving(true)
    setActionMsg("")
    try {
      const res = await fetch(`/api/admin/config/${packId}/versions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          weights:       editWeights,
          thresholds:    editThresholds,
          switches:      editSwitches,
          change_summary: changeSummary,
          reason,
        }),
      })
      if (!res.ok) {
        const d = await res.json()
        throw new Error(d.error || "保存失败")
      }
      setActionMsg("✅ 草稿已保存")
      await loadDetail()
    } catch (e: unknown) {
      setActionMsg(`❌ ${e instanceof Error ? e.message : "保存失败"}`)
    } finally {
      setSaving(false)
    }
  }

  const handleRelease = async (action: string, extra?: Record<string, unknown>) => {
    setSubmitting(true)
    setActionMsg("")
    const latestVersion = versions[0]?.version_no ?? 1
    try {
      const res = await fetch(`/api/admin/config/${packId}/release`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, version_no: latestVersion, ...extra }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || "操作失败")
      setActionMsg(`✅ ${action} 成功`)
      await loadDetail()
    } catch (e: unknown) {
      setActionMsg(`❌ ${e instanceof Error ? e.message : "操作失败"}`)
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <div className="flex items-center justify-center h-screen text-slate-400 text-sm">加载中…</div>
  if (!pack)   return <div className="flex items-center justify-center h-screen text-slate-400 text-sm">配置包不存在</div>

  const status = STATUS_META[pack.status] ?? { label: pack.status, color: "bg-gray-100 text-gray-600" }
  const weightGroups = ["activity", "hotel", "dining", "rhythm"] as const
  const groupLabels = { activity: "活动权重", hotel: "酒店权重", dining: "餐厅权重", rhythm: "节奏权重" }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-3 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/admin/config" className="text-slate-400 hover:text-slate-600 text-sm">← 返回</Link>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-sm font-semibold text-slate-900">{pack.name}</h1>
                <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${status.color}`}>
                  {status.label}
                </span>
                {pack.active_version_no && (
                  <span className="text-[11px] text-slate-400">v{pack.active_version_no}</span>
                )}
              </div>
              <p className="text-xs text-slate-500">{pack.pack_type} · {pack.pack_id.slice(0, 8)}</p>
            </div>
          </div>

          {/* 操作按钮 */}
          <div className="flex items-center gap-2">
            {actionMsg && (
              <span className="text-xs text-slate-600 mr-2">{actionMsg}</span>
            )}
            <button
              onClick={handleSaveDraft}
              disabled={saving}
              className="text-xs px-3 py-1.5 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            >
              {saving ? "保存中…" : "💾 保存草稿"}
            </button>
            {pack.status === "draft" && (
              <button
                onClick={() => handleRelease("submit")}
                disabled={submitting}
                className="text-xs px-3 py-1.5 rounded-lg bg-amber-500 text-white hover:bg-amber-600 disabled:opacity-50"
              >
                📤 送审
              </button>
            )}
            {pack.status === "approved" && (
              <button
                onClick={() => handleRelease("activate")}
                disabled={submitting}
                className="text-xs px-3 py-1.5 rounded-lg bg-green-600 text-white hover:bg-green-700 disabled:opacity-50"
              >
                🚀 激活
              </button>
            )}
            {pack.status === "active" && (
              <button
                onClick={() => {
                  const reason = window.prompt("回滚原因：")
                  if (reason !== null) handleRelease("rollback", { rollback_reason: reason })
                }}
                disabled={submitting}
                className="text-xs px-3 py-1.5 rounded-lg bg-red-100 text-red-700 hover:bg-red-200 disabled:opacity-50"
              >
                ↩️ 一键回滚
              </button>
            )}
          </div>
        </div>
      </header>

      <div className="max-w-5xl mx-auto p-6">
        {/* 变更说明 */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 mb-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">变更摘要</label>
              <input
                value={changeSummary}
                onChange={(e) => setChangeSummary(e.target.value)}
                placeholder="简要说明这次改了什么"
                className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-300"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">原因</label>
              <input
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="为什么要做这个调整？"
                className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-300"
              />
            </div>
          </div>
        </div>

        {/* Tab 导航 */}
        <div className="flex gap-1 mb-4 bg-white rounded-xl border border-slate-200 p-1">
          {(["weights", "thresholds", "switches", "scopes", "history"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 text-xs py-1.5 rounded-lg font-medium transition-colors ${
                activeTab === tab
                  ? "bg-indigo-600 text-white"
                  : "text-slate-600 hover:bg-slate-50"
              }`}
            >
              {{ weights: "⚖️ 权重", thresholds: "📏 阈值", switches: "🔀 开关", scopes: "🎯 作用域", history: "📋 历史" }[tab]}
            </button>
          ))}
        </div>

        {/* Tab 内容 */}
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          {activeTab === "weights" && (
            <div>
              {weightGroups.map((group) => {
                const keys = Object.entries(WEIGHT_DEFINITIONS)
                  .filter(([, v]) => v.group === group)
                  .map(([k]) => k)
                return (
                  <div key={group} className="mb-6">
                    <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
                      {groupLabels[group]}
                    </h3>
                    {keys.map((k) => (
                      <WeightSlider
                        key={k}
                        defKey={k}
                        value={editWeights[k] ?? WEIGHT_DEFINITIONS[k].default}
                        onChange={(v) => setEditWeights((prev) => ({ ...prev, [k]: v }))}
                      />
                    ))}
                  </div>
                )
              })}
            </div>
          )}

          {activeTab === "thresholds" && (
            <div>
              {Object.entries(THRESHOLD_DEFINITIONS).map(([k, def]) => (
                <div key={k} className="mb-4">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-1.5">
                      {def.danger && <span className="text-red-500 text-xs">⚠️</span>}
                      <span className="text-xs font-medium text-slate-700">{def.label}</span>
                      <span className="text-[10px] text-slate-400">({def.hint})</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-slate-400">默认: {def.default}{def.unit}</span>
                      <input
                        type="number"
                        value={editThresholds[k] ?? def.default}
                        step={k.includes("pct") || k.includes("redline") || k.includes("threshold") ? 0.05 : 1}
                        min={def.min}
                        max={def.max}
                        onChange={(e) => setEditThresholds((prev) => ({ ...prev, [k]: Number(e.target.value) }))}
                        className="w-20 text-xs border border-slate-200 rounded px-1.5 py-0.5 text-right"
                      />
                      {def.unit && <span className="text-xs text-slate-400">{def.unit}</span>}
                    </div>
                  </div>
                  <input
                    type="range"
                    min={def.min}
                    max={def.max}
                    step={k.includes("pct") || k.includes("redline") || k.includes("threshold") ? 0.05 : 1}
                    value={editThresholds[k] ?? def.default}
                    onChange={(e) => setEditThresholds((prev) => ({ ...prev, [k]: Number(e.target.value) }))}
                    className="w-full h-1.5 rounded-full appearance-none cursor-pointer bg-slate-200"
                  />
                  <div className="flex justify-between text-[10px] text-slate-400">
                    <span>{def.min}{def.unit}</span>
                    <span>{def.max}{def.unit}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === "switches" && (
            <div>
              <p className="text-xs text-slate-500 mb-4">⚠️ 标记"危险"的开关会影响全站行为，请谨慎操作。</p>
              {Object.keys(SWITCH_DEFINITIONS).map((k) => (
                <SwitchToggle
                  key={k}
                  defKey={k}
                  value={editSwitches[k] ?? false}
                  onChange={(v) => setEditSwitches((prev) => ({ ...prev, [k]: v }))}
                />
              ))}
            </div>
          )}

          {activeTab === "scopes" && (
            <div>
              <p className="text-xs text-slate-500 mb-4">
                此配置包的作用域绑定。优先级：plan_override &gt; segment &gt; circle &gt; global。
              </p>
              {scopes.length === 0 ? (
                <p className="text-sm text-slate-400 text-center py-8">暂无作用域绑定（全局生效）</p>
              ) : (
                <div className="space-y-2">
                  {scopes.map((s) => (
                    <div key={s.scope_id} className={`flex items-center justify-between p-3 rounded-lg border ${s.is_active ? "border-indigo-200 bg-indigo-50" : "border-slate-200"}`}>
                      <div>
                        <p className="text-xs font-medium text-slate-800">
                          {s.scope_type}
                          {s.scope_value ? `: ${s.scope_value}` : "（全局）"}
                        </p>
                        <p className="text-[10px] text-slate-400">
                          灰度 {Math.round((s.rollout_pct ?? 1) * 100)}% · {s.is_active ? "已激活" : "未激活"}
                        </p>
                      </div>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full ${s.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
                        {s.is_active ? "生效" : "停用"}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === "history" && (
            <div>
              <div className="space-y-2">
                {releases.length === 0 ? (
                  <p className="text-sm text-slate-400 text-center py-8">暂无发布记录</p>
                ) : (
                  releases.map((r) => (
                    <div key={r.record_id} className="flex items-start gap-3 p-3 rounded-lg border border-slate-100">
                      <div className="w-2 h-2 rounded-full bg-indigo-400 mt-1.5 flex-shrink-0" />
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <p className="text-xs font-medium text-slate-800">
                            {ACTION_RECORD_LABELS[r.action] ?? r.action}
                          </p>
                          <span className="text-[10px] text-slate-400">v{r.version_no}</span>
                        </div>
                        {r.notes && <p className="text-[10px] text-slate-500 mt-0.5">{r.notes}</p>}
                      </div>
                      <span className="text-[10px] text-slate-400 flex-shrink-0">
                        {new Date(r.created_at).toLocaleString("zh-CN", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </div>
                  ))
                )}
              </div>

              {/* 版本快照 */}
              {versions.length > 0 && (
                <div className="mt-6 pt-4 border-t border-slate-100">
                  <h3 className="text-xs font-semibold text-slate-500 mb-3">版本快照</h3>
                  <div className="space-y-2">
                    {versions.map((v) => (
                      <div key={v.version_id} className="p-3 rounded-lg border border-slate-100 bg-slate-50">
                        <div className="flex items-center justify-between">
                          <p className="text-xs font-medium text-slate-700">
                            v{v.version_no}
                            {v.version_no === pack.active_version_no && (
                              <span className="ml-2 text-[10px] bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full">当前激活</span>
                            )}
                          </p>
                          <span className="text-[10px] text-slate-400">
                            {new Date(v.created_at).toLocaleString("zh-CN")}
                          </span>
                        </div>
                        {v.change_summary && (
                          <p className="text-[10px] text-slate-500 mt-1">{v.change_summary}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
