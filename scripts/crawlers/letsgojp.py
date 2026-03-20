"""
樂吃購！日本 (letsgojp.com) 爬虫
====================================
抓取台湾最大日本旅游网站上的中文攻略文章。

采集字段:
  id, source, title, summary, city, category,
  tags, publish_date, url, image_url, language, crawled_at

站点特征:
  - WordPress 站，结构规律，直接 HTTP 抓取
  - URL 规则: /archives/category/area/{city}/
  - 内容为繁体中文 (zh-TW)

用法:
  python scripts/guide_crawl.py --source letsgojp --city tokyo --limit 20
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from scripts.crawlers.base import BaseCrawler

logger = logging.getLogger(__name__)

# ── 城市到分类路径映射 ─────────────────────────────────────────────────────────

CITY_PATHS: Dict[str, List[str]] = {
    "tokyo":  [
        "/archives/category/area/tokyo/",
        "/archives/category/area/tokyo-food/",
        "/archives/category/area/tokyo-shopping/",
    ],
    "osaka":  [
        "/archives/category/area/osaka/",
        "/archives/category/area/osaka-food/",
    ],
    "kyoto":  [
        "/archives/category/area/kyoto/",
        "/archives/category/area/kyoto-food/",
    ],
    "all": [
        "/archives/category/area/tokyo/",
        "/archives/category/area/osaka/",
        "/archives/category/area/kyoto/",
        "/archives/category/transport/",
        "/archives/category/travel-tips/",
    ],
}

# ── 标签/类别推断规则 ──────────────────────────────────────────────────────────

CATEGORY_RULES: List[tuple] = [
    (["美食", "食", "料理", "拉麵", "壽司", "抹茶", "咖啡", "甜點", "必吃"], "food"),
    (["購物", "必買", "伴手禮", "藥妝", "百貨", "outlet"], "shopping"),
    (["交通", "電車", "新幹線", "JR", "IC卡", "巴士", "機場"], "transport"),
    (["住宿", "飯店", "旅館", "民宿", "溫泉"], "accommodation"),
    (["賞櫻", "楓葉", "紅葉", "雪", "夏祭", "花火", "季節"], "seasonal"),
    (["景點", "必去", "打卡", "寺", "神社", "城", "公園", "博物館"], "attraction"),
    (["攻略", "自由行", "行程", "規劃", "簽證", "費用"], "guide"),
]

CITY_KEYWORD_MAP: Dict[str, str] = {
    "tokyo": "tokyo", "東京": "tokyo",
    "osaka": "osaka", "大阪": "osaka",
    "kyoto": "kyoto", "京都": "kyoto",
    "nara": "nara", "奈良": "nara",
    "hakone": "hakone", "箱根": "hakone",
    "sapporo": "sapporo", "北海道": "sapporo", "札幌": "sapporo",
    "okinawa": "okinawa", "沖繩": "okinawa",
    "kobe": "kobe", "神戶": "kobe",
    "nagoya": "nagoya", "名古屋": "nagoya",
    "fukuoka": "fukuoka", "福岡": "fukuoka",
    "hiroshima": "hiroshima", "廣島": "hiroshima",
    "kamakura": "kamakura", "鎌倉": "kamakura",
    "nikko": "nikko", "日光": "nikko",
}


def _infer_category(title: str, tags: List[str]) -> str:
    """根据标题和标签推断文章类别"""
    text = title + " ".join(tags)
    for keywords, cat in CATEGORY_RULES:
        if any(kw in text for kw in keywords):
            return cat
    return "guide"


def _infer_city(url: str, title: str) -> Optional[str]:
    """从 URL 路径或标题推断城市"""
    for key, code in CITY_KEYWORD_MAP.items():
        if key in url or key in title:
            return code
    return None


class LetsGoJPCrawler(BaseCrawler):
    """
    樂吃購！日本攻略爬虫。

    WordPress 站，HTTP 直接抓取，支持分页。
    """

    BASE = "https://www.letsgojp.com"

    def __init__(
        self,
        output_dir: str = "data/raw/letsgojp",
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("delay_range", (1.5, 3.5))
        super().__init__(**kwargs)
        self.output_dir = Path(output_dir)

    # ── 主入口 ────────────────────────────────────────────────────────────────

    async def crawl_category(
        self,
        city: str = "tokyo",
        pages: int = 5,
        fetch_detail: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        抓取某个地区的攻略文章列表。

        Args:
            city:         城市代码（tokyo/osaka/kyoto/all）
            pages:        每个分类抓取的页数
            fetch_detail: 是否进一步抓取文章详情（获取完整摘要）

        Returns:
            文章列表
        """
        paths = CITY_PATHS.get(city, CITY_PATHS["all"])
        all_articles: List[Dict[str, Any]] = []
        seen_urls: set = set()

        logger.info(f"🗾 樂吃購 [{city}]: 共 {len(paths)} 个分类，每类 {pages} 页")

        for path in paths:
            for page_num in range(1, pages + 1):
                if page_num == 1:
                    url = urljoin(self.BASE, path)
                else:
                    url = urljoin(self.BASE, path) + f"page/{page_num}/"

                articles = await self._parse_list_page(url, city)
                new_count = 0
                for art in articles:
                    if art["url"] not in seen_urls:
                        seen_urls.add(art["url"])
                        all_articles.append(art)
                        new_count += 1

                logger.info(f"  📄 {path} 第{page_num}页: {new_count} 篇新文章")

                if new_count == 0:
                    break  # 该分类已无更多内容

        if fetch_detail:
            logger.info(f"  🔍 抓取 {len(all_articles)} 篇文章详情...")
            for i, art in enumerate(all_articles):
                detail = await self.crawl_article(art["url"])
                if detail:
                    art.update({k: v for k, v in detail.items() if v})
                if (i + 1) % 10 == 0:
                    logger.info(f"  ✅ 已处理 {i+1}/{len(all_articles)}")

        logger.info(f"  ✅ 樂吃購 [{city}]: 共 {len(all_articles)} 篇文章")
        return all_articles

    async def crawl_article(self, url: str) -> Optional[Dict[str, Any]]:
        """
        抓取单篇文章详情。

        Args:
            url: 文章完整 URL

        Returns:
            文章详情字典（含 summary, full_tags, publish_date）
        """
        html = await self.fetch_text(url, referer=self.BASE)
        if not html:
            return None

        try:
            soup = BeautifulSoup(html, "html.parser")

            # 摘要（取正文前 150 字）
            content_el = (
                soup.find("div", class_=re.compile(r"entry-content|post-content|article-content"))
                or soup.find("article")
            )
            summary = ""
            if content_el:
                # 清除广告/脚本
                for tag in content_el.find_all(["script", "style", "ins", "aside"]):
                    tag.decompose()
                text = content_el.get_text(" ", strip=True)
                summary = text[:150].strip()

            # 详细标签
            tag_els = soup.find_all("a", rel=re.compile("tag")) or soup.find_all(
                "a", href=re.compile(r"/tag/")
            )
            tags = [t.get_text(strip=True) for t in tag_els][:15]

            # 发布日期
            date_el = (
                soup.find("time")
                or soup.find(class_=re.compile(r"published|entry-date|post-date"))
            )
            publish_date = ""
            if date_el:
                publish_date = date_el.get("datetime", "") or date_el.get_text(strip=True)
                publish_date = publish_date[:10] if publish_date else ""

            return {
                "summary": summary,
                "tags": tags,
                "publish_date": publish_date,
            }

        except Exception as e:
            logger.warning(f"  ⚠️  文章详情解析失败: {e} [{url}]")
            return None

    async def crawl_all(
        self,
        cities: Optional[List[str]] = None,
        pages: int = 5,
        save_json: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        批量采集所有城市文章。

        Args:
            cities:    城市列表，默认 ["tokyo", "osaka", "kyoto"]
            pages:     每个分类页数
            save_json: 是否保存 JSON

        Returns:
            全部文章列表
        """
        if cities is None:
            cities = ["tokyo", "osaka", "kyoto"]

        all_articles: List[Dict[str, Any]] = []
        for city in cities:
            articles = await self.crawl_category(city=city, pages=pages)
            all_articles.extend(articles)

        if save_json and all_articles:
            self._save_json(all_articles, "all")

        self._print_summary(all_articles)
        return all_articles

    # ── 内部解析 ──────────────────────────────────────────────────────────────

    async def _parse_list_page(
        self, url: str, city_hint: str
    ) -> List[Dict[str, Any]]:
        """解析文章列表页"""
        html = await self.fetch_text(url, referer=self.BASE)
        if not html:
            return []

        try:
            soup = BeautifulSoup(html, "html.parser")
            results = []

            # WordPress 文章卡片：多种可能的选择器
            cards = (
                soup.find_all("article")
                or soup.find_all("div", class_=re.compile(r"post-card|article-card|entry-card"))
                or soup.find_all("li", class_=re.compile(r"post-item|article-item"))
            )

            for card in cards:
                try:
                    article = self._parse_card(card, city_hint, url)
                    if article:
                        results.append(article)
                except Exception as e:
                    logger.debug(f"  卡片解析失败: {e}")

            return results

        except Exception as e:
            logger.warning(f"  ⚠️  列表页解析失败: {e} [{url}]")
            return []

    def _parse_card(
        self, card: Any, city_hint: str, page_url: str
    ) -> Optional[Dict[str, Any]]:
        """解析单个文章卡片"""
        # 标题 + 链接
        title_el = (
            card.find("h2") or card.find("h3") or card.find("h1")
            or card.find(class_=re.compile(r"entry-title|post-title|article-title"))
        )
        if not title_el:
            return None

        a_el = title_el.find("a") or card.find("a", href=re.compile(r"/archives/\d+"))
        if not a_el:
            return None

        title = a_el.get_text(strip=True)
        if not title or len(title) < 5:
            return None

        article_url = a_el.get("href", "")
        if not article_url:
            return None
        if not article_url.startswith("http"):
            article_url = urljoin(self.BASE, article_url)

        # 摘要
        summary_el = card.find(class_=re.compile(r"entry-summary|excerpt|post-excerpt|description"))
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
        tag_els = card.find_all("a", rel=re.compile("tag")) or card.find_all(
            "a", class_=re.compile(r"tag|label|badge")
        )
        tags = [t.get_text(strip=True) for t in tag_els if t.get_text(strip=True)][:10]

        # 分类 category
        cat_els = card.find_all("a", rel=re.compile("category")) or card.find_all(
            "a", class_=re.compile(r"cat-link|category-link")
        )
        for c in cat_els:
            tags.append(c.get_text(strip=True))

        # 发布日期
        date_el = card.find("time") or card.find(class_=re.compile(r"published|date|post-date"))
        publish_date = ""
        if date_el:
            publish_date = date_el.get("datetime", "") or date_el.get_text(strip=True)
            publish_date = publish_date[:10] if publish_date else ""

        # 城市推断
        city_code = _infer_city(article_url + " " + page_url, title)
        if not city_code and city_hint != "all":
            city_code = city_hint

        # 类别推断
        category = _infer_category(title, tags)

        # 生成 ID
        article_id = re.search(r"/archives/(\d+)", article_url)
        art_id = f"letsgojp_{article_id.group(1)}" if article_id else f"letsgojp_{hash(article_url) & 0xFFFFFF}"

        return {
            "id": art_id,
            "source": "letsgojp",
            "title": title,
            "summary": summary,
            "city": city_code,
            "category": category,
            "tags": list(dict.fromkeys(tags)),  # 去重保序
            "publish_date": publish_date,
            "url": article_url,
            "image_url": image_url,
            "language": "zh-TW",
            "engagement": None,
            "crawled_at": datetime.utcnow().isoformat(),
        }

    def _save_json(self, articles: List[Dict[str, Any]], city: str) -> None:
        """保存 JSON 到 data/raw/letsgojp/"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fp = self.output_dir / f"letsgojp_{city}_{ts}.json"
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(
                {"meta": {"city": city, "total": len(articles), "source": "letsgojp"},
                 "articles": articles},
                f, ensure_ascii=False, indent=2,
            )
        logger.info(f"💾 已保存: {fp}")

    def _print_summary(self, articles: List[Dict[str, Any]]) -> None:
        """打印采集摘要"""
        print(f"\n🗾 樂吃購！日本: {len(articles)} 篇攻略")
        by_city: Dict[str, int] = {}
        by_cat: Dict[str, int] = {}
        for a in articles:
            by_city[a.get("city") or "unknown"] = by_city.get(a.get("city") or "unknown", 0) + 1
            by_cat[a.get("category") or "guide"] = by_cat.get(a.get("category") or "guide", 0) + 1
        print("  城市分布:", dict(sorted(by_city.items())))
        print("  类别分布:", dict(sorted(by_cat.items())))
        for a in articles[:5]:
            print(f"  📖 [{a.get('city','?')}] {a['title'][:50]}")
