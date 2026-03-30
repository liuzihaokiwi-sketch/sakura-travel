#!/usr/bin/env python3
"""
B1 任务：Tabelog 餐厅全量拉取 — 札幌
=======================================
按 12 个菜系分别爬取 Tabelog 札幌餐厅（3.0+ 评分），
用 Google Places Text Search API 补坐标，
通过 upsert_entity 写入 DB。

运行：
    python -m scripts.crawl_sapporo_tabelog
    或
    python scripts/crawl_sapporo_tabelog.py

验证：
    SELECT cuisine_type, COUNT(*) FROM restaurants r
    JOIN entity_base e ON r.entity_id = e.entity_id
    WHERE e.city_code='sapporo' GROUP BY cuisine_type;
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import sys
import re
from typing import Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from dotenv import load_dotenv

# ── 项目根目录加入 path ────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── 数据库 ─────────────────────────────────────────────────────────────────────
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres123@localhost:5432/postgres",
)
GOOGLE_API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY", "")

# ── 常量 ───────────────────────────────────────────────────────────────────────
CITY_CODE = "sapporo"
TABELOG_CITY_PREFIX = "hokkaido/A0101"
PAGES_PER_CUISINE = 3       # 每菜系爬 3 页（每页约 20 条 → 至少 60 条机会）
REQUEST_DELAY_MIN = 3.0     # 请求间隔下限（秒）
REQUEST_DELAY_MAX = 5.0     # 请求间隔上限（秒）
MIN_SCORE = 3.0             # 只保留评分 ≥ 3.0 的餐厅

# 12 个目标菜系：(cuisine_type, tabelog_code, 日文关键词)
# Tabelog 分类代码参考：https://tabelog.com/help/category/
CUISINES = [
    ("sushi",    "RC020101", "寿司"),
    ("ramen",    "RC040201", "ラーメン"),
    ("kaiseki",  "RC010101", "和食"),
    ("yakitori", "RC010401", "焼き鳥・串焼き"),
    ("tempura",  "RC010301", "天ぷら"),
    ("udon",     "RC040101", "うどん"),
    ("izakaya",  "RC010301", "居酒屋"),
    ("seafood",  "RC020201", "海鮮料理"),
    ("curry",    "RC050101", "カレー"),
    ("cafe",     "RC070101", "カフェ"),
    ("yakiniku", "RC010601", "焼肉"),
    ("sukiyaki", "RC010201", "すき焼き"),
]

# User-Agent 轮换池
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]


def _get_headers() -> Dict[str, str]:
    """每次请求轮换 User-Agent"""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "ja-JP,ja;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
    }


# ── Tabelog 爬虫 ───────────────────────────────────────────────────────────────

async def fetch_tabelog_page(
    cuisine_code: str,
    page: int,
    client: httpx.AsyncClient,
) -> List[Dict[str, Any]]:
    """
    爬取一页 Tabelog 札幌餐厅列表。
    URL 格式：https://tabelog.com/hokkaido/A0101/rstLst/{cuisine_code}/{page}/
    """
    url = f"https://tabelog.com/{TABELOG_CITY_PREFIX}/rstLst/{cuisine_code}/{page}/"
    logger.debug("GET %s", url)

    try:
        resp = await client.get(url, headers=_get_headers(), timeout=25.0, follow_redirects=True)
        if resp.status_code == 403:
            logger.warning("403 Forbidden — Tabelog blocked, page %d cuisine %s", page, cuisine_code)
            return []
        if resp.status_code != 200:
            logger.warning("HTTP %d for %s", resp.status_code, url)
            return []
        return _parse_tabelog_list(resp.text)
    except httpx.TimeoutException:
        logger.warning("Timeout fetching %s", url)
        return []
    except Exception as e:
        logger.warning("Error fetching %s: %s", url, e)
        return []


def _parse_tabelog_list(html: str) -> List[Dict[str, Any]]:
    """解析 Tabelog 列表页，提取餐厅基础信息"""
    soup = BeautifulSoup(html, "lxml")
    results = []

    # Tabelog HTML 结构：餐厅名称链接 → 向上找到最近的 div.list-rst
    name_links = soup.select("a.list-rst__rst-name-target")

    for name_el in name_links:
        try:
            name_ja = name_el.get_text(strip=True)
            if not name_ja:
                continue
            href = name_el.get("href", "")
            tabelog_id = _extract_tabelog_id(href)

            # 向上找到 div.list-rst 容器（这才是一个餐厅的完整卡片）
            card = name_el
            while card:
                if card.name == "div" and "list-rst" in (card.get("class") or []):
                    break
                card = card.parent
            if not card:
                continue

            # 评分：div.list-rst 内有 span.c-rating__val
            score_els = card.select("span.c-rating__val")
            score = None
            if score_els:
                # 通常第一个是评分
                score_text = score_els[0].get_text(strip=True)
                try:
                    score = float(score_text)
                except (ValueError, TypeError):
                    pass

            # 过滤低评分
            if score is not None and score < MIN_SCORE:
                continue

            # 价格（通常是两个元素：午餐、晚餐）
            budget_els = card.select(".list-rst__budget-item")
            price_lunch = _parse_price(budget_els[0].get_text(strip=True) if len(budget_els) > 0 else "")
            price_dinner = _parse_price(budget_els[1].get_text(strip=True) if len(budget_els) > 1 else "")

            # 菜系
            cuisine_el = card.select_one(".list-rst__category-item")
            cuisine_raw = cuisine_el.get_text(strip=True) if cuisine_el else ""

            # 地区
            area_el = card.select_one(".list-rst__area-genre")
            district = area_el.get_text(strip=True) if area_el else ""

            # 评论数
            review_text_els = card.select(".list-rst__total-count-num")
            review_count = 0
            if review_text_els:
                try:
                    review_count = int(review_text_els[0].get_text(strip=True).replace(",", ""))
                except (ValueError, TypeError):
                    pass

            results.append({
                "name_ja": name_ja,
                "tabelog_id": tabelog_id,
                "tabelog_url": href,
                "tabelog_score": score,
                "tabelog_review_count": review_count,
                "price_lunch_jpy": price_lunch,
                "price_dinner_jpy": price_dinner,
                "cuisine_raw": cuisine_raw,
                "district": district,
            })
        except Exception as e:
            logger.debug("Error parsing name link: %s", e)
            continue

    return results


def _extract_tabelog_id(url: str) -> Optional[str]:
    """从 Tabelog URL 提取餐厅 ID（8 位数字）"""
    match = re.search(r'/(\d{8})/?', url)
    return match.group(1) if match else None


def _parse_price(price_str: str) -> Optional[int]:
    """解析价格字符串：¥3,000～¥3,999 → 3000"""
    if not price_str or price_str.strip() in ("-", ""):
        return None
    cleaned = re.sub(r'[¥￥,]', '', price_str)
    match = re.search(r'\d+', cleaned)
    if match:
        try:
            return int(match.group(0))
        except ValueError:
            return None
    return None


# ── Google Places 补坐标 ───────────────────────────────────────────────────────

async def geocode_by_name(
    name_ja: str,
    client: httpx.AsyncClient,
) -> Optional[Dict[str, Any]]:
    """
    用 Google Places Text Search 按餐厅日文名搜索，获取坐标和 place_id。
    搜索词加上 "札幌" 提高精度。
    """
    if not GOOGLE_API_KEY:
        return None

    query = f"{name_ja} 札幌"
    params = {
        "query": query,
        "language": "ja",
        "region": "jp",
        "key": GOOGLE_API_KEY,
        "fields": "place_id,name,geometry,formatted_address,rating,user_ratings_total",
    }

    try:
        resp = await client.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params=params,
            timeout=10.0,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data.get("status") not in ("OK",):
            return None
        results = data.get("results", [])
        if not results:
            return None

        r = results[0]
        loc = r.get("geometry", {}).get("location", {})
        return {
            "google_place_id": r.get("place_id"),
            "lat": loc.get("lat"),
            "lng": loc.get("lng"),
            "google_rating": r.get("rating"),
            "google_review_count": r.get("user_ratings_total"),
            "address_ja": r.get("formatted_address", ""),
        }
    except Exception as e:
        logger.debug("Geocode failed for %s: %s", name_ja, e)
        return None


# ── 菜系推断 ───────────────────────────────────────────────────────────────────

def _guess_cuisine(cuisine_raw: str, query_cuisine: str, district: str = "") -> str:
    """
    从 query_cuisine + Tabelog 菜系文本推断标准 cuisine_type。
    优先使用查询时的菜系类型（最可靠），其次从 district 或 cuisine_raw 推断。
    """
    # 查询菜系直接映射（最可靠）
    direct_map = {
        "sushi":    "sushi",
        "ramen":    "ramen",
        "kaiseki":  "kaiseki",
        "yakitori": "yakitori",
        "tempura":  "tempura",
        "udon":     "udon",
        "izakaya":  "izakaya",
        "seafood":  "seafood",
        "curry":    "curry",
        "cafe":     "cafe",
        "yakiniku": "yakiniku",
        "sukiyaki": "sukiyaki",
    }
    if query_cuisine in direct_map:
        return direct_map[query_cuisine]

    # 从日文文本推断（结合 cuisine_raw + district）
    text = f"{cuisine_raw} {district}"
    text_map = [
        ("寿司", "sushi"),
        ("スシ", "sushi"),
        ("ラーメン", "ramen"),
        ("拉麺", "ramen"),
        ("懐石", "kaiseki"),
        ("和食", "kaiseki"),
        ("料亭", "kaiseki"),
        ("焼き鳥", "yakitori"),
        ("串焼き", "yakitori"),
        ("天ぷら", "tempura"),
        ("うどん", "udon"),
        ("居酒屋", "izakaya"),
        ("海鮮", "seafood"),
        ("海鮮料理", "seafood"),
        ("カレー", "curry"),
        ("カレーライス", "curry"),
        ("カフェ", "cafe"),
        ("喫茶", "cafe"),
        ("焼肉", "yakiniku"),
        ("ジンギスカン", "yakiniku"),
        ("すき焼き", "sukiyaki"),
        ("すき焼", "sukiyaki"),
        ("鍋", "sukiyaki"),
    ]
    for kw, ct in text_map:
        if kw in text:
            return ct
    return "other"


# ── 主采集逻辑 ─────────────────────────────────────────────────────────────────

async def crawl_all_cuisines() -> List[Dict[str, Any]]:
    """
    按 12 个菜系爬取 Tabelog 札幌餐厅，去重后返回。
    每菜系爬 PAGES_PER_CUISINE 页。
    """
    seen_tabelog_ids: set = set()
    seen_names: set = set()
    all_restaurants: List[Dict[str, Any]] = []

    async with httpx.AsyncClient() as client:
        for cuisine_type, cuisine_code, cuisine_ja in CUISINES:
            logger.info("--- 开始爬取菜系：%s (%s) ---", cuisine_type, cuisine_ja)
            cuisine_count = 0

            for page in range(1, PAGES_PER_CUISINE + 1):
                logger.info("  爬取第 %d 页...", page)
                items = await fetch_tabelog_page(cuisine_code, page, client)
                logger.info("  获取 %d 条原始数据", len(items))

                for item in items:
                    # tabelog_id 去重
                    tid = item.get("tabelog_id")
                    if tid and tid in seen_tabelog_ids:
                        continue
                    # 名称去重（跨菜系同一家店可能出现）
                    name = item["name_ja"]
                    if name in seen_names:
                        continue

                    if tid:
                        seen_tabelog_ids.add(tid)
                    seen_names.add(name)

                    item["cuisine_type"] = _guess_cuisine(
                        item.get("cuisine_raw", ""),
                        cuisine_type,
                        item.get("district", "")
                    )
                    item["query_cuisine"] = cuisine_type  # 记录查询时的菜系
                    all_restaurants.append(item)
                    cuisine_count += 1

                # 请求间隔（防封）
                if page < PAGES_PER_CUISINE:
                    delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
                    logger.debug("  等待 %.1f 秒...", delay)
                    await asyncio.sleep(delay)

            logger.info("菜系 %s 获取 %d 家餐厅（去重后）", cuisine_type, cuisine_count)

            # 菜系间等待
            delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
            logger.info("  菜系间等待 %.1f 秒", delay)
            await asyncio.sleep(delay)

    logger.info("Tabelog 爬取完成：共 %d 家餐厅（去重）", len(all_restaurants))
    return all_restaurants


async def enrich_with_coordinates(
    restaurants: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    用 Google Places Text Search 为每家餐厅补坐标。
    有 tabelog_id 但坐标缺失时才调 API，避免浪费配额。
    """
    if not GOOGLE_API_KEY:
        logger.warning("GOOGLE_PLACES_API_KEY 未配置，跳过坐标补充")
        return restaurants

    geocoded = 0
    failed = 0
    total = len(restaurants)

    async with httpx.AsyncClient() as client:
        for i, rst in enumerate(restaurants):
            if rst.get("lat") and rst.get("lng"):
                continue  # 已有坐标跳过

            if i % 10 == 0:
                logger.info("坐标补充进度：%d/%d (geocoded=%d, failed=%d)",
                            i, total, geocoded, failed)

            geo = await geocode_by_name(rst["name_ja"], client)
            if geo:
                rst.update(geo)
                geocoded += 1
            else:
                failed += 1

            # Google Places 有速率限制，稍作等待
            await asyncio.sleep(0.3)

    logger.info("坐标补充完成：成功 %d，失败 %d（共 %d）", geocoded, failed, total)
    return restaurants


# ── 写入数据库 ─────────────────────────────────────────────────────────────────

async def write_to_db(
    restaurants: List[Dict[str, Any]],
    session: AsyncSession,
) -> Dict[str, int]:
    """将餐厅数据写入 DB，返回统计"""
    from app.domains.catalog.upsert import upsert_entity

    stats = {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0}
    cuisine_stats: Dict[str, int] = {}

    for i, rst in enumerate(restaurants):
        if i % 50 == 0:
            logger.info("写入进度：%d/%d ...", i, len(restaurants))

        name_ja = rst.get("name_ja", "")
        if not name_ja:
            stats["skipped"] += 1
            continue

        # 重新推断菜系（以防万一）
        cuisine_type = _guess_cuisine(
            rst.get("cuisine_raw", ""),
            rst.get("query_cuisine", ""),
            rst.get("district", "")
        )
        lat = rst.get("lat")
        lng = rst.get("lng")
        has_coords = lat is not None and lng is not None and (lat != 0 or lng != 0)

        db_data = {
            # entity_base 字段
            "name_ja":          name_ja,
            "name_zh":          name_ja,   # 暂用日文名，后续翻译任务填充
            "city_code":        CITY_CODE,
            "lat":              lat,
            "lng":              lng,
            "address_ja":       rst.get("address_ja", ""),
            "area_name":        rst.get("district", ""),
            "data_tier":        "A",
            "trust_status":     "unverified" if (rst.get("tabelog_id") and has_coords) else "suspicious",
            "google_place_id":  rst.get("google_place_id"),
            "tabelog_id":       rst.get("tabelog_id"),
            # restaurants 子表字段
            "cuisine_type":     cuisine_type,
            "tabelog_score":    rst.get("tabelog_score"),
            "budget_lunch_jpy": rst.get("price_lunch_jpy"),
            "budget_dinner_jpy": rst.get("price_dinner_jpy"),
            "price_range_min_jpy": rst.get("price_lunch_jpy"),
            "price_range_max_jpy": rst.get("price_dinner_jpy"),
        }
        # 清除 None
        db_data = {k: v for k, v in db_data.items() if v is not None}

        try:
            async with session.begin_nested():
                entity = await upsert_entity(
                    session=session,
                    entity_type="restaurant",
                    data=db_data,
                    google_place_id=rst.get("google_place_id"),
                    tabelog_id=rst.get("tabelog_id"),
                )
                _ = entity  # 记录 entity_id 可供后续扩展
            stats["inserted"] += 1
            cuisine_stats[cuisine_type] = cuisine_stats.get(cuisine_type, 0) + 1
        except Exception as e:
            logger.warning("写入失败 [%s]: %s", name_ja, e)
            stats["errors"] += 1

    logger.info("写入完成：%s", stats)
    logger.info("按菜系统计：")
    for ct, cnt in sorted(cuisine_stats.items(), key=lambda x: -x[1]):
        logger.info("  %-15s %d 家", ct, cnt)

    return stats


# ── 入口 ───────────────────────────────────────────────────────────────────────

async def main() -> None:
    logger.info("=" * 60)
    logger.info("B1 任务：Tabelog 札幌餐厅全量拉取")
    logger.info("目标：12 菜系 × 3 页，预计 500-700 家")
    logger.info("=" * 60)

    if not GOOGLE_API_KEY:
        logger.warning("⚠️  GOOGLE_PLACES_API_KEY 未配置，坐标补充将跳过")

    # Step 1: 爬取
    logger.info("\n[Step 1] 爬取 Tabelog 餐厅数据...")
    restaurants = await crawl_all_cuisines()
    logger.info("爬取结果：%d 家（去重）", len(restaurants))

    if not restaurants:
        logger.error("爬取结果为空，可能 Tabelog 已封锁。退出。")
        sys.exit(1)

    # 保存中间文件（方便调试/重试）
    raw_path = "data/tabelog_sapporo_raw.json"
    os.makedirs("data", exist_ok=True)
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(restaurants, f, ensure_ascii=False, indent=2)
    logger.info("原始数据已保存：%s", raw_path)

    # Step 2: 补坐标
    logger.info("\n[Step 2] Google Places 补坐标...")
    restaurants = await enrich_with_coordinates(restaurants)

    # 保存补坐标后的文件
    enriched_path = "data/tabelog_sapporo_enriched.json"
    with open(enriched_path, "w", encoding="utf-8") as f:
        json.dump(restaurants, f, ensure_ascii=False, indent=2)
    logger.info("补坐标数据已保存：%s", enriched_path)

    # Step 3: 写入 DB
    logger.info("\n[Step 3] 写入数据库...")
    engine = create_async_engine(DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as session:
        async with session.begin():
            stats = await write_to_db(restaurants, session)

    await engine.dispose()

    # Step 4: 验证
    logger.info("\n[Step 4] 验证结果...")
    await verify_results()

    logger.info("\n✅ B1 任务完成！")
    logger.info("总写入：%d 家", stats["inserted"])
    logger.info("跳过：%d，错误：%d", stats["skipped"], stats["errors"])


async def verify_results() -> None:
    """查询 DB 验证 12 菜系覆盖情况"""
    from sqlalchemy import text

    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT r.cuisine_type, COUNT(*) as cnt
            FROM restaurants r
            JOIN entity_base e ON r.entity_id = e.entity_id
            WHERE e.city_code = 'sapporo'
              AND e.trust_status != 'ai_generated'
            GROUP BY r.cuisine_type
            ORDER BY cnt DESC
        """))
        rows = result.fetchall()

    await engine.dispose()

    logger.info("\n📊 验证结果 — 札幌餐厅按菜系统计：")
    total = 0
    cuisines_ok = []
    cuisines_fail = []
    target_cuisines = {ct for ct, _, _ in CUISINES}

    cuisine_counts: Dict[str, int] = {}
    for row in rows:
        cuisine_type, cnt = row
        cuisine_counts[cuisine_type] = cnt
        total += cnt
        logger.info("  %-15s %d 家", cuisine_type, cnt)

    for ct in target_cuisines:
        cnt = cuisine_counts.get(ct, 0)
        if cnt >= 10:
            cuisines_ok.append(ct)
        else:
            cuisines_fail.append(f"{ct}({cnt})")

    logger.info("\n总计：%d 家餐厅", total)
    logger.info("✅ 达标菜系（≥10家）：%d/12 — %s", len(cuisines_ok), ", ".join(cuisines_ok))
    if cuisines_fail:
        logger.warning("⚠️  未达标菜系：%s", ", ".join(cuisines_fail))

    # 验证无 ai_generated
    engine2 = create_async_engine(DATABASE_URL, echo=False)
    async with engine2.connect() as conn:
        result2 = await conn.execute(text("""
            SELECT COUNT(*) FROM entity_base
            WHERE city_code = 'sapporo'
              AND entity_type = 'restaurant'
              AND trust_status = 'ai_generated'
        """))
        ai_count = result2.scalar()
    await engine2.dispose()

    if ai_count == 0:
        logger.info("✅ 无 AI 生成数据（trust_status='ai_generated' = 0）")
    else:
        logger.warning("⚠️  存在 %d 条 AI 生成数据，请检查！", ai_count)


if __name__ == "__main__":
    asyncio.run(main())
