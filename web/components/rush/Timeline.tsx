"use client";

import { useState } from "react";
import Image from "next/image";
import { cn } from "@/lib/utils";
import type { RushSpot, RushCity } from "@/lib/rush-data";

// ── BloomBar ────────────────────────────────────────────────────────────────

function BloomBar({ half, full, fall, className }: {
  half?: string; full?: string; fall?: string; className?: string;
}) {
  const pct = (s?: string) => {
    if (!s) return 0;
    const m = s.match(/(\d+)月(\d+)日/);
    if (!m) return 0;
    const d = new Date(2026, parseInt(m[1]) - 1, parseInt(m[2]));
    const start = new Date("2026-03-10").getTime();
    const range = (new Date("2026-04-25").getTime() - start) / 864e5;
    return Math.max(0, Math.min(100, ((d.getTime() - start) / 864e5) / range * 100));
  };
  const todayP = (() => {
    const now = new Date();
    const start = new Date("2026-03-10").getTime();
    const range = (new Date("2026-04-25").getTime() - start) / 864e5;
    return Math.max(0, Math.min(100, ((now.getTime() - start) / 864e5) / range * 100));
  })();

  return (
    <div className={cn("relative h-2 bg-stone-100 rounded-full", className)}>
      {half && <div className="absolute h-full rounded-full bg-gradient-to-r from-pink-200 to-pink-300" style={{ left: `${pct(half)}%`, width: `${Math.max(1, pct(full || half) - pct(half))}%` }} />}
      {full && <div className="absolute h-full rounded-full bg-gradient-to-r from-pink-500 to-pink-700" style={{ left: `${pct(full)}%`, width: `${Math.max(1, pct(fall || full) - pct(full))}%` }} />}
      {fall && <div className="absolute h-full rounded-full bg-gradient-to-r from-purple-300 to-purple-500" style={{ left: `${pct(fall)}%`, width: `${Math.min(8, 100 - pct(fall))}%` }} />}
      <div className="absolute -top-0.5 w-0.5 h-3 bg-stone-800 rounded-sm" style={{ left: `${todayP}%` }} />
    </div>
  );
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function fmtD(s?: string) {
  if (!s) return "?";
  return s.replace("月", "/").replace("日", "");
}

function daysTo(s?: string): number | null {
  if (!s) return null;
  const m = s.match(/(\d+)月(\d+)日/);
  if (!m) return null;
  const d = new Date(2026, parseInt(m[1]) - 1, parseInt(m[2]));
  const now = new Date(); now.setHours(0, 0, 0, 0);
  return Math.round((d.getTime() - now.getTime()) / 864e5);
}

function daysToStr(days: number | null): { text: string; className: string } {
  if (days === null) return { text: "", className: "text-stone-400" };
  if (days > 0) return { text: `${days}天后`, className: "text-pink-600 font-semibold" };
  if (days === 0) return { text: "🎉 今天!", className: "text-pink-600 font-bold" };
  return { text: `已过${Math.abs(days)}天`, className: "text-purple-600" };
}

// ── Group by region ─────────────────────────────────────────────────────────

function groupByRegion(spots: RushSpot[]): Array<{ region: string; spots: RushSpot[] }> {
  const map = new Map<string, RushSpot[]>();
  for (const s of spots) {
    const r = s.region || "其他";
    if (!map.has(r)) map.set(r, []);
    map.get(r)!.push(s);
  }
  return Array.from(map.entries()).map(([region, spots]) => ({ region, spots }));
}

// ── Spot Card ───────────────────────────────────────────────────────────────

function SpotCard({ spot, onMapClick }: { spot: RushSpot; onMapClick?: (spot: RushSpot) => void }) {
  const dn = daysTo(spot.full);
  const countdown = daysToStr(dn);
  const desc = (spot.desc_cn || spot.desc || "").slice(0, 80) + ((spot.desc_cn || spot.desc || "").length > 80 ? "..." : "");

  return (
    <div
      className="bg-white rounded-xl border border-stone-100 overflow-hidden hover:border-pink-200 hover:shadow-sm transition-all cursor-pointer"
      onClick={() => onMapClick?.(spot)}
    >
      {/* Top: photo + info */}
      <div className="flex gap-3 p-3">
        {/* Photo */}
        {spot.photo ? (
          <div className="relative w-20 h-20 md:w-24 md:h-24 rounded-lg overflow-hidden shrink-0">
            <Image src={spot.photo} alt={spot.name} fill className="object-cover" unoptimized />
          </div>
        ) : (
          <div className="w-20 h-20 md:w-24 md:h-24 rounded-lg bg-gradient-to-br from-pink-100 to-pink-200 flex items-center justify-center text-2xl shrink-0">🌸</div>
        )}

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-bold text-stone-900 truncate">{spot.name}</h4>
            <span className="text-base font-black text-pink-600 shrink-0">{spot.score}</span>
          </div>

          <div className="flex items-center gap-2 mt-1 text-xs text-stone-500">
            <span>满开 <b className="text-stone-700">{fmtD(spot.full)}</b></span>
            {dn !== null && <span className={countdown.className}>{countdown.text}</span>}
          </div>

          {/* Tags */}
          <div className="flex flex-wrap gap-1 mt-1.5">
            {spot.meisyo100 && <span className="text-[8px] px-1.5 py-0.5 rounded bg-orange-50 text-orange-700 font-medium">🏆 百选</span>}
            {spot.lightup && <span className="text-[8px] px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 font-medium">🌙 夜樱</span>}
            {spot.trees && <span className="text-[8px] px-1.5 py-0.5 rounded bg-green-50 text-green-700 font-medium">🌳 {spot.trees}</span>}
            {spot.namiki && <span className="text-[8px] px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 font-medium">🌸 樱花道</span>}
          </div>

          {/* Date dots */}
          <div className="flex gap-3 mt-1.5 text-[10px]">
            {spot.half && <span className="text-stone-500"><span className="inline-block w-1.5 h-1.5 rounded-full bg-pink-300 mr-0.5" />半开 {fmtD(spot.half)}</span>}
            {spot.full && <span className="text-pink-700 font-semibold"><span className="inline-block w-1.5 h-1.5 rounded-full bg-pink-600 mr-0.5" />满开 {fmtD(spot.full)}</span>}
            {spot.fall && <span className="text-stone-500"><span className="inline-block w-1.5 h-1.5 rounded-full bg-purple-500 mr-0.5" />飘落 {fmtD(spot.fall)}</span>}
          </div>
        </div>
      </div>

      {/* Bottom: bloom bar + desc */}
      <div className="px-3 pb-3 space-y-2">
        <BloomBar half={spot.half} full={spot.full} fall={spot.fall} />
        {desc && <p className="text-[11px] text-stone-500 leading-relaxed">{desc}</p>}
      </div>
    </div>
  );
}

// ── Main Export ──────────────────────────────────────────────────────────────

export interface TimelineProps {
  cities: RushCity[];
  initialCity?: number;
  onSpotClick?: (cityKey: string, spotId: string) => void;
}

export default function Timeline({ cities, initialCity = 0, onSpotClick }: TimelineProps) {
  const [cityIdx, setCityIdx] = useState(initialCity);
  const city = cities[cityIdx];
  const regions = groupByRegion(city.spots);

  return (
    <div className="space-y-4">
      {/* City tabs */}
      <div className="flex items-center gap-1 overflow-x-auto pb-1">
        {cities.map((c, i) => (
          <button
            key={c.key}
            onClick={() => setCityIdx(i)}
            className={cn(
              "px-3 py-1.5 text-xs font-semibold rounded-lg whitespace-nowrap transition-colors",
              i === cityIdx ? "text-white bg-pink-500" : "text-stone-500 bg-stone-100 hover:bg-stone-200"
            )}
          >
            {c.emoji} {c.name} ({c.spotCount})
          </button>
        ))}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 text-[10px] text-stone-500">
        <span className="flex items-center gap-1"><span className="w-4 h-1.5 rounded-full bg-gradient-to-r from-pink-200 to-pink-300" />开花~半开</span>
        <span className="flex items-center gap-1"><span className="w-4 h-1.5 rounded-full bg-gradient-to-r from-pink-500 to-pink-700" />满开(最佳)</span>
        <span className="flex items-center gap-1"><span className="w-4 h-1.5 rounded-full bg-gradient-to-r from-purple-300 to-purple-500" />飘落</span>
        <span className="flex items-center gap-1"><span className="w-0.5 h-2 bg-stone-800 rounded-sm" />今天</span>
      </div>

      {/* Regions */}
      {regions.map(({ region, spots }) => (
        <div key={region}>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm font-bold text-stone-800">📍 {region}</span>
            <span className="text-[10px] text-stone-400">{spots.length}个景点</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {spots.map((s) => (
              <SpotCard
                key={s.id}
                spot={s}
                onMapClick={() => onSpotClick?.(city.key, s.id)}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
