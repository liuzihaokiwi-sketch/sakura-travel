/**
 * POST /api/admin/config/[packId]/preview
 * 触发预览对比运行（异步）
 * body: { version_no, subjects: [{type: "order"|"eval_case", id: string}] }
 *
 * GET  /api/admin/config/[packId]/preview
 * 查询该 pack 所有预览运行记录
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

export async function GET(
  request: NextRequest,
  { params }: { params: { packId: string } },
) {
  const auth = await requireAdminSession(request)
  if (!auth.ok) return NextResponse.json({ error: "unauthorized" }, { status: 401 })

  const db = adminDb()
  const { data, error } = await db
    .from("config_preview_runs")
    .select("*")
    .eq("pack_id", params.packId)
    .order("created_at", { ascending: false })
    .limit(20)

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json({ runs: data })
}

export async function POST(
  request: NextRequest,
  { params }: { params: { packId: string } },
) {
  const auth = await requireAdminSession(request)
  if (!auth.ok) return NextResponse.json({ error: "unauthorized" }, { status: 401 })

  const body = await request.json()
  const { version_no, subjects } = body as {
    version_no: number
    subjects: Array<{ type: "order" | "eval_case"; id: string }>
  }

  if (!subjects?.length) {
    return NextResponse.json({ error: "subjects required" }, { status: 400 })
  }
  if (subjects.length > 5) {
    return NextResponse.json({ error: "最多 5 个预览对象" }, { status: 400 })
  }

  const db = adminDb()
  const runs = subjects.map((s) => ({
    pack_id:      params.packId,
    version_no,
    subject_type: s.type,
    subject_id:   s.id,
    status:       "pending",
  }))

  const { data, error } = await db
    .from("config_preview_runs")
    .insert(runs)
    .select()

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })

  // TODO P1: 触发异步 arq job 执行预览对比
  // await enqueueJob("run_config_preview", { run_ids: data.map(r => r.run_id) })

  return NextResponse.json({ runs: data }, { status: 201 })
}
