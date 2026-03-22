import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

// GET /api/admin/submissions — 列表 或 单条（传 id 参数）
export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const id = searchParams.get("id") || "";
    const status = searchParams.get("status") || "";

    // 单条查询
    if (id) {
      const res = await fetch(`${BACKEND_URL}/submissions/${id}`);
      if (!res.ok) {
        return NextResponse.json({ error: "not found" }, { status: 404 });
      }
      const data = await res.json();
      return NextResponse.json(data);
    }

    // 列表查询
    let url = `${BACKEND_URL}/submissions`;
    if (status) url += `?status_filter=${encodeURIComponent(status)}`;

    const res = await fetch(url);
    const data = await res.json();
    return NextResponse.json(data);
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}

// POST /api/admin/submissions?id=xxx&action=archive — 归档
export async function POST(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const id = searchParams.get("id");
    const action = searchParams.get("action");
    if (!id) return NextResponse.json({ error: "missing id" }, { status: 400 });

    if (action === "archive") {
      const res = await fetch(`${BACKEND_URL}/submissions/${id}/archive`, {
        method: "POST",
      });
      const data = await res.json();
      return NextResponse.json(data, { status: res.status });
    }

    return NextResponse.json({ error: "unknown action" }, { status: 400 });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}

// PATCH /api/admin/submissions?id=xxx — 更新状态
export async function PATCH(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const id = searchParams.get("id");
    if (!id) return NextResponse.json({ error: "missing id" }, { status: 400 });

    const body = await req.json();
    const res = await fetch(`${BACKEND_URL}/submissions/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}