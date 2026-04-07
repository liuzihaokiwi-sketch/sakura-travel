"""
step08_daily_constraints.py — 每日约束包构建

为每一天构建 DailyConstraints，包含：
  - date, day_of_week, sunrise, sunset
  - closed_entities: 该天关闭的实体id列表
  - low_freq_transits: 低频班次时间窗限制
  - anchors: 固定时间点（飞行、已订项目）
  - hotel_breakfast_included: 酒店早餐是否包含
  - hotel_dinner_included: 酒店晚餐是否包含

数据源：
  - EntityOperatingFact：各实体定休日
  - PoiOpeningSnapshot：已知关闭日期
  - entity_temporal_profiles：季节性约束
  - 天文计算（sunrise/sunset）
  - selected_hotel 的 pricing.includes_meal 字段
"""

import logging
from datetime import date, datetime, timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.snapshots import PoiOpeningSnapshot
from app.db.models.soft_rules import EntityOperatingFact
from app.domains.planning_v2.models import CircleProfile, DailyConstraints

logger = logging.getLogger(__name__)

try:
    from astral import LocationInfo
    from astral.sun import sun

    HAS_ASTRAL = True
except ImportError:
    HAS_ASTRAL = False
    LocationInfo = None
    logger.warning("astral library not available, using fallback sunrise/sunset calculation")


def _make_location(circle: CircleProfile) -> "LocationInfo | None":
    """从 CircleProfile 构造 astral LocationInfo。"""
    if not HAS_ASTRAL:
        return None
    lat, lng = circle.default_location
    return LocationInfo(
        name=circle.circle_id,
        region=circle.country.upper()[:2],
        timezone=circle.timezone,
        latitude=lat,
        longitude=lng,
    )


# 月份到季节映射
_MONTH_TO_SEASON = {
    1: "winter",
    2: "winter",
    3: "spring",
    4: "spring",
    5: "spring",
    6: "summer",
    7: "summer",
    8: "summer",
    9: "autumn",
    10: "autumn",
    11: "autumn",
    12: "winter",
}


async def build_daily_constraints_list(
    session: AsyncSession,
    trip_window: dict,  # {start_date, end_date, total_days}
    circle: CircleProfile,
    selected_hotel_id: str | None = None,
    user_party_type: str | None = None,
) -> list[DailyConstraints]:
    """
    为旅行期间的每一天构建 DailyConstraints。

    Args:
        session: 数据库会话
        trip_window: {start_date: 'YYYY-MM-DD', end_date: 'YYYY-MM-DD', total_days: int}
        selected_hotel_id: 选中酒店的 entity_id（Step 7 输出），可选
        user_party_type: 用户同行人类型（用于过滤不适用的限制），可选

    Returns:
        list[DailyConstraints]: 每天的约束列表，按日期排序

    Raises:
        ValueError: 如果 trip_window 数据不完整
    """

    # 1. 解析 trip_window
    start_date_str = trip_window.get("start_date")
    end_date_str = trip_window.get("end_date")

    if not start_date_str or not end_date_str:
        raise ValueError("trip_window 缺少 start_date 或 end_date")

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError as e:
        raise ValueError(f"无法解析日期格式：{e}")

    # 2. 生成日期列表
    current_date = start_date
    daily_list = []

    location = _make_location(circle)

    while current_date <= end_date:
        daily_constraints = await _build_single_day_constraints(
            session=session,
            date=current_date,
            selected_hotel_id=selected_hotel_id,
            user_party_type=user_party_type,
            location=location,
        )
        daily_list.append(daily_constraints)
        current_date += timedelta(days=1)

    logger.info(f"Built daily constraints for {len(daily_list)} days ({start_date} to {end_date})")

    return daily_list


async def _build_single_day_constraints(
    session: AsyncSession,
    date: date,
    selected_hotel_id: str | None = None,
    user_party_type: str | None = None,
    location=None,
) -> DailyConstraints:
    """
    为单一日期构建 DailyConstraints。

    Args:
        session: 数据库会话
        date: 日期对象
        selected_hotel_id: 选中酒店的 entity_id
        user_party_type: 用户同行人类型

    Returns:
        DailyConstraints: 该日的约束
    """

    date_str = date.strftime("%Y-%m-%d")
    day_of_week = _get_day_of_week_en(date)

    # 1. 计算 sunrise/sunset
    sunrise_time, sunset_time = await _get_sunrise_sunset(date, location)

    # 2. 查询该天关闭的实体
    closed_entities = await _get_closed_entities_for_date(session, date)

    # 3. 查询低频班次
    low_freq_transits = await _get_low_frequency_transits(session, date)

    # 4. 构建锚点（固定时间点）
    anchors = await _build_anchors(session, date, selected_hotel_id)

    # 5. 读取酒店早餐/晚餐信息
    hotel_breakfast_included, hotel_dinner_included = await _get_hotel_meal_inclusion(
        session, selected_hotel_id
    )

    logger.debug(
        f"Daily constraints for {date_str}: "
        f"sunrise={sunrise_time}, sunset={sunset_time}, "
        f"closed_entities={len(closed_entities)}, "
        f"low_freq_transits={len(low_freq_transits)}, "
        f"breakfast_included={hotel_breakfast_included}"
    )

    return DailyConstraints(
        date=date_str,
        day_of_week=day_of_week,
        sunrise=sunrise_time,
        sunset=sunset_time,
        closed_entities=closed_entities,
        low_freq_transits=low_freq_transits,
        anchors=anchors,
        hotel_breakfast_included=hotel_breakfast_included,
        hotel_dinner_included=hotel_dinner_included,
    )


async def _get_sunrise_sunset(date: date, _location=None) -> tuple[str, str]:
    """
    计算指定日期的日出日落时间。

    Args:
        date: 日期
        _location: astral LocationInfo（从 CircleProfile 构造）

    Fallback：如果 astral 库不可用，使用近似计算
    """

    if not HAS_ASTRAL or _location is None:
        return _fallback_sunrise_sunset(date)

    try:
        sun_data = sun(_location.observer, date=date)
        sunrise = sun_data["sunrise"].strftime("%H:%M")
        sunset = sun_data["sunset"].strftime("%H:%M")
        return (sunrise, sunset)
    except Exception as e:
        logger.warning(f"Failed to calculate sunrise/sunset for {date}: {e}, using fallback")
        return _fallback_sunrise_sunset(date)


def _fallback_sunrise_sunset(date: date) -> tuple[str, str]:
    """
    简单的日出日落近似计算（基于北半球、日本纬度）。

    实际值应该使用 astral 库或查表，这里提供 fallback。
    """

    # 简化近似：
    # 冬至（12/21）: sunrise ~06:47, sunset ~16:28
    # 夏至（6/21）: sunrise ~04:26, sunset ~18:47
    # 春秋分（3/21, 9/23）: sunrise ~06:00, sunset ~18:00

    # 使用日期序号来计算
    day_of_year = date.timetuple().tm_yday

    # 简单正弦波近似
    # 冬至 day_of_year ~355，夏至 ~172
    import math

    # 标准化到 [-1, 1]
    normalized = math.cos(2 * math.pi * (day_of_year - 1) / 365)

    # sunrise: 冬至 06:47, 夏至 04:26, 平均 05:36
    # 范围：约 4:26 - 6:47，差 2:21 = 141 分钟
    sunrise_mins = int(5 * 60 + 36 + (normalized * 70))  # 约 ±70 分钟
    sunrise_hour = sunrise_mins // 60
    sunrise_min = sunrise_mins % 60
    sunrise = f"{sunrise_hour:02d}:{sunrise_min:02d}"

    # sunset: 冬至 16:28, 夏至 18:47, 平均 17:37
    # 范围：约 16:28 - 18:47，差 2:19 = 139 分钟
    sunset_mins = int(17 * 60 + 37 - (normalized * 69))  # 冬至减小，夏至增大
    sunset_hour = sunset_mins // 60
    sunset_min = sunset_mins % 60
    sunset = f"{sunset_hour:02d}:{sunset_min:02d}"

    return (sunrise, sunset)


async def _get_closed_entities_for_date(session: AsyncSession, date: date) -> list[str]:
    """
    查询在指定日期关闭的实体列表。

    数据源：
      1. EntityOperatingFact：按 day_of_week 定休日
      2. PoiOpeningSnapshot：临时关闭

    Args:
        session: 数据库会话
        date: 日期对象

    Returns:
        list[str]: 关闭的实体 ID 列表
    """

    day_of_week = _get_day_of_week_en(date)
    closed_set = set()

    # 1. 从 EntityOperatingFact 查询定休日
    # 对应 day_of_week 为 "closed" 或 "off" 的记录
    stmt = select(EntityOperatingFact.entity_id).where(
        and_(
            EntityOperatingFact.day_of_week == day_of_week,
            # 假设 open_time 为 NULL 表示该天不营业
            EntityOperatingFact.open_time.is_(None),
        )
    )

    result = await session.execute(stmt)
    for row in result:
        closed_set.add(str(row[0]))

    # 2. 从 PoiOpeningSnapshot 查询临时关闭
    date_str = date.strftime("%Y-%m-%d")
    stmt = select(PoiOpeningSnapshot.entity_id).where(
        and_(PoiOpeningSnapshot.check_date == date_str, PoiOpeningSnapshot.is_open.is_(False))
    )

    result = await session.execute(stmt)
    for row in result:
        closed_set.add(str(row[0]))

    logger.debug(f"Found {len(closed_set)} closed entities for {date_str}")

    return list(closed_set)


async def _get_low_frequency_transits(session: AsyncSession, date: date) -> list[dict]:
    """
    查询指定日期的低频班次信息。

    低频班次：指班次较少的交通方式（如偏远景区的巴士）。
    这些限制应该在行程规划时考虑（必须赶上班次）。

    数据源：
      - entity_temporal_profiles: availability_notes 中可能包含班次信息
      - 未来版本：专门的 transit_frequency 表

    Args:
        session: 数据库会话
        date: 日期对象

    Returns:
        list[dict]: 低频班次列表，每项格式：
            {
                "start_time": "09:00",
                "end_time": "17:00",
                "frequency_mins": 60,
                "route": "JR嵯峨嵐山線",
                "constraint": "must_be_at_station_by"
            }
    """

    # 当前实现：返回空列表
    # TODO: 实现真实的低频班次查询
    # 可能需要：
    #   1. 专门的 transit_frequency 表
    #   2. 或从 entity_temporal_profiles.availability_notes 解析

    logger.debug(f"Low frequency transits for {date.strftime('%Y-%m-%d')}: none yet")

    return []


async def _build_anchors(
    session: AsyncSession, date: date, selected_hotel_id: str | None = None
) -> list[dict]:
    """
    构建当日的锚点（固定时间点）。

    锚点包括：
      1. 飞行时间（入境/出境）
      2. 已订酒店（check-in/check-out 时间）
      3. 其他已确认的预订项目

    Args:
        session: 数据库会话
        date: 日期对象
        selected_hotel_id: 选中酒店的 entity_id

    Returns:
        list[dict]: 锚点列表，每项格式：
            {
                "type": "flight" | "hotel_checkin" | "hotel_checkout" | "booked_item",
                "time": "HH:MM",
                "name": "描述",
                "constraint": "柔性 or 硬性约束"
            }
    """

    anchors = []

    # 1. 如果是到达日，添加飞行入境锚点
    # TODO: 从 trip_profile.arrival_local_datetime 读取

    # 2. 如果是离开日，添加飞行出境锚点
    # TODO: 从 trip_profile.departure_local_datetime 读取

    # 3. 添加酒店 check-in/check-out
    if selected_hotel_id:
        # 查询酒店 check-in 和 check-out 时间
        hotel_checkin, hotel_checkout = await _get_hotel_checkin_checkout(
            session, selected_hotel_id
        )

        # TODO: 根据日期判断是否添加 check-in/check-out 锚点

    logger.debug(f"Built {len(anchors)} anchors for {date.strftime('%Y-%m-%d')}")

    return anchors


async def _get_hotel_checkin_checkout(
    session: AsyncSession, hotel_id: str | None
) -> tuple[str | None, str | None]:
    """
    获取酒店的 check-in 和 check-out 时间。

    Args:
        session: 数据库会话
        hotel_id: 酒店的 entity_id

    Returns:
        (check_in_time: 'HH:MM', check_out_time: 'HH:MM')
    """

    if not hotel_id:
        return (None, None)

    import uuid

    try:
        hotel_uuid = uuid.UUID(hotel_id)
    except (ValueError, AttributeError):
        return (None, None)

    from app.db.models.catalog import Hotel

    stmt = select(Hotel).where(Hotel.entity_id == hotel_uuid)
    result = await session.execute(stmt)
    hotel = result.scalar_one_or_none()

    if hotel:
        return (hotel.check_in_time, hotel.check_out_time)

    return (None, None)


async def _get_hotel_meal_inclusion(
    session: AsyncSession, hotel_id: str | None
) -> tuple[bool, bool]:
    """
    查询选中酒店是否包含早餐和晚餐。

    从 Hotel 实体的 amenities 字段推断，或从 pricing 字段读取。

    Args:
        session: 数据库会话
        hotel_id: 酒店的 entity_id

    Returns:
        (breakfast_included, dinner_included): 布尔值对
    """

    if not hotel_id:
        return (False, False)

    import uuid

    try:
        hotel_uuid = uuid.UUID(hotel_id)
    except (ValueError, AttributeError):
        return (False, False)

    from app.db.models.catalog import Hotel

    stmt = select(Hotel).where(Hotel.entity_id == hotel_uuid)
    result = await session.execute(stmt)
    hotel = result.scalar_one_or_none()

    if not hotel:
        return (False, False)

    # 检查 amenities 中是否有早餐相关标签
    amenities = hotel.amenities or []
    breakfast_included = "breakfast" in amenities or "included_breakfast" in amenities
    dinner_included = "dinner" in amenities or "included_dinner" in amenities

    logger.debug(
        f"Hotel {hotel_id} meal inclusion: breakfast={breakfast_included}, dinner={dinner_included}"
    )

    return (breakfast_included, dinner_included)


def _get_day_of_week_en(date: date) -> str:
    """
    获取日期的英文星期名（Mon, Tue, ... Sun）。

    Args:
        date: 日期对象

    Returns:
        str: 星期名 (Mon/Tue/Wed/Thu/Fri/Sat/Sun)
    """

    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    return day_names[date.weekday()]


def _get_day_of_week_jp(date: date) -> str:
    """
    获取日期的日文星期名（月/火/水/木/金/土/日）。

    Args:
        date: 日期对象

    Returns:
        str: 星期名
    """

    day_names = ["月", "火", "水", "木", "金", "土", "日"]
    return day_names[date.weekday()]
