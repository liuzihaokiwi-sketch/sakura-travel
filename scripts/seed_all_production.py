"""
seed_all_production.py — 8 城市圈全量数据采集

调用 catalog/pipeline.py 的 run_city_pipeline 为每个城市生成/爬取数据。
网络可用时走真实爬虫（OSM/Tabelog），不可用时走 AI 生成。

用法：
    # 全部城市圈
    python scripts/seed_all_production.py

    # 只跑某个圈
    python scripts/seed_all_production.py --circle kansai

    # 只跑某个城市
    python scripts/seed_all_production.py --city tokyo

    # 强制 AI 生成（不检查网络）
    python scripts/seed_all_production.py --force-ai

    # 自定义数量（每类别）
    python scripts/seed_all_production.py --poi-count 10 --restaurant-count 8 --hotel-count 5

    # 断点续跑（跳过上次已成功的城市）
    python scripts/seed_all_production.py --resume
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import AsyncSessionLocal
from app.domains.catalog.pipeline import run_city_pipeline

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

PROGRESS_FILE = DATA_DIR / "seed_progress.json"

# ── logging: stdout + 文件双写，屏蔽 sqlalchemy SQL 噪音 ──────────────────

_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
_log_file = LOG_DIR / f"seed_{_ts}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(str(_log_file), encoding="utf-8"),
    ],
)
# 屏蔽 sqlalchemy 的 SQL 日志，让关键进度信息清晰可见
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
logger.info("日志文件: %s", _log_file)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 城市圈 → 城市列表
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CIRCLE_CITIES: dict[str, list[str]] = {
    "kansai": [
        "kyoto", "osaka", "nara", "kobe", "uji", "arima_onsen",
    ],
    "kanto": [
        "tokyo", "yokohama", "kamakura", "hakone", "nikko", "kawaguchiko",
    ],
    "hokkaido": [
        "sapporo", "otaru", "hakodate", "noboribetsu", "furano", "biei",
        "asahikawa", "toya",
    ],
    "guangfu": [
        "guangzhou", "shenzhen", "hongkong", "macau", "zhuhai", "foshan",
    ],
    "xinjiang": [
        "urumqi", "yili", "altay", "burqin", "kanas", "hemu",
        "nalati", "sailimu",
    ],
    "guangdong": [
        "chaozhou", "shantou", "meizhou", "zhaoqing", "shaoguan",
        "qingyuan", "jiangmen",
    ],
    "huadong": [
        "shanghai", "hangzhou", "suzhou", "nanjing", "wuxi",
        "wuzhen", "xitang", "zhoushan", "huangshan", "moganshan",
    ],
}

# 每个城市的采集规模（每类别生成数量）
# 核心城市多生成，边缘城市少生成
CITY_SCALE: dict[str, dict[str, int]] = {
    # 核心大城市：每类别 10-12 条
    "tokyo":     {"poi": 12, "restaurant": 10, "hotel": 6},
    "osaka":     {"poi": 10, "restaurant": 10, "hotel": 5},
    "kyoto":     {"poi": 12, "restaurant": 10, "hotel": 5},
    "guangzhou":  {"poi": 10, "restaurant": 12, "hotel": 5},
    "shenzhen":   {"poi": 8,  "restaurant": 10, "hotel": 5},
    "hongkong":   {"poi": 10, "restaurant": 12, "hotel": 6},
    "sapporo":    {"poi": 10, "restaurant": 8,  "hotel": 5},
    # 重要中等城市：每类别 6-8 条
    "yokohama":   {"poi": 6, "restaurant": 6, "hotel": 3},
    "kobe":       {"poi": 6, "restaurant": 6, "hotel": 3},
    "nara":       {"poi": 6, "restaurant": 6, "hotel": 2},
    "macau":      {"poi": 6, "restaurant": 8, "hotel": 3},
    "hakodate":   {"poi": 6, "restaurant": 6, "hotel": 3},
    "urumqi":     {"poi": 6, "restaurant": 6, "hotel": 3},
    "yili":       {"poi": 6, "restaurant": 5, "hotel": 3},
    "foshan":     {"poi": 5, "restaurant": 8, "hotel": 2},
    "chaozhou":   {"poi": 5, "restaurant": 8, "hotel": 2},
    "shantou":    {"poi": 5, "restaurant": 8, "hotel": 2},
    # 日归/小城市：每类别 3-5 条
    "kamakura":   {"poi": 5, "restaurant": 4, "hotel": 1},
    "hakone":     {"poi": 5, "restaurant": 3, "hotel": 3},
    "nikko":      {"poi": 5, "restaurant": 3, "hotel": 2},
    "kawaguchiko": {"poi": 4, "restaurant": 3, "hotel": 2},
    "uji":        {"poi": 4, "restaurant": 3, "hotel": 1},
    "arima_onsen": {"poi": 3, "restaurant": 3, "hotel": 3},
    "otaru":      {"poi": 5, "restaurant": 5, "hotel": 2},
    "noboribetsu": {"poi": 3, "restaurant": 2, "hotel": 3},
    "furano":     {"poi": 4, "restaurant": 3, "hotel": 2},
    "biei":       {"poi": 4, "restaurant": 2, "hotel": 1},
    "asahikawa":  {"poi": 4, "restaurant": 3, "hotel": 2},
    "toya":       {"poi": 3, "restaurant": 2, "hotel": 2},
    "zhuhai":     {"poi": 4, "restaurant": 4, "hotel": 2},
    "altay":      {"poi": 4, "restaurant": 3, "hotel": 2},
    "burqin":     {"poi": 3, "restaurant": 2, "hotel": 2},
    "kanas":      {"poi": 4, "restaurant": 2, "hotel": 2},
    "hemu":       {"poi": 3, "restaurant": 2, "hotel": 2},
    "nalati":     {"poi": 4, "restaurant": 2, "hotel": 2},
    "sailimu":    {"poi": 3, "restaurant": 1, "hotel": 1},
    "meizhou":    {"poi": 4, "restaurant": 5, "hotel": 2},
    "zhaoqing":   {"poi": 4, "restaurant": 4, "hotel": 2},
    "shaoguan":   {"poi": 4, "restaurant": 3, "hotel": 2},
    "qingyuan":   {"poi": 4, "restaurant": 3, "hotel": 2},
    "jiangmen":   {"poi": 4, "restaurant": 4, "hotel": 2},
    "karuizawa":  {"poi": 4, "restaurant": 3, "hotel": 2},
    # 华东圈
    "shanghai":   {"poi": 12, "restaurant": 12, "hotel": 6},
    "hangzhou":   {"poi": 10, "restaurant": 10, "hotel": 5},
    "suzhou":     {"poi": 8,  "restaurant": 8,  "hotel": 4},
    "nanjing":    {"poi": 8,  "restaurant": 8,  "hotel": 4},
    "wuxi":       {"poi": 6,  "restaurant": 6,  "hotel": 3},
    "wuzhen":     {"poi": 4,  "restaurant": 3,  "hotel": 2},
    "xitang":     {"poi": 3,  "restaurant": 2,  "hotel": 2},
    "zhoushan":   {"poi": 4,  "restaurant": 4,  "hotel": 3},
    "huangshan":  {"poi": 5,  "restaurant": 3,  "hotel": 3},
    "moganshan":  {"poi": 3,  "restaurant": 2,  "hotel": 3},
}

DEFAULT_SCALE = {"poi": 5, "restaurant": 5, "hotel": 3}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 进度持久化
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _load_progress() -> dict:
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
    return {"cities": {}, "started_at": None, "updated_at": None}


def _save_progress(progress: dict):
    progress["updated_at"] = datetime.now(timezone.utc).isoformat()
    PROGRESS_FILE.write_text(
        json.dumps(progress, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _city_done(progress: dict, city: str) -> bool:
    entry = progress["cities"].get(city, {})
    return entry.get("status") == "ok"


def _record_city(progress: dict, city: str, circle: str, stats: dict):
    progress["cities"][city] = {
        "circle": circle,
        "status": "ok",
        "pois": stats.get("pois", 0),
        "restaurants": stats.get("restaurants", 0),
        "hotels": stats.get("hotels", 0),
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_progress(progress)


def _record_city_error(progress: dict, city: str, circle: str, error: str):
    progress["cities"][city] = {
        "circle": circle,
        "status": "error",
        "error": error,
        "failed_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_progress(progress)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 采集逻辑
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def seed_circle(circle_name: str, force_ai: bool = False,
                      resume: bool = False,
                      poi_override: int | None = None,
                      rest_override: int | None = None,
                      hotel_override: int | None = None,
                      _global_counter: dict | None = None):
    """
    采集一个城市圈的所有城市。

    _global_counter: 跨圈共享的进度计数器 {"done": n, "total": m}，用于全量采集时显示总进度。
    """
    cities = CIRCLE_CITIES.get(circle_name)
    if not cities:
        logger.error("未知城市圈: %s (可选: %s)", circle_name, list(CIRCLE_CITIES.keys()))
        return

    progress = _load_progress()
    if not progress["started_at"]:
        progress["started_at"] = datetime.now(timezone.utc).isoformat()
        _save_progress(progress)

    logger.info("=" * 60)
    logger.info("开始采集城市圈: %s (%d 个城市)", circle_name, len(cities))
    logger.info("=" * 60)

    all_stats = []
    import time as _time
    async with AsyncSessionLocal() as session:
        for i, city in enumerate(cities, 1):
            gc = _global_counter or {}
            global_idx = gc.get("done", 0) + 1
            global_total = gc.get("total", len(cities))
            prefix = f"[{global_idx}/{global_total}]"

            # 断点续跑：跳过已成功的
            if resume and _city_done(progress, city):
                logger.info("%s %s — 已完成，跳过", prefix, city)
                if _global_counter is not None:
                    _global_counter["done"] += 1
                continue

            scale = CITY_SCALE.get(city, DEFAULT_SCALE)
            poi_count = poi_override or scale["poi"]
            rest_count = rest_override or scale["restaurant"]
            hotel_count = hotel_override or scale["hotel"]

            logger.info("%s %s: poi=%d restaurant=%d hotel=%d",
                        prefix, city, poi_count, rest_count, hotel_count)
            t0 = _time.time()
            try:
                stats = await run_city_pipeline(
                    session=session,
                    city_code=city,
                    force_ai=force_ai,
                    poi_count=poi_count,
                    restaurant_count=rest_count,
                    hotel_count=hotel_count,
                )
                all_stats.append(stats)
                await session.commit()
                elapsed = _time.time() - t0
                err_count = len(stats.get("errors", []))
                status_icon = "✅" if not err_count else "⚠️"
                logger.info(
                    "%s %s: POI=%d 餐厅=%d 酒店=%d (%.1fs) %s",
                    prefix, city,
                    stats.get("pois", 0),
                    stats.get("restaurants", 0),
                    stats.get("hotels", 0),
                    elapsed,
                    status_icon,
                )
                if err_count:
                    for e in stats.get("errors", []):
                        logger.warning("    ↳ %s", e)
                _record_city(progress, city, circle_name, stats)
            except Exception as exc:
                tb = traceback.format_exc()
                elapsed = _time.time() - t0
                logger.error("%s %s: 失败 (%.1fs) ❌  %s\n%s",
                             prefix, city, elapsed, exc, tb)
                await session.rollback()
                all_stats.append({"city": city, "error": str(exc)})
                _record_city_error(progress, city, circle_name, str(exc))

            if _global_counter is not None:
                _global_counter["done"] += 1

            await asyncio.sleep(15)  # 城市间间隔 15 秒，避免 API 封 IP

    # 汇总
    total_pois = sum(s.get("pois", 0) for s in all_stats)
    total_rests = sum(s.get("restaurants", 0) for s in all_stats)
    total_hotels = sum(s.get("hotels", 0) for s in all_stats)
    errors = [s for s in all_stats if "error" in s]

    logger.info("=" * 60)
    logger.info("城市圈 %s 采集完成", circle_name)
    logger.info("  POI: %d  餐厅: %d  酒店: %d  总计: %d",
                total_pois, total_rests, total_hotels,
                total_pois + total_rests + total_hotels)
    if errors:
        logger.warning("  失败城市: %s", [e["city"] for e in errors])
    logger.info("=" * 60)


async def seed_city(city_code: str, force_ai: bool = False,
                    poi_override: int | None = None,
                    rest_override: int | None = None,
                    hotel_override: int | None = None):
    """采集单个城市。"""
    scale = CITY_SCALE.get(city_code, DEFAULT_SCALE)
    poi_count = poi_override or scale["poi"]
    rest_count = rest_override or scale["restaurant"]
    hotel_count = hotel_override or scale["hotel"]

    progress = _load_progress()
    if not progress["started_at"]:
        progress["started_at"] = datetime.now(timezone.utc).isoformat()
        _save_progress(progress)

    async with AsyncSessionLocal() as session:
        stats = await run_city_pipeline(
            session=session,
            city_code=city_code,
            force_ai=force_ai,
            poi_count=poi_count,
            restaurant_count=rest_count,
            hotel_count=hotel_count,
        )
        await session.commit()

    logger.info("完成: %s — POI=%d 餐厅=%d 酒店=%d",
                city_code, stats.get("pois", 0),
                stats.get("restaurants", 0), stats.get("hotels", 0))
    _record_city(progress, city_code, "single", stats)


async def seed_all(force_ai: bool = False, resume: bool = False, **kwargs):
    """采集所有城市圈。"""
    import time as _time
    total_cities = sum(len(v) for v in CIRCLE_CITIES.values())
    counter = {"done": 0, "total": total_cities}
    t_start = _time.time()

    for circle_name in CIRCLE_CITIES:
        await seed_circle(
            circle_name,
            force_ai=force_ai,
            resume=resume,
            _global_counter=counter,
            **kwargs,
        )

    elapsed_min = (_time.time() - t_start) / 60
    logger.info("全量采集完成，总耗时 %.1f 分钟", elapsed_min)
    # 全部跑完后生成汇总报告
    _write_report()


def _write_report():
    """从 progress.json 生成可读的汇总报告。"""
    progress = _load_progress()
    cities = progress.get("cities", {})
    if not cities:
        return

    ok = {k: v for k, v in cities.items() if v["status"] == "ok"}
    failed = {k: v for k, v in cities.items() if v["status"] == "error"}

    total_pois = sum(v.get("pois", 0) for v in ok.values())
    total_rests = sum(v.get("restaurants", 0) for v in ok.values())
    total_hotels = sum(v.get("hotels", 0) for v in ok.values())

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "started_at": progress.get("started_at"),
        "summary": {
            "total_cities": len(cities),
            "succeeded": len(ok),
            "failed": len(failed),
            "pois": total_pois,
            "restaurants": total_rests,
            "hotels": total_hotels,
            "entities_total": total_pois + total_rests + total_hotels,
        },
        "failed_cities": {k: v["error"] for k, v in failed.items()},
        "per_circle": {},
    }

    # 按圈汇总
    for city, info in ok.items():
        circle = info.get("circle", "unknown")
        bucket = report["per_circle"].setdefault(circle, {
            "cities": 0, "pois": 0, "restaurants": 0, "hotels": 0,
        })
        bucket["cities"] += 1
        bucket["pois"] += info.get("pois", 0)
        bucket["restaurants"] += info.get("restaurants", 0)
        bucket["hotels"] += info.get("hotels", 0)

    report_file = LOG_DIR / f"seed_report_{_ts}.json"
    report_file.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("汇总报告已写入: %s", report_file)

    # 打印摘要到日志
    logger.info("=" * 60)
    logger.info("=== 采集完成 ===")
    logger.info("  成功: %d/%d 城市", len(ok), len(cities))
    logger.info("  失败: %d 城市", len(failed))
    logger.info("  实体: POI=%d  餐厅=%d  酒店=%d  总计=%d",
                total_pois, total_rests, total_hotels,
                total_pois + total_rests + total_hotels)
    if failed:
        logger.warning("  失败城市: %s", list(failed.keys()))
        logger.info("  可用 --resume 重跑失败城市")
    logger.info("  报告文件: %s", report_file)
    logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="8 城市圈全量数据采集")
    parser.add_argument("--circle", help="只采集指定城市圈")
    parser.add_argument("--city", help="只采集指定城市")
    parser.add_argument("--force-ai", action="store_true", help="强制 AI 生成（不检查网络）")
    parser.add_argument("--resume", action="store_true",
                        help="断点续跑，跳过 seed_progress.json 中已成功的城市")
    parser.add_argument("--report", action="store_true",
                        help="只生成汇总报告（不采集）")
    parser.add_argument("--poi-count", type=int, help="覆盖每类别 POI 数量")
    parser.add_argument("--restaurant-count", type=int, help="覆盖每类别餐厅数量")
    parser.add_argument("--hotel-count", type=int, help="覆盖每档位酒店数量")

    args = parser.parse_args()

    if args.report:
        _write_report()
        return

    kwargs = {}
    if args.poi_count:
        kwargs["poi_override"] = args.poi_count
    if args.restaurant_count:
        kwargs["rest_override"] = args.restaurant_count
    if args.hotel_count:
        kwargs["hotel_override"] = args.hotel_count

    if args.city:
        asyncio.run(seed_city(args.city, force_ai=args.force_ai, **kwargs))
    elif args.circle:
        asyncio.run(seed_circle(args.circle, force_ai=args.force_ai,
                                resume=args.resume, **kwargs))
    else:
        asyncio.run(seed_all(force_ai=args.force_ai, resume=args.resume, **kwargs))


if __name__ == "__main__":
    main()
