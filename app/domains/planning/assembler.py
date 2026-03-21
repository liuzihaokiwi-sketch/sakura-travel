"""
行程装配引擎 v1 — 基于路线模板 + 评分数据装配结构化行程

流程：
    load_template → apply_scene_variant
    → 逐日逐槽位 fetch_slot_candidates → 填充实体
    → assemble_trip → 写入 DB + enqueue run_guardrails
"""
from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.queue import enqueue_job
from app.db.models.catalog import EntityBase, EntityTag, EntityEditorNote
from app.db.models.derived import (
    EntityScore,
    ItineraryDay,
    ItineraryItem,
    ItineraryPlan,
    PlannerRun,
    RouteTemplate,
)
from app.domains.ranking.scorer import (
    CandidateScoreResult,
    EntitySignals,
    compute_candidate_score,
)
from app.domains.ranking.soft_rules.weight_packs import (
    SEGMENT_PACK_SEEDS,
    STAGE_PACK_SEEDS,
    merge_weight_packs,
    aggregate_soft_rule_score,
)

logger = logging.getLogger(__name__)

# ─── party_type → segment_pack_id 映射 ──────────────────────────────────────────
_PARTY_TO_SEGMENT: dict[str, str] = {
    "solo": "first_time_fit",
    "couple": "couple",
    "family_child": "family_child",
    "family_no_child": "parents",
    "group": "friends_small_group",
    "senior": "parents",
    # quiz 前端可能传的别名
    "friends": "friends_small_group",
    "besties": "besties",
    "parents": "parents",
}


# ─── 用户权重构建 ──────────────────────────────────────────────────────────────

async def _build_user_weights(
    session: AsyncSession,
    trip_request_id: uuid.UUID,
    stage: str = "standard",
) -> tuple[dict[str, float], str, str]:
    """从 TripProfile 构建 user_weights（用于 context_score 计算）。

    Returns:
        (merged_weights, segment_pack_id, stage_pack_id)
    """
    from app.db.models.business import TripProfile

    result = await session.execute(
        select(TripProfile).where(TripProfile.trip_request_id == trip_request_id)
    )
    profile = result.scalar_one_or_none()

    # 确定客群包
    segment_pack_id = "first_time_fit"  # 默认
    if profile and profile.party_type:
        segment_pack_id = _PARTY_TO_SEGMENT.get(profile.party_type, "first_time_fit")

    # 确定阶段包
    stage_pack_id = stage if stage in STAGE_PACK_SEEDS else "standard"

    # 获取 seed 权重（不走 DB，直接用内存 seeds；DB 权重包表可能尚未灌入数据）
    seg_weights = SEGMENT_PACK_SEEDS.get(segment_pack_id, SEGMENT_PACK_SEEDS["first_time_fit"])
    stg_weights = STAGE_PACK_SEEDS.get(stage_pack_id, STAGE_PACK_SEEDS["standard"])
    merged = merge_weight_packs(seg_weights, stg_weights)

    logger.info(
        "user_weights built: segment=%s stage=%s trip=%s",
        segment_pack_id, stage_pack_id, trip_request_id,
    )
    return merged, segment_pack_id, stage_pack_id


async def _build_entity_affinity(
    session: AsyncSession,
    entity_ids: list[uuid.UUID],
) -> dict[uuid.UUID, dict[str, int]]:
    """批量查询实体的主题亲和度标签 → {entity_id: {theme: affinity_score}}。"""
    if not entity_ids:
        return {}

    result = await session.execute(
        select(EntityTag).where(
            EntityTag.entity_id.in_(entity_ids),
            EntityTag.tag_namespace == "affinity",
        )
    )
    tags = result.scalars().all()

    affinity_map: dict[uuid.UUID, dict[str, int]] = {}
    for tag in tags:
        parts = (tag.tag_value or "").split(":", 1)
        if len(parts) == 2:
            try:
                affinity_map.setdefault(tag.entity_id, {})[parts[0].lower()] = int(parts[1])
            except ValueError:
                pass
    return affinity_map


async def _get_entity_soft_scores(
    session: AsyncSession,
    entity_ids: list[uuid.UUID],
) -> dict[uuid.UUID, float]:
    """查询实体的软规则聚合分（如果 entity_soft_scores 表存在）。

    Returns:
        {entity_id: soft_rule_score (0-100)} — 缺失的实体不在 dict 中
    """
    try:
        from app.db.models.soft_rules import EntitySoftScore
        result = await session.execute(
            select(EntitySoftScore).where(
                EntitySoftScore.entity_id.in_(entity_ids),
            )
        )
        scores = result.scalars().all()

        soft_map: dict[uuid.UUID, float] = {}
        for s in scores:
            # EntitySoftScore 有 12 个维度列，需要聚合
            dim_scores: dict[str, float] = {}
            from app.domains.ranking.soft_rules.dimensions import DIMENSION_IDS
            for dim_id in DIMENSION_IDS:
                val = getattr(s, dim_id, None)
                if val is not None:
                    dim_scores[dim_id] = float(val)
            if dim_scores:
                from app.domains.ranking.soft_rules.dimensions import DEFAULT_WEIGHTS
                soft_map[s.entity_id] = aggregate_soft_rule_score(dim_scores, DEFAULT_WEIGHTS)
        return soft_map
    except Exception:
        # 表不存在或其他错误 → 退化到 2D
        logger.debug("entity_soft_scores 不可用，退化到 2D 评分")
        return {}


async def _rescore_candidates(
    session: AsyncSession,
    candidates: list[EntityBase],
    user_weights: dict[str, float],
    segment_pack_id: str,
    stage_pack_id: str,
) -> list[EntityBase]:
    """对候选实体用三维公式重新评分，按 final_score 降序排序。"""
    if not candidates:
        return candidates

    entity_ids = [e.entity_id for e in candidates]

    # 批量查询 affinity + soft scores
    affinity_map = await _build_entity_affinity(session, entity_ids)
    soft_score_map = await _get_entity_soft_scores(session, entity_ids)

    # 批量查询 EntityScore（获取 base signals）
    es_result = await session.execute(
        select(EntityScore).where(
            EntityScore.entity_id.in_(entity_ids),
            EntityScore.score_profile == "general",
        )
    )
    es_map = {es.entity_id: es for es in es_result.scalars().all()}

    # 批量查询 editorial boost
    en_result = await session.execute(
        select(EntityEditorNote).where(
            EntityEditorNote.entity_id.in_(entity_ids),
        )
    )
    boost_map: dict[uuid.UUID, int] = {}
    for note in en_result.scalars().all():
        boost = getattr(note, "boost", 0) or getattr(note, "editorial_boost", 0) or 0
        boost_map[note.entity_id] = boost

    # 逐候选评分
    scored: list[tuple[EntityBase, float]] = []
    for entity in candidates:
        eid = entity.entity_id
        es = es_map.get(eid)

        # 构建 signals
        signals = EntitySignals(
            entity_type=entity.entity_type or "poi",
            data_tier=entity.data_tier or "B",
            google_rating=getattr(entity, "google_rating", None),
            google_review_count=getattr(entity, "google_review_count", None),
            editorial_boost=boost_map.get(eid, 0),
        )

        # entity affinity
        entity_affinity = affinity_map.get(eid, {})

        # soft rule score（可能为 None → 退化 2D）
        soft_score = soft_score_map.get(eid, None)

        result = compute_candidate_score(
            signals=signals,
            user_weights=user_weights,
            entity_affinity=entity_affinity,
            soft_rule_score=soft_score,
            segment_pack_id=segment_pack_id,
            stage_pack_id=stage_pack_id,
        )
        scored.append((entity, result.final_score))

    # 按 final_score 降序排序
    scored.sort(key=lambda x: x[1], reverse=True)
    return [entity for entity, _ in scored]


# ─── 模板加载 ──────────────────────────────────────────────────────────────────

# 英文 template_code → 中文 name_zh 映射（兼容旧数据）
_CODE_TO_NAME_ZH: dict[str, str] = {
    "tokyo_classic_3d": "东京精华3日",
    "tokyo_classic_5d": "东京经典5日",
    "tokyo_classic_7d": "东京经典7日",
    "tokyo_sakura_7d": "东京樱花季7日",
    "kansai_classic_4d": "关西精华4日",
    "kansai_classic_6d": "关西经典6日",
    "kansai_classic_7d": "关西经典7日",
    "tokyo_kansai_8d": "东京+关西联程8日",
}


async def load_template(session: AsyncSession, template_code: str) -> dict:
    """从 route_templates 表加载路线模板 JSON。

    支持两种 code 格式：
    - 英文 code（如 ``tokyo_classic_5d``）→ 通过 _CODE_TO_NAME_ZH 映射查找
    - 中文 name_zh（直接匹配 ``name_zh`` 列）
    - meta.template_code 精确匹配（fallback）
    """
    # 优先通过英文 code 映射到中文名
    name_zh_lookup = _CODE_TO_NAME_ZH.get(template_code, template_code)

    result = await session.execute(
        select(RouteTemplate).where(
            RouteTemplate.name_zh == name_zh_lookup,
            RouteTemplate.is_active == True,  # noqa: E712
        )
    )
    tmpl = result.scalar_one_or_none()
    if tmpl is not None:
        return tmpl.template_data

    # Fallback：遍历所有活跃模板，按 meta.template_code 精确匹配
    result2 = await session.execute(
        select(RouteTemplate).where(RouteTemplate.is_active == True)  # noqa: E712
    )
    all_tmpls = result2.scalars().all()
    for t in all_tmpls:
        meta = t.template_data.get("meta", {})
        if meta.get("template_code") == template_code:
            return t.template_data

    raise ValueError(f"路线模板 '{template_code}' 不存在或未激活")


def apply_scene_variant(template: dict, scene: str) -> dict:
    """将 scene_variants 的覆盖参数合并到模板中，返回新模板 dict（不修改原始）。"""
    import copy
    tmpl = copy.deepcopy(template)
    variants = tmpl.get("scene_variants", {})
    if scene not in variants:
        logger.debug("场景 '%s' 无变体配置，使用默认模板", scene)
        return tmpl

    variant = variants[scene]
    # 记录场景信息
    tmpl["_applied_scene"] = scene
    tmpl["_tag_weight_overrides"] = variant.get("tag_weight_overrides", {})
    tmpl["_filter_exclude_tags"] = variant.get("filter_exclude_tags", {})
    if "tagline_suffix_zh" in variant:
        meta = tmpl.get("meta", {})
        meta["tagline_zh"] = meta.get("tagline_zh", "") + f" · {variant['tagline_suffix_zh']}"
        tmpl["meta"] = meta
    return tmpl


# ─── 候选召回 ──────────────────────────────────────────────────────────────────

async def fetch_slot_candidates(
    session: AsyncSession,
    slot: dict,
    city_code: str,
    exclude_ids: set[uuid.UUID],
    tag_weight_overrides: dict[str, float] | None = None,
    filter_exclude_tags: dict[str, int] | None = None,
    area_strict: bool = True,
) -> list[EntityBase]:
    """
    按槽位条件召回候选实体，按 final_score 降序返回。

    Args:
        slot: 时间块定义（含 slot_type / tags_required / area_hint）
        city_code: 城市代码
        exclude_ids: 已选实体 ID 集合（去重用）
        tag_weight_overrides: 场景权重覆盖（暂用于排序调整）
        filter_exclude_tags: 需要排除的标签条件
        area_strict: True 时按 area_hint 过滤，False 时全城市召回（fallback）
    """
    # 从 slot_id 或 tags_required 推断实体类型
    slot_id: str = slot.get("slot_id", "")
    tags_required_raw = slot.get("tags_required", [])
    # 兼容 list 格式（实际数据）和 dict 格式（设计稿）
    if isinstance(tags_required_raw, list):
        tags_required_list: list[str] = tags_required_raw
        tags_required_dict: dict[str, int] = {}
    else:
        tags_required_dict = tags_required_raw
        tags_required_list = list(tags_required_raw.keys())

    area_hint: str | None = slot.get("area_hint")

    # 从 slot_id 或 tags 推断实体类型
    slot_type = slot.get("slot_type", "")
    if not slot_type:
        # 按 tags_required 推断
        all_tags_lower = [t.lower() for t in tags_required_list]
        if any(t in all_tags_lower for t in ("restaurant", "cafe", "ramen", "sushi", "izakaya", "lunch", "dinner")):
            slot_type = "restaurant"
        else:
            slot_type = "poi"

    entity_type_map = {
        "poi": "poi",
        "restaurant": "restaurant",
        "hotel_area": None,
        "transport": None,
    }
    entity_type = entity_type_map.get(slot_type, "poi")
    if slot_type in ("hotel_area", "transport"):
        return []

    # 基础查询：EntityBase JOIN EntityScore
    from app.db.models.derived import EntityScore

    stmt = (
        select(EntityBase)
        .join(
            EntityScore,
            and_(
                EntityScore.entity_id == EntityBase.entity_id,
                EntityScore.score_profile == "general",
            ),
        )
        .where(
            EntityBase.entity_type == entity_type,
            EntityBase.city_code == city_code,
            EntityBase.is_active == True,  # noqa: E712
            EntityBase.entity_id.not_in(list(exclude_ids)) if exclude_ids else True,
        )
        .order_by(EntityScore.final_score.desc())
        .limit(20)
    )

    # area_hint 过滤
    if area_strict and area_hint:
        stmt = stmt.where(
            EntityBase.area_name.ilike(f"%{area_hint}%")
        )

    # 数据层级优先（S/A 先，B 作 fallback）
    stmt = stmt.order_by(
        EntityBase.data_tier.asc(),  # S < A < B（字母序）
        EntityScore.final_score.desc(),
    )

    result = await session.execute(stmt)
    candidates = result.scalars().all()

    # 应用 tags_required 过滤（软过滤）
    if tags_required_list:
        candidates = await _filter_by_tags(session, candidates, tags_required_list)

    # 应用 filter_exclude_tags（排除夜生活等）
    if filter_exclude_tags:
        candidates = await _exclude_by_tags(session, candidates, filter_exclude_tags)

    return list(candidates)


async def _filter_by_tags(
    session: AsyncSession,
    candidates: list[EntityBase],
    tags_required: list[str] | dict[str, int],
) -> list[EntityBase]:
    """按标签过滤候选实体。

    支持两种格式：
    - list[str]：标签名列表，实体包含任一标签即可（OR 语义）
    - dict[str, int]：{theme: min_score}，所有条件必须满足（AND 语义）
    """
    if not candidates or not tags_required:
        return candidates

    entity_ids = [e.entity_id for e in candidates]

    # 查询所有候选实体的标签（tag_value 可能是标签名或 "theme:score" 格式）
    result = await session.execute(
        select(EntityTag).where(
            EntityTag.entity_id.in_(entity_ids),
        )
    )
    all_tags = result.scalars().all()

    # 建立 entity_id → tag_set 映射
    tag_set_map: dict[uuid.UUID, set[str]] = {}
    tag_score_map: dict[uuid.UUID, dict[str, int]] = {}
    for tag in all_tags:
        eid = tag.entity_id
        tag_set_map.setdefault(eid, set())
        tag_score_map.setdefault(eid, {})
        val = tag.tag_value or ""
        tag_set_map[eid].add(val.lower())
        # 支持 "theme:score" 格式
        parts = val.split(":", 1)
        if len(parts) == 2:
            try:
                tag_score_map[eid][parts[0].lower()] = int(parts[1])
            except ValueError:
                pass
        else:
            tag_score_map[eid][val.lower()] = 1

    filtered = []
    if isinstance(tags_required, list):
        # OR 语义：包含任一标签即可
        required_lower = {t.lower() for t in tags_required}
        for entity in candidates:
            eid = entity.entity_id
            entity_tag_set = tag_set_map.get(eid, set())
            entity_score_keys = set(tag_score_map.get(eid, {}).keys())
            if entity_tag_set & required_lower or entity_score_keys & required_lower:
                filtered.append(entity)
    else:
        # AND+最低分语义
        for entity in candidates:
            eid = entity.entity_id
            scores = tag_score_map.get(eid, {})
            meets = all(
                scores.get(theme.lower(), 0) >= min_score
                for theme, min_score in tags_required.items()
            )
            if meets:
                filtered.append(entity)

    return filtered if filtered else candidates  # 无候选时返回全量（降级）


async def _exclude_by_tags(
    session: AsyncSession,
    candidates: list[EntityBase],
    filter_exclude_tags: dict[str, int],
) -> list[EntityBase]:
    """排除含有超标标签的实体（如家庭游排除夜生活 >= 3 的实体）。"""
    if not candidates or not filter_exclude_tags:
        return candidates

    entity_ids = [e.entity_id for e in candidates]
    result = await session.execute(
        select(EntityTag).where(
            EntityTag.entity_id.in_(entity_ids),
            EntityTag.tag_namespace == "affinity",
        )
    )
    all_tags = result.scalars().all()

    # 建立排除集合
    exclude_ids: set[uuid.UUID] = set()
    tag_map: dict[uuid.UUID, dict[str, int]] = {}
    for tag in all_tags:
        parts = tag.tag_value.split(":", 1)
        if len(parts) == 2:
            try:
                tag_map.setdefault(tag.entity_id, {})[parts[0]] = int(parts[1])
            except ValueError:
                pass

    for eid, tags in tag_map.items():
        for theme, threshold in filter_exclude_tags.items():
            if tags.get(theme, 0) >= threshold:
                exclude_ids.add(eid)

    return [e for e in candidates if e.entity_id not in exclude_ids]


# ─── 天数裁剪 / 扩展 ──────────────────────────────────────────────────────────

def trim_to_days(template: dict, target_days: int) -> dict:
    """将模板裁剪或扩展到指定天数。

    裁剪逻辑 (target < template):
        - 保留前 target 天
        - 最后一天强制替换为模板最后一天（收尾主题）

    扩展逻辑 (target > template):
        - 保留全部模板天数
        - 多出的天数自动填充"自由活动日"
        - 自由活动日只有 morning + lunch + afternoon 三个轻量 slot
    """
    import copy

    tmpl = copy.deepcopy(template)
    original_days = tmpl.get("days", [])
    n_original = len(original_days)

    if target_days == n_original:
        return tmpl

    if target_days < n_original:
        # 裁剪：取前 (target-1) 天 + 原始最后一天
        if target_days <= 0:
            target_days = 1
        if target_days == 1:
            trimmed = [original_days[-1]]
        else:
            trimmed = original_days[:target_days - 1] + [original_days[-1]]
        # 重新编号 day
        for i, d in enumerate(trimmed):
            d["day"] = i + 1
        tmpl["days"] = trimmed

    else:
        # 扩展：保留全部 + 追加自由活动日
        for extra_i in range(n_original + 1, target_days + 1):
            # 复用前几天的 city_code（循环）
            ref_day = original_days[(extra_i - 1) % n_original]
            city_code = ref_day.get("city_code", "tokyo")
            free_day = {
                "day": extra_i,
                "theme_zh": f"自由活动日 — 深度探索{city_code}",
                "city_code": city_code,
                "time_blocks": [
                    {
                        "slot_id": f"d{extra_i}_morning",
                        "time": "10:00",
                        "duration_min": 120,
                        "tags_required": ["park", "garden", "nature", "culture"],
                        "area_hint": None,
                        "fallback_entity_id": None,
                        "note_zh": "自由探索 — 选择自己感兴趣的景点"
                    },
                    {
                        "slot_id": f"d{extra_i}_lunch",
                        "time": "12:30",
                        "duration_min": 60,
                        "tags_required": ["restaurant", "japanese"],
                        "area_hint": None,
                        "fallback_entity_id": None,
                        "note_zh": "午餐"
                    },
                    {
                        "slot_id": f"d{extra_i}_afternoon",
                        "time": "14:30",
                        "duration_min": 120,
                        "tags_required": ["shopping", "culture", "museum"],
                        "area_hint": None,
                        "fallback_entity_id": None,
                        "note_zh": "下午自由活动 — 购物或博物馆"
                    },
                ],
            }
            original_days.append(free_day)
        tmpl["days"] = original_days

    tmpl["total_days"] = target_days
    return tmpl


# ─── 主装配函数 ────────────────────────────────────────────────────────────────

async def assemble_trip(
    session: AsyncSession,
    trip_request_id: uuid.UUID,
    template_code: str,
    scene: str = "general",
) -> uuid.UUID:
    """
    主装配函数：模板 + 评分 → 结构化行程写入 DB。

    Returns:
        plan_id: 新创建的 ItineraryPlan 的 UUID
    """
    start_time = time.time()
    logger.info("开始装配行程 trip=%s template=%s scene=%s", trip_request_id, template_code, scene)

    # 1. 加载并应用场景变体
    template = await load_template(session, template_code)
    template = apply_scene_variant(template, scene)

    # 1b. 天数裁剪/扩展 — 读取 trip_request 的 duration
    from app.db.models.business import TripRequest
    trip_req = await session.get(TripRequest, trip_request_id)
    requested_days: int | None = None
    if trip_req:
        # 优先用 duration_days 字段
        if hasattr(trip_req, "duration_days") and trip_req.duration_days:
            requested_days = trip_req.duration_days
        elif hasattr(trip_req, "cities") and trip_req.cities:
            # fallback: cities[*].nights 求和 + 1
            total_nights = sum(c.get("nights", 0) for c in trip_req.cities)
            if total_nights > 0:
                requested_days = total_nights + 1

    template_days = len(template.get("days", []))
    if requested_days and requested_days != template_days:
        logger.info("天数裁剪: 模板%d天 → 请求%d天", template_days, requested_days)
        template = trim_to_days(template, requested_days)

    # 1c. 读取 TripProfile 的 budget_focus，叠加到 tag_weight_overrides
    budget_focus: str | None = None
    from app.db.models.business import TripProfile as _TripProfile
    _profile_result = await session.execute(
        select(_TripProfile).where(
            _TripProfile.trip_request_id == trip_request_id
        )
    )
    _profile = _profile_result.scalar_one_or_none()
    if _profile and hasattr(_profile, "budget_focus"):
        budget_focus = _profile.budget_focus

    # budget_focus → tag_weight 映射
    _BUDGET_FOCUS_WEIGHTS: dict[str, dict[str, float]] = {
        "better_stay":       {"hotel_premium": 2.0, "hotel_boutique": 1.5},
        "better_food":       {"restaurant_premium": 2.0, "fine_dining": 1.8, "tabelog_top": 1.5},
        "better_experience": {"unique_experience": 2.0, "hidden_gem": 1.5, "local_authentic": 1.5},
        "balanced":          {},  # 不做额外权重覆盖
        "best_value":        {"budget_friendly": 1.8, "free_entry": 1.5},
    }
    if budget_focus and budget_focus in _BUDGET_FOCUS_WEIGHTS:
        extra_weights = _BUDGET_FOCUS_WEIGHTS[budget_focus]
        if extra_weights:
            logger.info("budget_focus=%s 应用额外权重: %s", budget_focus, extra_weights)
            # 将 budget_focus 权重注入到模板，与场景权重合并
            existing = template.get("_tag_weight_overrides", {})
            merged = {**extra_weights, **existing}  # 场景权重优先
            template["_tag_weight_overrides"] = merged

    meta = template.get("meta", {})
    # 兼容顶层字段和 meta 子对象两种格式
    _city_code_raw = template.get("city_code") or meta.get("city_code") or meta.get("city_codes")
    if isinstance(_city_code_raw, list):
        city_codes: list[str] = _city_code_raw
    elif _city_code_raw:
        city_codes = [_city_code_raw]
    else:
        city_codes = ["tokyo"]
    total_days: int = (
        template.get("total_days") or meta.get("total_days") or len(template.get("days", []))
    )
    tag_weight_overrides = template.get("_tag_weight_overrides", {})
    filter_exclude_tags = template.get("_filter_exclude_tags", {})

    # 1d. 构建三维评分 user_weights
    user_weights, segment_pack_id, stage_pack_id = await _build_user_weights(
        session, trip_request_id, stage="standard",
    )

    # 2. 创建 PlannerRun 追溯记录
    planner_run = PlannerRun(
        trip_request_id=trip_request_id,
        status="running",
        algorithm_version="assembler-v2-3d",
        run_params={
            "template_code": template_code,
            "scene": scene,
            "city_codes": city_codes,
            "segment_pack": segment_pack_id,
            "stage_pack": stage_pack_id,
        },
        started_at=datetime.now(tz=timezone.utc),
    )
    session.add(planner_run)
    await session.flush()  # 获取 planner_run_id

    # 3. 创建 ItineraryPlan
    plan = ItineraryPlan(
        trip_request_id=trip_request_id,
        planner_run_id=planner_run.planner_run_id,
        status="assembling",
        plan_metadata={
            "template_code": template_code,
            "scene": scene,
            "total_days": total_days,
            "city_codes": city_codes,
            "template_meta": meta,
        },
    )
    session.add(plan)
    await session.flush()  # 获取 plan_id

    # 4. 逐日逐槽位装配
    used_entity_ids: set[uuid.UUID] = set()
    entity_ids_log: list[str] = []
    days_data = template.get("days", [])

    for day_data in days_data:
        # 兼容 day_num / day 两种字段名
        day_num: int = day_data.get("day_num") or day_data.get("day", 1)
        city_code = day_data.get("city_code") or (city_codes[0] if city_codes else "tokyo")
        if len(city_codes) > 1 and day_num > (total_days // 2):
            city_code = city_codes[-1]

        # 创建 ItineraryDay
        itinerary_day = ItineraryDay(
            plan_id=plan.plan_id,
            day_number=day_num,
            city_code=city_code,
            day_theme=day_data.get("theme_zh"),
            day_summary_zh=day_data.get("area_zh"),
        )
        session.add(itinerary_day)
        await session.flush()

        # 逐槽位填充
        time_blocks = day_data.get("time_blocks", [])
        for sort_idx, slot in enumerate(time_blocks):
            # 兼容 slot_type 字段缺失（从 tags 推断）
            slot_type = slot.get("slot_type", "")
            # duration 字段兼容两种命名
            duration_min = slot.get("duration_min") or slot.get("duration_minutes", 60)

            # hotel_area / transport 不需要实体（按 slot_id 后缀也可判断）
            slot_id_lower = slot.get("slot_id", "").lower()
            if slot_type in ("hotel_area", "transport") or any(
                kw in slot_id_lower for kw in ("hotel", "checkin", "checkout", "transport", "transfer")
            ):
                item = ItineraryItem(
                    day_id=itinerary_day.day_id,
                    sort_order=sort_idx,
                    item_type=slot_type,
                    entity_id=None,
                    duration_min=duration_min,
                    notes_zh=slot.get("notes_zh") or day_data.get("transport_notes_zh"),
                )
                session.add(item)
                continue

            # 召回候选（先严格 area，再全城市 fallback）
            candidates = await fetch_slot_candidates(
                session, slot, city_code, used_entity_ids,
                tag_weight_overrides=tag_weight_overrides,
                filter_exclude_tags=filter_exclude_tags,
                area_strict=True,
            )
            if not candidates:
                candidates = await fetch_slot_candidates(
                    session, slot, city_code, used_entity_ids,
                    tag_weight_overrides=tag_weight_overrides,
                    filter_exclude_tags=filter_exclude_tags,
                    area_strict=False,
                )

            # 三维评分重排序（用 user_weights + entity_affinity + soft_rule_score）
            if candidates:
                candidates = await _rescore_candidates(
                    session, candidates, user_weights, segment_pack_id, stage_pack_id,
                )

            # 选 Top 1
            chosen_entity: EntityBase | None = candidates[0] if candidates else None

            if chosen_entity:
                used_entity_ids.add(chosen_entity.entity_id)
                entity_ids_log.append(str(chosen_entity.entity_id))
                entity_type = chosen_entity.entity_type
            else:
                # fallback_entity_id 处理
                fallback_id = slot.get("fallback_entity_id")
                if fallback_id:
                    chosen_entity = await session.get(EntityBase, uuid.UUID(fallback_id))
                    if chosen_entity:
                        used_entity_ids.add(chosen_entity.entity_id)
                        entity_ids_log.append(str(chosen_entity.entity_id))
                entity_type = slot_type

            item = ItineraryItem(
                day_id=itinerary_day.day_id,
                sort_order=sort_idx,
                item_type=entity_type,
                entity_id=chosen_entity.entity_id if chosen_entity else None,
                duration_min=duration_min,
                notes_zh=None,  # 后续由 ai-copywriter 填充
                is_optional=chosen_entity is None,  # 无实体时标记为可选
            )
            session.add(item)

    # 5. 装配后交通时间校验
    route_warnings = await _post_check_commute(session, plan.plan_id)

    # 6. 更新 PlannerRun 完成状态
    elapsed_ms = int((time.time() - start_time) * 1000)
    planner_run.status = "completed"
    planner_run.completed_at = datetime.now(tz=timezone.utc)
    planner_run.run_log = {
        "entity_ids_used": entity_ids_log,
        "total_entities": len(entity_ids_log),
        "duration_ms": elapsed_ms,
        "route_warnings_count": len(route_warnings),
    }

    # 7. 更新 ItineraryPlan 状态 + 写入 route_warnings
    plan.status = "reviewing"
    plan_meta = plan.plan_metadata or {}
    plan_meta["route_warnings"] = route_warnings
    plan_meta["segment_pack"] = segment_pack_id
    plan_meta["stage_pack"] = stage_pack_id
    plan.plan_metadata = plan_meta

    await session.commit()
    logger.info(
        "装配完成 plan=%s 用时 %dms，实体 %d 个，交通警告 %d 条",
        plan.plan_id, elapsed_ms, len(entity_ids_log), len(route_warnings),
    )

    return plan.plan_id


# ─── 装配后交通时间校验 ────────────────────────────────────────────────────────

COMMUTE_WARNING_THRESHOLD_MIN = 45  # 超过此阈值的相邻实体对记录为 warning

async def _post_check_commute(
    session: AsyncSession,
    plan_id: uuid.UUID,
) -> list[dict]:
    """遍历每天相邻实体对，调用 route_matrix 检查通勤时间。

    Returns:
        route_warnings: [{day, from_entity, to_entity, duration_min}]
    """
    from app.domains.planning.route_matrix import get_travel_time

    warnings: list[dict] = []

    # 查所有天
    days_result = await session.execute(
        select(ItineraryDay).where(ItineraryDay.plan_id == plan_id).order_by(ItineraryDay.day_number)
    )
    days = days_result.scalars().all()

    for day in days:
        # 查当天所有有实体的 items（按 sort_order）
        items_result = await session.execute(
            select(ItineraryItem).where(
                ItineraryItem.day_id == day.day_id,
                ItineraryItem.entity_id.is_not(None),
            ).order_by(ItineraryItem.sort_order)
        )
        items = items_result.scalars().all()

        # 相邻实体对
        for i in range(len(items) - 1):
            origin_id = items[i].entity_id
            dest_id = items[i + 1].entity_id
            if not origin_id or not dest_id:
                continue

            try:
                travel = await get_travel_time(session, origin_id, dest_id, mode="transit")
                duration = travel.get("duration_min", 0) if travel else 0
            except Exception:
                # route_matrix 不可用时跳过，不阻塞装配
                logger.debug("route_matrix 查询失败: %s → %s", origin_id, dest_id)
                continue

            if duration > COMMUTE_WARNING_THRESHOLD_MIN:
                warnings.append({
                    "day": day.day_number,
                    "from_entity": str(origin_id),
                    "to_entity": str(dest_id),
                    "duration_min": duration,
                })
                logger.warning(
                    "通勤超标 Day%d: %s → %s = %d min",
                    day.day_number, origin_id, dest_id, duration,
                )

    return warnings


# ─── 文案批量更新（Task 3.5）────────────────────────────────────────────────────

async def enrich_itinerary_with_copy(
    session: AsyncSession,
    plan_id: uuid.UUID,
    scene: str,
    redis_client=None,
) -> None:
    """
    装配完成后批量调用 AI 文案润色，更新 itinerary_items.notes_zh。

    notes_zh 使用 JSON 格式存储文案：
        {"copy_zh": "...", "tips_zh": "...", "_source": "ai"}

    Args:
        session:      AsyncSession
        plan_id:      ItineraryPlan 的 UUID
        scene:        场景（couple / family / solo / general）
        redis_client: Redis 连接（可选，None 时跳过缓存）
    """
    from app.domains.planning.copywriter import batch_generate_copy

    logger.info("开始 AI 文案润色 plan=%s scene=%s", plan_id, scene)

    # 1. 查询所有 days 和 items
    days_result = await session.execute(
        select(ItineraryDay).where(ItineraryDay.plan_id == plan_id)
    )
    days = days_result.scalars().all()

    # 2. 收集所有需要文案的 items + entities
    items_with_entities: list[tuple[ItineraryItem, EntityBase]] = []
    for day in days:
        items_result = await session.execute(
            select(ItineraryItem).where(
                ItineraryItem.day_id == day.day_id,
                ItineraryItem.entity_id.is_not(None),
            )
        )
        items = items_result.scalars().all()
        for item in items:
            # 使用 selectinload eager load tags 关系，避免 async session 中
            # _get_tags_str 访问 entity.tags 时触发 lazy load → MissingGreenlet 异常
            entity_result = await session.execute(
                select(EntityBase)
                .options(selectinload(EntityBase.tags))
                .where(EntityBase.entity_id == item.entity_id)
            )
            entity = entity_result.scalar_one_or_none()
            if entity:
                items_with_entities.append((item, entity))

    if not items_with_entities:
        logger.info("无需文案润色的实体（plan=%s）", plan_id)
        return

    # 3. 查询编辑备注
    entity_ids = [e.entity_id for _, e in items_with_entities]
    editorial_result = await session.execute(
        select(EntityEditorNote).where(
            EntityEditorNote.entity_id.in_(entity_ids)
        )
    )
    editorial_map: dict[str, str] = {}
    for note in editorial_result.scalars().all():
        eid = str(note.entity_id)
        reason = getattr(note, "reason_zh", "") or getattr(note, "editorial_reason", "") or ""
        if reason:
            editorial_map[eid] = reason

    # 4. 批量生成文案
    copy_map = await batch_generate_copy(
        items_with_entities, scene, redis_client, editorial_map
    )

    # 5. 回写 notes_zh（JSON 格式）
    import json as _json
    updated = 0
    for item, entity in items_with_entities:
        eid = str(entity.entity_id)
        if eid in copy_map:
            copy_data = copy_map[eid]
            item.notes_zh = _json.dumps(
                {**copy_data, "_source": "ai"},
                ensure_ascii=False,
            )
            updated += 1

    await session.commit()
    logger.info("文案润色完成 plan=%s，更新 %d 条 notes_zh", plan_id, updated)
