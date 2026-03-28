import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

type TraceRun = {
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
};

const MOCK_RUNS: TraceRun[] = [
  {
    run_id: "11111111-0000-0000-0000-000000000001",
    submission_id: "SUB-MOCK-001",
    order_id: "ORDER-MOCK-001",
    mode: "full",
    status: "completed",
    generation_mode: "city_circle_main_chain",
    engine_version: "phase2",
    model_id: "gpt-5",
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

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const limitRaw = Number(searchParams.get("limit") || "50");
  const limit = Number.isFinite(limitRaw) && limitRaw > 0 ? limitRaw : 50;
  return NextResponse.json({ runs: MOCK_RUNS.slice(0, limit) });
}
