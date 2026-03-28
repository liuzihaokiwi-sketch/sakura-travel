import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "日本旅行工具箱 — 免费实用工具",
  description: "樱花/红叶花期预报、旅行预算计算器、行李清单生成、交通卡选择……一站式日本旅行准备工具",
};

const TOOLS = [
  {
    href: "/tools/sakura",
    emoji: "🌸",
    title: "樱花花期追踪",
    desc: "240+景点实时花期 · 6大数据源 · 每天更新",
    badge: "🔥 季节热门",
    badgeColor: "bg-pink-100 text-pink-700",
    accent: "from-pink-50 to-rose-50 border-pink-100",
  },
  {
    href: "/tools/koyo",
    emoji: "🍁",
    title: "红叶见顷预报",
    desc: "全国主要赏枫地点预测 · 最佳时间一览",
    badge: "10-11月",
    badgeColor: "bg-orange-100 text-orange-700",
    accent: "from-orange-50 to-amber-50 border-orange-100",
  },
  {
    href: "/tools/budget",
    emoji: "💰",
    title: "旅行预算计算器",
    desc: "选目的地+天数+人数，自动计算每日花费",
    badge: "常青工具",
    badgeColor: "bg-emerald-100 text-emerald-700",
    accent: "from-emerald-50 to-teal-50 border-emerald-100",
  },
  {
    href: "/tools/packing",
    emoji: "🧳",
    title: "行李清单生成器",
    desc: "根据季节/行程自动生成可勾选清单",
    badge: "出发必备",
    badgeColor: "bg-sky-100 text-sky-700",
    accent: "from-sky-50 to-blue-50 border-sky-100",
  },
  {
    href: "/tools/transport-pass",
    emoji: "🚅",
    title: "交通卡选择器",
    desc: "告诉我你去哪，推荐最划算的 JR Pass/IC卡",
    badge: "省钱攻略",
    badgeColor: "bg-violet-100 text-violet-700",
    accent: "from-violet-50 to-purple-50 border-violet-100",
  },
];

export default function ToolsIndexPage() {
  return (
    <div>
      <div className="text-center mb-8">
        <h1 className="text-2xl font-black text-stone-900 mb-2">日本旅行工具箱</h1>
        <p className="text-sm text-stone-500">出发前把这几个工具用一遍，省时省钱不踩坑</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {TOOLS.map((tool) => (
          <Link
            key={tool.href}
            href={tool.href}
            className={`group block bg-gradient-to-br ${tool.accent} border rounded-2xl p-5 hover:shadow-md hover:-translate-y-0.5 transition-all duration-200`}
          >
            <div className="flex items-start justify-between mb-3">
              <span className="text-3xl">{tool.emoji}</span>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${tool.badgeColor}`}>
                {tool.badge}
              </span>
            </div>
            <h2 className="text-base font-bold text-stone-900 mb-1 group-hover:text-amber-700 transition-colors">
              {tool.title}
            </h2>
            <p className="text-xs text-stone-500 leading-relaxed">{tool.desc}</p>
            <div className="mt-3 text-xs font-semibold text-amber-600 group-hover:underline">
              立即使用 →
            </div>
          </Link>
        ))}
      </div>

      <div className="mt-10 text-center">
        <p className="text-xs text-stone-400">工具免费使用 · 需要完整定制行程请点击下方按钮</p>
      </div>
    </div>
  );
}
