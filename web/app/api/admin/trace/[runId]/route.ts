import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const MOCK_TRACE = {
  run: {
    run_id: "11111111-0000-0000-0000-000000000001",
    order_id: "ORDER-MOCK-001",
    mode: "full",
    status: "completed",
    generation_mode: "city_circle_main_chain",
    fragment_adopted_count: 3,
    fragment_rejected_count: 1,
    ai_calls_count: 4,
    total_tokens: 18420,
    total_latency_ms: 16100,
    quality_gate_passed: true,
    review_verdict: "publish",
    risk_level: "low",
    started_at: "2026-03-22T04:00:00Z",
  },
  steps: [
    { step_run_id: "1", step_name: "normalize_profile", step_order: 1, status: "completed", latency_ms: 120, parent_step_id: null, warnings: [], errors: [] },
    { step_run_id: "2", step_name: "fragment_search", step_order: 2, status: "completed", latency_ms: 480, parent_step_id: "1", warnings: [], errors: [] },
    { step_run_id: "3", step_name: "quality_gate", step_order: 3, status: "completed", latency_ms: 310, parent_step_id: "2", warnings: [], errors: [] },
  ],
  fragment_hits: [
    {
      fragment_id: "frag-001",
      day_index: 1,
      hit_tier: "A",
      metadata_score: 0.92,
      semantic_score: 0.88,
      hard_rule_pass: true,
      soft_rule_score: 0.84,
      final_score: 0.88,
      adopted: true,
      reject_reason: null,
    },
  ],
  rule_evals: [
    {
      rule_type: "hard",
      rule_id: "requested_city_circle",
      target_type: "contract",
      target_id: "kansai_classic_circle",
      result: "pass",
      score_delta: 0,
      explanation: "explicit canonical city circle respected",
    },
  ],
  prompt_runs: [
    {
      prompt_name: "overview_generation",
      model_name: "gpt-5",
      cache_hit: false,
      input_tokens: 1200,
      output_tokens: 860,
      latency_ms: 3200,
    },
  ],
};

export async function GET(
  _req: Request,
  { params }: { params: { runId: string } },
) {
  return NextResponse.json({
    ...MOCK_TRACE,
    run: {
      ...MOCK_TRACE.run,
      run_id: params.runId,
    },
  });
}
