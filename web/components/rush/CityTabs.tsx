"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { CITIES } from "@/lib/constants";

interface CityTabsProps {
  active: string;
  onChange: (code: string) => void;
}

export function CityTabs({ active, onChange }: CityTabsProps) {
  return (
    <div className="flex items-center gap-1 bg-stone-100 rounded-xl p-1">
      {CITIES.map((c) => (
        <button
          key={c.code}
          onClick={() => onChange(c.code)}
          className={cn(
            "relative px-4 py-1.5 rounded-lg text-sm font-medium transition-all duration-200",
            active === c.code
              ? "text-white"
              : "text-stone-500 hover:text-stone-700"
          )}
        >
          {active === c.code && (
            <motion.div
              layoutId="city-tab-bg"
              className="absolute inset-0 bg-gradient-to-r from-sakura-400 to-warm-300 rounded-lg"
              transition={{ type: "spring", bounce: 0.2, duration: 0.4 }}
            />
          )}
          <span className="relative z-10">
            {c.nameCn}
            <span className="ml-1 text-xs opacity-70">({c.spotCount})</span>
          </span>
        </button>
      ))}
    </div>
  );
}
