"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { WECHAT_ID } from "@/lib/constants";

export function FloatingCTA() {
  const searchParams = useSearchParams();
  const isExport = searchParams.get("export") === "true";
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(false);

  if (isExport) return null;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(WECHAT_ID);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-2">
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.9 }}
            className="bg-stone-900 text-white rounded-xl px-4 py-3 shadow-2xl text-sm"
          >
            <p className="text-stone-400 text-xs mb-1">加微信 · 备注「樱花」</p>
            <button
              onClick={handleCopy}
              className="font-mono text-warm-300 hover:text-warm-200 transition-colors"
            >
              {copied ? "✅ 已复制!" : WECHAT_ID}
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.button
        onClick={() => setExpanded(!expanded)}
        className="h-14 w-14 rounded-full bg-gradient-to-br from-warm-300 to-sakura-400 text-white shadow-lg flex items-center justify-center text-xl"
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
        animate={{
          boxShadow: [
            "0 0 0 0 rgba(247,147,30,0.4)",
            "0 0 0 12px rgba(247,147,30,0)",
          ],
        }}
        transition={{
          boxShadow: { duration: 1.5, repeat: Infinity },
        }}
      >
        {expanded ? "✕" : "💬"}
      </motion.button>
    </div>
  );
}
