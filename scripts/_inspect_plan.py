"""Inspect generated plan content in detail."""
import asyncio, json
from app.db.session import AsyncSessionLocal
from sqlalchemy import text

PLAN_ID = "8b12a29e-d751-42fb-b4c3-4ccea67642ef"

async def main():
    async with AsyncSessionLocal() as s:
        # Days
        days = await s.execute(text(
            f"SELECT day_number, city_code, day_theme, estimated_cost_jpy "
            f"FROM itinerary_days WHERE plan_id='{PLAN_ID}' ORDER BY day_number"
        ))
        print("=== DAYS ===")
        for d in days.fetchall():
            print(f"  Day {d[0]}: {d[1]} | {d[2]} | cost={d[3]}")

        # Items - full detail
        items = await s.execute(text(
            f"SELECT d.day_number, i.item_type, i.start_time, i.end_time, "
            f"i.duration_min, i.notes_zh, i.estimated_cost_jpy, i.is_optional, "
            f"i.poi_snapshot "
            f"FROM itinerary_items i "
            f"JOIN itinerary_days d ON i.day_id = d.day_id "
            f"WHERE d.plan_id='{PLAN_ID}' "
            f"ORDER BY d.day_number, i.start_time"
        ))
        print("\n=== ITEMS (all) ===")
        for it in items.fetchall():
            snap = it[8] or {}
            name = snap.get("name_zh", snap.get("name_en", "?"))
            desc = (it[5] or "")[:80]
            print(f"  Day{it[0]} [{it[1]:10s}] {it[2]}-{it[3]} ({it[4]}min) "
                  f"{'[optional]' if it[7] else ''} "
                  f"{name} | {desc}")

        # Count
        cnt = await s.execute(text(
            f"SELECT count(*) FROM itinerary_items i "
            f"JOIN itinerary_days d ON i.day_id=d.day_id "
            f"WHERE d.plan_id='{PLAN_ID}'"
        ))
        print(f"\nTotal items: {cnt.scalar()}")

        # Check poi_snapshot richness on first item
        first = await s.execute(text(
            f"SELECT i.poi_snapshot, i.notes_zh FROM itinerary_items i "
            f"JOIN itinerary_days d ON i.day_id=d.day_id "
            f"WHERE d.plan_id='{PLAN_ID}' "
            f"ORDER BY d.day_number, i.start_time LIMIT 1"
        ))
        row = first.fetchone()
        print(f"\n=== FIRST ITEM poi_snapshot ===")
        print(json.dumps(row[0], ensure_ascii=False, indent=2) if row[0] else "EMPTY!")
        print(f"\n=== FIRST ITEM notes_zh ===")
        print(row[1] if row[1] else "EMPTY!")

if __name__ == "__main__":
    asyncio.run(main())
