"""
A1: 录入数据源注册表 + 北海道城市覆盖目标数量初始数据
运行：python scripts/seed_data_sources.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.db.session import AsyncSessionLocal
from app.db.models.data_sources import DataSourceRegistry, CityDataCoverage


DATA_SOURCES = [
    {
        "source_name": "google_places",
        "source_type": "infrastructure",
        "display_name": "Google Places API",
        "base_url": "https://maps.googleapis.com/maps/api/place",
        "coverage": {"countries": ["JP", "CN", "HK", "MO", "SG", "TH", "KR"]},
        "entity_types": ["poi", "hotel", "restaurant"],
        "priority": 10,
        "is_active": True,
        "rate_limit": {"requests_per_minute": 60, "daily_limit": 5000},
        "auth_config": {"api_key_env": "GOOGLE_PLACES_API_KEY"},
        "notes": "基础设施层：坐标、营业时间、place_id、照片。不作为评分主源。",
    },
    {
        "source_name": "tabelog",
        "source_type": "rating",
        "display_name": "食べログ (Tabelog)",
        "base_url": "https://tabelog.com",
        "coverage": {"countries": ["JP"], "cities": [
            "sapporo", "otaru", "hakodate", "asahikawa", "furano",
            "noboribetsu", "niseko", "abashiri", "kushiro", "toya",
            "tokyo", "osaka", "kyoto", "nara", "kobe",
        ]},
        "entity_types": ["restaurant"],
        "priority": 1,
        "is_active": True,
        "rate_limit": {"requests_per_minute": 10, "daily_limit": 500},
        "auth_config": {},
        "notes": "日本餐厅权威评分平台。3.5+ 视为高品质，3.0-3.5 为中等。需遵守爬虫礼仪。",
    },
    {
        "source_name": "japan_guide",
        "source_type": "rating",
        "display_name": "Japan Guide",
        "base_url": "https://www.japan-guide.com",
        "coverage": {"countries": ["JP"], "cities": [
            "sapporo", "otaru", "hakodate", "asahikawa", "furano", "biei",
            "noboribetsu", "niseko", "abashiri", "kushiro", "toya",
            "tokyo", "osaka", "kyoto", "nara",
        ]},
        "entity_types": ["poi"],
        "priority": 1,
        "is_active": True,
        "rate_limit": {"requests_per_minute": 5, "daily_limit": 200},
        "auth_config": {},
        "notes": "景点权威评级（1-3星）。北海道覆盖非常全，英文内容，适合外国游客。",
    },
    {
        "source_name": "jalan",
        "source_type": "rating",
        "display_name": "じゃらん (Jalan)",
        "base_url": "https://www.jalan.net",
        "coverage": {"countries": ["JP"]},
        "entity_types": ["hotel"],
        "priority": 2,
        "is_active": True,
        "rate_limit": {"requests_per_minute": 5, "daily_limit": 200},
        "auth_config": {},
        "notes": "日本本土第一酒店平台，温泉旅馆覆盖最全。",
    },
    {
        "source_name": "rakuten_travel",
        "source_type": "rating",
        "display_name": "楽天トラベル (Rakuten Travel)",
        "base_url": "https://travel.rakuten.com",
        "coverage": {"countries": ["JP"]},
        "entity_types": ["hotel"],
        "priority": 3,
        "is_active": True,
        "rate_limit": {"requests_per_minute": 5, "daily_limit": 200},
        "auth_config": {},
        "notes": "小旅馆/民宿覆盖比 Booking 强，补充 Jalan。",
    },
    {
        "source_name": "dianping",
        "source_type": "rating",
        "display_name": "大众点评",
        "base_url": "https://www.dianping.com",
        "coverage": {"countries": ["CN"], "cities": [
            "guangzhou", "shenzhen", "foshan", "shunde",
            "shanghai", "hangzhou", "suzhou", "nanjing",
            "chaozhou", "shantou", "meizhou",
            "urumqi",
        ]},
        "entity_types": ["restaurant", "poi"],
        "priority": 1,
        "is_active": True,
        "rate_limit": {"requests_per_minute": 5, "daily_limit": 200},
        "auth_config": {},
        "notes": "3.63亿条评价，中国内地餐厅最权威。反爬严格，需注意频率。",
    },
    {
        "source_name": "openrice",
        "source_type": "rating",
        "display_name": "OpenRice 开饭喇",
        "base_url": "https://www.openrice.com",
        "coverage": {"countries": ["HK", "MO", "SG"], "cities": ["hongkong", "macau"]},
        "entity_types": ["restaurant"],
        "priority": 1,
        "is_active": True,
        "rate_limit": {"requests_per_minute": 5, "daily_limit": 200},
        "auth_config": {},
        "notes": "香港美食第一平台，覆盖港澳新。",
    },
    {
        "source_name": "ctrip",
        "source_type": "rating",
        "display_name": "携程旅行",
        "base_url": "https://you.ctrip.com",
        "coverage": {"countries": ["CN"]},
        "entity_types": ["poi", "hotel"],
        "priority": 2,
        "is_active": True,
        "rate_limit": {"requests_per_minute": 5, "daily_limit": 200},
        "auth_config": {},
        "notes": "内地景点和酒店携程覆盖最全。",
    },
    {
        "source_name": "visit_hokkaido",
        "source_type": "official",
        "display_name": "Visit Hokkaido (北海道官方旅游)",
        "base_url": "https://www.visit-hokkaido.jp",
        "coverage": {"countries": ["JP"], "cities": [
            "sapporo", "otaru", "hakodate", "asahikawa", "furano", "biei",
            "noboribetsu", "niseko", "abashiri", "kushiro", "toya",
        ]},
        "entity_types": ["poi"],
        "priority": 1,
        "is_active": True,
        "rate_limit": {"requests_per_minute": 5, "daily_limit": 100},
        "auth_config": {},
        "notes": "北海道官方旅游网站，权威性最高。",
    },
    {
        "source_name": "retty",
        "source_type": "rating",
        "display_name": "Retty",
        "base_url": "https://retty.me",
        "coverage": {"countries": ["JP"]},
        "entity_types": ["restaurant"],
        "priority": 4,
        "is_active": True,
        "rate_limit": {"requests_per_minute": 5, "daily_limit": 200},
        "auth_config": {},
        "notes": "实名评价，可信度高，补充 Tabelog 的缺漏。",
    },
]

# 北海道10城市×品类覆盖目标
# 格式：(city_code, entity_type, sub_category, target_count, sources_pending)
HOKKAIDO_COVERAGE_TARGETS = [
    # ── 札幌（大城市）────────────────────────────────────────────
    ("sapporo", "poi", "shrine_temple", 20, ["japan_guide", "google_places"]),
    ("sapporo", "poi", "museum_art", 15, ["japan_guide", "google_places"]),
    ("sapporo", "poi", "park_nature", 15, ["japan_guide", "google_places"]),
    ("sapporo", "poi", "shopping_district", 8, ["google_places"]),
    ("sapporo", "poi", "landmark_tower", 6, ["japan_guide", "google_places"]),
    ("sapporo", "poi", "onsen", 8, ["japan_guide", "google_places"]),
    ("sapporo", "poi", "experience", 8, ["google_places"]),
    ("sapporo", "restaurant", "ramen", 20, ["tabelog", "google_places"]),
    ("sapporo", "restaurant", "sushi_seafood", 20, ["tabelog", "google_places"]),
    ("sapporo", "restaurant", "izakaya", 15, ["tabelog"]),
    ("sapporo", "restaurant", "yakiniku_genghis_khan", 12, ["tabelog", "google_places"]),
    ("sapporo", "restaurant", "soup_curry", 10, ["tabelog", "google_places"]),
    ("sapporo", "restaurant", "sweets_cafe", 15, ["tabelog", "google_places"]),
    ("sapporo", "restaurant", "breakfast", 8, ["google_places"]),
    ("sapporo", "restaurant", "kaiseki_fine", 8, ["tabelog"]),
    ("sapporo", "hotel", "budget", 15, ["google_places"]),
    ("sapporo", "hotel", "mid", 20, ["google_places"]),
    ("sapporo", "hotel", "premium", 12, ["jalan", "google_places"]),
    ("sapporo", "hotel", "luxury", 6, ["jalan", "google_places"]),
    ("sapporo", "poi", "souvenir_shop", 12, ["google_places"]),

    # ── 小樽（中型城市）──────────────────────────────────────────
    ("otaru", "poi", "general", 40, ["japan_guide", "google_places"]),
    ("otaru", "restaurant", "general", 50, ["tabelog", "google_places"]),
    ("otaru", "hotel", "general", 25, ["jalan", "google_places"]),
    ("otaru", "poi", "souvenir_shop", 8, ["google_places"]),

    # ── 函馆（中型城市）──────────────────────────────────────────
    ("hakodate", "poi", "general", 40, ["japan_guide", "google_places"]),
    ("hakodate", "restaurant", "general", 60, ["tabelog", "google_places"]),
    ("hakodate", "hotel", "general", 30, ["jalan", "google_places"]),
    ("hakodate", "poi", "souvenir_shop", 8, ["google_places"]),

    # ── 旭川（中型城市）──────────────────────────────────────────
    ("asahikawa", "poi", "general", 30, ["japan_guide", "google_places"]),
    ("asahikawa", "restaurant", "general", 40, ["tabelog", "google_places"]),
    ("asahikawa", "hotel", "general", 20, ["jalan", "google_places"]),

    # ── 富良野（小城市）──────────────────────────────────────────
    ("furano", "poi", "general", 20, ["japan_guide", "google_places"]),
    ("furano", "restaurant", "general", 20, ["tabelog", "google_places"]),
    ("furano", "hotel", "general", 15, ["jalan", "google_places"]),

    # ── 美瑛（小城市）────────────────────────────────────────────
    ("biei", "poi", "general", 15, ["japan_guide", "google_places"]),
    ("biei", "restaurant", "general", 15, ["tabelog", "google_places"]),
    ("biei", "hotel", "general", 10, ["jalan", "google_places"]),

    # ── 登别（小城市）────────────────────────────────────────────
    ("noboribetsu", "poi", "general", 15, ["japan_guide", "google_places"]),
    ("noboribetsu", "restaurant", "general", 15, ["tabelog", "google_places"]),
    ("noboribetsu", "hotel", "general", 12, ["jalan", "google_places"]),

    # ── 洞爷湖（小城市）──────────────────────────────────────────
    ("toya", "poi", "general", 12, ["japan_guide", "google_places"]),
    ("toya", "restaurant", "general", 15, ["tabelog", "google_places"]),
    ("toya", "hotel", "general", 12, ["jalan", "google_places"]),

    # ── 网走（小城市）────────────────────────────────────────────
    ("abashiri", "poi", "general", 12, ["japan_guide", "google_places"]),
    ("abashiri", "restaurant", "general", 15, ["tabelog", "google_places"]),
    ("abashiri", "hotel", "general", 10, ["jalan", "google_places"]),

    # ── 钏路（小城市）────────────────────────────────────────────
    ("kushiro", "poi", "general", 12, ["japan_guide", "google_places"]),
    ("kushiro", "restaurant", "general", 15, ["tabelog", "google_places"]),
    ("kushiro", "hotel", "general", 10, ["jalan", "google_places"]),
]


async def seed_data_sources(session: AsyncSession) -> None:
    print("[A1] seeding data sources...")
    for src in DATA_SOURCES:
        stmt = insert(DataSourceRegistry).values(**src).on_conflict_do_update(
            index_elements=["source_name"],
            set_={k: src[k] for k in src if k != "source_name"},
        )
        await session.execute(stmt)
    print(f"  OK: {len(DATA_SOURCES)} data sources inserted/updated")


async def seed_coverage_targets(session: AsyncSession) -> None:
    print("[A1] seeding coverage targets...")
    count = 0
    for city_code, entity_type, sub_category, target_count, sources_pending in HOKKAIDO_COVERAGE_TARGETS:
        stmt = insert(CityDataCoverage).values(
            city_code=city_code,
            entity_type=entity_type,
            sub_category=sub_category,
            target_count=target_count,
            current_count=0,
            verified_count=0,
            sources_used=[],
            sources_pending=sources_pending,
        ).on_conflict_do_update(
            constraint="uq_city_coverage",
            set_={
                "target_count": target_count,
                "sources_pending": sources_pending,
            },
        )
        await session.execute(stmt)
        count += 1
    city_count = len(set(t[0] for t in HOKKAIDO_COVERAGE_TARGETS))
    print(f"  OK: {count} coverage targets across {city_count} cities")


async def main() -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await seed_data_sources(session)
            await seed_coverage_targets(session)
    print("\nA1 seed DONE")


if __name__ == "__main__":
    asyncio.run(main())
