## ADDED Requirements

### Requirement: 软规则计算管线端到端流程

系统 SHALL 实现一条完整的软规则计算管线（pipeline），从实体数据到最终评分输出，流程为：

1. **读取城市实体和上下文**：从 entity_base + entity_tags + entity_media 读取实体数据
2. **硬约束过滤**：排除已关闭/永久歇业/数据质量 tier=C 的实体（此步复用现有硬规则系统，pipeline 不重新实现）
3. **计算 12 维度软规则分**：对每个通过过滤的实体，按维度来源（AI/统计/seed）分别计算
4. **写入 entity_soft_scores**：批量 UPSERT 维度分到数据库
5. **按需聚合**：在行程装配/预览/微调时，按当前客群和阶段权重包实时聚合 soft_rule_score

#### Scenario: 全量 pipeline 执行

- **WHEN** 运行 `score_soft_rules` job 且参数为 city_code="tokyo", mode="full"
- **THEN** 东京所有活跃实体的 12 维度软规则分被计算并写入 entity_soft_scores，耗时 SHOULD < 10 分钟

#### Scenario: 增量 pipeline 执行

- **WHEN** 运行 `score_soft_rules` job 且参数为 city_code="tokyo", mode="incremental"
- **THEN** 只处理 entity_base.updated_at > entity_soft_scores.calculated_at 的实体

### Requirement: 聚合评分输出

pipeline 的聚合阶段 SHALL 输出以下 4 种评分：

1. **itinerary_rank_score**：行程级排序分，用于模板装配时选择实体
   ```
   itinerary_rank_score = 0.45 × system_score + 0.30 × context_score + 0.25 × soft_rule_score(segment, "standard") - risk_penalty
   ```

2. **preview_day1_score**：预览选天分，用于免费 Day 1 选天引擎
   ```
   preview_day1_score = 按 preview-soft-engine spec 中的公式
   ```

3. **self_serve_swap_score**：微调替换分，用于自助微调候选排序
   ```
   self_serve_swap_score = 按 swap-soft-engine spec 中的 swap_score 公式
   ```

4. **editorial_polish_priority**：编辑润色优先级，用于人工审核时标识需要重点关注的实体
   ```
   editorial_polish_priority = 实体的 professional_judgement_feel < 5.0 ? "high" : 
                               实体的 professional_judgement_feel < 7.0 ? "medium" : "low"
   ```

#### Scenario: 装配时获取排序分

- **WHEN** 行程装配引擎请求东京 top 20 POI
- **THEN** 返回按 itinerary_rank_score 降序排列的 POI 列表，每个包含分项明细

#### Scenario: 审核时获取润色优先级

- **WHEN** 审核人员查看行程中的实体列表
- **THEN** 每个实体标注 editorial_polish_priority（high/medium/low）

### Requirement: 缓存策略

pipeline SHALL 实现以下缓存策略避免全量重算：

1. **entity_soft_scores**：写入数据库，作为主缓存，TTL = 7 天（每周批量刷新一次）
2. **聚合分 Redis 缓存**：`soft_rule:{entity_type}:{entity_id}:{segment}:{stage}` → 聚合分值，TTL = 1 小时
3. **权重包 Redis 缓存**：`weight_pack:{type}:{pack_id}` → 完整权重包 JSON，TTL = 24 小时，权重包更新时主动失效

当权重包被更新时，系统 SHALL 主动清除对应的 Redis 聚合分缓存（因为聚合公式依赖权重包）。

#### Scenario: 缓存命中

- **WHEN** 同一实体在 1 小时内被多次请求聚合分
- **THEN** 第一次从数据库计算，后续从 Redis 读取，延迟 < 5ms

#### Scenario: 权重包更新后缓存失效

- **WHEN** 管理员更新 couple 权重包
- **THEN** 所有 `soft_rule:*:*:couple:*` 的 Redis 缓存被清除，下次请求重新计算

### Requirement: 模块边界与函数签名

pipeline SHALL 由以下独立模块组成：

```python
# app/domains/ranking/soft_rules/dimensions.py
def get_soft_rule_dimensions() -> list[SoftRuleDimension]: ...
def compute_dimension_score(entity: Entity, dimension: SoftRuleDimension) -> DimensionScore: ...

# app/domains/ranking/soft_rules/weight_packs.py
def get_segment_weight_pack(pack_id: str) -> WeightPack: ...
def get_stage_weight_pack(pack_id: str) -> WeightPack: ...
def aggregate_soft_rule_score(dimension_scores: dict, segment_pack: WeightPack, stage_pack: WeightPack) -> float: ...

# app/domains/ranking/soft_rules/pipeline.py
async def run_soft_rule_pipeline(city_code: str, mode: str = "full") -> PipelineResult: ...
async def compute_entity_soft_scores(entity_id: UUID, entity_type: str) -> EntitySoftScores: ...

# app/domains/ranking/soft_rules/preview_engine.py
def select_preview_day(plan: ItineraryPlan, segment_pack: WeightPack) -> PreviewDayResult: ...

# app/domains/ranking/soft_rules/swap_engine.py
def rank_swap_candidates(plan: ItineraryPlan, target_entity_id: UUID, segment_pack: WeightPack) -> list[SwapCandidate]: ...
def validate_swap_impact(plan: ItineraryPlan, original_id: UUID, replacement_id: UUID) -> SwapImpact: ...
```

#### Scenario: 模块独立可测

- **WHEN** 单独运行 dimensions.py 的单元测试
- **THEN** 不依赖数据库或外部 API（可 mock），所有测试通过

#### Scenario: pipeline 可增量扩展

- **WHEN** 未来增加第 13 个软规则维度
- **THEN** 只需修改 dimensions.py 添加维度定义 + 修改权重包的 JSON，不需要改 pipeline.py 或聚合逻辑
