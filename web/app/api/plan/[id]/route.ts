/**
 * GET /api/plan/[id]
 * 代理后端，支持两种 ID 格式：
 *   - trip_request_id → 直接调 /trips/{id}/plan
 *   - submission_id   → 先查 trip_request_id，再调 /trips/{id}/plan
 * 
 * ?mode=preview → 返回 H5 预览数据
 */
import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const { id } = params;
  const mode = req.nextUrl.searchParams.get("mode");

  // 先尝试直接用 id 作为 trip_request_id 获取 plan
  const endpoint =
    mode === "preview"
      ? `${BACKEND_URL}/trips/${id}/preview-data`
      : `${BACKEND_URL}/trips/${id}/plan`;

  try {
    let res = await fetch(endpoint, {
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
    });

    // 如果 404，可能是 submission_id，尝试查找关联的 trip_request
    if (!res.ok && res.status === 404) {
      // 查询 submission 关联的 trip_request
      const subRes = await fetch(`${BACKEND_URL}/submissions/${id}`, {
        cache: "no-store",
      });
      
      if (subRes.ok) {
        const subData = await subRes.json();
        const tripRequestId = subData.trip_request_id;
        
        if (tripRequestId) {
          const tripEndpoint =
            mode === "preview"
              ? `${BACKEND_URL}/trips/${tripRequestId}/preview-data`
              : `${BACKEND_URL}/trips/${tripRequestId}/plan`;
          
          res = await fetch(tripEndpoint, {
            headers: { "Content-Type": "application/json" },
            cache: "no-store",
          });
        }
      }
    }

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