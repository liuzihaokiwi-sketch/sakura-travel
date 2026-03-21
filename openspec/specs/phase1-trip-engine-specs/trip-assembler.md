# Spec: trip-assembler

## 概述

行程装配引擎负责将路线模板 + 评分数据组合成结构化行程 JSON，写入 itinerary_plans / itinerary_days / itinerary_items 三张表。

---

## 装配流程

```
输入: trip_request_id, template_code, scene
  ↓
1. 加载路线模板（route_templates）
2. 应用 scene_variants 参数覆盖
3. 逐日逐槽位填充实体：
   a. 构建候选查询（tags_required + area_hint + city_code）
   b. 排除已选实体（去重）
   c. 取 final_score Top 1
   d. fallback 处理
4. 调用 AI 文案润色（ai-copywriter）
5. 写入 itinerary_plans → itinerary_days → itinerary_items
6. 写入 planner_runs（追溯记录）
7. enqueue run_guardrails(trip_id)
```

---

## 数据写入规格

### itinerary_plans
```
plan_id            UUID PK
trip_request_id    UUID FK
template_code      VARCHAR(64)
scene              VARCHAR(32)
status             VARCHAR(16)  -- assembling/reviewing/ready/failed
total_days         INTEGER
city_codes         TEXT[]
assembled_at       TIMESTAMPTZ
```

### itinerary_days
```
day_id             UUID PK
plan_id            UUID FK
day_num            INTEGER
theme_zh           VARCHAR(128)
area_zh            VARCHAR(128)
hotel_area_zh      VARCHAR(256)
transport_notes_zh TEXT
```

### itinerary_items
```
item_id            UUID PK
day_id             UUID FK
time_slot          VARCHAR(16)   -- morning/lunch/afternoon/evening
slot_type          VARCHAR(16)   -- poi/restaurant/hotel_area/transport
entity_id          UUID FK NULL  -- 若 slot_type=hotel_area 则为 null
entity_type        VARCHAR(16)   -- poi/restaurant/hotel
duration_minutes   INTEGER
copy_zh            TEXT          -- AI 润色后的描述
tips_zh            TEXT          -- 小 Tips
sort_order         INTEGER
```

### planner_runs
```
run_id             UUID PK
trip_request_id    UUID FK
plan_id            UUID FK
template_code      VARCHAR(64)
scene              VARCHAR(32)
score_version      VARCHAR(64)   -- 使用的评分版本（computed_at 时间戳）
template_version   VARCHAR(64)   -- 模板版本
entity_ids_used    UUID[]        -- 本次装配使用的实体 ID 列表
run_at             TIMESTAMPTZ
duration_ms        INTEGER
```

---

## 装配约束

| 约束 | 说明 |
|------|------|
| 实体不重复 | 同一 plan_id 中同一实体只能出现一次 |
| 候选充足 | 每个槽位候选 >= 3 个才认为覆盖充足，否则 soft_fail |
| 餐厅时段匹配 | lunch 槽位只召回 entity_type=restaurant，且开放午间营业 |
| 数据层级 | data_tier=S 或 A 的实体优先，B 级实体作为 fallback |

---

## 验收标准

- [ ] `assemble_trip(session, trip_request_id, template_code, scene)` 函数实现并可调用
- [ ] 装配完成后写入三张表，数据结构正确
- [ ] 实体不重复约束有效
- [ ] fallback 逻辑有效（无候选时不崩溃）
- [ ] planner_runs 追溯记录写入正确
