"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { Button } from "@/components/ui/button";

const fadeUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.5 } },
};

const FAQ_GROUPS: { category: string; items: { q: string; a: string }[] }[] = [
  {
    category: "关于产品",
    items: [
      { q: "攻略是通用模板还是为我定制的", a: "每一份都是根据你的出行日期、天数、同行人、偏好和预算倾向单独制作的，不是套模板，每份都不一样。" },
      { q: "攻略包含哪些内容", a: "封面 + 全程总纲 + 每日路线（精确到小时）+ 餐厅推荐（评分+人均+预约方法）+ 交通指南 + Plan B 备选 + 出片指南 + 行前准备与安全须知 + 每日预算小结，共 30-40 页。" },
      { q: "攻略是什么格式，怎么看", a: "网页版 + PDF 双格式。手机、iPad、电脑都能看。PDF 可以离线保存、打印带在身上。" },
      { q: "免费体验版有多少内容", a: "Day 1 完整可执行行程，包括路线、餐厅、交通和预算明细，跟付费版同样的细致程度。出片指南和 Plan B 会有演示样例供参考。其余天数展示亮点预告。" },
    ],
  },
  {
    category: "关于价格和修改",
    items: [
      { q: "¥248 和 ¥888 是固定价格吗", a: "这是 7 天行程的参考价。其他天数会按行程复杂度小幅浮动，付款前会跟你确认最终价格，不会有隐藏费用。" },
      { q: "不满意可以改吗", a: "可以！我们提供两种方式：① 自助微调——通过我们网站在线操作，替换景点、调整节奏，不限次数、不消耗修改权益；② 正式修改——自助微调后仍不满意，标准版含 1 次正式结构化修改，尊享版含 3 次。" },
      { q: "自助微调具体怎么操作", a: "收到攻略后，在我们网站的行程页面上，你可以直接点击某个景点或餐厅旁的「替换」按钮，系统会智能推荐合适的备选项，选中即替换，实时更新，不需要联系客服。" },
      { q: "尊享版和标准版主要区别是什么", a: "尊享版额外包含：1 对 1 沟通帮你把关行程合理性、旅途中微信实时答疑、3 次正式修改（标准版 1 次），以及深度比价方案——可帮你节省 15%-20% 的出行总费用，还有更深度的酒店推荐和特色体验筛选。" },
    ],
  },
  {
    category: "关于流程和交付",
    items: [
      { q: "多久能收到攻略", a: "提交信息后 24 小时内收到，樱花季/红叶季等高峰期不超过 48 小时。" },
      { q: "怎么付款", a: "先免费看 Day 1，满意后通过微信扫码付款。不满意完全不用付钱。" },
      { q: "行程是 AI 生成的吗", a: "我们的规划团队长期旅居日本，每条路线都经过实地验证和专业判断。系统辅助提高效率，但最终品质由团队把关。" },
      { q: "你们能帮忙订酒店和机票吗", a: "攻略中会给出酒店区域推荐和价位参考，但不代订酒店和机票。我们专注做好行程规划这一件事。" },
    ],
  },
  {
    category: "关于使用",
    items: [
      { q: "到了日本没网也能看吗", a: "PDF 版可以提前下载到手机，完全离线可用。我们也建议出发前下载保存。" },
      { q: "可以分享给同行的朋友吗", a: "可以。攻略带有轻度个性化水印，方便你的同伴一起参考使用。" },
      { q: "行程中有突发情况怎么办", a: "受天气、排队等影响的活动都有 Plan B 备选方案。尊享版用户还可以旅途中微信实时咨询。" },
    ],
  },
];

export default function FAQPage() {
  return (
    <div className="min-h-screen bg-stone-50 pt-20 pb-16 px-5">
      <div className="max-w-2xl mx-auto">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-10">
          <h1 className="text-2xl md:text-3xl font-bold text-stone-900 mb-2">常见问题</h1>
          <p className="text-sm text-stone-500">关于我们服务的全部解答</p>
        </motion.div>

        <div className="space-y-8">
          {FAQ_GROUPS.map((group) => (
            <motion.div key={group.category} variants={fadeUp} initial="initial" whileInView="animate" viewport={{ once: true }}>
              <p className="text-xs font-bold text-stone-400 uppercase tracking-wider mb-3 px-1">{group.category}</p>
              <div className="space-y-1.5">
                {group.items.map((f) => (
                  <details key={f.q} className="group bg-white rounded-xl border border-stone-100 overflow-hidden">
                    <summary className="flex items-center justify-between p-4 cursor-pointer text-sm font-medium text-stone-900 list-none">
                      {f.q}
                      <span className="ml-2 text-stone-400 group-open:rotate-180 transition-transform text-xs flex-shrink-0">▾</span>
                    </summary>
                    <div className="px-4 pb-4 text-sm text-stone-500 leading-relaxed">{f.a}</div>
                  </details>
                ))}
              </div>
            </motion.div>
          ))}
        </div>

        <div className="text-center mt-12">
          <p className="text-sm text-stone-500 mb-4">还有其他问题，先免费体验一下</p>
          <Link href="/quiz">
            <Button variant="warm" size="lg">
              免费生成我的攻略预览 →
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
