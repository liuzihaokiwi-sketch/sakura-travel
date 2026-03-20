"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { fadeInUp } from "@/lib/animations";
import { WECHAT_ID, TRUST_ITEMS } from "@/lib/constants";

export function CTABanner() {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(WECHAT_ID);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <motion.section
      variants={fadeInUp}
      initial="initial"
      whileInView="animate"
      viewport={{ once: true }}
      className="bg-gradient-to-r from-warm-300 to-warm-400 py-5"
    >
      <div className="mx-auto max-w-5xl px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="text-center sm:text-left">
          <p className="text-white font-bold text-lg">
            🎁 免费体验 · 加微信备注「樱花」· 不满意不收费
          </p>
          <div className="flex items-center gap-3 mt-1 justify-center sm:justify-start">
            {TRUST_ITEMS.map((t) => (
              <span key={t} className="text-xs text-white/80">{t}</span>
            ))}
          </div>
        </div>

        <button
          onClick={handleCopy}
          className="shrink-0 bg-white/20 backdrop-blur-sm border border-white/30 hover:bg-white/30 transition-colors rounded-xl px-5 py-2.5 flex items-center gap-2"
        >
          <span className="text-white text-sm">微信号</span>
          <span className="font-mono font-bold text-white text-base">
            {copied ? "✅ 已复制!" : WECHAT_ID}
          </span>
        </button>
      </div>
    </motion.section>
  );
}
