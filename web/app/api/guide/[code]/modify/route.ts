/**
 * POST /api/guide/[code]/modify — 提交 AI 修改意见
 */
import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(
  req: NextRequest,
  { params }: { params: { code: string } }
) {
  const { code } = params;
  const body = await req.json();

  // 查订单以获取 trip_request_id
  const orderRes = await fetch(`${BACKEND}/orders?trip_request_id=${code}`, {
    cache: "no-store",
  });

  if (!orderRes.ok) {
    return NextResponse.json({ error: "Order not found" }, { status: 404 });
  }

  const orderData = await orderRes.json();
  const order = Array.isArray(orderData) ? orderData[0] : orderData;

  if (!order?.trip_request_id) {
    return NextResponse.json({ error: "Trip not found" }, { status: 404 });
  }

  // 代理到后端修改端点
  const res = await fetch(`${BACKEND}/trips/${order.trip_request_id}/modifications`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: body.message,
      source: "user_guide_page",
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    return NextResponse.json({ error: text }, { status: res.status });
  }

  return NextResponse.json(await res.json());
}
