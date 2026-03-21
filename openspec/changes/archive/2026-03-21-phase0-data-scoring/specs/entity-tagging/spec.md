## ADDED Requirements

### Requirement: GPT 批量标签生成

系统 SHALL 提供 `app/domains/catalog/tagger.py` 模块，用 GPT-4o-mini 为实体批量生成 9 个主题维度的亲和度标签（0-5 强度），并写入 entity_tags 表。

9 个主题维度：shopping / food / culture_history / onsen_relaxation / nature_outdoors / anime_pop_culture / family_kids / nightlife_entertainment / photography_scenic

#### Scenario: 为一批 POI 生成标签
- **WHEN** 调用 `generate_tags_for_city(session, "tokyo", entity_type="poi")`
- **THEN** 该城市所有无标签的 POI 实体被 GPT 标注，entity_tags 表中写入每个实体 ×9 个维度的记录，tag_score 范围 0-5

#### Scenario: 已有标签的实体跳过
- **WHEN** 实体已有 entity_tags 记录（tag_count >= 9）
- **THEN** 跳过该实体不重复调用 GPT

#### Scenario: 种子数据覆盖 GPT 标签
- **WHEN** `entity_affinity_seed_v1.json` 中有该实体的人工标签
- **THEN** 人工标签覆盖 GPT 生成的标签（人工优先）

### Requirement: 标签批量导入脚本

系统 SHALL 提供 `scripts/generate_tags.py` 脚本，支持命令行执行批量标签生成。

#### Scenario: 命令行生成标签
- **WHEN** 执行 `python scripts/generate_tags.py --city tokyo`
- **THEN** 对东京所有无标签实体执行 GPT 标签生成，输出统计结果

#### Scenario: 导入种子数据
- **WHEN** 执行 `python scripts/generate_tags.py --seed-only`
- **THEN** 仅从 entity_affinity_seed_v1.json 导入种子标签，不调用 GPT

### Requirement: 标签亲和度查询

系统 SHALL 提供函数 `get_entity_affinity(entity_id) -> dict[str, int]`，返回实体在 9 个维度的亲和度字典。

#### Scenario: 查询已标签实体
- **WHEN** 调用 `get_entity_affinity(entity_id)` 且该实体有 9 条 entity_tags 记录
- **THEN** 返回 `{"shopping": 2, "food": 4, "culture_history": 5, ...}` 格式的字典

#### Scenario: 查询无标签实体
- **WHEN** 调用 `get_entity_affinity(entity_id)` 且该实体无 entity_tags 记录
- **THEN** 返回全 0 字典 `{"shopping": 0, "food": 0, ...}`

### Requirement: 标签生成 Prompt 规范

GPT 标签生成 prompt MUST 包含以下约束：
1. 只对真实存在的地点打标
2. 强度 0 = 完全无关，5 = 该维度核心代表
3. 输出 JSON 格式，每个维度一个 0-5 整数
4. 批量处理时每次最多 10 个实体，避免单次 prompt 过长

#### Scenario: Prompt 输出格式验证
- **WHEN** GPT 返回标签结果
- **THEN** 结果为合法 JSON，每个维度值为 0-5 整数，缺失维度补 0
