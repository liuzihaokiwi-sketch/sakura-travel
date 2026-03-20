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

// ── Data loaders ────────────────────────────────────────────────────────────

export function getRushScores(): RushScores {
  return readJson<RushScores>("sakura_rush_scores.json");
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
