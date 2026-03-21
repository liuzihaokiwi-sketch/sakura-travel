"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { fadeInUp, staggerContainer } from "@/lib/animations";
import { SavingsClaim } from "@/components/pricing/SavingsClaim";
import { PricingFAQ } from "@/components/pricing/PricingFAQ";
import { PRICING_FOOTNOTE, PDF_NOTICE } from "@/lib/content/pricing";
import type { PricingData } from "./page";

export default function PricingClient({ data }: { data: PricingData }) {
  const { tiers, compare_rows } = data;

  // 找出三档（兼容 id 字段 free/standard/premium）
  const freeTier = tiers.find((t) => t.id === "free");
  const standardTier = tiers.find((t) => t.id === "standard" || t.id === "main");
  const premiumTier = tiers.find((t) => t.id === "premium");

  return (
    <div className="min-h-[calc(100vh-3.5rem)] bg-warm-50 py-12 px-6">
      <div className="max-w-5xl mx-auto">

        {/* Header */}
        <motion.div variants={fadeInUp} initial="initial" animate="animate" className="text-center mb-12">
          <h1 className="font-display text-3xl md:text-4xl font-bold text-stone-900 mb-3">
            选一个适合你的方案
          </h1>
          <p className="text-stone-500 text-base max-w-lg mx-auto">
            不确定？先免费看一天，觉得好再决定。不满意不花一分钱。
          </p>
        </motion.div>

        {/* Pricing cards */}
        <motion.div
          variants={staggerContainer}
          initial="initial"
          animate="animate"
          className="grid md:grid-cols-3 gap-6 mb-16"
        >
          {tiers.map((tier) => (
            <motion.div
              key={tier.id}
              variants={fadeInUp}
              className={cn(
                "relative rounded-2xl p-6 flex flex-col",
                tier.featured
                  ? "bg-white border-2 border-warm-300 shadow-xl shadow-warm-200/20 scale-[1.03] z-10"
                  : "bg-white border border-stone-100 shadow-sm",
                tier.id === "premium" && "opacity-90"
              )}
            >
              {tier.badge && (
                <Badge variant="warm" className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 text-xs">
                  {tier.badge}
                </Badge>
              )}

              <h3 className="text-lg font-bold text-stone-900">{tier.name}</h3>
              <p className="text-sm text-stone-400 mt-1">{tier.tagline}</p>

              <div className="my-5">
                <span className={cn(
                  "font-mono font-black",
                  tier.featured ? "text-4xl text-warm-400" : "text-3xl text-stone-800"
                )}>
                  {tier.price_display}
                </span>
                {tier.price_note && (
                  <p className="text-xs text-stone-400 mt-1">
                    {tier.original_price && (
                      <span className="line-through mr-1">¥{tier.original_price}</span>
                    )}
                    <span className="text-warm-400 font-medium">{tier.price_note}</span>
                  </p>
                )}
              </div>

              {/* 深度比价系统（仅 premium 版） */}
              {tier.id === "premium" && (
                <div className="mb-2">
                  <SavingsClaim />
                </div>
              )}

              {/* Includes */}
              <ul className="space-y-2 flex-1 mb-6">
                {tier.includes.map((item) => (
                  <li key={item} className="flex items-start gap-2 text-sm">
                    <span className="text-warm-300 mt-0.5 shrink-0">✓</span>
                    <span className="text-stone-600">{item}</span>
                  </li>
                ))}
                {tier.excludes.map((item) => (
                  <li key={item} className="flex items-start gap-2 text-sm">
                    <span className="text-stone-300 mt-0.5 shrink-0">—</span>
                    <span className="text-stone-300">{item}</span>
                  </li>
                ))}
              </ul>

              {/* 精调次数角标 */}
              {tier.modifications > 0 && (
                <p className="text-[11px] text-warm-500 font-medium mb-2">
                  🔄 含 {tier.modifications} 次免费精调
                </p>
              )}

              {/* 天数浮动说明 */}
              {(tier.id === "standard" || tier.id === "premium") && (
                <p className="text-[11px] text-stone-400 mb-2">
                  其他天数小幅浮动，制作前与你确认
                </p>
              )}

              <p className="text-[11px] text-stone-400 mb-3">适合：{tier.who}</p>

              <Link href={tier.href}>
                <Button
                  variant={tier.featured ? "warm" : "outline"}
                  size={tier.featured ? "lg" : "default"}
                  className="w-full"
                >
                  {tier.cta}
                </Button>
              </Link>
            </motion.div>
          ))}
        </motion.div>

        {/* Comparison table */}
        <motion.div
          variants={fadeInUp}
          initial="initial"
          whileInView="animate"
          viewport={{ once: true }}
          className="bg-white rounded-2xl border border-stone-100 overflow-hidden"
        >
          <div className="p-6 border-b border-stone-100">
            <h2 className="text-lg font-bold text-stone-900">详细对比</h2>
            <p className="text-sm text-stone-400">从你关心的角度看区别</p>
          </div>

          {/* 手机端 Accordion（< md） */}
          <div className="block md:hidden divide-y divide-stone-100">
            {compare_rows.map((row) => (
              <details key={row.label} className="group">
                <summary className="flex items-center justify-between px-4 py-3 cursor-pointer list-none select-none">
                  <span className="text-sm font-medium text-stone-700">{row.label}</span>
                  <span className="text-stone-400 text-xs transition-transform duration-200 group-open:rotate-45 flex-shrink-0 ml-2">＋</span>
                </summary>
                <div className="px-4 pb-3 grid grid-cols-3 gap-2 text-xs">
                  <div className="text-center">
                    <p className="text-[10px] text-stone-400 mb-1">{freeTier?.name ?? "免费"}</p>
                    <p className="text-stone-500">{row.free || "—"}</p>
                  </div>
                  <div className="text-center bg-warm-50/50 rounded-lg px-1 py-1">
                    <p className="text-[10px] text-warm-500 font-bold mb-1">⭐ 推荐</p>
                    <p className="text-stone-800 font-medium">{row.standard || "—"}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-[10px] text-stone-400 mb-1">{premiumTier?.name ?? "尊享"}</p>
                    <p className="text-stone-500">{row.premium || "—"}</p>
                  </div>
                </div>
              </details>
            ))}
          </div>

          {/* 桌面端 Table（md+） */}
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-stone-100">
                  <th className="text-left p-4 text-stone-500 font-medium">你关心的</th>
                  <th className="p-4 text-stone-500 font-medium text-center">
                    {freeTier?.name ?? "免费体验"}
                  </th>
                  <th className="p-4 text-warm-400 font-bold text-center bg-warm-50/50">
                    ⭐ {standardTier?.name ?? "完整攻略"}
                  </th>
                  <th className="p-4 text-stone-500 font-medium text-center">
                    {premiumTier?.name ?? "尊享定制"}
                  </th>
                </tr>
              </thead>
              <tbody>
                {compare_rows.map((row, i) => (
                  <tr key={row.label} className={i % 2 === 0 ? "" : "bg-stone-50/50"}>
                    <td className="p-4 text-stone-700 font-medium">{row.label}</td>
                    <td className="p-4 text-center text-stone-400">{row.free}</td>
                    <td className="p-4 text-center text-stone-800 font-medium bg-warm-50/30">{row.standard}</td>
                    <td className="p-4 text-center text-stone-500">{row.premium}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>

        {/* 价格页小字 + PDF 说明 */}
        <motion.div
          variants={fadeInUp} initial="initial" whileInView="animate" viewport={{ once: true }}
          className="mt-10 space-y-2 text-center"
        >
          <p className="text-xs text-stone-400 max-w-xl mx-auto leading-relaxed">
            {PRICING_FOOTNOTE}
          </p>
          <p className="text-xs text-stone-400 max-w-xl mx-auto">
            {PDF_NOTICE.pricingPage}
          </p>
        </motion.div>

        {/* FAQ */}
        <motion.div
          variants={fadeInUp} initial="initial" whileInView="animate" viewport={{ once: true }}
          className="mt-12"
        >
          <PricingFAQ />
        </motion.div>

        {/* Bottom CTA */}
        <div className="text-center mt-12">
          <p className="text-stone-400 text-sm mb-4">不确定？先免费看一天，觉得好再决定</p>
          <Link href="/quiz">
            <Button variant="warm" size="xl">
              先免费看一天 →
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
