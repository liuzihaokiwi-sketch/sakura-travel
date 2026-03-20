"""
SkyscannerCrawler — Skyscanner 机票低价采集器
===============================================
利用 Skyscanner 内部 API 获取机票价格数据，无需 API Key。

数据源端点：
  1. Indicative Prices — 按月/按周的最低价日历（轻量，不限速）
  2. Browse Flights    — 具体航线+日期的详细报价（较重，需控速）

采集策略：
  1. 先用 Indicative 扫描全月最低价 → 找到低价日期窗口
  2. 再对低价日期跑 Browse 获取精确航班信息
  3. 存 JSON + 写入 flight_offer_snapshots

用法：
  async with SkyscannerCrawler() as crawler:
      deals = await crawler.scan_route("SHAA", "TYOA", months_ahead=3)

  # CLI
  python scripts/flight_crawl.py --origin SHA --dest TYO --months 3
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

# ── IATA → Skyscanner 地点代码映射 ───────────────────────────────────────────
# Skyscanner 用自己的 entity ID 系统，但也支持 IATA-Sky 代码
IATA_TO_SKY: Dict[str, Tuple[str, str]] = {
    # 中国出发城市 → (sky_code, entity_id)
    "SHA": ("SHAA", "27542066"),   # 上海（所有机场）
    "PVG": ("PVGA", "95673529"),   # 上海浦东
    "PEK": ("BJSA", "27539793"),   # 北京（所有机场）
    "CAN": ("CANA", "27544008"),   # 广州
    "CTU": ("CTUA", "27544195"),   # 成都
    "SZX": ("SZXA", "27544600"),   # 深圳
    "HGH": ("HGHA", "27544174"),   # 杭州
    "NKG": ("NKGA", "27544400"),   # 南京
    "WUH": ("WUHA", "27544707"),   # 武汉
    "CKG": ("CKGA", "27544043"),   # 重庆
    "XIY": ("XIYA", "27544736"),   # 西安
    # 日本目的地
    "TYO": ("TYOA", "27542307"),   # 东京（成田+羽田）
    "NRT": ("NRTA", "95673400"),   # 成田
    "HND": ("HNDA", "95673362"),   # 羽田
    "OSA": ("OSAA", "27542306"),   # 大阪（关西+伊丹）
    "KIX": ("KIXA", "95673370"),   # 关西
    "NGO": ("NGOA", "95673396"),   # 名古屋中部
    "FUK": ("FUKA", "95673344"),   # 福冈
    "CTS": ("CTSA", "95673320"),   # 札幌新千岁
    "OKA": ("OKAA", "95673406"),   # 冲绳那霸
}

# ── 中文名称 ──────────────────────────────────────────────────────────────────
AIRPORT_NAMES: Dict[str, str] = {
    "SHA": "上海", "PVG": "浦东", "PEK": "北京", "CAN": "广州",
    "CTU": "成都", "SZX": "深圳", "HGH": "杭州", "NKG": "南京",
    "WUH": "武汉", "CKG": "重庆", "XIY": "西安",
    "TYO": "东京", "NRT": "成田", "HND": "羽田",
    "OSA": "大阪", "KIX": "关西", "NGO": "名古屋",
    "FUK": "福冈", "CTS": "札幌", "OKA": "冲绳",
}

# ── 默认航线（中国主要城市 → 日本主要城市）─────────────────────────────────────
DEFAULT_ROUTES: List[Tuple[str, str]] = [
    ("SHA", "TYO"), ("SHA", "OSA"), ("SHA", "NGO"),
    ("PEK", "TYO"), ("PEK", "OSA"),
    ("CAN", "TYO"), ("CAN", "OSA"),
    ("CTU", "TYO"), ("CTU", "OSA"),
    ("SZX", "TYO"), ("SZX", "OSA"),
    ("HGH", "TYO"), ("HGH", "OSA"),
    ("CKG", "OSA"),
]

# ── 特价阈值（人民币，往返含税）──────────────────────────────────────────────
DEAL_THRESHOLDS: Dict[str, int] = {
    "SHA-TYO": 1200, "SHA-OSA": 1100, "SHA-NGO": 1000,
    "PEK-TYO": 1300, "PEK-OSA": 1200,
    "CAN-TYO": 1400, "CAN-OSA": 1300,
    "CTU-TYO": 1500, "CTU-OSA": 1400,
    "SZX-TYO": 1400, "SZX-OSA": 1300,
    "HGH-TYO": 1200, "HGH-OSA": 1100,
    "CKG-OSA": 1400,
    "_default": 1800,
}


class SkyscannerCrawler(BaseCrawler):
    """
    Skyscanner 内部 API 爬虫。

    两阶段采集：
      1. indicative prices → 月度/日度最低价日历
      2. search flights    → 具体航班详细报价

    无需 API Key，利用网站内部 BFF 接口。
    """

    # Skyscanner 内部 API base
    BASE = "https://www.skyscanner.net"
    API_BASE = "https://www.skyscanner.net/g/browse-view-bff"
    SEARCH_BASE = "https://www.skyscanner.net/g/conductor/v1/fps3/search"

    def __init__(
        self,
        market: str = "CN",
        currency: str = "CNY",
        locale: str = "zh-CN",
        output_dir: str = "data/flights_raw",
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("delay_range", (1.5, 3.5))
        kwargs.setdefault("max_retries", 3)
        kwargs.setdefault("max_concurrent", 2)
        super().__init__(**kwargs)

        self.market = market
        self.currency = currency
        self.locale = locale
        self.output_dir = Path(output_dir)

    async def before_crawl(self) -> None:
        """预热：访问首页获取 cookie + session"""
        logger.info("🔥 预热 Skyscanner Cookie...")
        resp = await self.fetch(
            f"{self.BASE}/flights",
            referer="https://www.google.com/",
        )
        if resp:
            logger.info(f"✅ Skyscanner 预热成功 (cookies: {len(resp.cookies)})")

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Indicative Prices — 最低价日历（轻量核心）
    # ─────────────────────────────────────────────────────────────────────────

    async def get_indicative_prices(
        self,
        origin: str,
        destination: str,
        year_month: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取指定航线的最低价日历。

        Args:
            origin:      IATA 代码（如 "SHA"）
            destination: IATA 代码（如 "TYO"）
            year_month:  "2026-04" 格式，None=未来最便宜

        Returns:
            [{"date": "2026-04-15", "price": 899, "direct": True}, ...]
        """
        sky_origin = IATA_TO_SKY.get(origin, (origin + "A", ""))[0]
        sky_dest = IATA_TO_SKY.get(destination, (destination + "A", ""))[0]
        entity_origin = IATA_TO_SKY.get(origin, ("", ""))[1]
        entity_dest = IATA_TO_SKY.get(destination, ("", ""))[1]

        date_param = year_month if year_month else "anytime"

        # Skyscanner 的 Create+Poll 模式
        url = f"{self.BASE}/g/indicative-browse-bff/dataservices/indicative/search"

        payload = {
            "query": {
                "market": self.market,
                "locale": self.locale,
                "currency": self.currency,
                "queryLegs": [
                    {
                        "originPlace": {"queryPlace": {"iata": origin}},
                        "destinationPlace": {"queryPlace": {"iata": destination}},
                        "anytime": True if date_param == "anytime" else False,
                        **({"fixedDate": {"year": int(year_month.split("-")[0]), "month": int(year_month.split("-")[1])}} if year_month else {}),
                    },
                    {
                        "originPlace": {"queryPlace": {"iata": destination}},
                        "destinationPlace": {"queryPlace": {"iata": origin}},
                        "anytime": True if date_param == "anytime" else False,
                        **({"fixedDate": {"year": int(year_month.split("-")[0]), "month": int(year_month.split("-")[1])}} if year_month else {}),
                    },
                ],
                "dateTimeGroupingType": "BY_DATE" if year_month else "BY_MONTH",
            }
        }

        origin_name = AIRPORT_NAMES.get(origin, origin)
        dest_name = AIRPORT_NAMES.get(destination, destination)
        logger.info(f"📅 低价日历: {origin_name}→{dest_name} ({date_param})")

        resp = await self.fetch(
            url,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            data=json.dumps(payload).encode() if isinstance(payload, dict) else payload,
            referer=f"{self.BASE}/transport/flights/{sky_origin.lower()}/{sky_dest.lower()}/",
        )

        if not resp:
            # Fallback: 尝试老版 browse 端点
            return await self._get_indicative_fallback(origin, destination, year_month)

        try:
            data = resp.json()
            return self._parse_indicative_response(data, origin, destination)
        except Exception as e:
            logger.warning(f"⚠️  解析 indicative 失败: {e}")
            return await self._get_indicative_fallback(origin, destination, year_month)

    async def _get_indicative_fallback(
        self,
        origin: str,
        destination: str,
        year_month: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fallback: 用老版 browse 端点"""
        sky_origin = IATA_TO_SKY.get(origin, (origin + "A", ""))[0]
        sky_dest = IATA_TO_SKY.get(destination, (destination + "A", ""))[0]

        date_part = year_month or "anytime"
        url = (
            f"{self.API_BASE}/dataservices/browse/v3/bvs/indicative"
            f"/anytime/one-way/{self.market}/{self.currency}/{self.locale}"
            f"/{sky_origin}/{sky_dest}/{date_part}"
        )

        resp = await self.fetch(
            url,
            headers={"Accept": "application/json"},
            referer=f"{self.BASE}/transport/flights/{sky_origin.lower()}/{sky_dest.lower()}/",
        )

        if not resp:
            return []

        try:
            data = resp.json()
            return self._parse_browse_response(data, origin, destination)
        except Exception as e:
            logger.warning(f"⚠️  browse fallback 解析失败: {e}")
            return []

    def _parse_indicative_response(
        self, data: dict, origin: str, destination: str
    ) -> List[Dict[str, Any]]:
        """解析 indicative search 响应"""
        results = []
        quotes = data.get("content", {}).get("results", {}).get("quotes", {})

        for quote_id, quote in quotes.items():
            price = quote.get("minPrice", {}).get("amount")
            if not price:
                continue

            # 提取日期
            outbound_leg = quote.get("outboundLeg", {})
            dep_date = None
            dep_info = outbound_leg.get("departureDateTime", {})
            if dep_info:
                dep_date = f"{dep_info.get('year', '')}-{dep_info.get('month', '01'):02d}-{dep_info.get('day', '01'):02d}"

            inbound_leg = quote.get("inboundLeg", {})
            ret_date = None
            ret_info = inbound_leg.get("departureDateTime", {})
            if ret_info:
                ret_date = f"{ret_info.get('year', '')}-{ret_info.get('month', '01'):02d}-{ret_info.get('day', '01'):02d}"

            is_direct = quote.get("isDirect", False)

            results.append({
                "origin": origin,
                "destination": destination,
                "departure_date": dep_date,
                "return_date": ret_date,
                "price": float(price),
                "currency": self.currency,
                "is_direct": is_direct,
                "source": "skyscanner_indicative",
                "crawled_at": datetime.utcnow().isoformat(),
            })

        # 按价格排序
        results.sort(key=lambda x: x["price"])
        logger.info(f"   ✅ {len(results)} 条报价，最低 ¥{results[0]['price']:.0f}" if results else "   📭 无数据")
        return results

    def _parse_browse_response(
        self, data: dict, origin: str, destination: str
    ) -> List[Dict[str, Any]]:
        """解析老版 browse 响应"""
        results = []

        # 尝试多种数据路径
        buckets = (
            data.get("PriceGrids", {}).get("Grid", [])
            or data.get("content", {}).get("sortingOptions", {}).get("cheapest", [])
            or []
        )

        quotes = data.get("Quotes") or data.get("quotes") or []
        for quote in quotes if isinstance(quotes, list) else quotes.values():
            if isinstance(quote, dict):
                price = (
                    quote.get("MinPrice")
                    or quote.get("minPrice", {}).get("amount")
                    or quote.get("price")
                )
                if price:
                    dep_date = quote.get("OutboundLeg", {}).get("DepartureDate", "")
                    ret_date = quote.get("InboundLeg", {}).get("DepartureDate", "")
                    direct = quote.get("Direct", quote.get("isDirect", False))

                    results.append({
                        "origin": origin,
                        "destination": destination,
                        "departure_date": dep_date[:10] if dep_date else None,
                        "return_date": ret_date[:10] if ret_date else None,
                        "price": float(price),
                        "currency": self.currency,
                        "is_direct": direct,
                        "source": "skyscanner_browse",
                        "crawled_at": datetime.utcnow().isoformat(),
                    })

        results.sort(key=lambda x: x["price"])
        return results

    # ─────────────────────────────────────────────────────────────────────────
    # 2. 航线全量扫描
    # ─────────────────────────────────────────────────────────────────────────

    async def scan_route(
        self,
        origin: str,
        destination: str,
        months_ahead: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        扫描单条航线未来 N 个月的最低价。

        Returns:
            按价格排序的所有低价报价
        """
        all_quotes: List[Dict[str, Any]] = []

        # 先查 anytime（获取全局最低价概览）
        anytime_quotes = await self.get_indicative_prices(origin, destination)
        all_quotes.extend(anytime_quotes)

        # 再逐月细查
        today = date.today()
        for m in range(months_ahead):
            target = today.replace(day=1) + timedelta(days=32 * m)
            ym = target.strftime("%Y-%m")
            monthly_quotes = await self.get_indicative_prices(origin, destination, ym)
            all_quotes.extend(monthly_quotes)

        # 去重（同一日期+价格视为重复）
        seen = set()
        unique = []
        for q in all_quotes:
            key = (q.get("departure_date"), q.get("return_date"), q.get("price"))
            if key not in seen:
                seen.add(key)
                unique.append(q)

        unique.sort(key=lambda x: x["price"])
        self.stats.items_scraped += len(unique)
        return unique

    async def scan_all_routes(
        self,
        routes: Optional[List[Tuple[str, str]]] = None,
        months_ahead: int = 3,
        save_json: bool = True,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        批量扫描所有航线。

        Args:
            routes:       航线列表 [(origin, dest), ...]，None=使用默认航线
            months_ahead: 扫描未来几个月
            save_json:    是否保存 JSON

        Returns:
            {"SHA-TYO": [quotes...], ...}
        """
        target_routes = routes or DEFAULT_ROUTES

        logger.info(
            f"✈️  开始扫描 {len(target_routes)} 条航线，"
            f"未来 {months_ahead} 个月"
        )

        await self.before_crawl()

        all_results: Dict[str, List[Dict[str, Any]]] = {}
        deals: List[Dict[str, Any]] = []  # 特价汇总

        for origin, dest in target_routes:
            route_key = f"{origin}-{dest}"
            origin_name = AIRPORT_NAMES.get(origin, origin)
            dest_name = AIRPORT_NAMES.get(dest, dest)

            logger.info(f"\n✈️  扫描 {origin_name}→{dest_name} ({route_key})")

            quotes = await self.scan_route(origin, dest, months_ahead)
            all_results[route_key] = quotes

            # 检查是否有特价
            threshold = DEAL_THRESHOLDS.get(route_key, DEAL_THRESHOLDS["_default"])
            route_deals = [q for q in quotes if q["price"] <= threshold]
            if route_deals:
                logger.info(
                    f"   🎉 发现 {len(route_deals)} 个特价！"
                    f"最低 ¥{route_deals[0]['price']:.0f} (阈值 ¥{threshold})"
                )
                for d in route_deals:
                    d["deal_threshold"] = threshold
                    d["route_key"] = route_key
                deals.extend(route_deals)
            else:
                cheapest = quotes[0]["price"] if quotes else "无数据"
                logger.info(f"   📊 最低 ¥{cheapest}，未达到特价阈值 ¥{threshold}")

        await self.after_crawl()

        # 保存
        if save_json:
            self._save_results(all_results, deals)

        # 统计
        total_quotes = sum(len(v) for v in all_results.values())
        logger.info(f"\n{self.stats.summary()}")
        logger.info(
            f"🎉 扫描完成: {len(target_routes)} 条航线, "
            f"{total_quotes} 条报价, {len(deals)} 个特价"
        )

        return all_results

    # ─────────────────────────────────────────────────────────────────────────
    # 3. 数据存储
    # ─────────────────────────────────────────────────────────────────────────

    def _save_results(
        self,
        all_results: Dict[str, List[Dict[str, Any]]],
        deals: List[Dict[str, Any]],
    ) -> None:
        """保存采集结果"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 全量数据
        full_path = self.output_dir / f"flights_all_{ts}.json"
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump({
                "meta": {
                    "crawled_at": datetime.utcnow().isoformat(),
                    "routes_count": len(all_results),
                    "total_quotes": sum(len(v) for v in all_results.values()),
                    "deals_count": len(deals),
                },
                "routes": {
                    k: v[:20] for k, v in all_results.items()  # 每条航线保留前20条
                },
            }, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 全量数据: {full_path}")

        # 特价专列
        if deals:
            deals_path = self.output_dir / f"flight_deals_{ts}.json"
            deals.sort(key=lambda x: x["price"])
            with open(deals_path, "w", encoding="utf-8") as f:
                json.dump({
                    "meta": {
                        "crawled_at": datetime.utcnow().isoformat(),
                        "total_deals": len(deals),
                    },
                    "deals": deals,
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"💰 特价数据: {deals_path}")

            # 打印特价摘要
            print("\n" + "=" * 60)
            print("💥 特价机票汇总")
            print("=" * 60)
            for d in deals[:15]:
                o = AIRPORT_NAMES.get(d["origin"], d["origin"])
                t = AIRPORT_NAMES.get(d["destination"], d["destination"])
                direct = "直飞" if d.get("is_direct") else "转机"
                dep = d.get("departure_date") or "灵活"
                print(f"  ¥{d['price']:>6.0f}  {o}→{t}  {dep}  {direct}")
            print("=" * 60)

    @staticmethod
    def format_deal_message(deal: Dict[str, Any]) -> str:
        """格式化单条特价信息（用于通知推送）"""
        o = AIRPORT_NAMES.get(deal["origin"], deal["origin"])
        d = AIRPORT_NAMES.get(deal["destination"], deal["destination"])
        dep = deal.get("departure_date") or "灵活日期"
        ret = deal.get("return_date") or ""
        direct = "直飞" if deal.get("is_direct") else "含转机"
        threshold = deal.get("deal_threshold", "")

        lines = [
            f"💥 特价机票！",
            f"✈️ {o} → {d}（{direct}）",
            f"📅 去程 {dep}" + (f" / 回程 {ret}" if ret else ""),
            f"💰 ¥{deal['price']:.0f}" + (f"（阈值 ¥{threshold}）" if threshold else ""),
            f"🔗 https://www.skyscanner.net/transport/flights/{deal['origin'].lower()}/{deal['destination'].lower()}/{dep.replace('-', '')}/"
        ]
        return "\n".join(lines)
