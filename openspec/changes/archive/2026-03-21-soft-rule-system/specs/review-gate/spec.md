## ADDED Requirements

### Requirement: 审核报告包含软规则可解释性输出

自动审核结果 SHALL 在 issues 列表中增加软规则相关的可解释性条目：

1. **soft_rule_summary**：每个被选入行程的实体的 top 3 高分维度和 top 1 低分维度
2. **day_soft_score**：每天的软规则聚合分
3. **preview_day_reason**：为什么选了这天做预览（preview_day1_score 分项）
4. **editorial_polish_hints**：professional_judgement_feel < 5.0 的实体列表，提示审核员重点关注

这些信息 SHALL 写入 qa_review_log.issues 的 JSONB 中，供人工审核参考。

#### Scenario: 审核报告包含软规则摘要

- **WHEN** 自动审核完成后查看审核报告
- **THEN** issues 中包含 soft_rule_summary 条目，列出每个实体的维度亮点和短板

#### Scenario: 需人工润色的实体标注

- **WHEN** 行程中有 3 个实体的 professional_judgement_feel < 5.0
- **THEN** 审核报告中有 editorial_polish_hints 条目，列出这 3 个实体及其维度分
