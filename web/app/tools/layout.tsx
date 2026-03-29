import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: {
    default: "日本旅行工具箱",
    template: "%s · 日本旅行工具箱",
  },
  description: "实用的日本旅行免费工具：樱花/红叶预报、旅行预算计算器、行李清单、交通卡选择指南",
};

const TOOL_NAV = [
  { href: "/rush", label: "🌸 樱花追踪" },
  { href: "/tools/koyo", label: "🍁 红叶预报" },
  { href: "/tools/budget", label: "💰 预算计算" },
  { href: "/tools/packing", label: "🧳 行李清单" },
  { href: "/tools/transport-pass", label: "🚅 交通卡" },
];

export default function ToolsLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-stone-50 flex flex-col">
      {/* 工具页专属顶部导航（比全站 Navbar 更简洁） */}
      <header className="sticky top-14 z-40 bg-white/95 backdrop-blur-sm border-b border-stone-200 shadow-sm">
        <div className="max-w-5xl mx-auto px-4 overflow-x-auto">
          <nav className="flex items-center gap-1 py-1.5 min-w-max">
            {TOOL_NAV.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="px-3 py-1.5 text-xs font-semibold text-stone-600 hover:text-amber-700 hover:bg-amber-50 rounded-lg transition-colors whitespace-nowrap"
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>

      {/* 页面主体 — pb-20 为底部固定 CTA 留空间 */}
      <main className="flex-1 max-w-5xl mx-auto w-full px-4 py-6 pb-20">
        {children}
      </main>

      {/* 固定底部 CTA 引导栏 */}
      <div className="sticky bottom-0 z-50 bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg">
        <div className="max-w-5xl mx-auto px-4 py-2.5 flex items-center justify-between gap-3">
          <p className="text-xs font-semibold leading-tight">
            想要完整定制行程？<br className="sm:hidden" />
            <span className="opacity-80 text-[11px]">30-40页手册 · 精确到每餐每景点</span>
          </p>
          <Link
            href="/order"
            className="shrink-0 bg-white text-amber-600 text-xs font-bold px-4 py-2 rounded-full shadow hover:shadow-md transition-shadow whitespace-nowrap"
          >
            7天手账 ¥298 →
          </Link>
        </div>
      </div>
    </div>
  );
}
