from __future__ import annotations

"""
Google Places API 采集模块
- fetch_place_details: 按 place_id 拉取原始数据
- sync_poi_to_db:      拉取 + 写快照 + upsert_entity
- search_places:       按关键词搜索（用于初始种子采集）
"""

from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.snapshots import record_snapshot
from app.domains.catalog.upsert import upsert_entity

# Google Places API (New) 端点
_PLACE_DETAILS_URL = "https://places.googleapis.com/v1/places/{place_id}"
_PLACE_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

# 请求的字段掩码（只拿需要的字段，省钱）
_DETAIL_FIELD_MASK = ",".join([
    "id", "displayName", "internationalPhoneNumber",
    "formattedAddress", "location", "rating", "userRatingCount",
    "regularOpeningHours", "primaryType", "types",
    "editorialSummary", "photos",
])


# ── 原始数据拉取 ───────────────────────────────────────────────────────────────

async def fetch_place_details(api_key: str, place_id: str) -> Dict[str, Any]:
    """
    调用 Google Places API (New) 获取地点详情。

    Args:
        api_key:  Google Places API Key
        place_id: Google Place ID（格式：places/ChIJ...）

    Returns:
        原始 API 响应 dict

    Raises:
        httpx.HTTPStatusError: 非 2xx 响应
    """
    # place_id 可能带 "places/" 前缀，也可能不带
    clean_id = place_id.removeprefix("places/")
    url = _PLACE_DETAILS_URL.format(place_id=clean_id)

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            url,
            headers={
                "X-Goog-Api-Key": api_key,
                "X-Goog-FieldMask": _DETAIL_FIELD_MASK,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def search_places(
    api_key: str,
    query: str,
    language_code: str = "zh-TW",
    max_results: int = 20,
) -> List[Dict[str, Any]]:
    """
    按文字搜索地点（用于批量种子采集）。

    Args:
        api_key:       Google Places API Key
        query:         搜索词，如 "东京景点" / "京都温泉旅馆"
        language_code: 返回语言
        max_results:   最多返回条数（1-20）

    Returns:
        places 列表
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            _PLACE_SEARCH_URL,
            headers={
                "X-Goog-Api-Key": api_key,
                "X-Goog-FieldMask": f"places.{_DETAIL_FIELD_MASK}",
                "Content-Type": "application/json",
            },
            json={
                "textQuery": query,
                "languageCode": language_code,
                "pageSize": min(max_results, 20),
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("places", [])


# ── 数据转换 ──────────────────────────────────────────────────────────────────

def _parse_place_to_entity_data(
    raw: Dict[str, Any],
    city_code: str,
    entity_type: str = "poi",
) -> Dict[str, Any]:
    """
    把 Google Places 原始响应转换为 upsert_entity 所需的 data dict。
    """
    loc = raw.get("location", {})
    display_name = raw.get("displayName", {})
    opening = raw.get("regularOpeningHours", {})

    # 开放时间转为标准 JSONB
    opening_hours_json: Optional[Dict[str, Any]] = None
    if opening:
        opening_hours_json = {
            "periods": opening.get("periods", []),
            "weekday_text": opening.get("weekdayDescriptions", []),
        }

    # 主分类
    primary_type = raw.get("primaryType", "")
    poi_category = _map_google_type_to_category(primary_type)

    data: Dict[str, Any] = {
        # base 字段
        "name_zh": display_name.get("text", ""),
        "city_code": city_code,
        "lat": loc.get("latitude"),
        "lng": loc.get("longitude"),
        "address_en": raw.get("formattedAddress"),
        "google_place_id": raw.get("id", "").removeprefix("places/"),
        # poi 子表字段
        "google_rating": raw.get("rating"),
        "google_review_count": raw.get("userRatingCount"),
        "opening_hours_json": opening_hours_json,
        "poi_category": poi_category,
    }
    return {k: v for k, v in data.items() if v is not None}


def _map_google_type_to_category(primary_type: str) -> str:
    """Google primaryType → 内部 poi_category"""
    mapping = {
        "shinto_shrine": "shrine",
        "buddhist_temple": "temple",
        "hindu_temple": "temple",
        "place_of_worship": "temple",
        "national_park": "park",
        "park": "park",
        "amusement_park": "theme_park",
        "theme_park": "theme_park",
        "museum": "museum",
        "art_gallery": "museum",
        "aquarium": "museum",
        "zoo": "museum",
        "castle": "castle",
        "historical_landmark": "landmark",
        "tourist_attraction": "landmark",
        "shopping_mall": "shopping",
        "market": "shopping",
        "department_store": "shopping",
        "onsen": "onsen",
        "spa": "onsen",
    }
    return mapping.get(primary_type, "other")


# ── 完整采集流程 ───────────────────────────────────────────────────────────────

async def sync_poi_to_db(
    session: AsyncSession,
    api_key: str,
    place_id: str,
    city_code: str,
    data_tier: str = "A",
) -> str:
    """
    完整的 POI 采集流程：
      1. 调用 Google Places API
      2. 用 record_snapshot 写原始快照
      3. 用 upsert_entity 幂等写入 entity_base + pois

    Args:
        session:   AsyncSession
        api_key:   Google Places API Key
        place_id:  Google Place ID
        city_code: 所属城市代码
        data_tier: 数据级别（S/A/B）

    Returns:
        entity_id（UUID 字符串）
    """
    # 1. 拉取数据
    raw = await fetch_place_details(api_key, place_id)

    # 2. 记录快照
    clean_id = place_id.removeprefix("places/")
    await record_snapshot(
        session=session,
        source_name="google_places",
        object_type="poi",
        object_id=clean_id,
        raw_payload=raw,
        expires_in_days=30,
        http_status=200,
        request_url=_PLACE_DETAILS_URL.format(place_id=clean_id),
    )

    # 3. 转换 + upsert
    data = _parse_place_to_entity_data(raw, city_code=city_code)
    data["data_tier"] = data_tier

    entity = await upsert_entity(
        session=session,
        entity_type="poi",
        data=data,
        google_place_id=clean_id,
    )

    return str(entity.entity_id)


async def sync_hotel_to_db(
    session: AsyncSession,
    api_key: str,
    place_id: str,
    city_code: str,
    extra_data: Optional[Dict[str, Any]] = None,
    data_tier: str = "A",
) -> str:
    """
    酒店采集流程（Google Places + 可追加 Booking.com 字段）。

    Args:
        extra_data: 可传入 booking_hotel_id / star_rating 等补充字段
    """
    raw = await fetch_place_details(api_key, place_id)

    clean_id = place_id.removeprefix("places/")
    await record_snapshot(
        session=session,
        source_name="google_places",
        object_type="hotel",
        object_id=clean_id,
        raw_payload=raw,
        expires_in_days=30,
        http_status=200,
    )

    data = _parse_place_to_entity_data(raw, city_code=city_code, entity_type="hotel")
    data["data_tier"] = data_tier
    if extra_data:
        data.update(extra_data)

    entity = await upsert_entity(
        session=session,
        entity_type="hotel",
        data=data,
        google_place_id=clean_id,
    )
    return str(entity.entity_id)
