"""Seed route_templates into DB from JSON files."""
import asyncio
import json
import uuid
from pathlib import Path

from sqlalchemy import text
from app.db.session import AsyncSessionLocal

SEED_DIR = Path("data/seed/route_templates")


async def seed_templates():
    files = list(SEED_DIR.glob("*.json"))
    print(f"Found {len(files)} template files")

    async with AsyncSessionLocal() as session:
        for f in files:
            data = json.loads(f.read_text(encoding="utf-8"))
            code = data["template_code"]
            name_zh = data.get("name_zh", code)
            city_code = data.get("city_code", "tokyo")
            duration = data.get("total_days", 5)
            theme = data.get("theme", "classic")

            # Check if already exists
            result = await session.execute(
                text("SELECT template_id FROM route_templates WHERE name_zh = :name"),
                {"name": name_zh},
            )
            existing = result.scalar_one_or_none()
            if existing:
                print(f"  SKIP {code} (already exists)")
                continue

            await session.execute(
                text("""
                    INSERT INTO route_templates (template_id, name_zh, city_code, duration_days, theme, sku_tier, template_data, is_active)
                    VALUES (:id, :name_zh, :city, :days, :theme, 'standard', cast(:data as jsonb), true)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "name_zh": name_zh,
                    "city": city_code,
                    "days": duration,
                    "theme": theme,
                    "data": json.dumps(data, ensure_ascii=False),
                },
            )
            print(f"  INSERT {code}")

        await session.commit()
        print("Done!")


if __name__ == "__main__":
    asyncio.run(seed_templates())
