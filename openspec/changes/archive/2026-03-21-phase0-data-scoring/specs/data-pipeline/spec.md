## ADDED Requirements

### Requirement: Google Places 采集写入快照

每次调用 Google Places API 获取的原始返回数据 SHALL 写入 source_snapshots 表，source_name="google_places"。

#### Scenario: Place Details 采集快照
- **WHEN** 调用 `fetch_place_details(api_key, place_id)` 并成功获取数据
- **THEN** source_snapshots 表新增一条记录，source_name="google_places"，source_object_type="place_detail"，source_object_id=place_id，raw_payload 包含完整 API 响应

### Requirement: AI 生成器采集写入快照

通过 AI 生成器产出的数据 SHALL 写入 source_snapshots 表，source_name="ai_generator"。

#### Scenario: AI 生成 POI 数据快照
- **WHEN** 调用 `generate_pois()` 成功生成数据
- **THEN** source_snapshots 表新增记录，source_name="ai_generator"，source_object_type="poi_batch"，raw_payload 包含 GPT 返回的原始 JSON

### Requirement: Google Places Field Mask 配置

Google Places API 调用 MUST 使用 field mask 控制返回字段，避免不必要的成本。

默认 field mask：`displayName,formattedAddress,location,rating,userRatingCount,types,regularOpeningHours,photos,editorialSummary,primaryType`

#### Scenario: 使用 field mask 采集
- **WHEN** 调用 Google Places Place Details API
- **THEN** 请求中包含 field mask 参数，只返回指定字段

## MODIFIED Requirements

### Requirement: 采集流程集成快照

数据管道的采集流程 SHALL 在写入 Catalog 主档的同时写入 source_snapshots。

```
1. 按城市+类型调用数据源
2. 获取原始返回数据
3. 写入 source_snapshots（原始追溯）
4. 归一化后写入 entity_base + 扩展表
5. GPT 辅助打标签 → entity_tags
6. 自动触发 score_entities job
```

#### Scenario: 完整采集流程
- **WHEN** 执行 `run_city_pipeline("kyoto")`
- **THEN** entity_base 有新增记录，source_snapshots 有对应快照，score_entities job 已入队
