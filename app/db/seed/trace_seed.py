"""
生成追踪 Mock 种子数据 (L26)

插入一条完整的 trace 样例，覆盖 7 张日志表：
  generation_runs → generation_step_runs → fragment_hit_logs
  → rule_evaluation_logs → prompt_run_logs → review_action_logs → export_logs

用于前端 M10/M11 开发联调，无需真实生成运行。

运行方式：
  python -m app.db.seed.trace_seed
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, text

from app.db.session import AsyncSessionLocal

# ── 固定 UUID（幂等用）────────────────────────────────────────────────────────
RUN_ID          = uuid.UUID("11111111-0000-0000-0000-000000000001")
STEP_IDS = [
    uuid.UUID(f"22222222-0000-0000-0000-{str(i).zfill(12)}")
    for i in range(1, 13)   # 12 步
]
FRAG_HIT_IDS    = [uuid.UUID(f"33333333-0000-0000-0000-{str(i).zfill(12)}") for i in range(1, 4)]
RULE_EVAL_IDS   = [uuid.UUID(f"44444444-0000-0000-0000-{str(i).zfill(12)}") for i in range(1, 9)]
PROMPT_IDS      = [uuid.UUID(f"55555555-0000-0000-0000-{str(i).zfill(12)}") for i in range(1, 5)]
REVIEW_ID       = uuid.UUID("66666666-0000-0000-0000-000000000001")
EXPORT_ID       = uuid.UUID("77777777-0000-0000-0000-000000000001")

NOW = datetime(2026, 3, 22, 4, 0, 0, tzinfo=timezone.utc)

STEP_DEFS = [
    ("normalize_profile",    1,  120),
    ("fragment_search",      2,  480),
    ("hard_rule_check",      3,  95),
    ("soft_rule_scoring",    4,  210),
    ("skeleton_assembly",    5,  55),
    ("overview_generation",  6, 3200),
    ("day1_generation",      7, 2800),
    ("day2_generation",      8, 2950),
    ("day3_generation",      9, 3100),
    ("day4_generation",     10, 2700),
    ("static_block_inject", 11,  80),
    ("quality_gate",        12, 310),
]

FRAGMENT_HITS = [
    (FRAG_HIT_IDS[0], "tokyo_route_shinjuku_harajuku", "A", 0.94, True,  None),
    (FRAG_HIT_IDS[1], "tokyo_logistics_airport_to_city", "A", 0.91, True, None),
    (FRAG_HIT_IDS[2], "tokyo_tips_jrpass_decision", "B", 0.77, True, None),
]

RULE_EVALS = [
    # (id, rule_id, type, passed, score)
    (RULE_EVAL_IDS[0], "R001_arrival_time_consistent", "hard", True,  None),
    (RULE_EVAL_IDS[1], "R002_no_closed_day",           "hard", True,  None),
    (RULE_EVAL_IDS[2], "R003_jr_pass_coherent",        "hard", True,  None),
    (RULE_EVAL_IDS[3], "R004_budget_range",            "hard", True,  None),
    (RULE_EVAL_IDS[4], "S001_localness",               "soft", False, 62.0),
    (RULE_EVAL_IDS[5], "S002_photo_shareability",      "soft", True,  81.0),
    (RULE_EVAL_IDS[6], "S003_pace_density",            "soft", True,  75.0),
    (RULE_EVAL_IDS[7], "S004_dining_diversity",        "soft", True,  88.0),
]


async def seed_trace(session):
    # 幂等检查
    existing = await session.execute(
        text("SELECT run_id FROM generation_runs WHERE run_id = :id"),
        {"id": str(RUN_ID)},
    )
    if existing.fetchone():
        print("⏭️  trace mock 数据已存在，跳过")
        return

    # ── 1. generation_run ──────────────────────────────────────────────────────
    await session.execute(text("""
        INSERT INTO generation_runs (
            run_id, submission_id, mode, status, generation_mode,
            engine_version, fragment_lib_version, soft_rules_version,
            hard_rules_version, template_version, prompt_version,
            grader_version, model_id,
            total_steps, completed_steps,
            fragment_hit_count, rule_pass_count, rule_fail_count,
            llm_call_count, total_tokens, total_latency_ms, quality_score,
            started_at, completed_at
        ) VALUES (
            :run_id, 'SUB-MOCK-001', 'full', 'completed', 'fragment_first',
            'v1.2.0', 'v0.3.1', 'v2.1.0', 'v1.0.5', 'v0.8.2', 'v1.1.0',
            'v0.2.0', 'claude-sonnet-4-5',
            12, 12,
            3, 6, 0,
            4, 18420, 16100, 83.5,
            :started_at, :completed_at
        )
    """), {
        "run_id": str(RUN_ID),
        "started_at": NOW,
        "completed_at": NOW + timedelta(seconds=16),
    })

    # ── 2. generation_step_runs ────────────────────────────────────────────────
    t = NOW
    for step_id, (step_name, step_order, latency_ms) in zip(STEP_IDS, STEP_DEFS):
        await session.execute(text("""
            INSERT INTO generation_step_runs (
                step_run_id, run_id, step_name, step_order, status,
                latency_ms, started_at, completed_at
            ) VALUES (
                :id, :run_id, :name, :order, 'completed',
                :lat, :start, :end
            )
        """), {
            "id": str(step_id),
            "run_id": str(RUN_ID),
            "name": step_name,
            "order": step_order,
            "lat": latency_ms,
            "start": t,
            "end": t + timedelta(milliseconds=latency_ms),
        })
        t += timedelta(milliseconds=latency_ms)

    # ── 3. fragment_hit_logs ───────────────────────────────────────────────────
    for hit_id, slug, tier, score, used, reject in FRAGMENT_HITS:
        await session.execute(text("""
            INSERT INTO fragment_hit_logs (
                hit_id, run_id, fragment_slug, hit_tier,
                similarity_score, used_in_output, rejection_reason, logged_at
            ) VALUES (:id, :run_id, :slug, :tier, :score, :used, :rej, :ts)
        """), {
            "id": str(hit_id), "run_id": str(RUN_ID),
            "slug": slug, "tier": tier, "score": score,
            "used": used, "rej": reject, "ts": NOW,
        })

    # ── 4. rule_evaluation_logs ────────────────────────────────────────────────
    for eval_id, rule_id, rtype, passed, score in RULE_EVALS:
        await session.execute(text("""
            INSERT INTO rule_evaluation_logs (
                eval_id, run_id, rule_id, rule_type, passed, score, logged_at
            ) VALUES (:id, :run_id, :rule, :type, :passed, :score, :ts)
        """), {
            "id": str(eval_id), "run_id": str(RUN_ID),
            "rule": rule_id, "type": rtype,
            "passed": passed, "score": score, "ts": NOW,
        })

    # ── 5. prompt_run_logs ─────────────────────────────────────────────────────
    prompt_steps = [
        (PROMPT_IDS[0], STEP_IDS[5], "overview",       1840, 620,  3200, 0.0082),
        (PROMPT_IDS[1], STEP_IDS[6], "daily_itinerary", 2100, 980,  2800, 0.0110),
        (PROMPT_IDS[2], STEP_IDS[7], "daily_itinerary", 2100, 1020, 2950, 0.0115),
        (PROMPT_IDS[3], STEP_IDS[8], "daily_itinerary", 2050, 990,  3100, 0.0108),
    ]
    for pid, sid, tmpl, in_tok, out_tok, lat, cost in prompt_steps:
        await session.execute(text("""
            INSERT INTO prompt_run_logs (
                prompt_run_id, run_id, step_run_id, model_id,
                prompt_template_id, prompt_version,
                input_tokens, output_tokens, latency_ms,
                finish_reason, cost_usd, called_at
            ) VALUES (
                :id, :run_id, :step_id, 'claude-sonnet-4-5',
                :tmpl, 'v1.1.0',
                :in_tok, :out_tok, :lat,
                'stop', :cost, :ts
            )
        """), {
            "id": str(pid), "run_id": str(RUN_ID), "step_id": str(sid),
            "tmpl": tmpl, "in_tok": in_tok, "out_tok": out_tok,
            "lat": lat, "cost": cost, "ts": NOW,
        })

    # ── 6. review_action_logs ──────────────────────────────────────────────────
    await session.execute(text("""
        INSERT INTO review_action_logs (
            action_id, run_id, reviewer_id, action_type,
            target_section, comment, acted_at
        ) VALUES (
            :id, :run_id, 'admin-001', 'approve',
            NULL, '整体质量良好，东京首刷行程节奏合理，片段命中率高', :ts
        )
    """), {
        "id": str(REVIEW_ID), "run_id": str(RUN_ID),
        "ts": NOW + timedelta(minutes=5),
    })

    # ── 7. export_logs ─────────────────────────────────────────────────────────
    await session.execute(text("""
        INSERT INTO export_logs (
            export_id, run_id, format, status,
            file_url, file_size_bytes, render_latency_ms, watermarked, exported_at
        ) VALUES (
            :id, :run_id, 'pdf', 'completed',
            '/exports/mock-tokyo-7day.pdf', 524288, 1240, true, :ts
        )
    """), {
        "id": str(EXPORT_ID), "run_id": str(RUN_ID),
        "ts": NOW + timedelta(minutes=6),
    })

    await session.commit()
    print("✅ trace mock 种子数据插入完成")
    print(f"   run_id: {RUN_ID}")
    print(f"   步骤: 12 步 | 片段命中: 3 | 规则评估: 8 | LLM 调用: 4")


async def main():
    async with AsyncSessionLocal() as session:
        await seed_trace(session)


if __name__ == "__main__":
    asyncio.run(main())
