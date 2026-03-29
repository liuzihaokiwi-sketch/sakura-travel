/**
 * GET  /api/forms/[code]   — 加载表单草稿（by order_code）
 * PATCH /api/forms/[code]  — 保存表单草稿
 */
import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET(
  _req: NextRequest,
  { params }: { params: { code: string } }
) {
  const { code } = params;
  const res = await fetch(`${BACKEND}/detail-forms/by-submission/${code}`, {
    cache: "no-store",
  });

  if (!res.ok) {
    const text = await res.text();
    return NextResponse.json({ error: text || "Not found" }, { status: res.status });
  }

  return NextResponse.json(await res.json());
}

export async function PATCH(
  req: NextRequest,
  { params }: { params: { code: string } }
) {
  const { code } = params;
  const body = await req.json();

  // 先用 order_code 查 form_id
  const lookupRes = await fetch(`${BACKEND}/detail-forms/by-submission/${code}`, {
    cache: "no-store",
  });

  if (!lookupRes.ok) {
    return NextResponse.json({ error: "Form not found" }, { status: 404 });
  }

  const form = await lookupRes.json();
  const formId = form.form_id;

  const res = await fetch(`${BACKEND}/detail-forms/${formId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text();
    return NextResponse.json({ error: text }, { status: res.status });
  }

  return NextResponse.json(await res.json());
}
