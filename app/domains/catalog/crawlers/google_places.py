"""
Google Places API 爬虫

覆盖：日本（及全球）城市的酒店、特色店铺、POI、餐厅
API: Places API (New) — Nearby Search / Text Search
费用: $200/月免费额度，约 6000 次搜索/月

用法:
    from app.domains.catalog.crawlers.google_places import (
        fetch_hotels, fetch_specialty_shops, fetch_pois, fetch_restaurants,
    )
    results = await fetch_hotels("sapporo", limit=20)
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# 城市中心坐标（用于 Nearby Search 的圆心）
# 不在此表中的城市会通过 Nominatim 自动查询
# ─────────────────────────────────────────────────────────────────────────────
CITY_CENTER: Dict[str, tuple[float, float]] = {
    # 北海道
    "sapporo":     (43.0621, 141.3544),
    "otaru":       (43.1907, 140.9945),
    "hakodate":    (41.7687, 140.7288),
    "asahikawa":   (43.7707, 142.3650),
    "furano":      (43.3420, 142.3833),
    "biei":        (43.5862, 142.4718),
    "noboribetsu": (42.4127, 141.1071),
    "niseko":      (42.8604, 140.6874),
    "abashiri":    (44.0206, 144.2736),
    "kushiro":     (42.9850, 144.3815),
    "toya":        (42.6069, 140.8428),
    # 关西
    "tokyo":       (35.6762, 139.6503),
    "osaka":       (34.6937, 135.5023),
    "kyoto":       (35.0116, 135.7681),
    "nara":        (34.6851, 135.8048),
    "kobe":        (34.6901, 135.1956),
    # 关东
    "hakone":      (35.2326, 139.1070),
    "kamakura":    (35.3197, 139.5466),
    "yokohama":    (35.4437, 139.6380),
    "nikko":       (36.7500, 139.5986),
    "kawaguchiko": (35.5162, 138.7553),
    # 九州
    "fukuoka":     (33.5904, 130.4017),
    # 冲绳
    "naha":        (26.2124, 127.6809),
    "ishigaki":    (24.3448, 124.1553),
    # 其他
    "kanazawa":    (36.5613, 136.6562),
    "hiroshima":   (34.3853, 132.4553),
    "nagoya":      (35.1815, 136.9066),
    "sendai":      (38.2682, 140.8694),
}

# 搜索半径（米）：小城市用大半径确保有结果
CITY_RADIUS: Dict[str, int] = {
    "tokyo": 15000, "osaka": 12000, "sapporo": 10000,
    "furano": 20000, "biei": 25000, "niseko": 25000,
    "abashiri": 20000, "kushiro": 15000, "toya": 20000,
}
DEFAULT_RADIUS = 10000  # 10km


# ─────────────────────────────────────────────────────────────────────────────
# API 调用核心
# ─────────────────────────────────────────────────────────────────────────────

_API_BASE = "https://maps.googleapis.com/maps/api/place"

# 每日调用计数器（简易防超额，生产环境应用 Redis）
_daily_call_count = 0
_DAILY_LIMIT = 500  # 保守限制，$200 额度约支撑 6000 次


async def _get_city_center(city_code: str) -> Optional[tuple[float, float]]:
    """获取城市中心坐标，先查本地映射，不在则用 Nominatim 查询"""
    if city_code in CITY_CENTER:
        return CITY_CENTER[city_code]

    # Nominatim 免费地理编码
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": city_code, "format": "json", "limit": 1},
                headers={"User-Agent": "TravelAI/1.0"},
            )
            if resp.status_code == 200 and resp.json():
                r = resp.json()[0]
                center = (float(r["lat"]), float(r["lon"]))
                CITY_CENTER[city_code] = center  # 缓存
                return center
    except Exception as e:
        logger.warning("Nominatim lookup failed for %s: %s", city_code, e)
    return None


async def _nearby_search(
    lat: float, lng: float, radius: int,
    place_type: str,
    keyword: str = "",
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    Google Places Nearby Search API 调用

    Returns: list of place dicts with standardized fields
    """
    global _daily_call_count
    settings = get_settings()
    api_key = settings.google_places_api_key

    if not api_key:
        logger.debug("Google Places API key not configured, skipping")
        return []

    if _daily_call_count >= _DAILY_LIMIT:
        logger.warning("Google Places daily limit reached (%d), skipping", _DAILY_LIMIT)
        return []

    params: Dict[str, Any] = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "type": place_type,
        "language": "ja",
        "key": api_key,
    }
    if keyword:
        params["keyword"] = keyword

    all_results: List[Dict[str, Any]] = []

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # 首页
            resp = await client.get(f"{_API_BASE}/nearbysearch/json", params=params)
            _daily_call_count += 1

            if resp.status_code != 200:
                logger.warning("Google Places API returned %d", resp.status_code)
                return []

            body = resp.json()
            if body.get("status") not in ("OK", "ZERO_RESULTS"):
                logger.warning("Google Places API status: %s — %s",
                               body.get("status"), body.get("error_message", ""))
                return []

            all_results.extend(body.get("results", []))

            # 翻页（最多 3 页，每页 20 条）
            while len(all_results) < limit and body.get("next_page_token"):
                await asyncio.sleep(2)  # Google 要求等 2 秒
                page_params = {"pagetoken": body["next_page_token"], "key": api_key}
                resp = await client.get(f"{_API_BASE}/nearbysearch/json", params=page_params)
                _daily_call_count += 1
                body = resp.json()
                all_results.extend(body.get("results", []))

    except Exception as e:
        logger.warning("Google Places Nearby Search failed: %s", e)
        return []

    return all_results[:limit]


def _parse_place(place: Dict[str, Any], city_code: str, entity_type: str) -> Dict[str, Any]:
    """将 Google Places API 原始结果转为 upsert_entity 兼容格式"""
    loc = place.get("geometry", {}).get("location", {})

    result: Dict[str, Any] = {
        "name_ja": place.get("name", ""),
        "name_zh": place.get("name", ""),  # 日文名先做 name_zh，后续可翻译
        "name_en": "",
        "city_code": city_code,
        "lat": loc.get("lat"),
        "lng": loc.get("lng"),
        "google_place_id": place.get("place_id"),
        "google_rating": place.get("rating"),
        "google_review_count": place.get("user_ratings_total"),
        "data_tier": "A",
        "source": "google",
    }

    # 地址
    result["address_ja"] = place.get("vicinity", "")

    # 营业状态
    opening = place.get("opening_hours", {})
    if opening.get("open_now") is not None:
        result["is_active"] = True

    return result


def _parse_hotel(place: Dict[str, Any], city_code: str) -> Dict[str, Any]:
    """解析酒店特有字段"""
    base = _parse_place(place, city_code, "hotel")

    # price_level: 0=free, 1=cheap, 2=moderate, 3=expensive, 4=very expensive
    price_level = place.get("price_level")
    tier_map = {0: "budget", 1: "budget", 2: "mid", 3: "premium", 4: "luxury"}
    base["price_tier"] = tier_map.get(price_level, "mid")

    # 从 types 推断酒店类型
    types = set(place.get("types", []))
    if "lodging" in types and "spa" in types:
        base["hotel_type"] = "ryokan"
    elif "lodging" in types:
        base["hotel_type"] = "city_hotel"

    return base


def _parse_restaurant(place: Dict[str, Any], city_code: str) -> Dict[str, Any]:
    """解析餐厅特有字段"""
    base = _parse_place(place, city_code, "restaurant")

    price_level = place.get("price_level")
    if price_level is not None:
        # 粗略映射：日本餐厅价格
        price_map = {
            0: (500, 500), 1: (800, 1200),
            2: (1200, 3000), 3: (3000, 8000), 4: (8000, 20000),
        }
        lo, hi = price_map.get(price_level, (1200, 3000))
        base["price_range_min_jpy"] = lo
        base["price_range_max_jpy"] = hi
        base["budget_lunch_jpy"] = lo
        base["budget_dinner_jpy"] = hi

    # 从 types 推断菜系
    types = set(place.get("types", []))
    if "meal_delivery" in types or "meal_takeaway" in types:
        base["cuisine_type"] = "fast_food"
    # 更精确的菜系需要 Place Details API（后续增强）

    return base


def _parse_specialty_shop(place: Dict[str, Any], city_code: str) -> Dict[str, Any]:
    """解析特色店铺 → 作为 POI (poi_category=specialty_shop)"""
    base = _parse_place(place, city_code, "poi")
    base["poi_category"] = "specialty_shop"
    base["typical_duration_min"] = 30  # 特色店铺默认 30 分钟
    base["admission_free"] = True
    return base


# ─────────────────────────────────────────────────────────────────────────────
# 公开 API：各类型实体抓取
# ─────────────────────────────────────────────────────────────────────────────

async def fetch_hotels(city_code: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    从 Google Places 抓取酒店数据

    Args:
        city_code: 城市代码
        limit: 最大数量

    Returns:
        酒店数据列表（兼容 upsert_entity 格式）
    """
    center = await _get_city_center(city_code)
    if not center:
        logger.warning("[google_places] No center coords for %s", city_code)
        return []

    radius = CITY_RADIUS.get(city_code, DEFAULT_RADIUS)
    raw = await _nearby_search(center[0], center[1], radius, "lodging", limit=limit)

    results = []
    for place in raw:
        parsed = _parse_hotel(place, city_code)
        if parsed.get("lat") and parsed.get("lng"):
            results.append(parsed)

    logger.info("[google_places] %s hotels: %d/%d raw", city_code, len(results), len(raw))
    return results


async def fetch_restaurants(city_code: str, limit: int = 20) -> List[Dict[str, Any]]:
    """从 Google Places 抓取餐厅数据"""
    center = await _get_city_center(city_code)
    if not center:
        return []

    radius = CITY_RADIUS.get(city_code, DEFAULT_RADIUS)
    raw = await _nearby_search(center[0], center[1], radius, "restaurant", limit=limit)

    results = []
    for place in raw:
        parsed = _parse_restaurant(place, city_code)
        if parsed.get("lat") and parsed.get("lng"):
            results.append(parsed)

    logger.info("[google_places] %s restaurants: %d", city_code, len(results))
    return results


async def fetch_pois(city_code: str, limit: int = 20) -> List[Dict[str, Any]]:
    """从 Google Places 抓取景点数据"""
    center = await _get_city_center(city_code)
    if not center:
        return []

    radius = CITY_RADIUS.get(city_code, DEFAULT_RADIUS)
    raw = await _nearby_search(center[0], center[1], radius, "tourist_attraction", limit=limit)

    results = []
    for place in raw:
        parsed = _parse_place(place, city_code, "poi")
        # 从 types 推断 poi_category
        types = set(place.get("types", []))
        if "museum" in types:
            parsed["poi_category"] = "museum"
        elif "park" in types:
            parsed["poi_category"] = "park"
        elif "church" in types or "place_of_worship" in types:
            parsed["poi_category"] = "temple"
        else:
            parsed["poi_category"] = "landmark"
        parsed["typical_duration_min"] = 60
        if parsed.get("lat") and parsed.get("lng"):
            results.append(parsed)

    logger.info("[google_places] %s POIs: %d", city_code, len(results))
    return results


async def fetch_specialty_shops(
    city_code: str,
    limit: int = 15,
    keywords: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    从 Google Places 抓取特色店铺（手工艺品、纪念品、本地特产等）

    Args:
        city_code: 城市代码
        limit: 最大数量
        keywords: 搜索关键词列表，默认使用日本特色店铺关键词

    Returns:
        POI 数据列表（poi_category=specialty_shop）
    """
    center = await _get_city_center(city_code)
    if not center:
        return []

    radius = CITY_RADIUS.get(city_code, DEFAULT_RADIUS)

    if keywords is None:
        keywords = [
            "お土産 手作り",      # 手工纪念品
            "工芸品 伝統",        # 传统工艺品
            "地元 特産品",        # 本地特产
            "雑貨 セレクトショップ",  # 杂货精选店
        ]

    all_results: List[Dict[str, Any]] = []
    seen_place_ids: set[str] = set()

    for kw in keywords:
        if len(all_results) >= limit:
            break
        raw = await _nearby_search(
            center[0], center[1], radius,
            "store", keyword=kw, limit=limit,
        )
        for place in raw:
            pid = place.get("place_id", "")
            if pid in seen_place_ids:
                continue
            seen_place_ids.add(pid)
            parsed = _parse_specialty_shop(place, city_code)
            if parsed.get("lat") and parsed.get("lng"):
                all_results.append(parsed)
        await asyncio.sleep(1)  # 关键词之间间隔

    logger.info("[google_places] %s specialty shops: %d", city_code, len(all_results))
    return all_results[:limit]


# ─────────────────────────────────────────────────────────────────────────────
# Place Details（补充详细信息，单独调用）
# ─────────────────────────────────────────────────────────────────────────────

async def fetch_place_details(place_id: str) -> Optional[Dict[str, Any]]:
    """
    获取单个地点的详细信息（用于补充数据）

    费用: $17/1000 次
    """
    global _daily_call_count
    settings = get_settings()
    api_key = settings.google_places_api_key

    if not api_key or _daily_call_count >= _DAILY_LIMIT:
        return None

    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,formatted_phone_number,website,"
                  "opening_hours,price_level,rating,user_ratings_total,"
                  "reviews,photos,types,geometry",
        "language": "ja",
        "key": api_key,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{_API_BASE}/details/json", params=params)
            _daily_call_count += 1
            body = resp.json()
            if body.get("status") == "OK":
                return body.get("result")
            logger.warning("Place Details failed: %s", body.get("status"))
    except Exception as e:
        logger.warning("Place Details request failed: %s", e)
    return None
