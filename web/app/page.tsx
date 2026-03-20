"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { fadeInUp, staggerContainer } from "@/lib/animations";

// ── Animation variants ──────────────────────────────────────────────────────

const fadeIn = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.5 } },
};

// ═══════════════════════════════════════════════════════════════════════════════
// MODULE 1: Hero
// ═══════════════════════════════════════════════════════════════════════════════

function Hero() {
  return (
    <section className="relative flex items-center justify-center overflow-hidden min-h-[85vh]">
      {/* Background */}
      <div
        className="absolute inset-0 bg-cover bg-center"
        style={{ backgroundImage: "url('https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=1920&q=80')" }}
      />
      <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/40 to-black/70" />

      <motion.div
        className="relative z-10 text-center px-6 max-w-3xl"
        variants={staggerContainer}
        initial="initial"
        animate="animate"
      >
        <motion.div variants={fadeInUp} className="flex justify-center gap-2 mb-6">
          {["东京", "京都", "大阪", "北海道", "冲绳"].map((c) => (
            <span key={c} className="text-xs bg-white/10 text-white/70 px-3 py-1 rounded-full">{c}</span>
          ))}
        </motion.div>

        <motion.h1
          variants={fadeInUp}
          className="font-display text-4xl md:text-5xl lg:text-6xl font-bold text-white leading-tight mb-4"
        >
          你的日本行程
          <br />
          <span className="bg-gradient-to-r from-warm-200 via-warm-300 to-sakura-300 bg-clip-text text-transparent">
            已经有人替你想好了
          </span>
        </motion.h1>

        <motion.p
          variants={fadeInUp}
          className="text-base md:text-lg text-white/70 mb-3 max-w-xl mx-auto leading-relaxed"
        >
          30-40页完整攻略 · 精确到每一天每一餐每一站 · 拿到就能出发
        </motion.p>

        <motion.p variants={fadeInUp} className="text-xs text-white/40 mb-8">
          已为 1,200+ 位旅行者定制行程
        </motion.p>

        <motion.div variants={fadeInUp}>
          <Link href="/quiz">
            <Button variant="warm" size="xl" className="shadow-xl shadow-warm-300/30 min-w-[260px]">
              🆓 先免费看一天 →
            </Button>
          </Link>
        </motion.div>
      </motion.div>
    </section>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MODULE 2: Pain Points
// ═══════════════════════════════════════════════════════════════════════════════

const PAINS = [
  { emoji: "😵‍💫", title: "攻略越看越乱", desc: "小红书收藏了 200 篇，打开全是碎片信息，拼不成一条完整路线" },
  { emoji: "⏰", title: "花了两周还没定下来", desc: "光是研究交通换乘 + 门票预约就耗掉所有下班时间，行程还是一团浆糊" },
  { emoji: "😰", title: "怕踩坑又怕错过", desc: "不知道哪些值得去、哪些是游客陷阱，总觉得会漏掉什么" },
  { emoji: "🤷", title: "同行人众口难调", desc: "有人想逛街、有人想泡温泉、有人带娃，根本没法让所有人都满意" },
];

function PainPoints() {
  return (
    <section className="py-16 px-6 bg-white">
      <div className="max-w-4xl mx-auto">
        <motion.h2 variants={fadeIn} initial="initial" whileInView="animate" viewport={{ once: true }}
          className="font-display text-2xl md:text-3xl font-bold text-stone-900 text-center mb-10">
          每次计划日本旅行，是不是都卡在这里？
        </motion.h2>
        <motion.div variants={staggerContainer} initial="initial" whileInView="animate" viewport={{ once: true }}
          className="grid sm:grid-cols-2 gap-4">
          {PAINS.map((p) => (
            <motion.div key={p.title} variants={fadeInUp}
              className="bg-stone-50 rounded-2xl p-6 border border-stone-100">
              <span className="text-3xl mb-3 block">{p.emoji}</span>
              <h3 className="font-bold text-stone-900 mb-1">{p.title}</h3>
              <p className="text-sm text-stone-500 leading-relaxed">{p.desc}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MODULE 3: Solution
// ═══════════════════════════════════════════════════════════════════════════════

const RESULTS = [
  { icon: "📖", title: "30-40页完整手册", desc: "不是简单的行程表，是一本翻开就能出发的旅行说明书" },
  { icon: "🗓️", title: "逐日路线精确到小时", desc: "每天几点出发、去哪里、怎么去，全部安排好" },
  { icon: "🍜", title: "每餐推荐+备选", desc: "午饭吃什么、备选餐厅在哪、人均多少，不用现场纠结" },
  { icon: "🚃", title: "交通方案手把手教", desc: "坐哪趟车、到哪个站换乘、买什么交通卡最省钱" },
];

function Solution() {
  return (
    <section className="py-16 px-6 bg-warm-50">
      <div className="max-w-4xl mx-auto text-center">
        <motion.div variants={fadeIn} initial="initial" whileInView="animate" viewport={{ once: true }}>
          <h2 className="font-display text-2xl md:text-3xl font-bold text-stone-900 mb-2">
            你只需要告诉我们「去哪、几天、和谁」
          </h2>
          <p className="text-stone-500 mb-10">剩下的，全部交给我们</p>
        </motion.div>
        <motion.div variants={staggerContainer} initial="initial" whileInView="animate" viewport={{ once: true }}
          className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {RESULTS.map((r) => (
            <motion.div key={r.title} variants={fadeInUp}
              className="bg-white rounded-2xl p-5 border border-stone-100 text-center">
              <span className="text-3xl mb-3 block">{r.icon}</span>
              <h3 className="font-bold text-stone-900 text-sm mb-1">{r.title}</h3>
              <p className="text-xs text-stone-500 leading-relaxed">{r.desc}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MODULE 4: Free Preview
// ═══════════════════════════════════════════════════════════════════════════════

function FreePreview() {
  return (
    <section className="py-16 px-6 bg-white">
      <div className="max-w-4xl mx-auto">
        <motion.div variants={fadeIn} initial="initial" whileInView="animate" viewport={{ once: true }}
          className="bg-gradient-to-br from-warm-50 to-sakura-50 rounded-3xl p-8 md:p-12 border border-warm-100">
          <div className="md:flex items-center gap-10">
            <div className="flex-1 mb-6 md:mb-0">
              <Badge variant="warm" className="mb-4">🆓 免费</Badge>
              <h2 className="font-display text-2xl md:text-3xl font-bold text-stone-900 mb-3">
                先免费看看，你的攻略会长什么样
              </h2>
              <p className="text-sm text-stone-500 leading-relaxed mb-6">
                填写你的出行信息后，我们会先为你生成一份<strong>免费预览版</strong>——包含第一天的完整行程。
                你可以先看看攻略的细致程度。觉得值，再看完整版；觉得不合适，一分钱不花。
                <br /><br />
                <strong>没有套路，先看货再决定。</strong>
              </p>
              <Link href="/quiz">
                <Button variant="warm" size="lg" className="min-w-[220px]">
                  🆓 免费生成我的攻略预览 →
                </Button>
              </Link>
            </div>
            <div className="flex-shrink-0 w-full md:w-60">
              {/* Preview vs Full mockup */}
              <div className="relative">
                <div className="bg-white rounded-xl shadow-lg p-4 border border-stone-100">
                  <div className="text-xs font-mono text-stone-400 mb-2">预览版 · Day 1</div>
                  <div className="space-y-2">
                    {["09:00 🌸 上野公园", "12:00 🍜 浅草弁天", "13:30 ⛩️ 浅草寺", "17:00 🌇 隅田川"].map((l) => (
                      <div key={l} className="text-xs text-stone-600 bg-stone-50 rounded-lg px-3 py-2">{l}</div>
                    ))}
                  </div>
                </div>
                <div className="absolute -bottom-3 -right-3 bg-stone-200 rounded-xl p-4 w-48 h-32 flex items-center justify-center opacity-60">
                  <div className="text-center">
                    <span className="text-2xl">🔒</span>
                    <p className="text-[10px] text-stone-500 mt-1">完整版 30-40页</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MODULE 5: Main Plan (¥248) — 主推
// ═══════════════════════════════════════════════════════════════════════════════

function MainPlan() {
  return (
    <section className="py-16 px-6 bg-warm-50">
      <div className="max-w-3xl mx-auto">
        <motion.div variants={fadeIn} initial="initial" whileInView="animate" viewport={{ once: true }}
          className="bg-white rounded-3xl border-2 border-warm-300 shadow-xl shadow-warm-200/20 p-8 md:p-10 relative overflow-hidden">
          <Badge variant="warm" className="absolute top-4 right-4 px-4 py-1">🔥 90%用户选择</Badge>
          <h2 className="font-display text-2xl md:text-3xl font-bold text-stone-900 mb-1">
            首发特惠 ¥248，拿走你的完整攻略
          </h2>
          <p className="text-sm text-stone-400 mb-6">
            <span className="line-through">原价 ¥368</span> · 首批用户专属 · 随时恢复原价
          </p>
          <p className="text-sm text-stone-600 leading-relaxed mb-6">
            一份 30-40 页的完整日本旅行手册，从出发到回程每一步都替你安排好。
            省下的不只是钱——是你两周的下班时间、无数次纠结、和旅途中踩坑的风险。
            <br /><br />
            <strong>¥248，比你请朋友吃顿日料还便宜，但换来的是一趟真正省心的旅行。</strong>
          </p>
          <div className="grid sm:grid-cols-2 gap-2 mb-8">
            {[
              "✅ 逐日行程精确到小时",
              "✅ 餐厅推荐+备选方案",
              "✅ 交通方案手把手教",
              "✅ 门票预约提醒清单",
              "✅ Plan B 备选方案",
              "✅ 预订优先级提醒",
              "✅ 全程预算参考",
              "✅ 避坑指南+出行准备",
              "✅ 拍照最佳时段",
              "✅ 2 次免费精调",
            ].map((item) => (
              <p key={item} className="text-sm text-stone-700">{item}</p>
            ))}
          </div>
          <Link href="/quiz">
            <Button variant="warm" size="xl" className="w-full md:w-auto min-w-[300px]">
              🔥 先免费看一天，满意再付 ¥248 →
            </Button>
          </Link>
        </motion.div>
      </div>
    </section>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MODULE 6: Premium Anchor (¥888) — 锚点，低调
// ═══════════════════════════════════════════════════════════════════════════════

function PremiumAnchor() {
  return (
    <section className="py-10 px-6 bg-warm-50">
      <div className="max-w-3xl mx-auto">
        <motion.div variants={fadeIn} initial="initial" whileInView="animate" viewport={{ once: true }}
          className="bg-stone-50 rounded-2xl border border-stone-200 p-6 md:p-8 opacity-90">
          <h3 className="text-lg font-bold text-stone-700 mb-1">想要更多？还有尊享定制版</h3>
          <p className="text-sm text-stone-400 mb-3">适合蜜月、纪念日、或对品质有极致追求的你</p>
          <p className="text-sm text-stone-500 leading-relaxed mb-4">
            在完整版攻略基础上，额外包含：<strong>专属 1v1 行程沟通</strong>、隐藏小众目的地推荐、
            高端餐厅酒店精选方案、以及出行期间的实时答疑支持。
          </p>
          <p className="text-2xl font-mono font-bold text-stone-600">¥888</p>
          <Link href="/quiz" className="text-sm text-stone-400 hover:text-stone-600 mt-2 inline-block transition-colors">
            了解尊享定制 →
          </Link>
        </motion.div>
      </div>
    </section>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MODULE 7: Delivery Showcase — 攻略长什么样
// ═══════════════════════════════════════════════════════════════════════════════

function DeliveryShowcase() {
  const PAGES = [
    { title: "封面", desc: "你的名字 + 目的地 + 旅行日期", color: "bg-stone-900 text-white" },
    { title: "总览", desc: "7天行程一览 + 设计说明", color: "bg-warm-50" },
    { title: "Day 1 路线", desc: "上野→浅草→隅田川 精确到分钟", color: "bg-white" },
    { title: "餐厅推荐", desc: "浅草弁天 ⭐4.2 · 人均¥80 · 需预约", color: "bg-white" },
    { title: "交通指南", desc: "JR上野站→浅草站 · 银座线 · 5分钟", color: "bg-blue-50" },
    { title: "预算小结", desc: "Day 1 合计约 ¥580/人", color: "bg-green-50" },
  ];

  return (
    <section className="py-16 px-6 bg-white">
      <div className="max-w-4xl mx-auto">
        <motion.div variants={fadeIn} initial="initial" whileInView="animate" viewport={{ once: true }}
          className="text-center mb-10">
          <h2 className="font-display text-2xl md:text-3xl font-bold text-stone-900 mb-2">
            你将收到的攻略，长这样
          </h2>
          <p className="text-sm text-stone-500">
            30-40页 · 不是流水账，是一本真正能用的旅行手册
          </p>
        </motion.div>
        <motion.div variants={staggerContainer} initial="initial" whileInView="animate" viewport={{ once: true }}
          className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {PAGES.map((p, i) => (
            <motion.div key={p.title} variants={fadeInUp}
              className={cn("rounded-2xl p-5 border border-stone-100 shadow-sm", p.color)}>
              <p className="text-[10px] font-mono text-stone-400 mb-2">第 {i + 1} 页 / 共 36 页</p>
              <h4 className="font-bold text-sm mb-1">{p.title}</h4>
              <p className="text-xs text-stone-500">{p.desc}</p>
            </motion.div>
          ))}
        </motion.div>
        <p className="text-xs text-stone-400 text-center mt-6">
          ↑ 仅展示部分页面，完整攻略包含每天 4-5 页详细内容
        </p>
      </div>
    </section>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MODULE 8: Trust
// ═══════════════════════════════════════════════════════════════════════════════

function Trust() {
  const ITEMS = [
    { icon: "🏠", title: "旅居日本", desc: "团队在日本生活，推荐的每条路线都亲自走过" },
    { icon: "📊", title: "数据驱动", desc: "整合 Tabelog、Booking、Google 等多平台真实评分" },
    { icon: "🔄", title: "不满意可改", desc: "248 含 2 次免费精调，确保你拿到真正满意的方案" },
    { icon: "🆓", title: "先看后决定", desc: "免费看完第一天行程，觉得值再付费，零风险" },
  ];

  return (
    <section className="py-12 px-6 bg-stone-50">
      <div className="max-w-4xl mx-auto">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {ITEMS.map((t) => (
            <div key={t.title} className="text-center p-4">
              <span className="text-2xl block mb-2">{t.icon}</span>
              <h4 className="font-bold text-stone-900 text-sm mb-1">{t.title}</h4>
              <p className="text-xs text-stone-500">{t.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MODULE 9: FAQ
// ═══════════════════════════════════════════════════════════════════════════════

const FAQS = [
  {
    q: "攻略是通用模板还是为我定制的？",
    a: "每一份攻略都是根据你填写的出行日期、天数、人数、偏好单独制作的，不是套模板。你的攻略和别人的不会一样。",
  },
  {
    q: "免费版和完整版有什么区别？",
    a: "免费版包含第一天的完整行程，让你感受攻略风格和质量。完整版是30-40页的全量手册，精确到每个时间段、每顿饭、每段交通、每个备选方案。",
  },
  {
    q: "多久能收到攻略？",
    a: "提交信息后，24小时内你会收到完整攻略。高峰期可能稍有延迟，但不会超过48小时。",
  },
  {
    q: "如果攻略不满意怎么办？",
    a: "248元套餐包含2次免费精调。如果整体方向不对，可以沟通调整。我们的目标是让你拿到一份真正能用的攻略。",
  },
  {
    q: "¥248 首发价还能维持多久？",
    a: "首发价是限量的，达到一定用户数后会恢复原价 ¥368。具体截止时间不确定，当前下单锁定 ¥248。",
  },
  {
    q: "攻略是什么格式？",
    a: "网页版 H5，手机、iPad、电脑都能打开，也可以导出长图保存到相册或打印出来带着走。",
  },
];

function FAQ() {
  return (
    <section className="py-16 px-6 bg-white">
      <div className="max-w-3xl mx-auto">
        <h2 className="font-display text-2xl font-bold text-stone-900 text-center mb-10">
          你可能还想知道
        </h2>
        <div className="space-y-4">
          {FAQS.map((f) => (
            <details key={f.q} className="group bg-stone-50 rounded-2xl border border-stone-100 overflow-hidden">
              <summary className="flex items-center justify-between p-5 cursor-pointer text-sm font-medium text-stone-900 list-none">
                {f.q}
                <span className="ml-2 text-stone-400 group-open:rotate-180 transition-transform">▾</span>
              </summary>
              <div className="px-5 pb-5 text-sm text-stone-500 leading-relaxed">{f.a}</div>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MODULE 10: Final CTA
// ═══════════════════════════════════════════════════════════════════════════════

function FinalCTA() {
  return (
    <section className="py-16 px-6 bg-gradient-to-b from-warm-50 to-sakura-50">
      <div className="max-w-2xl mx-auto text-center">
        <h2 className="font-display text-2xl md:text-3xl font-bold text-stone-900 mb-3">
          别再纠结了，先免费看看
        </h2>
        <p className="text-sm text-stone-500 mb-8 leading-relaxed max-w-md mx-auto">
          最坏的结果，也不过是免费拿到一份行程参考。
          <br />
          最好的结果，是你省下两周时间，换来一趟真正省心的日本旅行。
        </p>
        <div className="flex flex-col items-center gap-3">
          <Link href="/quiz">
            <Button variant="warm" size="xl" className="min-w-[280px] shadow-lg shadow-warm-300/20">
              🆓 免费生成我的攻略预览 →
            </Button>
          </Link>
          <Link href="/quiz">
            <Button variant="outline" size="lg" className="min-w-[280px]">
              🔥 ¥248 直接定制完整攻略（首发价）
            </Button>
          </Link>
        </div>
        <div className="flex justify-center gap-4 mt-8 text-xs text-stone-400">
          <span>⏱️ 24h交付</span>
          <span>·</span>
          <span>🔄 不满意可改</span>
          <span>·</span>
          <span>🌸 已服务 1,200+ 旅行者</span>
        </div>
      </div>
    </section>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// PAGE: 首页
// ═══════════════════════════════════════════════════════════════════════════════

export default function Home() {
  return (
    <div className="flex flex-col">
      <Hero />
      <PainPoints />
      <Solution />
      <FreePreview />
      <MainPlan />
      <PremiumAnchor />
      <DeliveryShowcase />
      <Trust />
      <FAQ />
      <FinalCTA />
    </div>
  );
}