import { NextResponse } from "next/server"

export async function GET() {
  return NextResponse.json(
    {
      error: "legacy_report_api_retired",
      message:
        "旧 report API 已退出主路径，请改用 /api/plan/{id}/page-models 与 /api/plan/{id}/page-render。",
    },
    { status: 410 },
  )
}

