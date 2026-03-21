# 全局任务并行执行 + AI 分级方案

> 汇总所有 active changes 的未完成任务，按并行组 + AI 等级规划
> 更新时间：2026-03-21

---

## AI 等级定义

| 等级 | 代号 | 适用场景 | 代表模型 |
|------|------|----------|----------|
| 🟢 **L** (低级) | Copilot级 | 模板代码、ORM/Migration、CRUD API、seed 脚本、简单组件、文档填充、配置文件 | GPT-4o-mini / Cursor Tab / Copilot |
| 🟡 **M** (中级) | 工程师级 | 有业务逻辑的 service、需理解上下文的 API、前端交互组件、测试编写、集成调试 | GPT-4o / Claude Sonnet |
| 🔴 **H** (高级) | 架构师级 | 核心算法、多系统集成、Prompt 工程、评分公式设计、端到端流程编排、产品决策 | Claude Opus / GPT-4o (深度思考) |

**判断原则**：
- 如果任务的 spec/design 文档已经写到"复制粘贴就能实现"的程度 → 🟢 L
- 如果需要理解 2-3 个文件的上下文才能正确实现 → 🟡 M  
- 如果需要理解整个系统架构、做权衡决策、或写 LLM prompt → 🔴 H

---

## 任务来源汇总

| Change | 未完成任务数 | 主要内容 |
|--------|-------------|----------|
| `system-closure-v1` | 26 | 预览引擎/自助微调/City Context/权重包/多Agent评审/反馈/评测 |
| `soft-rule-system` | ~60 | 12维软规则/权重包/预览选天/自助微调引擎/埋点/校准 |
| `strategic-upgrade` | 29 | 产品真相源/质量门控/Day1标杆/免费预览/微调MVP/多模型评审 |
| `product-conversion-redesign` | ~8 | C4导出/F1-F4集成验证/文案审查 |
| `phase1-trip-engine` | ~3 | PDF验证/多场景攻略生成 |
| `phase0-data-scoring` | 1 | GPT标签全量生成 |
| `all-remaining-tasks` | ~35 | 管理后台/数据补全/文档填充/导出/收尾 |
| `repo-restructure` | 文档已完成 | 执行阶段：data重组/README/安全扫尾 |

---

## ⚠️ 重叠任务合并

以下任务在多个 change 中重复定义，**只做一次**，以最详细的 spec 为准：

| 重叠主题 | 涉及 changes | 合并到 | 最详细 spec |
|----------|-------------|--------|------------|
| 权重包表+resolver | system-closure-v1 T0.3 ≈ soft-rule-system 1.4+1.5+3.x | soft-rule-system | soft-rule-system（12维+7客群+4阶段） |
| Preview Engine 选天 | system-closure-v1 T1.2-T1.4 ≈ soft-rule-system 7.x | soft-rule-system | soft-rule-system（含5维分项+护栏） |
| 自助微调引擎 | system-closure-v1 T2.1-T2.3 ≈ soft-rule-system 8.x ≈ strategic T10-T14 | soft-rule-system | soft-rule-system（含slot_compat+differentiation） |
| City Context 表 | system-closure-v1 T0.1 ≈ strategic T18-T21 | system-closure-v1 | system-closure-v1（6张表完整定义） |
| product_config 表 | system-closure-v1 T0.2 ≈ strategic T1 | system-closure-v1 | system-closure-v1（含JSONB schema） |
| 多模型评审 | system-closure-v1 T3.x ≈ strategic T22-T25 | system-closure-v1 | system-closure-v1（含并行架构+token预算） |
| 反馈埋点 | system-closure-v1 T4.x ≈ soft-rule-system 11.x | soft-rule-system | soft-rule-system（含A/B实验分组） |
| 管理后台 | all-remaining 1.x ≈ strategic T3-T4 | all-remaining | all-remaining（含详细提示词） |

**合并后实际独立任务总数：~80 个**

---

## 并行执行组

### 🔵 Wave 0：无依赖基础层（可开 5 个 AI 窗口）

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  窗口 A      │  │  窗口 B      │  │  窗口 C      │  │  窗口 D      │  │  窗口 E      │
│  DB Schema   │  │  Seed数据    │  │  前端后台     │  │  文档体系     │  │  工具+治理    │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
```

#### 窗口 A — DB Schema & Migration 🟢L
> 纯模板工作，design.md 已给出完整字段定义

| # | 任务 | 来源 | AI级 |
|---|------|------|------|
| A1 | 创建 6 张 City Context 表 ORM + Migration | closure T0.1 | 🟢L |
| A2 | 创建 product_config 表 ORM + Migration + Pydantic schema | closure T0.2 | 🟢L |
| A3 | ALTER entity_scores 增加 preview_score + context_score | closure T0.4 | 🟢L |
| A4 | ALTER itinerary_items 增加 swap_candidates JSONB | closure T0.5 | 🟢L |
| A5 | 创建 entity_soft_scores 表（12维度列）| soft-rule 1.1 | 🟢L |
| A6 | 创建 editorial_seed_overrides 表 | soft-rule 1.2 | 🟢L |
| A7 | 创建 soft_rule_explanations 表 | soft-rule 1.3 | 🟢L |
| A8 | 创建 segment_weight_packs + stage_weight_packs 表 | soft-rule 1.4+1.5 | 🟢L |
| A9 | 创建 preview_trigger_scores 表 | soft-rule 1.6 | 🟢L |
| A10 | 创建 swap_candidate_soft_scores 表 | soft-rule 1.7 | 🟢L |
| A11 | 创建 soft_rule_feedback_log 表 | soft-rule 1.8 | 🟢L |
| A12 | 修改 entity_scores 增加 soft_rule_score 等 4 字段 | soft-rule 1.9 | 🟢L |
| A13 | 所有新表的 SQLAlchemy ORM 模型文件 | soft-rule 1.10 | 🟢L |
| A14 | 创建 feature_flags 表 + is_feature_enabled() | closure T5.3 | 🟢L |
| A15 | 创建 user_events 表 | closure T4.1(部分) | 🟢L |

#### 窗口 B — Seed 数据 & 维度定义 🟢L~🟡M
> 大部分是照着 JSON 模板写，少量需要理解业务语义

| # | 任务 | 来源 | AI级 |
|---|------|------|------|
| B1 | product_config 3个SKU seed 脚本 | closure T0.2 | 🟢L |
| B2 | Tokyo Top50 实体 timeslot_rules seed | closure T0.1 | 🟡M（需查实际营业数据）|
| B3 | Tokyo Top50 实体 entity_operating_facts seed | closure T0.1 | 🟡M（需查实际营业数据）|
| B4 | Tokyo Top50 实体 audience_fit seed（4客群）| closure T0.1 | 🟡M（需理解客群匹配）|
| B5 | 12维软规则 dimensions.py 定义 + 校验函数 | soft-rule 2.2+2.3 | 🟡M |
| B6 | soft_rule_seeds.json（12维默认权重）| soft-rule 2.4 | 🟢L |
| B7 | 7个客群权重包 seed → segment_weight_packs | soft-rule 2.5 | 🟡M（需理解客群差异）|
| B8 | 4个阶段权重包 seed → stage_weight_packs | soft-rule 2.6 | 🟡M |
| B9 | GPT 标签全量生成（tokyo/osaka/kyoto）| phase0 7.5 | 🟢L（运行现有脚本）|
| B10 | preview_score 批量初始化脚本 | closure T0.4 | 🟡M |

#### 窗口 C — 管理后台 + 审核 API 🟡M
> 需要理解前后端联动，但模式固定

| # | 任务 | 来源 | AI级 |
|---|------|------|------|
| C1 | Admin 密码保护中间件 | remaining 1.1 | 🟢L |
| C2 | 订单看板 /admin | remaining 1.2 | 🟡M |
| C3 | 单订单审核页 /admin/order/[id] | remaining 1.3 | 🟡M |
| C4 | 修改请求 API | remaining 1.4 | 🟡M |
| C5 | 审核操作 API | remaining 1.5 | 🟡M |

#### 窗口 D — 文档体系 🟢L
> 纯文档写作，读代码后填充

| # | 任务 | 来源 | AI级 |
|---|------|------|------|
| D1 | docs-human/ 10份文档填充 | remaining 4.1 | 🟢L |
| D2 | docs-ai/ 10份文档填充 | remaining 4.2 | 🟢L |
| D3 | README + CONTRIBUTING + CODEOWNERS | remaining 2.7 | 🟢L |
| D4 | 软规则系统 README | soft-rule 13.3 | 🟢L |
| D5 | 全站文案审查报告 | remaining 4.4 | 🟡M（需品牌理解）|

#### 窗口 E — 工具 & 仓库治理 🟢L~🟡M
> 脚本为主

| # | 任务 | 来源 | AI级 |
|---|------|------|------|
| E1 | batch_translate.py（DeepL翻译脚本）| remaining 2.2 | 🟢L |
| E2 | AI 模型分层配置 | remaining 2.3 | 🟢L |
| E3 | AI 调用缓存中间件 ai_cache.py | remaining 2.4 | 🟡M |
| E4 | 安全扫尾（.env历史清理+pre-commit）| remaining 2.5 | 🟢L |
| E5 | data/ 目录重组 | remaining 2.6 | 🟢L |
| E6 | structlog 集成 | remaining 5.5 | 🟢L |
| E7 | tenacity 重试替换 | remaining 5.6 | 🟢L |

---

### 🟣 Wave 1：核心 Service 层（等 Wave 0 完成，可开 4 个 AI 窗口）

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  窗口 F       │  │  窗口 G       │  │  窗口 H       │  │  窗口 I       │
│  软规则计算    │  │  预览引擎      │  │  Product API  │  │  前端组件      │
│  🔴H          │  │  🔴H          │  │  🟡M          │  │  🟡M          │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
```

#### 窗口 F — 软规则计算引擎 🔴H
> 核心算法，需理解评分体系+Prompt工程+融合逻辑

| # | 任务 | 来源 | AI级 |
|---|------|------|------|
| F1 | 权重包管理模块 weight_packs.py | soft-rule 3.1-3.4 | 🟡M |
| F2 | AI 估计器（GPT-4o-mini 12维评分）| soft-rule 4.1 | 🔴H（Prompt工程）|
| F3 | 统计特征计算器 | soft-rule 4.2 | 🟡M |
| F4 | 人工 seed 读取器 | soft-rule 4.3 | 🟢L |
| F5 | 维度分融合逻辑（manual>stat>ai）| soft-rule 4.4 | 🔴H（优先级设计）|
| F6 | 可解释性记录 | soft-rule 4.5 | 🟢L |
| F7 | 软规则计算 pipeline（全量/增量）| soft-rule 5.1-5.5 | 🔴H |
| F8 | 评分引擎集成（三维公式+退化）| soft-rule 6.1-6.4 | 🔴H |

#### 窗口 G — 预览引擎 🔴H
> 核心成交机制，需理解转化心理+评分公式

| # | 任务 | 来源 | AI级 |
|---|------|------|------|
| G1 | Preview Score Calculator（5维公式）| closure T1.2 / soft-rule 7.1 | 🔴H |
| G2 | Preview Validator（5条校验）| closure T1.3 | 🟡M |
| G3 | 选天护栏（到达日降权/自包含性）| soft-rule 7.2 | 🔴H |
| G4 | Preview Engine 主流程 + 降级 | closure T1.4 / soft-rule 7.3 | 🔴H |
| G5 | 模块露出/锁定策略配置 | soft-rule 7.4 | 🟡M |
| G6 | CTA 触发点插入逻辑 | soft-rule 7.5 | 🟡M |

#### 窗口 H — Product Config API + 事件 API 🟡M
> 标准 CRUD，但需理解 SKU 权益模型

| # | 任务 | 来源 | AI级 |
|---|------|------|------|
| H1 | GET /products + /products/{sku_id} | closure T1.1 | 🟡M |
| H2 | GET /products/{sku_id}/preview-rules | closure T1.1 | 🟡M |
| H3 | POST /events 埋点接收 API | closure T4.1 | 🟢L |
| H4 | 质量校验门控（11条规则）| strategic T5 | 🔴H |

#### 窗口 I — 前端组件 🟡M
> UI组件，需理解设计语言

| # | 任务 | 来源 | AI级 |
|---|------|------|------|
| I1 | BloomTimeline 花期组件 | remaining 4.3 | 🟡M |
| I2 | 前端 useProductConfig hook | closure T1.5 | 🟢L |
| I3 | 预览页（shown+locked模块）| closure T1.5 | 🟡M |
| I4 | 前端埋点 tracking.ts + useTracking | closure T4.4 | 🟡M |

---

### 🟠 Wave 2：自助微调 + 多Agent（等 Wave 1 完成，可开 3 个 AI 窗口）

```
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  窗口 J           │  │  窗口 K           │  │  窗口 L           │
│  自助微调引擎      │  │  多Agent评审       │  │  反馈+导出+验证    │
│  🔴H             │  │  🔴H             │  │  🟡M             │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

#### 窗口 J — 自助微调引擎 🔴H
> 核心体验，替换+重排+校验+回退

| # | 任务 | 来源 | AI级 |
|---|------|------|------|
| J1 | Swap Candidates 预计算 | closure T2.1 / soft-rule 8.1 | 🔴H |
| J2 | slot_compatibility 计算 | soft-rule 8.2 | 🟡M |
| J3 | differentiation 计算 | soft-rule 8.3 | 🟡M |
| J4 | Partial Reassemble 引擎 | closure T2.2 / soft-rule 8.5 | 🔴H |
| J5 | validate_swap_impact（跌幅三档）| soft-rule 8.4 | 🔴H |
| J6 | 节奏轻重切换 | soft-rule 8.6 | 🟡M |
| J7 | Self-Serve Tuning API（3个端点+限流）| closure T2.3 | 🟡M |
| J8 | 前端微调 UI（SwapPanel）| closure T2.4 | 🟡M |
| J9 | 行程装配集成（传入segment+stage）| soft-rule 9.1-9.3 | 🔴H |

#### 窗口 K — 多Agent评审流水线 🔴H
> Prompt 工程密集，需理解旅行质量标准

| # | 任务 | 来源 | AI级 |
|---|------|------|------|
| K1 | ReviewAgent 基类 + Issue 模型 | closure T3.1 | 🟡M |
| K2 | QA Agent（时间冲突/营业时间）| closure T3.2 | 🔴H（Prompt工程）|
| K3 | User Proxy Agent（客群视角）| closure T3.3 | 🔴H（Prompt工程）|
| K4 | Ops Proxy Agent（执行风险）| closure T3.4 | 🔴H（Prompt工程）|
| K5 | Final Judge 裁决逻辑 | closure T3.5(部分) | 🔴H |
| K6 | Pipeline 集成（并行+rewrite）| closure T3.5 | 🔴H |
| K7 | 审核报告增加 soft_rule_summary | soft-rule 10.1-10.3 | 🟡M |

#### 窗口 L — 反馈回写 + 导出 + 验证 🟡M
> 逻辑明确，但需要多系统联调

| # | 任务 | 来源 | AI级 |
|---|------|------|------|
| L1 | 反馈回写引擎 feedback_writer.py | closure T4.2 | 🟡M |
| L2 | 预览页埋点 SDK | soft-rule 11.1 | 🟢L |
| L3 | 微调页埋点 SDK | soft-rule 11.2 | 🟢L |
| L4 | 转化埋点 | soft-rule 11.3 | 🟢L |
| L5 | A/B test 实验分组 | soft-rule 11.4-11.5 | 🟡M |
| L6 | 交付页导出为图片 | remaining C4 | 🟡M |
| L7 | PDF 验证 | trip-engine 8.2 | 🟢L |
| L8 | 多场景攻略生成验证 | trip-engine 8.6 | 🟡M |

---

### 🔴 Wave 3：端到端验证 + 高级分析（等 Wave 2 完成，可开 2 个 AI 窗口）

```
┌──────────────────────┐  ┌──────────────────────┐
│  窗口 M               │  │  窗口 N               │
│  端到端验证+收尾        │  │  离线评测+校准分析      │
│  🟡M~🔴H             │  │  🔴H                  │
└──────────────────────┘  └──────────────────────┘
```

#### 窗口 M — 端到端验证 + 视觉收尾 🟡M
| # | 任务 | 来源 | AI级 |
|---|------|------|------|
| M1 | 端到端全漏斗走通 | remaining F1 | 🟡M |
| M2 | 移动端适配验证 | remaining F3 | 🟢L |
| M3 | 社交分享验证（OG图）| remaining F4 | 🟢L |
| M4 | 全页面视觉走查 | remaining 5.1 | 🟡M |
| M5 | ?export=true 验证 | remaining 5.2 | 🟢L |
| M6 | 小红书图+朋友圈图导出 | remaining 5.3 | 🟡M |
| M7 | Satori 批量导出封面 | remaining 5.4 | 🟡M |
| M8 | Admin 风险标红+替换日志 | closure T5.2 | 🟡M |
| M9 | Weight Pack 接入 Scorer | closure T5.1 | 🔴H |
| M10 | OpenSpec 归档所有 changes | remaining 5.7 | 🟢L |

#### 窗口 N — 离线评测 + 校准 🔴H
| # | 任务 | 来源 | AI级 |
|---|------|------|------|
| N1 | 20个评测样本 JSON | closure T4.3 | 🟡M |
| N2 | 6维自动评分器 | closure T4.3 | 🔴H |
| N3 | run_eval.py 评测脚本 | closure T4.3 | 🟡M |
| N4 | analyze_preview_feedback batch job | soft-rule 12.1 | 🔴H |
| N5 | 客群平衡性检查 | soft-rule 12.2 | 🟡M |
| N6 | CLI 工具（score_soft_rules / weight_packs）| soft-rule 13.1-13.2 | 🟢L |

---

## 汇总统计

### 按 AI 等级

| 等级 | 任务数 | 占比 | 适合谁 |
|------|--------|------|--------|
| 🟢 **L** (低级) | ~32 | 40% | Copilot / GPT-4o-mini / 初级AI窗口 |
| 🟡 **M** (中级) | ~28 | 35% | GPT-4o / Claude Sonnet / 有上下文的AI窗口 |
| 🔴 **H** (高级) | ~20 | 25% | Claude Opus / 你亲自监督的AI窗口 |

### 按 Wave 并行度

| Wave | 可并行窗口数 | 耗时预估 | 瓶颈 |
|------|------------|----------|------|
| Wave 0 | **5** | 2-3天 | B2-B4 seed数据需查真实信息 |
| Wave 1 | **4** | 4-5天 | F7/F8 评分引擎 + G1/G4 预览引擎 |
| Wave 2 | **3** | 5-7天 | J4 Partial Reassemble + K2-K4 Prompt工程 |
| Wave 3 | **2** | 3-4天 | N2/N4 评测+校准 |
| **总计** | **14 → 34天** | **→ 并行后 14-19天** | |

### 最大并行效率

如果同时开 **5 个 AI 窗口**：
- Wave 0 全部并行 → **2-3 天搞定 40% 的任务**
- Wave 1 全部并行 → **4-5 天搞定核心引擎**
- Wave 2+3 → **8-11 天搞定集成和验证**
- **总计约 14-19 个工作日**（原串行估计 34 天）

### 推荐配置

| 窗口 | AI 等级 | 工作描述 |
|------|---------|----------|
| 窗口 1 | 🟢 低级 | DB schema / migration / ORM — 最适合批量模板化任务 |
| 窗口 2 | 🟢 低级 | 文档 / seed 脚本 / 配置 / 简单工具脚本 |
| 窗口 3 | 🟡 中级 | 前端组件 / 管理后台 / CRUD API |
| 窗口 4 | 🔴 高级 | 评分引擎 / 预览引擎 / 软规则算法 |
| 窗口 5 | 🔴 高级 | Prompt 工程 / 多Agent / 端到端集成 |
