"""
FIX-1: 从 entity_base 实际统计更新 city_data_coverage.current_count

对于有 sub_category 的行（sapporo），用 poi_category/cuisine_type/price_tier 来匹配；
对于 sub_category='general' 的行（其他城市），直接统计城市+类型总数。

运行: python scripts/fix_coverage_counts.py
"""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import AsyncSessionLocal

# sub_category → poi_category / cuisine_type / price_tier 映射
POI_SUBCAT_MAP = {
    "shrine_temple":   ["shrine", "temple"],
    "museum_art":      ["museum"],
    "park_nature":     ["park", "nature"],
    "landmark_tower":  ["landmark", "tower", "viewpoint"],
    "onsen":           ["onsen", "hot_spring"],
    "experience":      ["experience", "activity"],
    "shopping_district": ["shopping", "commercial"],
    "souvenir_shop":   ["specialty_shop", "souvenir"],
    "general":         None,   # 无子分类 → 统计全部
}

RESTAURANT_SUBCAT_MAP = {
    "ramen":              ["ramen"],
    "sushi_seafood":      ["sushi", "seafood"],
    "izakaya":            ["izakaya"],
    "yakiniku_genghis_khan": ["yakiniku", "genghis_khan", "bbq"],
    "soup_curry":         ["soup_curry", "curry"],
    "sweets_cafe":        ["sweets", "cafe", "dessert"],
    "breakfast":          ["breakfast"],
    "kaiseki_fine":       ["kaiseki", "fine_dining"],
    "general":            None,
}

HOTEL_SUBCAT_MAP = {
    "budget":    ["budget"],
    "mid":       ["mid"],
    "premium":   ["premium"],
    "luxury":    ["luxury"],
    "general":   None,
}


async def get_actual_count(session, city_code: str, entity_type: str,
                           sub_category: str) -> int:
    """从 entity_base + 子表中统计实际数量"""
    if sub_category == "general" or sub_category is None:
        r = await session.execute(text("""
            SELECT COUNT(*) FROM entity_base
            WHERE city_code = :city AND entity_type = :etype AND is_active = true
        """), {"city": city_code, "etype": entity_type})
        return r.scalar() or 0

    if entity_type == "poi":
        cats = POI_SUBCAT_MAP.get(sub_category, [sub_category])
        if not cats:
            r = await session.execute(text("""
                SELECT COUNT(*) FROM entity_base
                WHERE city_code = :city AND entity_type = 'poi' AND is_active = true
            """), {"city": city_code})
            return r.scalar() or 0
        r = await session.execute(text("""
            SELECT COUNT(*) FROM entity_base e
            JOIN pois p ON p.entity_id = e.entity_id
            WHERE e.city_code = :city AND e.is_active = true
              AND p.poi_category = ANY(:cats)
        """), {"city": city_code, "cats": cats})
        return r.scalar() or 0

    elif entity_type == "restaurant":
        cats = RESTAURANT_SUBCAT_MAP.get(sub_category, [sub_category])
        if not cats:
            r = await session.execute(text("""
                SELECT COUNT(*) FROM entity_base
                WHERE city_code = :city AND entity_type = 'restaurant' AND is_active = true
            """), {"city": city_code})
            return r.scalar() or 0
        r = await session.execute(text("""
            SELECT COUNT(*) FROM entity_base e
            JOIN restaurants r ON r.entity_id = e.entity_id
            WHERE e.city_code = :city AND e.is_active = true
              AND r.cuisine_type = ANY(:cats)
        """), {"city": city_code, "cats": cats})
        return r.scalar() or 0

    elif entity_type == "hotel":
        tiers = HOTEL_SUBCAT_MAP.get(sub_category, [sub_category])
        if not tiers:
            r = await session.execute(text("""
                SELECT COUNT(*) FROM entity_base
                WHERE city_code = :city AND entity_type = 'hotel' AND is_active = true
            """), {"city": city_code})
            return r.scalar() or 0
        r = await session.execute(text("""
            SELECT COUNT(*) FROM entity_base e
            JOIN hotels h ON h.entity_id = e.entity_id
            WHERE e.city_code = :city AND e.is_active = true
              AND h.price_tier = ANY(:tiers)
        """), {"city": city_code, "tiers": tiers})
        return r.scalar() or 0

    return 0


async def main() -> None:
    async with AsyncSessionLocal() as session:
        # 加载所有 coverage 行
        rows = (await session.execute(text(
            "SELECT id, city_code, entity_type, sub_category FROM city_data_coverage"
        ))).fetchall()
        print(f"[FIX-1] Updating {len(rows)} coverage rows...")

        updated = 0
        for row_id, city_code, entity_type, sub_category in rows:
            count = await get_actual_count(session, city_code, entity_type, sub_category)
            await session.execute(text("""
                UPDATE city_data_coverage
                SET current_count = :count, last_updated = NOW()
                WHERE id = :id
            """), {"count": count, "id": row_id})
            updated += 1

        await session.commit()
        print(f"  Updated {updated} rows")

        # Verify sapporo
        r = await session.execute(text("""
            SELECT entity_type, sub_category, current_count, target_count
            FROM city_data_coverage
            WHERE city_code = 'sapporo'
            ORDER BY entity_type, sub_category
        """))
        print("\nsapporo coverage:")
        for row in r.fetchall():
            pct = f"{row[2]*100//row[3]}%" if row[3] else "?"
            print(f"  {row[0]:<12} {row[1]:<25} {row[2]:>4}/{row[3]:<4} {pct}")

    print("\nFIX-1 DONE")


if __name__ == "__main__":
    asyncio.run(main())
