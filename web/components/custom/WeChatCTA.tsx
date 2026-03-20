"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { scaleIn } from "@/lib/animations";
import { WECHAT_ID, TRUST_ITEMS } from "@/lib/constants";

export function WeChatCTA() {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(WECHAT_ID);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <motion.div
      variants={scaleIn}
      initial="initial"
      animate="animate"
      className="bg-stone-900 rounded-2xl p-5 text-center"
    >
      <p className="text-stone-400 text-xs tracking-wide mb-2">
        加微信 · 备注「樱花」
      </p>

      <p className="font-mono text-xl font-bold bg-gradient-to-r from-warm-300 to-sakura-300 bg-clip-text text-transparent mb-3">
        {WECHAT_ID}
      </p>

      <button
        onClick={handleCopy}
        className="w-full bg-gradient-to-r from-warm-300 to-warm-400 hover:from-warm-400 hover:to-warm-500 text-white font-semibold py-2.5 rounded-xl transition-all duration-200 text-sm shadow-lg shadow-warm-300/30"
      >
        {copied ? "✅ 已复制!" : "一键复制微信号"}
      </button>

      <div className="flex flex-wrap justify-center gap-2 mt-3">
        {TRUST_ITEMS.map((t) => (
          <span key={t} className="text-[10px] text-stone-500">{t}</span>
        ))}
      </div>
    </motion.div>
  );
}
