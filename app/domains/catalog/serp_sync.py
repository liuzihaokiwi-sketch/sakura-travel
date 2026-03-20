from __future__ import annotations

"""
SerpAPI 数据采集模块
- search_tabelog_restaurants: 从 Tabelog 搜索餐厅数据
- search_google_pois:         用 Google 搜索景点信息
- sync_restaurant_via_serp:   采集餐厅 → 写快照 → upsert_entity
- sync_poi_via_serp:          采集景点 → 写快照 → upsert_entity
"""

import asyncio
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.snapshots import record_snapshot
from app.domains.catalog.upsert import upsert_entity

_SERPAPI_URL = "https://serpapi.com/search.json"


# ── 底层搜索函数 ───────────────────────────────────────────────────────────────

async def _serp_search(params: Dict[str, Any]) -> Dict[str, Any]:
    """调用 SerpAPI，返回原始 JSON"""
    params["api_key"] = settings.serpapi_key
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(_SERPAPI_URL, params=params)
        resp.raise_for_status()
        return resp.json()


# ── Tabelog 餐厅搜索 ──────────────────────────────────────────────────────────

async def search_tabelog_restaurants(
    city: str,
    cuisine: str = "",
    max_results: int = 10,
) -> List[Dict[str, Any]]:
    """
    通过 Google 搜索 Tabelog 餐厅页面，提取餐厅信息。

    Args:
        city:        城市名，如 "东京" / "tokyo"
        cuisine:     菜系，如 "寿司" / "拉面"（可选）
        max_results: 最多结果数

    Returns:
        餐厅信息列表
    """
    query = f"site:tabelog.com {city} {cuisine} 餐厅 评分".strip()
    params = {
        "engine": "google",
        "q": query,
        "hl": "zh-cn",
        "gl": "jp",
        "num": max_results,
    }
    data = await _serp_search(params)
    results = data.get("organic_results", [])

    restaurants = []
    for r in results:
        # 只处理 tabelog.com 的链接
        link = r.get("link", "")
        if "tabelog.com" not in link:
            continue

        # 尝试从 snippet 提取评分
        snippet = r.get("snippet", "")
        rating = _extract_tabelog_rating(snippet)

        restaurants.append({
            "name": r.get("title", "").replace(" | 食べログ", "").strip(),
            "url": link,
            "snippet": snippet,
            "tabelog_rating": rating,
            "source": "tabelog",
        })

    return restaurants[:max_results]


def _extract_tabelog_rating(snippet: str) -> Optional[float]:
    """从 Tabelog snippet 文字中提取评分（如 '3.85'）"""
    import re
    # Tabelog 评分格式：3.50 ~ 4.99
    match = re.search(r'\b([3-4]\.\d{2})\b', snippet)
    if match:
        return float(match.group(1))
    return None


# ── Google POI 搜索 ───────────────────────────────────────────────────────────

async def search_google_pois(
    city: str,
    category: str = "景点",
    max_results: int = 10,
) -> List[Dict[str, Any]]:
    """
    通过 Google 搜索景点信息（使用 SerpAPI Google Maps 引擎）。

    Args:
        city:        城市名，如 "东京"
        category:    类别，如 "神社" / "博物馆" / "景点"
        max_results: 最多结果数

    Returns:
        景点信息列表
    """
    params = {
        "engine": "google_maps",
        "q": f"{city} {category}",
        "hl": "zh-cn",
        "gl": "jp",
        "type": "search",
    }
    data = await _serp_search(params)
    results = data.get("local_results", [])

    pois = []
    for r in results[:max_results]:
        gps = r.get("gps_coordinates", {})
        pois.append({
            "name": r.get("title", ""),
            "address": r.get("address", ""),
            "rating": r.get("rating"),
            "reviews": r.get("reviews"),
            "lat": gps.get("latitude"),
            "lng": gps.get("longitude"),
            "type": r.get("type", ""),
            "place_id": r.get("place_id", ""),
            "source": "google_maps",
        })

    return pois


# ── 完整采集流程：餐厅 ────────────────────────────────────────────────────────

async def sync_restaurant_via_serp(
    session: AsyncSession,
    city_code: str,
    city_name_ja: str,
    cuisine: str = "",
    max_results: int = 10,
) -> List[str]:
    """
    用 SerpAPI 批量采集餐厅并写入 DB。

    Returns:
        写入的 entity_id 列表
    """
    raw_list = await search_tabelog_restaurants(
        city=city_name_ja,
        cuisine=cuisine,
        max_results=max_results,
    )

    entity_ids = []
    for raw in raw_list:
        if not raw.get("name"):
            continue

        # 记录快照
        await record_snapshot(
            session=session,
            source_name="serpapi_tabelog",
            object_type="restaurant",
            object_id=raw.get("url", raw["name"]),
            raw_payload=raw,
            expires_in_days=7,
            http_status=200,
            request_url=raw.get("url", ""),
        )

        # 构建 upsert 数据
        data: Dict[str, Any] = {
            "name_zh": raw["name"],
            "city_code": city_code,
            "data_tier": "B",
            "tabelog_score": raw.get("tabelog_rating"),
            "cuisine_type": cuisine or "japanese",
        }
        # tabelog URL 作为去重 key
        tabelog_id = _extract_tabelog_id(raw.get("url", ""))

        try:
            entity = await upsert_entity(
                session=session,
                entity_type="restaurant",
                data={k: v for k, v in data.items() if v is not None},
                tabelog_id=tabelog_id,
            )
            entity_ids.append(str(entity.entity_id))
        except Exception:
            continue

    return entity_ids


def _extract_tabelog_id(url: str) -> Optional[str]:
    """从 Tabelog URL 提取餐厅 ID，如 https://tabelog.com/tokyo/A1301/A130101/13000001/ → '13000001'"""
    import re
    match = re.search(r'/(\d{8})/?$', url)
    if match:
        return match.group(1)
    # fallback：用 URL 最后段
    parts = url.rstrip("/").split("/")
    return parts[-1] if parts else None


# ── 完整采集流程：景点 ────────────────────────────────────────────────────────

async def sync_poi_via_serp(
    session: AsyncSession,
    city_code: str,
    city_name_ja: str,
    category: str = "景点",
    max_results: int = 10,
) -> List[str]:
    """
    用 SerpAPI Google Maps 批量采集景点并写入 DB。

    Returns:
        写入的 entity_id 列表
    """
    raw_list = await search_google_pois(
        city=city_name_ja,
        category=category,
        max_results=max_results,
    )

    # 类别映射
    category_map = {
        "神社": "shrine", "寺庙": "temple", "寺院": "temple",
        "博物馆": "museum", "美术馆": "museum",
        "公园": "park", "城堡": "castle",
        "温泉": "onsen", "购物": "shopping",
        "景点": "landmark", "主题公园": "theme_park",
    }
    poi_category = category_map.get(category, "landmark")

    entity_ids = []
    for raw in raw_list:
        if not raw.get("name"):
            continue

        await record_snapshot(
            session=session,
            source_name="serpapi_google_maps",
            object_type="poi",
            object_id=raw.get("place_id", raw["name"]),
            raw_payload=raw,
            expires_in_days=30,
            http_status=200,
        )

        data: Dict[str, Any] = {
            "name_zh": raw["name"],
            "city_code": city_code,
            "data_tier": "B",
            "lat": raw.get("lat"),
            "lng": raw.get("lng"),
            "address_en": raw.get("address"),
            "google_rating": raw.get("rating"),
            "google_review_count": raw.get("reviews"),
            "poi_category": poi_category,
        }

        google_place_id = raw.get("place_id") or None

        try:
            entity = await upsert_entity(
                session=session,
                entity_type="poi",
                data={k: v for k, v in data.items() if v is not None},
                google_place_id=google_place_id,
            )
            entity_ids.append(str(entity.entity_id))
        except Exception:
            continue

    return entity_ids


# ── 批量城市采集（一键启动）──────────────────────────────────────────────────

CITY_CONFIG = {
    "tokyo":     {"name_ja": "東京",  "name_zh": "东京"},
    "osaka":     {"name_ja": "大阪",  "name_zh": "大阪"},
    "kyoto":     {"name_ja": "京都",  "name_zh": "京都"},
    "nara":      {"name_ja": "奈良",  "name_zh": "奈良"},
    "hakone":    {"name_ja": "箱根",  "name_zh": "箱根"},
    "sapporo":   {"name_ja": "札幌",  "name_zh": "札幌"},
    "fukuoka":   {"name_ja": "福岡",  "name_zh": "福冈"},
    "hiroshima": {"name_ja": "広島",  "name_zh": "广岛"},
    "naha":      {"name_ja": "那覇",  "name_zh": "那霸"},
}

POI_CATEGORIES = ["神社", "寺院", "博物馆", "公园", "城堡", "温泉", "景点"]
RESTAURANT_CUISINES = ["寿司", "拉面", "天妇罗", "烧鸟", "怀石料理", "居酒屋"]


async def bulk_sync_city(
    session: AsyncSession,
    city_code: str,
    sync_pois: bool = True,
    sync_restaurants: bool = True,
) -> Dict[str, int]:
    """
    一键采集指定城市的所有景点和餐厅。

    Returns:
        {"pois": 采集数量, "restaurants": 采集数量}
    """
    city_info = CITY_CONFIG.get(city_code)
    if not city_info:
        raise ValueError(f"未知城市代码: {city_code}")

    city_name = city_info["name_ja"]
    total_pois = 0
    total_restaurants = 0

    if sync_pois:
        for cat in POI_CATEGORIES:
            ids = await sync_poi_via_serp(
                session, city_code, city_name, category=cat, max_results=5
            )
            total_pois += len(ids)
            await asyncio.sleep(1)  # 避免 SerpAPI 频率限制

    if sync_restaurants:
        for cuisine in RESTAURANT_CUISINES:
            ids = await sync_restaurant_via_serp(
                session, city_code, city_name, cuisine=cuisine, max_results=5
            )
            total_restaurants += len(ids)
            await asyncio.sleep(1)

    return {"pois": total_pois, "restaurants": total_restaurants}
