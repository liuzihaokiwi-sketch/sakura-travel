"use client";

import { useEffect, useRef } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from "react-leaflet";
import { getCityCoord } from "@/lib/city-coords";
import type { Spot } from "@/lib/data";
import "leaflet/dist/leaflet.css";

// ── Bloom color map ─────────────────────────────────────────────────────────

function getMarkerColor(spot: Spot): string {
  if (spot.stage === "full_bloom" || spot.full) {
    const now = new Date();
    if (spot.full) {
      const [m, d] = spot.full.split("/").map(Number);
      if (m && d) {
        const bloom = new Date(now.getFullYear(), m - 1, d);
        const diff = (now.getTime() - bloom.getTime()) / 86400000;
        if (diff > 7) return "#9E9E9E"; // 散落
        if (diff >= -2) return "#C2185B"; // 満開
      }
    }
    return "#C2185B";
  }
  if (spot.stage === "approaching" || spot.half) return "#E91E63"; // 五分咲
  if (spot.stage === "starting") return "#F8BBD0"; // 三分咲
  if (spot.stage === "falling") return "#9E9E9E"; // 散落
  return "#4CAF50"; // 未開
}

// ── FlyTo handler ───────────────────────────────────────────────────────────

function FlyToCity({ cityCode }: { cityCode: string }) {
  const map = useMap();
  useEffect(() => {
    const coord = getCityCoord(cityCode);
    map.flyTo([coord.lat, coord.lng], coord.zoom, { duration: 1.2 });
  }, [cityCode, map]);
  return null;
}

// ── Main component ──────────────────────────────────────────────────────────

interface SakuraMapProps {
  spots: Spot[];
  activeCity: string;
  onSpotClick: (spot: Spot) => void;
}

export default function SakuraMap({ spots, activeCity, onSpotClick }: SakuraMapProps) {
  const coord = getCityCoord(activeCity);

  // Filter spots that have coordinates (from weathernews data)
  const mappableSpots = spots.filter(s => {
    // Use dummy coords based on city center + random offset for now
    // TODO: Replace with real lat/lng from weathernews crawl
    return true;
  });

  return (
    <div className="w-full h-[400px] rounded-2xl overflow-hidden border border-stone-200">
      <MapContainer
        center={[coord.lat, coord.lng]}
        zoom={coord.zoom}
        className="w-full h-full"
        scrollWheelZoom={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <FlyToCity cityCode={activeCity} />

        {mappableSpots.map((spot, i) => {
          // Generate deterministic offset from spot name hash
          const hash = spot.name.split("").reduce((acc, ch) => acc + ch.charCodeAt(0), 0);
          const lat = coord.lat + ((hash % 100) - 50) * 0.003;
          const lng = coord.lng + (((hash * 7) % 100) - 50) * 0.004;
          const color = getMarkerColor(spot);

          return (
            <CircleMarker
              key={`${activeCity}-${spot.name}`}
              center={[lat, lng]}
              radius={8}
              pathOptions={{ color, fillColor: color, fillOpacity: 0.8, weight: 2 }}
              eventHandlers={{ click: () => onSpotClick(spot) }}
            >
              <Popup>
                <div className="text-xs min-w-[140px]">
                  <p className="font-bold text-stone-900">{spot.name}</p>
                  <p className="text-stone-500 mt-0.5">能冲指数: <strong>{spot.score}</strong></p>
                  <button
                    onClick={() => onSpotClick(spot)}
                    className="mt-1 text-rose-600 font-medium hover:underline"
                  >
                    查看详情 →
                  </button>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
}
