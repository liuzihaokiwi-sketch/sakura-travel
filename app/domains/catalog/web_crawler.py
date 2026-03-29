from __future__ import annotations

"""
真实网络爬虫模块（网络畅通时使用）
数据源：
  1. OpenStreetMap Overpass API — 景点坐标/基础信息（完全免费）
  2. Tabelog HTML 爬虫          — 餐厅评分/价格（免费，解析HTML）
  3. Wikipedia API              — 景点描述/图片（完全免费）

使用前请确认网络可以访问这些域名：
  - overpass-api.de 或 overpass.kumi.systems
  - tabelog.com
  - ja.wikipedia.org
"""

import asyncio
import random
import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

# ── 请求头（模拟浏览器，防止被拒） ──────────────────────────────────────────────
_HEADERS_JA = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja-JP,ja;q=0.9,zh-CN;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

_OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

# 城市边界框 (south, west, north, east)
# 格式：中心点 ± 约 0.1 度（~10km），小城市用更大范围
CITY_BBOX = {
    # 关东
    "tokyo":      (35.53, 139.45, 35.82, 139.92),
    "yokohama":   (35.38, 139.57, 35.52, 139.72),
    "kamakura":   (35.28, 139.50, 35.34, 139.58),
    "hakone":     (35.15, 138.95, 35.30, 139.10),
    "nikko":      (36.70, 139.55, 36.80, 139.65),
    "kawaguchiko":(35.46, 138.69, 35.57, 138.83),
    # 関西
    "osaka":      (34.55, 135.40, 34.75, 135.65),
    "kyoto":      (34.90, 135.65, 35.10, 135.85),
    "nara":       (34.60, 135.75, 34.75, 135.90),
    "kobe":       (34.62, 135.08, 34.76, 135.30),
    # 中部・北陸
    "nagoya":     (35.10, 136.83, 35.25, 137.05),
    "kanazawa":   (36.53, 136.60, 36.60, 136.68),
    # 中国・四国
    "hiroshima":  (34.32, 132.40, 34.45, 132.52),
    # 九州
    "fukuoka":    (33.52, 130.33, 33.66, 130.48),
    "nagasaki":   (32.71, 129.84, 32.80, 129.92),
    "kumamoto":   (32.73, 130.64, 32.84, 130.78),
    "beppu":      (33.25, 131.44, 33.35, 131.52),
    # 北海道
    "sapporo":    (42.98, 141.25, 43.18, 141.45),
    "otaru":      (43.14, 140.93, 43.24, 141.07),
    "hakodate":   (41.73, 140.69, 41.82, 140.78),
    "asahikawa":  (43.73, 142.31, 43.82, 142.42),
    "furano":     (43.27, 142.32, 43.42, 142.47),
    "biei":       (43.54, 142.41, 43.63, 142.54),
    "noboribetsu":(42.38, 141.05, 42.46, 141.17),
    "niseko":     (42.82, 140.61, 42.91, 140.74),
    "abashiri":   (43.95, 144.22, 44.06, 144.35),
    "kushiro":    (42.93, 144.31, 43.04, 144.45),
    # 沖縄
    "naha":       (26.18, 127.65, 26.25, 127.73),
    "ishigaki":   (24.29, 124.08, 24.41, 124.23),
    # 東北
    "sendai":     (38.21, 140.82, 38.34, 140.96),
}

# OSM tourism 标签 → poi_category 映射
OSM_TOURISM_MAP = {
    "attraction":    "landmark",
    "museum":        "museum",
    "gallery":       "museum",
    "artwork":       "landmark",
    "theme_park":    "theme_park",
    "viewpoint":     "landmark",
    "zoo":           "park",
    "aquarium":      "museum",
}
OSM_HISTORIC_MAP = {
    "castle":        "castle",
    "temple":        "temple",
    "shrine":        "shrine",
    "monument":      "landmark",
    "ruins":         "landmark",
}
OSM_LEISURE_MAP = {
    "park":          "park",
    "garden":        "garden",
    "nature_reserve": "park",
}
OSM_AMENITY_MAP = {
    "place_of_worship": "shrine",  # 细分由 religion/denomination 决定
}


# ─────────────────────────────────────────────────────────────────────────────
# OSM Overpass API
# ─────────────────────────────────────────────────────────────────────────────

async def _overpass_query(query: str, timeout: int = 30) -> Dict[str, Any]:
    """向 Overpass API 发送查询，自动尝试多个节点"""
    for endpoint in _OVERPASS_ENDPOINTS:
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(endpoint, data={"data": query})
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            continue
    return {"elements": []}


async def fetch_osm_pois(
    city_code: str,
    category: str = "attraction",
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    从 OpenStreetMap 获取指定城市的景点数据。

    Args:
        city_code: 城市代码
        category:  OSM 类别 (attraction/museum/shrine/temple/castle/park)
        limit:     最大数量

    Returns:
        原始 POI 数据列表
    """
    bbox = CITY_BBOX.get(city_code)
    if not bbox:
        return []

    s, w, n, e = bbox
    bbox_str = f"{s},{w},{n},{e}"

    # 构建 Overpass QL 查询
    if category in ("shrine", "temple"):
        # 神社寺庙通过 historic 标签
        query = f"""
[out:json][timeout:25];
(
  node[historic={category}]({bbox_str});
  way[historic={category}]({bbox_str});
);
out center {limit};
"""
    elif category in ("museum", "attraction", "theme_park"):
        query = f"""
[out:json][timeout:25];
(
  node[tourism={category}]({bbox_str});
  way[tourism={category}]({bbox_str});
);
out center {limit};
"""
    elif category == "park":
        query = f"""
[out:json][timeout:25];
(
  node[leisure=park][name]({bbox_str});
  way[leisure=park][name]({bbox_str});
  relation[leisure=park][name]({bbox_str});
);
out center {limit};
"""
    elif category == "castle":
        query = f"""
[out:json][timeout:25];
(
  node[historic=castle]({bbox_str});
  way[historic=castle]({bbox_str});
);
out center {limit};
"""
    else:
        query = f"""
[out:json][timeout:25];
(
  node[tourism]({bbox_str});
  way[tourism]({bbox_str});
);
out center {limit};
"""

    data = await _overpass_query(query)
    elements = data.get("elements", [])

    results = []
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name") or tags.get("name:zh") or tags.get("name:en")
        if not name:
            continue

        # 获取坐标（way 用 center）
        if el.get("type") == "way":
            center = el.get("center", {})
            lat = center.get("lat")
            lng = center.get("lon")
        else:
            lat = el.get("lat")
            lng = el.get("lon")

        if not lat or not lng:
            continue

        # 确定 poi_category
        poi_cat = _resolve_poi_category(tags, category)

        results.append({
            "name_ja": tags.get("name", name),
            "name_zh": tags.get("name:zh") or tags.get("name:zh-Hans") or "",
            "name_en": tags.get("name:en", ""),
            "city_code": city_code,
            "poi_category": poi_cat,
            "lat": lat,
            "lng": lng,
            "address_ja": _build_address(tags),
            "osm_id": str(el.get("id", "")),
            "wikipedia": tags.get("wikipedia", ""),
            "wikidata": tags.get("wikidata", ""),
            "opening_hours": tags.get("opening_hours", ""),
            "entrance_fee_jpy": _parse_fee(tags.get("fee", "")),
            "source": "osm",
        })

    return results


def _resolve_poi_category(tags: Dict, fallback: str) -> str:
    """根据 OSM 标签推断 poi_category"""
    if tags.get("historic") in OSM_HISTORIC_MAP:
        return OSM_HISTORIC_MAP[tags["historic"]]
    if tags.get("tourism") in OSM_TOURISM_MAP:
        return OSM_TOURISM_MAP[tags["tourism"]]
    if tags.get("leisure") in OSM_LEISURE_MAP:
        return OSM_LEISURE_MAP[tags["leisure"]]
    # 神社/寺庙细分
    if tags.get("amenity") == "place_of_worship":
        religion = tags.get("religion", "")
        denomination = tags.get("denomination", "")
        if religion == "shinto" or denomination == "shinto":
            return "shrine"
        return "temple"
    return fallback


def _build_address(tags: Dict) -> str:
    """从 OSM 标签组合地址"""
    parts = []
    for key in ["addr:province", "addr:city", "addr:suburb", "addr:street", "addr:housenumber"]:
        v = tags.get(key)
        if v:
            parts.append(v)
    return "".join(parts)


def _parse_fee(fee_str: str) -> Optional[int]:
    """解析门票费用"""
    if not fee_str or fee_str.lower() in ("no", "free", "0"):
        return 0
    match = re.search(r'(\d+)', fee_str.replace(",", ""))
    return int(match.group(1)) if match else None


# ─────────────────────────────────────────────────────────────────────────────
# Tabelog 爬虫
# ─────────────────────────────────────────────────────────────────────────────

# 城市代码 → Tabelog URL 路径前缀
TABELOG_CITY_PREFIX = {
    # 関東
    "tokyo":       "tokyo",
    "yokohama":    "kanagawa/A1401",
    "kamakura":    "kanagawa/A1407",
    "hakone":      "kanagawa/A1410",
    "nikko":       "tochigi/A0901",
    "kawaguchiko": "yamanashi/A1901",
    # 関西
    "osaka":       "osaka",
    "kyoto":       "kyoto",
    "nara":        "nara",
    "kobe":        "hyogo/A2801",
    # 中部・北陸
    "nagoya":      "aichi/A2301",
    "kanazawa":    "ishikawa/A1701",
    # 中国
    "hiroshima":   "hiroshima/A3401",
    # 九州
    "fukuoka":     "fukuoka/A4001",
    "nagasaki":    "nagasaki/A4201",
    "kumamoto":    "kumamoto/A4301",
    "beppu":       "oita/A4402",
    # 北海道
    "sapporo":     "hokkaido/A0101",
    "otaru":       "hokkaido/A0103",
    "hakodate":    "hokkaido/A0105",
    "asahikawa":   "hokkaido/A0102",
    # 沖縄
    "naha":        "okinawa/A4701",
    # 東北
    "sendai":      "miyagi/A0401",
}

# 菜系 → Tabelog 分类代码
TABELOG_CUISINE_CODE = {
    "sushi":    "RC020101",
    "ramen":    "RC040201",
    "kaiseki":  "RC010101",
    "tempura":  "RC010301",
    "yakitori": "RC010401",
    "wagyu":    "RC010601",
    "izakaya":  "RC010101",
    "udon":     "RC040101",
    "soba":     "RC040102",
    "seafood":  "RC020201",
}


async def fetch_tabelog_restaurants(
    city_code: str,
    cuisine: str = "",
    page: int = 1,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    爬取 Tabelog 餐厅列表页，提取餐厅基础信息。

    Args:
        city_code: 城市代码
        cuisine:   菜系代码（可选）
        page:      翻页（1-起始）
        limit:     最大条数

    Returns:
        餐厅数据列表
    """
    city_prefix = TABELOG_CITY_PREFIX.get(city_code, city_code)
    cuisine_code = TABELOG_CUISINE_CODE.get(cuisine, "")

    if cuisine_code:
        url = f"https://tabelog.com/{city_prefix}/rstLst/{cuisine_code}/{page}/"
    else:
        url = f"https://tabelog.com/{city_prefix}/rstLst/{page}/"

    try:
        async with httpx.AsyncClient(
            timeout=20.0,
            headers=_HEADERS_JA,
            follow_redirects=True,
        ) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return []
            html = resp.text
    except Exception:
        return []

    return _parse_tabelog_list(html, city_code, limit)


def _parse_tabelog_list(html: str, city_code: str, limit: int) -> List[Dict[str, Any]]:
    """解析 Tabelog 列表页 HTML"""
    soup = BeautifulSoup(html, "lxml")
    results = []

    # Tabelog 餐厅卡片选择器
    cards = soup.select("li.list-rst__item")[:limit]

    for card in cards:
        try:
            # 名称
            name_el = card.select_one(".list-rst__rst-name-target")
            name_ja = name_el.get_text(strip=True) if name_el else ""
            if not name_ja:
                continue

            # 链接 → tabelog_id
            href = name_el.get("href", "") if name_el else ""
            tabelog_id = _extract_tabelog_id_from_url(href)

            # 评分
            score_el = card.select_one(".c-rating__val")
            score_text = score_el.get_text(strip=True) if score_el else ""
            try:
                score = float(score_text)
            except ValueError:
                score = None

            # 价格
            budget_els = card.select(".list-rst__budget-item")
            price_lunch = _parse_tabelog_price(
                budget_els[0].get_text(strip=True) if len(budget_els) > 0 else ""
            )
            price_dinner = _parse_tabelog_price(
                budget_els[1].get_text(strip=True) if len(budget_els) > 1 else ""
            )

            # 菜系
            cuisine_el = card.select_one(".list-rst__category-item")
            cuisine_text = cuisine_el.get_text(strip=True) if cuisine_el else ""

            # 地区
            area_el = card.select_one(".list-rst__area-genre .c-rating__prefecture")
            area = area_el.get_text(strip=True) if area_el else ""

            # 评论数
            review_el = card.select_one(".list-rst__total-count-num")
            review_text = review_el.get_text(strip=True) if review_el else "0"
            try:
                reviews = int(review_text.replace(",", ""))
            except ValueError:
                reviews = 0

            results.append({
                "name_ja": name_ja,
                "name_zh": "",
                "name_en": "",
                "city_code": city_code,
                "tabelog_id": tabelog_id,
                "tabelog_url": href,
                "tabelog_score": score,
                "tabelog_review_count": reviews,
                "price_lunch_jpy": price_lunch,
                "price_dinner_jpy": price_dinner,
                "cuisine_raw": cuisine_text,
                "district": area,
                "source": "tabelog",
            })
        except Exception:
            continue

    return results


def _extract_tabelog_id_from_url(url: str) -> Optional[str]:
    """从 Tabelog URL 提取餐厅 ID"""
    match = re.search(r'/(\d{8})/?', url)
    return match.group(1) if match else None


def _parse_tabelog_price(price_str: str) -> Optional[int]:
    """解析 Tabelog 价格字符串，如 '¥3,000～¥3,999' → 3000"""
    if not price_str or price_str == "-":
        return None
    # 提取第一个数字
    match = re.search(r'[\d,]+', price_str.replace("¥", "").replace("￥", ""))
    if match:
        try:
            return int(match.group(0).replace(",", ""))
        except ValueError:
            return None
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Wikipedia API — 获取景点描述
# ─────────────────────────────────────────────────────────────────────────────

async def fetch_wikipedia_summary(
    title_ja: str,
    lang: str = "ja",
) -> Dict[str, Any]:
    """
    从 Wikipedia 获取景点摘要和坐标。

    Args:
        title_ja: 日文标题，如 "浅草寺"
        lang:     语言版本 (ja/zh/en)

    Returns:
        包含 extract, coordinates, thumbnail 的字典
    """
    encoded = quote(title_ja)
    url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{encoded}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers={"User-Agent": "JapanTravelAI/1.0"})
            if resp.status_code == 200:
                data = resp.json()
                coords = data.get("coordinates", {})
                return {
                    "description": data.get("extract", "")[:500],
                    "lat": coords.get("lat"),
                    "lng": coords.get("lon"),
                    "thumbnail": data.get("thumbnail", {}).get("source", ""),
                    "wikipedia_url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                }
    except Exception:
        pass

    return {}


# ─────────────────────────────────────────────────────────────────────────────
# 连通性检查
# ─────────────────────────────────────────────────────────────────────────────

async def check_connectivity() -> Dict[str, bool]:
    """
    检查各数据源的网络连通性。
    在开始批量爬取前调用，决定使用哪些数据源。
    """
    results: Dict[str, bool] = {}

    checks = {
        "osm_overpass": "https://overpass-api.de/api/status",
        "tabelog":      "https://tabelog.com/",
        "wikipedia_ja": "https://ja.wikipedia.org/",
        "nominatim":    "https://nominatim.openstreetmap.org/",
    }

    for name, url in checks.items():
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
                results[name] = resp.status_code < 500
        except Exception:
            results[name] = False

    return results
