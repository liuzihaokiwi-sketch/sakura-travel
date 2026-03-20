"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { fadeInUp, staggerContainer } from "@/lib/animations";

const TIERS = [
  {
    id: "free",
    name: "一日体验版",
    tagline: "先看看适不适合你",
    price: "免费",
    priceNote: "",
    featured: false,
    cta: "先免费看一天 →",
    href: "/quiz",
    includes: [
      "1 天完整行程安排",
      "2-3 个景点的推荐理由",
      "当天交通指引",
      "行程品质预览",
    ],
    excludes: [
      "其余天数行程",
      "餐厅和酒店推荐",
      "避坑指南和出行准备",
    ],
    who: "想先看看效果再决定的人",
  },
  {
    id: "main",
    name: "完整攻略·首发特惠",
    tagline: "完整行程 · 每一天都安排好",
    price: "¥248",
    priceNote: "首发特惠 · 原价¥368",
    featured: true,
    cta: "先免费看一天 →",
    href: "/quiz",
    badge: "🔥 90%用户选择",
    includes: [
      "全程每日行程（30-40页完整攻略）",
      "每天为什么这样安排的解释",
      "餐厅精选 + 预约指引 + 替代方案",
      "酒店区域建议 + 选择理由",
      "交通最优方案 + 省钱技巧",
      "避坑指南 + 出行前准备清单",
      "拍照攻略 + 最佳时段",
      "Plan B 备选方案",
      "预订优先级提醒",
      "全程预算参考",
      "2 次行程精调",
    ],
    excludes: [
      "1对1深度沟通",
      "出行期间答疑",
    ],
    who: "第一次去日本、想省心不踩坑的人",
  },
  {
    id: "premium",
    name: "尊享定制版",
    tagline: "有人帮你全程把关",
    price: "¥888",
    priceNote: "",
    featured: false,
    cta: "了解尊享定制 →",
    href: "/quiz",
    includes: [
      "完整攻略全部内容",
      "1对1需求深度沟通",
      "不限次行程精调",
      "出行期间实时答疑",
      "蜜月/纪念日特别安排",
      "隐藏小众目的地推荐",
      "高端餐厅酒店精选",
    ],
    excludes: [],
    who: "蜜月、纪念日、或想要全程有人跟进的人",
  },
];

// Comparison table — 从用户结果角度写
const COMPARE_ROWS = [
  { label: "知道每天去哪、路线怎么走", free: "1天", main: "✅ 精确到小时", premium: "✅ 精确到小时" },
  { label: "不用自己查交通换乘", free: "—", main: "✅ 手把手写清楚", premium: "✅ 手把手写清楚" },
  { label: "每顿饭不用现场纠结", free: "—", main: "✅ 推荐+备选", premium: "✅ 推荐+备选+高端精选" },
  { label: "门票/预约不怕漏掉", free: "—", main: "✅ 提醒清单", premium: "✅ 提醒清单" },
  { label: "下雨/排队有备选方案", free: "—", main: "✅ 每天都有Plan B", premium: "✅ 每天都有Plan B" },
  { label: "不用花两周做功课", free: "部分", main: "✅ 拿到就能出发", premium: "✅ 拿到就能出发" },
  { label: "有人帮我把关行程合理性", free: "—", main: "—", premium: "✅ 1对1沟通" },
  { label: "旅途中遇到问题能问人", free: "—", main: "—", premium: "✅ 实时答疑" },
  { label: "攻略页数", free: "3-5页", main: "30-40页", premium: "40-50页" },
  { label: "有人帮我调整行程", free: "—", main: "2次精调", premium: "不限次精调" },
];

export default function PricingPage() {
  return (
    <div className="min-h-[calc(100vh-3.5rem)] bg-warm-50 py-12 px-6">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <motion.div
          variants={fadeInUp}
          initial="initial"
          animate="animate"
          className="text-center mb-12"
        >
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
          {TIERS.map((tier) => (
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
                  {tier.price}
                </span>
                {tier.priceNote && (
                  <p className="text-xs text-stone-400 mt-1">
                    <span className="line-through">¥368</span>{" "}
                    <span className="text-warm-400 font-medium">{tier.priceNote}</span>
                  </p>
                )}
              </div>

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
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-stone-100">
                  <th className="text-left p-4 text-stone-500 font-medium">你关心的</th>
                  <th className="p-4 text-stone-500 font-medium text-center">免费体验</th>
                  <th className="p-4 text-warm-400 font-bold text-center bg-warm-50/50">⭐ 完整攻略</th>
                  <th className="p-4 text-stone-500 font-medium text-center">尊享定制</th>
                </tr>
              </thead>
              <tbody>
                {COMPARE_ROWS.map((row, i) => (
                  <tr key={row.label} className={i % 2 === 0 ? "" : "bg-stone-50/50"}>
                    <td className="p-4 text-stone-700 font-medium">{row.label}</td>
                    <td className="p-4 text-center text-stone-400">{row.free}</td>
                    <td className="p-4 text-center text-stone-800 font-medium bg-warm-50/30">{row.main}</td>
                    <td className="p-4 text-center text-stone-500">{row.premium}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
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