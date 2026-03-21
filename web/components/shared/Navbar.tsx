"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/", label: "首页" },
  { href: "/pricing", label: "方案与价格" },
];

export function Navbar() {
  const searchParams = useSearchParams();
  const isExport = searchParams.get("export") === "true";

  if (isExport) return null;

  return (
    <nav className="fixed top-0 inset-x-0 z-50 h-14 border-b border-white/10 bg-white/80 backdrop-blur-xl">
      <div className="mx-auto max-w-7xl h-full flex items-center justify-between px-4">
        {/* Logo — 主站品牌 */}
        <Link href="/" className="flex items-center gap-2">
          <span className="text-xl">✈️</span>
          <span className="font-display text-lg font-bold tracking-tight text-stone-900">
            日本旅行定制
          </span>
        </Link>

        {/* Nav links */}
        <div className="hidden sm:flex items-center gap-1">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "px-3 py-1.5 rounded-lg text-sm font-medium text-stone-600",
                "hover:text-stone-900 hover:bg-stone-100 transition-colors"
              )}
            >
              {item.label}
            </Link>
          ))}
          {/* 季节性入口 — 樱花季期间显示 */}
          <Link
            href="/rush"
            className="px-2.5 py-1 rounded-lg text-xs font-medium text-pink-600 bg-pink-50 hover:bg-pink-100 transition-colors"
          >
            🌸 樱花季
          </Link>
        </div>

        {/* CTA */}
        <Link href="/quiz">
          <Button variant="warm" size="sm">
            免费看看我的行程
          </Button>
        </Link>
      </div>
    </nav>
  );
}
