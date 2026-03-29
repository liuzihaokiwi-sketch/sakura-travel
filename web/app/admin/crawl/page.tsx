"use client";

import { useState, useEffect, useRef } from "react";

interface CrawlJob {
  job_id: string;
  city_code: string;
  status: "queued" | "running" | "done" | "error";
  created_at: string | null;
  started_at: string | null;
  finished_at: string | null;
  result: Record<string, unknown> | null;
  error: string | null;
}

const CITIES = [
  { value: "tokyo", label: "东京" },
  { value: "osaka", label: "大阪" },
  { value: "kyoto", label: "京都" },
  { value: "sapporo", label: "札幌" },
  { value: "fukuoka", label: "福冈" },
  { value: "naha", label: "冲绳（那霸）" },
  { value: "hakone", label: "箱根" },
  { value: "nikko", label: "日光" },
  { value: "hiroshima", label: "广岛" },
  { value: "nara", label: "奈良" },
];

const STATUS_STYLE: Record<string, string> = {
  queued: "bg-slate-100 text-slate-600",
  running: "bg-blue-100 text-blue-700 animate-pulse",
  done: "bg-emerald-100 text-emerald-700",
  error: "bg-red-100 text-red-700",
};

const STATUS_LABEL: Record<string, string> = {
  queued: "排队中",
  running: "运行中",
  done: "已完成",
  error: "出错",
};

export default function CrawlPage() {
  const [city, setCity] = useState("tokyo");
  const [types, setTypes] = useState({
    sync_pois: true,
    sync_restaurants: true,
    sync_hotels: true,
  });
  const [forceAi, setForceAi] = useState(false);
  const [counts, setCounts] = useState({ poi_count: 5, restaurant_count: 5, hotel_count: 4 });
  const [submitting, setSubmitting] = useState(false);
  const [jobs, setJobs] = useState<CrawlJob[]>([]);
  const [lastJobId, setLastJobId] = useState<string | null>(null);
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  const loadJobs = async () => {
    try {
      const res = await fetch("/api/admin/crawl");
      const data = await res.json();
      setJobs(data.jobs || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadJobs();
  }, []);

  // 如果有运行中的任务，每 3 秒轮询
  useEffect(() => {
    const hasRunning = jobs.some((j) => j.status === "queued" || j.status === "running");
    if (hasRunning) {
      pollRef.current = setTimeout(() => loadJobs(), 3000);
    }
    return () => { if (pollRef.current) clearTimeout(pollRef.current); };
  }, [jobs]);

  const handleSubmit = async () => {
    if (!types.sync_pois && !types.sync_restaurants && !types.sync_hotels) {
      alert("请至少选择一个抓取类型");
      return;
    }
    setSubmitting(true);
    try {
      const res = await fetch("/api/admin/crawl", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          city_code: city,
          ...types,
          force_ai: forceAi,
          ...counts,
        }),
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setLastJobId(data.job_id);
      await loadJobs();
    } catch (e: any) {
      alert(`提交失败：${e.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const toggleType = (key: keyof typeof types) => {
    setTypes((p) => ({ ...p, [key]: !p[key] }));
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-3">
        <h1 className="text-sm font-semibold text-slate-900">数据抓取</h1>
        <p className="text-xs text-slate-400">触发城市数据采集任务</p>
      </header>

      <div className="px-6 py-6 max-w-2xl">
        {/* 表单卡片 */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 mb-6">
          <h2 className="text-sm font-semibold text-slate-800 mb-4">新建抓取任务</h2>

          {/* 城市选择 */}
          <div className="mb-4">
            <label className="text-xs text-slate-500 mb-1.5 block font-medium">目标城市</label>
            <select
              value={city}
              onChange={(e) => setCity(e.target.value)}
              className="border border-slate-200 rounded-lg px-3 py-2 text-sm w-full focus:outline-none focus:ring-1 focus:ring-indigo-400"
            >
              {CITIES.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>

          {/* 抓取类型 */}
          <div className="mb-4">
            <label className="text-xs text-slate-500 mb-2 block font-medium">抓取类型</label>
            <div className="flex flex-wrap gap-3">
              {[
                { key: "sync_pois" as const, label: "🗺️ 景点" },
                { key: "sync_hotels" as const, label: "🏨 酒店" },
                { key: "sync_restaurants" as const, label: "🍽️ 餐厅" },
              ].map(({ key, label }) => (
                <label key={key} className="flex items-center gap-2 cursor-pointer text-sm text-slate-700">
                  <input
                    type="checkbox"
                    checked={types[key]}
                    onChange={() => toggleType(key)}
                    className="accent-indigo-600"
                  />
                  {label}
                </label>
              ))}
            </div>
          </div>

          {/* 数量设置 */}
          <div className="mb-4 grid grid-cols-3 gap-3">
            <div>
              <label className="text-xs text-slate-500 mb-1 block">景点数量</label>
              <input
                type="number" min={1} max={20} value={counts.poi_count}
                onChange={(e) => setCounts((p) => ({ ...p, poi_count: Number(e.target.value) }))}
                className="border border-slate-200 rounded px-2 py-1.5 text-sm w-full focus:outline-none focus:ring-1 focus:ring-indigo-400"
              />
            </div>
            <div>
              <label className="text-xs text-slate-500 mb-1 block">酒店数量</label>
              <input
                type="number" min={1} max={20} value={counts.hotel_count}
                onChange={(e) => setCounts((p) => ({ ...p, hotel_count: Number(e.target.value) }))}
                className="border border-slate-200 rounded px-2 py-1.5 text-sm w-full focus:outline-none focus:ring-1 focus:ring-indigo-400"
              />
            </div>
            <div>
              <label className="text-xs text-slate-500 mb-1 block">餐厅数量</label>
              <input
                type="number" min={1} max={20} value={counts.restaurant_count}
                onChange={(e) => setCounts((p) => ({ ...p, restaurant_count: Number(e.target.value) }))}
                className="border border-slate-200 rounded px-2 py-1.5 text-sm w-full focus:outline-none focus:ring-1 focus:ring-indigo-400"
              />
            </div>
          </div>

          {/* 强制 AI */}
          <div className="mb-5">
            <label className="flex items-center gap-2 cursor-pointer text-sm text-slate-700">
              <input
                type="checkbox"
                checked={forceAi}
                onChange={(e) => setForceAi(e.target.checked)}
                className="accent-indigo-600"
              />
              强制使用 AI 生成（不检查网络，跳过真实爬虫）
            </label>
            <p className="text-xs text-slate-400 mt-1 ml-5">
              生产环境默认先尝试真实数据源，AI 只兜底
            </p>
          </div>

          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="w-full py-2.5 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? "提交中..." : "🚀 开始抓取"}
          </button>
        </div>

        {/* 任务列表 */}
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-800">任务记录</h2>
            <button onClick={loadJobs} className="text-xs text-indigo-600 hover:text-indigo-800">刷新</button>
          </div>

          {jobs.length === 0 ? (
            <p className="text-xs text-slate-400 py-4 text-center">暂无任务记录</p>
          ) : (
            <div className="space-y-3">
              {jobs.map((job) => (
                <div
                  key={job.job_id}
                  className={`border rounded-lg p-3 ${
                    job.job_id === lastJobId ? "border-indigo-200 bg-indigo-50" : "border-slate-100"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs text-slate-500">{job.job_id}</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_STYLE[job.status] || "bg-slate-100 text-slate-600"}`}>
                          {STATUS_LABEL[job.status] || job.status}
                        </span>
                        <span className="text-xs text-slate-600 font-medium">
                          {CITIES.find((c) => c.value === job.city_code)?.label || job.city_code}
                        </span>
                      </div>
                      <div className="text-xs text-slate-400 mt-1">
                        创建: {job.created_at ? new Date(job.created_at).toLocaleTimeString("zh-CN") : "—"}
                        {job.finished_at && ` · 完成: ${new Date(job.finished_at).toLocaleTimeString("zh-CN")}`}
                      </div>
                    </div>
                  </div>

                  {job.status === "done" && job.result && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {Object.entries(job.result).map(([k, v]) => (
                        typeof v === "number" ? (
                          <span key={k} className="text-xs bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded">
                            {k}: {v}
                          </span>
                        ) : null
                      ))}
                    </div>
                  )}

                  {job.status === "error" && job.error && (
                    <p className="mt-2 text-xs text-red-600 bg-red-50 px-2 py-1 rounded">{job.error}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
