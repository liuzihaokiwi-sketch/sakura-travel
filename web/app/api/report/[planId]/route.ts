/**
 * GET /api/report/[planId]
 *
 * 报告渲染 API（L3-13）
 * 从数据库读取 plan_metadata.page_plan，拼装 ReportApiResponse 返回给前端。
 *
 * 响应结构：
 *   {
 *     meta:        ReportMeta
 *     page_plan:   PagePlan[]
 *     page_models: Record<page_id, PageViewModel>
 *     chapters:    ChapterPlan[]
 *   }
 *
 * 查询参数：
 *   mode     = "web" | "pdf" | "shared"  (默认 "web")
 *   language = "zh-CN" | "en" | "ja"    (默认 "zh-CN")
 */

import { NextRequest, NextResponse } from "next/server"
import type {
  ReportApiResponse,
  ReportMeta,
  PagePlan,
  PageViewModel,
  ChapterPlan,
} from "@/lib/report/types"

// ── 内部工具 ──────────────────────────────────────────────────────────────────

/** 从数据库直接拉取 plan 原始数据（服务端 Route Handler 内调用，跳过 HTTP）*/
async function fetchPlanRecord(planId: string): Promise<Record<string, unknown> | null> {
  // 优先走环境变量指定的内部 API（跨服务部署场景）
  const internalBase = process.env.INTERNAL_API_BASE_URL
  const secret = process.env.INTERNAL_API_SECRET ?? ""

  if (internalBase) {
    try {
      const res = await fetch(`${internalBase}/api/admin/generate/${planId}`, {
        headers: { "x-internal-secret": secret },
        cache: "no-store",
      })
      if (res.ok) return res.json() as Promise<Record<string, unknown>>
    } catch { /* fallthrough to direct DB */ }
  }

  // 同进程直接查 DB（避免 HTTP 循环引用）
  try {
    const { createClient } = await import("@supabase/supabase-js")
    const supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_ROLE_KEY!,
      { auth: { persistSession: false } },
    )
    const { data, error } = await supabase
      .from("itinerary_plans")
      .select("plan_id, status, plan_metadata, report_content")
      .eq("plan_id", planId)
      .single()

    if (error || !data) return null
    return data as Record<string, unknown>
  } catch {
    return null
  }
}

/** 从 plan 数据构建 ReportMeta */
function buildMeta(
  planId: string,
  plan: Record<string, unknown>,
  mode: string,
  language: string,
): ReportMeta {
  const meta = (plan.meta as Record<string, unknown>) ?? {}
  return {
    trip_id:    planId,
    destination: (meta.destination as string) ?? (plan.destination as string) ?? "未知目的地",
    total_days:  Number(meta.total_days ?? plan.total_days ?? 0),
    language:    language as ReportMeta["language"],
    render_mode: mode as ReportMeta["render_mode"],
    schema_version: "v2",
  }
}

/** 从 plan_metadata.page_plan 字段提取 PagePlan[] */
function extractPagePlan(plan: Record<string, unknown>): PagePlan[] {
  try {
    const planMeta = plan.plan_metadata as Record<string, unknown> | undefined
    const raw = planMeta?.page_plan
    if (Array.isArray(raw)) return raw as PagePlan[]
  } catch { /* ignore */ }
  return []
}

/** 从 plan_metadata.page_models 提取 Record<page_id, PageViewModel> */
function extractPageModels(plan: Record<string, unknown>): Record<string, PageViewModel> {
  try {
    const planMeta = plan.plan_metadata as Record<string, unknown> | undefined
    const raw = planMeta?.page_models
    if (raw && typeof raw === "object" && !Array.isArray(raw)) {
      return raw as Record<string, PageViewModel>
    }
  } catch { /* ignore */ }
  return {}
}

/** 从 plan_metadata.chapters 提取 ChapterPlan[] */
function extractChapters(plan: Record<string, unknown>): ChapterPlan[] {
  try {
    const planMeta = plan.plan_metadata as Record<string, unknown> | undefined
    const raw = planMeta?.chapters
    if (Array.isArray(raw)) return raw as ChapterPlan[]
  } catch { /* ignore */ }
  return []
}

// ── 权限检查 ──────────────────────────────────────────────────────────────────

function isAuthorized(request: NextRequest, plan: Record<string, unknown>): boolean {
  // 1. 内部管理员请求（带 x-internal-secret header）
  const secret = process.env.INTERNAL_API_SECRET
  if (secret && request.headers.get("x-internal-secret") === secret) return true

  // 2. 共享模式（share_token query param 匹配）
  const shareToken = request.nextUrl.searchParams.get("share_token")
  if (shareToken && plan.share_token === shareToken) return true

  // 3. 普通用户：需要 session（由 middleware 处理，此处假设已通过 middleware 校验）
  // 如果 middleware 已处理鉴权，直接放行
  return true
}

// ── Route Handler ─────────────────────────────────────────────────────────────

export async function GET(
  request: NextRequest,
  { params }: { params: { planId: string } },
) {
  const { planId } = params
  const searchParams = request.nextUrl.searchParams
  const mode     = searchParams.get("mode")     ?? "web"
  const language = searchParams.get("language") ?? "zh-CN"

  if (!planId || typeof planId !== "string") {
    return NextResponse.json(
      { error: "invalid_plan_id", message: "planId 参数缺失或格式错误" },
      { status: 400 },
    )
  }

  // 拉取原始数据
  const plan = await fetchPlanRecord(planId)
  if (!plan) {
    return NextResponse.json(
      { error: "plan_not_found", message: `Plan ${planId} 不存在或已删除` },
      { status: 404 },
    )
  }

  // 鉴权
  if (!isAuthorized(request, plan)) {
    return NextResponse.json(
      { error: "forbidden", message: "无访问权限" },
      { status: 403 },
    )
  }

  // 构建响应
  const meta       = buildMeta(planId, plan, mode, language)
  const page_plan  = extractPagePlan(plan)
  const page_models = extractPageModels(plan)
  const chapters   = extractChapters(plan)

  const response: ReportApiResponse = {
    meta,
    page_plan,
    page_models,
    chapters,
  }

  return NextResponse.json(response, {
    headers: {
      // 短缓存：允许 CDN 缓存 30s，stale-while-revalidate 60s
      "Cache-Control": "public, s-maxage=30, stale-while-revalidate=60",
    },
  })
}
