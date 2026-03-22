/**
 * web/app/api/report/[planId]/pages/route.ts — 报告 API 端点（L3-13）
 *
 * GET /api/report/{planId}/pages
 *
 * 返回：
 *   { meta, page_plan, page_models, chapters }
 *
 * 优先读取 plan_metadata.page_plan（持久化版本，F8），
 * 若无则临时从 report_content 重新规划。
 */

import { NextRequest, NextResponse } from "next/server"

const BACKEND_BASE = process.env.BACKEND_URL ?? "http://localhost:8000"

export async function GET(
  req: NextRequest,
  { params }: { params: { planId: string } }
) {
  const { planId } = params

  try {
    // 1. 从后端获取计划数据
    const planRes = await fetch(
      `${BACKEND_BASE}/api/plans/${planId}/report`,
      {
        headers: {
          "Content-Type": "application/json",
          // 透传鉴权 cookie
          Cookie: req.headers.get("cookie") ?? "",
        },
        cache: "no-store",
      }
    )

    if (!planRes.ok) {
      return NextResponse.json(
        { error: `后端返回 ${planRes.status}`, planId },
        { status: planRes.status }
      )
    }

    const planData = await planRes.json()

    // 2. 如果后端直接返回了 page_plan（持久化版本，F8）
    const reportContent = planData.report_content ?? planData
    const persistedPagePlan = planData.plan_metadata?.page_plan ?? null

    // 3. 构建响应
    //    - page_plan：优先使用持久化版本
    //    - page_models：由后端 /api/plans/{planId}/render 提供，或此处从 report_content 解析
    const response = {
      meta: reportContent.meta ?? null,
      page_plan: persistedPagePlan ?? reportContent.page_plan ?? [],
      page_models: reportContent.page_models ?? {},
      chapters: reportContent.chapters ?? [],
    }

    // 4. 如果后端没有 page_plan，尝试调用 render 端点重新规划
    if (!response.page_plan || response.page_plan.length === 0) {
      try {
        const renderRes = await fetch(
          `${BACKEND_BASE}/api/plans/${planId}/render`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Cookie: req.headers.get("cookie") ?? "",
            },
            body: JSON.stringify({ plan_id: planId }),
            cache: "no-store",
          }
        )
        if (renderRes.ok) {
          const renderData = await renderRes.json()
          response.page_plan = renderData.page_plan ?? []
          response.page_models = renderData.page_models ?? {}
          response.chapters = renderData.chapters ?? []
        }
      } catch {
        // render 端点不可用时忽略，返回空 page_plan
      }
    }

    return NextResponse.json(response)
  } catch (err) {
    console.error("[report/pages] error:", err)
    return NextResponse.json(
      { error: "内部错误", detail: String(err) },
      { status: 500 }
    )
  }
}
