/**
 * GET  /api/admin/config         列出所有配置包
 * POST /api/admin/config         创建新配置包（草稿）
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

export async function GET(request: NextRequest) {
  const auth = await requireAdminSession(request)
  if (!auth.ok) return NextResponse.json({ error: "unauthorized" }, { status: 401 })

  const db = adminDb()
  const { searchParams } = request.nextUrl
  const status    = searchParams.get("status")
  const pack_type = searchParams.get("pack_type")

  let query = db
    .from("config_packs")
    .select(`
      pack_id, name, description, pack_type, active_version_no, status,
      created_by, created_at, updated_at,
      config_scopes ( scope_id, scope_type, scope_value, rollout_pct, is_active )
    `)
    .order("updated_at", { ascending: false })
    .limit(100)

  if (status)    query = query.eq("status", status)
  if (pack_type) query = query.eq("pack_type", pack_type)

  const { data, error } = await query
  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json({ packs: data })
}

export async function POST(request: NextRequest) {
  const auth = await requireAdminSession(request)
  if (!auth.ok) return NextResponse.json({ error: "unauthorized" }, { status: 401 })

  const body = await request.json()
  const { name, description, pack_type = "weights" } = body

  if (!name?.trim()) {
    return NextResponse.json({ error: "name is required" }, { status: 400 })
  }

  const db = adminDb()
  const { data, error } = await db
    .from("config_packs")
    .insert({ name: name.trim(), description, pack_type, status: "draft" })
    .select()
    .single()

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json({ pack: data }, { status: 201 })
}
