import type { Metadata } from "next";
import Link from "next/link";
import koyoData from "@/data/koyo/spots.json";

export const metadata: Metadata = {
  title: "2026日本红叶见顷预报",
  description: "2026年日本各地红叶见顷预测时间、推荐赏枫地点和实用小贴士，从北海道到关西全覆盖",
  openGraph: {
    title: "2026日本红叶见顷预报",
    description: "从北海道到关西，全国红叶见顷时间一览",
  },
};

interface KoyoSpot {
  name: string;
  peak: string;
  type: string;
  score: number;
  note: string;
  tips: string;
}

interface KoyoRegion {
  key: string;
  name: string;
  emoji: string;
  status: string;
  season: string;
  spots: KoyoSpot[];
}

interface KoyoData {
  year: number;
  updated: string;
  regions: KoyoRegion[];
  tips: string[];
  totalSpots?: number;
}

const data = koyoData as KoyoData;

// ── Score Bar ────────────────────────────────────────────────────────────────

function ScoreBar({ score }: { score: number }) {
  const color = score >= 95 ? "bg-red-500" : score >= 90 ? "bg-orange-500" : "bg-amber-400";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-stone-100 rounded-full h-1.5 overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${score}%` }} />
      </div>
      <span className="text-xs font-bold text-stone-700 w-6 text-right">{score}</span>
    </div>
  );
}

// ── Spot Card ────────────────────────────────────────────────────────────────

function SpotCard({ spot }: { spot: KoyoSpot }) {
  return (
    <div className="bg-white rounded-xl border border-stone-100 p-4 hover:border-orange-200 hover:shadow-sm transition-all">
      <div className="flex items-start justify-between gap-2 mb-2">
        <div>
          <h4 className="text-sm font-bold text-stone-900">{spot.name}</h4>
          <span className="text-[10px] text-stone-400 bg-stone-50 px-1.5 py-0.5 rounded">{spot.type}</span>
        </div>
        <div className="shrink-0 text-center bg-orange-50 rounded-lg px-2.5 py-1.5 border border-orange-100">
          <div className="text-lg font-black text-orange-600 leading-none">{spot.score}</div>
          <div className="text-[8px] text-orange-400 font-bold mt-0.5">好看指数</div>
        </div>
      </div>
      <ScoreBar score={spot.score} />
      <div className="mt-2 space-y-1">
        <p className="text-xs text-stone-600">
          <span className="font-semibold text-orange-600">🍁 见顷：</span>{spot.peak}
        </p>
        <p className="text-xs text-stone-500">{spot.note}</p>
        <p className="text-xs text-amber-700 bg-amber-50 rounded px-2 py-1">
          💡 {spot.tips}
        </p>
      </div>
    </div>
  );
}

// ── Region Section ───────────────────────────────────────────────────────────

function RegionSection({ region }: { region: KoyoRegion }) {
  return (
    <section className="mb-8">
      <div className="flex items-center gap-3 mb-4">
        <span className="text-2xl">{region.emoji}</span>
        <div>
          <h2 className="text-lg font-extrabold text-stone-900">{region.name}</h2>
          <p className="text-xs text-stone-500">
            <span className="font-semibold text-orange-600">见顷时期：</span>{region.season}
            <span className="ml-3 text-stone-400">· {region.status}</span>
          </p>
        </div>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {region.spots.map((spot) => (
          <SpotCard key={spot.name} spot={spot} />
        ))}
      </div>
    </section>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function KoyoPage() {
  const totalSpots = data.regions.reduce((acc, r) => acc + r.spots.length, 0);

  return (
    <div>
      {/* Hero */}
      <div className="bg-gradient-to-br from-stone-900 via-stone-800 to-[#2d1a0a] text-white rounded-2xl px-6 py-10 mb-8 overflow-hidden relative">
        <div className="absolute right-4 top-4 text-[120px] opacity-[0.05] pointer-events-none select-none">🍁</div>
        <div className="relative z-10">
          <span className="inline-block text-[10px] font-semibold text-orange-300 border border-orange-300/30 px-2.5 py-1 rounded tracking-widest uppercase mb-3">
            KOYO FORECAST {data.year}
          </span>
          <h1 className="text-2xl md:text-3xl font-black leading-tight mb-2">
            {data.year}年 日本红叶<br />
            <em className="not-italic text-orange-300">见顷预报</em>
          </h1>
          <p className="text-xs text-white/50">数据更新于 {data.updated} · 红叶时期受气温影响，仅供参考</p>

          <div className="grid grid-cols-3 gap-3 mt-5 max-w-xs">
            {[
              { val: `${totalSpots}+`, label: "景点" },
              { val: `${data.regions.length}`, label: "地区" },
              { val: "年度更新", label: "维护频率" },
            ].map((item) => (
              <div key={item.label} className="text-center bg-white/5 rounded-lg py-2">
                <div className="text-lg font-black text-orange-300">{item.val}</div>
                <div className="text-[9px] text-white/40 mt-0.5">{item.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 时间轴提示 */}
      <div className="mb-6 overflow-x-auto pb-2">
        <div className="flex items-center gap-2 min-w-max">
          {data.regions.map((region) => (
            <a key={region.key} href={`#${region.key}`} className="flex-shrink-0 bg-white border border-stone-200 rounded-full px-3 py-1.5 text-xs font-semibold text-stone-700 hover:border-orange-300 hover:text-orange-700 transition-colors">
              {region.emoji} {region.name}
              <span className="ml-1.5 text-stone-400 text-[10px]">{region.season.split("-")[0]}</span>
            </a>
          ))}
        </div>
      </div>

      {/* 各地区 */}
      {data.regions.map((region) => (
        <div key={region.key} id={region.key}>
          <RegionSection region={region} />
        </div>
      ))}

      {/* 贴士 */}
      <section className="bg-amber-50 border border-amber-100 rounded-2xl p-5 mb-6">
        <h3 className="text-sm font-bold text-stone-900 mb-3">🍂 赏枫实用贴士</h3>
        <ul className="space-y-2">
          {data.tips.map((tip, i) => (
            <li key={i} className="text-xs text-stone-600 flex gap-2">
              <span className="text-orange-400 font-bold shrink-0">{i + 1}.</span>
              <span>{tip}</span>
            </li>
          ))}
        </ul>
      </section>

      {/* CTA */}
      <div className="bg-gradient-to-br from-orange-50 to-amber-50 border border-orange-100 rounded-2xl p-6 text-center">
        <h3 className="text-lg font-extrabold text-stone-900 mb-2">
          想要一份完整的赏枫行程？
        </h3>
        <p className="text-sm text-stone-500 mb-4">
          精确到每日路线 · 含交通换乘 · 推荐餐厅 · 30-40页手册
        </p>
        <Link
          href="/quiz?from=koyo_tool"
          className="inline-block bg-gradient-to-r from-amber-500 to-orange-500 text-white font-bold text-sm px-6 py-3 rounded-full shadow-lg hover:shadow-xl hover:-translate-y-0.5 transition-all"
        >
          免费定制行程 →
        </Link>
      </div>
    </div>
  );
}
