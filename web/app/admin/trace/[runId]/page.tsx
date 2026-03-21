"use client";

import { useEffect, useState } from "react";

/**
 * 生成追踪中心 (H15b) — /admin/trace/[runId]
 *
 * 6 个视图中的核心 2 个：
 * 1. DAG Graph View — 生成步骤图谱
 * 2. Fragments & Rules — 片段命中/硬规则过滤/软规则重排
 */

interface TraceData {
  run: GenerationRun;
  steps: StepRun[];
  fragment_hits: FragmentHit[];
  rule_evals: RuleEval[];
  prompt_runs: PromptRun[];
}

interface GenerationRun {
  run_id: string;
  order_id: string;
  mode: string;
  status: string;
  generation_mode: string;
  fragment_adopted_count: number;
  fragment_rejected_count: number;
  ai_calls_count: number;
  total_tokens: number;
  total_latency_ms: number;
  quality_gate_passed: boolean;
  review_verdict: string;
  risk_level: string;
  started_at: string;
}

interface StepRun {
  step_run_id: string;
  step_name: string;
  step_order: number;
  status: string;
  latency_ms: number;
  parent_step_id: string | null;
  warnings: string[];
  errors: string[];
}

interface FragmentHit {
  fragment_id: string;
  day_index: number;
  hit_tier: string;
  metadata_score: number;
  semantic_score: number;
  hard_rule_pass: boolean;
  soft_rule_score: number;
  final_score: number;
  adopted: boolean;
  reject_reason: string | null;
}

interface RuleEval {
  rule_type: string;
  rule_id: string;
  target_type: string;
  target_id: string;
  result: string;
  score_delta: number;
  explanation: string;
}

interface PromptRun {
  prompt_name: string;
  model_name: string;
  cache_hit: boolean;
  input_tokens: number;
  output_tokens: number;
  latency_ms: number;
}

type TabView = "graph" | "fragments" | "rules";

const STEP_STATUS_COLORS: Record<string, string> = {
  completed: "bg-emerald-500",
  running: "bg-blue-500 animate-pulse",
  failed: "bg-red-500",
  skipped: "bg-gray-300",
};

const TIER_COLORS: Record<string, string> = {
  A: "bg-emerald-100 text-emerald-800 border-emerald-300",
  B: "bg-blue-100 text-blue-800 border-blue-300",
  C: "bg-amber-100 text-amber-800 border-amber-300",
  D: "bg-red-100 text-red-800 border-red-300",
};

export default function TracePage({ params }: { params: { runId: string } }) {
  const [data, setData] = useState<TraceData | null>(null);
  const [tab, setTab] = useState<TabView>("graph");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/admin/trace/${params.runId}`)
      .then((r) => (r.ok ? r.json() : null))
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [params.runId]);

  if (loading) return <div className="p-10 text-center text-gray-400">加载中...</div>;
  if (!data) return <div className="p-10 text-center text-red-400">追踪数据不存在</div>;

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold">🔍 生成追踪 · {data.run.run_id.slice(0, 8)}</h1>
            <div className="flex gap-3 mt-1 text-xs text-gray-500">
              <span>模式: <b>{data.run.generation_mode || data.run.mode}</b></span>
              <span>片段: <b className="text-emerald-600">{data.run.fragment_adopted_count}</b>/{data.run.fragment_adopted_count + data.run.fragment_rejected_count}</span>
              <span>AI: <b>{data.run.ai_calls_count}</b> 次 · {data.run.total_tokens} tokens</span>
              <span>耗时: <b>{data.run.total_latency_ms}ms</b></span>
              <span className={`px-1.5 py-0.5 rounded ${data.run.risk_level === "high" ? "bg-red-100 text-red-700" : data.run.risk_level === "medium" ? "bg-amber-100 text-amber-700" : "bg-emerald-100 text-emerald-700"}`}>
                风险: {data.run.risk_level || "—"}
              </span>
            </div>
          </div>
          <a href="/admin" className="px-3 py-1.5 text-sm bg-gray-100 rounded-lg hover:bg-gray-200">← 回管理台</a>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mt-4">
          {(["graph", "fragments", "rules"] as TabView[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 text-sm rounded-t-lg transition ${
                tab === t ? "bg-white border border-b-0 font-medium" : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {{ graph: "📊 生成图谱", fragments: "🧩 片段命中", rules: "📏 规则评估" }[t]}
            </button>
          ))}
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {tab === "graph" && <GraphView steps={data.steps} prompts={data.prompt_runs} />}
        {tab === "fragments" && <FragmentsView hits={data.fragment_hits} />}
        {tab === "rules" && <RulesView evals={data.rule_evals} />}
      </div>
    </div>
  );
}

/* ── Tab 1: DAG Graph View ─────────────────────────────────────────────── */

function GraphView({ steps, prompts }: { steps: StepRun[]; prompts: PromptRun[] }) {
  const sorted = [...steps].sort((a, b) => a.step_order - b.step_order);

  return (
    <div className="space-y-4">
      {/* Step Timeline */}
      <div className="bg-white rounded-lg border p-4">
        <h3 className="text-sm font-semibold mb-3">生成步骤（{sorted.length} 步）</h3>
        <div className="relative">
          {sorted.map((step, i) => (
            <div key={step.step_run_id} className="flex items-start gap-3 mb-3">
              {/* Status dot + connector */}
              <div className="flex flex-col items-center">
                <div className={`w-3 h-3 rounded-full ${STEP_STATUS_COLORS[step.status] || "bg-gray-300"}`} />
                {i < sorted.length - 1 && <div className="w-0.5 h-8 bg-gray-200" />}
              </div>
              {/* Step info */}
              <div className="flex-1 -mt-0.5">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{step.step_name}</span>
                  <span className="text-xs text-gray-400">{step.latency_ms}ms</span>
                  {step.status === "failed" && <span className="text-xs text-red-500">⚠ 失败</span>}
                </div>
                {step.warnings && step.warnings.length > 0 && (
                  <div className="text-xs text-amber-600 mt-0.5">⚠ {step.warnings.join(", ")}</div>
                )}
                {step.errors && step.errors.length > 0 && (
                  <div className="text-xs text-red-600 mt-0.5">✗ {step.errors.join(", ")}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* AI Calls Summary */}
      <div className="bg-white rounded-lg border p-4">
        <h3 className="text-sm font-semibold mb-3">AI 调用（{prompts.length} 次）</h3>
        <table className="w-full text-sm">
          <thead className="text-gray-500 text-xs">
            <tr>
              <th className="text-left py-1">Prompt</th>
              <th className="text-left py-1">Model</th>
              <th className="text-center py-1">Cache</th>
              <th className="text-right py-1">Input</th>
              <th className="text-right py-1">Output</th>
              <th className="text-right py-1">耗时</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {prompts.map((p, i) => (
              <tr key={i} className="hover:bg-gray-50">
                <td className="py-1.5 font-mono text-xs">{p.prompt_name}</td>
                <td className="py-1.5 text-xs">{p.model_name}</td>
                <td className="py-1.5 text-center">{p.cache_hit ? "✓" : "—"}</td>
                <td className="py-1.5 text-right text-xs text-gray-500">{p.input_tokens}</td>
                <td className="py-1.5 text-right text-xs text-gray-500">{p.output_tokens}</td>
                <td className="py-1.5 text-right text-xs">{p.latency_ms}ms</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ── Tab 2: Fragments View ─────────────────────────────────────────────── */

function FragmentsView({ hits }: { hits: FragmentHit[] }) {
  const adopted = hits.filter((h) => h.adopted);
  const rejected = hits.filter((h) => !h.adopted);

  return (
    <div className="space-y-4">
      {/* Adopted */}
      <div className="bg-white rounded-lg border p-4">
        <h3 className="text-sm font-semibold mb-3 text-emerald-700">✅ 已采纳 ({adopted.length})</h3>
        <div className="space-y-2">
          {adopted.map((h) => (
            <FragmentCard key={h.fragment_id} hit={h} />
          ))}
          {adopted.length === 0 && <p className="text-sm text-gray-400">无采纳片段</p>}
        </div>
      </div>

      {/* Rejected */}
      <div className="bg-white rounded-lg border p-4">
        <h3 className="text-sm font-semibold mb-3 text-red-600">✗ 被拒 ({rejected.length})</h3>
        <div className="space-y-2">
          {rejected.map((h) => (
            <FragmentCard key={h.fragment_id} hit={h} />
          ))}
          {rejected.length === 0 && <p className="text-sm text-gray-400">无被拒片段</p>}
        </div>
      </div>
    </div>
  );
}

function FragmentCard({ hit }: { hit: FragmentHit }) {
  return (
    <div className={`flex items-center gap-3 p-2 rounded-lg border ${TIER_COLORS[hit.hit_tier] || "bg-gray-50 border-gray-200"}`}>
      <span className="text-lg font-bold w-8 text-center">{hit.hit_tier}</span>
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs">{hit.fragment_id.slice(0, 12)}</span>
          <span className="text-xs text-gray-500">Day {hit.day_index}</span>
        </div>
        <div className="flex gap-3 mt-0.5 text-xs text-gray-500">
          <span>meta: {(hit.metadata_score * 100).toFixed(0)}%</span>
          <span>sem: {(hit.semantic_score * 100).toFixed(0)}%</span>
          <span>soft: {(hit.soft_rule_score * 100).toFixed(0)}%</span>
          <span className="font-medium">final: {(hit.final_score * 100).toFixed(0)}%</span>
          {!hit.hard_rule_pass && <span className="text-red-500">硬规则拦截</span>}
          {hit.reject_reason && <span className="text-red-500">{hit.reject_reason}</span>}
        </div>
      </div>
    </div>
  );
}

/* ── Tab 3: Rules View ─────────────────────────────────────────────────── */

function RulesView({ evals }: { evals: RuleEval[] }) {
  const hard = evals.filter((e) => e.rule_type === "hard");
  const soft = evals.filter((e) => e.rule_type === "soft");

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-lg border p-4">
        <h3 className="text-sm font-semibold mb-3">🛡️ 硬规则 ({hard.length})</h3>
        <RuleTable rules={hard} />
      </div>
      <div className="bg-white rounded-lg border p-4">
        <h3 className="text-sm font-semibold mb-3">📊 软规则 ({soft.length})</h3>
        <RuleTable rules={soft} />
      </div>
    </div>
  );
}

function RuleTable({ rules }: { rules: RuleEval[] }) {
  if (rules.length === 0) return <p className="text-sm text-gray-400">无记录</p>;
  return (
    <table className="w-full text-sm">
      <thead className="text-gray-500 text-xs">
        <tr>
          <th className="text-left py-1">规则</th>
          <th className="text-left py-1">目标</th>
          <th className="text-center py-1">结果</th>
          <th className="text-right py-1">分数变化</th>
          <th className="text-left py-1">说明</th>
        </tr>
      </thead>
      <tbody className="divide-y">
        {rules.map((r, i) => (
          <tr key={i} className="hover:bg-gray-50">
            <td className="py-1.5 font-mono text-xs">{r.rule_id}</td>
            <td className="py-1.5 text-xs">{r.target_type}: {r.target_id?.slice(0, 8) || "—"}</td>
            <td className="py-1.5 text-center">
              <span className={`px-1.5 py-0.5 rounded text-xs ${r.result === "pass" ? "bg-emerald-100 text-emerald-700" : r.result === "fail" ? "bg-red-100 text-red-700" : "bg-gray-100"}`}>
                {r.result}
              </span>
            </td>
            <td className={`py-1.5 text-right text-xs ${(r.score_delta || 0) > 0 ? "text-emerald-600" : (r.score_delta || 0) < 0 ? "text-red-600" : ""}`}>
              {r.score_delta ? (r.score_delta > 0 ? "+" : "") + r.score_delta.toFixed(2) : "—"}
            </td>
            <td className="py-1.5 text-xs text-gray-500 max-w-xs truncate">{r.explanation || "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
