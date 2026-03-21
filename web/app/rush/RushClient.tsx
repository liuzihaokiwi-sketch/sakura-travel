"use client";

import { useState, useCallback } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import Image from "next/image";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import type { RushData, RushCity, RushSpot } from "@/lib/rush-data";

// Lazy-load heavy components
const SakuraMap = dynamic(() => import("@/components/rush/SakuraMap"), { ssr: false, loading: () => <div className="h-[700px] bg-stone-100 animate-pulse rounded-xl" /> });
const Timeline = dynamic(() => import("@/components/rush/Timeline"), { loading: () => <div className="h-96 bg-stone-50 animate-pulse rounded-xl" /> });

// ── Tab types ───────────────────────────────────────────────────────────────

type TabKey = "home" | "map" | "timeline";

const TABS: { key: TabKey; label: string; icon: string }[] = [
  { key: "home", label: "首页", icon: "🏠" },
  // { key: "map", label: "地图", icon: "🗺️" },  // 暂时隐藏
  { key: "timeline", label: "时间轴", icon: "📅" },
];

// ── Helpers ─────────────────────────────────────────────────────────────────

function fmtD(s?: string) {
  if (!s) return "?";
  return s.replace("月", "/").replace("日", "");
}

function bloomStatus(s: RushSpot): { label: string; emoji: string; cls: string; bgCls: string } {
  const now = new Date(); now.setHours(0, 0, 0, 0);
  const toD = (str?: string) => {
    if (!str) return null;
    const m = str.match(/(\d+)月(\d+)日/);
    return m ? new Date(2026, parseInt(m[1]) - 1, parseInt(m[2])) : null;
  };
  const halfD = toD(s.half), fullD = toD(s.full), fallD = toD(s.fall);
  if (fallD && now > fallD) return { label: "飘落中", emoji: "🍂", cls: "text-purple-700", bgCls: "bg-purple-50 border-purple-200" };
  if (fullD && now >= fullD) return { label: "满开中", emoji: "🌸", cls: "text-pink-700", bgCls: "bg-pink-50 border-pink-200" };
  if (halfD && now >= halfD) return { label: "开花中", emoji: "🌱", cls: "text-pink-600", bgCls: "bg-pink-50 border-pink-100" };
  if (fullD) {
    const days = Math.ceil((fullD.getTime() - now.getTime()) / 864e5);
    if (days <= 3) return { label: `${days}天后满开`, emoji: "⏰", cls: "text-orange-600", bgCls: "bg-orange-50 border-orange-200" };
    if (days <= 7) return { label: `${days}天后满开`, emoji: "🌤️", cls: "text-amber-600", bgCls: "bg-amber-50 border-amber-200" };
    return { label: `${days}天后满开`, emoji: "📅", cls: "text-stone-600", bgCls: "bg-stone-50 border-stone-200" };
  }
  return { label: "花苞期", emoji: "🌿", cls: "text-green-700", bgCls: "bg-green-50 border-green-200" };
}

// ── Hero Section ────────────────────────────────────────────────────────────

function HeroSection({ data }: { data: RushData }) {
  return (
    <div className="relative bg-gradient-to-br from-stone-900 via-stone-800 to-[#2d1a22] text-white px-6 py-10 md:px-10 md:py-14 overflow-hidden">
      <div className="absolute right-[-20px] top-[-20px] text-[160px] opacity-[0.04] pointer-events-none select-none">🌸</div>
      <div className="relative z-10 max-w-4xl mx-auto">
        <span className="inline-block text-[10px] font-semibold text-pink-300 border border-pink-300/30 px-2.5 py-1 rounded tracking-widest uppercase mb-3">
          SAKURA RUSH 2026
        </span>
        <h2 className="text-2xl md:text-3xl font-black leading-tight mb-1">
          日本樱花 <em className="not-italic text-pink-300">实时花期</em>
        </h2>
        <p className="text-xs text-white/40 mt-1">数据每天更新 · {data.weekLabel}</p>
        <div className="grid grid-cols-4 gap-3 mt-5 max-w-sm">
          {[
            { val: `${data.totalSpots}+`, label: "追踪景点" },
            { val: "6", label: "数据源" },
            { val: "3次/天", label: "更新频率" },
            { val: "±2天", label: "预测精度" },
          ].map((item) => (
            <div key={item.label} className="text-center bg-white/5 rounded-lg py-2">
              <div className="text-lg md:text-xl font-black text-pink-300">{item.val}</div>
              <div className="text-[9px] text-white/40 mt-0.5">{item.label}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Spot Card (shared between Hot / City) ───────────────────────────────────

function SpotCard({ spot, cityName, cityEmoji, onClick }: {
  spot: RushSpot; cityName: string; cityEmoji: string; onClick?: () => void;
}) {
  const status = bloomStatus(spot);
  return (
    <div
      className="bg-white rounded-xl border border-stone-100 overflow-hidden hover:border-pink-200 hover:shadow-md transition-all cursor-pointer"
      onClick={onClick}
    >
      {/* Photo top */}
      <div className="relative">
        {spot.photo ? (
          <div className="relative w-full h-36 md:h-40">
            <Image src={spot.photo} alt={spot.name} fill className="object-cover" unoptimized />
          </div>
        ) : (
          <div className="w-full h-28 bg-gradient-to-br from-pink-100 to-pink-200 flex items-center justify-center text-4xl">🌸</div>
        )}
        {/* Bloom badge overlay */}
        <div className={cn("absolute top-2 left-2 px-2 py-1 rounded-lg text-xs font-bold border backdrop-blur-sm", status.bgCls, status.cls)}>
          {status.emoji} {status.label}
        </div>
      </div>

      {/* Info */}
      <div className="p-3 space-y-2">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <h4 className="text-sm font-bold text-stone-900 leading-tight">{spot.name}</h4>
            <p className="text-[11px] text-stone-500 mt-0.5">{cityEmoji} {cityName} · 满开 {fmtD(spot.full)}</p>
          </div>
          {/* Score — prominent with clear label */}
          <div className="shrink-0 text-center bg-pink-50 rounded-lg px-2.5 py-1.5 border border-pink-100">
            <div className="text-xl font-black text-pink-600 leading-none">{spot.score}</div>
            <div className="text-[8px] text-pink-400 font-bold mt-0.5">好看指数</div>
          </div>
        </div>

        {/* Tags */}
        <div className="flex flex-wrap gap-1">
          {spot.meisyo100 && <span className="text-[9px] px-1.5 py-0.5 rounded-md bg-orange-50 text-orange-700 font-semibold border border-orange-100">🏆 百选名所</span>}
          {spot.lightup && <span className="text-[9px] px-1.5 py-0.5 rounded-md bg-purple-50 text-purple-700 font-semibold border border-purple-100">🌙 夜樱</span>}
          {spot.trees && <span className="text-[9px] px-1.5 py-0.5 rounded-md bg-green-50 text-green-700 font-semibold border border-green-100">🌳 {spot.trees}</span>}
        </div>
      </div>
    </div>
  );
}

// ── Hot Spots Section (card grid, no 1/2/3) ─────────────────────────────────

function HotSpots({ cities, onViewMap }: { cities: RushCity[]; onViewMap: (cityIdx: number) => void }) {
  return (
    <div className="px-4 md:px-6 py-6">
      <div className="flex items-center gap-2 mb-4">
        <h3 className="text-lg font-extrabold text-stone-900">🔥 本周最值得冲的景点</h3>
        <span className="text-xs text-pink-600 font-semibold ml-auto cursor-pointer" onClick={() => onViewMap(0)}>查看全部 →</span>
      </div>

      {/* Score meaning callout */}
      <div className="flex items-center gap-2 mb-4 px-3 py-2 bg-amber-50 border border-amber-100 rounded-lg">
        <span className="text-base">💡</span>
        <p className="text-xs text-amber-800"><b>好看指数</b>（0-100）= 满开时这个景点有多好看，综合规模、名气、夜樱等评分。<b>花期状态</b>是指现在是否开花。</p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
        {cities.map((city) =>
          city.spots.slice(0, 3).map((s, i) => (
            <SpotCard
              key={`${city.key}-${i}`}
              spot={s}
              cityName={city.name}
              cityEmoji={city.emoji}
              onClick={() => onViewMap(cities.indexOf(city))}
            />
          ))
        )}
      </div>
    </div>
  );
}

// ── City Overview Cards ─────────────────────────────────────────────────────

function CityOverview({ cities, onViewMap }: { cities: RushCity[]; onViewMap: (idx: number) => void }) {
  return (
    <div className="px-4 md:px-6 py-6">
      <h3 className="text-lg font-extrabold text-stone-900 mb-4">🏙️ 城市概览</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {cities.map((city, ci) => {
          const bloomPercent = city.spotCount > 0 ? Math.round((city.bloomCount / city.spotCount) * 100) : 0;
          return (
            <div
              key={city.key}
              className="bg-white border border-stone-100 rounded-xl overflow-hidden hover:border-pink-200 hover:shadow-md transition-all cursor-pointer"
              onClick={() => onViewMap(ci)}
            >
              {/* Header */}
              <div className="flex items-center gap-3 px-4 py-3 bg-gradient-to-r from-stone-50 to-white border-b border-stone-100">
                <span className="text-2xl">{city.emoji}</span>
                <div className="flex-1">
                  <div className="text-base font-extrabold text-stone-900">{city.name}</div>
                  <div className="text-xs text-stone-500">{city.spotCount} 个樱花景点</div>
                </div>
                <div className={cn(
                  "text-xs font-bold text-white px-2.5 py-1 rounded-lg",
                  city.status.includes("已") ? "bg-pink-500" : "bg-amber-500"
                )}>
                  {city.status}
                </div>
              </div>

              {/* Top 3 photos */}
              <div className="flex gap-1 p-2">
                {city.spots.slice(0, 3).map((s, i) => (
                  <div key={i} className="flex-1">
                    {s.photo ? (
                      <div className="relative w-full h-20 rounded-lg overflow-hidden">
                        <Image src={s.photo} alt={s.name} fill className="object-cover" unoptimized />
                      </div>
                    ) : (
                      <div className="w-full h-20 rounded-lg bg-gradient-to-br from-pink-100 to-pink-200 flex items-center justify-center text-xl">🌸</div>
                    )}
                    <div className="text-[10px] font-bold text-stone-700 mt-1 truncate text-center">{s.name}</div>
                  </div>
                ))}
              </div>

              {/* Stats bar */}
              <div className="flex items-center gap-2 px-3 pb-3">
                <div className="flex-1 bg-stone-100 rounded-full h-2 overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-pink-400 to-pink-600 rounded-full transition-all" style={{ width: `${bloomPercent}%` }} />
                </div>
                <span className="text-xs font-bold text-pink-600 shrink-0">{bloomPercent}% 已开花</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Source Bar ───────────────────────────────────────────────────────────────

function SourceBar() {
  const sources = ["JMA 气象厅", "JMC 气象协会", "Weathernews", "Walker+", "地方观光协会", "AI融合引擎"];
  return (
    <div className="px-4 md:px-6 py-4 bg-stone-50 border-t border-stone-100">
      <div className="text-xs font-bold text-stone-400 mb-2">数据来源</div>
      <div className="flex flex-wrap gap-1.5">
        {sources.map((s) => (
          <span key={s} className="text-[10px] px-2 py-1 rounded-md bg-white border border-stone-100 text-stone-600 font-medium">{s}</span>
        ))}
      </div>
    </div>
  );
}

// ── CTA Section ─────────────────────────────────────────────────────────────

function CtaSection() {
  return (
    <div className="px-4 md:px-6 py-10 text-center bg-gradient-to-b from-pink-50 to-white border-t border-stone-100">
      <h3 className="text-xl font-extrabold text-stone-900 mb-2">看完花期，定制你的专属行程</h3>
      <p className="text-sm text-stone-500 mb-5">30-40页完整手册 · 精确到每一天每一餐 · 拿到就能出发</p>
      <div className="relative inline-block group">
        <div className="absolute -inset-1 bg-gradient-to-r from-amber-400 via-pink-400 to-amber-400 rounded-2xl blur-md opacity-30 group-hover:opacity-50 transition-opacity animate-pulse" />
        <Link href="/">
          <Button variant="warm" size="lg" className="relative font-bold shadow-lg">先免费看一天 →</Button>
        </Link>
      </div>
    </div>
  );
}

// ── Main RushClient ─────────────────────────────────────────────────────────

export default function RushClient({ data }: { data: RushData }) {
  const [tab, setTab] = useState<TabKey>("home");
  const [mapInitCity, setMapInitCity] = useState(0);

  const goToMap = useCallback((cityIdx: number) => {
    setMapInitCity(cityIdx);
    setTab("map");
  }, []);

  return (
    <div className="min-h-screen bg-[#fdfaf7]">
      {/* Sub-nav (rush internal tabs) — 更醒目 */}
      <div className="sticky top-14 z-40 bg-white/95 backdrop-blur-sm border-b border-stone-200 shadow-sm">
        <div className="max-w-7xl mx-auto flex items-center px-4">
          <div className="flex items-center gap-1 py-1.5">
            {TABS.map((t) => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={cn(
                  "px-4 py-2 text-sm font-bold rounded-lg transition-all",
                  tab === t.key
                    ? "text-white bg-pink-500 shadow-md shadow-pink-200"
                    : "text-stone-600 hover:text-pink-600 hover:bg-pink-50 border border-transparent hover:border-pink-100"
                )}
              >
                {t.icon} {t.label}
              </button>
            ))}
          </div>
          <div className="ml-auto">
            <Link href="/" className="text-xs text-pink-600 font-bold hover:underline">
              定制行程 →
            </Link>
          </div>
        </div>
      </div>

      {/* 引流框 */}
      <div className="max-w-7xl mx-auto px-4 pt-2 pb-1">
        <Link href="/quiz" className="block">
          <div className="flex items-center justify-between bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-xl px-4 py-3 hover:shadow-md transition-shadow">
            <div>
              <p className="text-sm font-bold text-stone-800">想要一份专属于你的日本行程攻略</p>
              <p className="text-xs text-stone-500 mt-0.5">免费定制一天试试，满意再付费 →</p>
            </div>
            <span className="shrink-0 bg-gradient-to-r from-amber-400 to-orange-400 text-white text-xs font-bold px-3 py-1.5 rounded-full shadow-sm">
              免费试试
            </span>
          </div>
        </Link>
      </div>

      {/* Tab content */}
      {tab === "home" && (
        <div>
          <HeroSection data={data} />
          <HotSpots cities={data.cities} onViewMap={goToMap} />
          <CityOverview cities={data.cities} onViewMap={goToMap} />
          <SourceBar />
          <CtaSection />
        </div>
      )}

      {tab === "map" && (
        <div className="max-w-7xl mx-auto p-0 md:p-4">
          <SakuraMap cities={data.cities} landmarks={data.landmarks} initialCity={mapInitCity} />
        </div>
      )}

      {tab === "timeline" && (
        <div className="max-w-7xl mx-auto px-4 py-4">
          <Timeline cities={data.cities} onSpotClick={(cityKey) => {
            const idx = data.cities.findIndex((c) => c.key === cityKey);
            if (idx >= 0) goToMap(idx);
          }} />
        </div>
      )}
    </div>
  );
}