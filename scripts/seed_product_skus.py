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
# 参考 docs/STATUS.md 新定价模型（2026.03 更新）
#
# 新定价公式:
#   base = ¥198（含 3 天）
#   + ¥20 × max(0, total_days - 3)       按天加价
#   + ¥29 × max(0, volumes - 1)          拆册费（多册）
#
# 三档 SKU: 免费预览 / ¥198 标准版（主推） / ¥888 尊享定制

# ── 价格计算常量 ──────────────────────────────────────────────────────────────
BASE_PRICE_CNY = 198          # 基础价（含 3 天）
BASE_DAYS_INCLUDED = 3        # 基础价包含天数
EXTRA_DAY_PRICE = 20          # 每多 1 天加价
SPLIT_BOOK_PRICE = 29         # 拆册费（每多 1 册）


def calculate_price(total_days: int, volumes: int = 1) -> float:
    """
    计算标准版实际价格。

    Parameters
    ----------
    total_days : int  行程总天数（>= 1）
    volumes    : int  手账本册数（>= 1，默认 1）

    Returns
    -------
    float  总价（元）
    """
    extra_days = max(0, total_days - BASE_DAYS_INCLUDED)
    extra_volumes = max(0, volumes - 1)
    return BASE_PRICE_CNY + EXTRA_DAY_PRICE * extra_days + SPLIT_BOOK_PRICE * extra_volumes


SKUS = [
    # ── 免费预览版 ────────────────────────────────────────────
    {
        "sku_id": "free_preview",
        "sku_name": "日本旅行·免费预览",
        "price_cny": 0,
        "sku_type": "preview",
        "max_days": 30,
        "features": {
            "preview_days": 1,
            "refine_count": 0,
            "sections": [
                "daily_timeline", "route_map", "spot_info",
                "area_hotel_tip", "basic_transport",
            ],
            "workflow_config": {
                "mode": "preview",
                "preview_only": True,
            },
            "display": {
                "name": "一日体验版",
                "tagline": "先看看适不适合你",
                "badge": None,
            },
        },
    },
    # ── ¥198 标准版（主推，含 3 天，每多 1 天 +¥20）─────────
    {
        "sku_id": "standard_198",
        "sku_name": "日本旅行·完整攻略",
        "price_cny": BASE_PRICE_CNY,
        "sku_type": "standard",
        "max_days": 21,
        "features": {
            "refine_count": 2,
            "pages_estimate": "30-40",
            "sections": [
                "daily_timeline", "route_map", "spot_info",
                "transport_detailed", "transport_pass_guide",
                "hotel_report", "restaurant_report",
                "pre_trip_guide", "safety_guide", "avoid_traps",
                "photo_spots", "plan_b",
                "design_rationale", "booking_priority", "budget_summary",
            ],
            "workflow_config": {
                "mode": "personalized",
                "allow_custom_days": True,
                "base_days": BASE_DAYS_INCLUDED,
                "extra_day_price": EXTRA_DAY_PRICE,
                "split_book_price": SPLIT_BOOK_PRICE,
            },
            "pricing": {
                "base_price_cny": BASE_PRICE_CNY,
                "base_days_included": BASE_DAYS_INCLUDED,
                "extra_day_price": EXTRA_DAY_PRICE,
                "split_book_price": SPLIT_BOOK_PRICE,
                "formula": "¥198 + ¥20×(天数-3) + ¥29×(册数-1)",
                "examples": {
                    "3天1册": "¥198",
                    "5天1册": "¥238",
                    "7天1册": "¥278",
                    "7天2册": "¥307",
                    "10天2册": "¥367",
                },
            },
            "display": {
                "name": "完整攻略",
                "tagline": "完整行程 · 每一天都安排好",
                "badge": "🔥 90%用户选择",
                "is_featured": True,
            },
        },
    },
    # ── ¥888 尊享定制版（锚点） ───────────────────────────────
    {
        "sku_id": "premium_888",
        "sku_name": "日本旅行·尊享定制",
        "price_cny": 888.0,
        "sku_type": "premium",
        "max_days": 30,
        "features": {
            "refine_count": -1,  # 不限次
            "pages_estimate": "40-50",
            "has_1v1_consult": True,
            "has_realtime_support": True,
            "sections": [
                "daily_timeline", "route_map", "spot_info",
                "transport_optimal", "transport_pass_guide",
                "hotel_report_detailed", "restaurant_report_detailed",
                "pre_trip_guide", "safety_guide", "avoid_traps_deep",
                "photo_spots", "instagrammable_guide", "plan_b",
                "design_rationale", "booking_priority", "budget_summary",
                "honeymoon_highlights", "luxury_dining",
            ],
            "workflow_config": {
                "mode": "premium",
                "allow_custom_days": True,
                "base_days": BASE_DAYS_INCLUDED,
                "extra_day_price": EXTRA_DAY_PRICE,
                "split_book_price": SPLIT_BOOK_PRICE,
            },
            "display": {
                "name": "尊享定制版",
                "tagline": "有人帮你全程把关",
                "badge": None,
                "is_featured": False,
            },
        },
    },
]

# ── 旧 SKU（下线但保留）──────────────────────────────────────────────────────
LEGACY_SKUS_TO_DEACTIVATE = [
    "basic_20", "flex_68", "standard_128", "deep_298",
    "compare_888", "honeymoon_1999",
    "standard_248",  # 旧 ¥248 首发特惠版
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
