"""
AI 估计器（AI Estimator）

使用 GPT-4o-mini 批量评估实体的软规则维度分。
每次调用评估一个实体的多个维度，返回 0-10 分 + 一句话理由。

设计原则：
  1. 一次 prompt 评估所有 12 维度（减少 API 调用次数）
  2. 输出强制 JSON 格式（用 response_format）
  3. prompt 中包含 calculation_hint 作为评估标准
  4. 实体信息只传核心字段（控制 token < 2K）
  5. 失败时返回默认分 5.0（中间值），不中断管线
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from app.domains.ranking.soft_rules.dimensions import (
    SOFT_RULE_DIMENSIONS,
    DIMENSION_IDS,
    SoftRuleDimension,
)

logger = logging.getLogger(__name__)


# ── 数据结构 ───────────────────────────────────────────────────────────────────

@dataclass
class DimensionEstimate:
    """单个维度的 AI 估计结果"""
    dimension_id: str
    score: float           # 0-10
    reason: str            # 一句话理由
    confidence: float      # AI 自评置信度 0-1（保留字段，v1 不使用）


# ── Prompt 模板 ────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """你是一个日本旅行产品的资深评分专家。你需要从"用户体验感受"角度为旅行实体（景点/餐厅/酒店）打分。

评分规则：
- 每个维度打 0-10 分（可用小数，如 7.5）
- 0 分 = 完全不符合 / 不适用
- 5 分 = 中等 / 一般
- 10 分 = 极致优秀
- 你的评分应基于该实体的客观属性和通常游客的体验感受
- 不要给所有维度都打中间分，要有区分度

输出格式要求：
返回一个 JSON 对象，key 是维度 ID，value 是 {"score": 数字, "reason": "一句话理由"}
不要输出任何 JSON 之外的内容。"""


def _build_entity_context(entity: dict[str, Any]) -> str:
    """
    从实体数据中提取 AI 评估需要的核心上下文。
    控制在 ~300 tokens 以内。
    """
    parts = []

    # 基本信息
    name = entity.get("name_local") or entity.get("name") or "未知"
    name_zh = entity.get("name_zh") or ""
    entity_type = entity.get("entity_type", "poi")
    city = entity.get("city_code", "")
    area = entity.get("area_name", "")

    parts.append(f"名称：{name}")
    if name_zh:
        parts.append(f"中文名：{name_zh}")
    parts.append(f"类型：{entity_type}")
    if city:
        parts.append(f"城市：{city}")
    if area:
        parts.append(f"区域：{area}")

    # 评分信号
    google_rating = entity.get("google_rating")
    if google_rating:
        parts.append(f"Google 评分：{google_rating}/5")

    review_count = entity.get("google_review_count")
    if review_count:
        parts.append(f"评论数：{review_count}")

    tabelog = entity.get("tabelog_score")
    if tabelog:
        parts.append(f"Tabelog 评分：{tabelog}/5")

    # 分类标签
    tags = entity.get("tags") or entity.get("types") or []
    if tags:
        tag_str = ", ".join(tags[:8])  # 最多 8 个标签
        parts.append(f"标签：{tag_str}")

    # 价格
    price_level = entity.get("price_level")
    if price_level:
        parts.append(f"价格等级：{price_level}")

    # 营业信息
    has_hours = entity.get("opening_hours_json") is not None
    parts.append(f"营业时间信息：{'有' if has_hours else '无'}")

    # 描述（截断到 100 字）
    desc = entity.get("description") or entity.get("editorial_note") or ""
    if desc:
        desc = desc[:100]
        parts.append(f"简介：{desc}")

    # 位置特征
    indoor = entity.get("is_indoor")
    if indoor is not None:
        parts.append(f"室内/室外：{'室内' if indoor else '室外'}")

    return "\n".join(parts)


def _build_dimension_criteria() -> str:
    """
    构建维度评估标准说明，包含每个维度的 calculation_hint。
    """
    lines = []
    for dim in SOFT_RULE_DIMENSIONS:
        lines.append(
            f"### {dim.id}（{dim.name_cn}）\n"
            f"说明：{dim.description}\n"
            f"评估标准：{dim.calculation_hint}\n"
        )
    return "\n".join(lines)


def _build_user_prompt(entity_context: str, dimension_criteria: str) -> str:
    """构建完整的 user prompt"""
    return f"""请为以下旅行实体的 12 个软规则维度打分。

## 实体信息
{entity_context}

## 评估维度及标准
{dimension_criteria}

请直接输出 JSON，格式如下（所有 12 个维度都要评）：
{{
  "emotional_value": {{"score": 7.5, "reason": "..."}},
  "shareability": {{"score": 8.0, "reason": "..."}},
  ...
}}"""


# ── 主函数 ─────────────────────────────────────────────────────────────────────

async def estimate_dimensions_by_ai(
    entity: dict[str, Any],
    ai_client: Any = None,
    model: str = "gpt-4o-mini",
) -> dict[str, DimensionEstimate]:
    """
    使用 AI 估计实体的 12 个软规则维度分。

    Args:
        entity: 实体数据字典（从 ORM 转化，包含 name_local/entity_type/google_rating 等字段）
        ai_client: OpenAI AsyncClient 实例（传 None 时返回默认分）
        model: 使用的模型名（默认 gpt-4o-mini）

    Returns:
        {dimension_id: DimensionEstimate} 字典

    Notes:
        - 如果 AI 调用失败，所有维度返回默认分 5.0
        - 如果某个维度解析失败，该维度返回默认分 5.0
        - 预计 token 消耗：~1500 input + ~500 output ≈ 2K tokens/实体
    """
    # Fallback：无 AI client 时返回默认分
    if ai_client is None:
        return _default_estimates()

    entity_context = _build_entity_context(entity)
    dimension_criteria = _build_dimension_criteria()
    user_prompt = _build_user_prompt(entity_context, dimension_criteria)

    try:
        response = await ai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,  # 低温度，提高一致性
            max_tokens=1000,
        )

        content = response.choices[0].message.content
        return _parse_ai_response(content)

    except Exception as e:
        logger.warning(
            "AI estimation failed for entity %s: %s",
            entity.get("id", "unknown"),
            str(e),
        )
        return _default_estimates()


def _parse_ai_response(content: str) -> dict[str, DimensionEstimate]:
    """
    解析 AI 返回的 JSON，提取每个维度的 score 和 reason。
    对解析失败的维度使用默认分 5.0。
    """
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        logger.warning("AI response is not valid JSON, using defaults")
        return _default_estimates()

    estimates: dict[str, DimensionEstimate] = {}

    for dim_id in DIMENSION_IDS:
        dim_data = data.get(dim_id)

        if isinstance(dim_data, dict):
            score = dim_data.get("score", 5.0)
            reason = dim_data.get("reason", "")

            # 校验分值范围
            try:
                score = float(score)
                score = max(0.0, min(10.0, score))
            except (TypeError, ValueError):
                score = 5.0

            estimates[dim_id] = DimensionEstimate(
                dimension_id=dim_id,
                score=round(score, 1),
                reason=str(reason)[:200],  # 截断过长的理由
                confidence=0.7,  # v1 固定置信度
            )
        elif isinstance(dim_data, (int, float)):
            # 简化格式：只给了分数
            score = max(0.0, min(10.0, float(dim_data)))
            estimates[dim_id] = DimensionEstimate(
                dimension_id=dim_id,
                score=round(score, 1),
                reason="",
                confidence=0.7,
            )
        else:
            estimates[dim_id] = DimensionEstimate(
                dimension_id=dim_id,
                score=5.0,
                reason="AI 未返回此维度",
                confidence=0.0,
            )

    return estimates


def _default_estimates() -> dict[str, DimensionEstimate]:
    """所有维度使用默认中间分 5.0"""
    return {
        dim_id: DimensionEstimate(
            dimension_id=dim_id,
            score=5.0,
            reason="默认分（AI 不可用）",
            confidence=0.0,
        )
        for dim_id in DIMENSION_IDS
    }


# ── 批量估计 ───────────────────────────────────────────────────────────────────

async def batch_estimate(
    entities: list[dict[str, Any]],
    ai_client: Any = None,
    model: str = "gpt-4o-mini",
    concurrency: int = 5,
) -> dict[str, dict[str, DimensionEstimate]]:
    """
    批量估计多个实体的维度分。

    使用 asyncio.Semaphore 控制并发，避免触发 rate limit。

    Args:
        entities: 实体数据字典列表
        ai_client: OpenAI AsyncClient
        model: 模型名
        concurrency: 最大并发数

    Returns:
        {entity_id: {dimension_id: DimensionEstimate}} 嵌套字典
    """
    import asyncio

    semaphore = asyncio.Semaphore(concurrency)
    results: dict[str, dict[str, DimensionEstimate]] = {}

    async def _estimate_one(entity: dict[str, Any]) -> None:
        entity_id = str(entity.get("id", "unknown"))
        async with semaphore:
            estimates = await estimate_dimensions_by_ai(entity, ai_client, model)
            results[entity_id] = estimates

    tasks = [_estimate_one(e) for e in entities]
    await asyncio.gather(*tasks, return_exceptions=True)

    # 确保所有实体都有结果（即使失败的）
    for entity in entities:
        entity_id = str(entity.get("id", "unknown"))
        if entity_id not in results:
            results[entity_id] = _default_estimates()

    logger.info(
        "Batch AI estimation complete: %d entities, %d succeeded",
        len(entities),
        sum(1 for r in results.values() if any(e.confidence > 0 for e in r.values())),
    )

    return results
