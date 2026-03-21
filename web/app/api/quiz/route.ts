import { NextRequest, NextResponse } from "next/server";
import { supabase } from "@/lib/supabase";

export const dynamic = "force-dynamic";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    const { destination, duration_days, party_type, japan_experience, play_mode, styles, wechat_id } = body;

    // Validate required fields
    if (!destination || !party_type || !wechat_id) {
      return NextResponse.json({ error: "缺少必填字段" }, { status: 400 });
    }

    const { data, error } = await supabase
      .from("quiz_submissions")
      .insert({
        destination,
        duration_days: parseInt(duration_days) || 7,
        party_type,
        japan_experience: japan_experience || null,
        play_mode: play_mode || null,
        styles: styles || [],
        wechat_id: wechat_id.trim(),
        status: "new",
      } as any)
      .select("id")
      .single();

    if (error) {
      console.error("Supabase insert error:", error);
      return NextResponse.json({ error: "提交失败，请稍后重试" }, { status: 500 });
    }

    return NextResponse.json({ trip_request_id: (data as any).id, success: true });
  } catch (e: any) {
    console.error("Quiz API error:", e);
    return NextResponse.json({ error: "服务器错误" }, { status: 500 });
  }
}
