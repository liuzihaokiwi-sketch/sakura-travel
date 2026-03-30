"""
Japan Guide 景点爬虫

爬取 japan-guide.com 的北海道各城市景点页面。
提取：景点名、评级（1-3星）、描述、地址。
与 entity_base 通过名字+城市匹配关联，存入 entity_source_scores。

Japan Guide 的景点页结构：
  https://www.japan-guide.com/e/e2164.html  — Sapporo
  https://www.japan-guide.com/e/e2161.html  — Hokkaido overview
  各景点有 1-3 星评级（★★★ = must-see, ★★ = recommended, ★ = nice to visit）

使用策略：
  - 先抓列表页得到景点名+评级
  - 不抓详情页（避免过度爬取）
  - 通过景点名与 entity_base 模糊匹配（英文名 or 日文名）
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Japan Guide 城市景点页面 URL mapping
JAPAN_GUIDE_PAGES: Dict[str, List[str]] = {
    "sapporo":     ["https://www.japan-guide.com/e/e2163.html"],
    "otaru":       ["https://www.japan-guide.com/e/e6700.html"],
    "hakodate":    ["https://www.japan-guide.com/e/e5350.html"],
    "asahikawa":   ["https://www.japan-guide.com/e/e6890.html"],
    "furano":      ["https://www.japan-guide.com/e/e6825.html"],
    "noboribetsu": ["https://www.japan-guide.com/e/e6750.html"],
    "niseko":      ["https://www.japan-guide.com/e/e6720.html"],
    "abashiri":    ["https://www.japan-guide.com/e/e6865.html"],
    "kushiro":     ["https://www.japan-guide.com/e/e6790.html"],
    "toya":        ["https://www.japan-guide.com/e/e6725.html"],
    # Hokkaido overview (landscape attractions)
    "_hokkaido":   ["https://www.japan-guide.com/list/e1101.html"],
}

# 评级标记 → 数字
STAR_MAP = {"★★★": 3, "★★": 2, "★": 1}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def _parse_star_rating(text: str) -> Optional[int]:
    """从文本中提取 1-3 星评级"""
    for star_text, val in STAR_MAP.items():
        if star_text in text:
            return val
    # 也支持 alt text: "Highly Recommended" → 3, "Recommended" → 2
    text_lower = text.lower()
    if "highly recommended" in text_lower or "must-see" in text_lower:
        return 3
    if "recommended" in text_lower:
        return 2
    if "worth" in text_lower or "nice" in text_lower:
        return 1
    return None


def _extract_attractions_from_page(html: str, city_code: str) -> List[Dict[str, Any]]:
    """
    从 Japan Guide 页面提取景点列表。

    HTML 结构（2025+）：
    <li class="spot_list__spot ...">
      <a class="spot_list__spot__name" href="/e/eXXXX.html">
        Name<span class="dot_rating" data-dots="2" data-tooltip-label="Highly Recommended">••</span>
      </a>
      <div class="spot_list__spot__desc">Description text</div>
      <span class="user_ratings__value">4.6</span>  (user rating)
    </li>
    """
    soup = BeautifulSoup(html, "html.parser")
    attractions = []

    # 主选择器：spot_list__spot li 项目
    for item in soup.select("li.spot_list__spot"):
        # 名称链接
        name_link = item.select_one("a.spot_list__spot__name")
        if not name_link:
            continue

        href = name_link.get("href", "")
        url = f"https://www.japan-guide.com{href}" if href.startswith("/") else href

        # JG 内部评级（data-dots 或 aria-label）— 必须在 decompose 前提取
        dots_elem = item.select_one("[data-dots]")
        rating_stars = None
        if dots_elem:
            try:
                val = int(dots_elem.get("data-dots", 0))
                rating_stars = val if val > 0 else None
            except (ValueError, TypeError):
                pass
        if not rating_stars:
            aria = item.find(attrs={"aria-label": re.compile(r"JG Rating: \d")})
            if aria:
                m = re.search(r"JG Rating: (\d)", aria.get("aria-label", ""))
                if m:
                    rating_stars = int(m.group(1))

        # 名称：去掉 dot_rating span 再取文字
        dot_rating_span = name_link.select_one(".dot_rating")
        if dot_rating_span:
            dot_rating_span.decompose()
        name_en = name_link.get_text(strip=True)
        name_en = re.sub(r"[•·\u2022\u00b7]+$", "", name_en).strip()

        if not name_en or len(name_en) < 2:
            continue

        # 描述
        desc_elem = item.select_one(".spot_list__spot__desc")
        desc = desc_elem.get_text(strip=True) if desc_elem else None

        # 用户评分
        rating_elem = item.select_one(".user_ratings__value")
        user_rating = None
        if rating_elem:
            try:
                user_rating = float(rating_elem.get_text(strip=True))
            except ValueError:
                pass

        # 类型（Festival / Park / Museum 等）
        meta_elem = item.select_one(".spot_list__spot__meta--context")
        category_hint = meta_elem.get_text(strip=True) if meta_elem else None

        attractions.append({
            "name_en": name_en,
            "rating_stars": rating_stars,
            "user_rating": user_rating,
            "description_en": desc,
            "url": url,
            "city_code": city_code,
            "source_name": "japan_guide",
            "category_hint": category_hint,
        })

    # 去重
    seen: set[str] = set()
    unique = []
    for a in attractions:
        key = a["name_en"].lower().strip()
        if key not in seen and len(key) > 2:
            seen.add(key)
            unique.append(a)

    return unique


async def fetch_attractions(
    city_code: str,
    delay: float = 2.0,
) -> List[Dict[str, Any]]:
    """
    抓取指定城市的 Japan Guide 景点列表。

    Args:
        city_code: 城市代码
        delay: 请求间隔（秒）

    Returns:
        景点信息列表
    """
    pages = JAPAN_GUIDE_PAGES.get(city_code, [])
    if not pages:
        logger.warning("[japan_guide] No pages configured for %s", city_code)
        return []

    all_attractions: List[Dict[str, Any]] = []
    seen_names: set[str] = set()

    async with httpx.AsyncClient(
        headers=_HEADERS,
        timeout=20.0,
        follow_redirects=True,
    ) as client:
        for url in pages:
            try:
                logger.info("[japan_guide] Fetching %s", url)
                resp = await client.get(url)

                if resp.status_code != 200:
                    logger.warning("[japan_guide] HTTP %d for %s", resp.status_code, url)
                    continue

                attractions = _extract_attractions_from_page(resp.text, city_code)
                for a in attractions:
                    key = a["name_en"].lower().strip()
                    if key not in seen_names:
                        seen_names.add(key)
                        all_attractions.append(a)

                logger.info("[japan_guide] %s: found %d attractions from %s",
                            city_code, len(attractions), url)

                await asyncio.sleep(delay)

            except Exception as e:
                logger.error("[japan_guide] Failed to fetch %s: %s", url, e)

    return all_attractions


def normalize_name_for_match(name: str) -> str:
    """标准化名称用于匹配"""
    # 去掉括号内容、特殊字符，小写
    name = re.sub(r"\([^)]*\)", "", name)
    name = re.sub(r"['\"-]", " ", name)
    return name.lower().strip()


async def match_and_store_scores(
    session,
    attractions: List[Dict[str, Any]],
    city_code: str,
) -> Tuple[int, int]:
    """
    将 Japan Guide 景点与 entity_base 关联，存入 entity_source_scores。

    Returns:
        (matched_count, unmatched_count)
    """
    from sqlalchemy import text

    matched = 0
    unmatched = 0

    for attraction in attractions:
        name_en = attraction.get("name_en", "")
        rating_stars = attraction.get("rating_stars")

        if not name_en:
            continue

        # 尝试通过英文名匹配（忽略大小写）
        normalized = normalize_name_for_match(name_en)
        result = await session.execute(text("""
            SELECT entity_id FROM entity_base
            WHERE city_code = :city_code
              AND is_active = true
              AND (
                LOWER(name_en) LIKE :pattern
                OR LOWER(name_ja) LIKE :pattern
                OR LOWER(name_zh) LIKE :pattern
              )
            LIMIT 1
        """), {
            "city_code": city_code,
            "pattern": f"%{normalized}%",
        })
        row = result.fetchone()

        if row:
            entity_id = row[0]
            # user_rating から normalized_score を優先計算（0-5 → 0-100）
            user_rating = attraction.get("user_rating")
            jg_stars = rating_stars if rating_stars and rating_stars > 0 else None
            # normalized_score: JG内部评级优先（3星=100），否则用用户评分（5.0=100）
            if jg_stars:
                normalized_score = round(jg_stars / 3.0 * 100, 1)
                raw_score = float(jg_stars)
            elif user_rating:
                normalized_score = round(user_rating / 5.0 * 100, 1)
                raw_score = user_rating
            else:
                normalized_score = None
                raw_score = None

            import json
            extra_json = json.dumps({
                "name_en": name_en,
                "jg_rating_stars": jg_stars,
                "user_rating": user_rating,
                "description_en": attraction.get("description_en"),
                "source_url": attraction.get("url"),
                "category_hint": attraction.get("category_hint"),
            })
            await session.execute(text("""
                INSERT INTO entity_source_scores
                  (entity_id, source_name, raw_score, normalized_score, extra, fetched_at)
                VALUES
                  (:entity_id, 'japan_guide', :raw_score, :normalized_score,
                   CAST(:extra AS jsonb), NOW())
                ON CONFLICT (entity_id, source_name) DO UPDATE SET
                  raw_score = EXCLUDED.raw_score,
                  normalized_score = EXCLUDED.normalized_score,
                  extra = EXCLUDED.extra,
                  fetched_at = NOW()
            """), {
                "entity_id": str(entity_id),
                "raw_score": raw_score,
                "normalized_score": normalized_score,
                "extra": extra_json,
            })
            matched += 1
        else:
            unmatched += 1

    await session.commit()
    return matched, unmatched
