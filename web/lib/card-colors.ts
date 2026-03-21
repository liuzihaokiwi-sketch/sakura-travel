/**
 * Unified card color system & bloom utilities for Satori templates.
 * Mirrors the /rush page Tailwind warm palette.
 */

import type { Spot } from "./data";

// ── Brand palette ───────────────────────────────────────────────────────────

export const C = {
  bgPrimary: "#fefaf6",       // warm-50
  bgDark: "#1c1917",          // stone-900
  bgDarkSoft: "#292524",      // stone-800
  textPrimary: "#1c1917",     // stone-900
  textSecondary: "#78716c",   // stone-500
  textMuted: "#a8a29e",       // stone-400
  textLight: "#d6d3d1",       // stone-300
  accent: "#f7931e",          // warm-500 / brand orange
  accentLight: "#fff7ed",     // warm-50 tinted
  divider: "#e7e5e4",         // stone-200
  white: "#ffffff",
  black: "#000000",

  bloomFull: "#ec4899",       // pink-500
  bloomHalf: "#22c55e",       // green-500
  bloomStart: "#a3e635",      // lime-400
  bloomFall: "#f59e0b",       // amber-500
  bloomDormant: "#a8a29e",    // stone-400
} as const;

// ── Bloom stage helpers ─────────────────────────────────────────────────────

export interface BloomInfo {
  label: string;
  labelCn: string;
  color: string;
  emoji: string;
}

export function getBloomInfo(spot: Spot): BloomInfo {
  if (spot.stage === "full_bloom" || spot.full) {
    return { label: "満開", labelCn: "满开", color: C.bloomFull, emoji: "✿" };
  }
  if (spot.stage === "approaching" || spot.half) {
    return { label: "五分咲", labelCn: "五分咲", color: C.bloomHalf, emoji: "❀" };
  }
  if (spot.stage === "starting") {
    return { label: "三分咲", labelCn: "三分咲", color: C.bloomStart, emoji: "❀" };
  }
  if (spot.stage === "falling") {
    return { label: "散り始め", labelCn: "散落", color: C.bloomFall, emoji: "〜" };
  }
  return { label: "未開", labelCn: "未开", color: C.bloomDormant, emoji: "○" };
}

// ── CTA & Brand text ────────────────────────────────────────────────────────

export const BRAND = {
  title: "SAKURA RUSH 2026",
  subtitle: "6大数据源融合",
  ctaPrimary: "✿ 关注我，获取每日花期更新",
  ctaSecondary: `私信"樱花"获取完整景点推荐 →`,
  sources: "JMA · JMC · Weathernews · 地方官方 · 历史 · AI引擎",
} as const;

// ── City display names ──────────────────────────────────────────────────────

export const CITY_NAMES: Record<string, string> = {
  tokyo: "东京",
  kyoto: "京都",
  osaka: "大阪",
  aichi: "爱知",
  hiroshima: "广岛",
};
