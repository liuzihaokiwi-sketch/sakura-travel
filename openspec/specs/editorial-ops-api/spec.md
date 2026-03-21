## ADDED Requirements

### Requirement: Editorial Boost 录入 API

系统 SHALL 提供 `POST /ops/entities/{entity_type}/{entity_id}/editorial-score` 接口，允许运营录入 editorial_boost 和 editorial_label。

请求体 schema：
```json
{
  "boost_value": -8 to +8,
  "label": "recommended|caution|avoid|force_include|force_exclude",
  "reason": "string",
  "tags": ["family_friendly", "photo_spot"],
  "valid_until": "2026-12-31T00:00:00Z" (可选)
}
```

#### Scenario: 录入正向 boost
- **WHEN** POST `/ops/entities/poi/{entity_id}/editorial-score` with `{"boost_value": 5, "label": "recommended", "reason": "东京必去景点"}`
- **THEN** entity_editor_notes 表新增一条记录，note_type="editorial_boost"，boost_value=5，返回 201

#### Scenario: boost 值超出范围
- **WHEN** POST 时 `boost_value` 为 15
- **THEN** 返回 HTTP 422，提示 boost_value 必须在 -8 到 +8 之间

#### Scenario: 实体不存在
- **WHEN** POST 时 entity_id 不存在
- **THEN** 返回 HTTP 404

#### Scenario: 录入后自动触发重新评分
- **WHEN** 成功录入 editorial_boost
- **THEN** 自动将该实体的 `score_entities` job 入队重新计算分数

### Requirement: 按评分排序的实体召回接口

系统 SHALL 提供 `GET /ops/entities/ranked` 接口，返回按 final_score 降序排列的实体列表。

查询参数：city_code, entity_type, score_profile (默认 "general"), limit (默认 50), offset

#### Scenario: 查询东京 POI 排名
- **WHEN** GET `/ops/entities/ranked?city_code=tokyo&entity_type=poi&limit=20`
- **THEN** 返回东京 POI 按 final_score 降序排列的前 20 条，每条包含 entity_id、name_zh、final_score、base_score、editorial_boost、score_breakdown

#### Scenario: 无评分数据
- **WHEN** 查询的城市/类型组合没有 entity_scores 记录
- **THEN** 返回空列表 `{"items": [], "total": 0}`

### Requirement: Data Tier 批量标记

系统 SHALL 提供 `PATCH /ops/entities/{entity_id}/data-tier` 接口和 `scripts/mark_data_tier.py` 脚本，支持单条和批量标记 data_tier。

自动标记规则：
- 有 google_place_id → A
- 有 OSM 来源（source="osm"） → A
- 纯 AI 生成 → B
- 人工确认 → S

#### Scenario: 手动提升为 S 级
- **WHEN** PATCH `/ops/entities/{entity_id}/data-tier` with `{"data_tier": "S"}`
- **THEN** entity_base.data_tier 更新为 "S"，返回 200

#### Scenario: 批量自动标记
- **WHEN** 执行 `python scripts/mark_data_tier.py --city tokyo`
- **THEN** 按规则自动标记该城市所有实体的 data_tier，输出统计（S: x, A: y, B: z）

### Requirement: Editorial Boost 查询

系统 SHALL 提供 `GET /ops/entities/{entity_type}/{entity_id}/editorial-history` 接口，返回该实体的所有 editorial_boost 历史记录。

#### Scenario: 查询编辑历史
- **WHEN** GET `/ops/entities/poi/{entity_id}/editorial-history`
- **THEN** 返回该实体所有 note_type="editorial_boost" 的记录列表，按 created_at 降序排列
