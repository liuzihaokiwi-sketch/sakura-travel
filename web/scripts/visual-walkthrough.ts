/**
 * 全站视觉走查脚本 — 批量截图所有页面，输出到 output/walkthrough/
 *
 * Usage:
 *   npx tsx scripts/visual-walkthrough.ts
 *   npx tsx scripts/visual-walkthrough.ts --baseUrl http://localhost:3000
 *
 * Output:
 *   output/walkthrough/
 *     home_desktop.png          首页桌面端 (1440×900)
 *     home_mobile.png           首页移动端 (390×844)
 *     rush_desktop.png          排行榜桌面端
 *     rush_mobile.png           排行榜移动端
 *     custom_desktop.png        定制页桌面端
 *     custom_mobile.png         定制页移动端
 *     home_export.png           首页导出模式 (1080×1440)
 *     rush_export.png           排行榜导出模式 (1080×1440)
 */

import { chromium, type Browser, type Page } from "playwright";
import { mkdirSync, existsSync, statSync } from "fs";
import { resolve } from "path";

// ── Config ───────────────────────────────────────────────────────────────────

interface ShotConfig {
  name: string;
  path: string;
  width: number;
  height: number;
  fullPage: boolean;
  exportMode?: boolean;
  description: string;
}

const SHOTS: ShotConfig[] = [
  // ── 首页
  {
    name: "home_desktop",
    path: "/",
    width: 1440,
    height: 900,
    fullPage: true,
    description: "首页 · 桌面端全页",
  },
  {
    name: "home_mobile",
    path: "/",
    width: 390,
    height: 844,
    fullPage: true,
    description: "首页 · 移动端全页",
  },
  // ── 樱花排行榜
  {
    name: "rush_desktop",
    path: "/rush",
    width: 1440,
    height: 900,
    fullPage: true,
    description: "排行榜 · 桌面端全页",
  },
  {
    name: "rush_mobile",
    path: "/rush",
    width: 390,
    height: 844,
    fullPage: true,
    description: "排行榜 · 移动端全页",
  },
  // ── 定制服务
  {
    name: "custom_desktop",
    path: "/custom",
    width: 1440,
    height: 900,
    fullPage: true,
    description: "定制服务 · 桌面端全页",
  },
  {
    name: "custom_mobile",
    path: "/custom",
    width: 390,
    height: 844,
    fullPage: true,
    description: "定制服务 · 移动端全页",
  },
  // ── 导出模式截图（杂志级设计检查）
  {
    name: "home_export",
    path: "/",
    width: 1080,
    height: 1440,
    fullPage: false,
    exportMode: true,
    description: "首页 · 导出模式 1080×1440",
  },
  {
    name: "rush_export",
    path: "/rush",
    width: 1080,
    height: 1440,
    fullPage: false,
    exportMode: true,
    description: "排行榜 · 导出模式 1080×1440",
  },
  {
    name: "custom_export",
    path: "/custom",
    width: 1080,
    height: 1440,
    fullPage: false,
    exportMode: true,
    description: "定制服务 · 导出模式 1080×1440",
  },
];

// ── Helpers ──────────────────────────────────────────────────────────────────

function parseArgs() {
  const args = process.argv.slice(2);
  const parsed: Record<string, string> = {};
  for (let i = 0; i < args.length; i += 2) {
    const key = args[i].replace(/^--/, "");
    parsed[key] = args[i + 1];
  }
  return {
    baseUrl: parsed.baseUrl || "http://localhost:3000",
    outDir: parsed.outDir || "output/walkthrough",
  };
}

function fileSizeKB(path: string): number {
  try {
    return Math.round(statSync(path).size / 1024);
  } catch {
    return 0;
  }
}

async function captureShot(
  browser: Browser,
  baseUrl: string,
  shot: ShotConfig,
  outputPath: string
): Promise<{ success: boolean; sizeKB: number; error?: string }> {
  const page: Page = await browser.newPage();

  try {
    await page.setViewportSize({ width: shot.width, height: shot.height });

    const url = shot.exportMode
      ? `${baseUrl}${shot.path}${shot.path.includes("?") ? "&" : "?"}export=true`
      : `${baseUrl}${shot.path}`;

    await page.goto(url, { waitUntil: "networkidle" });

    // Wait for fonts, animations, images
    await page.waitForTimeout(shot.fullPage ? 2000 : 1800);

    await page.screenshot({
      path: outputPath,
      fullPage: shot.fullPage,
      type: "png",
    });

    await page.close();
    return { success: true, sizeKB: fileSizeKB(outputPath) };
  } catch (err: unknown) {
    await page.close();
    const msg = err instanceof Error ? err.message : String(err);
    return { success: false, sizeKB: 0, error: msg };
  }
}

// ── Main ─────────────────────────────────────────────────────────────────────

async function main() {
  const { baseUrl, outDir } = parseArgs();
  const resolvedOutDir = resolve(outDir);

  if (!existsSync(resolvedOutDir)) {
    mkdirSync(resolvedOutDir, { recursive: true });
  }

  console.log(`\n🔍 全站视觉走查`);
  console.log(`   baseUrl : ${baseUrl}`);
  console.log(`   outDir  : ${resolvedOutDir}`);
  console.log(`   截图数  : ${SHOTS.length}\n`);
  console.log("=".repeat(65));

  const browser = await chromium.launch();
  const results: { name: string; description: string; success: boolean; sizeKB: number; error?: string }[] = [];

  for (const shot of SHOTS) {
    const outputPath = resolve(resolvedOutDir, `${shot.name}.png`);
    console.log(`\n📸 ${shot.description}`);
    console.log(`   ${shot.width}×${shot.height}${shot.exportMode ? " [export]" : ""}${shot.fullPage ? " [full-page]" : ""}`);

    const result = await captureShot(browser, baseUrl, shot, outputPath);

    if (result.success) {
      const quality = result.sizeKB < 80 ? "⚠️  内容可能不足" : "✓";
      console.log(`   ✅ 已保存 · ${result.sizeKB}KB ${quality}`);
    } else {
      console.log(`   ❌ 失败: ${result.error}`);
    }

    results.push({ name: shot.name, description: shot.description, ...result });
  }

  await browser.close();

  // ── Summary ──────────────────────────────────────────────────────────────

  console.log("\n" + "=".repeat(65));
  console.log("\n📊 走查汇总报告:\n");

  console.log("  页面截图                            尺寸        状态");
  console.log("  " + "-".repeat(60));

  results.forEach(({ description, sizeKB, success, error }) => {
    const status = success ? `${sizeKB}KB ✅` : `❌ ${error?.slice(0, 40)}`;
    console.log(`  ${description.padEnd(36)} ${status}`);
  });

  const passCount = results.filter((r) => r.success).length;
  console.log(`\n  完成: ${passCount}/${results.length} 张截图`);
  console.log(`  输出: ${resolvedOutDir}/\n`);

  if (passCount === results.length) {
    console.log("✅ 全站视觉走查完成！请打开 output/walkthrough/ 目录检查截图质量。\n");
  } else {
    console.log("⚠️  部分截图失败，请确认 dev server 正在运行（npm run dev）\n");
    process.exit(1);
  }
}

main().catch((err) => {
  console.error("❌ 走查脚本异常:", err);
  process.exit(1);
});
