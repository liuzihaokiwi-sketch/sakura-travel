"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import dynamic from "next/dynamic";
import Image from "next/image";
import { cn } from "@/lib/utils";
import type { RushSpot, RushCity, Landmark } from "@/lib/rush-data";

// Lazy-load Leaflet (SSR incompatible)
const MapContainer = dynamic(() => import("react-leaflet").then((m) => m.MapContainer), { ssr: false });
const TileLayer = dynamic(() => import("react-leaflet").then((m) => m.TileLayer), { ssr: false });
const CircleMarker = dynamic(() => import("react-leaflet").then((m) => m.CircleMarker), { ssr: false });
const Tooltip = dynamic(() => import("react-leaflet").then((m) => m.Tooltip), { ssr: false });
const Marker = dynamic(() => import("react-leaflet").then((m) => m.Marker), { ssr: false });
const Popup = dynamic(() => import("react-leaflet").then((m) => m.Popup), { ssr: false });

// ── BloomBar (inline, shared with Timeline) ─────────────────────────────────

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

function daysToStr(s?: string) {
  if (!s) return "";
  const m = s.match(/(\d+)月(\d+)日/);
  if (!m) return "";
  const d = new Date(2026, parseInt(m[1]) - 1, parseInt(m[2]));
  const now = new Date(); now.setHours(0, 0, 0, 0);
  const days = Math.round((d.getTime() - now.getTime()) / 864e5);
  if (days > 0) return `${days}天后`;
  if (days === 0) return "今天!";
  return `已过${Math.abs(days)}天`;
}

// ── Left Panel Item ─────────────────────────────────────────────────────────

function LeftPanelItem({ spot, rank, active, onClick }: {
  spot: RushSpot; rank: number; active: boolean; onClick: () => void;
}) {
  const rankClass = rank === 1 ? "bg-gradient-to-br from-yellow-400 to-amber-500"
    : rank === 2 ? "bg-gradient-to-br from-gray-300 to-gray-400"
    : rank === 3 ? "bg-gradient-to-br from-amber-600 to-amber-700"
    : "bg-stone-200 text-stone-500";

  return (
    <div
      className={cn(
        "px-2.5 py-2 border-b border-stone-50 cursor-pointer transition-colors border-l-[3px]",
        active ? "bg-pink-50 border-l-pink-500" : "border-l-transparent hover:bg-stone-50"
      )}
      onClick={onClick}
    >
      <div className="flex items-center gap-1.5">
        <span className={cn("inline-flex items-center justify-center w-5 h-5 rounded-full text-[9px] font-bold text-white", rankClass)}>
          {rank}
        </span>
        <span className="text-[11px] font-semibold text-stone-800 truncate">{spot.name.slice(0, 10)}</span>
      </div>
      <div className="ml-6 mt-0.5 text-[9px] text-stone-500">
        <b className="text-pink-700">满开 {fmtD(spot.full)}</b> {daysToStr(spot.full)}
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
        点击地图或左侧列表<br />查看景点详情
      </div>
    );
  }

  const reasons: string[] = [];
  const tn = spot.trees ? parseInt(spot.trees.match(/(\d+)/)?.[1] || "0") : 0;
  if (spot.meisyo100) reasons.push("🏆 名所100选");
  if (tn >= 1000) reasons.push(`🌳 ${spot.trees}，规模壮观`);
  else if (tn >= 500) reasons.push(`🌳 ${spot.trees}`);
  if (spot.lightup) reasons.push("🌙 夜樱灯光");

  return (
    <div className="overflow-y-auto">
      {/* Photo */}
      {spot.photo ? (
        <div className="relative w-full h-40">
          <Image src={spot.photo} alt={spot.name} fill className="object-cover" unoptimized />
        </div>
      ) : (
        <div className="w-full h-24 bg-gradient-to-br from-pink-100 to-pink-200 flex items-center justify-center text-4xl">🌸</div>
      )}

      <div className="p-3">
        {/* Name + score */}
        <h3 className="text-[17px] font-bold text-stone-900">{spot.name}</h3>
        <div className="flex items-center gap-2 mt-2 p-2 bg-pink-50 rounded-lg">
          <span className="text-2xl font-black text-pink-700">{spot.score}</span>
          <div>
            <div className="text-[11px] font-semibold text-pink-700">推荐指数</div>
            <div className="text-[9px] text-stone-500">{reasons.join(" · ") || "樱花名所"}</div>
          </div>
        </div>

        {/* Dates */}
        <div className="mt-2.5 space-y-1">
          {spot.half && (
            <div className="flex items-center gap-1.5 text-xs">
              <span className="w-2 h-2 rounded-full bg-pink-300" />
              <span className="w-8 text-stone-500">半开</span>
              <span className="font-bold flex-1">{fmtD(spot.half)}</span>
              <span className="text-stone-400 text-[10px]">{daysToStr(spot.half)}</span>
            </div>
          )}
          {spot.full && (
            <div className="flex items-center gap-1.5 text-xs">
              <span className="w-2 h-2 rounded-full bg-pink-600" />
              <span className="w-8 text-stone-500">满开</span>
              <span className="font-bold flex-1 text-pink-700">{fmtD(spot.full)}</span>
              <span className="text-pink-600 text-[10px] font-semibold">{daysToStr(spot.full)}</span>
            </div>
          )}
          {spot.fall && (
            <div className="flex items-center gap-1.5 text-xs">
              <span className="w-2 h-2 rounded-full bg-purple-500" />
              <span className="w-8 text-stone-500">飘落</span>
              <span className="font-bold flex-1">{fmtD(spot.fall)}</span>
              <span className="text-stone-400 text-[10px]">{daysToStr(spot.fall)}</span>
            </div>
          )}
        </div>

        {/* Bloom bar */}
        <BloomBar half={spot.half} full={spot.full} fall={spot.fall} className="mt-2" />

        {/* Tags */}
        <div className="flex flex-wrap gap-1 mt-2.5">
          {spot.meisyo100 && <span className="text-[9px] px-1.5 py-0.5 rounded bg-orange-50 text-orange-700">🏆 名所百选</span>}
          {spot.lightup && <span className="text-[9px] px-1.5 py-0.5 rounded bg-purple-50 text-purple-700">🌙 夜樱灯光</span>}
          {spot.trees && <span className="text-[9px] px-1.5 py-0.5 rounded bg-green-50 text-green-700">🌳 {spot.trees}</span>}
          {spot.namiki && <span className="text-[9px] px-1.5 py-0.5 rounded bg-blue-50 text-blue-700">🌸 樱花隧道</span>}
        </div>

        {/* Description */}
        {(spot.desc_cn || spot.desc) && (
          <p className="mt-2.5 text-[11px] text-stone-600 leading-relaxed">
            {spot.desc_cn || spot.desc}
          </p>
        )}
      </div>
    </div>
  );
}

// ── MapView Component ───────────────────────────────────────────────────────

function MapViewInner({ city, landmarks, onSelectSpot, selectedIdx }: {
  city: RushCity;
  landmarks: Landmark[];
  onSelectSpot: (idx: number) => void;
  selectedIdx: number;
}) {
  return (
    <MapContainer
      center={city.center}
      zoom={city.zoom}
      className="w-full h-full"
      zoomControl={false}
      attributionControl={false}
      dragging={false}
      scrollWheelZoom={false}
      doubleClickZoom={false}
      touchZoom={false}
    >
      <TileLayer url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png" />

      {/* Spot markers */}
      {city.spots.map((s, i) => {
        if (!s.lat || !s.lon) return null;
        return (
          <CircleMarker
            key={s.id}
            center={[s.lat, s.lon]}
            radius={selectedIdx === i ? 10 : 7}
            fillColor={s.color}
            fillOpacity={0.8}
            color={selectedIdx === i ? "#333" : "#fff"}
            weight={selectedIdx === i ? 2 : 1.5}
            eventHandlers={{ click: () => onSelectSpot(i) }}
          >
            <Popup>{s.name}<br />满开: {fmtD(s.full)}</Popup>
            {/* Permanent label for top 6 */}
            {i < 6 && (
              <Tooltip permanent direction={i % 2 === 0 ? "right" : "left"} offset={i % 2 === 0 ? [10, 0] : [-10, 0]}>
                <div className="text-[9px] font-bold">{s.name.slice(0, 8)}</div>
                <div className="text-[8px] text-pink-600">
                  满开 {fmtD(s.full)}
                  {s.score >= 90 && <span className="ml-1 text-white bg-pink-500 rounded px-0.5">{s.score}</span>}
                </div>
              </Tooltip>
            )}
          </CircleMarker>
        );
      })}

      {/* Landmark markers */}
      {landmarks.map((lm, i) => (
        <CircleMarker key={`lm-${i}`} center={[lm.lat, lm.lon]} radius={3} fillColor="#ccc" fillOpacity={0.5} color="#aaa" weight={1}>
          <Tooltip direction="top" offset={[0, -5]}>
            <span className="text-[8px]">{lm.emoji} {lm.name}</span>
          </Tooltip>
        </CircleMarker>
      ))}
    </MapContainer>
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
    <div className="flex flex-col h-[calc(100vh-56px)] md:h-[700px] bg-white rounded-xl overflow-hidden border border-stone-200">
      {/* City tabs */}
      <div className="flex items-center gap-0.5 px-3 py-2 border-b border-stone-100 bg-stone-50 overflow-x-auto shrink-0">
        {cities.map((c, i) => (
          <button
            key={c.key}
            onClick={() => handleCitySwitch(i)}
            className={cn(
              "px-3 py-1 text-xs font-semibold rounded-md whitespace-nowrap transition-colors",
              i === cityIdx ? "text-pink-700 bg-pink-50" : "text-stone-500 hover:text-stone-700"
            )}
          >
            {c.emoji} {c.name}
          </button>
        ))}
      </div>

      {/* Three-column layout (desktop) / stacked (mobile) */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left panel — hidden on mobile */}
        <div className="hidden md:flex flex-col w-[220px] border-r border-stone-100 bg-white shrink-0">
          <div className="px-2.5 py-2 text-xs font-bold border-b border-stone-50 flex items-center gap-1 shrink-0">
            <span>{city.emoji}</span>
            {city.name} TOP {Math.min(city.spots.length, 20)}
            <span className="text-[9px] text-pink-600 font-semibold ml-auto">{city.status}</span>
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
        <div className="flex-1 relative">
          <MapViewInner
            city={city}
            landmarks={cityLandmarks}
            onSelectSpot={handleSelectSpot}
            selectedIdx={selectedSpot}
          />
        </div>

        {/* Right panel — hidden on mobile */}
        <div className="hidden md:flex flex-col w-[300px] border-l border-stone-100 bg-white shrink-0">
          <DetailPanel spot={spot} />
        </div>
      </div>

      {/* Mobile bottom sheet */}
      {showMobileDetail && spot && (
        <div className="md:hidden fixed inset-x-0 bottom-0 z-50 bg-white rounded-t-2xl shadow-2xl max-h-[60vh] overflow-y-auto animate-in slide-in-from-bottom">
          <div className="flex justify-center py-2">
            <div className="w-10 h-1 bg-stone-300 rounded-full" />
          </div>
          <button
            onClick={() => setShowMobileDetail(false)}
            className="absolute top-2 right-3 text-stone-400 text-lg"
          >
            ✕
          </button>
          <DetailPanel spot={spot} />
        </div>
      )}
    </div>
  );
}