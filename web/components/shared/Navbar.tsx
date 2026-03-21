"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/", label: "首页" },
  { href: "/rush", label: "🌸 樱花季" },
];

export function Navbar() {
  const searchParams = useSearchParams();
  const isExport = searchParams.get("export") === "true";

  if (isExport) return null;

  return (
    <nav className="fixed top-0 inset-x-0 z-50 h-14 border-b border-white/10 bg-white/80 backdrop-blur-xl">
      <div className="mx-auto max-w-7xl h-full flex items-center justify-between px-4">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <span className="text-xl">🌸</span>
          <span className="font-display text-base font-bold tracking-tight text-stone-900">
            Sakura Plan
          </span>
        </Link>

        {/* Nav links */}
        <div className="flex items-center gap-2">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "px-4 py-1.5 rounded-full text-sm font-semibold transition-all duration-200",
                item.href === "/rush"
                  ? "bg-gradient-to-r from-pink-500 to-rose-400 text-white shadow-md shadow-pink-200/40 hover:shadow-lg hover:shadow-pink-200/50"
                  : "bg-stone-100 text-stone-700 hover:bg-stone-200"
              )}
            >
              {item.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}