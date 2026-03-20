## ADDED Requirements

### Requirement: data_tier 批量标记工具

系统 SHALL 提供 `scripts/mark_data_tier.py` 脚本，按规则自动标记实体的 data_tier 字段。

规则优先级：
1. 人工确认的实体 → S
2. 有 google_place_id 的实体 → A
3. source="osm" 的实体 → A
4. 其他（纯 AI 生成） → B

#### Scenario: 批量标记城市
- **WHEN** 执行 `python scripts/mark_data_tier.py --city tokyo`
- **THEN** 该城市所有实体按规则标记 data_tier，输出统计 "S: 0, A: 120, B: 180"

### Requirement: entity_media 初始数据

采集流程 SHALL 在写入 entity_base 时，同时将可用的图片 URL 写入 entity_media 表（仅记录 URL，不下载）。

#### Scenario: Google Places 图片 URL 写入
- **WHEN** Google Places API 返回 photos 字段
- **THEN** entity_media 表新增记录，media_type="photo"，url 为 Google Places photo reference URL，source="google_places"

#### Scenario: 无图片时跳过
- **WHEN** 数据源未返回图片信息
- **THEN** 不写入 entity_media 记录，不报错
