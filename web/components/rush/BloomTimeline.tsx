"use client";

import { useRef, useEffect, useState } from "react";
import { motion } from "framer-motion";

// ── Types ────────────────────────────────────────────────────────────────────

type BloomStatus = "未開" | "3分咲" | "5分咲" | "満開" | "桜吹雪";

interface BloomNode {
  label: string;       // e.g. "3月上旬"
  dateRange: string;   // e.g. "3/1-3/10"
  status: BloomStatus;
}

// ── Data ─────────────────────────────────────────────────────────────────────

const BLOOM_DATA: BloomNode[] = [
  { label: "3月上旬", dateRange: "3/1-3/10",   status: "未開" },
  { label: "3月中旬", dateRange: "3/11-3/20",  status: "未開" },
  { label: "3月下旬", dateRange: "3/21-3/31",  status: "3分咲" },
  { label: "4月上旬", dateRange: "4/1-4/10",   status: "満開" },
  { label: "4月中旬", dateRange: "4/11-4/20",  status: "5分咲" },
  { label: "4月下旬", dateRange: "4/21-4/30",  status: "桜吹雪" },
];

const STATUS_CONFIG: Record<BloomStatus, { color: string; bg: string; emoji: string; glow: string }> = {
  "未開":   { color: "text-stone-400", bg: "bg-stone-100",  emoji: "🌱", glow: "" },
  "3分咲":  { color: "text-pink-400",  bg: "bg-pink-100",   emoji: "🌸", glow: "" },
  "5分咲":  { color: "text-pink-500",  bg: "bg-pink-200",   emoji: "🌸", glow: "shadow-pink-200/50" },
  "満開":   { color: "text-pink-600",  bg: "bg-pink-300",   emoji: "🌸", glow: "shadow-lg shadow-pink-300/60" },
  "桜吹雪": { color: "text-pink-400",  bg: "bg-pink-100",   emoji: "🍃", glow: "" },
};

// ── Helpers ──────────────────────────────────────────────────────────────────

function getCurrentPeriodIndex(): number {
  const now = new Date();
  const month = now.getMonth() + 1; // 1-indexed
  const day = now.getDate();

  if (month === 3) {
    if (day <= 10) return 0;
    if (day <= 20) return 1;
    return 2;
  }
  if (month === 4) {
    if (day <= 10) return 3;
    if (day <= 20) return 4;
    return 5;
  }
  // Outside bloom season — show no highlight
  return -1;
}

// ── Component ────────────────────────────────────────────────────────────────

interface BloomTimelineProps {
  className?: string;
}

export default function BloomTimeline({ className = "" }: BloomTimelineProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [currentIndex] = useState(getCurrentPeriodIndex);

  // Auto-scroll to current period on mount
  useEffect(() => {
    if (currentIndex >= 0 && scrollRef.current) {
      const nodeWidth = 140; // approximate node width + gap
      const scrollTo = Math.max(0, currentIndex * nodeWidth - scrollRef.current.clientWidth / 2 + nodeWidth / 2);
      scrollRef.current.scrollTo({ left: scrollTo, behavior: "smooth" });
    }
  }, [currentIndex]);

  return (
    <div className={`w-full ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4 px-1">
        <h3 className="text-sm font-bold text-stone-700 flex items-center gap-1.5">
          <span>🌸</span> 花期时间轴
        </h3>
        <span className="text-[10px] text-stone-400">
          {currentIndex >= 0 ? `当前：${BLOOM_DATA[currentIndex].label}` : "非花期"}
        </span>
      </div>

      {/* Scrollable timeline */}
      <div
        ref={scrollRef}
        className="overflow-x-auto scrollbar-hide pb-2"
        style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
      >
        <div className="flex items-center gap-0 min-w-max px-2">
          {BLOOM_DATA.map((node, i) => {
            const config = STATUS_CONFIG[node.status];
            const isCurrent = i === currentIndex;

            return (
              <div key={node.label} className="flex items-center">
                {/* Node */}
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: i * 0.08, duration: 0.3 }}
                  className="flex flex-col items-center w-[120px]"
                >
                  {/* Status emoji + ring */}
                  <div className="relative">
                    <motion.div
                      className={`
                        w-12 h-12 rounded-full flex items-center justify-center
                        ${config.bg} ${config.glow}
                        ${isCurrent ? "ring-2 ring-pink-400 ring-offset-2" : ""}
                        transition-all duration-300
                      `}
                      animate={isCurrent ? { scale: [1, 1.08, 1] } : {}}
                      transition={isCurrent ? { repeat: Infinity, duration: 2, ease: "easeInOut" } : {}}
                    >
                      <span className="text-xl">{config.emoji}</span>
                    </motion.div>

                    {/* Current indicator arrow */}
                    {isCurrent && (
                      <motion.div
                        initial={{ opacity: 0, y: -4 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="absolute -top-5 left-1/2 -translate-x-1/2"
                      >
                        <span className="text-[10px] text-pink-500 font-bold whitespace-nowrap">📍 NOW</span>
                      </motion.div>
                    )}
                  </div>

                  {/* Label */}
                  <p className={`mt-2 text-xs font-medium ${isCurrent ? "text-pink-600" : "text-stone-600"}`}>
                    {node.label}
                  </p>

                  {/* Status text */}
                  <p className={`text-[10px] ${config.color} font-medium`}>
                    {node.status}
                  </p>

                  {/* Date range */}
                  <p className="text-[9px] text-stone-300 mt-0.5">
                    {node.dateRange}
                  </p>
                </motion.div>

                {/* Connector line (not after last node) */}
                {i < BLOOM_DATA.length - 1 && (
                  <div className="flex items-center -mx-1">
                    <motion.div
                      initial={{ scaleX: 0 }}
                      animate={{ scaleX: 1 }}
                      transition={{ delay: i * 0.08 + 0.15, duration: 0.2 }}
                      className={`
                        h-[2px] w-6 origin-left
                        ${i < currentIndex
                          ? "bg-gradient-to-r from-pink-300 to-pink-200"
                          : i === currentIndex
                            ? "bg-gradient-to-r from-pink-400 to-pink-200"
                            : "bg-stone-200"
                        }
                      `}
                    />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap justify-center gap-3 mt-3 px-2">
        {(["未開", "3分咲", "5分咲", "満開", "桜吹雪"] as BloomStatus[]).map((status) => {
          const config = STATUS_CONFIG[status];
          return (
            <div key={status} className="flex items-center gap-1">
              <div className={`w-2.5 h-2.5 rounded-full ${config.bg}`} />
              <span className="text-[9px] text-stone-400">{status}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
