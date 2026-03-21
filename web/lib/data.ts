import { readFileSync } from "fs";
import { join } from "path";

// ── Data directory ──────────────────────────────────────────────────────────
const DATA_DIR = process.env.DATA_DIR || join(process.cwd(), "..", "data", "sakura");

function readJson<T>(filename: string): T {
  const raw = readFileSync(join(DATA_DIR, filename), "utf-8");
  return JSON.parse(raw) as T;
}

// ── Type definitions ────────────────────────────────────────────────────────

export interface Spot {
  name: string;
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
  photo?: string;
  region?: string;
  // extended fields from crawled data
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

const STAGE_TO_BLOOM: Record<string, string | undefined> = {
  "starting": "3分咲",
  "approaching": "5分咲",
  "full_bloom": "満開",
  "falling": "桜吹雪",
  "ended": undefined,
};

// ── Helpers: parse best_viewing to approximate full bloom date ───────────────

function bestViewingToFullDate(bestViewing?: string): string | undefined {
  if (!bestViewing) return undefined;
  // Format: "2026-03-26 ~ 2026-04-02" → use midpoint as full bloom
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
  const raw = readJson<any>("sakura_rush_scores.json");

  // Adapt crawled format → frontend format
  const cities: CityData[] = (raw.cities || []).map((c: any) => {
    const mapped = CITY_NAME_MAP[c.city_name] || { code: c.city_name?.toLowerCase() || "unknown", cn: c.city_name || "未知" };

    const spots: Spot[] = (c.spots || []).map((s: any) => {
      const fullDate = bestViewingToFullDate(s.best_viewing);
      return {
        name: s.name_zh || s.name_ja || s.name || "未知",
        desc_cn: s.desc_cn,
        half: fullDate ? (() => {
          // half bloom ~5 days before full
          const [m, d] = fullDate.split("/").map(Number);
          const dt = new Date(2026, m - 1, d - 5);
          return `${dt.getMonth() + 1}/${dt.getDate()}`;
        })() : undefined,
        full: fullDate,
        fall: fullDate ? (() => {
          const [m, d] = fullDate.split("/").map(Number);
          const dt = new Date(2026, m - 1, d + 7);
          return `${dt.getMonth() + 1}/${dt.getDate()}`;
        })() : undefined,
        trees: undefined,
        lightup: s.nightlit || false,
        meisyo100: false,
        nightview: s.nightlit || false,
        score: s.rush_score || 0,
        photo: undefined, // numeric photo rating, not a URL
        region: undefined,
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

  // Build week label
  const now = new Date();
  const weekNum = Math.ceil(now.getDate() / 7);
  const monthNames = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"];
  const weekLabel = `${monthNames[now.getMonth()]}第${weekNum}周`;

  return {
    updated_at: raw.generated_at || new Date().toISOString().slice(0, 10),
    week_label: weekLabel,
    cities,
  };
}

export function getWeathernewsSpots(): Record<string, Spot[]> {
  return readJson<Record<string, Spot[]>>("weathernews_all_spots.json");
}

export function getSpotsForCity(cityCode: string): Spot[] {
  const all = getWeathernewsSpots();
  return all[cityCode] || [];
}

export function getJmaCities(): { bloom_count: number; cities: JmaCity[] } {
  return readJson("jma/jma_city_truth_2026.json");
}

export function getAllCityCodes(): string[] {
  return Object.keys(getWeathernewsSpots());
}