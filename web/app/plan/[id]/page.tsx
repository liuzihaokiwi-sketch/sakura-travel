"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import Link from "next/link";
import { Suspense } from "react";
import { Button } from "@/components/ui/button";
import { PDF_NOTICE } from "@/lib/content/pricing";
import { cn } from "@/lib/utils";
import { fadeInUp, staggerContainer } from "@/lib/animations";
import { WECHAT_ID } from "@/lib/constants";
import { copyToClipboard } from "@/lib/clipboard";

// ── Types ──────────────────────────────────────────────────────────────────
interface PlanItem {
  time?: string;
  icon?: string;
  place?: string;
  entity_name?: string;  // backend field
  reason?: string;
  copy_zh?: string;      // backend field
  duration?: string;
  duration_min?: number; // backend field
  item_type?: string;
}

interface PlanDay {
  num?: number;
  day_number?: number;   // backend field
  theme?: string;
  day_theme?: string;    // backend field
  items: PlanItem[];
  tips?: { photo?: string; avoid?: string };
}

interface ReportContent {
  version?: string;
  generated_at?: string;
  layer1_overview?: {
    design_philosophy?: { summary?: string; key_points?: string[] };
    overview?: { route_summary?: string; intensity_map?: string[]; highlights?: string[] };
    booking_reminders?: { item?: string; deadline?: string; impact?: string }[];
    seasonal_tips?: string;
    prep_checklist?: { title?: string; sections?: { heading?: string; content?: string }[] };
  };
  layer2_daily?: {
    day_number?: number;
    city_code?: string;
    day_theme?: string;
    items?: PlanItem[];
    report?: {
      execution_overview?: { timeline_summary?: string; area?: string; intensity?: string; top_expectation?: string };
      why_this_arrangement?: string[];
      highlights?: { name?: string; description?: string; photo_tip?: string; nearby_bonus?: string }[];
      notes_and_planb?: { risk_warnings?: string[]; weather_plan?: string; energy_plan?: string; clothing_tip?: string };
    };
    conditional_pages?: string[];
  }[];
  layer3_appendix?: {
    prep_checklist?: { title?: string; sections?: { heading?: string; content?: string }[] };
  };
  meta?: Record<string, unknown>;
}

interface PlanData {
  title?: string;
  tags?: string[];
  dates?: string;
  days: PlanDay[];
  hotel?: { area?: string; reason?: string; budget?: string };
  transport?: string;
  checklist?: string[];
  // backend fields
  plan_id?: string;
  plan_metadata?: Record<string, unknown>;
  report_content?: ReportContent;
}

// ── Mock complete plan data (fallback when API unavailable) ─────────────────
const MOCK_PLAN: PlanData = {
  title: "东京 7 日 · 樱花季深度行程",
  tags: ["👫 两人出行", "📸 出片优先", "🍣 美食探索", "🌸 樱花季"],
  dates: "2026年3月28日 — 4月3日",
  days: [
    {
      num: 1, theme: "浅草·上野 — 历史与下町风情",
      items: [
        { time: "09:00", icon: "🌸", place: "上野恩赐公园", reason: "早上人少，樱花光线最柔和", duration: "1.5h" },
        { time: "10:30", icon: "🏛️", place: "东京国立博物馆", reason: "就在公园旁，不用额外赶路", duration: "1h" },
        { time: "12:00", icon: "🍜", place: "浅草 弁天（拉面）", reason: "浓厚豚骨系，步行3分钟到浅草寺", duration: "1h" },
        { time: "13:30", icon: "⛩️", place: "浅草寺 + 仲见世通", reason: "午后人流比上午少30%，拍照更舒服", duration: "1.5h" },
        { time: "15:30", icon: "🛍️", place: "阿美横丁", reason: "从浅草走10分钟，顺路不回头", duration: "1h" },
        { time: "17:00", icon: "🌇", place: "隅田川河畔散步", reason: "本地人傍晚散步的路线，天际线很美", duration: "40min" },
      ],
      tips: { photo: "上野公园9点前拍樱花，光线柔和人极少", avoid: "仲见世通的人形烧店排队很久，不如去旁边小巷" },
    },
    {
      num: 2, theme: "涩谷·原宿 — 潮流与绿意",
      items: [
        { time: "09:00", icon: "⛩️", place: "明治神宫", reason: "早晨安静庄严，和下午的原宿形成对比", duration: "1h" },
        { time: "10:30", icon: "🛍️", place: "竹下通 + 表参道", reason: "上午人少，适合逛和拍", duration: "2h" },
        { time: "12:30", icon: "🍣", place: "涩谷 鮨 小野（寿司）", reason: "当地人午间套餐性价比极高", duration: "1h" },
        { time: "14:00", icon: "🌸", place: "代代木公园", reason: "东京市中心最大的赏樱地，可以野餐", duration: "1.5h" },
        { time: "16:00", icon: "🏙️", place: "涩谷Sky展望台", reason: "日落前上去，同时看白天和夜景", duration: "1h" },
        { time: "18:00", icon: "🌆", place: "涩谷十字路口", reason: "日落后灯光亮起拍最经典", duration: "30min" },
      ],
      tips: { photo: "涩谷十字路口18:30灯光最好看，站在星巴克二楼拍", avoid: "原宿周末人非常多，我们安排在工作日" },
    },
    {
      num: 3, theme: "新宿·中野 — 繁华与动漫",
      items: [
        { time: "09:00", icon: "🌸", place: "新宿御苑", reason: "65种1000+棵樱花，东京最美赏樱地", duration: "2h" },
        { time: "11:30", icon: "🍜", place: "风雲児（沾面）", reason: "Tabelog 3.7，新宿最佳拉面之一", duration: "1h" },
        { time: "13:00", icon: "🏬", place: "伊势丹百货", reason: "地下食品层是隐藏美食天堂", duration: "1h" },
        { time: "14:30", icon: "🎮", place: "中野百老汇", reason: "比秋叶原更本地的动漫圣地", duration: "1.5h" },
        { time: "16:30", icon: "📸", place: "歌舞伎町一番街", reason: "白天安全，适合拍经典霓虹招牌", duration: "30min" },
        { time: "17:30", icon: "🌇", place: "东京都厅展望室", reason: "免费！360度看东京日落", duration: "1h" },
      ],
      tips: { photo: "新宿御苑禁止饮酒，但可以野餐拍照", avoid: "歌舞伎町晚上不建议深入，白天拍照即可" },
    },
  ],
  hotel: { area: "新宿西口", reason: "到上野/涩谷/新宿御苑都在20分钟内，性价比最高的中间位置", budget: "¥600-900/晚" },
  transport: "7日内推荐用 Suica + 都营一日券组合，比JR Pass省约¥3000",
  checklist: ["护照（有效期6个月以上）", "Visit Japan Web 提前注册", "Suica 卡（到达后充值）", "移动WiFi/流量卡", "舒适步行鞋（日均1.5万步）", "充电宝", "常用药品", "日元现金 ¥30,000备用"],
};

// ── Normalize backend plan to frontend shape ────────────────────────────────
function normalizePlan(raw: PlanData): PlanData {
  const days: PlanDay[] = (raw.days || []).map((d) => ({
    num: d.day_number ?? d.num,
    theme: d.day_theme ?? d.theme ?? "",
    items: (d.items || []).map((item) => ({
      time: item.time ?? "",
      icon: item.icon ?? (item.item_type === "restaurant" ? "🍽️" : "📍"),
      place: item.entity_name ?? item.place ?? "",
      reason: item.copy_zh ?? item.reason ?? "",
      duration: item.duration ?? (item.duration_min ? `${item.duration_min}min` : ""),
    })),
    tips: d.tips,
  }));
  const meta = (raw.plan_metadata as Record<string, unknown>) ?? {};
  return {
    title: (meta.title as string) ?? raw.title ?? MOCK_PLAN.title,
    tags: (meta.tags as string[]) ?? raw.tags ?? MOCK_PLAN.tags,
    dates: (meta.dates as string) ?? raw.dates ?? MOCK_PLAN.dates,
    days: days.length > 0 ? days : MOCK_PLAN.days,
    hotel: (meta.hotel as PlanData["hotel"]) ?? raw.hotel ?? MOCK_PLAN.hotel,
    transport: (meta.transport as string) ?? raw.transport ?? MOCK_PLAN.transport,
    checklist: (meta.checklist as string[]) ?? raw.checklist ?? MOCK_PLAN.checklist,
  };
}

// ── Plan content component ──────────────────────────────────────────────────

function PlanContent({ params }: { params: { id: string } }) {
  const searchParams = useSearchParams();
  const mode = searchParams.get("mode");
  const isPreview = mode === "preview";
  const isExport = searchParams.get("export") === "true";
  const [exporting, setExporting] = useState(false);
  const [expandedDay, setExpandedDay] = useState(0);
  const [plan, setPlan] = useState<PlanData>(MOCK_PLAN);
  const [loading, setLoading] = useState(true);

  const [report, setReport] = useState<ReportContent | null>(null);

  // Fetch real plan data from API
  useEffect(() => {
    const isMockId = params.id === "demo" || params.id === "preview";
    if (isMockId) { setLoading(false); return; }

    fetch(`/api/plan/${params.id}`)
      .then((r) => r.json())
      .then((data) => {
        if (!data.error) {
          setPlan(normalizePlan(data));
          if (data.report_content?.layer2_daily) {
            setReport(data.report_content);
          }
        }
      })
      .catch(() => { /* silently use MOCK */ })
      .finally(() => setLoading(false));
  }, [params.id]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-warm-50">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-warm-300 border-t-warm-500 rounded-full animate-spin mx-auto mb-3" />
          <p className="text-stone-400 text-sm">正在加载你的行程...</p>
        </div>
      </div>
    );
  }

  // In preview mode, only show Day 1
  const visibleDays = isPreview ? plan.days.slice(0, 1) : plan.days;
  const totalDays = 7;

  return (
    <div className="min-h-screen bg-warm-50">
      {/* Preview banner */}
      {isPreview && (
        <div className="bg-warm-100 border-b border-warm-200 py-3 px-6 text-center sticky top-0 z-50">
          <p className="text-sm text-warm-600 font-medium">
            🆓 这是你的免费预览 · 完整版还有 {totalDays - 1} 天精彩内容
          </p>
        </div>
      )}

      {/* Cover */}
      <div className="relative bg-gradient-to-b from-stone-900 via-stone-800 to-stone-900 text-white py-16 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <p className="text-xs tracking-[0.3em] text-white/40 font-mono mb-4">
            {isPreview ? "FREE PREVIEW · DAY 1" : "YOUR TRAVEL PLAN"}
          </p>
          <h1 className="font-display text-3xl md:text-4xl font-bold mb-3">{plan.title}</h1>
          <p className="text-white/50 text-sm mb-4">{plan.dates}</p>
          <div className="flex flex-wrap justify-center gap-2">
            {(plan.tags ?? []).map((t) => (
              <span key={t} className="text-xs bg-white/10 px-3 py-1 rounded-full">{t}</span>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-4 md:px-6 py-8 space-y-8">
        {/* Overview */}
        <motion.section variants={fadeInUp} initial="initial" animate="animate">
          <h2 className="text-lg font-bold text-stone-900 mb-4">📋 行程总览</h2>
          <div className="overflow-x-auto scrollbar-hide -mx-1 px-1">
            <div className="grid grid-cols-7 gap-2 min-w-[340px]">
            {Array.from({ length: totalDays }, (_, i) => {
              const d = plan.days[i];
              const isLocked = isPreview && i > 0;
              return (
                <button
                  key={i}
                  onClick={() => !isLocked && d && setExpandedDay(i)}
                  className={cn(
                    "rounded-xl p-3 text-center transition-all",
                    isLocked
                      ? "bg-stone-100/50 cursor-not-allowed opacity-60"
                      : d
                        ? "bg-white border border-stone-100 hover:shadow-md cursor-pointer"
                        : "bg-stone-100/50"
                  )}
                >
                  <p className="text-xs font-bold text-warm-400">Day {i + 1}</p>
                  <p className="text-[9px] text-stone-400 mt-1 line-clamp-2">
                    {isLocked ? "🔒" : d?.theme?.split("—")[0] || "..."}
                  </p>
                </button>
              );
            })}
            </div>
          </div>
        </motion.section>

        {/* Daily details */}
        {visibleDays.map((day) => (
          <motion.section key={day.num} variants={staggerContainer} initial="initial" whileInView="animate" viewport={{ once: true }}>
            <div className="flex items-center gap-3 mb-4">
              <span className="w-10 h-10 rounded-full bg-gradient-to-br from-warm-300 to-sakura-400 text-white flex items-center justify-center font-bold text-sm shadow">{day.num}</span>
              <div>
                <h3 className="text-lg font-bold text-stone-900">Day {day.num}</h3>
                <p className="text-sm text-warm-400">{day.theme}</p>
              </div>
            </div>

            {day.items.map((item) => (
              <motion.div key={item.time} variants={fadeInUp} className="flex gap-4 mb-3">
                <div className="flex flex-col items-center">
                  <span className="text-xs font-mono text-stone-400 w-12 text-right">{item.time}</span>
                  <div className="w-px flex-1 bg-stone-200 mt-1" />
                </div>
                <div className="flex-1 bg-white rounded-xl border border-stone-100 p-4">
                  <div className="flex items-center gap-2 mb-1">
                    <span>{item.icon}</span>
                    <h4 className="font-semibold text-stone-900 text-sm">{item.place}</h4>
                    <span className="text-xs text-stone-400 ml-auto">{item.duration}</span>
                  </div>
                  <p className="text-xs text-stone-500 leading-relaxed">💡 {item.reason}</p>
                </div>
              </motion.div>
            ))}

            {/* Tips sidebar */}
            {(day.tips?.photo || day.tips?.avoid) && (
              <div className="grid grid-cols-2 gap-3 mt-2 mb-6">
                {day.tips?.photo && (
                  <div className="bg-sakura-50 border border-sakura-100 rounded-xl p-3">
                    <p className="text-xs font-semibold text-sakura-500 mb-1">📸 拍照提示</p>
                    <p className="text-xs text-stone-600">{day.tips.photo}</p>
                  </div>
                )}
                {day.tips?.avoid && (
                  <div className="bg-amber-50 border border-amber-100 rounded-xl p-3">
                    <p className="text-xs font-semibold text-amber-600 mb-1">⚠️ 避坑提醒</p>
                    <p className="text-xs text-stone-600">{day.tips.avoid}</p>
                  </div>
                )}
              </div>
            )}
          </motion.section>
        ))}

        {/* ══════ REPORT CONTENT (3-Layer) ══════ */}
        {report && !isPreview && (
          <>
            {/* Layer 1: Design Philosophy */}
            {report.layer1_overview?.design_philosophy?.summary && (
              <section className="bg-gradient-to-br from-indigo-50 to-violet-50 rounded-2xl border border-indigo-100 p-6">
                <h2 className="text-lg font-bold text-indigo-900 mb-3">🎯 设计理念</h2>
                <p className="text-sm text-indigo-800 leading-relaxed">{report.layer1_overview.design_philosophy.summary}</p>
                {report.layer1_overview.design_philosophy.key_points && (
                  <ul className="mt-3 space-y-1.5">
                    {report.layer1_overview.design_philosophy.key_points.map((p, i) => (
                      <li key={i} className="text-xs text-indigo-700 flex items-start gap-2">
                        <span className="text-indigo-400 mt-0.5">▸</span>{p}
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            )}

            {/* Layer 1: Route Overview */}
            {report.layer1_overview?.overview?.route_summary && (
              <section className="bg-white rounded-2xl border border-stone-100 p-6">
                <h2 className="text-lg font-bold text-stone-900 mb-3">🗺️ 路线概述</h2>
                <p className="text-sm text-stone-600 leading-relaxed">{report.layer1_overview.overview.route_summary}</p>
                {report.layer1_overview.overview.intensity_map && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {report.layer1_overview.overview.intensity_map.map((m, i) => (
                      <span key={i} className="text-xs bg-warm-50 text-warm-600 px-3 py-1 rounded-full border border-warm-200">{m}</span>
                    ))}
                  </div>
                )}
                {report.layer1_overview.overview.highlights && (
                  <div className="mt-4">
                    <p className="text-xs font-semibold text-stone-500 mb-2">✨ 全程亮点</p>
                    <ul className="space-y-1">
                      {report.layer1_overview.overview.highlights.map((h, i) => (
                        <li key={i} className="text-xs text-stone-600 flex items-start gap-2">
                          <span className="text-amber-400">★</span>{h}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </section>
            )}

            {/* Layer 1: Booking Reminders */}
            {report.layer1_overview?.booking_reminders && report.layer1_overview.booking_reminders.length > 0 && (
              <section className="bg-amber-50 rounded-2xl border border-amber-200 p-6">
                <h2 className="text-lg font-bold text-amber-900 mb-3">📅 预约提醒</h2>
                <div className="space-y-2">
                  {report.layer1_overview.booking_reminders.map((b, i) => (
                    <div key={i} className="bg-white rounded-xl p-3 border border-amber-100">
                      <p className="text-sm font-medium text-stone-800">{b.item}</p>
                      {b.deadline && <p className="text-xs text-amber-600 mt-1">⏰ {b.deadline}</p>}
                      {b.impact && <p className="text-xs text-stone-500 mt-0.5">💡 {b.impact}</p>}
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* Layer 1: Seasonal Tips */}
            {report.layer1_overview?.seasonal_tips && (
              <section className="bg-emerald-50 rounded-2xl border border-emerald-200 p-4">
                <p className="text-sm text-emerald-800">🌸 {report.layer1_overview.seasonal_tips}</p>
              </section>
            )}

            {/* Layer 2: Daily Reports */}
            {report.layer2_daily?.map((day) => {
              const rpt = day.report;
              if (!rpt) return null;
              return (
                <section key={day.day_number} className="bg-white rounded-2xl border border-stone-100 p-6 space-y-4">
                  <div className="flex items-center gap-3">
                    <span className="w-10 h-10 rounded-full bg-gradient-to-br from-sky-400 to-blue-500 text-white flex items-center justify-center font-bold text-sm shadow">{day.day_number}</span>
                    <div>
                      <h3 className="text-lg font-bold text-stone-900">Day {day.day_number} 攻略</h3>
                      <p className="text-sm text-stone-400">{day.day_theme} · {day.city_code}</p>
                    </div>
                    {rpt.execution_overview?.intensity && (
                      <span className="ml-auto text-xs bg-sky-50 text-sky-600 px-3 py-1 rounded-full border border-sky-200">{rpt.execution_overview.intensity}</span>
                    )}
                  </div>

                  {/* Timeline */}
                  {rpt.execution_overview?.timeline_summary && (
                    <div className="bg-stone-50 rounded-xl p-4">
                      <p className="text-xs font-semibold text-stone-500 mb-1">📍 今日概览</p>
                      <p className="text-sm text-stone-700 leading-relaxed">{rpt.execution_overview.timeline_summary}</p>
                      {rpt.execution_overview.top_expectation && (
                        <p className="text-xs text-amber-600 mt-2">🌟 最期待：{rpt.execution_overview.top_expectation}</p>
                      )}
                    </div>
                  )}

                  {/* Why this arrangement */}
                  {rpt.why_this_arrangement && rpt.why_this_arrangement.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-stone-500 mb-2">💡 为什么这样安排</p>
                      <ul className="space-y-1">
                        {rpt.why_this_arrangement.map((w, i) => (
                          <li key={i} className="text-xs text-stone-600 flex items-start gap-2">
                            <span className="text-indigo-400 mt-0.5">▸</span>{w}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Highlights */}
                  {rpt.highlights && rpt.highlights.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-stone-500 mb-2">✨ 今日亮点</p>
                      <div className="space-y-3">
                        {rpt.highlights.map((h, i) => (
                          <div key={i} className="bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl p-4 border border-amber-100">
                            <h4 className="text-sm font-semibold text-stone-800">{h.name}</h4>
                            {h.description && <p className="text-xs text-stone-600 mt-1 leading-relaxed">{h.description}</p>}
                            <div className="flex flex-wrap gap-3 mt-2">
                              {h.photo_tip && <span className="text-[10px] text-sakura-500">📸 {h.photo_tip}</span>}
                              {h.nearby_bonus && <span className="text-[10px] text-emerald-600">📍 {h.nearby_bonus}</span>}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Notes & Plan B */}
                  {rpt.notes_and_planb && (
                    <div className="grid grid-cols-2 gap-3">
                      {rpt.notes_and_planb.risk_warnings && rpt.notes_and_planb.risk_warnings.length > 0 && (
                        <div className="bg-red-50 rounded-xl p-3 border border-red-100">
                          <p className="text-xs font-semibold text-red-600 mb-1">⚠️ 注意事项</p>
                          {rpt.notes_and_planb.risk_warnings.map((w, i) => (
                            <p key={i} className="text-[10px] text-red-700">{w}</p>
                          ))}
                        </div>
                      )}
                      {rpt.notes_and_planb.weather_plan && (
                        <div className="bg-blue-50 rounded-xl p-3 border border-blue-100">
                          <p className="text-xs font-semibold text-blue-600 mb-1">🌧️ 雨天备选</p>
                          <p className="text-[10px] text-blue-700">{rpt.notes_and_planb.weather_plan}</p>
                        </div>
                      )}
                      {rpt.notes_and_planb.energy_plan && (
                        <div className="bg-orange-50 rounded-xl p-3 border border-orange-100">
                          <p className="text-xs font-semibold text-orange-600 mb-1">⚡ 体力不够</p>
                          <p className="text-[10px] text-orange-700">{rpt.notes_and_planb.energy_plan}</p>
                        </div>
                      )}
                      {rpt.notes_and_planb.clothing_tip && (
                        <div className="bg-violet-50 rounded-xl p-3 border border-violet-100">
                          <p className="text-xs font-semibold text-violet-600 mb-1">👔 穿着建议</p>
                          <p className="text-[10px] text-violet-700">{rpt.notes_and_planb.clothing_tip}</p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Conditional pages */}
                  {day.conditional_pages && day.conditional_pages.length > 0 && (
                    <div className="flex gap-2 pt-2 border-t border-stone-100">
                      {day.conditional_pages.map((p) => (
                        <span key={p} className="text-[10px] bg-stone-100 text-stone-500 px-2 py-0.5 rounded-full">
                          {p === "transport" ? "🚃 交通页" : p === "hotel" ? "🏨 住宿页" : p === "restaurant" ? "🍽️ 美食页" : p}
                        </span>
                      ))}
                    </div>
                  )}
                </section>
              );
            })}

            {/* Layer 3: Prep Checklist */}
            {report.layer3_appendix?.prep_checklist?.sections && (
              <section className="bg-white rounded-2xl border border-stone-100 p-6">
                <h2 className="text-lg font-bold text-stone-900 mb-4">{report.layer3_appendix.prep_checklist.title || "📋 出发准备"}</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {report.layer3_appendix.prep_checklist.sections.map((sec, i) => (
                    <div key={i} className="bg-stone-50 rounded-xl p-4">
                      <p className="text-sm font-semibold text-stone-800 mb-1">{sec.heading}</p>
                      <p className="text-xs text-stone-600 leading-relaxed">{sec.content}</p>
                    </div>
                  ))}
                </div>
              </section>
            )}
          </>
        )}

        {/* Preview: locked content teaser */}
        {isPreview && (
          <section className="relative">
            {/* Blurred fake content */}
            <div className="space-y-4 opacity-30 blur-[2px] select-none pointer-events-none">
              {[2, 3, 4].map((n) => (
                <div key={n} className="bg-white rounded-xl border border-stone-100 p-6">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 rounded-full bg-stone-200" />
                    <div>
                      <div className="h-4 w-32 bg-stone-200 rounded" />
                      <div className="h-3 w-48 bg-stone-100 rounded mt-1" />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="h-3 w-full bg-stone-100 rounded" />
                    <div className="h-3 w-3/4 bg-stone-100 rounded" />
                    <div className="h-3 w-5/6 bg-stone-100 rounded" />
                  </div>
                </div>
              ))}
            </div>
            {/* Overlay CTA */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="bg-white/95 backdrop-blur-sm rounded-2xl shadow-xl p-8 text-center max-w-sm mx-6 border border-warm-100">
                <span className="text-4xl block mb-3">🔒</span>
                <h3 className="font-display text-xl font-bold text-stone-900 mb-2">
                  还有 {totalDays - 1} 天精彩内容
                </h3>
                <p className="text-sm text-stone-500 mb-1">
                  完整版包含每天的详细路线、餐厅推荐、交通方案、备选计划...
                </p>
                <p className="text-sm text-stone-500 mb-6">
                  共 <strong>30-40 页</strong>，首发价仅 <strong className="text-warm-500">¥248</strong>
                </p>
                <p className="text-xs text-stone-400 mb-4">
                  联系你的规划师解锁完整方案 👇
                </p>
                <div className="flex flex-col items-center gap-2">
                  <p className="text-sm font-medium text-stone-700">
                    微信：<span className="font-mono">{WECHAT_ID}</span>
                  </p>
                  <button
                    onClick={() => copyToClipboard(WECHAT_ID)}
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-warm-100 text-warm-600 text-sm font-medium hover:bg-warm-200 transition-colors"
                  >
                    📋 复制微信号
                  </button>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* Full version: hotel, transport, checklist */}
        {!isPreview && (
          <>
            {/* Hotel */}
            <section className="bg-white rounded-2xl border border-stone-100 p-6">
              <h2 className="text-lg font-bold text-stone-900 mb-3">🏨 住宿建议</h2>
              <p className="text-sm text-stone-700 font-medium">{plan.hotel?.area}</p>
              <p className="text-xs text-stone-500 mt-1">💡 {plan.hotel?.reason}</p>
              <p className="text-xs text-warm-400 mt-2">预算参考：{plan.hotel?.budget}</p>
            </section>

            {/* Transport */}
            <section className="bg-white rounded-2xl border border-stone-100 p-6">
              <h2 className="text-lg font-bold text-stone-900 mb-3">🚃 交通方案</h2>
              <p className="text-sm text-stone-600">{plan.transport}</p>
            </section>

            {/* Checklist */}
            <section className="bg-white rounded-2xl border border-stone-100 p-6">
              <h2 className="text-lg font-bold text-stone-900 mb-3">✅ 出行准备清单</h2>
              <div className="grid grid-cols-2 gap-2">
                {(plan.checklist ?? []).map((item) => (
                  <label key={item} className="flex items-center gap-2 text-sm text-stone-600 cursor-pointer">
                    <input type="checkbox" className="rounded border-stone-300 text-warm-400 focus:ring-warm-300" />
                    <span>{item}</span>
                  </label>
                ))}
              </div>
            </section>

            {/* Actions — hidden in export mode */}
            {!isExport && (
              <>
                <div className="flex gap-3">
                  <Link href={`/plan/${params.id}/edit`} className="flex-1">
                    <Button variant="outline" className="w-full">✏️ 精调行程（剩余2次）</Button>
                  </Link>
                  <Link href={`/plan/${params.id}/upgrade`} className="flex-1">
                    <Button variant="warm" className="w-full">⭐ 升级管家版</Button>
                  </Link>
                </div>

                {/* Share + Export */}
                <div className="text-center py-6 border-t border-stone-100 space-y-4">
                  <p className="text-sm text-stone-500 mb-2">觉得有用？分享给一起去的朋友</p>
                  
                  {/* 导出 PDF — 主要 CTA */}
                  <Button
                    variant="warm"
                    className="w-full max-w-xs mx-auto"
                    disabled={exporting}
                    onClick={async () => {
                      setExporting(true);
                      try {
                        const resp = await fetch(`/api/plan/${params.id}/pdf`);
                        if (!resp.ok) {
                          const err = await resp.json().catch(() => ({}));
                          throw new Error(err.error || "PDF 生成失败");
                        }
                        const contentType = resp.headers.get("content-type") || "";
                        if (contentType.includes("application/pdf")) {
                          // 直接下载 PDF
                          const blob = await resp.blob();
                          const url = URL.createObjectURL(blob);
                          const a = document.createElement("a");
                          a.href = url;
                          a.download = `sakura-plan-${params.id.slice(0, 8)}.pdf`;
                          a.click();
                          URL.revokeObjectURL(url);
                        } else {
                          // 后端返回了打印友好 HTML（weasyprint 不可用时）
                          const html = await resp.text();
                          const w = window.open("", "_blank");
                          if (w) {
                            w.document.write(html);
                            w.document.close();
                          }
                        }
                      } catch (err: unknown) {
                        alert(err instanceof Error ? err.message : "PDF 导出失败，请稍后重试");
                        console.error(err);
                      } finally {
                        setExporting(false);
                      }
                    }}
                  >
                    {exporting ? "⏳ 正在生成 PDF..." : "📄 导出完整 PDF 攻略"}
                  </Button>

                  <div className="flex justify-center gap-3">
                    <Button variant="outline" size="sm">📤 分享行程</Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={exporting}
                      onClick={async () => {
                        setExporting(true);
                        try {
                          const resp = await fetch("/api/export/plan-image", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ planId: params.id }),
                          });
                          if (!resp.ok) throw new Error("导出失败");
                          const blob = await resp.blob();
                          const url = URL.createObjectURL(blob);
                          const a = document.createElement("a");
                          a.href = url;
                          a.download = `plan-${params.id}-share.png`;
                          a.click();
                          URL.revokeObjectURL(url);
                        } catch (err) {
                          alert("导出图片失败，请稍后重试");
                          console.error(err);
                        } finally {
                          setExporting(false);
                        }
                      }}
                    >
                      {exporting ? "⏳ 生成中..." : "🖼️ 导出朋友圈图"}
                    </Button>
                  </div>
                </div>

                {/* PDF 交付说明（折叠式） */}
                <details className="group rounded-xl border border-stone-100 bg-stone-50 overflow-hidden">
                  <summary className="flex cursor-pointer items-center justify-between px-4 py-3 text-sm font-medium text-stone-600 hover:bg-stone-100 transition-colors marker:content-none">
                    <span className="flex items-center gap-2">
                      <span>📄</span>
                      <span>{PDF_NOTICE.deliveryPage.heading}</span>
                    </span>
                    <span className="text-stone-400 text-xs transition-transform duration-200 group-open:rotate-45">＋</span>
                  </summary>
                  <ul className="px-4 pb-4 pt-1 space-y-1.5">
                    {PDF_NOTICE.deliveryPage.bullets.map((b) => (
                      <li key={b} className="flex items-start gap-2 text-xs text-stone-500">
                        <span className="text-stone-400 flex-shrink-0 mt-0.5">·</span>
                        <span>{b}</span>
                      </li>
                    ))}
                  </ul>
                </details>
              </>
            )}

            {/* Export mode: watermark branding */}
            {isExport && (
              <div className="text-center py-6 border-t border-stone-100">
                <p className="text-xs text-stone-400">🌸 Sakura Rush 2026 · 定制行程</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// ── Page wrapper ────────────────────────────────────────────────────────────

export default function PlanPage({ params }: { params: { id: string } }) {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-warm-50">
        <p className="text-stone-400">加载行程...</p>
      </div>
    }>
      <PlanContent params={params} />
    </Suspense>
  );
}