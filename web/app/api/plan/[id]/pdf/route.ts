import { NextRequest, NextResponse } from "next/server";

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  return NextResponse.json(
    {
      error: "legacy_pdf_route_retired",
      message:
        "旧 PDF 导出代理已退出主路径。请改用 page-model-first 的 shared export contract 导出链路。",
    },
    { status: 410 },
  );
}
