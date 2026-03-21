## ADDED Requirements

### Requirement: 替换候选排序引擎

系统 SHALL 实现 swap candidate ranker，当用户在自助微调中请求替换某个实体时，从候选池中生成排好序的替换建议列表。

swap_score 公式：
```
swap_score = 0.40 × context_fit        # 和被替换实体的场景适配度匹配
           + 0.25 × soft_rule_score    # 使用 self_serve_tuning 阶段权重的软规则聚合分
           + 0.20 × slot_compatibility # 时间窗口/地理位置/实体类型兼容性
           + 0.15 × differentiation    # 和被替换实体的差异度（避免推荐太类似的）
```

其中：
- context_fit：候选实体的 context_score 与原实体 context_score 的接近度
- slot_compatibility：候选实体是否能放入同一时间槽（营业时间匹配、步行距离合理、类型一致）
- differentiation：候选与原实体的标签重合度反比（鼓励推荐"不同但等效"的替代）

#### Scenario: 餐厅替换

- **WHEN** 用户请求替换午餐餐厅 A
- **THEN** 系统返回 3-5 个替换候选，按 swap_score 降序排列，每个候选包含名称、swap_score 分项、一句话推荐理由

#### Scenario: POI 替换

- **WHEN** 用户请求替换下午的景点 B
- **THEN** 系统返回 3-5 个替换候选，所有候选的营业时间 MUST 覆盖原时间槽，距离上下游实体步行时间 MUST 不超过原实体的 1.5 倍

#### Scenario: 酒店替换

- **WHEN** 用户请求替换酒店
- **THEN** 系统返回 3-5 个替换候选，所有候选 MUST 在同一区域或相邻区域，价格区间 MUST 在原酒店 ±30% 范围内

### Requirement: 局部重排引擎

当用户选择替换实体后，系统 SHALL 对当天行程进行局部重排，但 MUST NOT 修改其他天的行程。

局部重排逻辑：
1. 将新实体放入原时间槽
2. 重新计算当天的交通时间（前一站 → 新实体 → 下一站）
3. 如果时间溢出（当天总时间超限 > 30 分钟），自动微调相邻实体的停留时间
4. 如果时间溢出严重（> 60 分钟），提示用户当天可能需要删减一个实体
5. 重算当天的 day_soft_score

#### Scenario: 正常替换

- **WHEN** 用户将景点 A 替换为景点 B，B 步行时间多 5 分钟
- **THEN** 系统调整当天时间表，B 的停留时间和前后交通时间更新，其他天不变

#### Scenario: 时间溢出警告

- **WHEN** 用户替换后当天总时间超出 45 分钟
- **THEN** 系统显示警告"替换后当天行程可能较紧凑，建议减少一个景点"并提供删减建议

### Requirement: 整体体验保底机制

系统 SHALL 在每次替换后检查整体行程的 itinerary_soft_score 跌幅。

保底规则：
1. 计算替换后的新 itinerary_soft_score
2. 与替换前对比，跌幅阈值为 15%
3. 跌幅 <= 15%：正常执行替换
4. 跌幅 > 15% 且 <= 25%：执行替换但显示"温和警告"（"这个替换可能略微降低整体体验"）
5. 跌幅 > 25%：显示"强烈警告"（"这个替换会显著影响整体体验，建议选择其他候选"），但不阻止用户

系统 MUST NOT 阻止用户的任何替换选择，只提供信息和建议。

#### Scenario: 无跌幅替换

- **WHEN** 替换后 itinerary_soft_score 跌幅 5%
- **THEN** 正常执行替换，不显示警告

#### Scenario: 中等跌幅替换

- **WHEN** 替换后 itinerary_soft_score 跌幅 20%
- **THEN** 执行替换并显示温和警告

#### Scenario: 严重跌幅替换

- **WHEN** 替换后 itinerary_soft_score 跌幅 30%
- **THEN** 执行替换并显示强烈警告和替代建议，但不阻止

### Requirement: 节奏轻重切换

系统 SHALL 支持用户在自助微调中切换当天的整体节奏：

- **轻松模式**：减少 1-2 个实体，加长午休/自由时间，relaxation_feel 权重临时上调 50%
- **充实模式**：增加 1-2 个实体，压缩间隔时间，memory_point / emotional_value 权重临时上调 30%

切换后系统自动重新装配当天行程。

#### Scenario: 切换到轻松模式

- **WHEN** 用户对 Day 3 选择"轻松模式"
- **THEN** Day 3 减少 1-2 个低优先级实体，加入自由时间块，重新计算当天 day_soft_score

#### Scenario: 切换到充实模式

- **WHEN** 用户对 Day 3 选择"充实模式"
- **THEN** Day 3 从候选池补充 1-2 个高软规则分实体，压缩间隔，重新计算当天 day_soft_score

### Requirement: 替换候选排序数据表

系统 SHALL 创建 swap_candidate_soft_scores 表：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | 主键 |
| plan_id | UUID NOT NULL | 关联行程 |
| original_entity_type | VARCHAR | 被替换实体类型 |
| original_entity_id | UUID | 被替换实体 ID |
| candidate_entity_id | UUID | 候选实体 ID |
| context_fit | DECIMAL(5,2) | 场景适配分 |
| soft_rule_score | DECIMAL(5,2) | 软规则分 |
| slot_compatibility | DECIMAL(5,2) | 兼容性分 |
| differentiation | DECIMAL(5,2) | 差异度分 |
| swap_score | DECIMAL(5,2) | 最终替换分 |
| was_selected | BOOLEAN DEFAULT FALSE | 用户是否选了这个 |
| created_at | TIMESTAMP | 创建时间 |

索引：plan_id + original_entity_id

#### Scenario: 替换记录追溯

- **WHEN** 查询某次替换的候选列表
- **THEN** 可通过 plan_id + original_entity_id 查到所有候选及其分项分数
