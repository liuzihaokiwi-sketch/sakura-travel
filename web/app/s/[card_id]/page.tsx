"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { fadeInUp, staggerContainer } from "@/lib/animations";

interface ShareCardData {
  card_id: string;
  type: "day1" | "result" | "savings" | "review" | "invite";
  city: string;
  city_name: string;
  plan_id?: string;
  days?: number;
  theme?: string;
  invite_code?: string;
  discount?: number;
  sharer_name?: string;
  created_at: string;
}

const CITY_EMOJI: Record<string, string> = {
  tokyo: "🗼", osaka: "🏯", kyoto: "⛩️", hokkaido: "🌨️", okinawa: "🌺",
};

// ── 各卡片类型的对应落地内容 ─────────────────────────────────────────────

function Day1Landing({ data }: { data: ShareCardData }) {
  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-br from-stone-900 to-stone-800 rounded-2xl p-6 text-white">
        <div className="text-xs text-warm-300 font-medium mb-2">
          {CITY_EMOJI[data.city] || "🗾"} {data.city_name} · Day 1 预览
        </div>
        <h2 className="text-xl font-bold mb-3">
          {data.theme || `${data.city_name}最值得去的一天`}
        </h2>
        <p className="text-sm text-stone-400 leading-relaxed">
          这份行程由 AI 根据真实数据定制，精确到每个时间段和每一餐。
          免费查看第一天完整内容，觉得好再决定是否购买完整版。
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {[
          { icon: "📍", text: "每个景点都有具体推荐理由" },
          { icon: "⏰", text: "精确到分钟的时间线" },
          { icon: "🍜", text: "每顿饭推荐 + 备选方案" },
          { icon: "🔄", text: "不满意可以免费调整" },
        ].map((item) => (
          <div key={item.text} className="bg-stone-50 rounded-xl p-3 flex items-start gap-2">
            <span className="text-lg flex-shrink-0">{item.icon}</span>
            <span className="text-xs text-stone-600">{item.text}</span>
          </div>
        ))}
      </div>

      <Link href={data.plan_id ? "/order" : "/order"}>
        <Button variant="warm" size="lg" className="w-full">
          🆓 免费查看第一天行程 →
        </Button>
      </Link>
      <p className="text-center text-xs text-stone-400">
        或者 <Link href="/order" className="underline">填写我的出行信息，生成专属方案</Link>
      </p>
    </div>
  );
}

function InviteLanding({ data }: { data: ShareCardData }) {
  const [copied, setCopied] = useState(false);

  function copyCode() {
    if (data.invite_code) {
      navigator.clipboard.writeText(data.invite_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-br from-warm-50 to-sakura-50 rounded-2xl p-6 border border-warm-100">
        <div className="text-xs text-warm-500 font-medium mb-2">专属邀请</div>
        <h2 className="text-xl font-bold text-stone-900 mb-2">
          你的朋友邀请你试试这个日本AI攻略
        </h2>
        <p className="text-sm text-stone-500">
          使用邀请码，享受 ¥{data.discount ?? 20} 元专属优惠
        </p>
      </div>

      {data.invite_code && (
        <div
          className="flex items-center justify-between bg-stone-900 rounded-xl p-4 cursor-pointer"
          onClick={copyCode}
        >
          <div>
            <p className="text-xs text-stone-500 mb-1">邀请码</p>
            <p className="text-2xl font-mono font-bold text-warm-300 tracking-widest">
              {data.invite_code}
            </p>
          </div>
          <div className="text-sm text-stone-400">
            {copied ? "✓ 已复制" : "点击复制"}
          </div>
        </div>
      )}

      <Link href="/order">
        <Button variant="warm" size="lg" className="w-full">
          🆓 免费试试，填写出行信息 →
        </Button>
      </Link>
      <p className="text-center text-xs text-stone-400">
        免费看第一天 · 满意再付费 ¥198起
      </p>
    </div>
  );
}

function GenericLanding({ data }: { data: ShareCardData }) {
  return (
    <div className="space-y-6">
      <div className="bg-warm-50 rounded-2xl p-6 border border-warm-100">
        <h2 className="text-xl font-bold text-stone-900 mb-2">
          {CITY_EMOJI[data.city] || "🗾"} {data.city_name} AI 定制行程
        </h2>
        <p className="text-sm text-stone-500 leading-relaxed">
          填写你的出行信息，AI 为你生成专属的 {data.days ?? 5} 天 {data.city_name} 行程方案。
          先免费看第一天，觉得好再决定。
        </p>
      </div>

      <Link href="/order">
        <Button variant="warm" size="lg" className="w-full">
          🆓 免费生成我的专属行程 →
        </Button>
      </Link>
    </div>
  );
}

// ── 主页面 ─────────────────────────────────────────────────────────────────

export default function SharePage({ params }: { params: { card_id: string } }) {
  const [data, setData] = useState<ShareCardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch(`/api/share/${params.card_id}`);
        if (res.ok) setData(await res.json());
      } catch {
        // 使用默认兜底
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [params.card_id]);

  // 卡片图 URL
  const cardImgUrl = data
    ? `/api/share/card?type=${data.type}&city=${data.city}&plan=${data.plan_id ?? ""}&theme=${encodeURIComponent(data.theme ?? "")}`
    : null;

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-stone-50">
      <div className="animate-pulse text-stone-400">加载中...</div>
    </div>
  );

  // 无数据时的通用落地页
  if (!data) return (
    <div className="min-h-screen bg-warm-50 py-12 px-4">
      <div className="max-w-md mx-auto">
        <motion.div variants={staggerContainer} initial="initial" animate="animate" className="space-y-8">
          <motion.div variants={fadeInUp} className="text-center">
            <span className="text-5xl block mb-4">🗾</span>
            <h1 className="font-display text-2xl font-bold text-stone-900 mb-2">
              日本 AI 定制攻略
            </h1>
            <p className="text-stone-500 text-sm">
              先免费看第一天，觉得好再决定
            </p>
          </motion.div>
          <motion.div variants={fadeInUp}>
            <Link href="/order">
              <Button variant="warm" size="lg" className="w-full">
                🆓 免费生成我的专属行程 →
              </Button>
            </Link>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-warm-50 py-8 px-4">
      <div className="max-w-md mx-auto">
        <motion.div variants={staggerContainer} initial="initial" animate="animate" className="space-y-6">

          {/* 分享卡片预览图 */}
          {cardImgUrl && (
            <motion.div variants={fadeInUp} className="rounded-2xl overflow-hidden shadow-lg">
              <img
                src={cardImgUrl}
                alt="行程分享卡"
                className="w-full"
                style={{ aspectRatio: "800/420" }}
              />
            </motion.div>
          )}

          {/* 品牌标识 */}
          <motion.div variants={fadeInUp} className="text-center">
            <p className="text-xs text-stone-400">jtrip.ai · 日本旅行 AI 定制攻略</p>
          </motion.div>

          {/* 卡片类型对应内容 */}
          <motion.div variants={fadeInUp}>
            {data.type === "invite" ? (
              <InviteLanding data={data} />
            ) : data.type === "day1" || data.type === "result" ? (
              <Day1Landing data={data} />
            ) : (
              <GenericLanding data={data} />
            )}
          </motion.div>

          {/* 底部信任背书 */}
          <motion.div variants={fadeInUp} className="text-center space-y-1">
            <p className="text-xs text-stone-400">已为 1,200+ 旅行者定制行程</p>
            <p className="text-xs text-stone-400">免费看 · 满意再付 · 2次不满意可改</p>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}
