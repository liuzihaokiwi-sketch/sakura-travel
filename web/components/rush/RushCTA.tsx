"use client";

/**
 * RushCTA.tsx — M2: 定制服务 CTA Section
 * 包含: 痛点 + 流程 + 微信复制按钮 + 信任标签
 * CTA 按钮跳转到 /quiz
 * Client Component（微信复制需要 navigator.clipboard）
 */

import { useState } from "react";
import Link from "next/link";

// ── 痛点数据 ─────────────────────────────────────────────────────────────

const PAIN_CARDS = [
  {
    icon: "🇯🇵",
    title: "旅居验证 · 不踩坑",
    pain: "AI推荐的餐厅已倒闭、景点在维修、交通是错的",
    sol: <>我们<b className="text-orange-500">实际住在日本</b>，每条路线亲自走过。餐厅是否还开、景点有无在修——<b className="text-orange-500">实地确认才推荐</b>。</>,
  },
  {
    icon: "✨",
    title: "拒绝审美疲劳",
    pain: "10个人搜出一模一样的行程，去了全是人头",
    sol: <><b className="text-orange-500">隐藏樱花路 + 限定夜樱 + 屋台小吃</b>，让你的行程跟别人不一样。<b className="text-orange-500">朋友圈绝对不撞款</b>。</>,
  },
  {
    icon: "🍣",
    title: "详细菜单 · 真实评价",
    pain: "只推荐名字没有评价，不知道点啥、要不要预约",
    sol: <>每家餐厅附<b className="text-orange-500">真实体验、招牌菜、人均</b>。<b className="text-orange-500">Tabelog 3.5+ 才入选</b>，含隐藏居酒屋。</>,
  },
  {
    icon: "🌸",
    title: "240 景点 · 实时花期",
    pain: `去了才发现"开花了" ≠ 好看，白跑一趟浪费钱`,
    sol: <><b className="text-orange-500">6大数据源 + 3次/天更新</b>，精确到每个景点的最佳窗口。<b className="text-orange-500">不让你浪费一分钱一分钟</b>。</>,
  },
  {
    icon: "📸",
    title: "保证出片效果",
    pain: "热门景点拍的和别人一样，朋友圈没人点赞",
    sol: <><b className="text-orange-500">最佳拍摄时段 + 小众机位 + 错峰路线</b>。告诉你几点去人最少、哪个角度最美。</>,
  },
  {
    icon: "💰",
    title: "全方位省钱避坑",
    pain: "樱花季溢价严重，机票酒店交通都被坑",
    sol: <><b className="text-orange-500">20+ 渠道比价省 30-50%</b>。机票含里程票/转机组合，交通 Pass <b className="text-orange-500">自动计算最省方案</b>。</>,
  },
];

// ── 流程步骤 ─────────────────────────────────────────────────────────────

const FLOW_STEPS = [
  { n: "1", t: "加微信" },
  { n: "2", t: "告知日期" },
  { n: "3", t: "免费1天攻略" },
  { n: "4", t: "满意再付费" },
];

const WECHAT_ID = "Kiwi_iloveu_O-o";

// ── Main Component ────────────────────────────────────────────────────────

export default function RushCTA() {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(WECHAT_ID).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  }

  return (
    <div className="w-full bg-white border-t border-gray-100">

      {/* ── CTA Hero ─────────────────────────────────────────────────── */}
      <div className="relative bg-gradient-to-br from-gray-900 via-[#2d1a22] to-[#3d1428] px-5 py-8 sm:px-10 overflow-hidden">
        <span className="pointer-events-none absolute right-4 top-3 text-2xl opacity-15 tracking-widest select-none">✈️ 🏨 🍣 🌸</span>
        <div className="relative z-10 max-w-4xl mx-auto">
          <span className="inline-block text-[10px] font-bold tracking-widest text-pink-300 border border-pink-300/25 px-3 py-1 rounded mb-3">
            🎁 免费体验
          </span>
          <h2 className="text-xl sm:text-3xl font-black text-white leading-tight mb-1">
            为什么不直接用 AI 生成？<br />
            <span className="text-pink-300">因为我们做的更好</span>
          </h2>
          <p className="text-xs text-white/35">每条路线人工验证 · 旅居团队 · 满意再付费</p>
        </div>
      </div>

      {/* ── 痛点卡片网格 ─────────────────────────────────────────────── */}
      <div className="px-4 sm:px-6 py-5 max-w-4xl mx-auto">
        <p className="text-[11px] text-gray-400 mb-3 text-center">每一个痛点，我们都有对应的解决方案</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {PAIN_CARDS.map((c) => (
            <div
              key={c.title}
              className="flex flex-col p-4 border border-gray-100 rounded-xl hover:border-pink-200 hover:shadow-sm transition-all"
            >
              <span className="text-2xl mb-2">{c.icon}</span>
              <div className="text-sm font-black text-gray-900 mb-1">{c.title}</div>
              <div className="text-[11px] text-red-600 font-semibold mb-2 px-2 py-1.5 bg-red-50 rounded border-l-2 border-red-400 leading-snug">
                ❌ {c.pain}
              </div>
              <div className="text-xs text-gray-500 leading-relaxed flex-1">{c.sol}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── 流程 + 微信 ─────────────────────────────────────────────── */}
      <div className="px-4 sm:px-6 pb-6 max-w-4xl mx-auto">
        <div className="flex flex-col sm:flex-row gap-4">

          {/* 流程步骤 */}
          <div className="flex-1 bg-gray-50 rounded-2xl p-5">
            <div className="text-xs font-bold text-gray-400 mb-3">📋 怎么开始</div>
            <div className="flex flex-wrap items-center gap-2">
              {FLOW_STEPS.map((s, i) => (
                <>
                  <div key={s.n} className="flex items-center gap-1.5 text-sm text-gray-700">
                    <span className="w-6 h-6 rounded-full bg-gradient-to-br from-orange-400 to-amber-400 text-white text-[11px] font-black flex items-center justify-center">
                      {s.n}
                    </span>
                    {s.t}
                  </div>
                  {i < FLOW_STEPS.length - 1 && (
                    <span key={`arrow-${i}`} className="text-gray-300 text-lg">→</span>
                  )}
                </>
              ))}
            </div>

            {/* 信任标签 */}
            <div className="flex flex-wrap gap-2 mt-4">
              {["✅ 不满意不收费", "🤝 满意再付费", "🇯🇵 旅居团队", "🔍 人工验证"].map((t) => (
                <span key={t} className="text-[10px] text-gray-500 bg-white border border-gray-200 px-2 py-1 rounded-full">{t}</span>
              ))}
            </div>
          </div>

          {/* 微信区 + CTA */}
          <div className="sm:w-64 flex flex-col gap-3">
            {/* 微信卡 */}
            <div className="bg-gradient-to-br from-gray-900 to-[#2d1a22] rounded-2xl p-5 text-white">
              <div className="text-[10px] text-white/30 mb-1">加微信 · 备注「樱花」</div>
              <div className="flex items-center justify-between mt-1">
                <span className="text-lg font-black text-amber-400 select-all">{WECHAT_ID}</span>
                <button
                  onClick={handleCopy}
                  className="bg-gradient-to-r from-orange-500 to-amber-400 text-white text-[11px] font-bold px-3 py-1.5 rounded-lg transition-transform active:scale-95"
                >
                  {copied ? "✅ 已复制!" : "📋 复制微信号"}
                </button>
              </div>
            </div>

            {/* 前往问卷 */}
            <Link
              href="/quiz"
              className="flex items-center justify-center gap-2 py-3.5 rounded-2xl bg-gradient-to-r from-rose-500 to-pink-500 text-white font-bold text-sm hover:opacity-90 transition-opacity active:scale-95"
            >
              🌸 免费定制行程 →
            </Link>
            <p className="text-center text-[10px] text-gray-400">填写问卷 · 2分钟 · 不收取任何费用</p>
          </div>
        </div>
      </div>
    </div>
  );
}
