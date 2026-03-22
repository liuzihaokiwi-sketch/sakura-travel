# 四层收尾：剩余任务全景拆解

> 创建：2026-03-23
> 目标：从"模块都有"到"链路跑通"

---

## 依赖关系图

```
P0-H1 管线串联（高级）
  ├─→ P1-H1 关西圈种子设计（高级）
  │     └─→ P1-L1 种子 SQL 文件（低级）
  │     └─→ P1-L2 corridors 种子（低级）
  │     └─→ P1-L3 hotel_presets 种子（低级）
  │
  ├─→ P1-L4 Alembic migration（低级）  ← 不依赖种子，可并行
  │
  ├─→ P2-L1~L5 Layer 4 任务（低级）   ← 已有任务书
  │     └─→ P0-H2 override 接入（高级）← 依赖 L4-01+02 完成
  │
  ├─→ P3-L1~L7 前端页型组件（低级）   ← 已有任务书
  │     └─→ P3-L8 报告 API（低级）
  │
  └─→ P4-H1 E2E 测试用例设计（高级）
        └─→ P4-L1 E2E 测试实现（低级）
```

---

## P0：管线串联（最高优先级）

### P0-H1：generate_trip 管线补全 ⭐ ✅ 完成

**级别**: 高级 AI
**状态**: ✅ 已完成

**串联的模块**:
1. ✅ CorridorResolver 初始化 + load_cache
2. ✅ Step 7: fill_secondary_activities — 从 circle_entity_roles 查 POI 候选池
3. ✅ Step 8: fill_meals — 从 circle_entity_roles 查 restaurant 候选池
4. ✅ Step 9: compute_itinerary_fit_async + suggest_swaps — 逐天逐 slot 评分
5. ✅ build_itinerary_records 传入真实 fills（替换 =[]）
6. ✅ Layer 3 page pipeline: plan_chapters → plan_pages_and_persist → build_view_models
7. ✅ filler_summary decision 快照

**关键决策**:
- candidate_pool: circle_entity_roles JOIN entity_base WHERE entity_type IN (poi, activity)
- restaurant_pool: 同上 WHERE entity_type = restaurant
- SlotContext: 从 DayFrame 直接映射 primary_corridor/transfer_budget
- swap 结果只记 trace，不自动应用（避免无声替换）
- meal_flex_filler.fill_meals() 已补 corridor_resolver 参数

---

### P0-H2：override_resolver 接入

**级别**: 高级 AI
**依赖**: L4-01 + L4-02 完成后
**文件**: `eligibility_gate.py` + `major_activity_ranker.py` + `secondary_filler.py`

**需要做的**:
1. `eligibility_gate.py` 追加 EG-008: `is_blocked()` → fail
2. `major_activity_ranker.py` 的 context_fit 加 `get_weight_delta()`
3. `secondary_filler.py` 的候选池过滤 `is_blocked()`
4. `generate_trip.py` 初始化时 `await override_resolver.load_active()`

---

## P1：数据种子

### P1-H1：关西圈种子数据设计

**级别**: 高级 AI
**依赖**: P0-H1（串联完才知道数据格式对不对）

**需要设计**:
1. `city_circles`: 关西圈定义（base_cities=kyoto,osaka / extension=nara,kobe）
2. `activity_clusters`: 12-15 个活动簇，含 S/A/B 分级
   - 如：伏见稻荷(S) / 岚山竹林(S) / 祇園散步(A) / 锦市场(A) / 奈良公园(A) / 道顿堀(B) ...
   - 每个簇定义 primary_corridor / default_duration / capacity_units
3. `corridors`: 京都 6-8 条 + 大阪 4-5 条 + 奈良 2 条 + 神户 2 条
4. `hotel_strategy_presets`: 关西 3 种住法（纯京都 / 京阪双基 / 京阪神三基）
5. 每个 cluster → entity 的 anchor/secondary 角色映射关系

**产出**: 一份完整的种子数据 JSON/YAML 设计文档

---

### P1-L1：种子 SQL — city_circles + activity_clusters + circle_entity_roles

**级别**: 低级 AI
**依赖**: P1-H1 的设计文档
**文件**: 新建 `scripts/seeds/seed_kansai_circle.sql`

**任务**: 按照 P1-H1 的设计文档，生成 INSERT 语句。字段严格对齐表结构。

---

### P1-L2：种子 SQL — corridors + corridor_alias_map

**级别**: 低级 AI
**依赖**: P1-H1
**文件**: 新建 `scripts/seeds/seed_kansai_corridors.sql`

**任务**: 每个 corridor 至少 3 个别名（中文/英文/日文罗马音）。`normalized_text` 统一小写去空格。

---

### P1-L3：种子 SQL — hotel_strategy_presets

**级别**: 低级 AI
**依赖**: P1-H1
**文件**: 新建 `scripts/seeds/seed_kansai_hotel_presets.sql`

---

### P1-L4：Alembic migration

**级别**: 低级 AI
**依赖**: 无（可与种子并行）
**文件**: `alembic/versions/`

**任务**: 对以下新表生成 migration:
- `entity_alias`
- `entity_field_provenance`
- `entity_mapping_reviews`
- `entity_temporal_profiles`
- `city_circles`
- `activity_clusters`
- `circle_entity_roles`
- `hotel_strategy_presets`
- `corridors`
- `corridor_alias_map`
- `page_hero_registry`
- `generation_step_runs`（如果 trace_writer 新建的话）
- `operator_overrides`（L4-01 完成后）
- `live_risk_rules`（L4-03 完成后）

执行 `alembic revision --autogenerate -m "四层架构新增表"`，检查生成的 migration 是否完整。

---

## P2：Layer 4 剩余任务（已有任务书）

| 任务 | 级别 | 依赖 | 状态 |
|------|------|------|------|
| L4-01 operator_overrides 模型 | 低级 | 无 | 🔲 |
| L4-02 override_resolver 服务 | 低级 | L4-01 | 🔲 |
| L4-03 live_risk_monitor | 低级 | 无 | 🔲 |
| L4-04 pipeline_versions | 低级 | 无 | 🔲 |
| L4-05 offline_eval +2 维度 | 低级 | 无 | 🔲 |

详见 `fix/TASK_L4_评测校验运营层任务书_Sonnet46.md`

---

## P3：前端页型组件（已有任务书）

| 任务 | 级别 | 依赖 | 状态 |
|------|------|------|------|
| L3-06 TypeScript 类型 | 低级 | L3-05 后端 ✅ | 🔲 |
| L3-07 PageShell 组件 | 低级 | L3-06 | 🔲 |
| L3-08 固定前置页(6个) | 低级 | L3-07 | 🔲 |
| L3-09 每日执行页 | 低级 | L3-07 | 🔲 |
| L3-10 酒店详情页 | 低级 | L3-07 | 🔲 |
| L3-11 餐厅详情页 | 低级 | L3-07 | 🔲 |
| L3-12 章节 opener 页 | 低级 | L3-07 | 🔲 |
| L3-13 报告 API 端点 | 低级 | L3-06 | 🔲 |

详见 `fix/TASK_L3_渲染层任务书_Sonnet46.md`

---

## P4：E2E 验证

### P4-H1：E2E 测试用例设计

**级别**: 高级 AI
**依赖**: P0-H1 + P1-L1~L3（管线通 + 数据就绪）

**需要设计**:
1. Happy path: 关西 5 天情侣游 → 完整跑通所有阶段
2. Fallback path: 缺数据圈 → 降级到旧 assembler
3. Validation fail: 红灯表单 → 阻断
4. Shadow diff: shadow 模式输出 → 对比旧 plan
5. Review rewrite: 评审 hard_fail → 触发重写
6. 边界: 1 天 / 14 天 / 跨 3 圈

---

### P4-L1：E2E 测试实现

**级别**: 低级 AI
**依赖**: P4-H1
**文件**: `tests/e2e/test_full_pipeline.py`

**任务**: 按 P4-H1 设计的用例，用 pytest + async fixture 实现。

---

## 执行顺序总结

```
第 1 轮（可并行）:
  高级 AI: P0-H1 管线串联
  低级 AI: P1-L4 migration + P2 全部(L4-01~05) + P3 全部(L3-06~13)

第 2 轮（依赖第 1 轮）:
  高级 AI: P1-H1 种子设计 + P0-H2 override 接入
  低级 AI: P1-L1~L3 种子 SQL

第 3 轮（依赖第 2 轮）:
  高级 AI: P4-H1 E2E 测试设计
  低级 AI: P4-L1 E2E 测试实现
```

**高级 AI 总工作量**: 4 个任务（P0-H1, P0-H2, P1-H1, P4-H1）
**低级 AI 总工作量**: 15 个任务（P1-L1~L4, P2 ×5, P3 ×8, P4-L1）
