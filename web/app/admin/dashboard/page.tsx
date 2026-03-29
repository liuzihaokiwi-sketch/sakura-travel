"use client";

import { useState, useEffect } from "react";

interface DashboardStats {
  summary: {
    total_entities: number;
    verified_count: number;
    total_clusters: number;
    pending_review: number;
  };
  entity_counts: Record<string, { poi: number; hotel: number; restaurant: number }>;
  trust_distribution: Record<string, number>;
  source_distribution: Record<string, number>;
  cluster_stats: {
    total: number;
    active: number;
    with_anchors: number;
    without_anchors: number;
  };
  recent_entities: Array<{
    entity_id: string;
    name_zh: string;
    entity_type: string;
    city_code: string;
    trust_status: string;
    created_at: string | null;
  }>;
}

const CITY_LABELS: Record<string, string> = {
  tokyo: "东京",
  osaka: "大阪",
  kyoto: "京都",
  sapporo: "札幌",
  fukuoka: "福冈",
  naha: "冲绳",
  hakone: "箱根",
  nikko: "日光",
  hiroshima: "广岛",
  nara: "奈良",
};

const TRUST_LABELS: Record<string, { label: string; color: string }> = {
  verified: { label: "已验证", color: "bg-emerald-500" },
  unverified: { label: "未验证", color: "bg-slate-400" },
  ai_generated: { label: "AI生成", color: "bg-orange-400" },
  suspicious: { label: "存疑", color: "bg-red-400" },
  rejected: { label: "已拒绝", color: "bg-slate-800" },
};

const ENTITY_TYPE_LABELS: Record<string, string> = {
  poi: "景点",
  hotel: "酒店",
  restaurant: "餐厅",
};

const TRUST_STATUS_STYLE: Record<string, string> = {
  verified: "bg-emerald-100 text-emerald-700",
  unverified: "bg-slate-100 text-slate-600",
  ai_generated: "bg-orange-100 text-orange-700",
  suspicious: "bg-red-100 text-red-700",
  rejected: "bg-slate-200 text-slate-800",
};

function SummaryCard({
  label,
  value,
  icon,
  color,
}: {
  label: string;
  value: number;
  icon: string;
  color: string;
}) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 px-6 py-5 flex items-center gap-4">
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-xl ${color}`}>
        {icon}
      </div>
      <div>
        <p className="text-2xl font-bold text-slate-900">{value.toLocaleString()}</p>
        <p className="text-xs text-slate-500 mt-0.5">{label}</p>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/admin/dashboard")
      .then((r) => r.json())
      .then((data) => {
        if (data.error) throw new Error(data.error);
        setStats(data);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <p className="text-slate-400 text-sm">加载中...</p>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="bg-red-50 border border-red-200 rounded-xl px-6 py-4 text-sm text-red-700">
          加载失败：{error}
        </div>
      </div>
    );
  }

  // 城市柱状图数据
  const cityEntries = Object.entries(stats.entity_counts).sort(
    ([, a], [, b]) => (b.poi + b.hotel + b.restaurant) - (a.poi + a.hotel + a.restaurant)
  );
  const maxCityTotal = Math.max(
    ...cityEntries.map(([, v]) => v.poi + v.hotel + v.restaurant),
    1
  );

  // trust 分布圆环数据
  const trustTotal = Object.values(stats.trust_distribution).reduce((a, b) => a + b, 0) || 1;
  let cumulativePct = 0;
  const trustSegments = Object.entries(stats.trust_distribution).map(([key, cnt]) => {
    const pct = (cnt / trustTotal) * 100;
    const start = cumulativePct;
    cumulativePct += pct;
    return { key, cnt, pct, start };
  });

  // CSS conic-gradient for donut
  const conicGradient = trustSegments
    .map(({ key, pct, start }) => {
      const colorMap: Record<string, string> = {
        verified: "#10b981",
        unverified: "#94a3b8",
        ai_generated: "#fb923c",
        suspicious: "#f87171",
        rejected: "#1e293b",
      };
      const color = colorMap[key] || "#94a3b8";
      return `${color} ${start.toFixed(1)}% ${(start + pct).toFixed(1)}%`;
    })
    .join(", ");

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-3">
        <h1 className="text-sm font-semibold text-slate-900">数据概览</h1>
        <p className="text-xs text-slate-400">内容库与活动簇汇总统计</p>
      </header>

      <div className="px-6 py-6 space-y-6">
        {/* 顶部数字卡片 */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <SummaryCard
            label="总实体数（活跃）"
            value={stats.summary.total_entities}
            icon="🏨"
            color="bg-indigo-50"
          />
          <SummaryCard
            label="已验证实体"
            value={stats.summary.verified_count}
            icon="✅"
            color="bg-emerald-50"
          />
          <SummaryCard
            label="活动簇总数"
            value={stats.summary.total_clusters}
            icon="🗺️"
            color="bg-sky-50"
          />
          <SummaryCard
            label="待审核（未验证）"
            value={stats.summary.pending_review}
            icon="⚠️"
            color="bg-amber-50"
          />
        </div>

        {/* 中间：柱状图 + 圆环图 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* 按城市实体数量柱状图 */}
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <h2 className="text-sm font-semibold text-slate-800 mb-4">按城市实体分布</h2>
            {cityEntries.length === 0 ? (
              <p className="text-xs text-slate-400 py-8 text-center">暂无数据</p>
            ) : (
              <div className="space-y-3">
                {cityEntries.map(([city, counts]) => {
                  const total = counts.poi + counts.hotel + counts.restaurant;
                  const totalPct = (total / maxCityTotal) * 100;
                  const poiPct = (counts.poi / (total || 1)) * 100;
                  const hotelPct = (counts.hotel / (total || 1)) * 100;
                  const restPct = (counts.restaurant / (total || 1)) * 100;
                  return (
                    <div key={city}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-slate-700 font-medium">
                          {CITY_LABELS[city] || city}
                        </span>
                        <span className="text-slate-400">{total}</span>
                      </div>
                      <div
                        className="h-5 bg-slate-100 rounded overflow-hidden"
                        style={{ width: "100%" }}
                      >
                        <div
                          className="h-full flex rounded overflow-hidden"
                          style={{ width: `${totalPct}%` }}
                        >
                          <div
                            className="bg-sky-400 h-full"
                            style={{ width: `${poiPct}%` }}
                            title={`景点: ${counts.poi}`}
                          />
                          <div
                            className="bg-indigo-400 h-full"
                            style={{ width: `${hotelPct}%` }}
                            title={`酒店: ${counts.hotel}`}
                          />
                          <div
                            className="bg-emerald-400 h-full"
                            style={{ width: `${restPct}%` }}
                            title={`餐厅: ${counts.restaurant}`}
                          />
                        </div>
                      </div>
                    </div>
                  );
                })}
                <div className="flex gap-4 pt-2 text-xs text-slate-500">
                  <span><span className="inline-block w-3 h-3 bg-sky-400 rounded-sm mr-1" />景点</span>
                  <span><span className="inline-block w-3 h-3 bg-indigo-400 rounded-sm mr-1" />酒店</span>
                  <span><span className="inline-block w-3 h-3 bg-emerald-400 rounded-sm mr-1" />餐厅</span>
                </div>
              </div>
            )}
          </div>

          {/* Trust 分布 CSS 圆环 */}
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <h2 className="text-sm font-semibold text-slate-800 mb-4">信任状态分布</h2>
            <div className="flex items-center gap-6">
              {/* 圆环 */}
              <div className="relative flex-shrink-0" style={{ width: 120, height: 120 }}>
                <div
                  className="rounded-full"
                  style={{
                    width: 120,
                    height: 120,
                    background: `conic-gradient(${conicGradient})`,
                  }}
                />
                {/* 中间镂空 */}
                <div
                  className="absolute inset-0 m-auto rounded-full bg-white flex items-center justify-center"
                  style={{ width: 70, height: 70, top: "50%", left: "50%", transform: "translate(-50%, -50%)", position: "absolute" }}
                >
                  <span className="text-xs font-semibold text-slate-700">{trustTotal}</span>
                </div>
              </div>

              {/* 图例 */}
              <div className="space-y-2 flex-1">
                {trustSegments.map(({ key, cnt, pct }) => (
                  <div key={key} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span
                        className={`inline-block w-2.5 h-2.5 rounded-full ${TRUST_LABELS[key]?.color || "bg-slate-300"}`}
                      />
                      <span className="text-slate-600">{TRUST_LABELS[key]?.label || key}</span>
                    </div>
                    <span className="text-slate-500">
                      {cnt} <span className="text-slate-300">({pct.toFixed(0)}%)</span>
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* 活动簇小卡 */}
            <div className="mt-4 pt-4 border-t border-slate-100 grid grid-cols-3 gap-3">
              <div className="text-center">
                <p className="text-lg font-bold text-slate-900">{stats.cluster_stats.total}</p>
                <p className="text-xs text-slate-400">总簇数</p>
              </div>
              <div className="text-center">
                <p className="text-lg font-bold text-emerald-600">{stats.cluster_stats.active}</p>
                <p className="text-xs text-slate-400">已启用</p>
              </div>
              <div className="text-center">
                <p className="text-lg font-bold text-indigo-600">{stats.cluster_stats.with_anchors}</p>
                <p className="text-xs text-slate-400">有 Anchor</p>
              </div>
            </div>
          </div>
        </div>

        {/* 最近新增实体 */}
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h2 className="text-sm font-semibold text-slate-800 mb-4">最近新增实体</h2>
          {stats.recent_entities.length === 0 ? (
            <p className="text-xs text-slate-400 py-4 text-center">暂无数据</p>
          ) : (
            <div className="space-y-2">
              {stats.recent_entities.map((e) => (
                <div
                  key={e.entity_id}
                  className="flex items-center gap-4 px-4 py-2.5 bg-slate-50 rounded-lg text-sm"
                >
                  <span className="text-slate-700 font-medium flex-1 min-w-0 truncate">
                    {e.name_zh}
                  </span>
                  <span className="text-xs text-slate-400 w-12 text-center">
                    {ENTITY_TYPE_LABELS[e.entity_type] || e.entity_type}
                  </span>
                  <span className="text-xs text-slate-400 w-16 text-center">
                    {CITY_LABELS[e.city_code] || e.city_code}
                  </span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full w-16 text-center ${
                      TRUST_STATUS_STYLE[e.trust_status] || "bg-slate-100 text-slate-600"
                    }`}
                  >
                    {TRUST_LABELS[e.trust_status]?.label || e.trust_status}
                  </span>
                  <span className="text-xs text-slate-400 hidden md:block">
                    {e.created_at ? new Date(e.created_at).toLocaleDateString("zh-CN") : "—"}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
