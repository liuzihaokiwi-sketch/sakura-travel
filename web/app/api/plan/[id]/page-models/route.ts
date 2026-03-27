import { NextResponse } from "next/server";

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

export async function GET(
  _req: Request,
  { params }: { params: { id: string } }
) {
  const tripRequestId = await resolveTripRequestId(params.id);

  try {
    const res = await fetch(`${BACKEND_URL}/trips/${tripRequestId}/page-models`, {
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
    });

    const text = await res.text();
    if (!res.ok) {
      return NextResponse.json(
        { error: text || "Failed to load page models" },
        { status: res.status }
      );
    }

    try {
      return NextResponse.json(JSON.parse(text));
    } catch {
      return NextResponse.json({ error: "Invalid backend JSON" }, { status: 502 });
    }
  } catch (err) {
    console.error("[plan/page-models] fetch error:", err);
    return NextResponse.json({ error: "Backend unavailable" }, { status: 503 });
  }
}
