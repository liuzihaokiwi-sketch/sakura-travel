"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { fadeInUp, staggerContainer } from "@/lib/animations";

export function HeroSection() {
  return (
    <section
      className="relative flex items-center justify-center overflow-hidden"
      style={{ height: "60vh" }}
    >
      {/* Background */}
      <div
        className="absolute inset-0 bg-cover bg-center"
        style={{
          backgroundImage:
            "url('/images/hero-sakura.jpg')",
        }}
      />
      <div className="absolute inset-0 bg-gradient-to-b from-black/65 via-black/45 to-black/75" />

      {/* Content */}
      <motion.div
        className="relative z-10 text-center px-6 max-w-3xl"
        variants={staggerContainer}
        initial="initial"
        animate="animate"
      >
        <motion.p
          variants={fadeInUp}
          className="text-sm tracking-[0.3em] text-white/60 mb-4 font-mono"
        >
          4 DATA SOURCES · 240+ SPOTS · DAILY 3× UPDATE
        </motion.p>

        <motion.h1
          variants={fadeInUp}
          className="font-display text-5xl md:text-6xl font-bold text-white leading-tight mb-3"
        >
          全日本樱花
          <br />
          <span className="bg-gradient-to-r from-warm-200 via-warm-300 to-sakura-300 bg-clip-text text-transparent">
            多源数据融合
          </span>
        </motion.h1>

        <motion.p
          variants={fadeInUp}
          className="text-base text-white/70 mb-8 max-w-lg mx-auto leading-relaxed"
        >
          不是搬运某个网站，而是 JMA · JMC · Weathernews · 地方官方
          <br />4 大权威源智能融合，精准追樱不踩坑
        </motion.p>

        <motion.div variants={fadeInUp}>
          <Link href="/custom">
            <Button variant="warm" size="xl" className="shadow-xl shadow-warm-300/30">
              🎁 免费定制攻略 →
            </Button>
          </Link>
        </motion.div>
      </motion.div>
    </section>
  );
}
