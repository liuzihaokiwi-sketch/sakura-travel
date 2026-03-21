/**
 * 验证 ?export=true 模式下 Navbar / FloatingCTA 正确隐藏
 *
 * Usage:
 *   npx tsx scripts/verify-export-mode.ts
 *   npx tsx scripts/verify-export-mode.ts --baseUrl http://localhost:3000
 */

import { chromium } from "playwright";

const PAGES = ["/", "/rush", "/custom"];

function parseArgs() {
  const args = process.argv.slice(2);
  const parsed: Record<string, string> = {};
  for (let i = 0; i < args.length; i += 2) {
    const key = args[i].replace(/^--/, "");
    parsed[key] = args[i + 1];
  }
  return {
    baseUrl: parsed.baseUrl || "http://localhost:3000",
  };
}

async function verifyPage(
  baseUrl: string,
  path: string
): Promise<{ page: string; pass: boolean; details: string[] }> {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const playwrightPage = await context.newPage();
  const details: string[] = [];
  let pass = true;

  try {
    // ── 1. 普通模式：Navbar & FloatingCTA 应可见 ───────────────────────────
    const normalUrl = `${baseUrl}${path}`;
    await playwrightPage.goto(normalUrl, { waitUntil: "networkidle" });
    await playwrightPage.waitForTimeout(800);

    const navbarNormal = await playwrightPage.$("nav");
    const floatingNormal = await playwrightPage.$("[data-testid='floating-cta']");

    if (navbarNormal) {
      details.push("✅ 普通模式: Navbar 存在（正确）");
    } else {
      // nav 元素缺失也可能是页面本身问题，不作为 export 验证失败
      details.push("⚠️  普通模式: Navbar 未找到（可能页面无 nav）");
    }

    if (floatingNormal) {
      details.push("✅ 普通模式: FloatingCTA 存在（正确）");
    } else {
      details.push("⚠️  普通模式: FloatingCTA 未找到 data-testid");
    }

    // ── 2. export=true 模式：Navbar & FloatingCTA 应隐藏 ──────────────────
    const exportUrl = `${baseUrl}${path}?export=true`;
    await playwrightPage.goto(exportUrl, { waitUntil: "networkidle" });
    await playwrightPage.waitForTimeout(800);

    const navbarExport = await playwrightPage.$("nav");
    const floatingExport = await playwrightPage.$("[data-testid='floating-cta']");

    if (!navbarExport) {
      details.push("✅ export 模式: Navbar 已隐藏（正确）");
    } else {
      details.push("❌ export 模式: Navbar 仍然可见（需要修复）");
      pass = false;
    }

    if (!floatingExport) {
      details.push("✅ export 模式: FloatingCTA 已隐藏（正确）");
    } else {
      details.push("❌ export 模式: FloatingCTA 仍然可见（需要修复）");
      pass = false;
    }

    // ── 3. 截图对比存档 ────────────────────────────────────────────────────
    const slug = path === "/" ? "home" : path.replace(/\//g, "");
    const exportScreenshot = `output/verify-export-${slug}.png`;
    await playwrightPage.setViewportSize({ width: 1080, height: 1440 });
    await playwrightPage.goto(exportUrl, { waitUntil: "networkidle" });
    await playwrightPage.waitForTimeout(800);
    await playwrightPage.screenshot({ path: exportScreenshot, fullPage: false });
    details.push(`📸 截图已保存: ${exportScreenshot}`);
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    details.push(`❌ 错误: ${msg}`);
    pass = false;
  } finally {
    await browser.close();
  }

  return { page: path, pass, details };
}

async function main() {
  const { baseUrl } = parseArgs();
  console.log(`\n🔍 验证 export=true 模式 | baseUrl: ${baseUrl}\n`);
  console.log("=".repeat(60));

  const results = [];
  for (const path of PAGES) {
    console.log(`\n📄 页面: ${path}`);
    const result = await verifyPage(baseUrl, path);
    results.push(result);
    result.details.forEach((d) => console.log("  " + d));
    console.log(`  ${result.pass ? "🟢 PASS" : "🔴 FAIL"}`);
  }

  console.log("\n" + "=".repeat(60));
  console.log("\n📊 汇总结果:\n");
  results.forEach(({ page, pass }) => {
    console.log(`  ${pass ? "🟢" : "🔴"} ${page}`);
  });

  const allPass = results.every((r) => r.pass);
  console.log(`\n${allPass ? "✅ 所有验证通过！" : "❌ 存在验证失败，请检查上方详情"}\n`);

  if (!allPass) process.exit(1);
}

main().catch((err) => {
  console.error("❌ 验证脚本异常:", err);
  process.exit(1);
});
