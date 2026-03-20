"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const STEPS = [
  {
    id: "budget",
    title: "预算大概多少？",
    subtitle: "每人的大致预算，帮我们匹配合适的方案",
    type: "slider" as const,
    min: 3000,
    max: 30000,
    step: 1000,
    default: 10000,
    format: (v: number) => `¥${(v / 1000).toFixed(0)}k`,
  },
  {
    id: "hotel",
    title: "住宿偏好？",
    subtitle: "帮我们选对住的区域和价位",
    type: "single" as const,
    options: [
      { value: "budget", label: "经济实惠", icon: "🏠", desc: "干净方便就行" },
      { value: "comfort", label: "舒适型", icon: "🏨", desc: "位置好、评价高" },
      { value: "luxury", label: "高端享受", icon: "🏯", desc: "体验感优先" },
      { value: "unsure", label: "不确定", icon: "🤷", desc: "帮我推荐" },
    ],
  },
  {
    id: "diet",
    title: "有忌口或偏好吗？",
    subtitle: "我们会在餐厅推荐里避开",
    type: "multi" as const,
    options: [
      { value: "seafood", label: "不吃海鲜", icon: "🦐" },
      { value: "raw", label: "不吃生食", icon: "🍣" },
      { value: "vegetarian", label: "素食", icon: "🥬" },
      { value: "halal", label: "清真", icon: "🌙" },
      { value: "none", label: "什么都吃", icon: "😋" },
    ],
  },
  {
    id: "notes",
    title: "还有什么特别想要的？",
    subtitle: "不填也完全没问题",
    type: "text" as const,
    placeholder: "比如想看夜樱、想买药妆、想带老人泡温泉、想去动漫圣地巡礼…",
    maxLength: 100,
  },
];

export default function QuestionnairePage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, any>>({ budget: 10000 });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const q = STEPS[step];
  const total = STEPS.length;
  const progress = ((step + 1) / total) * 100;

  function handleSingleSelect(value: string) {
    setAnswers({ ...answers, [q.id]: value });
    setTimeout(() => { if (step < total - 1) setStep(step + 1); }, 300);
  }

  function handleMultiSelect(value: string) {
    const current = (answers[q.id] as string[]) || [];
    if (value === "none") {
      setAnswers({ ...answers, [q.id]: ["none"] });
    } else {
      const filtered = current.filter((v) => v !== "none");
      if (filtered.includes(value)) {
        setAnswers({ ...answers, [q.id]: filtered.filter((v) => v !== value) });
      } else {
        setAnswers({ ...answers, [q.id]: [...filtered, value] });
      }
    }
  }

  function isSelected(value: string) {
    const a = answers[q.id];
    if (Array.isArray(a)) return a.includes(value);
    return a === value;
  }

  async function handleSubmit() {
    setIsSubmitting(true);
    // TODO: POST to /api/questionnaire
    setTimeout(() => router.push(`/generating/${params.id}`), 800);
  }

  const isLast = step === total - 1;

  return (
    <div className="min-h-[calc(100vh-3.5rem)] flex flex-col bg-warm-50">
      {/* Progress */}
      <div className="h-1 bg-stone-100">
        <motion.div className="h-full bg-gradient-to-r from-warm-300 to-sakura-400" animate={{ width: `${progress}%` }} transition={{ duration: 0.3 }} />
      </div>
      <div className="text-center pt-6 pb-2">
        <span className="text-xs font-mono text-stone-400">深度定制 {step + 1} / {total}</span>
      </div>

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
            <h2 className="font-display text-2xl md:text-3xl font-bold text-stone-900 text-center mb-2">{q.title}</h2>
            <p className="text-sm text-stone-400 text-center mb-8">{q.subtitle}</p>

            {/* Slider */}
            {q.type === "slider" && (
              <div className="space-y-6">
                <div className="text-center">
                  <span className="font-mono text-4xl font-black text-warm-400">
                    ¥{(answers.budget || q.default).toLocaleString()}
                  </span>
                  <span className="text-stone-400 text-sm ml-1">/人</span>
                </div>
                <input
                  type="range"
                  min={q.min}
                  max={q.max}
                  step={q.step}
                  value={answers.budget || q.default}
                  onChange={(e) => setAnswers({ ...answers, budget: parseInt(e.target.value) })}
                  className="w-full h-2 bg-stone-200 rounded-full appearance-none cursor-pointer accent-warm-300"
                />
                <div className="flex justify-between text-xs text-stone-400">
                  <span>¥3,000</span>
                  <span>¥30,000</span>
                </div>
                <div className="flex justify-center mt-4">
                  <Button variant="warm" size="lg" onClick={() => setStep(step + 1)}>下一步 →</Button>
                </div>
              </div>
            )}

            {/* Single select */}
            {q.type === "single" && (
              <div className="grid grid-cols-2 gap-3">
                {q.options!.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => handleSingleSelect(opt.value)}
                    className={cn(
                      "flex flex-col items-center gap-2 p-5 rounded-2xl border-2 transition-all duration-200",
                      isSelected(opt.value) ? "border-warm-300 bg-warm-50 shadow-md" : "border-stone-100 bg-white hover:border-stone-200"
                    )}
                  >
                    <span className="text-3xl">{opt.icon}</span>
                    <span className={cn("text-sm font-medium", isSelected(opt.value) ? "text-warm-500" : "text-stone-600")}>{opt.label}</span>
                    {"desc" in opt && <span className="text-[10px] text-stone-400">{(opt as any).desc}</span>}
                  </button>
                ))}
              </div>
            )}

            {/* Multi select */}
            {q.type === "multi" && (
              <>
                <div className="grid grid-cols-3 gap-3">
                  {q.options!.map((opt) => (
                    <button
                      key={opt.value}
                      onClick={() => handleMultiSelect(opt.value)}
                      className={cn(
                        "flex flex-col items-center gap-2 p-4 rounded-2xl border-2 transition-all duration-200",
                        isSelected(opt.value) ? "border-warm-300 bg-warm-50 shadow-md" : "border-stone-100 bg-white hover:border-stone-200"
                      )}
                    >
                      <span className="text-2xl">{opt.icon}</span>
                      <span className={cn("text-xs font-medium", isSelected(opt.value) ? "text-warm-500" : "text-stone-600")}>{opt.label}</span>
                    </button>
                  ))}
                </div>
                <div className="mt-6 flex justify-center">
                  <Button variant="warm" size="lg" onClick={() => setStep(step + 1)} disabled={!answers[q.id]?.length}>下一步 →</Button>
                </div>
              </>
            )}

            {/* Text input */}
            {q.type === "text" && (
              <div className="space-y-4">
                <textarea
                  value={answers.notes || ""}
                  onChange={(e) => setAnswers({ ...answers, notes: e.target.value.slice(0, q.maxLength!) })}
                  placeholder={q.placeholder}
                  rows={4}
                  className="w-full bg-white border border-stone-200 rounded-xl p-4 text-sm text-stone-700 placeholder:text-stone-300 focus:outline-none focus:ring-2 focus:ring-warm-300 resize-none"
                />
                <p className="text-xs text-stone-400 text-right">{(answers.notes || "").length}/{q.maxLength}</p>
                <div className="flex justify-center">
                  <Button variant="warm" size="xl" onClick={handleSubmit} disabled={isSubmitting} className="min-w-[240px]">
                    {isSubmitting ? "正在提交..." : "开始规划我的行程 →"}
                  </Button>
                </div>
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>

      {step > 0 && (
        <div className="pb-6 text-center">
          <button onClick={() => setStep(step - 1)} className="text-sm text-stone-400 hover:text-stone-600 transition-colors">← 上一步</button>
        </div>
      )}
    </div>
  );
}
