"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/admin/dashboard", icon: "📊", label: "数据概览" },
  { href: "/admin", icon: "📋", label: "订单看板", exact: true },
  { href: "/admin/catalog", icon: "🏨", label: "内容库" },
  { href: "/admin/clusters", icon: "🗺️", label: "活动簇" },
  { href: "/admin/crawl", icon: "🔄", label: "数据抓取" },
  { href: "/admin/config", icon: "⚙️", label: "配置管理" },
  { href: "/admin/conversion", icon: "📈", label: "转化分析" },
  { href: "/admin/trace", icon: "🔍", label: "链路追踪" },
];

function AdminSidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-screen w-48 bg-white border-r border-slate-200 z-40 flex flex-col">
      <div className="px-4 py-4 border-b border-slate-100">
        <p className="text-xs font-bold text-slate-900 tracking-wide">Travel AI</p>
        <p className="text-xs text-slate-400">管理后台</p>
      </div>
      <nav className="flex-1 py-3 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const isActive = item.exact
            ? pathname === item.href
            : pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-2.5 px-4 py-2.5 text-sm transition-colors ${
                isActive
                  ? "bg-indigo-50 text-indigo-700 font-medium border-r-2 border-indigo-600"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              }`}
            >
              <span className="text-base leading-none">{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="px-4 py-3 border-t border-slate-100">
        <p className="text-xs text-slate-400">v0.1.0</p>
      </div>
    </aside>
  );
}

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-slate-50 !pt-0">
      {/* Override the main layout's pt-14 and hide sakura/navbar via CSS */}
      <style>{`
        body > .sakura-container,
        nav,
        body > div > nav,
        [data-floating-cta] {
          display: none !important;
        }
        main.relative {
          padding-top: 0 !important;
        }
      `}</style>
      <AdminSidebar />
      <div className="pl-48 min-h-screen">
        {children}
      </div>
    </div>
  );
}
