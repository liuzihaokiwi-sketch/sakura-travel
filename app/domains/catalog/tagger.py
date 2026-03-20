from __future__ import annotations

"""
GPT 辅助标签生成模块（Entity Tagger）

功能：
  - generate_tags_for_entities: 为一批实体调用 GPT-4o-mini 生成 9 维主题亲和度标签
  - generate_tags_for_city:     按城市批量生成标签（跳过已有标签的实体）
  - get_entity_affinity:        查询单个实体的 9 维亲和度字典
  - apply_seed_overrides:       从种子 JSON 覆盖人工标签（人工优先于 GPT）

9 个主题维度（与 context_score_design.json 对齐）：
  shopping / food / culture_history / onsen_relaxation / nature_outdoors
  anime_pop_culture / family_kids / nightlife_entertainment / photography_scenic
"""

import json
import logging
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.catalog import EntityBase, EntityTag

logger = logging.getLogger(__name__)

# ── 常量 ─────────────────────────────────────────────────────────────────────

THEME_DIMENSIONS: list[str] = [
    "shopping",
    "food",
    "culture_history",
    "onsen_relaxation",
    "nature_outdoors",
    "anime_pop_culture",
    "family_kids",
    "nightlife_entertainment",
    "photography_scenic",
]

SEED_DATA_PATH = Path(__file__).parent.parent.parent.parent / "data" / "entity_affinity_seed_v1.json"
BATCH_SIZE = 10  # GPT 单次处理实体上限


# ── GPT 客户端（懒初始化）────────────────────────────────────────────────────

def _get_client() -> AsyncOpenAI:
    from app.core.config import settings
    return AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.ai_base_url if settings.ai_base_url else None,
    )


# ── Prompt 模板 ───────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """你是日本旅游内容标注专家。
请为提供的地点列表，在以下 9 个主题维度上打 0-5 强度分：
shopping（购物）/ food（美食）/ culture_history（文化历史）/
onsen_relaxation（温泉放松）/ nature_outdoors（自然户外）/
anime_pop_culture（动漫流行文化）/ family_kids（亲子）/
nightlife_entertainment（夜生活娱乐）/ photography_scenic（摄影风景）

评分规则：
- 0 = 完全无关
- 1-2 = 轻微相关
- 3 = 中度相关
- 4 = 强相关
- 5 = 该维度的核心代表（标志性）

重要约束：
1. 只标注真实存在的知名地点，若不确定请打 0
2. 每个维度必须给分，不可缺项
3. 输出严格 JSON 格式：{"entity_name": {"shopping": 0, "food": 3, ...}, ...}"""

_USER_PROMPT_TEMPLATE = """请为以下 {count} 个日本地点打主题亲和度标签：

{entities_json}

输出格式：JSON 对象，key 为地点名称，value 为 9 维评分字典。"""


# ── 核心函数 ──────────────────────────────────────────────────────────────────

async def generate_tags_for_entities(
    session: AsyncSession,
    entities: list[EntityBase],
) -> dict[str, dict[str, int]]:
    """
    为一批实体调用 GPT-4o-mini 生成主题亲和度标签并写入 entity_tags 表。

    Args:
        session:  AsyncSession
        entities: EntityBase 对象列表（长度建议 ≤ 10）

    Returns:
        {entity_id_str: {theme: score}} 已写入的标签字典
    """
    if not entities:
        return {}

    client = _get_client()

    # 构建 GPT 输入
    entity_info = [
        {
            "name": e.name_zh or e.name_ja or "Unknown",
            "type": e.entity_type,
            "city": e.city_code,
            "entity_id": str(e.entity_id),
        }
        for e in entities
    ]
    entities_json = json.dumps(entity_info, ensure_ascii=False, indent=2)

    try:
        from app.core.config import settings as _settings
        resp = await client.chat.completions.create(
            model=_settings.ai_model_light,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _USER_PROMPT_TEMPLATE.format(
                    count=len(entities),
                    entities_json=entities_json,
                )},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=2000,
        )
        raw_text = resp.choices[0].message.content or "{}"
        gpt_result: dict[str, Any] = json.loads(raw_text)
    except Exception as e:
        logger.error(f"GPT 标签生成失败: {e}")
        return {}

    # 将 GPT 结果匹配回 entity，写入 entity_tags
    name_to_entity = {
        (e.name_zh or e.name_ja or ""): e
        for e in entities
    }
    written: dict[str, dict[str, int]] = {}

    for name_key, scores in gpt_result.items():
        entity = name_to_entity.get(name_key)
        if entity is None:
            # 尝试模糊匹配（GPT 可能改了名字格式）
            for candidate_name, candidate_entity in name_to_entity.items():
                if name_key in candidate_name or candidate_name in name_key:
                    entity = candidate_entity
                    break
        if entity is None:
            continue

        tag_scores = _normalize_scores(scores)
        await _upsert_entity_tags(session, entity, tag_scores, source="gpt")
        written[str(entity.entity_id)] = tag_scores

    return written


async def generate_tags_for_city(
    session: AsyncSession,
    city_code: str,
    entity_type: str | None = None,
    force_regenerate: bool = False,
) -> dict[str, Any]:
    """
    批量为城市内没有标签的实体生成标签。

    Args:
        session:           AsyncSession
        city_code:         城市代码
        entity_type:       可选，过滤类型 poi/hotel/restaurant
        force_regenerate:  True = 重新生成所有实体的标签

    Returns:
        统计结果字典
    """
    # 查询需要打标的实体：无 entity_tags 记录，或强制重新生成
    if force_regenerate:
        stmt = select(EntityBase).where(
            EntityBase.city_code == city_code,
            EntityBase.is_active == True,  # noqa: E712
        )
    else:
        # 子查询：已有 ≥9 条 affinity 标签的 entity_id（已完整打标）
        tagged_subq = (
            select(EntityTag.entity_id)
            .where(EntityTag.tag_namespace == "affinity")
            .group_by(EntityTag.entity_id)
            .having(func.count(EntityTag.id) >= 9)
            .scalar_subquery()
        )
        stmt = select(EntityBase).where(
            EntityBase.city_code == city_code,
            EntityBase.is_active == True,  # noqa: E712
            EntityBase.entity_id.not_in(tagged_subq),
        )

    if entity_type:
        stmt = stmt.where(EntityBase.entity_type == entity_type)

    result = await session.execute(stmt)
    entities = result.scalars().all()

    if not entities:
        logger.info(f"[{city_code}] 无需打标的实体")
        return {"city_code": city_code, "processed": 0, "written": 0}

    logger.info(f"[{city_code}] 待打标实体 {len(entities)} 条，分批处理...")

    total_written = 0
    errors = 0

    # 分批处理
    for i in range(0, len(entities), BATCH_SIZE):
        batch = list(entities[i: i + BATCH_SIZE])
        try:
            written = await generate_tags_for_entities(session, batch)
            total_written += len(written)
            await session.commit()
            logger.debug(f"[{city_code}] 批次 {i//BATCH_SIZE + 1} 完成，写入 {len(written)} 条")
        except Exception as e:
            logger.error(f"[{city_code}] 批次 {i//BATCH_SIZE + 1} 失败: {e}")
            await session.rollback()
            errors += 1

    return {
        "city_code": city_code,
        "processed": len(entities),
        "written": total_written,
        "errors": errors,
    }


async def get_entity_affinity(
    session: AsyncSession,
    entity_id: str,
) -> dict[str, int]:
    """
    查询单个实体的 9 维主题亲和度字典。

    Args:
        session:   AsyncSession
        entity_id: 实体 UUID 字符串

    Returns:
        {theme_key: score (0-5)}，无标签时返回全 0
    """
    import uuid as _uuid
    try:
        eid = _uuid.UUID(entity_id)
    except ValueError:
        return {k: 0 for k in THEME_DIMENSIONS}

    stmt = select(EntityTag).where(EntityTag.entity_id == eid)
    result = await session.execute(stmt)
    tags = result.scalars().all()

    affinity = {k: 0 for k in THEME_DIMENSIONS}
    for tag in tags:
        # tag_value 格式："{theme}:{score}"
        if tag.tag_namespace == "affinity" and ":" in (tag.tag_value or ""):
            theme, _, score_str = tag.tag_value.partition(":")
            if theme in affinity:
                try:
                    affinity[theme] = int(score_str)
                except ValueError:
                    pass

    return affinity


async def apply_seed_overrides(
    session: AsyncSession,
    seed_path: Path | None = None,
) -> dict[str, Any]:
    """
    从 entity_affinity_seed_v1.json 加载人工标签，覆盖写入 entity_tags 表。
    匹配策略：按 entity_id（精确）或 name_zh（模糊）匹配实体。

    Args:
        session:   AsyncSession
        seed_path: 种子文件路径，默认为 data/entity_affinity_seed_v1.json

    Returns:
        统计结果字典
    """
    path = seed_path or SEED_DATA_PATH
    if not path.exists():
        logger.warning(f"种子文件不存在: {path}")
        return {"status": "skipped", "reason": "file_not_found"}

    with open(path, encoding="utf-8") as f:
        seed_data: list | dict = json.load(f)

    # 兼容多种格式：
    #   - 列表格式: [{"entity_name": ..., "affinity_scores": ...}, ...]
    #   - 带 entities 字段: {"entities": [...], ...}
    #   - 纯字典: {name: scores, ...}
    if isinstance(seed_data, list):
        items = seed_data
    elif isinstance(seed_data, dict):
        if "entities" in seed_data:
            items = seed_data["entities"]
        else:
            items = list(seed_data.values())
    else:
        items = []

    written = 0
    skipped = 0

    for item in items:
        if not isinstance(item, dict):
            skipped += 1
            continue
        entity_id_str = item.get("entity_id")
        # 兼容 entity_name（中文）/ name_zh / name_ja 三种字段名
        name_zh = (
            item.get("name_zh")
            or item.get("entity_name")
            or item.get("name_ja")
        )
        # 兼容 affinity_scores / theme_affinity / affinity 三种字段名
        affinity_raw = (
            item.get("affinity_scores")
            or item.get("theme_affinity")
            or item.get("affinity")
            or {}
        )

        if not affinity_raw:
            skipped += 1
            continue

        # 查找实体
        entity = None
        if entity_id_str:
            import uuid as _uuid
            try:
                stmt = select(EntityBase).where(
                    EntityBase.entity_id == _uuid.UUID(entity_id_str)
                )
                result = await session.execute(stmt)
                entity = result.scalar_one_or_none()
            except Exception:
                pass

        if entity is None and name_zh:
            stmt = select(EntityBase).where(EntityBase.name_zh == name_zh)
            result = await session.execute(stmt)
            entity = result.scalar_one_or_none()

        if entity is None:
            skipped += 1
            continue

        tag_scores = _normalize_scores(affinity_raw)
        await _upsert_entity_tags(session, entity, tag_scores, source="seed")
        written += 1

    await session.commit()
    logger.info(f"种子标签覆盖完成 — 写入: {written}, 跳过: {skipped}")
    return {"written": written, "skipped": skipped}


# ── 内部工具函数 ──────────────────────────────────────────────────────────────

def _normalize_scores(raw: dict) -> dict[str, int]:
    """将 GPT / 种子数据中的分数规范化为 0-5 整数，缺失维度补 0。"""
    result: dict[str, int] = {}
    for dim in THEME_DIMENSIONS:
        val = raw.get(dim, 0)
        try:
            score = max(0, min(5, int(float(val))))
        except (TypeError, ValueError):
            score = 0
        result[dim] = score
    return result


async def _upsert_entity_tags(
    session: AsyncSession,
    entity: EntityBase,
    tag_scores: dict[str, int],
    source: str = "gpt",
) -> None:
    """删除旧主题亲和度标签后重新写入（当 source 优先级更高时才覆盖）。
    EntityTag 模型字段：tag_namespace / tag_value / source
    主题标签存储方式：tag_namespace="affinity", tag_value="{theme}:{score}"
    """
    # 检查是否已有 seed 来源的标签（seed > gpt，不用 gpt 覆盖 seed）
    if source == "gpt":
        check_stmt = select(EntityTag).where(
            EntityTag.entity_id == entity.entity_id,
            EntityTag.tag_namespace == "affinity",
            EntityTag.source == "seed",
        ).limit(1)
        existing = await session.execute(check_stmt)
        if existing.scalar_one_or_none() is not None:
            logger.debug(f"跳过 GPT 覆盖 {entity.name_zh}（已有 seed 标签）")
            return

    # 删除该实体的主题亲和度标签
    await session.execute(
        delete(EntityTag).where(
            EntityTag.entity_id == entity.entity_id,
            EntityTag.tag_namespace == "affinity",
        )
    )

    # 写入新标签（tag_namespace="affinity", tag_value="{theme}:{score}"）
    for theme, score in tag_scores.items():
        tag = EntityTag(
            entity_id=entity.entity_id,
            tag_namespace="affinity",
            tag_value=f"{theme}:{score}",
            source=source,
        )
        session.add(tag)
