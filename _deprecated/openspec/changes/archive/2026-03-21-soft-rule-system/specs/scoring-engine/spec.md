## MODIFIED Requirements

### Requirement: 候选排序分公式

系统的候选排序分公式 SHALL 从两维扩展为三维，新增 soft_rule_score：

原公式：
```
candidate_score = 0.60 × system_score + 0.40 × context_score - risk_penalty
```

新公式：
```
candidate_score = 0.45 × system_score + 0.30 × context_score + 0.25 × soft_rule_score - risk_penalty
```

其中 soft_rule_score 由 `compute_soft_rule_score(entity_id, segment_pack_id, stage_pack_id)` 计算，范围 0-100。

当 soft_rule_score 不可用时（entity_soft_scores 表中无记录），SHALL 退化为原公式（system_score 权重恢复为 0.60，context_score 恢复为 0.40）。

#### Scenario: 三维评分计算

- **WHEN** 实体有 system_score=80, context_score=70, soft_rule_score=65, risk_penalty=5
- **THEN** candidate_score = 0.45×80 + 0.30×70 + 0.25×65 - 5 = 36 + 21 + 16.25 - 5 = 68.25

#### Scenario: 软规则分不可用时退化

- **WHEN** 实体有 system_score=80, context_score=70 但无 soft_rule_score
- **THEN** candidate_score = 0.60×80 + 0.40×70 - risk_penalty（使用原公式）

### Requirement: entity_scores 表新增 soft_rule_score 字段

entity_scores 表 SHALL 新增以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| soft_rule_score | DECIMAL(5,2) NULL | 软规则聚合分 0-100 |
| soft_rule_score_detail | JSONB NULL | 12 维度分项明细 |
| segment_pack_id | VARCHAR NULL | 使用的客群权重包 |
| stage_pack_id | VARCHAR NULL | 使用的阶段权重包 |

soft_rule_score 为 NULL 时表示尚未计算，系统 SHALL 使用退化公式。

#### Scenario: 评分记录包含软规则

- **WHEN** 运行带软规则的评分 job
- **THEN** entity_scores 记录中 soft_rule_score 有值，soft_rule_score_detail 包含 12 个维度的分项

#### Scenario: 向后兼容

- **WHEN** 已有 entity_scores 记录没有 soft_rule_score 字段
- **THEN** migration 将 soft_rule_score 设为 NULL，评分引擎使用退化公式

## ADDED Requirements

### Requirement: Ranked 实体召回支持软规则

`get_ranked_entities()` 函数 SHALL 新增可选参数 `segment_pack_id` 和 `stage_pack_id`，当提供时使用三维评分公式排序。

```python
def get_ranked_entities(
    city_code: str,
    entity_type: str,
    score_profile: str = "general",
    limit: int = 20,
    segment_pack_id: str | None = None,
    stage_pack_id: str | None = None,
) -> list[RankedEntity]: ...
```

#### Scenario: 带软规则的 top 20

- **WHEN** 调用 `get_ranked_entities("tokyo", "poi", "general", 20, "couple", "standard")`
- **THEN** 返回使用三维评分公式（含 couple+standard 软规则聚合分）的 top 20 POI
