## Why

当前评分体系（system_score + context_score + editorial_boost）只解决"硬事实排序"——谁评分高、谁离得近、谁更匹配主题。但用户愿不愿意为免费 Day 1 付费、用了之后会不会复购/转介绍，核心驱动力是**软价值**：氛围感、懂我感、顺滑感、分享欲、记忆点。如果把这些写成大量 if-else，只会越来越脆且难以校准。

外部信号也验证了这个方向：JNTO 统计库将游客拆成"同行人、预订方式、住宿、地区访问率、消费"等维度而非通用模型；Dragon Trail 2025 调研显示 50% 中国出境游客从中文社交媒体获得灵感、64% 主要为放松休闲、40% 为深入体验当地文化。软规则最该围绕的不是"写得更文艺"，而是：**放松感、文化沉浸感、分享感、确定感、顺滑感**。

现在系统已有三层评分、模板装配、护栏检查、免费 Day 1 预览、审核发布和结构化修改入口——具备将软规则挂到各层的基础条件。**现在做**是因为 Phase 1 行程引擎即将上线，在 19.9 基础版交付之前把软规则植入，可以让免费 Day 1 的转付费率从第一批用户开始就有保障。

### 在产品价位梯度中的作用

- **19.9 基础版**：软规则提升免费 Day 1 杀伤力和付费转化率，是引流款从"能用"到"想买"的关键
- **69-199 利润款**：软规则权重包按客群差异化，让半定制攻略真正"懂我"
- **高客单版**：软规则校准数据积累后，支撑高端版的个性化推荐和专业判断感

## What Changes

### 新增能力

- 设计 12 个软规则评分维度（emotional_value / shareability / relaxation_feel / memory_point / localness / smoothness / food_certainty / night_completion / recovery_friendliness / weather_resilience_soft / professional_judgement_feel / preview_conversion_power），每个维度 0-10 分
- 设计客群权重包系统（couple / besties / friends_small_group / parents / family_child / first_time_fit / repeat_fit），不预设哪个客群优先
- 设计套餐/阶段权重包（preview_day1 / standard / premium / self_serve_tuning），每个阶段不同的软规则优先级
- 设计免费 Day 1 专用软规则引擎——不是完整版第一天的简单截取，而是主动选"最能成交的一天"
- 设计自助微调专用软规则引擎——替换候选排序、局部重排、防崩逻辑
- 设计软规则计算管线——从候选排序到 preview_day1_score / self_serve_swap_score / editorial_polish_priority
- 设计校准与学习机制——用户行为反哺、A/B test 框架、埋点规范
- 提供 v1 推荐种子值（默认权重 + 各客群 pack + 各阶段 pack），即使无全量数据也能启动

### 核心设计原则

- 软规则 ≠ if-else，而是"可调的评分维度 + 客群权重包 + 场景重写器"
- 优先级：免费转付费 > 喜欢度/满意度/复购/转介绍 > 减少人工介入 > token 成本
- 必须数据化、表结构化、排序化，尽量不依赖人工一条条维护

## Capabilities

### New Capabilities

- `soft-rule-dimensions`: 12 个软规则评分维度定义、评估方法、生效阶段、默认权重种子
- `segment-weight-packs`: 客群权重包系统——每个客群的核心目标、维度权重、Day 1 触发点、复购触发点、微调敏感模块
- `stage-weight-packs`: 套餐/阶段权重包——preview_day1 / standard / premium / self_serve_tuning 各阶段的维度优先级差异
- `preview-soft-engine`: 免费 Day 1 专用软规则引擎——选天逻辑、预览专属评分公式、模块露出/锁定策略、CTA 联动
- `swap-soft-engine`: 自助微调专用软规则引擎——替换候选排序、局部重排、整体体验保底、防改崩机制
- `soft-rule-pipeline`: 软规则计算管线——从维度分计算到多维聚合到结果回写的完整流程、缓存策略
- `soft-rule-calibration`: 校准与学习机制——用户行为反向验证、付费率反哺、A/B test 框架、埋点规范

### Modified Capabilities

- `scoring-engine`: 在现有 system_score + context_score + editorial_boost 基础上，新增 soft_rule_score 层，修改 final_score 合成公式
- `itinerary-planner`: 行程装配逻辑需要接入软规则维度分，影响日程安排和实体选择
- `review-gate`: 审核流程增加软规则维度的可解释性输出（为什么选了这些内容）

## Impact

### 代码变更

- 新增 `app/domains/ranking/soft_rules/` — 软规则评分系统核心
  - `dimensions.py` — 12 维度定义与计算
  - `weight_packs.py` — 客群 + 阶段权重包
  - `pipeline.py` — 软规则计算管线
  - `preview_engine.py` — 免费 Day 1 软规则引擎
  - `swap_engine.py` — 自助微调软规则引擎
  - `calibration.py` — 校准与学习
- 修改 `app/domains/ranking/scorer.py` — 集成 soft_rule_score
- 修改 `app/domains/planning/` — 装配逻辑接入软规则
- 新增 `data/seeds/soft_rule_seeds.json` — v1 种子数据

### 数据库

- 新增表：soft_rule_dimensions / segment_weight_packs / stage_weight_packs / city_context_soft_scores / preview_trigger_scores / swap_candidate_soft_scores / editorial_seed_overrides / soft_rule_explanations / soft_rule_feedback_log
- 修改表：entity_scores 增加 soft_rule_score 字段

### 外部依赖

- OpenAI GPT-4o-mini（部分维度的 AI 估计，如 emotional_value / localness）
- 无新外部 API 依赖

### MVP 优先级

| 优先级 | 能力 | 理由 |
|--------|------|------|
| P0 必须 | soft-rule-dimensions + segment-weight-packs + stage-weight-packs | 基础维度和权重是所有后续模块的前提 |
| P0 必须 | soft-rule-pipeline | 没有计算管线，维度定义无法生效 |
| P0 必须 | preview-soft-engine | Day 1 转付费是当前最核心商业目标 |
| P1 重要 | swap-soft-engine | 自助微调影响用户满意度和修改次数 |
| P1 重要 | scoring-engine 集成 | 让软规则分参与实际排序 |
| P2 可延后 | soft-rule-calibration | 先用种子值跑起来，有用户数据后再做校准 |
