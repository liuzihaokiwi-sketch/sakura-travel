#!/usr/bin/env python3
"""
B7: 7个客群权重包 seed → segment_weight_packs
基于 openspec/changes/soft-rule-system/specs/segment-weight-packs/spec.md
用法: python scripts/seed_segment_weight_packs.py [--dry-run]
功能: 幂等写入 7 个客群权重包到 segment_weight_packs 表
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# ── 路径修复 ──────────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.db.models.soft_rules import SegmentWeightPack
from app.domains.scoring.soft_rule_dimensions import SOFT_RULE_DIMENSIONS

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# ── 客群权重包定义 ──────────────────────────────────────────────────────────────
# 基于 segment-weight-packs/spec.md 的 v1 种子值
SEGMENT_WEIGHT_PACKS = [
    {
        "pack_id": "couple",
        "name_cn": "情侣",
        "description": "浪漫氛围、出片、记忆点",
        "weights": {
            "emotional_value": 0.16,
            "shareability": 0.14,
            "relaxation_feel": 0.10,
            "memory_point": 0.13,
            "localness": 0.09,
            "smoothness": 0.06,
            "food_certainty": 0.08,
            "night_completion": 0.08,
            "recovery_friendliness": 0.04,
            "weather_resilience_soft": 0.03,
            "professional_judgement_feel": 0.07,
            "preview_conversion_power": 0.02
        },
        "top_dimensions": [
            "emotional_value", "shareability", "memory_point", "relaxation_feel",
            "night_completion", "food_certainty"
        ],
        "low_dimensions": [
            "recovery_friendliness", "weather_resilience_soft", "preview_conversion_power"
        ],
        "day1_trigger": "有明确的约会感氛围场景 + 出片点",
        "repurchase_trigger": "记忆点够独特、不是'谁都能找到的攻略'",
        "tuning_sensitivity": ["hotel", "restaurant", "night_activity"]
    },
    {
        "pack_id": "besties",
        "name_cn": "闺蜜好友",
        "description": "分享感、出片、轻松",
        "weights": {
            "emotional_value": 0.13,
            "shareability": 0.16,
            "relaxation_feel": 0.12,
            "memory_point": 0.10,
            "localness": 0.08,
            "smoothness": 0.07,
            "food_certainty": 0.09,
            "night_completion": 0.09,
            "recovery_friendliness": 0.05,
            "weather_resilience_soft": 0.04,
            "professional_judgement_feel": 0.04,
            "preview_conversion_power": 0.03
        },
        "top_dimensions": [
            "shareability", "emotional_value", "relaxation_feel", "memory_point",
            "food_certainty", "night_completion"
        ],
        "low_dimensions": [
            "recovery_friendliness", "weather_resilience_soft", "professional_judgement_feel"
        ],
        "day1_trigger": "高出片回报 + 闺蜜合照场景",
        "repurchase_trigger": "内容值得在朋友圈晒",
        "tuning_sensitivity": ["photo_spots", "restaurant", "shopping"]
    },
    {
        "pack_id": "parents",
        "name_cn": "带父母",
        "description": "舒适、少折腾、餐饮确定",
        "weights": {
            "emotional_value": 0.08,
            "shareability": 0.05,
            "relaxation_feel": 0.12,
            "memory_point": 0.05,
            "localness": 0.06,
            "smoothness": 0.15,
            "food_certainty": 0.13,
            "night_completion": 0.04,
            "recovery_friendliness": 0.13,
            "weather_resilience_soft": 0.08,
            "professional_judgement_feel": 0.09,
            "preview_conversion_power": 0.02
        },
        "top_dimensions": [
            "smoothness", "recovery_friendliness", "food_certainty", "relaxation_feel",
            "professional_judgement_feel", "weather_resilience_soft"
        ],
        "low_dimensions": [
            "shareability", "memory_point", "night_completion", "preview_conversion_power"
        ],
        "day1_trigger": "行程节奏松弛 + 餐厅确定 + 交通方便",
        "repurchase_trigger": "父母体验好没有不开心",
        "tuning_sensitivity": ["transport", "restaurant", "walking_distance"]
    },
    {
        "pack_id": "family_child",
        "name_cn": "带孩子",
        "description": "安全、恢复友好、餐饮",
        "weights": {
            "emotional_value": 0.08,
            "shareability": 0.06,
            "relaxation_feel": 0.10,
            "memory_point": 0.07,
            "localness": 0.05,
            "smoothness": 0.14,
            "food_certainty": 0.12,
            "night_completion": 0.04,
            "recovery_friendliness": 0.14,
            "weather_resilience_soft": 0.10,
            "professional_judgement_feel": 0.07,
            "preview_conversion_power": 0.03
        },
        "top_dimensions": [
            "smoothness", "recovery_friendliness", "food_certainty", "weather_resilience_soft",
            "relaxation_feel", "professional_judgement_feel"
        ],
        "low_dimensions": [
            "shareability", "localness", "night_completion", "memory_point"
        ],
        "day1_trigger": "明确的亲子友好内容 + 雨天备案",
        "repurchase_trigger": "全家体验顺畅无负担",
        "tuning_sensitivity": ["child_friendly", "restaurant", "indoor_activities"]
    },
    {
        "pack_id": "first_time_fit",
        "name_cn": "首次赴日双人自由行",
        "description": "确定感、顺滑、专业感",
        "weights": {
            "emotional_value": 0.09,
            "shareability": 0.08,
            "relaxation_feel": 0.09,
            "memory_point": 0.08,
            "localness": 0.06,
            "smoothness": 0.14,
            "food_certainty": 0.11,
            "night_completion": 0.05,
            "recovery_friendliness": 0.04,
            "weather_resilience_soft": 0.03,
            "professional_judgement_feel": 0.13,
            "preview_conversion_power": 0.10
        },
        "top_dimensions": [
            "smoothness", "professional_judgement_feel", "food_certainty", "preview_conversion_power",
            "emotional_value", "relaxation_feel"
        ],
        "low_dimensions": [
            "recovery_friendliness", "weather_resilience_soft", "night_completion", "localness"
        ],
        "day1_trigger": "确定感 + '按这个走不会出错'",
        "repurchase_trigger": "第一次就很顺、建立信任",
        "tuning_sensitivity": ["transport", "landmarks", "must_visit"]
    },
    {
        "pack_id": "friends_small_group",
        "name_cn": "朋友结伴",
        "description": "丰富体验、高效、夜间",
        "weights": {
            "emotional_value": 0.11,
            "shareability": 0.11,
            "relaxation_feel": 0.08,
            "memory_point": 0.13,
            "localness": 0.09,
            "smoothness": 0.08,
            "food_certainty": 0.09,
            "night_completion": 0.12,
            "recovery_friendliness": 0.06,
            "weather_resilience_soft": 0.05,
            "professional_judgement_feel": 0.05,
            "preview_conversion_power": 0.03
        },
        "top_dimensions": [
            "memory_point", "night_completion", "emotional_value", "shareability",
            "food_certainty", "localness"
        ],
        "low_dimensions": [
            "recovery_friendliness", "weather_resilience_soft", "professional_judgement_feel",
            "preview_conversion_power"
        ],
        "day1_trigger": "有明确的'高光时刻' + 夜间活动",
        "repurchase_trigger": "朋友们都觉得好玩",
        "tuning_sensitivity": ["night_life", "group_activities", "unique_experiences"]
    },
    {
        "pack_id": "repeat_fit",
        "name_cn": "二刷日本",
        "description": "当地感、记忆点、新鲜",
        "weights": {
            "emotional_value": 0.12,
            "shareability": 0.08,
            "relaxation_feel": 0.09,
            "memory_point": 0.14,
            "localness": 0.16,
            "smoothness": 0.06,
            "food_certainty": 0.10,
            "night_completion": 0.07,
            "recovery_friendliness": 0.04,
            "weather_resilience_soft": 0.03,
            "professional_judgement_feel": 0.08,
            "preview_conversion_power": 0.03
        },
        "top_dimensions": [
            "localness", "memory_point", "emotional_value", "food_certainty",
            "professional_judgement_feel", "shareability"
        ],
        "low_dimensions": [
            "smoothness", "recovery_friendliness", "weather_resilience_soft",
            "preview_conversion_power"
        ],
        "day1_trigger": "'这些地方我自己找不到' 的惊喜感",
        "repurchase_trigger": "确实推荐了非主流好去处",
        "tuning_sensitivity": ["local_experiences", "hidden_gems", "seasonal_special"]
    }
]


def validate_weight_pack(pack: Dict[str, Any]) -> List[str]:
    """验证权重包数据"""
    errors = []
    
    # 检查必要字段
    required_fields = ["pack_id", "name_cn", "weights"]
    for field in required_fields:
        if field not in pack:
            errors.append(f"缺少必要字段: {field}")
    
    if "weights" in pack:
        weights = pack["weights"]
        
        # 检查权重数量
        if len(weights) != len(SOFT_RULE_DIMENSIONS):
            errors.append(f"权重数量不正确: 应有 {len(SOFT_RULE_DIMENSIONS)} 个，实际 {len(weights)} 个")
        
        # 检查权重键名
        for dim_id in weights.keys():
            if dim_id not in SOFT_RULE_DIMENSIONS:
                errors.append(f"未知维度: {dim_id}")
        
        # 检查权重总和
        total_weight = sum(weights.values())
        if abs(total_weight - 1.0) > 0.01:
            errors.append(f"权重总和不为1: {total_weight:.4f}")
    
    return errors


async def seed_segment_weight_packs(dry_run: bool = False) -> None:
    """写入客群权重包种子数据"""
    logger.info("开始写入客群权重包种子数据...")
    
    # 验证所有权重包
    all_errors = []
    for pack in SEGMENT_WEIGHT_PACKS:
        errors = validate_weight_pack(pack)
        if errors:
            all_errors.append(f"{pack['pack_id']}: {errors}")
    
    if all_errors:
        logger.error("权重包验证失败:")
        for error in all_errors:
            logger.error(f"  {error}")
        raise ValueError("权重包数据验证失败")
    
    async with AsyncSessionLocal() as session:
        for pack_data in SEGMENT_WEIGHT_PACKS:
            pack_id = pack_data["pack_id"]
            
            # 检查是否已存在
            stmt = select(SegmentWeightPack).where(SegmentWeightPack.pack_id == pack_id)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                # 更新现有权重包
                logger.info(f"更新现有权重包: {pack_id}")
                if not dry_run:
                    existing.name_cn = pack_data["name_cn"]
                    existing.description = pack_data.get("description")
                    existing.weights = pack_data["weights"]
                    existing.top_dimensions = pack_data.get("top_dimensions")
                    existing.low_dimensions = pack_data.get("low_dimensions")
                    existing.day1_trigger = pack_data.get("day1_trigger")
                    existing.repurchase_trigger = pack_data.get("repurchase_trigger")
                    existing.tuning_sensitivity = pack_data.get("tuning_sensitivity")
                    existing.version += 1
                    existing.updated_at = datetime.now()
            else:
                # 创建新权重包
                logger.info(f"创建新权重包: {pack_id}")
                if not dry_run:
                    weight_pack = SegmentWeightPack(
                        pack_id=pack_id,
                        name_cn=pack_data["name_cn"],
                        description=pack_data.get("description"),
                        weights=pack_data["weights"],
                        top_dimensions=pack_data.get("top_dimensions"),
                        low_dimensions=pack_data.get("low_dimensions"),
                        day1_trigger=pack_data.get("day1_trigger"),
                        repurchase_trigger=pack_data.get("repurchase_trigger"),
                        tuning_sensitivity=pack_data.get("tuning_sensitivity"),
                        version=1
                    )
                    session.add(weight_pack)
        
        if not dry_run:
            await session.commit()
            logger.info("客群权重包种子数据写入完成")
        else:
            logger.info("Dry run 模式，未实际写入数据库")
    
    # 打印摘要信息
    print("\n" + "="*60)
    print("客群权重包种子数据摘要")
    print("="*60)
    
    for pack in SEGMENT_WEIGHT_PACKS:
        total_weight = sum(pack["weights"].values())
        print(f"\n{pack['pack_id']}: {pack['name_cn']}")
        print(f"  权重总和: {total_weight:.4f}")
        print(f"  高权重维度: {', '.join(pack.get('top_dimensions', [])[:3])}")
        print(f"  Day1触发点: {pack.get('day1_trigger', 'N/A')[:50]}...")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="写入客群权重包种子数据")
    parser.add_argument("--dry-run", action="store_true", help="试运行，不实际写入数据库")
    args = parser.parse_args()
    
    asyncio.run(seed_segment_weight_packs(dry_run=args.dry_run))


if __name__ == "__main__":
    main()