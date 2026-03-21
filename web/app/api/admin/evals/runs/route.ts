import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

/**
 * GET /api/admin/evals/runs — 读取 evals/runs/ 下所有 JSON 结果
 * 直接读文件系统（评测结果保存在 evals/runs/*.json）
 */
export async function GET() {
  try {
    const runsDir = path.join(process.cwd(), "..", "evals", "runs");

    if (!fs.existsSync(runsDir)) {
      return NextResponse.json([]);
    }

    const files = fs
      .readdirSync(runsDir)
      .filter((f) => f.endsWith(".json"))
      .sort()
      .reverse(); // 最新的在前

    const runs = files.map((f) => {
      const content = fs.readFileSync(path.join(runsDir, f), "utf-8");
      return JSON.parse(content);
    });

    return NextResponse.json(runs);
  } catch (e) {
    console.error("Failed to load eval runs:", e);
    return NextResponse.json([]);
  }
}
