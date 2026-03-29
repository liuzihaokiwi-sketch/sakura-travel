"use client";

import { useState, useEffect, useCallback, useRef } from "react";

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// AI Chat 类型
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface AIAction {
  type: "search" | "create" | "update" | "delete" | "boost" | "confirm_needed";
  params?: Record<string, string>;
  entity_type?: string;
  data?: Record<string, unknown>;
  entity_id?: string;
  editorial_boost?: number;
  score_profile?: string;
  description?: string;
}

interface AIResponse {
  reply: string;
  action: AIAction | null;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// AI Chat Panel 组件
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function AIChatPanel({
  activeTab,
  city,
  onSearch,
  onRefresh,
}: {
  activeTab: EntityType;
  city: string;
  onSearch: (q: string, entityType?: string, cityCode?: string) => void;
  onRefresh: () => void;
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [pendingAction, setPendingAction] = useState<AIAction | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const executeAction = useCallback(
    async (action: AIAction): Promise<string> => {
      try {
        if (action.type === "search") {
          onSearch(action.params?.q ?? "", action.params?.entity_type, action.params?.city_code);
          return "已更新列表筛选条件。";
        }
        if (action.type === "create") {
          const res = await fetch("/api/admin/catalog/entities", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ entity_type: action.entity_type, ...action.data }),
          });
          if (!res.ok) { const err = await res.json(); return `创建失败：${err.detail ?? err.error ?? res.statusText}`; }
          onRefresh();
          return "✅ 创建成功，列表已刷新。";
        }
        if (action.type === "update") {
          const res = await fetch(`/api/admin/catalog/entities/${action.entity_id}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(action.data),
          });
          if (!res.ok) { const err = await res.json(); return `修改失败：${err.detail ?? err.error ?? res.statusText}`; }
          onRefresh();
          return "✅ 修改成功，列表已刷新。";
        }
        if (action.type === "delete") {
          const res = await fetch(`/api/admin/catalog/entities/${action.entity_id}`, { method: "DELETE" });
          if (!res.ok) { const err = await res.json(); return `停用失败：${err.detail ?? err.error ?? res.statusText}`; }
          onRefresh();
          return "✅ 已停用，列表已刷新。";
        }
        if (action.type === "boost") {
          const res = await fetch(`/api/admin/catalog/entities/${action.entity_id}/score`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ editorial_boost: action.editorial_boost, score_profile: action.score_profile ?? "general" }),
          });
          if (!res.ok) { const err = await res.json(); return `调权失败：${err.detail ?? err.error ?? res.statusText}`; }
          onRefresh();
          return `✅ editorial_boost 已设为 ${action.editorial_boost}，列表已刷新。`;
        }
        return "未知操作类型。";
      } catch (e: any) {
        return `操作出错：${e.message}`;
      }
    },
    [onSearch, onRefresh]
  );

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || loading) return;
      const userMsg: ChatMessage = { role: "user", content: text };
      const newMessages = [...messages, userMsg];
      setMessages(newMessages);
      setInput("");
      setLoading(true);
      try {
        const res = await fetch("/api/admin/catalog/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ messages: newMessages, context: { activeTab, currentFilter: city ? { city_code: city } : {} } }),
        });
        const aiResp: AIResponse = await res.json();
        let replyText = aiResp.reply;
        if (aiResp.action) {
          if (aiResp.action.type === "confirm_needed") {
            setPendingAction(aiResp.action);
          } else {
            const result = await executeAction(aiResp.action);
            replyText = `${aiResp.reply}\n\n${result}`;
          }
        }
        setMessages((prev) => [...prev, { role: "assistant", content: replyText }]);
      } catch (e: any) {
        setMessages((prev) => [...prev, { role: "assistant", content: `出错了：${e.message}` }]);
      } finally {
        setLoading(false);
        inputRef.current?.focus();
      }
    },
    [messages, loading, activeTab, city, executeAction]
  );

  const handleConfirm = async () => {
    if (!pendingAction) return;
    setPendingAction(null);
    setLoading(true);
    const confirmMsg: ChatMessage = { role: "user", content: "确认，请执行。" };
    const newMessages = [...messages, confirmMsg];
    setMessages(newMessages);
    try {
      const res = await fetch("/api/admin/catalog/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: newMessages, context: { activeTab } }),
      });
      const aiResp: AIResponse = await res.json();
      let replyText = aiResp.reply;
      if (aiResp.action && aiResp.action.type !== "confirm_needed") {
        const result = await executeAction(aiResp.action);
        replyText = `${aiResp.reply}\n\n${result}`;
      }
      setMessages((prev) => [...prev, { role: "assistant", content: replyText }]);
    } catch (e: any) {
      setMessages((prev) => [...prev, { role: "assistant", content: `执行出错：${e.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  const QUICK_PROMPTS = ["找一下当前城市的酒店", "新建一个餐厅", "把某个景点的权重调高", "停用一个重复的条目"];

  return (
    <div className="flex flex-col h-full bg-white border-l border-slate-200" style={{ minHeight: 0 }}>
      <div className="px-4 py-3 border-b border-slate-200 flex-shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-full bg-indigo-600 flex items-center justify-center text-white text-xs">AI</div>
          <div>
            <p className="text-sm font-semibold text-slate-800">AI 内容助手</p>
            <p className="text-xs text-slate-400">用自然语言增删改查</p>
          </div>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3" style={{ minHeight: 0 }}>
        {messages.length === 0 && (
          <div className="space-y-2">
            <p className="text-xs text-slate-400 text-center py-4">说说你想做什么，例如：</p>
            {QUICK_PROMPTS.map((p) => (
              <button key={p} onClick={() => sendMessage(p)}
                className="w-full text-left px-3 py-2 text-xs text-slate-600 bg-slate-50 border border-slate-200 rounded-lg hover:bg-indigo-50 hover:border-indigo-200 hover:text-indigo-700 transition-colors">
                {p}
              </button>
            ))}
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[85%] px-3 py-2 rounded-xl text-xs leading-relaxed whitespace-pre-wrap ${
              msg.role === "user" ? "bg-indigo-600 text-white rounded-br-sm" : "bg-slate-100 text-slate-800 rounded-bl-sm"
            }`}>{msg.content}</div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-100 rounded-xl rounded-bl-sm px-3 py-2 flex gap-1 items-center">
              {[0, 1, 2].map((i) => (
                <span key={i} className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
              ))}
            </div>
          </div>
        )}
        {pendingAction && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 text-xs">
            <p className="text-amber-800 font-medium mb-2">⚠️ 需要确认</p>
            <p className="text-amber-700 mb-3">{pendingAction.description}</p>
            <div className="flex gap-2">
              <button onClick={handleConfirm} className="px-3 py-1.5 bg-amber-600 text-white rounded-lg text-xs font-medium hover:bg-amber-700">确认执行</button>
              <button onClick={() => setPendingAction(null)} className="px-3 py-1.5 bg-slate-100 text-slate-600 rounded-lg text-xs hover:bg-slate-200">取消</button>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      {messages.length > 0 && (
        <div className="px-4 pb-1 flex-shrink-0">
          <button onClick={() => { setMessages([]); setPendingAction(null); }} className="text-xs text-slate-400 hover:text-slate-600">清空对话</button>
        </div>
      )}
      <div className="px-4 pb-4 pt-2 border-t border-slate-100 flex-shrink-0">
        <div className="flex gap-2 items-end">
          <textarea ref={inputRef} value={input} onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(input); } }}
            placeholder="输入指令… (Enter 发送)" rows={2}
            className="flex-1 border border-slate-200 rounded-lg px-3 py-2 text-xs resize-none focus:outline-none focus:ring-1 focus:ring-indigo-400 placeholder-slate-400" />
          <button onClick={() => sendMessage(input)} disabled={!input.trim() || loading}
            className="px-3 py-2 bg-indigo-600 text-white rounded-lg text-xs font-medium hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed flex-shrink-0">
            发送
          </button>
        </div>
      </div>
    </div>
  );
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 类型定义
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

type EntityType = "hotel" | "restaurant" | "poi";

interface ScoreItem {
  score_id: number;
  score_profile: string;
  base_score: number;
  editorial_boost: number;
  final_score: number;
  computed_at: string | null;
}

interface Entity {
  entity_id: string;
  entity_type: EntityType;
  name_zh: string;
  name_en: string | null;
  name_ja: string | null;
  city_code: string;
  area_name: string | null;
  address_ja: string | null;
  lat: number | null;
  lng: number | null;
  data_tier: string;
  is_active: boolean;
  google_place_id: string | null;
  created_at: string | null;
  updated_at: string | null;
  scores: ScoreItem[];
  trust_status: string;
  verified_by: string | null;
  verified_at: string | null;
  trust_note: string | null;
  data_source: string;
  // POI
  poi_category?: string;
  typical_duration_min?: number;
  admission_fee_jpy?: number;
  admission_free?: boolean;
  google_rating?: number;
  google_review_count?: number;
  requires_advance_booking?: boolean;
  best_season?: string;
  crowd_level_typical?: string;
  // Hotel
  hotel_type?: string;
  star_rating?: number;
  chain_name?: string;
  price_tier?: string;
  typical_price_min_jpy?: number;
  booking_score?: number;
  amenities?: string[];
  is_family_friendly?: boolean;
  check_in_time?: string;
  check_out_time?: string;
  // Restaurant
  cuisine_type?: string;
  michelin_star?: number;
  tabelog_score?: number;
  price_range_min_jpy?: number;
  price_range_max_jpy?: number;
  requires_reservation?: boolean;
  reservation_difficulty?: string;
  has_english_menu?: boolean;
}

interface ListResponse {
  total: number;
  offset: number;
  limit: number;
  items: Entity[];
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 配置
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

const TABS: { key: EntityType; label: string; icon: string }[] = [
  { key: "hotel", label: "酒店", icon: "🏨" },
  { key: "restaurant", label: "餐厅", icon: "🍽️" },
  { key: "poi", label: "景点/活动", icon: "🗺️" },
];

const CITIES = [
  { value: "", label: "全部城市" },
  { value: "tokyo", label: "东京" },
  { value: "osaka", label: "大阪" },
  { value: "kyoto", label: "京都" },
  { value: "sapporo", label: "札幌" },
  { value: "fukuoka", label: "福冈" },
  { value: "naha", label: "冲绳" },
  { value: "hakone", label: "箱根" },
  { value: "nikko", label: "日光" },
];

const TIERS = [
  { value: "", label: "全部层级" },
  { value: "S", label: "S 级 (核心)" },
  { value: "A", label: "A 级 (优质)" },
  { value: "B", label: "B 级 (普通)" },
];

const TRUST_STATUSES = [
  { value: "", label: "全部状态" },
  { value: "verified", label: "已验证" },
  { value: "unverified", label: "未验证" },
  { value: "ai_generated", label: "AI生成" },
  { value: "suspicious", label: "存疑" },
  { value: "rejected", label: "已拒绝" },
];

const TIER_STYLE: Record<string, string> = {
  S: "bg-amber-100 text-amber-800 border-amber-300",
  A: "bg-sky-100 text-sky-800 border-sky-300",
  B: "bg-slate-100 text-slate-600 border-slate-300",
};

const TRUST_STYLE: Record<string, string> = {
  verified: "bg-emerald-100 text-emerald-700",
  unverified: "bg-slate-100 text-slate-500",
  ai_generated: "bg-orange-100 text-orange-700",
  suspicious: "bg-red-100 text-red-700",
  rejected: "bg-slate-200 text-slate-800",
};

const TRUST_LABEL: Record<string, string> = {
  verified: "已验证",
  unverified: "未验证",
  ai_generated: "AI生成",
  suspicious: "存疑",
  rejected: "已拒绝",
};

const SOURCE_STYLE: Record<string, string> = {
  google: "bg-emerald-100 text-emerald-700",
  tabelog: "bg-sky-100 text-sky-700",
  ai: "bg-red-100 text-red-700",
};

const SOURCE_LABEL: Record<string, string> = {
  google: "Google",
  tabelog: "Tabelog",
  ai: "AI生成",
};

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// API 函数
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async function fetchEntities(params: Record<string, string>): Promise<ListResponse> {
  const qs = new URLSearchParams(params).toString();
  const res = await fetch(`/api/admin/catalog/entities?${qs}`);
  if (!res.ok) throw new Error("加载失败");
  return res.json();
}

async function deleteEntity(id: string): Promise<void> {
  const res = await fetch(`/api/admin/catalog/entities/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("删除失败");
}

async function updateEntity(id: string, data: Record<string, unknown>): Promise<void> {
  const res = await fetch(`/api/admin/catalog/entities/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("更新失败");
}

async function updateScore(id: string, editorial_boost: number, score_profile = "general"): Promise<void> {
  const res = await fetch(`/api/admin/catalog/entities/${id}/score`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ editorial_boost, score_profile }),
  });
  if (!res.ok) throw new Error("评分更新失败");
}

async function createEntity(data: Record<string, unknown>): Promise<void> {
  const res = await fetch("/api/admin/catalog/entities", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("创建失败");
}

async function batchUpdateTrust(entityIds: string[], trustStatus: string): Promise<void> {
  const res = await fetch("/api/admin/catalog/entities", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ entity_ids: entityIds, trust_status: trustStatus }),
  });
  if (!res.ok) throw new Error("批量更新失败");
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 子组件：实体行详情（展开状态）
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function EntityDetailRow({
  entity,
  onRefresh,
  onDelete,
}: {
  entity: Entity;
  onRefresh: () => void;
  onDelete: (id: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [boostVal, setBoostVal] = useState<number>(
    entity.scores.find((s) => s.score_profile === "general")?.editorial_boost ?? 0
  );
  const [saving, setSaving] = useState(false);
  const [editFields, setEditFields] = useState({
    name_zh: entity.name_zh,
    area_name: entity.area_name ?? "",
    data_tier: entity.data_tier,
    is_active: entity.is_active,
    google_rating: entity.google_rating ?? "",
    hotel_type: entity.hotel_type ?? "",
    star_rating: entity.star_rating ?? "",
    price_tier: entity.price_tier ?? "",
    typical_price_min_jpy: entity.typical_price_min_jpy ?? "",
    cuisine_type: entity.cuisine_type ?? "",
    michelin_star: entity.michelin_star ?? "",
    tabelog_score: entity.tabelog_score ?? "",
    price_range_min_jpy: entity.price_range_min_jpy ?? "",
    price_range_max_jpy: entity.price_range_max_jpy ?? "",
    requires_reservation: entity.requires_reservation ?? false,
    poi_category: entity.poi_category ?? "",
    typical_duration_min: entity.typical_duration_min ?? "",
    admission_fee_jpy: entity.admission_fee_jpy ?? "",
    admission_free: entity.admission_free ?? false,
    requires_advance_booking: entity.requires_advance_booking ?? false,
  });

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload: Record<string, unknown> = {
        name_zh: editFields.name_zh,
        area_name: editFields.area_name || null,
        data_tier: editFields.data_tier,
        is_active: editFields.is_active,
      };
      if (entity.entity_type === "poi") {
        Object.assign(payload, {
          poi_category: editFields.poi_category || null,
          typical_duration_min: editFields.typical_duration_min ? Number(editFields.typical_duration_min) : null,
          admission_fee_jpy: editFields.admission_fee_jpy ? Number(editFields.admission_fee_jpy) : null,
          admission_free: editFields.admission_free,
          google_rating: editFields.google_rating ? Number(editFields.google_rating) : null,
          requires_advance_booking: editFields.requires_advance_booking,
        });
      }
      if (entity.entity_type === "hotel") {
        Object.assign(payload, {
          hotel_type: editFields.hotel_type || null,
          star_rating: editFields.star_rating ? Number(editFields.star_rating) : null,
          price_tier: editFields.price_tier || null,
          typical_price_min_jpy: editFields.typical_price_min_jpy ? Number(editFields.typical_price_min_jpy) : null,
        });
      }
      if (entity.entity_type === "restaurant") {
        Object.assign(payload, {
          cuisine_type: editFields.cuisine_type || null,
          michelin_star: editFields.michelin_star ? Number(editFields.michelin_star) : null,
          tabelog_score: editFields.tabelog_score ? Number(editFields.tabelog_score) : null,
          price_range_min_jpy: editFields.price_range_min_jpy ? Number(editFields.price_range_min_jpy) : null,
          price_range_max_jpy: editFields.price_range_max_jpy ? Number(editFields.price_range_max_jpy) : null,
          requires_reservation: editFields.requires_reservation,
        });
      }
      await updateEntity(entity.entity_id, payload);
      await updateScore(entity.entity_id, boostVal);
      setEditing(false);
      onRefresh();
    } catch (e: any) {
      alert(e.message);
    } finally {
      setSaving(false);
    }
  };

  const inp = "border border-slate-200 rounded px-2 py-1 text-xs w-full focus:outline-none focus:ring-1 focus:ring-indigo-400";

  return (
    <div className="bg-slate-50 border-x border-b border-slate-200 rounded-b-lg px-4 py-4">
      {editing ? (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <div><label className="text-xs text-slate-500 mb-1 block">名称（中文）</label>
              <input className={inp} value={editFields.name_zh} onChange={e => setEditFields(p => ({ ...p, name_zh: e.target.value }))} /></div>
            <div><label className="text-xs text-slate-500 mb-1 block">区域</label>
              <input className={inp} value={editFields.area_name} onChange={e => setEditFields(p => ({ ...p, area_name: e.target.value }))} /></div>
            <div><label className="text-xs text-slate-500 mb-1 block">数据层级</label>
              <select className={inp} value={editFields.data_tier} onChange={e => setEditFields(p => ({ ...p, data_tier: e.target.value }))}>
                <option value="S">S</option><option value="A">A</option><option value="B">B</option>
              </select></div>
            <div><label className="text-xs text-slate-500 mb-1 block">状态</label>
              <select className={inp} value={editFields.is_active ? "true" : "false"} onChange={e => setEditFields(p => ({ ...p, is_active: e.target.value === "true" }))}>
                <option value="true">启用</option><option value="false">停用</option>
              </select></div>
          </div>
          {entity.entity_type === "poi" && (
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              <div><label className="text-xs text-slate-500 mb-1 block">分类</label>
                <input className={inp} value={editFields.poi_category} onChange={e => setEditFields(p => ({ ...p, poi_category: e.target.value }))} placeholder="shrine/temple/park..." /></div>
              <div><label className="text-xs text-slate-500 mb-1 block">游览时长(分钟)</label>
                <input className={inp} type="number" value={editFields.typical_duration_min} onChange={e => setEditFields(p => ({ ...p, typical_duration_min: e.target.value as any }))} /></div>
              <div><label className="text-xs text-slate-500 mb-1 block">Google 评分</label>
                <input className={inp} type="number" step="0.1" min="0" max="5" value={editFields.google_rating} onChange={e => setEditFields(p => ({ ...p, google_rating: e.target.value as any }))} /></div>
              <div><label className="text-xs text-slate-500 mb-1 block">门票(日元)</label>
                <input className={inp} type="number" value={editFields.admission_fee_jpy} onChange={e => setEditFields(p => ({ ...p, admission_fee_jpy: e.target.value as any }))} /></div>
              <div className="flex items-center gap-2">
                <input type="checkbox" checked={editFields.admission_free} onChange={e => setEditFields(p => ({ ...p, admission_free: e.target.checked }))} id={`free-${entity.entity_id}`} />
                <label className="text-xs text-slate-600" htmlFor={`free-${entity.entity_id}`}>免费入场</label></div>
              <div className="flex items-center gap-2">
                <input type="checkbox" checked={editFields.requires_advance_booking} onChange={e => setEditFields(p => ({ ...p, requires_advance_booking: e.target.checked }))} id={`book-${entity.entity_id}`} />
                <label className="text-xs text-slate-600" htmlFor={`book-${entity.entity_id}`}>需提前预约</label></div>
            </div>
          )}
          {entity.entity_type === "hotel" && (
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              <div><label className="text-xs text-slate-500 mb-1 block">类型</label>
                <input className={inp} value={editFields.hotel_type} onChange={e => setEditFields(p => ({ ...p, hotel_type: e.target.value }))} placeholder="business/ryokan/resort..." /></div>
              <div><label className="text-xs text-slate-500 mb-1 block">星级</label>
                <input className={inp} type="number" step="0.5" min="1" max="5" value={editFields.star_rating} onChange={e => setEditFields(p => ({ ...p, star_rating: e.target.value as any }))} /></div>
              <div><label className="text-xs text-slate-500 mb-1 block">价格段</label>
                <select className={inp} value={editFields.price_tier} onChange={e => setEditFields(p => ({ ...p, price_tier: e.target.value }))}>
                  <option value="">不限</option><option value="budget">经济</option><option value="mid">中档</option><option value="premium">高档</option><option value="luxury">奢华</option>
                </select></div>
              <div><label className="text-xs text-slate-500 mb-1 block">最低房价(日元/晚)</label>
                <input className={inp} type="number" value={editFields.typical_price_min_jpy} onChange={e => setEditFields(p => ({ ...p, typical_price_min_jpy: e.target.value as any }))} /></div>
            </div>
          )}
          {entity.entity_type === "restaurant" && (
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              <div><label className="text-xs text-slate-500 mb-1 block">菜系</label>
                <input className={inp} value={editFields.cuisine_type} onChange={e => setEditFields(p => ({ ...p, cuisine_type: e.target.value }))} placeholder="sushi/ramen/kaiseki..." /></div>
              <div><label className="text-xs text-slate-500 mb-1 block">米其林星级</label>
                <select className={inp} value={editFields.michelin_star} onChange={e => setEditFields(p => ({ ...p, michelin_star: e.target.value as any }))}>
                  <option value="">无</option><option value="1">★ 一星</option><option value="2">★★ 二星</option><option value="3">★★★ 三星</option>
                </select></div>
              <div><label className="text-xs text-slate-500 mb-1 block">Tabelog 评分</label>
                <input className={inp} type="number" step="0.01" min="0" max="5" value={editFields.tabelog_score} onChange={e => setEditFields(p => ({ ...p, tabelog_score: e.target.value as any }))} /></div>
              <div><label className="text-xs text-slate-500 mb-1 block">人均最低(日元)</label>
                <input className={inp} type="number" value={editFields.price_range_min_jpy} onChange={e => setEditFields(p => ({ ...p, price_range_min_jpy: e.target.value as any }))} /></div>
              <div><label className="text-xs text-slate-500 mb-1 block">人均最高(日元)</label>
                <input className={inp} type="number" value={editFields.price_range_max_jpy} onChange={e => setEditFields(p => ({ ...p, price_range_max_jpy: e.target.value as any }))} /></div>
              <div className="flex items-center gap-2">
                <input type="checkbox" checked={editFields.requires_reservation} onChange={e => setEditFields(p => ({ ...p, requires_reservation: e.target.checked }))} id={`rsv-${entity.entity_id}`} />
                <label className="text-xs text-slate-600" htmlFor={`rsv-${entity.entity_id}`}>需要预约</label></div>
            </div>
          )}
          <div className="border-t border-slate-200 pt-3">
            <label className="text-xs text-slate-500 mb-2 block font-medium">📊 编辑加权（Editorial Boost）— general 档案</label>
            <div className="flex items-center gap-3">
              <input type="range" min="-8" max="8" step="1" value={boostVal} onChange={e => setBoostVal(Number(e.target.value))} className="flex-1 accent-indigo-600" />
              <span className={`text-sm font-bold w-8 text-center ${boostVal > 0 ? "text-emerald-600" : boostVal < 0 ? "text-red-600" : "text-slate-500"}`}>
                {boostVal > 0 ? `+${boostVal}` : boostVal}
              </span>
            </div>
          </div>
          <div className="flex gap-2 pt-1">
            <button onClick={handleSave} disabled={saving} className="px-3 py-1.5 bg-indigo-600 text-white text-xs rounded-md hover:bg-indigo-700 disabled:opacity-50">
              {saving ? "保存中..." : "💾 保存"}
            </button>
            <button onClick={() => setEditing(false)} className="px-3 py-1.5 bg-slate-100 text-slate-600 text-xs rounded-md hover:bg-slate-200">取消</button>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {/* 信任状态 + 来源信息 */}
          <div className="flex flex-wrap gap-3 text-xs">
            <div className="flex items-center gap-1.5">
              <span className="text-slate-400">信任状态:</span>
              <span className={`px-2 py-0.5 rounded-full font-medium ${TRUST_STYLE[entity.trust_status] || "bg-slate-100 text-slate-600"}`}>
                {TRUST_LABEL[entity.trust_status] || entity.trust_status}
              </span>
            </div>
            {entity.verified_by && (
              <span className="text-slate-400">审核人: <span className="text-slate-600">{entity.verified_by}</span></span>
            )}
            {entity.verified_at && (
              <span className="text-slate-400">审核时间: <span className="text-slate-600">{new Date(entity.verified_at).toLocaleDateString("zh-CN")}</span></span>
            )}
            {entity.google_place_id && (
              <span className="text-emerald-600">Google Place ID: <span className="font-mono text-xs">{entity.google_place_id}</span></span>
            )}
          </div>

          {/* 坐标 */}
          {entity.lat && entity.lng && (
            <div className="text-xs">
              <span className="text-slate-400">坐标: </span>
              <a
                href={`https://maps.google.com/?q=${entity.lat},${entity.lng}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sky-600 hover:underline"
              >
                {entity.lat.toFixed(6)}, {entity.lng.toFixed(6)} 🗺️
              </a>
            </div>
          )}

          {/* 其他详情 */}
          <div className="flex flex-wrap gap-4 text-xs text-slate-600">
            {entity.address_ja && <span>📍 {entity.address_ja}</span>}
            {entity.entity_type === "poi" && (
              <>
                {entity.poi_category && <span>🏷️ {entity.poi_category}</span>}
                {entity.typical_duration_min && <span>⏱️ 约{entity.typical_duration_min}分钟</span>}
                {entity.admission_free ? <span>🆓 免费</span> : entity.admission_fee_jpy ? <span>🎫 ¥{entity.admission_fee_jpy.toLocaleString()}</span> : null}
                {entity.requires_advance_booking && <span className="text-amber-600">⚠️ 需提前预约</span>}
                {entity.best_season && <span>🌸 最佳季节: {entity.best_season}</span>}
              </>
            )}
            {entity.entity_type === "hotel" && (
              <>
                {entity.hotel_type && <span>🏩 {entity.hotel_type}</span>}
                {entity.star_rating && <span>⭐ {entity.star_rating}星</span>}
                {entity.price_tier && <span>💰 {entity.price_tier}</span>}
                {entity.typical_price_min_jpy && <span>💴 起价 ¥{entity.typical_price_min_jpy.toLocaleString()}/晚</span>}
                {entity.check_in_time && <span>🏷️ 入住 {entity.check_in_time}</span>}
              </>
            )}
            {entity.entity_type === "restaurant" && (
              <>
                {entity.cuisine_type && <span>🍴 {entity.cuisine_type}</span>}
                {entity.michelin_star ? <span className="text-amber-600">⭐ 米其林 {entity.michelin_star}星</span> : null}
                {entity.tabelog_score && <span>📊 Tabelog {entity.tabelog_score}</span>}
                {entity.price_range_min_jpy && <span>💴 ¥{entity.price_range_min_jpy.toLocaleString()}~{entity.price_range_max_jpy?.toLocaleString()}</span>}
                {entity.requires_reservation && <span className="text-amber-600">📅 需预约</span>}
              </>
            )}
          </div>

          {/* 评分详情 */}
          {entity.scores.length > 0 && (
            <div className="pt-2 border-t border-slate-100 flex gap-3 flex-wrap">
              {entity.scores.map((s) => (
                <span key={s.score_id} className="text-xs text-slate-500">
                  [{s.score_profile}] 基础: {s.base_score.toFixed(1)} + boost: {s.editorial_boost} = <strong>{s.final_score.toFixed(1)}</strong>
                </span>
              ))}
            </div>
          )}

          <div className="flex gap-2 pt-2 border-t border-slate-100">
            <button onClick={() => setEditing(true)} className="px-2.5 py-1 bg-slate-100 text-slate-700 text-xs rounded hover:bg-slate-200">✏️ 编辑</button>
            <button onClick={() => onDelete(entity.entity_id)} className="px-2.5 py-1 bg-red-50 text-red-600 text-xs rounded hover:bg-red-100">🗑️ 停用</button>
          </div>
        </div>
      )}
    </div>
  );
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 子组件：实体列表行
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function EntityRow({
  entity,
  onRefresh,
  onDelete,
  selected,
  onToggleSelect,
}: {
  entity: Entity;
  onRefresh: () => void;
  onDelete: (id: string) => void;
  selected: boolean;
  onToggleSelect: (id: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="mb-2">
      <div
        className={`flex items-center gap-3 px-4 py-3 bg-white border cursor-pointer hover:bg-slate-50 transition-colors
          ${expanded ? "rounded-t-lg border-b-0" : "rounded-lg"}
          ${selected ? "border-indigo-300 bg-indigo-50 hover:bg-indigo-50" : "border-slate-200"}`}
      >
        {/* 勾选框 */}
        <input
          type="checkbox"
          checked={selected}
          onChange={() => onToggleSelect(entity.entity_id)}
          onClick={(e) => e.stopPropagation()}
          className="accent-indigo-600 flex-shrink-0"
        />

        {/* 展开箭头 */}
        <span
          className={`text-slate-400 text-xs transition-transform flex-shrink-0 ${expanded ? "rotate-90" : ""}`}
          onClick={() => setExpanded((v) => !v)}
        >▶</span>

        {/* 名称 */}
        <div className="flex-1 min-w-0" onClick={() => setExpanded((v) => !v)}>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-slate-900 text-sm">{entity.name_zh}</span>
            {entity.name_en && <span className="text-xs text-slate-400">{entity.name_en}</span>}
            {!entity.is_active && <span className="text-xs px-1.5 py-0.5 bg-red-100 text-red-600 rounded">已停用</span>}
          </div>
          <div className="flex items-center gap-2 mt-0.5 flex-wrap">
            <span className="text-xs text-slate-500">{entity.city_code}</span>
            {entity.area_name && <span className="text-xs text-slate-400">· {entity.area_name}</span>}
          </div>
        </div>

        {/* 数据来源 */}
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium hidden sm:inline-block ${SOURCE_STYLE[entity.data_source] || "bg-slate-100 text-slate-500"}`}>
          {SOURCE_LABEL[entity.data_source] || entity.data_source}
        </span>

        {/* 信任状态 */}
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium hidden md:inline-block ${TRUST_STYLE[entity.trust_status] || "bg-slate-100 text-slate-500"}`}>
          {TRUST_LABEL[entity.trust_status] || entity.trust_status}
        </span>

        {/* Tier 徽章 */}
        <span className={`text-xs px-2 py-0.5 rounded border font-semibold ${TIER_STYLE[entity.data_tier] ?? "bg-slate-100 text-slate-500 border-slate-200"}`}>
          {entity.data_tier}
        </span>

        {/* Google 评分 */}
        {entity.google_rating ? (
          <div className="hidden md:flex items-center gap-1 text-xs text-amber-600 w-16 justify-end">
            <span>★</span><span>{entity.google_rating}</span>
          </div>
        ) : (
          <div className="hidden md:block w-16" />
        )}
      </div>

      {expanded && (
        <EntityDetailRow entity={entity} onRefresh={onRefresh} onDelete={onDelete} />
      )}
    </div>
  );
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 子组件：新建实体弹窗
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function CreateModal({ entityType, onClose, onCreated }: {
  entityType: EntityType;
  onClose: () => void;
  onCreated: () => void;
}) {
  const [form, setForm] = useState({
    name_zh: "", name_en: "", city_code: "tokyo", area_name: "", data_tier: "B",
    poi_category: "", typical_duration_min: "", google_rating: "", admission_free: false,
    hotel_type: "", star_rating: "", price_tier: "mid", typical_price_min_jpy: "",
    cuisine_type: "", michelin_star: "", tabelog_score: "", price_range_min_jpy: "", price_range_max_jpy: "", requires_reservation: false,
  });
  const [saving, setSaving] = useState(false);
  const inp = "border border-slate-200 rounded px-2 py-1.5 text-sm w-full focus:outline-none focus:ring-1 focus:ring-indigo-400";

  const handleCreate = async () => {
    if (!form.name_zh.trim()) return alert("请填写名称");
    setSaving(true);
    try {
      const payload: Record<string, unknown> = {
        entity_type: entityType, name_zh: form.name_zh, name_en: form.name_en || null,
        city_code: form.city_code, area_name: form.area_name || null, data_tier: form.data_tier,
      };
      if (entityType === "poi") Object.assign(payload, {
        poi_category: form.poi_category || null,
        typical_duration_min: form.typical_duration_min ? Number(form.typical_duration_min) : null,
        google_rating: form.google_rating ? Number(form.google_rating) : null,
        admission_free: form.admission_free,
      });
      if (entityType === "hotel") Object.assign(payload, {
        hotel_type: form.hotel_type || null, star_rating: form.star_rating ? Number(form.star_rating) : null,
        price_tier: form.price_tier || null, typical_price_min_jpy: form.typical_price_min_jpy ? Number(form.typical_price_min_jpy) : null,
      });
      if (entityType === "restaurant") Object.assign(payload, {
        cuisine_type: form.cuisine_type || null, michelin_star: form.michelin_star ? Number(form.michelin_star) : null,
        tabelog_score: form.tabelog_score ? Number(form.tabelog_score) : null,
        price_range_min_jpy: form.price_range_min_jpy ? Number(form.price_range_min_jpy) : null,
        price_range_max_jpy: form.price_range_max_jpy ? Number(form.price_range_max_jpy) : null,
        requires_reservation: form.requires_reservation,
      });
      await createEntity(payload);
      onCreated();
      onClose();
    } catch (e: any) {
      alert(e.message);
    } finally {
      setSaving(false);
    }
  };

  const typeLabels: Record<EntityType, string> = { hotel: "酒店", restaurant: "餐厅", poi: "景点/活动" };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <h2 className="text-base font-semibold text-slate-900">➕ 新建{typeLabels[entityType]}</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-xl leading-none">×</button>
        </div>
        <div className="px-6 py-4 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div><label className="text-xs text-slate-500 mb-1 block">名称（中文）*</label>
              <input className={inp} value={form.name_zh} onChange={e => setForm(p => ({ ...p, name_zh: e.target.value }))} placeholder="如：浅草寺" /></div>
            <div><label className="text-xs text-slate-500 mb-1 block">名称（英文）</label>
              <input className={inp} value={form.name_en} onChange={e => setForm(p => ({ ...p, name_en: e.target.value }))} placeholder="Senso-ji" /></div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div><label className="text-xs text-slate-500 mb-1 block">城市 *</label>
              <select className={inp} value={form.city_code} onChange={e => setForm(p => ({ ...p, city_code: e.target.value }))}>
                {CITIES.filter(c => c.value).map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select></div>
            <div><label className="text-xs text-slate-500 mb-1 block">区域</label>
              <input className={inp} value={form.area_name} onChange={e => setForm(p => ({ ...p, area_name: e.target.value }))} placeholder="浅草/新宿..." /></div>
            <div><label className="text-xs text-slate-500 mb-1 block">数据层级</label>
              <select className={inp} value={form.data_tier} onChange={e => setForm(p => ({ ...p, data_tier: e.target.value }))}>
                <option value="S">S（核心）</option><option value="A">A（优质）</option><option value="B">B（普通）</option>
              </select></div>
          </div>
          {entityType === "poi" && (
            <div className="grid grid-cols-2 gap-3">
              <div><label className="text-xs text-slate-500 mb-1 block">分类</label>
                <input className={inp} value={form.poi_category} onChange={e => setForm(p => ({ ...p, poi_category: e.target.value }))} placeholder="shrine/park/museum..." /></div>
              <div><label className="text-xs text-slate-500 mb-1 block">Google 评分 (0-5)</label>
                <input className={inp} type="number" step="0.1" min="0" max="5" value={form.google_rating} onChange={e => setForm(p => ({ ...p, google_rating: e.target.value }))} /></div>
              <div><label className="text-xs text-slate-500 mb-1 block">游览时长（分钟）</label>
                <input className={inp} type="number" value={form.typical_duration_min} onChange={e => setForm(p => ({ ...p, typical_duration_min: e.target.value }))} /></div>
              <div className="flex items-center gap-2 mt-4">
                <input type="checkbox" checked={form.admission_free} onChange={e => setForm(p => ({ ...p, admission_free: e.target.checked }))} id="create-free" />
                <label className="text-sm text-slate-600" htmlFor="create-free">免费入场</label></div>
            </div>
          )}
          {entityType === "hotel" && (
            <div className="grid grid-cols-2 gap-3">
              <div><label className="text-xs text-slate-500 mb-1 block">类型</label>
                <input className={inp} value={form.hotel_type} onChange={e => setForm(p => ({ ...p, hotel_type: e.target.value }))} placeholder="business/ryokan/boutique..." /></div>
              <div><label className="text-xs text-slate-500 mb-1 block">星级</label>
                <input className={inp} type="number" step="0.5" min="1" max="5" value={form.star_rating} onChange={e => setForm(p => ({ ...p, star_rating: e.target.value }))} /></div>
              <div><label className="text-xs text-slate-500 mb-1 block">价格段</label>
                <select className={inp} value={form.price_tier} onChange={e => setForm(p => ({ ...p, price_tier: e.target.value }))}>
                  <option value="budget">经济</option><option value="mid">中档</option><option value="premium">高档</option><option value="luxury">奢华</option>
                </select></div>
              <div><label className="text-xs text-slate-500 mb-1 block">最低房价（日元/晚）</label>
                <input className={inp} type="number" value={form.typical_price_min_jpy} onChange={e => setForm(p => ({ ...p, typical_price_min_jpy: e.target.value }))} /></div>
            </div>
          )}
          {entityType === "restaurant" && (
            <div className="grid grid-cols-2 gap-3">
              <div><label className="text-xs text-slate-500 mb-1 block">菜系</label>
                <input className={inp} value={form.cuisine_type} onChange={e => setForm(p => ({ ...p, cuisine_type: e.target.value }))} placeholder="sushi/ramen/kaiseki..." /></div>
              <div><label className="text-xs text-slate-500 mb-1 block">Tabelog 评分</label>
                <input className={inp} type="number" step="0.01" min="0" max="5" value={form.tabelog_score} onChange={e => setForm(p => ({ ...p, tabelog_score: e.target.value }))} /></div>
              <div><label className="text-xs text-slate-500 mb-1 block">米其林星级</label>
                <select className={inp} value={form.michelin_star} onChange={e => setForm(p => ({ ...p, michelin_star: e.target.value }))}>
                  <option value="">无</option><option value="1">1 星</option><option value="2">2 星</option><option value="3">3 星</option>
                </select></div>
              <div className="flex items-center gap-2 mt-4">
                <input type="checkbox" checked={form.requires_reservation} onChange={e => setForm(p => ({ ...p, requires_reservation: e.target.checked }))} id="create-rsv" />
                <label className="text-sm text-slate-600" htmlFor="create-rsv">需要预约</label></div>
            </div>
          )}
        </div>
        <div className="px-6 py-4 border-t border-slate-100 flex justify-end gap-2">
          <button onClick={onClose} className="px-4 py-2 text-sm text-slate-600 bg-slate-100 rounded-lg hover:bg-slate-200">取消</button>
          <button onClick={handleCreate} disabled={saving} className="px-4 py-2 text-sm text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50">
            {saving ? "创建中..." : "✅ 确认创建"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 主页面
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

export default function CatalogPage() {
  const [activeTab, setActiveTab] = useState<EntityType>("hotel");
  const [city, setCity] = useState("");
  const [tier, setTier] = useState("");
  const [trustFilter, setTrustFilter] = useState("");
  const [query, setQuery] = useState("");
  const [showInactive, setShowInactive] = useState(false);
  const [page, setPage] = useState(0);
  const [data, setData] = useState<ListResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [showAI, setShowAI] = useState(true);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [batchWorking, setBatchWorking] = useState(false);
  const searchTimeout = useRef<NodeJS.Timeout | null>(null);

  const handleAISearch = useCallback((q: string, entityType?: string, cityCode?: string) => {
    if (entityType && ["hotel", "restaurant", "poi"].includes(entityType)) setActiveTab(entityType as EntityType);
    if (cityCode !== undefined) setCity(cityCode);
    if (q !== undefined) setQuery(q);
  }, []);

  const LIMIT = 50;

  const load = useCallback(async (resetPage = false) => {
    const offset = resetPage ? 0 : page * LIMIT;
    if (resetPage) setPage(0);
    setLoading(true);
    try {
      const params: Record<string, string> = {
        entity_type: activeTab, limit: String(LIMIT), offset: String(offset),
      };
      if (city) params.city_code = city;
      if (tier) params.data_tier = tier;
      if (trustFilter) params.trust_status = trustFilter;
      if (query) params.q = query;
      if (!showInactive) params.is_active = "true";
      const res = await fetchEntities(params);
      setData(res);
      setSelectedIds(new Set());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [activeTab, city, tier, trustFilter, query, showInactive, page]);

  useEffect(() => { load(true); }, [activeTab, city, tier, trustFilter, showInactive]);
  useEffect(() => {
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(() => load(true), 400);
    return () => { if (searchTimeout.current) clearTimeout(searchTimeout.current); };
  }, [query]);
  useEffect(() => { load(); }, [page]);

  const handleDelete = async (id: string) => {
    if (!confirm("确认停用这个条目？（软删除，可恢复）")) return;
    try {
      await deleteEntity(id);
      load(true);
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleToggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const handleSelectAll = () => {
    if (!data) return;
    if (selectedIds.size === data.items.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(data.items.map((e) => e.entity_id)));
    }
  };

  const handleBatchTrust = async (trustStatus: string) => {
    if (selectedIds.size === 0) return;
    if (!confirm(`确认将 ${selectedIds.size} 条记录标记为「${TRUST_LABEL[trustStatus]}」？`)) return;
    setBatchWorking(true);
    try {
      await batchUpdateTrust(Array.from(selectedIds), trustStatus);
      await load(false);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setBatchWorking(false);
    }
  };

  const totalPages = data ? Math.ceil(data.total / LIMIT) : 0;
  const allSelected = data && data.items.length > 0 && selectedIds.size === data.items.length;

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-3 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-sm font-semibold text-slate-900">内容库管理</h1>
            <p className="text-xs text-slate-400">酒店 · 餐厅 · 景点 CRUD 与评分</p>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={() => setShowAI((v) => !v)}
              className={`px-3 py-1.5 text-xs rounded-lg border font-medium transition-colors ${
                showAI ? "bg-indigo-50 text-indigo-700 border-indigo-200 hover:bg-indigo-100" : "bg-slate-100 text-slate-600 border-slate-200 hover:bg-slate-200"
              }`}>
              {showAI ? "✦ AI 助手 ●" : "✦ AI 助手"}
            </button>
            <button onClick={() => setShowCreate(true)} className="px-3 py-1.5 bg-indigo-600 text-white text-xs rounded-lg hover:bg-indigo-700 font-medium">
              ➕ 新建
            </button>
          </div>
        </div>
      </header>

      {/* 主体 */}
      <div className="flex flex-1 overflow-hidden" style={{ height: "calc(100vh - 57px)" }}>
        {/* 左侧列表区 */}
        <div className="flex-1 overflow-y-auto px-6 py-6" style={{ minWidth: 0 }}>
          {/* 小页签 */}
          <div className="flex gap-1 mb-6 bg-white border border-slate-200 rounded-xl p-1 w-fit">
            {TABS.map((tab) => (
              <button key={tab.key} onClick={() => setActiveTab(tab.key)}
                className={`px-5 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === tab.key ? "bg-indigo-600 text-white shadow-sm" : "text-slate-600 hover:bg-slate-100"
                }`}>
                {tab.icon} {tab.label}
              </button>
            ))}
          </div>

          {/* 过滤器 + 搜索 */}
          <div className="flex flex-wrap gap-3 mb-4">
            <input type="text" placeholder="🔍 搜索名称..." value={query} onChange={e => setQuery(e.target.value)}
              className="border border-slate-200 rounded-lg px-3 py-2 text-sm w-48 focus:outline-none focus:ring-1 focus:ring-indigo-400" />
            <select value={city} onChange={e => setCity(e.target.value)} className="border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none">
              {CITIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
            </select>
            <select value={tier} onChange={e => setTier(e.target.value)} className="border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none">
              {TIERS.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
            <select value={trustFilter} onChange={e => setTrustFilter(e.target.value)} className="border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none">
              {TRUST_STATUSES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
            <label className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer">
              <input type="checkbox" checked={showInactive} onChange={e => setShowInactive(e.target.checked)} className="accent-indigo-600" />
              显示已停用
            </label>
            <div className="ml-auto text-sm text-slate-400 self-center">{data ? `共 ${data.total} 条` : ""}</div>
          </div>

          {/* 批量操作栏 */}
          {selectedIds.size > 0 && (
            <div className="flex items-center gap-2 mb-4 px-4 py-2.5 bg-indigo-50 border border-indigo-200 rounded-xl">
              <span className="text-xs text-indigo-700 font-medium">已选 {selectedIds.size} 条</span>
              <div className="flex gap-2 ml-2">
                <button onClick={() => handleBatchTrust("verified")} disabled={batchWorking}
                  className="px-3 py-1 text-xs bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50">
                  ✓ 批量验证
                </button>
                <button onClick={() => handleBatchTrust("suspicious")} disabled={batchWorking}
                  className="px-3 py-1 text-xs bg-amber-500 text-white rounded-lg hover:bg-amber-600 disabled:opacity-50">
                  ⚠ 标记存疑
                </button>
                <button onClick={() => handleBatchTrust("rejected")} disabled={batchWorking}
                  className="px-3 py-1 text-xs bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50">
                  ✗ 批量拒绝
                </button>
              </div>
              <button onClick={() => setSelectedIds(new Set())} className="ml-auto text-xs text-indigo-500 hover:text-indigo-700">取消选择</button>
            </div>
          )}

          {/* 列表 */}
          {loading && !data ? (
            <div className="flex justify-center py-20 text-slate-400 text-sm">加载中...</div>
          ) : data?.items.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-slate-400">
              <span className="text-4xl mb-3">{TABS.find(t => t.key === activeTab)?.icon}</span>
              <p className="text-sm">暂无数据，点击右上角"新建"添加</p>
            </div>
          ) : (
            <>
              {/* 列头 */}
              <div className="flex items-center gap-3 px-4 py-2 text-xs text-slate-400 font-medium uppercase tracking-wide">
                <input type="checkbox" checked={!!allSelected} onChange={handleSelectAll} className="accent-indigo-600" />
                <span className="w-4" />
                <span className="flex-1">名称 / 城市 / 区域</span>
                <span className="hidden sm:block w-16 text-center">来源</span>
                <span className="hidden md:block w-16 text-center">信任</span>
                <span className="w-12 text-center">层级</span>
                <span className="hidden md:block w-16 text-right">★ Google</span>
              </div>

              <div className={`transition-opacity ${loading ? "opacity-50" : "opacity-100"}`}>
                {data?.items.map((entity) => (
                  <EntityRow
                    key={entity.entity_id}
                    entity={entity}
                    onRefresh={() => load()}
                    onDelete={handleDelete}
                    selected={selectedIds.has(entity.entity_id)}
                    onToggleSelect={handleToggleSelect}
                  />
                ))}
              </div>

              {/* 分页 */}
              {totalPages > 1 && (
                <div className="flex justify-center gap-2 mt-6">
                  <button disabled={page === 0} onClick={() => setPage(p => p - 1)}
                    className="px-3 py-1.5 text-xs border border-slate-200 rounded-lg disabled:opacity-40 hover:bg-slate-100">
                    ← 上一页
                  </button>
                  <span className="px-3 py-1.5 text-xs text-slate-500">{page + 1} / {totalPages}</span>
                  <button disabled={page >= totalPages - 1} onClick={() => setPage(p => p + 1)}
                    className="px-3 py-1.5 text-xs border border-slate-200 rounded-lg disabled:opacity-40 hover:bg-slate-100">
                    下一页 →
                  </button>
                </div>
              )}
            </>
          )}
        </div>

        {/* 右侧 AI 面板 */}
        {showAI && (
          <div className="flex-shrink-0 flex flex-col" style={{ width: "340px" }}>
            <AIChatPanel activeTab={activeTab} city={city} onSearch={handleAISearch} onRefresh={() => load(true)} />
          </div>
        )}
      </div>

      {/* 新建弹窗 */}
      {showCreate && (
        <CreateModal entityType={activeTab} onClose={() => setShowCreate(false)} onCreated={() => load(true)} />
      )}
    </div>
  );
}
