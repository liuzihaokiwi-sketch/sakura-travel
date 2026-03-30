"""
C3: 从 C2 的维度评分自动推断标签，存入 entity_tags

运行: python scripts/generate_review_tags.py
"""
import asyncio, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import AsyncSessionLocal

DIMENSION_TAG_RULES = [
    ("queue_risk","high","practical","long_queue"),
    ("queue_risk","medium","practical","moderate_queue"),
    ("reservation_difficulty","hard","practical","reservation_required"),
    ("payment_method","cash_only","practical","cash_only"),
    ("language_friendliness","english_ok","practical","english_ok"),
    ("value_perception","excellent","experience","great_value"),
    ("value_perception","poor","experience","pricey"),
    ("weather_sensitivity","rain_ok","practical","rainy_day_ok"),
    ("weather_sensitivity","rain_ruins","practical","outdoor_only"),
    ("weather_sensitivity","indoor_ok","practical","rainy_day_ok"),
    ("physical_demand","strenuous","practical","physically_demanding"),
    ("physical_demand","easy","audience","accessible"),
    ("best_timing","morning","experience","early_morning_best"),
    ("best_timing","evening","experience","evening_best"),
    ("photo_value","excellent","experience","photo_spot"),
    ("crowd_pattern","always_crowded","practical","always_crowded"),
    ("child_friendly","great","audience","family_friendly"),
    ("child_friendly","not_suitable","audience","adults_only"),
    ("season_dependency","specific_season","experience","seasonal"),
    ("bath_quality","excellent","experience","great_bath"),
    ("breakfast_quality","excellent","experience","great_breakfast"),
    ("soundproofing","poor","practical","noisy_rooms"),
    ("location_convenience","excellent","practical","great_location"),
    ("best_for","couple","audience","couple"),
    ("best_for","family","audience","family_friendly"),
    ("best_for","business","audience","business_friendly"),
]

POS_KEYWORD_RULES = [
    ("無料","practical","free_entry"),("免費","practical","free_entry"),
    ("無料","practical","free_entry"),
    ("英語","practical","english_ok"),("English","practical","english_ok"),
    ("排队","practical","long_queue"),("並ぶ","practical","long_queue"),
    ("夜景","experience","night_view"),
    ("写真","experience","photo_spot"),("フォト","experience","photo_spot"),
    ("子供","audience","family_friendly"),("家族","audience","family_friendly"),
    ("カップル","audience","couple"),
    ("バリアフリー","audience","accessible"),
    ("予約","practical","reservation_required"),
]


async def main():
    async with AsyncSessionLocal() as session:
        rows = (await session.execute(text("""
            SELECT ers.entity_id, ers.positive_tags, ers.negative_tags,
                   ers.summary_tags, ers.queue_risk_level, e.entity_type
            FROM entity_review_signals ers
            JOIN entity_base e ON e.entity_id = ers.entity_id
            WHERE ers.rating_source = 'google_reviews'
        """))).fetchall()

        print(f"[C3] Processing {len(rows)} entities...")
        total = 0

        for entity_id, pos_tags, neg_tags, dims, queue_risk, entity_type in rows:
            pos_list = pos_tags if isinstance(pos_tags, list) else []
            neg_list = neg_tags if isinstance(neg_tags, list) else []
            dims_dict = dims if isinstance(dims, dict) else {}

            tags = set()
            for dk, dv, ns, tv in DIMENSION_TAG_RULES:
                if dims_dict.get(dk) == dv:
                    tags.add((ns, tv))
            if queue_risk == "high":
                tags.add(("practical", "long_queue"))
            elif queue_risk == "medium":
                tags.add(("practical", "moderate_queue"))
            all_text = " ".join(pos_list + neg_list)
            for kw, ns, tv in POS_KEYWORD_RULES:
                if kw in all_text:
                    tags.add((ns, tv))

            await session.execute(text(
                "DELETE FROM entity_tags WHERE entity_id=:eid AND source='algorithm'"
            ), {"eid": str(entity_id)})

            for ns, tv in tags:
                await session.execute(text("""
                    INSERT INTO entity_tags (entity_id, tag_namespace, tag_value, source)
                    VALUES (:eid, :ns, :tv, 'algorithm')
                    ON CONFLICT DO NOTHING
                """), {"eid": str(entity_id), "ns": ns, "tv": tv})
                total += 1

        await session.commit()
        print(f"  OK: {total} tags inserted")

        r = await session.execute(text("""
            SELECT tag_namespace, tag_value, COUNT(*)
            FROM entity_tags WHERE source='algorithm'
            GROUP BY tag_namespace, tag_value ORDER BY count DESC LIMIT 20
        """))
        print("Top tags:")
        for row in r.fetchall():
            print(f"  {row[0]:<12} {row[1]:<25} {row[2]}")

    print("\nC3 DONE")


if __name__ == "__main__":
    asyncio.run(main())
