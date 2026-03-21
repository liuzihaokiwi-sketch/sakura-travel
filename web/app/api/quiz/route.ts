import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    const res = await fetch(`${BACKEND_URL}/submissions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await res.json();

    if (!res.ok) {
      console.error("Backend submission error:", data);
      return NextResponse.json(
        { error: data.detail || "提交失败，请稍后重试" },
        { status: res.status }
      );
    }

    return NextResponse.json({
      trip_request_id: data.id,
      success: true,
    });
  } catch (e: any) {
    console.error("Quiz API error:", e);
    return NextResponse.json({ error: "服务器错误" }, { status: 500 });
  }
}