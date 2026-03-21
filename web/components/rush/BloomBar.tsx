/**
 * BloomBar.tsx — M3: 花期进度条组件
 * 可复用于地图、时间轴、首页等场景
 *
 * 日期格式支持: "3月25日" / "3/25" / "2026-03-25"
 * 颜色语义:
 *   粉色   (from-pink-300 to-pink-400)  = 开花中
 *   深粉   (from-pink-500 to-rose-600)  = 满开最佳
 *   紫色   (from-purple-400 to-purple-600) = 飘落中
 *   灰色   = 未开花 / 无数据
 */

interface BloomBarProps {
  half?: string;   // 半开日期
  full?: string;   // 满开日期
  fall?: string;   // 飘落日期
  /** 进度条高度，默认 4px */
  height?: "xs" | "sm" | "md";
  /** 是否显示日期标签 */
  showLabels?: boolean;
  className?: string;
}

const SEASON_START = new Date(2026, 2, 10); // 3月10日
const SEASON_END   = new Date(2026, 3, 25); // 4月25日
const SEASON_SPAN  = SEASON_END.getTime() - SEASON_START.getTime();

function parseDate(str?: string): Date | null {
  if (!str) return null;
  // "3月25日"
  const m1 = str.match(/(\d+)月(\d+)日/);
  if (m1) return new Date(2026, parseInt(m1[1]) - 1, parseInt(m1[2]));
  // "3/25"
  const m2 = str.match(/^(\d+)\/(\d+)$/);
  if (m2) return new Date(2026, parseInt(m2[1]) - 1, parseInt(m2[2]));
  // ISO: "2026-03-25"
  const d = new Date(str);
  if (!isNaN(d.getTime())) return d;
  return null;
}

function toPct(d: Date | null): number {
  if (!d) return 0;
  const pct = (d.getTime() - SEASON_START.getTime()) / SEASON_SPAN;
  return Math.max(0, Math.min(100, pct * 100));
}

export function BloomBar({ half, full, fall, height = "sm", showLabels = false, className = "" }: BloomBarProps) {
  const halfD = parseDate(half);
  const fullD = parseDate(full);
  const fallD = parseDate(fall);
  const today = new Date();

  const halfPct = toPct(halfD);
  const fullPct = toPct(fullD);
  const fallPct = toPct(fallD);
  const todayPct = toPct(today);

  // 判断当前阶段
  const isFallen  = fallD  && today > fallD;
  const isFullBloom = fullD && today >= fullD && (!fallD || today <= fallD);
  const isHalfBloom = halfD && today >= halfD && (!fullD || today < fullD);

  // 填充条颜色
  let barColor = "bg-gray-200"; // 未开花
  if (isFallen)    barColor = "bg-gradient-to-r from-purple-400 to-purple-600";
  else if (isFullBloom) barColor = "bg-gradient-to-r from-pink-500 to-rose-600";
  else if (isHalfBloom) barColor = "bg-gradient-to-r from-pink-300 to-pink-400";

  // 填充范围: 从 halfPct 到 today / fallPct 的最小值
  const fillStart = halfPct;
  const fillEnd   = Math.min(todayPct, fallPct || 100);
  const fillWidth = Math.max(0, fillEnd - fillStart);

  const hMap = { xs: "h-1", sm: "h-1.5", md: "h-2.5" };
  const barH = hMap[height];

  return (
    <div className={`w-full ${className}`}>
      {/* Track */}
      <div className={`relative w-full ${barH} rounded-full bg-gray-100 overflow-visible`}>
        {/* Fill */}
        {halfPct < 100 && fillWidth > 0 && (
          <div
            className={`absolute top-0 h-full rounded-full ${barColor}`}
            style={{ left: `${fillStart}%`, width: `${fillWidth}%` }}
          />
        )}

        {/* half marker */}
        {halfD && (
          <div
            className="absolute top-1/2 -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-pink-300 ring-1 ring-white"
            style={{ left: `${halfPct}%` }}
            title={`半开: ${half}`}
          />
        )}

        {/* full marker */}
        {fullD && (
          <div
            className="absolute top-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-rose-500 ring-1 ring-white"
            style={{ left: `${fullPct}%` }}
            title={`满开: ${full}`}
          />
        )}

        {/* fall marker */}
        {fallD && (
          <div
            className="absolute top-1/2 -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-purple-400 ring-1 ring-white"
            style={{ left: `${fallPct}%` }}
            title={`飘落: ${fall}`}
          />
        )}

        {/* today line */}
        <div
          className="absolute top-1/2 -translate-y-1/2 w-0.5 h-3 bg-gray-800/60 rounded-full"
          style={{ left: `${Math.min(todayPct, 99)}%` }}
          title="今天"
        />
      </div>

      {/* Labels */}
      {showLabels && (
        <div className="flex justify-between mt-1 text-[9px] text-gray-400">
          {half  && <span className="text-pink-400">半 {half.replace("2026-", "").replace(/-0?/, "/")}</span>}
          {full  && <span className="text-rose-500 font-semibold">满 {full.replace("2026-", "").replace(/-0?/, "/")}</span>}
          {fall  && <span className="text-purple-400">落 {fall.replace("2026-", "").replace(/-0?/, "/")}</span>}
        </div>
      )}
    </div>
  );
}
