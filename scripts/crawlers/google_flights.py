"""
GoogleFlightsCrawler — Google Flights 机票数据采集器
=====================================================
Google Flights 数据最全（GDS 底层），覆盖全球所有航司。

三种模式：
  1. Lite 模式（默认）— 解析 Google Flights URL 的 SSR 数据，不需要浏览器
  2. Full 模式        — 用 Playwright 自动化交互搜索，数据最完整
  3. Calendar 模式    — 用 Playwright 读取价格日历，获取一整月最低价

用法：
  async with GoogleFlightsCrawler() as crawler:
      # Lite: 只需 httpx（数据有限）
      results = await crawler.search_flights("SHA", "TYO", "2026-05-01")

      # Full: 需要 playwright（数据最完整，包含航司/时段/经停等）
      results = await crawler.search_flights_full("SHA", "TYO", "2025-07-20", "2025-07-26")

      # Calendar: 获取每日最低价（价格趋势分析）
      calendar = await crawler.search_calendar_prices("SHA", "TYO", "2025-07")
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from scripts.crawlers.base import BaseCrawler

logger = logging.getLogger(__name__)

# Google Flights 参数编码
CABIN_CLASS = {"economy": "1", "premium_economy": "2", "business": "3", "first": "4"}


class GoogleFlightsCrawler(BaseCrawler):
    """
    Google Flights 爬虫。

    Lite 模式利用 Google Flights 的 SSR/批量数据接口，
    从服务端渲染的 HTML 中提取航班数据。
    """

    BASE = "https://www.google.com/travel/flights"

    # ─────────────────────────────────────────────────────────────────────────
    # 城市名映射（用于自动化 UI 交互）
    # ─────────────────────────────────────────────────────────────────────────

    _CITY_NAMES: Dict[str, str] = {
        "SHA": "上海", "PVG": "上海",
        "PEK": "北京", "PKX": "北京", "BJS": "北京",
        "CAN": "广州", "SZX": "深圳", "CTU": "成都",
        "HKG": "香港", "TPE": "台北",
        "TYO": "东京", "NRT": "东京", "HND": "东京",
        "OSA": "大阪", "KIX": "大阪", "ITM": "大阪",
        "NGO": "名古屋", "FUK": "福冈", "CTS": "札幌",
        "OKA": "那霸", "ICN": "首尔", "BKK": "曼谷",
        "SIN": "新加坡",
    }

    def __init__(
        self,
        currency: str = "CNY",
        language: str = "zh-CN",
        output_dir: str = "data/flights_raw",
        **kwargs: Any,
    ) -> None:
        # Google 对爬虫相对宽容，但也需要控速
        kwargs.setdefault("delay_range", (2.0, 4.0))
        kwargs.setdefault("max_retries", 2)
        kwargs.setdefault("max_concurrent", 1)
        super().__init__(**kwargs)

        self.currency = currency
        self.language = language
        self.output_dir = Path(output_dir)

    def _build_search_url(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        cabin: str = "economy",
        adults: int = 1,
        nonstop_only: bool = False,
    ) -> str:
        """构建 Google Flights 搜索 URL"""
        # Google Flights URL 格式:
        # /travel/flights/search?tfs=CBwQAhooEgoyMDI2LTA1LTAxagwIAhIIL20vMGgyNjdyDAgCEggvbS8wN2RmeEABSAFwAYIBCwj___________8BmAEC
        # 但更简单的是用 explore 格式:
        # /travel/flights?q=Flights+to+TYO+from+SHA+on+2026-05-01

        base = f"{self.BASE}/search"
        params = {
            "q": f"flights from {origin} to {destination} on {departure_date}",
            "curr": self.currency,
            "hl": self.language,
        }
        if return_date:
            params["q"] += f" return {return_date}"

        # 使用更结构化的 URL
        url = f"{self.BASE}?hl={self.language}&curr={self.currency}"
        return url

    def _build_explore_url(
        self,
        origin: str,
        destination: str,
    ) -> str:
        """构建 Google Flights 探索模式 URL（发现最便宜日期）"""
        return (
            f"https://www.google.com/travel/explore"
            f"?q=flights+from+{origin}+to+{destination}"
            f"&curr={self.currency}&hl={self.language}"
        )

    def _build_tfs_url(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
    ) -> str:
        """
        构建 Google Flights 搜索 URL。

        使用 Google 内部的 tfs (travel flight search) 参数编码。
        tfs 参数是 base64 编码的 protobuf，我们用简化构建方式。
        """
        import base64

        # 构建简化版 protobuf-like 参数
        # 格式参考 Google Flights URL 结构:
        # CBwQAhoSEgoyMDI2LTA0LTIwagMiUFZHcgMiVFlP...
        # 但直接构建完整 protobuf 太复杂，用一种 Google 能解析的 URL 格式

        # 方案: 使用 Google Flights 的结构化路径格式
        # /travel/flights/search?sxsrf=...&tfs=...
        # 这里我们用一种简化的编码方式

        origin_code = origin if len(origin) == 3 else origin[:3]
        dest_code = destination if len(destination) == 3 else destination[:3]

        # Google Flights 也接受这种直接格式
        base = "https://www.google.com/travel/flights"
        params = {
            "hl": self.language,
            "curr": self.currency,
        }
        param_str = "&".join(f"{k}={v}" for k, v in params.items())

        if return_date:
            # 往返
            return (
                f"{base}/search?q=Flights+from+{origin_code}+to+{dest_code}"
                f"+departing+{departure_date}+returning+{return_date}"
                f"&{param_str}"
            )
        else:
            # 单程
            return (
                f"{base}/search?q=Flights+from+{origin_code}+to+{dest_code}"
                f"+on+{departure_date}"
                f"&{param_str}"
            )

    def _build_tfs_encoded_url(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
    ) -> str:
        """
        构建带 tfs 编码参数的 Google Flights URL。
        这种格式返回的数据更完整（SSR 内嵌航班数据）。
        """
        import base64
        import struct

        # 简化的 protobuf 编码（field tag + value）
        def encode_string(field_num: int, value: str) -> bytes:
            tag = (field_num << 3) | 2  # wire type 2 = length-delimited
            encoded = value.encode("utf-8")
            return bytes([tag, len(encoded)]) + encoded

        def encode_leg(dep_date: str, orig: str, dest: str) -> bytes:
            """编码单程航段"""
            date_bytes = encode_string(1, dep_date)
            orig_bytes = encode_string(13, orig)
            dest_bytes = encode_string(14, dest)
            return date_bytes + orig_bytes + dest_bytes

        try:
            # 构建去程
            outbound = encode_leg(departure_date, origin, destination)
            leg1 = bytes([(2 << 3) | 2, len(outbound)]) + outbound

            parts = leg1
            if return_date:
                inbound = encode_leg(return_date, destination, origin)
                leg2 = bytes([(2 << 3) | 2, len(inbound)]) + inbound
                parts += leg2

            # 添加旅客信息 (1 adult)
            parts += bytes([0x40, 0x01])  # adults=1
            parts += bytes([0x48, 0x01])  # cabin=economy
            parts += bytes([0x70, 0x01])  # nonstop preference

            tfs = base64.urlsafe_b64encode(parts).decode().rstrip("=")
            return (
                f"https://www.google.com/travel/flights/search"
                f"?tfs={tfs}&hl={self.language}&curr={self.currency}"
            )
        except Exception:
            # Fallback to q= format
            return self._build_tfs_url(origin, destination, departure_date, return_date)

    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Lite 模式搜索航班（纯 HTTP，解析 SSR 内嵌数据）。

        Google Flights 的 SSR 页面中通过 AF_initDataCallback 内嵌了
        完整的航班数据（protobuf-like 数组结构），我们直接从中提取。
        """
        # 优先用 tfs 编码格式（数据更完整）
        url = self._build_tfs_encoded_url(origin, destination, departure_date, return_date)

        logger.info(f"🔍 Google Flights: {origin}→{destination} {departure_date}")

        html = await self.fetch_text(
            url,
            referer="https://www.google.com/travel/flights",
        )

        if not html or len(html) < 10000:
            # tfs 编码可能失败，fallback 到 q= 格式
            url = self._build_tfs_url(origin, destination, departure_date, return_date)
            html = await self.fetch_text(url, referer="https://www.google.com/travel/flights")

        if not html:
            return []

        # 优先从 SSR 数据提取
        results = self._parse_ssr_data(html, origin, destination, departure_date, return_date)
        if not results:
            # Fallback: 从 HTML 文本中提取
            results = self._parse_google_search_results(html, origin, destination, departure_date, return_date)

        return results

    def _parse_ssr_data(
        self,
        html: str,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str],
    ) -> List[Dict[str, Any]]:
        """
        从 Google Flights SSR 页面的 AF_initDataCallback 数据块中提取航班信息。

        Google 在 SSR 渲染中把航班数据以 protobuf-like 嵌套数组的形式
        通过 AF_initDataCallback 注入页面。价格数据的典型格式：
          [[null, PRICE], "booking_token_base64..."]
        """
        results = []

        # 提取所有 AF_initDataCallback 数据块
        af_blocks = re.findall(
            r"AF_initDataCallback\(\{key:\s*'([^']+)'.*?data:(.*?)\}\);",
            html,
            re.DOTALL,
        )

        # 合并所有数据块为一个大文本来搜索
        all_data = " ".join(data for _, data in af_blocks)
        if not all_data:
            all_data = html

        # 策略1: 提取 [[null, PRICE], "token..."] 格式的价格
        # 这是 Google Flights 价格数据的典型结构
        price_matches = re.findall(
            r'\[\s*null\s*,\s*(\d{3,6})\s*\]\s*,\s*"([A-Za-z0-9+/=_-]{20,})"',
            all_data,
        )

        seen_prices = set()
        for price_str, token in price_matches:
            try:
                price = int(price_str)
                if 200 < price < 30000 and price not in seen_prices:
                    seen_prices.add(price)
                    results.append({
                        "origin": origin,
                        "destination": destination,
                        "departure_date": departure_date,
                        "return_date": return_date,
                        "price": float(price),
                        "currency": self.currency,
                        "booking_token": token[:50] + "...",
                        "source": "google_flights_ssr",
                        "crawled_at": datetime.utcnow().isoformat(),
                    })
            except (ValueError, TypeError):
                continue

        # 策略2: 从 protobuf 数组中搜索价格模式
        # 格式: ,PRICE.XX, 或 ,PRICE, （浮点或整数）
        if not results:
            float_prices = re.findall(r',(\d{3,6}\.\d{1,2}),', all_data)
            for fp in float_prices:
                try:
                    price = float(fp)
                    price_int = int(price)
                    if 200 < price_int < 30000 and price_int not in seen_prices:
                        seen_prices.add(price_int)
                        results.append({
                            "origin": origin,
                            "destination": destination,
                            "departure_date": departure_date,
                            "return_date": return_date,
                            "price": price,
                            "currency": self.currency,
                            "source": "google_flights_ssr",
                            "crawled_at": datetime.utcnow().isoformat(),
                        })
                except (ValueError, TypeError):
                    continue

        # 尝试从数据中提取航司和时间
        # 航司 IATA 代码常见格式: "MU","CA","NH","JL","9C","HO"
        airline_codes = re.findall(
            r'"(MU|CA|NH|JL|9C|HO|CZ|HU|ZH|FM|3U|GS|GJ|MM|GK)"',
            all_data,
        )
        airline_map = {
            "MU": "东方航空", "CA": "国航", "NH": "全日空/ANA", "JL": "日航/JAL",
            "9C": "春秋航空", "HO": "吉祥航空", "CZ": "南方航空", "HU": "海南航空",
            "ZH": "深圳航空", "FM": "上海航空", "3U": "四川航空",
            "GS": "天津航空", "GJ": "浙江长龙", "MM": "乐桃航空", "GK": "捷星日本",
        }

        # 为结果补充航司信息
        unique_airlines = list(dict.fromkeys(airline_codes))  # 保持顺序去重
        for i, r in enumerate(results):
            if i < len(unique_airlines):
                code = unique_airlines[i]
                r["airline_code"] = code
                r["airline"] = airline_map.get(code, code)

        results.sort(key=lambda x: x["price"])

        if results:
            logger.info(
                f"   ✅ SSR 提取 {len(results)} 条航班, "
                f"最低 ¥{results[0]['price']:.0f}"
                + (f" ({results[0].get('airline', '?')})" if results[0].get('airline') else "")
            )
        else:
            logger.debug("   SSR 未提取到数据，尝试 fallback")

        self.stats.items_scraped += len(results)
        return results

    def _parse_google_search_results(
        self,
        html: str,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str],
    ) -> List[Dict[str, Any]]:
        """
        Fallback: 从 HTML 可见文本中提取价格。
        """
        results = []
        try:
            # 提取所有价格
            price_patterns = re.findall(r'(?:¥|￥|CN¥|CNY\s*)(\d[\d,]*)', html)
            seen = set()
            for p in price_patterns:
                try:
                    val = int(p.replace(",", ""))
                    if 200 < val < 30000 and val not in seen:
                        seen.add(val)
                        results.append({
                            "origin": origin,
                            "destination": destination,
                            "departure_date": departure_date,
                            "return_date": return_date,
                            "price": float(val),
                            "currency": "CNY",
                            "source": "google_flights_text",
                            "crawled_at": datetime.utcnow().isoformat(),
                        })
                except ValueError:
                    continue

            results.sort(key=lambda x: x["price"])
            if results:
                logger.info(f"   ✅ 文本提取 {len(results)} 条价格, 最低 ¥{results[0]['price']:.0f}")

        except Exception as e:
            logger.warning(f"⚠️  fallback 解析失败: {e}")

        return results

    # ─────────────────────────────────────────────────────────────────────────
    # Full 模式（Playwright 自动化交互）
    # ─────────────────────────────────────────────────────────────────────────

    async def search_flights_full(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        headed: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Full 模式搜索航班 — 使用 Playwright 自动化 Google Flights UI。

        流程: 打开首页 → 填出发地 → 填目的地 → 日历选日期 → 搜索 → 解析结果

        需要: pip install playwright && python -m playwright install chromium
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error(
                "❌ Full 模式需要 Playwright。安装: "
                "pip install playwright && python -m playwright install chromium"
            )
            return await self.search_flights(origin, destination, departure_date, return_date)

        origin_city = self._CITY_NAMES.get(origin.upper(), origin)
        dest_city = self._CITY_NAMES.get(destination.upper(), destination)
        logger.info(
            f"🌐 Playwright 模式: {origin_city}({origin})→{dest_city}({destination}) "
            f"{departure_date}" + (f"~{return_date}" if return_date else " 单程")
        )

        results: List[Dict[str, Any]] = []

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=not headed)
            ctx = await browser.new_context(
                locale=self.language,
                viewport={"width": 1280, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            )
            page = await ctx.new_page()
            page.set_default_timeout(10000)

            try:
                results = await self._pw_interactive_search(
                    page, origin, origin_city, destination, dest_city,
                    departure_date, return_date,
                )
            except Exception as e:
                logger.warning(f"⚠️  Playwright 搜索异常: {e}")
                try:
                    self.output_dir.mkdir(parents=True, exist_ok=True)
                    await page.screenshot(path=str(self.output_dir / "gf_error.png"))
                except Exception:
                    pass
            finally:
                await browser.close()

        results.sort(key=lambda x: x.get("price") or 99999)
        if results:
            logger.info(
                f"   ✅ {len(results)} 条航班, "
                f"最低 ¥{results[0]['price']:.0f}"
                + (f" ({results[0].get('airline', '')})" if results[0].get("airline") else "")
            )

        self.stats.items_scraped += len(results)
        return results

    # ─── Playwright 内部方法 ─────────────────────────────────────────────────

    async def _pw_interactive_search(
        self,
        page,
        origin: str,
        origin_city: str,
        destination: str,
        dest_city: str,
        departure_date: str,
        return_date: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Playwright 自动化交互: 填表 → 选日期 → 搜索 → 提取结果。"""
        import asyncio as aio
        from datetime import datetime as dt

        dep_dt = dt.strptime(departure_date, "%Y-%m-%d")
        ret_dt = dt.strptime(return_date, "%Y-%m-%d") if return_date else None

        # ── 1. 加载首页 ──
        logger.debug("  [1/6] 加载首页...")
        await page.goto(
            f"https://www.google.com/travel/flights?hl={self.language}&curr={self.currency}",
            wait_until="networkidle", timeout=30000,
        )
        await aio.sleep(3)

        # ── 2. 出发地 ──
        logger.debug(f"  [2/6] 出发地: {origin_city}")
        await self._pw_fill_city(page, origin_city, is_origin=True)

        # ── 3. 目的地 ──
        logger.debug(f"  [3/6] 目的地: {dest_city}")
        await self._pw_fill_city(page, dest_city, is_origin=False)

        # ── 4. 日历选日期 ──
        logger.debug(f"  [4/6] 日期: {departure_date}" + (f" ~ {return_date}" if return_date else ""))
        await page.locator('input[placeholder="出发时间"]').first.click()
        await aio.sleep(1.5)

        # 翻页到目标月份
        now = dt.now()
        target_month_idx = dep_dt.year * 12 + dep_dt.month
        current_month_idx = now.year * 12 + now.month
        pages_needed = max(0, (target_month_idx - current_month_idx) // 2)

        if pages_needed > 0:
            logger.debug(f"       翻页 {pages_needed} 次...")
            for _ in range(pages_needed):
                await page.mouse.click(1130, 625)
                await aio.sleep(0.6)

        # 验证月份 — 用 page 全文检查（dialog innerText 在某些情况下返回空）
        month_name = self._month_name_zh(dep_dt.month)
        for _ in range(4):
            page_text = await page.evaluate("() => document.body.innerText")
            if month_name in page_text:
                break
            await page.mouse.click(1130, 625)
            await aio.sleep(0.8)

        # 点击出发日
        await self._click_calendar_date(page, dep_dt)
        await aio.sleep(0.8)

        # 点击返程日
        if ret_dt:
            ret_month_name = self._month_name_zh(ret_dt.month)
            cal_text2 = await page.evaluate(
                '() => { var d = document.querySelector(\'[role="dialog"]\'); return d ? d.innerText : ""; }'
            )
            if ret_month_name not in cal_text2:
                await page.mouse.click(1130, 625)
                await aio.sleep(0.8)
            await self._click_calendar_date(page, ret_dt)
            await aio.sleep(0.8)

        # 点完成
        await page.mouse.click(1082, 867)
        await aio.sleep(2)

        # ── 5. 搜索 ──
        logger.debug("  [5/6] 搜索...")
        for txt in ["搜索", "探索", "Search", "Explore"]:
            try:
                await page.locator(f'button:has-text("{txt}")').first.click(timeout=3000)
                break
            except Exception:
                continue

        # ── 6. 提取结果 ──
        logger.debug("  [6/6] 提取结果...")
        # 等待搜索结果加载（检测到时间格式则提前结束）
        body = ""
        for wait_round in range(6):
            await aio.sleep(3)
            body = await page.evaluate("() => document.body.innerText")
            time_pairs = re.findall(r"\d{1,2}:\d{2}\s*[–\-]\s*\d{1,2}:\d{2}", body)
            if len(time_pairs) >= 3:
                logger.debug(f"       {len(time_pairs)} 条航班已加载 (等待 {(wait_round+1)*3}s)")
                break
        else:
            logger.debug("       等待超时，使用已有内容解析")

        return self._parse_full_results(body, origin, destination, departure_date, return_date)

    async def _pw_fill_city(self, page, city_name: str, is_origin: bool = True) -> None:
        """Playwright 填写城市（出发地或目的地）"""
        import asyncio as aio

        if is_origin:
            await page.click('[aria-label="从哪里出发？"]')
            await aio.sleep(0.3)
            await page.keyboard.press("Meta+a")
            await page.keyboard.press("Backspace")
        else:
            await page.click('[placeholder="要去哪儿？"]')
            await aio.sleep(0.3)

        await page.keyboard.type(city_name, delay=50)
        await aio.sleep(1.5)
        await page.evaluate(
            """(city) => {
                for (var ul of document.querySelectorAll('ul[role="listbox"]'))
                    if (ul.offsetParent !== null)
                        for (var li of ul.querySelectorAll('li'))
                            if (li.innerText.includes(city)) { li.click(); return true; }
                return false;
            }""",
            city_name,
        )
        await aio.sleep(0.5)

    @staticmethod
    def _month_name_zh(month: int) -> str:
        """月份数字转中文名"""
        names = {
            1: "一月", 2: "二月", 3: "三月", 4: "四月",
            5: "五月", 6: "六月", 7: "七月", 8: "八月",
            9: "九月", 10: "十月", 11: "十一月", 12: "十二月",
        }
        return names.get(month, "")

    async def _click_calendar_date(self, page, target_dt) -> None:
        """
        在 Google Flights 日历中点击指定日期。

        日历布局（1280x900 viewport）：
        - 左侧月份列 x: 日~408, 一~456, 二~504, 三~550, 四~598, 五~645, 六~693
        - 右侧月份偏移 +385
        - 行高 ~52px, 第一行 y ~535
        """
        import asyncio as aio
        import calendar as cal_mod

        month = target_dt.month
        day = target_dt.day
        year = target_dt.year
        month_name = self._month_name_zh(month)

        # 判断目标月在左侧还是右侧
        is_right = await page.evaluate(
            """(monthName) => {
                var dialog = document.querySelector('[role="dialog"]');
                if (!dialog) return false;
                var text = dialog.innerText;
                var parts = text.split(monthName);
                if (parts.length < 2) return false;
                var before = parts[0];
                var zhMonths = ['一月','二月','三月','四月','五月','六月',
                                '七月','八月','九月','十月','十一月','十二月'];
                for (var m of zhMonths) {
                    if (m !== monthName && before.includes(m)) return true;
                }
                return false;
            }""",
            month_name,
        )

        # 计算日期行/列
        first_weekday = cal_mod.monthrange(year, month)[0]  # 0=Mon
        first_col = (first_weekday + 1) % 7  # 转日=0体系
        day_offset = first_col + (day - 1)
        row = day_offset // 7
        col = day_offset % 7

        col_x_left = [408, 456, 504, 550, 598, 645, 693]
        col_x_right = [x + 385 for x in col_x_left]
        base_y = 535
        row_height = 52

        x = (col_x_right if is_right else col_x_left)[col]
        y = base_y + row * row_height

        logger.debug(f"       点击 {month_name}{day}日 ({'右' if is_right else '左'}侧 行{row}列{col} @{x},{y})")
        await page.mouse.click(x, y)

    def _parse_full_results(
        self,
        body: str,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str],
    ) -> List[Dict[str, Any]]:
        """
        从 Google Flights 搜索结果页面全文本中解析航班数据。

        注意: innerText 中时间可能分三行:
            19:10       ← 出发时间
            –           ← 分隔符
            23:00       ← 到达时间
            春航         ← 航司
            2 小时 50 分钟
            PVG–HND
            直达
            ¥1,950
            往返票价
        """
        results = []
        lines = [l.strip() for l in body.split("\n") if l.strip()]

        # 航司列表（长名称在前避免短名误匹配）
        carriers = [
            "春秋航空日本", "春秋航空", "春航",
            "吉祥航空", "中国东方航空", "东方航空",
            "上航东航", "上航 · 东航", "上航", "东航",
            "中国南方航空", "南方航空",
            "中国国际航空", "国航",
            "海南航空", "深圳航空", "四川航空", "厦门航空", "厦航",
            "全日空", "ANA", "日本航空", "JAL",
            "乐桃航空", "Peach", "捷星日本", "捷星", "Jetstar",
            "酷航", "Scoot", "香港快运", "HK Express",
        ]

        i = 0
        while i < len(lines):
            # 模式1: 时间在同一行 "19:10 – 23:00"
            same_line = re.match(
                r"(\d{1,2}:\d{2})\s*[–\-]\s*(\d{1,2}:\d{2})", lines[i]
            )
            # 模式2: 时间分三行 "19:10" / "–" / "23:00"
            split_line = False
            if (
                not same_line
                and re.match(r"^\d{1,2}:\d{2}$", lines[i])
                and i + 2 < len(lines)
                and lines[i + 1] in ("–", "-", "—")
                and re.match(r"^\d{1,2}:\d{2}", lines[i + 2])
            ):
                split_line = True

            if not same_line and not split_line:
                i += 1
                continue

            if same_line:
                dep_time = same_line.group(1)
                arr_time = same_line.group(2)
                scan_start = i + 1
            else:
                dep_time = lines[i]
                arr_time = re.match(r"(\d{1,2}:\d{2})", lines[i + 2]).group(1)
                scan_start = i + 3  # 跳过时间的3行

            # 向后扫描提取航班详情
            airline = None
            duration_min = None
            route = None
            is_direct = False
            stops = 0
            price = None

            for j in range(scan_start, min(scan_start + 12, len(lines))):
                line = lines[j]

                # 遇到下一个航班的时间就停止
                if re.match(r"^\d{1,2}:\d{2}$", line) and j > scan_start + 1:
                    break

                # 航司
                if not airline:
                    for carrier in carriers:
                        if carrier in line:
                            airline = carrier
                            break

                # 飞行时长: "2 小时 50 分钟" 或 "3 小时"
                dur_m = re.match(r"(\d+)\s*小时\s*(?:(\d+)\s*分)?", line)
                if dur_m and not duration_min:
                    duration_min = int(dur_m.group(1)) * 60 + int(dur_m.group(2) or 0)

                # 航线: "PVG–NRT"
                route_m = re.match(r"([A-Z]{3})\s*[–\-]\s*([A-Z]{3})", line)
                if route_m:
                    route = f"{route_m.group(1)}-{route_m.group(2)}"

                # 直达/经停
                if "直达" in line or "nonstop" in line.lower():
                    is_direct = True
                    stops = 0
                stops_m = re.match(r"经停\s*(\d+)\s*次", line)
                if stops_m:
                    stops = int(stops_m.group(1))
                    is_direct = False

                # 价格: "¥1,950"
                price_m = re.search(r"[¥￥]\s*([\d,]+)", line)
                if price_m:
                    val = int(price_m.group(1).replace(",", ""))
                    if 200 < val < 50000:
                        price = val
                        break

                # "无价格信息" 也是终止信号
                if "无价格信息" in line:
                    break

            if price or airline:  # 即使没价格也保留航班信息
                results.append({
                    "origin": origin,
                    "destination": destination,
                    "departure_date": departure_date,
                    "return_date": return_date,
                    "departure_time": dep_time,
                    "arrival_time": arr_time,
                    "airline": airline,
                    "duration_min": duration_min,
                    "route": route,
                    "is_direct": is_direct,
                    "stops": stops,
                    "price": float(price) if price else None,
                    "currency": self.currency,
                    "source": "google_flights_full",
                    "crawled_at": datetime.utcnow().isoformat(),
                })

            # 跳过已扫描的行
            i = scan_start + 1 if same_line else i + 3 + 1

        return results

    # ─────────────────────────────────────────────────────────────────────────
    # Calendar 模式 — 获取每日最低价
    # ─────────────────────────────────────────────────────────────────────────

    async def search_calendar_prices(
        self,
        origin: str,
        destination: str,
        target_month: str,
        trip_days: int = 7,
    ) -> List[Dict[str, Any]]:
        """
        从 Google Flights 日历中提取每日最低往返价格。

        Google Flights 的日期选择器中每个日期下方都显示了
        "7天行程"的最低往返价，是极佳的价格趋势数据源。

        参数:
            origin: 出发地 IATA
            destination: 目的地 IATA
            target_month: 目标月份 "YYYY-MM"
            trip_days: 行程天数（日历底部显示的 "N天行程"）
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error("❌ Calendar 模式需要 Playwright")
            return []

        import asyncio as aio
        from datetime import datetime as dt

        origin_city = self._CITY_NAMES.get(origin.upper(), origin)
        dest_city = self._CITY_NAMES.get(destination.upper(), destination)
        year, month = map(int, target_month.split("-"))
        target_dt = dt(year, month, 1)

        logger.info(f"📅 日历模式: {origin_city}→{dest_city} {target_month}")

        results: List[Dict[str, Any]] = []

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            ctx = await browser.new_context(
                locale=self.language,
                viewport={"width": 1280, "height": 900},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            )
            page = await ctx.new_page()
            page.set_default_timeout(10000)

            try:
                await page.goto(
                    f"https://www.google.com/travel/flights?hl={self.language}&curr={self.currency}",
                    wait_until="networkidle",
                    timeout=30000,
                )
                await aio.sleep(3)

                # 填写出发地/目的地
                await self._pw_fill_city(page, origin_city, is_origin=True)
                await self._pw_fill_city(page, dest_city, is_origin=False)

                # 打开日历
                await page.locator('input[placeholder="出发时间"]').first.click()
                await aio.sleep(1.5)

                # 翻页到目标月份
                now = dt.now()
                target_month_idx = year * 12 + month
                current_month_idx = now.year * 12 + now.month
                pages_needed = max(0, (target_month_idx - current_month_idx) // 2)

                for _ in range(pages_needed):
                    await page.mouse.click(1130, 625)
                    await aio.sleep(0.6)

                # 验证并微调
                month_name = self._month_name_zh(month)
                for _ in range(3):
                    cal_text = await page.evaluate(
                        """() => {
                            var d = document.querySelector('[role="dialog"]');
                            return d ? d.innerText : '';
                        }"""
                    )
                    if month_name in cal_text:
                        break
                    await page.mouse.click(1130, 625)
                    await aio.sleep(0.6)

                # 从日历文本中提取每日价格
                results = self._parse_calendar_prices(
                    cal_text, year, month, origin, destination
                )

                logger.info(f"   ✅ 提取 {len(results)} 天价格数据")

            except Exception as e:
                logger.warning(f"⚠️  日历模式异常: {e}")
            finally:
                await browser.close()

        return results

    def _parse_calendar_prices(
        self,
        cal_text: str,
        year: int,
        month: int,
        origin: str,
        destination: str,
    ) -> List[Dict[str, Any]]:
        """
        从日历文本中提取每日最低价。

        日历文本格式:
            七月
            日 一 二 三 四 五 六
            1
            ¥2,340
            2
            ¥2,430
            ...
        """
        import calendar as cal_mod

        results = []
        month_name = self._month_name_zh(month)

        lines = cal_text.split("\n")
        in_target = False
        day_prices: Dict[int, int] = {}

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if month_name == line:
                in_target = True
                i += 1
                continue

            if in_target:
                other_months = [self._month_name_zh(m) for m in range(1, 13) if m != month]
                if line in other_months:
                    break

                if re.match(r"^\d{1,2}$", line):
                    day = int(line)
                    if 1 <= day <= 31:
                        if i + 1 < len(lines):
                            price_m = re.match(
                                r"[¥￥]([\d,]+)", lines[i + 1].strip()
                            )
                            if price_m:
                                day_prices[day] = int(
                                    price_m.group(1).replace(",", "")
                                )
                                i += 2
                                continue
            i += 1

        _, max_day = cal_mod.monthrange(year, month)
        for day in sorted(day_prices.keys()):
            if day <= max_day:
                results.append({
                    "date": f"{year}-{month:02d}-{day:02d}",
                    "price": day_prices[day],
                    "currency": self.currency,
                    "origin": origin,
                    "destination": destination,
                    "source": "google_flights_calendar",
                    "crawled_at": datetime.utcnow().isoformat(),
                })

        return results