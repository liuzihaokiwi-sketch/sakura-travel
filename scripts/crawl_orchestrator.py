#!/usr/bin/env python3
"""
🕷️ 全日本数据并行爬取调度器 (Autonomous Crawler Orchestrator)
==============================================================

特性:
  ✅ 完全自治 — 断开 IDE 连接也能持续运行
  ✅ 自适应速率 — 成功率下降自动减速，恢复后加速
  ✅ 最大并行 — 不同站点并行爬取，同站点限速
  ✅ 断点续传 — 进度持久化到 JSON，重启后继续
  ✅ 实时日志 — 写入 logs/crawler_orchestrator.log
  ✅ 状态面板 — 定期输出汇总到 data/crawl_status.json

用法:
  # 启动全量爬取（后台运行）
  python scripts/crawl_orchestrator.py

  # 只跑 P0 优先级
  python scripts/crawl_orchestrator.py --priority P0

  # 只跑酒店任务
  python scripts/crawl_orchestrator.py --type hotel

  # 查看当前进度
  python scripts/crawl_orchestrator.py --status

  # 重置某个任务
  python scripts/crawl_orchestrator.py --reset hotel_osaka_booking
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import signal
import sys
import time
import traceback
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Awaitable

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# ── 日志配置 ─────────────────────────────────────────────────────────────────

LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

log_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

file_handler = logging.FileHandler(LOG_DIR / "crawler_orchestrator.log", encoding="utf-8")
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s", datefmt="%H:%M:%S"))
console_handler.setLevel(logging.INFO)

logger = logging.getLogger("orchestrator")
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# ── 状态持久化路径 ────────────────────────────────────────────────────────────

DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
STATUS_FILE = DATA_DIR / "crawl_status.json"
PROGRESS_FILE = DATA_DIR / "crawl_progress.json"


# ── 自适应速率控制器 ─────────────────────────────────────────────────────────

class AdaptiveRateController:
    """
    根据成功率动态调整爬取速度。

    - 成功率 > 90%: 逐步加速 (减少延迟)
    - 成功率 70-90%: 保持当前速度
    - 成功率 50-70%: 减速 50%
    - 成功率 < 50%: 大幅减速 + 暂停一段时间
    - 连续失败 > threshold: 自动暂停该站点
    """

    def __init__(
        self,
        site_name: str,
        initial_delay: float = 2.0,
        min_delay: float = 0.5,
        max_delay: float = 30.0,
        window_size: int = 20,
        pause_threshold: int = 10,
    ):
        self.site_name = site_name
        self.delay = initial_delay
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.window_size = window_size
        self.pause_threshold = pause_threshold

        self._results: list[bool] = []  # True=success, False=fail
        self._consecutive_fails = 0
        self._paused = False
        self._pause_until: float = 0

    @property
    def success_rate(self) -> float:
        if not self._results:
            return 1.0
        recent = self._results[-self.window_size:]
        return sum(recent) / len(recent)

    @property
    def is_paused(self) -> bool:
        if self._paused and time.time() >= self._pause_until:
            self._paused = False
            self._consecutive_fails = 0
            logger.info(f"⏯️  [{self.site_name}] 暂停结束，恢复爬取 (delay={self.delay:.1f}s)")
        return self._paused

    def record_success(self):
        self._results.append(True)
        self._consecutive_fails = 0
        self._adjust()

    def record_failure(self):
        self._results.append(False)
        self._consecutive_fails += 1
        self._adjust()

        if self._consecutive_fails >= self.pause_threshold:
            pause_secs = min(300, 30 * (self._consecutive_fails // self.pause_threshold))
            self._paused = True
            self._pause_until = time.time() + pause_secs
            logger.warning(
                f"⏸️  [{self.site_name}] 连续失败 {self._consecutive_fails} 次，"
                f"暂停 {pause_secs}s (delay={self.delay:.1f}s)"
            )

    def _adjust(self):
        rate = self.success_rate
        old = self.delay

        if rate > 0.9:
            # 加速
            self.delay = max(self.min_delay, self.delay * 0.9)
        elif rate > 0.7:
            # 保持
            pass
        elif rate > 0.5:
            # 减速
            self.delay = min(self.max_delay, self.delay * 1.5)
        else:
            # 大幅减速
            self.delay = min(self.max_delay, self.delay * 2.0)

        if abs(old - self.delay) > 0.3:
            logger.debug(
                f"🎚️  [{self.site_name}] 速率调整: {old:.1f}s → {self.delay:.1f}s "
                f"(成功率={rate:.0%})"
            )

    async def wait(self):
        """等待自适应延迟"""
        if self.is_paused:
            wait_time = self._pause_until - time.time()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        import random
        jitter = random.uniform(0.5, 1.5)
        await asyncio.sleep(self.delay * jitter)

    def status(self) -> dict:
        return {
            "site": self.site_name,
            "delay": round(self.delay, 2),
            "success_rate": round(self.success_rate, 3),
            "total_requests": len(self._results),
            "consecutive_fails": self._consecutive_fails,
            "paused": self._paused,
        }


# ── 任务定义 ─────────────────────────────────────────────────────────────────

@dataclass
class CrawlTask:
    """一个爬取任务"""
    task_id: str
    priority: str          # P0 / P1 / P2 / P3
    task_type: str         # hotel / poi / restaurant / guide / event / experience
    site: str              # booking / ctrip / tabelog / jnto / ...
    city: str              # tokyo / osaka / ...
    description: str
    pages: int = 5         # 爬取页数
    status: str = "pending"  # pending / running / done / failed / skipped
    items_count: int = 0
    error: str = ""
    started_at: str = ""
    finished_at: str = ""
    retry_count: int = 0


# ── 全部任务列表 ─────────────────────────────────────────────────────────────

# 城市列表
P0_CITIES = ["tokyo", "osaka", "kyoto"]
P1_CITIES = ["okinawa", "fukuoka", "sapporo", "hakone", "nagoya", "kobe", "nara", "yokohama"]
P2_CITIES = [
    "hiroshima", "sendai", "kanazawa", "kamakura", "takayama",
    "nagasaki", "beppu", "nikko", "karuizawa", "kawaguchiko",
    "otaru", "hakodate", "kumamoto", "naoshima", "furano",
]
P3_CITIES = [
    "shirakawago", "shimonoseki", "takamatsu", "matsuyama",
    "yakushima", "ishigaki", "miyakojima", "niigata",
    "izu", "kurashiki", "saga", "aomori",
    "akita", "tottori", "matsumoto", "kamikochi",
    "uji", "kusatsu", "kinosaki", "ise", "kagoshima",
]

HOTEL_PLATFORMS = ["booking", "ctrip", "agoda", "jalan"]


def generate_all_tasks() -> list[CrawlTask]:
    """生成全部爬取任务"""
    tasks: list[CrawlTask] = []
    task_id = 0

    def add(priority, task_type, site, city, desc, pages=5):
        nonlocal task_id
        task_id += 1
        tasks.append(CrawlTask(
            task_id=f"{task_type}_{city}_{site}_{task_id:04d}",
            priority=priority,
            task_type=task_type,
            site=site,
            city=city,
            description=desc,
            pages=pages,
        ))

    # ── P0: 核心城市 ──────────────────────────────────────────────
    for city in P0_CITIES:
        for plat in HOTEL_PLATFORMS:
            add("P0", "hotel", plat, city, f"{city} 酒店 ({plat})", pages=10)
        add("P0", "restaurant", "tabelog", city, f"{city} 餐厅 (Tabelog)", pages=10)
        add("P0", "poi", "jnto", city, f"{city} 景点 (JNTO)", pages=5)
        add("P0", "poi", "google", city, f"{city} 景点 (Google Places)", pages=5)
        add("P0", "event", "japan_guide", city, f"{city} 活动 (japan-guide)", pages=3)

    # P0: 攻略源
    add("P0", "guide", "letsgojp", "all", "樂吃購 全站攻略", pages=20)
    add("P0", "guide", "matcha", "all", "MATCHA 全站攻略", pages=20)
    add("P0", "guide", "mafengwo", "all", "马蜂窝 日本攻略", pages=30)
    add("P0", "guide", "xiaohongshu", "all", "小红书 日本攻略", pages=20)

    # P0: 日本官方
    add("P0", "official", "jnto", "all", "JNTO 全站目的地", pages=10)
    add("P0", "official", "gotokyo", "tokyo", "GO TOKYO 全站", pages=10)
    add("P0", "official", "osaka_info", "osaka", "大阪观光局", pages=10)
    add("P0", "official", "kyoto_travel", "kyoto", "京都观光协会", pages=10)

    # P0: 活动/节庆
    add("P0", "event", "walker_hanabi", "all", "花火大会 (Walker Plus)", pages=5)
    add("P0", "event", "walker_illumination", "all", "冬季灯光秀 (Walker Plus)", pages=5)
    add("P0", "event", "sakura", "all", "樱花前线", pages=3)

    # ── P1: 热门城市 ──────────────────────────────────────────────
    for city in P1_CITIES:
        for plat in HOTEL_PLATFORMS:
            add("P1", "hotel", plat, city, f"{city} 酒店 ({plat})", pages=8)
        add("P1", "restaurant", "tabelog", city, f"{city} 餐厅 (Tabelog)", pages=5)
        add("P1", "poi", "jnto", city, f"{city} 景点 (JNTO)", pages=3)

    # P1: 额外攻略源
    add("P1", "guide", "ctrip_guide", "all", "携程攻略 日本", pages=20)
    add("P1", "guide", "qyer", "all", "穷游 日本攻略", pages=15)

    # P1: 体验
    for city in P0_CITIES + ["okinawa", "hakone"]:
        add("P1", "experience", "veltra", city, f"{city} 体验 (VELTRA)", pages=5)
        add("P1", "experience", "kkday", city, f"{city} 体验 (KKday)", pages=5)
        add("P1", "experience", "klook", city, f"{city} 体验 (Klook)", pages=5)

    # P1: 官方观光
    add("P1", "official", "visit_hokkaido", "sapporo", "北海道观光", pages=5)
    add("P1", "official", "visit_okinawa", "okinawa", "冲绳观光", pages=5)

    # P1: 红叶
    add("P1", "event", "koyo", "all", "红叶前线 (Walker Plus)", pages=3)

    # ── P2: 进阶城市 ──────────────────────────────────────────────
    for city in P2_CITIES:
        for plat in ["booking", "jalan"]:  # P2 只用两个主平台
            add("P2", "hotel", plat, city, f"{city} 酒店 ({plat})", pages=5)
        add("P2", "restaurant", "tabelog", city, f"{city} 餐厅 (Tabelog)", pages=3)

    # P2: 攻略补全
    add("P2", "guide", "pixnet", "all", "痞客邦 日本游记", pages=10)
    add("P2", "guide", "tripadvisor", "all", "TripAdvisor 日本排行", pages=10)

    # ── P3: 小众城市 ──────────────────────────────────────────────
    for city in P3_CITIES:
        add("P3", "hotel", "booking", city, f"{city} 酒店 (Booking)", pages=3)
        add("P3", "hotel", "jalan", city, f"{city} 酒店 (Jalan)", pages=3)

    return tasks


# ── 任务执行器 ────────────────────────────────────────────────────────────────

class TaskExecutor:
    """执行单个爬取任务，调用对应的爬虫模块"""

    def __init__(self, rate_controllers: dict[str, AdaptiveRateController]):
        self.rate_controllers = rate_controllers

    def _get_controller(self, site: str) -> AdaptiveRateController:
        if site not in self.rate_controllers:
            self.rate_controllers[site] = AdaptiveRateController(site)
        return self.rate_controllers[site]

    async def execute(self, task: CrawlTask) -> CrawlTask:
        """执行任务，返回更新后的任务"""
        ctrl = self._get_controller(task.site)
        task.status = "running"
        task.started_at = datetime.now().isoformat()

        try:
            # 等待自适应延迟
            if ctrl.is_paused:
                await ctrl.wait()

            items = await self._dispatch(task, ctrl)
            task.items_count = items
            task.status = "done"
            ctrl.record_success()
            logger.info(
                f"✅ [{task.task_id}] 完成: {items} 条 "
                f"(速率: {ctrl.delay:.1f}s, 成功率: {ctrl.success_rate:.0%})"
            )

        except NotImplementedError:
            task.status = "skipped"
            task.error = "爬虫未实现"
            logger.warning(f"⏭️  [{task.task_id}] 跳过: 爬虫未实现 ({task.site})")

        except Exception as e:
            task.status = "failed"
            task.error = str(e)[:200]
            task.retry_count += 1
            ctrl.record_failure()
            logger.error(
                f"❌ [{task.task_id}] 失败: {e} "
                f"(重试次数: {task.retry_count}, 速率: {ctrl.delay:.1f}s)"
            )

        task.finished_at = datetime.now().isoformat()
        return task

    async def _dispatch(self, task: CrawlTask, ctrl: AdaptiveRateController) -> int:
        """根据 task 类型分发到对应爬虫"""
        site = task.site
        city = task.city
        pages = task.pages

        # ── 酒店 ──────────────────────────────────────────────────────
        if task.task_type == "hotel" and site in ("booking", "ctrip", "agoda", "jalan"):
            from scripts.crawlers.hotels import HotelCrawler, CITY_CONFIG
            if city not in CITY_CONFIG:
                logger.warning(f"⏭️  城市 {city} 不在 CITY_CONFIG 中，跳过")
                return 0
            crawler = HotelCrawler(delay_range=(ctrl.delay, ctrl.delay * 2))
            async with crawler:
                method = getattr(crawler, f"crawl_{site}")
                results = await method(city, max_pages=pages)
                return len(results)

        # ── 餐厅 (Tabelog) ────────────────────────────────────────────
        if task.task_type == "restaurant" and site == "tabelog":
            from scripts.crawlers.tabelog import TabelogCrawler, TABELOG_AREA_MAP
            if city not in TABELOG_AREA_MAP:
                return 0
            crawler = TabelogCrawler(delay_range=(ctrl.delay, ctrl.delay * 2))
            async with crawler:
                results = await crawler.crawl_city(city, max_pages=pages, save_json=True)
                return len(results)

        # ── 景点 (JNTO) ──────────────────────────────────────────────
        if task.task_type == "poi" and site == "jnto":
            from scripts.crawlers.jnto import JNTOCrawler
            crawler = JNTOCrawler(delay_range=(ctrl.delay, ctrl.delay * 2))
            async with crawler:
                results = await crawler.crawl_all()
                total = sum(len(v) if isinstance(v, list) else 0 for v in results.values())
                return total

        # ── 活动 (japan-guide) ────────────────────────────────────────
        if task.task_type == "event" and site == "japan_guide":
            from scripts.crawlers.events import EventCrawler
            crawler = EventCrawler(delay_range=(ctrl.delay, ctrl.delay * 2))
            async with crawler:
                results = await crawler.crawl_all()
                total = sum(len(v) if isinstance(v, list) else 0 for v in results.values())
                return total

        # ── 体验 (VELTRA) ────────────────────────────────────────────
        if task.task_type == "experience" and site == "veltra":
            from scripts.crawlers.experiences import ExperienceCrawler
            crawler = ExperienceCrawler(delay_range=(ctrl.delay, ctrl.delay * 2))
            async with crawler:
                results = await crawler.crawl_veltra(city, pages=pages)
                return len(results)

        # ── 攻略 (letsgojp) ──────────────────────────────────────────
        if task.task_type == "guide" and site == "letsgojp":
            from scripts.crawlers.letsgojp import LetsGoJPCrawler
            crawler = LetsGoJPCrawler(delay_range=(ctrl.delay, ctrl.delay * 2))
            async with crawler:
                results = await crawler.crawl_all(max_pages=pages)
                return len(results) if isinstance(results, list) else 0

        # ── 攻略 (matcha) ────────────────────────────────────────────
        if task.task_type == "guide" and site == "matcha":
            from scripts.crawlers.matcha import MATCHACrawler
            crawler = MATCHACrawler(delay_range=(ctrl.delay, ctrl.delay * 2))
            async with crawler:
                results = await crawler.crawl_all(limit=pages * 20)
                return len(results) if isinstance(results, list) else 0

        # ── 小红书 ───────────────────────────────────────────────────
        if task.task_type == "guide" and site == "xiaohongshu":
            from scripts.crawlers.xiaohongshu import XiaohongshuCrawler
            crawler = XiaohongshuCrawler()
            async with crawler:
                results = await crawler.crawl_by_city(city)
                return len(results) if isinstance(results, list) else 0

        # ── 未实现的爬虫 ─────────────────────────────────────────────
        raise NotImplementedError(f"爬虫未实现: {task.task_type}/{task.site}")


# ── 调度器 ────────────────────────────────────────────────────────────────────

class CrawlOrchestrator:
    """
    并行爬取调度器。

    - 不同站点(site)之间完全并行
    - 同一站点的任务串行执行（避免被封）
    - 支持断点续传：进度保存到 JSON
    - 定期输出状态面板
    """

    def __init__(
        self,
        max_site_parallel: int = 8,
        max_retries: int = 3,
        priority_filter: Optional[str] = None,
        type_filter: Optional[str] = None,
    ):
        self.max_site_parallel = max_site_parallel
        self.max_retries = max_retries
        self.priority_filter = priority_filter
        self.type_filter = type_filter

        self.rate_controllers: dict[str, AdaptiveRateController] = {}
        self.executor = TaskExecutor(self.rate_controllers)
        self.tasks: list[CrawlTask] = []
        self._shutdown = False
        self._start_time = time.time()

    def _load_progress(self) -> dict[str, dict]:
        """加载已有进度"""
        if PROGRESS_FILE.exists():
            try:
                with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_progress(self):
        """保存进度到 JSON"""
        progress = {}
        for t in self.tasks:
            progress[t.task_id] = asdict(t)
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)

    def _save_status(self):
        """保存状态面板到 JSON"""
        done = [t for t in self.tasks if t.status == "done"]
        failed = [t for t in self.tasks if t.status == "failed"]
        running = [t for t in self.tasks if t.status == "running"]
        pending = [t for t in self.tasks if t.status == "pending"]
        skipped = [t for t in self.tasks if t.status == "skipped"]

        total_items = sum(t.items_count for t in done)
        elapsed = time.time() - self._start_time

        status = {
            "updated_at": datetime.now().isoformat(),
            "elapsed_seconds": round(elapsed),
            "elapsed_human": f"{elapsed/3600:.1f}h",
            "summary": {
                "total": len(self.tasks),
                "done": len(done),
                "failed": len(failed),
                "running": len(running),
                "pending": len(pending),
                "skipped": len(skipped),
                "total_items": total_items,
            },
            "by_priority": {},
            "by_type": {},
            "rate_controllers": {k: v.status() for k, v in self.rate_controllers.items()},
            "recent_failures": [
                {"task": t.task_id, "error": t.error} for t in failed[-10:]
            ],
        }

        # 按优先级统计
        for p in ["P0", "P1", "P2", "P3"]:
            pt = [t for t in self.tasks if t.priority == p]
            pd = [t for t in pt if t.status == "done"]
            status["by_priority"][p] = {
                "total": len(pt),
                "done": len(pd),
                "items": sum(t.items_count for t in pd),
            }

        # 按类型统计
        for ty in set(t.task_type for t in self.tasks):
            tt = [t for t in self.tasks if t.task_type == ty]
            td = [t for t in tt if t.status == "done"]
            status["by_type"][ty] = {
                "total": len(tt),
                "done": len(td),
                "items": sum(t.items_count for t in td),
            }

        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(status, f, ensure_ascii=False, indent=2)

    def _print_progress(self):
        """打印进度到控制台"""
        done = sum(1 for t in self.tasks if t.status == "done")
        failed = sum(1 for t in self.tasks if t.status == "failed")
        running = sum(1 for t in self.tasks if t.status == "running")
        pending = sum(1 for t in self.tasks if t.status == "pending")
        skipped = sum(1 for t in self.tasks if t.status == "skipped")
        total_items = sum(t.items_count for t in self.tasks if t.status == "done")
        elapsed = time.time() - self._start_time

        logger.info(
            f"📊 进度: ✅{done} ❌{failed} 🔄{running} ⏳{pending} ⏭️{skipped} "
            f"/ {len(self.tasks)} 总计 | "
            f"📦{total_items:,} 条数据 | ⏱️{elapsed/60:.0f}min"
        )

    async def _run_site_queue(self, site: str, site_tasks: list[CrawlTask]):
        """串行执行同一站点的所有任务"""
        for task in site_tasks:
            if self._shutdown:
                break
            if task.status in ("done", "skipped"):
                continue
            if task.status == "failed" and task.retry_count >= self.max_retries:
                continue

            task = await self.executor.execute(task)

            # 如果失败但还有重试次数，重新排入队列
            if task.status == "failed" and task.retry_count < self.max_retries:
                task.status = "pending"

            # 定期保存进度
            self._save_progress()

    async def _status_ticker(self):
        """定期输出状态"""
        while not self._shutdown:
            await asyncio.sleep(60)  # 每分钟输出一次
            self._print_progress()
            self._save_status()

    async def run(self):
        """启动调度器"""
        # 1. 生成任务
        all_tasks = generate_all_tasks()

        # 2. 应用过滤器
        if self.priority_filter:
            all_tasks = [t for t in all_tasks if t.priority == self.priority_filter]
        if self.type_filter:
            all_tasks = [t for t in all_tasks if t.task_type == self.type_filter]

        # 3. 加载已有进度（断点续传）
        saved = self._load_progress()
        for t in all_tasks:
            if t.task_id in saved:
                s = saved[t.task_id]
                t.status = s.get("status", "pending")
                t.items_count = s.get("items_count", 0)
                t.error = s.get("error", "")
                t.retry_count = s.get("retry_count", 0)
                t.started_at = s.get("started_at", "")
                t.finished_at = s.get("finished_at", "")

        self.tasks = all_tasks

        # 4. 统计
        pending = sum(1 for t in self.tasks if t.status in ("pending", "failed"))
        done = sum(1 for t in self.tasks if t.status == "done")
        logger.info(f"{'='*60}")
        logger.info(f"🕷️  全日本数据爬取调度器启动")
        logger.info(f"   总任务: {len(self.tasks)} | 待执行: {pending} | 已完成: {done}")
        logger.info(f"   优先级: {self.priority_filter or '全部'} | 类型: {self.type_filter or '全部'}")
        logger.info(f"   最大并行站点: {self.max_site_parallel}")
        logger.info(f"   进度文件: {PROGRESS_FILE}")
        logger.info(f"   状态面板: {STATUS_FILE}")
        logger.info(f"   日志文件: {LOG_DIR / 'crawler_orchestrator.log'}")
        logger.info(f"{'='*60}")

        # 5. 按站点分组
        site_groups: dict[str, list[CrawlTask]] = {}
        for t in self.tasks:
            if t.status in ("done", "skipped") and t.retry_count >= self.max_retries:
                continue
            if t.status == "done":
                continue
            key = t.site
            if key not in site_groups:
                site_groups[key] = []
            site_groups[key].append(t)

        # 按优先级排序每个站点的任务
        priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
        for tasks in site_groups.values():
            tasks.sort(key=lambda t: priority_order.get(t.priority, 99))

        logger.info(f"📋 站点分组: {', '.join(f'{k}({len(v)})' for k, v in site_groups.items())}")

        # 6. 并行执行
        sem = asyncio.Semaphore(self.max_site_parallel)

        async def _bounded_site_run(site: str, tasks: list[CrawlTask]):
            async with sem:
                await self._run_site_queue(site, tasks)

        # 启动状态打印协程
        ticker = asyncio.create_task(self._status_ticker())

        try:
            await asyncio.gather(
                *[_bounded_site_run(site, tasks) for site, tasks in site_groups.items()]
            )
        finally:
            self._shutdown = True
            ticker.cancel()
            self._save_progress()
            self._save_status()

        # 7. 最终汇总
        self._print_final_summary()

    def _print_final_summary(self):
        done = [t for t in self.tasks if t.status == "done"]
        failed = [t for t in self.tasks if t.status == "failed"]
        skipped = [t for t in self.tasks if t.status == "skipped"]
        total_items = sum(t.items_count for t in done)
        elapsed = time.time() - self._start_time

        logger.info(f"\n{'='*60}")
        logger.info(f"🏁 爬取完成！")
        logger.info(f"   耗时: {elapsed/3600:.1f} 小时")
        logger.info(f"   完成: {len(done)} 任务, {total_items:,} 条数据")
        logger.info(f"   失败: {len(failed)} 任务")
        logger.info(f"   跳过: {len(skipped)} 任务 (爬虫未实现)")

        if failed:
            logger.info(f"\n   失败任务:")
            for t in failed[:20]:
                logger.info(f"     ❌ {t.task_id}: {t.error[:80]}")

        logger.info(f"\n   状态面板: {STATUS_FILE}")
        logger.info(f"{'='*60}")


# ── 查看状态 ──────────────────────────────────────────────────────────────────

def show_status():
    """打印当前爬取状态"""
    if not STATUS_FILE.exists():
        print("❌ 没有运行中的爬取任务 (status file not found)")
        return

    with open(STATUS_FILE, "r", encoding="utf-8") as f:
        status = json.load(f)

    s = status["summary"]
    print(f"\n{'='*60}")
    print(f"🕷️  爬取状态 (更新于: {status['updated_at']})")
    print(f"   运行时间: {status.get('elapsed_human', '?')}")
    print(f"\n   📊 总计: {s['total']} 任务")
    print(f"   ✅ 完成: {s['done']}  ❌ 失败: {s['failed']}  🔄 运行中: {s['running']}  ⏳ 等待: {s['pending']}  ⏭️ 跳过: {s['skipped']}")
    print(f"   📦 已采集数据: {s['total_items']:,} 条")

    print(f"\n   按优先级:")
    for p, v in status.get("by_priority", {}).items():
        print(f"     {p}: {v['done']}/{v['total']} 完成, {v['items']:,} 条")

    print(f"\n   按类型:")
    for ty, v in status.get("by_type", {}).items():
        print(f"     {ty}: {v['done']}/{v['total']} 完成, {v['items']:,} 条")

    print(f"\n   站点速率:")
    for k, v in status.get("rate_controllers", {}).items():
        paused = " ⏸️暂停" if v.get("paused") else ""
        print(f"     {k}: delay={v['delay']}s 成功率={v['success_rate']:.0%} 请求={v['total_requests']}{paused}")

    fails = status.get("recent_failures", [])
    if fails:
        print(f"\n   最近失败:")
        for f in fails[-5:]:
            print(f"     ❌ {f['task']}: {f['error'][:60]}")

    print(f"{'='*60}\n")


def reset_task(task_id: str):
    """重置某个任务"""
    if not PROGRESS_FILE.exists():
        print("❌ 进度文件不存在")
        return
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        progress = json.load(f)
    if task_id in progress:
        progress[task_id]["status"] = "pending"
        progress[task_id]["retry_count"] = 0
        progress[task_id]["error"] = ""
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
        print(f"✅ 已重置任务: {task_id}")
    else:
        print(f"❌ 未找到任务: {task_id}")


# ── 入口 ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="全日本数据并行爬取调度器")
    parser.add_argument("--priority", choices=["P0", "P1", "P2", "P3"], help="只跑指定优先级")
    parser.add_argument("--type", dest="task_type", help="只跑指定类型 (hotel/poi/restaurant/guide/event/experience)")
    parser.add_argument("--parallel", type=int, default=8, help="最大并行站点数 (默认8)")
    parser.add_argument("--status", action="store_true", help="查看当前状态")
    parser.add_argument("--reset", type=str, help="重置指定任务 ID")
    parser.add_argument("--reset-failed", action="store_true", help="重置所有失败任务")

    args = parser.parse_args()

    if args.status:
        show_status()
        return

    if args.reset:
        reset_task(args.reset)
        return

    if args.reset_failed:
        if PROGRESS_FILE.exists():
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                progress = json.load(f)
            count = 0
            for tid, data in progress.items():
                if data.get("status") == "failed":
                    data["status"] = "pending"
                    data["retry_count"] = 0
                    data["error"] = ""
                    count += 1
            with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
                json.dump(progress, f, ensure_ascii=False, indent=2)
            print(f"✅ 已重置 {count} 个失败任务")
        return

    # 注册信号处理（优雅关闭）
    orchestrator = CrawlOrchestrator(
        max_site_parallel=args.parallel,
        priority_filter=args.priority,
        type_filter=args.task_type,
    )

    def _signal_handler(sig, frame):
        logger.info("\n⚠️  收到中断信号，正在保存进度并优雅退出...")
        orchestrator._shutdown = True

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    asyncio.run(orchestrator.run())


if __name__ == "__main__":
    main()
