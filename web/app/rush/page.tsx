import { getRushScores } from "@/lib/data";
import RushClient from "./RushClient";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "2026 日本樱花实时追踪 — 240+ 景点花期数据",
  description: "实时追踪全日本 240+ 赏樱景点花期数据，融合气象厅等 6 大权威数据源。查看东京、京都、大阪最新开花状态和最佳赏樱时间。",
  openGraph: {
    title: "🌸 2026 日本樱花实时追踪",
    description: "融合 6 大权威数据源，240+ 景点实时花期 · 每天更新 3 次",
    url: "/rush",
  },
};

// ISR: 每 30 分钟自动刷新，数据更新不需要重新部署
export const revalidate = 1800;

export default function RushPage() {
  const data = getRushScores();
  return <RushClient data={data} />;
}