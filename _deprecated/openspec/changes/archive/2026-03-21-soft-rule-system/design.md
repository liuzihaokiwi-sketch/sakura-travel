## Context

当前系统的评分架构是两阶段模型：

1. **阶段 1 候选排序分**：`candidate_score = 0.60 × system_score + 0.40 × context_score - risk_penalty`
2. **阶段 2 编辑修正分**：`final_entity_score = candidate_score + editorial_boost`

其中 system_score 已实现 6 维度加权（评分口碑/评论量/热度/主题匹配/区域串联/新鲜度），editorial_boost ±8 已实现，context_score 是 P0 待办。行程级别有独立的 itinerary_score 公式。

软规则系统要在这个已有架构上**叠加一层**，不是替换。它的本质是把"什么叫更讨喜、更值得付费、更值得分享"这些主观感受量化为可计算、可排序、可校准的维度分。

### 当前系统已有的基础设施

- entity_scores 表：存储每个实体的评分记录和明细
- entity_editor_notes 表：存储编辑修正（boost / label / tags / theme_affinity）
- entity_tags 表：9 维主题标签（shopping / food / culture / nature / onsen / photo_spots / comfort / art / anime / nightlife）
- score_entities arq Job：批量评分任务
- 行程编排引擎（Phase 1 设计中）：模板 + 评分 → 结构化行程 JSON
- 免费 Day 1 预览机制（产品设计已有）
- 自助微调结构化修改入口（产品设计已有）

## Goals / Non-Goals

**Goals:**

- 设计 12 个软规则评分维度，每个维度有明确的计算方法、生效阶段、默认权重
- 让软规则以"评分维度 + 权重包 + 场景重排"的形式嵌入现有评分/编排管线，而非 if-else
- 让免费 Day 1 预览能通过软规则主动选"最能成交的一天"
- 让自助微调的替换候选排序考虑软规则，避免用户一改就把整体体验改崩
- 用 v1 种子值让系统能无数据冷启动，后续通过用户行为校准
- 所有软规则分可解释、可版本化、可回放

**Non-Goals:**

- 不重新设计硬规则体系（时间冲突/交通不可达/闭馆 等已有护栏检查管辖）
- 不做实时个性化推荐引擎（v1 是静态权重包 + 批量预计算）
- 不做 AI 文案风格的软规则（AI copywriter 层另行设计）
- 不做全量 A/B test 平台建设（v1 只需要埋点 + 简单分桶）
- 不做多语言软规则适配（v1 只面向中文用户）

## Decisions

### Decision 1：软规则分作为独立层叠加，而非替换现有评分

**选择**：新增 `soft_rule_score` 作为独立维度，修改合成公式为：
```
candidate_score = 0.45 × system_score + 0.30 × context_score + 0.25 × soft_rule_score - risk_penalty
final_entity_score = candidate_score + editorial_boost
```

**为什么不直接把软规则揉进 context_score**：
- context_score 是"用户画像 × 实体标签"的主题匹配分，是事实性的
- soft_rule_score 是"这个实体/这段行程是否讨喜"的感受性分，来源和校准方式不同
- 分离后可独立 A/B test 软规则权重，不影响主题匹配逻辑
- 后续若软规则效果不好，可以把权重调到 0 回退

**替代方案考虑**：
- 方案 B：把软规则加到 editorial_boost 里 → 拒绝，因为 editorial_boost 是人工修正，±8 范围太小
- 方案 C：用 softmax 而非线性加权 → 过早优化，v1 先线性

### Decision 2：软规则维度分存储在实体级和行程级两层

**选择**：
- **实体级软规则分**：存在 `entity_soft_scores` 表，每个实体一行，12 维度各一个 0-10 分，由 batch job 预计算
- **行程级软规则分**：在行程装配时实时聚合，不单独存表（因为是权重包 × 实体分的加权平均，计算量小）

**为什么不全实时算**：
- 实体数量多（~800 per city），如果每次生成行程都重算所有实体的 12 维度，延迟不可接受
- 实体级维度分变化频率低（跟实体本身属性绑定），适合批量预计算 + 缓存
- 行程级聚合只涉及 shortlist 内的 ~30 个实体，可以实时

### Decision 3：权重包存 JSONB，不做关系范式

**选择**：segment_weight_packs 和 stage_weight_packs 各存为一张表，每行一个 pack，weights 字段是 JSONB 存 12 维度权重。

**为什么不拆成维度×权重包的关系表**：
- 维度数量固定（12 个），不会频繁增减
- 一个权重包的 12 个权重语义上是一个整体，修改时必须一起看
- JSONB 查询在 PostgreSQL 中性能完全够用
- 后续加维度时只需要 migration 默认值，不需要改关系

### Decision 4：免费 Day 1 不固定展示第一天，而是选 preview_day1_score 最高的一天

**选择**：从完整行程的 N 天中，计算每天的 `preview_day1_score`，选得分最高的一天作为免费预览。

**preview_day1_score 公式**：
```
preview_day1_score = 0.30 × avg_entity_soft_score_of_day
                   + 0.25 × variety_score        # 当天实体类型丰富度
                   + 0.20 × hero_moment_score     # 是否有明确的高光时刻
                   + 0.15 × shareability_score    # 当天平均分享感
                   + 0.10 × completeness_score    # 餐饮/夜间是否完整
```

**为什么不固定第一天**：
- 用户的实际第一天往往是到达日，时间碎片化，可能不够精彩
- 选最精彩的一天展示，更容易触发"这个攻略真懂我"的感觉
- 但必须加护栏：选出的天必须是"自包含的"（不需要前一天的前置体验才能理解）

### Decision 5：自助微调作为受约束的重排序系统

**选择**：用户请求替换某个实体时，系统不是给随机替代，而是：
1. 从候选池中筛选满足硬约束的替代实体
2. 按 `swap_score` 排序，取 top 3-5 展示给用户
3. 用户选择后，局部重排当天行程（调整时间/交通），但不重排其他天
4. 检查替换后整体行程的 itinerary_soft_score 是否跌幅超过阈值（>15%），若是则警告

**swap_score 公式**：
```
swap_score = 0.40 × context_fit          # 和原实体的场景适配度匹配
           + 0.25 × soft_rule_score      # 软规则分
           + 0.20 × slot_compatibility   # 时间/位置/类型兼容性
           + 0.15 × differentiation      # 和被替换实体的差异度（避免推荐太相似的）
```

### Decision 6：v1 种子值来源分三档

| 来源 | 维度 | 理由 |
|------|------|------|
| 人工 seed | emotional_value / memory_point / localness / professional_judgement_feel | 这 4 个维度最依赖主观判断，AI 估计不稳定 |
| AI 估计 | shareability / relaxation_feel / food_certainty / night_completion / weather_resilience_soft | 这 5 个维度可通过实体属性和标签推断 |
| 统计特征 | smoothness / recovery_friendliness / preview_conversion_power | 这 3 个维度可通过地理/交通/价格数据算 |

v1 先统一用 AI 估计 + 默认种子顶上所有维度，后续按此分档逐步校准。

## Risks / Trade-offs

### [风险] 12 维度全部预计算的冷启动成本

→ **缓解**：v1 只对已入库的 ~800 实体（三城市）计算，用 batch job 一次性跑完，后续增量计算。第一次全量计算约 800 × 12 = 9600 次评估，用 GPT-4o-mini 批量跑约 $2-5，可接受。

### [风险] 软规则权重全部是拍脑袋的种子值

→ **缓解**：这是已知的 v1 限制。种子值设计为表配置，不硬编码，可随时调整。Phase 1 结束后有真实用户数据再校准。最值得先校准的 4 个维度：preview_conversion_power / shareability / relaxation_feel / food_certainty。

### [风险] 免费 Day 1 选天逻辑可能导致"预览太精彩，正式版反而失望"

→ **缓解**：preview_day1_score 的设计会同时考虑"代表性"——不能把全部高光都放在预览天。正式版每天的 avg_soft_score 应该也在 6+ 以上。后续通过"预览天 vs 全行程均分"比值设上限。

### [风险] candidate_score 公式改动影响现有排序

→ **缓解**：
1. soft_rule_score 权重 0.25 初始可调低到 0.10 灰度上线
2. 新公式和旧公式可同时计算对比
3. 有 score_version 字段可追溯

### [风险] 自助微调的"防改崩"检查增加延迟

→ **缓解**：局部重排只涉及当天 ~5-8 个实体，itinerary_soft_score 计算量极小（<50ms）。阈值检查是纯数值比较。

## Open Questions

1. **preview_day1 是否需要支持"选半天"**——有些行程可能没有单独一整天特别精彩，选最精彩的半天 + 锁住另外半天可能效果更好？
2. **客群权重包的初始覆盖范围**——v1 是否需要覆盖全部 7 个客群，还是先做 3-4 个最常见的（couple / first_time_fit / family_child）？
3. **AI 估计维度分的 prompt 设计**——是用一次 prompt 批量评估 12 维度，还是分维度评估以提高稳定性？trade-off 是 token 成本 vs 评估质量。
4. **editorial_seed_overrides 的录入 UI**——是否需要在管理后台增加软规则分手动修正入口，还是 v1 先通过 JSON 文件导入？
