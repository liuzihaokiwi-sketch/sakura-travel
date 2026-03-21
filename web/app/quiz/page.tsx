"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";

/* ── 选项数据 ──────────────────────────────────────────────────────────────── */

const DESTINATIONS = [
  { value: "tokyo", label: "东京", img: "/destinations/tokyo.jpg" },
  { value: "osaka_kyoto", label: "大阪+京都", img: "/destinations/osaka.jpg" },
  { value: "tokyo_osaka_kyoto", label: "东京+大阪+京都", img: "/destinations/tokyo_osaka.jpg" },
  { value: "hokkaido", label: "北海道", img: "/destinations/hokkaido.jpg" },
  { value: "okinawa", label: "冲绳", img: "/destinations/okinawa.jpg" },
  { value: "other", label: "其他", img: "/destinations/other.jpg" },
];

const STYLES = [
  { value: "classic", label: "经典打卡", icon: "⛩️" },
  { value: "food", label: "美食为主", icon: "�" },
  { value: "photo", label: "拍照出片", icon: "📸" },
  { value: "culture", label: "深度文化", icon: "�" },
  { value: "family", label: "亲子轻松", icon: "👶" },
  { value: "shopping", label: "买买买", icon: "🛍️" },
];

/* ── Component ───────────────────────────────────────────────────────────────── */

export default function QuizPage() {
  const router = useRouter();
  const [destination, setDestination] = useState("tokyo"); // 默认东京
  const [style, setStyle] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleStyleSelect(selectedStyle: string) {
    setStyle(selectedStyle);
    setSubmitting(true);
    setError("");

    try {
      const res = await fetch("/api/quiz", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          destination,
          styles: [selectedStyle],
          // 免费阶段只收这 2 个信息
          party_type: "unknown",
          duration_days: 7,
        }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || "提交失败");
      }

      const data = await res.json();
      // 跳转到样片展示页
      router.push(`/sample/${data.trip_request_id}?dest=${destination}&style=${selectedStyle}`);
    } catch (e: any) {
      setError(e.message || "网络异常，请重试");
      setStyle(null);
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-[100dvh] bg-gradient-to-b from-stone-50 to-amber-50/30 flex items-center justify-center px-4 py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-lg"
      >
        {/* ── 目的地 ── */}
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-stone-900 mb-1">你想去哪？</h1>
          <p className="text-sm text-stone-400">选一个目的地，3 秒后看你的行程</p>
        </div>

        <div className="grid grid-cols-3 gap-2.5 mb-8">
          {DESTINATIONS.map((d) => (
            <button
              key={d.value}
              onClick={() => setDestination(d.value)}
              disabled={submitting}
              className={cn(
                "relative rounded-xl border-2 py-4 px-2 transition-all duration-200 text-center",
                destination === d.value
                  ? "border-amber-400 bg-amber-50 shadow-md shadow-amber-100/50 scale-[1.03]"
                  : "border-stone-100 bg-white hover:border-stone-200 hover:shadow-sm"
              )}
            >
              <span className={cn(
                "text-sm font-bold block",
                destination === d.value ? "text-amber-700" : "text-stone-700"
              )}>
                {d.label}
              </span>
            </button>
          ))}
        </div>

        {/* ── 风格 ── */}
        <div className="text-center mb-5">
          <h2 className="text-xl font-bold text-stone-900 mb-1">你更想怎么玩？</h2>
          <p className="text-sm text-stone-400">选完立即生成你的专属行程</p>
        </div>

        <div className="grid grid-cols-3 gap-2.5">
          {STYLES.map((s) => (
            <button
              key={s.value}
              onClick={() => handleStyleSelect(s.value)}
              disabled={submitting}
              className={cn(
                "flex flex-col items-center gap-2 py-4 px-2 rounded-xl border-2 transition-all duration-200",
                style === s.value
                  ? "border-amber-400 bg-amber-50 shadow-md scale-[1.03]"
                  : "border-stone-100 bg-white hover:border-stone-200 hover:shadow-sm",
                submitting && style !== s.value && "opacity-40 pointer-events-none"
              )}
            >
              <span className="text-2xl">{s.icon}</span>
              <span className={cn(
                "text-xs font-bold",
                style === s.value ? "text-amber-700" : "text-stone-600"
              )}>
                {s.label}
              </span>
            </button>
          ))}
        </div>

        {/* 加载状态 */}
        {submitting && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-6 text-center"
          >
            <div className="inline-flex items-center gap-2 text-amber-600">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <span className="text-sm font-medium">正在为你规划…</span>
            </div>
          </motion.div>
        )}

        {/* 错误 */}
        {error && (
          <p className="mt-4 text-center text-sm text-red-500">{error}</p>
        )}

        {/* 底部提示 */}
        <p className="mt-8 text-center text-[11px] text-stone-300">
          免费体验 · 无需注册 · 3 秒出结果
        </p>
      </motion.div>
    </div>
  );
}