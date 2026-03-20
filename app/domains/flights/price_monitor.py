"""
app/domains/flights/price_monitor.py

机票特价监控核心逻辑：
- 轮询所有航线组合
- 写入 flight_offer_snapshots
- 与历史低价对比，触发特价提醒
"""
from __future__ import annotations

import itertools
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.flights.amadeus_client import (
    DEST_AIRPORTS,
    ORIGIN_AIRPORTS,
    fetch_flight_offers,
    fetch_inspiration_prices,
    get_alert_threshold,
    get_amadeus_client,
    get_upcoming_weekends,
)
from app.domains.flights.notifier import send_price_alert

logger = logging.getLogger(__name__)


# ── 数据库写入 ─────────────────────────────────────────────────────────────────

async def save_snapshot(
    session: AsyncSession,
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str],
    price: float,
    currency: str,
    raw_payload: dict,
) -> None:
    """写入 flight_offer_snapshots，使用原生 SQL 兼容现有表结构"""
    from sqlalchemy import text
    await session.execute(
        text("""
            INSERT INTO flight_offer_snapshots
                (origin_iata, dest_iata, departure_date, return_date,
                 source_name, fetched_at, currency, min_price, raw_payload)
            VALUES
                (:origin, :dest, :dep_date, :ret_date,
                 'amadeus', :fetched_at, :currency, :price, :raw)
        """),
        {
            "origin": origin,
            "dest": destination,
            "dep_date": departure_date,
            "ret_date": return_date,
            "fetched_at": datetime.now(timezone.utc),
            "currency": currency,
            "price": price,
            "raw": __import__("json").dumps(raw_payload, ensure_ascii=False),
        },
    )


async def get_historical_low(
    session: AsyncSession,
    origin: str,
    destination: str,
) -> Optional[float]:
    """查询该航线历史最低价（最近30天）"""
    from sqlalchemy import text
    result = await session.execute(
        text("""
            SELECT MIN(min_price) FROM flight_offer_snapshots
            WHERE origin_iata = :origin
              AND dest_iata = :dest
              AND fetched_at > NOW() - INTERVAL '30 days'
        """),
        {"origin": origin, "dest": destination},
    )
    return result.scalar()


# ── 核心监控逻辑 ───────────────────────────────────────────────────────────────

async def run_price_scan(session: AsyncSession) -> dict:
    """
    全量扫描：
    1. Inspiration Search 找低价窗口
    2. 对低价窗口跑 Flight Offers Search 获取精确价格
    3. 与历史低价比较，触发提醒
    返回统计摘要
    """
    client = get_amadeus_client()
    weekends = get_upcoming_weekends(weeks_ahead=8)

    stats = {
        "scanned": 0,
        "alerts": 0,
        "saved": 0,
        "errors": 0,
    }

    for origin in ORIGIN_AIRPORTS:
        # Step 1: Inspiration Search 快速过滤有日本低价的时间窗口
        inspiration = fetch_inspiration_prices(client, origin)
        low_price_dates: set[str] = {
            item["departure_date"] for item in inspiration
            if item["departure_date"]
        }

        # Step 2: 对每个目的地 + 时间组合精确查价
        for dest in DEST_AIRPORTS:
            threshold = get_alert_threshold(origin, dest)
            hist_low = await get_historical_low(session, origin, dest)

            # 优先查 inspiration 命中的日期，其次查固定周末
            target_dates = [
                (dep, ret) for (dep, ret) in weekends
                if dep in low_price_dates
            ] or weekends[:4]  # fallback: 查最近4个周末

            for dep_date, ret_date in target_dates:
                stats["scanned"] += 1
                offers = fetch_flight_offers(
                    client,
                    origin=origin,
                    destination=dest,
                    departure_date=dep_date,
                    return_date=ret_date,
                    max_results=3,
                )

                if not offers:
                    continue

                best = offers[0]
                price = best["price"]
                currency = best["currency"]

                try:
                    await save_snapshot(
                        session, origin, dest, dep_date, ret_date,
                        price, currency, best["raw"]
                    )
                    stats["saved"] += 1
                except Exception as e:
                    logger.warning("保存快照失败 %s→%s %s: %s", origin, dest, dep_date, e)
                    stats["errors"] += 1

                # 判断是否触发特价提醒
                is_new_low = hist_low is None or price < hist_low * 0.9
                is_below_threshold = price <= threshold

                if is_below_threshold or is_new_low:
                    logger.info(
                        "🎉 特价！%s→%s %s-%s ¥%.0f (阈值¥%.0f，历史低¥%s)",
                        origin, dest, dep_date, ret_date, price, threshold,
                        f"{hist_low:.0f}" if hist_low else "无",
                    )
                    await send_price_alert(
                        origin=origin,
                        destination=dest,
                        departure_date=dep_date,
                        return_date=ret_date,
                        price=price,
                        currency=currency,
                        is_new_low=is_new_low,
                        historical_low=hist_low,
                    )
                    stats["alerts"] += 1

        await session.commit()

    logger.info("价格扫描完成: %s", stats)
    return stats
