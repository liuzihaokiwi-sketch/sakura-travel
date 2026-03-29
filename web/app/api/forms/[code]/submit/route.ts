/**
 * POST /api/forms/[code]/submit — 提交表单，触发后端生成任务
 */
import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(
  _req: NextRequest,
  { params }: { params: { code: string } }
) {
  const { code } = params;

  // 先用 order_code 查 form_id
  const lookupRes = await fetch(`${BACKEND}/detail-forms/by-submission/${code}`, {
    cache: "no-store",
  });

  if (!lookupRes.ok) {
    return NextResponse.json({ error: "Form not found" }, { status: 404 });
  }

  const form = await lookupRes.json();
  const formId = form.form_id;

  const res = await fetch(`${BACKEND}/detail-forms/${formId}/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });

  if (!res.ok) {
    const text = await res.text();
    return NextResponse.json({ error: text }, { status: res.status });
  }

  return NextResponse.json(await res.json());
}
