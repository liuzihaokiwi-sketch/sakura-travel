"""
arq Job: scan_flight_prices
定时机票特价监控，每6小时跑一次
"""
from __future__ import annotations

import logging

from app.db.session import AsyncSessionLocal
from app.domains.flights.price_monitor import run_price_scan

logger = logging.getLogger(__name__)


async def scan_flight_prices(ctx: dict) -> dict:
    """
    arq Job: 扫描所有航线特价，写入快照，触发提醒。
    建议调度：每6小时执行一次（早6/12/18/24点）
    """
    logger.info("scan_flight_prices 开始")
    async with AsyncSessionLocal() as session:
        stats = await run_price_scan(session)
    logger.info("scan_flight_prices 完成: %s", stats)
    return stats
