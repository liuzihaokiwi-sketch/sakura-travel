"use client";

/**
 * SakuraMap.tsx — 静态地图组件（纯 CSS，不依赖 Leaflet 瓦片）
 * 每个城市一张区域底图，景点用绝对定位圆点标注
 */

import { useState, useCallback } from "react";
import Image from "next/image";
import { cn } from "@/lib/utils";
import type { RushSpot, RushCity, Landmark } from "@/lib/rush-data";

// ── Helpers ──────────────────────────────────────────────────────────────────

function fmtD(s?: string) {
  if (!s) return "?";
  return s.replace("月", "/").replace("日", "");
}

function bloomStatus(s: RushSpot): { label: string; cls: string } {
  const now = new Date(); now.setHours(0, 0, 0, 0);
  const toD = (str?: string) => {
    if (!str) return null;
    const m = str.match(/(\d+)月(\d+)日/);
    return m ? new Date(2026, parseInt(m[1]) - 1, parseInt(m[2])) : null;
  };
  const halfD = toD(s.half), fullD = toD(s.full), fallD = toD(s.fall);
  if (fallD && now > fallD) return { label: "🍂 飘落中", cls: "text-purple-600" };
  if (fullD && now >= fullD) return { label: "🌸 满开中", cls: "text-pink-600 font-bold" };
  if (halfD && now >= halfD) return { label: "🌱 开花中", cls: "text-pink-500" };
  if (fullD) {
    const days = Math.ceil((fullD.getTime() - now.getTime()) / 864e5);
    if (days <= 3) return { label: `⏰ ${days}天后满开`, cls: "text-orange-500 font-semibold" };
    return { label: `${days}天后满开`, cls: "text-stone-500" };
  }
  return { label: "花苞", cls: "text-green-600" };
}

// ── 经纬度转百分比坐标 ─────────────────────────────────────────────────────

function getBounds(city: RushCity) {
  // zoom 越大区域越小
  const span = city.zoom >= 12 ? 0.15 : city.zoom >= 11 ? 0.25 : 0.4;
  return {
    latMin: city.center[0] - span,
    latMax: city.center[0] + span,
    lonMin: city.center[1] - span * 1.3,
    lonMax: city.center[1] + span * 1.3,
  };
}

function toPercent(lat: number, lon: number, bounds: ReturnType<typeof getBounds>) {
  const x = ((lon - bounds.lonMin) / (bounds.lonMax - bounds.lonMin)) * 100;
  const y = ((bounds.latMax - lat) / (bounds.latMax - bounds.latMin)) * 100; // 纬度翻转
  return { x: Math.max(2, Math.min(98, x)), y: Math.max(2, Math.min(98, y)) };
}

// ── Detail Panel ─────────────────────────────────────────────────────────────

function DetailPanel({ spot, onClose }: { spot: RushSpot; onClose: () => void }) {
  const status = bloomStatus(spot);
  return (
    <div className="bg-white rounded-2xl shadow-xl border border-stone-200 overflow-hidden max-w-sm w-full">
      {spot.photo ? (
        <div className="relative w-full h-36">
          <Image src={spot.photo} alt={spot.name} fill className="object-cover" unoptimized />
        </div>
      ) : (
        <div className="w-full h-24 bg-gradient-to-br from-pink-100 to-pink-200 flex items-center justify-center text-4xl">🌸</div>
      )}
      <div className="p-4 space-y-2">
        <div className="flex items-start justify-between">
          <h3 className="text-base font-bold text-stone-900">{spot.name}</h3>
          <button onClick={onClose} className="text-stone-400 hover:text-stone-600 text-lg leading-none">✕</button>
        </div>
        <div className={cn("text-xs font-bold", status.cls)}>{status.label}</div>
        <div className="p-2 bg-pink-50 rounded-lg flex items-center gap-2">
          <span className="text-2xl font-black text-pink-700">{spot.score}</span>
          <div>
            <div className="text-[11px] font-bold text-pink-700">好看指数 / 100</div>
            <div className="text-[9px] text-stone-500">综合规模、名气、夜樱等</div>
          </div>
        </div>
        <div className="flex gap-3 text-xs">
          {spot.half && <span>半开 <b>{fmtD(spot.half)}</b></span>}
          {spot.full && <span className="text-pink-700">满开 <b>{fmtD(spot.full)}</b></span>}
          {spot.fall && <span>飘落 <b>{fmtD(spot.fall)}</b></span>}
        </div>
        <div className="flex flex-wrap gap-1">
          {spot.meisyo100 && <span className="text-[9px] px-1.5 py-0.5 rounded bg-orange-50 text-orange-700 font-semibold">🏆 百选</span>}
          {spot.lightup && <span className="text-[9px] px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 font-semibold">🌙 夜樱</span>}
          {spot.trees && <span className="text-[9px] px-1.5 py-0.5 rounded bg-green-50 text-green-700 font-semibold">🌳 {spot.trees}</span>}
        </div>
        {(spot.desc_cn || spot.desc) && (
          <p className="text-[11px] text-stone-600 leading-relaxed">{spot.desc_cn || spot.desc}</p>
        )}
      </div>
    </div>
  );
}

// ── Main Export ──────────────────────────────────────────────────────────────

export interface SakuraMapProps {
  cities: RushCity[];
  landmarks: Record<string, Landmark[]>;
  initialCity?: number;
}

const CITY_MAP_IMG: Record<string, string> = {
  tokyo: "/images/map-tokyo.png",
  kyoto: "/images/map-kyoto.png",
  osaka: "/images/map-osaka.png",
  aichi: "/images/map-nagoya.png",
  hiroshima: "/images/map-hiroshima.png",
};

export default function SakuraMap({ cities, landmarks, initialCity = 0 }: SakuraMapProps) {
  const [cityIdx, setCityIdx] = useState(initialCity);
  const [selectedSpot, setSelectedSpot] = useState<number | null>(null);

  const city = cities[cityIdx];
  const bounds = getBounds(city);
  const mapImg = CITY_MAP_IMG[city.key] || CITY_MAP_IMG.tokyo;
  const spot = selectedSpot !== null ? city.spots[selectedSpot] : null;

  return (
    <div className="flex flex-col bg-white rounded-xl overflow-hidden border border-stone-200">
      {/* City tabs */}
      <div className="flex items-center gap-0.5 px-3 py-2 border-b border-stone-100 bg-stone-50 overflow-x-auto shrink-0">
        {cities.map((c, i) => (
          <button
            key={c.key}
            onClick={() => { setCityIdx(i); setSelectedSpot(null); }}
            className={cn(
              "px-3 py-1.5 text-xs font-semibold rounded-md whitespace-nowrap transition-colors",
              i === cityIdx ? "text-pink-700 bg-pink-50 border border-pink-200" : "text-stone-500 hover:text-stone-700"
            )}
          >
            {c.emoji} {c.name}
          </button>
        ))}
      </div>

      {/* 地图区域 */}
      <div className="relative w-full" style={{ paddingBottom: "100%" }}>
        {/* 底图 — 城市地图截图 */}
        <div className="absolute inset-0 bg-cover bg-center" style={{ backgroundImage: `url('${mapImg}')` }} />

        {/* 景点圆点 */}
        {city.spots.map((s, i) => {
          if (!s.lat || !s.lon) return null;
          const pos = toPercent(s.lat, s.lon, bounds);
          const isSelected = i === selectedSpot;
          return (
            <button
              key={s.id}
              onClick={() => setSelectedSpot(isSelected ? null : i)}
              className={cn(
                "absolute rounded-full border-2 transition-all duration-200 z-10",
                isSelected
                  ? "w-5 h-5 border-stone-800 scale-125 z-20"
                  : "w-3.5 h-3.5 border-white hover:scale-125 hover:z-20"
              )}
              style={{
                left: `${pos.x}%`,
                top: `${pos.y}%`,
                transform: "translate(-50%, -50%)",
                backgroundColor: s.color || "#e91e63",
                boxShadow: isSelected ? "0 0 0 3px rgba(0,0,0,0.15)" : "0 1px 3px rgba(0,0,0,0.2)",
              }}
              title={`${s.name} · 好看${s.score}`}
            >
              {/* TOP5 显示名字标签 */}
              {i < 5 && (
                <span className={cn(
                  "absolute whitespace-nowrap text-[10px] font-bold pointer-events-none",
                  isSelected ? "text-stone-900" : "text-stone-700",
                  i % 2 === 0 ? "left-full ml-1.5" : "right-full mr-1.5"
                )}>
                  {s.name.slice(0, 6)}
                </span>
              )}
            </button>
          );
        })}

        {/* 地标 */}
        {(landmarks[city.key] || []).map((lm, i) => {
          const pos = toPercent(lm.lat, lm.lon, bounds);
          return (
            <div
              key={`lm-${i}`}
              className="absolute flex items-center gap-0.5 bg-white/90 border border-stone-300 rounded px-1.5 py-0.5 text-[10px] font-semibold text-stone-600 z-[5] pointer-events-none"
              style={{ left: `${pos.x}%`, top: `${pos.y}%`, transform: "translate(-50%, -50%)" }}
            >
              <span>{lm.emoji}</span>{lm.name}
            </div>
          );
        })}

        {/* 图例 */}
        <div className="absolute bottom-2 left-2 z-30 bg-white/90 backdrop-blur-sm rounded-lg px-2.5 py-1.5 shadow border border-stone-200">
          <div className="flex gap-2 text-[9px]">
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-[#c2185b]" />满开</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-[#e91e63]" />开花</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-[#81c784]" />未开</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-[#9c27b0]" />飘落</span>
          </div>
        </div>

        {/* 城市名水印 */}
        <div className="absolute top-3 right-3 text-lg font-black text-stone-200/50 z-[1] pointer-events-none">
          {city.emoji} {city.name}
        </div>
      </div>

      {/* 底部列表 — 手机横向滚动 */}
      <div className="flex gap-2 px-3 py-2 overflow-x-auto border-t border-stone-100 bg-white shrink-0">
        {city.spots.slice(0, 15).map((s, i) => {
          const st = bloomStatus(s);
          const isActive = i === selectedSpot;
          return (
            <button
              key={s.id}
              onClick={() => setSelectedSpot(isActive ? null : i)}
              className={cn(
                "shrink-0 px-3 py-2 rounded-lg text-left border transition-all",
                isActive ? "border-pink-300 bg-pink-50 shadow-sm" : "border-stone-100 hover:border-stone-200"
              )}
              style={{ minWidth: 120 }}
            >
              <div className="text-[11px] font-bold text-stone-800 truncate">{s.name.slice(0, 8)}</div>
              <div className={cn("text-[10px] mt-0.5", st.cls)}>{st.label}</div>
              <div className="text-[10px] text-stone-400 mt-0.5">好看 <b className="text-pink-600">{s.score}</b></div>
            </button>
          );
        })}
      </div>

      {/* 选中景点详情弹层 */}
      {spot && (
        <div className="fixed inset-0 z-50 flex items-end md:items-center justify-center bg-black/30 backdrop-blur-sm"
          onClick={() => setSelectedSpot(null)}
        >
          <div onClick={(e) => e.stopPropagation()} className="w-full md:w-auto md:mx-4 max-h-[80vh] overflow-y-auto">
            <DetailPanel spot={spot} onClose={() => setSelectedSpot(null)} />
          </div>
        </div>
      )}
    </div>
  );
}