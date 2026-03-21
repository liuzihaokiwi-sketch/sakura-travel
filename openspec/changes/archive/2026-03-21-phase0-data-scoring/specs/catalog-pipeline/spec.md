## ADDED Requirements

### Requirement: Catalog Pipeline 全流程采集

系统 SHALL 提供 `run_city_pipeline(city_code)` 函数，自动选择最优数据源（OSM/Tabelog 真实爬虫 → AI 生成器兜底）采集指定城市的景点、酒店、餐厅数据，写入 entity_base + 扩展表，并为每次采集写入 source_snapshots 追溯记录。

#### Scenario: 采集东京全量数据
- **WHEN** 调用 `run_city_pipeline(session, "tokyo", sync_pois=True, sync_restaurants=True, sync_hotels=True)`
- **THEN** entity_base 表中 city_code="tokyo" 的记录数增加（景点 + 餐厅 + 酒店），source_snapshots 中有对应采集记录，返回统计摘要包含 pois/restaurants/hotels 数量

#### Scenario: 网络不可用时降级 AI 生成
- **WHEN** OSM 和 Tabelog 网络不通
- **THEN** 系统自动使用 AI 生成器产出实体数据，stats.mode 返回 "ai_generator"

#### Scenario: 强制使用 AI 生成器
- **WHEN** 调用时传入 `force_ai=True`
- **THEN** 跳过网络检查，直接使用 AI 生成器

### Requirement: 采集完成后自动触发评分

系统 SHALL 在 `run_city_pipeline()` 成功完成后自动将 `score_entities` job 入队，确保新灌入数据立即有评分。

#### Scenario: 采集后自动入队评分
- **WHEN** `run_city_pipeline("osaka")` 成功完成且写入 >0 条实体
- **THEN** arq 队列中出现 `score_entities` job，参数包含 `city_code="osaka"`

#### Scenario: 采集无新数据时不触发
- **WHEN** `run_city_pipeline()` 写入 0 条实体（全部跳过或失败）
- **THEN** 不入队评分 job

### Requirement: Batch 采集脚本

系统 SHALL 提供 `scripts/crawl.py` 命令行脚本，支持按城市和类型参数化执行采集。

#### Scenario: 命令行采集指定城市
- **WHEN** 执行 `python -m scripts.crawl --city tokyo --type all`
- **THEN** 对东京执行全类型采集并输出统计结果

#### Scenario: 批量采集所有城市
- **WHEN** 执行 `python -m scripts.crawl --city all`
- **THEN** 按顺序采集所有已配置城市（每城市间隔 2s 避免限速）

### Requirement: 采集快照追溯

每次从外部 API 获取的原始返回数据 SHALL 写入 `source_snapshots` 表，包含 source_name、object_type、object_id、raw_payload、expires_at。

#### Scenario: Google Places 采集写入快照
- **WHEN** 通过 Google Places API 采集一条 POI
- **THEN** source_snapshots 表中有一条记录，source_name="google_places"，raw_payload 包含 API 原始返回 JSON

#### Scenario: AI 生成也记录快照
- **WHEN** 通过 AI 生成器生成实体数据
- **THEN** source_snapshots 表中有一条记录，source_name="ai_generator"，raw_payload 包含生成的 JSON
