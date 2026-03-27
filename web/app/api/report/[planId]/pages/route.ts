import { NextResponse } from "next/server"

export async function GET() {
  return NextResponse.json(
    {
      error: "legacy_report_pages_api_retired",
      message:
        "旧 report/pages API 已退出主路径，请改用 /api/plan/{id}/page-models 读取 page-model-first 数据。",
    },
    { status: 410 },
  )
}

