#!/usr/bin/env python3
"""
scripts/scan_flights.py
手动触发机票特价扫描（无需启动 worker）

用法:
    python3 scripts/scan_flights.py                    # 全量扫描
    python3 scripts/scan_flights.py --origin SHA --dest TYO  # 指定航线
    python3 scripts/scan_flights.py --dry-run          # 只打印，不写库
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


async def run(origin: str | None, dest: str | None, dry_run: bool) -> None:
    from app.db.session import AsyncSessionLocal
    from app.domains.flights.amadeus_client import (
        DEST_AIRPORTS, ORIGIN_AIRPORTS,
        fetch_flight_offers, get_amadeus_client,
        get_alert_threshold, get_upcoming_weekends,
    )
    from app.domains.flights.price_monitor import run_price_scan, save_snapshot

    client = get_amadeus_client()

    if origin and dest:
        # 单条航线精确查询
        weekends = get_upcoming_weekends(weeks_ahead=4)
        print(f"\n🔍 查询 {origin} → {dest}，未来4个周末：\n")
        for dep, ret in weekends:
            offers = fetch_flight_offers(client, origin, dest, dep, ret, max_results=3)
            if offers:
                best = offers[0]
                threshold = get_alert_threshold(origin, dest)
                flag = "🔥" if best["price"] <= threshold else "  "
                print(f"  {flag} {dep}→{ret}  ¥{best['price']:.0f}  {best['airline']}")
                if not dry_run:
                    async with AsyncSessionLocal() as session:
                        await save_snapshot(
                            session, origin, dest, dep, ret,
                            best["price"], best["currency"], best["raw"]
                        )
                        await session.commit()
            else:
                print(f"     {dep}→{ret}  暂无报价")
    else:
        # 全量扫描
        if dry_run:
            print("⚠️  dry-run 模式下全量扫描会调用 API 但不写库")
        async with AsyncSessionLocal() as session:
            stats = await run_price_scan(session)
        print(f"\n✅ 扫描完成: {stats}")


def main() -> None:
    parser = argparse.ArgumentParser(description="机票特价手动扫描")
    parser.add_argument("--origin", help="出发机场 IATA，如 SHA")
    parser.add_argument("--dest", help="目的机场 IATA，如 TYO")
    parser.add_argument("--dry-run", action="store_true", help="只查询，不写数据库")
    args = parser.parse_args()

    asyncio.run(run(args.origin, args.dest, args.dry_run))


if __name__ == "__main__":
    main()
