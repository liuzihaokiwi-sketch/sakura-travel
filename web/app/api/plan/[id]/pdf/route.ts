/**
 * GET /api/plan/[id]/pdf
 * 代理后端 PDF 导出 — 支持 submission_id 和 trip_request_id
 * 如果后端返回真 PDF → 直接下载
 * 如果后端返回 HTML（weasyprint 不可用）→ 透传 HTML，前端在新窗口打开打印
 */
import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const { id } = params;

  // 先查 submission 获取 trip_request_id
  let tripRequestId = id;
  try {
    const subRes = await fetch(`${BACKEND_URL}/submissions/${id}`, { cache: "no-store" });
    if (subRes.ok) {
      const subData = await subRes.json();
      if (subData.trip_request_id) {
        tripRequestId = subData.trip_request_id;
      }
    }
  } catch {
    // 如果查不到 submission，直接用 id 作为 trip_request_id
  }

  try {
    const res = await fetch(`${BACKEND_URL}/trips/${tripRequestId}/export?fmt=pdf`, {
      cache: "no-store",
    });

    if (!res.ok) {
      const errText = await res.text();
      return NextResponse.json(
        { error: errText || "PDF generation failed" },
        { status: res.status }
      );
    }

    // 透传后端的 Content-Type
    const backendContentType = res.headers.get("content-type") || "";
    const buffer = await res.arrayBuffer();

    if (backendContentType.includes("application/pdf")) {
      // 真 PDF — 直接下载
      return new NextResponse(buffer, {
        status: 200,
        headers: {
          "Content-Type": "application/pdf",
          "Content-Disposition": `attachment; filename=sakura-plan-${id.slice(0, 8)}.pdf`,
        },
      });
    } else {
      // HTML fallback（weasyprint 不可用时）— 透传 HTML
      return new NextResponse(buffer, {
        status: 200,
        headers: {
          "Content-Type": "text/html; charset=utf-8",
        },
      });
    }
  } catch (err) {
    console.error("[plan/pdf] fetch error:", err);
    return NextResponse.json(
      { error: "Backend unavailable" },
      { status: 503 }
    );
  }
}