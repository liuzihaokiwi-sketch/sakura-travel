"""
Trace 对接评测 — E9

从 generation_runs / generation_step_runs / fragment_hit_logs / rule_evaluation_logs
日志表中读取 trace 数据，自动构建 grader 输入，无需重新运行生成。

支持：
  - 从 run_id 构建完整评测上下文
  - 自动填充 fragment_hit_result（片段命中情况）
  - 自动填充 trace_summary（规则通过/失败统计）
  - 调用 FailureAnalyzer 生成标准化归因

使用方式：
  adapter = TraceEvalAdapter(db_session)
  ctx = await adapter.build_eval_context("run-id-xxx")
  analyzer = FailureAnalyzer()
  attribution = analyzer.analyze(case_id=ctx["case_id"], **ctx["analyzer_kwargs"])
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.evals.failure_analyzer import FailureAnalyzer

logger = logging.getLogger(__name__)


class TraceEvalAdapter:
    """
    从已完成的 generation_run trace 中，提取 grader 所需的输入上下文。
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def build_eval_context(self, run_id: str) -> dict[str, Any]:
        """
        读取指定 run_id 的所有 trace 记录，组装评测上下文。

        Returns
        -------
        dict with keys:
            run_id, case_id, trace_summary, fragment_hit_result,
            grader_outputs (partial), analyzer_kwargs
        """
        # ── 1. generation_runs 主记录 ─────────────────────────────────────────
        run_row = await self._fetch_run(run_id)
        if not run_row:
            raise ValueError(f"GenerationRun {run_id} not found")

        # ── 2. fragment_hit_logs ──────────────────────────────────────────────
        hit_rows = await self._fetch_fragment_hits(run_id)
        must_hit   = [r["fragment_slug"] for r in hit_rows if r["used_in_output"]]
        not_hit    = [r["fragment_slug"] for r in hit_rows if not r["used_in_output"]]
        fragment_hit_result = {
            "must_hit":     must_hit,
            "actually_hit": must_hit,
            "missed":       not_hit,
            "hit_tiers":    {r["fragment_slug"]: r["hit_tier"] for r in hit_rows},
        }

        # ── 3. rule_evaluation_logs ───────────────────────────────────────────
        rule_rows = await self._fetch_rule_evals(run_id)
        rule_pass  = sum(1 for r in rule_rows if r["passed"])
        rule_fail  = sum(1 for r in rule_rows if not r["passed"])
        hard_violations = [r["rule_id"] for r in rule_rows
                           if not r["passed"] and r["rule_type"] == "hard"]
        soft_low = [r["rule_id"] for r in rule_rows
                    if not r["passed"] and r["rule_type"] == "soft" and (r["score"] or 100) < 65]

        trace_summary = {
            "run_id":           run_id,
            "status":           run_row["status"],
            "generation_mode":  run_row.get("generation_mode"),
            "fragment_hit_count": run_row.get("fragment_hit_count", len(must_hit)),
            "rule_pass_count":  rule_pass,
            "rule_fail_count":  rule_fail,
            "hard_violations":  hard_violations,
            "soft_low_scores":  soft_low,
            "total_tokens":     run_row.get("total_tokens"),
            "total_latency_ms": run_row.get("total_latency_ms"),
            "quality_score":    run_row.get("quality_score"),
        }

        # ── 4. grader_outputs（从 trace 推断部分维度）─────────────────────────
        # 注：结构 grader / 用户价值 grader 需要实际文本，这里提供规划层推断
        planning_score = self._estimate_planning_score(rule_rows, hit_rows)
        grader_outputs = {
            "planning": {
                "score": planning_score,
                "max_score": 100,
                "passed": planning_score >= 65,
                "dimension_scores": [
                    {"id": "P3", "score": 0 if hard_violations else 20, "max": 20,
                     "issues": [f"硬规则违规: {v}" for v in hard_violations[:2]]},
                    {"id": "P4", "score": max(0, 25 - len(soft_low) * 8), "max": 25,
                     "issues": [f"软规则偏低: {s}" for s in soft_low[:2]]},
                    {"id": "P5", "score": min(30, len(must_hit) * 10), "max": 30,
                     "issues": [] if must_hit else ["无片段命中"]},
                ],
                "issues": hard_violations + soft_low,
            }
        }

        return {
            "run_id":               run_id,
            "case_id":              run_row.get("submission_id", run_id[:8]),
            "trace_summary":        trace_summary,
            "fragment_hit_result":  fragment_hit_result,
            "grader_outputs":       grader_outputs,
            "analyzer_kwargs": {
                "grader_outputs":       grader_outputs,
                "fragment_hit_result":  fragment_hit_result,
                "trace_summary":        trace_summary,
            },
        }

    async def run_attribution(self, run_id: str) -> dict[str, Any]:
        """
        一步完成：读取 trace → 构建上下文 → 运行失败归因。

        Returns
        -------
        dict: attribution.to_dict() + eval_context metadata
        """
        ctx = await self.build_eval_context(run_id)
        analyzer = FailureAnalyzer()
        attribution = analyzer.analyze(
            case_id=ctx["case_id"],
            **ctx["analyzer_kwargs"],
        )
        return {
            "run_id": run_id,
            "attribution": attribution.to_dict(),
            "trace_summary": ctx["trace_summary"],
        }

    # ── 内部 DB 查询 ───────────────────────────────────────────────────────────

    async def _fetch_run(self, run_id: str) -> Optional[dict]:
        result = await self.db.execute(text("""
            SELECT run_id, submission_id, status, generation_mode,
                   fragment_hit_count, rule_pass_count, rule_fail_count,
                   total_tokens, total_latency_ms, quality_score
            FROM generation_runs WHERE run_id = :id
        """), {"id": run_id})
        row = result.mappings().fetchone()
        return dict(row) if row else None

    async def _fetch_fragment_hits(self, run_id: str) -> list[dict]:
        result = await self.db.execute(text("""
            SELECT fragment_slug, hit_tier, similarity_score, used_in_output, rejection_reason
            FROM fragment_hit_logs WHERE run_id = :id
        """), {"id": run_id})
        return [dict(r) for r in result.mappings().fetchall()]

    async def _fetch_rule_evals(self, run_id: str) -> list[dict]:
        result = await self.db.execute(text("""
            SELECT rule_id, rule_type, passed, score
            FROM rule_evaluation_logs WHERE run_id = :id
        """), {"id": run_id})
        return [dict(r) for r in result.mappings().fetchall()]

    @staticmethod
    def _estimate_planning_score(rule_rows: list[dict], hit_rows: list[dict]) -> int:
        """根据规则评估 + 片段命中估算规划层得分（满分 100）"""
        score = 100
        for r in rule_rows:
            if not r["passed"]:
                score -= 20 if r["rule_type"] == "hard" else 8
        # 无片段命中扣分
        if not any(r["used_in_output"] for r in hit_rows):
            score -= 20
        return max(0, min(100, score))
