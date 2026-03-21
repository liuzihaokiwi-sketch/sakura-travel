## Context

当前代码由多轮 AI 迭代生成，产品方向经过几次调整后，`docs-human`（产品真相源）与实际代码出现了多处偏差。最严重的是：
1. 精调次数：后端硬编码 `{standard_248: 1, premium_888: 3}`，前端硬编码 2/5 次
2. 自助微调 API 引用 `plan_slots`、`entities` 等不存在的表名（直接 raw SQL），会 500
3. PDF 前端承诺了轻水印，但渲染层完全没实现
4. product_sku fallback 还是旧价位（¥19.9），与三档不匹配
5. 订单状态机文档写的是简化版，代码实际更细（多了 quiz_submitted / preview_sent / generating）

## Goals / Non-Goals

**Goals:**
- G1: 后端精调次数从 SKU features JSON 动态读取，不再硬编码
- G2: PDF 渲染层加入轻水印（订单号 + 仅供本人使用）
- G3: self_adjustment.py 改用 ORM 模型（ItineraryItem/ItineraryDay/EntityBase）
- G4: products.py fallback 对齐三档（免费/248/888）
- G5: 订单状态机文档与代码统一
- G6: 攻略生成结构预留总纲页、条件页接口占位

**Non-Goals:**
- ❌ 不修改前端页面组件（后续单独处理）
- ❌ 不重构 product_sku 表结构（保持兼容）
- ❌ 不实现完整的条件页触发逻辑（只做占位）
- ❌ 不改变现有 assembler 的核心填充流程

## Decisions

### D1: 精调次数读取方式
**选择**: 从 `product_sku.features` 的 `max_modifications` 字段读取，fallback 到硬编码 map
**替代方案**: 创建独立 config 表 → 过重，当前阶段不需要
**理由**: 最小改动，SKU features 已是 JSONB，加一个字段零迁移成本

### D2: PDF 水印实现位置
**选择**: 在 Jinja2 模板层（HTML CSS）实现，WeasyPrint 渲染时自然带入 PDF
**替代方案**: 用 Python PDF 后处理库（如 PyMuPDF）叠加水印 → 额外依赖，维护复杂
**理由**: CSS 方案与现有模板体系一致，无新依赖，水印样式可在模板中直接调整

### D3: self_adjustment.py ORM 迁移策略
**选择**: 将 raw SQL 改写为 SQLAlchemy ORM 查询，使用现有 ItineraryDay/ItineraryItem/EntityBase
**替代方案**: 创建 plan_slots/plan_swap_logs 新表 → 与现有 itinerary_items 语义重复
**理由**: 代码中已有 ItineraryItem（含 entity_id, day_id, sort_order），语义等价于 plan_slots

### D4: 订单状态机统一
**选择**: 以代码实际的 6 态为准（quiz_submitted→preview_sent→paid→generating→review→delivered），更新文档
**替代方案**: 简化代码状态机 → 已有数据依赖，改代码风险大
**理由**: 代码状态机更细更合理，文档适配代码成本更低

### D5: 攻略结构增强
**选择**: 在渲染 context 中增加 `overview_page` 字段（总纲），assembler 输出增加 `conditional_pages` 列表（条件页占位）
**替代方案**: 完整实现条件页系统 → 规模太大，不属于本次对齐任务
**理由**: 占位设计让后续实现有锚点，不影响现有流程

## Risks / Trade-offs

- **R1: self_adjustment 改 ORM 后行为变化** → 原 API 本就 500（表不存在），改后至少能正常返回，风险可控
- **R2: 水印 CSS 在不同 WeasyPrint 版本渲染不一致** → 使用 `position: fixed; bottom` 最基础 CSS，兼容性好
- **R3: SKU features 中 max_modifications 字段不存在** → fallback 到默认 map，向后兼容
- **R4: 前端精调次数未同步** → 已标记，用户确认后续单独处理，短期内价格页文案已修正