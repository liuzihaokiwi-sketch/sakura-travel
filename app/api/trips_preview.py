"""
GET /trips/{id}/preview-data → 返回结构化预览数据

为 H5 预览页提供所需的所有数据：
- 选出的最佳预览天（完整展示，部分条目锁定）
- 其他天的摘要（仅 theme + city + item count）
- SKU 信息（从 product_config.json 读取）
"""

from __future__ import annotations

import json
import logging
import random
import uuid
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.catalog import EntityBase
from app.db.models.derived import ItineraryDay, ItineraryItem, ItineraryPlan
from app.db.session import get_db
from app.domains.ranking.soft_rules.preview_engine import select_preview_day

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trips", tags=["trips-preview"])


# ── 配置加载 ──────────────────────────────────────────────────────────────────

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "data" / "config" / "product_config.json"
_config_cache: dict | None = None


def _load_config() -> dict:
    global _config_cache
    if _config_cache is None:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            _config_cache = json.load(f)
    return _config_cache


# ── 响应模型 ──────────────────────────────────────────────────────────────────

class PreviewItemOut(BaseModel):
    time: Optional[str] = None
    icon: Optional[str] = None
    name: str
    entity_type: str
    reason: Optional[str] = None
    is_locked: bool = False
    teaser: Optional[str] = None


class PreviewDayOut(BaseModel):
    day_number: int
    theme: str
    city: str
    items: list[PreviewItemOut]
    is_preview_day: bool


class SkuOut(BaseModel):
    price: int
    name: str
    tagline: str
    cta_text: str


class PreviewDataOut(BaseModel):
    plan_id: str
    total_days: int
    preview_day_index: int
    days: list[PreviewDayOut]
    sku: SkuOut


# ── Entity Icon 映射 ─────────────────────────────────────────────────────────

ENTITY_ICONS = {
    "poi": "📍",
    "restaurant": "🍜",
    "hotel": "🏨",
    "transit": "🚃",
    "free_time": "☕",
    "note": "📝",
}


# ── 工具函数 ──────────────────────────────────────────────────────────────────

def _should_lock_item(
    item_index: int,
    total_items: int,
    lock_ratio: float,
) -> bool:
    """
    决定预览天中的某条目是否应该锁定。

    策略：保留前几个 + 中间的高光 → 锁定后面的。
    具体：前 2 个永不锁 + 最后 1 个永不锁（作为 cliffhanger），中间按 lock_ratio 随机锁。
    """
    if total_items <= 3:
        return False  # 太少了不锁

    # 前 2 个和最后 1 个不锁
    if item_index < 2 or item_index == total_items - 1:
        return False

    # 中间部分按比例锁定
    middle_count = total_items - 3
    locked_count = max(1, round(middle_count * lock_ratio))

    # 用确定性的方式选锁定位置（不是完全随机，保证每次渲染一致）
    # 锁定中间段偏后的条目（用户已被前面吸引，后面锁住制造悬念）
    middle_start = 2
    middle_end = total_items - 1
    lock_start = middle_end - locked_count

    return item_index >= lock_start


def _get_random_teaser(templates: list[str], item_type: str) -> str:
    """根据条目类型选择合适的 teaser 文案。"""
    type_specific = {
        "restaurant": "这里有一家当地人才知道的店…",
        "transit": "付费版包含详细交通指引",
        "poi": "解锁查看隐藏的小众景点",
    }
    if item_type in type_specific:
        return type_specific[item_type]
    return random.choice(templates) if templates else "解锁完整版查看详情"


# ── 主端点 ────────────────────────────────────────────────────────────────────

@router.get("/{trip_request_id}/preview-data", response_model=PreviewDataOut)
async def get_preview_data(
    trip_request_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    返回 H5 预览页所需的结构化数据。

    流程：
    1. 查询 plan → days → items → entity
    2. 调用 preview_engine.select_preview_day() 选最佳天
    3. 构建预览天完整数据（部分锁定）+ 其他天摘要
    4. 附加 SKU 信息
    """
    # ── 参数校验 ──
    try:
        req_uuid = uuid.UUID(trip_request_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid trip_request_id format")

    # ── 查询 Plan ──
    plan_result = await db.execute(
        select(ItineraryPlan)
        .where(ItineraryPlan.trip_request_id == req_uuid)
        .order_by(ItineraryPlan.version.desc())
        .limit(1)
    )
    plan = plan_result.scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail="No itinerary plan found")

    # ── 查询 Days + Items ──
    days_result = await db.execute(
        select(ItineraryDay)
        .where(ItineraryDay.plan_id == plan.plan_id)
        .order_by(ItineraryDay.day_number)
    )
    days = days_result.scalars().all()

    if not days:
        raise HTTPException(status_code=404, detail="Itinerary has no days")

    # 收集所有 entity_id 用于批量查询
    all_entity_ids: set[uuid.UUID] = set()
    days_items: list[list[ItineraryItem]] = []

    for day in days:
        items_result = await db.execute(
            select(ItineraryItem)
            .where(ItineraryItem.day_id == day.day_id)
            .order_by(ItineraryItem.sort_order)
        )
        items = items_result.scalars().all()
        days_items.append(items)
        for item in items:
            if item.entity_id:
                all_entity_ids.add(item.entity_id)

    # ── 批量查询 Entity 信息 ──
    entity_map: dict[uuid.UUID, EntityBase] = {}
    if all_entity_ids:
        entity_result = await db.execute(
            select(EntityBase)
            .where(EntityBase.entity_id.in_(list(all_entity_ids)))
        )
        for entity in entity_result.scalars().all():
            entity_map[entity.entity_id] = entity

    # ── 构建 preview engine 输入 ──
    itinerary_for_engine: list[list[dict]] = []
    for items in days_items:
        day_dicts = []
        for item in items:
            entity = entity_map.get(item.entity_id) if item.entity_id else None
            d: dict[str, Any] = {
                "entity_type": item.item_type,
                "type": item.item_type,
                "time_slot": item.start_time or "",
                "soft_rule_score": None,
                "soft_scores": {},
            }
            if entity:
                d["name"] = entity.name_zh
                d["entity_type"] = entity.entity_type
            day_dicts.append(d)
        itinerary_for_engine.append(day_dicts)

    # ── 调用 Preview Engine ──
    preview_result = select_preview_day(
        itinerary_days=itinerary_for_engine,
        arrival_day_index=0,
        departure_day_index=len(days) - 1 if len(days) > 1 else None,
    )

    selected_idx = preview_result.selected_day_index
    logger.info(
        "Preview day for trip %s: Day %d (%s)",
        trip_request_id,
        selected_idx + 1,
        preview_result.selection_reason,
    )

    # ── 加载配置 ──
    config = _load_config()
    preview_cfg = config.get("preview", {})
    lock_ratio = preview_cfg.get("lock_ratio", 0.35)
    teaser_templates = preview_cfg.get("lock_teaser_templates", [])
    default_sku_key = preview_cfg.get("default_sku", "premium_248")
    sku_data = config.get("skus", {}).get(default_sku_key, {})

    # ── 构建输出 ──
    days_out: list[PreviewDayOut] = []

    for day_idx, (day, items) in enumerate(zip(days, days_items)):
        is_preview = day_idx == selected_idx

        if is_preview:
            # 预览天：展示完整条目，部分锁定
            preview_items: list[PreviewItemOut] = []
            total = len(items)

            for item_idx, item in enumerate(items):
                entity = entity_map.get(item.entity_id) if item.entity_id else None
                locked = _should_lock_item(item_idx, total, lock_ratio)

                if locked:
                    preview_items.append(PreviewItemOut(
                        time=item.start_time,
                        icon="🔒",
                        name="???",
                        entity_type=item.item_type,
                        is_locked=True,
                        teaser=_get_random_teaser(teaser_templates, item.item_type),
                    ))
                else:
                    name = entity.name_zh if entity else (item.notes_zh or item.item_type)
                    preview_items.append(PreviewItemOut(
                        time=item.start_time,
                        icon=ENTITY_ICONS.get(item.item_type, "📌"),
                        name=name,
                        entity_type=entity.entity_type if entity else item.item_type,
                        reason=item.notes_zh if entity else None,
                    ))

            days_out.append(PreviewDayOut(
                day_number=day.day_number,
                theme=day.day_theme or f"Day {day.day_number}",
                city=day.city_code,
                items=preview_items,
                is_preview_day=True,
            ))
        else:
            # 非预览天：仅摘要（条目为空）
            days_out.append(PreviewDayOut(
                day_number=day.day_number,
                theme=day.day_theme or f"Day {day.day_number}",
                city=day.city_code,
                items=[],
                is_preview_day=False,
            ))

    return PreviewDataOut(
        plan_id=str(plan.plan_id),
        total_days=len(days),
        preview_day_index=selected_idx,
        days=days_out,
        sku=SkuOut(
            price=sku_data.get("price", 248),
            name=sku_data.get("name", "日本定制行程"),
            tagline=sku_data.get("tagline", ""),
            cta_text=sku_data.get("cta_text", "解锁完整方案"),
        ),
    )
