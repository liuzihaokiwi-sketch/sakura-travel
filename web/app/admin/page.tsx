"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { type OrderItem, fetchOrders } from "@/lib/admin-api";

// ── Status column config（按新状态流分 6 列）────────────────────────────────
const COLUMNS = [
  {
    key: "pending",
    label: "待处理",
    icon: "📋",
    statuses: ["new", "sample_viewed", "quiz_submitted"],
    bg: "bg-amber-50",
    border: "border-amber-200",
    badge: "bg-amber-100 text-amber-800",
  },
  {
    key: "paid",
    label: "已付费",
    icon: "💰",
    statuses: ["paid"],
    bg: "bg-green-50",
    border: "border-green-200",
    badge: "bg-green-100 text-green-800",
  },
  {
    key: "form",
    label: "表单中",
    icon: "📝",
    statuses: ["detail_filling", "detail_submitted", "needs_fix"],
    bg: "bg-blue-50",
    border: "border-blue-200",
    badge: "bg-blue-100 text-blue-800",
  },
  {
    key: "validated",
    label: "待生成",
    icon: "✅",
    statuses: ["validating", "validated"],
    bg: "bg-violet-50",
    border: "border-violet-200",
    badge: "bg-violet-100 text-violet-800",
  },
  {
    key: "generating",
    label: "生成中",
    icon: "⚙️",
    statuses: ["generating", "generating_full", "assembling", "reviewing"],
    bg: "bg-sky-50",
    border: "border-sky-200",
    badge: "bg-sky-100 text-sky-800",
  },
  {
    key: "done",
    label: "已交付",
    icon: "🎉",
    statuses: ["done", "delivered"],
    bg: "bg-emerald-50",
    border: "border-emerald-200",
    badge: "bg-emerald-100 text-emerald-800",
  },
  {
    key: "using",
    label: "使用中",
    icon: "✈️",
    statuses: ["using"],
    bg: "bg-teal-50",
    border: "border-teal-200",
    badge: "bg-teal-100 text-teal-800",
  },
];

const STATUS_LABELS: Record<string, string> = {
  new: "新提交",
  sample_viewed: "已看样片",
  quiz_submitted: "已提交问卷",
  paid: "已付费",
  detail_filling: "填写详细信息中",
  detail_submitted: "详细信息已提交",
  validating: "校验中",
  needs_fix: "需补充信息",
  validated: "校验通过",
  generating: "生成中",
  generating_full: "完整生成中",
  assembling: "装配中",
  reviewing: "审核中",
  done: "攻略完成",
  delivered: "已交付",
  using: "使用中",
  archived: "已归档",
  refunded: "已退款",
  cancelled: "已取消",
};

const SKU_LABELS: Record<string, string> = {
  standard_198: "完整攻略 ¥198起",
  standard_248: "行程优化版 ¥248（旧）",
  premium_888: "尊享定制版 ¥888",
  basic_free: "免费预览",
  free_preview: "免费预览",
};

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}分钟前`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}小时前`;
  const days = Math.floor(hours / 24);
  return `${days}天前`;
}

// ── Order Card ───────────────────────────────────────────────────────────────
function OrderCard({ order }: { order: OrderItem }) {
  const isUrgent =
    Date.now() - new Date(order.created_at).getTime() > 2 * 60 * 60 * 1000 &&
    !["delivered", "refunded", "cancelled"].includes(order.status);

  return (
    <Link
      href={`/admin/order/${order.order_id}`}
      className="block bg-white rounded-lg border border-slate-200 p-4 hover:shadow-md hover:border-slate-300 transition-all cursor-pointer"
    >
      <div className="flex items-start justify-between mb-2">
        <span className="font-mono text-xs text-slate-500">
          #{order.order_id.slice(0, 8)}
        </span>
        <div className="flex gap-1">
          {isUrgent && (
            <span className="text-xs px-1.5 py-0.5 rounded bg-red-100 text-red-700 font-medium">
              紧急
            </span>
          )}
          <span className="text-xs px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
            {STATUS_LABELS[order.status] || order.status}
          </span>
        </div>
      </div>

      <div className="space-y-1.5">
        {order.destination && (
          <p className="text-sm font-medium text-slate-900">
            {order.destination}
            {order.duration_days && (
              <span className="text-slate-500 font-normal">
                {" "}
                · {order.duration_days}天
              </span>
            )}
          </p>
        )}

        <p className="text-xs text-slate-500">
          {SKU_LABELS[order.sku_id] || order.sku_id}
        </p>

        {order.wechat_id && (
          <p className="text-xs text-slate-400">微信: {order.wechat_id}</p>
        )}
      </div>

      <div className="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between">
        <span className="text-xs text-slate-400">{timeAgo(order.created_at)}</span>
        <span className="text-xs font-medium text-slate-600">
          ¥{order.amount_cny}
        </span>
      </div>
    </Link>
  );
}

// ── Kanban Column ────────────────────────────────────────────────────────────
function KanbanColumn({
  label,
  icon,
  orders,
  bg,
  border,
  badge,
}: {
  label: string;
  icon: string;
  orders: OrderItem[];
  bg: string;
  border: string;
  badge: string;
}) {
  return (
    <div className={`flex-1 min-w-[240px] max-w-[320px] rounded-xl ${bg} border ${border} p-4`} style={{ scrollSnapAlign: "start" }}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-slate-700">
          {icon} {label}
        </h2>
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${badge}`}>
          {orders.length}
        </span>
      </div>
      <div className="space-y-3">
        {orders.length === 0 ? (
          <p className="text-center text-sm text-slate-400 py-8">暂无订单</p>
        ) : (
          orders.map((order) => <OrderCard key={order.order_id} order={order} />)
        )}
      </div>
    </div>
  );
}

// ── Main Page ────────────────────────────────────────────────────────────────
export default function AdminDashboard() {
  const [orders, setOrders] = useState<OrderItem[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const loadOrders = useCallback(async () => {
    try {
      const all = await fetchOrders();
      setOrders(all);
    } catch (e) {
      console.error("Failed to load orders:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadOrders();
    const interval = setInterval(loadOrders, 30000); // Poll every 30s
    return () => clearInterval(interval);
  }, [loadOrders]);

  const handleLogout = async () => {
    await fetch("/api/admin/logout", { method: "POST" });
    router.push("/admin/login");
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-3">
        <div className="max-w-[1600px] mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-slate-900 rounded-lg flex items-center justify-center">
              <span className="text-white text-sm">✈️</span>
            </div>
            <div>
              <h1 className="text-sm font-semibold text-slate-900">Travel AI 管理后台</h1>
              <p className="text-xs text-slate-500">订单管理 · 审核工作台</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Link
              href="/admin/trace"
              className="text-xs text-slate-500 hover:text-slate-900 transition-colors flex items-center gap-1"
            >
              🔍 生成追踪
            </Link>
            <Link
              href="/admin/evals"
              className="text-xs text-slate-500 hover:text-slate-900 transition-colors flex items-center gap-1"
            >
              📈 评测仪表板
            </Link>
            <Link
              href="/admin/conversion"
              className="text-xs text-slate-500 hover:text-slate-900 transition-colors flex items-center gap-1"
            >
              📊 转化看板
            </Link>
            <Link
              href="/admin/history"
              className="text-xs text-slate-500 hover:text-slate-900 transition-colors flex items-center gap-1"
            >
              📁 历史表单
            </Link>
            <Link
              href="/admin/catalog"
              className="text-xs font-medium text-indigo-600 hover:text-indigo-800 transition-colors flex items-center gap-1 px-2.5 py-1 bg-indigo-50 rounded-lg border border-indigo-200"
            >
              🗂️ 内容库
            </Link>
            <span className="text-xs text-slate-400">
              共 {orders.length} 个订单 · 每 30 秒刷新
            </span>
            <button
              onClick={handleLogout}
              className="text-xs text-slate-500 hover:text-slate-900 transition-colors"
            >
              退出登录
            </button>
          </div>
        </div>
      </header>

      {/* Kanban — 按 COLUMNS 配置动态渲染 6 列 */}
      <div className="max-w-[1600px] mx-auto p-6">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-sm text-slate-400">加载中...</div>
          </div>
        ) : (
          <div className="flex gap-4 overflow-x-auto pb-4" style={{ scrollSnapType: "x mandatory" }}>
            {COLUMNS.map((col) => (
              <KanbanColumn
                key={col.key}
                label={col.label}
                icon={col.icon}
                orders={orders.filter((o) => col.statuses.includes(o.status))}
                bg={col.bg}
                border={col.border}
                badge={col.badge}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
