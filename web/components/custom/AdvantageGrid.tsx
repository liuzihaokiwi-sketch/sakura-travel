"use client";

import { motion } from "framer-motion";
import { fadeInUp, staggerContainerSlow } from "@/lib/animations";
import { ADVANTAGES } from "@/lib/constants";

const BG_IMAGES = [
  "photo-1528360983277-13d401cdc186", // 日本街道
  "photo-1493976040374-85c8e12f0c0e", // 路线地图
  "photo-1529655683826-aba9b3e77383", // 情侣旅行
  "photo-1490806843957-31f4c9a91c65", // 富士山
  "photo-1535090467336-9501f96eef89", // 日本料理
  "photo-1551218808-94e220e084d2", // 数据图表
  "photo-1544716278-ca5e3f4abd8c", // 杂志
  "photo-1558618666-fcd25c85f82e", // 科技
  "photo-1492571350019-22de08371fd3", // 祭典
  "photo-1524413840807-0c3cb6fa808d", // 日本地图
  "photo-1540959733332-eab4deabeeaf", // 东京
  "photo-1493780474015-ba834fd0ce2f", // 相机
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
              backgroundImage: `url('https://images.unsplash.com/${BG_IMAGES[i]}?w=400&q=40')`,
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
