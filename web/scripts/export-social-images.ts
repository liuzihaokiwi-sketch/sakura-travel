/**
 * Playwright 批量导出社交媒体图片
 *
 * 导出内容：
 *   - 小红书封面  1080×1440  ?export=true
 *   - 小红书内容  1080×1440  ?export=true
 *   - 朋友圈卡片  1080×1080  ?export=true
 *
 * Usage:
 *   npx tsx scripts/export-social-images.ts
 *   npx tsx scripts/export-social-images.ts --baseUrl http://localhost:3000 --outDir output
 *
 * Output:
 *   output/
 *     xhs-cover.png        (1080×1440)
 *     xhs-content.png      (1080×1440)
 *     moment-card.png      (1080×1080)
 */

import { chromium } from "playwright";
import { mkdirSync, existsSync, statSync } from "fs";
import { resolve } from "path";

// ── Types ───────────────────────────────────────────────────────────────────

interface ExportTarget {
  name: string;
  route: string;
  width: number;
  height: number;
  output: string;
}

// ── Parse CLI args ──────────────────────────────────────────────────────────

function parseArgs() {
  const args = process.argv.slice(2);
  const parsed: Record<string, string> = {};
  for (let i = 0; i < args.length; i += 2) {
    const key = args[i].replace(/^--/, "");
    parsed[key] = args[i + 1];
  }
  return {
    baseUrl: parsed.baseUrl || "http://localhost:3000",
    outDir: parsed.outDir || "output",
  };
}

// ── Quality Check ────────────────────────────────────────────────────────────

function checkQuality(outputPath: string, name: string): void {
  try {
    const stats = statSync(outputPath);
    const sizeKB = Math.round(stats.size / 1024);
    if (sizeKB < 50) {
      console.warn(`  ⚠️  ${name}: 文件较小（${sizeKB}KB），请检查内容是否正确渲染`);
    } else {
      console.log(`  📊 ${name}: ${sizeKB}KB ✓`);
    }
  } catch {
    console.warn(`  ⚠️  无法检查文件大小: ${outputPath}`);
  }
}

// ── Main ────────────────────────────────────────────────────────────────────

async function main() {
  const { baseUrl, outDir } = parseArgs();

  // Ensure output directory exists
  const resolvedOutDir = resolve(outDir);
  if (!existsSync(resolvedOutDir)) {
    mkdirSync(resolvedOutDir, { recursive: true });
  }

  const targets: ExportTarget[] = [
    {
      name: "小红书封面 (XHS Cover)",
      route: "/rush",
      width: 1080,
      height: 1440,
      output: `${outDir}/xhs-cover.png`,
    },
    {
      name: "小红书内容页 (XHS Content)",
      route: "/rush?city=tokyo",
      width: 1080,
      height: 1440,
      output: `${outDir}/xhs-content.png`,
    },
    {
      name: "朋友圈卡片 (Moment Card)",
      route: "/rush",
      width: 1080,
      height: 1080,
      output: `${outDir}/moment-card.png`,
    },
  ];

  console.log(`\n🌸 Sakura Rush — 社交媒体图片导出`);
  console.log(`   baseUrl : ${baseUrl}`);
  console.log(`   outDir  : ${resolvedOutDir}`);
  console.log(`   共计    : ${targets.length} 张\n`);
  console.log("=".repeat(60));

  const browser = await chromium.launch();

  const results: { name: string; output: string; success: boolean; error?: string }[] = [];

  for (const target of targets) {
    const exportUrl = `${baseUrl}${target.route}${target.route.includes("?") ? "&" : "?"}export=true`;
    const outputPath = resolve(target.output);

    console.log(`\n📸 ${target.name}`);
    console.log(`   URL   : ${exportUrl}`);
    console.log(`   尺寸  : ${target.width}×${target.height}`);
    console.log(`   输出  : ${outputPath}`);

    try {
      const page = await browser.newPage();

      await page.setViewportSize({
        width: target.width,
        height: target.height,
      });

      // Navigate and wait for full render
      await page.goto(exportUrl, { waitUntil: "networkidle" });

      // Wait for fonts, images and animations to settle
      await page.waitForTimeout(2000);

      // Verify no Navbar/FloatingCTA in export mode
      const navbarVisible = await page.$("nav");
      if (navbarVisible) {
        console.warn("  ⚠️  警告: Navbar 在 export 模式下仍可见，请检查实现");
      } else {
        console.log("  ✅ Navbar 已隐藏（export 模式正常）");
      }

      // Take screenshot
      await page.screenshot({
        path: outputPath,
        fullPage: false,
        type: "png",
      });

      await page.close();

      // Quality check
      checkQuality(outputPath, target.name);
      console.log(`  ✅ 已保存: ${target.output}`);
      results.push({ name: target.name, output: target.output, success: true });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      console.error(`  ❌ 失败: ${msg}`);
      results.push({ name: target.name, output: target.output, success: false, error: msg });
    }
  }

  await browser.close();

  // ── Summary ──────────────────────────────────────────────────────────────

  console.log("\n" + "=".repeat(60));
  console.log("\n📊 导出汇总:\n");
  results.forEach(({ name, output, success, error }) => {
    if (success) {
      console.log(`  🟢 ${name}`);
      console.log(`       → ${output}`);
    } else {
      console.log(`  🔴 ${name}`);
      console.log(`       ❌ ${error}`);
    }
  });

  const successCount = results.filter((r) => r.success).length;
  console.log(`\n✨ 完成: ${successCount}/${results.length} 张导出成功\n`);

  if (successCount < results.length) {
    process.exit(1);
  }
}

main().catch((err) => {
  console.error("❌ 导出失败:", err);
  process.exit(1);
});
