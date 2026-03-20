"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CityTabs } from "@/components/rush/CityTabs";
import { SpotCard } from "@/components/rush/SpotCard";
import { staggerContainerSlow } from "@/lib/animations";
import type { Spot } from "@/lib/data";

interface RushClientProps {
  dataByCity: Record<string, Spot[]>;
}

export default function RushClient({ dataByCity }: RushClientProps) {
  const [city, setCity] = useState("tokyo");
  const spots = dataByCity[city] || [];
  const topSpots = spots.slice(0, 12);

  // Count spots at "full bloom" this week (simplified)
  const fullBloomCount = spots.filter((s) => s.full).length;

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Weekly Rush Banner */}
      <div className="shrink-0 bg-gradient-to-r from-warm-300 to-sakura-400 px-6 py-3">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <p className="text-white font-bold text-sm">
            🌸 本周 {fullBloomCount} 个景点满开 · 错过等明年！
          </p>
          <div className="flex gap-1.5 overflow-x-auto">
            {spots
              .filter((s) => s.full)
              .slice(0, 5)
              .map((s) => (
                <span
                  key={s.name}
                  className="shrink-0 text-[10px] bg-white/20 text-white px-2 py-0.5 rounded-full"
                >
                  {s.name}
                </span>
              ))}
          </div>
        </div>
      </div>

      {/* City Tabs */}
      <div className="shrink-0 px-6 py-3 flex justify-center">
        <CityTabs active={city} onChange={setCity} />
      </div>

      {/* Spot Grid */}
      <div className="flex-1 overflow-y-auto px-6 pb-4">
        <AnimatePresence mode="wait">
          <motion.div
            key={city}
            variants={staggerContainerSlow}
            initial="initial"
            animate="animate"
            exit={{ opacity: 0 }}
            className="max-w-6xl mx-auto grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3"
          >
            {topSpots.map((spot, i) => (
              <SpotCard key={`${city}-${spot.name}`} spot={spot} rank={i + 1} />
            ))}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
