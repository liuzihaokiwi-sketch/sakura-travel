"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { type OrderItem, fetchOrderById, publishOrder, rejectOrder, updateOrderStatus } from "@/lib/admin-api";

/* ── 11 状态完整标签配置 ─────────────────────────────────────────────────────── */

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: string }> = {
  new:              { label: "新提交",         color: "bg-amber-100 text-amber-700",   icon: "📋" },
  sample_viewed:    { label: "已查看样片",     color: "bg-orange-100 text-orange-700",  icon: "👀" },
  paid:             { label: "已付费",         color: "bg-green-100 text-green-700",    icon: "💰" },
  detail_filling:   { label: "详情填写中",     color: "bg-blue-100 text-blue-700",      icon: "📝" },
  detail_submitted: { label: "详情已提交",     color: "bg-blue-100 text-blue-700",      icon: "📨" },
  validating:       { label: "校验中",         color: "bg-violet-100 text-violet-700",  icon: "🔍" },
  needs_fix:        { label: "需补充信息",     color: "bg-red-100 text-red-600",        icon: "⚠️" },
  validated:        { label: "校验通过",       color: "bg-violet-100 text-violet-700",  icon: "✅" },
  generating:       { label: "生成中",         color: "bg-sky-100 text-sky-700",        icon: "⚙️" },
  generating_full:  { label: "完整生成中",     color: "bg-sky-100 text-sky-700",        icon: "⚙️" },
  done:             { label: "攻略完成",       color: "bg-emerald-100 text-emerald-700",icon: "🎉" },
  delivered:        { label: "已交付",         color: "bg-green-100 text-green-700",    icon: "📬" },
  using:            { label: "使用中",         color: "bg-teal-100 text-teal-700",      icon: "✈️" },
  archived:         { label: "已归档",         color: "bg-gray-100 text-gray-500",      icon: "📁" },
  cancelled:        { label: "已取消",         color: "bg-gray-100 text-gray-500",      icon: "❌" },
  refunded:         { label: "已退款",         color: "bg-red-100 text-red-600",        icon: "💸" },
};

/* ── 状态机流转：当前状态 → 可执行的操作列表 ─────────────────────────────────── */

interface StatusAction {
  label: string;
  target: string;
  style: "primary" | "secondary" | "danger";
  confirm?: string;
}

const STATUS_ACTIONS: Record<string, StatusAction[]> = {
  new: [
    { label: "标记已看样片", target: "sample_viewed", style: "secondary" },
    { label: "取消订单",     target: "cancelled",     style: "danger", confirm: "确定取消该订单？" },
  ],
  sample_viewed: [
    { label: "确认付费",  target: "paid",      style: "primary" },
    { label: "取消订单",  target: "cancelled", style: "danger", confirm: "确定取消该订单？" },
  ],
  paid: [
    { label: "开始填写详情", target: "detail_filling", style: "primary" },
    { label: "申请退款",     target: "refunded",       style: "danger", confirm: "确定退款？" },
  ],
  detail_filling: [
    { label: "提交详情", target: "detail_submitted", style: "primary" },
  ],
  detail_submitted: [
    { label: "开始校验", target: "validating", style: "primary" },
  ],
  validating: [
    { label: "校验通过", target: "validated", style: "primary" },
    { label: "需补充信息", target: "needs_fix", style: "secondary" },
  ],
  needs_fix: [
    { label: "返回填写", target: "detail_filling", style: "secondary" },
  ],
  validated: [
    { label: "🚀 开始生成攻略", target: "generating", style: "primary" },
  ],
  generating: [
    { label: "标记完成", target: "done", style: "primary" },
  ],
  done: [
    { label: "📤 交付给用户", target: "delivered", style: "primary" },
    { label: "打回重做",     target: "generating", style: "danger", confirm: "确定打回重新生成？" },
  ],
  delivered: [
    { label: "✈️ 标记使用中", target: "using",    style: "primary" },
    { label: "申请退款",       target: "refunded", style: "danger", confirm: "确定退款？" },
  ],
  using: [
    { label: "📁 归档", target: "archived", style: "secondary", confirm: "确定归档？旅程结束后归档。" },
  ],
};

const PARTY_LABELS: Record<string, string> = {
  solo: "独自出行", couple: "情侣/夫妻", family: "带孩子",
  parents: "带父母", friends: "朋友闺蜜",
};
const EXP_LABELS: Record<string, string> = {
  first_time: "第一次去日本", few_times: "去过 1–2 次", experienced: "去过很多次",
};
const PLAY_LABELS: Record<string, string> = {
  multi_city: "多城顺玩", single_city: "一地深玩", undecided: "还没想好",
};
const BUDGET_LABELS: Record<string, string> = {
  better_stay: "住得更好", better_food: "吃得更好",
  better_experience: "体验更特别", balanced: "更均衡", best_value: "看重性价比",
};
const STYLE_LABELS: Record<string, string> = {
  culture: "🏛 文化古迹", food: "🍣 美食探店", photo: "📸 拍照出片",
  shopping: "🛍 购物买买", nature: "🌿 自然风景", relax: "🧖 慢节奏",
};

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins} 分钟前`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} 小时前`;
  return `${Math.floor(hours / 24)} 天前`;
}

/* ── 状态进度条 ────────────────────────────────────────────────────────────── */

const PROGRESS_STEPS = [
  { key: "new",            label: "提交" },
  { key: "paid",           label: "付费" },
  { key: "detail_filling", label: "填表" },
  { key: "validated",      label: "校验" },
  { key: "generating",     label: "生成" },
  { key: "done",           label: "完成" },
  { key: "delivered",      label: "交付" },
];

const STATUS_TO_PROGRESS: Record<string, number> = {
  new: 0, sample_viewed: 0, paid: 1, detail_filling: 2,
  detail_submitted: 2, validating: 3, needs_fix: 2, validated: 3,
  generating: 4, done: 5, delivered: 6, cancelled: -1, refunded: -1,
};

function ProgressBar({ status }: { status: string }) {
  const current = STATUS_TO_PROGRESS[status] ?? -1;
  if (current < 0) return null;

  return (
    <div className="flex items-center gap-1 w-full">
      {PROGRESS_STEPS.map((step, i) => {
        const done = i <= current;
        const active = i === current;
        return (
          <div key={step.key} className="flex-1 flex flex-col items-center gap-1.5">
            <div className="flex items-center w-full">
              {i > 0 && (
                <div className={`flex-1 h-0.5 ${i <= current ? "bg-indigo-400" : "bg-gray-200"}`} />
              )}
              <div className={[
                "w-3 h-3 rounded-full flex-shrink-0 transition-all",
                done ? "bg-indigo-500" : "bg-gray-200",
                active ? "ring-4 ring-indigo-100 scale-125" : "",
              ].join(" ")} />
              {i < PROGRESS_STEPS.length - 1 && (
                <div className={`flex-1 h-0.5 ${i < current ? "bg-indigo-400" : "bg-gray-200"}`} />
              )}
            </div>
            <span className={`text-[10px] ${active ? "text-indigo-600 font-bold" : done ? "text-gray-500" : "text-gray-300"}`}>
              {step.label}
            </span>
          </div>
        );
      })}
    </div>
  );
}

/* ── Action Button ─────────────────────────────────────────────────────────── */

function ActionButton({
  action,
  loading,
  onClick,
}: {
  action: StatusAction;
  loading: boolean;
  onClick: () => void;
}) {
  const styles = {
    primary:   "bg-gradient-to-r from-indigo-500 to-blue-500 text-white shadow-md hover:shadow-lg hover:scale-[1.02]",
    secondary: "bg-white border-2 border-gray-200 text-gray-700 hover:bg-gray-50 hover:border-gray-300",
    danger:    "bg-white border-2 border-red-200 text-red-600 hover:bg-red-50 hover:border-red-300",
  };

  return (
    <button
      onClick={onClick}
      disabled={loading}
      className={`flex-1 min-w-[140px] py-3 px-5 rounded-xl font-semibold text-sm transition-all duration-200 disabled:opacity-50 disabled:pointer-events-none ${styles[action.style]}`}
    >
      {loading ? (
        <span className="flex items-center justify-center gap-2">
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          处理中…
        </span>
      ) : (
        action.label
      )}
    </button>
  );
}

/* ── Main Page ─────────────────────────────────────────────────────────────── */

export default function OrderDetailPage() {
  const params = useParams();
  const router = useRouter();
  const orderId = params.id as string;

  const [order, setOrder] = useState<OrderItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [formId, setFormId] = useState<string | null>(null);
  const [formLoading, setFormLoading] = useState(false);
  const [linkCopied, setLinkCopied] = useState(false);

  useEffect(() => {
    fetchOrderById(orderId).then((data) => {
      setOrder(data);
      setLoading(false);
    });
    // 检查是否已有表单
    fetch(`/api/detail-forms/by-submission/${orderId}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => { if (d?.form_id) setFormId(d.form_id); })
      .catch(() => {});
  }, [orderId]);

  async function handleAction(action: StatusAction) {
    if (action.confirm && !window.confirm(action.confirm)) return;
    setActionLoading(action.target);
    let ok: boolean;
    if (action.target === "delivered") {
      ok = await publishOrder(orderId);
    } else if (action.target === "rejected") {
      ok = await rejectOrder(orderId);
    } else {
      ok = await updateOrderStatus(orderId, action.target, action.label);
    }
    if (ok) {
      const fresh = await fetchOrderById(orderId);
      setOrder(fresh);
    } else {
      alert("操作失败，请重试");
    }
    setActionLoading(null);
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-gray-100 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <svg className="animate-spin h-6 w-6 text-indigo-400" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <p className="text-sm text-slate-400">加载中…</p>
        </div>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-gray-100 flex flex-col items-center justify-center gap-4">
        <p className="text-sm text-slate-500">订单不存在</p>
        <Link href="/admin" className="text-sm text-indigo-600 hover:text-indigo-800 font-medium">
          ← 返回看板
        </Link>
      </div>
    );
  }

  const statusCfg = STATUS_CONFIG[order.status] || { label: order.status, color: "bg-slate-100 text-slate-600", icon: "❓" };
  const actions = STATUS_ACTIONS[order.status] ?? [];
  const isTerminal = ["cancelled", "refunded"].includes(order.status);
  const isGenerating = order.status === "generating";

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-gray-100">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-gray-200/60 px-6 py-3 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              href="/admin"
              className="text-sm text-slate-500 hover:text-slate-900 transition-colors flex items-center gap-1"
            >
              ← 看板
            </Link>
            <span className="text-gray-200">|</span>
            <span className="font-mono text-xs text-slate-400">#{orderId.slice(0, 8)}</span>
            <span className={`text-xs px-3 py-1 rounded-full font-semibold ${statusCfg.color}`}>
              {statusCfg.icon} {statusCfg.label}
            </span>
          </div>
          <div className="text-xs text-slate-400">
            提交于 {timeAgo(order.created_at)}
          </div>
        </div>
      </header>

      <div className="max-w-4xl mx-auto p-6 space-y-5">
        {/* 进度条 */}
        {!isTerminal && (
          <div className="bg-white rounded-2xl border border-gray-200/60 shadow-sm p-5">
            <ProgressBar status={order.status} />
          </div>
        )}

        {/* ── 用户信息卡片 ── */}
        <div className="bg-white rounded-2xl border border-gray-200/60 shadow-sm p-6">
          <h2 className="text-base font-bold text-gray-900 mb-4 flex items-center gap-2">
            📋 用户需求
          </h2>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <InfoItem label="姓名" value={order.name || "—"} />
            <InfoItem label="目的地" value={order.destination} highlight />
            <InfoItem label="天数" value={`${order.duration_days} 天`} highlight />
            <InfoItem label="人数" value={order.people_count ? `${order.people_count} 人` : "—"} />
            <InfoItem label="同行人" value={PARTY_LABELS[order.party_type] || order.party_type} />
            <InfoItem label="日本经验" value={order.japan_experience ? EXP_LABELS[order.japan_experience] || order.japan_experience : "—"} />
            <InfoItem label="玩法偏好" value={order.play_mode ? PLAY_LABELS[order.play_mode] || order.play_mode : "—"} />
            <InfoItem label="预算重点" value={order.budget_focus ? BUDGET_LABELS[order.budget_focus] || order.budget_focus : "—"} />
          </div>

          {/* 风格标签 */}
          {order.styles && order.styles.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-100">
              <p className="text-xs text-gray-400 mb-2">旅行风格</p>
              <div className="flex flex-wrap gap-2">
                {order.styles.map((s) => (
                  <span
                    key={s}
                    className="text-xs px-3 py-1.5 rounded-full bg-gradient-to-r from-amber-50 to-orange-50 text-amber-700 border border-amber-200/60 font-medium"
                  >
                    {STYLE_LABELS[s] || s}
                  </span>
                ))}
              </div>
            </div>
          )}

          {order.wechat_id && (
            <div className="mt-4 pt-4 border-t border-gray-100 flex items-center gap-2">
              <span className="text-xs text-gray-400">微信号</span>
              <span className="text-sm font-mono text-gray-800 bg-gray-50 px-2.5 py-1 rounded-lg">
                {order.wechat_id}
              </span>
            </div>
          )}
        </div>

        {/* ── 操作区 ── */}
        <div className="bg-white rounded-2xl border border-gray-200/60 shadow-sm p-6">
          <h2 className="text-base font-bold text-gray-900 mb-4 flex items-center gap-2">
            🎯 操作
          </h2>

          {/* 生成中 — 旋转动画 */}
          {isGenerating && (
            <div className="text-center py-8">
              <div className="inline-flex items-center gap-3 px-6 py-3 rounded-2xl bg-sky-50 border border-sky-200">
                <svg className="animate-spin h-5 w-5 text-sky-600" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                <span className="text-sm font-medium text-sky-700">正在生成攻略…</span>
              </div>
              <p className="text-xs text-gray-400 mt-3">生成完成后可预览并交付</p>
            </div>
          )}

          {/* 终态 */}
          {isTerminal && (
            <div className="text-center py-6">
              <span className="text-3xl">{statusCfg.icon}</span>
              <p className="text-sm font-medium text-gray-500 mt-2">{statusCfg.label}</p>
            </div>
          )}

          {/* done 状态 — 预览按钮 */}
          {(order.status === "done" || order.status === "delivered") && (
            <div className="mb-4">
              <button
                onClick={() => window.open(`/plan/${orderId}`, "_blank")}
                className="w-full py-3 px-4 rounded-xl border-2 border-indigo-200 text-indigo-600 font-semibold text-sm hover:bg-indigo-50 transition-colors flex items-center justify-center gap-2"
              >
                👁️ 预览攻略
              </button>
            </div>
          )}

          {/* 动态操作按钮 */}
          {actions.length > 0 && (
            <div className="flex flex-wrap gap-3">
              {actions.map((action) => (
                <ActionButton
                  key={action.target}
                  action={action}
                  loading={actionLoading === action.target}
                  onClick={() => handleAction(action)}
                />
              ))}
            </div>
          )}
        </div>

        {/* ── 📝 表单管理 ── */}
        {!isTerminal && (
          <div className="bg-white rounded-2xl border border-gray-200/60 shadow-sm p-6">
            <h2 className="text-base font-bold text-gray-900 mb-4 flex items-center gap-2">
              📝 详细表单
            </h2>

            {formId ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <span className="text-green-500">✓</span>
                  表单已创建
                  <span className="font-mono text-xs text-gray-400">#{formId.slice(0, 8)}</span>
                </div>

                {/* 复制链接按钮 */}
                <div className="flex flex-wrap gap-3">
                  <button
                    onClick={() => {
                      const url = `${window.location.origin}/detail-form/${formId}`;
                      navigator.clipboard.writeText(url).then(() => {
                        setLinkCopied(true);
                        setTimeout(() => setLinkCopied(false), 2000);
                      });
                    }}
                    className="flex-1 py-3 px-4 rounded-xl bg-gradient-to-r from-blue-500 to-indigo-500 text-white font-semibold text-sm shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2"
                  >
                    {linkCopied ? "✓ 链接已复制！" : "📋 复制表单链接（发给客户）"}
                  </button>
                  <button
                    onClick={() => window.open(`/detail-form/${formId}`, "_blank")}
                    className="py-3 px-4 rounded-xl border-2 border-gray-200 text-gray-700 font-semibold text-sm hover:bg-gray-50 transition-all"
                  >
                    👁️ 查看/编辑表单
                  </button>
                </div>

                <p className="text-xs text-gray-400">
                  💡 客服和用户都可以通过此链接反复修改表单内容，无需登录
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                <p className="text-sm text-gray-500">用户付费后，创建表单并将链接发给客户填写</p>
                <button
                  onClick={async () => {
                    setFormLoading(true);
                    try {
                      const res = await fetch(`/api/detail-forms/${orderId}/create`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ submission_id: orderId }),
                      });
                      if (res.ok) {
                        const data = await res.json();
                        setFormId(data.form_id);
                      } else {
                        const err = await res.json().catch(() => ({}));
                        alert(err.detail || "创建失败");
                      }
                    } catch {
                      alert("网络错误，请重试");
                    }
                    setFormLoading(false);
                  }}
                  disabled={formLoading}
                  className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-blue-500 to-indigo-500 text-white font-semibold text-sm shadow-md hover:shadow-lg transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {formLoading ? (
                    <>
                      <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      创建中…
                    </>
                  ) : (
                    "📝 创建详细表单"
                  )}
                </button>
              </div>
            )}
          </div>
        )}

        {/* ── 备注 ── */}
        {order.notes && (
          <div className="bg-white rounded-2xl border border-gray-200/60 shadow-sm p-6">
            <h2 className="text-base font-bold text-gray-900 mb-2">📝 备注</h2>
            <p className="text-sm text-gray-600 leading-relaxed">{order.notes}</p>
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Helper components ─────────────────────────────────────────────────────── */

function InfoItem({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div>
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      <p className={`text-sm font-medium ${highlight ? "text-gray-900" : "text-gray-600"}`}>
        {value}
      </p>
    </div>
  );
}