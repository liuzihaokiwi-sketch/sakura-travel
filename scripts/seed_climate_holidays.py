"""
A3: 录入北海道气候数据 + 2026年日本假日数据
运行：python scripts/seed_climate_holidays.py
"""
import asyncio
import json
import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from app.db.session import AsyncSessionLocal

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIMATE_FILE = os.path.join(BASE_DIR, "data", "seed", "climate_hokkaido.json")
HOLIDAYS_FILE = os.path.join(BASE_DIR, "data", "seed", "holidays_jp_2026.json")


async def seed_climate(session) -> None:
    print("[A3] seeding climate data...")
    with open(CLIMATE_FILE, encoding="utf-8") as f:
        data = json.load(f)

    rows = []
    for city_code, city_data in data["cities"].items():
        for m in city_data["months"]:
            rows.append({
                "city_code": city_code,
                "month": m["month"],
                "avg_temp_high": m["avg_temp_high"],
                "avg_temp_low": m["avg_temp_low"],
                "precipitation": m["precipitation"],
                "sunshine_hours": m["sunshine_hours"],
                "snow_days": m.get("snow_days"),
                "notes": m.get("notes"),
                "data_source": "Japan Meteorological Agency (30-year normals)",
            })

    for row in rows:
        await session.execute(
            text("""
                INSERT INTO city_climate_monthly
                  (city_code, month, avg_temp_high, avg_temp_low, precipitation,
                   sunshine_hours, snow_days, notes, data_source)
                VALUES
                  (:city_code, :month, :avg_temp_high, :avg_temp_low, :precipitation,
                   :sunshine_hours, :snow_days, :notes, :data_source)
                ON CONFLICT (city_code, month) DO UPDATE SET
                  avg_temp_high = EXCLUDED.avg_temp_high,
                  avg_temp_low = EXCLUDED.avg_temp_low,
                  precipitation = EXCLUDED.precipitation,
                  sunshine_hours = EXCLUDED.sunshine_hours,
                  snow_days = EXCLUDED.snow_days,
                  notes = EXCLUDED.notes
            """),
            row,
        )

    city_count = len(data["cities"])
    print(f"  OK: {len(rows)} climate records ({city_count} cities x 12 months)")


async def seed_holidays(session) -> None:
    print("[A3] seeding holiday data...")
    with open(HOLIDAYS_FILE, encoding="utf-8") as f:
        data = json.load(f)

    # National holidays
    holiday_rows = []
    for h in data["holidays"]:
        holiday_rows.append({
            "date": date.fromisoformat(h["date"]),
            "end_date": None,
            "name_ja": h.get("name_ja"),
            "name_en": h["name_en"],
            "country_code": "JP",
            "city_code": None,
            "type": h["type"],
            "crowd_level": h.get("crowd_level"),
            "notes": h.get("notes"),
        })

    # Hokkaido festivals
    for f in data["hokkaido_festivals"]:
        holiday_rows.append({
            "date": date.fromisoformat(f["start_date"]),
            "end_date": date.fromisoformat(f["end_date"]) if f.get("end_date") else None,
            "name_ja": f.get("name_ja"),
            "name_en": f["name_en"],
            "country_code": "JP",
            "city_code": f["city_code"],
            "type": "festival",
            "crowd_level": f.get("crowd_level"),
            "notes": f.get("notes"),
        })

    for row in holiday_rows:
        await session.execute(
            text("""
                INSERT INTO holiday_calendar
                  (date, end_date, name_ja, name_en, country_code, city_code, type, crowd_level, notes)
                VALUES
                  (:date, :end_date, :name_ja, :name_en, :country_code, :city_code, :type, :crowd_level, :notes)
                ON CONFLICT DO NOTHING
            """),
            row,
        )

    print(f"  OK: {len(data['holidays'])} national holidays + {len(data['hokkaido_festivals'])} Hokkaido festivals")


async def main() -> None:
    async with AsyncSessionLocal() as session:
        await seed_climate(session)
        await seed_holidays(session)
        await session.commit()
    print("\nA3 seed DONE")


if __name__ == "__main__":
    asyncio.run(main())
