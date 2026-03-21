"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { type OrderItem, fetchOrderById, updateOrderStatus, confirmPayment, refundOrder } from "@/lib/admin-api";

// ── Mock plan data (same structure as /plan/[id]) ────────────────────────────
const MOCK_PLAN = {
  title: "东京 7 日 · 樱花季深度行程",
  tags: ["👫 两人出行", "📸 出片优先", "🍣 美食探索", "🌸 樱花季"],
  dates: "2026年3月28日 — 4月3日",
  days: [
    {
      num: 1, theme: "浅草·上野 — 历史与下町风情",
      items: [
        { time: "09:00", icon: "🌸", place: "上野恩赐公园", reason: "早上人少，樱花光线最柔和", duration: "1.5h", id: "e001" },
        { time: "10:30", icon: "🏛️", place: "东京国立博物馆", reason: "就在公园旁，不用额外赶路", duration: "1h", id: "e002" },
        { time: "12:00", icon: "🍜", place: "浅草 弁天（拉面）", reason: "浓厚豚骨系，步行3分钟到浅草寺", duration: "1h", id: "e003" },
        { time: "13:30", icon: "⛩️", place: "浅草寺 + 仲见世通", reason: "午后人流比上午少30%", duration: "1.5h", id: "e004" },
        { time: "15:30", icon: "🛍️", place: "阿美横丁", reason: "从浅草走10分钟，顺路不回头", duration: "1h", id: "e005" },
      ],
    },
    {
      num: 2, theme: "涩谷·原宿 — 潮流与青春",
      items: [
        { time: "09:30", icon: "⛩️", place: "明治神宫", reason: "早上参拜人少，森林步道清静", duration: "1h", id: "e011" },
        { time: "11:00", icon: "🛍️", place: "竹下通 + 表参道", reason: "潮流聚集地，拍照出片率极高", duration: "2h", id: "e012" },
        { time: "13:00", icon: "🍣", place: "涩谷 回转寿司", reason: "性价比高，不排长队", duration: "1h", id: "e013" },
        { time: "14:30", icon: "🏙️", place: "涩谷 Sky 展望台", reason: "360度城市全景，日落前最佳", duration: "1.5h", id: "e014" },
      ],
    },
    {
      num: 3, theme: "新宿·池袋 — 购物与美食",
      items: [
        { time: "10:00", icon: "🌸", place: "新宿御苑", reason: "樱花品种最多的公园", duration: "2h", id: "e021" },
        { time: "12:30", icon: "🍜", place: "一兰拉面（新宿店）", reason: "经典博多风味", duration: "1h", id: "e022" },
        { time: "14:00", icon: "🛍️", place: "新宿百货商圈", reason: "伊势丹+高岛屋一站式购物", duration: "2h", id: "e023" },
      ],
    },
  ],
};

// ── Alternate candidates for replacement ─────────────────────────────────────
const SPOT_ALTERNATIVES: Record<string, { id: string; name: string; reason: string }[]> = {
  default: [
    { id: "alt1", name: "代代木公园", reason: "人少清静，本地人赏樱首选" },
    { id: "alt2", name: "千�的渊", reason: "护城河樱花倒影，经典打卡点" },
    { id: "alt3", name: "目黑川", reason: "最火网红樱花，但人多" },
    { id: "alt4", name: "六义園", reason: "枝垂樱名所，夜樱很美" },
    { id: "alt5", name: "隅田公园", reason: "河畔樱花道，适合散步" },
  ],
};

const RESTAURANT_ALTERNATIVES = [
  { id: "ralt1", name: "�的里（拉面）", reason: "浓厚鱼介系" },
  { id: "ralt2", name: "天丼 金子半之助", reason: "排队名店但值得" },
  { id: "ralt3", name: "叙叙苑（午市套餐）", reason: "性价比最高的烤肉" },
  { id: "ralt4", name: "Afuri（拉面）", reason: "清爽柚子味" },
  { id: "ralt5", name: "矶丸水产", reason: "海鲜居酒屋，氛围好" },
];

// ── Types ────────────────────────────────────────────────────────────────────
type Tab = "edit" | "prompt" | "history";

interface VersionEntry {
  version: number;
  time: string;
  summary: string;
}

// ── Main Page ────────────────────────────────────────────────────────────────
export default function OrderReviewPage() {
  const params = useParams();
  const router = useRouter();
  const orderId = params.id as string;

  const [order, setOrder] = useState<OrderItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>("edit");
  const [selectedDay, setSelectedDay] = useState(1);
  const [promptText, setPromptText] = useState("");
  const [saving, setSaving] = useState(false);
  const [publishing, setPublishing] = useState(false);

  const [versions] = useState<VersionEntry[]>([
    { version: 1, time: "2026-03-20 14:30", summary: "初始生成" },
  ]);

  useEffect(() => {
    async function load() {
      const data = await fetchOrderById(orderId);
      setOrder(data);
      setLoading(false);
    }
    load();
  }, [orderId]);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "s") {
        e.preventDefault();
        handleSave();
      }
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
        e.preventDefault();
        handlePublish();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  });

  const handleSave = async () => {
    setSaving(true);
    // TODO: save draft via API
    await new Promise((r) => setTimeout(r, 500));
    setSaving(false);
  };

  const handlePublish = async () => {
    if (!confirm("确认发布给用户？")) return;
    setPublishing(true);
    const ok = await updateOrderStatus(orderId, "delivered", "admin_publish");
    if (ok) {
      router.push("/admin");
    } else {
      alert("发布失败，请检查订单状态");
    }
    setPublishing(false);
  };

  const handleReject = async () => {
    if (!confirm("确认打回重新生成？")) return;
    await updateOrderStatus(orderId, "generating", "admin_reject");
    router.push("/admin");
  };

  const handleConfirmPayment = async () => {
    if (!confirm("确认已收到用户付款？这将把订单状态改为「已付款」")) return;
    const ok = await confirmPayment(orderId);
    if (ok) {
      // Refresh order data
      const fresh = await fetchOrderById(orderId);
      setOrder(fresh);
      alert("已确认收款 ✓");
    } else {
      alert("操作失败，请检查订单状态");
    }
  };

  const handleRefund = async () => {
    const reason = prompt(
      "退款原因（必填，会记录到订单）：\n\n常用原因：\n• 用户主动取消旅行\n• 方案质量不满意\n• 重复购买\n• 其他"
    );
    if (!reason) return;
    if (!confirm(`确认退款？\n原因：${reason}\n\n💡 退款话术提示：\n"您好，您的订单退款已处理，1-3个工作日内到账，感谢理解～"`)) return;
    const ok = await refundOrder(orderId, reason);
    if (ok) {
      const fresh = await fetchOrderById(orderId);
      setOrder(fresh);
      alert("退款已处理 ✓");
    } else {
      alert("退款失败，请联系技术支持");
    }
  };

  const currentDay = MOCK_PLAN.days.find((d) => d.num === selectedDay) || MOCK_PLAN.days[0];

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <p className="text-sm text-slate-400">加载中...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Top bar */}
      <header className="bg-white border-b border-slate-200 px-4 py-2.5 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <Link
            href="/admin"
            className="text-sm text-slate-500 hover:text-slate-900 transition-colors"
          >
            ← 返回看板
          </Link>
          <span className="text-xs text-slate-300">|</span>
          <span className="font-mono text-xs text-slate-500">#{orderId.slice(0, 8)}</span>
          {order && (
            <>
              <span className="text-xs text-slate-400">
                {order.destination} · {order.duration_days}天
              </span>
              <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                {order.status}
              </span>
            </>
          )}
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 mr-2">v{versions.length}</span>

          {/* 确认收款（仅 quiz_submitted / preview_sent 状态显示）*/}
          {order && ["quiz_submitted", "preview_sent"].includes(order.status) && (
            <button
              onClick={handleConfirmPayment}
              className="px-3 py-1.5 text-xs border border-green-300 rounded-lg text-green-700 hover:bg-green-50 transition-colors font-medium"
            >
              💰 确认收款
            </button>
          )}

          {/* 退款（已付款/生成中/审核中状态才能退）*/}
          {order && ["paid", "generating", "review", "delivered"].includes(order.status) && (
            <button
              onClick={handleRefund}
              className="px-3 py-1.5 text-xs border border-red-200 rounded-lg text-red-600 hover:bg-red-50 transition-colors"
            >
              退款
            </button>
          )}

          <button
            onClick={handleReject}
            className="px-3 py-1.5 text-xs border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50 transition-colors"
          >
            打回重做
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-3 py-1.5 text-xs border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50 transition-colors"
          >
            {saving ? "保存中..." : "保存草稿"}
          </button>
          <button
            onClick={() => window.open(`/plan/${orderId}`, "_blank")}
            className="px-3 py-1.5 text-xs border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50 transition-colors"
          >
            预览效果
          </button>
          <button
            onClick={handlePublish}
            disabled={publishing}
            className="px-4 py-1.5 text-xs bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors font-medium"
          >
            {publishing ? "发布中..." : "发布给用户 ✓"}
          </button>
        </div>
      </header>

      {/* Main content: left preview + right panel */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: Plan Preview (60%) */}
        <div className="w-[60%] overflow-y-auto border-r border-slate-200 bg-white p-6">
          <div className="max-w-2xl mx-auto">
            <h2 className="text-lg font-semibold text-slate-900 mb-1">{MOCK_PLAN.title}</h2>
            <p className="text-sm text-slate-500 mb-4">{MOCK_PLAN.dates}</p>
            <div className="flex flex-wrap gap-1.5 mb-6">
              {MOCK_PLAN.tags.map((tag) => (
                <span key={tag} className="text-xs px-2 py-1 rounded-full bg-slate-100 text-slate-600">
                  {tag}
                </span>
              ))}
            </div>

            {/* Day cards */}
            {MOCK_PLAN.days.map((day) => (
              <div
                key={day.num}
                className={`mb-6 rounded-xl border p-5 transition-all ${
                  day.num === selectedDay
                    ? "border-blue-300 bg-blue-50/30 ring-1 ring-blue-200"
                    : "border-slate-200 bg-white"
                }`}
                onClick={() => setSelectedDay(day.num)}
              >
                <h3 className="text-sm font-semibold text-slate-800 mb-3">
                  Day {day.num} · {day.theme}
                </h3>
                <div className="space-y-2.5">
                  {day.items.map((item, idx) => (
                    <div
                      key={idx}
                      className="flex items-start gap-3 text-sm group"
                    >
                      <span className="text-xs text-slate-400 font-mono w-12 shrink-0 pt-0.5">
                        {item.time}
                      </span>
                      <span className="text-base">{item.icon}</span>
                      <div className="flex-1 min-w-0">
                        <span className="font-medium text-slate-800">{item.place}</span>
                        <span className="text-slate-400 ml-1.5 text-xs">{item.duration}</span>
                        <p className="text-xs text-slate-500 mt-0.5">{item.reason}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Edit Panel (40%) */}
        <div className="w-[40%] flex flex-col overflow-hidden bg-slate-50">
          {/* Tab bar */}
          <div className="flex border-b border-slate-200 bg-white shrink-0">
            {(
              [
                { key: "edit" as Tab, label: "结构化修改" },
                { key: "prompt" as Tab, label: "提示词补充" },
                { key: "history" as Tab, label: "历史版本" },
              ] as const
            ).map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`flex-1 py-2.5 text-xs font-medium transition-colors ${
                  activeTab === tab.key
                    ? "text-slate-900 border-b-2 border-slate-900"
                    : "text-slate-500 hover:text-slate-700"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-y-auto p-4">
            {activeTab === "edit" && (
              <div className="space-y-4">
                {/* Day selector */}
                <div>
                  <label className="block text-xs font-medium text-slate-500 mb-2">选择天数</label>
                  <div className="flex gap-1.5 flex-wrap">
                    {MOCK_PLAN.days.map((day) => (
                      <button
                        key={day.num}
                        onClick={() => setSelectedDay(day.num)}
                        className={`px-3 py-1.5 text-xs rounded-lg transition-colors ${
                          selectedDay === day.num
                            ? "bg-slate-900 text-white"
                            : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"
                        }`}
                      >
                        Day {day.num}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Spot list for selected day */}
                <div>
                  <label className="block text-xs font-medium text-slate-500 mb-2">
                    Day {selectedDay} 景点列表
                  </label>
                  <div className="space-y-2">
                    {currentDay.items.map((item, idx) => (
                      <div
                        key={idx}
                        className="bg-white rounded-lg border border-slate-200 p-3"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span>{item.icon}</span>
                            <span className="text-sm font-medium text-slate-800">
                              {item.place}
                            </span>
                          </div>
                          <span className="text-xs text-slate-400">{item.time}</span>
                        </div>

                        {/* Replacement dropdown */}
                        <select className="w-full text-xs border border-slate-200 rounded-lg px-3 py-2 text-slate-600 bg-slate-50 focus:outline-none focus:ring-1 focus:ring-slate-300">
                          <option value="">保持不变</option>
                          {(SPOT_ALTERNATIVES.default || []).map((alt) => (
                            <option key={alt.id} value={alt.id}>
                              替换为：{alt.name} — {alt.reason}
                            </option>
                          ))}
                        </select>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Restaurant replacement */}
                <div>
                  <label className="block text-xs font-medium text-slate-500 mb-2">
                    替换餐厅
                  </label>
                  <select className="w-full text-xs border border-slate-200 rounded-lg px-3 py-2 text-slate-600 bg-white focus:outline-none focus:ring-1 focus:ring-slate-300">
                    <option value="">保持不变</option>
                    {RESTAURANT_ALTERNATIVES.map((alt) => (
                      <option key={alt.id} value={alt.id}>
                        {alt.name} — {alt.reason}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Quick actions */}
                <div className="pt-2 border-t border-slate-200">
                  <button className="w-full py-2 text-xs text-slate-600 border border-slate-200 rounded-lg hover:bg-white transition-colors">
                    🔄 重新生成 Day {selectedDay}
                  </button>
                </div>
              </div>
            )}

            {activeTab === "prompt" && (
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-slate-500 mb-2">
                    提示词补充（内部使用，用户不可见）
                  </label>
                  <textarea
                    value={promptText}
                    onChange={(e) => setPromptText(e.target.value)}
                    placeholder="例如：Day 3 下午增加一个甜品店，用户提到喜欢抹茶..."
                    className="w-full h-40 text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white text-slate-700 placeholder-slate-400 resize-none focus:outline-none focus:ring-1 focus:ring-slate-300"
                  />
                </div>

                <div className="flex gap-2">
                  <button className="flex-1 py-2 text-xs bg-white border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50 transition-colors">
                    重新生成 Day {selectedDay}
                  </button>
                  <button className="flex-1 py-2 text-xs bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-colors">
                    重新生成全部
                  </button>
                </div>

                <p className="text-xs text-slate-400">
                  💡 提示：结构化修改按钮搞不定的特殊情况才用这里。
                </p>
              </div>
            )}

            {activeTab === "history" && (
              <div className="space-y-3">
                {versions.map((v) => (
                  <div
                    key={v.version}
                    className="bg-white rounded-lg border border-slate-200 p-3"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-slate-800">
                        v{v.version}
                      </span>
                      <span className="text-xs text-slate-400">{v.time}</span>
                    </div>
                    <p className="text-xs text-slate-500">{v.summary}</p>
                    {v.version < versions.length && (
                      <button className="mt-2 text-xs text-blue-600 hover:text-blue-800">
                        回退到此版本
                      </button>
                    )}
                  </div>
                ))}

                {versions.length === 0 && (
                  <p className="text-center text-sm text-slate-400 py-8">暂无历史版本</p>
                )}
              </div>
            )}
          </div>

          {/* Keyboard shortcuts hint */}
          <div className="shrink-0 px-4 py-2 bg-white border-t border-slate-200">
            <p className="text-xs text-slate-400">
              ⌘S 保存 · ⌘Enter 发布 · 点击左侧卡片选择天数
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
