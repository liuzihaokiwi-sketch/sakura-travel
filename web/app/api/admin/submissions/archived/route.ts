import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

// GET /api/admin/submissions/archived — 归档历史列表
export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const destination = searchParams.get("destination") || "";
    const limit = searchParams.get("limit") || "200";
    const offset = searchParams.get("offset") || "0";

    let url = `${BACKEND_URL}/submissions/archived/list?limit=${limit}&offset=${offset}`;
    if (destination) url += `&destination=${encodeURIComponent(destination)}`;

    const res = await fetch(url);
    const data = await res.json();
    return NextResponse.json(data);
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
