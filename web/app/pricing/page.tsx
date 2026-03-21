import { Suspense } from "react";
import PricingClient from "./PricingClient";
import { FREE_TIER_COPY, COMPARE_ROWS } from "@/lib/content/pricing";

// ── 价格数据类型 ────────────────────────────────────────────────────────────
export interface PricingTier {
  id: string;
  name: string;
  tagline: string;
  price: number;
  price_display: string;
  price_note: string;
  original_price: number | null;
  featured: boolean;
  badge: string | null;
  cta: string;
  href: string;
  modifications: number;
  includes: string[];
  excludes: string[];
  who: string;
}

export type { CompareRow } from "@/lib/content/pricing";
import type { CompareRow } from "@/lib/content/pricing";

export interface PricingData {
  tiers: PricingTier[];
  compare_rows: CompareRow[];
}

// ── 默认兜底 ────────────────────────────────────────────────────────────────
const FALLBACK: PricingData = {
  tiers: [
    {
      id: "free",
      name: FREE_TIER_COPY.name,
      tagline: FREE_TIER_COPY.tagline,
      price: FREE_TIER_COPY.price,
      price_display: FREE_TIER_COPY.price_display,
      price_note: FREE_TIER_COPY.price_note ?? "",
      original_price: null,
      featured: false,
      badge: FREE_TIER_COPY.badge,
      cta: FREE_TIER_COPY.cta,
      href: FREE_TIER_COPY.href,
      modifications: 0,
      includes: [...FREE_TIER_COPY.includes],
      excludes: [...FREE_TIER_COPY.excludes],
      who: FREE_TIER_COPY.who,
    },
    {
      id: "standard", name: "完整攻略·首发特惠", tagline: "完整行程 · 每一天都安排好",
      price: 248, price_display: "¥248", price_note: "首发特惠 · 原价¥368", original_price: 368,
      featured: true, badge: "🔥 90%用户选择", cta: "先免费看一天 →", href: "/quiz",
      modifications: 2,
      includes: [
        "全程每日行程（30-40页完整攻略）", "每天为什么这样安排的解释",
        "餐厅精选 + 预约指引 + 替代方案", "酒店区域建议 + 选择理由",
        "交通最优方案 + 省钱技巧", "避坑指南 + 出行前准备清单",
        "拍照攻略 + 最佳时段", "Plan B 备选方案", "预订优先级提醒",
        "全程预算参考", "2 次行程精调",
      ],
      excludes: ["1对1深度沟通", "出行期间答疑"],
      who: "第一次去日本、想省心不踩坑的人",
    },
    {
      id: "premium", name: "尊享定制版", tagline: "有人帮你全程把关",
      price: 888, price_display: "¥888", price_note: "", original_price: null,
      featured: false, badge: null, cta: "了解尊享定制 →", href: "/quiz",
      modifications: 5,
      includes: [
        "完整攻略全部内容", "1对1需求深度沟通", "5 次行程精调",
        "出行期间实时答疑", "蜜月/纪念日特别安排", "隐藏小众目的地推荐", "高端餐厅酒店精选",
      ],
      excludes: [],
      who: "蜜月、纪念日、或想要全程有人跟进的人",
    },
  ],
  compare_rows: COMPARE_ROWS,
};

// ── 服务端数据拉取（ISR 缓存5分钟）────────────────────────────────────────
async function fetchPricingData(): Promise<PricingData> {
  const BACKEND = process.env.BACKEND_URL || "http://localhost:8000";
  try {
    const res = await fetch(`${BACKEND}/config/product-tiers`, {
      next: { revalidate: 300 },
    });
    if (!res.ok) return FALLBACK;
    return (await res.json()) as PricingData;
  } catch {
    return FALLBACK;
  }
}

// ── Server Component（无 "use client"，可用 async/await）────────────────────
export default async function PricingPage() {
  const data = await fetchPricingData();
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center text-stone-400">加载中...</div>
    }>
      <PricingClient data={data} />
    </Suspense>
  );
}

