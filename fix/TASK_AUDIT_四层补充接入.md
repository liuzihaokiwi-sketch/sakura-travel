# 四层逻辑补充接入 — 任务跟踪

> 创建：2026-03-22
> 依据：fix/四层逻辑补充接入审计_v1.md
> 执行优先级：第一批(立刻接入) → 第二批(复用高级能力) → 第三批(飞轮沉淀)

---

## 状态总览

| # | 接入项 | 目标层 | 状态 | 说明 |
|---|--------|--------|------|------|
| 1 | `route_matrix` → itinerary_fit | L2 | ✅ | async 变体 + real_transit_min + CorridorResolver v2 评分 |
| 2 | `validation/engine` → 前置门控 | L4 | ✅ | generate_trip.py 红灯阻断，黄灯放行 |
| 3 | `offline_eval` → quality gate | L4 | ✅ | 6 维评分写入 plan_metadata.offline_eval |
| 4 | `review_ops` → 评审回写飞轮 | L4 | ✅ | review_writeback.py: QA→stale, Ops→booking, UserProxy→decisions, Tuning→tunable |
| 5 | `feedback/distillation` → entity/circle 回写 | L1 | ✅ | _update_entity_quality: per-entity 信号 + circle 级 NPS |
| 6 | `swap_engine` → E3 复用 | L2 | 🔲 | Phase C (E3) 时做，已有成熟逻辑不重写 |
| 7 | `swap_safety` → post-plan guardrail | L4 | 🔲 | Phase C (E3) 时做 |
| 8 | `preview_engine` → Layer 3 | L3 | ✅ | 已在 generate_trip.py Step 2.3 接入 |
| 9 | `fragment_pipeline` → decision cache | L1 | 🔲 | Phase B (E6) 时重构 |
| 10 | `region_router` → profile 矩阵迁移 | L1 | 🔲 | 低优先级，作为 circle_selector seed |

---

## 已完成详情

### 接入 1: route_matrix → itinerary_fit_scorer
- `itinerary_fit_scorer.py`: 新增 `compute_itinerary_fit_async()`
- 自动查 `route_matrix.get_travel_time()` 获取 real_transit_min
- `_score_corridor_alignment_v2()` 使用 CorridorResolver（精确+相邻评分）
- `_score_sequence_fit_v2()` / `_score_backtrack_v2()` 使用 real transit
- 完全向后兼容：同步版 `compute_itinerary_fit()` 不变

### 接入 2: validation/engine → 前置门控
- `generate_trip.py`: 在 circle pipeline 之前加载 DetailForm → 跑 ValidationEngine
- RED → `validation_failed` 状态，立即返回，不浪费生成资源
- YELLOW → 日志记录，继续执行
- 异常 → 非阻塞，继续执行

### 接入 3: offline_eval → quality gate
- `generate_trip.py` Step 2.6: 每次生成后自动跑 6 维评分
- 评分结果写入 `plan_metadata.offline_eval` + `offline_eval_overall`
- 用于 E6a shadow write 对比 + feature flag 放量验收

### 接入 4: review_ops → 评审回写飞轮
- 新建 `app/domains/review_ops/review_writeback.py`
- QA hard_fail(closed_entity/closed_day) → 标记 entity_field_provenance stale
- Ops critical(reservation_needed) → 更新 entity_base.requires_advance_booking
- User Proxy highlights/complaints → generation_decisions 快照
- Tuning Guard tunable/locked → plan_metadata.tunable_items
- 全部 PipelineResult → review_pipeline 阶段 decision 快照

### 接入 5: feedback/distillation → entity/circle 质量回写
- `distillation.py`: 新增 `_update_entity_quality()`
- 每个行程实体按 day_rating 写入 positive/negative 信号到 generation_decisions
- circle 级 NPS 信号（overall_rating ≥4 → nps_positive, ≤2 → nps_negative）
- 不直接改 entity_base（保留可追溯性），通过 decisions 累积后批量统计
