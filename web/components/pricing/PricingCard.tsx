import Link from "next/link";
import { cn } from "@/lib/utils";
import { PRICING_CARDS } from "@/lib/content/pricing";
import { SavingsClaim } from "./SavingsClaim";

interface PricingCardProps {
  tier: "standard" | "pro";
  /** 从问卷页跳转时带上 from 参数，用于转化追踪 */
  quizHref?: string;
}

export function PricingCard({ tier, quizHref }: PricingCardProps) {
  const card = PRICING_CARDS[tier];
  const isPro = tier === "pro";
  const href = quizHref ?? `/quiz?from=pricing&tier=${tier}`;

  return (
    <div
      className={cn(
        "relative flex flex-col rounded-2xl border p-6 shadow-sm transition-shadow hover:shadow-md",
        isPro
          ? "border-rose-300 bg-white ring-2 ring-rose-200"
          : "border-stone-200 bg-white"
      )}
    >
      {/* 推荐角标 */}
      {card.badge && (
        <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-rose-600 px-4 py-0.5 text-xs font-semibold text-white shadow">
          {card.badge}
        </span>
      )}

      {/* 标题 */}
      <h3 className="text-base font-bold text-stone-800">{card.title}</h3>

      {/* 价格 */}
      <div className="mt-3 flex items-baseline gap-1">
        <span className="text-4xl font-extrabold text-stone-900">
          ¥{card.price}
        </span>
      </div>
      <p className="mt-0.5 text-xs text-stone-400">{card.priceSuffix}</p>

      {/* 比价系统 block（仅深度版） */}
      {"savingsClaim" in card && <SavingsClaim />}

      {/* 权益列表 */}
      <ul className="mt-4 space-y-2 flex-1">
        {card.benefits.map((b) => (
          <li key={b} className="flex items-start gap-2 text-sm text-stone-700">
            <span className="mt-0.5 flex-shrink-0 text-emerald-500 font-bold">✓</span>
            <span>{b}</span>
          </li>
        ))}
      </ul>

      {/* 浮动说明 */}
      <p className="mt-4 text-xs text-stone-400">{card.floatNote}</p>

      {/* CTA */}
      <Link
        href={href}
        className={cn(
          "mt-5 block rounded-full py-3 text-center text-sm font-semibold transition-colors",
          isPro
            ? "bg-rose-600 text-white hover:bg-rose-700"
            : "border border-stone-300 text-stone-700 hover:border-rose-400 hover:text-rose-600"
        )}
      >
        {card.cta}
      </Link>
    </div>
  );
}
