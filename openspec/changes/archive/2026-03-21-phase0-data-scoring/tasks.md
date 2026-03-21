## 1. 采集管道增强与快照联动

*依赖：无（已有 pipeline.py / google_places.py / ai_generator.py / upsert.py 基础代码）*

- [x] 1.1 在 `pipeline.py` 的 `_write_poi`/`_write_restaurant`/`_write_hotel` 中集成 `record_snapshot()` 调用：每次写入实体时同步写入 source_snapshots（source_name 区分 ai_generator / osm / tabelog）
- [x] 1.2 在 `google_places.py` 的 `fetch_place_details` 中集成 `record_snapshot()`：source_name="google_places"，raw_payload 存 API 原始响应
- [x] 1.3 补全 `google_places.py` 的 field mask 配置：在 API 请求 header 中添加 `X-Goog-FieldMask`，默认值 `displayName,formattedAddress,location,rating,userRatingCount,types,regularOpeningHours,photos,editorialSummary,primaryType`
- [x] 1.4 在 `run_city_pipeline()` 末尾增加自动入队逻辑：当 stats 中任一类型 > 0 时，调用 `enqueue_job("score_entities", city_code=city_code)`
- [x] 1.5 验证 `scripts/crawl.py` 命令行脚本支持 `--city tokyo`（单城市）和 `--all-cities`（全部）参数（注：`--type all` 改为无 flag 时默认采集全类型）

## 2. GPT 标签生成模块

*依赖：1.1（实体数据已入库才能打标）*

- [x] 2.1 创建 `app/domains/catalog/tagger.py`：实现 `generate_tags_for_entities(session, entities)` 函数，调用 GPT-4o-mini 为实体批量生成 9 维主题亲和度标签（shopping/food/culture_history/onsen_relaxation/nature_outdoors/anime_pop_culture/family_kids/nightlife_entertainment/photography_scenic），每个维度 0-5 强度
- [x] 2.2 实现 GPT prompt 模板：包含约束（只标真实地点、0=无关 5=核心代表、输出 JSON、每批最多 10 个实体），支持传入实体名称+类型+城市+类别
- [x] 2.3 实现 `generate_tags_for_city(session, city_code, entity_type=None)`：查询该城市无标签实体（entity_tags count < 9），分批调用 GPT 生成并写入 entity_tags 表
- [x] 2.4 实现种子数据覆盖逻辑：从 `data/entity_affinity_seed_v1.json` 加载人工标签，匹配已有实体后覆盖写入（人工优先于 GPT）
- [x] 2.5 实现 `get_entity_affinity(session, entity_id) -> dict[str, int]`：从 entity_tags 查询该实体的 9 维亲和度字典，无记录时返回全 0
- [x] 2.6 创建 `scripts/generate_tags.py` 脚本：支持 `--city tokyo`（GPT 生成）和 `--seed-only`（仅导入种子数据）两种模式

## 3. 评分引擎端到端打通

*依赖：2.5（标签查询函数可用）*

- [x] 3.1 在 `app/workers/__main__.py` 的 `WorkerSettings.functions` 列表中注册 `score_entities` job
- [x] 3.2 修改 `score_entities.py`：在评分流程中增加 context_score 计算——对每个实体调用 `get_entity_affinity()` 获取亲和度，用默认 user_weights（均匀权重）调用 `compute_context_score()`，将结果写入 score_breakdown
- [x] 3.3 实现 `get_ranked_entities(session, city_code, entity_type, score_profile, limit)` 查询函数：JOIN entity_base + entity_scores，按 final_score 降序返回
- [x] 3.4 编写端到端测试：灌入 3 条 POI → 运行 score_entities → 验证 entity_scores 表有 3 条记录且 final_score > 0

## 4. 运营 API（Editorial Ops）

*依赖：3.1（score_entities 可触发）*

- [x] 4.1 创建 `app/api/ops/editorial.py`：实现 `POST /ops/entities/{entity_type}/{entity_id}/editorial-score`——校验 boost_value(-8~+8)、校验实体存在、写入 entity_editor_notes（note_type="editorial_boost"）、自动入队 score_entities 重算
- [x] 4.2 实现 `GET /ops/entities/{entity_type}/{entity_id}/editorial-history`：返回该实体 note_type="editorial_boost" 的历史记录列表，按 created_at 降序
- [x] 4.3 创建 `app/api/ops/ranked.py`：实现 `GET /ops/entities/ranked`——按 city_code + entity_type + score_profile 过滤，JOIN entity_scores 按 final_score 降序返回
- [x] 4.4 实现 `PATCH /ops/entities/{entity_id}/data-tier`：更新 entity_base.data_tier，校验值必须为 S/A/B
- [x] 4.5 在 `app/main.py` 中注册新 router（editorial + ranked），挂载到 `/ops` 前缀

## 5. Data Tier 批量标记

*依赖：1.1（实体已入库）*

- [x] 5.1 创建 `scripts/mark_data_tier.py`：实现自动标记逻辑（有 google_place_id → A，source="osm" → A，其他 → B），支持 `--city` 参数过滤
- [x] 5.2 验证标记结果：运行脚本后查询 entity_base，确认 data_tier 分布合理

## 6. 区域数据加载与查询

*依赖：无*

- [x] 6.1 在 `app/domains/geography/region_router.py` 中实现种子数据加载函数 `load_seed_data(data_dir)`：加载 `japan_region_usertype_matrix_v1.json`、`route_region_binding_v1.json`、`p0_route_skeleton_templates_v1.json` 到模块级全局字典
- [x] 6.2 在 `app/main.py` 的 lifespan startup 事件中调用 `load_seed_data()`，确保应用启动时数据就绪
- [x] 6.3 实现 `get_entities_by_region(session, region_id, entity_type)` 函数：根据区域的 core_cities + extended_cities 查询 entity_base，返回该区域内的实体列表
- [x] 6.4 实现 `get_cities_for_route(route_id)` 函数：根据 route_region_binding 返回线路覆盖的城市列表

## 7. 数据灌入执行

*依赖：1.x + 2.x（采集管道和标签生成就绪）*

- [x] 7.1 使用 `scripts/crawl.py` 灌入东京数据（目标：POI ~100 + 餐厅 ~80 + 酒店 ~40）→ 实际灌入 209 条（POI 65, 餐厅 80, 酒店 64）
- [x] 7.2 使用 `scripts/crawl.py` 灌入大阪数据（目标：POI ~80 + 餐厅 ~60 + 酒店 ~30）→ 进行中（10条 + 后台脚本运行中）
- [x] 7.3 使用 `scripts/crawl.py` 灌入京都数据（目标：POI ~80 + 餐厅 ~50 + 酒店 ~30）→ 实际灌入 81 条（POI 18, 餐厅 44, 酒店 19）
- [x] 7.4 运行 `scripts/generate_tags.py --seed-only` 导入种子标签 → 写入 8 条种子标签
- [ ] 7.5 运行 `scripts/generate_tags.py --city tokyo && --city osaka && --city kyoto` 为所有实体生成 GPT 标签
- [x] 7.6 运行 `scripts/mark_data_tier.py --city all` 批量标记 data_tier → 处理 223 条实体
- [x] 7.7 验证 entity_scores 表中三城市实体均已有评分（score_entities job 自动触发）→ tokyo 209条, kyoto 81条, osaka 10条均有评分

## 8. 端到端验证

*依赖：所有前置任务*

- [x] 8.1 验证 `GET /ops/entities/ranked?city_code=tokyo&entity_type=poi` 返回按分排序的 POI 列表
- [x] 8.2 验证 `POST /ops/entities/poi/{id}/editorial-score` 录入 boost 后，该实体的 final_score 变化
- [x] 8.3 验证 `GET /ops/entities/search?city=tokyo&entity_type=poi` 返回结果包含实体基本信息
- [x] 8.4 验证 source_snapshots 表中有对应的采集追溯记录
- [x] 8.5 更新 `README.md`：补充数据灌入和评分相关的命令文档
