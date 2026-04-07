"""
step01_constraints.py — 用户约束解析

从 TripProfile 或 DetailForm 解析 UserConstraints，包含：
  - trip_window: {start_date, end_date, total_days}
  - user_profile: {party_type, budget_tier, must_have_tags, nice_to_have_tags}
  - constraints: {must_visit, do_not_go, visited, booked_items}
"""

import logging
from datetime import datetime, date
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.business import TripProfile, TripRequest
from app.domains.planning_v2.models import UserConstraints

logger = logging.getLogger(__name__)


async def resolve_user_constraints(
    session: AsyncSession,
    trip_request_id: str
) -> UserConstraints:
    """
    从 TripProfile 或 DetailForm 解析 UserConstraints。

    流程：
      1. 加载 TripRequest，然后加载 TripProfile
      2. 从 TripProfile 提取：cities, travel_dates, party_type, budget_level 等
      3. 规范化为 UserConstraints 标准格式

    Args:
        session: 数据库会话
        trip_request_id: TripRequest 的 ID (UUID 字符串)

    Returns:
        UserConstraints: 标准化用户约束对象

    Raises:
        ValueError: 如果 TripRequest 或 TripProfile 不存在或数据不完整
    """

    # 1. 加载 TripRequest
    trip_request_uuid = _parse_uuid(trip_request_id)

    stmt = select(TripRequest).where(TripRequest.trip_request_id == trip_request_uuid)
    result = await session.execute(stmt)
    trip_request = result.scalar_one_or_none()

    if not trip_request:
        raise ValueError(f"TripRequest {trip_request_id} not found")

    # 2. 加载 TripProfile
    stmt = select(TripProfile).where(
        TripProfile.trip_request_id == trip_request_uuid
    )
    result = await session.execute(stmt)
    trip_profile = result.scalar_one_or_none()

    if not trip_profile:
        raise ValueError(f"TripProfile not found for TripRequest {trip_request_id}")

    # 3. 解析 trip_window
    trip_window = _parse_trip_window(trip_profile)

    # 4. 解析 user_profile
    user_profile = _parse_user_profile(trip_profile)

    # 5. 解析 constraints
    constraints = _parse_constraints(trip_profile)

    logger.info(
        f"Resolved user constraints for {trip_request_id}: "
        f"{trip_window['total_days']} days, {user_profile['party_type']}, "
        f"must_visit={len(constraints['must_visit'])}, "
        f"do_not_go={len(constraints['do_not_go'])}"
    )

    return UserConstraints(
        trip_window=trip_window,
        user_profile=user_profile,
        constraints=constraints
    )


def _parse_uuid(uuid_str: str):
    """安全地解析 UUID 字符串"""
    import uuid
    try:
        return uuid.UUID(uuid_str)
    except (ValueError, AttributeError):
        # 如果已经是 UUID，直接返回
        return uuid_str


def _parse_trip_window(trip_profile: TripProfile) -> dict:
    """
    解析旅行时间窗口。

    从 TripProfile 的 travel_dates 字段解析。
    travel_dates 格式: {'start': 'YYYY-MM-DD', 'end': 'YYYY-MM-DD'}
    或直接从 duration_days 推算。
    """

    travel_dates = trip_profile.travel_dates or {}
    start_date = travel_dates.get('start')
    end_date = travel_dates.get('end')
    duration_days = trip_profile.duration_days or 1

    # 尝试从 travel_dates 计算 total_days
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            calculated_days = (end - start).days + 1  # 包含到达日和离开日
            total_days = max(calculated_days, 1)
        except Exception:
            total_days = duration_days
    else:
        total_days = duration_days

    return {
        'start_date': start_date or '',
        'end_date': end_date or '',
        'total_days': total_days
    }


def _parse_user_profile(trip_profile: TripProfile) -> dict:
    """
    解析用户画像。

    包含：party_type, budget_tier, must_have_tags, nice_to_have_tags
    """

    party_type = trip_profile.party_type or 'couple'
    budget_level = trip_profile.budget_level or 'mid'
    must_have_tags = trip_profile.must_have_tags or []
    nice_to_have_tags = trip_profile.nice_to_have_tags or []

    # 提取同行人详细信息（如果可用）
    companion_breakdown = trip_profile.companion_breakdown or {}

    return {
        'party_type': party_type,
        'budget_tier': budget_level,
        'must_have_tags': must_have_tags,
        'nice_to_have_tags': nice_to_have_tags,
        'companion_breakdown': companion_breakdown,
        'special_requirements': trip_profile.special_requirements or {},
    }


def _parse_constraints(trip_profile: TripProfile) -> dict:
    """
    解析约束条件。

    包含：must_visit, do_not_go, visited, booked_items
    """

    must_visit_places = trip_profile.must_visit_places or []
    do_not_go_places = trip_profile.do_not_go_places or []
    visited_places = trip_profile.visited_places or []
    booked_items = trip_profile.booked_items or []

    # 规范化为列表（可能输入为 string 或 list）
    must_visit = _ensure_list(must_visit_places)
    do_not_go = _ensure_list(do_not_go_places)
    visited = _ensure_list(visited_places)
    booked = _ensure_list(booked_items)

    return {
        'must_visit': must_visit,
        'do_not_go': do_not_go,
        'visited': visited,
        'booked_items': booked,
    }


def _ensure_list(value) -> list:
    """
    确保值为列表。

    处理：
      - None -> []
      - str -> [str]
      - list -> list
    """
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]
