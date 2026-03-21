## MODIFIED Requirements

### Requirement: 日程装配打分排序

行程串联模块的"打分排序"步骤（子流程第 2 步）SHALL 使用三维评分公式调用评分引擎，传入当前用户的 segment_pack_id 和 stage_pack_id。

原行为：调用 `get_ranked_entities()` 获取按 candidate_score 排序的候选
新行为：调用 `get_ranked_entities(city, entity_type, profile, limit, segment_pack_id, stage_pack_id)` 获取包含 soft_rule_score 的三维排序候选

#### Scenario: 带软规则的候选召回

- **WHEN** 为情侣用户（segment=couple）装配标准版行程（stage=standard）
- **THEN** 候选召回使用 couple + standard 权重包计算的 soft_rule_score 参与排序

## ADDED Requirements

### Requirement: 日程装配软规则约束

日程装配 SHALL 在现有约束规则（节奏/步行/换乘等）基础上，增加以下软规则约束：

1. **节奏多样性**：同一天不能连续安排 3 个以上 relaxation_feel < 4 的"高强度"实体
2. **餐饮确定性**：如果用户客群为 parents / family_child，午餐餐厅的 food_certainty MUST >= 6.0
3. **夜间完成度**：每天 18:00 后 SHOULD 至少有一个 night_completion >= 5.0 的实体或明确的自由时间
4. **记忆点分布**：整个行程中 memory_point >= 8.0 的实体 SHOULD 均匀分布，不集中在同一天

这些为 soft_fail 级别约束，违反时标记但不阻断。

#### Scenario: 连续高强度检测

- **WHEN** 装配结果中某天连续 4 个 POI 的 relaxation_feel 均 < 4
- **THEN** 产生 soft_fail 提示"当天节奏可能过紧"

#### Scenario: 家庭客群餐饮确定性

- **WHEN** 为 family_child 客群装配行程，某天午餐餐厅 food_certainty = 4.0
- **THEN** 产生 soft_fail 提示"午餐餐厅确定性偏低，建议替换为高确定性餐厅"
