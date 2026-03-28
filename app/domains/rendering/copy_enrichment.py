"""
copy_enrichment.py — 页面文案 AI 填充（从 report_generator 解耦）

在 page pipeline 完成之后调用，对需要文案的页面补充 AI 生成的文字。
文案是可选的：没有文案页面也能渲染（用占位符）。

当前支持：
- day_execution 页面: mood_sentence + day_intro_draft
- cover 页面: trip_tagline
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


async def enrich_page_copy(
    page_models: dict[str, Any],
    planning_output: Any,
    session: Any | None = None,
) -> dict[str, Any]:
    """
    对 page_models 中需要文案的页面填充 AI 生成的文字。

    Args:
        page_models: dict[page_id → PageViewModel（序列化后的 dict 或 dataclass）]
        planning_output: PlanningOutput 数据源
        session: 可选 DB session（未来可用于缓存/fragment 复用）

    Returns:
        更新后的 page_models（原地修改并返回）
    """
    tasks = []

    for page_id, vm in page_models.items():
        page_type = _get_field(vm, "page_type")

        if page_type == "day_execution":
            tasks.append(_enrich_day_execution(vm, planning_output))
        elif page_type == "cover":
            tasks.append(_enrich_cover(vm, planning_output))

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

    logger.info("[CopyEnrichment] enriched %d pages", len(tasks))
    return page_models


async def _enrich_day_execution(vm: Any, planning_output: Any) -> None:
    """为 day_execution 页面生成 mood_sentence 和 day_intro_draft。"""
    day_index = _get_field(vm, "day_index")
    if day_index is None:
        return

    # 从 emotional_goals 获取基础 mood（已由规则生成）
    mood = ""
    day_goal = ""
    for eg in planning_output.emotional_goals:
        if eg.day_index == day_index:
            mood = eg.mood_sentence
            break

    # 从 days 获取结构化信息
    for day in planning_output.days:
        if day.day_index == day_index:
            day_goal = day.day_goal or f"{day.primary_area} · {day.intensity}"
            break

    # 尝试 AI 生成更好的文案
    try:
        ai_copy = await _ai_generate_day_copy(day_index, planning_output)
        if ai_copy:
            mood = ai_copy.get("mood_sentence", mood)
            day_goal = ai_copy.get("day_intro", day_goal)
    except Exception as exc:
        logger.debug("[CopyEnrichment] AI day copy failed (using rule fallback): %s", exc)

    # 写入 editable_content
    ec = _get_field(vm, "editable_content") or {}
    if isinstance(vm, dict):
        ec["mood_sentence"] = mood
        ec["day_intro_draft"] = day_goal
        vm["editable_content"] = ec
    else:
        ec["mood_sentence"] = mood
        ec["day_intro_draft"] = day_goal
        vm.editable_content = ec


async def _enrich_cover(vm: Any, planning_output: Any) -> None:
    """为封面生成 trip tagline。"""
    dest = planning_output.meta.destination
    days = planning_output.meta.total_days
    party = planning_output.profile_summary.party_type

    tagline = f"{dest} {days}天 · 专属手账"

    # 尝试 AI 生成更好的 tagline
    try:
        ai_copy = await _ai_generate_cover_copy(planning_output)
        if ai_copy and ai_copy.get("tagline"):
            tagline = ai_copy["tagline"]
    except Exception as exc:
        logger.debug("[CopyEnrichment] AI cover copy failed (using rule fallback): %s", exc)

    ec = _get_field(vm, "editable_content") or {}
    if isinstance(vm, dict):
        ec["trip_tagline"] = tagline
        vm["editable_content"] = ec
    else:
        ec["trip_tagline"] = tagline
        vm.editable_content = ec


# ── AI 调用（可选，失败不影响页面结构） ─────────────────────────────────────


async def _ai_generate_day_copy(day_index: int, planning_output: Any) -> dict | None:
    """调用 AI 生成每天的文案。失败返回 None。"""
    try:
        from app.core.ai_client import get_openai_client
        client = get_openai_client()
    except Exception:
        return None

    day = next((d for d in planning_output.days if d.day_index == day_index), None)
    if not day:
        return None

    slot_names = [s.title for s in day.slots[:6]]
    prompt = (
        f"为旅行手账第 {day_index} 天写一句简短的心情描述和一段简短的日程介绍。\n"
        f"区域: {day.primary_area}\n"
        f"节奏: {day.intensity}\n"
        f"景点: {', '.join(slot_names)}\n"
        f"要求: 口语化，温暖，不超过30字。\n"
        f"返回 JSON: {{\"mood_sentence\": \"...\", \"day_intro\": \"...\"}}"
    )

    try:
        import json
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7,
        )
        text = response.choices[0].message.content.strip()
        # 提取 JSON
        if "{" in text:
            json_str = text[text.index("{"):text.rindex("}") + 1]
            return json.loads(json_str)
    except Exception:
        pass
    return None


async def _ai_generate_cover_copy(planning_output: Any) -> dict | None:
    """调用 AI 生成封面文案。失败返回 None。"""
    try:
        from app.core.ai_client import get_openai_client
        client = get_openai_client()
    except Exception:
        return None

    dest = planning_output.meta.destination
    days = planning_output.meta.total_days
    party = planning_output.profile_summary.party_type

    prompt = (
        f"为一本旅行手账写一句封面标语。\n"
        f"目的地: {dest}\n"
        f"天数: {days}\n"
        f"同行: {party}\n"
        f"要求: 文艺感，不超过15字。\n"
        f"返回 JSON: {{\"tagline\": \"...\"}}"
    )

    try:
        import json
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.8,
        )
        text = response.choices[0].message.content.strip()
        if "{" in text:
            json_str = text[text.index("{"):text.rindex("}") + 1]
            return json.loads(json_str)
    except Exception:
        pass
    return None


def _get_field(obj: Any, field: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(field)
    return getattr(obj, field, None)
