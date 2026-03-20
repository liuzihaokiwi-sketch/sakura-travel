/**
 * Playwright 全页截图导出脚本
 *
 * Usage:
 *   npx tsx scripts/export-playwright.ts --url /rush --width 1080 --height 1440 --output output/rush.png
 *   npx tsx scripts/export-playwright.ts --url /custom --width 1080 --height 1080 --output output/custom.png
 */

import { chromium } from "playwright";
import { mkdirSync, existsSync } from "fs";
import { dirname, resolve } from "path";

// ── Parse CLI args ──────────────────────────────────────────────────────────

function parseArgs() {
  const args = process.argv.slice(2);
  const parsed: Record<string, string> = {};

  for (let i = 0; i < args.length; i += 2) {
    const key = args[i].replace(/^--/, "");
    parsed[key] = args[i + 1];
  }

  return {
    url: parsed.url || "/",
    width: parseInt(parsed.width || "1080", 10),
    height: parseInt(parsed.height || "1440", 10),
    output: parsed.output || "output/screenshot.png",
    baseUrl: parsed.baseUrl || "http://localhost:3000",
  };
}

// ── Main ────────────────────────────────────────────────────────────────────

async function main() {
  const opts = parseArgs();
  const fullUrl = `${opts.baseUrl}${opts.url}${opts.url.includes("?") ? "&" : "?"}export=true`;
  const outputPath = resolve(opts.output);

  // Ensure output directory exists
  const dir = dirname(outputPath);
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }

  console.log(`📸 Capturing: ${fullUrl}`);
  console.log(`   Size: ${opts.width}×${opts.height}`);
  console.log(`   Output: ${outputPath}`);

  const browser = await chromium.launch();
  const page = await browser.newPage();

  await page.setViewportSize({
    width: opts.width,
    height: opts.height,
  });

  // Navigate and wait for network idle
  await page.goto(fullUrl, { waitUntil: "networkidle" });

  // Wait a bit for fonts & images
  await page.waitForTimeout(1500);

  // Screenshot (clip to viewport, no full page scroll)
  await page.screenshot({
    path: outputPath,
    fullPage: false,
    type: "png",
  });

  await browser.close();
  console.log(`✅ Saved: ${outputPath}`);
}

main().catch((err) => {
  console.error("❌ Export failed:", err);
  process.exit(1);
});
