"""
自助微调 API — Self-Serve Tuning

端点：
  GET  /trips/{id}/swap-candidates?item_id=xxx  → 获取候选列表
  POST /trips/{id}/swap                         → 执行替换
  POST /trips/{id}/swap/undo                    → 撤销上一次替换
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.catalog import EntityBase
from app.db.models.derived import ItineraryDay, ItineraryItem, ItineraryPlan
from app.db.models.soft_rules import EntitySoftScore
from app.db.session import get_db
from app.domains.ranking.soft_rules.swap_engine import rank_swap_candidates, SwapCandidate
from app.domains.ranking.soft_rules.swap_safety import validate_swap

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/trips", tags=["self-serve-tuning"])

# ── 冷却限制 ───────────────────────────────────────────────────────────────────
MAX_SWAPS_PER_ENTITY_24H = 5


# ── 请求/响应模型 ──────────────────────────────────────────────────────────────

class SwapCandidateOut(BaseModel):
    entity_id: str
    entity_type: str
    name: str
    name_zh: Optional[str]
    area_name: Optional[str]
    swap_score: float
    context_fit: float
    soft_rule_score: float
    slot_compatibility: float
    differentiation: float
    swap_reason: str
    impact_level: str
    estimated_score_change: float


class SwapCandidatesResponse(BaseModel):
    target_entity_id: str
    target_name: str
    candidates: list[SwapCandidateOut]
    pool_size: int
    message: str


class SwapRequest(BaseModel):
    item_id: int
    new_entity_id: str


class SwapResponse(BaseModel):
    success: bool
    impact_level: str
    score_before: float
    score_after: float
    score_change_pct: float
    user_message: str
    guardrail_issues: list[dict]
    can_undo: bool


class UndoRequest(BaseModel):
    item_id: int


# ── 获取候选 ───────────────────────────────────────────────────────────────────

@router.get("/{trip_request_id}/swap-candidates", response_model=SwapCandidatesResponse)
async def get_swap_candidates(
    trip_request_id: str,
    item_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取某个行程条目的替换候选列表。"""
    # 查找 item
    item_result = await db.execute(
        select(ItineraryItem).where(ItineraryItem.item_id == item_id)
    )
    item = item_result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Item not found")

    if not item.entity_id:
        raise HTTPException(400, "This item has no entity to swap")

    # 查找 day
    day_result = await db.execute(
        select(ItineraryDay).where(ItineraryDay.day_id == item.day_id)
    )
    day = day_result.scalar_one_or_none()
    if not day:
        raise HTTPException(404, "Day not found")

    # 查找当前实体
    target_entity = await db.execute(
        select(EntityBase).where(EntityBase.entity_id == item.entity_id)
    )
    target = target_entity.scalar_one_or_none()
    if not target:
        raise HTTPException(404, "Target entity not found")

    # 获取同天其他 items
    day_items_result = await db.execute(
        select(ItineraryItem)
        .where(ItineraryItem.day_id == item.day_id)
        .order_by(ItineraryItem.sort_order)
    )
    day_items = day_items_result.scalars().all()

    # 前后 item 的区域
    item_idx = next((i for i, di in enumerate(day_items) if di.item_id == item_id), 0)
    prev_area = None
    next_area = None
    if item_idx > 0:
        prev_eid = day_items[item_idx - 1].entity_id
        if prev_eid:
            prev_e = (await db.execute(select(EntityBase).where(EntityBase.entity_id == prev_eid))).scalar_one_or_none()
            if prev_e:
                prev_area = prev_e.area_code if hasattr(prev_e, 'area_code') else None
    if item_idx < len(day_items) - 1:
        next_eid = day_items[item_idx + 1].entity_id
        if next_eid:
            next_e = (await db.execute(select(EntityBase).where(EntityBase.entity_id == next_eid))).scalar_one_or_none()
            if next_e:
                next_area = next_e.area_code if hasattr(next_e, 'area_code') else None

    # 构建候选池：同城市同类型的实体
    candidate_query = (
        select(EntityBase)
        .where(
            EntityBase.entity_type == target.entity_type,
            EntityBase.city_code == target.city_code,
            EntityBase.entity_id != target.entity_id,
        )
        .limit(50)
    )
    cand_result = await db.execute(candidate_query)
    candidates_raw = cand_result.scalars().all()

    # 批量获取软规则分数
    cand_ids = [c.entity_id for c in candidates_raw]
    soft_scores_map: dict[uuid.UUID, float] = {}
    if cand_ids:
        ss_result = await db.execute(
            select(EntitySoftScore)
            .where(EntitySoftScore.entity_id.in_(cand_ids))
        )
        for ss in ss_result.scalars().all():
            # 取 12 维均值作为整体 soft score
            dims = [
                ss.emotional_value, ss.shareability, ss.relaxation_feel,
                ss.memory_point, ss.localness, ss.smoothness,
                ss.food_certainty, ss.night_completion, ss.recovery_friendliness,
                ss.weather_resilience_soft, ss.professional_judgement_feel,
                ss.preview_conversion_power,
            ]
            valid = [float(d) for d in dims if d is not None]
            soft_scores_map[ss.entity_id] = sum(valid) / len(valid) if valid else 5.0

    # 转换为 swap engine 需要的 dict 格式
    target_dict = _entity_to_dict(target, soft_scores_map.get(target.entity_id, 5.0))
    pool = [_entity_to_dict(c, soft_scores_map.get(c.entity_id, 5.0)) for c in candidates_raw]

    day_items_dicts = [
        {"entity_id": str(di.entity_id) if di.entity_id else None, "entity_type": di.item_type}
        for di in day_items
    ]

    # 调用 swap engine
    time_slot = _infer_time_slot(item.start_time)
    result = rank_swap_candidates(
        target_entity=target_dict,
        candidate_pool=pool,
        time_slot=time_slot,
        prev_item_area=prev_area,
        next_item_area=next_area,
        day_items=day_items_dicts,
        max_results=5,
    )

    return SwapCandidatesResponse(
        target_entity_id=str(target.entity_id),
        target_name=target.name_zh or target.name_local or "",
        candidates=[
            SwapCandidateOut(
                entity_id=c.entity_id,
                entity_type=c.entity_type,
                name=c.name,
                name_zh=c.name_zh,
                area_name=c.area_name,
                swap_score=c.swap_score,
                context_fit=c.context_fit,
                soft_rule_score=c.soft_rule_score,
                slot_compatibility=c.slot_compatibility,
                differentiation=c.differentiation,
                swap_reason=c.swap_reason,
                impact_level=c.impact_level,
                estimated_score_change=c.estimated_score_change,
            )
            for c in result.candidates
        ],
        pool_size=result.pool_size,
        message=result.message,
    )


# ── 执行替换 ───────────────────────────────────────────────────────────────────

@router.post("/{trip_request_id}/swap", response_model=SwapResponse)
async def execute_swap(
    trip_request_id: str,
    body: SwapRequest,
    db: AsyncSession = Depends(get_db),
):
    """执行自助替换，包含安全检查。"""
    item_result = await db.execute(
        select(ItineraryItem).where(ItineraryItem.item_id == body.item_id)
    )
    item = item_result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Item not found")

    old_entity_id = item.entity_id
    new_entity_id = uuid.UUID(body.new_entity_id)

    # 验证新实体存在
    new_entity_result = await db.execute(
        select(EntityBase).where(EntityBase.entity_id == new_entity_id)
    )
    new_entity = new_entity_result.scalar_one_or_none()
    if not new_entity:
        raise HTTPException(404, "New entity not found")

    # 获取当天所有 items
    day_items_result = await db.execute(
        select(ItineraryItem)
        .where(ItineraryItem.day_id == item.day_id)
        .order_by(ItineraryItem.sort_order)
    )
    day_items = day_items_result.scalars().all()

    # 构建替换前后的 day_items dict
    item_idx = next((i for i, di in enumerate(day_items) if di.item_id == body.item_id), 0)

    before_dicts = [_item_to_safety_dict(di) for di in day_items]
    after_dicts = list(before_dicts)
    after_dicts[item_idx] = {
        **after_dicts[item_idx],
        "entity_id": str(new_entity_id),
        "name": new_entity.name_zh or new_entity.name_local or "",
        "entity_type": new_entity.entity_type,
    }

    # 获取 day_of_week
    day_result = await db.execute(
        select(ItineraryDay).where(ItineraryDay.day_id == item.day_id)
    )
    day = day_result.scalar_one_or_none()
    day_of_week = _date_to_dow(day.date) if day and day.date else None

    # 运行安全检查
    safety = await validate_swap(
        day_items_before=before_dicts,
        day_items_after=after_dicts,
        swap_target_index=item_idx,
        replacement_entity={"soft_rule_score": 50},
        day_number=day.day_number if day else 1,
        day_of_week=day_of_week,
    )

    # 如果有 hard_fail，不执行替换
    if not safety.is_safe:
        return SwapResponse(
            success=False,
            impact_level=safety.impact_level,
            score_before=safety.score_before,
            score_after=safety.score_after,
            score_change_pct=safety.score_change_pct,
            user_message=safety.user_message,
            guardrail_issues=[
                {"rule_id": g.rule_id, "severity": g.severity, "description": g.description}
                for g in safety.guardrail_issues
            ],
            can_undo=False,
        )

    # 执行替换：保存旧值到 swap_candidates（用于 undo）
    undo_data = {
        "previous_entity_id": str(old_entity_id) if old_entity_id else None,
        "swapped_at": datetime.now(timezone.utc).isoformat(),
        "swap_reason": "self_serve",
    }

    await db.execute(
        update(ItineraryItem)
        .where(ItineraryItem.item_id == body.item_id)
        .values(
            entity_id=new_entity_id,
            swap_candidates=undo_data,
        )
    )
    await db.commit()

    logger.info(
        "Swap executed: item=%d, %s → %s, impact=%s",
        body.item_id, old_entity_id, new_entity_id, safety.impact_level,
    )

    return SwapResponse(
        success=True,
        impact_level=safety.impact_level,
        score_before=safety.score_before,
        score_after=safety.score_after,
        score_change_pct=safety.score_change_pct,
        user_message=safety.user_message,
        guardrail_issues=[
            {"rule_id": g.rule_id, "severity": g.severity, "description": g.description}
            for g in safety.guardrail_issues
        ],
        can_undo=True,
    )


# ── 撤销替换 ───────────────────────────────────────────────────────────────────

@router.post("/{trip_request_id}/swap/undo", response_model=SwapResponse)
async def undo_swap(
    trip_request_id: str,
    body: UndoRequest,
    db: AsyncSession = Depends(get_db),
):
    """撤销上一次替换。"""
    item_result = await db.execute(
        select(ItineraryItem).where(ItineraryItem.item_id == body.item_id)
    )
    item = item_result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Item not found")

    undo_data = item.swap_candidates
    if not undo_data or "previous_entity_id" not in undo_data:
        raise HTTPException(400, "No swap to undo")

    previous_id = undo_data["previous_entity_id"]
    if not previous_id:
        raise HTTPException(400, "No previous entity recorded")

    await db.execute(
        update(ItineraryItem)
        .where(ItineraryItem.item_id == body.item_id)
        .values(
            entity_id=uuid.UUID(previous_id),
            swap_candidates=None,
        )
    )
    await db.commit()

    logger.info("Swap undone: item=%d, restored to %s", body.item_id, previous_id)

    return SwapResponse(
        success=True,
        impact_level="green",
        score_before=0,
        score_after=0,
        score_change_pct=0,
        user_message="✅ 已恢复为原来的安排。",
        guardrail_issues=[],
        can_undo=False,
    )


# ── 工具函数 ───────────────────────────────────────────────────────────────────

def _entity_to_dict(entity: EntityBase, soft_score: float) -> dict[str, Any]:
    return {
        "id": str(entity.entity_id),
        "entity_type": entity.entity_type,
        "name": entity.name_local or "",
        "name_zh": entity.name_zh,
        "city_code": entity.city_code,
        "area_code": getattr(entity, "area_code", None),
        "area_name": getattr(entity, "area_name", None),
        "price_level": getattr(entity, "price_level", None),
        "tags": getattr(entity, "tags", []),
        "soft_rule_score": soft_score,
        "valid_time_slots": [],
    }


def _item_to_safety_dict(item: ItineraryItem) -> dict[str, Any]:
    return {
        "entity_id": str(item.entity_id) if item.entity_id else None,
        "entity_type": item.item_type,
        "name": item.notes_zh or item.item_type,
        "start_time": item.start_time,
        "time_slot": _infer_time_slot(item.start_time),
        "soft_rule_score": 50,
    }


def _infer_time_slot(start_time: str | None) -> str:
    if not start_time:
        return "afternoon"
    try:
        hour = int(start_time.split(":")[0])
        if hour < 11:
            return "morning"
        elif hour < 14:
            return "lunch"
        elif hour < 17:
            return "afternoon"
        elif hour < 20:
            return "evening"
        else:
            return "night"
    except (ValueError, IndexError):
        return "afternoon"


def _date_to_dow(date_str: str | None) -> str | None:
    if not date_str:
        return None
    try:
        from datetime import date as dt_date
        d = dt_date.fromisoformat(date_str)
        return ["mon", "tue", "wed", "thu", "fri", "sat", "sun"][d.weekday()]
    except (ValueError, IndexError):
        return None
