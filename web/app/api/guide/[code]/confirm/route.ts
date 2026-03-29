/**
 * POST /api/guide/[code]/confirm — 确认解锁手账（preview → unlocked）
 *
 * 推进订单状态：done → delivered（或直接标记为已确认）
 */
import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(
  _req: NextRequest,
  { params }: { params: { code: string } }
) {
  const { code } = params;

  // 1. 查订单
  const orderRes = await fetch(`${BACKEND}/orders?trip_request_id=${code}`, {
    cache: "no-store",
  });

  if (!orderRes.ok) {
    return NextResponse.json({ error: "Order not found" }, { status: 404 });
  }

  const orderData = await orderRes.json();
  const order = Array.isArray(orderData) ? orderData[0] : orderData;

  if (!order) {
    return NextResponse.json({ error: "Order not found" }, { status: 404 });
  }

  // 2. 推进状态到 delivered（用户已确认查看）
  const patchRes = await fetch(`${BACKEND}/orders/${order.order_id}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ new_status: "delivered", reason: "user_confirmed_guide" }),
  });

  if (!patchRes.ok) {
    const text = await patchRes.text();
    return NextResponse.json({ error: text }, { status: patchRes.status });
  }

  return NextResponse.json({ success: true, status: "unlocked" });
}
