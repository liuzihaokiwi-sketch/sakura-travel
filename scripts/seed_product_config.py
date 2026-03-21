#!/usr/bin/env python3
"""
B1: product_config 3个SKU seed 脚本
基于 system-closure-v1/design.md 的 D1 部分
用法: python scripts/seed_product_config.py [--dry-run]
功能: 幂等写入 3 个 SKU 配置到 product_config 表
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# ── 路径修复 ──────────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.db.models.soft_rules import ProductConfig

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# ── 产品配置定义 ──────────────────────────────────────────────────────────────
# 基于 design.md 的 D1 部分配置模型
PRODUCT_CONFIGS = [
    {
        "config_key": "sku_standard_248",
        "config_value": {
            "sku_id": "standard_248",
            "display_name": "标准版",
            "price_cny": 248,
            "preview": {
                "days_shown": 1,
                "modules_shown": [
                    "day_overview",
                    "top3_pois",
                    "lunch_pick",
                    "transport_summary"
                ],
                "modules_locked": [
                    "hotel_detail",
                    "dinner_picks",
                    "insider_tips",
                    "full_schedule"
                ],
                "show_total_days": True,
                "show_locked_count": True
            },
            "entitlements": {
                "full_days": True,
                "self_serve_swaps_unlimited": True,
                "formal_revision_count": 2,
                "formal_revision_includes": [
                    "restructure_day",
                    "change_city_order",
                    "add_custom_requirement"
                ],
                "hotel_recommendation": "area_only",
                "restaurant_detail": True,
                "transport_detail": True,
                "pdf_export": True,
                "share_link": True,
                "wechat_consult_unlimited": True,
                "travel_day_support": False
            },
            "copywriting": {
                "tagline": "完整行程 + 随时问我",
                "value_props": [
                    "5-7天完整规划",
                    "餐厅精选+避坑",
                    "2次深度修改",
                    "无限微信咨询"
                ],
                "cta_text": "立即获取完整方案"
            }
        },
        "version": 1,
        "is_active": True
    },
    {
        "config_key": "sku_premium_888",
        "config_value": {
            "sku_id": "premium_888",
            "display_name": "尊享定制版",
            "price_cny": 888,
            "preview": {
                "days_shown": 2,
                "modules_shown": [
                    "day_overview",
                    "top3_pois",
                    "lunch_pick",
                    "dinner_pick",
                    "transport_summary",
                    "insider_tips"
                ],
                "modules_locked": [
                    "hotel_detail",
                    "full_schedule",
                    "custom_requirements"
                ],
                "show_total_days": True,
                "show_locked_count": True
            },
            "entitlements": {
                "full_days": True,
                "self_serve_swaps_unlimited": True,
                "formal_revision_count": -1,  # 不限次
                "formal_revision_includes": [
                    "restructure_day",
                    "change_city_order",
                    "add_custom_requirement",
                    "custom_theme_focus",
                    "priority_support"
                ],
                "hotel_recommendation": "specific_hotels",
                "restaurant_detail": True,
                "transport_detail": True,
                "pdf_export": True,
                "share_link": True,
                "wechat_consult_unlimited": True,
                "travel_day_support": True,
                "priority_queue": True,
                "custom_theme": True
            },
            "copywriting": {
                "tagline": "极致个性化 + 专家全程陪",
                "value_props": [
                    "深度定制行程",
                    "专家1对1咨询",
                    "无限次修改",
                    "旅行当日支持",
                    "优先排队"
                ],
                "cta_text": "开启专属定制"
            }
        },
        "version": 1,
        "is_active": True
    },
    {
        "config_key": "sku_free_preview",
        "config_value": {
            "sku_id": "free_preview",
            "display_name": "免费预览版",
            "price_cny": 0,
            "preview": {
                "days_shown": 1,
                "modules_shown": [
                    "day_overview",
                    "top2_pois",
                    "lunch_pick"
                ],
                "modules_locked": [
                    "dinner_pick",
                    "transport_summary",
                    "hotel_detail",
                    "insider_tips",
                    "full_schedule"
                ],
                "show_total_days": False,
                "show_locked_count": True
            },
            "entitlements": {
                "full_days": False,
                "self_serve_swaps_unlimited": False,
                "formal_revision_count": 0,
                "formal_revision_includes": [],
                "hotel_recommendation": "none",
                "restaurant_detail": False,
                "transport_detail": False,
                "pdf_export": False,
                "share_link": False,
                "wechat_consult_unlimited": False,
                "travel_day_support": False
            },
            "copywriting": {
                "tagline": "先体验再决定",
                "value_props": [
                    "免费查看第一天",
                    "体验AI规划质量",
                    "无风险尝试"
                ],
                "cta_text": "免费体验"
            }
        },
        "version": 1,
        "is_active": True
    }
]


async def seed_product_config(dry_run: bool = False) -> None:
    """写入产品配置种子数据"""
    logger.info("开始写入 product_config 种子数据...")
    
    async with AsyncSessionLocal() as session:
        for config_data in PRODUCT_CONFIGS:
            config_key = config_data["config_key"]
            
            # 检查是否已存在
            stmt = select(ProductConfig).where(ProductConfig.config_key == config_key)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                # 更新现有配置
                logger.info(f"更新现有配置: {config_key}")
                if not dry_run:
                    existing.config_value = config_data["config_value"]
                    existing.version = config_data["version"]
                    existing.is_active = config_data["is_active"]
                    existing.updated_at = datetime.now()
            else:
                # 创建新配置
                logger.info(f"创建新配置: {config_key}")
                if not dry_run:
                    product_config = ProductConfig(
                        config_key=config_key,
                        config_value=config_data["config_value"],
                        version=config_data["version"],
                        is_active=config_data["is_active"]
                    )
                    session.add(product_config)
        
        if not dry_run:
            await session.commit()
            logger.info("product_config 种子数据写入完成")
        else:
            logger.info("Dry run 模式，未实际写入数据库")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="写入 product_config 种子数据")
    parser.add_argument("--dry-run", action="store_true", help="试运行，不实际写入数据库")
    args = parser.parse_args()
    
    asyncio.run(seed_product_config(dry_run=args.dry_run))


if __name__ == "__main__":
    main()