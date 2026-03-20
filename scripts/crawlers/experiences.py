"""
ExperienceCrawler — 第二层活动体验爬虫
========================================
支持平台：
  - KKday   (中文站, HTTP + JSON API)
  - Klook   (Next.js SSR, __NEXT_DATA__ 提取)
  - VELTRA  (日本本地体验, HTTP HTML)
  - Rakuten Travel Experiences (HTTP HTML)

价格统一转换为 CNY。
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from scripts.crawlers.base import BaseCrawler

logger = logging.getLogger(__name__)

# ── 汇率 ─────────────────────────────────────────────────────────────────────

_CURRENCY_TO_CNY: Dict[str, float] = {
    "JPY": 0.048,
    "¥": 0.048,
    "USD": 7.25,
    "$": 7.25,
    "TWD": 0.22,
    "NT$": 0.22,
    "HKD": 0.93,
    "HK$": 0.93,
    "KRW": 0.0053,
    "CNY": 1.0,
    "￥": 1.0,
}

# ── 城市名映射 ────────────────────────────────────────────────────────────────

_KKDAY_CITY_SLUGS: Dict[str, str] = {
    "tokyo": "tokyo",
    "osaka": "osaka",
    "kyoto": "kyoto",
    "hokkaido": "hokkaido",
    "okinawa": "okinawa",
}

_KLOOK_CITY_IDS: Dict[str, str] = {
    "tokyo": "1-tokyo",
    "osaka": "2-osaka",
    "kyoto": "3-kyoto",
    "hokkaido": "4-hokkaido",
    "okinawa": "71-okinawa",
}

_VELTRA_CITY_SLUGS: Dict[str, str] = {
    "tokyo": "tokyo",
    "osaka": "osaka",
    "kyoto": "kyoto",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def _convert_price(amount: Any, currency: str) -> Optional[float]:
    """将价格转换为 CNY，失败返回 None"""
    try:
        rate = _CURRENCY_TO_CNY.get(currency.upper(), None)
        if rate is None:
            rate = _CURRENCY_TO_CNY.get(currency, None)
        if rate is None:
            return None
        return round(float(amount) * rate, 2)
    except (TypeError, ValueError):
        return None


# ─────────────────────────────────────────────────────────────────────────────
# ExperienceCrawler
# ─────────────────────────────────────────────────────────────────────────────

class ExperienceCrawler(BaseCrawler):
    """多平台活动体验爬虫"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("delay_range", (1.5, 3.5))
        super().__init__(**kwargs)

    # ── KKday ─────────────────────────────────────────────────────────────────

    async def crawl_kkday(self, city: str, pages: int = 3) -> List[Dict]:
        """
        爬取 KKday 中文站某城市的体验列表。
        KKday 有 REST-like 接口：
          GET /api/products?city=<city>&lang=zh-cn&page=<n>
        """
        slug = _KKDAY_CITY_SLUGS.get(city, city)
        results: List[Dict] = []

        for page in range(1, pages + 1):
            url = f"https://www.kkday.com/zh-cn/city/{slug}"
            params: Dict[str, Any] = {
                "page": page,
                "lang": "zh-cn",
                "sort": "reviews",
            }
            headers = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Referer": "https://www.kkday.com/zh-cn/country/japan",
            }

            resp = await self.fetch(url, params=params, headers=headers)
            if not resp:
                logger.warning(f"KKday: 无响应 city={city} page={page}")
                break

            items = self._parse_kkday_html(resp.text, city)
            if not items:
                logger.info(f"KKday: city={city} page={page} 无数据，停止翻页")
                break

            results.extend(items)
            logger.info(f"KKday: city={city} page={page} 获取 {len(items)} 条")

        # 去重
        seen: set = set()
        unique: List[Dict] = []
        for item in results:
            key = item.get("url", item.get("name", ""))
            if key and key not in seen:
                seen.add(key)
                unique.append(item)

        self.stats.items_scraped += len(unique)
        return unique

    def _parse_kkday_html(self, html: str, city: str) -> List[Dict]:
        """解析 KKday 城市页 HTML"""
        soup = BeautifulSoup(html, "html.parser")
        items: List[Dict] = []

        # KKday 产品卡片：data-cy="product-card" 或 class 包含 "product-card"
        cards = soup.select("[data-cy='product-card'], .product-card, .kk-card")
        if not cards:
            # fallback：找包含价格的 article/div
            cards = soup.select("article.product, div.product-item, li.product-item")

        for card in cards:
            try:
                item = self._extract_kkday_card(card, city)
                if item:
                    items.append(item)
            except Exception as e:
                logger.warning(f"KKday 解析卡片失败: {e}")

        return items

    def _extract_kkday_card(self, card: Any, city: str) -> Optional[Dict]:
        """从单个 KKday 卡片提取数据"""
        # 名称
        name_el = (
            card.select_one("[data-cy='product-name']")
            or card.select_one(".product-name")
            or card.select_one("h3")
            or card.select_one("h2")
        )
        name = name_el.get_text(strip=True) if name_el else None
        if not name:
            return None

        # 链接
        link_el = card.select_one("a[href]")
        url = ""
        if link_el:
            href = link_el.get("href", "")
            url = href if href.startswith("http") else f"https://www.kkday.com{href}"

        # 价格（CNY，KKday 中文站直接是人民币）
        price_cny: Optional[float] = None
        price_el = (
            card.select_one("[data-cy='product-price']")
            or card.select_one(".price")
            or card.select_one(".kk-price")
        )
        if price_el:
            raw = re.sub(r"[^\d.]", "", price_el.get_text())
            try:
                price_cny = float(raw)
            except ValueError:
                pass

        # 评分
        rating: Optional[float] = None
        rating_el = card.select_one("[data-cy='product-rating'], .rating, .score")
        if rating_el:
            try:
                rating = float(re.sub(r"[^\d.]", "", rating_el.get_text()))
            except ValueError:
                pass

        # 评论数
        review_count: Optional[int] = None
        review_el = card.select_one("[data-cy='product-reviews'], .review-count, .reviews")
        if review_el:
            m = re.search(r"(\d[\d,]*)", review_el.get_text())
            if m:
                try:
                    review_count = int(m.group(1).replace(",", ""))
                except ValueError:
                    pass

        # 图片
        img_el = card.select_one("img[src], img[data-src]")
        image_url = ""
        if img_el:
            image_url = img_el.get("src") or img_el.get("data-src") or ""

        # 产品 ID
        prod_id = card.get("data-id") or card.get("data-product-id") or ""
        if not prod_id and url:
            m = re.search(r"/product/(\d+)", url)
            prod_id = m.group(1) if m else ""

        return {
            "id": f"kkday_{prod_id}" if prod_id else f"kkday_{hash(name) & 0xFFFFFF}",
            "source": "kkday",
            "name": name,
            "name_en": "",
            "city": city,
            "category": "attraction",
            "price_cny": price_cny,
            "original_price": price_cny,
            "original_currency": "CNY",
            "rating": rating,
            "review_count": review_count,
            "duration_hours": None,
            "is_refundable": None,
            "url": url,
            "image_url": image_url,
            "tags": [],
            "crawled_at": _now_iso(),
        }

    # ── Klook ─────────────────────────────────────────────────────────────────

    async def crawl_klook(self, city: str, pages: int = 3) -> List[Dict]:
        """
        爬取 Klook 中文站某城市体验列表。
        Klook 是 Next.js SSR，从 __NEXT_DATA__ 提取 JSON。
        """
        city_slug = _KLOOK_CITY_IDS.get(city, f"{city}-things-to-do")
        results: List[Dict] = []

        for page in range(1, pages + 1):
            url = f"https://www.klook.com/zh-CN/city/{city_slug}/"
            params: Dict[str, Any] = {"page": page}
            headers = {
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Referer": "https://www.klook.com/zh-CN/",
            }

            resp = await self.fetch(url, params=params, headers=headers)
            if not resp:
                logger.warning(f"Klook: 无响应 city={city} page={page}")
                break

            items = self._parse_klook_html(resp.text, city)
            if not items:
                logger.info(f"Klook: city={city} page={page} 无数据，停止翻页")
                break

            results.extend(items)
            logger.info(f"Klook: city={city} page={page} 获取 {len(items)} 条")

        seen: set = set()
        unique: List[Dict] = []
        for item in results:
            key = item.get("url", item.get("name", ""))
            if key and key not in seen:
                seen.add(key)
                unique.append(item)

        self.stats.items_scraped += len(unique)
        return unique

    def _parse_klook_html(self, html: str, city: str) -> List[Dict]:
        """从 Klook 页面提取 __NEXT_DATA__ 或 HTML 卡片"""
        # 尝试 __NEXT_DATA__
        m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)
        if m:
            try:
                data = json.loads(m.group(1))
                return self._extract_klook_next_data(data, city)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Klook __NEXT_DATA__ 解析失败: {e}")

        # fallback: HTML 解析
        return self._parse_klook_html_cards(html, city)

    def _extract_klook_next_data(self, data: Dict, city: str) -> List[Dict]:
        """从 Klook __NEXT_DATA__ JSON 提取活动列表"""
        items: List[Dict] = []
        try:
            # 路径可能多种，遍历常见路径
            props = data.get("props", {})
            page_props = props.get("pageProps", {})

            # 尝试多个可能的数据路径
            activity_list: List[Dict] = []
            for key in ("activityList", "activities", "products", "items"):
                val = page_props.get(key)
                if isinstance(val, list):
                    activity_list = val
                    break
                # 再往下找一层
                if isinstance(val, dict):
                    for k2 in ("list", "data", "items"):
                        inner = val.get(k2)
                        if isinstance(inner, list):
                            activity_list = inner
                            break

            for act in activity_list:
                try:
                    item = self._normalize_klook_activity(act, city)
                    if item:
                        items.append(item)
                except Exception as e:
                    logger.warning(f"Klook 活动解析失败: {e}")
        except Exception as e:
            logger.warning(f"Klook NEXT_DATA 结构解析失败: {e}")
        return items

    def _normalize_klook_activity(self, act: Dict, city: str) -> Optional[Dict]:
        """将 Klook 活动 JSON 归一化为标准格式"""
        name = act.get("title") or act.get("name") or act.get("activityName") or ""
        if not name:
            return None

        # 价格
        price_info = act.get("price") or act.get("priceInfo") or {}
        original_price: Optional[float] = None
        original_currency = "HKD"
        price_cny: Optional[float] = None

        if isinstance(price_info, dict):
            original_price = price_info.get("originalPrice") or price_info.get("price")
            original_currency = price_info.get("currency", "HKD")
        elif isinstance(price_info, (int, float)):
            original_price = float(price_info)

        if original_price is not None:
            price_cny = _convert_price(original_price, original_currency)

        # 评分
        rating = act.get("rating") or act.get("score")
        try:
            rating = float(rating) if rating else None
        except (TypeError, ValueError):
            rating = None

        review_count = act.get("reviewCount") or act.get("reviews") or act.get("commentCount")
        try:
            review_count = int(review_count) if review_count else None
        except (TypeError, ValueError):
            review_count = None

        activity_id = str(act.get("id") or act.get("activityId") or "")
        url_path = act.get("url") or act.get("href") or f"/zh-CN/activity/{activity_id}/"
        url = url_path if url_path.startswith("http") else f"https://www.klook.com{url_path}"

        image_url = ""
        img = act.get("image") or act.get("coverImage") or act.get("thumbnail")
        if isinstance(img, str):
            image_url = img
        elif isinstance(img, dict):
            image_url = img.get("url") or img.get("src") or ""

        tags = act.get("tags") or act.get("labels") or []
        if not isinstance(tags, list):
            tags = []
        tags = [t if isinstance(t, str) else t.get("name", "") for t in tags]

        return {
            "id": f"klook_{activity_id}" if activity_id else f"klook_{hash(name) & 0xFFFFFF}",
            "source": "klook",
            "name": name,
            "name_en": act.get("titleEn") or "",
            "city": city,
            "category": "attraction",
            "price_cny": price_cny,
            "original_price": original_price,
            "original_currency": original_currency,
            "rating": rating,
            "review_count": review_count,
            "duration_hours": None,
            "is_refundable": act.get("isRefundable"),
            "url": url,
            "image_url": image_url,
            "tags": [t for t in tags if t],
            "crawled_at": _now_iso(),
        }

    def _parse_klook_html_cards(self, html: str, city: str) -> List[Dict]:
        """Klook HTML fallback 解析"""
        soup = BeautifulSoup(html, "html.parser")
        items: List[Dict] = []
        cards = soup.select(".activity-card, .product-card, [class*='ActivityCard'], [class*='activityCard']")

        for card in cards:
            try:
                name_el = card.select_one("h3, h2, [class*='title'], [class*='Title']")
                name = name_el.get_text(strip=True) if name_el else None
                if not name:
                    continue

                link_el = card.select_one("a[href]")
                href = link_el.get("href", "") if link_el else ""
                url = href if href.startswith("http") else f"https://www.klook.com{href}"

                price_el = card.select_one("[class*='price'], [class*='Price']")
                price_cny: Optional[float] = None
                if price_el:
                    raw = re.sub(r"[^\d.]", "", price_el.get_text())
                    try:
                        hkd_price = float(raw)
                        price_cny = _convert_price(hkd_price, "HKD")
                    except ValueError:
                        pass

                items.append({
                    "id": f"klook_{hash(name) & 0xFFFFFF}",
                    "source": "klook",
                    "name": name,
                    "name_en": "",
                    "city": city,
                    "category": "attraction",
                    "price_cny": price_cny,
                    "original_price": None,
                    "original_currency": "HKD",
                    "rating": None,
                    "review_count": None,
                    "duration_hours": None,
                    "is_refundable": None,
                    "url": url,
                    "image_url": "",
                    "tags": [],
                    "crawled_at": _now_iso(),
                })
            except Exception as e:
                logger.warning(f"Klook HTML 卡片解析失败: {e}")

        return items

    # ── VELTRA ────────────────────────────────────────────────────────────────

    async def crawl_veltra(self, city: str, pages: int = 3) -> List[Dict]:
        """
        爬取 VELTRA 日本体验列表。
        价格为 JPY，需转换为 CNY。
        """
        slug = _VELTRA_CITY_SLUGS.get(city, city)
        results: List[Dict] = []

        for page in range(1, pages + 1):
            url = f"https://www.veltra.com/en/asia/japan/{slug}/"
            params: Dict[str, Any] = {"page": page}
            headers = {
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.veltra.com/en/asia/japan/",
            }

            resp = await self.fetch(url, params=params, headers=headers)
            if not resp:
                logger.warning(f"VELTRA: 无响应 city={city} page={page}")
                break

            items = self._parse_veltra_html(resp.text, city)
            if not items:
                logger.info(f"VELTRA: city={city} page={page} 无数据，停止翻页")
                break

            results.extend(items)
            logger.info(f"VELTRA: city={city} page={page} 获取 {len(items)} 条")

        seen: set = set()
        unique: List[Dict] = []
        for item in results:
            key = item.get("url", item.get("name", ""))
            if key and key not in seen:
                seen.add(key)
                unique.append(item)

        self.stats.items_scraped += len(unique)
        return unique

    def _parse_veltra_html(self, html: str, city: str) -> List[Dict]:
        """解析 VELTRA 列表页 — 基于 [data-package-id] 容器"""
        soup = BeautifulSoup(html, "html.parser")
        items: List[Dict] = []

        # VELTRA 每个活动卡片有 data-package-id 属性
        cards = soup.select("[data-package-id]")
        if not cards:
            # fallback: 旧版选择器
            cards = soup.select(".activity-card, .product-card, article")

        for card in cards:
            try:
                item = self._extract_veltra_card(card, city)
                if item:
                    items.append(item)
            except Exception as e:
                logger.warning(f"VELTRA 解析卡片失败: {e}")

        return items

    def _extract_veltra_card(self, card: Any, city: str) -> Optional[Dict]:
        """
        提取 VELTRA 单卡片数据。
        card-body 文本格式: "活动名称|评分|(评论数)|USD|价格"
        """
        # 包 ID
        package_id = card.get("data-package-id", "")

        # 链接
        link_el = card.select_one('a[href*="/a/"]')
        href = link_el.get("href", "") if link_el else ""
        url = href if href.startswith("http") else f"https://www.veltra.com{href}"

        # 从 card-body 提取: "名称|评分|(评论数)|USD|97.13"
        body = card.select_one(".card-body")
        if not body:
            return None

        text_parts = [t.strip() for t in body.get_text(separator="|", strip=True).split("|") if t.strip()]
        if not text_parts:
            return None

        name = text_parts[0] if text_parts else None
        if not name or len(name) < 3:
            return None

        # 解析评分和评论数
        rating: Optional[float] = None
        review_count: Optional[int] = None
        original_price: Optional[float] = None
        original_currency = "USD"
        price_cny: Optional[float] = None

        for part in text_parts[1:]:
            # 评分: "4.97"
            if re.match(r"^\d\.\d+$", part):
                try:
                    rating = float(part)
                except ValueError:
                    pass
            # 评论数: "(193)"
            elif re.match(r"^\((\d[\d,]*)\)$", part):
                m = re.match(r"\((\d[\d,]*)\)", part)
                if m:
                    review_count = int(m.group(1).replace(",", ""))
            # 货币: "USD" / "JPY"
            elif part in ("USD", "JPY", "EUR", "CNY"):
                original_currency = part
            # 价格: "97.13"
            elif re.match(r"^[\d,]+\.?\d*$", part):
                try:
                    original_price = float(part.replace(",", ""))
                except ValueError:
                    pass

        # 转换价格到 CNY
        if original_price is not None:
            price_cny = _convert_price(original_price, original_currency)

        # 时长 — 从额外信息提取
        duration_hours: Optional[float] = None
        dur_el = card.select_one("[class*='duration'], [class*='time']")
        if dur_el:
            dur_text = dur_el.get_text()
            m = re.search(r"(\d+(?:\.\d+)?)\s*(?:hour|hr|h)", dur_text, re.I)
            if m:
                try:
                    duration_hours = float(m.group(1))
                except ValueError:
                    pass

        img_el = card.select_one("img[src], img[data-src]")
        image_url = ""
        if img_el:
            image_url = img_el.get("src") or img_el.get("data-src") or ""

        # 类别
        category = "attraction"
        cat_el = card.select_one(".category, .tag, [class*='category']")
        if cat_el:
            cat_text = cat_el.get_text(strip=True).lower()
            if "food" in cat_text or "restaurant" in cat_text:
                category = "food"
            elif "tour" in cat_text:
                category = "tour"
            elif "transport" in cat_text:
                category = "transport"
            elif "culture" in cat_text or "art" in cat_text:
                category = "culture"

        return {
            "id": f"veltra_{hash(url or name) & 0xFFFFFF}",
            "source": "veltra",
            "name": name,
            "name_en": name,
            "city": city,
            "category": category,
            "price_cny": price_cny,
            "original_price": original_price,
            "original_currency": "JPY",
            "rating": rating,
            "review_count": review_count,
            "duration_hours": duration_hours,
            "is_refundable": None,
            "url": url,
            "image_url": image_url,
            "tags": [],
            "crawled_at": _now_iso(),
        }

    # ── Rakuten Travel Experiences ────────────────────────────────────────────

    async def crawl_rakuten(self, city: str, pages: int = 3) -> List[Dict]:
        """
        爬取 Rakuten Travel Experiences。
        价格为 JPY，需转换为 CNY。
        """
        results: List[Dict] = []
        city_map = {
            "tokyo": "tokyo",
            "osaka": "osaka",
            "kyoto": "kyoto",
        }
        city_slug = city_map.get(city, city)

        for page in range(1, pages + 1):
            url = "https://experiences.travel.rakuten.co.jp/search"
            params: Dict[str, Any] = {
                "area": city_slug,
                "page": page,
                "lang": "en",
            }
            headers = {
                "Accept-Language": "ja-JP,ja;q=0.9,en;q=0.8",
                "Referer": "https://experiences.travel.rakuten.co.jp/",
            }

            resp = await self.fetch(url, params=params, headers=headers)
            if not resp:
                logger.warning(f"Rakuten: 无响应 city={city} page={page}")
                break

            items = self._parse_rakuten_html(resp.text, city)
            if not items:
                logger.info(f"Rakuten: city={city} page={page} 无数据，停止翻页")
                break

            results.extend(items)
            logger.info(f"Rakuten: city={city} page={page} 获取 {len(items)} 条")

        seen: set = set()
        unique: List[Dict] = []
        for item in results:
            key = item.get("url", item.get("name", ""))
            if key and key not in seen:
                seen.add(key)
                unique.append(item)

        self.stats.items_scraped += len(unique)
        return unique

    def _parse_rakuten_html(self, html: str, city: str) -> List[Dict]:
        """解析 Rakuten 体验列表页"""
        soup = BeautifulSoup(html, "html.parser")
        items: List[Dict] = []

        cards = soup.select(".experience-card, .plan-card, .item-card, [class*='ExperienceCard']")
        if not cards:
            cards = soup.select("article, li.plan-item, .plan-list li")

        for card in cards:
            try:
                item = self._extract_rakuten_card(card, city)
                if item:
                    items.append(item)
            except Exception as e:
                logger.warning(f"Rakuten 解析卡片失败: {e}")

        return items

    def _extract_rakuten_card(self, card: Any, city: str) -> Optional[Dict]:
        """提取 Rakuten 单卡片数据"""
        name_el = card.select_one("h3, h2, .plan-name, .experience-name, .title")
        name = name_el.get_text(strip=True) if name_el else None
        if not name:
            return None

        link_el = card.select_one("a[href]")
        href = link_el.get("href", "") if link_el else ""
        url = href if href.startswith("http") else f"https://experiences.travel.rakuten.co.jp{href}"

        original_price: Optional[float] = None
        price_cny: Optional[float] = None
        price_el = card.select_one(".price, .amount, [class*='price'], [class*='Price']")
        if price_el:
            raw = re.sub(r"[^\d]", "", price_el.get_text())
            try:
                original_price = float(raw)
                price_cny = _convert_price(original_price, "JPY")
            except ValueError:
                pass

        rating: Optional[float] = None
        rating_el = card.select_one(".rating, .score, [class*='rating']")
        if rating_el:
            try:
                rating = float(re.sub(r"[^\d.]", "", rating_el.get_text()))
            except ValueError:
                pass

        img_el = card.select_one("img[src], img[data-src]")
        image_url = ""
        if img_el:
            image_url = img_el.get("src") or img_el.get("data-src") or ""

        return {
            "id": f"rakuten_{hash(url or name) & 0xFFFFFF}",
            "source": "rakuten",
            "name": name,
            "name_en": name,
            "city": city,
            "category": "attraction",
            "price_cny": price_cny,
            "original_price": original_price,
            "original_currency": "JPY",
            "rating": rating,
            "review_count": None,
            "duration_hours": None,
            "is_refundable": None,
            "url": url,
            "image_url": image_url,
            "tags": [],
            "crawled_at": _now_iso(),
        }

    # ── 汇总入口 ──────────────────────────────────────────────────────────────

    async def crawl_all(
        self,
        cities: List[str] = None,
        sources: List[str] = None,
        pages: int = 3,
    ) -> List[Dict]:
        """
        爬取所有平台、所有城市的体验数据。

        Args:
            cities:  城市列表，默认 ["tokyo", "osaka", "kyoto"]
            sources: 平台列表，默认全部 ["kkday", "klook", "veltra", "rakuten"]
            pages:   每个城市每平台最多爬取页数
        """
        if cities is None:
            cities = ["tokyo", "osaka", "kyoto"]
        if sources is None:
            sources = ["kkday", "klook", "veltra", "rakuten"]

        all_results: List[Dict] = []

        for city in cities:
            for source in sources:
                logger.info(f"开始爬取 {source.upper()} city={city}")
                try:
                    if source == "kkday":
                        items = await self.crawl_kkday(city, pages=pages)
                    elif source == "klook":
                        items = await self.crawl_klook(city, pages=pages)
                    elif source == "veltra":
                        items = await self.crawl_veltra(city, pages=pages)
                    elif source == "rakuten":
                        items = await self.crawl_rakuten(city, pages=pages)
                    else:
                        logger.warning(f"未知平台: {source}")
                        continue

                    logger.info(f"✅ {source.upper()} city={city}: {len(items)} 条")
                    all_results.extend(items)
                except Exception as e:
                    logger.error(f"❌ {source.upper()} city={city} 异常: {e}")

        # 跨平台粗去重：name + city
        seen_key: set = set()
        unique: List[Dict] = []
        for item in all_results:
            key = f"{item.get('name', '')}|{item.get('city', '')}"
            if key not in seen_key:
                seen_key.add(key)
                unique.append(item)

        logger.info(f"📦 总计: {len(all_results)} 条 → 去重后 {len(unique)} 条")
        return unique
