"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import type { Metadata } from "next";

// ── 数据定义 ─────────────────────────────────────────────────────────────────

const CIRCLES = [
  { key: "kansai", name: "关西（京都/大阪/奈良）", emoji: "⛩️" },
  { key: "kanto", name: "关东（东京/横滨/镰仓）", emoji: "🗼" },
  { key: "hokkaido", name: "北海道（札幌/函馆/富良野）", emoji: "🐻" },
  { key: "okinawa", name: "冲绳（那霸/石垣岛）", emoji: "🌊" },
];

const BUDGET_LEVELS = [
  { key: "budget", label: "穷游", desc: "青旅/胶囊酒店，便利店+食堂", emoji: "🎒" },
  { key: "mid", label: "普通", desc: "商务酒店，拉面+回转寿司", emoji: "🏨" },
  { key: "premium", label: "享受型", desc: "精品酒店，料亭+izakaya", emoji: "✨" },
  { key: "luxury", label: "奢华", desc: "顶级旅馆，米其林餐厅", emoji: "👑" },
];

// 各圈各档位每日花费（人均/天，含住宿，CNY）
const DAILY_COSTS: Record<string, Record<string, {
  hotel: [number, number];
  food: [number, number];
  transport: [number, number];
  attraction: [number, number];
  shopping: [number, number];
  tips: string[];
}>> = {
  kansai: {
    budget:  { hotel:[100,180], food:[80,120],  transport:[30,50],  attraction:[20,50],  shopping:[50,100], tips:["关西1日周游券省交通费","松屋/吉野家解决早餐，50元内"] },
    mid:     { hotel:[300,500], food:[200,350],  transport:[60,100], attraction:[50,100], shopping:[150,300],tips:["买JR关西广域Pass可省交通","烧肉定食150元够营养"] },
    premium: { hotel:[800,1500],food:[500,900],  transport:[100,200],attraction:[100,200],shopping:[500,1000],tips:["京都料亭需提前1-2个月订","嵐山精品旅馆含早需早订"] },
    luxury:  { hotel:[2000,5000],food:[1500,3000],transport:[200,400],attraction:[200,400],shopping:[1000,3000],tips:["顶级料亭如吉兆需中介预约","专车接送需提前安排"] },
  },
  kanto: {
    budget:  { hotel:[120,200], food:[80,130],  transport:[40,70],  attraction:[20,60],  shopping:[50,100], tips:["东京都市1日券680日元","东京无处不在的吉野家"] },
    mid:     { hotel:[350,600], food:[220,380],  transport:[80,130], attraction:[60,120], shopping:[200,350],tips:["Suica/Pasmo交通卡全城通用","浅草仲见世伴手礼性价比高"] },
    premium: { hotel:[1000,2000],food:[600,1000], transport:[150,250],attraction:[120,250],shopping:[600,1200],tips:["西麻布料理亭需提前预约","新宿高岛屋地下美食精选"] },
    luxury:  { hotel:[2500,6000],food:[2000,4000],transport:[250,500],attraction:[250,500],shopping:[1500,4000],tips:["东京湾豪华游艇晚餐需预约","银座顶级购物需预算充足"] },
  },
  hokkaido: {
    budget:  { hotel:[100,180], food:[80,130],  transport:[50,80],  attraction:[20,50],  shopping:[50,100], tips:["JR北海道铁路通票推荐","旋转寿司150元吃饱"] },
    mid:     { hotel:[280,480], food:[200,350],  transport:[100,160],attraction:[50,100], shopping:[150,250],tips:["租车自驾比电车灵活","富良野花田门票约¥500"] },
    premium: { hotel:[700,1400],food:[500,800],  transport:[150,250],attraction:[100,200],shopping:[400,800], tips:["富良野农场餐厅需提前订","支笏湖温泉旅馆含早晚餐"] },
    luxury:  { hotel:[1800,4500],food:[1500,2500],transport:[300,500],attraction:[200,400],shopping:[800,2000],tips:["阿寒湖爱努风料理独特体验","包车赏花效率最高"] },
  },
  okinawa: {
    budget:  { hotel:[120,200], food:[80,120],  transport:[60,100], attraction:[30,60],  shopping:[50,100], tips:["公交车较少，建议租摩托","A&W汉堡是本地平价选择"] },
    mid:     { hotel:[300,550], food:[180,300],  transport:[100,180],attraction:[80,150], shopping:[150,300],tips:["租车必备，否则景区难到达","沖縄そば（冲绳荞麦面）必吃"] },
    premium: { hotel:[800,1600],food:[400,700],  transport:[150,280],attraction:[120,250],shopping:[400,800], tips:["石垣岛度假村含早晚餐","潜水证书提前考好"] },
    luxury:  { hotel:[2000,5000],food:[1200,2500],transport:[300,600],attraction:[250,500],shopping:[800,2500],tips:["私人游艇出海需提前预约","顶级度假酒店早订享折扣"] },
  },
};

type BudgetCategory = "hotel" | "food" | "transport" | "attraction" | "shopping";

const CATEGORY_LABELS: Record<BudgetCategory, { icon: string; label: string }> = {
  hotel:      { icon: "🏨", label: "住宿" },
  food:       { icon: "🍜", label: "餐饮" },
  transport:  { icon: "🚅", label: "交通" },
  attraction: { icon: "🎡", label: "门票" },
  shopping:   { icon: "🛍️", label: "购物" },
};

// ── Component ────────────────────────────────────────────────────────────────

function RangeBar({ min, max, globalMax }: { min: number; max: number; globalMax: number }) {
  const leftPct = (min / globalMax) * 100;
  const widthPct = ((max - min) / globalMax) * 100;
  return (
    <div className="relative h-2 bg-stone-100 rounded-full overflow-hidden">
      <div
        className="absolute h-full bg-gradient-to-r from-amber-400 to-orange-400 rounded-full"
        style={{ left: `${leftPct}%`, width: `${Math.max(widthPct, 2)}%` }}
      />
    </div>
  );
}

export default function BudgetPage() {
  const [circle, setCircle] = useState("kansai");
  const [days, setDays] = useState(7);
  const [persons, setPersons] = useState(2);
  const [level, setLevel] = useState("mid");

  const costs = useMemo(() => {
    const data = DAILY_COSTS[circle]?.[level];
    if (!data) return null;
    const categories = Object.keys(CATEGORY_LABELS) as BudgetCategory[];
    const daily = categories.map((cat) => {
      const [lo, hi] = data[cat] as [number, number];
      return { cat, min: lo, max: hi };
    });
    const dailyMin = daily.reduce((a, c) => a + c.min, 0);
    const dailyMax = daily.reduce((a, c) => a + c.max, 0);
    const totalMin = dailyMin * days * persons;
    const totalMax = dailyMax * days * persons;
    // 加机票估算
    const flightEst = { kansai: [2500, 5000], kanto: [2500, 5000], hokkaido: [2800, 5500], okinawa: [2000, 4500] }[circle] || [2500, 5000];
    const grandMin = totalMin + flightEst[0] * persons;
    const grandMax = totalMax + flightEst[1] * persons;
    const globalMax = daily.reduce((a, c) => Math.max(a, c.max), 0);
    return { daily, dailyMin, dailyMax, totalMin, totalMax, grandMin, grandMax, tips: data.tips, flightEst, globalMax };
  }, [circle, days, persons, level]);

  const circleName = CIRCLES.find((c) => c.key === circle)?.name ?? "";
  const levelLabel = BUDGET_LEVELS.find((b) => b.key === level)?.label ?? "";

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-black text-stone-900 mb-1">旅行预算计算器</h1>
      <p className="text-sm text-stone-500 mb-6">选择目的地和出行方式，自动估算花费</p>

      {/* 参数选择 */}
      <div className="bg-white rounded-2xl border border-stone-100 p-5 mb-6 space-y-5">
        {/* 城市圈 */}
        <div>
          <label className="text-xs font-bold text-stone-700 mb-2 block">目的地城市圈</label>
          <div className="grid grid-cols-2 gap-2">
            {CIRCLES.map((c) => (
              <button
                key={c.key}
                onClick={() => setCircle(c.key)}
                className={`flex items-center gap-2 px-3 py-2.5 rounded-xl border text-sm font-semibold transition-all ${
                  circle === c.key ? "bg-amber-50 border-amber-300 text-amber-800" : "border-stone-200 text-stone-600 hover:border-amber-200"
                }`}
              >
                <span>{c.emoji}</span>
                <span className="text-xs leading-tight">{c.name}</span>
              </button>
            ))}
          </div>
        </div>

        {/* 天数 + 人数 */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-bold text-stone-700 mb-2 block">天数：{days}天</label>
            <input
              type="range" min={3} max={14} value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="w-full accent-amber-500"
            />
            <div className="flex justify-between text-[10px] text-stone-400 mt-1">
              <span>3天</span><span>14天</span>
            </div>
          </div>
          <div>
            <label className="text-xs font-bold text-stone-700 mb-2 block">人数：{persons}人</label>
            <input
              type="range" min={1} max={6} value={persons}
              onChange={(e) => setPersons(Number(e.target.value))}
              className="w-full accent-amber-500"
            />
            <div className="flex justify-between text-[10px] text-stone-400 mt-1">
              <span>1人</span><span>6人</span>
            </div>
          </div>
        </div>

        {/* 预算档位 */}
        <div>
          <label className="text-xs font-bold text-stone-700 mb-2 block">预算档位</label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {BUDGET_LEVELS.map((b) => (
              <button
                key={b.key}
                onClick={() => setLevel(b.key)}
                className={`p-2.5 rounded-xl border text-center transition-all ${
                  level === b.key ? "bg-amber-50 border-amber-300" : "border-stone-200 hover:border-amber-200"
                }`}
              >
                <div className="text-xl mb-0.5">{b.emoji}</div>
                <div className="text-xs font-bold text-stone-900">{b.label}</div>
                <div className="text-[9px] text-stone-400 mt-0.5 leading-tight">{b.desc}</div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 结果 */}
      {costs && (
        <>
          <div className="bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200 rounded-2xl p-5 mb-4">
            <div className="text-center mb-4">
              <p className="text-xs text-stone-500 mb-1">{persons}人 · {days}天 · {levelLabel}档 · {circleName.split("（")[0]}</p>
              <p className="text-2xl font-black text-stone-900">
                ¥{Math.round(costs.grandMin / 1000)}k – ¥{Math.round(costs.grandMax / 1000)}k
              </p>
              <p className="text-xs text-stone-500">总预算（含机票估算）</p>
            </div>

            <div className="space-y-3">
              {costs.daily.map(({ cat, min, max }) => {
                const meta = CATEGORY_LABELS[cat];
                return (
                  <div key={cat}>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs font-semibold text-stone-700">{meta.icon} {meta.label}（人均/天）</span>
                      <span className="text-xs font-bold text-amber-700">¥{min}–¥{max}</span>
                    </div>
                    <RangeBar min={min} max={max} globalMax={costs.globalMax} />
                  </div>
                );
              })}

              <div className="border-t border-amber-200 pt-3 mt-3 flex justify-between text-sm font-bold">
                <span className="text-stone-700">每人每天合计</span>
                <span className="text-amber-700">¥{costs.dailyMin}–¥{costs.dailyMax}</span>
              </div>
              <div className="flex justify-between text-xs text-stone-500">
                <span>机票（每人估算）</span>
                <span>¥{costs.flightEst[0]}–¥{costs.flightEst[1]}</span>
              </div>
            </div>
          </div>

          {/* 省钱建议 */}
          <div className="bg-white rounded-2xl border border-stone-100 p-4 mb-6">
            <h3 className="text-sm font-bold text-stone-900 mb-2">💡 省钱建议</h3>
            <ul className="space-y-1.5">
              {costs.tips.map((tip, i) => (
                <li key={i} className="text-xs text-stone-600 flex gap-2">
                  <span className="text-amber-400 font-bold shrink-0">▸</span>
                  <span>{tip}</span>
                </li>
              ))}
            </ul>
          </div>
        </>
      )}

      {/* CTA */}
      <div className="bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-100 rounded-2xl p-5 text-center">
        <p className="text-sm font-bold text-stone-900 mb-1">想要精确到每餐每景点的行程？</p>
        <p className="text-xs text-stone-500 mb-3">AI定制行程 · 30-40页手册 · 拿到就能出发</p>
        <Link
          href="/quiz?from=budget_tool"
          className="inline-block bg-gradient-to-r from-amber-500 to-orange-500 text-white font-bold text-sm px-5 py-2.5 rounded-full shadow hover:shadow-md transition-all"
        >
          免费定制行程 →
        </Link>
      </div>
    </div>
  );
}
