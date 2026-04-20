"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import type { DayTemplate, TemplateSlot } from "@/app/api/admin/templates/route";

export type ViewMode = "opus" | "full";

// ── 翻译映射 ────────────────────────────────────────────────────────────

const BEST_PACE_LABEL: Record<string, string> = {
  compact: "推荐紧凑",
  standard: "标准节奏",
  relaxed: "推荐悠闲",
  locked: "强度固定",
};

const BEST_PACE_COLOR: Record<string, string> = {
  compact: "bg-orange-50 text-orange-700 border-orange-200",
  standard: "bg-slate-50 text-slate-600 border-slate-200",
  relaxed: "bg-emerald-50 text-emerald-700 border-emerald-200",
  locked: "bg-red-50 text-red-700 border-red-200",
};

const PHASE_LABEL: Record<string, string> = {
  arrival: "到达日",
  departure: "离开日",
  transfer: "换城日",
  sightseeing: "游玩日",
};

const PHASE_COLOR: Record<string, string> = {
  arrival: "bg-sky-50 text-sky-700 border-sky-200",
  departure: "bg-violet-50 text-violet-700 border-violet-200",
  transfer: "bg-blue-50 text-blue-700 border-blue-200",
  sightseeing: "bg-slate-50 text-slate-600 border-slate-200",
};

const AUDIENCE_LABEL: Record<string, string> = {
  all: "所有人群",
  couple: "情侣",
  friends: "闺蜜/朋友",
  family: "亲子",
  default: "通用",
  elderly: "长辈",
};

const CITY_LABEL: Record<string, string> = {
  kyoto: "京都",
  osaka: "大阪",
  kobe: "神户",
  nara: "奈良",
  uji: "宇治",
  kinosaki: "城崎",
  koyasan: "高野山",
};

// ── 辅助函数 ────────────────────────────────────────────────────────────

function extractDayMood(description: string): string {
  for (const part of description.split("。")) {
    if (part.includes("day_mood:") || part.includes("day_mood：")) {
      return part.split(/day_mood[:：]/)[1]?.trim() ?? "";
    }
  }
  return "";
}

function cleanDescription(description: string): string {
  return description
    .split("。")
    .filter((p) => !p.includes("day_mood"))
    .join("。")
    .trim()
    .replace(/^。/, "")
    .replace(/。$/, "");
}

function translateAudience(fit: string | string[]): string {
  if (Array.isArray(fit)) {
    return fit.map((a) => AUDIENCE_LABEL[a] ?? a).join("、");
  }
  return AUDIENCE_LABEL[fit] ?? fit;
}

function formatArea(area: string, areas: Record<string, string>, showId = false): string {
  const zh = areas[area];
  if (!zh) return area;
  return showId ? `${zh.split("・")[0]} (${area})` : zh.split("・")[0];
}

function getSlotLabel(slot: TemplateSlot): string {
  if (slot.type === "meal") {
    const id = slot.slot_id ?? "";
    return id.includes("lunch") || id.includes("_lunch") ? "午餐" : "晚餐";
  }
  if (slot.type === "walk") return slot.entity_hint ?? "散步";
  if (slot.type === "rest") return "休息";
  if (slot.type === "transport") return "交通";
  if (slot.type === "evening_auto") return "晚间自由";
  if (slot.type === "optional_poi") return slot.entity_hint ?? "可选活动";
  if (slot.entity_hint) return slot.entity_hint;
  if (slot.note) {
    const first = slot.note.split(/[。，、\n]/)[0]?.trim();
    if (first && first.length <= 20) return first;
  }
  return "活动";
}

function getCoreNoteOpus(note: string): string {
  const sentences = note
    .replace(/——/g, "。")
    .split("。")
    .map((s) => s.trim())
    .filter((s) => s.length > 6);
  for (const s of sentences) {
    if (!s.startsWith("¥") && !s.startsWith("免费") && s.length > 8) {
      return s.length > 55 ? s.slice(0, 55) + "…" : s;
    }
  }
  return sentences[0]?.slice(0, 55) ?? "";
}

// 从 time_range 推断是第几天（D1/D2）
function getDayNum(timeRange: string | null): number | null {
  if (!timeRange) return null;
  const m = timeRange.match(/^D(\d+)/);
  return m ? parseInt(m[1]) : null;
}

// ── Opus 视角 Slot 渲染 ─────────────────────────────────────────────────

function SlotLineOpus({ slot, areas = {} }: { slot: TemplateSlot; areas?: Record<string, string> }) {
  if (slot.type === "shop_info") return null;

  if (slot.type === "transport") {
    const summary = slot.note ? slot.note.split("。")[0] : "移动";
    return (
      <div className="flex items-center gap-1.5 py-1.5 pl-3 text-xs text-blue-500">
        <span>🚃</span>
        <span className="leading-relaxed">{summary}</span>
      </div>
    );
  }

  const isMeal = slot.type === "meal";
  const label = getSlotLabel(slot);

  if (isMeal) {
    return (
      <div className="flex items-center gap-1.5 py-1 pl-3 text-xs text-slate-400">
        <span className="w-4 text-center">🍽</span>
        <span>{label}</span>
        {slot.area && <span className="text-slate-300">· {formatArea(slot.area, areas)}</span>}
      </div>
    );
  }

  const priorityConfig: Record<string, { dot: string; text: string; bg: string }> = {
    P1: { dot: "bg-rose-500", text: "text-slate-800 font-semibold", bg: "bg-rose-50/50" },
    P2: { dot: "bg-amber-400", text: "text-slate-700 font-medium", bg: "" },
    P3: { dot: "bg-slate-300", text: "text-slate-500", bg: "" },
  };
  const cfg = slot.priority ? priorityConfig[slot.priority] ?? priorityConfig.P3 : priorityConfig.P3;
  const dur = slot.duration_min ? `${slot.duration_min}min` : "";
  const note = slot.note ? getCoreNoteOpus(slot.note) : "";

  return (
    <div className={`flex gap-2.5 py-2 pl-3 pr-2 rounded-md ${cfg.bg}`}>
      <div className={`mt-1.5 w-1.5 h-1.5 rounded-full shrink-0 ${cfg.dot}`} />
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline gap-1.5 flex-wrap">
          <span className={`text-sm leading-snug ${cfg.text}`}>{label}</span>
          {slot.priority && <span className="text-[10px] text-slate-400">{slot.priority}</span>}
          {dur && <span className="text-[10px] text-slate-400">{dur}</span>}
          {slot.area && <span className="text-[10px] text-slate-400">{formatArea(slot.area, areas)}</span>}
        </div>
        {note && (
          <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">{note}</p>
        )}
      </div>
    </div>
  );
}

// ── 完整视角 Slot 渲染 ──────────────────────────────────────────────────

function SlotLineFull({ slot, areas = {} }: { slot: TemplateSlot; areas?: Record<string, string> }) {
  if (slot.type === "shop_info") {
    return (
      <div className="mt-3 pt-3 border-t border-dashed border-slate-200 text-xs text-slate-400">
        <span className="font-medium">🛍 购物参考：</span>
        {slot.note && <span className="ml-1">{slot.note}</span>}
      </div>
    );
  }

  if (slot.type === "transport") {
    return (
      <div className="flex gap-2 py-2 px-3 my-1 bg-blue-50/50 rounded-md text-xs text-blue-600 leading-relaxed">
        <span className="shrink-0 mt-0.5">🚃</span>
        <span>{slot.note ?? ""}</span>
      </div>
    );
  }

  const isMeal = slot.type === "meal";
  const label = getSlotLabel(slot);
  const timeRange = slot.time_range?.replace(/^D\d+\s*/, "") ?? "";
  const dur = slot.duration_min ? `${slot.duration_min}min` : "";
  const area = slot.area ? formatArea(slot.area, areas, true) : "";

  const priorityStyle: Record<string, { border: string; badge: string; bg: string }> = {
    P1: { border: "border-l-rose-400", badge: "bg-rose-100 text-rose-700", bg: "bg-rose-50/30" },
    P2: { border: "border-l-amber-300", badge: "bg-amber-100 text-amber-700", bg: "" },
    P3: { border: "border-l-slate-200", badge: "bg-slate-100 text-slate-500", bg: "" },
  };
  const style = slot.priority ? priorityStyle[slot.priority] ?? priorityStyle.P3 : priorityStyle.P3;

  return (
    <div className={`border-l-2 ${style.border} ${style.bg} pl-3 py-2 my-1.5 rounded-r-md`}>
      <div className="flex items-center gap-2 flex-wrap">
        {slot.priority && (
          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${style.badge}`}>{slot.priority}</span>
        )}
        {timeRange && (
          <span className="text-[10px] text-slate-400 font-mono">{timeRange}</span>
        )}
        <span className="font-medium text-sm text-slate-800">{isMeal ? label : (slot.entity_hint ?? label)}</span>
        {area && <span className="text-[10px] text-slate-400">{area}</span>}
        {dur && <span className="text-[10px] text-slate-400">{dur}</span>}
      </div>
      {slot.note && (
        <p className="mt-1 text-xs text-slate-500 leading-relaxed">{slot.note}</p>
      )}
    </div>
  );
}

// ── 主组件 ───────────────────────────────────────────────────────────────

interface TemplateCardProps {
  template: DayTemplate;
  viewMode: ViewMode;
  areas?: Record<string, string>;
}

export function TemplateCard({ template, viewMode, areas = {} }: TemplateCardProps) {
  const { assembly, description, label, template_id, core_entities, fit_audience,
    weather_sensitive, hotel_area_note, slots = [], days } = template;
  const [descExpanded, setDescExpanded] = useState(false);

  const mood = extractDayMood(description);
  const descClean = cleanDescription(description);
  const audienceZh = translateAudience(fit_audience);
  const paceLabel = BEST_PACE_LABEL[assembly.best_pace] ?? assembly.best_pace;
  const paceColor = BEST_PACE_COLOR[assembly.best_pace] ?? "";
  const phaseLabel = PHASE_LABEL[assembly.phase] ?? assembly.phase;
  const phaseColor = PHASE_COLOR[assembly.phase] ?? "";
  const cityZh = CITY_LABEL[template.city] ?? template.city;

  // 多日模板按 D1/D2 分组
  const allSlots = slots;
  const slotsByDay: Map<number, TemplateSlot[]> = new Map();
  let isMultiDay = false;
  for (const s of allSlots) {
    const dn = getDayNum(s.time_range);
    if (dn !== null) {
      isMultiDay = true;
      if (!slotsByDay.has(dn)) slotsByDay.set(dn, []);
      slotsByDay.get(dn)!.push(s);
    }
  }

  const needsTransport = assembly.phase !== "sightseeing" ||
    !["osaka", "kyoto"].includes(template.city);

  const descTooLong = descClean.length > 120;
  const descDisplay = descTooLong && !descExpanded ? descClean.slice(0, 120) + "…" : descClean;

  return (
    <Card className="hover:shadow-md transition-shadow overflow-hidden">
      {/* 顶部色条 */}
      <div className={`h-1 ${
        assembly.phase === "arrival" ? "bg-sky-400" :
        assembly.phase === "departure" ? "bg-violet-400" :
        assembly.phase === "transfer" ? "bg-blue-400" :
        assembly.best_pace === "locked" ? "bg-red-400" :
        "bg-slate-200"
      }`} />

      <CardHeader className="pb-2 pt-4">
        {/* 城市 + 标签行 */}
        <div className="flex items-center gap-2 mb-2 flex-wrap">
          <span className="text-xs font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded">{cityZh}</span>
          <span className={`text-xs px-2 py-0.5 rounded border ${phaseColor}`}>{phaseLabel}</span>
          <span className={`text-xs px-2 py-0.5 rounded border ${paceColor}`}>{paceLabel}</span>
          {assembly.span_days && (
            <span className="text-xs px-2 py-0.5 rounded bg-indigo-50 text-indigo-600 border border-indigo-200">{assembly.span_days}日</span>
          )}
          {weather_sensitive && (
            <span className="text-xs px-2 py-0.5 rounded bg-yellow-50 text-yellow-700 border border-yellow-200">天气敏感</span>
          )}
        </div>

        {/* 标题 */}
        <h3 className="font-bold text-slate-900 text-base leading-snug">{label}</h3>
        <p className="text-[10px] text-slate-400 mt-0.5 font-mono">{template_id}</p>

        {/* 情绪 */}
        {mood && (
          <p className="text-sm text-indigo-500 mt-1.5">「{mood}」</p>
        )}

        {/* 元信息 */}
        <div className="flex flex-wrap gap-x-3 gap-y-1 mt-2 text-xs text-slate-500">
          {core_entities.length > 0 && (
            <span>灵魂景点：{core_entities.join("、")}</span>
          )}
          <span>人群：{audienceZh}</span>
        </div>
      </CardHeader>

      <CardContent className="pt-0 pb-4">
        {/* 描述 */}
        {descClean && (
          <div className="mb-3">
            <p className="text-sm text-slate-600 leading-relaxed">{descDisplay}</p>
            {descTooLong && (
              <button onClick={() => setDescExpanded(!descExpanded)} className="text-xs text-indigo-500 mt-1 hover:underline">
                {descExpanded ? "收起" : "展开全部"}
              </button>
            )}
          </div>
        )}

        {/* 交通/住宿提示 */}
        {hotel_area_note && (
          <div className={`mb-3 p-2.5 rounded-lg text-xs leading-relaxed ${
            needsTransport ? "bg-blue-50 text-blue-700" : "bg-slate-50 text-slate-600"
          }`}>
            <span className="font-medium">{needsTransport ? "🚃 交通" : "🏨 住宿"}：</span>
            {hotel_area_note}
          </div>
        )}

        {/* 时间线 */}
        <div className="border-t border-slate-100 pt-3">
          <p className="text-[10px] text-slate-400 mb-2 font-medium uppercase tracking-wider">
            {viewMode === "opus" ? "行程脉络" : "完整时间线"}
          </p>

          {isMultiDay ? (
            // 多日模板分天
            Array.from(slotsByDay.entries())
              .sort(([a], [b]) => a - b)
              .map(([dayNum, daySlots]) => (
                <div key={dayNum} className="mb-3">
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="text-xs font-bold text-indigo-500 bg-indigo-50 px-2 py-0.5 rounded">
                      第{dayNum}天
                    </span>
                    <div className="flex-1 h-px bg-slate-100" />
                  </div>
                  {daySlots.map((slot) =>
                    viewMode === "opus"
                      ? <SlotLineOpus key={slot.slot_id} slot={slot} areas={areas} />
                      : <SlotLineFull key={slot.slot_id} slot={slot} areas={areas} />
                  )}
                </div>
              ))
          ) : (
            allSlots.map((slot) =>
              viewMode === "opus"
                ? <SlotLineOpus key={slot.slot_id} slot={slot} areas={areas} />
                : <SlotLineFull key={slot.slot_id} slot={slot} areas={areas} />
            )
          )}
        </div>
      </CardContent>
    </Card>
  );
}
