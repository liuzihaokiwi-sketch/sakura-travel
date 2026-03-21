import { AdvantageGrid } from "@/components/custom/AdvantageGrid";
import { ProcessSteps } from "@/components/custom/ProcessSteps";
import { WeChatCTA } from "@/components/custom/WeChatCTA";
import { MobileBottomCTA } from "@/components/custom/MobileBottomCTA";

export default function CustomPage() {
  return (
    <div
      className="flex overflow-hidden"
      style={{ height: "calc(100vh - 3.5rem)" }}
    >
      {/* Left: Dark Hero Column */}
      <div className="hidden lg:flex w-[280px] shrink-0 relative overflow-hidden flex-col justify-between">
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{
            backgroundImage:
              "url('https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=600&q=80')",
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-black/80 via-black/75 to-black/85" />

        <div className="relative z-10 p-6 flex-1 flex flex-col justify-center">
          <p className="text-xs text-white/50 tracking-widest mb-4 font-mono">
            CUSTOM SERVICE
          </p>
          <h2 className="font-display text-2xl font-bold text-white leading-snug mb-3">
            别再用AI
            <br />
            生成行程了
          </h2>
          <p className="text-lg font-bold bg-gradient-to-r from-warm-200 to-warm-300 bg-clip-text text-transparent mb-6">
            我们比AI好10倍
          </p>

          <div className="space-y-2 text-xs text-white/60 leading-relaxed">
            <p>❌ AI不知道餐厅倒闭了</p>
            <p>❌ AI不知道最佳拍照角度</p>
            <p>❌ AI不知道当地人去哪</p>
            <p className="text-warm-200 font-semibold mt-3">
              ✅ 我们住在日本，亲自走过
            </p>
          </div>
        </div>

        {/* Bottom tech badges */}
        <div className="relative z-10 p-4 space-y-2">
          {[
            { icon: "🧠", text: "12维智能评分 · 三平台融合" },
            { icon: "📊", text: "240+景点 · 4大数据源" },
            { icon: "🇯🇵", text: "旅居日本 · 人工验证" },
            { icon: "📸", text: "出片保证 · 小众机位" },
          ].map((b) => (
            <div
              key={b.text}
              className="bg-white/[0.06] rounded-lg px-3 py-2 flex items-center gap-2"
            >
              <span className="text-sm">{b.icon}</span>
              <span className="text-[10px] text-white/70">{b.text}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Center: Advantage Grid */}
      <div className="flex-1 flex flex-col p-4 overflow-hidden pb-20 lg:pb-4">
        <h2 className="text-lg font-bold text-stone-900 mb-3 shrink-0">
          🏆 为什么选我们 · <span className="text-warm-400">12项真实优势</span>
        </h2>
        <AdvantageGrid />
      </div>

      {/* Right: Process + CTA（桌面端） */}
      <div className="hidden lg:flex w-[230px] shrink-0 flex-col p-4 gap-4 justify-center border-l border-stone-100">
        <ProcessSteps />
        <WeChatCTA />
      </div>

      {/* 手机端固定底部操作区（< lg，client component） */}
      <MobileBottomCTA />
    </div>
  );
}
