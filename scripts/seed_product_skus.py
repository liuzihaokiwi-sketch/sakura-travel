#!/usr/bin/env python3
"""
D2.1  product_sku 种子数据写入
用法: python scripts/seed_product_skus.py [--dry-run]
功能: 幂等写入 6 个 SKU 记录到 product_sku 表（已存在则跳过/更新）
"""
from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

# ── 路径修复 ──────────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.db.models.business import ProductSku

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── SKU 定义 ──────────────────────────────────────────────────────────────────
# 参考 docs/PRODUCT_TIERS_V2.md 第十节

SKUS = [
    {
        "sku_id": "basic_20",
        "sku_name": "日本旅行行程·模板版",
        "price_cny": 19.9,
        "sku_type": "template",
        "max_days": 7,
        "features": {
            "has_restaurant": False,
            "has_hotel_filter": False,
            "custom_input": False,
            "has_photo_guide": False,
            "has_flight_compare": False,
            "has_hotel_compare": False,
            "has_avoid_traps": False,
            "has_pre_trip_guide": False,
            "has_safety_guide": False,
            "sections": ["daily_timeline", "route_map", "spot_info", "area_hotel_tip", "basic_transport"],
            "workflow_config": {
                "mode": "template",
                "allow_custom_days": False,
                "fixed_days": 7,
            },
        },
    },
    {
        "sku_id": "flex_68",
        "sku_name": "日本旅行行程·弹性版",
        "price_cny": 68.0,
        "sku_type": "template",
        "max_days": 14,
        "features": {
            "has_restaurant": True,
            "has_hotel_filter": False,
            "custom_input": False,
            "has_photo_guide": False,
            "has_flight_compare": False,
            "has_hotel_compare": False,
            "has_avoid_traps": False,
            "has_pre_trip_guide": False,
            "has_safety_guide": False,
            "sections": [
                "daily_timeline", "route_map", "spot_info",
                "area_hotel_tip", "transport", "hotel_list_simple",
            ],
            "workflow_config": {
                "mode": "auto_generate",
                "allow_custom_days": True,
                "base_days": 7,
                "extra_day_price": 10,
            },
        },
    },
    {
        "sku_id": "standard_128",
        "sku_name": "日本旅行行程·标准个性化版",
        "price_cny": 128.0,
        "sku_type": "personalized",
        "max_days": 14,
        "features": {
            "has_restaurant": True,
            "has_hotel_filter": True,
            "custom_input": True,
            "has_photo_guide": False,
            "has_flight_compare": False,
            "has_hotel_compare": False,
            "has_avoid_traps": True,
            "has_pre_trip_guide": True,
            "has_safety_guide": True,
            "sections": [
                "daily_timeline", "route_map", "spot_info", "transport_detailed",
                "hotel_report", "restaurant_report",
                "pre_trip_guide", "safety_guide", "transport_pass_guide", "avoid_traps",
            ],
            "workflow_config": {
                "mode": "personalized",
                "allow_custom_days": True,
                "base_days": 9,
                "extra_day_price": 10,
                "modules": ["restaurant_report", "hotel_detailed", "pre_trip_guide", "safety_guide"],
            },
        },
    },
    {
        "sku_id": "deep_298",
        "sku_name": "日本旅行行程·深度定制版",
        "price_cny": 298.0,
        "sku_type": "personalized",
        "max_days": 21,
        "features": {
            "has_restaurant": True,
            "has_hotel_filter": True,
            "custom_input": True,
            "has_photo_guide": True,
            "has_flight_compare": False,
            "has_hotel_compare": False,
            "has_avoid_traps": True,
            "has_pre_trip_guide": True,
            "has_safety_guide": True,
            "sections": [
                "daily_timeline", "route_map", "spot_info", "transport_optimal",
                "hotel_report_detailed", "restaurant_report_detailed",
                "pre_trip_guide", "safety_guide", "transport_pass_guide", "avoid_traps_deep",
                "photo_spots", "instagrammable_guide",
            ],
            "workflow_config": {
                "mode": "deep_personalized",
                "allow_custom_days": True,
                "base_days": 9,
                "extra_day_price": 20,
                "modules": [
                    "restaurant_report", "hotel_detailed", "pre_trip_guide", "safety_guide",
                    "custom_route", "photo_guide", "instagrammable_guide", "avoid_traps_deep",
                ],
            },
        },
    },
    {
        "sku_id": "compare_888",
        "sku_name": "日本旅行·全套比价优化版",
        "price_cny": 888.0,
        "sku_type": "premium",
        "max_days": 21,
        "features": {
            "has_restaurant": True,
            "has_hotel_filter": True,
            "custom_input": True,
            "has_photo_guide": True,
            "has_flight_compare": True,
            "has_hotel_compare": True,
            "has_avoid_traps": True,
            "has_pre_trip_guide": True,
            "has_safety_guide": True,
            "sections": [
                "daily_timeline", "route_map", "spot_info", "transport_optimal",
                "hotel_report_detailed", "restaurant_report_detailed",
                "pre_trip_guide", "safety_guide", "transport_pass_guide", "avoid_traps_deep",
                "photo_spots", "instagrammable_guide",
                "flight_compare_report", "hotel_compare_report", "savings_summary",
            ],
            "workflow_config": {
                "mode": "premium",
                "allow_custom_days": True,
                "base_days": 10,
                "extra_day_price": 30,
                "modules": [
                    "all_298_modules", "flight_compare", "hotel_compare",
                    "combo_optimize", "savings_report", "pre_trip_qa",
                ],
            },
        },
    },
    {
        "sku_id": "honeymoon_1999",
        "sku_name": "日本旅行·蜜月全案定制版",
        "price_cny": 1999.0,
        "sku_type": "premium",
        "max_days": 30,
        "features": {
            "has_restaurant": True,
            "has_hotel_filter": True,
            "custom_input": True,
            "has_photo_guide": True,
            "has_flight_compare": True,
            "has_hotel_compare": True,
            "has_avoid_traps": True,
            "has_pre_trip_guide": True,
            "has_safety_guide": True,
            "sections": [
                "daily_timeline", "route_map", "spot_info", "transport_optimal",
                "hotel_report_detailed", "restaurant_report_detailed",
                "pre_trip_guide", "safety_guide", "transport_pass_guide", "avoid_traps_deep",
                "photo_spots", "instagrammable_guide",
                "flight_compare_report", "hotel_compare_report", "savings_summary",
                "version_comparison", "honeymoon_highlights", "luxury_dining",
            ],
            "workflow_config": {
                "mode": "full_custom",
                "allow_custom_days": True,
                "base_days": 14,
                "extra_day_price": 50,
                "modules": [
                    "all_888_modules", "multi_version", "honeymoon_scene",
                    "luxury_hotel_filter", "deep_pre_trip_qa",
                ],
            },
        },
    },
]


async def seed_skus(dry_run: bool = False) -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            inserted = 0
            updated = 0
            for sku_def in SKUS:
                existing = (await session.execute(
                    select(ProductSku).where(ProductSku.sku_id == sku_def["sku_id"])
                )).scalar_one_or_none()

                if existing:
                    # 更新价格和 features（幂等）
                    existing.sku_name = sku_def["sku_name"]
                    existing.price_cny = sku_def["price_cny"]
                    existing.sku_type = sku_def["sku_type"]
                    existing.features = sku_def["features"]
                    existing.max_days = sku_def["max_days"]
                    updated += 1
                    logger.info(f"  [更新] {sku_def['sku_id']}  ¥{sku_def['price_cny']}")
                else:
                    sku = ProductSku(
                        sku_id=sku_def["sku_id"],
                        sku_name=sku_def["sku_name"],
                        price_cny=sku_def["price_cny"],
                        sku_type=sku_def["sku_type"],
                        features=sku_def["features"],
                        max_days=sku_def["max_days"],
                        is_active=True,
                    )
                    session.add(sku)
                    inserted += 1
                    logger.info(f"  [写入] {sku_def['sku_id']}  ¥{sku_def['price_cny']}")

            if dry_run:
                await session.rollback()
                logger.info(f"[DRY-RUN] 将写入 {inserted} 条, 更新 {updated} 条（已回滚）")
            else:
                logger.info(f"[seed_product_skus] 完成: 写入 {inserted} 条, 更新 {updated} 条")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    asyncio.run(seed_skus(dry_run=dry_run))
