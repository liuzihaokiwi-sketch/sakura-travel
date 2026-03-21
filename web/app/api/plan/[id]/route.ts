/**
 * GET /api/plan/[id]
 * 代理后端，支持两种模式：
 *   - 默认：GET /trips/{id}/plan（完整方案）
 *   - ?mode=preview：GET /trips/{id}/preview-data（H5 预览数据）
 */
import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const { id } = params;
  const mode = req.nextUrl.searchParams.get("mode");

  // 根据模式选择后端端点
  const endpoint =
    mode === "preview"
      ? `${BACKEND_URL}/trips/${id}/preview-data`
      : `${BACKEND_URL}/trips/${id}/plan`;

  try {
    const res = await fetch(endpoint, {
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
    });

    if (!res.ok) {
      const errText = await res.text();
      return NextResponse.json(
        { error: errText || "Plan not found" },
        { status: res.status }
      );
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (err) {
    console.error("[plan/api] fetch error:", err);
    return NextResponse.json(
      { error: "Backend unavailable" },
      { status: 503 }
    );
  }
}