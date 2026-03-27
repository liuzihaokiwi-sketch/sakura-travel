import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

async function resolveTripRequestId(id: string): Promise<string> {
  try {
    const subRes = await fetch(`${BACKEND_URL}/submissions/${id}`, { cache: "no-store" });
    if (subRes.ok) {
      const subData = await subRes.json();
      if (subData.trip_request_id) {
        return subData.trip_request_id;
      }
    }
  } catch {
    // Fallback to treating id as trip_request_id.
  }
  return id;
}

export async function POST(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const tripRequestId = await resolveTripRequestId(params.id);

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  try {
    const res = await fetch(`${BACKEND_URL}/trips/${tripRequestId}/page-overrides`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
    });

    const text = await res.text();
    if (!res.ok) {
      return NextResponse.json(
        { error: text || "Failed to save page overrides" },
        { status: res.status }
      );
    }

    try {
      return NextResponse.json(JSON.parse(text));
    } catch {
      return NextResponse.json({ ok: true, detail: text });
    }
  } catch (err) {
    console.error("[plan/page-overrides] fetch error:", err);
    return NextResponse.json({ error: "Backend unavailable" }, { status: 503 });
  }
}
