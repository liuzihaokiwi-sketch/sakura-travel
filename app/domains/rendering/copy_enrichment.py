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
        results = await asyncio.gather(*tasks, return_exceptions=True)
        failures = sum(1 for r in results if isinstance(r, Exception))
        if failures:
            logger.warning("[CopyEnrichment] %d/%d enrichment tasks failed", failures, len(tasks))

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
        logger.warning("[CopyEnrichment] AI day copy failed day=%s (using rule fallback): %s", day_index, exc)

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
        logger.warning("[CopyEnrichment] AI cover copy failed (using rule fallback): %s", exc)

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
    persona = _load_persona(planning_output)

    system_prompt = (
        f"你是{persona['name']}，{persona['bio']}\n\n"
        "你正在帮朋友写旅行手账。语气像一个去过很多次的朋友在微信上给你划重点——\n"
        "口语化、有画面感、偶尔带一点小得意（\"这个我私藏很久了\"），但绝不做作。\n"
        "避免：旅游广告腔（\"感受当地风情\"）、空洞形容词（\"美丽的\"\"壮观的\"）、感叹号堆砌。\n"
        "好的例子：\"岚山早上人少得离谱，趁这会儿慢慢走\" \"这天节奏松，睡到自然醒也来得及\"\n"
        "差的例子：\"今天我们将开启一段美好的旅程！\" \"感受千年古都的魅力\""
    )

    user_prompt = (
        f"手账第 {day_index} 天：\n"
        f"区域: {day.primary_area}\n"
        f"节奏: {day.intensity}\n"
        f"安排: {', '.join(slot_names)}\n\n"
        "请写：\n"
        "1. mood_sentence — 这天的一句话心情/氛围（15字以内，像朋友随口说的）\n"
        "2. day_intro — 这天的简介（30-50字，划重点式，告诉朋友今天怎么玩）\n\n"
        "返回 JSON: {\"mood_sentence\": \"...\", \"day_intro\": \"...\"}"
    )

    try:
        import json
        from app.core.config import get_settings
        _model = get_settings().ai_model_light
        response = await client.chat.completions.create(
            model=_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=200,
            temperature=0.7,
        )
        text = response.choices[0].message.content.strip()
        if "{" in text:
            json_str = text[text.index("{"):text.rindex("}") + 1]
            return json.loads(json_str)
    except Exception as exc:
        logger.warning("[CopyEnrichment] AI day copy API/parse error: %s", exc)
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
    persona = _load_persona(planning_output)

    system_prompt = (
        f"你是{persona['name']}，{persona['bio']}\n\n"
        "你在帮朋友做一本旅行手账的封面标语。\n"
        "风格：简洁、有期待感、稍带文艺但不矫情。像在手账封面用好看的字写下的一句话。\n"
        "好的例子：\"京都的风，大阪的胃\" \"五天四夜，把关西装进口袋\" \"带着好胃口出发\"\n"
        "差的例子：\"开启一段难忘的旅程\" \"感受日本文化的魅力\""
    )

    user_prompt = (
        f"目的地: {dest}\n"
        f"天数: {days}天\n"
        f"同行: {party}\n\n"
        "写一句封面标语，15字以内。\n"
        "返回 JSON: {\"tagline\": \"...\"}"
    )

    try:
        import json
        from app.core.config import get_settings
        _model = get_settings().ai_model_light
        response = await client.chat.completions.create(
            model=_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=100,
            temperature=0.8,
        )
        text = response.choices[0].message.content.strip()
        if "{" in text:
            json_str = text[text.index("{"):text.rindex("}") + 1]
            return json.loads(json_str)
    except Exception as exc:
        logger.warning("[CopyEnrichment] AI cover copy API/parse error: %s", exc)
    return None


def _load_persona(planning_output: Any) -> dict[str, str]:
    """从 circle_content 加载角色信息，失败时返回通用默认值。"""
    default = {
        "name": "小旅",
        "bio": '你热爱旅行，去过无数次，对每个街区了如指掌，特别懂得如何在"不踩坑"和"有惊喜"之间找到平衡。',
    }
    try:
        from app.domains.planning.circle_content import get_circle_content, get_circle_family_from_circle_id
        # 从 meta.circle（SelectedCircleInfo）取 circle_id
        circle_id = ""
        circle = getattr(planning_output.meta, "circle", None)
        if circle:
            circle_id = getattr(circle, "circle_id", "") or ""
        # fallback: 从 circles 列表取
        if not circle_id:
            circles = getattr(planning_output, "circles", []) or []
            if circles:
                circle_id = getattr(circles[0], "circle_id", "") or ""
        if not circle_id:
            return default
        circle_family = get_circle_family_from_circle_id(circle_id)
        content = get_circle_content(circle_family)
        if content:
            return {
                "name": content.persona_name,
                "bio": content.persona_bio,
            }
    except Exception:
        pass
    return default


def _get_field(obj: Any, field: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(field)
    return getattr(obj, field, None)
