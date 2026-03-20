"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { fadeInUp } from "@/lib/animations";
import { WECHAT_ID, TRUST_ITEMS } from "@/lib/constants";

export default function CheckoutPage({ params }: { params: { id: string } }) {
  const [copied, setCopied] = useState(false);
  const [confirmed, setConfirmed] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(WECHAT_ID);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="min-h-[calc(100vh-3.5rem)] flex items-center justify-center bg-warm-50 px-6">
      <motion.div
        variants={fadeInUp}
        initial="initial"
        animate="animate"
        className="w-full max-w-md"
      >
        {/* Order summary */}
        <div className="bg-white rounded-2xl border border-stone-100 shadow-sm p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="font-bold text-stone-900">行程优化版</h2>
              <p className="text-xs text-stone-400">完整行程 · 30-40页 · 含2次精调</p>
            </div>
            <Badge variant="warm">首批专享</Badge>
          </div>

          <div className="flex items-baseline gap-2 mb-4">
            <span className="font-mono text-3xl font-black text-warm-400">¥248</span>
            <span className="text-sm text-stone-400 line-through">¥298</span>
          </div>

          <div className="border-t border-stone-100 pt-4 space-y-2 text-sm text-stone-500">
            <div className="flex justify-between">
              <span>订单号</span>
              <span className="font-mono text-stone-700">{params.id.slice(0, 8).toUpperCase()}</span>
            </div>
            <div className="flex justify-between">
              <span>交付方式</span>
              <span className="text-stone-700">H5在线查看 + 可导出图片</span>
            </div>
            <div className="flex justify-between">
              <span>交付时间</span>
              <span className="text-stone-700">付款后24小时内</span>
            </div>
          </div>
        </div>

        {/* Payment method */}
        <div className="bg-white rounded-2xl border border-stone-100 shadow-sm p-6 mb-6">
          <h3 className="font-bold text-stone-900 mb-4">付款方式</h3>
          
          <div className="bg-stone-50 rounded-xl p-5 text-center mb-4">
            <p className="text-sm text-stone-500 mb-3">添加专属顾问微信，备注订单号即可付款</p>
            
            <div className="bg-stone-900 rounded-xl p-4 inline-block mb-3">
              <p className="text-stone-400 text-xs mb-1">微信号</p>
              <p className="font-mono text-lg font-bold bg-gradient-to-r from-warm-300 to-sakura-300 bg-clip-text text-transparent">
                {WECHAT_ID}
              </p>
            </div>

            <div>
              <button
                onClick={handleCopy}
                className="bg-warm-300 hover:bg-warm-400 text-white font-semibold py-2 px-6 rounded-xl transition-colors text-sm"
              >
                {copied ? "✅ 已复制!" : "一键复制微信号"}
              </button>
            </div>
          </div>

          <div className="space-y-2 text-xs text-stone-400">
            <p>📋 添加微信后，发送订单号 <span className="font-mono text-stone-600">{params.id.slice(0, 8).toUpperCase()}</span></p>
            <p>💳 支持微信转账 / 支付宝转账 / 红包</p>
            <p>⏱️ 确认付款后，会发送正式问卷链接</p>
          </div>
        </div>

        {/* Already paid */}
        {!confirmed ? (
          <Button
            variant="outline"
            className="w-full"
            onClick={() => setConfirmed(true)}
          >
            我已添加微信并付款
          </Button>
        ) : (
          <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 text-center">
            <p className="text-emerald-700 font-medium text-sm">✅ 收到！我们会在微信上确认并发送问卷</p>
            <p className="text-emerald-600/60 text-xs mt-1">通常 10 分钟内响应</p>
          </div>
        )}

        {/* Trust */}
        <div className="flex justify-center gap-4 mt-6">
          {TRUST_ITEMS.map((t) => (
            <span key={t} className="text-xs text-stone-400">{t}</span>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
