/**
 * POST /api/admin/config/[packId]/versions
 * 保存新版本快照（版本号自增）
 */
import { NextRequest, NextResponse } from "next/server"
import { requireAdminSession } from "@/lib/admin-auth"
import { createClient } from "@supabase/supabase-js"

function adminDb() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { persistSession: false } },
  )
}

export async function POST(
  request: NextRequest,
  { params }: { params: { packId: string } },
) {
  const auth = await requireAdminSession(request)
  if (!auth.ok) return NextResponse.json({ error: "unauthorized" }, { status: 401 })

  const db = adminDb()
  const { packId } = params
  const body = await request.json()
  const { weights, thresholds, switches, hard_rules, change_summary, reason } = body

  // 获取当前最大版本号
  const { data: latest } = await db
    .from("config_pack_versions")
    .select("version_no")
    .eq("pack_id", packId)
    .order("version_no", { ascending: false })
    .limit(1)
    .single()

  const next_version_no = (latest?.version_no ?? 0) + 1

  // 计算 changed_fields
  const changed_fields = [
    weights    && "weights",
    thresholds && "thresholds",
    switches   && "switches",
    hard_rules && "hard_rules",
  ].filter(Boolean)

  const { data, error } = await db
    .from("config_pack_versions")
    .insert({
      pack_id: packId,
      version_no: next_version_no,
      weights,
      thresholds,
      switches,
      hard_rules,
      change_summary,
      changed_fields,
      reason,
    })
    .select()
    .single()

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })

  // 更新 pack 的 updated_at
  await db
    .from("config_packs")
    .update({ updated_at: new Date().toISOString() })
    .eq("pack_id", packId)

  // 写审计记录
  await db.from("config_release_records").insert({
    pack_id: packId,
    version_no: next_version_no,
    action: "draft_saved",
    notes: change_summary,
  })

  return NextResponse.json({ version: data }, { status: 201 })
}
