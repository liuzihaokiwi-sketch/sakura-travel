"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { fadeInUp, staggerContainer, staggerContainerSlow } from "@/lib/animations";
import BloomTimeline from "@/components/rush/BloomTimeline";
import type { RushScores, CityData, Spot } from "@/lib/data";

// ── Weekly Rush Summary ─────────────────────────────────────────────────────

function WeeklyRush({ data }: { data: RushScores }) {
  const allSpots = data.cities.flatMap((c) => c.spots);
  const now = new Date();
  const fullBloomSpots = allSpots.filter((s) => {
    if (!s.full) return false;
    const [m, d] = s.full.split("/").map(Number);
    if (!m || !d) return false;
    const bloom = new Date(now.getFullYear(), m - 1, d);
    const diff = Math.abs(now.getTime() - bloom.getTime()) / (1000 * 60 * 60 * 24);
    return diff <= 7;
  });

  return (
    <motion.section
      variants={fadeInUp}
      initial="initial"
      animate="animate"
      className="bg-gradient-to-br from-sakura-50 to-warm-50 rounded-2xl border border-sakura-100 p-6 mb-8"
    >
      <div className="flex items-center gap-2 mb-3">
        <span className="text-2xl">🔥</span>
        <h2 className="font-display text-xl font-bold text-stone-900">
          本周冲
        </h2>
        <Badge variant="warm" className="ml-auto text-xs">
          {data.week_label}
        </Badge>
      </div>
      {fullBloomSpots.length > 0 ? (
        <p className="text-sm text-stone-600 leading-relaxed">
          本周 <strong className="text-sakura-500">{fullBloomSpots.length} 个景点</strong>接近满开，
          错过等明年！推荐优先冲：
          <span className="font-medium text-stone-800">
            {" "}
            {fullBloomSpots.slice(0, 5).map((s) => s.name).join("、")}
          </span>
        </p>
      ) : (
        <p className="text-sm text-stone-500">
          本周暂无满开景点，持续追踪中…关注花期时间轴了解最新进展 👇
        </p>
      )}
    </motion.section>
  );
}

// ── Spot Card ───────────────────────────────────────────────────────────────

function SpotCard({ spot, rank }: { spot: Spot; rank: number }) {
  const isFullBloom = (() => {
    if (!spot.full) return false;
    const now = new Date();
    const [m, d] = spot.full.split("/").map(Number);
    if (!m || !d) return false;
    const bloom = new Date(now.getFullYear(), m - 1, d);
    const diff = Math.abs(now.getTime() - bloom.getTime()) / (1000 * 60 * 60 * 24);
    return diff <= 5;
  })();

  return (
    <motion.div
      variants={fadeInUp}
      className={cn(
        "bg-white rounded-2xl border overflow-hidden transition-shadow hover:shadow-lg",
        isFullBloom
          ? "border-sakura-200 bg-gradient-to-br from-white to-sakura-50"
          : "border-stone-100"
      )}
    >
      {/* Photo placeholder */}
      <div className="relative h-40 bg-gradient-to-br from-stone-100 to-stone-200 flex items-center justify-center overflow-hidden">
        {spot.photo ? (
          <img
            src={spot.photo}
            alt={spot.name}
            className="w-full h-full object-cover"
            loading="lazy"
          />
        ) : (
          <span className="text-4xl opacity-40">🌸</span>
        )}
        {/* Rank badge */}
        <div className="absolute top-3 left-3 w-8 h-8 rounded-full bg-stone-900/70 text-white text-xs font-bold flex items-center justify-center">
          {rank}
        </div>
        {/* Status badges */}
        <div className="absolute top-3 right-3 flex gap-1.5">
          {isFullBloom && (
            <Badge className="bg-gradient-to-r from-sakura-400 to-pink-400 text-white border-0 text-[10px]">
              🌸 満開中
            </Badge>
          )}
          {spot.lightup && (
            <Badge className="bg-indigo-500/80 text-white border-0 text-[10px]">
              🌙 夜樱
            </Badge>
          )}
          {spot.meisyo100 && (
            <Badge className="bg-warm-400/80 text-white border-0 text-[10px]">
              🏅 名所百選
            </Badge>
          )}
        </div>
      </div>

      {/* Info */}
      <div className="p-4">
        <h3 className="font-bold text-stone-900 text-sm mb-1 line-clamp-1">
          {spot.name}
        </h3>
        {spot.desc_cn && (
          <p className="text-xs text-stone-500 mb-2 line-clamp-2">{spot.desc_cn}</p>
        )}

        {/* Bloom dates */}
        <div className="flex flex-wrap gap-x-3 gap-y-1 text-[10px] text-stone-400 mb-2">
          {spot.half && <span>🌱 五分: {spot.half}</span>}
          {spot.full && <span>🌸 満開: {spot.full}</span>}
          {spot.fall && <span>🍃 散り: {spot.fall}</span>}
        </div>

        {/* Bottom row */}
        <div className="flex items-center justify-between">
          <div className="flex gap-2 text-[10px] text-stone-400">
            {spot.trees && <span>🌳 {spot.trees}</span>}
            {spot.nightview && <span>🌃 夜景</span>}
          </div>
          <div className="flex items-center gap-1">
            <div className="h-1.5 w-12 rounded-full bg-stone-100 overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-warm-300 to-sakura-400"
                style={{ width: `${Math.min(spot.score, 100)}%` }}
              />
            </div>
            <span className="text-[10px] font-mono text-stone-400">{spot.score}</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

// ── City Tabs ───────────────────────────────────────────────────────────────

function CityTabs({
  cities,
  active,
  onChange,
}: {
  cities: CityData[];
  active: string;
  onChange: (code: string) => void;
}) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide mb-6">
      {cities.map((city) => (
        <button
          key={city.city_code}
          onClick={() => onChange(city.city_code)}
          className={cn(
            "px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all",
            active === city.city_code
              ? "bg-stone-900 text-white shadow-md"
              : "bg-white text-stone-600 border border-stone-200 hover:border-stone-300"
          )}
        >
          {city.city_name_cn}
          <span className="ml-1 text-xs opacity-60">({city.spots.length})</span>
        </button>
      ))}
    </div>
  );
}

// ── Main Client Component ───────────────────────────────────────────────────

export default function RushClient({ data }: { data: RushScores }) {
  const [activeCity, setActiveCity] = useState(
    data.cities[0]?.city_code || "tokyo"
  );

  const currentCity = data.cities.find((c) => c.city_code === activeCity);
  const spots = currentCity?.spots.sort((a, b) => b.score - a.score) || [];

  return (
    <div className="min-h-screen bg-warm-50">
      {/* Hero header */}
      <section className="bg-gradient-to-b from-stone-900 to-stone-800 text-white py-12 px-6 text-center">
        <motion.div variants={fadeInUp} initial="initial" animate="animate">
          <p className="text-xs tracking-[0.3em] text-white/40 font-mono mb-3">
            SAKURA RUSH 2026
          </p>
          <h1 className="font-display text-3xl md:text-4xl font-bold mb-2">
            🌸 樱花冲刺排行榜
          </h1>
          <p className="text-sm text-white/60 max-w-md mx-auto">
            实时追踪全日本 240+ 赏樱景点 · 4 大数据源融合 · 每天 3 次更新
          </p>
          <p className="text-xs text-white/30 mt-3 font-mono">
            最后更新：{data.updated_at}
          </p>
        </motion.div>
      </section>

      <div className="max-w-5xl mx-auto px-4 py-8">
        {/* Weekly Rush */}
        <WeeklyRush data={data} />

        {/* Bloom Timeline */}
        <div className="mb-8 bg-white rounded-2xl border border-stone-100 p-5">
          <BloomTimeline />
        </div>

        {/* City Tabs */}
        <CityTabs
          cities={data.cities}
          active={activeCity}
          onChange={setActiveCity}
        />

        {/* Spot Grid */}
        <AnimatePresence mode="wait">
          <motion.div
            key={activeCity}
            variants={staggerContainerSlow}
            initial="initial"
            animate="animate"
            exit={{ opacity: 0 }}
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
          >
            {spots.map((spot, i) => (
              <SpotCard key={spot.name} spot={spot} rank={i + 1} />
            ))}
          </motion.div>
        </AnimatePresence>

        {spots.length === 0 && (
          <div className="text-center py-16 text-stone-400">
            <span className="text-4xl block mb-3">🌱</span>
            <p className="text-sm">该城市暂无赏樱数据</p>
          </div>
        )}
      </div>
    </div>
  );
}
