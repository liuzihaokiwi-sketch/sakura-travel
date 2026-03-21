"use client";

import { motion } from "framer-motion";
import { fadeInUp, staggerContainerSlow } from "@/lib/animations";
import { ADVANTAGES } from "@/lib/constants";

const BG_IMAGES = [
  "/images/japan-street.jpg",   // 日本街道
  "/images/kyoto.jpg",          // 路线地图
  "/images/couple-travel.jpg",  // 情侣旅行
  "/images/fuji.jpg",           // 富士山
  "/images/sushi.jpg",          // 日本料理
  "/images/data-chart.jpg",     // 数据图表
  "/images/magazine.jpg",       // 杂志
  "/images/tech.jpg",           // 科技
  "/images/festival.jpg",       // 祭典
  "/images/japan-map.jpg",      // 日本地图
  "/images/tokyo.jpg",          // 东京
  "/images/camera.jpg",         // 相机
];

export function AdvantageGrid() {
  return (
    <motion.div
      variants={staggerContainerSlow}
      initial="initial"
      animate="animate"
      className="grid grid-cols-3 lg:grid-cols-4 gap-2.5 flex-1 auto-rows-fr"
    >
      {ADVANTAGES.map((adv, i) => (
        <motion.div
          key={adv.title}
          variants={fadeInUp}
          className="group relative bg-white rounded-xl border border-stone-100 overflow-hidden hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200 flex flex-col"
        >
          {/* Themed background */}
          <div
            className="absolute inset-0 bg-cover bg-center opacity-[0.12] group-hover:opacity-[0.22] transition-opacity duration-300"
            style={{
              backgroundImage: `url('${BG_IMAGES[i]}')`,
            }}
          />

          <div className="relative p-3 flex-1 flex flex-col">
            {/* Title */}
            <h4 className="text-sm font-extrabold text-stone-900 tracking-tight mb-1.5 flex items-center gap-1">
              <span>{adv.icon}</span> {adv.title}
            </h4>

            {/* Pain point */}
            <div className="bg-red-50 border-l-[3px] border-red-400 rounded-r px-2 py-1 mb-1.5">
              <p className="text-[10px] text-red-600 font-semibold">❌ {adv.pain}</p>
            </div>

            {/* Solution */}
            <p className="text-[11px] text-stone-500 leading-relaxed flex-1">
              ✅{" "}
              {adv.solution.split(adv.highlight).map((part, j, arr) => (
                <span key={j}>
                  {part}
                  {j < arr.length - 1 && (
                    <b className="text-warm-400">{adv.highlight}</b>
                  )}
                </span>
              ))}
            </p>
          </div>
        </motion.div>
      ))}
    </motion.div>
  );
}
