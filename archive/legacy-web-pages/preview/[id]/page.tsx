"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { fadeInUp, staggerContainer } from "@/lib/animations";

// Mock 1-day preview data
const PREVIEW_DAY = {
  dayNum: 1,
  title: "浅草·上野 — 历史与下町风情",
  timeline: [
    { time: "09:00", icon: "🌸", place: "上野恩赐公园", note: "樱花季这里是东京最经典的赏樱地，早上人少光线好", duration: "1.5h" },
    { time: "10:30", icon: "🏛️", place: "东京国立博物馆", note: "选这里是因为就在公园旁边，不用额外赶路", duration: "1h" },
    { time: "12:00", icon: "🍜", place: "午餐 · 浅草周边", note: "选在浅草寺附近，步行就能到，不浪费时间", duration: "1h", locked: false },
    { time: "13:30", icon: "⛩️", place: "浅草寺 + 仲见世通", note: "午后去人流比上午少，拍照更方便", duration: "1.5h" },
    { time: "15:30", icon: "🛍️", place: "阿美横丁", note: "从浅草走过去10分钟，顺路不走回头路", duration: "1h" },
    { time: "17:00", icon: "🌇", place: "隅田川河畔", note: "傍晚散步看天际线，是本地人喜欢的路线", duration: "30min" },
  ],
  insight: "这天的安排把上野和浅草串在一起，全程步行+短途地铁，不走回头路。上午先去人少的公园赏樱，下午再去浅草寺避开高峰，节奏不紧不松。",
};

const LOCKED_DAYS = [
  { day: 2, title: "涩谷·原宿 — 潮流与绿意", spots: "明治神宫 · 竹下通 · 代代木公园" },
  { day: 3, title: "新宿·中目黑 — 樱花隧道与夜景", spots: "新宿御苑 · 中目黑 · 歌舞伎町" },
  { day: 4, title: "�的仓一日 — 海边古都", spots: "鶴岡八幡宮 · 小町通 · 江之电" },
  { day: 5, title: "六本木·东京塔 — 城市与樱花", spots: "毛利庭园 · 芝公园 · 东京塔夜景" },
  { day: 6, title: "千鸟之渊·银座 — 皇居樱花与购物", spots: "千鳥ヶ淵 · 皇居东御苑 · 银座" },
  { day: 7, title: "下北·吉祥寺 — 文艺收尾", spots: "下北泽 · 井之头公园 · 吉祥寺" },
];

export default function PreviewPage({ params }: { params: { id: string } }) {
  return (
    <div className="min-h-screen bg-warm-50">
      {/* Header */}
      <div className="bg-gradient-to-b from-stone-900 to-stone-800 text-white py-12 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <Badge variant="warm" className="mb-4">免费预览</Badge>
          <h1 className="font-display text-3xl font-bold mb-2">你的东京 7 日行程</h1>
          <p className="text-white/60 text-sm">以下是 Day 1 的完整规划 · 觉得好再解锁全部</p>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-6 py-8">
        {/* Day 1 — Full preview */}
        <motion.div
          variants={staggerContainer}
          initial="initial"
          animate="animate"
        >
          <motion.div variants={fadeInUp} className="mb-6">
            <div className="flex items-center gap-3 mb-2">
              <span className="w-10 h-10 rounded-full bg-warm-300 text-white flex items-center justify-center font-bold text-sm">1</span>
              <div>
                <h2 className="text-xl font-bold text-stone-900">Day {PREVIEW_DAY.dayNum}</h2>
                <p className="text-sm text-warm-400 font-medium">{PREVIEW_DAY.title}</p>
              </div>
            </div>
          </motion.div>

          {/* Timeline */}
          {PREVIEW_DAY.timeline.map((item, i) => (
            <motion.div
              key={item.time}
              variants={fadeInUp}
              className="flex gap-4 mb-4"
            >
              <div className="flex flex-col items-center">
                <span className="text-xs font-mono text-stone-400 w-12 text-right">{item.time}</span>
                <div className="w-px flex-1 bg-stone-200 mt-2" />
              </div>
              <div className="flex-1 bg-white rounded-xl border border-stone-100 p-4 hover:shadow-sm transition-shadow">
                <div className="flex items-center gap-2 mb-1">
                  <span>{item.icon}</span>
                  <h3 className="font-semibold text-stone-900 text-sm">{item.place}</h3>
                  <span className="text-xs text-stone-400 ml-auto">{item.duration}</span>
                </div>
                <p className="text-xs text-stone-500 leading-relaxed">{item.note}</p>
              </div>
            </motion.div>
          ))}

          {/* Professional insight */}
          <motion.div variants={fadeInUp} className="bg-warm-50 border border-warm-200/50 rounded-xl p-5 mt-6 mb-8">
            <p className="text-xs text-warm-400 font-semibold mb-1">💡 为什么这样安排</p>
            <p className="text-sm text-stone-600 leading-relaxed">{PREVIEW_DAY.insight}</p>
          </motion.div>
        </motion.div>

        {/* Locked days — blurred teaser */}
        <div className="relative mt-8">
          <h3 className="text-lg font-bold text-stone-900 mb-4">剩余 6 天行程</h3>
          <div className="space-y-3">
            {LOCKED_DAYS.map((day) => (
              <div
                key={day.day}
                className="bg-white/60 backdrop-blur-sm rounded-xl border border-stone-100 p-4 flex items-center gap-4"
              >
                <span className="w-8 h-8 rounded-full bg-stone-200 text-stone-400 flex items-center justify-center font-bold text-sm">
                  {day.day}
                </span>
                <div className="flex-1">
                  <p className="font-medium text-stone-800 text-sm">{day.title}</p>
                  <p className="text-xs text-stone-400">{day.spots}</p>
                </div>
                <span className="text-xs text-stone-300">🔒</span>
              </div>
            ))}
          </div>

          {/* Blur overlay */}
          <div className="absolute inset-x-0 bottom-0 h-32 bg-gradient-to-t from-warm-50 to-transparent pointer-events-none" />
        </div>

        {/* Upgrade CTA */}
        <div className="sticky bottom-0 bg-warm-50/95 backdrop-blur-sm border-t border-stone-100 py-6 mt-8 -mx-6 px-6">
          <div className="max-w-md mx-auto text-center">
            <p className="text-stone-600 font-medium mb-1">觉得 Day 1 的质量不错？</p>
            <p className="text-sm text-stone-400 mb-4">
              完整版包含 7 天行程 + 餐厅酒店 + 避坑指南 + 出行准备，共 30-40 页
            </p>
            <Link href="/pricing">
              <Button variant="warm" size="xl" className="w-full max-w-xs shadow-lg shadow-warm-300/30">
                解锁完整行程 · ¥248
              </Button>
            </Link>
            <p className="text-xs text-stone-400 mt-2">首批用户专享价 · 原价¥298 · 不满意不收费</p>
          </div>
        </div>
      </div>
    </div>
  );
}
