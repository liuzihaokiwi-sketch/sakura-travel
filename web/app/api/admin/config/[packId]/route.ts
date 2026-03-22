/**
 * GET    /api/admin/config/[packId]          读取配置包详情（含最新版本）
 * PATCH  /api/admin/config/[packId]          更新配置包基本信息
 * DELETE /api/admin/config/[packId]          归档配置包
 * POST   /api/admin/config/[packId]/versions 保存新版本（草稿）
 * POST   /api/admin/config/[packId]/submit   送审
 * POST   /api/admin/config/[packId]/approve  审批通过
 * POST   /api/admin/config/[packId]/activate 正式激活
 * POST   /api/admin/config/[packId]/rollback 一键回滚
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

type Params = { params: { packId: string } }

// ── GET ──────────────────────────────────────────────────────────────────────

export async function GET(request: NextRequest, { params }: Params) {
  const auth = await requireAdminSession(request)
  if (!auth.ok) return NextResponse.json({ error: "unauthorized" }, { status: 401 })

  const db = adminDb()
  const { packId } = params

  const { data: pack, error: packErr } = await db
    .from("config_packs")
    .select("*")
    .eq("pack_id", packId)
    .single()
  if (packErr || !pack) return NextResponse.json({ error: "not found" }, { status: 404 })

  // 最新 5 个版本
  const { data: versions } = await db
    .from("config_pack_versions")
    .select("*")
    .eq("pack_id", packId)
    .order("version_no", { ascending: false })
    .limit(5)

  // 作用域绑定
  const { data: scopes } = await db
    .from("config_scopes")
    .select("*")
    .eq("pack_id", packId)

  // 最近 10 条发布记录
  const { data: releases } = await db
    .from("config_release_records")
    .select("*")
    .eq("pack_id", packId)
    .order("created_at", { ascending: false })
    .limit(10)

  return NextResponse.json({ pack, versions, scopes, releases })
}

// ── PATCH ─────────────────────────────────────────────────────────────────────

export async function PATCH(request: NextRequest, { params }: Params) {
  const auth = await requireAdminSession(request)
  if (!auth.ok) return NextResponse.json({ error: "unauthorized" }, { status: 401 })

  const body = await request.json()
  const { name, description } = body
  const db = adminDb()

  const { data, error } = await db
    .from("config_packs")
    .update({ name, description, updated_at: new Date().toISOString() })
    .eq("pack_id", params.packId)
    .select()
    .single()
  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json({ pack: data })
}

// ── DELETE（归档）─────────────────────────────────────────────────────────────

export async function DELETE(request: NextRequest, { params }: Params) {
  const auth = await requireAdminSession(request)
  if (!auth.ok) return NextResponse.json({ error: "unauthorized" }, { status: 401 })

  const db = adminDb()
  const { error } = await db
    .from("config_packs")
    .update({ status: "archived", updated_at: new Date().toISOString() })
    .eq("pack_id", params.packId)
  if (error) return NextResponse.json({ error: error.message }, { status: 500 })

  await db.from("config_release_records").insert({
    pack_id: params.packId,
    version_no: 0,
    action: "archived",
    changed_by: null,
  })
  return NextResponse.json({ ok: true })
}
