"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// ── Animations ──────────────────────────────────────────────────────────────

const fadeUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.5 } },
};

const stagger = {
  animate: { transition: { staggerChildren: 0.1 } },
};

// ═════════════════════════════════════════════════════════════════════════════
// SECTION 1: Hero — 最核心的一句话
// ═════════════════════════════════════════════════════════════════════════════

const SELLING_CARDS: { text: React.ReactNode; img: string }[] = [
  {
    text: <><span className="text-amber-600 font-semibold">旅日博主精选</span>，有审美有深度，拒绝网红路线</>,
    img: "/images/japan-temple.jpg",
  },
  {
    text: <>精选<span className="text-amber-600 font-semibold">上千家</span>餐厅酒店，花最少的钱<span className="text-amber-600 font-semibold">吃最好的</span></>,
    img: "/images/japan-food.jpg",
  },
  {
    text: <><span className="text-pink-600 font-semibold">出片机位</span> + 最佳时间，省了请摄影师的钱</>,
    img: "/images/kyoto.jpg",
  },
  {
    text: <>天气不好也没关系，每个活动都有 <span className="text-sky-600 font-semibold">Plan B</span></>,
    img: "/images/japan-city.jpg",
  },
];

function Hero() {
  return (
    <section className="relative bg-gradient-to-b from-amber-50/50 via-white to-stone-50 px-5 pt-0 pb-6 md:pt-4 md:pb-10 overflow-hidden">
      {/* 装饰光斑 */}
      <div className="absolute -top-10 -left-10 w-72 h-72 bg-pink-300/30 rounded-full blur-[80px]" />
      <div className="absolute top-40 -right-16 w-80 h-80 bg-amber-300/25 rounded-full blur-[80px]" />
      <div className="absolute bottom-0 left-1/3 w-72 h-72 bg-sky-200/25 rounded-full blur-[80px]" />
      {/* 点阵装饰 */}
      <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: "radial-gradient(circle, #000 1px, transparent 1px)", backgroundSize: "24px 24px" }} />
      <motion.div
        className="max-w-3xl mx-auto w-full"
        initial="initial" animate="animate" variants={stagger}
      >
        {/* 标题区 */}
        <div className="text-center mb-3">
          <motion.div variants={fadeUp} className="flex justify-center gap-2 mb-1.5">
            {["东京", "京都", "大阪", "北海道", "冲绳"].map((c) => (
              <span key={c} className="text-[11px] bg-stone-100 text-stone-500 px-3 py-1 rounded-full">{c}</span>
            ))}
          </motion.div>

          <motion.div variants={fadeUp}>
            <h1 className="text-2xl md:text-4xl font-bold text-stone-800 leading-tight mb-1">
              一本翻开就能出发的
            </h1>
            <h1 className="text-2xl md:text-4xl font-black leading-tight">
              <span className="bg-gradient-to-r from-amber-500 via-orange-500 to-pink-500 bg-clip-text text-transparent">
                为你量身定制的日本旅行手册
              </span>
            </h1>
          </motion.div>

          <motion.p variants={fadeUp} className="text-sm md:text-base text-stone-500 leading-relaxed mt-2 max-w-md mx-auto">
            从路线到餐厅到交通，<span className="bg-gradient-to-r from-amber-500 to-pink-500 bg-clip-text text-transparent font-bold">40页+</span> 全部安排好
            <br />
            不绕路、有备选、精确到每一分钟
          </motion.p>
        </div>

        {/* 4 张卡片 — 有图片，遮罩浅 */}
        <motion.div className="grid grid-cols-2 gap-3 mt-4" variants={stagger}>
          {SELLING_CARDS.map((card, i) => (
            <motion.div
              key={i}
              variants={fadeUp}
              className="rounded-2xl overflow-hidden bg-white border border-stone-100/80 shadow-lg shadow-stone-300/40 group hover:-translate-y-1.5 hover:shadow-xl hover:shadow-stone-300/50 transition-all duration-300"
            >
              <div className="relative h-20 sm:h-28 overflow-hidden">
                <div
                  className="absolute inset-0 bg-cover bg-center transition-transform duration-500 group-hover:scale-105"
                  style={{ backgroundImage: `url('${card.img}')` }}
                />
              </div>
              <div className="px-3 py-2.5">
                <p className="text-[12px] md:text-[13px] text-stone-600 leading-relaxed">
                  {card.text}
                </p>
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* 底部信息 + CTA */}
        <motion.div variants={fadeUp} className="text-center mt-5 mb-2">
          <p className="text-xs text-stone-700 mb-3 font-bold">已为 <span className="text-amber-600">1,200+</span> 位旅行者定制行程</p>
          <Link href="/quiz" className="inline-block relative group">
            {/* 动态边框 */}
            <span className="absolute -inset-[3px] rounded-2xl bg-gradient-to-r from-amber-400 via-pink-400 to-amber-400 bg-[length:200%_100%] animate-[shimmer_2s_linear_infinite] opacity-80 group-hover:opacity-100 blur-[2px]" />
            <Button variant="warm" size="xl" className="relative min-w-[260px] text-base py-4 font-bold shadow-xl shadow-orange-300/50">
              免费看看你的行程 →
            </Button>
          </Link>
          <p className="text-sm text-stone-700 mt-3 font-bold">先免费体验一天完整行程，满意再付费定制全部</p>
        </motion.div>
      </motion.div>
    </section>
  );
}

// ═════════════════════════════════════════════════════════════════════════════
// SECTION 2: Pain → Solution — 痛点 + 优势整合
// ═════════════════════════════════════════════════════════════════════════════

const PAIN_SOLUTION_PAIRS = [
  {
    pain: { emoji: "😵‍💫", title: "攻略越看越乱", desc: "收藏 200 篇小红书，全是碎片拼不出完整路线" },
    solution: { icon: "🏠", title: "团队旅居日本", desc: "每条路线亲自走过，不是网上拼凑", accent: "from-amber-400 to-orange-400" },
  },
  {
    pain: { emoji: "⏰", title: "两周还没定下来", desc: "交通换乘 + 门票预约耗掉所有下班时间" },
    solution: { icon: "⚡", title: "24 小时交付", desc: "提交信息后次日收到完整攻略", accent: "from-sky-400 to-blue-500" },
  },
  {
    pain: { emoji: "😰", title: "怕踩坑又怕错过", desc: "不知道哪些值得去、哪些是游客陷阱" },
    solution: { icon: "📊", title: "6 大数据源融合", desc: "Tabelog · Booking · Google 多平台真实评分，AI 智能排序", accent: "from-emerald-400 to-teal-500" },
  },
  {
    pain: { emoji: "🤷", title: "同行人众口难调", desc: "逛街、温泉、带娃需求全不同" },
    solution: { icon: "🎯", title: "完全定制，不套模板", desc: "根据日期、人数、偏好单独制作，每份都不一样", accent: "from-pink-400 to-rose-500" },
  },
];

function PainAndSolution() {
  return (
    <section id="showcase" className="py-10 px-5 bg-gradient-to-b from-stone-50 to-amber-50/30 scroll-mt-14">
      <div className="max-w-4xl mx-auto">
        <motion.div variants={fadeUp} initial="initial" whileInView="animate" viewport={{ once: true }} className="text-center mb-12">
          <p className="text-xs font-mono tracking-widest text-stone-400 uppercase mb-3">Problem → Solution</p>
          <h2 className="text-2xl md:text-3xl font-black text-stone-900 leading-snug">
            你的焦虑，我们<span className="bg-gradient-to-r from-amber-500 to-pink-500 bg-clip-text text-transparent">逐一击破</span>
          </h2>
          <p className="text-sm text-stone-400 mt-2">1,200+ 位旅行者已验证的解法</p>
        </motion.div>

        <div className="space-y-4">
          {PAIN_SOLUTION_PAIRS.map((pair, i) => (
            <motion.div
              key={i}
              variants={fadeUp}
              initial="initial"
              whileInView="animate"
              viewport={{ once: true }}
              className="grid grid-cols-[1fr_auto_1fr] items-center gap-3 md:gap-5"
            >
              <div className="bg-white rounded-2xl p-4 md:p-5 border border-stone-100 shadow-sm h-full flex flex-col justify-center">
                <span className="text-xl md:text-2xl mb-2 block">{pair.pain.emoji}</span>
                <h3 className="font-bold text-stone-800 text-sm md:text-base mb-1">{pair.pain.title}</h3>
                <p className="text-[11px] md:text-xs text-stone-400 leading-relaxed">{pair.pain.desc}</p>
              </div>

              <div className="flex flex-col items-center gap-1">
                <div className={cn("w-8 h-8 md:w-9 md:h-9 rounded-full bg-gradient-to-br flex items-center justify-center shadow-lg", pair.solution.accent)}>
                  <span className="text-white text-sm font-bold">→</span>
                </div>
              </div>

              <div className={cn(
                "relative rounded-2xl p-4 md:p-5 h-full flex flex-col justify-center overflow-hidden",
                "bg-gradient-to-br border border-white/20 shadow-md",
                pair.solution.accent
              )}>
                <div className="absolute inset-0 bg-white/90" />
                <div className="relative">
                  <span className="text-xl md:text-2xl mb-2 block">{pair.solution.icon}</span>
                  <h3 className="font-bold text-stone-900 text-sm md:text-base mb-1">{pair.solution.title}</h3>
                  <p className="text-[11px] md:text-xs text-stone-500 leading-relaxed">{pair.solution.desc}</p>
                </div>
                <div className={cn("absolute top-0 right-0 w-16 h-16 rounded-bl-[3rem] opacity-10 bg-gradient-to-br", pair.solution.accent)} />
              </div>
            </motion.div>
          ))}
        </div>

        <motion.div
          variants={fadeUp} initial="initial" whileInView="animate" viewport={{ once: true }}
          className="mt-10 flex items-center justify-center gap-6 md:gap-10"
        >
          {[
            { num: "1,200+", label: "已服务旅行者" },
            { num: "4.9", label: "平均满意度" },
            { num: "24h", label: "极速交付" },
            { num: "6", label: "数据源融合" },
          ].map((stat) => (
            <div key={stat.label} className="text-center">
              <p className="text-lg md:text-xl font-black bg-gradient-to-r from-amber-500 to-pink-500 bg-clip-text text-transparent">
                {stat.num}
              </p>
              <p className="text-[10px] md:text-xs text-stone-400">{stat.label}</p>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

// ═════════════════════════════════════════════════════════════════════════════
// SECTION 3: Showcase — 攻略 8 大模块展示
// ═════════════════════════════════════════════════════════════════════════════

/* 内联 SVG 图标组件 */
const ModIcon = ({ d, color }: { d: string; color: string }) => (
  <svg className={cn("w-7 h-7 mb-2 transition-transform duration-300 group-hover:scale-110", color)} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d={d}/>
  </svg>
);

const GUIDE_MODULES: { iconD: string; iconColor: string; title: string; desc: string; highlight: string; color: string; highlightClass: string; descClass: string }[] = [
  {
    iconD: "M12 20h9M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z",
    iconColor: "text-amber-500",
    title: "设计方案",
    desc: "拒绝千篇一律的网红打卡，人工精选小众与经典的最佳组合",
    highlight: "每条路线都有「为什么这样排」",
    color: "bg-gradient-to-br from-amber-50 to-orange-50",
    highlightClass: "bg-gradient-to-r from-amber-600 to-orange-500 bg-clip-text text-transparent",
    descClass: "text-stone-500",
  },
  {
    iconD: "M12 22s-8-4.5-8-11.8A8 8 0 0 1 12 2a8 8 0 0 1 8 8.2c0 7.3-8 11.8-8 11.8z M12 13a3 3 0 1 0 0-6 3 3 0 0 0 0 6z",
    iconColor: "text-rose-500",
    title: "每日路线",
    desc: "数据优化路线顺序，省下宝贵的体力和时间，不绕路不暴走",
    highlight: "精确到每小时，拿到就能出发",
    color: "bg-white",
    highlightClass: "bg-gradient-to-r from-amber-600 to-pink-500 bg-clip-text text-transparent",
    descClass: "text-stone-500",
  },
  {
    iconD: "M18 8h1a4 4 0 0 1 0 8h-1M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z M6 1v3 M10 1v3 M14 1v3",
    iconColor: "text-orange-500",
    title: "餐厅推荐",
    desc: "从上千家餐厅中人工筛选，最合你口味、有独特体验的那几家",
    highlight: "评分 + 人均 + 预约手把手教",
    color: "bg-white",
    highlightClass: "text-amber-600",
    descClass: "text-stone-500",
  },
  {
    iconD: "M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z M9 22V12h6v10",
    iconColor: "text-sky-500",
    title: "酒店推荐",
    desc: "人工比价筛选，让你好好休息的同时带来独特体验",
    highlight: "位置 + 价格 + 特色，帮你选到最值",
    color: "bg-sky-50",
    highlightClass: "text-sky-600",
    descClass: "text-stone-500",
  },
  {
    iconD: "M1 3h15v13H1z M16 8h4l3 3v5h-7V8z M5.5 21a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z M18.5 21a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z",
    iconColor: "text-blue-500",
    title: "交通指南",
    desc: "站名 · 线路 · 几号口出，人工标注每一步怎么走",
    highlight: "手写级清楚，不用再查换乘案内",
    color: "bg-blue-50",
    highlightClass: "text-blue-600",
    descClass: "text-stone-500",
  },
  {
    iconD: "M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z",
    iconColor: "text-emerald-500",
    title: "Plan B 备选",
    desc: "拒绝旅行焦虑，天气不好、电车晚点也没关系，给你不输原方案的替代计划",
    highlight: "受影响的活动都有应急方案",
    color: "bg-emerald-50",
    highlightClass: "text-emerald-600",
    descClass: "text-stone-500",
  },
  {
    iconD: "M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z M12 17a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
    iconColor: "text-pink-500",
    title: "出片指南",
    desc: "最佳机位 + 最佳时间 + 构图建议，省了请摄影师的钱",
    highlight: "拍了就发朋友圈，缓解情侣出片危机",
    color: "bg-pink-50",
    highlightClass: "text-pink-600",
    descClass: "text-stone-500",
  },
  {
    iconD: "M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4 M16 17l5-5-5-5 M21 12H9",
    iconColor: "text-violet-500",
    title: "行前准备 + 安全须知",
    desc: "出发清单 · eSIM · 支付 · 交通卡 · 常用App · 医疗急救 · 预约总表",
    highlight: "靠谱保证，一份搞定不用到处找",
    color: "bg-violet-50",
    highlightClass: "text-violet-600",
    descClass: "text-stone-500",
  },
];

function Showcase() {
  return (
    <section className="py-10 px-6 bg-gradient-to-b from-amber-50/30 to-stone-50/50">
      <div className="max-w-5xl mx-auto">
        <motion.div variants={fadeUp} initial="initial" whileInView="animate" viewport={{ once: true }}
          className="text-center mb-10">
          <h2 className="text-xl md:text-2xl font-bold text-stone-900 mb-2">
            你将收到的攻略，长这样
          </h2>
          <p className="text-xs md:text-sm text-stone-500">30-40 页 · 不是流水账，是一本能直接照着走的旅行手册</p>
        </motion.div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
          {GUIDE_MODULES.map((m, i) => (
            <motion.div
              key={m.title}
              variants={fadeUp}
              initial="initial"
              whileInView="animate"
              viewport={{ once: true }}
              className={cn(
                "rounded-2xl p-4 md:p-5 border border-stone-100/80 shadow-sm min-h-[160px] md:min-h-[180px] flex flex-col justify-between",
                "hover:-translate-y-1 transition-transform duration-300 group",
                m.color,
              )}
            >
              <div>
                <ModIcon d={m.iconD} color={m.iconColor} />
                <h4 className="font-bold text-sm md:text-base mb-1.5 font-[family-name:var(--font-display)]">{m.title}</h4>
                <p className={cn("text-[11px] md:text-xs leading-relaxed mb-2", m.descClass)}>{m.desc}</p>
              </div>
              <p className={cn("text-[11px] md:text-xs font-extrabold leading-snug", m.highlightClass)}>
                {m.highlight}
              </p>
            </motion.div>
          ))}
        </div>

        <p className="text-[10px] text-stone-400 text-center mt-5">
          ↑ 完整攻略包含每天 4-5 页详细内容 + 满足条件时自动生成酒店页、出片页、交通专页等
        </p>
      </div>
    </section>
  );
}

// ═════════════════════════════════════════════════════════════════════════════
// SECTION 4: 对比表 + 价格
// ═════════════════════════════════════════════════════════════════════════════

/* 对勾 & 横线组件 */
const Check = () => (
  <svg className="w-4 h-4 mx-auto text-emerald-500" viewBox="0 0 20 20" fill="currentColor">
    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
  </svg>
);
const Dash = () => <span className="block text-center text-stone-300">—</span>;
const Num = ({ n }: { n: string }) => <span className="block text-center text-xs font-bold text-stone-700">{n}</span>;

const COMPARE_ROWS: { label: React.ReactNode; free: React.ReactNode; std: React.ReactNode; pre: React.ReactNode; accent?: boolean }[] = [
  { label: "每日路线",   free: <Check />, std: <Check />, pre: <Check /> },
  { label: "交通指南",   free: <Check />, std: <Check />, pre: <Check /> },
  { label: "餐厅推荐",   free: <Check />, std: <Check />, pre: <Check /> },
  { label: "出片指南",   free: <Dash />,  std: <Check />, pre: <Check /> },
  { label: "Plan B",     free: <Dash />,  std: <Check />, pre: <Check /> },
  { label: "行前须知",   free: <Dash />,  std: <Check />, pre: <Check /> },
  { label: "预算明细",   free: <Check />, std: <Check />, pre: <Check /> },
  { label: <span className="text-amber-600 font-bold">深度比价</span>, free: <Dash />, std: <Dash />, pre: <Check />, accent: true },
  { label: "自助微调",   free: <Dash />,  std: <Check />, pre: <Check /> },
  { label: "正式修改",   free: <Dash />,  std: <Num n="1次" />, pre: <Num n="3次" /> },
  { label: <span className="text-violet-600 font-bold">专属规划师</span>, free: <Dash />, std: <Dash />, pre: <Check />, accent: true },
  { label: <span className="text-violet-600 font-bold">实时答疑</span>,   free: <Dash />, std: <Dash />, pre: <Check />, accent: true },
  { label: "攻略页数",   free: <Num n="3-5" />, std: <Num n="30-40" />, pre: <Num n="40-50" /> },
];

function ComparisonTable() {
  return (
    <section className="py-10 px-4 md:px-6 bg-gradient-to-b from-stone-50/80 to-white">
      <div className="max-w-3xl mx-auto">
        <motion.div variants={fadeUp} initial="initial" whileInView="animate" viewport={{ once: true }}
          className="text-center mb-6">
          <h2 className="text-xl md:text-2xl font-bold text-stone-900 mb-1">
            从你关心的角度看区别
          </h2>
          <p className="text-xs md:text-sm text-stone-400">三个版本，总有一个适合你</p>
        </motion.div>

        <motion.div variants={fadeUp} initial="initial" whileInView="animate" viewport={{ once: true }}
          className="bg-white rounded-2xl border border-stone-100 shadow-sm overflow-hidden mt-4">
          <table className="w-full text-xs">
            {/* 表头：价格行 */}
            <thead>
              <tr className="border-b-2 border-stone-100">
                <th className="w-[34%]" />
                <th className="px-1 py-3 md:px-3 md:py-4 text-center w-[22%]">
                  <p className="text-stone-400 text-[10px] md:text-xs">体验版</p>
                  <p className="text-sm md:text-lg font-black text-stone-600 mt-0.5">免费</p>
                </th>
                <th className="px-1 py-3 md:px-3 md:py-4 text-center w-[22%] bg-amber-50/60 border-x-2 border-amber-100 relative">
                  <div className="absolute -top-2.5 left-1/2 -translate-x-1/2 bg-amber-500 text-white text-[7px] md:text-[10px] font-bold px-1.5 py-0.5 rounded-full whitespace-nowrap">
                    首发特惠
                  </div>
                  <p className="text-amber-600 text-[10px] md:text-xs font-medium">完整攻略</p>
                  <p className="text-stone-300 line-through text-[9px] md:text-xs">¥368</p>
                  <p className="text-base md:text-xl font-black bg-gradient-to-r from-amber-600 to-orange-500 bg-clip-text text-transparent">¥248</p>
                  <p className="text-[7px] md:text-[10px] text-stone-400">7天参考价</p>
                </th>
                <th className="px-1 py-3 md:px-3 md:py-4 text-center w-[22%]">
                  <p className="text-violet-500 text-[10px] md:text-xs font-medium">尊享版</p>
                  <p className="text-base md:text-xl font-black text-violet-600 mt-0.5">¥888</p>
                  <p className="text-[7px] md:text-[10px] text-stone-400">7天参考价</p>
                </th>
              </tr>
            </thead>
            {/* 内容行 */}
            <tbody>
              {COMPARE_ROWS.map((row, i) => (
                <tr key={i} className={cn(
                  "border-b border-stone-50",
                  i % 2 === 0 ? "bg-white" : "bg-stone-50/30",
                  row.accent && "bg-gradient-to-r from-amber-50/40 to-violet-50/40",
                )}>
                  <td className="px-3 py-2 md:px-4 md:py-2.5 text-[11px] md:text-sm font-medium text-stone-700">{row.label}</td>
                  <td className="px-1 py-2 md:px-3 md:py-2.5 text-center">{row.free}</td>
                  <td className="px-1 py-2 md:px-3 md:py-2.5 text-center bg-amber-50/20 border-x border-amber-50/60">{row.std}</td>
                  <td className="px-1 py-2 md:px-3 md:py-2.5 text-center">{row.pre}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </motion.div>

        <p className="text-center text-[10px] text-stone-400 mt-3">其他天数按行程复杂度小幅浮动，付款前确认最终价格</p>
      </div>
    </section>
  );
}

// ═════════════════════════════════════════════════════════════════════════════
// SECTION 5: FAQ — 首页精选 5 题
// ═════════════════════════════════════════════════════════════════════════════

const TOP_FAQS = [
  { q: "攻略是通用模板还是为我定制的", a: "每一份都是根据你的出行日期、天数、同行人、偏好单独制作的，不是套模板，每份都不一样。" },
  { q: "免费体验版有多少内容", a: "Day 1 完整可执行行程，包括路线、餐厅、交通和预算明细，跟付费版同样的细致程度。出片指南和 Plan B 会有演示样例供参考。" },
  { q: "不满意可以改吗", a: "可以！先通过网站自助微调（不限次数），仍不满意再使用正式修改权益（标准版 1 次 / 尊享版 3 次）。" },
  { q: "多久能收到攻略", a: "提交信息后 24 小时内收到，樱花季/红叶季等高峰期不超过 48 小时。" },
  { q: "攻略是什么格式", a: "网页版 + PDF 双格式。手机、iPad、电脑都能看，PDF 可离线保存。" },
];

function FAQ() {
  return (
    <section className="py-10 px-6 bg-gradient-to-b from-white to-stone-50">
      <div className="max-w-2xl mx-auto">
        <motion.div variants={fadeUp} initial="initial" whileInView="animate" viewport={{ once: true }}
          className="text-center mb-6">
          <h2 className="text-lg md:text-xl font-bold text-stone-900">常见问题</h2>
        </motion.div>

        <div className="space-y-1.5">
          {TOP_FAQS.map((f) => (
            <details key={f.q} className="group bg-white rounded-xl border border-stone-100 overflow-hidden">
              <summary className="flex items-center justify-between p-4 cursor-pointer text-sm font-medium text-stone-900 list-none">
                {f.q}
                <span className="ml-2 text-stone-400 group-open:rotate-180 transition-transform text-xs">▾</span>
              </summary>
              <div className="px-4 pb-4 text-sm text-stone-500 leading-relaxed">{f.a}</div>
            </details>
          ))}
        </div>

        <div className="text-center mt-5">
          <Link href="/faq" className="text-sm text-amber-600 hover:text-amber-700 font-medium transition-colors">
            查看全部常见问题 →
          </Link>
        </div>
      </div>
    </section>
  );
}

// ═════════════════════════════════════════════════════════════════════════════
// SECTION 6: Final CTA（保持不变）
// ═════════════════════════════════════════════════════════════════════════════

function FinalCTA() {
  return (
    <section className="py-10 px-6 bg-gradient-to-b from-stone-50/50 to-stone-50/80">
      <div className="max-w-2xl mx-auto text-center">
        <motion.div variants={fadeUp} initial="initial" whileInView="animate" viewport={{ once: true }}>
          <p className="text-sm text-stone-500 mb-5">不确定的话，先免费定制一天，觉得好再决定</p>

          <div className="relative inline-block group">
            <div className="absolute -inset-1 bg-gradient-to-r from-amber-400 via-pink-400 to-amber-400 rounded-2xl blur-md opacity-40 group-hover:opacity-60 transition-opacity animate-pulse" />
          <Link href="/quiz">
            <motion.div
              className="relative inline-block"
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
            >
              {/* 光晕 */}
              <motion.div
                className="absolute -inset-4 rounded-full bg-gradient-to-r from-amber-400/70 via-orange-400/60 to-pink-400/70 blur-2xl"
                animate={{ opacity: [0.3, 1, 0.3], scale: [0.9, 1.1, 0.9] }}
                transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
              />
              <motion.div
                className="absolute -inset-3 rounded-full bg-amber-300/40 blur-lg"
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut" }}
              />
              <Button variant="warm" size="xl" className="relative min-w-[260px] text-base py-4 font-bold shadow-lg shadow-orange-200/40">
                免费看看你的行程 →
              </Button>
            </motion.div>
          </Link>
          </div>

          <div className="flex justify-center gap-3 mt-5 text-[10px] text-stone-400">
            <span>⏱️ 24h 交付</span>
            <span>·</span>
            <span>🔄 不满意可改</span>
            <span>·</span>
            <span>🌸 已服务 1,200+</span>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

// ═════════════════════════════════════════════════════════════════════════════
// PAGE
// ═════════════════════════════════════════════════════════════════════════════

export default function WhyPage() {
  return (
    <div className="flex flex-col">
      <Hero />
    </div>
  );
}