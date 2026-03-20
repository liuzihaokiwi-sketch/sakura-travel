"""
天巡 (Skyscanner) Playwright 机票爬虫
======================================
天巡 = Skyscanner 中国站，用 Playwright 绕过验证码。

采集流程:
  1. 打开天巡搜索页
  2. 等待航班结果加载
  3. 从 DOM 提取航班卡片数据
  4. 翻页/排序获取更多结果

用法:
  python scripts/flight_crawl.py --source tianxun --origin SHA --dest TYO
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from scripts.crawlers.playwright_base import PlaywrightCrawler

logger = logging.getLogger(__name__)

# IATA → 天巡 URL 代码
SKY_CODES = {
    "SHA": "SHAA", "PVG": "PVGA", "PEK": "BJSA", "CAN": "CANA",
    "CTU": "CTUA", "SZX": "SZXA", "HGH": "HGHA", "NKG": "NKGA",
    "TYO": "TYOA", "NRT": "NRTA", "HND": "HNDA",
    "OSA": "OSAA", "KIX": "KIXA", "NGO": "NGOA",
    "FUK": "FUKA", "CTS": "CTSA", "OKA": "OKAA",
}

CITY_NAMES = {
    "SHA": "上海", "PVG": "浦东", "PEK": "北京", "CAN": "广州",
    "CTU": "成都", "SZX": "深圳", "HGH": "杭州",
    "TYO": "东京", "OSA": "大阪", "NGO": "名古屋",
    "FUK": "福冈", "CTS": "札幌", "OKA": "冲绳",
}


class TianxunFlightCrawler(PlaywrightCrawler):
    """
    天巡机票 Playwright 爬虫。

    通过真实浏览器渲染天巡搜索页，提取航班价格数据。
    """

    BASE = "https://www.tianxun.com"

    def __init__(
        self,
        output_dir: str = "data/flights_raw",
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("delay_range", (3.0, 6.0))
        kwargs.setdefault("locale", "zh-CN")
        super().__init__(**kwargs)
        self.output_dir = Path(output_dir)

    def _build_url(
        self,
        origin: str,
        destination: str,
        dep_date: str,
        ret_date: Optional[str] = None,
    ) -> str:
        """构建天巡搜索 URL"""
        sky_o = SKY_CODES.get(origin, origin.upper() + "A").lower()
        sky_d = SKY_CODES.get(destination, destination.upper() + "A").lower()

        dep_fmt = dep_date.replace("-", "")[2:]  # 2026-04-20 → 260420
        if ret_date:
            ret_fmt = ret_date.replace("-", "")[2:]
            return f"{self.BASE}/transport/flights/{sky_o}/{sky_d}/{dep_fmt}/{ret_fmt}/?adults=1&cabinclass=economy&currency=CNY"
        else:
            return f"{self.BASE}/transport/flights/{sky_o}/{sky_d}/{dep_fmt}/?adults=1&cabinclass=economy&currency=CNY"

    async def search_flights(
        self,
        origin: str,
        destination: str,
        dep_date: str,
        ret_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        搜索航班价格。

        Args:
            origin:      IATA 代码
            destination: IATA 代码
            dep_date:    "2026-04-20"
            ret_date:    可选回程日期

        Returns:
            航班报价列表
        """
        o_name = CITY_NAMES.get(origin, origin)
        d_name = CITY_NAMES.get(destination, destination)
        logger.info(f"✈️  天巡搜索: {o_name}→{d_name} {dep_date}")

        url = self._build_url(origin, destination, dep_date, ret_date)
        page = await self.new_page()
        results = []

        try:
            ok = await self.safe_goto(page, url, wait_until="domcontentloaded", timeout=30000)
            if not ok:
                return []

            # 等待搜索结果（天巡会有一个加载过程）
            logger.info("  ⏳ 等待航班结果加载...")

            # 等待结果容器出现
            try:
                await page.wait_for_selector(
                    "[class*='FlightsResults'], [class*='ResultsSummary'], "
                    "[class*='itinerary'], [class*='TicketBody']",
                    timeout=25000,
                )
                # 多等几秒让更多结果加载
                await self.random_delay()
                await self.random_delay()
            except Exception:
                logger.warning("  ⚠️  天巡结果加载超时，尝试解析已有内容")

            # 截图调试（可选）
            # await page.screenshot(path="debug_tianxun.png")

            # 方式1: 从 JS 变量中提取结构化数据
            js_results = await self._extract_from_js(page, origin, destination, dep_date, ret_date)
            if js_results:
                results = js_results
            else:
                # 方式2: 从 DOM 提取
                results = await self._extract_from_dom(page, origin, destination, dep_date, ret_date)

        except Exception as e:
            logger.error(f"  ❌ 天巡搜索异常: {e}")
        finally:
            await page.close()

        results.sort(key=lambda x: x.get("price", float("inf")))
        if results:
            logger.info(
                f"  ✅ {len(results)} 条结果，"
                f"最低 ¥{results[0]['price']:.0f}"
            )
        else:
            logger.info("  📭 未获取到数据")

        return results

    async def _extract_from_js(
        self, page: Any, origin: str, dest: str, dep_date: str, ret_date: Optional[str]
    ) -> List[Dict[str, Any]]:
        """从页面 JS 上下文中提取航班数据"""
        try:
            data = await page.evaluate("""
                () => {
                    // 天巡在全局状态中存储搜索结果
                    const stores = [
                        window.__NEXT_DATA__,
                        window.__FLIGHT_SEARCH_RESULTS__,
                        window.__state__,
                    ];
                    for (const s of stores) {
                        if (s) return JSON.stringify(s);
                    }

                    // 尝试从 Redux/MobX store 中提取
                    const scripts = document.querySelectorAll('script');
                    for (const s of scripts) {
                        const text = s.textContent || '';
                        if (text.includes('itineraries') || text.includes('FlightResults')) {
                            // 找到包含航班数据的 script
                            const match = text.match(/(\{.*"itineraries".*\})/s);
                            if (match) return match[1];
                        }
                    }

                    return null;
                }
            """)

            if not data:
                return []

            parsed = json.loads(data)
            return self._parse_tianxun_json(parsed, origin, dest, dep_date, ret_date)

        except Exception as e:
            logger.debug(f"  JS 提取失败: {e}")
            return []

    def _parse_tianxun_json(
        self, data: dict, origin: str, dest: str, dep_date: str, ret_date: Optional[str]
    ) -> List[Dict[str, Any]]:
        """解析天巡的 JSON 数据"""
        results = []

        # 多种可能的数据路径
        itineraries = (
            data.get("props", {}).get("pageProps", {}).get("itineraries", [])
            or data.get("itineraries", [])
            or data.get("data", {}).get("itineraries", [])
        )

        for itin in itineraries:
            price = (
                itin.get("price", {}).get("amount")
                or itin.get("minPrice")
                or itin.get("rawPrice")
            )
            if not price:
                continue

            # 航司
            legs = itin.get("legs", [])
            airline = None
            dep_time = None
            arr_time = None
            duration = None
            stops = 0

            if legs:
                leg = legs[0]
                carriers = leg.get("carriers", []) or leg.get("airlines", [])
                if carriers:
                    airline = carriers[0].get("name") or carriers[0].get("code")
                dep_time = leg.get("departureTime") or leg.get("departure")
                arr_time = leg.get("arrivalTime") or leg.get("arrival")
                duration = leg.get("duration") or leg.get("durationInMinutes")
                stops = leg.get("stopCount", 0)

            results.append({
                "origin": origin,
                "destination": dest,
                "departure_date": dep_date,
                "return_date": ret_date,
                "price": float(price),
                "currency": "CNY",
                "airline": airline,
                "departure_time": dep_time,
                "arrival_time": arr_time,
                "duration_min": duration,
                "stops": stops,
                "is_direct": stops == 0,
                "source": "tianxun",
                "crawled_at": datetime.utcnow().isoformat(),
            })

        return results

    async def _extract_from_dom(
        self, page: Any, origin: str, dest: str, dep_date: str, ret_date: Optional[str]
    ) -> List[Dict[str, Any]]:
        """从 DOM 元素中提取航班数据"""
        results = []

        # 获取整个页面文本
        body_text = await page.evaluate("() => document.body.innerText")

        # 提取价格
        prices = re.findall(r'(?:¥|￥|CN¥)\s*([\d,]+)', body_text)
        # 提取航司
        airlines = re.findall(
            r'(春秋航空|吉祥航空|东方航空|南方航空|国航|海南航空|'
            r'全日空|ANA|日本航空|JAL|乐桃航空|捷星|酷航|'
            r'深圳航空|四川航空|厦门航空|山东航空)',
            body_text,
        )
        # 提取时间段
        time_pairs = re.findall(r'(\d{1,2}:\d{2})\s*[-–—~]\s*(\d{1,2}:\d{2})', body_text)
        # 提取飞行时长
        durations = re.findall(r'(\d+)\s*[hH时小]\s*(?:(\d+)\s*[mM分])?', body_text)

        seen_prices = set()
        for i, p_str in enumerate(prices):
            try:
                price = int(p_str.replace(",", ""))
                if price < 200 or price > 30000:
                    continue
                if price in seen_prices:
                    continue
                seen_prices.add(price)

                airline = airlines[i] if i < len(airlines) else None
                dep_time = time_pairs[i][0] if i < len(time_pairs) else None
                arr_time = time_pairs[i][1] if i < len(time_pairs) else None
                dur_min = None
                if i < len(durations):
                    h = int(durations[i][0])
                    m = int(durations[i][1]) if durations[i][1] else 0
                    dur_min = h * 60 + m

                results.append({
                    "origin": origin,
                    "destination": dest,
                    "departure_date": dep_date,
                    "return_date": ret_date,
                    "price": float(price),
                    "currency": "CNY",
                    "airline": airline,
                    "departure_time": dep_time,
                    "arrival_time": arr_time,
                    "duration_min": dur_min,
                    "source": "tianxun_dom",
                    "crawled_at": datetime.utcnow().isoformat(),
                })
            except (ValueError, TypeError):
                continue

        return results

    async def scan_route(
        self,
        origin: str,
        destination: str,
        dep_date: str,
        ret_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """搜索单条航线"""
        return await self.search_flights(origin, destination, dep_date, ret_date)

    async def scan_all_routes(
        self,
        routes: List[tuple],
        dep_date: str,
        ret_date: Optional[str] = None,
        save_json: bool = True,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """批量搜索多条航线"""
        all_results = {}
        deals = []

        for origin, dest in routes:
            route_key = f"{origin}-{dest}"
            results = await self.scan_route(origin, dest, dep_date, ret_date)
            all_results[route_key] = results

            # 标记特价
            for r in results:
                if r["price"] <= 1500:  # 简单阈值
                    r["is_deal"] = True
                    deals.append(r)

        if save_json:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.output_dir / f"tianxun_flights_{ts}.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump({
                    "meta": {
                        "dep_date": dep_date,
                        "ret_date": ret_date,
                        "crawled_at": datetime.utcnow().isoformat(),
                        "routes": len(all_results),
                        "deals": len(deals),
                    },
                    "routes": all_results,
                    "deals": deals,
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 已保存: {filepath}")

        # 打印特价
        if deals:
            print(f"\n{'='*60}")
            print(f"💥 天巡特价: {len(deals)} 条")
            print(f"-" * 60)
            for d in sorted(deals, key=lambda x: x["price"])[:15]:
                o = CITY_NAMES.get(d["origin"], d["origin"])
                t = CITY_NAMES.get(d["destination"], d["destination"])
                airline = d.get("airline") or "?"
                print(f"  ¥{d['price']:>6.0f}  {o}→{t}  {airline}")
            print(f"{'='*60}")

        return all_results
