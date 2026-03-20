"""
交通矩阵模块 — 两点间交通时间查询

优先级：
    1. Redis 缓存（TTL 1 天）
    2. DB 缓存 route_matrix_cache（TTL 30 天）
    3. Google Routes API（Transit + Walking）
    4. Fallback：步行 15 分钟 / 公交 30 分钟

用法：
    from app.domains.planning.route_matrix import get_travel_time
    result = await get_travel_time(session, origin_id, dest_id, mode="transit")
"""
from __future__ import annotations

import json
import logging
import math
import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.catalog import EntityBase
from app.db.models.derived import RouteMatrixCache

logger = logging.getLogger(__name__)

TravelMode = Literal["transit", "walking", "driving"]

# Google Routes API 端点
_ROUTES_API_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"

# Redis key 前缀
_REDIS_PREFIX = "route_matrix:"
_REDIS_TTL = 86400  # 1 天

# DB 缓存 TTL
_DB_TTL_DAYS = 30

# Fallback 默认时间（分钟）
_FALLBACK_TRANSIT_MIN = 30
_FALLBACK_WALKING_MIN = 15
_FALLBACK_DRIVING_MIN = 20


# ─── 主入口 ────────────────────────────────────────────────────────────────────

async def get_travel_time(
    session: AsyncSession,
    origin_id: uuid.UUID,
    dest_id: uuid.UUID,
    mode: TravelMode = "transit",
    redis_client=None,
) -> dict:
    """获取两点间交通时间。

    Returns:
        {
            "duration_min": int,       # 分钟数
            "distance_km": float,      # 公里数（可能为 None）
            "mode": str,               # 实际使用的模式
            "source": str,             # "redis" / "db" / "api" / "fallback"
        }
    """
    cache_key = _build_redis_key(origin_id, dest_id, mode)

    # 1. Redis 缓存
    if redis_client:
        cached = await _get_from_redis(redis_client, cache_key)
        if cached:
            return cached

    # 2. DB 缓存
    db_cached = await _get_from_db(session, origin_id, dest_id, mode)
    if db_cached:
        if redis_client:
            await _set_to_redis(redis_client, cache_key, db_cached)
        return db_cached

    # 3. 获取实体坐标
    origin = await session.get(EntityBase, origin_id)
    dest = await session.get(EntityBase, dest_id)

    if not origin or not dest or not origin.lat or not dest.lat:
        return _fallback_result(mode)

    # 4. Google Routes API
    if settings.google_places_api_key:
        api_result = await _call_routes_api(
            lat1=float(origin.lat), lng1=float(origin.lng),
            lat2=float(dest.lat), lng2=float(dest.lng),
            mode=mode,
            api_key=settings.google_places_api_key,
        )
        if api_result:
            await _save_to_db(session, origin_id, dest_id, mode, api_result)
            if redis_client:
                await _set_to_redis(redis_client, cache_key, api_result)
            return api_result

    # 5. Fallback：haversine 估算
    result = _haversine_fallback(
        float(origin.lat), float(origin.lng),
        float(dest.lat), float(dest.lng),
        mode,
    )
    await _save_to_db(session, origin_id, dest_id, mode, result)
    if redis_client:
        await _set_to_redis(redis_client, cache_key, result)
    return result


# ─── Redis ─────────────────────────────────────────────────────────────────────

def _build_redis_key(origin_id: uuid.UUID, dest_id: uuid.UUID, mode: str) -> str:
    return f"{_REDIS_PREFIX}{origin_id}:{dest_id}:{mode}"


async def _get_from_redis(redis_client, key: str) -> Optional[dict]:
    try:
        raw = await redis_client.get(key)
        if raw:
            data = json.loads(raw)
            data["source"] = "redis"
            return data
    except Exception as e:
        logger.warning(f"Redis get failed: {e}")
    return None


async def _set_to_redis(redis_client, key: str, data: dict) -> None:
    try:
        payload = {k: v for k, v in data.items() if k != "source"}
        await redis_client.setex(key, _REDIS_TTL, json.dumps(payload))
    except Exception as e:
        logger.warning(f"Redis set failed: {e}")


# ─── DB 缓存 ───────────────────────────────────────────────────────────────────

async def _get_from_db(
    session: AsyncSession,
    origin_id: uuid.UUID,
    dest_id: uuid.UUID,
    mode: str,
) -> Optional[dict]:
    now = datetime.now(timezone.utc)
    stmt = select(RouteMatrixCache).where(
        RouteMatrixCache.origin_entity_id == origin_id,
        RouteMatrixCache.dest_entity_id == dest_id,
        RouteMatrixCache.travel_mode == mode,
        (RouteMatrixCache.expires_at == None) | (RouteMatrixCache.expires_at > now),  # noqa: E711
    ).limit(1)
    row = (await session.execute(stmt)).scalar_one_or_none()
    if row:
        return {
            "duration_min": row.duration_min,
            "distance_km": float(row.distance_km) if row.distance_km else None,
            "mode": row.travel_mode,
            "source": "db",
        }
    return None


async def _save_to_db(
    session: AsyncSession,
    origin_id: uuid.UUID,
    dest_id: uuid.UUID,
    mode: str,
    result: dict,
) -> None:
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=_DB_TTL_DAYS)
    record = RouteMatrixCache(
        origin_entity_id=origin_id,
        dest_entity_id=dest_id,
        travel_mode=mode,
        duration_min=result["duration_min"],
        distance_km=result.get("distance_km"),
        computed_at=now,
        expires_at=expires,
    )
    session.add(record)
    try:
        await session.flush()
    except Exception as e:
        logger.warning(f"DB cache save failed: {e}")
        await session.rollback()


# ─── Google Routes API ─────────────────────────────────────────────────────────

async def _call_routes_api(
    lat1: float, lng1: float,
    lat2: float, lng2: float,
    mode: str,
    api_key: str,
) -> Optional[dict]:
    """调用 Google Routes API。"""
    travel_mode_map = {
        "transit": "TRANSIT",
        "walking": "WALK",
        "driving": "DRIVE",
    }
    g_mode = travel_mode_map.get(mode, "TRANSIT")

    payload = {
        "origin": {"location": {"latLng": {"latitude": lat1, "longitude": lng1}}},
        "destination": {"location": {"latLng": {"latitude": lat2, "longitude": lng2}}},
        "travelMode": g_mode,
        "routingPreference": "TRAFFIC_AWARE" if mode == "driving" else None,
        "computeAlternativeRoutes": False,
        "languageCode": "zh-CN",
        "units": "METRIC",
    }
    # 清除 None 字段
    payload = {k: v for k, v in payload.items() if v is not None}

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "routes.duration,routes.distanceMeters",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(_ROUTES_API_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        routes = data.get("routes", [])
        if not routes:
            return None

        route = routes[0]
        # duration 格式 "123s"
        duration_str = route.get("duration", "0s")
        duration_sec = int(duration_str.rstrip("s")) if duration_str else 0
        duration_min = max(1, round(duration_sec / 60))
        distance_m = route.get("distanceMeters", 0)
        distance_km = round(distance_m / 1000, 2) if distance_m else None

        return {
            "duration_min": duration_min,
            "distance_km": distance_km,
            "mode": mode,
            "source": "api",
        }
    except Exception as e:
        logger.warning(f"Google Routes API failed: {e}")
        return None


# ─── Fallback ─────────────────────────────────────────────────────────────────

def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Haversine 公式计算两点直线距离（公里）。"""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lng2 - lng1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _haversine_fallback(
    lat1: float, lng1: float,
    lat2: float, lng2: float,
    mode: str,
) -> dict:
    """基于直线距离估算交通时间。

    估算速度：
        walking: 5 km/h
        transit: 25 km/h（含候车时间，最少 10 分钟）
        driving: 30 km/h（城市拥堵，最少 10 分钟）
    """
    dist_km = _haversine_km(lat1, lng1, lat2, lng2)

    if mode == "walking":
        speed_kmh = 5.0
        min_minutes = 5
    elif mode == "transit":
        speed_kmh = 25.0
        min_minutes = 10
    else:  # driving
        speed_kmh = 30.0
        min_minutes = 10

    duration_min = max(min_minutes, round(dist_km / speed_kmh * 60))

    return {
        "duration_min": duration_min,
        "distance_km": round(dist_km, 2),
        "mode": mode,
        "source": "fallback",
    }


def _fallback_result(mode: str) -> dict:
    """无坐标时的默认值。"""
    defaults = {
        "transit": _FALLBACK_TRANSIT_MIN,
        "walking": _FALLBACK_WALKING_MIN,
        "driving": _FALLBACK_DRIVING_MIN,
    }
    return {
        "duration_min": defaults.get(mode, _FALLBACK_TRANSIT_MIN),
        "distance_km": None,
        "mode": mode,
        "source": "fallback",
    }


# ─── 批量查询 ──────────────────────────────────────────────────────────────────

async def get_travel_time_matrix(
    session: AsyncSession,
    entity_ids: list[uuid.UUID],
    mode: TravelMode = "transit",
    redis_client=None,
) -> dict[tuple[uuid.UUID, uuid.UUID], dict]:
    """批量获取一组实体之间的两两交通时间。

    返回 {(origin_id, dest_id): result_dict}
    """
    results: dict[tuple[uuid.UUID, uuid.UUID], dict] = {}
    for i, origin_id in enumerate(entity_ids):
        for dest_id in entity_ids[i + 1:]:
            result = await get_travel_time(session, origin_id, dest_id, mode, redis_client)
            results[(origin_id, dest_id)] = result
            results[(dest_id, origin_id)] = {**result}  # 双向近似对称
    return results
