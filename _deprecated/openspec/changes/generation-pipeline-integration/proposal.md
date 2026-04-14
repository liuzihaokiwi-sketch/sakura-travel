## Why

攻略生成管线存在严重的"实现完整但未接入"问题。软规则体系（12 维度、权重包、三维候选分、preview 选天引擎、swap 安全检查）代码质量高、架构完整，但 assembler 主流程 **完全不调用** 这些模块——候选排序只用 `EntityScore.final_score` DESC，不涉及 context_score、soft_rule_score、route_matrix 交通时间。这意味着产品文档承诺的"个性化推荐"、"松弛感优先的家庭行程"、"通勤友好的路线排列"在实际生成中完全不存在。

此外，guardrails 极简（只查实体数和重复率），不检查定休日、暴走、缺餐等硬规则，而已实现的 `swap_safety.check_single_day_guardrails` 的 6 项检查只在微调时才触发。

MVP 优先级：**P0**。这是整个"AI 定制行程"区别于模板攻略的核心价值点，不接入等于产品核心承诺是空的。

在产品价位梯度中的作用：软规则是 ¥248→¥888 之间差异化的关键——标准版用 `standard` 权重包 + 2D 公式，尊享版用 `premium` 权重包 + 3D 公式。不接入意味着两个版本生成的行程几乎一样。

## What Changes

- **接入** assembler 的候选排序接入 `compute_candidate_score`（三维公式）
- **接入** assembler 装配后运行 `route_matrix.get_travel_time` 校验通勤
- **接入** guardrails 引入 `swap_safety.check_single_day_guardrails` 的 6 项检查
- **接入** preview_engine 标记最佳预览天到 plan_metadata
- **修复** generate_trip job 中引用不存在表的 raw SQL（entity_operating_facts, seasonal_events）
- **修复** review_pipeline 持久化引用不存在表（review_pipeline_runs, plan_review_reports）
- **统一** 两套 planner 的候选召回，让 planner.py 也使用 EntityScore

## Capabilities

### New Capabilities
- `assembler-scoring-integration`: assembler 候选排序接入三维评分公式
- `assembler-route-check`: assembler 装配后校验通勤时间，超标时触发 fallback
- `guardrails-full`: guardrails job 调用完整 6 项硬规则检查
- `preview-day-marking`: 装配完成后自动标记最佳预览天

### Modified Capabilities
- `itinerary-planner`: planner.py 候选排序从 google_rating 改为 EntityScore.final_score
- `scoring-engine`: assembler 调用 compute_candidate_score 需要传入 user_weights，需从 TripProfile 构建

## Impact

- **核心后端**：`app/domains/planning/assembler.py`（主改动点）
- **Worker jobs**：`app/workers/jobs/generate_trip.py`, `app/workers/jobs/run_guardrails.py`
- **Planner**：`app/domains/trip_core/planner.py`
- **已有模块（被接入方）**：`scorer.py`, `weight_packs.py`, `route_matrix.py`, `swap_safety.py`, `preview_engine.py` — 这些模块本身不需要修改
- **数据库**：可能需要为 `entity_operating_facts`, `seasonal_events`, `review_pipeline_runs`, `plan_review_reports` 补建 alembic migration（或者改为 JSONB 字段存储在现有表中）