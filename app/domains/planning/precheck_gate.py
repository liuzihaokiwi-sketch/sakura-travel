"""
precheck_gate.py — 前置可规避风险检查（Phase 1）

消费 PoiOpeningSnapshot + EntityOperatingFact，
在生成前清掉那些"提前就知道不能去"的活动。
区别于 live_risk_monitor（T-72h/T-24h 实时风险）。

检查规则 (PC-xxx)：
  PC-001  固定休馆日命中旅行日
  PC-002  已知维护/整修期间
  PC-003  门票/预约已售罄（如有快照）
  PC-004  季节窗口已过（如花期结束、夏季限定结束）
  PC-005  已知交通不可达（如冬季封路）
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.snapshots import PoiOpeningSnapshot
from app.db.models.soft_rules import EntityOperatingFact

logger = logging.getLogger(__name__)


@dataclass
class PrecheckVerdict:
    entity_id: uuid.UUID
    status: str = "pass"            # pass / fail / warn
    fail_codes: list[str] = field(default_factory=list)
    warn_codes: list[str] = field(default_factory=list)
    details: dict = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.status != "fail"


@dataclass
class PrecheckResult:
    """整批检查结果。"""
    verdicts: dict[uuid.UUID, PrecheckVerdict] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    @property
    def failed_ids(self) -> set[uuid.UUID]:
        return {eid for eid, v in self.verdicts.items() if v.status == "fail"}

    @property
    def warned_ids(self) -> set[uuid.UUID]:
        return {eid for eid, v in self.verdicts.items() if v.status == "warn"}


async def run_precheck_gate(
    session: AsyncSession,
    entity_ids: list[uuid.UUID],
    travel_dates: list[date],
) -> PrecheckResult:
    """
    对一批实体执行前置可规避风险检查。

    Args:
        entity_ids: 已通过 eligibility_gate 的实体
        travel_dates: 旅行覆盖的日期列表 [date(2026,4,1), date(2026,4,2), ...]
    """
    result = PrecheckResult()
    if not entity_ids or not travel_dates:
        return result

    travel_start = min(travel_dates)
    travel_end = max(travel_dates)
    weekdays_in_trip = {d.weekday() for d in travel_dates}  # 0=Mon, 6=Sun

    # 批量加载营业快照
    opening_map = await _load_opening_snapshots(session, entity_ids)

    # 批量加载运营事实
    facts_map = await _load_operating_facts(session, entity_ids)

    for eid in entity_ids:
        verdict = _check_entity_precheck(
            eid,
            opening_map.get(eid),
            facts_map.get(eid, []),
            travel_dates,
            travel_start,
            travel_end,
            weekdays_in_trip,
        )
        result.verdicts[eid] = verdict

    failed = sum(1 for v in result.verdicts.values() if v.status == "fail")
    warned = sum(1 for v in result.verdicts.values() if v.status == "warn")
    result.trace.append(
        f"precheck_gate: {len(entity_ids)} checked, "
        f"{failed} failed, {warned} warned"
    )
    return result


# ── 数据加载 ──────────────────────────────────────────────────────────────────

async def _load_opening_snapshots(
    session: AsyncSession,
    entity_ids: list[uuid.UUID],
) -> dict[uuid.UUID, PoiOpeningSnapshot]:
    """加载最新的营业快照。"""
    q = await session.execute(
        select(PoiOpeningSnapshot)
        .where(PoiOpeningSnapshot.entity_id.in_(entity_ids))
        .order_by(PoiOpeningSnapshot.snapshot_date.desc())
    )
    result: dict[uuid.UUID, PoiOpeningSnapshot] = {}
    for snap in q.scalars().all():
        # 只保留每个实体的最新快照
        if snap.entity_id not in result:
            result[snap.entity_id] = snap
    return result


async def _load_operating_facts(
    session: AsyncSession,
    entity_ids: list[uuid.UUID],
) -> dict[uuid.UUID, list[EntityOperatingFact]]:
    """加载运营事实。"""
    q = await session.execute(
        select(EntityOperatingFact)
        .where(EntityOperatingFact.entity_id.in_(entity_ids))
    )
    result: dict[uuid.UUID, list[EntityOperatingFact]] = {}
    for fact in q.scalars().all():
        result.setdefault(fact.entity_id, []).append(fact)
    return result


# ── 逐实体检查 ────────────────────────────────────────────────────────────────

def _check_entity_precheck(
    entity_id: uuid.UUID,
    opening: Optional[PoiOpeningSnapshot],
    facts: list,
    travel_dates: list[date],
    travel_start: date,
    travel_end: date,
    weekdays_in_trip: set[int],
) -> PrecheckVerdict:
    """对单个实体执行 PC-001~005 检查。"""
    verdict = PrecheckVerdict(entity_id=entity_id)

    # PC-001: 固定休馆日
    if opening and hasattr(opening, "regular_holidays"):
        holidays = opening.regular_holidays or []
        # holidays 格式: ["monday", "tuesday"] 或 [0, 1]
        closed_weekdays = _parse_closed_weekdays(holidays)
        if closed_weekdays:
            # 检查旅行期间是否每天都碰上休馆
            all_closed = closed_weekdays.issuperset(weekdays_in_trip)
            some_closed = bool(closed_weekdays & weekdays_in_trip)
            if all_closed:
                verdict.status = "fail"
                verdict.fail_codes.append("PC-001_ALL_DAYS_CLOSED")
            elif some_closed:
                # 部分天关，只是 warn（骨架层可以避开那天）
                verdict.warn_codes.append("PC-001_SOME_DAYS_CLOSED")
                verdict.details["closed_weekdays"] = sorted(closed_weekdays)

    # PC-002: 已知维护/整修期间
    for fact in facts:
        fact_key = getattr(fact, "fact_key", "") or ""
        fact_value = getattr(fact, "fact_value", "") or ""
        if fact_key in ("maintenance_start", "renovation_start"):
            try:
                maint_start = _parse_date(fact_value)
                # 查找对应的结束日期
                maint_end = _find_fact_date(facts, fact_key.replace("start", "end"))
                if maint_start and maint_end:
                    if maint_start <= travel_end and maint_end >= travel_start:
                        verdict.status = "fail"
                        verdict.fail_codes.append("PC-002_MAINTENANCE")
                        verdict.details["maintenance"] = {
                            "start": str(maint_start), "end": str(maint_end),
                        }
                elif maint_start and maint_start <= travel_end:
                    # 只有开始日没有结束日，保守处理
                    verdict.status = "warn" if verdict.status == "pass" else verdict.status
                    verdict.warn_codes.append("PC-002_MAINTENANCE_OPEN_END")
            except (ValueError, TypeError):
                pass

    # PC-003: 门票/预约已售罄
    for fact in facts:
        fact_key = getattr(fact, "fact_key", "") or ""
        fact_value = (getattr(fact, "fact_value", "") or "").lower()
        if fact_key == "ticket_status" and fact_value in ("sold_out", "unavailable"):
            verdict.status = "fail"
            verdict.fail_codes.append("PC-003_SOLD_OUT")
        elif fact_key == "reservation_status" and fact_value in ("full", "closed"):
            verdict.status = "warn" if verdict.status == "pass" else verdict.status
            verdict.warn_codes.append("PC-003_RESERVATION_FULL")

    # PC-004: 季节窗口已过
    for fact in facts:
        fact_key = getattr(fact, "fact_key", "") or ""
        fact_value = getattr(fact, "fact_value", "") or ""
        if fact_key == "seasonal_end":
            try:
                seasonal_end = _parse_date(fact_value)
                if seasonal_end and seasonal_end < travel_start:
                    verdict.status = "fail"
                    verdict.fail_codes.append("PC-004_SEASON_ENDED")
            except (ValueError, TypeError):
                pass

    # PC-005: 已知交通不可达
    for fact in facts:
        fact_key = getattr(fact, "fact_key", "") or ""
        fact_value = (getattr(fact, "fact_value", "") or "").lower()
        if fact_key == "access_status" and fact_value in ("closed", "impassable", "road_closed"):
            verdict.status = "fail"
            verdict.fail_codes.append("PC-005_INACCESSIBLE")

    # 如果有 warn 但没有 fail
    if verdict.status == "pass" and verdict.warn_codes:
        verdict.status = "warn"

    return verdict


# ── 辅助函数 ──────────────────────────────────────────────────────────────────

_WEEKDAY_MAP = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}

def _parse_closed_weekdays(holidays: list) -> set[int]:
    """解析休馆日列表为 weekday 集合 (0=Mon..6=Sun)。"""
    result: set[int] = set()
    for h in holidays:
        if isinstance(h, int) and 0 <= h <= 6:
            result.add(h)
        elif isinstance(h, str):
            wd = _WEEKDAY_MAP.get(h.lower().strip())
            if wd is not None:
                result.add(wd)
    return result


def _parse_date(value: str) -> Optional[date]:
    """尝试解析日期字符串。"""
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    return None


def _find_fact_date(facts: list, key: str) -> Optional[date]:
    """从事实列表中找指定 key 的日期值。"""
    for fact in facts:
        if getattr(fact, "fact_key", "") == key:
            val = getattr(fact, "fact_value", "")
            if val:
                return _parse_date(val)
    return None
