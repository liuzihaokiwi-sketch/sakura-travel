import { Suspense } from "react";
import PricingClient from "./PricingClient";

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

export interface CompareRow {
  label: string;
  free: string;
  standard: string;
  premium: string;
}

export interface PricingData {
  tiers: PricingTier[];
  compare_rows: CompareRow[];
}

// ── 默认兜底 ────────────────────────────────────────────────────────────────
const FALLBACK: PricingData = {
  tiers: [
    {
      id: "free", name: "一日体验版", tagline: "先看看适不适合你",
      price: 0, price_display: "免费", price_note: "", original_price: null,
      featured: false, badge: null, cta: "先免费看一天 →", href: "/quiz",
      modifications: 0,
      includes: ["1 天完整行程安排", "2-3 个景点的推荐理由", "当天交通指引", "行程品质预览"],
      excludes: ["其余天数行程", "餐厅和酒店推荐", "避坑指南和出行准备"],
      who: "想先看看效果再决定的人",
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
  compare_rows: [
    { label: "知道每天去哪、路线怎么走", free: "1天", standard: "✅ 精确到小时", premium: "✅ 精确到小时" },
    { label: "不用自己查交通换乘", free: "—", standard: "✅ 手把手写清楚", premium: "✅ 手把手写清楚" },
    { label: "每顿饭不用现场纠结", free: "—", standard: "✅ 推荐+备选", premium: "✅ 推荐+备选+高端精选" },
    { label: "门票/预约不怕漏掉", free: "—", standard: "✅ 提醒清单", premium: "✅ 提醒清单" },
    { label: "下雨/排队有备选方案", free: "—", standard: "✅ 每天都有Plan B", premium: "✅ 每天都有Plan B" },
    { label: "不用花两周做功课", free: "部分", standard: "✅ 拿到就能出发", premium: "✅ 拿到就能出发" },
    { label: "有人帮我把关行程合理性", free: "—", standard: "—", premium: "✅ 1对1沟通" },
    { label: "旅途中遇到问题能问人", free: "—", standard: "—", premium: "✅ 实时答疑" },
    { label: "攻略页数", free: "3-5页", standard: "30-40页", premium: "40-50页" },
    { label: "行程精调次数", free: "0次", standard: "2次", premium: "5次" },
  ],
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

