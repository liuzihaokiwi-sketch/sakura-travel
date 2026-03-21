"use client";

/**
 * SakuraMap.tsx — 三栏地图组件
 * 左栏: TOP20 排行 (桌面端)
 * 中间: Leaflet 地图 + 标记
 * 右栏: 景点详情 (桌面端) / 底部抽屉 (手机端)
 */

import { useState, useCallback, useEffect, useRef } from "react";
import Image from "next/image";
import { cn } from "@/lib/utils";
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Marker,
  Tooltip,
  Popup,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { RushSpot, RushCity, Landmark } from "@/lib/rush-data";

// ── Landmark icon ────────────────────────────────────────────────────────────

function createLandmarkIcon(emoji: string, name: string) {
  return L.divIcon({
    className: "landmark-icon",
    html: `<div style="display:flex;align-items:center;gap:3px;background:rgba(255,255,255,0.92);border:1.5px solid #a8a29e;border-radius:6px;padding:2px 6px;white-space:nowrap;box-shadow:0 1px 4px rgba(0,0,0,0.12);pointer-events:auto;">
      <span style="font-size:14px;">${emoji}</span>
      <span style="font-size:11px;font-weight:600;color:#44403c;">${name}</span>
    </div>`,
    iconSize: [0, 0],
    iconAnchor: [0, 12],
  });
}

// ── BloomBar (inline) ───────────────────────────────────────────────────────

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
    <div className={cn("relative h-1.5 bg-stone-100 rounded-full", className)}>
      {half && <div className="absolute h-full rounded-full bg-gradient-to-r from-pink-200 to-pink-300" style={{ left: `${pct(half)}%`, width: `${Math.max(1, pct(full || half) - pct(half))}%` }} />}
      {full && <div className="absolute h-full rounded-full bg-gradient-to-r from-pink-500 to-pink-700" style={{ left: `${pct(full)}%`, width: `${Math.max(1, pct(fall || full) - pct(full))}%` }} />}
      {fall && <div className="absolute h-full rounded-full bg-gradient-to-r from-purple-300 to-purple-500" style={{ left: `${pct(fall)}%`, width: `${Math.min(8, 100 - pct(fall))}%` }} />}
      <div className="absolute -top-0.5 w-0.5 h-2.5 bg-stone-800 rounded-sm" style={{ left: `${todayP}%` }} />
    </div>
  );
}

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

// ── FlyToCity ────────────────────────────────────────────────────────────────

function FlyToCity({ center, zoom }: { center: [number, number]; zoom: number }) {
  const map = useMap();
  useEffect(() => {
    map.flyTo(center, zoom, { duration: 0.8 });
  }, [map, center, zoom]);
  return null;
}

// ── InvalidateSize on mount (fix partial tile load) ─────────────────────────

function InvalidateSize() {
  const map = useMap();
  useEffect(() => {
    const timer = setTimeout(() => map.invalidateSize(), 300);
    return () => clearTimeout(timer);
  }, [map]);
  return null;
}

// ── Left Panel Item ─────────────────────────────────────────────────────────

function LeftPanelItem({ spot, rank, active, onClick }: {
  spot: RushSpot; rank: number; active: boolean; onClick: () => void;
}) {
  const status = bloomStatus(spot);
  return (
    <div
      className={cn(
        "px-2.5 py-2 border-b border-stone-50 cursor-pointer transition-colors border-l-[3px]",
        active ? "bg-pink-50 border-l-pink-500" : "border-l-transparent hover:bg-stone-50"
      )}
      onClick={onClick}
    >
      <div className="flex items-center gap-1.5">
        <span className={cn(
          "inline-flex items-center justify-center w-5 h-5 rounded-full text-[9px] font-bold text-white",
          rank <= 3 ? "bg-pink-500" : "bg-stone-300"
        )}>
          {rank}
        </span>
        <span className="text-[11px] font-semibold text-stone-800 truncate flex-1">{spot.name.slice(0, 10)}</span>
        <div className="shrink-0 flex items-center gap-1">
          <span className="text-[10px] font-black text-pink-600">{spot.score}</span>
          <span className="text-[7px] text-stone-400">分</span>
        </div>
      </div>
      <div className="ml-6 mt-0.5 flex items-center gap-2">
        <span className={cn("text-[9px]", status.cls)}>{status.label}</span>
        <span className="text-[9px] text-stone-400">满开 {fmtD(spot.full)}</span>
      </div>
      <BloomBar half={spot.half} full={spot.full} fall={spot.fall} className="ml-6 mt-1" />
    </div>
  );
}

// ── Right Detail Panel ──────────────────────────────────────────────────────

function DetailPanel({ spot }: { spot: RushSpot | null }) {
  if (!spot) {
    return (
      <div className="flex-1 flex items-center justify-center text-stone-300 text-sm p-5 text-center leading-relaxed">
        点击地图标记 或 左侧列表<br />查看景点详情
      </div>
    );
  }

  const status = bloomStatus(spot);

  return (
    <div className="overflow-y-auto">
      {spot.photo ? (
        <div className="relative w-full h-40">
          <Image src={spot.photo} alt={spot.name} fill className="object-cover" unoptimized />
        </div>
      ) : (
        <div className="w-full h-24 bg-gradient-to-br from-pink-100 to-pink-200 flex items-center justify-center text-4xl">🌸</div>
      )}

      <div className="p-3 space-y-2.5">
        <h3 className="text-[17px] font-bold text-stone-900">{spot.name}</h3>

        {/* 花期状态 */}
        <div className={cn("inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-bold border",
          status.label.includes("满开") ? "bg-pink-100 text-pink-700 border-pink-200" :
          status.label.includes("开花") ? "bg-pink-50 text-pink-600 border-pink-100" :
          status.label.includes("飘落") ? "bg-purple-50 text-purple-600 border-purple-100" :
          "bg-stone-50 text-stone-600 border-stone-200"
        )}>
          {status.label}
        </div>

        {/* 好看指数 — 明确说明 */}
        <div className="p-2.5 bg-pink-50 rounded-lg border border-pink-100">
          <div className="flex items-center gap-2">
            <span className="text-2xl font-black text-pink-700">{spot.score}</span>
            <div>
              <div className="text-[11px] font-bold text-pink-700">好看指数 <span className="text-[10px] font-normal text-pink-500">/ 100</span></div>
              <div className="text-[9px] text-stone-500">= 满开时的好看程度</div>
            </div>
          </div>
          <div className="text-[8px] text-stone-400 mt-1">综合规模、名气、夜樱、花期长度等</div>
        </div>

        {/* Dates */}
        <div className="space-y-1">
          {spot.half && (
            <div className="flex items-center gap-1.5 text-xs">
              <span className="w-2 h-2 rounded-full bg-pink-300" />
              <span className="w-8 text-stone-500">半开</span>
              <span className="font-bold flex-1">{fmtD(spot.half)}</span>
            </div>
          )}
          {spot.full && (
            <div className="flex items-center gap-1.5 text-xs">
              <span className="w-2 h-2 rounded-full bg-pink-600" />
              <span className="w-8 text-stone-500">满开</span>
              <span className="font-bold flex-1 text-pink-700">{fmtD(spot.full)}</span>
            </div>
          )}
          {spot.fall && (
            <div className="flex items-center gap-1.5 text-xs">
              <span className="w-2 h-2 rounded-full bg-purple-500" />
              <span className="w-8 text-stone-500">飘落</span>
              <span className="font-bold flex-1">{fmtD(spot.fall)}</span>
            </div>
          )}
        </div>

        <BloomBar half={spot.half} full={spot.full} fall={spot.fall} />

        <div className="flex flex-wrap gap-1">
          {spot.meisyo100 && <span className="text-[9px] px-1.5 py-0.5 rounded bg-orange-50 text-orange-700 font-semibold">🏆 名所百选</span>}
          {spot.lightup && <span className="text-[9px] px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 font-semibold">🌙 夜樱灯光</span>}
          {spot.trees && <span className="text-[9px] px-1.5 py-0.5 rounded bg-green-50 text-green-700 font-semibold">🌳 {spot.trees}</span>}
        </div>

        {(spot.desc_cn || spot.desc) && (
          <p className="text-[11px] text-stone-600 leading-relaxed">{spot.desc_cn || spot.desc}</p>
        )}
      </div>
    </div>
  );
}

// ── Map Legend ────────────────────────────────────────────────────────────────

function MapLegend() {
  return (
    <div className="absolute bottom-3 left-3 z-[999] bg-white/90 backdrop-blur-sm rounded-lg px-3 py-2 shadow-lg border border-stone-200">
      <div className="text-[9px] font-bold text-stone-500 mb-1">地图图例</div>
      <div className="flex flex-wrap gap-x-3 gap-y-1">
        <span className="flex items-center gap-1 text-[9px]"><span className="w-3 h-3 rounded-full bg-[#c2185b]" />满开</span>
        <span className="flex items-center gap-1 text-[9px]"><span className="w-3 h-3 rounded-full bg-[#e91e63]" />开花</span>
        <span className="flex items-center gap-1 text-[9px]"><span className="w-3 h-3 rounded-full bg-[#81c784]" />未开</span>
        <span className="flex items-center gap-1 text-[9px]"><span className="w-3 h-3 rounded-full bg-[#9c27b0]" />飘落</span>
        <span className="flex items-center gap-1 text-[9px]"><span className="w-3 h-3 rounded-sm bg-white border border-stone-300 text-[7px] font-bold flex items-center justify-center">🚉</span>地标</span>
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

export default function SakuraMap({ cities, landmarks, initialCity = 0 }: SakuraMapProps) {
  const [cityIdx, setCityIdx] = useState(initialCity);
  const [selectedSpot, setSelectedSpot] = useState(0);
  const [showMobileDetail, setShowMobileDetail] = useState(false);

  const city = cities[cityIdx];
  const cityLandmarks = landmarks[city.key] || [];
  const spot = city.spots[selectedSpot] || null;

  const handleSelectSpot = useCallback((idx: number) => {
    setSelectedSpot(idx);
    setShowMobileDetail(true);
  }, []);

  const handleCitySwitch = useCallback((idx: number) => {
    setCityIdx(idx);
    setSelectedSpot(0);
    setShowMobileDetail(false);
  }, []);

  return (
    <div className="flex flex-col h-[calc(100vh-120px)] md:h-[700px] bg-white rounded-xl overflow-hidden border border-stone-200">
      {/* City tabs */}
      <div className="flex items-center gap-0.5 px-3 py-2 border-b border-stone-100 bg-stone-50 overflow-x-auto shrink-0">
        {cities.map((c, i) => (
          <button
            key={c.key}
            onClick={() => handleCitySwitch(i)}
            className={cn(
              "px-3 py-1.5 text-xs font-semibold rounded-md whitespace-nowrap transition-colors",
              i === cityIdx ? "text-pink-700 bg-pink-50 border border-pink-200" : "text-stone-500 hover:text-stone-700"
            )}
          >
            {c.emoji} {c.name}
          </button>
        ))}
      </div>

      {/* Three-column layout */}
      <div className="flex flex-1 overflow-hidden min-h-0">
        {/* Left panel — hidden on mobile */}
        <div className="hidden md:flex flex-col w-[220px] border-r border-stone-100 bg-white shrink-0">
          <div className="px-2.5 py-2 text-xs font-bold border-b border-stone-50 flex items-center gap-1 shrink-0">
            <span>{city.emoji}</span>
            {city.name} TOP {Math.min(city.spots.length, 20)}
            <span className="text-[8px] text-stone-400 ml-auto">好看指数↓</span>
          </div>
          <div className="flex-1 overflow-y-auto">
            {city.spots.slice(0, 20).map((s, i) => (
              <LeftPanelItem
                key={s.id}
                spot={s}
                rank={i + 1}
                active={i === selectedSpot}
                onClick={() => handleSelectSpot(i)}
              />
            ))}
          </div>
        </div>

        {/* Center — map */}
        <div className="flex-1 relative min-h-[300px]">
          <MapContainer
            center={city.center}
            zoom={city.zoom}
            style={{ width: "100%", height: "100%" }}
            zoomControl={true}
            attributionControl={false}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              maxZoom={19}
            />
            <FlyToCity center={city.center} zoom={city.zoom} />
            <InvalidateSize />

            {/* Spot markers (cherry blossom spots) */}
            {city.spots.map((s, i) => {
              if (!s.lat || !s.lon) return null;
              const isSelected = i === selectedSpot;
              return (
                <CircleMarker
                  key={s.id}
                  center={[s.lat, s.lon]}
                  radius={isSelected ? 14 : 9}
                  pathOptions={{
                    fillColor: s.color,
                    fillOpacity: 0.9,
                    color: isSelected ? "#333" : "#fff",
                    weight: isSelected ? 3 : 2,
                  }}
                  eventHandlers={{ click: () => handleSelectSpot(i) }}
                >
                  {i < 5 && (
                    <Tooltip permanent direction={i % 2 === 0 ? "right" : "left"} offset={i % 2 === 0 ? [14, 0] : [-14, 0]}>
                      <div style={{ fontSize: 11, fontWeight: 700, lineHeight: 1.3 }}>
                        {s.name.slice(0, 8)}
                      </div>
                      <div style={{ fontSize: 10, color: "#be185d", fontWeight: 600 }}>
                        好看指数 {s.score} · 满开 {fmtD(s.full)}
                      </div>
                    </Tooltip>
                  )}
                </CircleMarker>
              );
            })}

            {/* Landmark markers — highly visible with emoji + name */}
            {cityLandmarks.map((lm, i) => (
              <Marker
                key={`lm-${i}`}
                position={[lm.lat, lm.lon]}
                icon={createLandmarkIcon(lm.emoji, lm.name)}
              />
            ))}
          </MapContainer>

          {/* Map legend */}
          <MapLegend />
        </div>

        {/* Right panel — hidden on mobile */}
        <div className="hidden md:flex flex-col w-[300px] border-l border-stone-100 bg-white shrink-0 overflow-hidden">
          <DetailPanel spot={spot} />
        </div>
      </div>

      {/* Mobile: spot list (horizontal scroll) */}
      <div className="md:hidden flex gap-2 px-3 py-2 overflow-x-auto border-t border-stone-100 bg-white shrink-0">
        {city.spots.slice(0, 10).map((s, i) => {
          const st = bloomStatus(s);
          return (
            <button
              key={s.id}
              onClick={() => handleSelectSpot(i)}
              className={cn(
                "shrink-0 px-3 py-2 rounded-lg text-left border transition-colors",
                i === selectedSpot ? "border-pink-300 bg-pink-50" : "border-stone-100"
              )}
              style={{ minWidth: 130 }}
            >
              <div className="text-[11px] font-bold text-stone-800 truncate">{s.name.slice(0, 8)}</div>
              <div className={cn("text-[10px] mt-0.5", st.cls)}>{st.label}</div>
              <div className="text-[10px] text-stone-400 mt-0.5">好看 <b className="text-pink-600">{s.score}</b></div>
            </button>
          );
        })}
      </div>

      {/* Mobile bottom sheet */}
      {showMobileDetail && spot && (
        <div className="md:hidden fixed inset-x-0 bottom-0 z-50 bg-white rounded-t-2xl shadow-2xl max-h-[55vh] overflow-y-auto border-t border-stone-200">
          <div className="flex justify-center py-2">
            <div className="w-10 h-1 bg-stone-300 rounded-full" />
          </div>
          <button
            onClick={() => setShowMobileDetail(false)}
            className="absolute top-2 right-3 text-stone-400 text-lg z-10"
          >
            ✕
          </button>
          <DetailPanel spot={spot} />
        </div>
      )}
    </div>
  );
}