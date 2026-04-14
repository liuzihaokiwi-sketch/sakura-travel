## ADDED Requirements

### Requirement: 用户行为反向验证机制

系统 SHALL 记录以下用户行为事件，用于后续反向验证软规则维度是否有效：

| 行为事件 | 事件名 | 可反推的维度 |
|---------|--------|------------|
| 免费 Day 1 → 付费 | preview_converted | preview_conversion_power, professional_judgement_feel, shareability |
| 免费 Day 1 → 未付费关闭 | preview_bounced | preview_conversion_power（负反馈） |
| 用户分享预览链接 | preview_shared | shareability |
| 用户发起自助微调 | self_serve_tuning_started | 被微调的实体对应维度分可能偏低 |
| 用户微调次数 | tuning_count | 微调次数多 = 初始推荐不够好 |
| 用户加微信咨询 | wechat_contact | professional_judgement_feel（可能不够高） |
| 用户复购 | repurchase | memory_point, localness, food_certainty |
| 用户转介绍 | referral | shareability, emotional_value |
| 用户对单日评价（如有） | day_rating | 该天所有维度的综合反馈 |
| 正式修改请求 | formal_modification | 自助微调未能满足 = 某些维度需要校准 |

#### Scenario: 事件记录

- **WHEN** 用户在预览页点击付费按钮并完成支付
- **THEN** 系统记录 preview_converted 事件，关联 plan_id / selected_preview_day / segment_pack_id

#### Scenario: 未付费退出记录

- **WHEN** 用户查看预览页超过 30 秒后关闭且未付费
- **THEN** 系统记录 preview_bounced 事件

### Requirement: 付费率反哺 preview 权重

系统 SHALL 支持通过 batch job 分析 preview_converted / preview_bounced 事件，输出 preview_day1 权重包的调整建议。

分析逻辑：
1. 统计过去 N 天的付费率（converted / (converted + bounced)）
2. 按预览天的 top 3 高分维度分组
3. 如果某维度高分的行程付费率显著高于平均（>1.2x），建议上调该维度在 preview_day1 的权重
4. 如果某维度高分的行程付费率显著低于平均（<0.8x），建议下调

输出为建议值，MUST 由管理员确认后才写入 stage_weight_packs。

#### Scenario: 生成调整建议

- **WHEN** 运行 `analyze_preview_feedback` batch job 且过去 30 天有 >= 50 条事件
- **THEN** 输出一份 preview_day1 权重调整建议 JSON，包含每个维度的当前权重和建议权重

#### Scenario: 样本量不足

- **WHEN** 过去 30 天 preview 事件 < 50 条
- **THEN** 不输出建议，返回"样本量不足，建议继续使用种子权重"

### Requirement: 必须埋点日志

系统 SHALL 在以下位置埋点，日志格式为结构化 JSON：

**预览页埋点**：
- page_view: { plan_id, preview_day_index, segment_pack_id, timestamp }
- cta_click: { plan_id, cta_position, cta_type, timestamp }
- scroll_depth: { plan_id, max_scroll_percent, timestamp }
- time_on_page: { plan_id, duration_seconds, timestamp }
- share_click: { plan_id, share_channel, timestamp }

**微调页埋点**：
- swap_initiated: { plan_id, original_entity_id, entity_type, timestamp }
- swap_candidates_viewed: { plan_id, original_entity_id, candidates_shown, timestamp }
- swap_selected: { plan_id, original_entity_id, selected_entity_id, swap_score, timestamp }
- swap_cancelled: { plan_id, original_entity_id, timestamp }
- pace_switch: { plan_id, day_index, new_pace, timestamp }

**转化埋点**：
- payment_started: { plan_id, price, timestamp }
- payment_completed: { plan_id, price, payment_method, timestamp }
- payment_abandoned: { plan_id, step_abandoned, timestamp }

#### Scenario: 预览页埋点完整性

- **WHEN** 用户访问预览页并执行浏览、点击 CTA、分享操作
- **THEN** 每个操作对应的埋点日志被记录到 soft_rule_feedback_log 表或日志服务

### Requirement: A/B test 框架基础

系统 SHALL 支持基础的 A/B test 能力，用于校准软规则权重：

1. 每个行程生成请求 SHALL 携带一个 experiment_group 字段（control / treatment_a / treatment_b...）
2. experiment_group 由用户 ID hash 决定，确保同一用户始终在同一组
3. 不同组可使用不同的权重包版本
4. 所有埋点日志 SHALL 包含 experiment_group 字段

v1 不需要自动化实验平台，只需要：
- 支持按 experiment_group 切换权重包
- 所有日志带 experiment_group
- 提供简单的分组统计查询

#### Scenario: 实验分组

- **WHEN** user_id = "abc123" 请求生成行程
- **THEN** hash("abc123") 决定 experiment_group，后续所有该用户的行程生成和埋点都使用同一 group

#### Scenario: 不同组不同权重

- **WHEN** control 组和 treatment_a 组同时生成行程
- **THEN** control 使用默认权重包，treatment_a 使用实验权重包

### Requirement: 防止过拟合某一类客群

系统 SHALL 在校准权重时检查客群平衡性：

1. 如果某个客群的事件数占总事件数 > 60%，校准分析 MUST 输出警告
2. 校准建议 MUST 同时输出按客群拆分的结果，不只看总体
3. 默认权重包（standard）MUST NOT 被单一客群的数据覆盖

#### Scenario: 客群失衡警告

- **WHEN** 过去 30 天 couple 客群事件占 70%
- **THEN** 校准分析输出"警告：couple 客群数据占比过高，建议结果可能偏向情侣场景"

### Requirement: 反馈日志数据表

系统 SHALL 创建 soft_rule_feedback_log 表：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | 主键 |
| plan_id | UUID | 关联行程 |
| user_id | VARCHAR | 用户 ID |
| event_type | VARCHAR NOT NULL | 事件类型 |
| event_data | JSONB | 事件详情 |
| segment_pack_id | VARCHAR | 当前客群权重包 |
| stage_pack_id | VARCHAR | 当前阶段权重包 |
| experiment_group | VARCHAR | 实验组 |
| created_at | TIMESTAMP | 事件时间 |

索引：event_type + created_at, plan_id, experiment_group

#### Scenario: 表创建

- **WHEN** 运行数据库迁移
- **THEN** soft_rule_feedback_log 表被创建
