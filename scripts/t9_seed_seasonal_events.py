"""
T9: seasonal_events 数据填充
北海道核心季节事件（真实事件，可查证日期）

运行: python scripts/t9_seed_seasonal_events.py [--dry-run]
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
import argparse
import uuid
from datetime import datetime, timezone, date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import AsyncSessionLocal

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# 参考年（用于 timestamptz，实际使用时按当年计算）
REF_YEAR = 2026

def ts(month: int, day: int) -> datetime:
    """构建 datetime 对象（UTC）"""
    return datetime(REF_YEAR, month, day, 0, 0, 0, tzinfo=timezone.utc)


# crowd_impact: 1=轻微 2=一般 3=较大 4=很大 5=极大（如雪祭）
SEASONAL_EVENTS = [
    # ── 冬 ────────────────────────────────────────────────────────────────────
    {
        "city_code": "sapporo",
        "area_code": "sapporo_center",
        "event_name": "さっぽろ雪まつり",
        "start_date": ts(2, 1),
        "end_date":   ts(2, 11),
        "crowd_impact": "5",
        "booking_required": True,
        "best_timing_tips": "大通会場は夕方のライトアップが美しい。大雪像は早朝が空いている。",
    },
    {
        "city_code": "otaru",
        "area_code": "otaru_center",
        "event_name": "小樽雪あかりの路",
        "start_date": ts(2, 8),
        "end_date":   ts(2, 17),
        "crowd_impact": "3",
        "booking_required": False,
        "best_timing_tips": "運河沿いのキャンドルは18時以降に点灯。週末は混雑するので平日夜がベスト。",
    },
    {
        "city_code": "sapporo",
        "area_code": "sapporo_center",
        "event_name": "札幌ホワイトイルミネーション",
        "start_date": ts(11, 22),
        "end_date":   ts(3, 14),
        "crowd_impact": "2",
        "booking_required": False,
        "best_timing_tips": "大通公園と駅前通が会場。クリスマス週間は特に混雑。",
    },
    {
        "city_code": "abashiri",
        "area_code": "abashiri_coast",
        "event_name": "知床・オホーツク流氷シーズン",
        "start_date": ts(1, 25),
        "end_date":   ts(3, 20),
        "crowd_impact": "3",
        "booking_required": True,
        "best_timing_tips": "流氷観光砕氷船「おーろら」は2月がピーク。早めの予約必須。",
    },
    {
        "city_code": "niseko",
        "area_code": "niseko_ski",
        "event_name": "ニセコスキーシーズン",
        "start_date": ts(12, 1),
        "end_date":   ts(4, 5),
        "crowd_impact": "4",
        "booking_required": True,
        "best_timing_tips": "1月-2月がパウダースノーのベストシーズン。豪雪のため防寒必須。",
    },
    # ── 春 ────────────────────────────────────────────────────────────────────
    {
        "city_code": "hakodate",
        "area_code": "hakodate_goryokaku",
        "event_name": "函館五稜郭桜まつり",
        "start_date": ts(4, 24),
        "end_date":   ts(5, 12),
        "crowd_impact": "3",
        "booking_required": False,
        "best_timing_tips": "五稜郭タワーからの花見が絶景。満開時は夜桜ライトアップあり。",
    },
    {
        "city_code": "sapporo",
        "area_code": "sapporo_center",
        "event_name": "札幌ライラックまつり",
        "start_date": ts(5, 17),
        "end_date":   ts(6, 4),
        "crowd_impact": "2",
        "booking_required": False,
        "best_timing_tips": "大通公園のライラックは5月下旬が見頃。屋外コンサートも開催。",
    },
    # ── 夏 ────────────────────────────────────────────────────────────────────
    {
        "city_code": "sapporo",
        "area_code": "sapporo_center",
        "event_name": "YOSAKOIソーラン祭り",
        "start_date": ts(6, 5),
        "end_date":   ts(6, 9),
        "crowd_impact": "4",
        "booking_required": False,
        "best_timing_tips": "参加チーム数200以上。大通公園メインステージは午後が最も盛り上がる。",
    },
    {
        "city_code": "furano",
        "area_code": "furano_biei",
        "event_name": "富良野・美瑛ラベンダーシーズン",
        "start_date": ts(7, 1),
        "end_date":   ts(8, 10),
        "crowd_impact": "4",
        "booking_required": True,
        "best_timing_tips": "7月中旬が満開。ファーム富田は朝7時開園、早朝訪問で人が少ない。",
    },
    {
        "city_code": "asahikawa",
        "area_code": "asahikawa_center",
        "event_name": "旭川夏まつり",
        "start_date": ts(8, 2),
        "end_date":   ts(8, 11),
        "crowd_impact": "3",
        "booking_required": False,
        "best_timing_tips": "石狩川河川敷会場での花火大会は8月5日頃。花火は橋の上から見るのがおすすめ。",
    },
    {
        "city_code": "noboribetsu",
        "area_code": "noboribetsu_onsen",
        "event_name": "登別地獄まつり",
        "start_date": ts(8, 25),
        "end_date":   ts(8, 26),
        "crowd_impact": "3",
        "booking_required": False,
        "best_timing_tips": "閻魔大王みこし行列が見所。温泉街全体がお祭りムードに包まれる。",
    },
    {
        "city_code": "toya",
        "area_code": "toya_lake",
        "event_name": "洞爺湖ロングラン花火大会",
        "start_date": ts(4, 28),
        "end_date":   ts(10, 31),
        "crowd_impact": "2",
        "booking_required": False,
        "best_timing_tips": "毎晩20:45から約20分間打ち上げ。湖畔のホテルや遊覧船から鑑賞できる。",
    },
    # ── 秋 ────────────────────────────────────────────────────────────────────
    {
        "city_code": "asahikawa",
        "area_code": "daisetsuzan",
        "event_name": "大雪山紅葉シーズン",
        "start_date": ts(9, 15),
        "end_date":   ts(10, 5),
        "crowd_impact": "3",
        "booking_required": False,
        "best_timing_tips": "旭岳の紅葉は9月中旬から。ロープウェイは早朝が空いている。",
    },
    {
        "city_code": "asahikawa",
        "area_code": "sounkyo",
        "event_name": "層雲峡紅葉まつり",
        "start_date": ts(9, 25),
        "end_date":   ts(10, 20),
        "crowd_impact": "3",
        "booking_required": False,
        "best_timing_tips": "渓谷沿いの紅葉は10月上旬が見頃。夜のライトアップも行われる。",
    },
    {
        "city_code": "sapporo",
        "area_code": "jozankei",
        "event_name": "定山渓紅葉シーズン",
        "start_date": ts(10, 5),
        "end_date":   ts(10, 20),
        "crowd_impact": "3",
        "booking_required": False,
        "best_timing_tips": "定山渓温泉から豊平峡ダムへのドライブが人気。紅葉トンネルが美しい。",
    },
    # ── 冬（クリスマス） ────────────────────────────────────────────────────────
    {
        "city_code": "hakodate",
        "area_code": "hakodate_bay",
        "event_name": "はこだてクリスマスファンタジー",
        "start_date": ts(12, 1),
        "end_date":   ts(12, 25),
        "crowd_impact": "2",
        "booking_required": False,
        "best_timing_tips": "赤レンガ倉庫前の巨大ツリーが名物。毎晩18時からカウントダウン点灯式。",
    },
]


async def main(dry_run: bool = False) -> None:
    async with AsyncSessionLocal() as session:
        r_before = await session.execute(text("SELECT COUNT(*) FROM seasonal_events"))
        print(f"Before: {r_before.scalar()} seasonal events")

        if dry_run:
            print(f"\n[DRY RUN] Would insert {len(SEASONAL_EVENTS)} events:")
            for ev in SEASONAL_EVENTS:
                print(f"  {ev['city_code']}: {ev['event_name']} ({ev['start_date'][:7]})")
            return

        inserted = skipped = 0
        for ev in SEASONAL_EVENTS:
            try:
                # 检查是否已存在（按 event_name + city_code）
                r_exists = await session.execute(text("""
                    SELECT event_id FROM seasonal_events
                    WHERE event_name = :name AND city_code = :city
                """), {"name": ev["event_name"], "city": ev["city_code"]})
                existing = r_exists.scalar_one_or_none()

                if existing:
                    # 更新
                    await session.execute(text("""
                        UPDATE seasonal_events
                        SET start_date = :start_date,
                            end_date = :end_date,
                            crowd_impact = :crowd_impact,
                            booking_required = :booking_required,
                            best_timing_tips = :best_timing_tips,
                            area_code = :area_code,
                            updated_at = NOW()
                        WHERE event_id = :eid
                    """), {**ev, "eid": str(existing)})
                    skipped += 1
                else:
                    # 插入
                    event_id = str(uuid.uuid4())
                    await session.execute(text("""
                        INSERT INTO seasonal_events
                            (event_id, city_code, area_code, event_name,
                             start_date, end_date, crowd_impact,
                             booking_required, best_timing_tips)
                        VALUES
                            (:event_id, :city_code, :area_code, :event_name,
                             :start_date, :end_date, :crowd_impact,
                             :booking_required, :best_timing_tips)
                    """), {**ev, "event_id": event_id})
                    inserted += 1
            except Exception as e:
                logger.error("Failed to insert event %s: %s", ev.get("event_name"), e)

        await session.commit()
        print(f"\nResult: inserted={inserted}, updated={skipped}")

        # 验证
        r_by_city = await session.execute(text("""
            SELECT city_code, COUNT(*) FROM seasonal_events GROUP BY city_code ORDER BY city_code
        """))
        print("\n=== Events by city ===")
        city_set = set()
        for row in r_by_city.fetchall():
            print(f"  {row[0]}: {row[1]}")
            city_set.add(row[0])

        if len(city_set) >= 8:
            print(f"\n[PASS] Verification: {len(city_set)} cities have events (target >= 8)")
        else:
            print(f"\n[WARN] Verification: only {len(city_set)} cities (target >= 8)")

        print("\n[OK] T9 DONE")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
