/**
 * 交付页导出为朋友圈分享图 API
 *
 * POST /api/export/plan-image
 * Body: { planId: string, width?: number, height?: number }
 *
 * 使用 Playwright 截图 /plan/[id]?export=true 页面，
 * 返回 PNG 图片（1080×1080 朋友圈尺寸）。
 */

import { NextRequest, NextResponse } from "next/server";
import { chromium } from "playwright";

const DEFAULT_WIDTH = 1080;
const DEFAULT_HEIGHT = 1080;
const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL || "http://localhost:3000";

export async function POST(request: NextRequest) {
  let browser;
  try {
    const body = await request.json();
    const { planId, width = DEFAULT_WIDTH, height = DEFAULT_HEIGHT } = body;

    if (!planId) {
      return NextResponse.json(
        { error: "planId is required" },
        { status: 400 }
      );
    }

    const targetUrl = `${BASE_URL}/plan/${planId}?export=true`;

    browser = await chromium.launch({
      args: [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
      ],
    });

    const page = await browser.newPage();
    await page.setViewportSize({ width, height });

    // Navigate and wait for content
    await page.goto(targetUrl, { waitUntil: "networkidle", timeout: 15000 });

    // Wait for fonts and images to load
    await page.waitForTimeout(1500);

    // Capture screenshot clipped to viewport (not full-page scroll)
    const screenshot = await page.screenshot({
      fullPage: false,
      type: "png",
    });

    await browser.close();
    browser = undefined;

    return new NextResponse(screenshot, {
      status: 200,
      headers: {
        "Content-Type": "image/png",
        "Content-Disposition": `inline; filename="plan-${planId}-share.png"`,
        "Cache-Control": "public, max-age=3600",
      },
    });
  } catch (err: any) {
    if (browser) {
      try { await browser.close(); } catch {}
    }
    console.error("Export plan image failed:", err);
    return NextResponse.json(
      { error: "Export failed", detail: err?.message || String(err) },
      { status: 500 }
    );
  }
}
