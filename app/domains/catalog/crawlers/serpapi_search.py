"""
SerpAPI 爬虫 — Google Places 的免费备选

用途：当 Google Places API key 不存在或额度用尽时，
      通过 SerpAPI 的 Google Maps 搜索抓取地点数据。

限制：免费计划 100 次/月，付费后可扩展。
API文档：https://serpapi.com/google-maps-api

用法:
    from app.domains.catalog.crawlers.serpapi_search import (
        fetch_serpapi_pois, fetch_serpapi_hotels,
    )
    results = await fetch_serpapi_pois("sapporo", limit=10)
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_SERPAPI_BASE = "https://serpapi.com/search"

# 搜索类型关键词
_QUERY_TEMPLATES = {
    "poi":          "{city} tourist attractions",
    "hotel":        "{city} hotels",
    "restaurant":   "{city} restaurants",
    "specialty_shop": "{city} 特色 手工艺品 specialty shop",
}

# 日调用计数（简易保护，生产用 Redis）
_daily_calls = 0
_DAILY_LIMIT = 80  # 保守留 20 次给其他用途


async def _serpapi_search(
    query: str,
    ll: Optional[str] = None,  # "@lat,lng,zoom" 格式
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    调用 SerpAPI Google Maps 搜索。

    Args:
        query: 搜索关键词
        ll: 坐标定位字符串，如 "@35.68,139.65,14z"
        limit: 最大结果数

    Returns:
        local_results 列表
    """
    global _daily_calls
    settings = get_settings()
    api_key = settings.serpapi_key

    if not api_key:
        logger.debug("[serpapi] SERPAPI_KEY 未配置，跳过")
        return []

    if _daily_calls >= _DAILY_LIMIT:
        logger.warning("[serpapi] 每日调用上限 %d，跳过", _DAILY_LIMIT)
        return []

    params: Dict[str, Any] = {
        "engine": "google_maps",
        "q": query,
        "api_key": api_key,
        "hl": "ja",
        "gl": "jp",
        "num": min(limit, 20),
    }
    if ll:
        params["ll"] = ll

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(_SERPAPI_BASE, params=params)
            _daily_calls += 1

            if resp.status_code != 200:
                logger.warning("[serpapi] HTTP %d for query '%s'", resp.status_code, query)
                return []

            body = resp.json()
            if "error" in body:
                logger.warning("[serpapi] API error: %s", body["error"])
                return []

            return body.get("local_results", [])[:limit]

    except Exception as e:
        logger.warning("[serpapi] Request failed: %s", e)
        return []


def _parse_result(result: Dict[str, Any], city_code: str, entity_type: str) -> Dict[str, Any]:
    """将 SerpAPI local_result 转为 upsert_entity 兼容格式"""
    gps = result.get("gps_coordinates", {})
    return {
        "name_ja": result.get("title", ""),
        "name_zh": result.get("title", ""),
        "name_en": result.get("title", ""),
        "city_code": city_code,
        "lat": gps.get("latitude"),
        "lng": gps.get("longitude"),
        "google_rating": result.get("rating"),
        "google_review_count": result.get("reviews"),
        "address_ja": result.get("address", ""),
        "data_tier": "A",
        "source": "serpapi",
    }


def _ll_from_city(city_code: str) -> Optional[str]:
    """从 google_places 的 CITY_CENTER 生成定位字符串"""
    try:
        from app.domains.catalog.crawlers.google_places import CITY_CENTER
        center = CITY_CENTER.get(city_code)
        if center:
            return f"@{center[0]},{center[1]},14z"
    except ImportError:
        pass
    return None


async def fetch_serpapi_pois(city_code: str, limit: int = 10) -> List[Dict[str, Any]]:
    """从 SerpAPI 抓取景点数据"""
    city_name = city_code.replace("_", " ").title()
    query = _QUERY_TEMPLATES["poi"].format(city=city_name)
    ll = _ll_from_city(city_code)
    raw = await _serpapi_search(query, ll=ll, limit=limit)

    results = []
    for r in raw:
        parsed = _parse_result(r, city_code, "poi")
        parsed["poi_category"] = "landmark"
        parsed["typical_duration_min"] = 60
        if parsed.get("lat") and parsed.get("lng"):
            results.append(parsed)

    logger.info("[serpapi] %s POIs: %d", city_code, len(results))
    return results


async def fetch_serpapi_hotels(city_code: str, limit: int = 10) -> List[Dict[str, Any]]:
    """从 SerpAPI 抓取酒店数据"""
    city_name = city_code.replace("_", " ").title()
    query = _QUERY_TEMPLATES["hotel"].format(city=city_name)
    ll = _ll_from_city(city_code)
    raw = await _serpapi_search(query, ll=ll, limit=limit)

    results = []
    for r in raw:
        parsed = _parse_result(r, city_code, "hotel")
        parsed["hotel_type"] = "city_hotel"
        parsed["price_tier"] = "mid"
        if parsed.get("lat") and parsed.get("lng"):
            results.append(parsed)

    logger.info("[serpapi] %s hotels: %d", city_code, len(results))
    return results


async def fetch_serpapi_restaurants(city_code: str, limit: int = 10) -> List[Dict[str, Any]]:
    """从 SerpAPI 抓取餐厅数据"""
    city_name = city_code.replace("_", " ").title()
    query = _QUERY_TEMPLATES["restaurant"].format(city=city_name)
    ll = _ll_from_city(city_code)
    raw = await _serpapi_search(query, ll=ll, limit=limit)

    results = []
    for r in raw:
        parsed = _parse_result(r, city_code, "restaurant")
        parsed["cuisine_type"] = "unknown"
        if parsed.get("lat") and parsed.get("lng"):
            results.append(parsed)

    logger.info("[serpapi] %s restaurants: %d", city_code, len(results))
    return results
