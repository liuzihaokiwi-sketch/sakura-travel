## Tasks

> 任务按依赖关系排序。每个 Phase 内的任务可并行，Phase 之间必须串行。
> P0 = 第一个真实用户上线前必须完成。P1 = 前 50 单内完成。P2 = 前 200 单内完成。

---

### Phase 0: 基础设施 & 数据层（第 1 周）

#### T0.1 — 创建 City Context 数据表 [P0]
- **Design Ref**: D4
- **文件**: `alembic/versions/xxx_city_context_tables.py`, `app/models/city_context.py`
- **子任务**:
  1. 定义 6 个 SQLAlchemy ORM Model：`area_profiles`, `timeslot_rules`, `seasonal_events`, `transport_links`, `audience_fit`, `entity_operating_facts`
  2. 创建 Alembic migration
  3. 编写 seed 脚本：为 Tokyo Top 50 实体填充 `timeslot_rules` + `entity_operating_facts`
  4. 编写 seed 脚本：为 Tokyo Top 50 实体填充 `audience_fit`（情侣/亲子/闺蜜/独行 四种客群）
- **验收**: `pytest tests/test_city_context_models.py` 通过；seed 后 `timeslot_rules` ≥ 50 行

#### T0.2 — 创建 product_config 表 [P0]
- **Design Ref**: D1
- **文件**: `alembic/versions/xxx_product_config.py`, `app/models/product_config.py`
- **子任务**:
  1. 定义 `ProductConfig` ORM Model（config_key PK, config_value JSONB, version, is_active）
  2. 创建 migration
  3. 编写 seed 脚本：插入 3 个 SKU 配置（引流款 29.9 / 标准版 248 / 高级版 488）
  4. 为 config_value 编写 Pydantic schema 校验（`ProductConfigSchema`）
- **验收**: seed 后 3 条 SKU 记录存在；Pydantic schema 校验通过

#### T0.3 — 创建 weight_packs 表 [P1]
- **Design Ref**: D5
- **文件**: `alembic/versions/xxx_weight_packs.py`, `app/models/weight_packs.py`
- **子任务**:
  1. 定义 `WeightPack` ORM Model
  2. 创建 migration
  3. 编写 seed 脚本：插入 6 个基础权重包（couple_poi, couple_restaurant, family_poi, family_restaurant, preview_poi, swap_poi）
  4. 编写 `weight_pack_resolver.py`：merge(base, audience, sku, stage) 逻辑
- **验收**: `pytest tests/test_weight_pack_resolver.py` 通过；couple_poi 和 family_poi 的 weights 有可见差异

#### T0.4 — entity_scores 表增加 preview_score 列 [P0]
- **Design Ref**: D2
- **文件**: `alembic/versions/xxx_add_preview_score.py`
- **子任务**:
  1. ALTER TABLE entity_scores ADD COLUMN preview_score FLOAT DEFAULT 0
  2. ALTER TABLE entity_scores ADD COLUMN context_score FLOAT DEFAULT 0
  3. 编写批量计算脚本：基于现有字段（has_image, tabelog_score, entity_type_variety）初始化 preview_score
- **验收**: 所有 entity_scores 记录有 preview_score 值；preview_score > 0 的记录 ≥ 500

#### T0.5 — itinerary_items 表增加 swap_candidates 字段 [P0]
- **Design Ref**: D3
- **文件**: `alembic/versions/xxx_add_swap_candidates.py`
- **子任务**:
  1. ALTER TABLE itinerary_items ADD COLUMN swap_candidates JSONB DEFAULT '[]'
  2. 定义 swap_candidates 的 JSON schema：`[{entity_id, name, reason, fit_score}]`
- **验收**: migration 执行成功；JSONB 字段可正常读写

---

### Phase 1: Preview Engine + Product Config API（第 2-3 周）

#### T1.1 — Product Config API [P0]
- **Design Ref**: D1
- **依赖**: T0.2
- **文件**: `app/api/routes/product_config.py`, `app/services/product_config_service.py`
- **子任务**:
  1. `GET /api/v1/products` — 返回所有 active SKU 配置（前端消费）
  2. `GET /api/v1/products/{sku_id}` — 返回单个 SKU 配置
  3. `GET /api/v1/products/{sku_id}/preview-rules` — 返回预览模块规则（哪些 show / 哪些 lock）
  4. 所有返回值从 product_config 表读取，不硬编码任何权益
- **验收**: `curl /api/v1/products` 返回 3 个 SKU；前端可用该 API 渲染价格/权益对比页

#### T1.2 — Preview Score Calculator [P0]
- **Design Ref**: D2
- **依赖**: T0.4, T0.1
- **文件**: `app/services/preview_scorer.py`
- **子任务**:
  1. 实现 `calculate_day_preview_score(day_items: list[ItineraryItem]) -> float`
  2. 五维评分：visual_appeal(0.30) + wow_factor(0.25) + variety(0.20) + evidence_density(0.15) + route_compactness(0.10)
  3. visual_appeal 基于 has_image + entity popularity
  4. evidence_density 基于 tabelog_score / review_count / distance 是否有值
  5. variety 基于 entity_type 的香农熵
- **验收**: 对同一行程的 5 天分别计算，得分不完全相同；Day 2 或 Day 3 通常得分高于 Day 1

#### T1.3 — Preview Validator [P0]
- **Design Ref**: D2
- **依赖**: T0.1
- **文件**: `app/services/preview_validator.py`
- **子任务**:
  1. 实现 5 条校验规则（≥3 POI + ≥1 餐厅 / 实体 active / 时间线无冲突 / ≥1 证据化理由 / 非移动日）
  2. 每条规则返回 `ValidationResult(passed: bool, reason: str)`
  3. 综合判定：all passed → OK / any failed → swap_to_next / all_days_failed → needs_human_review
- **验收**: 故意传入一个"纯移动日" → 校验失败；传入正常天 → 校验通过

#### T1.4 — Preview Engine 主流程 [P0]
- **Design Ref**: D2
- **依赖**: T1.2, T1.3, T1.1
- **文件**: `app/services/preview_engine.py`, `app/api/routes/preview.py`
- **子任务**:
  1. 实现 `select_best_preview_day(itinerary: Itinerary) -> PreviewDay`
     - 对每天算 preview_score → 排序 → 取最高分天
     - 对最高分天跑 validator → 通过则返回
     - 不通过 → 取下一个 → 直到通过或 fallback Day 1 → 仍不通过标记 human_review
  2. 实现 `render_preview(day: PreviewDay, sku_config: ProductConfig) -> PreviewPayload`
     - 根据 SKU 的 preview.modules_shown / modules_locked 过滤输出
     - 锁定模块用 `{locked: true, teaser: "解锁完整版查看全部餐厅推荐"}` 占位
  3. `GET /api/v1/trips/{trip_id}/preview` — 返回 PreviewPayload
- **验收**: 端到端测试：生成完整行程 → 调用 preview API → 返回包含 shown + locked 模块的 JSON

#### T1.5 — 前端对接 Product Config + Preview [P0]
- **依赖**: T1.1, T1.4
- **文件**: `web/lib/api.ts`, `web/app/trip/[id]/preview/page.tsx`
- **子任务**:
  1. 创建 `useProductConfig()` hook：从 API 获取 SKU 配置
  2. 创建预览页组件：渲染 shown 模块 + locked 模块（带解锁提示和 CTA 按钮）
  3. 价格/权益信息完全从 ProductConfig 驱动，前端零硬编码
  4. Locked 模块显示模糊背景 + 锁图标 + "查看完整版" CTA
- **验收**: 切换 SKU 配置的 modules_shown → 前端自动更新展示模块；无硬编码权益文案

---

### Phase 2: Self-Serve Tuning（第 4-5 周）

#### T2.1 — Swap Candidates 预计算 [P0]
- **Design Ref**: D3
- **依赖**: T0.5, T0.1, T0.3
- **文件**: `app/services/swap_candidate_generator.py`
- **子任务**:
  1. 实现 `generate_swap_candidates(item: ItineraryItem) -> list[SwapCandidate]`
  2. 查找规则：同 area_code + 同 entity_type + 同 time_slot + is_active → 按 fit_score 排序取 Top 5
  3. 如果 weight_packs 可用，使用 swap_* 权重包排序；否则用 final_score
  4. 排除已在当天出现的 entity
  5. 在行程生成完毕后批量调用，结果写入 itinerary_items.swap_candidates
- **验收**: 一个 5 天行程生成后，每个 item 的 swap_candidates 有 3-5 个候选（某些冷门区域可以 < 3）

#### T2.2 — Partial Reassemble 引擎 [P0]
- **Design Ref**: D3
- **依赖**: T2.1, T0.1
- **文件**: `app/services/partial_reassembler.py`
- **子任务**:
  1. 实现 `partial_reassemble(day_id, item_id, new_entity_id) -> ReassembleResult`
  2. 替换目标 item 的 entity_id
  3. 重算该天所有 item 的 start_time / end_time / transit_duration
  4. 检查相邻天影响（如果是酒店替换 → 次日出发地变化 → 重算次日首项 transit）
  5. 对修改后的天运行 `guardrails(day_id)` 单天校验
  6. 校验通过 → 写入新版本（itinerary_version + 1）；不通过 → 回退 + 返回错误原因和替代建议
- **验收**: 替换午餐 → 时间线自动调整；替换酒店 → 次日出发时间调整；替换导致时间冲突 → 回退成功

#### T2.3 — Self-Serve Tuning API [P0]
- **Design Ref**: D3
- **依赖**: T2.1, T2.2
- **文件**: `app/api/routes/tuning.py`
- **子任务**:
  1. `GET /api/v1/trips/{trip_id}/items/{item_id}/swaps` — 返回该 item 的 swap_candidates
  2. `POST /api/v1/trips/{trip_id}/items/{item_id}/swap` — 执行替换（body: {new_entity_id}）
  3. `POST /api/v1/trips/{trip_id}/items/{item_id}/revert` — 撤销最近一次替换
  4. 每次 swap 不消耗 formal_revision_count
  5. 每日限制 10 次 swap（从 ProductConfig 读取限额）
  6. 记录 swap_log（原 entity → 新 entity → 时间 → 结果）
- **验收**: 连续 swap 3 次 → 每次时间线正确更新；第 11 次 → 返回 429 限流

#### T2.4 — 前端微调 UI [P0]
- **依赖**: T2.3
- **文件**: `web/app/trip/[id]/page.tsx`, `web/components/SwapPanel.tsx`
- **子任务**:
  1. 每个可替换 item 右上角显示"换一个"按钮
  2. 点击后展示 SwapPanel：候选列表（名称 + 评分 + 推荐理由）
  3. 用户选择后调用 swap API → 成功 → 刷新该天视图 + 显示 toast
  4. 失败 → 显示错误原因 + 推荐替代
  5. 必去项（editorial_boost > 5）不显示"换一个"按钮
  6. 剩余可替换次数显示在顶部
- **验收**: 用户可视化完成替换流程；必去项无替换入口

---

### Phase 3: Multi-Agent Review（第 6-8 周）

#### T3.1 — Review Agent 基础框架 [P1]
- **Design Ref**: D6
- **文件**: `app/services/review/agent_base.py`, `app/services/review/pipeline.py`
- **子任务**:
  1. 定义 `ReviewAgent` 基类：`async def review(plan, context) -> list[Issue]`
  2. 定义 `Issue` 数据模型：severity(low/medium/high), category, description, fix_suggestion, auto_fixable
  3. 实现 `ReviewPipeline.run(plan)` 主流程：Planner 输出 → QA + UserProxy + OpsProxy（可并行）→ FinalJudge
  4. FinalJudge 裁决逻辑：pass / rewrite(max 2) / human
- **验收**: mock plan → pipeline 完整跑通 → 返回 verdict

#### T3.2 — QA Agent [P1]
- **Design Ref**: D6
- **依赖**: T3.1, T0.1
- **文件**: `app/services/review/qa_agent.py`
- **子任务**:
  1. Prompt 设计：输入 plan + timeslot_rules + entity_operating_facts → 找出时间冲突/营业时间错误/交通不可达
  2. 使用 GPT-4o-mini
  3. 输出结构化 issues[]
  4. Token 限制 < 2K input
- **验收**: 故意在 plan 中放一个"下午去筑地" → QA 检出并标 severity=high

#### T3.3 — User Proxy Agent [P1]
- **Design Ref**: D6
- **依赖**: T3.1, T0.1
- **文件**: `app/services/review/user_proxy_agent.py`
- **子任务**:
  1. Prompt 设计：输入 plan + trip_profile + audience_fit → 站在目标客群视角找不满意之处
  2. 使用 GPT-4o-mini
  3. 输出结构化 complaints[]：每个 complaint 有 fix_suggestion
  4. complaints.length > 3 → 触发人工
- **验收**: 输入"亲子家庭" profile + 含有"深夜酒吧"的 plan → 检出 complaint

#### T3.4 — Ops Proxy Agent [P1]
- **Design Ref**: D6
- **依赖**: T3.1, T0.1
- **文件**: `app/services/review/ops_proxy_agent.py`
- **子任务**:
  1. Prompt 设计：输入 plan + transport_links + seasonal_events → 检查执行风险
  2. 使用 GPT-4o-mini
  3. 输出结构化 warnings[]
  4. 特别关注：跨城市交通可达性、季节性人流影响、需要预约的景点
- **验收**: 输入含"祇园祭期间去清水寺"的 plan → 检出"极端拥挤"warning

#### T3.5 — Review Pipeline 集成 [P1]
- **依赖**: T3.2, T3.3, T3.4, T3.1
- **文件**: `app/services/review/pipeline.py`（扩展）
- **子任务**:
  1. QA + UserProxy + OpsProxy 并行执行（asyncio.gather）
  2. FinalJudge 合并所有 issues/complaints/warnings → 裁决
  3. rewrite 时只重写有问题的天（不重写全部）
  4. 记录 review_log（各 agent 的输出 + 最终裁决 + 耗时 + token 消耗）
  5. 集成到 assembler 主流程：生成完 → 自动 review → pass 才进入交付
- **验收**: 端到端：生成行程 → review → pass（0 issue 时 < 15s）；review → rewrite → pass（1-2 issue 时 < 30s）

---

### Phase 4: Feedback & Eval（持续）

#### T4.1 — 埋点事件 API [P1]
- **Design Ref**: D7
- **文件**: `app/api/routes/events.py`, `app/models/user_events.py`
- **子任务**:
  1. 创建 `user_events` 表：event_type, trip_id, entity_id, metadata JSONB, created_at
  2. `POST /api/v1/events` — 接收前端埋点
  3. 支持 9 种事件类型（preview_view, preview_stay_duration, preview_to_paid, swap_triggered, swap_accepted, swap_reverted, formal_revision_requested, share_link_clicked, feedback_submitted）
  4. 批量写入（前端攒 5 个一起发）
- **验收**: 前端发送 10 个事件 → 数据库 user_events 有 10 行

#### T4.2 — 反馈回写引擎 [P1]
- **Design Ref**: D7
- **依赖**: T4.1
- **文件**: `app/services/feedback_writer.py`
- **子任务**:
  1. 定时任务（每小时）：汇总最近事件，更新 entity 评分
  2. preview_to_paid 率高的天 → 该天 entities preview_score +1
  3. swap_triggered 率 > 30% 的 entity → base_score -2
  4. feedback_submitted 满意度 < 3 的 entity → editorial_boost -1
  5. 所有回写有 audit trail（feedback_adjustments 表）
- **验收**: 模拟 100 个 swap_triggered 事件集中在某 entity → 该 entity base_score 降低

#### T4.3 — 离线评测集 [P2]
- **Design Ref**: D8
- **文件**: `tests/eval/`, `tests/eval/test_cases/`, `scripts/run_eval.py`
- **子任务**:
  1. 创建 20 个评测样本 JSON（trip_profile + expected_constraints）
  2. 实现评测脚本：对每个样本生成行程 → 跑 6 个评分维度 → 汇总
  3. 6 维度自动评分器（基于规则，非 LLM）：时间线合理性 / 路线效率 / 客群匹配 / 证据密度 / 多样性 / 可执行性
  4. 输出 eval_report.json：每维度分数 + 总体通过/不通过
- **验收**: `python scripts/run_eval.py` 产出报告；当前基线可能 < 3.5，但流程跑通

#### T4.4 — 前端埋点接入 [P1]
- **依赖**: T4.1
- **文件**: `web/lib/tracking.ts`, `web/hooks/useTracking.ts`
- **子任务**:
  1. 实现 `track(eventType, metadata)` 工具函数
  2. 预览页：自动发送 preview_view + preview_stay_duration
  3. 微调面板：swap_triggered / swap_accepted / swap_reverted
  4. 付费完成：preview_to_paid
  5. 分享按钮：share_link_clicked
  6. 批量发送策略：攒满 5 个或页面离开时 flush
- **验收**: 打开预览页 → 30s 后查看 user_events 表有 preview_view + preview_stay_duration

---

### Phase 5: 权重校准 & 运维（持续）

#### T5.1 — Weight Pack 接入 Scorer [P1]
- **Design Ref**: D5
- **依赖**: T0.3
- **文件**: `app/services/scorer.py`（修改）
- **子任务**:
  1. 重构 `DIMENSIONS_BY_TYPE` → 从 weight_packs 表读取
  2. 实现 `resolve_weights(entity_type, audience, sku_tier, stage) -> dict`
  3. 保留硬编码值为 fallback（weight_packs 表为空时使用）
  4. 添加 `stage` 参数：preview / full / swap 三种模式使用不同权重
- **验收**: 切换 audience=couple vs audience=family → 同一 entity 得分有明显差异

#### T5.2 — Admin 风险标红 + 替换日志 [P1]
- **文件**: `web/app/admin/trips/[id]/page.tsx`, `app/api/routes/admin.py`
- **子任务**:
  1. `GET /api/v1/admin/trips/{trip_id}/review-log` — 返回 review pipeline 的完整日志
  2. `GET /api/v1/admin/trips/{trip_id}/swap-log` — 返回用户替换历史
  3. Admin 页面：review 结果中 severity=high 的行标红
  4. Admin 页面：显示用户替换历史时间线
- **验收**: 生成含 high-severity issue 的行程 → Admin 页面可见红色高亮

#### T5.3 — Feature Flags 框架 [P0]
- **文件**: `app/core/feature_flags.py`, `app/models/feature_flags.py`
- **子任务**:
  1. 创建 `feature_flags` 表：flag_key, is_enabled, metadata JSONB
  2. 实现 `is_feature_enabled(flag_key) -> bool`
  3. 为每个 Phase 创建 flag：`preview_engine_v2`, `self_serve_tuning`, `multi_agent_review`, `feedback_loop`
  4. 所有新功能入口用 flag 包裹，flag off 时走旧逻辑
- **验收**: toggle preview_engine_v2 off → preview API 返回旧版 Day 1 裁切

---

## Task Dependency Graph

```
T0.1 ──┬──▶ T1.2 ──┬──▶ T1.4 ──▶ T1.5
       │           │
       ├──▶ T1.3 ──┘
       │
       ├──▶ T2.1 ──▶ T2.2 ──▶ T2.3 ──▶ T2.4
       │
       ├──▶ T3.2 ──┐
       ├──▶ T3.3 ──┼──▶ T3.5
       └──▶ T3.4 ──┘

T0.2 ──▶ T1.1 ──▶ T1.4

T0.3 ──▶ T5.1
         T2.1

T0.4 ──▶ T1.2

T0.5 ──▶ T2.1

T4.1 ──▶ T4.2
T4.1 ──▶ T4.4

T5.3 (独立，尽早完成)
T4.3 (独立，可随时启动)
```

## Estimated Effort

| Phase | 任务数 | 预估工时 | 关键路径 |
|-------|--------|----------|----------|
| Phase 0 | 5 | 3-4 天 | T0.1（最大表最多 seed 数据） |
| Phase 1 | 5 | 5-7 天 | T1.4（Preview Engine 主流程） |
| Phase 2 | 4 | 5-7 天 | T2.2（Partial Reassemble 最复杂） |
| Phase 3 | 5 | 5-7 天 | T3.5（Pipeline 集成 + 调试） |
| Phase 4 | 4 | 3-5 天 | T4.3（评测集创建耗时） |
| Phase 5 | 3 | 3-4 天 | T5.1（Scorer 重构需谨慎） |
| **总计** | **26** | **24-34 天** | |
