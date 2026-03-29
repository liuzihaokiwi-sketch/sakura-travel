"""
携程酒店爬虫

覆盖：中国城市酒店数据
方式：解析携程酒店搜索结果页（HTML / API）
数据：酒店名、评分、价格区间、坐标、酒店类型

反爬策略：
  - User-Agent 轮换
  - 请求间隔 3-5s
  - 遇 Captcha → 记录失败，不重试
  - 不登录，只抓公开搜索结果

用法:
    from app.domains.catalog.crawlers.ctrip_scraper import fetch_ctrip_hotels
    results = await fetch_ctrip_hotels("guangzhou", limit=20)
"""
from __future__ import annotations

import asyncio
import json
import logging
import random
import re
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# 城市 → 携程城市 ID 映射
# ─────────────────────────────────────────────────────────────────────────────
CTRIP_CITY_ID: Dict[str, int] = {
    # 广府圈
    "guangzhou": 32,
    "shenzhen": 26,
    "hongkong": 38,
    "macau": 39,
    "zhuhai": 33,
    "foshan": 256,
    "shunde": 256,  # 归入佛山
    # 华东圈
    "shanghai": 2,
    "hangzhou": 14,
    "suzhou": 11,
    "nanjing": 9,
    "wuxi": 62,
    "wuzhen": 1442,
    "huangshan": 19,
    # 潮汕
    "chaozhou": 259,
    "shantou": 260,
    # 北疆
    "urumqi": 131,
    # 其他
    "meizhou": 361,
    "zhaoqing": 285,
    "shaoguan": 284,
    "qingyuan": 283,
    "jiangmen": 257,
}

# User-Agent 池
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


def _random_ua() -> str:
    return random.choice(_USER_AGENTS)


# ─────────────────────────────────────────────────────────────────────────────
# 携程 API 搜索（移动端 API，比网页更稳定）
# ─────────────────────────────────────────────────────────────────────────────

_CTRIP_HOTEL_LIST_URL = "https://m.ctrip.com/restapi/h5api/searchapp/hotel"
_CTRIP_SEARCH_URL = "https://m.ctrip.com/webapp/hotel/citylist"

# 携程移动端酒店搜索 API（公开，无需登录）
_CTRIP_API_URL = "https://m.ctrip.com/restapi/h5api/searchapp/hotel/city/list"


async def _fetch_ctrip_page(
    city_id: int,
    city_name_zh: str,
    page: int = 1,
    page_size: int = 25,
) -> List[Dict[str, Any]]:
    """
    调用携程移动端 API 获取酒店列表

    携程移动端 H5 API 比桌面版更容易抓取，返回 JSON。
    """
    # 携程 H5 搜索 API
    url = "https://m.ctrip.com/restapi/h5api/searchapp/hotel/city/list"

    headers = {
        "User-Agent": _random_ua(),
        "Accept": "application/json",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": f"https://m.ctrip.com/webapp/hotel/citylist/{city_id}",
        "Content-Type": "application/json",
    }

    payload = {
        "cityId": city_id,
        "cityName": city_name_zh,
        "pageIndex": page,
        "pageSize": page_size,
        "sortType": 2,  # 好评优先
        "filter": {},
    }

    try:
        async with httpx.AsyncClient(
            timeout=20.0,
            follow_redirects=True,
        ) as client:
            resp = await client.post(url, json=payload, headers=headers)

            if resp.status_code == 403:
                logger.warning("[ctrip] 403 Forbidden for city %d — possible captcha", city_id)
                return []

            if resp.status_code != 200:
                logger.warning("[ctrip] HTTP %d for city %d", resp.status_code, city_id)
                return []

            body = resp.json()

            # 携程 API 返回结构
            hotel_list = body.get("Response", {}).get("hotelList", [])
            if not hotel_list:
                # 尝试其他可能的路径
                hotel_list = body.get("hotelList", [])

            return hotel_list

    except httpx.TimeoutException:
        logger.warning("[ctrip] Timeout for city %d page %d", city_id, page)
        return []
    except Exception as e:
        logger.warning("[ctrip] Request failed for city %d: %s", city_id, e)
        return []


async def _fetch_ctrip_html(
    city_id: int,
    city_code: str,
) -> List[Dict[str, Any]]:
    """
    备选方案：解析携程搜索结果 HTML

    当 API 方式失败时（403/captcha），尝试直接抓取 HTML 页面。
    """
    url = f"https://hotels.ctrip.com/hotel/{city_code}"

    headers = {
        "User-Agent": _random_ua(),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }

    try:
        async with httpx.AsyncClient(
            timeout=20.0,
            follow_redirects=True,
        ) as client:
            resp = await client.get(url, headers=headers)

            if resp.status_code != 200:
                logger.warning("[ctrip_html] HTTP %d for %s", resp.status_code, city_code)
                return []

            html = resp.text

            # 携程在 HTML 中嵌入 JSON 数据
            # 搜索 window.IBU_HOTEL 或 hotelPositionJSON 变量
            results = []

            # 方法1: 提取 script 中的 JSON 数据
            json_match = re.search(
                r'window\.IBU_HOTEL\s*=\s*(\{.*?\});?\s*</script>',
                html, re.DOTALL
            )
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    htl_list = (data.get("initData", {})
                                .get("htlsData", {})
                                .get("inboundList", []))
                    for item in htl_list:
                        hotel = item.get("hotelBasicInfo", {})
                        if hotel.get("hotelName"):
                            results.append({
                                "hotelName": hotel.get("hotelName", ""),
                                "hotelNameEn": hotel.get("hotelNameEn", ""),
                                "price": hotel.get("price"),
                                "score": item.get("commentInfo", {}).get("commentScore"),
                                "lat": hotel.get("lat"),
                                "lon": hotel.get("lon"),
                                "star": hotel.get("star"),
                                "address": hotel.get("hotelAddress", ""),
                                "zoneName": hotel.get("zoneName", ""),
                            })
                    return results
                except (json.JSONDecodeError, KeyError) as e:
                    logger.debug("[ctrip_html] JSON parse failed: %s", e)

            # 方法2: 提取 hotelPositionJSON
            pos_match = re.search(
                r'hotelPositionJSON\s*=\s*(\[.*?\]);',
                html, re.DOTALL
            )
            if pos_match:
                try:
                    positions = json.loads(pos_match.group(1))
                    for p in positions:
                        results.append({
                            "hotelName": p.get("name", ""),
                            "lat": p.get("lat"),
                            "lon": p.get("lng"),
                            "price": p.get("amount"),
                            "score": p.get("score"),
                        })
                    return results
                except (json.JSONDecodeError, KeyError):
                    pass

            logger.info("[ctrip_html] Could not extract hotel data from HTML for %s", city_code)
            return results

    except Exception as e:
        logger.warning("[ctrip_html] Request failed for %s: %s", city_code, e)
        return []


def _parse_ctrip_hotel(raw: Dict[str, Any], city_code: str) -> Dict[str, Any]:
    """将携程原始数据转为 upsert_entity 兼容格式"""
    # 携程 API 格式
    name_zh = (raw.get("hotelName") or raw.get("name", "")).strip()
    name_en = (raw.get("hotelNameEn") or raw.get("englishName", "")).strip()

    # 坐标
    lat = raw.get("lat")
    lon = raw.get("lon") or raw.get("lng")

    # 评分：携程评分通常 1-5 或 满分 5.0
    score_raw = raw.get("score") or raw.get("commentScore")
    google_rating = None
    if score_raw:
        try:
            google_rating = min(float(score_raw), 5.0)
        except (TypeError, ValueError):
            pass

    # 价格
    price_raw = raw.get("price") or raw.get("minPrice")
    price_jpy = None
    if price_raw:
        try:
            # CNY → JPY（使用环境变量或默认 21）
            import os
            rate = float(os.environ.get("CNY_TO_JPY_RATE", "21"))
            price_jpy = int(float(price_raw) * rate)
        except (TypeError, ValueError):
            pass

    # 价格档次
    price_tier = "mid"
    if price_raw:
        try:
            p = float(price_raw)
            if p < 200:
                price_tier = "budget"
            elif p < 600:
                price_tier = "mid"
            elif p < 1500:
                price_tier = "premium"
            else:
                price_tier = "luxury"
        except (TypeError, ValueError):
            pass

    # 星级
    star_raw = raw.get("star") or raw.get("starLevel")
    star_rating = None
    if star_raw:
        try:
            star_rating = min(float(star_raw), 5.0)
        except (TypeError, ValueError):
            pass

    return {
        "name_zh": name_zh,
        "name_en": name_en,
        "name_ja": "",
        "city_code": city_code,
        "lat": lat,
        "lng": lon,
        "data_tier": "A",
        "source": "ctrip",
        "hotel_type": "city_hotel",
        "star_rating": star_rating,
        "google_rating": google_rating,
        "price_tier": price_tier,
        "typical_price_min_jpy": price_jpy,
        "district": raw.get("zoneName", "") or raw.get("address", ""),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 公开 API
# ─────────────────────────────────────────────────────────────────────────────

# 中文名映射（用于 API 调用）
from app.domains.catalog.ai_generator import CITY_MAP

async def fetch_ctrip_hotels(
    city_code: str,
    limit: int = 30,
) -> List[Dict[str, Any]]:
    """
    从携程抓取酒店数据

    Args:
        city_code: 城市代码（须在 CTRIP_CITY_ID 中）
        limit: 最大数量

    Returns:
        酒店数据列表（兼容 upsert_entity 格式）
    """
    city_id = CTRIP_CITY_ID.get(city_code)
    if not city_id:
        logger.info("[ctrip] No city_id mapping for %s, skipping", city_code)
        return []

    city_info = CITY_MAP.get(city_code)
    city_name_zh = city_info[0] if city_info else city_code

    all_hotels: List[Dict[str, Any]] = []
    max_pages = min(3, (limit + 24) // 25)  # 每页 25 条，最多 3 页

    # 策略1: 尝试 API
    for page in range(1, max_pages + 1):
        if len(all_hotels) >= limit:
            break

        raw_list = await _fetch_ctrip_page(city_id, city_name_zh, page=page)

        if not raw_list and page == 1:
            # API 失败，尝试 HTML 方案
            logger.info("[ctrip] API failed for %s, trying HTML scraping", city_code)
            raw_list = await _fetch_ctrip_html(city_id, city_code)
            if raw_list:
                for raw in raw_list[:limit]:
                    parsed = _parse_ctrip_hotel(raw, city_code)
                    if parsed["name_zh"]:
                        all_hotels.append(parsed)
                break  # HTML 方案只拿一页

        for raw in raw_list:
            parsed = _parse_ctrip_hotel(raw, city_code)
            if parsed["name_zh"]:
                all_hotels.append(parsed)

        # 请求间隔 3-5 秒
        if page < max_pages:
            await asyncio.sleep(random.uniform(3.0, 5.0))

    logger.info("[ctrip] %s hotels: %d", city_code, len(all_hotels))
    return all_hotels[:limit]
