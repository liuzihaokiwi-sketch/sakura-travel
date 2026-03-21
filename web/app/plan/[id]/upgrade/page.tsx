"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { fadeInUp } from "@/lib/animations";
import { WECHAT_ID } from "@/lib/constants";
import { copyToClipboard } from "@/lib/clipboard";
import { useState } from "react";

const UPGRADE_BENEFITS = [
  { icon: "💬", title: "1对1需求沟通", desc: "微信直接和规划师聊，说清楚你想要什么" },
  { icon: "✏️", title: "5次行程精调", desc: "比标准版多3次，改到你满意为止" },
  { icon: "📞", title: "出行前答疑", desc: "出发前有任何问题，随时问" },
  { icon: "💍", title: "特别场景安排", desc: "蜜月、求婚、纪念日、生日惊喜" },
  { icon: "🧑‍💼", title: "专属顾问跟进", desc: "不是机器回复，是真人帮你把关" },
];

export default function UpgradePage({ params }: { params: { id: string } }) {
  const [copied, setCopied] = useState(false);

  return (
    <div className="min-h-[calc(100vh-3.5rem)] bg-warm-50 py-12 px-6">
      <motion.div variants={fadeInUp} initial="initial" animate="animate" className="max-w-lg mx-auto text-center">
        <p className="text-xs tracking-widest text-warm-400 font-mono mb-2">UPGRADE</p>
        <h1 className="font-display text-3xl font-bold text-stone-900 mb-2">升级到深度管家版</h1>
        <p className="text-stone-500 text-sm mb-8">让人帮你全程把关，不只是给你方案</p>

        <div className="bg-white rounded-2xl border border-stone-100 p-6 text-left mb-6">
          <div className="flex items-baseline gap-2 mb-4">
            <span className="font-mono text-3xl font-black text-warm-400">¥888</span>
            <span className="text-sm text-stone-400">含行程优化版全部内容</span>
          </div>

          <p className="text-xs text-stone-400 mb-4">
            你已购买行程优化版（¥248），升级只需补差价 <span className="font-bold text-warm-400">¥640</span>
          </p>

          <div className="space-y-4">
            {UPGRADE_BENEFITS.map((b) => (
              <div key={b.title} className="flex gap-3">
                <span className="text-xl">{b.icon}</span>
                <div>
                  <p className="text-sm font-semibold text-stone-800">{b.title}</p>
                  <p className="text-xs text-stone-500">{b.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-stone-900 rounded-2xl p-6 mb-6">
          <p className="text-stone-400 text-xs mb-2">升级请联系专属顾问</p>
          <p className="font-mono text-xl font-bold bg-gradient-to-r from-warm-300 to-sakura-300 bg-clip-text text-transparent mb-3">{WECHAT_ID}</p>
          <button
            onClick={async () => { await copyToClipboard(WECHAT_ID); setCopied(true); setTimeout(() => setCopied(false), 1500); }}
            className="bg-gradient-to-r from-warm-300 to-warm-400 text-white font-semibold py-2.5 px-8 rounded-xl text-sm"
          >
            {copied ? "✅ 已复制!" : "复制微信号 · 备注「升级」"}
          </button>
        </div>

        <Link href={`/plan/${params.id}`}>
          <Button variant="ghost" size="sm">← 返回我的行程</Button>
        </Link>
      </motion.div>
    </div>
  );
}
