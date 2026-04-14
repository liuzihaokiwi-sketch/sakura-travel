## Context

当前攻略生成有两条路径：① 旧 `planner.py` → `day_builder.py`（基于 profiling，固定 7 槽），② 新 `assembler.py`（基于路线模板，动态 time_blocks）。新路径是主流程（`generate_trip` job 调用），旧路径仅在无 template_code 时触发。

问题是：`assembler.py` 的 `fetch_slot_candidates` 只做 `EntityScore.final_score DESC` + 简单 tag 过滤，不调用任何高级评分模块。而 `scorer.py` 的三维公式、`route_matrix.py` 的交通计算、`swap_safety.py` 的 guardrails 全部是"孤岛"——代码完整但无调用方。

## Goals / Non-Goals

**Goals:**
- G1: assembler 候选选择接入 `compute_candidate_score`，按三维分排序
- G2: assembler 装配后运行交通时间校验（route_matrix），超标项标记 warning
- G3: `run_guardrails` job 调用 `check_single_day_guardrails` 的 6 项检查
- G4: `generate_trip` job 装配后调用 `select_preview_day`，标记到 plan_metadata
- G5: `generate_trip` job 移除对不存在表的 raw SQL 引用
- G6: planner.py 候选排序改用 EntityScore

**Non-Goals:**
- ❌ 不修改 soft_rules 模块本身的算法逻辑（它们已经实现正确）
- ❌ 不新建 entity_operating_facts / seasonal_events 表（评审上下文暂设为可选）
- ❌ 不重构两套 planner 为一套（保持两条路径共存，但共享候选召回）
- ❌ 不修改前端

## Decisions

### D1: assembler 接入三维评分的方式
**选择**: 在 `fetch_slot_candidates` 内部，查出候选后调用 `compute_candidate_score`，用结果的 `final_score` 替代原来的 `EntityScore.final_score` 排序
**替代方案**: 预计算所有实体的 candidate_score 写入新表 → 预计算成本太高，user_weights 因人而异无法预存
**理由**: 实时计算是设计初衷（`scorer.py` 是纯函数无 I/O），20 个候选 × 少量计算完全可接受

### D2: user_weights 从哪来
**选择**: 从 `TripProfile` 的 `party_type` + `must_have_tags` 推导 user_weights（映射到 SEGMENT_PACK_SEEDS），再合并 stage_weight_pack
**替代方案**: 让用户在问卷中直接填权重 → 用户认知负担太高
**理由**: party_type 已经在问卷中收集，mapping 到客群包是最小路径

### D3: 交通时间校验策略
**选择**: 装配后 post-processing，遍历相邻实体对调 `get_travel_time`，超过 45min 的标记 warning 写入 plan_metadata.route_warnings
**替代方案**: 在候选选择阶段就过滤远距实体 → 可能过度限制候选池
**理由**: post-processing 风险低、不影响现有装配逻辑，warning 供审核时参考

### D4: guardrails 增强方式
**选择**: 在 `run_guardrails.py` 中导入 `check_single_day_guardrails`，对每天运行完整检查
**替代方案**: 合并 guardrails 到 quality_gate → quality_gate 是 AI 评审层，guardrails 是规则层，职责不同
**理由**: 保持分层：guardrails（规则校验）→ quality_gate（AI 质量评估）→ review_pipeline（多模型评审）

### D5: preview_day 标记位置
**选择**: 在 `generate_trip` job 的 Step 2 后（文案润色后、质量门控前）调用 `select_preview_day`，结果写入 `plan_metadata.preview_day`
**理由**: 需要文案数据才能计算 shareability/completeness

## Risks / Trade-offs

- **R1: 实时计算 candidate_score 增加装配耗时** → 评估：20 候选 × 纯函数计算 < 5ms，可忽略
- **R2: route_matrix 调 Google API 增加外部依赖** → fallback 到 haversine 估算，不会阻塞
- **R3: entity soft_scores 数据可能为空** → weight_packs.py 已有 fallback（默认中间分 5.0）
- **R4: guardrails 增强后可能导致更多 hard_fail** → 这是好事，说明之前有问题的行程被放过了
- **R5: generate_trip job 移除 raw SQL 后评审上下文变空** → 设为 optional，不影响评审主逻辑