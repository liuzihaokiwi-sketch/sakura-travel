## ADDED Requirements

### Requirement: 6 角色评审流水线

系统 SHALL 实现一条 6 角色链式评审流水线，在行程装配完成后、人工审核前自动执行。

| 步骤 | 角色 | 模型 | 输入 | 输出 | 自动通过条件 | 触发重写条件 | 触发人工条件 |
|------|------|------|------|------|------------|------------|------------|
| 1 | **Planner** | gpt-4o | trip_profile + template + entities | 完整行程 JSON | — | — | — |
| 2 | **QA Checker** | gpt-4o-mini | 行程 JSON | issues[] (hard_fail/soft_fail) | 0 hard_fail + ≤2 soft_fail | ≥1 hard_fail | ≥3 hard_fail 连续重写失败 |
| 3 | **User Proxy** | gpt-4o | 行程 JSON + 客群描述 | satisfaction_score(1-10) + complaints[] | score ≥ 7 且 0 complaints | score < 5 | score < 3 |
| 4 | **Ops Proxy** | gpt-4o-mini | 行程 JSON + entity_operational_context | ops_issues[] (预约/排队/交通/天气) | 0 critical ops_issues | ≥1 critical 但有替代方案 | ≥2 critical 无替代方案 |
| 5 | **Tuning Guard** | gpt-4o-mini | 行程 JSON + 候选池 | tunable_modules[] + locked_modules[] | 有 ≥3 个可微调点 | 可微调点 < 2 | — |
| 6 | **Final Judge** | gpt-4o | 行程 JSON + QA/User/Ops 结果 | verdict: publish/rewrite/human | verdict=publish | verdict=rewrite（最多 2 轮） | verdict=human |

流水线执行规则：
1. 步骤 1 (Planner) 由现有 assemble_trip + copywriter 完成，不是新增
2. 步骤 2-5 可并行执行（互不依赖）
3. 步骤 6 等步骤 2-5 全部完成后执行
4. rewrite 最多 2 轮，第 3 轮自动转人工
5. 每步有独立的 Redis 缓存（相同输入不重复调用）

#### Scenario: 全自动通过

- **WHEN** QA 0 hard_fail、User score=8、Ops 0 critical、Tuning ≥3 可微调点
- **THEN** Final Judge verdict=publish，行程自动进入渲染导出队列

#### Scenario: 自动重写

- **WHEN** QA 发现 1 个 hard_fail（午餐时段无餐厅）
- **THEN** Final Judge verdict=rewrite，系统自动重新装配受影响的天，再次执行步骤 2-6

#### Scenario: 转人工

- **WHEN** 重写 2 轮后 User Proxy score 仍 < 5
- **THEN** Final Judge verdict=human，行程进入人工审核队列，标注 User Proxy 的具体 complaints

### Requirement: 评审结果持久化

每次评审 SHALL 写入 `review_pipeline_runs` 表：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | 主键 |
| plan_id | UUID | 关联行程 |
| round | INT | 第几轮（1=首次，2=第一次重写...） |
| qa_result | JSONB | QA 结果 |
| user_proxy_result | JSONB | User Proxy 结果 |
| ops_proxy_result | JSONB | Ops Proxy 结果 |
| tuning_guard_result | JSONB | Tuning Guard 结果 |
| final_verdict | VARCHAR | publish / rewrite / human |
| final_reason | TEXT | 裁决理由 |
| total_tokens | INT | 本轮总 token 消耗 |
| total_duration_ms | INT | 本轮总耗时 |
| created_at | TIMESTAMP | 创建时间 |

#### Scenario: Token 成本追踪

- **WHEN** 查询某行程的评审成本
- **THEN** 可通过 review_pipeline_runs.total_tokens 汇总所有轮次的总 token 消耗

### Requirement: User Proxy 客群化 Prompt

User Proxy 的评审 prompt SHALL 根据客群动态调整：

- **couple**：重点检查"有没有浪漫氛围场景""出片点够不够""节奏是否太赶"
- **besties**：重点检查"有没有闺蜜合照场景""美食推荐是否精彩""夜间活动是否丰富"
- **parents**：重点检查"节奏是否太赶""有没有无障碍考虑""餐厅是否适合老人"
- **first_time_fit**：重点检查"是否涵盖经典必去""交通指引是否清晰""有没有让人安心的确定感"

#### Scenario: 情侣客群评审

- **WHEN** 为 couple 客群行程执行 User Proxy
- **THEN** prompt 中注入"你是一对即将去日本的情侣中的一位"，重点评估浪漫氛围和出片回报
