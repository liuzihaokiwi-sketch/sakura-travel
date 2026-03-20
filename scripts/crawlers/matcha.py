"""
MATCHA 繁中站 (matcha-jp.com/zh-Hant) 爬虫
===========================================
抓取日本出品、多语言旅游媒体 MATCHA 的繁体中文文章。

采集方式（按优先级）：
  1. REST API: GET /api/v1/articles?language=zh-Hant&...
  2. HTML 解析备选

采集字段:
  id, source, title, summary, city, category,
  tags, publish_date, url, image_url, language, crawled_at

用法:
  python scripts/guide_crawl.py --source matcha --city tokyo --limit 20
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scripts.crawlers.base import BaseCrawler

logger = logging.getLogger(__name__)

# ── 城市关键词映射 ─────────────────────────────────────────────────────────────

CITY_KEYWORD_MAP: Dict[str, str] = {
    "東京": "tokyo",    "tokyo": "tokyo",
    "大阪": "osaka",    "osaka": "osaka",
    "京都": "kyoto",    "kyoto": "kyoto",
    "奈良": "nara",     "nara": "nara",
    "箱根": "hakone",   "hakone": "hakone",
    "北海道": "sapporo", "札幌": "sapporo", "sapporo": "sapporo",
    "沖繩": "okinawa",  "okinawa": "okinawa",
    "神戶": "kobe",     "kobe": "kobe",
    "名古屋": "nagoya", "nagoya": "nagoya",
    "福岡": "fukuoka",  "fukuoka": "fukuoka",
    "廣島": "hiroshima", "hiroshima": "hiroshima",
    "鎌倉": "kamakura", "kamakura": "kamakura",
    "橫濱": "yokohama", "yokohama": "yokohama",
}

# MATCHA 城市/地区 slug（用于 API pref 参数）
CITY_PREF_MAP: Dict[str, str] = {
    "tokyo":     "tokyo",
    "osaka":     "osaka",
    "kyoto":     "kyoto",
    "nara":      "nara",
    "hakone":    "kanagawa",
    "sapporo":   "hokkaido",
    "okinawa":   "okinawa",
    "kobe":      "hyogo",
    "nagoya":    "aichi",
    "fukuoka":   "fukuoka",
    "hiroshima": "hiroshima",
    "kamakura":  "kanagawa",
    "yokohama":  "kanagawa",
}

# ── 类别映射 ───────────────────────────────────────────────────────────────────

CATEGORY_MAP: Dict[str, str] = {
    "gourmet":   "food",
    "food":      "food",
    "shopping":  "shopping",
    "transport": "transport",
    "hotel":     "accommodation",
    "stay":      "accommodation",
    "sightseeing": "attraction",
    "nature":    "attraction",
    "culture":   "attraction",
    "event":     "seasonal",
    "festival":  "seasonal",
    "tips":      "guide",
    "guide":     "guide",
}

CATEGORY_RULES: List[tuple] = [
    (["美食", "飲食", "料理", "拉麵", "壽司", "咖啡", "甜點"], "food"),
    (["購物", "必買", "伴手禮", "藥妝", "百貨"], "shopping"),
    (["交通", "電車", "新幹線", "JR", "IC卡", "巴士"], "transport"),
    (["住宿", "飯店", "旅館", "民宿", "溫泉"], "accommodation"),
    (["賞櫻", "楓葉", "紅葉", "祭典", "花火", "季節"], "seasonal"),
    (["景點", "必去", "寺", "神社", "城", "公園"], "attraction"),
]


def _map_category(api_category: str, title: str = "") -> str:
    """将 API 返回的 category 映射到本地分类"""
    if api_category:
        lower = api_category.lower()
        for key, val in CATEGORY_MAP.items():
            if key in lower:
                return val
    # 从标题推断
    for keywords, cat in CATEGORY_RULES:
        if any(kw in title for kw in keywords):
            return cat
    return "guide"


def _infer_city(text: str) -> Optional[str]:
    """从文本推断城市"""
    for key, code in CITY_KEYWORD_MAP.items():
        if key in text:
            return code
    return None


class MATCHACrawler(BaseCrawler):
    """
    MATCHA 繁中站爬虫。

    优先使用官方 REST API，失败时回退到 HTML 解析。
    """

    BASE = "https://matcha-jp.com"
    API = "https://matcha-jp.com/api/v1"

    def __init__(
        self,
        output_dir: str = "data/raw/matcha",
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("delay_range", (1.0, 2.5))
        super().__init__(**kwargs)
        self.output_dir = Path(output_dir)

    # ── 主入口 ────────────────────────────────────────────────────────────────

    async def crawl_by_city(
        self,
        city: str = "tokyo",
        limit: int = 50,
        save_json: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        按城市采集攻略文章。

        先尝试 API 方式，失败则用 HTML 解析。

        Args:
            city:      城市代码（tokyo/osaka/kyoto/...）
            limit:     最多采集条数
            save_json: 是否保存 JSON

        Returns:
            文章列表
        """
        logger.info(f"🍵 MATCHA [{city}]: 采集 {limit} 篇文章")

        # 优先 API
        articles = await self._crawl_by_api(city, limit)

        # API 失败时回退到 HTML
        if not articles:
            logger.warning(f"  ⚠️  API 未返回数据，改用 HTML 解析...")
            articles = await self._crawl_by_html(city, limit)

        if save_json and articles:
            self._save_json(articles, city)

        self._print_summary(articles, city)
        return articles

    async def crawl_all(
        self,
        cities: Optional[List[str]] = None,
        limit_per_city: int = 50,
        save_json: bool = True,
    ) -> List[Dict[str, Any]]:
        """采集所有城市文章"""
        if cities is None:
            cities = ["tokyo", "osaka", "kyoto"]

        all_articles: List[Dict[str, Any]] = []
        for city in cities:
            articles = await self.crawl_by_city(city=city, limit=limit_per_city, save_json=False)
            all_articles.extend(articles)

        if save_json and all_articles:
            self._save_json(all_articles, "all")

        return all_articles

    # ── API 方式 ──────────────────────────────────────────────────────────────

    async def _crawl_by_api(
        self, city: str, limit: int
    ) -> List[Dict[str, Any]]:
        """
        调用 MATCHA REST API 获取文章。

        尝试的 API 端点：
        - /api/v1/articles?language=zh-Hant&pref={pref}&per_page=20
        - /api/v1/articles?language=zh-Hant&tag={city}&per_page=20
        """
        pref = CITY_PREF_MAP.get(city, city)
        articles: List[Dict[str, Any]] = []

        # 尝试多个 API 变体
        api_urls = [
            f"{self.API}/articles",
        ]

        param_variants = [
            {"language": "zh-Hant", "pref": pref, "per_page": min(limit, 20)},
            {"language": "zh-Hant", "tag": city, "per_page": min(limit, 20)},
            {"language": "zh-Hant", "area": pref, "per_page": min(limit, 20)},
            {"locale": "zh-Hant", "pref": pref, "per_page": min(limit, 20)},
        ]

        for api_url in api_urls:
            for params in param_variants:
                resp = await self.fetch(
                    api_url,
                    params=params,
                    headers={
                        "Accept": "application/json",
                        "Referer": f"{self.BASE}/zh-Hant",
                    },
                )
                if not resp:
                    continue

                try:
                    data = resp.json()
                    raw_articles = []

                    # 多种 API 响应结构
                    if isinstance(data, list):
                        raw_articles = data
                    elif isinstance(data, dict):
                        raw_articles = (
                            data.get("articles", [])
                            or data.get("data", [])
                            or data.get("items", [])
                            or data.get("results", [])
                        )

                    if raw_articles:
                        logger.info(f"  ✅ API 返回 {len(raw_articles)} 条 (params={params})")
                        for item in raw_articles[:limit]:
                            article = self._parse_api_item(item, city)
                            if article:
                                articles.append(article)
                        if articles:
                            return articles

                except (json.JSONDecodeError, Exception) as e:
                    logger.debug(f"  API 解析失败: {e}")
                    continue

        return articles

    def _parse_api_item(
        self, item: Dict[str, Any], city_hint: str
    ) -> Optional[Dict[str, Any]]:
        """解析单条 API 返回项"""
        try:
            title = (
                item.get("title", "")
                or item.get("name", "")
                or item.get("headline", "")
            )
            if not title:
                return None

            article_id = str(item.get("id", "") or item.get("slug", ""))
            url = item.get("url", "") or item.get("link", "") or item.get("canonical_url", "")
            if url and not url.startswith("http"):
                url = urljoin(self.BASE, url)
            if not url and article_id:
                url = f"{self.BASE}/zh-Hant/{article_id}"

            summary = (
                item.get("summary", "")
                or item.get("description", "")
                or item.get("excerpt", "")
                or item.get("body", "")[:150]
            )
            if summary:
                summary = summary[:150]

            image_url = (
                item.get("thumbnail", "")
                or item.get("image", "")
                or item.get("cover_image", "")
            )
            if isinstance(image_url, dict):
                image_url = image_url.get("url", "") or image_url.get("src", "")

            # 标签
            tags_raw = item.get("tags", []) or item.get("labels", [])
            tags = []
            for t in tags_raw:
                if isinstance(t, dict):
                    tags.append(t.get("name", "") or t.get("label", ""))
                elif isinstance(t, str):
                    tags.append(t)
            tags = [t for t in tags if t][:10]

            # 城市
            city_code = _infer_city(title + " " + str(tags))
            if not city_code:
                pref_val = item.get("pref", "") or item.get("area", "") or item.get("region", "")
                for key, code in CITY_KEYWORD_MAP.items():
                    if key in str(pref_val):
                        city_code = code
                        break
            if not city_code:
                city_code = city_hint

            # 类别
            api_cat = str(item.get("category", "") or item.get("type", "") or item.get("genre", ""))
            category = _map_category(api_cat, title)

            # 日期
            publish_date = (
                item.get("published_at", "")
                or item.get("created_at", "")
                or item.get("date", "")
                or ""
            )
            if publish_date:
                publish_date = str(publish_date)[:10]

            return {
                "id": f"matcha_{article_id}" if article_id else f"matcha_{hash(url) & 0xFFFFFF}",
                "source": "matcha",
                "title": title,
                "summary": summary,
                "city": city_code,
                "category": category,
                "tags": tags,
                "publish_date": publish_date,
                "url": url,
                "image_url": image_url or "",
                "language": "zh-TW",
                "engagement": None,
                "crawled_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.debug(f"  API 项解析失败: {e}")
            return None

    # ── HTML 解析备选 ─────────────────────────────────────────────────────────

    async def _crawl_by_html(
        self, city: str, limit: int
    ) -> List[Dict[str, Any]]:
        """HTML 解析备选方案"""
        pref = CITY_PREF_MAP.get(city, city)
        articles: List[Dict[str, Any]] = []
        seen_urls: set = set()

        # 尝试多个 URL 格式
        list_urls = [
            f"{self.BASE}/zh-Hant/list?pref={pref}",
            f"{self.BASE}/zh-Hant/list?area={pref}",
            f"{self.BASE}/zh-Hant/tag/{city}",
            f"{self.BASE}/zh-Hant/search?q={city}",
        ]

        for list_url in list_urls:
            page_articles = await self._parse_html_list(list_url, city)
            for art in page_articles:
                if art["url"] not in seen_urls:
                    seen_urls.add(art["url"])
                    articles.append(art)
                    if len(articles) >= limit:
                        break
            if articles:
                break

        return articles[:limit]

    async def _parse_html_list(
        self, url: str, city_hint: str
    ) -> List[Dict[str, Any]]:
        """解析 HTML 列表页"""
        html = await self.fetch_text(
            url,
            headers={"Accept-Language": "zh-TW,zh;q=0.9"},
            referer=f"{self.BASE}/zh-Hant",
        )
        if not html:
            return []

        try:
            soup = BeautifulSoup(html, "html.parser")
            results = []

            # 多种文章卡片选择器
            cards = (
                soup.find_all("article")
                or soup.find_all("div", class_=re.compile(r"article-card|post-card|entry-item|list-item"))
                or soup.find_all("li", class_=re.compile(r"article|post|entry"))
                or soup.find_all("a", class_=re.compile(r"article-link|post-link"))
            )

            if not cards:
                # 尝试提取 JSON-LD
                for script in soup.find_all("script", type="application/ld+json"):
                    try:
                        ld = json.loads(script.string or "")
                        if isinstance(ld, dict) and ld.get("@type") == "ItemList":
                            for item in ld.get("itemListElement", []):
                                article = self._parse_ld_item(item, city_hint)
                                if article:
                                    results.append(article)
                    except Exception:
                        pass

            for card in cards:
                try:
                    article = self._parse_html_card(card, city_hint)
                    if article:
                        results.append(article)
                except Exception as e:
                    logger.debug(f"  HTML 卡片解析失败: {e}")

            logger.info(f"  📄 HTML 列表 [{url[-60:]}]: {len(results)} 篇")
            return results

        except Exception as e:
            logger.warning(f"  ⚠️  HTML 列表解析失败: {e}")
            return []

    def _parse_html_card(
        self, card: Any, city_hint: str
    ) -> Optional[Dict[str, Any]]:
        """解析单个 HTML 文章卡片"""
        # 链接
        a_el = card if card.name == "a" else card.find("a", href=True)
        if not a_el:
            return None

        url = a_el.get("href", "")
        if not url:
            return None
        if not url.startswith("http"):
            url = urljoin(self.BASE, url)

        # 标题
        title_el = (
            card.find(["h1", "h2", "h3", "h4"])
            or card.find(class_=re.compile(r"title|headline|heading"))
            or a_el
        )
        title = title_el.get_text(strip=True) if title_el else ""
        if not title or len(title) < 5:
            return None

        # 摘要
        summary_el = card.find(class_=re.compile(r"summary|excerpt|description|body"))
        summary = summary_el.get_text(strip=True)[:150] if summary_el else ""

        # 图片
        img_el = card.find("img")
        image_url = ""
        if img_el:
            image_url = (
                img_el.get("data-src") or img_el.get("data-lazy-src")
                or img_el.get("src", "")
            )
            if image_url and image_url.startswith("data:"):
                image_url = ""

        # 标签
        tag_els = card.find_all(class_=re.compile(r"tag|label|badge|category"))
        tags = [t.get_text(strip=True) for t in tag_els if len(t.get_text(strip=True)) < 20][:10]

        # 日期
        date_el = card.find("time") or card.find(class_=re.compile(r"date|published"))
        publish_date = ""
        if date_el:
            publish_date = date_el.get("datetime", "") or date_el.get_text(strip=True)
            publish_date = str(publish_date)[:10]

        city_code = _infer_city(title + " " + url + " " + " ".join(tags)) or city_hint
        category = _map_category("", title)

        url_id = re.search(r"/(\d+)/?$", url) or re.search(r"/([a-z0-9-]+)/?$", url)
        art_id = f"matcha_{url_id.group(1)}" if url_id else f"matcha_{hash(url) & 0xFFFFFF}"

        return {
            "id": art_id,
            "source": "matcha",
            "title": title,
            "summary": summary,
            "city": city_code,
            "category": category,
            "tags": tags,
            "publish_date": publish_date,
            "url": url,
            "image_url": image_url,
            "language": "zh-TW",
            "engagement": None,
            "crawled_at": datetime.utcnow().isoformat(),
        }

    def _parse_ld_item(
        self, item: Dict[str, Any], city_hint: str
    ) -> Optional[Dict[str, Any]]:
        """解析 JSON-LD ItemList 中的条目"""
        try:
            inner = item.get("item", item)
            url = inner.get("url", "") or inner.get("@id", "")
            title = inner.get("name", "")
            if not title or not url:
                return None

            return {
                "id": f"matcha_{hash(url) & 0xFFFFFF}",
                "source": "matcha",
                "title": title,
                "summary": inner.get("description", "")[:150],
                "city": _infer_city(title) or city_hint,
                "category": "guide",
                "tags": [],
                "publish_date": "",
                "url": url if url.startswith("http") else urljoin(self.BASE, url),
                "image_url": "",
                "language": "zh-TW",
                "engagement": None,
                "crawled_at": datetime.utcnow().isoformat(),
            }
        except Exception:
            return None

    # ── 工具 ──────────────────────────────────────────────────────────────────

    def _save_json(self, articles: List[Dict[str, Any]], city: str) -> None:
        """保存 JSON"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fp = self.output_dir / f"matcha_{city}_{ts}.json"
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(
                {"meta": {"city": city, "total": len(articles), "source": "matcha"},
                 "articles": articles},
                f, ensure_ascii=False, indent=2,
            )
        logger.info(f"💾 已保存: {fp}")

    def _print_summary(self, articles: List[Dict[str, Any]], city: str) -> None:
        """打印采集摘要"""
        print(f"\n🍵 MATCHA [{city}]: {len(articles)} 篇攻略")
        by_cat: Dict[str, int] = {}
        for a in articles:
            cat = a.get("category") or "guide"
            by_cat[cat] = by_cat.get(cat, 0) + 1
        print("  类别分布:", dict(sorted(by_cat.items())))
        for a in articles[:5]:
            print(f"  📖 [{a.get('city','?')}] {a['title'][:50]}")
