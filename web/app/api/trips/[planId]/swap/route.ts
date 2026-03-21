import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000";

/** POST /api/trips/[planId]/swap */
export async function POST(
  req: NextRequest,
  { params }: { params: { planId: string } }
) {
  const body = await req.json();
  const res = await fetch(`${BACKEND}/trips/${params.planId}/swap`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  return NextResponse.json(data, { status: res.status });
}

/** GET /api/trips/[planId]/swap-log */
export async function GET(
  _req: NextRequest,
  { params }: { params: { planId: string } }
) {
  const res = await fetch(`${BACKEND}/trips/${params.planId}/swap-log`, {
    next: { revalidate: 0 },
  });
  const data = await res.json().catch(() => ({}));
  return NextResponse.json(data, { status: res.status });
}
