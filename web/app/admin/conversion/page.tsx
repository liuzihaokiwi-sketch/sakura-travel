"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { fadeInUp } from "@/lib/animations";

// ── 数据类型 ─────────────────────────────────────────────────────────────
interface ConversionStats {
  period: string;
  preview_views: number;
  pricing_clicks: number;
  paid_orders: number;
  revenue: number;
  conversion_rate: number;   // preview → paid
  click_rate: number;        // preview → pricing click
}

interface FunnelStep {
  label: string;
  count: number;
  rate: number;              // 对上一步的转化率
  color: string;
}

interface TopCard {
  plan_id: string;
  city: string;
  stay_seconds: number;
  cta_clicks: number;
  converted: boolean;
}

// ── Mock 数据（后端未接入时的展示数据）────────────────────────────────────
const MOCK_STATS: ConversionStats[] = [
  { period: "今日", preview_views: 42, pricing_clicks: 18, paid_orders: 7, revenue: 1736, conversion_rate: 16.7, click_rate: 42.9 },
  { period: "7天", preview_views: 214, pricing_clicks: 91, paid_orders: 38, revenue: 9424, conversion_rate: 17.8, click_rate: 42.5 },
  { period: "30天", preview_views: 856, pricing_clicks: 364, paid_orders: 157, revenue: 38936, conversion_rate: 18.3, click_rate: 42.5 },
];

const MOCK_FUNNEL: FunnelStep[] = [
  { label: "访问首页", count: 1200, rate: 100, color: "bg-stone-200" },
  { label: "完成问卷", count: 342, rate: 28.5, color: "bg-blue-200" },
  { label: "查看预览", count: 214, rate: 62.6, color: "bg-warm-200" },
  { label: "点击价格页", count: 91, rate: 42.5, color: "bg-amber-300" },
  { label: "完成付款", count: 38, rate: 41.8, color: "bg-green-400" },
];

const MOCK_TOP_CARDS: TopCard[] = [
  { plan_id: "abc123", city: "东京", stay_seconds: 127, cta_clicks: 4, converted: true },
  { plan_id: "def456", city: "京都", stay_seconds: 89, cta_clicks: 2, converted: false },
  { plan_id: "ghi789", city: "大阪", stay_seconds: 203, cta_clicks: 7, converted: true },
  { plan_id: "jkl012", city: "东京", stay_seconds: 34, cta_clicks: 1, converted: false },
  { plan_id: "mno345", city: "北海道", stay_seconds: 156, cta_clicks: 5, converted: true },
];

// ── 组件 ─────────────────────────────────────────────────────────────────

function StatCard({ label, value, sub, color }: { label: string; value: string | number; sub?: string; color?: string }) {
  return (
    <div className="bg-white rounded-xl border border-stone-100 p-4 shadow-sm">
      <p className="text-xs text-stone-500 mb-1">{label}</p>
      <p className={`text-2xl font-bold font-mono ${color ?? "text-stone-900"}`}>{value}</p>
      {sub && <p className="text-xs text-stone-400 mt-1">{sub}</p>}
    </div>
  );
}

function FunnelChart({ steps }: { steps: FunnelStep[] }) {
  const max = steps[0]?.count ?? 1;
  return (
    <div className="space-y-3">
      {steps.map((step, i) => (
        <div key={step.label} className="flex items-center gap-3">
          <div className="w-24 text-xs text-stone-500 text-right flex-shrink-0">{step.label}</div>
          <div className="flex-1 bg-stone-100 rounded-full h-7 relative overflow-hidden">
            <div
              className={`${step.color} h-full rounded-full transition-all duration-700 flex items-center`}
              style={{ width: `${(step.count / max) * 100}%` }}
            >
              <span className="text-xs font-bold text-stone-700 px-2 truncate">{step.count.toLocaleString()}</span>
            </div>
          </div>
          <div className="w-16 text-xs text-right flex-shrink-0">
            {i > 0 ? (
              <span className={step.rate >= 30 ? "text-green-600 font-medium" : "text-stone-400"}>
                {step.rate.toFixed(1)}%
              </span>
            ) : <span className="text-stone-400">—</span>}
          </div>
        </div>
      ))}
    </div>
  );
}

function PeriodSelector({ periods, active, onChange }: { periods: ConversionStats[]; active: number; onChange: (i: number) => void }) {
  return (
    <div className="flex gap-1 bg-stone-100 rounded-lg p-1">
      {periods.map((p, i) => (
        <button
          key={p.period}
          onClick={() => onChange(i)}
          className={`flex-1 text-xs py-1.5 rounded-md font-medium transition-all ${
            active === i ? "bg-white shadow-sm text-stone-900" : "text-stone-500 hover:text-stone-700"
          }`}
        >
          {p.period}
        </button>
      ))}
    </div>
  );
}

// ── 主页面 ─────────────────────────────────────────────────────────────────

export default function ConversionDashboard() {
  const [stats] = useState<ConversionStats[]>(MOCK_STATS);
  const [funnel] = useState<FunnelStep[]>(MOCK_FUNNEL);
  const [topCards] = useState<TopCard[]>(MOCK_TOP_CARDS);
  const [activePeriod, setActivePeriod] = useState(0);
  const [loading, setLoading] = useState(false);

  const s = stats[activePeriod];

  // CTA 位置分析数据（模拟）
  const ctaBreakdown = [
    { label: "悬浮底栏（始终可见）", clicks: 41, conversion: 19.5 },
    { label: "预览天后 Inline CTA", clicks: 22, conversion: 22.7 },
    { label: "其他天 Teaser 卡片", clicks: 18, conversion: 16.7 },
    { label: "Header 小 Banner", clicks: 7, conversion: 28.6 },
    { label: "45秒停留弹层", clicks: 3, conversion: 33.3 },
  ];

  return (
    <div className="min-h-screen bg-stone-50 p-6">
      <div className="max-w-4xl mx-auto space-y-6">

        {/* Header */}
        <motion.div {...fadeInUp}>
          <h1 className="text-xl font-bold text-stone-900">预览成交看板</h1>
          <p className="text-sm text-stone-500">追踪免费预览 → 付费转化的完整漏斗</p>
        </motion.div>

        {/* 时间段选择器 */}
        <motion.div {...fadeInUp}>
          <PeriodSelector periods={stats} active={activePeriod} onChange={setActivePeriod} />
        </motion.div>

        {/* 核心指标 */}
        <motion.div {...fadeInUp} className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatCard
            label="预览页访问"
            value={s.preview_views.toLocaleString()}
            sub={`${activePeriod === 0 ? "今日" : activePeriod === 1 ? "近7天" : "近30天"}`}
          />
          <StatCard
            label="点击价格页"
            value={s.pricing_clicks.toLocaleString()}
            sub={`点击率 ${s.click_rate.toFixed(1)}%`}
            color="text-amber-600"
          />
          <StatCard
            label="付费订单"
            value={s.paid_orders.toLocaleString()}
            sub={`转化率 ${s.conversion_rate.toFixed(1)}%`}
            color="text-green-600"
          />
          <StatCard
            label="营收"
            value={`¥${s.revenue.toLocaleString()}`}
            sub={`均单 ¥${Math.round(s.revenue / Math.max(s.paid_orders, 1))}`}
            color="text-rose-600"
          />
        </motion.div>

        {/* 转化漏斗 */}
        <motion.div {...fadeInUp} className="bg-white rounded-2xl border border-stone-100 p-6">
          <h2 className="text-sm font-bold text-stone-900 mb-4">转化漏斗（近30天）</h2>
          <FunnelChart steps={funnel} />
        </motion.div>

        {/* CTA 位置效果分析 */}
        <motion.div {...fadeInUp} className="bg-white rounded-2xl border border-stone-100 p-6">
          <h2 className="text-sm font-bold text-stone-900 mb-4">CTA 位置效果分析</h2>
          <div className="space-y-3">
            {ctaBreakdown.map((cta) => (
              <div key={cta.label} className="flex items-center gap-3 text-sm">
                <div className="flex-1 text-stone-700">{cta.label}</div>
                <div className="text-stone-500 w-16 text-right font-mono">{cta.clicks} 次</div>
                <div className={`w-14 text-right font-medium ${cta.conversion >= 25 ? "text-green-600" : "text-stone-500"}`}>
                  {cta.conversion.toFixed(1)}%
                </div>
                <div className="w-20 bg-stone-100 rounded-full h-2">
                  <div
                    className={`${cta.conversion >= 25 ? "bg-green-400" : "bg-stone-300"} h-2 rounded-full`}
                    style={{ width: `${(cta.conversion / 35) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
          <p className="text-xs text-stone-400 mt-4">
            💡 Header Banner 和 45秒停留弹层转化率最高，建议优先优化这两个触点的文案
          </p>
        </motion.div>

        {/* 近期预览会话 */}
        <motion.div {...fadeInUp} className="bg-white rounded-2xl border border-stone-100 p-6">
          <h2 className="text-sm font-bold text-stone-900 mb-4">近期预览会话（实时）</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-stone-100 text-xs text-stone-500">
                  <th className="text-left pb-2 font-medium">方案 ID</th>
                  <th className="text-left pb-2 font-medium">城市</th>
                  <th className="text-right pb-2 font-medium">停留时长</th>
                  <th className="text-right pb-2 font-medium">CTA 点击</th>
                  <th className="text-right pb-2 font-medium">是否成交</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-50">
                {topCards.map((card) => (
                  <tr key={card.plan_id}>
                    <td className="py-2 font-mono text-xs text-stone-500">{card.plan_id}</td>
                    <td className="py-2">{card.city}</td>
                    <td className="py-2 text-right text-stone-600">
                      {card.stay_seconds >= 60
                        ? `${Math.floor(card.stay_seconds / 60)}m${card.stay_seconds % 60}s`
                        : `${card.stay_seconds}s`}
                    </td>
                    <td className="py-2 text-right">
                      <span className={`font-medium ${card.cta_clicks >= 3 ? "text-amber-600" : "text-stone-500"}`}>
                        {card.cta_clicks}
                      </span>
                    </td>
                    <td className="py-2 text-right">
                      {card.converted ? (
                        <span className="text-green-600 font-medium">✓ 已付款</span>
                      ) : (
                        <span className="text-stone-300">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>

        {/* 洞察卡 */}
        <motion.div {...fadeInUp} className="bg-gradient-to-r from-stone-900 to-stone-800 rounded-2xl p-6 text-white">
          <h2 className="text-sm font-bold mb-3">📊 关键洞察</h2>
          <ul className="space-y-2 text-sm text-stone-300">
            <li>• 停留时长 &gt;90秒 的用户付费转化率比 &lt;30秒 高 <span className="text-warm-300 font-bold">3.8×</span></li>
            <li>• 问卷完成率 28.5%，优化问卷流程可将付费用户数提升 40%+</li>
            <li>• 预览→价格页 转化率 42.5%，高于行业均值（约 25%），说明 Day1 内容质量有效</li>
            <li>• 京都方案停留时间最长（均 112s），建议优先完善京都模板</li>
          </ul>
        </motion.div>

      </div>
    </div>
  );
}
