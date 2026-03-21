## ADDED Requirements

### Requirement: 阶段权重包定义

系统 SHALL 支持 4 个阶段权重包（stage weight packs），每个阶段有不同的软规则优先级，反映该阶段的商业目标差异。

| 阶段 ID | 中文名 | 核心目标 |
|---------|--------|---------|
| preview_day1 | 免费 Day 1 预览 | 触发"想买"——最大化转付费率 |
| standard | 标准版完整行程 | 综合体验——平衡所有维度 |
| premium | 高客单定制版 | 极致体验——个性化 + 专业感 |
| self_serve_tuning | 自助微调 | 稳定体验——替换不崩、局部优化 |

#### Scenario: 加载预览阶段权重包

- **WHEN** 调用 `get_stage_weight_pack("preview_day1")`
- **THEN** 返回 preview_day1 权重包，preview_conversion_power / shareability / professional_judgement_feel 权重明显高于 standard

#### Scenario: 不同阶段目标差异

- **WHEN** 对比 preview_day1 和 standard 的 relaxation_feel 权重
- **THEN** standard 的 relaxation_feel 权重 SHALL 高于 preview_day1，因为预览阶段追求"精彩"，完整版追求"舒适"

### Requirement: 阶段权重包 v1 种子值

**preview_day1（免费 Day 1 预览）**：
- 目标：最大化"看了就想买"
- 高权重：preview_conversion_power=0.15, shareability=0.13, emotional_value=0.13, memory_point=0.12, professional_judgement_feel=0.11
- 中权重：food_certainty=0.09, localness=0.08, smoothness=0.07
- 低权重：relaxation_feel=0.05, night_completion=0.04, recovery_friendliness=0.02, weather_resilience_soft=0.01
- 设计理由：预览阶段要"秀肌肉"，松弛感和恢复友好度可以在正式版展现

**standard（标准版完整行程）**：
- 目标：综合体验最大化
- 权重：直接使用 12 维度的默认权重（与 soft-rule-dimensions 的默认权重一致）
- 设计理由：标准版是基准线，不应有额外偏向

**premium（高客单定制版）**：
- 目标：极致个性化 + 专业判断
- 高权重：professional_judgement_feel=0.14, localness=0.13, memory_point=0.12, emotional_value=0.11
- 中权重：food_certainty=0.10, shareability=0.09, relaxation_feel=0.08, smoothness=0.07
- 低权重：night_completion=0.06, recovery_friendliness=0.04, weather_resilience_soft=0.03, preview_conversion_power=0.03
- 设计理由：高客单用户要"不是 AI 随便出的" + "只有专家才知道的"

**self_serve_tuning（自助微调）**：
- 目标：替换后整体不崩
- 高权重：smoothness=0.16, food_certainty=0.13, relaxation_feel=0.12, recovery_friendliness=0.10
- 中权重：emotional_value=0.09, weather_resilience_soft=0.08, memory_point=0.07, localness=0.07
- 低权重：shareability=0.06, night_completion=0.05, professional_judgement_feel=0.04, preview_conversion_power=0.03
- 设计理由：微调阶段最怕"一改就崩"，顺滑感和确定感必须优先

#### Scenario: 种子数据加载

- **WHEN** 系统首次初始化
- **THEN** 4 个阶段权重包被写入 stage_weight_packs 表

#### Scenario: preview_day1 vs standard 差异可验证

- **WHEN** 同一实体分别用 preview_day1 和 standard 阶段权重包计算 soft_rule_score
- **THEN** 如果该实体 shareability 和 preview_conversion_power 很高，preview_day1 的聚合分 SHALL 显著高于 standard

### Requirement: 阶段权重包数据表

系统 SHALL 创建 stage_weight_packs 表：

| 字段 | 类型 | 说明 |
|------|------|------|
| pack_id | VARCHAR(50) PK | 阶段标识 |
| name_cn | VARCHAR(100) | 中文名 |
| description | TEXT | 核心目标描述 |
| weights | JSONB NOT NULL | 12 维度权重 |
| version | INT DEFAULT 1 | 版本号 |
| updated_at | TIMESTAMP | 更新时间 |

#### Scenario: 表创建

- **WHEN** 运行数据库迁移
- **THEN** stage_weight_packs 表被创建，pack_id 为主键

### Requirement: 为什么免费 Day 1 的软规则目标不等同于完整版

系统的 preview_day1 权重包 SHALL 与 standard 权重包有显著差异，因为：
1. 免费 Day 1 的唯一目标是"触发付费意愿"，不需要照顾全程节奏
2. 完整版需要"每天都舒服"，不能全部是高光
3. preview_day1 应最大化"专业感 + 分享感 + 记忆点"，让用户觉得"这个攻略有东西"
4. standard 应平衡"松弛感 + 顺滑感 + 恢复友好度"，让用户真正用起来不累

#### Scenario: 设计原则验证

- **WHEN** 系统为一个 5 日行程生成预览
- **THEN** 预览选择的那天，preview_day1_score 应高于该天的 standard_score；其他天的 standard_score 平均值应 >= 6.0

### Requirement: 为什么自助微调的排序目标不等同于初次生成

自助微调阶段的 self_serve_tuning 权重包 SHALL 重点保护"整体不崩"，而非追求"单点最优"，因为：
1. 用户替换一个实体后，如果连带的交通/时间/节奏都变了，整体体验可能急剧下降
2. 微调阶段应优先推荐和被替换实体"兼容性最高"的候选
3. smoothness 和 recovery_friendliness 在微调阶段的权重应明显高于初次生成

#### Scenario: 微调保底验证

- **WHEN** 用户在自助微调中替换一个餐厅
- **THEN** 推荐的替换候选按 self_serve_tuning 权重排序，smoothness 和 food_certainty 权重合计 >= 0.25
