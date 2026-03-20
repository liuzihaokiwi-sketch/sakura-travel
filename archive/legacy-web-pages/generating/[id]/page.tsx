"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";

const STEPS = [
  { label: "了解你的偏好", icon: "🎯", duration: 2000 },
  { label: "匹配最合适的路线", icon: "🗺️", duration: 3000 },
  { label: "挑选景点和节奏", icon: "⛩️", duration: 3000 },
  { label: "选餐厅、排交通", icon: "🍣", duration: 2500 },
  { label: "多源信息校验", icon: "📊", duration: 2000 },
  { label: "最终检查", icon: "✅", duration: 1500 },
];

export default function GeneratingPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(0);
  const totalDuration = STEPS.reduce((a, s) => a + s.duration, 0);

  useEffect(() => {
    let elapsed = 0;
    const timers: NodeJS.Timeout[] = [];

    STEPS.forEach((step, i) => {
      const t = setTimeout(() => setCurrentStep(i), elapsed);
      timers.push(t);
      elapsed += step.duration;
    });

    // Navigate to plan page when done
    const final = setTimeout(() => {
      router.push(`/plan/${params.id}`);
    }, elapsed + 500);
    timers.push(final);

    return () => timers.forEach(clearTimeout);
  }, [params.id, router]);

  const progress = Math.min(((currentStep + 1) / STEPS.length) * 100, 100);

  return (
    <div className="min-h-[calc(100vh-3.5rem)] flex items-center justify-center bg-warm-50 px-6">
      <div className="w-full max-w-md text-center">
        {/* Animated icon */}
        <motion.div
          key={currentStep}
          initial={{ scale: 0.5, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="text-6xl mb-6"
        >
          {STEPS[currentStep].icon}
        </motion.div>

        <h2 className="font-display text-2xl font-bold text-stone-900 mb-2">
          正在为你规划行程
        </h2>

        <motion.p
          key={`label-${currentStep}`}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-warm-400 font-medium mb-8"
        >
          {STEPS[currentStep].label}...
        </motion.p>

        {/* Progress bar */}
        <div className="w-full h-2 bg-stone-100 rounded-full overflow-hidden mb-4">
          <motion.div
            className="h-full bg-gradient-to-r from-warm-300 to-sakura-400 rounded-full"
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>

        {/* Steps list */}
        <div className="space-y-2 mt-8">
          {STEPS.map((step, i) => (
            <div
              key={step.label}
              className={`flex items-center gap-3 text-sm transition-all duration-300 ${
                i < currentStep
                  ? "text-stone-400"
                  : i === currentStep
                  ? "text-stone-800 font-medium"
                  : "text-stone-300"
              }`}
            >
              <span className="w-5 text-center">
                {i < currentStep ? "✓" : i === currentStep ? "●" : "○"}
              </span>
              <span>{step.label}</span>
            </div>
          ))}
        </div>

        <p className="text-xs text-stone-400 mt-8">
          预计 {Math.ceil(totalDuration / 1000)} 秒 · 正在做专业校验，不是简单拼接
        </p>
      </div>
    </div>
  );
}
