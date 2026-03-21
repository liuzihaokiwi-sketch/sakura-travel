"""add generation trace 7 tables (L25)

Revision ID: 20260322_040000
Revises: 20260322_030000
Create Date: 2026-03-22 04:00:00.000000

Tables:
  generation_runs         — 一整次生成任务
  generation_step_runs    — 每一步生成节点
  fragment_hit_logs       — 片段命中日志
  rule_evaluation_logs    — 规则评估日志
  prompt_run_logs         — AI 调用日志
  review_action_logs      — 人工审核/修改日志
  export_logs             — 渲染导出日志
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260322_040000"
down_revision = "20260322_030000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. generation_runs ────────────────────────────────────────────────────
    op.create_table(
        "generation_runs",
        sa.Column("run_id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("submission_id", sa.String(50), nullable=True),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("mode", sa.String(20), nullable=False, server_default="full",
                  comment="preview / full / revise / replay"),
        sa.Column("status", sa.String(20), nullable=False, server_default="running",
                  comment="running / completed / failed / cancelled"),
        sa.Column("generation_mode", sa.String(20), nullable=True,
                  comment="fragment_first / ai_first / hybrid"),
        # 版本快照（8 个版本号字段）
        sa.Column("engine_version", sa.String(20), nullable=True),
        sa.Column("fragment_lib_version", sa.String(20), nullable=True),
        sa.Column("soft_rules_version", sa.String(20), nullable=True),
        sa.Column("hard_rules_version", sa.String(20), nullable=True),
        sa.Column("template_version", sa.String(20), nullable=True),
        sa.Column("prompt_version", sa.String(20), nullable=True),
        sa.Column("grader_version", sa.String(20), nullable=True),
        sa.Column("model_id", sa.String(50), nullable=True),
        # 统计
        sa.Column("total_steps", sa.Integer(), nullable=True),
        sa.Column("completed_steps", sa.Integer(), nullable=True),
        sa.Column("fragment_hit_count", sa.Integer(), nullable=True),
        sa.Column("rule_pass_count", sa.Integer(), nullable=True),
        sa.Column("rule_fail_count", sa.Integer(), nullable=True),
        sa.Column("llm_call_count", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("total_latency_ms", sa.Integer(), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"),
                  nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extra", postgresql.JSONB(), nullable=True),
    )
    op.create_index("ix_gen_runs_order", "generation_runs", ["order_id"])
    op.create_index("ix_gen_runs_submission", "generation_runs", ["submission_id"])
    op.create_index("ix_gen_runs_status", "generation_runs", ["status"])
    op.create_index("ix_gen_runs_started", "generation_runs", ["started_at"])

    # ── 2. generation_step_runs ───────────────────────────────────────────────
    op.create_table(
        "generation_step_runs",
        sa.Column("step_run_id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("run_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("generation_runs.run_id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("step_name", sa.String(50), nullable=False,
                  comment="如 normalize_profile / fragment_search / hard_rule_check"),
        sa.Column("step_order", sa.SmallInteger(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("input_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("output_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_step_runs_run", "generation_step_runs", ["run_id"])
    op.create_index("ix_step_runs_name", "generation_step_runs", ["step_name"])

    # ── 3. fragment_hit_logs ──────────────────────────────────────────────────
    op.create_table(
        "fragment_hit_logs",
        sa.Column("hit_id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("run_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("generation_runs.run_id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("fragment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("fragment_slug", sa.String(100), nullable=True),
        sa.Column("hit_tier", sa.String(5), nullable=True,
                  comment="A / B / C / D"),
        sa.Column("similarity_score", sa.Float(), nullable=True),
        sa.Column("used_in_output", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("rejection_reason", sa.String(200), nullable=True),
        sa.Column("logged_at", sa.DateTime(timezone=True), server_default=sa.text("now()"),
                  nullable=False),
    )
    op.create_index("ix_frag_hit_run", "fragment_hit_logs", ["run_id"])
    op.create_index("ix_frag_hit_tier", "fragment_hit_logs", ["hit_tier"])

    # ── 4. rule_evaluation_logs ───────────────────────────────────────────────
    op.create_table(
        "rule_evaluation_logs",
        sa.Column("eval_id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("run_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("generation_runs.run_id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("rule_id", sa.String(50), nullable=False),
        sa.Column("rule_type", sa.String(10), nullable=False,
                  comment="hard / soft"),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True,
                  comment="软规则得分 0-100"),
        sa.Column("detail", postgresql.JSONB(), nullable=True),
        sa.Column("logged_at", sa.DateTime(timezone=True), server_default=sa.text("now()"),
                  nullable=False),
    )
    op.create_index("ix_rule_eval_run", "rule_evaluation_logs", ["run_id"])
    op.create_index("ix_rule_eval_rule", "rule_evaluation_logs", ["rule_id"])
    op.create_index("ix_rule_eval_type", "rule_evaluation_logs", ["rule_type"])

    # ── 5. prompt_run_logs ────────────────────────────────────────────────────
    op.create_table(
        "prompt_run_logs",
        sa.Column("prompt_run_id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("run_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("generation_runs.run_id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("step_run_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("generation_step_runs.step_run_id", ondelete="SET NULL"),
                  nullable=True),
        sa.Column("model_id", sa.String(50), nullable=True),
        sa.Column("prompt_template_id", sa.String(100), nullable=True),
        sa.Column("prompt_version", sa.String(20), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("finish_reason", sa.String(20), nullable=True),
        sa.Column("cost_usd", sa.Float(), nullable=True),
        sa.Column("prompt_snapshot", postgresql.JSONB(), nullable=True,
                  comment="prompt messages（截断到 2000 chars）"),
        sa.Column("response_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("called_at", sa.DateTime(timezone=True), server_default=sa.text("now()"),
                  nullable=False),
    )
    op.create_index("ix_prompt_run_run", "prompt_run_logs", ["run_id"])
    op.create_index("ix_prompt_run_model", "prompt_run_logs", ["model_id"])

    # ── 6. review_action_logs ─────────────────────────────────────────────────
    op.create_table(
        "review_action_logs",
        sa.Column("action_id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("run_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("generation_runs.run_id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("reviewer_id", sa.String(50), nullable=True),
        sa.Column("action_type", sa.String(30), nullable=False,
                  comment="approve / reject / edit_section / add_comment / request_regen"),
        sa.Column("target_section", sa.String(100), nullable=True),
        sa.Column("before_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("after_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("acted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"),
                  nullable=False),
    )
    op.create_index("ix_review_action_run", "review_action_logs", ["run_id"])

    # ── 7. export_logs ────────────────────────────────────────────────────────
    op.create_table(
        "export_logs",
        sa.Column("export_id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("run_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("generation_runs.run_id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("format", sa.String(10), nullable=False,
                  comment="pdf / html / json"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("file_url", sa.Text(), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("render_latency_ms", sa.Integer(), nullable=True),
        sa.Column("watermarked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("exported_at", sa.DateTime(timezone=True), server_default=sa.text("now()"),
                  nullable=False),
    )
    op.create_index("ix_export_run", "export_logs", ["run_id"])
    op.create_index("ix_export_format", "export_logs", ["format"])


def downgrade() -> None:
    op.drop_table("export_logs")
    op.drop_table("review_action_logs")
    op.drop_table("prompt_run_logs")
    op.drop_table("rule_evaluation_logs")
    op.drop_table("fragment_hit_logs")
    op.drop_table("generation_step_runs")
    op.drop_table("generation_runs")
