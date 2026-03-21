"""
维度分融合模块（Dimension Score Fusion）

将三种来源（manual / stat / ai）的维度分按优先级合并，
生成每个实体的最终 12 维度分。

优先级：manual > stat > ai
  - 如果某维度有人工 seed → 用人工 seed
  - 否则如果该维度的 source_type 是 stat 且有统计值 → 用统计值
  - 否则用 AI 估计值
  - 如果全部缺失 → 默认 5.0

同时记录每个维度的实际来源（score_sources），
用于审计、调试和后续校准。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from app.domains.ranking.soft_rules.dimensions import (
    DIMENSION_IDS,
    DIMENSION_BY_ID,
    SourceType,
)
from app.domains.ranking.soft_rules.estimators.ai_estimator import (
    DimensionEstimate,
    estimate_dimensions_by_ai,
    _default_estimates,
)
from app.domains.ranking.soft_rules.estimators.stat_estimator import (
    compute_stat_dimensions,
)

logger = logging.getLogger(__name__)


# ── 输出结构 ───────────────────────────────────────────────────────────────────

@dataclass
class FusedDimensionScore:
    """单个维度的融合后结果"""
    dimension_id: str
    score: float           # 最终分值 0-10
    source: str            # 实际来源："manual" / "stat" / "ai" / "default"
    reason: str            # 来源提供的理由
    confidence: float      # 置信度 0-1


@dataclass
class EntitySoftScores:
    """一个实体的完整 12 维度软规则分"""
    entity_id: str
    entity_type: str
    scores: dict[str, FusedDimensionScore]     # {dimension_id: FusedDimensionScore}
    score_sources: dict[str, str]              # {dimension_id: source_type} — 用于写入 DB
    score_version: str = "soft_v1.0"

    def to_dimension_scores(self) -> dict[str, float]:
        """提取纯分值字典，用于聚合计算。"""
        return {dim_id: fs.score for dim_id, fs in self.scores.items()}

    def to_db_row(self) -> dict[str, Any]:
        """转换为 entity_soft_scores 表的字段字典。"""
        row: dict[str, Any] = {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "score_version": self.score_version,
        }
        # 12 个维度列
        for dim_id, fused in self.scores.items():
            row[dim_id] = fused.score
        # JSONB 列
        row["score_sources"] = self.score_sources
        return row


# ── 融合主函数 ─────────────────────────────────────────────────────────────────

async def compute_entity_soft_scores(
    entity: dict[str, Any],
    manual_overrides: dict[str, float] | None = None,
    ai_client: Any = None,
    ai_model: str = "gpt-4o-mini",
) -> EntitySoftScores:
    """
    计算单个实体的完整 12 维度软规则分。

    融合流程：
    1. 先调用 stat_estimator 计算统计维度
    2. 再调用 ai_estimator 计算 AI 维度
    3. 把 stat 结果传给 preview_conversion_power 的派生计算
    4. 按优先级 manual > stat > ai > default 合并

    Args:
        entity: 实体数据字典（需包含 id, entity_type, name_local 等）
        manual_overrides: 人工 seed 覆盖 {dimension_id: score}
        ai_client: OpenAI AsyncClient（传 None 时 AI 维度用默认分）
        ai_model: AI 模型名

    Returns:
        EntitySoftScores 完整结果
    """
    entity_id = str(entity.get("id", "unknown"))
    entity_type = entity.get("entity_type", "poi")

    if manual_overrides is None:
        manual_overrides = {}

    # Step 1: AI 估计（覆盖所有 12 维度，作为兜底）
    ai_estimates = await estimate_dimensions_by_ai(entity, ai_client, ai_model)

    # Step 2: 统计特征计算（需要 AI 估计的部分分值来计算派生维度）
    ai_scores_for_stat = {
        dim_id: est.score for dim_id, est in ai_estimates.items()
    }
    stat_estimates = compute_stat_dimensions(entity, existing_scores=ai_scores_for_stat)

    # Step 3: 融合
    fused_scores: dict[str, FusedDimensionScore] = {}
    score_sources: dict[str, str] = {}

    for dim_id in DIMENSION_IDS:
        dim_def = DIMENSION_BY_ID[dim_id]

        # 优先级 1: 人工 seed
        if dim_id in manual_overrides:
            score = max(0.0, min(10.0, float(manual_overrides[dim_id])))
            fused_scores[dim_id] = FusedDimensionScore(
                dimension_id=dim_id,
                score=round(score, 1),
                source="manual",
                reason="人工 seed 覆盖",
                confidence=1.0,
            )
            score_sources[dim_id] = "manual"
            continue

        # 优先级 2: 统计特征（仅对 source_type=STAT 的维度，或者 stat 确实算出了值）
        if dim_id in stat_estimates:
            stat_est = stat_estimates[dim_id]
            # 如果该维度推荐用 stat，或者 stat 置信度高于 AI
            if dim_def.source_type == SourceType.STAT or stat_est.confidence > 0.75:
                fused_scores[dim_id] = FusedDimensionScore(
                    dimension_id=dim_id,
                    score=stat_est.score,
                    source="stat",
                    reason=stat_est.reason,
                    confidence=stat_est.confidence,
                )
                score_sources[dim_id] = "stat"
                continue

        # 优先级 3: AI 估计
        if dim_id in ai_estimates:
            ai_est = ai_estimates[dim_id]
            if ai_est.confidence > 0:
                fused_scores[dim_id] = FusedDimensionScore(
                    dimension_id=dim_id,
                    score=ai_est.score,
                    source="ai",
                    reason=ai_est.reason,
                    confidence=ai_est.confidence,
                )
                score_sources[dim_id] = "ai"
                continue

        # 优先级 4: 默认分
        fused_scores[dim_id] = FusedDimensionScore(
            dimension_id=dim_id,
            score=5.0,
            source="default",
            reason="无可用数据源",
            confidence=0.0,
        )
        score_sources[dim_id] = "default"

    result = EntitySoftScores(
        entity_id=entity_id,
        entity_type=entity_type,
        scores=fused_scores,
        score_sources=score_sources,
    )

    logger.debug(
        "Entity %s soft scores fused: manual=%d, stat=%d, ai=%d, default=%d",
        entity_id,
        sum(1 for s in score_sources.values() if s == "manual"),
        sum(1 for s in score_sources.values() if s == "stat"),
        sum(1 for s in score_sources.values() if s == "ai"),
        sum(1 for s in score_sources.values() if s == "default"),
    )

    return result


# ── 批量融合 ───────────────────────────────────────────────────────────────────

async def batch_compute_soft_scores(
    entities: list[dict[str, Any]],
    manual_overrides_map: dict[str, dict[str, float]] | None = None,
    ai_client: Any = None,
    ai_model: str = "gpt-4o-mini",
    concurrency: int = 5,
) -> list[EntitySoftScores]:
    """
    批量计算多个实体的软规则分。

    Args:
        entities: 实体数据字典列表
        manual_overrides_map: {entity_id: {dimension_id: score}} 人工覆盖映射
        ai_client: OpenAI AsyncClient
        ai_model: 模型名
        concurrency: 最大并发数

    Returns:
        EntitySoftScores 列表
    """
    import asyncio

    if manual_overrides_map is None:
        manual_overrides_map = {}

    semaphore = asyncio.Semaphore(concurrency)
    results: list[EntitySoftScores] = []

    async def _compute_one(entity: dict[str, Any]) -> EntitySoftScores:
        entity_id = str(entity.get("id", "unknown"))
        manual = manual_overrides_map.get(entity_id, {})
        async with semaphore:
            return await compute_entity_soft_scores(
                entity,
                manual_overrides=manual,
                ai_client=ai_client,
                ai_model=ai_model,
            )

    tasks = [_compute_one(e) for e in entities]
    completed = await asyncio.gather(*tasks, return_exceptions=True)

    for i, result in enumerate(completed):
        if isinstance(result, Exception):
            entity_id = str(entities[i].get("id", "unknown"))
            logger.error("Failed to compute soft scores for %s: %s", entity_id, result)
            # 创建全默认分的 fallback
            fused = {
                dim_id: FusedDimensionScore(
                    dimension_id=dim_id, score=5.0,
                    source="default", reason=f"Error: {result}",
                    confidence=0.0,
                )
                for dim_id in DIMENSION_IDS
            }
            results.append(EntitySoftScores(
                entity_id=entity_id,
                entity_type=entities[i].get("entity_type", "poi"),
                scores=fused,
                score_sources={d: "default" for d in DIMENSION_IDS},
            ))
        else:
            results.append(result)

    logger.info(
        "Batch soft score computation complete: %d entities, %d succeeded",
        len(entities),
        sum(1 for r in completed if not isinstance(r, Exception)),
    )

    return results
