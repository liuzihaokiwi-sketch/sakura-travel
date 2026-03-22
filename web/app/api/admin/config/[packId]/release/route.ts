/**
 * POST /api/admin/config/[packId]/release
 * 处理发布操作：approve | reject | canary | activate | rollback
 */
import { createClient } from "@supabase/supabase-js"
import { NextRequest, NextResponse } from "next/server"

const VALID_TRANSITIONS: Record<string, string[]> = {
  pending_review: ["approve", "reject"],
  approved:       ["canary", "activate"],
  canary:         ["activate"],
  active:         ["rollback"],
}

const TARGET_STATUS: Record<string, string> = {
  approve:  "approved",
  reject:   "draft",
  canary:   "canary",
  activate: "active",
  rollback: "rolled_back",
}

export async function POST(
  req: NextRequest,
  { params }: { params: { packId: string } }
) {
  const { packId } = params
  const body = await req.json()
  const { action, rollout_scope, rollback_reason } = body as {
    action: string
    rollout_scope?: { pct?: number }
    rollback_reason?: string
  }

  if (!action) {
    return NextResponse.json({ error: "action is required" }, { status: 400 })
  }

  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
  )

  // 获取当前配置包状态
  const { data: pack, error: fetchErr } = await supabase
    .from("config_packs")
    .select("pack_id, status, active_version_no")
    .eq("pack_id", packId)
    .single()

  if (fetchErr || !pack) {
    return NextResponse.json({ error: "config pack not found" }, { status: 404 })
  }

  const allowed = VALID_TRANSITIONS[pack.status] ?? []
  if (!allowed.includes(action)) {
    return NextResponse.json(
      { error: `action '${action}' is not allowed from status '${pack.status}'` },
      { status: 409 },
    )
  }

  const newStatus = TARGET_STATUS[action]

  // 更新配置包状态
  const { error: updateErr } = await supabase
    .from("config_packs")
    .update({ status: newStatus, updated_at: new Date().toISOString() })
    .eq("pack_id", packId)

  if (updateErr) {
    return NextResponse.json({ error: updateErr.message }, { status: 500 })
  }

  // 写入发布记录
  await supabase.from("config_release_records").insert({
    pack_id:          packId,
    version_no:       pack.active_version_no ?? 1,
    action,
    rollout_scope:    rollout_scope ?? null,
    rollback_reason:  rollback_reason ?? null,
    result:           "ok",
    created_at:       new Date().toISOString(),
  })

  // 如果是 canary，同时更新 scope 的 rollout_pct
  if (action === "canary" && rollout_scope?.pct !== undefined) {
    await supabase
      .from("config_scopes")
      .update({ rollout_pct: rollout_scope.pct })
      .eq("pack_id", packId)
  }

  return NextResponse.json({ ok: true, new_status: newStatus })
}