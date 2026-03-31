"""
时间线填充器（Timeline Filler）v2

取代 secondary_filler + meal_filler。

核心思想：
  1. 先确定硬约束（航班、大交通、核心活动时间窗、前一天结束时间）
  2. 在硬约束之间的空闲时段，按"当前时间→当前位置→附近有什么"顺序填充
  3. 根据精力曲线调整：上午放体力活动，午后放休息型，傍晚放轻量
  4. 强度是结果不是输入——一天的活动量由可用时间和候选数量自然决定
  5. 季节适配由上游 eligibility_gate EG-005 处理，此处信任候选池
"""
from __future__ import annotations

import logging
import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TimelineItem:
    """时间线上的一个元素"""
    entity_id: str = ""
    entity_type: str = "poi"        # poi / restaurant / hotel / transit
    name: str = ""
    city_code: str = ""
    lat: float = 0
    lng: float = 0
    start_time: int = 0             # 分钟数（从 00:00 起）
    duration_min: int = 60
    travel_from_prev_min: int = 0   # 从上一个地点过来的交通时间
    slot_type: str = ""             # morning_core / lunch / afternoon_easy / dinner / evening
    notes: str = ""
    score: float = 0
    is_anchor: bool = False
    is_transit: bool = False        # 大交通（JR 跨城等）


@dataclass
class DayTimeline:
    """一天的完整时间线"""
    day_index: int = 0
    day_type: str = "normal"
    city_code: str = ""
    available_from: int = 540       # 可用起始时间（分钟）
    available_until: int = 1260     # 可用结束时间
    items: List[TimelineItem] = field(default_factory=list)

    @property
    def total_items(self) -> int:
        return len([i for i in self.items if not i.is_transit])

    @property
    def start_time_hhmm(self) -> str:
        return _min_to_hhmm(self.available_from)

    @property
    def end_time_hhmm(self) -> str:
        return _min_to_hhmm(self.available_until)


# ─────────────────────────────────────────────────────────────────────────────
# 时间工具
# ─────────────────────────────────────────────────────────────────────────────

def _hhmm_to_min(hhmm: str) -> int:
    try:
        h, m = hhmm.split(":")
        return int(h) * 60 + int(m)
    except Exception:
        return 540

def _min_to_hhmm(minutes: int) -> str:
    h = min(23, max(0, minutes // 60))
    m = minutes % 60
    return f"{h:02d}:{m:02d}"

def _haversine_minutes(lat1: float, lng1: float, lat2: float, lng2: float) -> int:
    """步行时间估算。超过 30 分钟步行自动切换为公共交通估算。"""
    if not lat1 or not lng1 or not lat2 or not lng2:
        return 10
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    dist = R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    walk = int(dist * 1.3 / 66.7)  # 步行 4km/h + 绕路系数
    if walk > 30:
        return max(15, walk // 3)   # 公共交通约步行的 1/3
    return max(3, walk)


# ─────────────────────────────────────────────────────────────────────────────
# 时段判断
# ─────────────────────────────────────────────────────────────────────────────

def _slot_type_at(minute: int) -> str:
    """当前时间属于什么时段"""
    if minute < 11 * 60 + 30:
        return "morning_core"        # ~11:30 前：上午黄金段
    if minute < 12 * 60 + 30:
        return "lunch"               # 11:30-12:30：午餐时段
    if minute < 15 * 60:
        return "afternoon_easy"      # 12:30-15:00：午后低谷（休息型活动）
    if minute < 17 * 60 + 30:
        return "afternoon_light"     # 15:00-17:30：下午轻量
    if minute < 19 * 60:
        return "dinner"              # 17:30-19:00：晚餐时段
    return "evening"                 # 19:00+：晚间


# ─────────────────────────────────────────────────────────────────────────────
# 候选选择
# ─────────────────────────────────────────────────────────────────────────────

def _score_candidate(
    ent: Dict,
    slot_type: str,
    cur_lat: float,
    cur_lng: float,
    remaining_min: int,
) -> Tuple[float, int]:
    """
    为候选实体打分。返回 (score, travel_minutes)。
    score < 0 表示不合适。
    """
    e_lat = float(ent.get("lat") or 0)
    e_lng = float(ent.get("lng") or 0)
    if not e_lat or not e_lng:
        return -1, 0

    duration = ent.get("typical_duration_min") or ent.get("duration_min") or 60
    travel = _haversine_minutes(cur_lat, cur_lng, e_lat, e_lng)

    if travel + duration > remaining_min:
        return -1, travel  # 时间不够

    # 基础分
    base = float(ent.get("final_score") or ent.get("google_rating") or ent.get("tabelog_score") or 0)
    if base > 5:
        pass  # 已经是 0-100 制
    elif base > 0:
        base = base * 20  # 1-5 → 20-100
    else:
        base = 50

    # 距离惩罚（每分钟 -1 分）
    base -= travel * 1.0

    # 季节适配已由 eligibility_gate EG-005 在上游处理
    # timeline_filler 信任通过资格过滤的候选

    # 时段适配
    cat = (ent.get("poi_category") or ent.get("sub_category") or "").lower()
    etype = ent.get("entity_type", "poi")

    if slot_type == "morning_core":
        if cat in ("shrine", "temple", "park", "scenic_spot", "landmark", "market",
                    "zoo", "garden"):
            base += 15
    elif slot_type == "afternoon_easy":
        # 午后低谷：室内/轻松活动加分，但不再惩罚户外景点
        # （候选池可能只有这些类型，惩罚会导致整个时段空白）
        if cat in ("museum", "cafe", "specialty_shop", "shopping_mall", "onsen"):
            base += 20
        elif cat in ("landmark", "observation_deck", "market"):
            base += 10
        # shrine/temple/park 不加不减，保持中性
    elif slot_type == "afternoon_light":
        if cat in ("specialty_shop", "market", "street", "landmark", "district",
                    "shrine", "temple"):
            base += 10
    elif slot_type == "evening":
        if "night" in (ent.get("name") or "").lower() or "夜景" in (ent.get("name") or ""):
            base += 25
        if cat in ("landmark", "observation_deck"):
            base += 15
        if cat in ("onsen",):
            base += 10

    return base, travel


def _pick_best(
    slot_type: str,
    cur_lat: float,
    cur_lng: float,
    pool: List[Dict],
    used: set,
    remaining: int,
    entity_type_filter: str = "",
) -> Optional[Tuple[Dict, int]]:
    """选最佳候选。返回 (entity_dict, travel_minutes) 或 None。"""
    best = None
    best_score = -999
    best_travel = 0

    for ent in pool:
        eid = str(ent.get("entity_id", ""))
        if eid in used:
            continue
        if entity_type_filter and ent.get("entity_type", "") != entity_type_filter:
            continue

        score, travel = _score_candidate(ent, slot_type, cur_lat, cur_lng, remaining)
        if score > best_score:
            best_score = score
            best = ent
            best_travel = travel

    if best and best_score > 0:
        return best, best_travel
    return None


# ─────────────────────────────────────────────────────────────────────────────
# 核心：单日时间线填充
# ─────────────────────────────────────────────────────────────────────────────

def fill_day(
    day_index: int,
    day_type: str,
    day_city: str,
    available_from: int,
    available_until: int,
    anchor_entities: List[Dict],
    poi_pool: List[Dict],
    restaurant_pool: List[Dict],
    start_lat: float = 0,
    start_lng: float = 0,
) -> DayTimeline:
    """
    填充一天的时间线。

    逻辑：
    1. 从 available_from 开始
    2. 上午放 anchor（核心活动）→ 填充周边 POI → 午餐
    3. 午后放休息型活动 → 下午轻量 → 晚餐
    4. 晚上放夜景或结束
    5. 每一步检查剩余时间，不够就停
    """
    tl = DayTimeline(
        day_index=day_index,
        day_type=day_type,
        city_code=day_city,
        available_from=available_from,
        available_until=available_until,
    )

    cur_time = available_from
    cur_lat, cur_lng = start_lat, start_lng
    used: set = set()
    had_lunch = False
    had_dinner = False
    anchor_placed = False

    while cur_time < available_until - 20:
        remaining = available_until - cur_time
        slot = _slot_type_at(cur_time)

        # ── 午餐 ──
        if slot == "lunch" and not had_lunch:
            result = _pick_best("lunch", cur_lat, cur_lng, restaurant_pool, used, remaining)
            if result:
                ent, travel = result
                cur_time += travel
                item = TimelineItem(
                    entity_id=str(ent.get("entity_id", "")),
                    entity_type="restaurant",
                    name=ent.get("name_zh") or ent.get("name", ""),
                    city_code=ent.get("city_code", day_city),
                    lat=float(ent.get("lat", 0)), lng=float(ent.get("lng", 0)),
                    start_time=cur_time, duration_min=50,
                    travel_from_prev_min=travel, slot_type="lunch",
                    score=float(ent.get("tabelog_score") or ent.get("final_score") or 0),
                )
                tl.items.append(item)
                used.add(item.entity_id)
                cur_lat, cur_lng = item.lat, item.lng
                cur_time += 50
                had_lunch = True
                continue
            else:
                had_lunch = True  # 没找到也标记，避免死循环
                cur_time = 13 * 60  # 跳过午餐时段
                continue

        # ── 晚餐 ──
        if slot == "dinner" and not had_dinner:
            result = _pick_best("dinner", cur_lat, cur_lng, restaurant_pool, used, remaining)
            if result:
                ent, travel = result
                cur_time += travel
                item = TimelineItem(
                    entity_id=str(ent.get("entity_id", "")),
                    entity_type="restaurant",
                    name=ent.get("name_zh") or ent.get("name", ""),
                    city_code=ent.get("city_code", day_city),
                    lat=float(ent.get("lat", 0)), lng=float(ent.get("lng", 0)),
                    start_time=cur_time, duration_min=60,
                    travel_from_prev_min=travel, slot_type="dinner",
                    score=float(ent.get("tabelog_score") or ent.get("final_score") or 0),
                )
                tl.items.append(item)
                used.add(item.entity_id)
                cur_lat, cur_lng = item.lat, item.lng
                cur_time += 60
                had_dinner = True
                continue
            else:
                had_dinner = True
                cur_time += 60
                continue

        # ── 核心活动（上午优先放）──
        if slot == "morning_core" and not anchor_placed and anchor_entities:
            for anc in anchor_entities:
                aid = str(anc.get("entity_id", ""))
                if aid in used:
                    continue
                a_lat = float(anc.get("lat", 0))
                a_lng = float(anc.get("lng", 0))
                if not a_lat:
                    continue
                travel = _haversine_minutes(cur_lat, cur_lng, a_lat, a_lng)
                dur = anc.get("typical_duration_min") or 90
                if travel + dur > remaining:
                    continue
                cur_time += travel
                item = TimelineItem(
                    entity_id=aid, entity_type="poi",
                    name=anc.get("name_zh") or anc.get("name", ""),
                    city_code=anc.get("city_code", day_city),
                    lat=a_lat, lng=a_lng,
                    start_time=cur_time, duration_min=dur,
                    travel_from_prev_min=travel, slot_type="morning_core",
                    score=float(anc.get("final_score") or 0),
                    is_anchor=True,
                )
                tl.items.append(item)
                used.add(aid)
                cur_lat, cur_lng = a_lat, a_lng
                cur_time += dur
                break
            anchor_placed = True
            continue

        # ── 普通时段：找附近 POI ──
        result = _pick_best(slot, cur_lat, cur_lng, poi_pool, used, remaining)
        if result:
            ent, travel = result
            dur = ent.get("typical_duration_min") or ent.get("duration_min") or 45
            cur_time += travel
            item = TimelineItem(
                entity_id=str(ent.get("entity_id", "")),
                entity_type="poi",
                name=ent.get("name_zh") or ent.get("name", ""),
                city_code=ent.get("city_code", day_city),
                lat=float(ent.get("lat", 0)), lng=float(ent.get("lng", 0)),
                start_time=cur_time, duration_min=dur,
                travel_from_prev_min=travel, slot_type=slot,
                score=float(ent.get("final_score") or ent.get("google_rating") or 0),
            )
            tl.items.append(item)
            used.add(item.entity_id)
            cur_lat, cur_lng = item.lat, item.lng
            cur_time += dur
        else:
            cur_time += 30  # 没有合适的，快进

    return tl


# ─────────────────────────────────────────────────────────────────────────────
# 入口：写入 DB
# ─────────────────────────────────────────────────────────────────────────────

async def fill_and_write_timeline(
    session: AsyncSession,
    plan_id,
    frames: List,
    poi_pool: List[Dict],
    restaurant_pool: List[Dict],
    profile: Dict,
    ranking_result=None,
    hotel_result=None,
) -> Dict[str, Any]:
    """
    用时间线填充器生成行程并直接写入 DB。

    返回 {"days_created": N, "items_created": N, "plan_id": str}
    """
    from app.db.models.derived import ItineraryPlan, ItineraryDay, ItineraryItem

    # 城市推断：从 activity_clusters 表查 cluster_id→city_code 映射
    # 避免依赖脆弱的前缀硬编码（hok→sapporo 等错误）
    _cluster_city_map: Dict[str, str] = {}
    try:
        from sqlalchemy import select as _sel
        from app.db.models.city_circles import ActivityCluster
        _driver_ids = [
            (f.main_driver if hasattr(f, "main_driver") else "")
            for f in frames if (f.main_driver if hasattr(f, "main_driver") else "")
        ]
        if _driver_ids:
            _cq = await session.execute(
                _sel(ActivityCluster.cluster_id, ActivityCluster.city_code)
                .where(ActivityCluster.cluster_id.in_(_driver_ids))
            )
            for cid, cc in _cq.all():
                _cluster_city_map[cid] = cc
        logger.info("cluster→city map: %s", _cluster_city_map)
    except Exception as exc:
        logger.warning("Failed to load cluster→city mapping: %s", exc)

    # 酒店坐标缓存：从 DB 查各城市酒店实体的中心坐标
    # 这样新城市上线时自动覆盖，不需要手动维护硬编码表
    _CITY_HOTEL_COORDS: Dict[str, Tuple[float, float]] = {}
    try:
        from sqlalchemy import func as _func
        from app.db.models.catalog import EntityBase as _EB
        _hotel_q = await session.execute(
            _sel(_EB.city_code, _func.avg(_EB.lat), _func.avg(_EB.lng))
            .where(_EB.entity_type == "hotel", _EB.is_active == True,
                   _EB.lat.isnot(None), _EB.lng.isnot(None))
            .group_by(_EB.city_code)
        )
        for city, avg_lat, avg_lng in _hotel_q.all():
            if avg_lat and avg_lng:
                _CITY_HOTEL_COORDS[city] = (float(avg_lat), float(avg_lng))
        logger.info("Hotel coords loaded: %d cities", len(_CITY_HOTEL_COORDS))
    except Exception as exc:
        logger.warning("Failed to load hotel coords from DB: %s", exc)

    party_type = (profile.get("party_type") or "couple").lower()
    pace = (profile.get("pace") or "moderate").lower()

    # 默认起始坐标回退：如果某城市没有酒店，用该城市 POI 坐标的中心
    # 如果连 POI 都没有，用候选池第一个有坐标的实体
    default_hotel = (0.0, 0.0)
    if poi_pool:
        lats = [float(p["lat"]) for p in poi_pool if p.get("lat")]
        lngs = [float(p["lng"]) for p in poi_pool if p.get("lng")]
        if lats and lngs:
            default_hotel = (sum(lats) / len(lats), sum(lngs) / len(lngs))

    total_days = 0
    total_items = 0
    prev_end_min = 0
    global_used: set = set()

    for i, frame in enumerate(frames):
        day_idx = frame.day_index if hasattr(frame, "day_index") else i
        day_type = frame.day_type if hasattr(frame, "day_type") else "normal"
        driver = frame.main_driver if hasattr(frame, "main_driver") else ""
        corridor = frame.primary_corridor if hasattr(frame, "primary_corridor") else ""

        # 推断城市：优先从 cluster→city 映射，其次 sleep_base
        day_city = ""
        if driver and driver in _cluster_city_map:
            day_city = _cluster_city_map[driver]
        if not day_city:
            sleep = (frame.sleep_base if hasattr(frame, "sleep_base") else "") or ""
            if sleep:
                day_city = sleep
        if not day_city:
            day_city = "sapporo"

        # 确定时间窗（基于硬约束）
        if day_type == "arrival":
            avail_from = 14 * 60   # 到达日下午 14:00 开始
            avail_until = 21 * 60
        elif day_type == "departure":
            avail_from = 8 * 60    # 离开日早上
            avail_until = 14 * 60  # 下午要去机场
        else:
            avail_from = 9 * 60    # 普通日上午
            avail_until = 21 * 60

        # 前一天太晚 → 今天推迟出门
        if prev_end_min > 22 * 60:
            avail_from = max(avail_from, 10 * 60)
        elif prev_end_min > 21 * 60:
            avail_from = max(avail_from, 9 * 60 + 30)

        # 节奏调整
        if pace == "relaxed":
            avail_from += 30
            avail_until -= 30
        elif pace == "packed":
            avail_from = max(7 * 60 + 30, avail_from - 30)
            avail_until = min(23 * 60, avail_until + 60)

        # 带小孩/老人早点回
        if party_type in ("family_child", "senior"):
            avail_until = min(avail_until, 19 * 60 + 30)

        # anchor 实体
        anchors = []
        if ranking_result and hasattr(ranking_result, "selected_majors"):
            for major in ranking_result.selected_majors:
                m_id = major.cluster_id if hasattr(major, "cluster_id") else ""
                if m_id == driver:
                    for eid in (major.anchor_entity_ids or []):
                        for p in poi_pool:
                            if str(p.get("entity_id", "")) == str(eid) and str(eid) not in global_used:
                                anchors.append(p)
                                break

        # 过滤同城市候选
        city_pois = [p for p in poi_pool
                     if (p.get("city_code") or "").lower() == day_city.lower()
                     and str(p.get("entity_id", "")) not in global_used]
        city_rests = [r for r in restaurant_pool
                      if (r.get("city_code") or "").lower() == day_city.lower()
                      and str(r.get("entity_id", "")) not in global_used]

        # 起始坐标：用该城市的酒店坐标而非全局默认
        hotel_coords = _CITY_HOTEL_COORDS.get(day_city.lower(), default_hotel)

        # 填充
        day_tl = fill_day(
            day_index=day_idx,
            day_type=day_type,
            day_city=day_city,
            available_from=avail_from,
            available_until=avail_until,
            anchor_entities=anchors,
            poi_pool=city_pois,
            restaurant_pool=city_rests,
            start_lat=hotel_coords[0],
            start_lng=hotel_coords[1],
        )

        # 写 DB
        it_day = ItineraryDay(
            plan_id=plan_id,
            day_number=day_idx,
            city_code=day_city,
            day_theme=f"Day {day_idx}" if not driver else driver,
        )
        session.add(it_day)
        await session.flush()

        for sort_idx, item in enumerate(day_tl.items):
            if item.is_transit:
                continue
            it_item = ItineraryItem(
                day_id=it_day.day_id,
                sort_order=sort_idx,
                item_type=item.entity_type,
                entity_id=uuid.UUID(item.entity_id) if item.entity_id else None,
                start_time=_min_to_hhmm(item.start_time),
                end_time=_min_to_hhmm(item.start_time + item.duration_min),
                duration_min=item.duration_min,
                notes_zh=item.notes or "",
                is_optional=not item.is_anchor,
            )
            session.add(it_item)
            total_items += 1
            global_used.add(item.entity_id)

        total_days += 1
        prev_end_min = day_tl.available_until

        logger.info(
            "Timeline Day %d [%s] %s: %d items, %s-%s",
            day_idx, day_type, day_city,
            day_tl.total_items,
            day_tl.start_time_hhmm, day_tl.end_time_hhmm,
        )

    await session.flush()
    return {"days_created": total_days, "items_created": total_items, "plan_id": str(plan_id)}
