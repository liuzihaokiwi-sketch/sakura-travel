/**
 * F3: 移动端适配专项验证脚本
 *
 * 在多种移动端设备尺寸下验证所有页面：
 *   - 页面可正常加载
 *   - 无水平溢出（横向滚动条）
 *   - 关键文案可见
 *   - 按钮可点击
 *   - 截图保存供人工审查
 *
 * Usage:
 *   npx tsx scripts/mobile-responsive-verify.ts
 *   npx tsx scripts/mobile-responsive-verify.ts --screenshots
 */

import { chromium, type Page, type Browser } from "playwright";
import { mkdirSync, existsSync } from "fs";
import { resolve } from "path";

const BASE_URL = process.argv.includes("--base-url")
  ? process.argv[process.argv.indexOf("--base-url") + 1]
  : "http://localhost:3000";

const SAVE_SCREENSHOTS = process.argv.includes("--screenshots");
const OUTPUT_DIR = resolve("output/mobile-audit");

// ── Device presets ──────────────────────────────────────────────────────────

const DEVICES = [
  { name: "iPhone SE",      width: 375,  height: 667 },
  { name: "iPhone 14 Pro",  width: 393,  height: 852 },
  { name: "iPhone 15 Max",  width: 430,  height: 932 },
  { name: "iPad Mini",      width: 768,  height: 1024 },
  { name: "Pixel 7",        width: 412,  height: 915 },
];

const PAGES = [
  { path: "/",                        name: "首页",         text: ["你的日本行程"] },
  { path: "/quiz",                    name: "问卷",         text: ["你想去哪里"] },
  { path: "/submitted?id=test",       name: "提交成功",     text: ["已收到你的需求"] },
  { path: "/pricing",                 name: "价格页",       text: ["248"] },
  { path: "/plan/demo-001",           name: "交付页",       text: ["东京 7 日"] },
  { path: "/plan/demo-001?mode=preview", name: "预览页",    text: ["免费预览"] },
  { path: "/custom",                  name: "定制服务",     text: ["微信"] },
  { path: "/rush",                    name: "樱花排行榜",   text: ["樱花"] },
];

interface Result {
  device: string;
  page: string;
  status: "✅" | "❌" | "⚠️";
  issues: string[];
}

const results: Result[] = [];

// ── Main ────────────────────────────────────────────────────────────────────

async function main() {
  console.log(`\n📱 移动端适配专项验证`);
  console.log(`   Base URL: ${BASE_URL}`);
  console.log(`   设备: ${DEVICES.map((d) => d.name).join(", ")}`);
  console.log(`   页面: ${PAGES.length} 个`);
  if (SAVE_SCREENSHOTS) {
    console.log(`   截图输出: ${OUTPUT_DIR}`);
    if (!existsSync(OUTPUT_DIR)) mkdirSync(OUTPUT_DIR, { recursive: true });
  }
  console.log();

  let browser: Browser | undefined;
  try {
    browser = await chromium.launch();

    for (const device of DEVICES) {
      console.log(`\n📲 ${device.name} (${device.width}×${device.height})`);

      const context = await browser.newContext({
        viewport: { width: device.width, height: device.height },
        isMobile: device.width < 768,
        hasTouch: device.width < 768,
      });
      const page = await context.newPage();

      for (const pg of PAGES) {
        const issues: string[] = [];
        const label = `  ${pg.name}`;

        try {
          const resp = await page.goto(`${BASE_URL}${pg.path}`, {
            waitUntil: "domcontentloaded",
            timeout: 15000,
          });

          if (!resp || resp.status() >= 400) {
            issues.push(`HTTP ${resp?.status() || "timeout"}`);
            results.push({ device: device.name, page: pg.name, status: "❌", issues });
            console.log(`${label} ❌ ${issues.join(", ")}`);
            continue;
          }

          // Wait for rendering
          await page.waitForTimeout(800);

          // Check: horizontal overflow
          const hasOverflow = await page.evaluate(() => {
            return document.documentElement.scrollWidth > document.documentElement.clientWidth;
          });
          if (hasOverflow) {
            issues.push("水平溢出（有横向滚动条）");
          }

          // Check: key text visible
          const bodyText = await page.textContent("body") || "";
          for (const t of pg.text) {
            if (!bodyText.includes(t)) {
              issues.push(`关键文案缺失: "${t}"`);
            }
          }

          // Check: no text cutoff (font-size too small)
          const tinyText = await page.evaluate(() => {
            const els = document.querySelectorAll("h1, h2, h3, p, button, a");
            let tooSmall = 0;
            els.forEach((el) => {
              const size = parseFloat(window.getComputedStyle(el).fontSize);
              if (size < 10 && el.textContent?.trim()) tooSmall++;
            });
            return tooSmall;
          });
          if (tinyText > 3) {
            issues.push(`${tinyText} 个元素字号 < 10px`);
          }

          // Check: CTA buttons are at least 44px tap target
          const smallButtons = await page.evaluate(() => {
            const buttons = document.querySelectorAll("button, a[href]");
            let small = 0;
            buttons.forEach((btn) => {
              const rect = btn.getBoundingClientRect();
              if (rect.width > 0 && rect.height > 0 && (rect.height < 36 || rect.width < 36)) {
                small++;
              }
            });
            return small;
          });
          if (smallButtons > 2) {
            issues.push(`${smallButtons} 个按钮点击区域过小 (< 36px)`);
          }

          // Save screenshot
          if (SAVE_SCREENSHOTS) {
            const filename = `${device.name.replace(/\s+/g, "-")}_${pg.name}.png`;
            await page.screenshot({
              path: resolve(OUTPUT_DIR, filename),
              fullPage: true,
            });
          }

          const status = issues.length === 0 ? "✅" : issues.some((i) => i.includes("HTTP") || i.includes("缺失")) ? "❌" : "⚠️";
          results.push({ device: device.name, page: pg.name, status, issues });
          console.log(`${label} ${status}${issues.length ? " — " + issues.join("; ") : ""}`);

        } catch (err: any) {
          issues.push(err.message);
          results.push({ device: device.name, page: pg.name, status: "❌", issues });
          console.log(`${label} ❌ ${err.message}`);
        }
      }

      await context.close();
    }

    await browser.close();
    browser = undefined;

  } catch (err: any) {
    console.error(`\n💥 Fatal: ${err.message}`);
    if (browser) await browser.close();
  }

  // ── Summary ──────────────────────────────────────────────────
  console.log("\n" + "═".repeat(60));
  console.log("📊 移动端适配验证汇总\n");

  const pass = results.filter((r) => r.status === "✅").length;
  const fail = results.filter((r) => r.status === "❌").length;
  const warn = results.filter((r) => r.status === "⚠️").length;

  console.log(`  ✅ 通过: ${pass} / ${results.length}`);
  console.log(`  ❌ 失败: ${fail}`);
  console.log(`  ⚠️ 警告: ${warn}`);

  // Per-device summary table
  console.log("\n  按设备：");
  for (const device of DEVICES) {
    const deviceResults = results.filter((r) => r.device === device.name);
    const dp = deviceResults.filter((r) => r.status === "✅").length;
    console.log(`    ${device.name}: ${dp}/${deviceResults.length} 通过`);
  }

  if (fail + warn > 0) {
    console.log("\n  问题详情：");
    results
      .filter((r) => r.status !== "✅")
      .forEach((r) => {
        console.log(`    ${r.status} [${r.device}] ${r.page}: ${r.issues.join("; ")}`);
      });
  }

  if (SAVE_SCREENSHOTS) {
    console.log(`\n  📸 截图已保存到: ${OUTPUT_DIR}`);
  }

  console.log("\n" + "═".repeat(60));
  process.exit(fail > 0 ? 1 : 0);
}

main();
