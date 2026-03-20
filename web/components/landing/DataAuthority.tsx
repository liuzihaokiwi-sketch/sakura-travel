"use client";

import { motion } from "framer-motion";
import { fadeInUp, staggerContainer } from "@/lib/animations";
import { STATS } from "@/lib/constants";

const stats = Object.values(STATS);

export function DataAuthority() {
  return (
    <section className="flex-1 flex items-center bg-white/60 backdrop-blur-sm">
      <motion.div
        className="mx-auto max-w-6xl w-full px-6 grid grid-cols-4 lg:grid-cols-7 gap-3"
        variants={staggerContainer}
        initial="initial"
        whileInView="animate"
        viewport={{ once: true }}
      >
        {stats.map((s) => (
          <motion.div
            key={s.label}
            variants={fadeInUp}
            className="group bg-white rounded-xl border border-stone-100 p-4 text-center hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200 cursor-default"
          >
            <p className="font-mono text-2xl lg:text-3xl font-black text-stone-900 group-hover:text-warm-400 transition-colors">
              {s.value}
            </p>
            <p className="text-xs font-semibold text-stone-600 mt-1">{s.label}</p>
            <p className="text-[10px] text-stone-400 mt-0.5 hidden lg:block">{s.detail}</p>
          </motion.div>
        ))}
      </motion.div>
    </section>
  );
}
