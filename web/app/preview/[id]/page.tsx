"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { fadeInUp } from "@/lib/animations";
import { WECHAT_ID } from "@/lib/constants";

// ── Types ──────────────────────────────────────────────────────────────────

interface PreviewItem {
  time?: string;
  icon?: string;
  name: string;
  entity_type: string;
  reason?: string;
  photo_tip?: string;
  avoid_tip?: string;
  is_locked?: boolean;
  teaser?: string;
}

interface PreviewDay {
  day_number: number;
  theme: string;
  city: string;
  items: PreviewItem[];
  is_preview_day: boolean;
}

interface PreviewData {
  plan_id: string;
  total_days: number;
  preview_day_index: number;
  days: PreviewDay[];
  sku: {
    price: number;
    name: string;
    tagline: string;
    cta_text: string;
  };
}

// ── MOCK fallback 数据 ─────────────────────────────────────────────────────

const MOCK_PREVIEW: PreviewData = {
  plan_id: "demo",
  total_days: 5,
  preview_day_index: 0,
  sku: { price: 248, name: "标准个性化方案", tagline: "完整5日行程+餐厅推荐", cta_text: "立即解锁完整方案" },
  days: [
    {
      day_number: 1,
      theme: "上野 × 浅草 × 晴空塔：东京灵魂首日",
      city: "东京",
      is_preview_day: true,
      items: [
        { time: "09:00", icon: "🌸", name: "上野公园", entity_type: "attraction",
          reason: "东京最大公园，800棵染井吉野樱，春季全程免费观赏。博物馆群在公园内，逛累了可以直接进馆休息。",
          photo_tip: "早上9-10点逆光拍池边倒影，F8小光圈效果最佳。",
          avoid_tip: "黄金周人流极大，工作日早上9点前到达最为舒适。" },
        { time: "11:00", icon: "⛩️", name: "浅草寺·仲见世通", entity_type: "attraction",
          reason: "东京现存最古老寺庙，创建于628年。仲见世通全长250米87家商铺，雷门大灯笼是东京最具辨识度的地标之一。",
          photo_tip: "雷门正面拍摄最佳位置在入口往外退5步处，使用28mm广角，上午顺光。人潮在11:30后激增，赶早。",
          avoid_tip: "仲见世通商品价格偏高，同类纪念品在合羽桥道具街更便宜。" },
        { time: "12:30", icon: "🍜", name: "大黒家天妇罗（午餐）", entity_type: "restaurant",
          reason: "1887年创业，Tabelog 3.82分，浅草最具代表性的独孤天妇罗店。招牌天妇罗盖饭¥1800，芝麻油炸制香气浓郁。",
          photo_tip: "盖饭上桌时俯拍，自然光+木质托盘背景，饱和度高。",
          avoid_tip: "午饭时间排队约40分钟。11:30开门时到达或13:30后错峰。不接受预约，只能现场等待。" },
        { time: "14:30", icon: "🗼", name: "东京晴空塔", entity_type: "attraction",
          reason: "高634米，世界第二高塔。350米展望台可俯瞰关东平原全景，晴天可见富士山（概率约35%）。建议网上提前购票省去20-40分钟排队。",
          photo_tip: "350米天望甲板：向西南方向拍富士山（夏季可见率低，秋冬最佳）；向东北拍大川端的隅田川蛇形弯曲。落日时分天空层次最丰富。",
          avoid_tip: "不要在晴空塔内部餐厅用餐，性价比极低。周末提前2周在官网购票，节假日前一个月。" },
        { time: "17:00", icon: "🌅", name: "隅田川·吾妻桥", entity_type: "attraction",
          reason: "隅田川与晴空塔的标准打卡地。吾妻桥是拍晴空塔倒影最佳位置，傍晚金色光线搭配朱红色桥身，是东京最经典的拍照地之一。",
          photo_tip: "吾妻桥南侧护栏处拍水面晴空塔倒影，蹲低至护栏高度，前景纳入护栏金属质感。日落后15分钟塔灯亮起，蓝调时刻+灯光是最佳组合。",
          avoid_tip: "夏季（7-8月）会有隅田川烟花大会，届时人流极大，需提前数月预约观赏席。平时傍晚是当地居民散步时间，氛围最佳。" },
      ],
    },
    { day_number: 2, theme: "新宿 × 代代木公园 × 原宿", city: "东京", is_preview_day: false,
      items: Array(6).fill(null).map((_, i) => ({ name: `景点${i+1}`, entity_type: "attraction", is_locked: true })) },
    { day_number: 3, theme: "镰仓一日游", city: "神奈川", is_preview_day: false,
      items: Array(5).fill(null).map((_, i) => ({ name: `景点${i+1}`, entity_type: "attraction", is_locked: true })) },
    { day_number: 4, theme: "银座 × 筑地 × 汐留", city: "东京", is_preview_day: false,
      items: Array(5).fill(null).map((_, i) => ({ name: `景点${i+1}`, entity_type: "attraction", is_locked: true })) },
    { day_number: 5, theme: "秋叶原 × 御茶水 × 本乡", city: "东京", is_preview_day: false,
      items: Array(4).fill(null).map((_, i) => ({ name: `景点${i+1}`, entity_type: "attraction", is_locked: true })) },
  ],
};

// ── CTA 跳转 ───────────────────────────────────────────────────────────────

function goToPricing(planId?: string, source?: string) {
  const params = new URLSearchParams({ from: "preview" });
  if (planId) params.set("plan", planId);
  if (source) params.set("trigger", source);
  window.location.href = `/pricing?${params}`;
}

// ── 悬浮底栏 ───────────────────────────────────────────────────────────────

function FloatingCTA({ price, ctaText, planId }: { price: number; ctaText: string; planId?: string }) {
  const [visible, setVisible] = useState(false);
  useEffect(() => { const t = setTimeout(() => setVisible(true), 800); return () => clearTimeout(t); }, []);

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ y: 100, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 100, opacity: 0 }}
          className="fixed bottom-0 left-0 right-0 z-50 bg-white/96 backdrop-blur-sm border-t border-stone-200 px-4 py-3 safe-area-bottom"
        >
          <div className="max-w-lg mx-auto flex items-center justify-between gap-3">
            <div>
              <p className="text-xs text-stone-500">解锁完整行程方案</p>
              <p className="text-lg font-bold text-rose-600">¥{price}</p>
            </div>
            <Button
              className="bg-rose-600 hover:bg-rose-700 text-white px-6 py-3 rounded-full text-sm font-semibold shadow-lg"
              onClick={() => goToPricing(planId, "floating_bar")}
            >
              {ctaText}
            </Button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// ── Inline CTA 插入条 ─────────────────────────────────────────────────────

function InlineCTA({ message, price, planId, trigger }: { message: string; price: number; planId?: string; trigger?: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
      className="my-6 p-5 rounded-2xl bg-gradient-to-r from-rose-50 to-amber-50 border border-rose-200 text-center"
    >
      <p className="text-sm font-semibold text-stone-800 mb-1">{message}</p>
      <p className="text-xs text-stone-500 mb-4">完整版包含 30-40 页详细攻略 + 全部餐厅推荐 + 避坑提醒</p>
      <Button
        className="bg-rose-600 hover:bg-rose-700 text-white text-sm px-8 py-2.5 rounded-full font-semibold shadow-md"
        onClick={() => goToPricing(planId, trigger ?? "inline_cta")}
      >
        立即解锁完整方案 ¥{price} →
      </Button>
    </motion.div>
  );
}

// ── 锁定模块（模糊占位） ──────────────────────────────────────────────────

function LockedModule({ planId }: { planId?: string }) {
  return (
    <div
      className="relative overflow-hidden rounded-xl border border-stone-200 bg-gradient-to-b from-stone-50 to-stone-100 p-4 cursor-pointer group"
      onClick={() => goToPricing(planId, "locked_item")}
    >
      <div className="absolute inset-0 backdrop-blur-[6px] bg-white/40 z-10 flex flex-col items-center justify-center gap-2 group-hover:bg-white/55 transition-all">
        <div className="w-9 h-9 rounded-full bg-rose-100 flex items-center justify-center">
          <svg className="w-4 h-4 text-rose-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>
        <span className="text-xs font-semibold text-stone-700">付费后解锁此内容</span>
        <span className="text-xs text-rose-600 font-medium">点击查看完整方案 →</span>
      </div>
      <div className="space-y-2 select-none pointer-events-none">
        <div className="h-4 bg-stone-300 rounded w-2/3" />
        <div className="h-3 bg-stone-200 rounded w-full" />
        <div className="h-3 bg-stone-200 rounded w-3/4" />
        <div className="h-3 bg-stone-200 rounded w-1/2" />
      </div>
    </div>
  );
}

// ── 其他天 Teaser 卡片 ────────────────────────────────────────────────────

const DAY_ICONS: Record<number, string> = { 2: "🏯", 3: "⛩️", 4: "🛍️", 5: "🌸", 6: "🎡", 7: "🍣" };

function DayTeaser({ day, planId }: { day: PreviewDay; planId?: string }) {
  return (
    <motion.div
      layout
      className="flex items-center gap-3 p-3.5 rounded-xl border border-stone-200 bg-white cursor-pointer hover:border-rose-300 hover:bg-rose-50/30 hover:shadow-sm transition-all"
      onClick={() => goToPricing(planId, `day_teaser_${day.day_number}`)}
    >
      <div className="flex-shrink-0 w-11 h-11 rounded-full bg-gradient-to-br from-rose-100 to-amber-100 flex items-center justify-center text-lg">
        {DAY_ICONS[day.day_number] ?? "🗾"}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-stone-800 truncate">{day.theme}</p>
        <p className="text-xs text-stone-400 mt-0.5">{day.city} · {day.items.length} 个推荐 · <span className="text-stone-400">🔒 已锁定</span></p>
      </div>
      <span className="flex-shrink-0 text-xs font-semibold text-rose-500 bg-rose-50 border border-rose-200 px-2 py-1 rounded-full">解锁</span>
    </motion.div>
  );
}

// ── 景点卡片（展开态） ─────────────────────────────────────────────────────

function SpotCard({ item, index }: { item: PreviewItem; index: number }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.07 }}
      className="rounded-xl border border-stone-200 bg-white shadow-sm overflow-hidden"
    >
      {/* 主信息 */}
      <div
        className="flex items-start gap-3 p-4 cursor-pointer"
        onClick={() => setExpanded((v) => !v)}
      >
        {item.time && (
          <span className="text-xs font-mono text-stone-400 mt-0.5 w-12 flex-shrink-0">{item.time}</span>
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            {item.icon && <span>{item.icon}</span>}
            <h4 className="text-sm font-semibold text-stone-800">{item.name}</h4>
            {item.entity_type === "restaurant" && (
              <span className="text-xs bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full font-medium">美食</span>
            )}
            {(item.photo_tip || item.avoid_tip) && (
              <span className={cn("text-xs px-1.5 py-0.5 rounded-full", expanded ? "bg-stone-200 text-stone-600" : "bg-stone-100 text-stone-500")}>
                {expanded ? "收起" : "详情"} {expanded ? "▲" : "▼"}
              </span>
            )}
          </div>
          {item.reason && (
            <p className="mt-1.5 text-xs text-stone-500 leading-relaxed line-clamp-2">{item.reason}</p>
          )}
        </div>
      </div>

      {/* 展开：拍照贴士 + 避坑 */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden border-t border-stone-100"
          >
            {item.reason && (
              <div className="px-4 pt-3 pb-1">
                <p className="text-xs text-stone-500 leading-relaxed">{item.reason}</p>
              </div>
            )}
            <div className="grid grid-cols-2 gap-3 p-4 pt-2">
              {item.photo_tip && (
                <div className="bg-blue-50 rounded-lg p-3">
                  <p className="text-xs font-semibold text-blue-700 mb-1">📸 拍摄指南</p>
                  <p className="text-xs text-blue-600 leading-relaxed">{item.photo_tip}</p>
                </div>
              )}
              {item.avoid_tip && (
                <div className="bg-amber-50 rounded-lg p-3">
                  <p className="text-xs font-semibold text-amber-700 mb-1">⚠️ 避坑提醒</p>
                  <p className="text-xs text-amber-600 leading-relaxed">{item.avoid_tip}</p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// ── 时间轴 ─────────────────────────────────────────────────────────────────

function PreviewTimeline({ items, planId }: { items: PreviewItem[]; planId?: string }) {
  return (
    <div className="relative space-y-3 pl-8">
      <div className="absolute left-3 top-2 bottom-2 w-px bg-gradient-to-b from-rose-300 via-stone-200 to-stone-100" />
      {items.map((item, idx) => (
        <div key={idx} className="relative">
          <div className={cn(
            "absolute -left-5 top-3 w-3 h-3 rounded-full border-2",
            item.is_locked ? "border-stone-300 bg-stone-100"
              : item.entity_type === "restaurant" ? "border-amber-400 bg-amber-50"
              : "border-rose-400 bg-rose-50"
          )} />
          {item.is_locked ? (
            <LockedModule planId={planId} />
          ) : (
            <SpotCard item={item} index={idx} />
          )}
        </div>
      ))}
    </div>
  );
}

// ── 45s 停留弹窗 ──────────────────────────────────────────────────────────

function StayTimeCTA({ price, planId, onDismiss }: { price: number; planId?: string; onDismiss: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 60 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 60 }}
      className="fixed inset-x-4 bottom-24 z-40 bg-white rounded-2xl shadow-2xl border border-rose-200 p-5 max-w-lg mx-auto left-1/2 -translate-x-1/2"
    >
      <button onClick={onDismiss} className="absolute top-3 right-3 text-stone-400 hover:text-stone-700 text-lg leading-none">✕</button>
      <p className="text-sm font-bold text-stone-900 mb-1">📌 感觉还不错？</p>
      <p className="text-xs text-stone-500 mb-4 leading-relaxed">
        你已经预览了 Day 1——完整版还有 {" "}
        <span className="font-semibold text-stone-700">每天每餐每段交通</span>，全部安排好了。
      </p>
      <Button
        className="w-full bg-rose-600 hover:bg-rose-700 text-white rounded-full font-semibold"
        onClick={() => goToPricing(planId, "stay_45s")}
      >
        ¥{price} 解锁完整 {"{total}"} 天方案
      </Button>
    </motion.div>
  );
}

// ── 信任模块 ───────────────────────────────────────────────────────────────

function TrustModule({ planId, price }: { planId?: string; price: number }) {
  return (
    <motion.section {...fadeInUp} className="rounded-2xl bg-gradient-to-br from-stone-900 to-stone-800 text-white p-6 space-y-4">
      <h3 className="text-base font-bold">为什么选择我们的方案？</h3>
      <div className="grid grid-cols-2 gap-3">
        {[
          ["📍", "每个推荐都有具体理由"],
          ["⏰", "精确到分钟的时间线"],
          ["📸", "每个景点拍摄指南"],
          ["⚠️", "全程避坑提醒"],
          ["🔄", "2次不满意可修改"],
          ["💬", "付费后微信答疑"],
        ].map(([icon, text]) => (
          <div key={text} className="flex items-start gap-2 text-xs text-white/75">
            <span className="flex-shrink-0">{icon}</span><span>{text}</span>
          </div>
        ))}
      </div>
      <div className="space-y-2 pt-1">
        <Button
          className="w-full bg-rose-500 hover:bg-rose-400 text-white rounded-full font-semibold"
          onClick={() => goToPricing(planId, "trust_module")}
        >
          立即解锁完整方案 ¥{price}
        </Button>
        <p className="text-center text-xs text-white/40">不满意 7 天内全额退款</p>
      </div>
    </motion.section>
  );
}

// ── 微信引导 ───────────────────────────────────────────────────────────────

function WechatFallback() {
  const [copied, setCopied] = useState(false);
  async function copy() {
    await navigator.clipboard.writeText(WECHAT_ID).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }
  return (
    <motion.div {...fadeInUp} className="rounded-xl border border-stone-200 bg-white p-5 text-center">
      <p className="text-xs text-stone-400 mb-2">还在犹豫？先加微信聊聊 · 不买也没关系</p>
      <button
        onClick={copy}
        className="inline-flex items-center gap-2 bg-[#07C160] text-white text-sm px-5 py-2.5 rounded-full font-medium hover:bg-[#06A84F] transition-colors"
      >
        <span>💬</span>
        <span>{copied ? "已复制！" : `微信：${WECHAT_ID}`}</span>
      </button>
    </motion.div>
  );
}

// ── 主页面 ─────────────────────────────────────────────────────────────────

export default function PreviewPage({ params }: { params: { id: string } }) {
  const [data, setData] = useState<PreviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [isMock, setIsMock] = useState(false);
  const [stayTime, setStayTime] = useState(0);
  const [showStayCTA, setShowStayCTA] = useState(false);
  const [stayCTADismissed, setStayCTADismissed] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // 秒数计时
  useEffect(() => {
    timerRef.current = setInterval(() => setStayTime((t) => t + 1), 1000);
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, []);

  // 45s 弹窗
  useEffect(() => {
    if (stayTime === 45 && !stayCTADismissed) setShowStayCTA(true);
  }, [stayTime, stayCTADismissed]);

  // 加载预览数据
  useEffect(() => {
    async function load() {
      // demo / preview 使用 mock
      if (params.id === "demo" || params.id === "preview") {
        setData(MOCK_PREVIEW);
        setIsMock(true);
        setLoading(false);
        return;
      }
      try {
        const res = await fetch(`/api/plan/${params.id}?mode=preview`);
        if (res.ok) {
          const json = await res.json();
          setData(json);
        } else {
          // API 不通，展示 mock 作 fallback
          setData(MOCK_PREVIEW);
          setIsMock(true);
        }
      } catch {
        setData(MOCK_PREVIEW);
        setIsMock(true);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [params.id]);

  // ── Loading ──────────────────────────────────────────────────────────────
  if (loading) return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-stone-50 gap-4">
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 1.2, repeat: Infinity, ease: "linear" }}
        className="text-4xl"
      >
        🗾
      </motion.div>
      <p className="text-sm text-stone-400 animate-pulse">正在加载你的专属行程...</p>
    </div>
  );

  if (!data) return (
    <div className="min-h-screen flex items-center justify-center bg-stone-50">
      <div className="text-center space-y-4">
        <p className="text-stone-500">暂无预览数据</p>
        <Link href="/" className="text-rose-600 underline text-sm">返回首页</Link>
      </div>
    </div>
  );

  const previewDay = data.days.find((d) => d.is_preview_day);
  const otherDays = data.days.filter((d) => !d.is_preview_day);
  const planId = data.plan_id;
  const price = data.sku.price;

  return (
    <main className="min-h-screen bg-stone-50 pb-28">

      {/* ── Header ────────────────────────────────────────────────────── */}
      <div className="bg-gradient-to-b from-rose-50 via-rose-50/60 to-stone-50 px-4 pt-12 pb-8">
        <motion.div {...fadeInUp} className="max-w-lg mx-auto text-center">
          {isMock && (
            <span className="inline-block mb-3 text-xs bg-amber-100 text-amber-700 px-3 py-1 rounded-full font-medium">
              示例预览 · 真实方案根据你的问卷生成
            </span>
          )}
          <h1 className="text-2xl font-bold text-stone-900 leading-tight">
            你的专属行程已生成 ✨
          </h1>
          <p className="mt-2 text-sm text-stone-500">
            {data.total_days} 天完整方案 · 免费预览精选 Day 1
          </p>
          {/* 小 Banner CTA */}
          <motion.button
            initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.5 }}
            className="mt-4 inline-flex items-center gap-2 bg-rose-600 hover:bg-rose-700 text-white text-xs px-5 py-2.5 rounded-full shadow-md transition-colors font-medium"
            onClick={() => goToPricing(planId, "header_banner")}
          >
            🔥 完整版 ¥{price} · 立即解锁全部 {data.total_days} 天 →
          </motion.button>
        </motion.div>
      </div>

      <div className="max-w-lg mx-auto px-4 space-y-6">

        {/* ── Day 1 完整展示 ──────────────────────────────────────────── */}
        {previewDay && (
          <motion.section {...fadeInUp}>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-9 h-9 rounded-full bg-rose-600 text-white flex items-center justify-center text-sm font-bold flex-shrink-0">
                D1
              </div>
              <div>
                <h2 className="text-base font-bold text-stone-900 leading-tight">{previewDay.theme}</h2>
                <p className="text-xs text-stone-500">{previewDay.city}</p>
              </div>
            </div>
            <PreviewTimeline items={previewDay.items} planId={planId} />
          </motion.section>
        )}

        {/* ── Inline CTA 1（Day 1 结束后） ────────────────────────────── */}
        <InlineCTA
          message="喜欢这一天的安排？完整版还有更多惊喜"
          price={price}
          planId={planId}
          trigger="inline_after_day1"
        />

        {/* ── Day 2-N 锁定 Teaser ─────────────────────────────────────── */}
        {otherDays.length > 0 && (
          <motion.section {...fadeInUp}>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-stone-700">
                还有 {otherDays.length} 天精彩内容
              </h3>
              <span className="text-xs text-stone-400 bg-stone-100 px-2 py-1 rounded-full">🔒 付费解锁</span>
            </div>
            <div className="space-y-2">
              {otherDays.map((day) => (
                <DayTeaser key={day.day_number} day={day} planId={planId} />
              ))}
            </div>
          </motion.section>
        )}

        {/* ── Inline CTA 2（其他天之后） ──────────────────────────────── */}
        <InlineCTA
          message={`完整 ${data.total_days} 天方案包含所有餐厅·交通·避坑提醒`}
          price={price}
          planId={planId}
          trigger="inline_after_teasers"
        />

        {/* ── 信任模块 ─────────────────────────────────────────────────── */}
        <TrustModule planId={planId} price={price} />

        {/* ── 微信备选 ─────────────────────────────────────────────────── */}
        <WechatFallback />

        {/* 底部留白 */}
        <div className="h-4" />
      </div>

      {/* ── 固定底栏 ────────────────────────────────────────────────────── */}
      <FloatingCTA price={price} ctaText={data.sku.cta_text} planId={planId} />

      {/* ── 45s 停留弹窗 ─────────────────────────────────────────────────── */}
      <AnimatePresence>
        {showStayCTA && !stayCTADismissed && (
          <StayTimeCTA
            price={price}
            planId={planId}
            onDismiss={() => { setShowStayCTA(false); setStayCTADismissed(true); }}
          />
        )}
      </AnimatePresence>
    </main>
  );
}