import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export interface TemplateSlot {
  slot_id: string;
  time_range: string | null;
  type: string;
  area?: string;
  priority?: string;
  duration_min?: number;
  entity_hint?: string;
  note?: string;
}

export interface TemplateAssembly {
  phase: string;
  best_pace: string;
  span_days?: number;
}

export interface DayTemplate {
  template_id: string;
  label: string;
  city: string;
  circle: string;
  tags: string[];
  core_entities: string[];
  fit_audience: string | string[];
  weather_sensitive: boolean;
  condition?: string | null;
  assembly: TemplateAssembly;
  description: string;
  hotel_area_note?: string;
  slots?: TemplateSlot[];
  days?: TemplateSlot[][];
}

const CONTENT_DIR = path.join(process.cwd(), "..", "content");

function loadAreas(): Record<string, string> {
  const areas: Record<string, string> = {};
  if (!fs.existsSync(CONTENT_DIR)) return areas;
  for (const circle of fs.readdirSync(CONTENT_DIR)) {
    const circleDir = path.join(CONTENT_DIR, circle);
    if (!fs.statSync(circleDir).isDirectory()) continue;
    for (const city of fs.readdirSync(circleDir)) {
      const metaPath = path.join(circleDir, city, "days", "_meta.json");
      if (!fs.existsSync(metaPath)) continue;
      try {
        const meta = JSON.parse(fs.readFileSync(metaPath, "utf-8"));
        Object.assign(areas, meta._areas ?? {});
      } catch { /* skip */ }
    }
  }
  return areas;
}

function loadTemplates(): DayTemplate[] {
  const templates: DayTemplate[] = [];
  if (!fs.existsSync(CONTENT_DIR)) return templates;

  for (const circle of fs.readdirSync(CONTENT_DIR)) {
    const circleDir = path.join(CONTENT_DIR, circle);
    if (!fs.statSync(circleDir).isDirectory()) continue;

    for (const city of fs.readdirSync(circleDir)) {
      const daysDir = path.join(circleDir, city, "days");
      if (!fs.existsSync(daysDir) || !fs.statSync(daysDir).isDirectory()) continue;

      for (const file of fs.readdirSync(daysDir)) {
        if (!file.endsWith(".json") || file.startsWith("_")) continue;
        try {
          const raw = fs.readFileSync(path.join(daysDir, file), "utf-8");
          const tmpl = JSON.parse(raw) as DayTemplate;
          tmpl.city = city;
          tmpl.circle = circle;
          templates.push(tmpl);
        } catch {
          // skip malformed files
        }
      }
    }
  }

  return templates;
}

export async function GET() {
  const templates = loadTemplates();
  const areas = loadAreas();
  return NextResponse.json({ templates, total: templates.length, areas });
}
