#!/usr/bin/env python3
"""
B6: soft_rule_seeds.json（12维默认权重）种子脚本
基于 soft-rule-dimensions/spec.md 的默认权重
用法: python scripts/seed_soft_rule_defaults.py [--dry-run]
功能: 创建软规则默认权重JSON文件，用于后续导入
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# ── 路径修复 ──────────────────────────────────────────────────────────────────
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.domains.scoring.soft_rule_dimensions import get_default_weights, SOFT_RULE_DIMENSIONS

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def create_soft_rule_seeds() -> Dict[str, Any]:
    """创建软规则种子数据"""
    
    # 获取默认权重
    default_weights = get_default_weights()
    
    # 构建完整的种子数据结构
    seeds = {
        "version": "1.0.0",
        "created_at": datetime.now().isoformat(),
        "description": "12维软规则默认权重种子数据",
        "dimensions": {},
        "default_weights": default_weights,
        "dimension_details": []
    }
    
    # 添加每个维度的详细信息
    for dim_id, dimension in SOFT_RULE_DIMENSIONS.items():
        seeds["dimension_details"].append({
            "id": dimension.id,
            "name_cn": dimension.name_cn,
            "user_feeling": dimension.user_feeling,
            "main_impact": dimension.main_impact,
            "effective_stages": [stage.value for stage in dimension.effective_stages],
            "recommended_source": dimension.recommended_source.value,
            "default_weight": dimension.default_weight,
            "score_range": list(dimension.score_range)
        })
        
        # 简化的维度信息（用于快速查找）
        seeds["dimensions"][dim_id] = {
            "name_cn": dimension.name_cn,
            "default_weight": dimension.default_weight
        }
    
    return seeds


def save_soft_rule_seeds(seeds: Dict[str, Any], output_path: Path) -> None:
    """保存软规则种子数据到JSON文件"""
    
    # 确保输出目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 保存JSON文件（格式化输出）
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(seeds, f, ensure_ascii=False, indent=2)
    
    logger.info(f"软规则种子数据已保存到: {output_path}")
    logger.info(f"文件大小: {output_path.stat().st_size} 字节")
    
    # 验证权重总和
    total_weight = sum(seeds["default_weights"].values())
    logger.info(f"默认权重总和: {total_weight:.4f} (应为 1.0000)")
    
    if abs(total_weight - 1.0) > 0.001:
        logger.warning(f"权重总和偏差较大: {total_weight:.4f}")


def create_sample_entity_scores() -> Dict[str, Any]:
    """创建示例实体评分数据（用于测试）"""
    
    import random
    
    # 示例实体ID（假设的）
    sample_entities = [
        {"entity_id": "tokyo_tower", "entity_type": "poi", "name": "东京塔"},
        {"entity_id": "sensoji_temple", "entity_type": "poi", "name": "浅草寺"},
        {"entity_id": "tsukiji_market", "entity_type": "poi", "name": "筑地市场"},
        {"entity_id": "sukiyabashi_jiro", "entity_type": "restaurant", "name": "数寄屋桥次郎"},
        {"entity_id": "park_hyatt_tokyo", "entity_type": "hotel", "name": "东京柏悦酒店"}
    ]
    
    sample_scores = {
        "version": "1.0.0",
        "created_at": datetime.now().isoformat(),
        "description": "示例实体软规则评分数据（随机生成，仅用于测试）",
        "sample_entities": []
    }
    
    for entity in sample_entities:
        entity_scores = {
            "entity_id": entity["entity_id"],
            "entity_type": entity["entity_type"],
            "name": entity["name"],
            "scores": {},
            "calculated_at": datetime.now().isoformat()
        }
        
        # 为每个维度生成随机分数（0-10）
        for dim_id in SOFT_RULE_DIMENSIONS.keys():
            # 根据实体类型调整分数范围
            base_score = random.uniform(5.0, 9.0)
            
            # 酒店在 relaxation_feel 和 recovery_friendliness 上得分更高
            if entity["entity_type"] == "hotel":
                if dim_id in ["relaxation_feel", "recovery_friendliness"]:
                    base_score = random.uniform(7.0, 10.0)
                elif dim_id == "shareability":
                    base_score = random.uniform(6.0, 9.0)
            
            # 餐厅在 food_certainty 上得分更高
            elif entity["entity_type"] == "restaurant":
                if dim_id == "food_certainty":
                    base_score = random.uniform(7.0, 10.0)
                elif dim_id == "localness":
                    base_score = random.uniform(6.0, 9.5)
            
            # 景点在 emotional_value 和 shareability 上得分更高
            elif entity["entity_type"] == "poi":
                if dim_id in ["emotional_value", "shareability", "memory_point"]:
                    base_score = random.uniform(7.0, 10.0)
            
            entity_scores["scores"][dim_id] = round(base_score, 1)
        
        sample_scores["sample_entities"].append(entity_scores)
    
    return sample_scores


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="创建软规则种子数据")
    parser.add_argument("--output-dir", type=str, default="data/seed", 
                       help="输出目录路径")
    parser.add_argument("--create-samples", action="store_true",
                       help="同时创建示例实体评分数据")
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    
    try:
        # 1. 创建默认权重种子数据
        logger.info("创建软规则默认权重种子数据...")
        seeds = create_soft_rule_seeds()
        
        output_path = output_dir / "soft_rule_seeds.json"
        save_soft_rule_seeds(seeds, output_path)
        
        # 2. 可选：创建示例实体评分数据
        if args.create_samples:
            logger.info("创建示例实体评分数据...")
            sample_scores = create_sample_entity_scores()
            
            sample_path = output_dir / "soft_rule_sample_scores.json"
            with open(sample_path, 'w', encoding='utf-8') as f:
                json.dump(sample_scores, f, ensure_ascii=False, indent=2)
            
            logger.info(f"示例数据已保存到: {sample_path}")
        
        # 3. 打印摘要信息
        print("\n" + "="*60)
        print("软规则种子数据创建完成")
        print("="*60)
        
        print(f"\n维度数量: {len(seeds['dimension_details'])}")
        print(f"默认权重文件: {output_path}")
        
        # 打印权重摘要
        print("\n默认权重摘要:")
        for dim_detail in seeds["dimension_details"]:
            print(f"  {dim_detail['id']:30} {dim_detail['default_weight']:.3f} - {dim_detail['name_cn']}")
        
        total_weight = sum(seeds["default_weights"].values())
        print(f"\n权重总和: {total_weight:.4f}")
        
        if args.create_samples:
            print(f"\n示例数据文件: {sample_path}")
            print(f"示例实体数量: {len(sample_scores['sample_entities'])}")
        
        print("\n下一步:")
        print("1. 使用此种子数据初始化数据库")
        print("2. 运行权重包种子脚本 (B7-B8)")
        print("3. 测试软规则计算功能")
        
    except Exception as e:
        logger.error(f"创建种子数据失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()