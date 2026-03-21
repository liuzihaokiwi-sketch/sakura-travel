#!/usr/bin/env python3
"""
B8: 4个阶段权重包 seed → stage_weight_packs
基于 openspec/changes/soft-rule-system/specs/stage-weight-packs/spec.md
用法: python scripts/seed_stage_weight_packs.py [--dry-run]
功能: 幂等写入 4 个阶段权重包到 stage_weight_packs 表
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
from app.db.models.soft_rules import StageWeightPack
from app.domains.scoring.soft_rule_dimensions import SOFT_RULE_DIMENSIONS, get_default_weights

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# ── 阶段权重包定义 ──────────────────────────────────────────────────────────────
# 基于 stage-weight-packs/spec.md 的 v1 种子值
STAGE_WEIGHT_PACKS = [
    {
        "pack_id": "preview_day1",
        "name_cn": "免费 Day 1 预览",
        "description": "触发'想买'——最大化转付费率",
        "weights": {
            "emotional_value": 0.13,
            "shareability": 0.13,
            "relaxation_feel": 0.05,
            "memory_point": 0.12,
            "localness": 0.08,
            "smoothness": 0.07,
            "food_certainty": 0.09,
            "night_completion": 0.04,
            "recovery_friendliness": 0.02,
            "weather_resilience_soft": 0.01,
            "professional_judgement_feel": 0.11,
            "preview_conversion_power": 0.15
        }
    },
    {
        "pack_id": "standard",
        "name_cn": "标准版完整行程",
        "description": "综合体验——平衡所有维度",
        "weights": get_default_weights()  # 使用12维度的默认权重
    },
    {
        "pack_id": "premium",
        "name_cn": "高客单定制版",
        "description": "极致体验——个性化 + 专业感",
        "weights": {
            "emotional_value": 0.11,
            "shareability": 0.09,
            "relaxation_feel": 0.08,
            "memory_point": 0.12,
            "localness": 0.13,
            "smoothness": 0.07,
            "food_certainty": 0.10,
            "night_completion": 0.06,
            "recovery_friendliness": 0.04,
            "weather_resilience_soft": 0.03,
            "professional_judgement_feel": 0.14,
            "preview_conversion_power": 0.03
        }
    },
    {
        "pack_id": "self_serve_tuning",
        "name_cn": "自助微调",
        "description": "稳定体验——替换不崩、局部优化",
        "weights": {
            "emotional_value": 0.09,
            "shareability": 0.06,
            "relaxation_feel": 0.12,
            "memory_point": 0.07,
            "localness": 0.07,
            "smoothness": 0.16,
            "food_certainty": 0.13,
            "night_completion": 0.05,
            "recovery_friendliness": 0.10,
            "weather_resilience_soft": 0.08,
            "professional_judgement_feel": 0.04,
            "preview_conversion_power": 0.03
        }
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


def analyze_stage_differences() -> Dict[str, Dict[str, float]]:
    """分析阶段权重差异"""
    differences = {}
    
    # 获取标准权重作为基准
    standard_weights = get_default_weights()
    
    for pack in STAGE_WEIGHT_PACKS:
        pack_id = pack["pack_id"]
        if pack_id == "standard":
            continue
            
        weights = pack["weights"]
        diff = {}
        
        for dim_id in weights.keys():
            standard_weight = standard_weights.get(dim_id, 0)
            stage_weight = weights[dim_id]
            diff[dim_id] = stage_weight - standard_weight
        
        # 找出差异最大的维度
        sorted_diff = sorted(diff.items(), key=lambda x: abs(x[1]), reverse=True)
        top_diffs = {k: v for k, v in sorted_diff[:3]}
        
        differences[pack_id] = {
            "top_increases": {k: v for k, v in top_diffs.items() if v > 0},
            "top_decreases": {k: v for k, v in top_diffs.items() if v < 0},
            "total_diff": sum(abs(v) for v in diff.values())
        }
    
    return differences


async def seed_stage_weight_packs(dry_run: bool = False) -> None:
    """写入阶段权重包种子数据"""
    logger.info("开始写入阶段权重包种子数据...")
    
    # 验证所有权重包
    all_errors = []
    for pack in STAGE_WEIGHT_PACKS:
        errors = validate_weight_pack(pack)
        if errors:
            all_errors.append(f"{pack['pack_id']}: {errors}")
    
    if all_errors:
        logger.error("权重包验证失败:")
        for error in all_errors:
            logger.error(f"  {error}")
        raise ValueError("权重包数据验证失败")
    
    # 分析阶段差异
    differences = analyze_stage_differences()
    
    async with AsyncSessionLocal() as session:
        for pack_data in STAGE_WEIGHT_PACKS:
            pack_id = pack_data["pack_id"]
            
            # 检查是否已存在
            stmt = select(StageWeightPack).where(StageWeightPack.pack_id == pack_id)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                # 更新现有权重包
                logger.info(f"更新现有权重包: {pack_id}")
                if not dry_run:
                    existing.name_cn = pack_data["name_cn"]
                    existing.description = pack_data.get("description")
                    existing.weights = pack_data["weights"]
                    existing.version += 1
                    existing.updated_at = datetime.now()
            else:
                # 创建新权重包
                logger.info(f"创建新权重包: {pack_id}")
                if not dry_run:
                    weight_pack = StageWeightPack(
                        pack_id=pack_id,
                        name_cn=pack_data["name_cn"],
                        description=pack_data.get("description"),
                        weights=pack_data["weights"],
                        version=1
                    )
                    session.add(weight_pack)
        
        if not dry_run:
            await session.commit()
            logger.info("阶段权重包种子数据写入完成")
        else:
            logger.info("Dry run 模式，未实际写入数据库")
    
    # 打印摘要信息
    print("\n" + "="*60)
    print("阶段权重包种子数据摘要")
    print("="*60)
    
    for pack in STAGE_WEIGHT_PACKS:
        total_weight = sum(pack["weights"].values())
        print(f"\n{pack['pack_id']}: {pack['name_cn']}")
        print(f"  描述: {pack.get('description', 'N/A')}")
        print(f"  权重总和: {total_weight:.4f}")
        
        if pack["pack_id"] in differences:
            diff_info = differences[pack["pack_id"]]
            if diff_info["top_increases"]:
                increases = ", ".join([f"{k}(+{v:.2f})" for k, v in diff_info["top_increases"].items()])
                print(f"  相比标准版增加: {increases}")
            if diff_info["top_decreases"]:
                decreases = ", ".join([f"{k}({v:.2f})" for k, v in diff_info["top_decreases"].items()])
                print(f"  相比标准版减少: {decreases}")
    
    # 打印设计原则验证
    print("\n" + "="*60)
    print("设计原则验证")
    print("="*60)
    
    preview_weights = next(p["weights"] for p in STAGE_WEIGHT_PACKS if p["pack_id"] == "preview_day1")
    standard_weights = next(p["weights"] for p in STAGE_WEIGHT_PACKS if p["pack_id"] == "standard")
    
    # 验证预览阶段 vs 标准阶段
    print("\n1. 预览阶段 vs 标准阶段:")
    preview_higher = preview_weights["preview_conversion_power"] > standard_weights["preview_conversion_power"]
    print(f"   preview_conversion_power 更高: {'✅' if preview_higher else '❌'}")
    print(f"     预览: {preview_weights['preview_conversion_power']:.2f}, 标准: {standard_weights['preview_conversion_power']:.2f}")
    
    standard_higher = standard_weights["relaxation_feel"] > preview_weights["relaxation_feel"]
    print(f"   relaxation_feel 标准更高: {'✅' if standard_higher else '❌'}")
    print(f"     预览: {preview_weights['relaxation_feel']:.2f}, 标准: {standard_weights['relaxation_feel']:.2f}")
    
    # 验证自助微调阶段
    tuning_weights = next(p["weights"] for p in STAGE_WEIGHT_PACKS if p["pack_id"] == "self_serve_tuning")
    print("\n2. 自助微调阶段保护原则:")
    smoothness_high = tuning_weights["smoothness"] >= 0.15
    print(f"   smoothness 权重高(≥0.15): {'✅' if smoothness_high else '❌'} ({tuning_weights['smoothness']:.2f})")
    
    food_certainty_high = tuning_weights["food_certainty"] >= 0.13
    print(f"   food_certainty 权重高(≥0.13): {'✅' if food_certainty_high else '❌'} ({tuning_weights['food_certainty']:.2f})")
    
    protection_score = tuning_weights["smoothness"] + tuning_weights["food_certainty"]
    print(f"   保护性权重合计: {protection_score:.2f} (smoothness + food_certainty)")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="写入阶段权重包种子数据")
    parser.add_argument("--dry-run", action="store_true", help="试运行，不实际写入数据库")
    args = parser.parse_args()
    
    asyncio.run(seed_stage_weight_packs(dry_run=args.dry_run))


if __name__ == "__main__":
    main()