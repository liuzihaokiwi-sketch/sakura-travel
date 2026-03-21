#!/usr/bin/env python3
"""
B5: 12维软规则 dimensions.py 定义 + 校验函数
基于 openspec/changes/soft-rule-system/specs/soft-rule-dimensions/spec.md
"""

from __future__ import annotations

from typing import Dict, List, TypedDict, Optional
from enum import Enum
from dataclasses import dataclass


class DimensionSource(str, Enum):
    """维度评分来源"""
    AI_ESTIMATE = "ai"
    STATISTICAL = "stat"
    MANUAL_SEED = "manual"


class EffectiveStage(str, Enum):
    """生效阶段"""
    CANDIDATE_SORTING = "candidate_sorting"
    DAY1_PREVIEW = "day1_preview"
    BRAND_POLISHING = "brand_polishing"
    SCHEDULE_ASSEMBLY = "schedule_assembly"
    FINAL_REVIEW_REORDER = "final_review_reorder"
    SELF_SERVE_TUNING = "self_serve_tuning"


@dataclass
class SoftRuleDimension:
    """软规则维度定义"""
    id: str  # 英文 snake_case 标识
    name_cn: str  # 中文名
    user_feeling: str  # 解决的用户感受
    main_impact: str  # 主要影响
    effective_stages: List[EffectiveStage]  # 生效阶段列表
    recommended_source: DimensionSource  # 推荐评估来源
    default_weight: float  # 默认权重 0-1
    score_range: tuple[float, float] = (0.0, 10.0)  # 分值范围
    
    def validate_score(self, score: float) -> bool:
        """验证分值是否在有效范围内"""
        return self.score_range[0] <= score <= self.score_range[1]
    
    def validate_weight(self, weight: float) -> bool:
        """验证权重是否有效"""
        return 0.0 <= weight <= 1.0


# 12个软规则维度定义
# 基于 soft-rule-dimensions/spec.md 表格
SOFT_RULE_DIMENSIONS: Dict[str, SoftRuleDimension] = {
    "emotional_value": SoftRuleDimension(
        id="emotional_value",
        name_cn="情绪价值/氛围感",
        user_feeling='"这个地方有感觉"',
        main_impact="喜欢度",
        effective_stages=[
            EffectiveStage.CANDIDATE_SORTING,
            EffectiveStage.DAY1_PREVIEW,
            EffectiveStage.BRAND_POLISHING
        ],
        recommended_source=DimensionSource.AI_ESTIMATE,
        default_weight=0.12
    ),
    "shareability": SoftRuleDimension(
        id="shareability",
        name_cn="分享感/出片回报",
        user_feeling='"值得发朋友圈"',
        main_impact="转介绍",
        effective_stages=[
            EffectiveStage.CANDIDATE_SORTING,
            EffectiveStage.DAY1_PREVIEW,
            EffectiveStage.SELF_SERVE_TUNING
        ],
        recommended_source=DimensionSource.AI_ESTIMATE,
        default_weight=0.10
    ),
    "relaxation_feel": SoftRuleDimension(
        id="relaxation_feel",
        name_cn="松弛感/不赶感",
        user_feeling='"不累、不焦虑"',
        main_impact="喜欢度",
        effective_stages=[
            EffectiveStage.SCHEDULE_ASSEMBLY,
            EffectiveStage.FINAL_REVIEW_REORDER
        ],
        recommended_source=DimensionSource.AI_ESTIMATE,
        default_weight=0.10
    ),
    "memory_point": SoftRuleDimension(
        id="memory_point",
        name_cn="记忆点强度",
        user_feeling='"回来有故事讲"',
        main_impact="复购",
        effective_stages=[
            EffectiveStage.CANDIDATE_SORTING,
            EffectiveStage.DAY1_PREVIEW
        ],
        recommended_source=DimensionSource.AI_ESTIMATE,
        default_weight=0.10
    ),
    "localness": SoftRuleDimension(
        id="localness",
        name_cn="当地感/不模板感",
        user_feeling='"不是千篇一律"',
        main_impact="喜欢度",
        effective_stages=[
            EffectiveStage.CANDIDATE_SORTING,
            EffectiveStage.SELF_SERVE_TUNING
        ],
        recommended_source=DimensionSource.MANUAL_SEED,
        default_weight=0.08
    ),
    "smoothness": SoftRuleDimension(
        id="smoothness",
        name_cn="顺滑感/少折腾感",
        user_feeling='"不折腾、不绕路"',
        main_impact="免费转付费",
        effective_stages=[
            EffectiveStage.SCHEDULE_ASSEMBLY,
            EffectiveStage.FINAL_REVIEW_REORDER
        ],
        recommended_source=DimensionSource.STATISTICAL,
        default_weight=0.10
    ),
    "food_certainty": SoftRuleDimension(
        id="food_certainty",
        name_cn="餐饮确定感",
        user_feeling='"吃饭不踩雷"',
        main_impact="免费转付费",
        effective_stages=[
            EffectiveStage.SCHEDULE_ASSEMBLY,
            EffectiveStage.SELF_SERVE_TUNING
        ],
        recommended_source=DimensionSource.AI_ESTIMATE,
        default_weight=0.08
    ),
    "night_completion": SoftRuleDimension(
        id="night_completion",
        name_cn="夜间完成度",
        user_feeling='"晚上不无聊"',
        main_impact="喜欢度",
        effective_stages=[EffectiveStage.SCHEDULE_ASSEMBLY],
        recommended_source=DimensionSource.AI_ESTIMATE,
        default_weight=0.07
    ),
    "recovery_friendliness": SoftRuleDimension(
        id="recovery_friendliness",
        name_cn="恢复友好度",
        user_feeling='"累了能休息"',
        main_impact="喜欢度",
        effective_stages=[
            EffectiveStage.SCHEDULE_ASSEMBLY,
            EffectiveStage.FINAL_REVIEW_REORDER
        ],
        recommended_source=DimensionSource.STATISTICAL,
        default_weight=0.06
    ),
    "weather_resilience_soft": SoftRuleDimension(
        id="weather_resilience_soft",
        name_cn="雨天韧性",
        user_feeling='"下雨不废掉"',
        main_impact="免费转付费",
        effective_stages=[
            EffectiveStage.CANDIDATE_SORTING,
            EffectiveStage.SELF_SERVE_TUNING
        ],
        recommended_source=DimensionSource.AI_ESTIMATE,
        default_weight=0.05
    ),
    "professional_judgement_feel": SoftRuleDimension(
        id="professional_judgement_feel",
        name_cn="专业判断感",
        user_feeling='"不是 AI 随便生成的"',
        main_impact="免费转付费",
        effective_stages=[
            EffectiveStage.DAY1_PREVIEW,
            EffectiveStage.BRAND_POLISHING
        ],
        recommended_source=DimensionSource.MANUAL_SEED,
        default_weight=0.08
    ),
    "preview_conversion_power": SoftRuleDimension(
        id="preview_conversion_power",
        name_cn="免费 Day 1 杀伤力",
        user_feeling='"看了就想买"',
        main_impact="免费转付费",
        effective_stages=[EffectiveStage.DAY1_PREVIEW],
        recommended_source=DimensionSource.STATISTICAL,
        default_weight=0.06
    )
}


def get_soft_rule_dimensions() -> Dict[str, SoftRuleDimension]:
    """获取所有软规则维度定义"""
    return SOFT_RULE_DIMENSIONS.copy()


def get_dimension(dimension_id: str) -> Optional[SoftRuleDimension]:
    """获取指定维度的定义"""
    return SOFT_RULE_DIMENSIONS.get(dimension_id)


def validate_dimension_scores(scores: Dict[str, float]) -> Dict[str, str]:
    """验证维度分值，返回错误信息字典"""
    errors = {}
    
    for dim_id, score in scores.items():
        dimension = get_dimension(dim_id)
        if not dimension:
            errors[dim_id] = f"未知维度: {dim_id}"
        elif not dimension.validate_score(score):
            errors[dim_id] = f"分值 {score} 超出范围 {dimension.score_range}"
    
    return errors


def validate_weight_sum(weights: Dict[str, float], tolerance: float = 0.01) -> bool:
    """验证权重总和是否为1（允许容差）"""
    total = sum(weights.values())
    return abs(total - 1.0) <= tolerance


def get_default_weights() -> Dict[str, float]:
    """获取默认权重（12维度权重之和为1.00）"""
    return {dim_id: dim.default_weight for dim_id, dim in SOFT_RULE_DIMENSIONS.items()}


def get_dimensions_by_stage(stage: EffectiveStage) -> List[SoftRuleDimension]:
    """获取指定阶段生效的维度"""
    return [
        dim for dim in SOFT_RULE_DIMENSIONS.values()
        if stage in dim.effective_stages
    ]


def get_dimensions_by_source(source: DimensionSource) -> List[SoftRuleDimension]:
    """获取指定来源推荐的维度"""
    return [
        dim for dim in SOFT_RULE_DIMENSIONS.values()
        if dim.recommended_source == source
    ]


# 验证默认权重总和
_DEFAULT_WEIGHTS = get_default_weights()
if not validate_weight_sum(_DEFAULT_WEIGHTS):
    raise ValueError(f"默认权重总和不为1: {sum(_DEFAULT_WEIGHTS.values())}")


if __name__ == "__main__":
    # 测试代码
    print("12维软规则定义测试:")
    print(f"维度数量: {len(SOFT_RULE_DIMENSIONS)}")
    
    default_weights = get_default_weights()
    print(f"默认权重总和: {sum(default_weights.values()):.2f}")
    
    # 打印每个维度信息
    for dim_id, dimension in SOFT_RULE_DIMENSIONS.items():
        print(f"\n{dimension.id}: {dimension.name_cn}")
        print(f"  默认权重: {dimension.default_weight:.2f}")
        print(f"  生效阶段: {[stage.value for stage in dimension.effective_stages]}")
        print(f"  推荐来源: {dimension.recommended_source.value}")
    
    # 验证函数测试
    test_scores = {
        "emotional_value": 8.5,
        "shareability": 9.0,
        "relaxation_feel": 7.5
    }
    errors = validate_dimension_scores(test_scores)
    if errors:
        print(f"\n验证错误: {errors}")
    else:
        print("\n测试分值验证通过")