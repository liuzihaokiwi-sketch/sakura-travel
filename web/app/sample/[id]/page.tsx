"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import sampleData from "@/data/sample-templates.json";

const PLANNER_WECHAT = "Kiwi_iloveu_O-o";
function cn(...c: (string | boolean | undefined)[]) { return c.filter(Boolean).join(" "); }

/* ── 对比表 ─────────────────────────────────────────────────────────────────── */
const Chk = () => <svg className="w-4 h-4 mx-auto text-emerald-500" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/></svg>;
const Dsh = () => <span className="block text-center text-stone-300">—</span>;
const Nm = ({ n }: { n: string }) => <span className="block text-center text-xs font-bold text-stone-700">{n}</span>;

const ROWS = [
  { label: "每日路线", f: <Chk />, s: <Chk />, p: <Chk /> },
  { label: "交通指南", f: <Chk />, s: <Chk />, p: <Chk /> },
  { label: "餐厅推荐", f: <Chk />, s: <Chk />, p: <Chk /> },
  { label: "出片指南", f: <Chk />, s: <Chk />, p: <Chk /> },
  { label: "Plan B", f: <Chk />, s: <Chk />, p: <Chk /> },
  { label: "行前须知", f: <Dsh />, s: <Chk />, p: <Chk /> },
  { label: "预算明细", f: <Chk />, s: <Chk />, p: <Chk /> },
  { label: <><span className="text-amber-600 font-bold">深度比价</span><br/><span className="text-[10px] text-amber-500">预计节省 ¥1500~3000</span></>, f: <Dsh />, s: <Dsh />, p: <Chk />, accent: true },
  { label: "自助微调", f: <Dsh />, s: <Chk />, p: <Chk /> },
  { label: "正式修改", f: <Dsh />, s: <Nm n="1次" />, p: <Nm n="3次" /> },
  { label: <span className="text-violet-600 font-bold">专属规划师</span>, f: <Dsh />, s: <Dsh />, p: <Chk />, accent: true },
  { label: <span className="text-violet-600 font-bold">实时答疑</span>, f: <Dsh />, s: <Dsh />, p: <Chk />, accent: true },
  { label: "攻略页数", f: <Nm n="3-5" />, s: <Nm n="30-40" />, p: <Nm n="40-50" /> },
];

const FAQS = [
  { q: "免费体验版有多少内容", a: "Day 1 完整可执行行程，包括路线、餐厅、交通和预算明细。跟付费版同样的细致程度。" },
  { q: "攻略是模板还是定制的", a: "免费版是高质量样片，展示攻略水准。付费后根据你的具体日期、人数、偏好单独定制，每份都不一样。" },
  { q: "不满意可以改吗", a: "可以！先通过网站自助微调，仍不满意再使用正式修改权益（标准版 1 次 / 尊享版 3 次）。" },
  { q: "多久能收到攻略", a: "付费后 24 小时内收到，高峰期不超过 48 小时。" },
  { q: "攻略是什么格式", a: "网页版 + PDF 双格式。手机、iPad、电脑都能看，PDF 可离线保存。" },
];

/* ── Inner ────────────────────────────────────────────────────────────────── */
function SampleContent() {
  const params = useSearchParams();
  const dest = params.get("dest") || "tokyo";
  const style = params.get("style") || "classic";
  const [copied, setCopied] = useState(false);

  const key = `${dest}_${style}`;
  const template = (sampleData as any)[key] || (sampleData as any)["tokyo_classic"];
  const day1 = template.day1;
  const hooks = template.hooks;

  function copyWechat() {
    const ta = document.createElement("textarea");
    ta.value = PLANNER_WECHAT; ta.style.position = "fixed"; ta.style.left = "-9999px";
    document.body.appendChild(ta); ta.focus(); ta.select();
    try { document.execCommand("copy"); setCopied(true); setTimeout(() => setCopied(false), 2000); } catch { window.prompt("请长按复制微信号：", PLANNER_WECHAT); }
    document.body.removeChild(ta);
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-stone-50 via-white to-amber-50/20">

      {/* ── Day 1 完整样片 ── */}
      <section className="max-w-2xl mx-auto px-4 pt-8 pb-4">
        <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
          <p className="text-xs text-amber-500 font-bold mb-1 tracking-wider">免费体验</p>
          <h1 className="text-xl font-bold text-stone-900 mb-1">{template.title}</h1>
          <p className="text-sm text-stone-400 mb-6">{template.subtitle}</p>

          <div className="bg-gradient-to-r from-amber-500 to-orange-400 text-white rounded-t-2xl px-5 py-3">
            <h2 className="font-bold text-base">Day 1 · {day1.theme}</h2>
          </div>

          <div className="bg-white border-x-2 border-b-2 border-stone-100 rounded-b-2xl divide-y divide-stone-50">
            {day1.items.map((item: any, i: number) => (
              <motion.div key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.08 * i, duration: 0.3 }} className="flex gap-3 px-4 py-3">
                <div className="shrink-0 w-14 text-right"><span className="text-xs font-mono text-stone-400">{item.time}</span></div>
                <div className="shrink-0 text-lg">{item.icon}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-stone-800">{item.place}</span>
                    <span className="text-[10px] text-stone-400">{item.duration}</span>
                  </div>
                  <p className="text-xs text-stone-500 mt-0.5 leading-relaxed">{item.reason}</p>
                  {item.tip && <p className="text-[11px] text-amber-600 mt-1">💡 {item.tip}</p>}
                  {item.photo_spot && <p className="text-[11px] text-pink-500 mt-0.5">📸 {item.photo_spot}</p>}
                </div>
              </motion.div>
            ))}
          </div>

          <div className="flex gap-2 mt-3">
            <div className="flex-1 bg-blue-50 rounded-xl px-3 py-2">
              <p className="text-[10px] text-blue-400 font-bold mb-0.5">🚇 交通</p>
              <p className="text-xs text-blue-700">{day1.transport_summary}</p>
            </div>
            <div className="flex-1 bg-amber-50 rounded-xl px-3 py-2">
              <p className="text-[10px] text-amber-400 font-bold mb-0.5">💰 预算</p>
              <p className="text-xs text-amber-700">{day1.budget_summary}</p>
            </div>
          </div>
        </motion.div>
      </section>

      {/* ── 次CTA 1: 微信（看完一天后） ── */}
      <section className="max-w-2xl mx-auto px-4 py-3">
        <div className="bg-stone-50 rounded-xl px-4 py-3 flex items-center justify-between">
          <p className="text-xs text-stone-500">想把后面几天也排顺？</p>
          <button onClick={copyWechat} className="text-xs font-bold text-amber-600 hover:text-amber-700 transition-colors">
            {copied ? "✓ 已复制" : `加微信聊 → ${PLANNER_WECHAT}`}
          </button>
        </div>
      </section>

      {/* ── 后续高光钩子（模糊锁定） ── */}
      <section className="max-w-2xl mx-auto px-4 py-5">
        <h3 className="text-sm font-bold text-stone-500 mb-3 text-center">后面几天同样精彩</h3>
        <div className="space-y-2.5">
          {hooks.map((h: any, i: number) => (
            <div key={i} className="relative bg-white rounded-xl border border-stone-100 px-4 py-3 overflow-hidden">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-amber-500 font-bold">Day {h.day}</span>
                  <h4 className="text-sm font-bold text-stone-800">{h.title}</h4>
                  <p className="text-xs text-stone-400 mt-0.5">{h.teaser}</p>
                </div>
                <span className="text-2xl opacity-30">🔒</span>
              </div>
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-transparent to-white/80 pointer-events-none" />
            </div>
          ))}
        </div>
        <p className="text-center text-xs text-stone-400 mt-3">后面每一天都像 Day 1 一样细致 · 精确到每小时</p>
      </section>

      {/* ── 次CTA 2: 微信（钩子下面） ── */}
      <section className="max-w-2xl mx-auto px-4 py-2">
        <div className="text-center">
          <p className="text-xs text-stone-400 mb-1">你的情况如果更特殊，微信里可以直接说</p>
          <button onClick={copyWechat} className={cn(
            "text-xs font-bold px-4 py-1.5 rounded-full transition-all",
            copied ? "bg-green-100 text-green-600" : "bg-stone-100 text-stone-600 hover:bg-stone-200"
          )}>
            {copied ? "✓ 已复制微信号" : `复制微信号 ${PLANNER_WECHAT}`}
          </button>
        </div>
      </section>

      {/* ── 主CTA: 加微信咨询（原为直接付费，已改为引流客服） ── */}
      {/*
      <section className="max-w-2xl mx-auto px-4 py-6">
        <div className="bg-gradient-to-br from-amber-50 to-orange-50 border-2 border-amber-200 rounded-2xl p-5 text-center">
          <p className="text-xs text-amber-500 font-bold mb-1">解锁完整 {template.route_overview.total_days} 天定制攻略</p>
          <div className="mb-3">
            <span className="text-red-400 line-through text-lg font-bold mr-2">原价 ¥368</span>
            <span className="text-3xl font-black bg-gradient-to-r from-red-500 to-orange-500 bg-clip-text text-transparent">¥248</span>
          </div>
          <button className="w-full py-3 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 text-white font-bold text-base shadow-lg shadow-orange-200/50 active:scale-95 transition-transform">
            立即解锁完整攻略
          </button>
          <p className="text-[11px] text-stone-400 mt-2">付费后填写详细信息 → 24h 内收到专属定制攻略</p>
        </div>
      </section>
      */}
      <section className="max-w-2xl mx-auto px-4 py-6">
        <div className="bg-gradient-to-br from-emerald-50 to-teal-50 border-2 border-emerald-200 rounded-2xl p-5 text-center">
          <p className="text-xs text-emerald-600 font-bold mb-1">想要完整 {template.route_overview.total_days} 天定制攻略？</p>
          <p className="text-sm text-stone-600 mb-4 leading-relaxed">
            加规划师微信，聊聊你的行程想法<br/>
            <span className="text-stone-400 text-xs">不着急付费，先沟通确认方案合适再决定</span>
          </p>
          <button onClick={copyWechat} className="w-full py-3 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 text-white font-bold text-base shadow-lg shadow-emerald-200/50 active:scale-95 transition-transform">
            {copied ? "✓ 已复制微信号" : `加规划师微信 → ${PLANNER_WECHAT}`}
          </button>
          <p className="text-[11px] text-stone-400 mt-2">通常 2 小时内回复 · 免费沟通行程需求</p>
        </div>
      </section>

      {/* ── 三版对比表 ── */}
      <section className="max-w-2xl mx-auto px-4 py-6">
        <h2 className="text-lg font-bold text-stone-900 text-center mb-1">三个版本对比</h2>
        <p className="text-sm text-stone-400 text-center mb-5">总有一个适合你</p>
        <div className="bg-white rounded-2xl border border-stone-100 shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b-2 border-stone-100">
                <th className="w-[30%]" />
                <th className="px-2 py-4 text-center w-[23%]">
                  <p className="text-rose-400 text-[10px] font-bold">非定制</p>
                  <p className="text-stone-500 text-xs font-bold">首日样片</p>
                  <p className="text-xl font-black text-stone-600">免费</p>
                </th>
                <th className="px-2 pt-6 pb-4 text-center w-[24%] bg-amber-50 border-x-2 border-amber-200 relative">
                  <div className="absolute -top-0 left-1/2 -translate-x-1/2 bg-gradient-to-r from-amber-500 to-orange-500 text-white text-[10px] font-bold px-3 py-1 rounded-b-lg whitespace-nowrap shadow-md">首发特惠</div>
                  <p className="text-emerald-500 text-[10px] font-bold mt-1">定制</p>
                  <p className="text-amber-700 text-xs font-bold">完整攻略</p>
                  <p className="text-red-400 line-through text-base font-bold mt-1">原价 ¥368</p>
                  <p className="text-2xl font-black bg-gradient-to-r from-red-500 to-orange-500 bg-clip-text text-transparent leading-tight">¥248</p>
                </th>
                <th className="px-2 py-4 text-center w-[23%]">
                  <p className="text-emerald-500 text-[10px] font-bold">深度定制</p>
                  <p className="text-violet-500 text-xs font-bold">尊享版</p>
                  <p className="text-xl font-black text-violet-600">¥888</p>
                </th>
              </tr>
            </thead>
            <tbody>
              {ROWS.map((row, i) => (
                <tr key={i} className={cn("border-b border-stone-50", i % 2 === 0 ? "bg-white" : "bg-stone-50/30", row.accent && "bg-gradient-to-r from-amber-50/40 to-violet-50/40")}>
                  <td className="px-3 py-2.5 text-xs font-semibold text-stone-800">{row.label}</td>
                  <td className="px-1 py-2.5 text-center">{row.f}</td>
                  <td className="px-1 py-2.5 text-center bg-amber-50/20 border-x border-amber-50/60">{row.s}</td>
                  <td className="px-1 py-2.5 text-center">{row.p}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* ── FAQ ── */}
      <section className="max-w-2xl mx-auto px-4 py-6">
        <h2 className="text-lg font-bold text-stone-900 text-center mb-4">常见问题</h2>
        <div className="space-y-1.5">
          {FAQS.map((f) => (
            <div key={f.q} className="bg-white rounded-xl border border-stone-100 p-4">
              <h3 className="text-sm font-bold text-stone-900 mb-2">{f.q}</h3>
              <p className="text-sm text-stone-500 leading-relaxed">{f.a}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── PDF 下载（补充） ── */}
      <section className="max-w-2xl mx-auto px-4 py-4 text-center">
        <p className="text-xs text-stone-300 mb-1">方便保存给同行人</p>
        <button className="text-xs text-stone-400 border border-stone-200 rounded-full px-4 py-1.5 hover:bg-stone-50 transition-colors">
          📄 下载 Day 1 样片 PDF
        </button>
      </section>

      {/* ── 底部固定 CTA（原为付费按钮，已改为微信引流） ── */}
      {/*
      <div className="h-16" />
      <div className="fixed bottom-0 left-0 right-0 bg-white/95 backdrop-blur-sm border-t border-stone-100 px-4 py-3 z-50">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <div>
            <span className="text-red-400 line-through text-sm mr-1">¥368</span>
            <span className="text-xl font-black text-orange-500">¥248</span>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={copyWechat} className="text-xs text-stone-400 hover:text-stone-600 transition-colors px-2">
              {copied ? "✓" : "加微信"}
            </button>
            <button className="px-6 py-2.5 rounded-full bg-gradient-to-r from-amber-500 to-orange-500 text-white font-bold text-sm shadow-md active:scale-95 transition-transform">
              解锁完整攻略
            </button>
          </div>
        </div>
      </div>
      */}
      <div className="h-16" /> {/* spacer */}
      <div className="fixed bottom-0 left-0 right-0 bg-white/95 backdrop-blur-sm border-t border-stone-100 px-4 py-3 z-50">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <div>
            <p className="text-xs text-stone-500">想定制你的专属攻略？</p>
            <p className="text-[10px] text-stone-400">先聊聊，不着急付费</p>
          </div>
          <button onClick={copyWechat} className="px-6 py-2.5 rounded-full bg-gradient-to-r from-emerald-500 to-teal-500 text-white font-bold text-sm shadow-md active:scale-95 transition-transform">
            {copied ? "✓ 已复制微信号" : `加微信聊 →`}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function SamplePage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><p className="text-stone-400">加载中...</p></div>}>
      <SampleContent />
    </Suspense>
  );
}
