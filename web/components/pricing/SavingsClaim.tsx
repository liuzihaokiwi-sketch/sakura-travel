import { SAVINGS_CLAIM } from "@/lib/content/pricing";

export function SavingsClaim() {
  return (
    <div className="my-4 rounded-lg border-l-4 border-amber-400 bg-amber-50 px-4 py-3">
      <p className="text-sm font-bold text-amber-800">{SAVINGS_CLAIM.title}</p>
      <p className="mt-1 text-sm text-amber-700">{SAVINGS_CLAIM.headline}</p>
      <p className="text-sm text-amber-700">{SAVINGS_CLAIM.subline}</p>
      <div className="mt-2 rounded-md bg-amber-100 px-3 py-2">
        <p className="text-sm font-semibold text-amber-900">{SAVINGS_CLAIM.detail}</p>
        <p className="text-sm text-amber-800">→ {SAVINGS_CLAIM.roi}</p>
      </div>
      <p className="mt-2 text-xs text-amber-500">{SAVINGS_CLAIM.disclaimer}</p>
    </div>
  );
}
