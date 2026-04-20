import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(
  req: NextRequest,
  { params }: { params: { tripId: string } }
) {
  const body = await req.json();
  const res = await fetch(`${BACKEND}/v2/trips/${params.tripId}/plan-actions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  // 202 是正常响应（重新排队中）
  if (res.status === 202) {
    return NextResponse.json({ status: "regenerating" }, { status: 202 });
  }
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
