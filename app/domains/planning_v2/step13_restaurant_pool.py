"""
step13_restaurant_pool.py -- 按走廊和餐食约束构建餐厅候选池

业务逻辑：
  - 酒店含早餐 -> breakfast_pool 为空
  - 酒店含晚餐 -> dinner_pool 为空
  - 午餐始终生成，标记为 optional（弹性推荐）
  - 午餐候选分三类：正餐 / 咖啡厅甜点店 / 活动替代

过滤规则（顺序执行）：
  1. entity_type = 'restaurant'，city_code in circle_cities
  2. is_active = true
  3. 排除 do_not_go_places
  4. 按 budget_tier 过滤价格区间
  5. 按走廊过滤（优先 main_corridors 内）
  6. 按菜系分类（cafe/sweets vs restaurant）
  7. 营业时段校验（餐厅的营业时间是否覆盖对应餐食时段）
"""

import logging
import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.catalog import EntityBase, EntityTag, Restaurant
from app.domains.planning_v2.models import (
    CandidatePool,
    CircleProfile,
    DailyConstraints,
    UserConstraints,
)

logger = logging.getLogger(__name__)

# 咖啡厅 / 甜点店的 cuisine_type 或标签关键词
_CAFE_CUISINE_TYPES = frozenset(
    {
        "cafe",
        "coffee",
        "sweets",
        "dessert",
        "bakery",
        "tea",
        "patisserie",
        "gelato",
        "ice_cream",
    }
)

_CAFE_TAG_KEYWORDS = frozenset(
    {
        "cafe",
        "coffee",
        "sweets",
        "dessert",
        "bakery",
        "tea_house",
        "patisserie",
        "gelato",
        "ice_cream",
        "甜品",
        "咖啡",
        "茶",
        "面包",
    }
)

# 早餐相关 cuisine_type / 标签
_BREAKFAST_CUISINE_TYPES = frozenset(
    {
        "cafe",
        "coffee",
        "bakery",
        "breakfast",
        "morning_set",
    }
)

_BREAKFAST_TAG_KEYWORDS = frozenset(
    {
        "breakfast",
        "morning",
        "morning_set",
        "早餐",
        "cafe",
        "coffee",
        "bakery",
    }
)

# 预算 tier 对应的每人价格上限（v1 fallback，日元）
# 新圈从 circle.budget_config.restaurant_price_cap 读取
_PRICE_CAP_BY_TIER: dict[str, int] = {
    "budget": 2000,
    "mid": 5000,
    "premium": 15000,
    "luxury": 999999,  # 不限制
}

# 各餐食时段的典型时间窗（HH:MM），用于校验营业时间
_MEAL_TIME_WINDOWS: dict[str, tuple[str, str]] = {
    "breakfast": ("06:30", "09:30"),
    "lunch": ("11:00", "14:00"),
    "dinner": ("17:00", "21:00"),
}


def _covers_meal_window(
    open_hours: dict | None,
    meal_type: str,
) -> bool:
    """
    检查餐厅的营业时间是否覆盖指定餐食时段。

    Args:
        open_hours: 餐厅的 opening_hours_json，可能包含:
            - "open_time": "HH:MM", "close_time": "HH:MM" (简单格式)
            - "lunch_start": "HH:MM", "lunch_end": "HH:MM" (分段格式)
            - "dinner_start": "HH:MM", "dinner_end": "HH:MM"
        meal_type: "breakfast" / "lunch" / "dinner"

    Returns:
        True 如果营业时间覆盖该餐食时段，或无法判断（宽容策略）
    """
    if not open_hours:
        return True  # 无数据时不过滤（宽容）

    window = _MEAL_TIME_WINDOWS.get(meal_type)
    if not window:
        return True

    meal_start_str, meal_end_str = window

    # 尝试分段格式（lunch_start / dinner_start）
    segment_start = open_hours.get(f"{meal_type}_start")
    segment_end = open_hours.get(f"{meal_type}_end")
    if segment_start and segment_end:
        # 有明确的分段营业时间
        return segment_start <= meal_end_str and segment_end >= meal_start_str

    # 尝试通用格式（open_time / close_time）
    open_time = open_hours.get("open_time")
    close_time = open_hours.get("close_time")
    if open_time and close_time:
        return open_time <= meal_end_str and close_time >= meal_start_str

    return True  # 无法判断时不过滤


def _is_cafe_or_sweets(cuisine_type: str | None, tags: set[str]) -> bool:
    """判断是否为咖啡厅/甜点店类型。"""
    if cuisine_type and cuisine_type.lower() in _CAFE_CUISINE_TYPES:
        return True
    return bool(tags & _CAFE_TAG_KEYWORDS)


def _is_breakfast_suitable(cuisine_type: str | None, tags: set[str]) -> bool:
    """判断是否适合作为早餐候选。"""
    if cuisine_type and cuisine_type.lower() in _BREAKFAST_CUISINE_TYPES:
        return True
    return bool(tags & _BREAKFAST_TAG_KEYWORDS)


def _entity_to_candidate(
    entity: "EntityBase",
    restaurant: "Restaurant",
    tags: set[str],
    currency: str = "JPY",
) -> CandidatePool:
    """将 EntityBase + Restaurant 转换为 CandidatePool。"""
    # 价格：优先取午餐价，其次晚餐价，最后最低价（DB字段仍是_jpy，读取时映射到cost_local）
    cost_local = 0
    if restaurant.budget_lunch_jpy:
        cost_local = restaurant.budget_lunch_jpy
    elif restaurant.budget_dinner_jpy:
        cost_local = restaurant.budget_dinner_jpy
    elif restaurant.price_range_min_jpy:
        cost_local = restaurant.price_range_min_jpy

    # visit_minutes：餐厅默认 60 分钟
    visit_minutes = 60
    if entity.typical_duration_baseline:
        visit_minutes = int(entity.typical_duration_baseline)

    # 开放时间
    open_hours = {}
    if restaurant.opening_hours_json:
        open_hours = restaurant.opening_hours_json

    # 评分信号
    review_signals: dict = {}
    if restaurant.tabelog_score:
        review_signals["tabelog_score"] = float(restaurant.tabelog_score)
    if restaurant.michelin_star and restaurant.michelin_star > 0:
        review_signals["michelin_star"] = restaurant.michelin_star

    return CandidatePool(
        entity_id=str(entity.entity_id),
        name_zh=entity.name_zh,
        entity_type="restaurant",
        grade=entity.data_tier or "B",
        latitude=float(entity.lat) if entity.lat else 0.0,
        longitude=float(entity.lng) if entity.lng else 0.0,
        tags=list(tags),
        visit_minutes=visit_minutes,
        cost_local=cost_local,
        city_code=entity.city_code or "",
        currency=currency,
        open_hours=open_hours,
        review_signals=review_signals,
    )


def _check_meal_inclusion(
    daily_constraints: list[DailyConstraints],
) -> tuple[bool, bool]:
    """检查所有日期的酒店含餐情况。

    只要有任何一天不含早餐/晚餐，就需要生成对应的候选池。
    但如果所有天都含，则不生成。

    Returns:
        (all_breakfast_included, all_dinner_included)
    """
    if not daily_constraints:
        return False, False

    all_breakfast = all(dc.hotel_breakfast_included for dc in daily_constraints)
    all_dinner = all(dc.hotel_dinner_included for dc in daily_constraints)
    return all_breakfast, all_dinner


async def build_restaurant_pool(
    session: AsyncSession,
    user_constraints: UserConstraints,
    circle_cities: list[str],
    daily_constraints: list[DailyConstraints],
    main_corridors: list[str],
    circle: CircleProfile,
) -> dict:
    """按走廊和餐食约束构建餐厅候选池。

    Args:
        session: 数据库异步会话
        user_constraints: 用户约束
        circle_cities: 圈内城市代码列表
        daily_constraints: 每日约束列表
        main_corridors: Step 5 输出的主走廊列表

    Returns:
        {
          "breakfast_pool": [...],
          "lunch_pool": {
            "restaurants": [...],
            "cafes": [...],
          },
          "dinner_pool": [...],
          "pool_stats": {
            "total_restaurants": N,
            "breakfast_available": bool,
            "dinner_available": bool,
            "lunch_flex": true,
          }
        }
    """
    trace_log: list[str] = []

    if not circle_cities:
        logger.warning("[餐厅池] circle_cities 为空，返回空池")
        return _empty_result()

    # ── 解析约束 ─────────────────────────────────────────────────────
    do_not_go = set(user_constraints.constraints.get("do_not_go", []))
    user_profile = user_constraints.user_profile or {}
    budget_tier = user_profile.get("budget_tier", "mid")
    # 价格上限从圈配置读取（不同圈不同货币不同数值）
    if circle and circle.budget_config:
        price_cap_config = circle.budget_config.get("restaurant_price_cap", _PRICE_CAP_BY_TIER)
    else:
        price_cap_config = _PRICE_CAP_BY_TIER
    price_cap = price_cap_config.get(budget_tier, 5000)

    # ── 检查酒店含餐 ─────────────────────────────────────────────────
    all_breakfast, all_dinner = _check_meal_inclusion(daily_constraints)
    trace_log.append(f"hotel_meals: all_breakfast={all_breakfast}, all_dinner={all_dinner}")

    # ── 1. 查询基础餐厅实体 ──────────────────────────────────────────
    query = (
        select(EntityBase)
        .where(
            and_(
                EntityBase.entity_type == "restaurant",
                EntityBase.city_code.in_(circle_cities),
                EntityBase.is_active == True,  # noqa: E712
            )
        )
        .order_by(EntityBase.entity_id)
    )

    result = await session.execute(query)
    entities = result.scalars().all()
    count_base = len(entities)
    trace_log.append(f"base query: {count_base} restaurants")

    if not entities:
        logger.info("[餐厅池] 无餐厅实体: cities=%s", circle_cities)
        return _empty_result()

    entity_ids = [e.entity_id for e in entities]

    # ── 2. 批量加载 Restaurant 扩展表 ────────────────────────────────
    rest_query = select(Restaurant).where(Restaurant.entity_id.in_(entity_ids))
    rest_result = await session.execute(rest_query)
    rest_map: dict[uuid.UUID, Restaurant] = {r.entity_id: r for r in rest_result.scalars().all()}

    # ── 3. 批量加载标签 ──────────────────────────────────────────────
    tags_query = select(EntityTag).where(EntityTag.entity_id.in_(entity_ids))
    tags_result = await session.execute(tags_query)
    entity_tags: dict[uuid.UUID, set[str]] = {}
    for tag in tags_result.scalars().all():
        entity_tags.setdefault(tag.entity_id, set()).add(
            tag.tag_value.lower() if tag.tag_value else ""
        )

    # ── 4. 过滤 + 分类 ──────────────────────────────────────────────
    breakfast_pool: list[CandidatePool] = []
    lunch_restaurants: list[CandidatePool] = []
    lunch_cafes: list[CandidatePool] = []
    dinner_pool: list[CandidatePool] = []

    corridor_set = set(main_corridors) if main_corridors else set()

    for entity in entities:
        eid = entity.entity_id
        rest = rest_map.get(eid)
        if rest is None:
            continue  # 无扩展表数据，跳过

        tags = entity_tags.get(eid, set())

        # Rule 3: 排除 do_not_go
        if str(eid) in do_not_go:
            continue

        # Rule 4: 按 budget_tier 过滤
        min_price = rest.price_range_min_jpy or 0
        if min_price > price_cap:
            continue

        # Rule 10: 排除 risk_flags
        if entity.risk_flags:
            skip_flags = {"renovation", "construction", "unstable", "dangerous"}
            if any(flag in skip_flags for flag in entity.risk_flags):
                continue

        # 构建候选对象
        currency = circle.currency
        candidate = _entity_to_candidate(entity, rest, tags, currency)

        # Rule 5: 走廊优先标记（不排除非走廊，但标记用于排序）
        is_in_corridor = False
        if corridor_set:
            city_code = entity.city_code or ""
            if city_code in corridor_set:
                is_in_corridor = True
            # 也检查标签中是否有走廊名
            if tags & corridor_set:
                is_in_corridor = True

        # 用 review_signals 传递走廊优先信息
        if is_in_corridor:
            candidate.review_signals["in_main_corridor"] = True

        # Rule 6: 按菜系分类
        cuisine = (rest.cuisine_type or "").lower()
        is_cafe = _is_cafe_or_sweets(cuisine, tags)
        is_breakfast = _is_breakfast_suitable(cuisine, tags)

        # Rule 7: 营业时段校验 + 分类到各个池
        rest_open_hours = candidate.open_hours

        # 早餐池
        if not all_breakfast and is_breakfast:
            if _covers_meal_window(rest_open_hours, "breakfast"):
                breakfast_pool.append(candidate)

        # 午餐池（所有餐厅都可作为午餐候选）
        if _covers_meal_window(rest_open_hours, "lunch"):
            if is_cafe:
                lunch_cafes.append(candidate)
            else:
                lunch_restaurants.append(candidate)

        # 晚餐池（排除纯早餐/咖啡厅类型）
        if not all_dinner and not is_cafe:
            if _covers_meal_window(rest_open_hours, "dinner"):
                dinner_pool.append(candidate)

    # ── 5. 走廊优先排序 ──────────────────────────────────────────────
    def _corridor_sort_key(c: CandidatePool) -> tuple:
        in_corridor = c.review_signals.get("in_main_corridor", False)
        return (0 if in_corridor else 1, c.grade or "Z")

    breakfast_pool.sort(key=_corridor_sort_key)
    lunch_restaurants.sort(key=_corridor_sort_key)
    lunch_cafes.sort(key=_corridor_sort_key)
    dinner_pool.sort(key=_corridor_sort_key)

    # ── 6. 统计 ─────────────────────────────────────────────────────
    total = len(breakfast_pool) + len(lunch_restaurants) + len(lunch_cafes) + len(dinner_pool)
    breakfast_available = not all_breakfast and len(breakfast_pool) > 0
    dinner_available = not all_dinner and len(dinner_pool) > 0

    trace_log.append(
        f"pools: breakfast={len(breakfast_pool)}, "
        f"lunch_rest={len(lunch_restaurants)}, lunch_cafe={len(lunch_cafes)}, "
        f"dinner={len(dinner_pool)}"
    )

    logger.info(
        "[餐厅池] 完成: base=%d -> breakfast=%d, lunch=%d+%d, dinner=%d. tier=%s, corridors=%s",
        count_base,
        len(breakfast_pool),
        len(lunch_restaurants),
        len(lunch_cafes),
        len(dinner_pool),
        budget_tier,
        main_corridors,
    )
    for line in trace_log:
        logger.debug("  %s", line)

    return {
        "breakfast_pool": [] if all_breakfast else breakfast_pool,
        "lunch_pool": {
            "restaurants": lunch_restaurants,
            "cafes": lunch_cafes,
        },
        "dinner_pool": [] if all_dinner else dinner_pool,
        "pool_stats": {
            "total_restaurants": total,
            "breakfast_available": breakfast_available,
            "dinner_available": dinner_available,
            "lunch_flex": True,  # 午餐始终是弹性的
        },
    }


def _empty_result() -> dict:
    """返回空的餐厅池结构。"""
    return {
        "breakfast_pool": [],
        "lunch_pool": {
            "restaurants": [],
            "cafes": [],
        },
        "dinner_pool": [],
        "pool_stats": {
            "total_restaurants": 0,
            "breakfast_available": False,
            "dinner_available": False,
            "lunch_flex": True,
        },
    }
