## ADDED Requirements

### Requirement: arq Worker 启动与 Job 注册
系统 SHALL 提供基于 arq 的 Worker 进程，支持独立启动（`python -m app.workers`），可在不重启 API 服务的情况下单独重启 Worker。所有 Queue Job 函数 MUST 在 `WorkerSettings.functions` 中注册。

#### Scenario: Worker 独立启动
- **WHEN** 运行 `python -m app.workers`
- **THEN** arq Worker 进程启动，连接 Redis，日志输出已注册的 job 列表，等待任务入队

#### Scenario: 未注册的 Job 不被执行
- **WHEN** 向 Redis 入队一个未在 `WorkerSettings.functions` 中注册的 job 名
- **THEN** Worker 日志输出 `Unknown job function`，任务标记为失败，不抛出未捕获异常

### Requirement: normalize_trip_profile Job
系统 SHALL 实现 `normalize_trip_profile` 异步 job，从 `trip_requests` 读取表单数据，生成结构化画像写入 `trip_profiles`，并更新 `trip_requests.status`。

#### Scenario: Job 成功执行
- **WHEN** `normalize_trip_profile` job 被 Worker 消费，`trip_requests` 中对应记录存在
- **THEN** `trip_profiles` 新增记录，`trip_requests.status` 更新为 `profiled`，job 标记为成功

#### Scenario: Job 失败后自动重试
- **WHEN** `normalize_trip_profile` job 执行过程中抛出异常（如数据库超时）
- **THEN** arq 按退避策略最多重试 3 次，重试耗尽后 `trip_requests.status` 更新为 `failed`，错误信息记录到日志

### Requirement: Job 执行结果可追溯
每个 Job 执行 MUST 记录开始时间、结束时间、成功/失败状态和错误信息（如有），可通过 `trip_requests` 表的 `last_job_run_at`、`last_job_error` 字段查到。

#### Scenario: 查询失败原因
- **WHEN** `GET /trips/{id}/status` 返回 `status=failed`
- **THEN** response body 包含 `{"error_summary": "<最后一次 job 的错误信息前 200 字符>"}`
