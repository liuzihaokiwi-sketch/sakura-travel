import { readFileSync, existsSync } from "fs";
import { join } from "path";

// ── Data directory ──────────────────────────────────────────────────────────
// Vercel 上 cwd 是 web/，所以 ../data/sakura 找不到
// 优先用 web/data/sakura（Vercel），fallback 到 ../data/sakura（本地开发）
const DATA_DIR = process.env.DATA_DIR || (() => {
  const local = join(process.cwd(), "data", "sakura");
  const parent = join(process.cwd(), "..", "data", "sakura");
  return existsSync(local) ? local : parent;
})();

function readJson<T>(filename: string, fallback: T): T {
  const fp = join(DATA_DIR, filename);
  if (!existsSync(fp)) return fallback;
  try {
    const raw = readFileSync(fp, "utf-8");
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

// ── Type definitions ────────────────────────────────────────────────────────

export interface Spot {
  name: string;
  name_ja?: string;
  desc_cn?: string;
  half?: string;
  full?: string;
  fall?: string;
  trees?: string;
  lightup?: boolean;
  meisyo100?: boolean;
  namiki?: boolean;
  nightview?: boolean;
  score: number;
  photo?: string;       // URL 字符串
  region?: string;
  stage?: string;
  festival?: string;
  crowd?: string;
  best_viewing?: string;
  good_for?: string[];
}

export interface CityData {
  city_code: string;
  city_name_cn: string;
  city_name_ja?: string;
  spots: Spot[];
}

export interface RushScores {
  updated_at: string;
  week_label: string;
  cities: CityData[];
}

export interface JmaCity {
  name: string;
  bloom_date?: string;
  full_bloom_date?: string;
}

// ── City name mapping ───────────────────────────────────────────────────────

const CITY_NAME_MAP: Record<string, { code: string; cn: string }> = {
  "東京": { code: "tokyo", cn: "东京" },
  "京都": { code: "kyoto", cn: "京都" },
  "大阪": { code: "osaka", cn: "大阪" },
  "福岡": { code: "fukuoka", cn: "福冈" },
  "札幌": { code: "sapporo", cn: "札幌" },
  "名古屋": { code: "nagoya", cn: "名古屋" },
  "広島": { code: "hiroshima", cn: "广岛" },
  "仙台": { code: "sendai", cn: "仙台" },
  "鹿児島": { code: "kagoshima", cn: "鹿儿岛" },
  "静岡": { code: "shizuoka", cn: "静冈" },
};

// ── Build enrichment lookup from weathernews data ───────────────────────────

interface WnEnrichment {
  photo?: string;
  trees?: string;
  region?: string;
  desc?: string;
  namiki?: boolean;
  meisyo100?: boolean;
  half?: string;
  full?: string;
  fall?: string;
}

function buildWnLookup(): Record<string, WnEnrichment> {
  const wnData = readJson<Record<string, any[]>>("weathernews_all_spots.json", {});
  const lookup: Record<string, WnEnrichment> = {};
  for (const spots of Object.values(wnData)) {
    for (const s of spots) {
      if (!s.name) continue;
      lookup[s.name] = {
        photo: typeof s.photo === "string" ? s.photo : undefined,
        trees: s.trees,
        region: s.region,
        desc: s.desc,
        namiki: s.namiki,
        meisyo100: s.meisyo100,
        half: s.half,
        full: s.full,
        fall: s.fall,
      };
    }
  }
  return lookup;
}

let _wnLookup: Record<string, WnEnrichment> | null = null;
function getWnLookup(): Record<string, WnEnrichment> {
  if (!_wnLookup) _wnLookup = buildWnLookup();
  return _wnLookup;
}

// ── Helpers ─────────────────────────────────────────────────────────────────

function bestViewingToFullDate(bestViewing?: string): string | undefined {
  if (!bestViewing) return undefined;
  const parts = bestViewing.split("~").map((s) => s.trim());
  if (parts.length < 2) return undefined;
  const start = new Date(parts[0]);
  const end = new Date(parts[1]);
  if (isNaN(start.getTime()) || isNaN(end.getTime())) return undefined;
  const mid = new Date((start.getTime() + end.getTime()) / 2);
  return `${mid.getMonth() + 1}/${mid.getDate()}`;
}

// ── Data loaders ────────────────────────────────────────────────────────────

export function getRushScores(): RushScores {
  const raw = readJson<any>("sakura_rush_scores.json", { cities: [] });
  const wnLookup = getWnLookup();

  const cities: CityData[] = (raw.cities || []).map((c: any) => {
    const mapped = CITY_NAME_MAP[c.city_name] || {
      code: c.city_name?.toLowerCase() || "unknown",
      cn: c.city_name || "未知",
    };

    const spots: Spot[] = (c.spots || []).map((s: any) => {
      // 用日文名从 weathernews 补全字段
      const wn = wnLookup[s.name_ja] || {};

      return {
        name: s.name_zh || s.name_ja || s.name || "未知",
        name_ja: s.name_ja,
        desc_cn: s.desc_cn,
        half: wn.half || undefined,
        full: wn.full || undefined,
        fall: wn.fall || undefined,
        trees: wn.trees,
        lightup: s.nightlit || false,
        meisyo100: wn.meisyo100 || false,
        namiki: wn.namiki || false,
        nightview: s.nightlit || false,
        score: s.rush_score || 0,
        photo: wn.photo,
        region: wn.region,
        stage: s.stage,
        festival: s.festival,
        crowd: s.crowd,
        best_viewing: s.best_viewing,
        good_for: s.good_for,
      } satisfies Spot;
    });

    return {
      city_code: mapped.code,
      city_name_cn: mapped.cn,
      city_name_ja: c.city_name,
      spots,
    } satisfies CityData;
  });

  const now = new Date();
  const weekNum = Math.ceil(now.getDate() / 7);
  const monthNames = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"];

  return {
    updated_at: raw.generated_at || new Date().toISOString().slice(0, 10),
    week_label: `${monthNames[now.getMonth()]}第${weekNum}周`,
    cities,
  };
}

export function getWeathernewsSpots(): Record<string, Spot[]> {
  return readJson<Record<string, Spot[]>>("weathernews_all_spots.json", {});
}

export function getSpotsForCity(cityCode: string): Spot[] {
  const all = getWeathernewsSpots();
  return all[cityCode] || [];
}

export function getJmaCities(): { bloom_count: number; cities: JmaCity[] } {
  return readJson("jma/jma_city_truth_2026.json", { bloom_count: 0, cities: [] });
}

export function getAllCityCodes(): string[] {
  return Object.keys(getWeathernewsSpots());
}