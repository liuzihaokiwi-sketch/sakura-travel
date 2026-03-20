"""
app/domains/flights/amadeus_client.py

机票数据双源封装：
- 携程开放平台（国内精准，人民币，主力）
- Skyscanner RapidAPI（国际覆盖，低价发现，辅助）
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# 目标机场：中国主要出发地 → 日本目的地
ORIGIN_AIRPORTS = ["SHA", "PEK", "CAN", "CTU", "SZX"]  # 上海/北京/广州/成都/深圳
DEST_AIRPORTS = ["TYO", "OSA", "NGO"]  # 东京/大阪/名古屋

# 特价阈值（元）：低于此价格触发提醒
PRICE_ALERT_THRESHOLD: dict[str, float] = {
    "SHA-TYO": 1200,
    "SHA-OSA": 1100,
    "PEK-TYO": 1300,
    "CAN-TYO": 1400,
    "CAN-OSA": 1300,
    "CTU-TYO": 1500,
    "SZX-TYO": 1400,
    "default": 1800,
}


def get_amadeus_client() -> Client:
    """创建 Amadeus Client（自动管理 Token）"""
    return Client(
        client_id=settings.amadeus_client_id,
        client_secret=settings.amadeus_client_secret,
        hostname="production",  # 生产环境；测试用 "test"
        logger=logger,
        log_level="silent",
    )


def fetch_inspiration_prices(
    client: Client,
    origin: str,
    max_price: Optional[int] = None,
    duration: str = "1W",  # 1W / 2W / 1M / 2M
) -> list[dict]:
    """
    Flight Inspiration Search：查询从 origin 出发的低价目的地推荐。
    返回标准化列表：[{destination, departureDate, returnDate, price, currency}]
    """
    try:
        kwargs: dict = {
            "origin": origin,
            "oneWay": False,
            "duration": duration,
            "nonStop": False,
        }
        if max_price:
            kwargs["maxPrice"] = max_price

        response = client.shopping.flight_destinations.get(**kwargs)
        results = []
        for offer in response.data:
            dest = offer.get("destination", "")
            if dest not in DEST_AIRPORTS:
                continue
            links = offer.get("links", {})
            results.append({
                "origin": origin,
                "destination": dest,
                "departure_date": offer.get("departureDate"),
                "return_date": offer.get("returnDate"),
                "price": float(offer.get("price", {}).get("total", 0)),
                "currency": offer.get("price", {}).get("currency", "CNY"),
                "links": links,
            })
        return results

    except ResponseError as e:
        logger.warning("Amadeus inspiration search 失败 origin=%s: %s", origin, e)
        return []


def fetch_flight_offers(
    client: Client,
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
    max_results: int = 5,
) -> list[dict]:
    """
    Flight Offers Search：查询具体日期的最低报价。
    返回标准化列表：[{price, currency, validatingAirline, segments, raw}]
    """
    try:
        kwargs: dict = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": adults,
            "max": max_results,
            "currencyCode": "CNY",
        }
        if return_date:
            kwargs["returnDate"] = return_date

        response = client.shopping.flight_offers_search.get(**kwargs)
        results = []
        for offer in response.data:
            price_info = offer.get("price", {})
            total = float(price_info.get("grandTotal", price_info.get("total", 0)))
            currency = price_info.get("currency", "CNY")
            airline = offer.get("validatingAirlineCodes", ["??"])[0]

            results.append({
                "price": total,
                "currency": currency,
                "airline": airline,
                "raw": offer,
            })
        return sorted(results, key=lambda x: x["price"])

    except ResponseError as e:
        logger.warning(
            "Amadeus offers search 失败 %s→%s %s: %s",
            origin, destination, departure_date, e
        )
        return []


def get_alert_threshold(origin: str, destination: str) -> float:
    """获取该航线的特价阈值"""
    key = f"{origin}-{destination}"
    return PRICE_ALERT_THRESHOLD.get(key, PRICE_ALERT_THRESHOLD["default"])


def get_upcoming_weekends(weeks_ahead: int = 8) -> list[tuple[str, str]]:
    """
    生成未来 N 周的周五→周一日期对（适合短途周末游）
    返回 [(departure_date, return_date), ...]
    """
    today = date.today()
    results = []
    # 找到下一个周五
    days_to_friday = (4 - today.weekday()) % 7
    if days_to_friday == 0:
        days_to_friday = 7
    friday = today + timedelta(days=days_to_friday)

    for i in range(weeks_ahead):
        dep = friday + timedelta(weeks=i)
        ret = dep + timedelta(days=3)  # 周一返回
        results.append((dep.strftime("%Y-%m-%d"), ret.strftime("%Y-%m-%d")))
    return results
