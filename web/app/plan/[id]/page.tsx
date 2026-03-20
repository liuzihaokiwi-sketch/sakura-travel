"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import Link from "next/link";
import { Suspense } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { fadeInUp, staggerContainer } from "@/lib/animations";
import { WECHAT_ID } from "@/lib/constants";

// ── Mock complete plan data ─────────────────────────────────────────────────
const PLAN = {
  title: "东京 7 日 · 樱花季深度行程",
  tags: ["👫 两人出行", "📸 出片优先", "🍣 美食探索", "🌸 樱花季"],
  dates: "2026年3月28日 — 4月3日",
  days: [
    {
      num: 1, theme: "浅草·上野 — 历史与下町风情",
      items: [
        { time: "09:00", icon: "🌸", place: "上野恩赐公园", reason: "早上人少，樱花光线最柔和", duration: "1.5h" },
        { time: "10:30", icon: "🏛️", place: "东京国立博物馆", reason: "就在公园旁，不用额外赶路", duration: "1h" },
        { time: "12:00", icon: "🍜", place: "浅草 弁天（拉面）", reason: "浓厚豚骨系，步行3分钟到浅草寺", duration: "1h" },
        { time: "13:30", icon: "⛩️", place: "浅草寺 + 仲见世通", reason: "午后人流比上午少30%，拍照更舒服", duration: "1.5h" },
        { time: "15:30", icon: "🛍️", place: "阿美横丁", reason: "从浅草走10分钟，顺路不回头", duration: "1h" },
        { time: "17:00", icon: "🌇", place: "隅田川河畔散步", reason: "本地人傍晚散步的路线，天际线很美", duration: "40min" },
      ],
      tips: { photo: "上野公园9点前拍樱花，光线柔和人极少", avoid: "仲见世通的人形烧店排队很久，不如去旁边小巷" },
    },
    {
      num: 2, theme: "涩谷·原宿 — 潮流与绿意",
      items: [
        { time: "09:00", icon: "⛩️", place: "明治神宫", reason: "早晨安静庄严，和下午的原宿形成对比", duration: "1h" },
        { time: "10:30", icon: "🛍️", place: "竹下通 + 表参道", reason: "上午人少，适合逛和拍", duration: "2h" },
        { time: "12:30", icon: "🍣", place: "涩谷 鮨 小野（寿司）", reason: "当地人午间套餐性价比极高", duration: "1h" },
        { time: "14:00", icon: "🌸", place: "代代木公园", reason: "东京市中心最大的赏樱地，可以野餐", duration: "1.5h" },
        { time: "16:00", icon: "🏙️", place: "涩谷Sky展望台", reason: "日落前上去，同时看白天和夜景", duration: "1h" },
        { time: "18:00", icon: "🌆", place: "涩谷十字路口", reason: "日落后灯光亮起拍最经典", duration: "30min" },
      ],
      tips: { photo: "涩谷十字路口18:30灯光最好看，站在星巴克二楼拍", avoid: "原宿周末人非常多，我们安排在工作日" },
    },
    {
      num: 3, theme: "新宿·中野 — 繁华与动漫",
      items: [
        { time: "09:00", icon: "🌸", place: "新宿御苑", reason: "65种1000+棵樱花，东京最美赏樱地", duration: "2h" },
        { time: "11:30", icon: "🍜", place: "风雲児（沾面）", reason: "Tabelog 3.7，新宿最佳拉面之一", duration: "1h" },
        { time: "13:00", icon: "🏬", place: "伊势丹百货", reason: "地下食品层是隐藏美食天堂", duration: "1h" },
        { time: "14:30", icon: "🎮", place: "中野百老汇", reason: "比秋叶原更本地的动漫圣地", duration: "1.5h" },
        { time: "16:30", icon: "📸", place: "歌舞伎町一番街", reason: "白天安全，适合拍经典霓虹招牌", duration: "30min" },
        { time: "17:30", icon: "🌇", place: "东京都厅展望室", reason: "免费！360度看东京日落", duration: "1h" },
      ],
      tips: { photo: "新宿御苑禁止饮酒，但可以野餐拍照", avoid: "歌舞伎町晚上不建议深入，白天拍照即可" },
    },
  ],
  hotel: { area: "新宿西口", reason: "到上野/涩谷/新宿御苑都在20分钟内，性价比最高的中间位置", budget: "¥600-900/晚" },
  transport: "7日内推荐用 Suica + 都营一日券组合，比JR Pass省约¥3000",
  checklist: ["护照（有效期6个月以上）", "Visit Japan Web 提前注册", "Suica 卡（到达后充值）", "移动WiFi/流量卡", "舒适步行鞋（日均1.5万步）", "充电宝", "常用药品", "日元现金 ¥30,000备用"],
};

// ── Plan content component ──────────────────────────────────────────────────

function PlanContent({ params }: { params: { id: string } }) {
  const searchParams = useSearchParams();
  const mode = searchParams.get("mode");
  const isPreview = mode === "preview";

  const [expandedDay, setExpandedDay] = useState(0);

  // In preview mode, only show Day 1
  const visibleDays = isPreview ? PLAN.days.slice(0, 1) : PLAN.days;
  const totalDays = 7;

  return (
    <div className="min-h-screen bg-warm-50">
      {/* Preview banner */}
      {isPreview && (
        <div className="bg-warm-100 border-b border-warm-200 py-3 px-6 text-center sticky top-0 z-50">
          <p className="text-sm text-warm-600 font-medium">
            🆓 这是你的免费预览 · 完整版还有 {totalDays - 1} 天精彩内容
          </p>
        </div>
      )}

      {/* Cover */}
      <div className="relative bg-gradient-to-b from-stone-900 via-stone-800 to-stone-900 text-white py-16 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <p className="text-xs tracking-[0.3em] text-white/40 font-mono mb-4">
            {isPreview ? "FREE PREVIEW · DAY 1" : "YOUR TRAVEL PLAN"}
          </p>
          <h1 className="font-display text-3xl md:text-4xl font-bold mb-3">{PLAN.title}</h1>
          <p className="text-white/50 text-sm mb-4">{PLAN.dates}</p>
          <div className="flex flex-wrap justify-center gap-2">
            {PLAN.tags.map((t) => (
              <span key={t} className="text-xs bg-white/10 px-3 py-1 rounded-full">{t}</span>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-6 py-8 space-y-8">
        {/* Overview */}
        <motion.section variants={fadeInUp} initial="initial" animate="animate">
          <h2 className="text-lg font-bold text-stone-900 mb-4">📋 行程总览</h2>
          <div className="grid grid-cols-7 gap-2">
            {Array.from({ length: totalDays }, (_, i) => {
              const d = PLAN.days[i];
              const isLocked = isPreview && i > 0;
              return (
                <button
                  key={i}
                  onClick={() => !isLocked && d && setExpandedDay(i)}
                  className={cn(
                    "rounded-xl p-3 text-center transition-all",
                    isLocked
                      ? "bg-stone-100/50 cursor-not-allowed opacity-60"
                      : d
                        ? "bg-white border border-stone-100 hover:shadow-md cursor-pointer"
                        : "bg-stone-100/50"
                  )}
                >
                  <p className="text-xs font-bold text-warm-400">Day {i + 1}</p>
                  <p className="text-[9px] text-stone-400 mt-1 line-clamp-2">
                    {isLocked ? "🔒" : d?.theme.split("—")[0] || "..."}
                  </p>
                </button>
              );
            })}
          </div>
        </motion.section>

        {/* Daily details */}
        {visibleDays.map((day) => (
          <motion.section key={day.num} variants={staggerContainer} initial="initial" whileInView="animate" viewport={{ once: true }}>
            <div className="flex items-center gap-3 mb-4">
              <span className="w-10 h-10 rounded-full bg-gradient-to-br from-warm-300 to-sakura-400 text-white flex items-center justify-center font-bold text-sm shadow">{day.num}</span>
              <div>
                <h3 className="text-lg font-bold text-stone-900">Day {day.num}</h3>
                <p className="text-sm text-warm-400">{day.theme}</p>
              </div>
            </div>

            {day.items.map((item) => (
              <motion.div key={item.time} variants={fadeInUp} className="flex gap-4 mb-3">
                <div className="flex flex-col items-center">
                  <span className="text-xs font-mono text-stone-400 w-12 text-right">{item.time}</span>
                  <div className="w-px flex-1 bg-stone-200 mt-1" />
                </div>
                <div className="flex-1 bg-white rounded-xl border border-stone-100 p-4">
                  <div className="flex items-center gap-2 mb-1">
                    <span>{item.icon}</span>
                    <h4 className="font-semibold text-stone-900 text-sm">{item.place}</h4>
                    <span className="text-xs text-stone-400 ml-auto">{item.duration}</span>
                  </div>
                  <p className="text-xs text-stone-500 leading-relaxed">💡 {item.reason}</p>
                </div>
              </motion.div>
            ))}

            {/* Tips sidebar */}
            <div className="grid grid-cols-2 gap-3 mt-2 mb-6">
              <div className="bg-sakura-50 border border-sakura-100 rounded-xl p-3">
                <p className="text-xs font-semibold text-sakura-500 mb-1">📸 拍照提示</p>
                <p className="text-xs text-stone-600">{day.tips.photo}</p>
              </div>
              <div className="bg-amber-50 border border-amber-100 rounded-xl p-3">
                <p className="text-xs font-semibold text-amber-600 mb-1">⚠️ 避坑提醒</p>
                <p className="text-xs text-stone-600">{day.tips.avoid}</p>
              </div>
            </div>
          </motion.section>
        ))}

        {/* Preview: locked content teaser */}
        {isPreview && (
          <section className="relative">
            {/* Blurred fake content */}
            <div className="space-y-4 opacity-30 blur-[2px] select-none pointer-events-none">
              {[2, 3, 4].map((n) => (
                <div key={n} className="bg-white rounded-xl border border-stone-100 p-6">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 rounded-full bg-stone-200" />
                    <div>
                      <div className="h-4 w-32 bg-stone-200 rounded" />
                      <div className="h-3 w-48 bg-stone-100 rounded mt-1" />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="h-3 w-full bg-stone-100 rounded" />
                    <div className="h-3 w-3/4 bg-stone-100 rounded" />
                    <div className="h-3 w-5/6 bg-stone-100 rounded" />
                  </div>
                </div>
              ))}
            </div>
            {/* Overlay CTA */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="bg-white/95 backdrop-blur-sm rounded-2xl shadow-xl p-8 text-center max-w-sm mx-6 border border-warm-100">
                <span className="text-4xl block mb-3">🔒</span>
                <h3 className="font-display text-xl font-bold text-stone-900 mb-2">
                  还有 {totalDays - 1} 天精彩内容
                </h3>
                <p className="text-sm text-stone-500 mb-1">
                  完整版包含每天的详细路线、餐厅推荐、交通方案、备选计划...
                </p>
                <p className="text-sm text-stone-500 mb-6">
                  共 <strong>30-40 页</strong>，首发价仅 <strong className="text-warm-500">¥248</strong>
                </p>
                <p className="text-xs text-stone-400 mb-4">
                  联系你的规划师解锁完整方案 👇
                </p>
                <div className="flex flex-col items-center gap-2">
                  <p className="text-sm font-medium text-stone-700">
                    微信：<span className="font-mono">{WECHAT_ID}</span>
                  </p>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(WECHAT_ID).then(() => {
                        alert("已复制微信号：" + WECHAT_ID);
                      }).catch(() => {
                        prompt("请复制微信号：", WECHAT_ID);
                      });
                    }}
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-warm-100 text-warm-600 text-sm font-medium hover:bg-warm-200 transition-colors"
                  >
                    📋 复制微信号
                  </button>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* Full version: hotel, transport, checklist */}
        {!isPreview && (
          <>
            {/* Hotel */}
            <section className="bg-white rounded-2xl border border-stone-100 p-6">
              <h2 className="text-lg font-bold text-stone-900 mb-3">🏨 住宿建议</h2>
              <p className="text-sm text-stone-700 font-medium">{PLAN.hotel.area}</p>
              <p className="text-xs text-stone-500 mt-1">💡 {PLAN.hotel.reason}</p>
              <p className="text-xs text-warm-400 mt-2">预算参考：{PLAN.hotel.budget}</p>
            </section>

            {/* Transport */}
            <section className="bg-white rounded-2xl border border-stone-100 p-6">
              <h2 className="text-lg font-bold text-stone-900 mb-3">🚃 交通方案</h2>
              <p className="text-sm text-stone-600">{PLAN.transport}</p>
            </section>

            {/* Checklist */}
            <section className="bg-white rounded-2xl border border-stone-100 p-6">
              <h2 className="text-lg font-bold text-stone-900 mb-3">✅ 出行准备清单</h2>
              <div className="grid grid-cols-2 gap-2">
                {PLAN.checklist.map((item) => (
                  <label key={item} className="flex items-center gap-2 text-sm text-stone-600 cursor-pointer">
                    <input type="checkbox" className="rounded border-stone-300 text-warm-400 focus:ring-warm-300" />
                    <span>{item}</span>
                  </label>
                ))}
              </div>
            </section>

            {/* Actions */}
            <div className="flex gap-3">
              <Link href={`/plan/${params.id}/edit`} className="flex-1">
                <Button variant="outline" className="w-full">✏️ 精调行程（剩余2次）</Button>
              </Link>
              <Link href={`/plan/${params.id}/upgrade`} className="flex-1">
                <Button variant="warm" className="w-full">⭐ 升级管家版</Button>
              </Link>
            </div>

            {/* Share */}
            <div className="text-center py-6 border-t border-stone-100">
              <p className="text-sm text-stone-500 mb-2">觉得有用？分享给一起去的朋友</p>
              <Button variant="outline" size="sm">📤 分享行程</Button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ── Page wrapper ────────────────────────────────────────────────────────────

export default function PlanPage({ params }: { params: { id: string } }) {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-warm-50">
        <p className="text-stone-400">加载行程...</p>
      </div>
    }>
      <PlanContent params={params} />
    </Suspense>
  );
}