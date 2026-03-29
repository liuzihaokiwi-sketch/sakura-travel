"""
大众点评爬虫

覆盖：中国城市的餐厅和特色店铺
方式：解析大众点评搜索结果页 HTML / 移动端 API
数据：店名、评分、价格、菜系/品类、坐标

反爬策略：
  - User-Agent 轮换
  - 请求间隔 3-5s
  - 遇 Captcha/验证页 → 记录失败，不重试
  - 不登录，只抓公开搜索结果
  - 字体解密：大众点评用 CSS 字体加密数字/评分，需特殊处理

用法:
    from app.domains.catalog.crawlers.dianping_scraper import (
        fetch_dianping_restaurants,
        fetch_dianping_shops,
    )
    results = await fetch_dianping_restaurants("guangzhou", limit=20)
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
# 城市 → 大众点评城市 ID 映射
# ─────────────────────────────────────────────────────────────────────────────
DIANPING_CITY_ID: Dict[str, int] = {
    # 广府
    "guangzhou": 4,
    "shenzhen": 7,
    "hongkong": 1,   # 大众点评也覆盖香港
    "macau": 955,
    "zhuhai": 152,
    "foshan": 91,
    "shunde": 91,
    # 华东
    "shanghai": 1,
    "hangzhou": 3,
    "suzhou": 6,
    "nanjing": 5,
    "wuxi": 12,
    "huangshan": 229,
    # 潮汕
    "chaozhou": 211,
    "shantou": 212,
    # 北疆
    "urumqi": 93,
    # 其他
    "meizhou": 388,
    "zhaoqing": 321,
    "jiangmen": 133,
}

# 大众点评分类 ID
_FOOD_CATEGORY = 10  # 美食
_SHOP_CATEGORY = 50  # 购物
_LIFE_CATEGORY = 30  # 生活服务

# 中国特色店铺搜索关键词
_SPECIALTY_KEYWORDS_CN = [
    "手工艺品",
    "文创",
    "老字号",
    "非遗",
    "特产",
    "本地手信",
    "传统手作",
]

# User-Agent 池
_USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.0.0 Mobile/15E148 Safari/604.1",
]


def _random_ua() -> str:
    return random.choice(_USER_AGENTS)


# ─────────────────────────────────────────────────────────────────────────────
# 大众点评移动端搜索
# ─────────────────────────────────────────────────────────────────────────────

async def _search_dianping(
    city_id: int,
    keyword: str = "",
    category_id: int = _FOOD_CATEGORY,
    page: int = 1,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    大众点评移动端搜索 API

    大众点评的移动端网页（m.dianping.com）比桌面版反爬弱。
    """
    if keyword:
        url = f"https://m.dianping.com/search/keyword/{city_id}/0_{keyword}"
    else:
        url = f"https://m.dianping.com/citylist/category/{city_id}/{category_id}"

    headers = {
        "User-Agent": _random_ua(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept-Encoding": "gzip, deflate",
    }

    try:
        async with httpx.AsyncClient(
            timeout=20.0,
            follow_redirects=True,
        ) as client:
            resp = await client.get(url, headers=headers)

            if resp.status_code == 403:
                logger.warning("[dianping] 403 for city %d keyword '%s' — captcha", city_id, keyword)
                return []

            if resp.status_code != 200:
                logger.warning("[dianping] HTTP %d for city %d", resp.status_code, city_id)
                return []

            html = resp.text

            # 提取嵌入的 JSON 数据
            return _parse_dianping_html(html, city_id)

    except httpx.TimeoutException:
        logger.warning("[dianping] Timeout for city %d keyword '%s'", city_id, keyword)
        return []
    except Exception as e:
        logger.warning("[dianping] Request failed for city %d: %s", city_id, e)
        return []


async def _search_dianping_api(
    city_id: int,
    keyword: str = "",
    category_id: int = _FOOD_CATEGORY,
    start: int = 0,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    大众点评搜索 API（备选方案）

    尝试调用大众点评的内部 Ajax 搜索接口。
    """
    url = "https://m.dianping.com/search/ajax/list"

    headers = {
        "User-Agent": _random_ua(),
        "Accept": "application/json",
        "Referer": f"https://m.dianping.com/search/keyword/{city_id}/0_{keyword}",
        "X-Requested-With": "XMLHttpRequest",
    }

    params = {
        "cityId": city_id,
        "keyword": keyword,
        "categoryId": category_id,
        "start": start,
        "limit": limit,
        "sortId": 0,  # 默认排序
    }

    try:
        async with httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
        ) as client:
            resp = await client.get(url, params=params, headers=headers)

            if resp.status_code != 200:
                return []

            body = resp.json()
            return body.get("shopList", body.get("list", []))

    except Exception:
        return []


def _parse_dianping_html(html: str, city_id: int) -> List[Dict[str, Any]]:
    """
    从大众点评 HTML 中提取店铺数据

    大众点评在页面中嵌入 JSON 数据（window.__INITIAL_STATE__ 或类似变量）
    """
    results = []

    # 方法1: 提取 __INITIAL_STATE__
    state_match = re.search(
        r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\})\s*;?\s*(?:</script>|window\.)',
        html, re.DOTALL
    )
    if state_match:
        try:
            state = json.loads(state_match.group(1))
            # 搜索结果通常在 searchResult.listData 或 shopList
            shop_list = (
                state.get("searchResult", {}).get("listData", [])
                or state.get("shopList", {}).get("list", [])
                or state.get("list", [])
            )
            for shop in shop_list:
                item = _extract_shop_from_state(shop)
                if item:
                    results.append(item)
            return results
        except (json.JSONDecodeError, KeyError) as e:
            logger.debug("[dianping] __INITIAL_STATE__ parse failed: %s", e)

    # 方法2: 提取 shopAllListJson 或 searchShopData
    for pattern in [
        r'shopAllListJson\s*=\s*(\[.*?\]);',
        r'searchShopData\s*=\s*(\[.*?\]);',
        r'"shopList"\s*:\s*(\[.*?\])',
    ]:
        match = re.search(pattern, html, re.DOTALL)
        if match:
            try:
                items = json.loads(match.group(1))
                for item in items:
                    parsed = _extract_shop_from_state(item)
                    if parsed:
                        results.append(parsed)
                if results:
                    return results
            except (json.JSONDecodeError, KeyError):
                continue

    logger.debug("[dianping] Could not extract data from HTML (city=%d)", city_id)
    return results


def _extract_shop_from_state(shop: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """从大众点评 JSON state 中提取单个店铺数据"""
    name = (shop.get("shopName") or shop.get("name") or
            shop.get("title") or "").strip()
    if not name:
        return None

    # 评分：大众点评通常 0-5 分制（含 CSS 加密的数字）
    score_raw = shop.get("score") or shop.get("avgScore") or shop.get("starScore")
    score = None
    if score_raw:
        try:
            score = min(float(score_raw), 5.0)
        except (TypeError, ValueError):
            pass

    # 价格：人均消费（元）
    price_raw = shop.get("avgPrice") or shop.get("meanPrice")
    avg_price_cny = None
    if price_raw:
        try:
            avg_price_cny = int(float(str(price_raw).replace("¥", "").replace("元", "").strip()))
        except (TypeError, ValueError):
            pass

    # 坐标
    lat = shop.get("latitude") or shop.get("lat")
    lng = shop.get("longitude") or shop.get("lng") or shop.get("lon")

    # 分类/菜系
    category = (shop.get("categoryName") or shop.get("category") or
                shop.get("dishTag") or "")

    # 地址
    address = shop.get("address") or shop.get("shopAddress") or ""

    return {
        "name": name,
        "score": score,
        "avg_price_cny": avg_price_cny,
        "lat": lat,
        "lng": lng,
        "category": category,
        "address": address,
        "district": shop.get("regionName") or shop.get("district") or "",
        "review_count": shop.get("reviewCount") or shop.get("commentCount"),
        "dianping_id": shop.get("shopId") or shop.get("id"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 数据格式转换
# ─────────────────────────────────────────────────────────────────────────────

def _to_restaurant(raw: Dict[str, Any], city_code: str) -> Dict[str, Any]:
    """将大众点评原始数据转为餐厅格式（兼容 upsert_entity）"""
    import os
    rate = float(os.environ.get("CNY_TO_JPY_RATE", "21"))

    avg_price_cny = raw.get("avg_price_cny")
    lunch_jpy = int(avg_price_cny * rate) if avg_price_cny else None
    dinner_jpy = int(avg_price_cny * rate * 1.3) if avg_price_cny else None  # 晚餐通常贵 30%

    # 大众点评评分 → tabelog_score 字段（统一评分字段）
    score = raw.get("score")
    tabelog_score = None
    if score:
        # 大众点评 0-5 → 映射到 Tabelog 3.0-5.0 区间
        tabelog_score = max(3.0, min(5.0, float(score) * 0.8 + 1.0))

    # 菜系推断
    category = raw.get("category", "")
    cuisine_type = _guess_cn_cuisine(category)

    return {
        "name_zh": raw.get("name", ""),
        "name_en": "",
        "name_ja": "",
        "city_code": city_code,
        "lat": raw.get("lat"),
        "lng": raw.get("lng"),
        "data_tier": "A",
        "source": "dianping",
        "cuisine_type": cuisine_type,
        "tabelog_score": tabelog_score,
        "budget_lunch_jpy": lunch_jpy,
        "budget_dinner_jpy": dinner_jpy,
        "price_range_min_jpy": lunch_jpy,
        "price_range_max_jpy": dinner_jpy,
        "district": raw.get("district", ""),
    }


def _to_specialty_shop(raw: Dict[str, Any], city_code: str) -> Dict[str, Any]:
    """将大众点评原始数据转为特色店铺 POI 格式"""
    return {
        "name_zh": raw.get("name", ""),
        "name_en": "",
        "name_ja": "",
        "city_code": city_code,
        "lat": raw.get("lat"),
        "lng": raw.get("lng"),
        "data_tier": "A",
        "source": "dianping",
        "poi_category": "specialty_shop",
        "typical_duration_min": 30,
        "admission_free": True,
        "district": raw.get("district", ""),
    }


def _guess_cn_cuisine(category: str) -> str:
    """从大众点评分类推断菜系"""
    mapping = {
        "粤菜": "cantonese", "广东菜": "cantonese", "广府菜": "cantonese",
        "早茶": "dimsum", "茶餐厅": "dimsum",
        "潮汕": "teochew", "潮州菜": "teochew",
        "客家": "hakka",
        "火锅": "hotpot",
        "烧烤": "bbq", "烤肉": "bbq",
        "海鲜": "seafood",
        "面": "noodles", "粉": "noodles", "米线": "noodles",
        "小吃": "snack", "快餐": "snack",
        "西餐": "western", "意大利": "italian", "法国": "french",
        "日料": "japanese", "日本料理": "japanese",
        "韩国": "korean", "韩料": "korean",
        "咖啡": "cafe", "甜品": "cafe", "面包": "bakery",
        "川菜": "sichuan", "湘菜": "hunan",
        "东北": "dongbei", "新疆": "xinjiang",
    }
    for keyword, cuisine in mapping.items():
        if keyword in category:
            return cuisine
    return "local_cuisine"


# ─────────────────────────────────────────────────────────────────────────────
# 公开 API
# ─────────────────────────────────────────────────────────────────────────────

from app.domains.catalog.ai_generator import CITY_MAP

async def fetch_dianping_restaurants(
    city_code: str,
    limit: int = 30,
) -> List[Dict[str, Any]]:
    """
    从大众点评抓取餐厅数据

    Args:
        city_code: 城市代码
        limit: 最大数量

    Returns:
        餐厅数据列表（兼容 upsert_entity 格式）
    """
    city_id = DIANPING_CITY_ID.get(city_code)
    if not city_id:
        logger.info("[dianping] No city_id mapping for %s, skipping", city_code)
        return []

    # 先尝试 API，再 fallback 到 HTML
    raw_list = await _search_dianping_api(city_id, category_id=_FOOD_CATEGORY, limit=limit)

    if not raw_list:
        raw_list = await _search_dianping(city_id, category_id=_FOOD_CATEGORY)

    results = []
    for raw in raw_list:
        parsed = _to_restaurant(raw, city_code)
        if parsed["name_zh"]:
            results.append(parsed)

    logger.info("[dianping] %s restaurants: %d", city_code, len(results))
    return results[:limit]


async def fetch_dianping_shops(
    city_code: str,
    limit: int = 15,
    keywords: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    从大众点评抓取特色店铺（手工艺、文创、老字号等）

    Args:
        city_code: 城市代码
        limit: 最大数量
        keywords: 搜索关键词，默认使用中国特色店铺关键词

    Returns:
        POI 数据列表（poi_category=specialty_shop）
    """
    city_id = DIANPING_CITY_ID.get(city_code)
    if not city_id:
        logger.info("[dianping] No city_id mapping for %s, skipping", city_code)
        return []

    if keywords is None:
        keywords = _SPECIALTY_KEYWORDS_CN

    all_results: List[Dict[str, Any]] = []
    seen_names: set[str] = set()

    for kw in keywords:
        if len(all_results) >= limit:
            break

        # 先 API，再 HTML
        raw_list = await _search_dianping_api(city_id, keyword=kw, limit=10)
        if not raw_list:
            raw_list = await _search_dianping(city_id, keyword=kw)

        for raw in raw_list:
            name = raw.get("name", "")
            if name and name not in seen_names:
                seen_names.add(name)
                parsed = _to_specialty_shop(raw, city_code)
                if parsed["name_zh"]:
                    all_results.append(parsed)

        await asyncio.sleep(random.uniform(3.0, 5.0))

    logger.info("[dianping] %s specialty shops: %d", city_code, len(all_results))
    return all_results[:limit]
