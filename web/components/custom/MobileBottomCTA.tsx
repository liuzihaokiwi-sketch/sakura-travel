"use client";

import { WECHAT_ID } from "@/lib/constants";
import { copyToClipboard } from "@/lib/clipboard";

export function MobileBottomCTA() {
  return (
    <div className="lg:hidden fixed bottom-0 left-0 right-0 z-30 bg-white border-t border-stone-100 px-4 pt-3 pb-safe">
      <div className="flex items-center gap-3 pb-3">
        <div className="flex-1">
          <p className="text-xs font-semibold text-stone-800">想要这份专属行程？</p>
          <p className="text-xs text-stone-400 mt-0.5">微信联系，24h 内交付</p>
        </div>
        <button
          onClick={() => copyToClipboard(WECHAT_ID)}
          className="flex-shrink-0 bg-warm-400 hover:bg-warm-500 text-white text-sm font-semibold px-5 py-2.5 rounded-full transition-colors"
        >
          📋 复制微信号
        </button>
      </div>
    </div>
  );
}
