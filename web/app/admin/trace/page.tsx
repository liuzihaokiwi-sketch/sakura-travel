"use client";

import { useEffect, useState } from "react";

// ── 类型 ──────────────────────────────────────────────────────────────────────

interface GenerationRun {
  run_id: string;
  submission_id?: string;
  order_id?: string;
  mode: string;
  status: "running" | "completed" | "failed" | "cancelled";
  generation_mode?: string;
  engine_version?: string;
  model_id?: string;
  total_steps?: number;
  completed_steps?: number;
  fragment_hit_count?: number;
  rule_pass_count?: number;
  rule_fail_count?: number;
  llm_call_count?: number;
  total_tokens?: number;
  total_latency_ms?: number;
  quality_score?: number;
  error_message?: string;
  started_at: string;
  completed_at?: string;
}

// ── 工具 ──────────────────────────────────────────────────────────────────────

const API = process.env.NEXT_PUBLIC_API_URL ?? "";

function fmtMs(ms?: number) {
  if (!ms) return "—";
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function fmtTokens(n?: number) {
  if (!n) return "—";
  return n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n);
}

function statusBadge(s: string) {
  const map: Record<string, string> = {
    completed: "bg-green-100 text-green-700",
    running:   "bg-blue-100  text-blue-700 animate-pulse",
    failed:    "bg-red-100   text-red-700",
    cancelled: "bg-gray-100  text-gray-500",
  };
  return map[s] ?? "bg-gray-100 text-gray-500";
}

// ── 摘要卡 ────────────────────────────────────────────────────────────────────

function SummaryCard({ label, value, sub, color = "indigo" }: {
  label: string; value: string | number; sub?: string; color?: string;
}) {
  const colorMap: Record<string, string> = {
    indigo: "text-indigo-600", green: "text-green-600",
    red: "text-red-500", amber: "text-amber-600", gray: "text-gray-500",
  };
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 flex flex-col gap-1">
      <span className="text-xs text-gray-400 uppercase tracking-wide">{label}</span>
      <span className={`text-2xl font-bold ${colorMap[color] ?? colorMap.indigo}`}>{value}</span>
      {sub && <span className="text-xs text-gray-400">{sub}</span>}
    </div>
  );
}

// ── 时间线步骤 ────────────────────────────────────────────────────────────────

interface Step {
  step_name: string;
  step_order: number;
  status: string;
  latency_ms?: number;
  error?: string;
  started_at?: string;
}

const STEP_LABELS: Record<string, string> = {
  normalize_profile:    "用户画像标准化",
  fragment_search:      "片段库搜索",
  hard_rule_check:      "硬规则检查",
  soft_rule_scoring:    "软规则评分",
  skeleton_assembly:    "骨架装配",
  overview_generation:  "总纲生成",
  day1_generation:      "Day 1 生成",
  day2_generation:      "Day 2 生成",
  day3_generation:      "Day 3 生成",
  day4_generation:      "Day 4 生成",
  static_block_inject:  "静态块注入",
  quality_gate:         "质量门控",
};

function StepTimeline({ steps }: { steps: Step[] }) {
  return (
    <div className="relative">
      {/* 垂直轨道线 */}
      <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />
      <div className="space-y-2">
        {steps.sort((a, b) => a.step_order - b.step_order).map((s) => {
          const ok = s.status === "completed";
          const fail = s.status === "failed";
          return (
            <div key={s.step_order} className="flex items-start gap-3 relative pl-10">
              {/* 圆点 */}
              <div className={[
                "absolute left-2.5 top-3 w-3 h-3 rounded-full border-2 z-10",
                ok   ? "bg-green-400 border-green-500" :
                fail ? "bg-red-400 border-red-500" :
                       "bg-gray-300 border-gray-400",
              ].join(" ")} />

              <div className={[
                "flex-1 rounded-lg px-3 py-2 text-sm border",
                fail ? "border-red-200 bg-red-50" : "border-gray-100 bg-gray-50",
              ].join(" ")}>
                <div className="flex items-center justify-between">
                  <span className="font-medium text-gray-800">
                    {STEP_LABELS[s.step_name] ?? s.step_name}
                  </span>
                  <span className="text-xs text-gray-400 tabular-nums">
                    {fmtMs(s.latency_ms)}
                  </span>
                </div>
                {s.error && (
                  <p className="text-xs text-red-600 mt-1">{s.error}</p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── 主页面 ────────────────────────────────────────────────────────────────────

export default function TraceListPage() {
  const [runs, setRuns] = useState<GenerationRun[]>([]);
  const [selected, setSelected] = useState<GenerationRun | null>(null);
  const [steps, setSteps] = useState<Step[]>([]);
  const [loading, setLoading] = useState(true);
  const [stepLoading, setStepLoading] = useState(false);

  useEffect(() => {
    fetch(`${API}/admin/generation-runs?limit=50`)
      .then((r) => r.ok ? r.json() : { runs: _MOCK_RUNS })
      .then((d) => setRuns(d.runs ?? d))
      .catch(() => setRuns(_MOCK_RUNS))
      .finally(() => setLoading(false));
  }, []);

  const selectRun = async (run: GenerationRun) => {
    setSelected(run);
    setStepLoading(true);
    try {
      const r = await fetch(`${API}/admin/generation-runs/${run.run_id}/steps`);
      const d = r.ok ? await r.json() : { steps: _MOCK_STEPS };
      setSteps(d.steps ?? _MOCK_STEPS);
    } catch {
      setSteps(_MOCK_STEPS);
    } finally {
      setStepLoading(false);
    }
  };

  // 汇总统计
  const totalRuns = runs.length;
  const completed = runs.filter((r) => r.status === "completed").length;
  const failed    = runs.filter((r) => r.status === "failed").length;
  const avgScore  = runs.filter((r) => r.quality_score).length
    ? (runs.reduce((s, r) => s + (r.quality_score ?? 0), 0) /
       runs.filter((r) => r.quality_score).length).toFixed(1)
    : "—";
  const avgLatency = runs.filter((r) => r.total_latency_ms).length
    ? Math.round(runs.reduce((s, r) => s + (r.total_latency_ms ?? 0), 0) /
      runs.filter((r) => r.total_latency_ms).length)
    : 0;
  const totalTokens = runs.reduce((s, r) => s + (r.total_tokens ?? 0), 0);
  const fragHits    = runs.reduce((s, r) => s + (r.fragment_hit_count ?? 0), 0);
  const ruleViolations = runs.reduce((s, r) => s + (r.rule_fail_count ?? 0), 0);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* 标题 */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">生成追踪</h1>
        <p className="text-sm text-gray-500 mt-1">
          查看每次攻略生成的全链路运行状态、片段命中和规则评估
        </p>
      </div>

      {/* 8 张摘要卡 */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <SummaryCard label="总运行次数" value={totalRuns} color="indigo" />
        <SummaryCard label="成功" value={completed} color="green" />
        <SummaryCard label="失败" value={failed} color={failed > 0 ? "red" : "gray"} />
        <SummaryCard label="平均质量分" value={avgScore} sub="/100" color="indigo" />
        <SummaryCard label="平均延迟" value={fmtMs(avgLatency)} color="amber" />
        <SummaryCard label="总 Token 消耗" value={fmtTokens(totalTokens)} color="indigo" />
        <SummaryCard label="片段命中总计" value={fragHits} color="green" />
        <SummaryCard label="规则违规总计" value={ruleViolations}
          color={ruleViolations > 0 ? "red" : "gray"} />
      </div>

      {/* 主体：左列表 + 右时间线 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 运行列表 */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
            <h2 className="font-semibold text-gray-800">运行记录</h2>
            <span className="text-xs text-gray-400">{totalRuns} 条</span>
          </div>
          {loading ? (
            <div className="p-8 text-center text-gray-400 text-sm">加载中…</div>
          ) : (
            <div className="divide-y divide-gray-50 max-h-[520px] overflow-y-auto">
              {runs.map((run) => (
                <button
                  key={run.run_id}
                  onClick={() => selectRun(run)}
                  className={[
                    "w-full px-4 py-3 text-left hover:bg-gray-50 transition-colors",
                    selected?.run_id === run.run_id ? "bg-indigo-50" : "",
                  ].join(" ")}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {run.submission_id ?? run.run_id.slice(0, 8) + "…"}
                      </p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        {run.generation_mode ?? "full"} · {run.model_id ?? "—"}
                      </p>
                    </div>
                    <div className="flex flex-col items-end gap-1 flex-shrink-0">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusBadge(run.status)}`}>
                        {run.status}
                      </span>
                      {run.quality_score && (
                        <span className="text-xs text-gray-500">
                          {run.quality_score.toFixed(0)}/100
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-3 mt-1.5 text-xs text-gray-400">
                    <span>⏱ {fmtMs(run.total_latency_ms)}</span>
                    <span>🧩 {run.fragment_hit_count ?? 0} 片段</span>
                    <span>🪙 {fmtTokens(run.total_tokens)}</span>
                    {(run.rule_fail_count ?? 0) > 0 && (
                      <span className="text-red-500">⚠ {run.rule_fail_count} 违规</span>
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* 时间线详情 */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-100">
            <h2 className="font-semibold text-gray-800">
              {selected ? `${selected.submission_id ?? selected.run_id.slice(0, 8)} — 步骤时间线` : "选择运行查看时间线"}
            </h2>
            {selected && (
              <a
                href={`/admin/trace/${selected.run_id}`}
                className="text-xs text-indigo-500 hover:underline mt-0.5 block"
              >
                查看完整图谱 →
              </a>
            )}
          </div>
          <div className="p-4 max-h-[520px] overflow-y-auto">
            {!selected ? (
              <p className="text-sm text-gray-400 text-center py-12">← 点击左侧运行记录</p>
            ) : stepLoading ? (
              <p className="text-sm text-gray-400 text-center py-12">加载中…</p>
            ) : (
              <StepTimeline steps={steps} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Mock 数据（API 不可用时使用）────────────────────────────────────────────────

const _MOCK_RUNS: GenerationRun[] = [
  {
    run_id: "11111111-0000-0000-0000-000000000001",
    submission_id: "SUB-MOCK-001",
    mode: "full",
    status: "completed",
    generation_mode: "fragment_first",
    engine_version: "v1.2.0",
    model_id: "claude-sonnet-4-5",
    total_steps: 12,
    completed_steps: 12,
    fragment_hit_count: 3,
    rule_pass_count: 6,
    rule_fail_count: 0,
    llm_call_count: 4,
    total_tokens: 18420,
    total_latency_ms: 16100,
    quality_score: 83.5,
    started_at: "2026-03-22T04:00:00Z",
    completed_at: "2026-03-22T04:00:16Z",
  },
];

const _MOCK_STEPS: Step[] = [
  { step_name: "normalize_profile",   step_order: 1,  status: "completed", latency_ms: 120  },
  { step_name: "fragment_search",     step_order: 2,  status: "completed", latency_ms: 480  },
  { step_name: "hard_rule_check",     step_order: 3,  status: "completed", latency_ms: 95   },
  { step_name: "soft_rule_scoring",   step_order: 4,  status: "completed", latency_ms: 210  },
  { step_name: "skeleton_assembly",   step_order: 5,  status: "completed", latency_ms: 55   },
  { step_name: "overview_generation", step_order: 6,  status: "completed", latency_ms: 3200 },
  { step_name: "day1_generation",     step_order: 7,  status: "completed", latency_ms: 2800 },
  { step_name: "day2_generation",     step_order: 8,  status: "completed", latency_ms: 2950 },
  { step_name: "day3_generation",     step_order: 9,  status: "completed", latency_ms: 3100 },
  { step_name: "day4_generation",     step_order: 10, status: "completed", latency_ms: 2700 },
  { step_name: "static_block_inject", step_order: 11, status: "completed", latency_ms: 80   },
  { step_name: "quality_gate",        step_order: 12, status: "completed", latency_ms: 310  },
];
