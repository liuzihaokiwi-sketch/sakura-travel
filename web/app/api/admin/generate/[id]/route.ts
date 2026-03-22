/**
 * /api/admin/generate/[id] — 触发攻略生成
 * POST: 调后端 /trips/{id}/generate
 */
import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const body = await req.json().catch(() => ({}));
    const qs = new URLSearchParams();
    if (body.template_code) qs.set("template_code", body.template_code);
    if (body.scene) qs.set("scene", body.scene);

    const url = `${BACKEND_URL}/trips/${params.id}/generate${qs.toString() ? "?" + qs.toString() : ""}`;
    const res = await fetch(url, { method: "POST" });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 503 });
  }
}
