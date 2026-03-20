"use client";

import { motion } from "framer-motion";
import { fadeInUp, staggerContainer } from "@/lib/animations";
import { PROCESS_STEPS } from "@/lib/constants";

export function ProcessSteps() {
  return (
    <motion.div
      variants={staggerContainer}
      initial="initial"
      animate="animate"
      className="space-y-3"
    >
      <h3 className="text-base font-bold text-stone-900 mb-3">📋 怎么开始</h3>
      {PROCESS_STEPS.map((step) => (
        <motion.div
          key={step.num}
          variants={fadeInUp}
          className="flex items-start gap-3"
        >
          <div className="shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-warm-300 to-warm-400 flex items-center justify-center text-white text-sm font-bold shadow">
            {step.num}
          </div>
          <div>
            <p className="text-sm font-semibold text-stone-800">{step.title}</p>
            <p className="text-xs text-stone-400">{step.detail}</p>
          </div>
        </motion.div>
      ))}
    </motion.div>
  );
}
