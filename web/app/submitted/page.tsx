"use client";

import { motion } from "framer-motion";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { PDF_NOTICE } from "@/lib/content/pricing";

// ── Config: 规划师微信号（后续可改为环境变量或 API 获取）──────────────────────
const PLANNER_WECHAT = "sakura_plan";
const PLANNER_QR_IMAGE = "/planner-qr.png"; // public/planner-qr.png

// ── Inner component (uses useSearchParams) ──────────────────────────────────

function SubmittedContent() {
  const searchParams = useSearchParams();
  const tripId = searchParams.get("id") || "";

  return (
    <div className="min-h-screen flex items-center justify-center bg-warm-50 px-6 py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        {/* Success icon */}
        <div className="text-center mb-6">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
            className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-green-50"
          >
            <span className="text-4xl">✅</span>
          </motion.div>
        </div>

        {/* Main message */}
        <h1 className="font-display text-2xl md:text-3xl font-bold text-stone-900 text-center mb-2">
          已收到你的需求！
        </h1>
        <p className="text-stone-500 text-center mb-8">
          规划师正在为你安排行程
        </p>

        {/* Steps card */}
        <div className="bg-white rounded-2xl p-6 shadow-sm space-y-5 mb-6">
          <h2 className="text-lg font-semibold text-stone-900">接下来</h2>

          {/* Step 1 */}
          <div className="flex gap-4">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-warm-100 flex items-center justify-center">
              <span className="text-sm font-bold text-warm-500">1</span>
            </div>
            <div>
              <p className="font-medium text-stone-900">添加规划师微信</p>
              <p className="text-sm text-stone-500 mt-0.5">
                微信号：<span className="font-mono text-stone-700">{PLANNER_WECHAT}</span>
              </p>
            </div>
          </div>

          {/* Step 2 */}
          <div className="flex gap-4">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-warm-100 flex items-center justify-center">
              <span className="text-sm font-bold text-warm-500">2</span>
            </div>
            <div>
              <p className="font-medium text-stone-900">2 小时内收到第一天行程</p>
              <p className="text-sm text-stone-500 mt-0.5">
                规划师会通过微信把你的第一天行程发给你，先看看风格和质量
              </p>
            </div>
          </div>

          {/* Step 3 */}
          <div className="flex gap-4">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-warm-100 flex items-center justify-center">
              <span className="text-sm font-bold text-warm-500">3</span>
            </div>
            <div>
              <p className="font-medium text-stone-900">满意再决定</p>
              <p className="text-sm text-stone-500 mt-0.5">
                觉得不错再看完整方案，不满意不花一分钱
              </p>
            </div>
          </div>
        </div>

        {/* PDF 交付说明 */}
        <div className="bg-stone-50 rounded-2xl p-5 mb-6 border border-stone-100">
          <div className="flex items-start gap-3">
            <span className="text-xl flex-shrink-0">📄</span>
            <div>
              <h3 className="text-sm font-semibold text-stone-800 mb-1">
                {PDF_NOTICE.successPage.heading}
              </h3>
              <p className="text-xs text-stone-500 mb-2">{PDF_NOTICE.successPage.intro}</p>
              <ul className="space-y-1">
                {PDF_NOTICE.successPage.bullets.map((b) => (
                  <li key={b} className="flex items-start gap-1.5 text-xs text-stone-500">
                    <span className="text-stone-400 mt-0.5 flex-shrink-0">·</span>
                    <span>{b}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* QR Code area */}
        <div className="bg-white rounded-2xl p-6 shadow-sm text-center">
          <p className="text-sm text-stone-500 mb-4">扫码添加规划师微信</p>

          {/* QR placeholder — replace with actual QR image */}
          <div className="inline-block bg-stone-50 rounded-xl p-4 mb-4">
            <div className="w-48 h-48 bg-stone-100 rounded-lg flex items-center justify-center text-stone-400">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={PLANNER_QR_IMAGE}
                alt="规划师微信二维码"
                className="w-full h-full object-contain"
                onError={(e) => {
                  // Fallback if QR image not found
                  (e.target as HTMLImageElement).style.display = "none";
                  (e.target as HTMLImageElement).parentElement!.innerHTML =
                    '<div class="w-48 h-48 flex flex-col items-center justify-center text-stone-400"><span class="text-4xl mb-2">📱</span><span class="text-xs">请长按复制微信号添加</span></div>';
                }}
              />
            </div>
          </div>

          {/* Copy WeChat ID */}
          <button
            onClick={() => {
              navigator.clipboard.writeText(PLANNER_WECHAT).then(() => {
                alert("已复制微信号：" + PLANNER_WECHAT);
              }).catch(() => {
                // Fallback for browsers without clipboard API
                prompt("请复制微信号：", PLANNER_WECHAT);
              });
            }}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-warm-100 text-warm-600 text-sm font-medium hover:bg-warm-200 transition-colors"
          >
            📋 复制微信号
          </button>

          <p className="text-xs text-stone-400 mt-4">
            🔒 加微信是为了方便发方案和后续沟通，不会群发广告，随时可删
          </p>
        </div>

        {/* Trip ID reference (subtle) */}
        {tripId && (
          <p className="text-xs text-stone-300 text-center mt-6">
            参考编号：{tripId.slice(0, 8)}
          </p>
        )}
      </motion.div>
    </div>
  );
}

// ── Page wrapper (Suspense boundary for useSearchParams) ────────────────────

export default function SubmittedPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-warm-50">
        <p className="text-stone-400">加载中...</p>
      </div>
    }>
      <SubmittedContent />
    </Suspense>
  );
}
