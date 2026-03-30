"""
通用攻略网站爬虫 (Guide Scraper)

爬取攻略网站的札幌/北海道页面，提取被提及的地点名称列表。
存入 discovery_candidates 表，标记 source_count。
与 entity_base 关联（已有的标记，没有的作为新候选）。

目标站点：
  - letsgojp.cn (中文北海道攻略)
  - gltjp.com (中文日本旅游攻略)
  - uu-hokkaido.in (日文北海道攻略)
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,ja;q=0.8,en;q=0.7",
}

# 目标页面配置
GUIDE_PAGES: Dict[str, List[Dict[str, Any]]] = {
    "sapporo": [
        {
            "source": "lonelyplanet.com",
            "urls": [
                "https://www.lonelyplanet.com/japan/hokkaido/sapporo/attractions",
                "https://www.lonelyplanet.com/japan/hokkaido/sapporo/restaurants",
            ],
            "lang": "en",
        },
        {
            "source": "visit-hokkaido.jp",
            "urls": [
                "https://en.visit-hokkaido.jp/destinations/sapporo/",
                "https://en.visit-hokkaido.jp/spot/?area=sapporo",
            ],
            "lang": "en",
        },
        {
            "source": "uu-hokkaido.in",
            "urls": [
                "https://uu-hokkaido.in/sapporo/",
                "https://uu-hokkaido.in/sightseeing/",
                "https://uu-hokkaido.in/food/",
            ],
            "lang": "en",
        },
    ],
}

# 日本地名识别模式
# 日语地名：包含 駅/寺/神社/公園/館/山/川/湖/島/城/橋/市場/通り/タワー 等
_JA_PLACE_PATTERNS = [
    r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]{2,15}(?:駅|寺|神社|公園|館|山|川|湖|島|城|橋|市場|通り|タワー|温泉|牧場|スキー場|展望台|海岸|岬|池|滝|谷)",
    r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]{3,20}(?:ホテル|旅館|リゾート|ビール|ファクトリー|パーク|ガーデン)",
]
# 中文地名：包含 公园/神社/寺/博物馆/市场/山/温泉 等
_ZH_PLACE_PATTERNS = [
    r"[\u4e00-\u9fff]{2,12}(?:公园|神社|寺院|寺|博物馆|市场|温泉|山|湖|岛|城堡|塔|桥|展望台|牧场|滑雪场|海鲜市场|夜市)",
    r"[\u4e00-\u9fff]{3,15}(?:啤酒博物馆|巧克力工厂|乐园|动物园|水族馆|艺术馆)",
    r"(?:円山|大通|时计台|电视塔|白色恋人|薄野|二条|北海道神宫|定山溪|藻岩山|狸小路|钟楼|大通公园)",
]
# 英文地名（短于30字符的大写开头的名词）
_EN_PLACE_PATTERNS = [
    r"(?:Mount|Lake|Park|Shrine|Temple|Museum|Castle|Market|Tower|Onsen|Beer|Garden|Zoo)\s+\w+",
    r"\b(?:Odori|Susukino|Tanukikoji|Nijo|Curb Market|Shiroi Koibito|Okurayama|Moerenuma)\b",
]


def _extract_place_names(text: str, lang: str = "en") -> List[str]:
    """从文本中提取可能的地名"""
    found = []
    seen = set()

    if lang == "zh":
        active_patterns = _ZH_PLACE_PATTERNS + _EN_PLACE_PATTERNS
    elif lang == "ja":
        active_patterns = _JA_PLACE_PATTERNS + _EN_PLACE_PATTERNS
    else:  # en
        active_patterns = _EN_PLACE_PATTERNS + _JA_PLACE_PATTERNS

    for pattern in active_patterns:
        for m in re.finditer(pattern, text, re.IGNORECASE if lang == "en" else 0):
            name = m.group(0).strip()
            if name and name not in seen and 2 <= len(name) <= 40:
                seen.add(name)
                found.append(name)

    # 对英文页面：额外提取 h2/h3 标题作为潜在地名（需调用者传入）
    return found


def _extract_headings_as_places(html: str) -> List[str]:
    """
    从 HTML 标题标签提取景点名（作为补充）。
    只保留看起来是具体地名的标题。
    """
    soup = BeautifulSoup(html, "html.parser")
    places = []
    seen = set()

    # 常见地名关键词（英文）
    place_indicators = {
        "park", "shrine", "temple", "museum", "castle", "tower", "market",
        "garden", "zoo", "aquarium", "pond", "lake", "mount", "mountain",
        "onsen", "brewery", "brewery", "factory", "district", "street",
        "canal", "station", "hill", "island", "bay", "beach", "observatory",
        "botanical", "memorial", "historic", "palace",
    }
    # 排除词（这些标题一定不是地名）
    skip_words = {
        "introduction", "overview", "how to", "best time", "getting",
        "transport", "accommodation", "tips", "things to", "places to",
        "where to", "what to", "about", "contact", "privacy", "newsletter",
        "subscribe", "follow", "read more", "see more", "click", "explore more",
        "popular", "featured", "recommended", "travel", "booking", "spring",
        "summer", "autumn", "winter", "season", "access", "ranking",
    }

    for tag in soup.find_all(["h2", "h3", "h4"]):
        text = tag.get_text(strip=True)
        if not text or len(text) < 4 or len(text) > 60:
            continue

        text_lower = text.lower()

        # 跳过明显非地名
        if any(w in text_lower for w in skip_words):
            continue

        # 必须包含地名指示词，或是日文/中文名称
        has_place_word = any(w in text_lower for w in place_indicators)
        has_cjk = bool(re.search(r"[\u4e00-\u9fff\u3040-\u30ff]", text))

        if (has_place_word or has_cjk) and text not in seen:
            seen.add(text)
            places.append(text)

    return places


def _clean_text(html: str) -> str:
    """清理 HTML，提取正文文本"""
    soup = BeautifulSoup(html, "html.parser")

    # 移除脚本、样式、导航
    for tag in soup.find_all(["script", "style", "nav", "header", "footer",
                               "aside", ".sidebar", ".ad", ".advertisement"]):
        tag.decompose()

    # 优先取文章主体
    main = (
        soup.find("article") or
        soup.find("main") or
        soup.find(class_=re.compile(r"content|article|post|entry", re.I)) or
        soup.body
    )
    if main:
        return main.get_text(" ", strip=True)
    return soup.get_text(" ", strip=True)


async def scrape_page(
    url: str,
    source: str,
    city_code: str,
    lang: str = "zh",
    timeout: float = 15.0,
) -> Tuple[List[str], str]:
    """
    爬取一个页面，提取地名列表和原始文本摘要。

    Returns:
        (place_names, text_snippet)
    """
    try:
        async with httpx.AsyncClient(
            headers=_HEADERS,
            timeout=timeout,
            follow_redirects=True,
        ) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                logger.warning("[guide_scraper] HTTP %d for %s", resp.status_code, url)
                return [], ""

            text = _clean_text(resp.text)
            # 模式匹配提取
            pattern_names = _extract_place_names(text, lang=lang)
            # 标题提取（补充）
            heading_names = _extract_headings_as_places(resp.text)
            # 合并去重
            all_names = list(dict.fromkeys(pattern_names + heading_names))
            snippet = text[:1000]

            logger.info("[guide_scraper] %s -> %s: %d place names extracted (%d pattern + %d heading)",
                        source, city_code, len(all_names), len(pattern_names), len(heading_names))
            return all_names, snippet

    except Exception as e:
        logger.error("[guide_scraper] Failed to scrape %s: %s", url, e)
        return [], ""


async def scrape_city_guides(
    city_code: str,
    delay: float = 2.0,
) -> Dict[str, Any]:
    """
    爬取指定城市的所有攻略页面。

    Returns:
        {source: [place_names], ...}
    """
    pages = GUIDE_PAGES.get(city_code, [])
    results: Dict[str, List[str]] = {}

    for page_config in pages:
        source = page_config["source"]
        lang = page_config.get("lang", "zh")
        seen_for_source: set[str] = set()

        for url in page_config["urls"]:
            names, _ = await scrape_page(url, source, city_code, lang=lang)
            for n in names:
                if n not in seen_for_source:
                    seen_for_source.add(n)

            await asyncio.sleep(delay)

        results[source] = list(seen_for_source)
        logger.info("[guide_scraper] %s/%s: %d unique names",
                    source, city_code, len(seen_for_source))

    return results


async def upsert_discovery_candidates(
    session,
    city_code: str,
    source_results: Dict[str, List[str]],
) -> Tuple[int, int]:
    """
    将爬取结果写入 discovery_candidates 表。
    已有的条目：更新 source_count 和 sources 列表。
    新条目：插入。

    Returns:
        (new_count, updated_count)
    """
    from sqlalchemy import text

    # 合并所有 source 的结果：{name: [source1, source2, ...]}
    name_sources: Dict[str, List[str]] = {}
    for source, names in source_results.items():
        for name in names:
            if name not in name_sources:
                name_sources[name] = []
            name_sources[name].append(source)

    new_count = 0
    updated_count = 0

    for name_raw, sources in name_sources.items():
        if not name_raw or len(name_raw) < 2:
            continue

        # 检查是否已存在
        existing = await session.execute(text("""
            SELECT id, source_count, sources
            FROM discovery_candidates
            WHERE city_code = :city_code AND name_raw = :name_raw
            LIMIT 1
        """), {"city_code": city_code, "name_raw": name_raw})
        row = existing.fetchone()

        if row:
            # 更新：合并 sources
            existing_sources = row[2] if row[2] else []
            merged = list(set(existing_sources + sources))
            await session.execute(text("""
                UPDATE discovery_candidates
                SET source_count = :source_count,
                    sources = CAST(:sources AS jsonb)
                WHERE id = :id
            """), {
                "id": row[0],
                "source_count": len(merged),
                "sources": json.dumps(merged),
            })
            updated_count += 1
        else:
            # 新插入
            # 尝试与 entity_base 匹配
            normalized = name_raw.lower().strip()
            match_result = await session.execute(text("""
                SELECT entity_id FROM entity_base
                WHERE city_code = :city_code
                  AND is_active = true
                  AND (
                    LOWER(name_zh) LIKE :pattern
                    OR LOWER(name_ja) LIKE :pattern
                    OR LOWER(name_en) LIKE :pattern
                  )
                LIMIT 1
            """), {"city_code": city_code, "pattern": f"%{normalized}%"})
            match_row = match_result.fetchone()

            matched_entity_id = str(match_row[0]) if match_row else None
            status = "matched" if matched_entity_id else "pending"

            await session.execute(text("""
                INSERT INTO discovery_candidates
                  (city_code, name_raw, name_normalized, source_count, sources,
                   matched_entity_id, match_confidence, status)
                VALUES
                  (:city_code, :name_raw, :name_normalized, :source_count,
                   CAST(:sources AS jsonb), :matched_entity_id, :confidence, :status)
                ON CONFLICT DO NOTHING
            """), {
                "city_code": city_code,
                "name_raw": name_raw,
                "name_normalized": normalized,
                "source_count": len(sources),
                "sources": json.dumps(sources),
                "matched_entity_id": matched_entity_id,
                "confidence": 0.7 if matched_entity_id else None,
                "status": status,
            })
            new_count += 1

    await session.commit()
    return new_count, updated_count
