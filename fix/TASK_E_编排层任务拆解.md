# Layer 2: 决策与编排层任务拆解

> 创建：2026-03-22
> 依据：docs/Layer_2_决策与编排层实现方案_v1.md + 项目现状审计
> 执行顺序：E1 → E4 → E5 → E2 → E6a → E6b → E3

---

## 状态总览

| ID | 任务 | 状态 | 说明 |
|----|------|------|------|
| E1 | generation_decisions 快照回写 | ✅ 完成 | decision_writer.py + generate_trip.py 8 类快照 |
| E4 | explain 字段同步生成 | ✅ 完成 | CircleExplain / MajorExplain / HotelExplain 结构化输出 |
| E5 | secondary_filler 接入 CorridorResolver | ✅ 完成 | secondary_filler + meal_flex_filler 均接入 |
| E2 | fallback_router 精细化 | ✅ 完成 | FULL/MAJOR 退出，FILLER/SECTION 继续新链路 |
| E6a | build_itinerary_records (shadow write) | ✅ 完成 | itinerary_builder.py + shadow diff 对比 |
| E6b | feature flag 正式切换 | ✅ 完成 | CIRCLE_WRITE_MODE live/shadow/disabled 三态 |
| E3 | itinerary_fit_scorer 小范围替换 | ✅ 完成 | suggest_swaps + suggest_meal_swaps + corridor 候选 |

---

## Phase A — ✅ 已完成

### E1 — generation_decisions 快照回写
**文件**：
- 新建 `app/domains/planning/decision_writer.py`
- 修改 `app/workers/jobs/generate_trip.py`

**写入的 8 类快照**：
1. `normalized_profile` — 画像标准化完成
2. `circle_selection` — 选中城市圈 + 备选方案评分
3. `eligibility` — 资格过滤结果
4. `major_activity_plan` — 选中主活动 + 全排名 + why_selected/why_not
5. `hotel_strategy` — 住法策略 + 基点明细
6. `day_frame` — 骨架概况（走廊/driver/intensity per day）
7. `fallback` — 降级决策（如触发）
8. plan_id 延迟回写（assembler 返回后补 plan_id）

**关键设计**：
- `input_hash` = SHA-256(profile_json)，支持重跑检测
- `invalidate_previous_decisions()` 在每次跑之前作废旧决策
- 所有 decision 用 `is_current=True` 标记当前有效版本

### E4 — explain 字段同步生成
**文件**：
- `city_circle_selector.py` → CircleExplain
- `major_activity_ranker.py` → MajorExplain
- `hotel_base_builder.py` → HotelExplain

**每个 Explain 结构包含**：
- `why_selected` — 入选理由
- `why_not_selected` — 落选理由
- `expected_tradeoff` — 预期代价
- `fallback_hint` — 降级提示

### E5 — secondary_filler + meal_filler 接入 CorridorResolver
**文件**：
- `secondary_filler.py` — `_score_entity()` 接入 resolver，支持相邻走廊 +12 分
- `meal_flex_filler.py` — `_score_restaurant()` 接入 resolver，支持相邻走廊 +8 分
- 向后兼容：resolver=None 时自动降级为字符串包含判断

### E2 — fallback_router 精细化
**文件**：
- `app/workers/jobs/generate_trip.py` 降级检查改为：
  - `FULL_LEGACY` → 完全退出到旧链路
  - `MAJOR_LEGACY` → 完全退出到旧链路
  - `FILLER_LEGACY` → 继续新链路，仅 secondary/meal 降级
  - `SECTION_ADAPTER` → 继续新链路，仅渲染层降级
  - `NONE` → 全新链路

---

## Phase B — E6a ✅ / E6b 🔲

### E6a — build_itinerary_records (shadow write) ✅
**文件**：`app/domains/planning/itinerary_builder.py` (新建)
**集成**：`app/workers/jobs/generate_trip.py` Step 7 后

**已实现**：
- `CIRCLE_WRITE_MODE` feature flag（disabled / shadow / live）
- `build_itinerary_records()`: 从 skeleton + secondary + meal 直写 Plan/Day/Item
- 逐天构建：早餐 → 主活动(anchor entities) → 午餐 → 次要活动 → 晚餐 → 酒店
- `_compute_shadow_diff()`: 对比新旧 plan 的 entity overlap rate / missing / extra
- Shadow plan 存入 plan_artifacts（artifact_type="shadow_plan"）
- diff 写入 plan_metadata.shadow_diff
- `_infer_city_code()`: 从 corridor ID 前缀推断城市
- `_get_anchor_entities()`: 从 ranking_result 查找 cluster 的 anchor entity IDs

### E6b — feature flag 正式切换
**级别**：高级 AI
**依赖**：E6a 验收通过
**文件**：修改 `generate_trip.py`

**切换策略**：
- `CIRCLE_WRITE_MODE = "shadow" | "live" | "disabled"`
- `live` 模式下：跳过旧 assembler，直接用 build_itinerary_records
- 按城市圈维度灰度（如先 kansai → 再 tokyo）

---

## Phase C — 🔲 待做

### E3 — itinerary_fit_scorer 小范围替换
**级别**：高级 AI
**依赖**：E6b
**文件**：修改 `itinerary_fit_scorer.py`

**新增能力**：
- `suggest_swap()` — 如果某个次要活动 backtrack 严重，建议同 corridor 替代
- `suggest_meal_swap()` — 如果某个 route_meal 时间窗冲突，建议 backup_meal
- 替换结果写入 trace，不静默替换
