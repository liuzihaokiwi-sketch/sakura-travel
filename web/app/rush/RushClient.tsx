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
  { key: "map", label: "地图", icon: "🗺️" },
  { key: "timeline", label: "时间轴", icon: "📅" },
];

// ── Helper ──────────────────────────────────────────────────────────────────

function fmtD(s?: string) {
  if (!s) return "?";
  return s.replace("月", "/").replace("日", "");
}

// ── Hero Section ────────────────────────────────────────────────────────────

function HeroSection({ data }: { data: RushData }) {
  return (
    <div className="relative bg-gradient-to-br from-stone-900 via-stone-800 to-[#2d1a22] text-white px-6 py-10 md:px-10 md:py-14 overflow-hidden">
      <div className="absolute right-[-20px] top-[-20px] text-[160px] opacity-[0.04] pointer-events-none select-none">🌸</div>

      <div className="relative z-10 max-w-4xl mx-auto">
        <span className="inline-block text-[9px] font-semibold text-pink-300 border border-pink-300/30 px-2.5 py-1 rounded tracking-widest uppercase mb-3">
          SAKURA RUSH 2026
        </span>
        <h2 className="text-2xl md:text-3xl font-black leading-tight mb-1">
          日本樱花 <em className="not-italic text-pink-300">实时花期</em>
        </h2>
        <p className="text-xs text-white/35">数据每天更新 · {data.weekLabel}</p>

        <div className="flex gap-6 mt-5">
          <div className="text-center">
            <div className="text-2xl font-black text-pink-300">{data.totalSpots}+</div>
            <div className="text-[8px] text-white/30">追踪景点</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-black text-pink-300">6</div>
            <div className="text-[8px] text-white/30">数据源</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-black text-pink-300">3次/天</div>
            <div className="text-[8px] text-white/30">更新频率</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-black text-pink-300">±2天</div>
            <div className="text-[8px] text-white/30">预测精度</div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Hot Spots Section ───────────────────────────────────────────────────────

function HotSpots({ cities, onViewMap }: { cities: RushCity[]; onViewMap: (cityIdx: number) => void }) {
  return (
    <div className="px-4 md:px-6 py-5">
      <div className="flex items-center gap-2 mb-3">
        <h3 className="text-base font-extrabold text-stone-900">🔥 本周推荐</h3>
        <span className="text-[10px] text-pink-600 font-semibold ml-auto cursor-pointer" onClick={() => onViewMap(0)}>查看全部 →</span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
        {cities.map((city) =>
          city.spots.slice(0, 3).map((s, i) => (
            <div key={`${city.key}-${i}`} className="flex gap-2 p-2.5 border border-stone-100 rounded-lg hover:border-pink-200 transition-colors cursor-pointer" onClick={() => onViewMap(cities.indexOf(city))}>
              <span className={cn(
                "w-6 h-6 rounded-md text-xs font-black flex items-center justify-center text-white shrink-0 mt-0.5",
                i === 0 ? "bg-stone-900" : i === 1 ? "bg-stone-500" : "bg-stone-300"
              )}>{i + 1}</span>
              {s.photo ? (
                <div className="relative w-14 h-14 rounded-lg overflow-hidden shrink-0">
                  <Image src={s.photo} alt={s.name} fill className="object-cover" unoptimized />
                </div>
              ) : (
                <div className="w-14 h-14 rounded-lg bg-gradient-to-br from-pink-100 to-pink-200 flex items-center justify-center text-lg shrink-0">🌸</div>
              )}
              <div className="flex-1 min-w-0">
                <div className="text-xs font-bold text-stone-900 truncate">{s.name}</div>
                <div className="text-[9px] text-stone-500 mt-0.5">{city.emoji} {city.name} · 满开 {fmtD(s.full)}</div>
                <div className="flex flex-wrap gap-0.5 mt-1">
                  {s.meisyo100 && <span className="text-[7px] px-1 py-0.5 rounded bg-orange-50 text-orange-600">🏆 百选</span>}
                  {s.lightup && <span className="text-[7px] px-1 py-0.5 rounded bg-purple-50 text-purple-600">🌙 夜樱</span>}
                </div>
              </div>
              <div className="text-right shrink-0">
                <div className={cn("text-[9px] font-bold", s.color === "#c2185b" || s.color === "#e91e63" ? "text-pink-600" : s.color === "#9c27b0" ? "text-purple-600" : "text-stone-400")}>
                  {s.color === "#c2185b" ? "满开中" : s.color === "#e91e63" ? "开花中" : s.color === "#9c27b0" ? "飘落中" : "即将开"}
                </div>
                <div className="text-base font-black text-pink-600">{s.score}</div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// ── City Overview Cards ─────────────────────────────────────────────────────

function CityOverview({ cities, onViewMap }: { cities: RushCity[]; onViewMap: (idx: number) => void }) {
  return (
    <div className="px-4 md:px-6 py-5">
      <h3 className="text-base font-extrabold text-stone-900 mb-3">🏙️ 城市概览</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {cities.map((city, ci) => (
          <div key={city.key} className="border border-stone-100 rounded-xl overflow-hidden hover:border-pink-200 transition-colors cursor-pointer" onClick={() => onViewMap(ci)}>
            <div className="flex items-center gap-2 px-3 py-2.5 bg-stone-50 border-b border-stone-100">
              <span className="text-xl">{city.emoji}</span>
              <span className="text-base font-extrabold text-stone-900">{city.name}</span>
              <span className={cn("text-[9px] font-bold text-white px-1.5 py-0.5 rounded", city.status.includes("已") ? "bg-green-600" : "bg-orange-600")}>{city.status}</span>
              <span className="text-[10px] text-stone-400 ml-auto">{city.spotCount}景点</span>
            </div>
            {/* Top 3 photos */}
            <div className="flex gap-1.5 p-2.5">
              {city.spots.slice(0, 3).map((s, i) => (
                <div key={i} className="flex-1 text-center">
                  {s.photo ? (
                    <div className="relative w-full h-16 rounded-md overflow-hidden">
                      <Image src={s.photo} alt={s.name} fill className="object-cover" unoptimized />
                    </div>
                  ) : (
                    <div className="w-full h-16 rounded-md bg-gradient-to-br from-pink-100 to-pink-200 flex items-center justify-center text-lg">🌸</div>
                  )}
                  <div className="text-[9px] font-bold text-stone-700 mt-1 truncate">{s.name}</div>
                  <div className="text-[8px] text-pink-600 font-semibold">{fmtD(s.full)}</div>
                </div>
              ))}
            </div>
            {/* Stats */}
            <div className="flex gap-2 px-2.5 pb-2.5">
              <div className="flex-1 text-center p-1 bg-stone-50 rounded-md">
                <div className="text-xs font-black text-stone-900">{city.spotCount}</div>
                <div className="text-[7px] text-stone-400">景点</div>
              </div>
              <div className="flex-1 text-center p-1 bg-stone-50 rounded-md">
                <div className="text-xs font-black text-stone-900">{city.bloomCount}</div>
                <div className="text-[7px] text-stone-400">已满开</div>
              </div>
              <div className="flex-1 text-center p-1 bg-stone-50 rounded-md">
                <div className="text-xs font-black text-pink-600">{city.avgScore}</div>
                <div className="text-[7px] text-stone-400">均分</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Source Bar ───────────────────────────────────────────────────────────────

function SourceBar() {
  const sources = ["JMA 气象厅", "JMC 气象协会", "Weathernews", "Walker+", "地方观光协会", "AI融合引擎"];
  return (
    <div className="px-4 md:px-6 py-4 bg-stone-50 border-t border-stone-100">
      <div className="text-[11px] font-bold text-stone-400 mb-2">数据来源</div>
      <div className="flex flex-wrap gap-1">
        {sources.map((s) => (
          <span key={s} className="text-[9px] px-2 py-1 rounded bg-white border border-stone-100 text-stone-600 font-medium">{s}</span>
        ))}
      </div>
    </div>
  );
}

// ── CTA Section ─────────────────────────────────────────────────────────────

function CtaSection() {
  return (
    <div className="px-4 md:px-6 py-8 text-center bg-gradient-to-b from-pink-50 to-white border-t border-stone-100">
      <h3 className="text-lg font-extrabold text-stone-900 mb-2">看完花期，定制你的专属行程</h3>
      <p className="text-sm text-stone-500 mb-4">AI 生成 · 精确到每一天每一餐 · 拿到就能出发</p>
      <Link href="/quiz">
        <Button variant="warm" size="lg">免费看看我的行程 →</Button>
      </Link>
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
    <div className="min-h-screen bg-[#fdfaf7] pt-14">
      {/* Sub-nav (rush internal tabs) */}
      <div className="sticky top-14 z-40 bg-white/90 backdrop-blur-sm border-b border-stone-200">
        <div className="max-w-7xl mx-auto flex items-center px-4">
          <div className="flex items-center gap-1 py-1.5">
            {TABS.map((t) => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={cn(
                  "px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors",
                  tab === t.key ? "text-pink-700 bg-pink-50" : "text-stone-500 hover:text-stone-700"
                )}
              >
                {t.icon} {t.label}
              </button>
            ))}
          </div>
          <div className="ml-auto">
            <Link href="/quiz" className="text-[10px] text-pink-600 font-semibold hover:underline">
              定制行程 →
            </Link>
          </div>
        </div>
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