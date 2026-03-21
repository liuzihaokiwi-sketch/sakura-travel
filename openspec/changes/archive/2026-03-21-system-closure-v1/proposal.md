## Why

当前系统拥有完整的技术骨架（实体池 → 评分 → 装配 → 渲染 → 交付），但缺少让它稳定产出可成交攻略的**闭环能力**。具体来说：

1. **免费预览不是独立的成交引擎**——它只是完整版的 Day 1 裁切，无法最大化"看一天就想付费"的转化
2. **自助微调不存在**——用户任何不满意都需要消耗正式修改次数或人工介入
3. **产品真相源不统一**——SKU 权益、文案承诺、后台逻辑、客服话术之间存在矛盾
4. **城市上下文数据未收敛**——缺少时段/季节/天气/客群维度的结构化数据，AI 生成仍依赖 prompt hacking
5. **软规则散落在代码中**——没有可配置、可学习的权重包体系
6. **质量评审靠人工**——缺少多模型流水线自动发现问题
7. **无反馈学习回路**——用户行为不回写评分和排序
8. **无离线评测集**——无法判断改动是改善还是退步

**为什么现在做**：系统即将接入真实用户。如果这些缺口不补，第一批用户的体验将不可控，导致口碑崩塌。现在补这些缺口的成本远低于上线后返工。

**在产品价位梯度中的作用**：
- Preview Engine → 直接决定引流款（19.9~29.9）的成交转化率
- Self-Serve Tuning → 直接降低利润款（69~199）的人工修改成本
- City Context + Soft Rules → 决定所有价位产品的推荐质量
- Multi-Agent Review → 替代人工审核，使高客单价产品的交付可规模化

**MVP 优先级标注**：每个 capability 已标注 P0/P1/P2。P0 = 第一个真实用户上线前必须完成。

## What Changes

### 核心增加

- **单一真相源配置系统**：所有 SKU 权益、文案、规则从一个 JSON/DB 表读取
- **Preview Engine**：独立的预览生成+排序+校验+降级流程
- **Self-Serve Tuning Loop**：用户可自助替换酒店/餐厅/体验，系统自动局部重排+重检
- **City Context 数据表**：6 张新表，覆盖时段/季节/区域/交通/客群维度
- **Soft Rules + Weight Packs**：可配置的评分权重包，按客群/套餐/阶段切换
- **Multi-Agent Review Pipeline**：Planner → QA → UserProxy → OpsProxy → FinalJudge
- **Feedback & Learning Loop**：埋点 → 指标 → 权重回写
- **Offline Eval**：评测集 + 回归测试 + 验收流程
- **Admin 补全**：风险标红、替换日志、预览表现、行为回放

### 核心修改

- `entity_scores` 表增加 context_score 和 preview_score 两个独立评分
- `itinerary_items` 表增加 swap_candidates JSONB 字段
- `product_sku` 表重构为配置驱动（features → 单一真相源）
- assembler.py 增加 preview 模式和 swap 模式
- scorer.py 接入 weight packs 而非硬编码权重

## Capabilities

### New Capabilities

- `product-truth-source`: 单一产品真相源——统一 SKU 权益/文案/规则的配置模型 (P0)
- `preview-engine`: 独立预览引擎——选天、排序、校验、降级、成交优化 (P0)
- `self-serve-tuning`: 自助微调闭环——替换/局部重排/自动重检/修改次数扣减 (P0)
- `city-context-data`: 城市上下文数据系统——时段/季节/交通/客群结构化数据 (P0)
- `soft-rules-weight-packs`: 软规则与权重包——可配置/可学习的评分权重体系 (P1)
- `multi-agent-review`: 多模型评审流水线——自动质检/用户视角/运营视角/裁决 (P1)
- `feedback-learning-loop`: 反馈学习回路——埋点/指标/权重回写 (P1)
- `offline-eval`: 离线评测集与验收机制——评测/回归/发布门控 (P2)
- `admin-ops-v2`: 后台与运营能力补全——风险标红/行为回放/替换日志 (P1)

### Modified Capabilities

- `scoring-engine`: 评分引擎需支持 weight packs 和 preview_score 独立计算
- `trip-assembler`: 装配器需支持 preview 模式（选最佳天）和 swap 模式（局部替换+重排）

## Impact

- **数据库**：新增 6 张表，修改 3 张表（entity_scores / itinerary_items / product_sku）
- **后端 API**：新增 preview / tuning / feedback 三组 API
- **前端**：交付页增加自助微调 UI，admin 增加风险标红和行为回放
- **AI 调用**：新增 multi-agent review pipeline（5 步 LLM 调用），需控制 token 预算
- **评分引擎**：scorer.py 需重构为 weight pack 驱动
- **装配器**：assembler.py 需支持三种模式（full / preview / swap）
