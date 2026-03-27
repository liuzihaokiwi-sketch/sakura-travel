"""
Minimal seed for Phase 2 real-circle validation.

Scope:
- city_circles
- activity_clusters
- hotel_strategy_presets

Target circles:
- kanto_city_circle
- hokkaido_city_circle
- south_china_five_city_circle
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from sqlalchemy import and_, select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.models.city_circles import ActivityCluster, CityCircle, HotelStrategyPreset
from app.db.session import AsyncSessionLocal

CIRCLES: list[dict] = [
    {
        "circle_id": "kanto_city_circle",
        "name_zh": "关东城市圈",
        "name_en": "Kanto City Circle",
        "base_city_codes": ["tokyo"],
        "extension_city_codes": ["yokohama", "kamakura"],
        "min_days": 4,
        "max_days": 9,
        "recommended_days_range": "4-7",
        "tier": "hot",
        "fit_profiles": {
            "party_types": ["couple", "friends", "family_child", "solo"],
            "themes": ["culture", "food", "photo", "shopping"],
        },
        "friendly_airports": ["HND", "NRT"],
        "season_strength": {"spring": 0.9, "summer": 0.7, "autumn": 0.8, "winter": 0.7},
        "notes": "Phase2 minimal real seed.",
        "is_active": True,
    },
    {
        "circle_id": "hokkaido_city_circle",
        "name_zh": "北海道城市圈",
        "name_en": "Hokkaido City Circle",
        "base_city_codes": ["sapporo"],
        "extension_city_codes": ["otaru", "niseko"],
        "min_days": 4,
        "max_days": 8,
        "recommended_days_range": "4-6",
        "tier": "hot",
        "fit_profiles": {
            "party_types": ["couple", "friends", "family_child", "solo"],
            "themes": ["nature", "food", "culture", "photo"],
        },
        "friendly_airports": ["CTS"],
        "season_strength": {"spring": 0.7, "summer": 0.8, "autumn": 0.8, "winter": 0.95},
        "notes": "Phase2 minimal real seed.",
        "is_active": True,
    },
    {
        "circle_id": "south_china_five_city_circle",
        "name_zh": "华南五城圈",
        "name_en": "South China Five-City Circle",
        "base_city_codes": ["guangzhou", "shenzhen"],
        "extension_city_codes": ["foshan", "dongguan", "zhuhai"],
        "min_days": 4,
        "max_days": 8,
        "recommended_days_range": "4-6",
        "tier": "hot",
        "fit_profiles": {
            "party_types": ["couple", "friends", "family_child", "solo"],
            "themes": ["food", "photo", "citywalk", "culture"],
        },
        "friendly_airports": ["CAN", "SZX"],
        "season_strength": {"spring": 0.8, "summer": 0.75, "autumn": 0.8, "winter": 0.85},
        "notes": "Phase2 minimal real seed.",
        "is_active": True,
    },
]

CLUSTERS: list[dict] = [
    {
        "cluster_id": "tok_asakusa_senso_ji",
        "circle_id": "kanto_city_circle",
        "name_zh": "浅草寺经典线",
        "name_en": "Asakusa Senso-ji Classic",
        "level": "S",
        "default_duration": "half_day",
        "primary_corridor": "asakusa",
        "seasonality": ["all_year"],
        "profile_fit": ["culture", "photo", "first_timer"],
        "trip_role": "anchor",
        "time_window_strength": "medium",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": True,
        "notes": "phase2 must-go anchor",
    },
    {
        "cluster_id": "tok_shinjuku_shibuya_night",
        "circle_id": "kanto_city_circle",
        "name_zh": "新宿涩谷夜生活",
        "name_en": "Shinjuku Shibuya Night",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "shinjuku",
        "seasonality": ["all_year"],
        "profile_fit": ["nightlife", "friends"],
        "trip_role": "enrichment",
        "time_window_strength": "weak",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "phase2 do-not-go validation",
    },
    {
        "cluster_id": "tok_yokohama_bayside",
        "circle_id": "kanto_city_circle",
        "name_zh": "横滨港区漫游",
        "name_en": "Yokohama Bayside Walk",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "yokohama_bay",
        "seasonality": ["all_year"],
        "profile_fit": ["photo", "food", "couple"],
        "trip_role": "anchor",
        "time_window_strength": "weak",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": True,
        "notes": "phase2 filler",
    },
    {
        "cluster_id": "hok_sapporo_odori_susukino",
        "circle_id": "hokkaido_city_circle",
        "name_zh": "札幌大通薄野线",
        "name_en": "Sapporo Odori Susukino",
        "level": "S",
        "default_duration": "half_day",
        "primary_corridor": "sapporo_central",
        "seasonality": ["all_year", "winter"],
        "profile_fit": ["food", "culture", "first_timer"],
        "trip_role": "anchor",
        "time_window_strength": "weak",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": True,
        "notes": "phase2 must-go anchor",
    },
    {
        "cluster_id": "hok_niseko_skiing",
        "circle_id": "hokkaido_city_circle",
        "name_zh": "二世谷滑雪",
        "name_en": "Niseko Skiing",
        "level": "B",
        "default_duration": "full_day",
        "primary_corridor": "niseko",
        "seasonality": ["winter"],
        "profile_fit": ["skiing", "friends"],
        "trip_role": "enrichment",
        "time_window_strength": "strong",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "phase2 do-not-go validation",
    },
    {
        "cluster_id": "hok_otaru_canal_day",
        "circle_id": "hokkaido_city_circle",
        "name_zh": "小樽运河半日",
        "name_en": "Otaru Canal Half Day",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "otaru",
        "seasonality": ["all_year"],
        "profile_fit": ["photo", "couple", "culture"],
        "trip_role": "anchor",
        "time_window_strength": "weak",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": True,
        "notes": "phase2 filler",
    },
    {
        "cluster_id": "gz_canton_tower_river_night",
        "circle_id": "south_china_five_city_circle",
        "name_zh": "广州塔珠江夜景",
        "name_en": "Canton Tower and Pearl River Night",
        "level": "S",
        "default_duration": "half_day",
        "primary_corridor": "zhujiang_new_town",
        "seasonality": ["all_year"],
        "profile_fit": ["photo", "citywalk", "couple"],
        "trip_role": "anchor",
        "time_window_strength": "weak",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": True,
        "notes": "phase2 must-go anchor",
    },
    {
        "cluster_id": "sz_window_of_the_world",
        "circle_id": "south_china_five_city_circle",
        "name_zh": "世界之窗",
        "name_en": "Window of the World",
        "level": "B",
        "default_duration": "half_day",
        "primary_corridor": "nanshan",
        "seasonality": ["all_year"],
        "profile_fit": ["theme_park", "family_child"],
        "trip_role": "enrichment",
        "time_window_strength": "medium",
        "reservation_pressure": "medium",
        "secondary_attach_capacity": 1,
        "default_selected": False,
        "notes": "phase2 do-not-go validation",
    },
    {
        "cluster_id": "sz_nanshan_bay_walk",
        "circle_id": "south_china_five_city_circle",
        "name_zh": "深圳湾海滨漫游",
        "name_en": "Shenzhen Bay Walk",
        "level": "A",
        "default_duration": "half_day",
        "primary_corridor": "shenzhen_bay",
        "seasonality": ["all_year"],
        "profile_fit": ["photo", "citywalk", "food"],
        "trip_role": "anchor",
        "time_window_strength": "weak",
        "reservation_pressure": "low",
        "secondary_attach_capacity": 2,
        "default_selected": True,
        "notes": "phase2 filler",
    },
]

HOTEL_PRESETS: list[dict] = [
    {
        "circle_id": "kanto_city_circle",
        "name_zh": "关东单基点（东京）",
        "min_days": 4,
        "max_days": 9,
        "bases": [
            {
                "base_city": "tokyo",
                "area": "asakusa",
                "nights_range": "4-8",
                "served_cluster_ids": [
                    "tok_asakusa_senso_ji",
                    "tok_yokohama_bayside",
                    "tok_shinjuku_shibuya_night",
                ],
            }
        ],
        "fit_party_types": ["couple", "friends", "family_child", "solo"],
        "fit_budget_levels": ["budget", "mid", "premium"],
        "switch_count": 0,
        "switch_cost_minutes": 0,
        "last_night_airport_minutes": 70,
        "priority": 5,
        "notes": "Phase2 minimal seed preset.",
        "is_active": True,
    },
    {
        "circle_id": "hokkaido_city_circle",
        "name_zh": "北海道单基点（札幌）",
        "min_days": 4,
        "max_days": 8,
        "bases": [
            {
                "base_city": "sapporo",
                "area": "sapporo_station",
                "nights_range": "3-7",
                "served_cluster_ids": [
                    "hok_sapporo_odori_susukino",
                    "hok_otaru_canal_day",
                    "hok_niseko_skiing",
                ],
            }
        ],
        "fit_party_types": ["couple", "friends", "family_child", "solo"],
        "fit_budget_levels": ["budget", "mid", "premium"],
        "switch_count": 0,
        "switch_cost_minutes": 0,
        "last_night_airport_minutes": 45,
        "priority": 5,
        "notes": "Phase2 minimal seed preset.",
        "is_active": True,
    },
    {
        "circle_id": "south_china_five_city_circle",
        "name_zh": "华南双基点（广深）",
        "min_days": 4,
        "max_days": 8,
        "bases": [
            {
                "base_city": "guangzhou",
                "area": "zhujiang_new_town",
                "nights_range": "2-3",
                "served_cluster_ids": ["gz_canton_tower_river_night"],
            },
            {
                "base_city": "shenzhen",
                "area": "nanshan",
                "nights_range": "1-3",
                "served_cluster_ids": ["sz_nanshan_bay_walk", "sz_window_of_the_world"],
            },
        ],
        "fit_party_types": ["couple", "friends", "family_child", "solo"],
        "fit_budget_levels": ["budget", "mid", "premium"],
        "switch_count": 1,
        "switch_cost_minutes": 70,
        "last_night_airport_minutes": 40,
        "priority": 5,
        "notes": "Phase2 minimal seed preset.",
        "is_active": True,
    },
]


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        inserted = {"circles": 0, "clusters": 0, "presets": 0}

        for data in CIRCLES:
            existing = await session.get(CityCircle, data["circle_id"])
            if existing is None:
                session.add(CityCircle(**data))
                inserted["circles"] += 1

        for data in CLUSTERS:
            existing = await session.get(ActivityCluster, data["cluster_id"])
            if existing is None:
                session.add(ActivityCluster(**data))
                inserted["clusters"] += 1

        for data in HOTEL_PRESETS:
            q = await session.execute(
                select(HotelStrategyPreset).where(
                    and_(
                        HotelStrategyPreset.circle_id == data["circle_id"],
                        HotelStrategyPreset.name_zh == data["name_zh"],
                    )
                )
            )
            if q.scalar_one_or_none() is None:
                session.add(HotelStrategyPreset(**data))
                inserted["presets"] += 1

        await session.commit()
        print(
            "seed_phase2_real_circles done:",
            f"circles+{inserted['circles']}",
            f"clusters+{inserted['clusters']}",
            f"presets+{inserted['presets']}",
        )


if __name__ == "__main__":
    asyncio.run(seed())
