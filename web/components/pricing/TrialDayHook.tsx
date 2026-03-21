"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { fadeInUp, staggerContainer } from "@/lib/animations";
import {
  HIGHLIGHT_CARDS,
  RHYTHM_GUIDE,
  type Scenario,
  type HighlightCard,
} from "@/lib/content/trial-day-hook";

// ── Types ──────────────────────────────────────────────────────────────────

interface DayStrip {
  day_number: number;
  theme: string;
  city: string;
  is_preview_day: boolean;
}

interface TrialDayHookProps {
  days: DayStrip[];
  totalDays: number;
  price: number;
  planId?: string;
  scenario?: Scenario;
  onUnlock: (trigger: string) => void;
}

// ── Journey Map Strip ──────────────────────────────────────────────────────

function JourneyMapStrip({ days }: { days: DayStrip[] }) {
  return (
    <div className="overflow-x-auto scrollbar-hide -mx-1 px-1">
      <div className="flex gap-2 pb-1" style={{ minWidth: "max-content" }}>
        {days.map((d) => {
          const isUnlocked = d.is_preview_day;
          return (
            <div
              key={d.day_number}
              className={cn(
                "flex-shrink-0 w-24 rounded-xl border p-2.5 text-center transition-all",
                isUnlocked
                  ? "bg-white border-rose-200 shadow-sm"
                  : "bg-stone-50 border-stone-200 opacity-70"
              )}
            >
              <p
                className={cn(
                  "text-[10px] font-bold mb-0.5",
                  isUnlocked ? "text-rose-500" : "text-stone-400"
                )}
              >
                Day {d.day_number}
              </p>
              <p className="text-[10px] text-stone-500 font-medium truncate">{d.city}</p>
              <p className="text-[9px] text-stone-400 mt-0.5 line-clamp-2 leading-tight">
                {isUnlocked ? d.theme.split("×")[0].trim() : "🔒 锁定"}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Highlight Preview Card ─────────────────────────────────────────────────

function HighlightPreviewCard({
  card,
  onClick,
}: {
  card: HighlightCard;
  onClick: () => void;
}) {
  return (
    <motion.div
      variants={fadeInUp}
      className="relative rounded-2xl border border-stone-200 bg-white overflow-hidden cursor-pointer hover:border-rose-300 hover:shadow-md transition-all group"
      onClick={onClick}
    >
      {/* 锁定标记 */}
      <div className="absolute top-2.5 right-2.5 w-6 h-6 rounded-full bg-stone-100 flex items-center justify-center">
        <svg className="w-3 h-3 text-stone-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
            d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
      </div>

      <div className="p-4">
        {/* Emoji 视觉焦点 */}
        <div className="text-3xl mb-2">{card.emoji}</div>

        {/* 标题 */}
        <p className="text-xs font-bold text-stone-800 mb-1">{card.title}</p>

        {/* 情感描述 */}
        <p className="text-xs text-stone-500 leading-relaxed">{card.teaser}</p>

        {/* 解锁提示 */}
        <p className="mt-3 text-xs text-rose-500 font-semibold group-hover:text-rose-600 transition-colors">
          解锁查看完整方案 →
        </p>
      </div>
    </motion.div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────

export function TrialDayHook({
  days,
  totalDays,
  price,
  planId,
  scenario = "default",
  onUnlock,
}: TrialDayHookProps) {
  const cards = HIGHLIGHT_CARDS[scenario] ?? HIGHLIGHT_CARDS.default;
  const rhythm = RHYTHM_GUIDE[scenario] ?? RHYTHM_GUIDE.default;

  // 只展示 2 张卡（避免过度信息）
  const displayCards = cards.slice(0, 2);

  return (
    <motion.div
      variants={staggerContainer}
      initial="initial"
      whileInView="animate"
      viewport={{ once: true, amount: 0.2 }}
      className="space-y-5"
    >
      {/* Section Header */}
      <motion.div variants={fadeInUp} className="flex items-center gap-3">
        <div className="flex-1 h-px bg-stone-200" />
        <p className="text-xs font-semibold text-stone-400 uppercase tracking-widest whitespace-nowrap">
          后续行程预告
        </p>
        <div className="flex-1 h-px bg-stone-200" />
      </motion.div>

      {/* 行程脉络图 */}
      <motion.div variants={fadeInUp}>
        <p className="text-xs text-stone-400 mb-2">📍 你的完整行程脉络</p>
        <JourneyMapStrip days={days} />
      </motion.div>

      {/* 亮点预告卡 */}
      <motion.div variants={fadeInUp}>
        <p className="text-xs text-stone-400 mb-2">✨ 后面你会最喜欢的时刻</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {displayCards.map((card) => (
            <HighlightPreviewCard
              key={card.dayNum}
              card={card}
              onClick={() => onUnlock(`highlight_card_${card.dayNum}`)}
            />
          ))}
        </div>
      </motion.div>

      {/* 节奏引导句 + CTA */}
      <motion.div
        variants={fadeInUp}
        className="rounded-2xl bg-gradient-to-r from-rose-50 to-amber-50 border border-rose-100 p-5 text-center"
      >
        <p className="text-sm font-bold text-stone-800 mb-1 leading-snug">
          {rhythm.headline}
        </p>
        <p className="text-xs text-stone-500 mb-4 leading-relaxed">{rhythm.sub}</p>
        <button
          className="bg-rose-600 hover:bg-rose-700 text-white text-sm px-8 py-2.5 rounded-full font-semibold shadow-md transition-colors"
          onClick={() => onUnlock("rhythm_cta")}
        >
          解锁全部 {totalDays} 天方案 · ¥{price}
        </button>
        <p className="text-xs text-stone-400 mt-2">不满意 7 天内全额退款</p>
      </motion.div>
    </motion.div>
  );
}
