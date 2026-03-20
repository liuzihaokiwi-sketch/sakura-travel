"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// ── Question data ───────────────────────────────────────────────────────────

const QUESTIONS = [
  {
    id: "destination",
    title: "你想去哪里？",
    subtitle: "选一个目的地（之后还可以调整）",
    type: "single" as const,
    options: [
      { value: "tokyo", label: "东京", icon: "🗼" },
      { value: "osaka-kyoto", label: "大阪+京都", icon: "⛩️" },
      { value: "tokyo-osaka-kyoto", label: "东京+大阪+京都", icon: "🗾" },
      { value: "hokkaido", label: "北海道", icon: "❄️" },
      { value: "okinawa", label: "冲绳", icon: "🏖️" },
      { value: "other", label: "其他", icon: "�" },
    ],
  },
  {
    id: "duration",
    title: "打算玩几天？",
    subtitle: "包含到达和离开当天",
    type: "single" as const,
    options: [
      { value: "3", label: "3天", icon: "3️⃣" },
      { value: "4", label: "4天", icon: "4️⃣" },
      { value: "5", label: "5天", icon: "5️⃣" },
      { value: "6", label: "6天", icon: "6️⃣" },
      { value: "7", label: "7天", icon: "7️⃣" },
      { value: "8", label: "8天+", icon: "�" },
    ],
  },
  {
    id: "party",
    title: "和谁一起去？",
    subtitle: "不同的同行人，行程安排完全不同",
    type: "single" as const,
    options: [
      { value: "solo", label: "自己一个人", icon: "🧑" },
      { value: "couple", label: "情侣/夫妻", icon: "💑" },
      { value: "family", label: "带孩子", icon: "👨‍👩‍👧" },
      { value: "parents", label: "带父母", icon: "👴" },
      { value: "friends", label: "朋友闺蜜", icon: "�" },
    ],
  },
  {
    id: "style",
    title: "你更偏向哪种旅行风格？",
    subtitle: "可以多选，最多 3 个（不选也没关系）",
    type: "multi" as const,
    maxSelect: 3,
    optional: true,
    options: [
      { value: "culture", label: "文化古迹", icon: "⛩️" },
      { value: "food", label: "美食探店", icon: "�" },
      { value: "photo", label: "拍照出片", icon: "�" },
      { value: "shopping", label: "购物买买买", icon: "🛍️" },
      { value: "nature", label: "自然风景", icon: "�" },
      { value: "relax", label: "慢节奏放松", icon: "🧘" },
      { value: "kids", label: "亲子乐园", icon: "🎢" },
    ],
  },
  {
    id: "wechat",
    title: "方案做好后发给你",
    subtitle: "我们会通过微信把行程发给你，通常 2 小时内",
    type: "input" as const,
    placeholder: "你的微信号",
    privacyNote: "仅用于发送方案，不会群发广告",
    options: [],
  },
];

// ── API config ──────────────────────────────────────────────────────────────

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Component ───────────────────────────────────────────────────────────────

export default function QuizPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string | string[]>>({});
  const [wechatId, setWechatId] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const q = QUESTIONS[step];
  const total = QUESTIONS.length;
  const progress = ((step + 1) / total) * 100;

  const currentAnswer = answers[q.id];

  function handleSelect(value: string) {
    if (q.type === "single") {
      setAnswers({ ...answers, [q.id]: value });
      // Auto advance after short delay
      setTimeout(() => {
        if (step < total - 1) setStep(step + 1);
      }, 300);
    } else if (q.type === "multi") {
      // Multi select
      const current = (currentAnswer as string[]) || [];
      const maxSel = (q as any).maxSelect || 99;
      if (current.includes(value)) {
        setAnswers({ ...answers, [q.id]: current.filter((v) => v !== value) });
      } else if (current.length < maxSel) {
        setAnswers({ ...answers, [q.id]: [...current, value] });
      }
    }
  }

  function isSelected(value: string) {
    if (q.type === "single") return currentAnswer === value;
    return ((currentAnswer as string[]) || []).includes(value);
  }

  function canProceed() {
    if (q.type === "input") return wechatId.trim().length > 0;
    if (q.type === "single") return !!currentAnswer;
    if ((q as any).optional) return true;  // style step is optional
    return ((currentAnswer as string[]) || []).length > 0;
  }

  async function handleSubmit() {
    setIsSubmitting(true);
    setError("");

    const payload = {
      destination: answers.destination as string,
      duration_days: parseInt(answers.duration as string) || 7,
      party_type: answers.party as string,
      styles: (answers.style as string[]) || [],
      wechat_id: wechatId.trim(),
      travel_time: null,
    };

    try {
      const res = await fetch(`${API_BASE}/quiz`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `提交失败 (${res.status})`);
      }

      const data = await res.json();
      // 跳转到提交成功页，带上 trip_request_id
      router.push(`/submitted?id=${data.trip_request_id}`);
    } catch (e: any) {
      setError(e.message || "网络异常，请稍后重试");
      setIsSubmitting(false);
    }
  }

  const isLast = step === total - 1;

  return (
    <div className="min-h-[calc(100vh-3.5rem)] flex flex-col bg-warm-50">
      {/* Progress bar */}
      <div className="h-1 bg-stone-100">
        <motion.div
          className="h-full bg-gradient-to-r from-warm-300 to-sakura-400"
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.3 }}
        />
      </div>

      {/* Step indicator */}
      <div className="text-center pt-6 pb-2">
        <span className="text-xs font-mono text-stone-400">{step + 1} / {total}</span>
      </div>

      {/* Question area */}
      <div className="flex-1 flex items-center justify-center px-6">
        <AnimatePresence mode="wait">
          <motion.div
            key={q.id}
            initial={{ opacity: 0, x: 40 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -40 }}
            transition={{ duration: 0.3 }}
            className="w-full max-w-lg"
          >
            {/* Title */}
            <h2 className="font-display text-2xl md:text-3xl font-bold text-stone-900 text-center mb-2">
              {q.title}
            </h2>
            <p className="text-sm text-stone-400 text-center mb-8">{q.subtitle}</p>

            {/* Input type (Step 5: WeChat ID) */}
            {q.type === "input" && (
              <div className="space-y-4">
                <input
                  type="text"
                  value={wechatId}
                  onChange={(e) => setWechatId(e.target.value)}
                  placeholder={(q as any).placeholder}
                  className="w-full px-4 py-4 rounded-2xl border-2 border-stone-200 bg-white text-center text-lg focus:border-warm-300 focus:outline-none transition-colors"
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && canProceed()) handleSubmit();
                  }}
                />
                {(q as any).privacyNote && (
                  <p className="text-xs text-stone-400 text-center">
                    🔒 {(q as any).privacyNote}
                  </p>
                )}
              </div>
            )}

            {/* Options grid (single & multi select) */}
            {(q.type === "single" || q.type === "multi") && (
              <div className={cn(
                "grid gap-3",
                q.options.length <= 4 ? "grid-cols-2" : "grid-cols-3"
              )}>
                {q.options.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => handleSelect(opt.value)}
                    className={cn(
                      "flex flex-col items-center gap-2 p-5 rounded-2xl border-2 transition-all duration-200",
                      isSelected(opt.value)
                        ? "border-warm-300 bg-warm-50 shadow-md shadow-warm-200/30 scale-[1.02]"
                        : "border-stone-100 bg-white hover:border-stone-200 hover:shadow-sm"
                    )}
                  >
                    <span className="text-3xl">{opt.icon}</span>
                    <span className={cn(
                      "text-sm font-medium",
                      isSelected(opt.value) ? "text-warm-500" : "text-stone-600"
                    )}>
                      {opt.label}
                    </span>
                  </button>
                ))}
              </div>
            )}

            {/* Error message */}
            {error && (
              <p className="mt-4 text-sm text-red-500 text-center">{error}</p>
            )}

            {/* Multi-select / input: next or submit button */}
            {(q.type === "multi" || q.type === "input") && (
              <div className="mt-8 flex justify-center">
                {isLast ? (
                  <Button
                    variant="warm"
                    size="xl"
                    onClick={handleSubmit}
                    disabled={!canProceed() || isSubmitting}
                    className="min-w-[280px]"
                  >
                    {isSubmitting ? "正在提交..." : "提交，等规划师联系我 →"}
                  </Button>
                ) : (
                  <Button
                    variant="warm"
                    size="lg"
                    onClick={() => setStep(step + 1)}
                    disabled={!canProceed()}
                  >
                    {(q as any).optional && !((currentAnswer as string[]) || []).length
                      ? "跳过 →"
                      : "下一步 →"
                    }
                  </Button>
                )}
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Back button */}
      {step > 0 && (
        <div className="pb-6 text-center">
          <button
            onClick={() => setStep(step - 1)}
            className="text-sm text-stone-400 hover:text-stone-600 transition-colors"
          >
            ← 上一步
          </button>
        </div>
      )}
    </div>
  );
}