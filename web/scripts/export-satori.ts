/**
 * Satori 批量社交卡片生成脚本
 *
 * Usage:
 *   npx tsx scripts/export-satori.ts --template xhs-cover --output output/xhs/
 *   npx tsx scripts/export-satori.ts --template moment --output output/moments/
 *   npx tsx scripts/export-satori.ts --template xhs-content --output output/xhs-content/
 */

import { writeFileSync, mkdirSync, existsSync } from "fs";
import { join, resolve } from "path";
import React from "react";
import { renderToPng, SIZES } from "../lib/satori";
import { getWeathernewsSpots, type Spot } from "../lib/data";

// ── Parse CLI args ──────────────────────────────────────────────────────────

function parseArgs() {
  const args = process.argv.slice(2);
  const parsed: Record<string, string> = {};

  for (let i = 0; i < args.length; i += 2) {
    const key = args[i].replace(/^--/, "");
    parsed[key] = args[i + 1];
  }

  return {
    template: parsed.template || "xhs-cover",
    output: parsed.output || "output/cards/",
  };
}

// ── City display names ──────────────────────────────────────────────────────

const CITY_NAMES: Record<string, string> = {
  tokyo: "东京",
  kyoto: "京都",
  osaka: "大阪",
  aichi: "爱知",
  hiroshima: "广岛",
};

// ── Template renderers ──────────────────────────────────────────────────────

function createCoverElement(city: string, spots: Spot[]): React.ReactElement {
  const top3 = spots.slice(0, 3);
  return React.createElement(
    "div",
    {
      style: {
        display: "flex",
        flexDirection: "column",
        width: "100%",
        height: "100%",
        background: "linear-gradient(180deg, #1a0a0f 0%, #2d1525 100%)",
        padding: "60px",
        fontFamily: "Noto Sans SC",
      },
    },
    // Title
    React.createElement(
      "div",
      { style: { display: "flex", flexDirection: "column", alignItems: "center", marginBottom: "40px" } },
      React.createElement("div", { style: { fontSize: "48px", fontWeight: 900, color: "white" } }, "2026 樱花季"),
      React.createElement("div", { style: { fontSize: "32px", color: "#f8bbd0", marginTop: "12px" } }, `${CITY_NAMES[city] || city} · TOP 赏樱地`)
    ),
    // Spot list
    React.createElement(
      "div",
      { style: { display: "flex", flexDirection: "column", flex: 1, gap: "24px" } },
      ...top3.map((spot, i) =>
        React.createElement(
          "div",
          {
            key: i,
            style: {
              display: "flex",
              alignItems: "center",
              background: "rgba(255,255,255,0.1)",
              borderRadius: "16px",
              padding: "24px",
              gap: "24px",
            },
          },
          React.createElement("div", { style: { fontSize: "64px", fontWeight: 900, color: "#f7931e", width: "80px" } }, `${i + 1}`),
          React.createElement(
            "div",
            { style: { display: "flex", flexDirection: "column", flex: 1 } },
            React.createElement("div", { style: { fontSize: "28px", color: "white", fontWeight: 700 } }, spot.name),
            React.createElement("div", { style: { fontSize: "22px", color: "#f8bbd0", marginTop: "8px" } }, `满开: ${spot.full || "待定"}`),
          ),
          React.createElement(
            "div",
            { style: { display: "flex", background: "#f7931e", borderRadius: "12px", padding: "8px 16px" } },
            React.createElement("div", { style: { fontSize: "24px", color: "white", fontWeight: 700 } }, `${spot.score}分`)
          )
        )
      )
    ),
    // Footer
    React.createElement(
      "div",
      { style: { display: "flex", flexDirection: "column", alignItems: "center", borderTop: "1px solid rgba(255,255,255,0.1)", paddingTop: "30px", marginTop: "20px" } },
      React.createElement("div", { style: { fontSize: "24px", color: "#f8bbd0" } }, "📊 4大权威数据源融合"),
      React.createElement("div", { style: { fontSize: "20px", color: "rgba(255,255,255,0.5)", marginTop: "8px" } }, "🌸 每天3次更新 · 240+景点覆盖"),
      React.createElement("div", { style: { fontSize: "28px", color: "#f7931e", fontWeight: 700, marginTop: "16px" } }, "关注获取完整榜单 ↑"),
      React.createElement("div", { style: { fontSize: "16px", color: "rgba(255,255,255,0.2)", marginTop: "12px" } }, "数据融合自 JMA · JMC · Weathernews · 地方官方")
    )
  );
}

function createMomentElement(spot: Spot, city: string): React.ReactElement {
  return React.createElement(
    "div",
    {
      style: {
        display: "flex",
        flexDirection: "column",
        width: "100%",
        height: "100%",
        fontFamily: "Noto Sans SC",
      },
    },
    // Top half
    React.createElement(
      "div",
      {
        style: {
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          flex: "55",
          background: "linear-gradient(180deg, #1a0a0f 0%, #2d1525 100%)",
          padding: "40px",
        },
      },
      React.createElement("div", { style: { fontSize: "56px", fontWeight: 900, color: "white" } }, spot.name),
      React.createElement("div", { style: { fontSize: "28px", color: "rgba(255,255,255,0.6)", marginTop: "8px" } }, spot.desc_cn || CITY_NAMES[city]),
      React.createElement("div", { style: { fontSize: "120px", fontWeight: 900, color: "#f7931e", marginTop: "20px" } }, `${spot.score}`),
      React.createElement("div", { style: { fontSize: "32px", color: "rgba(255,255,255,0.3)" } }, "/100")
    ),
    // Bottom half
    React.createElement(
      "div",
      {
        style: {
          display: "flex",
          flexDirection: "column",
          flex: "45",
          background: "#fefaf6",
          padding: "40px",
        },
      },
      React.createElement(
        "div",
        { style: { display: "flex", flexWrap: "wrap", gap: "20px", marginBottom: "30px" } },
        React.createElement("div", { style: { display: "flex", fontSize: "22px", color: "#44403c" } }, `🌸 满开: ${spot.full || "待定"}`),
        React.createElement("div", { style: { display: "flex", fontSize: "22px", color: "#44403c" } }, `🌳 樱花树: ${spot.trees || "未知"}`),
        React.createElement("div", { style: { display: "flex", fontSize: "22px", color: "#44403c" } }, `📍 区域: ${spot.region || CITY_NAMES[city]}`),
        React.createElement("div", { style: { display: "flex", fontSize: "22px", color: "#44403c" } }, `🌙 夜樱: ${spot.lightup ? "有" : "无"}`)
      ),
      React.createElement("div", { style: { display: "flex", borderTop: "1px solid #e7e5e4", paddingTop: "20px", flexDirection: "column", alignItems: "center" } },
        React.createElement("div", { style: { fontSize: "18px", color: "#a8a29e" } }, "樱花冲刺 2026 · 数据融合预测"),
        React.createElement("div", { style: { fontSize: "20px", color: "#f7931e", marginTop: "8px" } }, "更多景点→微信 Kiwi_iloveu_O-o")
      )
    )
  );
}

// ── Main ────────────────────────────────────────────────────────────────────

async function main() {
  const opts = parseArgs();
  const outputDir = resolve(opts.output);

  if (!existsSync(outputDir)) {
    mkdirSync(outputDir, { recursive: true });
  }

  console.log(`🎨 Template: ${opts.template}`);
  console.log(`📁 Output: ${outputDir}`);

  const allSpots = getWeathernewsSpots();
  let count = 0;

  for (const [city, spots] of Object.entries(allSpots)) {
    const sorted = [...spots].sort((a, b) => (b.score || 0) - (a.score || 0));

    if (opts.template === "xhs-cover") {
      const element = createCoverElement(city, sorted);
      const png = await renderToPng(element, SIZES.XHS);
      const path = join(outputDir, `${city}_cover.png`);
      writeFileSync(path, png);
      console.log(`  ✅ ${path}`);
      count++;
    } else if (opts.template === "moment") {
      // Generate card for top spot
      if (sorted.length > 0) {
        const element = createMomentElement(sorted[0], city);
        const png = await renderToPng(element, SIZES.MOMENT);
        const path = join(outputDir, `${city}_top1.png`);
        writeFileSync(path, png);
        console.log(`  ✅ ${path}`);
        count++;
      }
    } else if (opts.template === "xhs-content") {
      // TODO: implement XhsContent template
      console.log(`  ⏭️ xhs-content template not yet implemented for ${city}`);
    }
  }

  console.log(`\n🎉 Done! Generated ${count} cards.`);
}

main().catch((err) => {
  console.error("❌ Export failed:", err);
  process.exit(1);
});
