"use client";

import { motion } from "framer-motion";
import { fadeInUp } from "@/lib/animations";
import { Badge } from "@/components/ui/badge";
import type { Spot } from "@/lib/data";

function getBloomStatus(spot: Spot): { label: string; variant: "bloom" | "success" | "warning" | "secondary" } {
  // Simple heuristic based on dates
  if (spot.full) return { label: "🌸 满开", variant: "bloom" };
  if (spot.half) return { label: "🌱 五分咲", variant: "success" };
  if (spot.fall) return { label: "🍂 散り始め", variant: "warning" };
  return { label: "⏳ 待开", variant: "secondary" };
}

export function SpotCard({ spot, rank }: { spot: Spot; rank: number }) {
  const bloom = getBloomStatus(spot);

  return (
    <motion.div
      variants={fadeInUp}
      className="group bg-white rounded-xl border border-stone-100 overflow-hidden hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200 flex flex-col"
    >
      {/* Photo */}
      {spot.photo && (
        <div className="relative h-28 overflow-hidden">
          <img
            src={spot.photo}
            alt={spot.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
          {/* Rank badge */}
          <div className="absolute top-2 left-2 w-7 h-7 rounded-full bg-gradient-to-br from-warm-300 to-warm-400 flex items-center justify-center text-white text-xs font-bold shadow">
            {rank}
          </div>
          {/* Score */}
          <div className="absolute top-2 right-2 bg-black/60 backdrop-blur-sm text-white text-xs font-mono font-bold px-2 py-0.5 rounded-full">
            {spot.score}
          </div>
        </div>
      )}

      <div className="p-3 flex-1 flex flex-col">
        {/* Name + Status */}
        <div className="flex items-start justify-between gap-2 mb-1.5">
          <h3 className="text-sm font-bold text-stone-900 leading-tight">{spot.name}</h3>
          <Badge variant={bloom.variant} className="shrink-0 text-[10px]">{bloom.label}</Badge>
        </div>

        {spot.desc_cn && (
          <p className="text-[11px] text-stone-400 mb-2">{spot.desc_cn}</p>
        )}

        {/* Dates */}
        <div className="text-[10px] text-stone-500 space-y-0.5 mb-2">
          {spot.half && <span>🌱 五分咲 {spot.half}</span>}
          {spot.full && <span className="ml-2">🌸 满开 {spot.full}</span>}
          {spot.fall && <span className="ml-2">🍂 散始 {spot.fall}</span>}
        </div>

        {/* Tags */}
        <div className="mt-auto flex flex-wrap gap-1">
          {spot.trees && (
            <span className="text-[9px] bg-stone-50 text-stone-500 px-1.5 py-0.5 rounded">
              🌳 {spot.trees}
            </span>
          )}
          {spot.lightup && (
            <span className="text-[9px] bg-indigo-50 text-indigo-500 px-1.5 py-0.5 rounded">
              🌙 夜樱
            </span>
          )}
          {spot.meisyo100 && (
            <span className="text-[9px] bg-amber-50 text-amber-600 px-1.5 py-0.5 rounded">
              ⭐ 名所百选
            </span>
          )}
          {spot.region && (
            <span className="text-[9px] bg-stone-50 text-stone-400 px-1.5 py-0.5 rounded">
              📍 {spot.region}
            </span>
          )}
        </div>
      </div>
    </motion.div>
  );
}
