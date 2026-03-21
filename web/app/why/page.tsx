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

const SELLING_CARDS = [
  {
    text: "旅日博主精选，有审美有深度，不是千篇一律的网红路线",
    img: "https://images.unsplash.com/photo-1545569341-9eb8b30979d9?w=400&q=60",
  },
  {
    text: "根据你的喜好量身定制",
    img: "https://images.unsplash.com/photo-1528360983277-13d401cdc186?w=400&q=60",
  },
  {
    text: "研究上千家餐厅酒店，最少的钱最好的体验",
    img: "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=400&q=60",
  },
  {
    text: "深度规划路线搭配，不花冤枉钱，不审美疲劳",
    img: "https://images.unsplash.com/photo-1624253321171-1be53e12f5f4?w=400&q=60",
  },
  {
    text: "周边好店、出片机位、伴手礼全标注，更有审美也更容易出片",
    img: "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=400&q=60",
  },
  {
    text: "每天都有 Plan B，出门更安心",
    img: "https://images.unsplash.com/photo-1480796927426-f609979314bd?w=400&q=60",
  },
];

function Hero() {
  return (
    <section className="relative overflow-hidden">
      {/* Background */}
      <div
        className="absolute inset-0 bg-cover bg-center"
        style={{ backgroundImage: "url('https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=1920&q=80')" }}
      />
      <div className="absolute inset-0 bg-gradient-to-b from-black/65 via-black/50 to-black/75" />

      <motion.div
        className="relative z-10 max-w-4xl mx-auto px-5 pt-20 pb-14 md:pt-28 md:pb-20"
        initial="initial" animate="animate" variants={stagger}
      >
        {/* 城市标签 */}
        <motion.div variants={fadeUp} className="flex justify-center gap-2 mb-6">
          {["东京", "京都", "大阪", "北海道", "冲绳"].map((c) => (
            <span key={c} className="text-[10px] bg-white/10 text-white/50 px-2.5 py-1 rounded-full">{c}</span>
          ))}
        </motion.div>

        {/* 主标题 */}
        <motion.div variants={fadeUp} className="text-center mb-6">
          <h1 className="text-2xl md:text-4xl font-bold text-white/80 leading-tight mb-1">
            一本翻开就能出发的
          </h1>
          <h1 className="text-3xl md:text-5xl font-black leading-tight">
            <span className="bg-gradient-to-r from-amber-200 via-orange-200 to-pink-200 bg-clip-text text-transparent">
              为你量身定制的日本旅行手册
            </span>
          </h1>
        </motion.div>

        {/* 副标题 */}
        <motion.p variants={fadeUp} className="text-sm md:text-base text-white/45 leading-relaxed text-center mb-8 max-w-md mx-auto">
          从路线到餐厅到交通，30页+ 全部安排好
          <br />
          不绕路、有备选、精确到每一个小时
        </motion.p>

        {/* 六张卡牌 — 横排，主题背景图 */}
        <motion.div variants={fadeUp} className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5 mb-10">
          {SELLING_CARDS.map((card, i) => (
            <div
              key={i}
              className="relative rounded-xl overflow-hidden h-28 sm:h-32 group"
            >
              {/* 背景图 */}
              <div
                className="absolute inset-0 bg-cover bg-center transition-transform duration-500 group-hover:scale-105"
                style={{ backgroundImage: `url('${card.img}')` }}
              />
              <div className="absolute inset-0 bg-black/55 group-hover:bg-black/45 transition-colors" />
              {/* 文字 */}
              <div className="relative z-10 flex items-end p-3 h-full">
                <p className="text-[11px] md:text-[12px] text-white font-semibold leading-snug drop-shadow-md">
                  {card.text}
                </p>
              </div>
            </div>
          ))}
        </motion.div>

        <motion.p variants={fadeUp} className="text-[10px] text-white/20 text-center mb-5">
          已为 1,200+ 位旅行者定制行程
        </motion.p>

        {/* CTA */}
        <motion.div variants={fadeUp} className="text-center">
          <div className="relative inline-block group">
            <div className="absolute -inset-1 bg-gradient-to-r from-amber-400 via-pink-400 to-amber-400 rounded-2xl blur-md opacity-30 group-hover:opacity-50 transition-opacity animate-pulse" />
            <a href="#showcase">
              <Button variant="warm" size="xl" className="relative shadow-xl shadow-orange-300/30 min-w-[260px] text-base font-bold">
                先免费看一天 →
              </Button>
            </a>
          </div>
        </motion.div>
      </motion.div>
    </section>
  );
}

// ═════════════════════════════════════════════════════════════════════════════
// SECTION 2: Pain Points — 共鸣
// ═════════════════════════════════════════════════════════════════════════════

const PAINS = [
  { emoji: "😵‍💫", title: "攻略越看越乱", desc: "小红书收藏了 200 篇，打开全是碎片信息，拼不出一条完整路线" },
  { emoji: "⏰", title: "花了两周还没定下来", desc: "光是研究交通换乘 + 门票预约就耗掉所有下班时间" },
  { emoji: "😰", title: "怕踩坑又怕错过", desc: "不知道哪些值得去、哪些是游客陷阱" },
  { emoji: "🤷", title: "同行人众口难调", desc: "有人想逛街、有人想泡温泉、有人带娃，没法让所有人都满意" },
];

function PainPoints() {
  return (
    <section className="py-14 px-6 bg-white">
      <div className="max-w-3xl mx-auto">
        <motion.h2 variants={fadeUp} initial="initial" whileInView="animate" viewport={{ once: true }}
          className="text-xl md:text-2xl font-bold text-stone-900 text-center mb-8">
          每次计划日本旅行，是不是卡在这？
        </motion.h2>
        <div className="grid sm:grid-cols-2 gap-3">
          {PAINS.map((p) => (
            <motion.div key={p.title} variants={fadeUp} initial="initial" whileInView="animate" viewport={{ once: true }}
              className="bg-stone-50 rounded-xl p-5 border border-stone-100">
              <span className="text-2xl mb-2 block">{p.emoji}</span>
              <h3 className="font-bold text-stone-900 text-sm mb-1">{p.title}</h3>
              <p className="text-xs text-stone-500 leading-relaxed">{p.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ═════════════════════════════════════════════════════════════════════════════
// SECTION 3: Showcase — 攻略实物展示（核心说服力）
// ═════════════════════════════════════════════════════════════════════════════

function Showcase() {
  const PAGES = [
    { title: "封面", desc: "你的名字 + 目的地 + 旅行日期", color: "bg-stone-900 text-white", accent: true },
    { title: "总览地图", desc: "7天行程一览 + 路线设计说明", color: "bg-amber-50" },
    { title: "Day 1 路线", desc: "上野→浅草→隅田川 精确到分钟", color: "bg-white" },
    { title: "餐厅推荐", desc: "浅草弁天 ⭐4.2 · 人均¥80 · 含预约方法", color: "bg-white" },
    { title: "交通指南", desc: "JR上野站→浅草站 · 银座线 · 5分钟", color: "bg-blue-50" },
    { title: "预算小结", desc: "Day 1 合计约 ¥580/人 · 含门票交通餐饮", color: "bg-green-50" },
  ];

  return (
    <section id="showcase" className="py-14 px-6 bg-gradient-to-b from-amber-50/50 to-white scroll-mt-14">
      <div className="max-w-4xl mx-auto">
        <motion.div variants={fadeUp} initial="initial" whileInView="animate" viewport={{ once: true }}
          className="text-center mb-8">
          <h2 className="text-xl md:text-2xl font-bold text-stone-900 mb-2">
            你将收到的攻略，长这样
          </h2>
          <p className="text-xs text-stone-500">30-40页 · 不是流水账，是一本真正能用的旅行手册</p>
        </motion.div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {PAGES.map((p, i) => (
            <motion.div key={p.title} variants={fadeUp} initial="initial" whileInView="animate" viewport={{ once: true }}
              className={cn("rounded-xl p-4 border border-stone-100 shadow-sm", p.color)}>
              <p className="text-[9px] font-mono text-stone-400 mb-1.5">第 {i + 1} 页 / 36 页</p>
              <h4 className="font-bold text-sm mb-1">{p.title}</h4>
              <p className="text-[11px] text-stone-500">{p.desc}</p>
            </motion.div>
          ))}
        </div>
        <p className="text-[10px] text-stone-400 text-center mt-4">
          ↑ 仅展示部分页面，完整攻略包含每天 4-5 页详细内容
        </p>
      </div>
    </section>
  );
}

// ═════════════════════════════════════════════════════════════════════════════
// SECTION 4: 核心优势 — 为什么选我们
// ═════════════════════════════════════════════════════════════════════════════

function CoreAdvantages() {
  const items = [
    { icon: "🏠", title: "团队旅居日本", desc: "推荐的每条路线都亲自走过，不是网上抄来的", highlight: false },
    { icon: "📊", title: "6大数据源融合", desc: "Tabelog、Booking、Google 等多平台真实评分，AI 智能排序", highlight: false },
    { icon: "🎯", title: "完全定制，不套模板", desc: "根据你的日期、人数、偏好单独制作，每份都不一样", highlight: true },
    { icon: "⚡", title: "24小时交付", desc: "提交信息后 24h 内收到完整攻略，不用等一周", highlight: false },
  ];

  return (
    <section className="py-14 px-6 bg-white">
      <div className="max-w-3xl mx-auto">
        <motion.h2 variants={fadeUp} initial="initial" whileInView="animate" viewport={{ once: true }}
          className="text-xl md:text-2xl font-bold text-stone-900 text-center mb-8">
          为什么 1,200+ 人选择我们
        </motion.h2>
        <div className="grid sm:grid-cols-2 gap-3">
          {items.map((t) => (
            <motion.div key={t.title} variants={fadeUp} initial="initial" whileInView="animate" viewport={{ once: true }}
              className={cn(
                "rounded-xl p-5 border text-center",
                t.highlight ? "bg-amber-50 border-amber-200" : "bg-stone-50 border-stone-100"
              )}>
              <span className="text-3xl block mb-2">{t.icon}</span>
              <h4 className="font-bold text-stone-900 text-sm mb-1">{t.title}</h4>
              <p className="text-xs text-stone-500 leading-relaxed">{t.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ═════════════════════════════════════════════════════════════════════════════
// SECTION 5: Free Preview 说明 — 零风险
// ═════════════════════════════════════════════════════════════════════════════

function FreePreviewExplainer() {
  return (
    <section className="py-14 px-6 bg-gradient-to-b from-pink-50/30 to-white">
      <div className="max-w-3xl mx-auto">
        <motion.div variants={fadeUp} initial="initial" whileInView="animate" viewport={{ once: true }}
          className="bg-white rounded-2xl border-2 border-pink-200 shadow-lg shadow-pink-100/30 p-6 md:p-10">
          <div className="text-center mb-6">
            <span className="inline-block text-4xl mb-3">🆓</span>
            <h2 className="text-xl md:text-2xl font-bold text-stone-900 mb-2">先免费看效果，满意再下单</h2>
            <p className="text-sm text-stone-500">零风险，不花一分钱</p>
          </div>

          {/* Step flow */}
          <div className="flex flex-col md:flex-row items-center gap-4 md:gap-2 mb-8">
            {[
              { step: "1", title: "填写出行信息", desc: "目的地、天数、人数、偏好", emoji: "📝" },
              { step: "2", title: "免费收到 Day 1", desc: "第一天的完整行程预览", emoji: "📖" },
              { step: "3", title: "觉得好再下单", desc: "满意再付费，不满意不花钱", emoji: "✅" },
            ].map((s, i) => (
              <div key={s.step} className="flex md:flex-col items-center gap-3 md:gap-2 flex-1">
                {i > 0 && <div className="hidden md:block w-full h-[2px] bg-pink-100 -mt-3" />}
                <div className="w-10 h-10 rounded-full bg-pink-500 text-white flex items-center justify-center text-sm font-bold shrink-0">
                  {s.step}
                </div>
                <div className="md:text-center">
                  <div className="text-sm font-bold text-stone-900">{s.emoji} {s.title}</div>
                  <div className="text-[11px] text-stone-500">{s.desc}</div>
                </div>
              </div>
            ))}
          </div>

          {/* Preview vs Full */}
          <div className="grid grid-cols-2 gap-3 mb-6">
            <div className="bg-green-50 rounded-xl p-4 border border-green-100">
              <div className="text-xs font-bold text-green-700 mb-2">🆓 免费预览版</div>
              <ul className="text-[11px] text-stone-600 space-y-1">
                <li>✅ 第一天完整行程</li>
                <li>✅ 感受攻略的细致程度</li>
                <li>✅ 包含路线、餐厅、交通</li>
                <li className="text-stone-400">🔒 Day 2-7 锁定</li>
              </ul>
            </div>
            <div className="bg-amber-50 rounded-xl p-4 border border-amber-200">
              <div className="text-xs font-bold text-amber-700 mb-2">📖 完整版 ¥248</div>
              <ul className="text-[11px] text-stone-600 space-y-1">
                <li>✅ 全部 30-40 页内容</li>
                <li>✅ 每天路线 + 餐厅 + 交通</li>
                <li>✅ Plan B 备选 + 预算表</li>
                <li>✅ 含 2 次免费精调</li>
              </ul>
              <div className="text-[10px] text-stone-400 mt-1 line-through">原价 ¥368</div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

// ═════════════════════════════════════════════════════════════════════════════
// SECTION 6: FAQ
// ═════════════════════════════════════════════════════════════════════════════

const FAQS = [
  { q: "攻略是通用模板还是为我定制的？", a: "每一份都是根据你填写的日期、天数、人数、偏好单独制作，不是套模板。" },
  { q: "多久能收到？", a: "提交信息后 24h 内收到，高峰期不超过 48h。" },
  { q: "不满意怎么办？", a: "¥248 含 2 次免费精调。整体方向不对可以沟通调整。" },
  { q: "¥248 首发价还能维持多久？", a: "限量首发价，达到一定用户数后恢复原价 ¥368。" },
  { q: "攻略是什么格式？", a: "网页版 H5，手机 iPad 电脑都能打开，也可导出长图保存。" },
];

function FAQ() {
  return (
    <section className="py-14 px-6 bg-stone-50">
      <div className="max-w-2xl mx-auto">
        <h2 className="text-lg font-bold text-stone-900 text-center mb-6">常见问题</h2>
        <div className="space-y-2">
          {FAQS.map((f) => (
            <details key={f.q} className="group bg-white rounded-xl border border-stone-100 overflow-hidden">
              <summary className="flex items-center justify-between p-4 cursor-pointer text-sm font-medium text-stone-900 list-none">
                {f.q}
                <span className="ml-2 text-stone-400 group-open:rotate-180 transition-transform text-xs">▾</span>
              </summary>
              <div className="px-4 pb-4 text-sm text-stone-500 leading-relaxed">{f.a}</div>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}

// ═════════════════════════════════════════════════════════════════════════════
// SECTION 7: Final CTA — 唯一的表单入口
// ═════════════════════════════════════════════════════════════════════════════

function FinalCTA() {
  return (
    <section className="py-16 px-6 bg-gradient-to-b from-amber-50 to-pink-50">
      <div className="max-w-2xl mx-auto text-center">
        <motion.div variants={fadeUp} initial="initial" whileInView="animate" viewport={{ once: true }}>
          <h2 className="text-2xl md:text-3xl font-black text-stone-900 mb-3">
            别再纠结了，先免费看看
          </h2>
          <p className="text-sm text-stone-500 mb-2 leading-relaxed max-w-md mx-auto">
            最坏的结果 = 免费拿到一份行程参考
            <br />
            最好的结果 = 省下两周时间，换来一趟真正省心的旅行
          </p>
          <p className="text-xs text-stone-400 mb-8">填写出行信息 → 免费看 Day 1 → 满意再付费</p>

          {/* 超级醒目的 CTA */}
          <div className="relative inline-block group">
            {/* Glow effect */}
            <div className="absolute -inset-1 bg-gradient-to-r from-amber-400 via-pink-400 to-amber-400 rounded-2xl blur-md opacity-40 group-hover:opacity-60 transition-opacity animate-pulse" />
            <Link href="/quiz">
              <Button variant="warm" size="xl" className="relative min-w-[300px] text-base py-5 shadow-2xl shadow-orange-300/40 font-bold">
                🆓 免费生成我的攻略预览 →
              </Button>
            </Link>
          </div>

          <div className="flex justify-center gap-3 mt-6 text-[10px] text-stone-400">
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
    <div className="flex flex-col pt-14">
      <Hero />
      <PainPoints />
      <Showcase />
      <CoreAdvantages />
      <FreePreviewExplainer />
      <FAQ />
      <FinalCTA />
    </div>
  );
}
