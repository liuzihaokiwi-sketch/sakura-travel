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

function createXhsContentElement(city: string, spots: Spot[]): React.ReactElement {
  const top5 = spots.slice(0, 5);
  const cityName = CITY_NAMES[city] || city;

  return React.createElement(
    "div",
    {
      style: {
        display: "flex",
        flexDirection: "column",
        width: "100%",
        height: "100%",
        background: "#fefaf6",
        fontFamily: "Noto Sans SC",
      },
    },
    // Header band
    React.createElement(
      "div",
      {
        style: {
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          background: "linear-gradient(135deg, #1a0a0f 0%, #2d1525 60%, #3d1a2a 100%)",
          padding: "56px 60px 40px",
        },
      },
      React.createElement(
        "div",
        { style: { display: "flex", alignItems: "center", gap: "16px", marginBottom: "16px" } },
        React.createElement("div", { style: { fontSize: "32px" } }, "🌸"),
        React.createElement("div", { style: { fontSize: "22px", color: "rgba(255,255,255,0.5)", letterSpacing: "4px" } }, "SAKURA RUSH 2026")
      ),
      React.createElement(
        "div",
        { style: { fontSize: "52px", fontWeight: 900, color: "white", textAlign: "center" as const } },
        `${cityName} 赏樱榜`
      ),
      React.createElement(
        "div",
        { style: { display: "flex", gap: "24px", marginTop: "16px" } },
        React.createElement("div", { style: { fontSize: "18px", color: "#f8bbd0" } }, "📊 数据融合排名"),
        React.createElement("div", { style: { fontSize: "18px", color: "rgba(255,255,255,0.3)" } }, "·"),
        React.createElement("div", { style: { fontSize: "18px", color: "#f8bbd0" } }, "每天3次更新")
      )
    ),
    // Spot list
    React.createElement(
      "div",
      {
        style: {
          display: "flex",
          flexDirection: "column",
          flex: 1,
          padding: "32px 48px",
          gap: "20px",
        },
      },
      ...top5.map((spot, i) =>
        React.createElement(
          "div",
          {
            key: i,
            style: {
              display: "flex",
              alignItems: "center",
              background: i === 0 ? "linear-gradient(135deg, #fff7ed, #fef3e2)" : "white",
              borderRadius: "20px",
              padding: "24px 28px",
              gap: "20px",
              border: i === 0 ? "2px solid #f7931e" : "1px solid #f5f0eb",
            },
          },
          // Rank badge
          React.createElement(
            "div",
            {
              style: {
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                width: "56px",
                height: "56px",
                borderRadius: "50%",
                background: i === 0 ? "#f7931e" : i === 1 ? "#c0c0c0" : i === 2 ? "#cd7f32" : "#e7e5e4",
                flexShrink: 0,
              },
            },
            React.createElement(
              "div",
              { style: { fontSize: "28px", fontWeight: 900, color: i <= 2 ? "white" : "#78716c" } },
              `${i + 1}`
            )
          ),
          // Spot info
          React.createElement(
            "div",
            { style: { display: "flex", flexDirection: "column", flex: 1, gap: "6px" } },
            React.createElement(
              "div",
              { style: { fontSize: i === 0 ? "30px" : "26px", fontWeight: 700, color: "#1c1917" } },
              spot.name
            ),
            React.createElement(
              "div",
              { style: { display: "flex", gap: "16px" } },
              React.createElement("div", { style: { fontSize: "18px", color: "#78716c" } }, `🌸 满开: ${spot.full || "待定"}`),
              spot.lightup
                ? React.createElement("div", { style: { fontSize: "18px", color: "#78716c" } }, "🌙 夜樱")
                : null,
              spot.meisyo100
                ? React.createElement("div", { style: { fontSize: "18px", color: "#f7931e" } }, "⭐ 名所百选")
                : null
            ).valueOf()
          ),
          // Score
          React.createElement(
            "div",
            {
              style: {
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                flexShrink: 0,
              },
            },
            React.createElement(
              "div",
              { style: { fontSize: "36px", fontWeight: 900, color: i === 0 ? "#f7931e" : "#44403c" } },
              `${spot.score}`
            ),
            React.createElement("div", { style: { fontSize: "14px", color: "#a8a29e" } }, "/ 100")
          )
        )
      )
    ),
    // Footer
    React.createElement(
      "div",
      {
        style: {
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "24px 48px",
          borderTop: "1px solid #e7e5e4",
        },
      },
      React.createElement("div", { style: { fontSize: "18px", color: "#a8a29e" } }, "4大权威数据源 · JMA + JMC + Weathernews + 地方官方"),
      React.createElement(
        "div",
        { style: { display: "flex", background: "#1a0a0f", borderRadius: "12px", padding: "10px 20px" } },
        React.createElement("div", { style: { fontSize: "18px", color: "#f7931e", fontWeight: 700 } }, "关注看完整榜 ↗")
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
      const element = createXhsContentElement(city, sorted);
      const png = await renderToPng(element, SIZES.XHS);
      const path = join(outputDir, `${city}_content.png`);
      writeFileSync(path, png);
      console.log(`  ✅ ${path}`);
      count++;
    }
  }

  console.log(`\n🎉 Done! Generated ${count} cards.`);
}

main().catch((err) => {
  console.error("❌ Export failed:", err);
  process.exit(1);
});
