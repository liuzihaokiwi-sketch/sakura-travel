/**
 * Satori 批量社交卡片生成脚本 v2
 *
 * Usage:
 *   npx tsx scripts/export-satori.ts --all --output output/xhs/
 *   npx tsx scripts/export-satori.ts --template xhs-cover --output output/xhs/
 *   npx tsx scripts/export-satori.ts --template xhs-spot --city tokyo --output output/xhs/
 *   npx tsx scripts/export-satori.ts --template xhs-spot --city tokyo --spot "上野恩賜公園" --output output/xhs/
 */

import { writeFileSync, mkdirSync, existsSync } from "fs";
import { join, resolve } from "path";
import { renderToPng, SIZES } from "../lib/satori";
import { getWeathernewsSpots, type Spot } from "../lib/data";
import { batchFetchPhotos } from "../lib/photo-cache";
import { CITY_NAMES } from "../lib/card-colors";
import {
  createXhsCoverElement,
  createXhsSpotElement,
  createXhsCompareElement,
  createMomentElement,
  createXhsStoryElement,
  type TemplateData,
} from "../lib/card-templates";

// ── CLI argument parser ─────────────────────────────────────────────────────

function parseArgs() {
  const args = process.argv.slice(2);
  const parsed: Record<string, string> = {};
  let allMode = false;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--all") {
      allMode = true;
    } else if (args[i].startsWith("--") && i + 1 < args.length) {
      parsed[args[i].replace(/^--/, "")] = args[i + 1];
      i++;
    }
  }

  return {
    template: parsed.template || (allMode ? "all" : "xhs-cover"),
    city: parsed.city || undefined,
    spot: parsed.spot || undefined,
    output: parsed.output || "output/cards/",
    all: allMode,
  };
}

// ── Template size map ───────────────────────────────────────────────────────

const TEMPLATE_SIZES: Record<string, { width: number; height: number }> = {
  "xhs-cover": SIZES.XHS,
  "xhs-spot": SIZES.XHS,
  "xhs-compare": SIZES.XHS,
  "wechat-moment": SIZES.MOMENT,
  "xhs-story": SIZES.STORY,
};

const ALL_TEMPLATES = ["xhs-cover", "xhs-spot", "xhs-compare", "wechat-moment", "xhs-story"];

// ── Main ────────────────────────────────────────────────────────────────────

async function main() {
  const opts = parseArgs();
  const outputDir = resolve(opts.output);

  if (!existsSync(outputDir)) mkdirSync(outputDir, { recursive: true });

  console.log(`\n🎨 XHS Social Cards v2`);
  console.log(`📁 Output: ${outputDir}`);
  console.log(`🔧 Template: ${opts.all ? "ALL" : opts.template}`);
  if (opts.city) console.log(`🏙️  City: ${opts.city}`);
  if (opts.spot) console.log(`📍 Spot: ${opts.spot}`);
  console.log("");

  // Load spot data
  const allSpots = getWeathernewsSpots();
  const cities = opts.city ? [opts.city] : Object.keys(allSpots);

  // Build TemplateData for each city
  const allTemplateData: TemplateData[] = [];

  for (const city of cities) {
    const spots = allSpots[city];
    if (!spots || spots.length === 0) continue;

    const sorted = [...spots].sort((a, b) => (b.score || 0) - (a.score || 0));
    const topSpots = sorted.slice(0, 10); // Fetch photos for top 10

    console.log(`📷 Fetching photos for ${CITY_NAMES[city] || city} (top ${topSpots.length} spots)...`);
    const photoBuffers = await batchFetchPhotos(topSpots);
    console.log(`   ✅ Cached ${Object.keys(photoBuffers).length} photos\n`);

    allTemplateData.push({
      city,
      cityName: CITY_NAMES[city] || city,
      spots: sorted,
      photoBuffers,
      updatedAt: new Date().toLocaleDateString("zh-CN"),
    });
  }

  // Determine which templates to generate
  const templates = opts.all ? ALL_TEMPLATES : [opts.template];
  let count = 0;

  for (const tmpl of templates) {
    const size = TEMPLATE_SIZES[tmpl];
    if (!size) {
      console.warn(`  ⚠️ Unknown template: ${tmpl}`);
      continue;
    }

    if (tmpl === "xhs-compare") {
      // Compare uses all cities at once
      console.log(`  🖼️  Generating ${tmpl}...`);
      const element = createXhsCompareElement(allTemplateData);
      const png = await renderToPng(element, size);
      const path = join(outputDir, `compare_all_cities.png`);
      writeFileSync(path, png);
      console.log(`     ✅ ${path}`);
      count++;
      continue;
    }

    for (const data of allTemplateData) {
      if (tmpl === "xhs-spot") {
        // Generate for specific spot or top 3
        if (opts.spot) {
          const idx = data.spots.findIndex((s) => s.name === opts.spot);
          if (idx === -1) continue;
          console.log(`  🖼️  Generating ${tmpl} — ${data.cityName} / ${opts.spot}...`);
          const element = createXhsSpotElement(data, idx);
          const png = await renderToPng(element, size);
          const safeName = opts.spot.replace(/[^a-zA-Z0-9\u4e00-\u9fff]/g, "_");
          const path = join(outputDir, `${data.city}_spot_${safeName}.png`);
          writeFileSync(path, png);
          console.log(`     ✅ ${path}`);
          count++;
        } else {
          // Top 3 spots
          const top = Math.min(3, data.spots.length);
          for (let i = 0; i < top; i++) {
            const spot = data.spots[i];
            console.log(`  🖼️  Generating ${tmpl} — ${data.cityName} / ${spot.name}...`);
            const element = createXhsSpotElement(data, i);
            const png = await renderToPng(element, size);
            const safeName = spot.name.replace(/[^a-zA-Z0-9\u4e00-\u9fff]/g, "_");
            const path = join(outputDir, `${data.city}_spot_${safeName}.png`);
            writeFileSync(path, png);
            console.log(`     ✅ ${path}`);
            count++;
          }
        }
      } else {
        // xhs-cover, wechat-moment, xhs-story
        console.log(`  🖼️  Generating ${tmpl} — ${data.cityName}...`);
        let element;
        if (tmpl === "xhs-cover") element = createXhsCoverElement(data);
        else if (tmpl === "wechat-moment") element = createMomentElement(data);
        else if (tmpl === "xhs-story") element = createXhsStoryElement(data);
        else continue;

        const png = await renderToPng(element, size);
        const path = join(outputDir, `${data.city}_${tmpl.replace("xhs-", "").replace("wechat-", "")}.png`);
        writeFileSync(path, png);
        console.log(`     ✅ ${path}`);
        count++;
      }
    }
  }

  console.log(`\n🎉 Done! Generated ${count} cards in ${outputDir}\n`);
}

main().catch((err) => {
  console.error("❌ Export failed:", err);
  process.exit(1);
});