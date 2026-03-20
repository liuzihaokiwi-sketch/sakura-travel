#!/usr/bin/env python3
"""
机票特价扫描 CLI — 纯爬虫，无需 API Key
==========================================

数据源：
  1. Skyscanner 内部 API（主力，覆盖全球 1000+ 航司含廉航）
  2. Google Flights（补充，GDS 全量数据）

用法：
  # 扫描默认航线（中国 5 城 → 日本 3 城，共 15 条航线）
  python scripts/flight_crawl.py

  # 指定航线
  python scripts/flight_crawl.py --origin SHA --dest TYO

  # 多条航线
  python scripts/flight_crawl.py --origin SHA PEK --dest TYO OSA

  # 扫描未来 6 个月
  python scripts/flight_crawl.py --months 6

  # 只用 Skyscanner（默认，最快）
  python scripts/flight_crawl.py --source skyscanner

  # 同时用 Google Flights 补充
  python scripts/flight_crawl.py --source all

  # 只看特价
  python scripts/flight_crawl.py --deals-only

  # 写入数据库
  python scripts/flight_crawl.py --write-db

  # 触发通知（企业微信/邮件）
  python scripts/flight_crawl.py --notify
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


async def main(args: argparse.Namespace) -> None:
    from scripts.crawlers.skyscanner import (
        SkyscannerCrawler,
        DEFAULT_ROUTES,
        DEAL_THRESHOLDS,
        AIRPORT_NAMES,
    )

    # 构建航线列表
    if args.origin and args.dest:
        routes = [(o, d) for o in args.origin for d in args.dest]
    else:
        routes = DEFAULT_ROUTES

    all_deals = []

    # ── 天巡 Playwright（主力推荐）─────────────────────────────────────────
    if args.source in ("tianxun", "all"):
        from scripts.crawlers.tianxun import TianxunFlightCrawler
        from datetime import date as _date, timedelta as _td

        # 生成搜索日期（未来2-8周的周六出发，下周日回）
        today = _date.today()
        dep_date = (today + _td(weeks=4)).strftime("%Y-%m-%d")
        ret_date = (today + _td(weeks=4, days=6)).strftime("%Y-%m-%d")

        async with TianxunFlightCrawler(
            output_dir=args.output_dir,
            headless=not getattr(args, 'headed', False),
        ) as crawler:
            results = await crawler.scan_all_routes(
                routes=routes,
                dep_date=dep_date,
                ret_date=ret_date,
                save_json=True,
            )

            for route_key, quotes in results.items():
                threshold = DEAL_THRESHOLDS.get(route_key, DEAL_THRESHOLDS["_default"])
                for q in quotes:
                    if q["price"] <= threshold:
                        q["route_key"] = route_key
                        q["deal_threshold"] = threshold
                        all_deals.append(q)

    # ── Skyscanner HTTP（备用）────────────────────────────────────────────
    if args.source == "skyscanner":
        async with SkyscannerCrawler(
            output_dir=args.output_dir,
            delay_range=tuple(args.delay),
        ) as crawler:
            results = await crawler.scan_all_routes(
                routes=routes,
                months_ahead=args.months,
                save_json=True,
            )

            for route_key, quotes in results.items():
                threshold = DEAL_THRESHOLDS.get(route_key, DEAL_THRESHOLDS["_default"])
                for q in quotes:
                    if q["price"] <= threshold:
                        q["route_key"] = route_key
                        q["deal_threshold"] = threshold
                        all_deals.append(q)

    # ── Google Flights（补充）─────────────────────────────────────────────
    if args.source in ("google", "all"):
        from scripts.crawlers.google_flights import GoogleFlightsCrawler
        from datetime import date, timedelta

        async with GoogleFlightsCrawler(output_dir=args.output_dir) as g_crawler:
            # 对每条航线查几个关键日期（往返，5-7天行程）
            today = date.today()
            sample_windows = [
                (today + timedelta(weeks=w), today + timedelta(weeks=w, days=6))
                for w in [2, 4, 6, 8]
            ]
            for origin, dest in routes[:5]:  # 限制数量，Google 较慢
                for dep_dt, ret_dt in sample_windows:
                    dep_date = dep_dt.strftime("%Y-%m-%d")
                    ret_date = ret_dt.strftime("%Y-%m-%d")
                    flights = await g_crawler.search_flights(origin, dest, dep_date, ret_date)
                    for f in flights:
                        route_key = f"{origin}-{dest}"
                        threshold = DEAL_THRESHOLDS.get(route_key, DEAL_THRESHOLDS.get("_default", 1800))
                        if f["price"] <= threshold:
                            f["route_key"] = route_key
                            f["deal_threshold"] = threshold
                            all_deals.append(f)

    # ── 结果汇总 ──────────────────────────────────────────────────────────
    all_deals.sort(key=lambda x: x["price"])

    print("\n" + "=" * 65)
    if all_deals:
        print(f"💥 发现 {len(all_deals)} 个特价机票！")
        print("-" * 65)
        for d in all_deals[:20]:
            o = AIRPORT_NAMES.get(d["origin"], d["origin"])
            t = AIRPORT_NAMES.get(d["destination"], d["destination"])
            direct = "直飞" if d.get("is_direct") else "转机"
            dep = d.get("departure_date") or "灵活"
            src = d.get("source", "?")[:10]
            print(f"  ¥{d['price']:>6.0f}  {o}→{t}  {dep}  {direct}  [{src}]")
    else:
        print("📭 暂无特价（低于阈值的航班），可调高 --months 扫描更多月份")
    print("=" * 65)

    # ── 写入数据库 ────────────────────────────────────────────────────────
    if args.write_db and all_deals:
        await _write_deals_to_db(all_deals)

    # ── 触发通知 ──────────────────────────────────────────────────────────
    if args.notify and all_deals:
        await _send_notifications(all_deals[:5])


async def _write_deals_to_db(deals: list) -> None:
    """写入 flight_offer_snapshots"""
    try:
        from app.domains.flights.price_monitor import save_snapshot
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            for d in deals:
                await save_snapshot(
                    session,
                    origin=d["origin"],
                    destination=d["destination"],
                    departure_date=d.get("departure_date", ""),
                    return_date=d.get("return_date"),
                    price=d["price"],
                    currency=d.get("currency", "CNY"),
                    raw_payload=d,
                )
            await session.commit()
            logger.info(f"✅ 写入数据库: {len(deals)} 条")
    except Exception as e:
        logger.error(f"❌ 写入数据库失败: {e}")


async def _send_notifications(deals: list) -> None:
    """发送特价通知"""
    try:
        from scripts.crawlers.skyscanner import SkyscannerCrawler

        for d in deals:
            msg = SkyscannerCrawler.format_deal_message(d)
            # 尝试企业微信
            try:
                from app.domains.flights.notifier import send_wecom_alert
                await send_wecom_alert(msg)
            except ImportError:
                print(f"\n📱 通知内容:\n{msg}\n")
    except Exception as e:
        logger.error(f"❌ 通知发送失败: {e}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="机票特价扫描（纯爬虫，无需 API Key）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--origin", nargs="+", type=str,
        help="出发城市 IATA 代码（如 SHA PEK CAN）",
    )
    parser.add_argument(
        "--dest", nargs="+", type=str,
        help="目的城市 IATA 代码（如 TYO OSA NGO）",
    )
    parser.add_argument(
        "--months", type=int, default=3,
        help="扫描未来几个月（默认 3）",
    )
    parser.add_argument(
        "--source", type=str, default="tianxun",
        choices=["tianxun", "google", "skyscanner", "all"],
        help="数据源（默认 tianxun；all=天巡+Google 都用）",
    )
    parser.add_argument(
        "--headed", action="store_true",
        help="显示浏览器窗口（调试用，仅天巡）",
    )
    parser.add_argument(
        "--deals-only", action="store_true",
        help="只显示特价",
    )
    parser.add_argument(
        "--delay", type=float, nargs=2, default=[1.5, 3.5],
        metavar=("MIN", "MAX"),
        help="请求延迟范围/秒（默认 1.5 3.5）",
    )
    parser.add_argument(
        "--output-dir", type=str, default="data/flights_raw",
        help="输出目录",
    )
    parser.add_argument(
        "--write-db", action="store_true",
        help="写入数据库",
    )
    parser.add_argument(
        "--notify", action="store_true",
        help="发现特价时推送通知",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="详细日志",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    asyncio.run(main(args))
