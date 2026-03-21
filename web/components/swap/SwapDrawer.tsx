"use client";

/**
 * T13: 自助微调前端组件
 * 用法：在行程详情页的每个景点/餐厅卡片旁显示「换一换」按钮，
 * 点击弹出候选卡片抽屉，选择后调用 swap API 替换。
 */

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// ── Types ──────────────────────────────────────────────────────────────────

interface Candidate {
  entity_id: string;
  name_zh: string;
  address_zh?: string;
  google_rating?: number;
  tabelog_score?: number;
  cover_image_url?: string;
  similarity_score: number;
  distance_km?: number;
  reason_zh?: string;
  rank: number;
}

interface SwapDrawerProps {
  planId: string;
  dayNumber: number;
  slotIndex: number;
  sourceEntityName: string;
  category: string;
  onSwapSuccess?: (newEntityName: string) => void;
}

// ── 候选卡片 ───────────────────────────────────────────────────────────────

function CandidateCard({
  candidate,
  onSelect,
  isSelected,
}: {
  candidate: Candidate;
  onSelect: () => void;
  isSelected: boolean;
}) {
  const rating = candidate.tabelog_score ?? candidate.google_rating;
  const ratingLabel = candidate.tabelog_score ? "Tabelog" : "Google";

  return (
    <motion.button
      layout
      onClick={onSelect}
      className={cn(
        "w-full text-left rounded-xl border-2 p-3 transition-all",
        isSelected
          ? "border-rose-500 bg-rose-50"
          : "border-stone-200 bg-white hover:border-rose-300 hover:bg-rose-50/50"
      )}
    >
      <div className="flex gap-3 items-start">
        {/* 封面图 */}
        <div className="w-16 h-16 rounded-lg bg-stone-100 flex-shrink-0 overflow-hidden">
          {candidate.cover_image_url ? (
            <img
              src={candidate.cover_image_url}
              alt={candidate.name_zh}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-2xl">
              {getCategoryEmoji(candidate)}
            </div>
          )}
        </div>

        {/* 信息 */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold text-stone-800 text-sm">{candidate.name_zh}</span>
            {isSelected && (
              <span className="text-xs bg-rose-500 text-white px-1.5 py-0.5 rounded-full">
                已选
              </span>
            )}
          </div>

          {/* 评分 + 距离 */}
          <div className="flex items-center gap-3 mt-1 text-xs text-stone-500">
            {rating && (
              <span>
                ⭐ {rating.toFixed(1)} <span className="text-stone-400">{ratingLabel}</span>
              </span>
            )}
            {candidate.distance_km && (
              <span>📍 距原景点 {candidate.distance_km.toFixed(1)}km</span>
            )}
          </div>

          {/* 推荐理由 */}
          {candidate.reason_zh && (
            <p className="text-xs text-stone-500 mt-1 line-clamp-2">{candidate.reason_zh}</p>
          )}
        </div>

        {/* 相似度徽章 */}
        <div className="flex-shrink-0">
          <span
            className={cn(
              "text-xs px-1.5 py-0.5 rounded-full font-medium",
              candidate.similarity_score >= 0.7
                ? "bg-green-100 text-green-700"
                : candidate.similarity_score >= 0.4
                ? "bg-yellow-100 text-yellow-700"
                : "bg-stone-100 text-stone-500"
            )}
          >
            {Math.round(candidate.similarity_score * 100)}% 匹配
          </span>
        </div>
      </div>
    </motion.button>
  );
}

function getCategoryEmoji(candidate: Candidate): string {
  // 根据 reason_zh 或名称推断 emoji
  const name = candidate.name_zh?.toLowerCase() ?? "";
  if (name.includes("市场") || name.includes("商场")) return "🏪";
  if (name.includes("神社") || name.includes("寺")) return "⛩️";
  if (name.includes("公园")) return "🌿";
  return "📍";
}

// ── 主组件：换一换抽屉 ────────────────────────────────────────────────────

export function SwapDrawer({
  planId,
  dayNumber,
  slotIndex,
  sourceEntityName,
  category,
  onSwapSuccess,
}: SwapDrawerProps) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<string | null>(null);
  const [cacheStatus, setCacheStatus] = useState<"hit" | "miss" | null>(null);

  async function openDrawer() {
    setOpen(true);
    if (candidates.length > 0) return; // 已加载过，不重复请求

    setLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `/api/trips/${planId}/alternatives/${dayNumber}/${slotIndex}`
      );
      const data = await res.json();
      setCandidates(data.candidates ?? []);
      setCacheStatus(data.cache_status ?? null);
    } catch (e) {
      setError("加载候选列表失败，请稍后重试");
    } finally {
      setLoading(false);
    }
  }

  async function handleSwap() {
    if (!selected) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch(`/api/trips/${planId}/swap`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          day_number: dayNumber,
          slot_index: slotIndex,
          new_entity_id: selected,
        }),
      });
      const data = await res.json();
      if (data.success) {
        setResult(data.message);
        onSwapSuccess?.(data.new_entity_name ?? "");
        setTimeout(() => {
          setOpen(false);
          setResult(null);
          setSelected(null);
          setCandidates([]); // 让下次重新拉取（缓存已失效）
        }, 1800);
      } else {
        setError(data.message);
      }
    } catch (e) {
      setError("替换失败，请稍后重试");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      {/* 触发按钮 */}
      <button
        onClick={openDrawer}
        className="text-xs text-stone-400 hover:text-rose-500 flex items-center gap-1 transition-colors mt-1"
      >
        <span>🔄</span>
        <span>换一换</span>
      </button>

      {/* 遮罩 + 抽屉 */}
      <AnimatePresence>
        {open && (
          <>
            {/* 遮罩 */}
            <motion.div
              key="overlay"
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.4 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40 bg-black"
              onClick={() => setOpen(false)}
            />

            {/* 底部抽屉 */}
            <motion.div
              key="drawer"
              initial={{ y: "100%" }}
              animate={{ y: 0 }}
              exit={{ y: "100%" }}
              transition={{ type: "spring", damping: 28, stiffness: 350 }}
              className="fixed bottom-0 left-0 right-0 z-50 bg-white rounded-t-2xl shadow-2xl max-h-[80vh] flex flex-col"
            >
              {/* 拖动条 */}
              <div className="flex justify-center pt-3 pb-1">
                <div className="w-10 h-1 bg-stone-300 rounded-full" />
              </div>

              {/* 标题 */}
              <div className="px-5 pb-3 border-b border-stone-100">
                <h3 className="font-semibold text-stone-800 text-base">
                  换掉「{sourceEntityName}」
                </h3>
                <p className="text-xs text-stone-400 mt-0.5">
                  以下是风格相近、距离合理的替换选项
                </p>
                {cacheStatus === "miss" && (
                  <p className="text-xs text-amber-500 mt-1">⏳ 候选数据准备中，当前显示实时结果</p>
                )}
              </div>

              {/* 内容区 */}
              <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
                {loading && (
                  <div className="text-center py-10 text-stone-400">
                    <div className="animate-spin text-2xl mb-2">⟳</div>
                    <p className="text-sm">正在加载候选...</p>
                  </div>
                )}

                {!loading && candidates.length === 0 && !error && (
                  <div className="text-center py-10 text-stone-400">
                    <p className="text-2xl mb-2">🔍</p>
                    <p className="text-sm">暂无推荐替换选项</p>
                    <p className="text-xs mt-1 text-stone-300">
                      当前景点可能是此区域的最优选择
                    </p>
                  </div>
                )}

                {error && (
                  <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-sm text-red-600">
                    {error}
                  </div>
                )}

                {result && (
                  <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    className="bg-green-50 border border-green-200 rounded-xl p-4 text-center"
                  >
                    <div className="text-2xl mb-1">✅</div>
                    <p className="text-sm text-green-700 font-medium">{result}</p>
                  </motion.div>
                )}

                {!loading &&
                  !result &&
                  candidates.map((c) => (
                    <CandidateCard
                      key={c.entity_id}
                      candidate={c}
                      isSelected={selected === c.entity_id}
                      onSelect={() =>
                        setSelected(selected === c.entity_id ? null : c.entity_id)
                      }
                    />
                  ))}
              </div>

              {/* 底部操作栏 */}
              {!result && (
                <div className="px-4 py-4 border-t border-stone-100 bg-white safe-area-bottom">
                  <div className="flex gap-3">
                    <Button
                      variant="outline"
                      className="flex-1"
                      onClick={() => setOpen(false)}
                    >
                      取消
                    </Button>
                    <Button
                      className="flex-1 bg-rose-600 hover:bg-rose-700 text-white"
                      disabled={!selected || submitting}
                      onClick={handleSwap}
                    >
                      {submitting ? "替换中..." : "确认替换"}
                    </Button>
                  </div>
                  {selected && (
                    <p className="text-xs text-center text-stone-400 mt-2">
                      替换后当天路线顺序自动重排
                    </p>
                  )}
                </div>
              )}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
