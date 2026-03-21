import { PRICING_FAQ } from "@/lib/content/pricing";

export function PricingFAQ() {
  return (
    <section className="mx-auto max-w-2xl">
      <h2 className="mb-4 text-lg font-bold text-stone-800">常见问题</h2>
      <div className="divide-y divide-stone-100 rounded-xl border border-stone-200 bg-white overflow-hidden">
        {PRICING_FAQ.map(({ q, a }, i) => (
          <details key={i} className="group">
            <summary className="flex cursor-pointer items-start justify-between gap-4 px-5 py-4 text-sm font-medium text-stone-800 marker:content-none hover:bg-stone-50 transition-colors">
              <span>{q}</span>
              {/* 展开/收起箭头 */}
              <span className="mt-0.5 flex-shrink-0 text-stone-400 transition-transform duration-200 group-open:rotate-45">
                ＋
              </span>
            </summary>
            {/* CSS transition via max-height trick */}
            <div className="overflow-hidden px-5 pb-4">
              <p className="text-sm leading-relaxed text-stone-500">{a}</p>
            </div>
          </details>
        ))}
      </div>
    </section>
  );
}
