"""
软规则维度定义（Soft Rule Dimensions）

定义 12 个软规则维度，每个维度描述实体/行程的一个"感受性"特征。
这些维度是整个软规则子系统的核心数据结构，所有计算都围绕它们展开。

设计原则：
  1. 每个维度分范围 0-10（DECIMAL(3,1)），方便 human review
  2. 维度分来源分三档：manual（人工 seed） > stat（统计特征） > ai（GPT 估计）
  3. 默认权重之和 = 1.00，权重包可覆盖但仍须求和约等于 1.0
  4. 每个维度有 effective_stages 标注它在哪些阶段生效
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal


# ── 枚举定义 ───────────────────────────────────────────────────────────────────

class SourceType(str, Enum):
    """维度分值的数据来源类型，按优先级从高到低排列"""
    MANUAL = "manual"    # 人工 seed / 编辑覆盖
    STAT = "stat"        # 从实体属性统计计算
    AI = "ai"            # GPT-4o-mini 估计


class Stage(str, Enum):
    """评分使用阶段"""
    PREVIEW = "preview"          # 免费预览选天
    STANDARD = "standard"        # 标准版排序
    PREMIUM = "premium"          # 高级版排序
    SELF_SERVE = "self_serve"    # 自助微调候选排序


# ── 维度数据结构 ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SoftRuleDimension:
    """
    单个软规则维度定义。

    Attributes:
        id: 唯一标识（snake_case），对应 entity_soft_scores 表的列名
        name_cn: 中文名称（用于 UI/报告/日志）
        description: 一句话说明这个维度衡量什么
        score_range: 分值范围 (min, max)，固定 (0, 10)
        default_weight: 默认权重（所有维度之和 = 1.00）
        effective_stages: 该维度在哪些阶段生效
        source_type: v1 推荐的分值来源类型
        calculation_hint: 给计算器的简要说明（方便 AI estimator prompt 引用）
    """
    id: str
    name_cn: str
    description: str
    score_range: tuple[float, float]
    default_weight: float
    effective_stages: tuple[Stage, ...]
    source_type: SourceType
    calculation_hint: str


# ── 12 个软规则维度 ────────────────────────────────────────────────────────────

SOFT_RULE_DIMENSIONS: tuple[SoftRuleDimension, ...] = (

    # ── 情感与体验维度（影响"喜欢"） ────────────────────────────────────

    SoftRuleDimension(
        id="emotional_value",
        name_cn="情绪价值",
        description="这个地方/体验能给用户带来多少情绪共鸣（感动/惊叹/治愈/幸福感）",
        score_range=(0, 10),
        default_weight=0.12,
        effective_stages=(Stage.STANDARD, Stage.PREMIUM, Stage.PREVIEW),
        source_type=SourceType.MANUAL,
        calculation_hint="评估该实体是否有明确的情感触发点：绝美风景、独特文化仪式、"
                         "温馨的店主互动、出乎意料的体验。纯功能性场所（便利店/车站）得低分。",
    ),

    SoftRuleDimension(
        id="shareability",
        name_cn="分享感",
        description="用户体验后在朋友圈/小红书发图分享的概率",
        score_range=(0, 10),
        default_weight=0.10,
        effective_stages=(Stage.STANDARD, Stage.PREMIUM, Stage.PREVIEW),
        source_type=SourceType.AI,
        calculation_hint="有视觉冲击力的场景（千本鸟居/竹林/东京塔夜景）得高分。"
                         "有明确出片角度且不需要专业设备的加分。纯室内功能场所得低分。",
    ),

    SoftRuleDimension(
        id="relaxation_feel",
        name_cn="松弛感",
        description="这个安排给用户的压力感有多低（不赶时间、不拥挤、不需要复杂操作）",
        score_range=(0, 10),
        default_weight=0.10,
        effective_stages=(Stage.STANDARD, Stage.PREMIUM, Stage.SELF_SERVE),
        source_type=SourceType.AI,
        calculation_hint="无需预约、无明显排队、步行可达、停留时间灵活的得高分。"
                         "需要抢票/精确预约/高峰时段才能体验的得低分。",
    ),

    SoftRuleDimension(
        id="memory_point",
        name_cn="记忆锚点",
        description="旅行结束后回忆这段旅程时，这个地方被提到的概率",
        score_range=(0, 10),
        default_weight=0.10,
        effective_stages=(Stage.STANDARD, Stage.PREMIUM, Stage.PREVIEW),
        source_type=SourceType.MANUAL,
        calculation_hint="独特性是关键：只有日本有的体验、季节限定、小众发现。"
                         "满大街都有的连锁店/标准商场得低分。地标景点因辨识度得中分。",
    ),

    # ── 品质与可信维度（影响"信任"） ────────────────────────────────────

    SoftRuleDimension(
        id="localness",
        name_cn="在地感",
        description="这个推荐多大程度上体现'真正的日本/当地生活'而非游客陷阱",
        score_range=(0, 10),
        default_weight=0.08,
        effective_stages=(Stage.STANDARD, Stage.PREMIUM),
        source_type=SourceType.MANUAL,
        calculation_hint="本地人常去的店、隐藏的社区美食、传统工艺体验得高分。"
                         "纯观光巴士线路、旅游街价格虚高的店得低分。",
    ),

    SoftRuleDimension(
        id="food_certainty",
        name_cn="餐饮确定性",
        description="用户按这个推荐去吃，踩雷的概率有多低",
        score_range=(0, 10),
        default_weight=0.08,
        effective_stages=(Stage.STANDARD, Stage.PREMIUM, Stage.SELF_SERVE),
        source_type=SourceType.AI,
        calculation_hint="Tabelog 3.5+、Google 4.0+、有具体推荐菜品、价格范围明确的得高分。"
                         "无评分/评论极少/价格不透明/经常临时关门的得低分。",
    ),

    SoftRuleDimension(
        id="professional_judgement_feel",
        name_cn="专业判断感",
        description="用户看到这个推荐时，能否感受到'这是懂行的人帮我挑的'",
        score_range=(0, 10),
        default_weight=0.08,
        effective_stages=(Stage.STANDARD, Stage.PREMIUM, Stage.PREVIEW),
        source_type=SourceType.MANUAL,
        calculation_hint="有具体的推荐理由（'下午3点去人最少'/'二楼靠窗位看日落'）、"
                         "有证据支撑（Tabelog 分数/步行距离/评论量）、有避坑提醒的得高分。"
                         "只说'很有名'/'值得去'的得低分。",
    ),

    # ── 执行与可行维度（影响"可执行性"） ────────────────────────────────

    SoftRuleDimension(
        id="smoothness",
        name_cn="顺滑度",
        description="这个实体放在当天行程中，交通衔接有多顺畅",
        score_range=(0, 10),
        default_weight=0.10,
        effective_stages=(Stage.STANDARD, Stage.PREMIUM, Stage.SELF_SERVE),
        source_type=SourceType.STAT,
        calculation_hint="同区域/一条线路上的得高分。需要跨城/换乘3次以上的得低分。"
                         "步行可达上一站的满分，公交直达的 7-8 分，需要换乘 5-6 分。",
    ),

    SoftRuleDimension(
        id="night_completion",
        name_cn="夜间完成度",
        description="晚餐之后的时段安排是否完整（有去处、不尴尬、不虚度）",
        score_range=(0, 10),
        default_weight=0.07,
        effective_stages=(Stage.STANDARD, Stage.PREMIUM),
        source_type=SourceType.AI,
        calculation_hint="有夜景/酒吧/居酒屋/夜间开放景点推荐的得高分。"
                         "晚餐后直接'回酒店休息'的得低分（除非是温泉酒店等自身有夜间体验的）。",
    ),

    SoftRuleDimension(
        id="recovery_friendliness",
        name_cn="体力友好度",
        description="这个安排对体力消耗是否友好（不会让人走断腿）",
        score_range=(0, 10),
        default_weight=0.06,
        effective_stages=(Stage.STANDARD, Stage.PREMIUM, Stage.SELF_SERVE),
        source_type=SourceType.STAT,
        calculation_hint="室内为主/有休息区/步行量适中/有坐下来的环节的得高分。"
                         "全天暴走/爬山/无休息点的得低分。对亲子客群此维度权重应更高。",
    ),

    SoftRuleDimension(
        id="weather_resilience_soft",
        name_cn="天气适应性",
        description="下雨天这个安排还能否正常进行",
        score_range=(0, 10),
        default_weight=0.05,
        effective_stages=(Stage.STANDARD, Stage.PREMIUM),
        source_type=SourceType.STAT,
        calculation_hint="纯室内（博物馆/商场/温泉）满分。有室内备选方案的 7-8 分。"
                         "纯户外且无雨天替代方案的得低分。",
    ),

    # ── 转化维度（影响"付费"） ──────────────────────────────────────────

    SoftRuleDimension(
        id="preview_conversion_power",
        name_cn="预览转化力",
        description="这个实体出现在免费预览中时，对促成付费的贡献度",
        score_range=(0, 10),
        default_weight=0.06,
        effective_stages=(Stage.PREVIEW,),
        source_type=SourceType.STAT,
        calculation_hint="视觉吸引力强 + 有证据化推荐理由 + 有独特卖点 = 高转化力。"
                         "预览转化力 = 0.4×shareability + 0.3×professional_judgement_feel + 0.3×memory_point"
                         "（可用其他维度分推算，是一个派生维度）",
    ),
)


# ── 维度快捷索引 ───────────────────────────────────────────────────────────────

DIMENSION_IDS: tuple[str, ...] = tuple(d.id for d in SOFT_RULE_DIMENSIONS)
"""所有维度 ID 的有序元组（与表列顺序一致）"""

DIMENSION_BY_ID: dict[str, SoftRuleDimension] = {
    d.id: d for d in SOFT_RULE_DIMENSIONS
}
"""ID → 维度定义的快速查找字典"""

DIMENSION_COUNT: int = len(SOFT_RULE_DIMENSIONS)
"""维度总数（应为 12）"""


# ── 默认权重 ───────────────────────────────────────────────────────────────────

DEFAULT_WEIGHTS: dict[str, float] = {
    d.id: d.default_weight for d in SOFT_RULE_DIMENSIONS
}
"""默认权重字典，所有维度之和应为 1.00"""


# ── 公共函数 ───────────────────────────────────────────────────────────────────

def get_soft_rule_dimensions() -> tuple[SoftRuleDimension, ...]:
    """返回所有 12 个软规则维度定义。"""
    return SOFT_RULE_DIMENSIONS


def get_dimension(dimension_id: str) -> SoftRuleDimension:
    """
    根据 ID 获取单个维度定义。

    Raises:
        KeyError: 如果 dimension_id 不存在
    """
    try:
        return DIMENSION_BY_ID[dimension_id]
    except KeyError:
        valid = ", ".join(DIMENSION_IDS)
        raise KeyError(
            f"Unknown soft rule dimension: {dimension_id!r}. "
            f"Valid dimensions: {valid}"
        ) from None


def validate_weights(
    weights: dict[str, float],
    tolerance: float = 0.02,
) -> tuple[bool, str]:
    """
    校验权重包的合法性。

    检查项：
    1. 所有 key 必须是合法维度 ID
    2. 所有 value 必须 >= 0
    3. 权重之和在 [1.0 - tolerance, 1.0 + tolerance] 内

    Args:
        weights: 待校验的权重字典 {dimension_id: weight}
        tolerance: 求和容差（默认 0.02，即 0.98-1.02 均可）

    Returns:
        (is_valid, error_message)
        is_valid=True 时 error_message 为空字符串
    """
    # 检查 key 合法性
    unknown_keys = set(weights.keys()) - set(DIMENSION_IDS)
    if unknown_keys:
        return False, f"Unknown dimension IDs: {unknown_keys}"

    # 检查 key 完整性（权重包必须覆盖所有 12 个维度）
    missing_keys = set(DIMENSION_IDS) - set(weights.keys())
    if missing_keys:
        return False, f"Missing dimension IDs: {missing_keys}"

    # 检查 value 非负
    negative_keys = [k for k, v in weights.items() if v < 0]
    if negative_keys:
        return False, f"Negative weights for: {negative_keys}"

    # 检查求和
    total = sum(weights.values())
    if abs(total - 1.0) > tolerance:
        return False, f"Weights sum to {total:.4f}, expected ~1.0 (tolerance={tolerance})"

    return True, ""


def get_dimensions_for_stage(stage: Stage) -> tuple[SoftRuleDimension, ...]:
    """返回在指定阶段生效的维度列表。"""
    return tuple(d for d in SOFT_RULE_DIMENSIONS if stage in d.effective_stages)


def get_dimensions_by_source(source: SourceType) -> tuple[SoftRuleDimension, ...]:
    """返回指定来源类型的维度列表。"""
    return tuple(d for d in SOFT_RULE_DIMENSIONS if d.source_type == source)


# ── 模块自检 ───────────────────────────────────────────────────────────────────

def _self_check() -> None:
    """
    模块加载时自检（仅在 DEBUG 模式下有意义，生产环境被 Python 优化器跳过）。
    确保维度定义的内部一致性。
    """
    # 维度数量
    assert DIMENSION_COUNT == 12, f"Expected 12 dimensions, got {DIMENSION_COUNT}"

    # ID 唯一性
    assert len(set(DIMENSION_IDS)) == DIMENSION_COUNT, "Duplicate dimension IDs detected"

    # 默认权重求和
    is_valid, err = validate_weights(DEFAULT_WEIGHTS)
    assert is_valid, f"Default weights validation failed: {err}"


# 仅在非优化模式下运行自检
if __debug__:
    _self_check()
