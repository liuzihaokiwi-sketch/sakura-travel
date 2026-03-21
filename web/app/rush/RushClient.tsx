"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence, useInView } from "framer-motion";
import dynamic from "next/dynamic";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ENTRY_COPY } from "@/lib/content/segmentation";
import { cn } from "@/lib/utils";
import { fadeInUp, staggerContainer } from "@/lib/animations";
import { WECHAT_ID } from "@/lib/constants";
import { getCityCoord } from "@/lib/city-coords";
import type { RushScores, CityData, Spot } from "@/lib/data";

const SakuraMap = dynamic(() => import("@/components/rush/SakuraMap"), {
  ssr: false,
  loading: () => <div className="w-full h-[400px] bg-stone-100 rounded-2xl flex items-center justify-center"><span className="text-stone-400 text-sm">🗺️ 地图加载中...</span></div>,
});

function getBloomStage(spot: Spot): { label: string; color: string; key: string } {
  if (spot.stage === "full_bloom" || spot.full) return { label: "🌸 満開", color: "bg-pink-100 text-pink-700", key: "full" };
  if (spot.stage === "approaching" || spot.half) return { label: "🌱 五分咲", color: "bg-green-100 text-green-700", key: "half" };
  if (spot.stage === "starting") return { label: "🌱 三分咲", color: "bg-emerald-50 text-emerald-600", key: "starting" };
  if (spot.stage === "falling") return { label: "🍃 散り始め", color: "bg-amber-100 text-amber-700", key: "falling" };
  return { label: "⏳ 未開", color: "bg-stone-100 text-stone-500", key: "dormant" };
}

function getCitySummary(city: CityData): string {
  const stages = city.spots.map(s => getBloomStage(s).key);
  if (stages.includes("full")) return "已满开";
  if (stages.includes("half")) return "五分咲";
  if (stages.includes("starting")) return "三分咲";
  return "未開";
}

function HeroSection({ data }: { data: RushScores }) {
  const statusText = data.cities.map(c => `${c.city_name_cn} ${getCitySummary(c)}`).join(" · ");
  return (
    <section className="relative bg-gradient-to-b from-stone-900 via-stone-800 to-stone-900 text-white overflow-hidden">
      <div className="absolute inset-0 opacity-5 text-[200px] leading-none select-none pointer-events-none flex items-center justify-center">🌸</div>
      <div className="relative max-w-4xl mx-auto px-4 py-16 md:py-20 text-center">
        <motion.div {...fadeInUp}>
          <p className="text-xs tracking-[0.3em] text-white/30 font-mono mb-4">SAKURA RUSH 2026</p>
          <h1 className="font-display text-3xl md:text-5xl font-bold mb-3">2026 日本樱花实时追踪</h1>
          <p className="text-sm md:text-base text-white/60 max-w-lg mx-auto mb-6">融合 6 大权威数据源 · 覆盖 240+ 赏樱景点 · 每天更新 3 次</p>
          <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm rounded-full px-4 py-2 mb-8">
            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            <span className="text-sm text-white/80">{statusText}</span>
          </div>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <Button variant="warm" size="lg" className="rounded-full px-8" onClick={() => document.getElementById("rankings")?.scrollIntoView({ behavior: "smooth" })}>查看景点排行 ↓</Button>
            <Link href="/quiz"><Button variant="outline" size="lg" className="rounded-full px-8 border-white/20 text-white hover:bg-white/10">帮我安排进行程 →</Button></Link>
          </div>
          <p className="text-xs text-white/20 mt-6 font-mono">最后更新：{data.updated_at}</p>
        </motion.div>
      </div>
    </section>
  );
}

function CityTabs({ cities, active, onChange }: { cities: CityData[]; active: string; onChange: (c: string) => void }) {
  return (
    <div className="flex items-center gap-1 bg-stone-100 rounded-xl p-1 overflow-x-auto scrollbar-hide">
      {cities.map(city => (
        <button key={city.city_code} onClick={() => onChange(city.city_code)} className={cn("relative px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors", active === city.city_code ? "text-white" : "text-stone-500 hover:text-stone-700")}>
          {active === city.city_code && <motion.div layoutId="rush-city-tab" className="absolute inset-0 bg-gradient-to-r from-warm-400 to-rose-400 rounded-lg" transition={{ type: "spring", bounce: 0.15, duration: 0.4 }} />}
          <span className="relative z-10">{city.city_name_cn} ({city.spots.length})</span>
        </button>
      ))}
    </div>
  );
}

function SpotCard({ spot, rank, onClick }: { spot: Spot; rank: number; onClick: () => void }) {
  const bloom = getBloomStage(spot);
  return (
    <motion.div variants={fadeInUp} onClick={onClick} className="group bg-white rounded-xl border border-stone-100 overflow-hidden hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200 cursor-pointer flex flex-col">
      <div className="relative h-32 sm:h-36 overflow-hidden bg-gradient-to-br from-stone-100 to-stone-200">
        {spot.photo ? <img src={spot.photo} alt={spot.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" loading="lazy" /> : <div className="w-full h-full flex items-center justify-center"><span className="text-5xl opacity-20">🌸</span></div>}
        <div className="absolute top-2 left-2 w-6 h-6 rounded-full bg-stone-900/70 flex items-center justify-center text-white text-[10px] font-bold">{rank}</div>
        <div className="absolute top-2 right-2 bg-black/60 text-white text-[10px] font-mono font-bold px-1.5 py-0.5 rounded-full">{spot.score}</div>
        <div className="absolute bottom-2 left-2"><span className={cn("text-[10px] font-medium px-2 py-0.5 rounded-full", bloom.color)}>{bloom.label}</span></div>
      </div>
      <div className="p-2.5 flex-1 flex flex-col">
        <h3 className="text-xs font-bold text-stone-900 leading-tight mb-1 line-clamp-1">{spot.name}</h3>
        <div className="flex flex-wrap gap-x-2 text-[9px] text-stone-400 mb-1.5">{spot.half && <span>🌱 {spot.half}</span>}{spot.full && <span>🌸 {spot.full}</span>}</div>
        <div className="mt-auto flex flex-wrap gap-0.5">
          {spot.lightup && <span className="text-[8px] bg-indigo-50 text-indigo-500 px-1 py-0.5 rounded">🌙 夜樱</span>}
          {spot.meisyo100 && <span className="text-[8px] bg-amber-50 text-amber-600 px-1 py-0.5 rounded">⭐ 名所</span>}
          {spot.trees && <span className="text-[8px] bg-green-50 text-green-600 px-1 py-0.5 rounded">🌳 {spot.trees}</span>}
        </div>
      </div>
    </motion.div>
  );
}

function SpotDetailDrawer({ spot, onClose }: { spot: Spot | null; onClose: () => void }) {
  if (!spot) return null;
  const bloom = getBloomStage(spot);
  return (
    <>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 bg-black/40 z-40" onClick={onClose} />
      <motion.div initial={{ x: "100%" }} animate={{ x: 0 }} exit={{ x: "100%" }} transition={{ type: "spring", bounce: 0.1, duration: 0.4 }} className="fixed top-0 right-0 bottom-0 w-full max-w-md bg-white z-50 overflow-y-auto shadow-2xl max-md:top-auto max-md:rounded-t-2xl max-md:max-w-full max-md:h-[85vh]">
        <button onClick={onClose} className="absolute top-3 right-3 z-10 w-8 h-8 rounded-full bg-black/10 flex items-center justify-center text-stone-600 hover:bg-black/20">✕</button>
        <div className="h-48 bg-gradient-to-br from-stone-100 to-stone-200 overflow-hidden">
          {spot.photo ? <img src={spot.photo} alt={spot.name} className="w-full h-full object-cover" /> : <div className="w-full h-full flex items-center justify-center text-6xl opacity-20">🌸</div>}
        </div>
        <div className="p-5 space-y-4">
          <div>
            <h3 className="text-xl font-bold text-stone-900">{spot.name}</h3>
            {spot.name_ja && <p className="text-xs text-stone-400">{spot.name_ja}</p>}
            <div className="flex items-center gap-3 mt-2">
              <span className={cn("text-xs font-medium px-2 py-1 rounded-full", bloom.color)}>{bloom.label}</span>
              <span className="text-2xl font-black text-warm-500 font-mono">{spot.score}</span>
              <span className="text-[10px] text-stone-400">能冲指数</span>
            </div>
          </div>
          {(spot.half || spot.full || spot.fall) && <div className="bg-stone-50 rounded-lg p-3"><p className="text-[10px] text-stone-400 mb-2 font-medium">花期日历</p><div className="flex items-center gap-2 text-xs">{spot.half && <span className="text-green-600">🌱 五分咲 {spot.half}</span>}{spot.full && <span className="text-pink-600">🌸 満開 {spot.full}</span>}{spot.fall && <span className="text-amber-600">🍃 散り {spot.fall}</span>}</div></div>}
          {spot.trees && <div className="flex items-center gap-2 text-sm text-stone-600"><span>🌳</span> 约 {spot.trees} 棵樱花树</div>}
          {spot.lightup && <div className="flex items-center gap-2 text-sm text-indigo-600"><span>🌙</span> 设有夜樱灯光</div>}
          {spot.festival && <div className="flex items-center gap-2 text-sm text-rose-600"><span>🎪</span> 祭典：{spot.festival}</div>}
          {spot.desc_cn && <p className="text-xs text-stone-500 leading-relaxed">{spot.desc_cn}</p>}
          <div className="pt-2 space-y-2">
            <Link href={`/quiz?spot=${encodeURIComponent(spot.name)}`} className="block"><Button variant="warm" className="w-full rounded-full">帮我安排进行程 →</Button></Link>
            <button onClick={async () => { const url = `${window.location.origin}/rush?spot=${encodeURIComponent(spot.name)}`; if (navigator.share) { try { await navigator.share({ title: spot.name, url }); } catch {} } else { await navigator.clipboard.writeText(url); alert("景点链接已复制！"); } }} className="w-full text-xs text-stone-400 hover:text-warm-500 py-2">📤 分享这个景点</button>
          </div>
        </div>
      </motion.div>
    </>
  );
}

const DATA_SOURCES = [
  { name: "日本气象厅", desc: "全国 58 个标本木观测点官方数据" },
  { name: "日本气象协会", desc: "基于 AI 模型的花期预测" },
  { name: "Weathernews", desc: "700+ 景点用户投稿实况" },
  { name: "地方观光协会", desc: "各地官方赏樱情报" },
  { name: "历史数据", desc: "过去 10 年花期统计" },
  { name: "AI 融合引擎", desc: "多源数据交叉验证与评分" },
];

const FAQ_ITEMS = [
  { q: "2026 年日本樱花什么时候开？", a: "预计 3 月中旬从九州开始开花，3 月下旬至 4 月上旬东京、京都、大阪陆续满开，4 月中下旬北海道迎来花期。" },
  { q: "东京最佳赏樱景点有哪些？", a: "上野公园（约 800 棵）、新宿御苑（65 品种 1100 棵）、千鸟渊、目黑川、代代木公园等。建议避开周末下午。" },
  { q: "京都和东京哪个赏樱更好？", a: "东京樱花早 3-5 天，景点集中交通便利；京都寺庙庭园搭配樱花出片率极高。首次建议东京，文化体验选京都。" },
  { q: "日本赏樱最佳时间是几月？", a: "热门城市最佳时间 3 月下旬至 4 月上旬。满开通常只持续 5-7 天，建议根据实时数据灵活调整。" },
  { q: "夜樱是什么？哪些景点有？", a: "夜间灯光照射下的樱花。上野公园、千鸟渊、目黑川、円山公園、二条城等都有，通常到 20:00-21:00。" },
];

export default function RushClient({ data }: { data: RushScores }) {
  const [activeCity, setActiveCity] = useState(data.cities[0]?.city_code || "tokyo");
  const [selectedSpot, setSelectedSpot] = useState<Spot | null>(null);
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInView = useInView(mapRef, { once: true, margin: "200px" });

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const c = params.get("city"); const s = params.get("spot");
    if (c && data.cities.find(ci => ci.city_code === c)) setActiveCity(c);
    if (s) { const found = data.cities.flatMap(ci => ci.spots).find(sp => sp.name === s); if (found) setTimeout(() => { setSelectedSpot(found); document.getElementById("rankings")?.scrollIntoView({ behavior: "smooth" }); }, 500); }
  }, [data]);

  const city = data.cities.find(c => c.city_code === activeCity);
  const spots = city?.spots.sort((a, b) => b.score - a.score) || [];
  const [expanded, setExpanded] = useState(false);

  // FAQ JSON-LD
  const faqSchema = { "@context": "https://schema.org", "@type": "FAQPage", mainEntity: FAQ_ITEMS.map(i => ({ "@type": "Question", name: i.q, acceptedAnswer: { "@type": "Answer", text: i.a } })) };

  return (
    <div className="min-h-screen bg-warm-50">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }} />
      <HeroSection data={data} />
      <div className="max-w-5xl mx-auto px-4 py-8 space-y-10">
        {/* Screen 2: Rankings */}
        <section id="rankings" className="scroll-mt-4">
          <h2 className="text-lg font-bold text-stone-900 mb-4">{city?.city_name_cn} 赏樱景点排行</h2>
          <CityTabs cities={data.cities} active={activeCity} onChange={setActiveCity} />
          <AnimatePresence mode="wait">
            <motion.div key={activeCity} variants={staggerContainer} initial="initial" animate="animate" exit={{ opacity: 0 }} className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 mt-4">
              {spots.map((s, i) => <SpotCard key={`${activeCity}-${s.name}`} spot={s} rank={i + 1} onClick={() => setSelectedSpot(s)} />)}
            </motion.div>
          </AnimatePresence>
          {spots.length === 0 && <div className="text-center py-12 text-stone-400"><span className="text-3xl block mb-2">🌱</span><p className="text-sm">暂无数据</p></div>}
          <motion.div {...fadeInUp} className="mt-6 p-4 rounded-xl bg-gradient-to-r from-warm-50 to-rose-50 border border-warm-200 text-center">
            <p className="text-sm text-stone-700">喜欢这些景点？帮你排进一天的赏樱路线</p>
            <Link href="/quiz"><Button variant="warm" size="sm" className="mt-2 rounded-full px-6">安排赏樱行程 →</Button></Link>
          </motion.div>
        </section>

        {/* Screen 3: Timeline */}
        <section>
          <h2 className="text-lg font-bold text-stone-900 mb-4">花期时间轴 — 什么时候去最好</h2>
          <div className="bg-white rounded-2xl border border-stone-100 p-5">
            {["东京", "京都", "大阪"].map((name, ci) => {
              const code = ["tokyo", "kyoto", "osaka"][ci];
              const stages = [0, 0, 1, 2, 2, 1]; // simplified: 0=dormant 1=bloom 2=full
              return (
                <div key={code} className={cn("flex items-center gap-1 mb-2", activeCity === code && "ring-2 ring-warm-200 rounded-lg p-1")}>
                  <div className="w-14 flex-shrink-0 text-xs font-medium text-stone-700">{name}</div>
                  {stages.map((s, i) => <div key={i} className={cn("flex-1 h-5 rounded", s === 0 ? "bg-stone-100" : s === 1 ? "bg-pink-200" : "bg-pink-400")} />)}
                </div>
              );
            })}
            <div className="flex gap-4 mt-3 text-[10px] text-stone-400 justify-center">
              <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-stone-100" /> 未開</span>
              <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-pink-200" /> 五分咲</span>
              <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-pink-400" /> 満開</span>
            </div>
          </div>
        </section>

        {/* Screen 4: Map */}
        <section ref={mapRef}>
          <h2 className="text-lg font-bold text-stone-900 mb-4">实时樱花地图</h2>
          {mapInView ? <SakuraMap spots={spots} activeCity={activeCity} onSpotClick={setSelectedSpot} /> : <div className="w-full h-[400px] bg-stone-100 rounded-2xl flex items-center justify-center"><span className="text-stone-300 text-sm">↓ 滚动加载地图</span></div>}
        </section>

        {/* Screen 5: Trust */}
        <section className="bg-white rounded-2xl border border-stone-100 p-5">
          <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1 text-xs text-stone-500 mb-2">{DATA_SOURCES.map(s => <span key={s.name} className="font-medium">{s.name}</span>)}</div>
          <p className="text-center text-xs text-stone-400">融合 6 大权威数据源，每天更新 3 次 · 最后更新 {data.updated_at}</p>
          <div className="text-center mt-2"><button onClick={() => setExpanded(!expanded)} className="text-[10px] text-warm-500 hover:underline">{expanded ? "收起" : "了解我们的数据有多硬 ↓"}</button></div>
          <AnimatePresence>{expanded && <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden"><div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-3 pt-3 border-t border-stone-100">{DATA_SOURCES.map(s => <div key={s.name} className="text-[10px]"><span className="font-medium text-stone-700">{s.name}</span><p className="text-stone-400">{s.desc}</p></div>)}</div></motion.div>}</AnimatePresence>
        </section>

        {/* FAQ */}
        <section><h2 className="text-lg font-bold text-stone-900 mb-4">常见问题</h2><div className="space-y-2">{FAQ_ITEMS.map(i => <details key={i.q} className="bg-white rounded-xl border border-stone-100 group"><summary className="p-4 text-sm font-medium text-stone-800 cursor-pointer list-none flex items-center justify-between">{i.q}<span className="text-stone-300 group-open:rotate-180 transition-transform">▾</span></summary><p className="px-4 pb-4 text-xs text-stone-500 leading-relaxed">{i.a}</p></details>)}</div></section>

        {/* Screen 6: Conversion */}
        <section>
          <h2 className="text-lg font-bold text-stone-900 mb-2 text-center">看完花期，接下来呢？</h2>
          <p className="text-sm text-stone-400 text-center mb-3">把喜欢的景点变成一份完整的行程方案</p>
          {/* 场景化入口短句 */}
          <div className="flex flex-wrap justify-center gap-2 mb-6">
            <span className="text-xs bg-rose-50 text-rose-500 px-3 py-1.5 rounded-full border border-rose-100">
              🚅 {ENTRY_COPY.multi_city.hook} {ENTRY_COPY.multi_city.sub}
            </span>
            <span className="text-xs bg-amber-50 text-amber-600 px-3 py-1.5 rounded-full border border-amber-100">
              📍 {ENTRY_COPY.single_city.hook} {ENTRY_COPY.single_city.sub}
            </span>
          </div>
          <div className="grid md:grid-cols-3 gap-4">
            {[
              { icon: "🌸", title: "帮我安排赏樱行程", desc: "AI 定制 + 在地顾问审核", href: "/quiz", cta: "免费开始 →" },
              { icon: "📖", title: "看看别人的行程", desc: "看一份真实的赏樱行程方案", href: "/plan/demo", cta: "查看样例 →" },
              { icon: "💬", title: "先加微信聊聊", desc: `微信 ${WECHAT_ID} 先聊再决定`, href: undefined as string | undefined, cta: `微信号：${WECHAT_ID}` },
            ].map(c => <div key={c.title} className="bg-white rounded-xl border border-stone-100 p-5 text-center hover:shadow-md transition-shadow"><span className="text-3xl block mb-3">{c.icon}</span><h3 className="text-sm font-bold text-stone-900 mb-1">{c.title}</h3><p className="text-xs text-stone-400 mb-4">{c.desc}</p>{c.href ? <Link href={c.href}><Button variant="warm" size="sm" className="rounded-full px-6">{c.cta}</Button></Link> : <span className="text-xs font-mono text-warm-500">{c.cta}</span>}</div>)}
          </div>
          <div className="text-center mt-4"><button onClick={async () => { if (navigator.share) { try { await navigator.share({ title: "2026 日本樱花追踪", url: window.location.href }); } catch {} } else { await navigator.clipboard.writeText(window.location.href); alert("链接已复制！"); } }} className="text-xs text-stone-400 hover:text-warm-500">📤 发给同行人一起选</button></div>
        </section>
      </div>

      <footer className="text-center py-6 text-[10px] text-stone-300 border-t border-stone-100">数据来源：日本气象厅 · Weathernews · 地方观光协会 · 更新 {data.updated_at}</footer>

      <AnimatePresence>{selectedSpot && <SpotDetailDrawer spot={selectedSpot} onClose={() => setSelectedSpot(null)} />}</AnimatePresence>
    </div>
  );
}
