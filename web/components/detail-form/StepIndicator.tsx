"use client";
import { CheckIcon } from "@heroicons/react/24/solid";

const STEPS = [
  { n: 1, label: "目的地" },
  { n: 2, label: "同行人" },
  { n: 3, label: "预算" },
  { n: 4, label: "兴趣" },
  { n: 5, label: "节奏" },
  { n: 6, label: "交通" },
];

export default function StepIndicator({
  currentStep,
  onStepClick,
  completedSteps,
}: {
  currentStep: number;
  onStepClick?: (n: number) => void;
  completedSteps: Set<number>;
}) {
  return (
    <div className="w-full px-4 py-3 bg-white border-b border-gray-100 sticky top-0 z-10">
      <div className="flex items-center justify-between max-w-md mx-auto">
        {STEPS.map((step, idx) => {
          const done = completedSteps.has(step.n);
          const active = currentStep === step.n;
          const accessible = done || step.n <= currentStep;
          return (
            <div key={step.n} className="flex items-center flex-1">
              <button
                onClick={() => accessible && onStepClick?.(step.n)}
                disabled={!accessible}
                className="flex flex-col items-center gap-0.5 group"
              >
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-all
                    ${done ? "bg-emerald-500 text-white" : ""}
                    ${active && !done ? "bg-indigo-600 text-white ring-2 ring-indigo-300" : ""}
                    ${!active && !done ? "bg-gray-100 text-gray-400" : ""}
                  `}
                >
                  {done ? <CheckIcon className="w-4 h-4" /> : step.n}
                </div>
                <span
                  className={`text-[10px] leading-none font-medium transition-colors
                    ${active ? "text-indigo-600" : done ? "text-emerald-600" : "text-gray-400"}
                  `}
                >
                  {step.label}
                </span>
              </button>
              {idx < STEPS.length - 1 && (
                <div
                  className={`flex-1 h-0.5 mx-1 rounded transition-colors
                    ${completedSteps.has(step.n) ? "bg-emerald-400" : "bg-gray-200"}
                  `}
                />
              )}
            </div>
          );
        })}
      </div>
      {/* 进度文字 */}
      <p className="text-center text-xs text-gray-400 mt-1.5">
        第 {currentStep} 步，共 6 步
      </p>
    </div>
  );
}
