/**
 * RushHome.tsx — M1: Rush 首页 Section
 * 包含: Hero 数据统计 + 本周 HOT 推荐网格 + 城市概览卡 + 数据来源信任条
 * 服务端组件，使用 RushData（来自 getRushData()）
 */

import Image from "next/image";
import { BloomBar } from "@/components/rush/BloomBar";
import type { RushData, RushCity, RushSpot } from "@/lib/rush-data";

interface RushHomeProps {
  data: RushData;
}

// ── Helper: 景点状态标签 ─────────────────────────────────────────────────

function bloomLabel(s: RushSpot): { label: string; cls: string } {
  const today = new Date();
  function toD(str?: string) {
    if (!str) return null;
    const m = str.match(/(\d+)月(\d+)日/);
    if (m) return new Date(2026, parseInt(m[1]) - 1, parseInt(m[2]));
    return null;
  }
  const halfD = toD(s.half);
  const fullD = toD(s.full);
  const fallD = toD(s.fall);
  if (fallD && today > fallD)  return { label: "飘落中",  cls: "text-purple-500" };
  if (fullD && today >= fullD) return { label: "🔥 满开", cls: "text-rose-600 font-bold" };
  if (halfD && today >= halfD) return { label: "开花中",  cls: "text-pink-500" };
  if (halfD) {
    const days = Math.ceil((halfD.getTime() - today.getTime()) / 864e5);
    return { label: `${days}天后开`, cls: "text-amber-500" };
  }
  return { label: "待定", cls: "text-gray-400" };
}

// ── HOT 推荐卡片 ─────────────────────────────────────────────────────────

function HotCard({ spot, rank }: { spot: RushSpot; rank: number }) {
  const status = bloomLabel(spot);
  const rankCls = rank === 1 ? "bg-gray-900" : rank === 2 ? "bg-gray-500" : "bg-gray-300";

  return (
    <div className="flex items-start gap-2 p-2.5 border border-gray-100 rounded-xl hover:border-pink-200 hover:shadow-sm transition-all cursor-pointer">
      <span className={`shrink-0 mt-0.5 w-6 h-6 rounded-md text-[11px] font-black text-white flex items-center justify-center ${rankCls}`}>
        {rank}
      </span>

      {spot.photo ? (
        <div className="relative shrink-0 w-14 h-14 rounded-lg overflow-hidden">
          <Image src={spot.photo} alt={spot.name_cn ?? spot.name} fill className="object-cover" sizes="56px" />
        </div>
      ) : (
        <div className="shrink-0 w-14 h-14 rounded-lg bg-gradient-to-br from-pink-100 to-pink-200 flex items-center justify-center text-lg">🌸</div>
      )}

      <div className="flex-1 min-w-0">
        <div className="text-xs font-bold text-gray-900 truncate">{spot.name_cn ?? spot.name}</div>
        <div className="text-[10px] text-gray-400 mt-0.5">{spot.region ?? ""}</div>
        <div className="flex flex-wrap gap-1 mt-1">
          {spot.meisyo100 && <span className="text-[9px] px-1.5 py-0.5 bg-amber-50 text-amber-600 rounded">名所100选</span>}
          {spot.lightup   && <span className="text-[9px] px-1.5 py-0.5 bg-purple-50 text-purple-500 rounded">夜樱</span>}
          {spot.namiki    && <span className="text-[9px] px-1.5 py-0.5 bg-green-50 text-green-600 rounded">并木道</span>}
        </div>
        <BloomBar half={spot.half} full={spot.full} fall={spot.fall} height="xs" className="mt-1.5" />
      </div>

      <div className="shrink-0 text-right">
        <div className={`text-[10px] font-semibold ${status.cls}`}>{status.label}</div>
        <div className="text-lg font-black text-rose-600 leading-tight">{spot.score}</div>
      </div>
    </div>
  );
}

// ── 城市概览卡 ───────────────────────────────────────────────────────────

function CityCard({ city }: { city: RushCity }) {
  const top3 = city.spots.slice(0, 3);

  return (
    <div className="border border-gray-100 rounded-xl overflow-hidden hover:border-pink-200 hover:shadow-sm transition-all cursor-pointer">
      <div className="flex items-center gap-2 px-3 py-2.5 bg-gray-50 border-b border-gray-100">
        <span className="text-xl">{city.emoji}</span>
        <span className="text-sm font-black text-gray-900">{city.name}</span>
        <span className={`ml-1 text-[9px] font-bold text-white px-2 py-0.5 rounded ${city.bloomCount > 0 ? "bg-green-600" : "bg-orange-500"}`}>
          {city.bloomCount > 0 ? "满开中" : city.status}
        </span>
        <span className="ml-auto text-[10px] text-gray-400">{city.spotCount} 景点</span>
      </div>

      <div className="flex gap-2 px-3 py-2.5">
        {top3.map((s) => (
          <div key={s.id} className="flex-1 text-center">
            {s.photo ? (
              <div className="relative w-full aspect-square rounded-md overflow-hidden mb-1">
                <Image src={s.photo} alt={s.name_cn ?? s.name} fill className="object-cover" sizes="80px" />
              </div>
            ) : (
              <div className="w-full aspect-square rounded-md bg-gradient-to-br from-pink-100 to-pink-200 flex items-center justify-center text-base mb-1">🌸</div>
            )}
            <div className="text-[9px] font-bold text-gray-800 truncate">{s.name_cn ?? s.name}</div>
            <div className="text-[8px] text-rose-500 font-semibold">{s.full ? `满 ${s.full}` : ""}</div>
          </div>
        ))}
      </div>

      <div className="flex border-t border-gray-100">
        {[
          { v: city.bloomCount,                                            l: "满开景点" },
          { v: city.spots.filter((s) => s.meisyo100).length, l: "名所100选" },
          { v: city.spots.filter((s) => s.lightup).length,   l: "夜樱灯光" },
        ].map(({ v, l }) => (
          <div key={l} className="flex-1 text-center py-2 border-r last:border-r-0 border-gray-100">
            <div className="text-xs font-black text-gray-900">{v}</div>
            <div className="text-[8px] text-gray-400">{l}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Main ─────────────────────────────────────────────────────────────────────

const SOURCES = [
  "WeatherNews 200万用户报告", "気象庁 JMA 官方预测", "日本花见カレンダー",
  "全国花見マップ", "桜開花予想 2026", "现地旅居团队实测",
];

export default function RushHome({ data }: RushHomeProps) {
  const hotSpots: Array<{ spot: RushSpot; rank: number }> = data.cities.flatMap((c) =>
    c.spots.slice(0, 3).map((s, i) => ({ spot: s, rank: i + 1 }))
  );

  return (
    <div className="w-full bg-white">

      {/* ── Hero ──────────────────────────────────────────────────────────── */}
      <section className="relative bg-gradient-to-br from-gray-900 via-[#2d1a22] to-gray-900 px-5 py-8 sm:px-10 sm:py-10 overflow-hidden">
        <span className="pointer-events-none absolute -top-5 -right-5 text-[140px] opacity-[0.03] select-none">🌸</span>
        <div className="relative z-10 max-w-4xl mx-auto">
          <span className="inline-block text-[10px] font-semibold tracking-widest text-pink-300 border border-pink-300/30 px-3 py-1 rounded mb-3">
            🔬 DATA-DRIVEN SAKURA TRACKING
          </span>
          <h2 className="text-2xl sm:text-4xl font-black text-white leading-tight mb-2">
            今年樱花，<span className="text-pink-300">该不该冲</span><br className="sm:hidden" />一眼看清
          </h2>
          <p className="text-xs sm:text-sm text-white/40 mb-5">
            融合 6 大权威数据源 · 覆盖 5 座热门城市 {data.totalSpots}+ 景点 · 每天更新 3 次 · 精确到 ±2 天
          </p>
          <div className="flex gap-6 sm:gap-10 flex-wrap">
            {[
              { v: `${data.totalSpots}+`, l: "实测景点" },
              { v: "6",                   l: "权威数据源" },
              { v: "3次/天",              l: "更新频率" },
              { v: "±2天",               l: "预测精度" },
            ].map(({ v, l }) => (
              <div key={l} className="text-center">
                <div className="text-2xl sm:text-4xl font-black text-pink-300">{v}</div>
                <div className="text-[10px] text-white/30 mt-0.5">{l}</div>
              </div>
            ))}
          </div>
          <p className="mt-4 text-[10px] text-white/20">数据更新时间: {data.updatedAt} · {data.weekLabel}</p>
        </div>
      </section>

      {/* ── 本周 HOT 推荐 ────────────────────────────────────────────────── */}
      <section className="px-4 sm:px-6 py-5">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-2 mb-3">
            <h3 className="text-base font-black text-gray-900">🔥 本周 HOT 推荐</h3>
            <span className="text-[10px] text-pink-500 font-semibold ml-auto">各城 TOP 3 · 共 {hotSpots.length} 个</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {hotSpots.map(({ spot, rank }, i) => (
              <HotCard key={`${spot.id}-${i}`} spot={spot} rank={rank} />
            ))}
          </div>
        </div>
      </section>

      {/* ── 城市概览卡 ──────────────────────────────────────────────────── */}
      <section className="px-4 sm:px-6 py-4 border-t border-gray-100">
        <div className="max-w-4xl mx-auto">
          <h3 className="text-base font-black text-gray-900 mb-3">🗾 5 城实况一览</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {data.cities.map((c) => (
              <CityCard key={c.key} city={c} />
            ))}
          </div>
        </div>
      </section>

      {/* ── 数据来源信任条 ───────────────────────────────────────────────── */}
      <section className="px-4 sm:px-6 py-4 bg-gray-50 border-t border-gray-100">
        <div className="max-w-4xl mx-auto">
          <div className="text-[10px] font-semibold text-gray-400 mb-2">📡 数据来源</div>
          <div className="flex flex-wrap gap-1.5">
            {SOURCES.map((s) => (
              <span key={s} className="text-[10px] px-2 py-1 rounded bg-white border border-gray-200 text-gray-500 font-medium">
                {s}
              </span>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}