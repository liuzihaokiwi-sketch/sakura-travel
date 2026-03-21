/**
 * rush-data.ts — 樱花追踪完整数据层
 *
 * 主数据源: weathernews_all_spots.json (240+ 景点)
 * 辅助数据: sakura_rush_scores.json (AI 评分覆盖)
 * 移植旧版 HTML calcScore() 评分算法
 */

import { readFileSync, existsSync } from "fs";
import { join } from "path";

// ── Data directory ──────────────────────────────────────────────────────────

const DATA_DIR = (() => {
  const local = join(process.cwd(), "data", "sakura");
  const parent = join(process.cwd(), "..", "data", "sakura");
  return existsSync(local) ? local : parent;
})();

function readJson<T>(filename: string, fallback: T): T {
  const fp = join(DATA_DIR, filename);
  if (!existsSync(fp)) return fallback;
  try {
    return JSON.parse(readFileSync(fp, "utf-8")) as T;
  } catch {
    return fallback;
  }
}

// ── Types ───────────────────────────────────────────────────────────────────

export interface RushSpot {
  id: string;
  name: string;          // 日文名
  name_cn?: string;      // 中文名
  lat: number;
  lon: number;
  half?: string;         // "3月24日"
  full?: string;         // "3月26日"
  fall?: string;         // "4月1日"
  trees?: string;        // "約800本"
  lightup?: boolean;
  meisyo100?: boolean;
  namiki?: boolean;
  desc?: string;         // 日文描述
  desc_cn?: string;      // 中文描述
  photo?: string;        // URL
  region?: string;       // "上野·文京"
  score: number;         // 0-100 推荐指数
  // 计算字段
  color: string;         // 地图标记颜色
  daysToFull: number | null;
}

export interface RushCity {
  key: string;
  name: string;          // 中文名
  emoji: string;
  status: string;
  center: [number, number];
  zoom: number;
  spots: RushSpot[];
  spotCount: number;
  bloomCount: number;    // 已开花的景点数
  avgScore: number;
}

export interface Landmark {
  name: string;
  emoji: string;
  lat: number;
  lon: number;
}

export interface RushData {
  cities: RushCity[];
  landmarks: Record<string, Landmark[]>;
  updatedAt: string;
  weekLabel: string;
  totalSpots: number;
  // 时间轴常量
  tlStart: string;       // "2026-03-10"
  tlEnd: string;         // "2026-04-25"
}

// ── City config ─────────────────────────────────────────────────────────────

const CITY_CONFIG: Array<{
  key: string;
  name: string;
  emoji: string;
  status: string;
  center: [number, number];
  zoom: number;
}> = [
  { key: "tokyo",     name: "东京",   emoji: "🗼", status: "已开花",    center: [35.69, 139.72], zoom: 12 },
  { key: "kyoto",     name: "京都",   emoji: "⛩",  status: "3/26预计",  center: [35.01, 135.76], zoom: 12 },
  { key: "osaka",     name: "大阪",   emoji: "🏯", status: "3/27预计",  center: [34.68, 135.50], zoom: 11 },
  { key: "aichi",     name: "名古屋", emoji: "🏢", status: "已开花",    center: [35.08, 136.92], zoom: 11 },
  { key: "hiroshima", name: "广岛",   emoji: "☮",  status: "已开花",    center: [34.55, 132.80], zoom: 10 },
];

// ── Landmarks ───────────────────────────────────────────────────────────────

// LANDMARKS_DATA 定义在文件底部的 LANDMARKS 导出中
// getRushData() 中通过 LANDMARKS 引用

// ── Date helpers ────────────────────────────────────────────────────────────

const TL_START = new Date("2026-03-10");
const TL_END   = new Date("2026-04-25");
const TL_DAYS  = (TL_END.getTime() - TL_START.getTime()) / 864e5;

function parseJpDate(s?: string): Date | null {
  if (!s) return null;
  const m = s.match(/(\d+)月(\d+)日/);
  if (!m) return null;
  return new Date(2026, parseInt(m[1]) - 1, parseInt(m[2]));
}

export function datePct(s?: string): number {
  const d = parseJpDate(s);
  if (!d) return 0;
  return Math.max(0, Math.min(100, ((d.getTime() - TL_START.getTime()) / 864e5) / TL_DAYS * 100));
}

export function todayPct(): number {
  const now = new Date();
  return Math.max(0, Math.min(100, ((now.getTime() - TL_START.getTime()) / 864e5) / TL_DAYS * 100));
}

export function fmtDate(s?: string): string {
  if (!s) return "?";
  return s.replace("月", "/").replace("日", "");
}

function daysTo(s?: string): number | null {
  const d = parseJpDate(s);
  if (!d) return null;
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  return Math.round((d.getTime() - now.getTime()) / 864e5);
}

// ── Scoring (移植旧版 calcScore) ────────────────────────────────────────────

function calcScore(s: Record<string, any>): number {
  let sc = 50;

  // 1) 规模 — 树的数量
  let treeNum = 0;
  if (s.trees) {
    const m = String(s.trees).match(/(\d+)/);
    if (m) treeNum = parseInt(m[1]);
  }
  if (treeNum >= 3000) sc += 25;
  else if (treeNum >= 1500) sc += 22;
  else if (treeNum >= 1000) sc += 20;
  else if (treeNum >= 500) sc += 15;
  else if (treeNum >= 200) sc += 10;
  else if (treeNum >= 100) sc += 6;
  else if (treeNum >= 30) sc += 3;

  // 2) 名所100选
  if (s.meisyo100) sc += 15;

  // 3) 夜樱灯光
  if (s.lightup) sc += 5;

  // 4) 樱花并木道
  if (s.namiki) sc += 3;

  // 5) 有实景照片
  if (s.photo) sc += 3;

  // 6) 有详细描述
  if (s.desc && s.desc.length > 50) sc += 4;
  else if (s.desc && s.desc.length > 0) sc += 2;

  // 7) 花期窗口长
  const halfD = parseJpDate(s.half);
  const fallD = parseJpDate(s.fall);
  if (halfD && fallD) {
    const span = Math.round((fallD.getTime() - halfD.getTime()) / 864e5);
    if (span >= 10) sc += 5;
    else if (span >= 7) sc += 3;
  }

  return Math.min(100, sc);
}

// ── Color (移植旧版 getColor) ───────────────────────────────────────────────

function getSpotColor(s: Record<string, any>): string {
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  const nowT = now.getTime();
  const halfD = parseJpDate(s.half);
  const fullD = parseJpDate(s.full);
  const fallD = parseJpDate(s.fall);

  if (fallD && nowT > fallD.getTime())        return "#9c27b0";   // 紫色 = 飘落
  if (fullD && nowT >= fullD.getTime())        return "#c2185b";   // 深粉 = 满开
  if (halfD && nowT >= halfD.getTime())        return "#e91e63";   // 粉红 = 开花中
  if (halfD && nowT >= halfD.getTime() - 3 * 864e5) return "#f48fb1"; // 浅粉 = 3天内
  if (halfD && nowT >= halfD.getTime() - 7 * 864e5) return "#f8bbd0"; // 更浅 = 7天内
  return "#81c784";                                                  // 绿色 = 花苞
}

// ── Build AI score lookup ───────────────────────────────────────────────────

function buildAiScoreLookup(): Record<string, number> {
  const raw = readJson<any>("sakura_rush_scores.json", { cities: [] });
  const lookup: Record<string, number> = {};
  for (const c of raw.cities || []) {
    for (const s of c.spots || []) {
      if (s.name_ja && s.rush_score) {
        lookup[s.name_ja] = s.rush_score;
      }
    }
  }
  return lookup;
}

// ── Main data loader ────────────────────────────────────────────────────────

let _cache: RushData | null = null;

export function getRushData(): RushData {
  if (_cache) return _cache;

  const wnData = readJson<Record<string, any[]>>("weathernews_all_spots.json", {});
  const aiScores = buildAiScoreLookup();

  let totalSpots = 0;

  const cities: RushCity[] = CITY_CONFIG.map((cfg) => {
    const rawSpots = wnData[cfg.key] || [];

    const spots: RushSpot[] = rawSpots.map((s: any, i: number) => {
      // AI 评分优先，fallback 到算法评分
      const aiScore = aiScores[s.name];
      const score = aiScore || calcScore(s);
      const color = getSpotColor(s);
      const dtf = daysTo(s.full);

      return {
        id: s.id || `${cfg.key}-${i}`,
        name: s.name || "未知",
        name_cn: s.desc_cn ? undefined : undefined,  // weathernews 没有单独中文名字段
        lat: s.lat || 0,
        lon: s.lon || 0,
        half: s.half,
        full: s.full,
        fall: s.fall,
        trees: s.trees,
        lightup: !!s.lightup,
        meisyo100: !!s.meisyo100,
        namiki: !!s.namiki,
        desc: s.desc,
        desc_cn: s.desc_cn,
        photo: s.photo,
        region: s.region || "其他",
        score,
        color,
        daysToFull: dtf,
      };
    });

    // Sort by score desc
    spots.sort((a, b) => b.score - a.score);
    totalSpots += spots.length;

    const bloomCount = spots.filter((s) => {
      const fullD = parseJpDate(s.full);
      if (!fullD) return false;
      return new Date() >= fullD;
    }).length;

    const avgScore = spots.length > 0
      ? Math.round(spots.reduce((sum, s) => sum + s.score, 0) / spots.length)
      : 0;

    return {
      ...cfg,
      spots,
      spotCount: spots.length,
      bloomCount,
      avgScore,
    };
  });

  const now = new Date();
  const weekNum = Math.ceil(now.getDate() / 7);
  const monthNames = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"];

  _cache = {
    cities,
    landmarks: LANDMARKS,
    updatedAt: new Date().toISOString().slice(0, 10),
    weekLabel: `${monthNames[now.getMonth()]}第${weekNum}周`,
    totalSpots,
    tlStart: "2026-03-10",
    tlEnd: "2026-04-25",
  };

  return _cache;
}

// ── Helpers for components ──────────────────────────────────────────────────

/** 获取景点推荐理由列表 */
export function getSpotReasons(s: RushSpot): string[] {
  const reasons: string[] = [];
  let treeNum = 0;
  if (s.trees) {
    const m = String(s.trees).match(/(\d+)/);
    if (m) treeNum = parseInt(m[1]);
  }
  if (s.meisyo100) reasons.push("🏆 日本樱花名所100选");
  if (treeNum >= 1000) reasons.push(`🌳 ${s.trees}樱花树，规模壮观`);
  else if (treeNum >= 500) reasons.push(`🌳 ${s.trees}樱花树`);
  if (s.lightup) reasons.push("🌙 有夜樱灯光");

  const halfD = parseJpDate(s.half);
  const fallD = parseJpDate(s.fall);
  if (halfD && fallD) {
    const span = Math.round((fallD.getTime() - halfD.getTime()) / 864e5);
    if (span >= 10) reasons.push(`🗓 花期长达${span}天`);
  }
  return reasons.slice(0, 3);
}

/** 按区域分组景点 */
export function groupByRegion(spots: RushSpot[]): Array<{ region: string; spots: RushSpot[] }> {
  const map = new Map<string, RushSpot[]>();
  for (const s of spots) {
    const r = s.region || "其他";
    if (!map.has(r)) map.set(r, []);
    map.get(r)!.push(s);
  }
  return Array.from(map.entries()).map(([region, spots]) => ({ region, spots }));
}

/** 格式化倒计时 */
export function fmtCountdown(days: number | null): string {
  if (days === null) return "";
  if (days > 0) return `${days}天后`;
  if (days === 0) return "🎉 今天!";
  return `已过${Math.abs(days)}天`;
}

/** 格式化倒计时带样式类名 */
export function countdownColor(days: number | null): string {
  if (days === null) return "text-stone-400";
  if (days > 0) return "text-pink-600 font-semibold";
  if (days === 0) return "text-pink-600 font-bold";
  return "text-purple-600";
}

// ── M5: CITIES & LANDMARKS 静态配置（从旧版 sakura_rush.html 迁移）────────

export interface CityConfig {
  key: string;
  name: string;
  emoji: string;
  status: string;
  center: [number, number]; // [lat, lon]
  zoom: number;
}

export const CITIES: CityConfig[] = [
  { key: "tokyo",     name: "东京",   emoji: "🗼", status: "已开花",   center: [35.69, 139.72], zoom: 12 },
  { key: "kyoto",     name: "京都",   emoji: "⛩",  status: "3/26预计", center: [35.01, 135.76], zoom: 12 },
  { key: "osaka",     name: "大阪",   emoji: "🏯", status: "3/27预计", center: [34.68, 135.50], zoom: 11 },
  { key: "aichi",     name: "名古屋", emoji: "🏢", status: "已开花",   center: [35.08, 136.92], zoom: 11 },
  { key: "hiroshima", name: "广岛",   emoji: "☮",  status: "已开花",   center: [34.55, 132.80], zoom: 10 },
];

export const LANDMARKS: Record<string, Landmark[]> = {
  tokyo: [
    { name: "东京站", emoji: "🚉", lat: 35.6812, lon: 139.7671 },
    { name: "新宿站", emoji: "🚉", lat: 35.6896, lon: 139.7006 },
    { name: "涩谷站", emoji: "🚉", lat: 35.6580, lon: 139.7016 },
    { name: "上野站", emoji: "🚉", lat: 35.7141, lon: 139.7774 },
    { name: "东京塔", emoji: "🗼", lat: 35.6586, lon: 139.7454 },
    { name: "晴空塔", emoji: "🏙️", lat: 35.7101, lon: 139.8107 },
    { name: "皇居",   emoji: "🏯", lat: 35.6852, lon: 139.7528 },
    { name: "浅草寺", emoji: "🛕", lat: 35.7148, lon: 139.7967 },
  ],
  kyoto: [
    { name: "京都站",   emoji: "🚉", lat: 35.0116, lon: 135.7681 },
    { name: "金阁寺",   emoji: "🛕", lat: 35.0394, lon: 135.7292 },
    { name: "伏见稻荷", emoji: "⛩️", lat: 34.9671, lon: 135.7727 },
    { name: "二条城",   emoji: "🏯", lat: 35.0142, lon: 135.7489 },
    { name: "祇园",     emoji: "🏮", lat: 35.0037, lon: 135.7756 },
  ],
  osaka: [
    { name: "大阪站",   emoji: "🚉", lat: 34.7024, lon: 135.4959 },
    { name: "难波站",   emoji: "🚉", lat: 34.6629, lon: 135.5014 },
    { name: "大阪城",   emoji: "🏯", lat: 34.6873, lon: 135.5262 },
    { name: "通天阁",   emoji: "🗼", lat: 34.6526, lon: 135.5064 },
    { name: "关西机场", emoji: "✈️", lat: 34.4320, lon: 135.2440 },
  ],
  aichi: [
    { name: "名古屋站", emoji: "🚉", lat: 35.1709, lon: 136.8815 },
    { name: "名古屋城", emoji: "🏯", lat: 35.1855, lon: 136.8990 },
    { name: "热田神宫", emoji: "⛩️", lat: 35.1277, lon: 136.9087 },
    { name: "中部机场", emoji: "✈️", lat: 34.8583, lon: 136.8124 },
  ],
  hiroshima: [
    { name: "广岛站",   emoji: "🚉", lat: 34.3963, lon: 132.4752 },
    { name: "原爆圆顶", emoji: "🕊️", lat: 34.3955, lon: 132.4536 },
    { name: "严岛神社", emoji: "⛩️", lat: 34.2960, lon: 132.3198 },
    { name: "广岛城",   emoji: "🏯", lat: 34.4017, lon: 132.4597 },
  ],
};

export function getCityConfig(key: string): CityConfig | undefined {
  return CITIES.find((c) => c.key === key);
}
