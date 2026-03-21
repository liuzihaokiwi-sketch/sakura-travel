import { getRushScores } from "@/lib/data";
import RushClient from "./RushClient";

export const metadata = {
  title: "🌸 樱花冲刺排行榜 · Sakura Rush 2026",
  description: "全日本赏樱景点实时排名，花期追踪，本周冲刺推荐",
};

export default function RushPage() {
  const data = getRushScores();
  return <RushClient data={data} />;
}
