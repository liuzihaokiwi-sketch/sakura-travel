"""
AI 文案润色层（ai-copywriter）

对装配完成的行程实体，用 GPT-4o-mini 生成：
  - copy_zh: 一句话描述（25-40字）
  - tips_zh: 旅行 Tips（15-25字）

缓存策略：Redis key=copywriter:{entity_id}:{scene}，TTL=7天
降级方案：GPT 失败/超时(3s) → 返回 Catalog 原始描述
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, Optional

from redis.asyncio import Redis

from app.core.ai_cache import cached_ai_call

logger = logging.getLogger(__name__)

_REDIS_TTL = 7 * 24 * 3600  # 7 天（秒）
_GPT_TIMEOUT = 3.0           # 超时阈值（秒）

# ── Prompt 模板 ────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
你是一个去过关西20次的资深旅行者，正在帮刚认识的朋友规划第一次关西之旅。

你的语气是：直接、具体、有温度，像老朋友发微信给你——不是旅游手册，也不是公众号。

写两样东西：
1. 一句话描述（25-40字）：说出这个地方最值得去的一个理由，要有画面感和情绪
2. 实用贴士（15-25字）：一句最关键的行动建议，能帮他少走弯路或把握最佳时机

语言规范：
- 禁用：著名/知名/有名/不得不/必打卡/人气/网红/体验感极佳/氛围感
- 禁用：这里/该景点/它/此处 作为开头
- 鼓励：具体的时间（"7点前""工作日下午"）、具体的位置（"二楼左转"）、具体的细节（"点招牌冷面"）
- 写完读一遍，如果感觉像广告文案就重写"""

_USER_PROMPT_TMPL = """\
地点：{name_zh}
类型：{entity_type} / {primary_type}
位置：{city} {area}
特点标签：{tags}
评分：{rating}（{review_count} 条真实评价）
编辑内部备注：{editorial_reason}

输出严格 JSON（不要 markdown 代码块）：
{{"copy_zh": "一句话描述，25-40字", "tips_zh": "实用贴士，15-25字"}}"""


# ── 核心函数 ───────────────────────────────────────────────────────────────────

async def generate_copy(
    entity: Any,
    scene: str,
    redis_client: Optional[Redis] = None,
    *,
    editorial_reason: str = "",
) -> Dict[str, str]:
    """
    为单个实体生成文案。

    Args:
        entity:           EntityBase ORM 对象（需含 entity_id / name_zh / entity_type 等字段）
        scene:            场景（couple / family / solo / general）
        redis_client:     Redis 连接，None 时跳过缓存
        editorial_reason: 人工编辑备注（优先展示）

    Returns:
        {"copy_zh": "...", "tips_zh": "..."}
    """
    entity_id = str(entity.entity_id)
    cache_key = f"copywriter:{entity_id}:{scene}"

    # 1. 尝试读 Redis 缓存
    if redis_client is not None:
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                logger.debug("copywriter cache hit: %s", cache_key)
                return json.loads(cached)
        except Exception as e:
            logger.warning("Redis 缓存读取失败，跳过缓存: %s", e)

    # 2. 人工 editorial_reason 优先（仍然调 GPT，但把备注传入以影响文案）
    fallback = _fallback_copy(entity)

    # 3. 调用 GPT-4o-mini
    try:
        result = await asyncio.wait_for(
            _call_gpt(entity, scene, editorial_reason),
            timeout=_GPT_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.warning("GPT 调用超时（entity=%s），启用降级方案", entity_id)
        return fallback
    except Exception as e:
        logger.warning("GPT 调用失败（entity=%s）: %s，启用降级方案", entity_id, e)
        return fallback

    # 4. 写入 Redis 缓存
    if redis_client is not None:
        try:
            await redis_client.set(cache_key, json.dumps(result, ensure_ascii=False), ex=_REDIS_TTL)
        except Exception as e:
            logger.warning("Redis 缓存写入失败（不影响结果）: %s", e)

    return result


async def _call_gpt(entity: Any, scene: str, editorial_reason: str) -> Dict[str, str]:
    """调用 AI 模型生成文案（经由 ai_cache 中间件），返回 {copy_zh, tips_zh}。"""
    from app.core.config import settings

    # 组装 prompt
    name_zh = getattr(entity, "name_zh", "") or ""
    entity_type = getattr(entity, "entity_type", "") or ""
    city_code = getattr(entity, "city_code", "") or ""
    area = getattr(entity, "area_name", "") or getattr(entity, "city_area", "") or ""
    rating = _get_rating(entity)
    review_count = _get_review_count(entity)
    primary_type = _get_primary_type(entity)
    tags = _get_tags_str(entity)

    user_prompt = _USER_PROMPT_TMPL.format(
        name_zh=name_zh,
        entity_type=entity_type,
        primary_type=primary_type,
        city=city_code,
        area=area,
        tags=tags,
        rating=rating,
        review_count=review_count,
        editorial_reason=editorial_reason or "无",
    )

    # 走 cached_ai_call，相同实体+场景命中缓存后不重复调用 AI
    content = await cached_ai_call(
        prompt=user_prompt,
        model=settings.ai_model_standard,
        system_prompt=_SYSTEM_PROMPT,
        temperature=0.7,
        max_tokens=200,
        response_format={"type": "json_object"},
    )

    data = json.loads(content or "{}")
    copy_zh = data.get("copy_zh", "").strip()
    tips_zh = data.get("tips_zh", "").strip()

    if not copy_zh or not tips_zh:
        raise ValueError(f"GPT 返回格式不完整: {data}")

    return {"copy_zh": copy_zh, "tips_zh": tips_zh}


def _fallback_copy(entity: Any) -> Dict[str, str]:
    """降级方案：使用 Catalog 原始描述。"""
    # 优先取 description_zh，回退到 name_zh
    description = (
        getattr(entity, "description_zh", None)
        or getattr(entity, "name_zh", "")
    )
    return {
        "copy_zh": description or "",
        "tips_zh": "建议提前查看官方开放时间",
    }


# ── 辅助函数 ───────────────────────────────────────────────────────────────────

def _get_rating(entity: Any) -> str:
    """从 entity 或其子表获取 Google 评分。"""
    for attr in ("google_rating",):
        val = getattr(entity, attr, None)
        if val is not None:
            return str(val)
    # 尝试从子关系获取
    for sub in ("poi", "restaurant", "hotel"):
        sub_obj = getattr(entity, sub, None)
        if sub_obj:
            val = getattr(sub_obj, "google_rating", None)
            if val is not None:
                return str(val)
    return "N/A"


def _get_review_count(entity: Any) -> str:
    for attr in ("google_review_count",):
        val = getattr(entity, attr, None)
        if val is not None:
            return str(val)
    for sub in ("poi", "restaurant", "hotel"):
        sub_obj = getattr(entity, sub, None)
        if sub_obj:
            val = getattr(sub_obj, "google_review_count", None)
            if val is not None:
                return str(val)
    return "N/A"


def _get_primary_type(entity: Any) -> str:
    entity_type = getattr(entity, "entity_type", "") or ""
    if entity_type == "poi":
        poi = getattr(entity, "poi", None)
        if poi:
            return getattr(poi, "poi_category", "") or entity_type
    elif entity_type == "restaurant":
        rest = getattr(entity, "restaurant", None)
        if rest:
            return getattr(rest, "cuisine_type", "") or entity_type
    elif entity_type == "hotel":
        hotel = getattr(entity, "hotel", None)
        if hotel:
            return getattr(hotel, "hotel_category", "") or entity_type
    return entity_type


def _get_tags_str(entity: Any) -> str:
    """把 entity.tags 转成可读字符串。"""
    tags = getattr(entity, "tags", None) or []
    tag_parts = []
    for tag in tags:
        ns = getattr(tag, "tag_namespace", "")
        val = getattr(tag, "tag_value", "")
        if ns == "affinity" and val:
            # 格式: "theme:score" → 取 theme
            theme = val.split(":")[0]
            tag_parts.append(theme)
    return "/".join(tag_parts[:5]) if tag_parts else "综合"


# ── 批量文案生成 ──────────────────────────────────────────────────────────────

async def batch_generate_copy(
    items_with_entities: list[tuple[Any, Any]],
    scene: str,
    redis_client: Optional[Redis] = None,
    editorial_map: Optional[Dict[str, str]] = None,
) -> Dict[str, Dict[str, str]]:
    """
    批量生成文案，并发调用 GPT（最多 5 并发）。

    Args:
        items_with_entities: [(ItineraryItem, EntityBase), ...]
        scene:               场景
        redis_client:        Redis 连接
        editorial_map:       {entity_id_str: editorial_reason}

    Returns:
        {entity_id_str: {"copy_zh": "...", "tips_zh": "..."}}
    """
    editorial_map = editorial_map or {}
    semaphore = asyncio.Semaphore(5)  # 最多 5 并发 GPT 调用

    async def _safe_generate(entity: Any) -> tuple[str, Dict[str, str]]:
        entity_id = str(entity.entity_id)
        async with semaphore:
            result = await generate_copy(
                entity,
                scene,
                redis_client,
                editorial_reason=editorial_map.get(entity_id, ""),
            )
        return entity_id, result

    tasks = []
    seen_ids: set[str] = set()
    for _, entity in items_with_entities:
        if entity is None:
            continue
        eid = str(entity.entity_id)
        if eid in seen_ids:
            continue
        seen_ids.add(eid)
        tasks.append(_safe_generate(entity))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    copy_map: Dict[str, Dict[str, str]] = {}
    for r in results:
        if isinstance(r, Exception):
            logger.warning("batch_generate_copy 单项失败: %s", r)
        else:
            eid, copy_data = r
            copy_map[eid] = copy_data

    return copy_map