## ADDED Requirements

### Requirement: 12 维度软规则定义

系统 SHALL 定义 12 个软规则评分维度，每个维度有唯一英文 snake_case 标识、中文名、分值范围 0-10、默认权重、生效阶段列表和推荐评估来源。

维度清单：

| 维度 ID | 中文名 | 解决的用户感受 | 主要影响 | 生效阶段 | 评估来源 | 默认权重 |
|---------|--------|--------------|---------|---------|---------|---------|
| emotional_value | 情绪价值/氛围感 | "这个地方有感觉" | 喜欢度 | 候选排序, Day 1 预览, 品牌润色 | AI 估计 + 人工 seed | 0.12 |
| shareability | 分享感/出片回报 | "值得发朋友圈" | 转介绍 | 候选排序, Day 1 预览, 自助微调 | AI 估计 | 0.10 |
| relaxation_feel | 松弛感/不赶感 | "不累、不焦虑" | 喜欢度 | 日程装配, 总审重排 | AI 估计 | 0.10 |
| memory_point | 记忆点强度 | "回来有故事讲" | 复购 | 候选排序, Day 1 预览 | 人工 seed + AI 估计 | 0.10 |
| localness | 当地感/不模板感 | "不是千篇一律" | 喜欢度 | 候选排序, 自助微调 | 人工 seed | 0.08 |
| smoothness | 顺滑感/少折腾感 | "不折腾、不绕路" | 免费转付费 | 日程装配, 总审重排 | 统计特征 | 0.10 |
| food_certainty | 餐饮确定感 | "吃饭不踩雷" | 免费转付费 | 日程装配, 自助微调 | AI 估计 | 0.08 |
| night_completion | 夜间完成度 | "晚上不无聊" | 喜欢度 | 日程装配 | AI 估计 | 0.07 |
| recovery_friendliness | 恢复友好度 | "累了能休息" | 喜欢度 | 日程装配, 总审重排 | 统计特征 | 0.06 |
| weather_resilience_soft | 雨天韧性 | "下雨不废掉" | 免费转付费 | 候选排序, 自助微调 | AI 估计 | 0.05 |
| professional_judgement_feel | 专业判断感 | "不是 AI 随便生成的" | 免费转付费 | Day 1 预览, 品牌润色 | 人工 seed | 0.08 |
| preview_conversion_power | 免费 Day 1 杀伤力 | "看了就想买" | 免费转付费 | Day 1 预览 | 统计特征 + AI 估计 | 0.06 |

所有维度默认权重之和 SHALL 等于 1.00。

#### Scenario: 查看维度定义

- **WHEN** 调用 `get_soft_rule_dimensions()`
- **THEN** 返回 12 个维度对象，每个包含 id / name_cn / score_range / default_weight / effective_stages / source_type

#### Scenario: 维度权重总和校验

- **WHEN** 加载任一权重包或默认权重集
- **THEN** 所有 12 个维度权重之和 SHALL 在 0.99-1.01 范围内（浮点精度容差）

### Requirement: 实体级软规则分计算

系统 SHALL 为每个实体（POI / 餐厅 / 酒店）计算 12 个维度的软规则分，每个维度分值范围 0-10，结果存入 entity_soft_scores 表。

计算方式分三类：
1. **AI 估计**：调用 LLM，输入实体名称/描述/标签/评论摘要，输出维度分 + 理由
2. **统计特征**：通过实体属性（位置/价格/交通/营业时间）程序化计算
3. **人工 seed**：从 editorial_seed_overrides 表读取手动设定值

当同一维度有多个来源时，优先级为：人工 seed > 统计特征 > AI 估计。

#### Scenario: 全量批量计算

- **WHEN** 运行 `score_soft_rules` batch job 且参数为 city_code="tokyo"
- **THEN** 东京所有实体的 entity_soft_scores 表被填充，每个实体 12 个维度均有值

#### Scenario: 人工 seed 覆盖 AI 估计

- **WHEN** 某实体的 emotional_value 在 editorial_seed_overrides 中有人工 seed 值 8.5
- **THEN** 该实体的 entity_soft_scores.emotional_value = 8.5，source = "manual_seed"

#### Scenario: 增量计算

- **WHEN** 新实体入库后运行增量 soft_rule 评分
- **THEN** 只计算新增实体和上次计算后有属性变更的实体，不重算无变更实体

### Requirement: 软规则聚合分计算

系统 SHALL 提供 `compute_soft_rule_score(entity_id, segment_pack_id, stage_pack_id)` 函数，根据客群权重包和阶段权重包，将 12 个维度分聚合为单一 soft_rule_score（0-100）。

公式：
```
soft_rule_score = Σ(dimension_score_i × segment_weight_i × stage_weight_i) / Σ(segment_weight_i × stage_weight_i) × 100 / 10
```

#### Scenario: 情侣标准版聚合

- **WHEN** 调用 `compute_soft_rule_score(entity_id, "couple", "standard")`
- **THEN** 返回基于 couple 权重包和 standard 阶段权重包的聚合分，0-100 范围

#### Scenario: 无权重包时使用默认

- **WHEN** 调用 `compute_soft_rule_score(entity_id, None, None)`
- **THEN** 使用 12 个维度的默认权重计算，不抛错

### Requirement: 软规则数据表结构

系统 SHALL 创建以下数据表：

**entity_soft_scores**：实体级 12 维度软规则分
- entity_type VARCHAR NOT NULL (poi / hotel / restaurant)
- entity_id UUID NOT NULL
- emotional_value DECIMAL(3,1) — 0-10
- shareability DECIMAL(3,1)
- relaxation_feel DECIMAL(3,1)
- memory_point DECIMAL(3,1)
- localness DECIMAL(3,1)
- smoothness DECIMAL(3,1)
- food_certainty DECIMAL(3,1)
- night_completion DECIMAL(3,1)
- recovery_friendliness DECIMAL(3,1)
- weather_resilience_soft DECIMAL(3,1)
- professional_judgement_feel DECIMAL(3,1)
- preview_conversion_power DECIMAL(3,1)
- score_sources JSONB — 每个维度的来源（ai / stat / manual）
- score_version VARCHAR — 评分引擎版本号
- calculated_at TIMESTAMP
- 主键：(entity_type, entity_id)
- 索引：entity_type + calculated_at

**editorial_seed_overrides**：人工修正种子值
- entity_type VARCHAR NOT NULL
- entity_id UUID NOT NULL
- dimension_id VARCHAR NOT NULL — 维度标识
- override_value DECIMAL(3,1) — 0-10
- reason TEXT — 修正理由
- editor_id VARCHAR
- updated_at TIMESTAMP
- 主键：(entity_type, entity_id, dimension_id)

**soft_rule_explanations**：每次评分的可解释性记录
- id UUID 主键
- entity_type VARCHAR
- entity_id UUID
- dimension_id VARCHAR
- score DECIMAL(3,1)
- explanation TEXT — 一句话理由
- source VARCHAR — ai / stat / manual
- score_version VARCHAR
- created_at TIMESTAMP

#### Scenario: 表创建与迁移

- **WHEN** 运行数据库迁移
- **THEN** entity_soft_scores / editorial_seed_overrides / soft_rule_explanations 三张表被创建，字段类型和约束符合上述定义

#### Scenario: 评分可追溯

- **WHEN** 查询某实体的软规则分
- **THEN** 可通过 soft_rule_explanations 追溯每个维度分的来源和理由
