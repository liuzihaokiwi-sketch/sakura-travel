## ADDED Requirements

### Requirement: 提交行程请求
系统 SHALL 提供 `POST /trips` 端点，接收用户需求（表单字段），创建 `trip_requests` 记录，触发 `normalize_trip_profile` 异步 job，并立即返回 `trip_id` 和初始状态。

#### Scenario: 成功提交行程请求
- **WHEN** 发送 `POST /trips`，body 包含 `destination_country`、`travel_days`、`party_type`、`budget_band` 等必填字段
- **THEN** 返回 HTTP 202，body 包含 `{"trip_id": "<uuid>", "status": "pending"}`，`normalize_trip_profile` job 入队

#### Scenario: 缺少必填字段时拒绝请求
- **WHEN** 发送 `POST /trips`，body 缺少 `travel_days`
- **THEN** 返回 HTTP 422，body 包含 `{"detail": [{"field": "travel_days", "msg": "field required"}]}`

### Requirement: 查询行程状态
系统 SHALL 提供 `GET /trips/{id}/status` 端点，返回当前工作流节点和进度。

#### Scenario: 查询进行中的行程
- **WHEN** 调用 `GET /trips/{id}/status`，该行程正在 normalize 阶段
- **THEN** 返回 HTTP 200，body 包含 `{"trip_id": "...", "status": "normalizing", "step": "normalize_trip_profile"}`

#### Scenario: 查询不存在的行程
- **WHEN** 调用 `GET /trips/{id}/status`，trip_id 不存在
- **THEN** 返回 HTTP 404，body 包含 `{"detail": "Trip not found"}`

### Requirement: trip_profile 标准化
系统 SHALL 将 `trip_requests` 的表单字段映射为结构化 `trip_profiles` JSON，存入数据库，更新行程状态为 `profiled`。

#### Scenario: 标准化成功后画像可查
- **WHEN** `normalize_trip_profile` job 执行完成
- **THEN** `trip_profiles` 表插入对应记录，`trip_requests.status` 更新为 `profiled`，画像包含 `must_have_tags`、`theme_weights` 等字段

#### Scenario: 亲子出行自动推导标签
- **WHEN** 用户输入 `party_type=family_child`
- **THEN** `trip_profiles.must_have_tags` 自动包含 `family_friendly`，`avoid_tags` 自动包含 `late_night`

### Requirement: source_snapshots 追溯机制
系统 SHALL 在每次调用外部 API 时，将原始返回写入 `source_snapshots` 表，包含 `source_name`、`fetched_at`、`expires_at`、`raw_payload`。

#### Scenario: Google Places 调用后快照入库
- **WHEN** 系统调用 Google Places API 查询某 place_id 详情
- **THEN** 原始 JSON 响应写入 `source_snapshots`，`source_name='google_places'`，`expires_at` 设为 90 天后
