"use client";

import { useEffect, useState } from "react";

/**
 * 评测仪表板 (E4) — /admin/evals
 *
 * 功能：
 * 1. Run 列表 — 每次评测运行的汇总
 * 2. 分层分数热力图 — input/planning/delivery/experience 四层
 * 3. 用例通过率趋势
 * 4. 失败归因分布
 */

interface EvalRun {
  run_id: string;
  suite: string;
  started_at: string;
  finished_at: string;
  total_cases: number;
  passed: number;
  warned: number;
  failed: number;
  errored: number;
  avg_score: number;
  layer_avg_scores: Record<string, number>;
  results: EvalCaseResult[];
}

interface EvalCaseResult {
  case_id: string;
  overall_score: number;
  severity: string;
  layer_scores: Record<string, number>;
  failure_attribution: string | null;
  duration_ms: number;
  grader_count: number;
}

const SEVERITY_COLORS: Record<string, string> = {
  pass: "bg-emerald-100 text-emerald-800",
  warning: "bg-amber-100 text-amber-800",
  fail: "bg-red-100 text-red-800",
  error: "bg-gray-100 text-gray-800",
};

const LAYER_LABELS: Record<string, string> = {
  input: "输入理解",
  planning: "规划",
  delivery: "交付",
  experience: "体验",
};

function ScoreBar({ score, max = 100 }: { score: number; max?: number }) {
  const pct = Math.min((score / max) * 100, 100);
  const color =
    pct >= 70 ? "bg-emerald-500" : pct >= 50 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono text-gray-600">{score.toFixed(1)}</span>
    </div>
  );
}

function SeverityBadge({ severity }: { severity: string }) {
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${SEVERITY_COLORS[severity] || "bg-gray-100"}`}>
      {severity}
    </span>
  );
}

export default function EvalsPage() {
  const [runs, setRuns] = useState<EvalRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<EvalRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [compareRunId, setCompareRunId] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/admin/evals/runs")
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => {
        setRuns(data);
        if (data.length > 0) setSelectedRun(data[0]);
      })
      .catch(() => setRuns([]))
      .finally(() => setLoading(false));
  }, []);

  const compareRun = compareRunId ? runs.find((r) => r.run_id === compareRunId) : null;

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">🧪 评测飞轮</h1>
          <p className="text-sm text-gray-500 mt-0.5">4 层评测 · 5 类用例 · 回归对比</p>
        </div>
        <div className="flex gap-2">
          <a href="/admin" className="px-3 py-1.5 text-sm bg-gray-100 rounded-lg hover:bg-gray-200">
            ← 回管理台
          </a>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {loading ? (
          <div className="text-center py-20 text-gray-400">加载中...</div>
        ) : runs.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="grid grid-cols-12 gap-6">
            {/* 左侧：Run 列表 */}
            <div className="col-span-3 space-y-2">
              <h2 className="text-sm font-semibold text-gray-500 mb-2">运行记录</h2>
              {runs.map((run) => (
                <button
                  key={run.run_id}
                  onClick={() => setSelectedRun(run)}
                  className={`w-full text-left p-3 rounded-lg border transition ${
                    selectedRun?.run_id === run.run_id
                      ? "border-blue-500 bg-blue-50"
                      : "border-gray-200 bg-white hover:border-gray-300"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-mono">{run.run_id}</span>
                    <span className="text-xs text-gray-400">{run.suite}</span>
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <ScoreBar score={run.avg_score} />
                  </div>
                  <div className="flex gap-1 mt-1.5">
                    {run.passed > 0 && <span className="text-xs text-emerald-600">✓{run.passed}</span>}
                    {run.warned > 0 && <span className="text-xs text-amber-600">⚠{run.warned}</span>}
                    {run.failed > 0 && <span className="text-xs text-red-600">✗{run.failed}</span>}
                    {run.errored > 0 && <span className="text-xs text-gray-500">E{run.errored}</span>}
                  </div>
                </button>
              ))}
            </div>

            {/* 右侧：详情 */}
            <div className="col-span-9 space-y-6">
              {selectedRun && (
                <>
                  {/* 摘要卡片 */}
                  <SummaryCards run={selectedRun} />

                  {/* 分层分数热力图 */}
                  <LayerHeatmap run={selectedRun} compareRun={compareRun} />

                  {/* 对比选择 */}
                  {runs.length > 1 && (
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-500">对比运行：</span>
                      <select
                        className="text-sm border rounded px-2 py-1"
                        value={compareRunId || ""}
                        onChange={(e) => setCompareRunId(e.target.value || null)}
                      >
                        <option value="">不对比</option>
                        {runs
                          .filter((r) => r.run_id !== selectedRun.run_id)
                          .map((r) => (
                            <option key={r.run_id} value={r.run_id}>
                              {r.run_id} ({r.suite}) — {r.avg_score.toFixed(1)}分
                            </option>
                          ))}
                      </select>
                    </div>
                  )}

                  {/* 用例列表 */}
                  <CaseTable results={selectedRun.results} compareResults={compareRun?.results} />

                  {/* 失败归因 */}
                  <FailureAttribution results={selectedRun.results} />
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="text-center py-20">
      <p className="text-6xl mb-4">🧪</p>
      <h2 className="text-xl font-bold text-gray-700">还没有评测记录</h2>
      <p className="text-gray-400 mt-2 max-w-md mx-auto">
        运行 <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm">python -m app.evals.cli run --suite regression</code> 开始首次评测
      </p>
    </div>
  );
}

function SummaryCards({ run }: { run: EvalRun }) {
  const cards = [
    { label: "总分", value: `${run.avg_score.toFixed(1)}`, color: run.avg_score >= 70 ? "text-emerald-600" : run.avg_score >= 50 ? "text-amber-600" : "text-red-600" },
    { label: "用例数", value: `${run.total_cases}`, color: "text-gray-700" },
    { label: "通过", value: `${run.passed}`, color: "text-emerald-600" },
    { label: "警告", value: `${run.warned}`, color: "text-amber-600" },
    { label: "失败", value: `${run.failed}`, color: "text-red-600" },
    { label: "错误", value: `${run.errored}`, color: "text-gray-500" },
  ];
  return (
    <div className="grid grid-cols-6 gap-3">
      {cards.map((c) => (
        <div key={c.label} className="bg-white rounded-lg border p-3 text-center">
          <p className="text-xs text-gray-400">{c.label}</p>
          <p className={`text-2xl font-bold ${c.color}`}>{c.value}</p>
        </div>
      ))}
    </div>
  );
}

function LayerHeatmap({ run, compareRun }: { run: EvalRun; compareRun?: EvalRun | null }) {
  const layers = ["input", "planning", "delivery", "experience"];
  return (
    <div className="bg-white rounded-lg border p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">分层评分</h3>
      <div className="grid grid-cols-4 gap-3">
        {layers.map((layer) => {
          const score = run.layer_avg_scores[layer] ?? 0;
          const cmpScore = compareRun?.layer_avg_scores[layer];
          const delta = cmpScore != null ? score - cmpScore : null;
          const bg = score >= 70 ? "bg-emerald-50 border-emerald-200" : score >= 50 ? "bg-amber-50 border-amber-200" : "bg-red-50 border-red-200";
          return (
            <div key={layer} className={`rounded-lg border p-3 ${bg}`}>
              <p className="text-xs text-gray-500">{LAYER_LABELS[layer] || layer}</p>
              <p className="text-2xl font-bold mt-1">{score.toFixed(1)}</p>
              {delta != null && (
                <p className={`text-xs mt-1 ${delta >= 0 ? "text-emerald-600" : "text-red-600"}`}>
                  {delta >= 0 ? "↑" : "↓"} {Math.abs(delta).toFixed(1)} vs {compareRun!.run_id}
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function CaseTable({ results, compareResults }: { results: EvalCaseResult[]; compareResults?: EvalCaseResult[] }) {
  const compareMap = new Map(compareResults?.map((r) => [r.case_id, r]) || []);
  return (
    <div className="bg-white rounded-lg border overflow-hidden">
      <h3 className="text-sm font-semibold text-gray-700 p-4 pb-2">用例详情</h3>
      <table className="w-full text-sm">
        <thead className="bg-gray-50 text-gray-500">
          <tr>
            <th className="text-left px-4 py-2">Case ID</th>
            <th className="text-center px-2 py-2">状态</th>
            <th className="text-center px-2 py-2">总分</th>
            {["input", "planning", "delivery", "experience"].map((l) => (
              <th key={l} className="text-center px-2 py-2">{LAYER_LABELS[l]?.slice(0, 2)}</th>
            ))}
            <th className="text-center px-2 py-2">归因</th>
            <th className="text-right px-4 py-2">耗时</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {results.map((r) => {
            const cmp = compareMap.get(r.case_id);
            return (
              <tr key={r.case_id} className="hover:bg-gray-50">
                <td className="px-4 py-2 font-mono text-xs">{r.case_id}</td>
                <td className="text-center px-2 py-2"><SeverityBadge severity={r.severity} /></td>
                <td className="text-center px-2 py-2">
                  <span className="font-bold">{r.overall_score.toFixed(1)}</span>
                  {cmp && (
                    <span className={`text-xs ml-1 ${r.overall_score >= cmp.overall_score ? "text-emerald-500" : "text-red-500"}`}>
                      ({r.overall_score >= cmp.overall_score ? "+" : ""}{(r.overall_score - cmp.overall_score).toFixed(1)})
                    </span>
                  )}
                </td>
                {["input", "planning", "delivery", "experience"].map((l) => (
                  <td key={l} className="text-center px-2 py-2 text-xs">
                    {r.layer_scores[l]?.toFixed(0) ?? "—"}
                  </td>
                ))}
                <td className="text-center px-2 py-2 text-xs text-gray-500">
                  {r.failure_attribution || "—"}
                </td>
                <td className="text-right px-4 py-2 text-xs text-gray-400">
                  {r.duration_ms}ms
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function FailureAttribution({ results }: { results: EvalCaseResult[] }) {
  const failed = results.filter((r) => r.failure_attribution);
  if (failed.length === 0) return null;

  const counts: Record<string, number> = {};
  failed.forEach((r) => {
    const key = r.failure_attribution!;
    counts[key] = (counts[key] || 0) + 1;
  });
  const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  const total = failed.length;

  return (
    <div className="bg-white rounded-lg border p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">失败归因分布</h3>
      <div className="space-y-2">
        {sorted.map(([layer, count]) => (
          <div key={layer} className="flex items-center gap-3">
            <span className="text-sm text-gray-600 w-24">{LAYER_LABELS[layer] || layer}</span>
            <div className="flex-1 h-4 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-red-400 rounded-full"
                style={{ width: `${(count / total) * 100}%` }}
              />
            </div>
            <span className="text-sm font-mono text-gray-500 w-16 text-right">
              {count} ({((count / total) * 100).toFixed(0)}%)
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
