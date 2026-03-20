"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { fadeInUp } from "@/lib/animations";

const DAYS = [
  { num: 1, theme: "浅草·上野" },
  { num: 2, theme: "涩谷·原宿" },
  { num: 3, theme: "新宿·中目黑" },
  { num: 4, theme: "镰仓一日" },
  { num: 5, theme: "六本木·东京塔" },
  { num: 6, theme: "千鸟之渊·银座" },
  { num: 7, theme: "下北·吉祥寺" },
];

const FOCUS_OPTIONS = ["📸 出片", "🍣 美食", "🛍️ 购物", "🏛️ 文化", "🧖 放松"];

export default function EditPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [selectedDay, setSelectedDay] = useState(0);
  const [pace, setPace] = useState(50);
  const [focus, setFocus] = useState("📸 出片");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = () => {
    setSubmitting(true);
    setTimeout(() => router.push(`/plan/${params.id}`), 1200);
  };

  return (
    <div className="min-h-[calc(100vh-3.5rem)] bg-warm-50 py-8 px-6">
      <motion.div variants={fadeInUp} initial="initial" animate="animate" className="max-w-2xl mx-auto">
        <h1 className="font-display text-2xl font-bold text-stone-900 mb-1">✏️ 精调行程</h1>
        <p className="text-sm text-stone-400 mb-8">选择要调整的天数和内容，我们会重新优化</p>

        {/* Day selector */}
        <div className="mb-6">
          <label className="text-sm font-semibold text-stone-700 mb-3 block">调整哪一天？</label>
          <div className="grid grid-cols-7 gap-2">
            {DAYS.map((d, i) => (
              <button key={d.num} onClick={() => setSelectedDay(i)}
                className={cn("rounded-xl p-3 text-center border-2 transition-all",
                  selectedDay === i ? "border-warm-300 bg-warm-50" : "border-stone-100 bg-white hover:border-stone-200"
                )}>
                <p className={cn("text-xs font-bold", selectedDay === i ? "text-warm-400" : "text-stone-500")}>Day {d.num}</p>
                <p className="text-[9px] text-stone-400 mt-1">{d.theme}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Pace slider */}
        <div className="bg-white rounded-2xl border border-stone-100 p-6 mb-4">
          <label className="text-sm font-semibold text-stone-700 mb-3 block">节奏调整</label>
          <div className="flex items-center gap-4">
            <span className="text-xs text-stone-400">宽松</span>
            <input type="range" min={0} max={100} value={pace} onChange={(e) => setPace(parseInt(e.target.value))}
              className="flex-1 h-2 bg-stone-200 rounded-full appearance-none cursor-pointer accent-warm-300" />
            <span className="text-xs text-stone-400">紧凑</span>
          </div>
          <p className="text-xs text-stone-400 mt-2 text-center">
            {pace < 30 ? "少安排几个点，多留自由时间" : pace > 70 ? "尽量多看，把时间塞满" : "不紧不松，适中节奏"}
          </p>
        </div>

        {/* Focus switch */}
        <div className="bg-white rounded-2xl border border-stone-100 p-6 mb-4">
          <label className="text-sm font-semibold text-stone-700 mb-3 block">这天的侧重</label>
          <div className="flex flex-wrap gap-2">
            {FOCUS_OPTIONS.map((f) => (
              <button key={f} onClick={() => setFocus(f)}
                className={cn("px-4 py-2 rounded-xl text-sm font-medium transition-all border",
                  focus === f ? "border-warm-300 bg-warm-50 text-warm-500" : "border-stone-100 bg-white text-stone-500 hover:border-stone-200"
                )}>
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* Replace spot */}
        <div className="bg-white rounded-2xl border border-stone-100 p-6 mb-4">
          <label className="text-sm font-semibold text-stone-700 mb-3 block">想换掉某个景点？</label>
          <p className="text-xs text-stone-400 mb-3">点击想换的景点，我们会给你同区域的 3 个备选</p>
          <div className="space-y-2">
            {["上野恩赐公园", "东京国立博物馆", "浅草寺", "阿美横丁"].map((spot) => (
              <button key={spot} className="w-full text-left px-4 py-3 rounded-xl border border-stone-100 hover:border-warm-200 hover:bg-warm-50/50 transition-all text-sm text-stone-600">
                🔄 {spot}
              </button>
            ))}
          </div>
        </div>

        {/* Submit */}
        <div className="mt-8">
          <Button variant="warm" size="xl" className="w-full" onClick={handleSubmit} disabled={submitting}>
            {submitting ? "正在重新优化..." : "提交精调"}
          </Button>
          <p className="text-xs text-stone-400 text-center mt-2">提交后预计 1-2 小时内更新</p>
        </div>
      </motion.div>
    </div>
  );
}
