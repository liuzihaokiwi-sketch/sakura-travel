"""
refresh_sla.py — T15: 数据新鲜度 SLA 管理 & stale 标记策略

基于 entity_field_provenance.updated_at，
定义每类字段的 refresh SLA（多久算过期），到期自动标记 stale。

两种使用方式：
1. 定时任务（scripts/maintain.py 调用）：扫描全库，批量标记 stale
2. 实时查询：在 precheck_gate / eligibility_gate 中判断实体字段是否可信

字段 SLA 配置：
  - opening_hours_json: 30 天（高频变动）
  - admission_fee_jpy:  90 天（季度调整）
  - google_rating:      60 天（平台数据）
  - typical_duration_*: 180 天（相对稳定）
  - price_band:         90 天
  - lat/lng:            365 天（几乎不变）

source_type 加权：
  - official:      SLA × 1.5（官方数据更稳定）
  - platform:      SLA × 1.0
  - ai_estimated:  SLA × 0.5（AI 推断衰减更快）
  - manual:        SLA × 1.2
  - rule_derived:  SLA × 0.8
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, update, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ── SLA 配置 ──────────────────────────────────────────────────────────────────

# 字段 → 基准 SLA（天）
FIELD_SLA_DAYS: dict[str, int] = {
    # 高频变动
    "opening_hours_json": 30,
    "requires_advance_booking": 30,
    "reservation_difficulty": 30,
    # 中频变动
    "admission_fee_jpy": 90,
    "price_band": 90,
    "price_range_min_jpy": 90,
    "price_range_max_jpy": 90,
    "budget_lunch_jpy": 90,
    "budget_dinner_jpy": 90,
    "typical_price_min_jpy": 90,
    # 平台数据
    "google_rating": 60,
    "google_review_count": 60,
    "booking_score": 60,
    "tabelog_score": 60,
    # 相对稳定
    "typical_duration_min": 180,
    "typical_duration_baseline": 180,
    "poi_category": 365,
    "sub_category": 365,
    "cuisine_type": 365,
    "hotel_type": 365,
    # 极少变动
    "lat": 730,
    "lng": 730,
    "address_ja": 365,
    "address_en": 365,
    "nearest_station": 365,
}

# 默认 SLA（不在配置中的字段）
DEFAULT_SLA_DAYS = 120

# source_type → SLA 倍率
SOURCE_TYPE_MULTIPLIER: dict[str, float] = {
    "official": 1.5,
    "platform": 1.0,
    "ai_estimated": 0.5,
    "manual": 1.2,
    "rule_derived": 0.8,
}


def get_sla_deadline(field_name: str, source_type: str, updated_at: datetime) -> datetime:
    """
    计算给定字段+来源的 SLA 到期时间。

    Args:
        field_name: 字段名
        source_type: 数据来源类型
        updated_at: 最近更新时间

    Returns:
        到期时间点（超过此时间即为 stale）
    """
    base_days = FIELD_SLA_DAYS.get(field_name, DEFAULT_SLA_DAYS)
    multiplier = SOURCE_TYPE_MULTIPLIER.get(source_type, 1.0)
    effective_days = int(base_days * multiplier)
    return updated_at + timedelta(days=effective_days)


def is_stale(field_name: str, source_type: str, updated_at: datetime, now: Optional[datetime] = None) -> bool:
    """判断字段是否已过期。"""
    now = now or datetime.now(timezone.utc)
    deadline = get_sla_deadline(field_name, source_type, updated_at)
    return now > deadline


# ── 批量 stale 扫描 ──────────────────────────────────────────────────────────

async def scan_and_mark_stale(
    session: AsyncSession,
    dry_run: bool = False,
) -> dict:
    """
    扫描 entity_field_provenance 表，将超期记录标记为 stale。

    只处理 review_status IN ('unreviewed', 'approved') 的记录，
    不动 'rejected' 和已经是 'stale' 的。

    Returns:
        {"total_scanned": N, "newly_stale": M, "by_field": {...}}
    """
    from app.db.models.catalog import EntityFieldProvenance

    now = datetime.now(timezone.utc)

    q = await session.execute(
        select(EntityFieldProvenance).where(
            EntityFieldProvenance.review_status.in_(["unreviewed", "approved"])
        )
    )
    records = q.scalars().all()

    stats = {
        "total_scanned": len(records),
        "newly_stale": 0,
        "by_field": {},
    }

    stale_ids: list[int] = []

    for rec in records:
        if is_stale(rec.field_name, rec.source_type, rec.updated_at, now):
            stale_ids.append(rec.provenance_id)
            stats["newly_stale"] += 1
            stats["by_field"].setdefault(rec.field_name, 0)
            stats["by_field"][rec.field_name] += 1

    if stale_ids and not dry_run:
        # 批量更新
        await session.execute(
            update(EntityFieldProvenance)
            .where(EntityFieldProvenance.provenance_id.in_(stale_ids))
            .values(review_status="stale")
        )
        await session.flush()

    logger.info(
        "Stale scan complete: scanned=%d, newly_stale=%d",
        stats["total_scanned"], stats["newly_stale"],
    )

    return stats


async def get_entity_freshness_report(
    session: AsyncSession,
    entity_id,
) -> list[dict]:
    """
    获取单个实体的字段新鲜度报告。

    Returns:
        [{field_name, source_type, updated_at, sla_deadline, is_stale, days_remaining}, ...]
    """
    from app.db.models.catalog import EntityFieldProvenance

    now = datetime.now(timezone.utc)

    q = await session.execute(
        select(EntityFieldProvenance).where(
            EntityFieldProvenance.entity_id == entity_id
        )
    )
    records = q.scalars().all()

    report = []
    for rec in records:
        deadline = get_sla_deadline(rec.field_name, rec.source_type, rec.updated_at)
        remaining = (deadline - now).days
        report.append({
            "field_name": rec.field_name,
            "source_type": rec.source_type,
            "confidence_score": float(rec.confidence_score) if rec.confidence_score else None,
            "review_status": rec.review_status,
            "updated_at": rec.updated_at.isoformat() if rec.updated_at else None,
            "sla_deadline": deadline.isoformat(),
            "is_stale": remaining < 0,
            "days_remaining": remaining,
        })

    return sorted(report, key=lambda x: x["days_remaining"])


async def get_stale_summary(session: AsyncSession) -> dict:
    """
    获取全库 stale 概况（用于 admin dashboard）。

    Returns:
        {
            "total_provenance_records": N,
            "stale_count": M,
            "stale_rate": 0.XX,
            "top_stale_fields": [{"field": "...", "count": N}, ...],
            "entities_with_stale_fields": K,
        }
    """
    from app.db.models.catalog import EntityFieldProvenance

    total = await session.scalar(select(func.count(EntityFieldProvenance.provenance_id)))
    stale = await session.scalar(
        select(func.count(EntityFieldProvenance.provenance_id)).where(
            EntityFieldProvenance.review_status == "stale"
        )
    )

    # 按字段统计 stale
    q = await session.execute(
        select(
            EntityFieldProvenance.field_name,
            func.count(EntityFieldProvenance.provenance_id),
        )
        .where(EntityFieldProvenance.review_status == "stale")
        .group_by(EntityFieldProvenance.field_name)
        .order_by(func.count(EntityFieldProvenance.provenance_id).desc())
        .limit(10)
    )
    top_fields = [{"field": row[0], "count": row[1]} for row in q.fetchall()]

    # 有 stale 字段的 entity 数
    stale_entities = await session.scalar(
        select(func.count(func.distinct(EntityFieldProvenance.entity_id))).where(
            EntityFieldProvenance.review_status == "stale"
        )
    )

    return {
        "total_provenance_records": total or 0,
        "stale_count": stale or 0,
        "stale_rate": round((stale or 0) / max(1, total or 1), 4),
        "top_stale_fields": top_fields,
        "entities_with_stale_fields": stale_entities or 0,
    }
