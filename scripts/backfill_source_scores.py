"""
FIX-3: 从子表回填评分到 entity_source_scores

- restaurants.tabelog_score → entity_source_scores (source_name='tabelog')
  normalized_score = tabelog_score / 5.0 * 100  (Tabelog 0-5, 通常 3.0-4.5)
- pois.google_rating → entity_source_scores (source_name='google_places')
  normalized_score = google_rating / 5.0 * 100
- hotels.google_rating → entity_source_scores (source_name='google_places')
  normalized_score = google_rating / 5.0 * 100

运行: python scripts/backfill_source_scores.py
"""
import asyncio, sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import AsyncSessionLocal

UPSERT_SQL = """
    INSERT INTO entity_source_scores
      (entity_id, source_name, raw_score, normalized_score, review_count, extra, fetched_at)
    VALUES
      (:entity_id, :source_name, :raw_score, :normalized_score, :review_count,
       CAST(:extra AS jsonb), NOW())
    ON CONFLICT (entity_id, source_name) DO UPDATE SET
      raw_score = EXCLUDED.raw_score,
      normalized_score = EXCLUDED.normalized_score,
      review_count = EXCLUDED.review_count,
      fetched_at = NOW()
"""


async def backfill_tabelog(session) -> int:
    """restaurants.tabelog_score → entity_source_scores[tabelog]"""
    rows = (await session.execute(text("""
        SELECT r.entity_id, r.tabelog_score, r.cuisine_type
        FROM restaurants r
        JOIN entity_base e ON e.entity_id = r.entity_id
        WHERE e.is_active = true AND r.tabelog_score IS NOT NULL
    """))).fetchall()

    count = 0
    for entity_id, score, cuisine in rows:
        normalized = round(float(score) / 5.0 * 100, 1)
        await session.execute(text(UPSERT_SQL), {
            "entity_id": str(entity_id),
            "source_name": "tabelog",
            "raw_score": float(score),
            "normalized_score": normalized,
            "review_count": None,
            "extra": json.dumps({"cuisine_type": cuisine}),
        })
        count += 1
    return count


async def backfill_google_pois(session) -> int:
    """pois.google_rating → entity_source_scores[google_places]"""
    rows = (await session.execute(text("""
        SELECT p.entity_id, p.google_rating, p.google_review_count, p.poi_category
        FROM pois p
        JOIN entity_base e ON e.entity_id = p.entity_id
        WHERE e.is_active = true AND p.google_rating IS NOT NULL
    """))).fetchall()

    count = 0
    for entity_id, rating, review_count, poi_cat in rows:
        normalized = round(float(rating) / 5.0 * 100, 1)
        await session.execute(text(UPSERT_SQL), {
            "entity_id": str(entity_id),
            "source_name": "google_places",
            "raw_score": float(rating),
            "normalized_score": normalized,
            "review_count": review_count,
            "extra": json.dumps({"poi_category": poi_cat}),
        })
        count += 1
    return count


async def backfill_google_hotels(session) -> int:
    """hotels.google_rating → entity_source_scores[google_places]"""
    rows = (await session.execute(text("""
        SELECT h.entity_id, h.google_rating, h.price_tier, h.hotel_type
        FROM hotels h
        JOIN entity_base e ON e.entity_id = h.entity_id
        WHERE e.is_active = true AND h.google_rating IS NOT NULL
    """))).fetchall()

    count = 0
    for entity_id, rating, price_tier, hotel_type in rows:
        normalized = round(float(rating) / 5.0 * 100, 1)
        await session.execute(text(UPSERT_SQL), {
            "entity_id": str(entity_id),
            "source_name": "google_places",
            "raw_score": float(rating),
            "normalized_score": normalized,
            "review_count": None,
            "extra": json.dumps({"price_tier": price_tier, "hotel_type": hotel_type}),
        })
        count += 1
    return count


async def main() -> None:
    async with AsyncSessionLocal() as session:
        print("[FIX-3] Backfilling source scores...")

        tabelog_count = await backfill_tabelog(session)
        print(f"  tabelog: {tabelog_count} rows")

        poi_count = await backfill_google_pois(session)
        print(f"  google_places (poi): {poi_count} rows")

        hotel_count = await backfill_google_hotels(session)
        print(f"  google_places (hotel): {hotel_count} rows")

        await session.commit()

        # Verify
        r = await session.execute(text(
            "SELECT source_name, COUNT(*) FROM entity_source_scores GROUP BY source_name ORDER BY source_name"
        ))
        print("\nentity_source_scores by source:")
        for row in r.fetchall():
            print(f"  {row[0]}: {row[1]}")

    print("\nFIX-3 DONE")


if __name__ == "__main__":
    asyncio.run(main())
