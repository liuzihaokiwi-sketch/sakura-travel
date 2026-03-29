/**
 * GET /api/guide/[code] — 获取手账状态和内容
 *
 * 返回结构：
 *   { status: "waiting" | "preview" | "unlocked", data: {...} }
 *
 * 映射关系：
 *   order.status == "done" | "delivered" → guide status = "unlocked"（已确认）
 *   order.status == "generating" | "validated" → guide status = "preview"（前置层）
 *   其他 → guide status = "waiting"
 */
import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL || "http://localhost:8000";

function mapOrderStatusToGuide(
  orderStatus: string
): "waiting" | "preview" | "unlocked" {
  if (orderStatus === "done" || orderStatus === "delivered") return "unlocked";
  if (orderStatus === "generating" || orderStatus === "validated") return "preview";
  return "waiting";
}

export async function GET(
  _req: NextRequest,
  { params }: { params: { code: string } }
) {
  const { code } = params;

  // 1. 通过 trip_request_id / order_code 查询订单
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

  const guideStatus = mapOrderStatusToGuide(order.status);

  // 2. 如果已生成，拉取 preview/plan 数据
  let planData = null;
  if (guideStatus === "preview" || guideStatus === "unlocked") {
    const tripId = order.trip_request_id;
    if (tripId) {
      const planRes = await fetch(`${BACKEND}/trips/${tripId}/preview-data`, {
        cache: "no-store",
      });
      if (planRes.ok) {
        planData = await planRes.json();
      }
    }
  }

  return NextResponse.json({
    code,
    status: guideStatus,
    order_id: order.order_id,
    trip_request_id: order.trip_request_id,
    data: planData,
  });
}
