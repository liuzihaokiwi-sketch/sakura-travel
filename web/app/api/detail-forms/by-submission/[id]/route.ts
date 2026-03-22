/**
 * /api/detail-forms/by-submission/[id] — 通过 submission_id 查询表单
 */
import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const res = await fetch(
      `${BACKEND_URL}/detail-forms/by-submission/${params.id}`,
      { cache: "no-store" }
    );
    if (!res.ok) {
      return NextResponse.json(null, { status: res.status });
    }
    return NextResponse.json(await res.json());
  } catch {
    return NextResponse.json(null, { status: 503 });
  }
}
