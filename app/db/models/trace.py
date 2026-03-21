"""
Generation Trace Models — 生成追踪 7 张日志表 (H15a)

对照 docs/admin_generation_observability_spec.md §五：
  1. generation_run      — 一整次生成任务
  2. generation_step_run  — 每一步生成节点
  3. fragment_hit_log    — 片段命中日志
  4. rule_evaluation_log — 规则评估日志
  5. prompt_run_log      — AI 调用日志
  6. review_action_log   — 人工审核/修改日志
  7. export_log          — 渲染导出日志
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger, Boolean, DateTime, Float, ForeignKey,
    Index, Integer, SmallInteger, String, Text, func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


# ── 1. generation_run ─────────────────────────────────────────────────────────

class GenerationRun(Base):
    """一整次生成任务"""
    __tablename__ = "generation_runs"

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    order_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    submission_id: Mapped[Optional[str]] = mapped_column(String(50))
    plan_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    mode: Mapped[str] = mapped_column(
        String(20), nullable=False, default="full",
        comment="preview / full / revise / replay"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="running",
        comment="running / completed / failed / cancelled"
    )
    triggered_by: Mapped[str] = mapped_column(
        String(20), nullable=False, default="system",
        comment="system / ops / replay / user"
    )

    # 画像快照
    profile_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB)
    generation_mode: Mapped[Optional[str]] = mapped_column(
        String(20), comment="fragment_first / template_only / hybrid"
    )

    # 统计
    total_steps: Mapped[int] = mapped_column(SmallInteger, default=0)
    fragment_adopted_count: Mapped[int] = mapped_column(SmallInteger, default=0)
    fragment_rejected_count: Mapped[int] = mapped_column(SmallInteger, default=0)
    ai_calls_count: Mapped[int] = mapped_column(SmallInteger, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_latency_ms: Mapped[int] = mapped_column(Integer, default=0)

    # 质量
    quality_gate_passed: Mapped[Optional[bool]] = mapped_column(Boolean)
    review_verdict: Mapped[Optional[str]] = mapped_column(
        String(20), comment="publish / rewrite / human"
    )
    risk_level: Mapped[Optional[str]] = mapped_column(
        String(10), comment="low / medium / high"
    )

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    steps: Mapped[list["GenerationStepRun"]] = relationship(back_populates="run", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_gen_runs_order", "order_id"),
        Index("ix_gen_runs_submission", "submission_id"),
        Index("ix_gen_runs_status", "status"),
    )


# ── 2. generation_step_run ────────────────────────────────────────────────────

class GenerationStepRun(Base):
    """每一步生成节点"""
    __tablename__ = "generation_step_runs"

    step_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("generation_runs.run_id", ondelete="CASCADE"), nullable=False,
    )
    parent_step_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    step_name: Mapped[str] = mapped_column(String(50), nullable=False)
    step_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="running",
        comment="running / completed / failed / skipped"
    )

    input_summary: Mapped[Optional[dict]] = mapped_column(JSONB)
    output_summary: Mapped[Optional[dict]] = mapped_column(JSONB)
    warnings: Mapped[Optional[list]] = mapped_column(JSONB)
    errors: Mapped[Optional[list]] = mapped_column(JSONB)

    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    run: Mapped["GenerationRun"] = relationship(back_populates="steps")

    __table_args__ = (
        Index("ix_step_runs_run", "run_id"),
        Index("ix_step_runs_name", "step_name"),
    )


# ── 3. fragment_hit_log ───────────────────────────────────────────────────────

class FragmentHitLog(Base):
    """片段命中日志"""
    __tablename__ = "fragment_hit_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("generation_runs.run_id", ondelete="CASCADE"), nullable=False,
    )
    day_index: Mapped[Optional[int]] = mapped_column(SmallInteger)
    fragment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    hit_tier: Mapped[str] = mapped_column(String(1), comment="A / B / C / D")
    metadata_score: Mapped[float] = mapped_column(Float, default=0)
    semantic_score: Mapped[float] = mapped_column(Float, default=0)
    hard_rule_pass: Mapped[bool] = mapped_column(Boolean, default=True)
    soft_rule_score: Mapped[float] = mapped_column(Float, default=0)
    final_score: Mapped[float] = mapped_column(Float, default=0)
    adopted: Mapped[bool] = mapped_column(Boolean, default=False)
    reject_reason: Mapped[Optional[str]] = mapped_column(String(200))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_frag_hit_run", "run_id"),
        Index("ix_frag_hit_fragment", "fragment_id"),
    )


# ── 4. rule_evaluation_log ────────────────────────────────────────────────────

class RuleEvaluationLog(Base):
    """规则评估日志"""
    __tablename__ = "rule_evaluation_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("generation_runs.run_id", ondelete="CASCADE"), nullable=False,
    )
    rule_type: Mapped[str] = mapped_column(String(10), comment="hard / soft")
    rule_id: Mapped[str] = mapped_column(String(50), nullable=False)
    target_type: Mapped[str] = mapped_column(String(20), comment="fragment / entity / day / plan")
    target_id: Mapped[Optional[str]] = mapped_column(String(50))

    result: Mapped[str] = mapped_column(String(20), comment="pass / fail / na")
    score_delta: Mapped[Optional[float]] = mapped_column(Float)
    explanation: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("ix_rule_eval_run", "run_id"),)


# ── 5. prompt_run_log ─────────────────────────────────────────────────────────

class PromptRunLog(Base):
    """AI 调用日志"""
    __tablename__ = "prompt_run_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("generation_runs.run_id", ondelete="CASCADE"), nullable=False,
    )
    step_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    prompt_name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[Optional[str]] = mapped_column(String(20))
    model_name: Mapped[str] = mapped_column(String(50), nullable=False)
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False)

    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[Optional[float]] = mapped_column(Float)

    output_summary: Mapped[Optional[dict]] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_prompt_run_run", "run_id"),
        Index("ix_prompt_run_model", "model_name"),
    )


# ── 6. review_action_log ──────────────────────────────────────────────────────

class ReviewActionLog(Base):
    """人工审核/修改日志"""
    __tablename__ = "review_action_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("generation_runs.run_id", ondelete="CASCADE"), nullable=False,
    )
    reviewer: Mapped[str] = mapped_column(String(100), nullable=False)
    action_type: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="approve / reject / edit_day / replace_entity / add_note / rerun"
    )
    target_day: Mapped[Optional[int]] = mapped_column(SmallInteger)
    target_block_id: Mapped[Optional[str]] = mapped_column(String(100))
    before_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB)
    after_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB)
    note: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("ix_review_action_run", "run_id"),)


# ── 7. export_log ─────────────────────────────────────────────────────────────

class ExportLog(Base):
    """渲染导出日志"""
    __tablename__ = "export_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("generation_runs.run_id", ondelete="CASCADE"), nullable=False,
    )
    export_type: Mapped[str] = mapped_column(String(10), comment="pdf / h5 / preview")
    version: Mapped[int] = mapped_column(SmallInteger, default=1)

    page_count: Mapped[Optional[int]] = mapped_column(SmallInteger)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    asset_url: Mapped[Optional[str]] = mapped_column(String(500))
    watermark_applied: Mapped[bool] = mapped_column(Boolean, default=False)

    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("ix_export_log_run", "run_id"),)
