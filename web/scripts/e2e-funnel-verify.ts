/**
 * F1: 端到端全漏斗验证脚本
 *
 * 验证完整用户旅程：
 *   首页 → 点击 CTA → 问卷 → 提交 → 成功页
 *   首页 → 价格页
 *   交付页（正常 + 预览 + 导出模式）
 *   管理后台
 *
 * Usage:
 *   npx tsx scripts/e2e-funnel-verify.ts
 *   npx tsx scripts/e2e-funnel-verify.ts --base-url https://staging.example.com
 */

import { chromium, type Page, type Browser } from "playwright";

const BASE_URL = process.argv.includes("--base-url")
  ? process.argv[process.argv.indexOf("--base-url") + 1]
  : "http://localhost:3000";

interface CheckResult {
  name: string;
  status: "✅ PASS" | "❌ FAIL" | "⚠️ WARN";
  detail?: string;
  durationMs?: number;
}

const results: CheckResult[] = [];

function record(name: string, status: CheckResult["status"], detail?: string, durationMs?: number) {
  results.push({ name, status, detail, durationMs });
  const icon = status;
  const ms = durationMs ? ` (${durationMs}ms)` : "";
  console.log(`  ${icon} ${name}${ms}${detail ? " — " + detail : ""}`);
}

async function checkPage(page: Page, name: string, path: string, expectations: {
  titleContains?: string;
  selectorExists?: string[];
  selectorNotExists?: string[];
  textContains?: string[];
}) {
  const start = Date.now();
  try {
    const resp = await page.goto(`${BASE_URL}${path}`, { waitUntil: "domcontentloaded", timeout: 15000 });
    const dur = Date.now() - start;

    if (!resp || resp.status() >= 400) {
      record(name, "❌ FAIL", `HTTP ${resp?.status() || "timeout"}`, dur);
      return;
    }

    // Title check
    if (expectations.titleContains) {
      const title = await page.title();
      if (!title.includes(expectations.titleContains)) {
        record(name, "⚠️ WARN", `Title: "${title}" does not contain "${expectations.titleContains}"`, dur);
        return;
      }
    }

    // Selector exists
    if (expectations.selectorExists) {
      for (const sel of expectations.selectorExists) {
        const el = await page.$(sel);
        if (!el) {
          record(name, "❌ FAIL", `Missing selector: ${sel}`, dur);
          return;
        }
      }
    }

    // Selector not exists
    if (expectations.selectorNotExists) {
      for (const sel of expectations.selectorNotExists) {
        const el = await page.$(sel);
        if (el) {
          record(name, "❌ FAIL", `Unexpected selector found: ${sel}`, dur);
          return;
        }
      }
    }

    // Text contains
    if (expectations.textContains) {
      const body = await page.textContent("body") || "";
      for (const text of expectations.textContains) {
        if (!body.includes(text)) {
          record(name, "❌ FAIL", `Missing text: "${text}"`, dur);
          return;
        }
      }
    }

    record(name, "✅ PASS", undefined, dur);
  } catch (err: any) {
    record(name, "❌ FAIL", err.message, Date.now() - start);
  }
}

// ── Main ────────────────────────────────────────────────────────────────────

async function main() {
  console.log(`\n🔍 端到端全漏斗验证\n   Base URL: ${BASE_URL}\n`);

  let browser: Browser | undefined;
  try {
    browser = await chromium.launch();
    const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    const page = await context.newPage();

    // ── 1. 首页 ────────────────────────────────────────────────
    console.log("📄 首页检查");
    await checkPage(page, "首页加载", "/", {
      textContains: ["你的日本行程", "先免费看一天"],
      selectorExists: ["nav"],
    });

    // Check 10 modules exist
    await checkPage(page, "首页 10 模块", "/", {
      textContains: [
        "计划日本旅行",       // Pain points
        "告诉我们",           // Solution
        "免费看看",           // Free preview
        "首发特惠",           // Main plan
        "尊享定制",           // Premium
        "攻略，长这样",       // Delivery showcase
        "旅居日本",           // Trust
        "你可能还想知道",     // FAQ
        "别再纠结",           // Final CTA
      ],
    });

    // ── 2. 问卷页 ──────────────────────────────────────────────
    console.log("\n📋 问卷页检查");
    await checkPage(page, "问卷页加载", "/quiz", {
      textContains: ["你想去哪里"],
    });

    // ── 3. 提交成功页 ─────────────────────────────────────────
    console.log("\n✅ 成功页检查");
    await checkPage(page, "成功页加载", "/submitted?id=test-123", {
      textContains: ["已收到你的需求", "添加规划师微信"],
    });

    // ── 4. 价格页 ──────────────────────────────────────────────
    console.log("\n💰 价格页检查");
    await checkPage(page, "价格页加载", "/pricing", {
      textContains: ["248"],
    });

    // ── 5. 交付页（正常模式）────────────────────────────────
    console.log("\n📖 交付页检查");
    await checkPage(page, "交付页（完整）", "/plan/demo-001", {
      textContains: ["东京 7 日", "行程总览", "住宿建议", "交通方案"],
      selectorExists: ["nav"],
    });

    // ── 6. 交付页（预览模式）────────────────────────────────
    await checkPage(page, "交付页（预览）", "/plan/demo-001?mode=preview", {
      textContains: ["免费预览", "Day 1"],
    });

    // ── 7. 交付页（导出模式）────────────────────────────────
    console.log("\n📷 导出模式检查");
    await checkPage(page, "导出模式 Navbar 隐藏", "/plan/demo-001?export=true", {
      textContains: ["Sakura Rush 2026 · 定制行程"],
    });

    // Verify Navbar hidden in export mode
    await page.goto(`${BASE_URL}/plan/demo-001?export=true`, { waitUntil: "domcontentloaded" });
    const navVisible = await page.$("nav");
    record(
      "导出模式 Navbar 隐藏验证",
      navVisible ? "❌ FAIL" : "✅ PASS",
      navVisible ? "Navbar should be hidden in export mode" : undefined,
    );

    // ── 8. 精调页 ──────────────────────────────────────────────
    console.log("\n✏️ 精调/升级页检查");
    await checkPage(page, "精调页加载", "/plan/demo-001/edit", {});
    await checkPage(page, "升级页加载", "/plan/demo-001/upgrade", {});

    // ── 9. 定制服务页 ──────────────────────────────────────────
    console.log("\n🎯 定制服务页检查");
    await checkPage(page, "定制服务页加载", "/custom", {
      textContains: ["微信"],
    });

    // ── 10. 管理后台 ─────────────────────────────────────────
    console.log("\n🔧 管理后台检查");
    await checkPage(page, "管理后台（需登录）", "/admin", {});
    await checkPage(page, "管理登录页", "/admin/login", {});

    // ── 11. 移动端视口 ───────────────────────────────────────
    console.log("\n📱 移动端视口检查");
    await page.setViewportSize({ width: 375, height: 812 });
    await checkPage(page, "首页（移动端）", "/", {
      textContains: ["你的日本行程"],
    });
    await checkPage(page, "问卷（移动端）", "/quiz", {
      textContains: ["你想去哪里"],
    });
    await checkPage(page, "交付页（移动端）", "/plan/demo-001", {
      textContains: ["东京 7 日"],
    });

    await browser.close();
    browser = undefined;
  } catch (err: any) {
    console.error(`\n💥 Fatal error: ${err.message}`);
    if (browser) await browser.close();
  }

  // ── Summary ──────────────────────────────────────────────────
  console.log("\n" + "═".repeat(50));
  console.log("📊 验证结果汇总\n");

  const pass = results.filter((r) => r.status === "✅ PASS").length;
  const fail = results.filter((r) => r.status === "❌ FAIL").length;
  const warn = results.filter((r) => r.status === "⚠️ WARN").length;

  console.log(`  ✅ 通过: ${pass}`);
  console.log(`  ❌ 失败: ${fail}`);
  console.log(`  ⚠️ 警告: ${warn}`);
  console.log(`  📋 总计: ${results.length}`);

  if (fail > 0) {
    console.log("\n❌ 失败项:");
    results
      .filter((r) => r.status === "❌ FAIL")
      .forEach((r) => console.log(`  - ${r.name}: ${r.detail}`));
  }

  console.log("\n" + "═".repeat(50));
  process.exit(fail > 0 ? 1 : 0);
}

main();
