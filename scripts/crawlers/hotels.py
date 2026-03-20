"""
HotelCrawler — 多平台酒店数据采集器 (Playwright)
==================================================
覆盖四大平台，专为日本旅行场景设计：

  1. Booking.com  — 国际用户首选，booking_score 权威
  2. 携程/Trip.com — 中国用户首选，人民币直报价
  3. Agoda        — 东南亚/日本强势，经常有独家低价
  4. Jalan        — 日本本土最大，旅馆/温泉酒店覆盖最全

采集字段（对齐 Hotel 模型）：
  基础: name_zh/ja/en, city_code, address_ja, lat, lng
  分类: hotel_type, star_rating, chain_name, price_tier
  设施: amenities, is_family_friendly, is_pet_friendly
  评分: google_rating, booking_score
  价格: typical_price_min_jpy
  外部ID: booking_hotel_id, agoda_hotel_id

依赖:
  pip install playwright && python -m playwright install chromium

用法:
  python scripts/hotel_crawl.py --city tokyo --platform all
  python scripts/hotel_crawl.py --city kyoto --platform booking ctrip --pages 2
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from scripts.crawlers.playwright_base import PlaywrightCrawler

logger = logging.getLogger(__name__)

# ── 城市映射 ─────────────────────────────────────────────────────────────────

CITY_CONFIG: Dict[str, Dict[str, Any]] = {
    "tokyo": {
        "name_zh": "东京", "name_ja": "東京",
        "booking_dest": "-246227",          # Booking dest_id
        "ctrip_id": "735",                  # 携程城市 ID
        "agoda_city": "tokyo",
        "jalan_area": "130000",             # Jalan 都道府県コード
    },
    "osaka": {
        "name_zh": "大阪", "name_ja": "大阪",
        "booking_dest": "-240905",
        "ctrip_id": "293",
        "agoda_city": "osaka",
        "jalan_area": "270000",
    },
    "kyoto": {
        "name_zh": "京都", "name_ja": "京都",
        "booking_dest": "-235402",
        "ctrip_id": "430",
        "agoda_city": "kyoto",
        "jalan_area": "260000",
    },
    "nara": {
        "name_zh": "奈良", "name_ja": "奈良",
        "booking_dest": "-240687",
        "ctrip_id": "1424",
        "agoda_city": "nara",
        "jalan_area": "290000",
    },
    "hakone": {
        "name_zh": "箱根", "name_ja": "箱根",
        "booking_dest": "-228221",
        "ctrip_id": "58197",
        "agoda_city": "hakone",
        "jalan_area": "140602",
    },
    "sapporo": {
        "name_zh": "札幌", "name_ja": "札幌",
        "booking_dest": "-243562",
        "ctrip_id": "709",
        "agoda_city": "sapporo",
        "jalan_area": "011002",
    },
    "fukuoka": {
        "name_zh": "福冈", "name_ja": "福岡",
        "booking_dest": "-227265",
        "ctrip_id": "713",
        "agoda_city": "fukuoka",
        "jalan_area": "400000",
    },
    "okinawa": {
        "name_zh": "冲绳", "name_ja": "沖縄",
        "booking_dest": "-5457485",
        "ctrip_id": "21658",
        "agoda_city": "okinawa",
        "jalan_area": "470000",
    },
    "kamakura": {
        "name_zh": "镰仓", "name_ja": "鎌倉",
        "booking_dest": "-232905",
        "ctrip_id": "58200",
        "agoda_city": "kamakura",
        "jalan_area": "140204",
    },
    "kanazawa": {
        "name_zh": "金泽", "name_ja": "金沢",
        "booking_dest": "-232651",
        "ctrip_id": "1425",
        "agoda_city": "kanazawa",
        "jalan_area": "170201",
    },
    "kobe": {
        "name_zh": "神户", "name_ja": "神戸",
        "booking_dest": "-234249",
        "ctrip_id": "651",
        "agoda_city": "kobe",
        "jalan_area": "280110",
    },
    "nagoya": {
        "name_zh": "名古屋", "name_ja": "名古屋",
        "booking_dest": "-240506",
        "ctrip_id": "714",
        "agoda_city": "nagoya",
        "jalan_area": "230000",
    },
}

# ── 酒店类型推断 ─────────────────────────────────────────────────────────────

def _infer_hotel_type(name: str, amenities: List[str] = None) -> str:
    """从名称和设施推断酒店类型"""
    name_lower = name.lower()
    amenities_str = " ".join(amenities or []).lower()
    combined = f"{name_lower} {amenities_str}"

    if any(k in combined for k in ["旅館", "ryokan", "旅馆"]):
        return "ryokan"
    if any(k in combined for k in ["カプセル", "capsule", "胶囊"]):
        return "capsule"
    if any(k in combined for k in ["ホステル", "hostel", "青旅", "民宿", "guesthouse"]):
        return "hostel"
    if any(k in combined for k in ["リゾート", "resort", "度假"]):
        return "resort"
    if any(k in combined for k in ["ビジネス", "business", "东横", "toyoko", "apa ", "dormy",
                                     "route inn", "comfort", "super hotel"]):
        return "business"
    return "city_hotel"


def _infer_price_tier(price_jpy: Optional[int]) -> str:
    """从价格推断档位"""
    if price_jpy is None:
        return "mid"
    if price_jpy < 5000:
        return "budget"
    if price_jpy < 15000:
        return "mid"
    if price_jpy < 40000:
        return "premium"
    return "luxury"


class HotelCrawler(PlaywrightCrawler):
    """
    多平台酒店爬虫（Playwright）。

    自动驱动 Chromium 浏览器访问 Booking/携程/Agoda/Jalan，
    解析搜索结果列表页，提取酒店数据。
    """

    def __init__(
        self,
        platforms: Optional[List[str]] = None,
        check_in_offset_days: int = 30,
        nights: int = 2,
        output_dir: str = "data/hotels_raw",
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("delay_range", (2.0, 4.0))
        super().__init__(**kwargs)

        self.platforms = platforms or ["booking", "ctrip", "agoda", "jalan"]
        self.check_in = date.today() + timedelta(days=check_in_offset_days)
        self.check_out = self.check_in + timedelta(days=nights)
        self.output_dir = Path(output_dir)

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Booking.com
    # ─────────────────────────────────────────────────────────────────────────

    async def crawl_booking(
        self, city_code: str, max_pages: int = 2
    ) -> List[Dict[str, Any]]:
        """Booking.com 酒店列表采集"""
        config = CITY_CONFIG.get(city_code, {})
        dest_id = config.get("booking_dest", "")
        city_name = config.get("name_zh", city_code)

        logger.info(f"🏨 [Booking] 采集 {city_name} ...")
        page = await self.new_page()
        results = []

        try:
            for pg in range(max_pages):
                offset = pg * 25
                url = (
                    f"https://www.booking.com/searchresults.zh-cn.html"
                    f"?dest_id={dest_id}&dest_type=city"
                    f"&checkin={self.check_in.isoformat()}"
                    f"&checkout={self.check_out.isoformat()}"
                    f"&group_adults=2&no_rooms=1"
                    f"&order=class&offset={offset}"
                )

                logger.info(f"  📄 Booking 第 {pg+1} 页")
                ok = await self.safe_goto(page, url, timeout=30000)
                if not ok:
                    break

                await self.random_delay()

                # 等待酒店卡片加载
                try:
                    await page.wait_for_selector(
                        "[data-testid='property-card']", timeout=15000
                    )
                except Exception:
                    logger.warning("  ⚠️  Booking 卡片加载超时")
                    break

                # 提取卡片
                cards = await page.query_selector_all("[data-testid='property-card']")
                logger.info(f"  找到 {len(cards)} 张卡片")

                for card in cards:
                    try:
                        hotel = await self._parse_booking_card(card, city_code)
                        if hotel:
                            results.append(hotel)
                    except Exception as e:
                        logger.debug(f"  解析 Booking 卡片失败: {e}")

                if len(cards) < 25:
                    break  # 最后一页

        finally:
            await page.close()

        logger.info(f"  ✅ [Booking] {city_name}: {len(results)} 家")
        return results

    # Booking 价格货币→JPY 粗算汇率
    _CURRENCY_TO_JPY = {
        "HK$": 19.0, "HKD": 19.0,
        "¥": 1.0, "￥": 1.0, "JPY": 1.0,
        "CN¥": 20.5, "CNY": 20.5, "RMB": 20.5,
        "US$": 150.0, "USD": 150.0, "$": 150.0,
        "€": 162.0, "EUR": 162.0,
        "£": 190.0, "GBP": 190.0,
        "₩": 0.11, "KRW": 0.11,
        "NT$": 4.8, "TWD": 4.8,
        "S$": 112.0, "SGD": 112.0,
    }

    async def _parse_booking_card(
        self, card: Any, city_code: str
    ) -> Optional[Dict[str, Any]]:
        """解析 Booking 酒店卡片"""

        # 名称
        name_el = await card.query_selector("[data-testid='title']")
        name = (await name_el.inner_text()).strip() if name_el else None
        if not name:
            return None

        # 链接 & booking_id
        link_el = await card.query_selector("a[data-testid='title-link']")
        link = await link_el.get_attribute("href") if link_el else ""
        booking_id = ""
        id_match = re.search(r'/hotel/jp/([^.?/]+)', link or "")
        if id_match:
            booking_id = id_match.group(1)

        # Booking 评分 (满分 10)
        score = None
        score_el = await card.query_selector("[data-testid='review-score']")
        if score_el:
            score_text = await score_el.inner_text()
            # 提取第一个浮点数（"评分9.0\n9.0\n好极了" → 9.0）
            m = re.search(r'(\d+\.?\d*)', score_text)
            if m:
                try:
                    s = float(m.group(1))
                    if 1.0 <= s <= 10.0:
                        score = s
                except (ValueError, TypeError):
                    pass

        # 评论数
        review_count = None
        if score_el:
            score_text = await score_el.inner_text()
            rc_match = re.search(r'([\d,]+)\s*条', score_text)
            if rc_match:
                review_count = int(rc_match.group(1).replace(",", ""))

        # 价格（处理多种货币）
        price_jpy = None
        price_raw = None
        price_el = await card.query_selector("[data-testid='price-and-discounted-price']")
        if price_el:
            price_text = await price_el.inner_text()
            price_raw = price_text.strip()

            # 解析货币和金额: "HK$ 6,086" / "¥ 13,631" / "US$ 85"
            currency_match = re.match(
                r'([A-Z]{2,3}\$?|[¥￥€£₩]|NT\$|S\$|HK\$|CN¥|US\$)\s*([\d,]+)',
                price_text.strip(),
            )
            if currency_match:
                currency_symbol = currency_match.group(1)
                amount = int(currency_match.group(2).replace(",", ""))
                rate = self._CURRENCY_TO_JPY.get(currency_symbol, 1.0)
                price_jpy = int(amount * rate)
            else:
                # 无货币符号，尝试纯数字
                nums = re.findall(r'[\d,]+', price_text)
                if nums:
                    price_jpy = int(nums[-1].replace(",", ""))

        # 2晚→1晚：检查 price-for-x-nights
        nights = 1
        nights_el = await card.query_selector("[data-testid='price-for-x-nights']")
        if nights_el:
            nights_text = await nights_el.inner_text()
            n_match = re.search(r'(\d+)\s*晚', nights_text)
            if n_match:
                nights = int(n_match.group(1))
        if price_jpy and nights > 1:
            price_jpy = price_jpy // nights  # 每晚价格

        # 星级：数 SVG 星星图标数量（每颗星是一个 svg）
        star = None
        star_container = await card.query_selector("[data-testid='rating-stars']")
        if star_container:
            svgs = await star_container.query_selector_all("svg")
            if svgs:
                star = float(len(svgs))
                if star > 5:
                    star = 5.0  # 最多5星

        # 地址/区域
        addr = ""
        addr_el = await card.query_selector("[data-testid='address'], [data-testid='address-link']")
        if addr_el:
            addr = (await addr_el.inner_text()).strip()

        # 距离
        distance = ""
        dist_el = await card.query_selector("[data-testid='distance']")
        if dist_el:
            distance = (await dist_el.inner_text()).strip()

        # 图片
        img = ""
        img_el = await card.query_selector("img[data-testid='image']")
        if img_el:
            img = await img_el.get_attribute("src") or ""

        hotel_type = _infer_hotel_type(name)

        return {
            "name_ja": name,
            "name_zh": "",
            "name_en": "",
            "city_code": city_code,
            "address_ja": addr,
            "distance_to_center": distance,
            "booking_hotel_id": booking_id,
            "booking_score": score,
            "booking_review_count": review_count,
            "booking_url": link,
            "star_rating": star,
            "hotel_type": hotel_type,
            "price_tier": _infer_price_tier(price_jpy),
            "typical_price_min_jpy": price_jpy,
            "price_raw": price_raw,
            "image_url": img,
            "source": "booking",
            "crawled_at": datetime.utcnow().isoformat(),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 2. 携程 (Trip.com)
    # ─────────────────────────────────────────────────────────────────────────

    async def crawl_ctrip(
        self, city_code: str, max_pages: int = 2
    ) -> List[Dict[str, Any]]:
        """携程酒店列表采集"""
        config = CITY_CONFIG.get(city_code, {})
        ctrip_id = config.get("ctrip_id", "")
        city_name = config.get("name_zh", city_code)

        logger.info(f"🏨 [携程] 采集 {city_name} ...")
        page = await self.new_page()
        results = []

        try:
            for pg in range(1, max_pages + 1):
                url = (
                    f"https://hotels.ctrip.com/hotels/list"
                    f"?countryId=68&city={ctrip_id}"
                    f"&checkin={self.check_in.isoformat()}"
                    f"&checkout={self.check_out.isoformat()}"
                    f"&optionId=1&optionType=Star"
                    f"&barCur498=0&page={pg}"
                )

                logger.info(f"  📄 携程 第 {pg} 页")
                ok = await self.safe_goto(page, url, timeout=30000)
                if not ok:
                    break

                await self.random_delay()

                # 等待酒店列表
                try:
                    await page.wait_for_selector(
                        "[class*='hotel-list'] [class*='list-card'], .hotel-info",
                        timeout=15000,
                    )
                except Exception:
                    logger.warning("  ⚠️  携程列表加载超时")
                    break

                # 提取酒店数据（从页面 JS 数据或 DOM）
                page_results = await self._parse_ctrip_page(page, city_code)
                results.extend(page_results)

                if len(page_results) < 20:
                    break

        finally:
            await page.close()

        logger.info(f"  ✅ [携程] {city_name}: {len(results)} 家")
        return results

    async def _parse_ctrip_page(
        self, page: Any, city_code: str
    ) -> List[Dict[str, Any]]:
        """解析携程酒店列表页"""
        results = []

        # 方式1: 尝试从 window.__NEXT_DATA__ 或类似全局变量提取 JSON
        try:
            json_data = await page.evaluate("""
                () => {
                    // 携程 SSR 数据
                    if (window.__NEXT_DATA__) return JSON.stringify(window.__NEXT_DATA__);
                    if (window.htlListData) return JSON.stringify(window.htlListData);
                    return null;
                }
            """)
            if json_data:
                data = json.loads(json_data)
                hotels = self._extract_ctrip_json(data, city_code)
                if hotels:
                    return hotels
        except Exception as e:
            logger.debug(f"  携程 JSON 提取失败: {e}")

        # 方式2: DOM 解析
        cards = await page.query_selector_all(
            "[class*='list-card'], [class*='hotel-card'], [class*='HotelCard']"
        )

        for card in cards:
            try:
                text = await card.inner_text()
                # 提取名称
                name_el = await card.query_selector("a[class*='name'], [class*='hotel-name']")
                name = (await name_el.inner_text()).strip() if name_el else ""
                if not name:
                    # 从文本的第一行提取
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    name = lines[0] if lines else ""

                if not name:
                    continue

                # 价格
                price_cny = None
                price_match = re.search(r'(?:¥|￥)\s*([\d,]+)', text)
                if price_match:
                    try:
                        price_cny = int(price_match.group(1).replace(",", ""))
                    except ValueError:
                        pass

                # 换算 JPY (粗算 1 CNY ≈ 20 JPY)
                price_jpy = int(price_cny * 20) if price_cny else None

                # 评分
                score = None
                score_match = re.search(r'(\d\.\d)\s*分', text)
                if score_match:
                    score = float(score_match.group(1))

                # 星级
                star = None
                star_match = re.search(r'(\d)\s*星', text)
                if star_match:
                    star = float(star_match.group(1))

                # 链接
                link_el = await card.query_selector("a[href*='hotel']")
                link = await link_el.get_attribute("href") if link_el else ""

                results.append({
                    "name_zh": name,
                    "name_ja": "",
                    "name_en": "",
                    "city_code": city_code,
                    "star_rating": star,
                    "hotel_type": _infer_hotel_type(name),
                    "price_tier": _infer_price_tier(price_jpy),
                    "typical_price_min_jpy": price_jpy,
                    "price_cny": price_cny,
                    "ctrip_score": score,
                    "ctrip_url": link if link and link.startswith("http") else f"https://hotels.ctrip.com{link}" if link else "",
                    "source": "ctrip",
                    "crawled_at": datetime.utcnow().isoformat(),
                })

            except Exception as e:
                logger.debug(f"  解析携程卡片失败: {e}")

        return results

    def _extract_ctrip_json(
        self, data: dict, city_code: str
    ) -> List[Dict[str, Any]]:
        """从携程 SSR JSON 数据中提取酒店"""
        results = []

        # 尝试多种数据路径
        hotel_list = (
            data.get("props", {}).get("pageProps", {}).get("hotelList", [])
            or data.get("hotelList", [])
            or data.get("data", {}).get("hotelList", [])
        )

        for h in hotel_list:
            name = h.get("hotelName", "") or h.get("name", "")
            if not name:
                continue

            price_cny = h.get("price", {}).get("amount") or h.get("lowestPrice")
            price_jpy = int(float(price_cny) * 20) if price_cny else None

            star = h.get("star") or h.get("starLevel")
            score = h.get("commentScore") or h.get("score")

            results.append({
                "name_zh": name,
                "name_ja": h.get("hotelNameEn", ""),
                "name_en": h.get("hotelNameEn", ""),
                "city_code": city_code,
                "address_ja": h.get("address", ""),
                "lat": h.get("lat"),
                "lng": h.get("lon") or h.get("lng"),
                "star_rating": float(star) if star else None,
                "hotel_type": _infer_hotel_type(name),
                "price_tier": _infer_price_tier(price_jpy),
                "typical_price_min_jpy": price_jpy,
                "price_cny": price_cny,
                "ctrip_score": float(score) if score else None,
                "ctrip_hotel_id": str(h.get("hotelId", "")),
                "image_url": h.get("picture", {}).get("url", "") if isinstance(h.get("picture"), dict) else h.get("picture", ""),
                "source": "ctrip",
                "crawled_at": datetime.utcnow().isoformat(),
            })

        return results

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Agoda
    # ─────────────────────────────────────────────────────────────────────────

    async def crawl_agoda(
        self, city_code: str, max_pages: int = 2
    ) -> List[Dict[str, Any]]:
        """Agoda 酒店列表采集"""
        config = CITY_CONFIG.get(city_code, {})
        agoda_city = config.get("agoda_city", city_code)
        city_name = config.get("name_zh", city_code)

        logger.info(f"🏨 [Agoda] 采集 {city_name} ...")
        page = await self.new_page()
        results = []

        try:
            for pg in range(1, max_pages + 1):
                url = (
                    f"https://www.agoda.com/zh-cn/search"
                    f"?city={agoda_city}&country=japan"
                    f"&checkIn={self.check_in.isoformat()}"
                    f"&checkOut={self.check_out.isoformat()}"
                    f"&rooms=1&adults=2&children=0"
                    f"&sort=priceLowToHigh&page={pg}"
                )

                logger.info(f"  📄 Agoda 第 {pg} 页")
                ok = await self.safe_goto(page, url, timeout=30000)
                if not ok:
                    break

                await self.random_delay()

                # 等待酒店卡片
                try:
                    await page.wait_for_selector(
                        "[data-selenium='hotel-item'], [class*='PropertyCard']",
                        timeout=15000,
                    )
                except Exception:
                    logger.warning("  ⚠️  Agoda 列表加载超时")
                    break

                cards = await page.query_selector_all(
                    "[data-selenium='hotel-item'], [class*='PropertyCard']"
                )
                logger.info(f"  找到 {len(cards)} 张卡片")

                for card in cards:
                    try:
                        hotel = await self._parse_agoda_card(card, city_code)
                        if hotel:
                            results.append(hotel)
                    except Exception as e:
                        logger.debug(f"  解析 Agoda 卡片失败: {e}")

                if len(cards) < 20:
                    break

        finally:
            await page.close()

        logger.info(f"  ✅ [Agoda] {city_name}: {len(results)} 家")
        return results

    async def _parse_agoda_card(
        self, card: Any, city_code: str
    ) -> Optional[Dict[str, Any]]:
        """解析 Agoda 酒店卡片"""
        text = await card.inner_text()

        # 名称
        name_el = (
            await card.query_selector("[data-selenium='hotel-name']")
            or await card.query_selector("h3")
            or await card.query_selector("[class*='PropertyName']")
        )
        name = (await name_el.inner_text()).strip() if name_el else ""
        if not name:
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            name = lines[0] if lines else ""
        if not name:
            return None

        # 链接 & ID
        link_el = await card.query_selector("a[href*='/hotel/']")
        link = await link_el.get_attribute("href") if link_el else ""
        agoda_id = ""
        id_match = re.search(r'/hotel/[^/]+/([^.?/]+)', link or "")
        if id_match:
            agoda_id = id_match.group(1)

        # 价格
        price_jpy = None
        price_match = re.search(r'(?:¥|￥|JPY)\s*([\d,]+)', text)
        if price_match:
            try:
                price_jpy = int(price_match.group(1).replace(",", ""))
            except ValueError:
                pass
        if not price_jpy:
            # Agoda 有时用 CNY 显示
            cny_match = re.search(r'(?:CN¥|RMB)\s*([\d,]+)', text)
            if cny_match:
                try:
                    price_jpy = int(float(cny_match.group(1).replace(",", "")) * 20)
                except ValueError:
                    pass

        # 评分
        score = None
        score_match = re.search(r'(\d+\.?\d*)\s*/\s*10', text)
        if not score_match:
            score_match = re.search(r'(\d\.\d)\s*(?:分|/)', text)
        if score_match:
            score = float(score_match.group(1))

        # 星级
        star = None
        star_els = await card.query_selector_all("[class*='star'] svg, [class*='Star']")
        if star_els:
            star = float(len(star_els))
        if not star:
            star_match = re.search(r'(\d)\s*(?:星|star)', text, re.IGNORECASE)
            if star_match:
                star = float(star_match.group(1))

        # 区域
        area_el = await card.query_selector("[data-selenium='area-city-text']")
        area = (await area_el.inner_text()).strip() if area_el else ""

        return {
            "name_ja": name,
            "name_zh": "",
            "name_en": "",
            "city_code": city_code,
            "address_ja": area,
            "agoda_hotel_id": agoda_id,
            "agoda_score": score,
            "agoda_url": f"https://www.agoda.com{link}" if link and not link.startswith("http") else link,
            "star_rating": star,
            "hotel_type": _infer_hotel_type(name),
            "price_tier": _infer_price_tier(price_jpy),
            "typical_price_min_jpy": price_jpy,
            "source": "agoda",
            "crawled_at": datetime.utcnow().isoformat(),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Jalan (じゃらん)
    # ─────────────────────────────────────────────────────────────────────────

    async def crawl_jalan(
        self, city_code: str, max_pages: int = 2
    ) -> List[Dict[str, Any]]:
        """Jalan (じゃらん) 酒店列表采集 — 旅馆/温泉酒店最强"""
        config = CITY_CONFIG.get(city_code, {})
        jalan_area = config.get("jalan_area", "")
        city_name = config.get("name_zh", city_code)

        logger.info(f"🏨 [Jalan] 采集 {city_name} ...")
        page = await self.new_page()
        results = []

        try:
            for pg in range(1, max_pages + 1):
                ci = self.check_in
                co = self.check_out
                url = (
                    f"https://www.jalan.net/yad/list.html"
                    f"?kenCd={jalan_area[:2]}&lrgCd={jalan_area[2:4]}"
                    f"&smlCd={jalan_area[4:6] if len(jalan_area) > 4 else ''}"
                    f"&dateUndecided=1"
                    f"&adultNum=2&roomCount=1"
                    f"&distCd=01&page={pg}"
                )

                logger.info(f"  📄 Jalan 第 {pg} 页")
                ok = await self.safe_goto(page, url, timeout=30000)
                if not ok:
                    break

                await self.random_delay()

                # Jalan 的酒店卡片
                try:
                    await page.wait_for_selector(
                        ".p-searchResultItem, .cassetteitem, [class*='result-item']",
                        timeout=15000,
                    )
                except Exception:
                    logger.warning("  ⚠️  Jalan 列表加载超时")
                    break

                cards = await page.query_selector_all(
                    ".p-searchResultItem, .cassetteitem, [class*='result-item']"
                )
                logger.info(f"  找到 {len(cards)} 张卡片")

                for card in cards:
                    try:
                        hotel = await self._parse_jalan_card(card, city_code)
                        if hotel:
                            results.append(hotel)
                    except Exception as e:
                        logger.debug(f"  解析 Jalan 卡片失败: {e}")

                if len(cards) < 20:
                    break

        finally:
            await page.close()

        logger.info(f"  ✅ [Jalan] {city_name}: {len(results)} 家")
        return results

    async def _parse_jalan_card(
        self, card: Any, city_code: str
    ) -> Optional[Dict[str, Any]]:
        """解析 Jalan 酒店卡片"""
        text = await card.inner_text()

        # 名称
        name_el = (
            await card.query_selector("h2 a, .p-searchResultItem__name a, [class*='hotel-name'] a")
        )
        name_ja = (await name_el.inner_text()).strip() if name_el else ""
        if not name_ja:
            return None

        # 链接
        link = await name_el.get_attribute("href") if name_el else ""
        if link and not link.startswith("http"):
            link = f"https://www.jalan.net{link}"

        # 价格（日元）
        price_jpy = None
        price_match = re.search(r'([\d,]+)\s*円', text)
        if price_match:
            try:
                price_jpy = int(price_match.group(1).replace(",", ""))
            except ValueError:
                pass

        # 评分 (Jalan 满分 5.0)
        score = None
        score_match = re.search(r'(\d\.\d)\s*(?:点|/)', text)
        if score_match:
            score = float(score_match.group(1))

        # 评论数
        review_count = None
        review_match = re.search(r'(\d+)\s*件', text)
        if review_match:
            review_count = int(review_match.group(1))

        # 图片
        img_el = await card.query_selector("img[src*='jalan']")
        img = await img_el.get_attribute("src") if img_el else ""

        hotel_type = _infer_hotel_type(name_ja)

        return {
            "name_ja": name_ja,
            "name_zh": "",
            "name_en": "",
            "city_code": city_code,
            "hotel_type": hotel_type,
            "star_rating": None,
            "price_tier": _infer_price_tier(price_jpy),
            "typical_price_min_jpy": price_jpy,
            "jalan_score": score,
            "jalan_review_count": review_count,
            "jalan_url": link,
            "image_url": img,
            "source": "jalan",
            "crawled_at": datetime.utcnow().isoformat(),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 统一入口
    # ─────────────────────────────────────────────────────────────────────────

    async def crawl_city(
        self,
        city_code: str,
        max_pages: int = 2,
        save_json: bool = True,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        采集指定城市所有平台的酒店数据。

        Returns:
            {"booking": [...], "ctrip": [...], "agoda": [...], "jalan": [...]}
        """
        if city_code not in CITY_CONFIG:
            logger.error(f"❌ 未知城市: {city_code}，支持: {list(CITY_CONFIG.keys())}")
            return {}

        city_name = CITY_CONFIG[city_code]["name_zh"]
        logger.info(
            f"🏙️  采集 {city_name} 酒店 | "
            f"平台: {', '.join(self.platforms)} | "
            f"入住: {self.check_in} 退房: {self.check_out}"
        )

        all_results: Dict[str, List[Dict[str, Any]]] = {}

        platform_methods = {
            "booking": self.crawl_booking,
            "ctrip": self.crawl_ctrip,
            "agoda": self.crawl_agoda,
            "jalan": self.crawl_jalan,
        }

        for platform in self.platforms:
            method = platform_methods.get(platform)
            if not method:
                logger.warning(f"⚠️  未知平台: {platform}")
                continue

            try:
                hotels = await method(city_code, max_pages=max_pages)
                all_results[platform] = hotels
            except Exception as e:
                logger.error(f"❌ [{platform}] 采集失败: {e}")
                all_results[platform] = []

        # 保存
        if save_json:
            self._save_results(city_code, all_results)

        # 打印摘要
        total = sum(len(v) for v in all_results.values())
        print(f"\n{'='*60}")
        print(f"🏨 {city_name} 酒店采集完成 | 共 {total} 家")
        print(f"-" * 60)
        for platform, hotels in all_results.items():
            if hotels:
                prices = [h.get("typical_price_min_jpy") for h in hotels if h.get("typical_price_min_jpy")]
                avg_price = sum(prices) // len(prices) if prices else 0
                print(f"  {platform:10s}  {len(hotels):>3d} 家  均价 ¥{avg_price:,}/晚")
            else:
                print(f"  {platform:10s}    0 家")
        print(f"{'='*60}")

        return all_results

    def _save_results(
        self,
        city_code: str,
        all_results: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """保存到 JSON"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        filepath = self.output_dir / f"hotels_{city_code}_{ts}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "meta": {
                        "city_code": city_code,
                        "check_in": self.check_in.isoformat(),
                        "check_out": self.check_out.isoformat(),
                        "crawled_at": datetime.utcnow().isoformat(),
                        "platforms": {k: len(v) for k, v in all_results.items()},
                    },
                    "hotels": all_results,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        logger.info(f"💾 已保存: {filepath}")
