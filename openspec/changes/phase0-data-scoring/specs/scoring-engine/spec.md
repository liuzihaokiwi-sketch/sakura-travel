## MODIFIED Requirements

### Requirement: score_entities Job 注册与自动触发

系统的 `score_entities` arq job SHALL 注册到 `WorkerSettings.functions` 列表中，可通过 `python -m app.workers` 启动并自动消费。

#### Scenario: Worker 启动后可消费评分任务
- **WHEN** 执行 `python -m app.workers` 启动 worker
- **THEN** worker 的 functions 列表包含 `score_entities`，队列中的评分任务被自动消费

#### Scenario: 手动触发全城市评分
- **WHEN** 调用 `await enqueue_job("score_entities", city_code="tokyo")`
- **THEN** worker 消费该 job，entity_scores 表中 tokyo 的实体分数被更新

### Requirement: context_score 端到端计算

scorer.py 中已有的 `compute_context_score()` 纯函数 SHALL 在 `score_entities` job 中被调用，从 entity_tags 表获取亲和度、从 trip_profile 获取用户权重，计算 context_score 并写入 entity_scores.score_breakdown。

#### Scenario: 有标签实体的 context_score 计算
- **WHEN** score_entities job 处理一个有 9 维标签的 POI
- **THEN** entity_scores.score_breakdown 中包含 context_score 分数和 breakdown 明细

#### Scenario: 无标签实体的 context_score 退化
- **WHEN** score_entities job 处理一个无 entity_tags 记录的实体
- **THEN** context_score = 0，不阻断整体评分流程

## ADDED Requirements

### Requirement: Ranked 实体召回

评分引擎 SHALL 提供 `get_ranked_entities(city_code, entity_type, score_profile, limit)` 函数，返回按 final_score 降序排列的实体列表，供 API 层和行程编排调用。

#### Scenario: 获取 top 20 POI
- **WHEN** 调用 `get_ranked_entities("tokyo", "poi", "general", limit=20)`
- **THEN** 返回东京 POI 按 final_score 降序排列的前 20 条，包含 entity 基本信息和评分明细
