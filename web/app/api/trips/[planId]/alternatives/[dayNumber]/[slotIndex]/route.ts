import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000";

/** GET /api/trips/[planId]/alternatives/[dayNumber]/[slotIndex] */
export async function GET(
  _req: NextRequest,
  { params }: { params: { planId: string; dayNumber: string; slotIndex: string } }
) {
  const { planId, dayNumber, slotIndex } = params;
  const res = await fetch(
    `${BACKEND}/trips/${planId}/alternatives/${dayNumber}/${slotIndex}`,
    { next: { revalidate: 0 } } // 不缓存，实时
  );
  const data = await res.json().catch(() => ({}));
  return NextResponse.json(data, { status: res.status });
}
