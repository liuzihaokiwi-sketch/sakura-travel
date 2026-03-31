"""
T2: 营业时间批量补充
Google Places Details API → opening_hours → pois/restaurants + entity_operating_facts

优先级:
  1. 被 day_fragments 引用的实体
  2. google_rating > 4.0 的实体
  3. 其余有 google_place_id 的实体

运行: python scripts/t2_backfill_opening_hours.py [--dry-run] [--limit 50]
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import argparse
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from app.domains.catalog.crawlers.google_places import fetch_place_details

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# 每次 API 调用间隔（秒），保持每秒 < 10 次
CALL_INTERVAL = 0.15

# 星期几映射（Google API: 0=Sunday, ..., 6=Saturday）
DOW_MAP = {0: "sun", 1: "mon", 2: "tue", 3: "wed", 4: "thu", 5: "fri", 6: "sat"}


async def get_priority_entities(session, limit: int) -> List[Tuple[str, str, str, str]]:
    """
    返回 (entity_id, google_place_id, entity_type, name) 按优先级排序
    优先级: 1. day_fragments 引用 2. rating > 4.0 3. 其余有 place_id 的
    """
    # 收集已在 day_fragments 中引用的实体
    r_frags = await session.execute(text("""
        SELECT DISTINCT unnest(df.entity_ids)::uuid AS entity_id
        FROM day_fragments df
        WHERE df.entity_ids IS NOT NULL AND array_length(df.entity_ids, 1) > 0
    """))
    fragment_entity_ids = {str(row[0]) for row in r_frags.fetchall()}

    # 获取所有有 google_place_id 且没有营业时间的实体
    r = await session.execute(text("""
        SELECT
            eb.entity_id::text,
            eb.google_place_id,
            eb.entity_type,
            eb.name_zh,
            COALESCE(p.google_rating, h_rating.google_rating) AS rating,
            CASE WHEN p.opening_hours_json IS NOT NULL OR r.opening_hours_json IS NOT NULL
                 THEN true ELSE false END AS has_hours
        FROM entity_base eb
        LEFT JOIN pois p ON p.entity_id = eb.entity_id
        LEFT JOIN restaurants r ON r.entity_id = eb.entity_id
        LEFT JOIN (
            SELECT entity_id, google_rating FROM pois
        ) h_rating ON h_rating.entity_id = eb.entity_id
        WHERE eb.is_active = true
          AND eb.google_place_id IS NOT NULL
          AND eb.entity_type IN ('poi', 'restaurant')
          AND (
              (eb.entity_type = 'poi' AND (p.opening_hours_json IS NULL))
              OR
              (eb.entity_type = 'restaurant' AND (r.opening_hours_json IS NULL))
          )
        LIMIT :limit
    """), {"limit": limit * 3})

    rows = r.fetchall()

    # 排序：fragment引用 > rating > 4.0 > 其余
    def priority(row):
        entity_id = row[0]
        rating = row[4] or 0
        in_fragment = entity_id in fragment_entity_ids
        return (0 if in_fragment else 1, 0 if rating >= 4.0 else 1, -rating)

    rows_sorted = sorted(rows, key=priority)[:limit]
    return [(row[0], row[1], row[2], row[3]) for row in rows_sorted]


def extract_closed_days(periods: List[Dict]) -> List[str]:
    """从 opening_hours.periods 提取定休日（全天关闭的星期几）"""
    if not periods:
        return []
    open_days = set()
    for period in periods:
        if period.get("open"):
            day_num = period["open"].get("day")
            if day_num is not None:
                open_days.add(day_num)
    all_days = set(range(7))
    closed_day_nums = all_days - open_days
    return [DOW_MAP[d] for d in sorted(closed_day_nums)]


async def upsert_opening_hours(
    session,
    entity_id: str,
    entity_type: str,
    details: Dict[str, Any],
    dry_run: bool,
) -> bool:
    """将 Place Details 的 opening_hours 写入对应子表 + entity_operating_facts"""
    opening_hours = details.get("opening_hours")
    if not opening_hours:
        return False

    hours_json = json.dumps(opening_hours, ensure_ascii=False)
    periods = opening_hours.get("periods", [])
    closed_days = extract_closed_days(periods)

    if dry_run:
        return True

    # 更新子表
    if entity_type == "poi":
        await session.execute(text("""
            UPDATE pois SET opening_hours_json = :hours
            WHERE entity_id = CAST(:eid AS uuid)
        """), {"hours": hours_json, "eid": entity_id})
    elif entity_type == "restaurant":
        await session.execute(text("""
            UPDATE restaurants SET opening_hours_json = :hours
            WHERE entity_id = CAST(:eid AS uuid)
        """), {"hours": hours_json, "eid": entity_id})

    # 从 periods 提取每天的开/收时间，写入 entity_operating_facts
    for period in periods:
        open_info = period.get("open", {})
        close_info = period.get("close", {})
        if not open_info:
            continue

        day_num = open_info.get("day")
        if day_num is None:
            continue
        dow = DOW_MAP.get(day_num, "unknown")
        open_time = open_info.get("time", "")  # "HHMM" format
        close_time = close_info.get("time", "") if close_info else ""

        # 格式化为 "HH:MM"
        def fmt_time(t: str) -> str:
            if len(t) == 4:
                return f"{t[:2]}:{t[2:]}"
            return t

        # insert entity_operating_facts (delete existing first to avoid dupes)
        await session.execute(text("""
            DELETE FROM entity_operating_facts
            WHERE entity_id = CAST(:eid AS uuid) AND day_of_week = :dow
        """), {"eid": entity_id, "dow": dow})
        await session.execute(text("""
            INSERT INTO entity_operating_facts
                (entity_id, day_of_week, open_time, close_time)
            VALUES (CAST(:eid AS uuid), :dow, :open_t, :close_t)
        """), {
            "eid": entity_id, "dow": dow,
            "open_t": fmt_time(open_time), "close_t": fmt_time(close_time),
        })

    return True


async def main(dry_run: bool = False, limit: int = 200) -> None:
    async with AsyncSessionLocal() as session:
        # 验证前状态
        r_before = await session.execute(text("""
            SELECT
                COUNT(CASE WHEN p.opening_hours_json IS NOT NULL THEN 1 END) AS poi_with,
                COUNT(*) AS poi_total
            FROM pois p JOIN entity_base eb ON eb.entity_id=p.entity_id
            WHERE eb.is_active=true
        """))
        row = r_before.fetchone()
        print(f"Before: pois with opening_hours: {row[0]}/{row[1]} ({row[0]/max(row[1],1)*100:.1f}%)")

        r_before_r = await session.execute(text("""
            SELECT
                COUNT(CASE WHEN r.opening_hours_json IS NOT NULL THEN 1 END) AS r_with,
                COUNT(*) AS r_total
            FROM restaurants r JOIN entity_base eb ON eb.entity_id=r.entity_id
            WHERE eb.is_active=true
        """))
        row_r = r_before_r.fetchone()
        print(f"Before: restaurants with opening_hours: {row_r[0]}/{row_r[1]}")

        entities = await get_priority_entities(session, limit)
        print(f"\nFetching details for {len(entities)} entities (limit={limit})...")

        processed = updated = failed = 0
        for entity_id, place_id, entity_type, name in entities:
            processed += 1
            if processed % 20 == 0:
                print(f"  Progress: {processed}/{len(entities)} (updated={updated})")

            try:
                details = await fetch_place_details(place_id)
                await asyncio.sleep(CALL_INTERVAL)

                if not details:
                    failed += 1
                    continue

                ok = await upsert_opening_hours(session, entity_id, entity_type, details, dry_run)
                if ok:
                    updated += 1
                    if not dry_run and updated % 20 == 0:
                        await session.flush()
            except Exception as e:
                failed += 1
                logger.debug("Failed %s (%s): %s", name, place_id, e)

        if not dry_run:
            await session.commit()

        print(f"\nResult: processed={processed}, updated={updated}, failed={failed}")

        if not dry_run:
            r_after = await session.execute(text("""
                SELECT
                    COUNT(CASE WHEN p.opening_hours_json IS NOT NULL THEN 1 END),
                    COUNT(*)
                FROM pois p JOIN entity_base eb ON eb.entity_id=p.entity_id
                WHERE eb.is_active=true
            """))
            row_a = r_after.fetchone()
            print(f"After: pois with opening_hours: {row_a[0]}/{row_a[1]} ({row_a[0]/max(row_a[1],1)*100:.1f}%)")

            r_after_r = await session.execute(text("""
                SELECT
                    COUNT(CASE WHEN r.opening_hours_json IS NOT NULL THEN 1 END),
                    COUNT(*)
                FROM restaurants r JOIN entity_base eb ON eb.entity_id=r.entity_id
                WHERE eb.is_active=true
            """))
            row_ar = r_after_r.fetchone()
            print(f"After: restaurants with opening_hours: {row_ar[0]}/{row_ar[1]}")

        print("\n[OK] T2 DONE")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=200,
                        help="Max entities to fetch (default 200)")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run, limit=args.limit))
