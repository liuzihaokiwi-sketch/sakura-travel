# Layer 2：决策与编排层实现方案 v1

> 目标：回答“这次旅行怎么排”，把数据层产出的城市圈/活动/酒店预设，转换成可执行的 `itinerary_days + itinerary_items + report_payload_vNext`。

---

## 1. 结论先说

当前项目对 Layer 2 的整理方向是对的，已经具备一条清晰的主链：

```text
normalize_profile
  → eligibility_gate
  → precheck_gate
  → select_circle
  → rank_major
  → build_hotel
  → build_skeleton
  → fill_secondary
  → fill_meals
  → itinerary_fit_scoring
```

这条链已经比旧的“模板驱动 → assembler 填槽 → AI 补解释”更合理，因为它把真正决定行程质量的部分提前到了“城市圈选择 / 主要活动选择 / 酒店基点 / 日骨架”这几步。

但工程上要把 Layer 2 做稳，不是只把模块文件建出来，而是要把它实现成：

1. **阶段化流水线**：每一阶段只做一种决策，不越权。
2. **纯函数优先**：阶段输入固定，输出固定，可重跑。
3. **阶段快照可落库**：每阶段都能复盘与回放。
4. **降级路径精确**：局部数据不足时只降级局部模块，不整条链回退。
5. **最终输出兼容旧下游**：仍然落到 `itinerary_days + itinerary_items + report_payload_vNext`。

---

## 2. Layer 2 在整套系统里的位置

整套系统建议这样看：

- **Layer 1：数据与知识层**
  - 城市圈、活动簇、角色、酒店预设、实体库、评分输入、运营事实
- **Layer 2：决策与编排层**
  - 本文对象：选圈、选主活动、定住法、排日骨架、填次要活动与餐厅
- **Layer 3：报告与渲染层**
  - 把 Layer 2 的结果变成 page plan / report payload / HTML / PDF
- **Layer 4：评测与运营层**
  - trace、质检、fallback、live risk、人工修正、版本演进

Layer 2 不是“数据查询 + 模板拼接”，而是**行程引擎**。

---

## 3. 不建议现在引入重型工作流引擎

从工程实现上，Layer 2 确实很像一个工作流 / 状态机：多个有序步骤、每步有输入输出、失败时需要恢复与重试。AWS Step Functions 官方就把 workflow 定义为由多个 state 组成的 state machine；Temporal 官方也强调 workflow execution 的事件历史、可恢复和确定性执行。  

但就当前项目阶段，不建议一开始就上 Temporal / Step Functions 一类重型编排引擎。

### 当前更合适的做法

继续使用现有 Python worker / job 主流程，做一个**轻量持久化编排器**：

- 主流程入口仍然在 `app/workers/jobs/generate_trip.py`
- 每个阶段是一个独立模块
- 每个阶段输入输出用 Pydantic / dataclass 定义
- 每个阶段结束后把结构化快照写入 `generation_decisions`
- 失败时从最近成功阶段继续跑

### 为什么这样更适合当前项目

- 现有项目已经有 `generate_trip.py + assembler + report_generator + renderer` 主链，不是空白项目
- 你们的风险主要不是分布式事务，而是**规则是否对、阶段输出是否稳、是否方便复盘**
- 先把阶段快照和接口定稳，比先上独立工作流平台更重要

---

## 4. 最终建议的实现形态

### 4.1 主流程入口

`app/workers/jobs/generate_trip.py`

职责：

- 接收 `plan_id`
- 读取表单 / trip profile
- 顺序调用 Layer 2 各阶段
- 每阶段写快照
- 发生错误时交给 `fallback_router`
- 最终输出给报告层

建议伪代码：

```python
profile = normalize_profile(plan_id)
write_decision(plan_id, "normalized_profile", profile)

eligible = eligibility_gate(profile)
write_decision(plan_id, "eligibility", eligible)

prechecked = precheck_gate(profile, eligible)
write_decision(plan_id, "precheck", prechecked)

circle_decision = city_circle_selector(profile, prechecked)
write_decision(plan_id, "circle_selection", circle_decision)

major_plan = major_activity_ranker(profile, circle_decision)
write_decision(plan_id, "major_activity_plan", major_plan)

hotel_plan = hotel_base_builder(profile, circle_decision, major_plan)
write_decision(plan_id, "hotel_strategy", hotel_plan)

skeleton = route_skeleton_builder(profile, circle_decision, major_plan, hotel_plan)
write_decision(plan_id, "day_frame", skeleton)

secondary_plan = secondary_filler(profile, skeleton, circle_decision)
write_decision(plan_id, "secondary_fill", secondary_plan)

meal_plan = meal_flex_filler(profile, skeleton, secondary_plan)
write_decision(plan_id, "meal_fill", meal_plan)

reranked = itinerary_fit_scorer(profile, skeleton, secondary_plan, meal_plan)
write_decision(plan_id, "itinerary_fit", reranked)

assembled = build_itinerary_records(reranked)
report_payload = build_report_payload_vnext(...)
```

---

## 5. 阶段实现细则

下面按模块说明怎么实现。

---

### 5.1 normalize_profile

**文件**：`app/workers/jobs/normalize_profile.py`

**职责**：把 DetailForm / 表单 / 已有用户输入，整理成 Layer 2 可消费的 `TripProfile`。

#### 输入

- detail form
- flight_info
- budget / pace / party_type
- must_go / avoid / free_text_wishes

#### 输出

`NormalizedTripProfile`

建议至少包含：

- `trip_days`
- `arrival_airport`
- `departure_airport`
- `arrival_day_shape`
- `departure_day_shape`
- `daytrip_tolerance`
- `hotel_switch_tolerance`
- `queue_tolerance`
- `weather_risk_tolerance`
- `food_priority`
- `photo_priority`
- `shopping_priority`
- `hotel_priority`
- `celebration_flags`
- `mobility_notes`
- `must_go_tags`
- `avoid_tags`

#### 当前缺口

这一层基础版已有，但**推导逻辑未做完**，这是当前 Layer 2 真正还没闭合的关键缺口之一。

#### 实现建议

- `arrival_day_shape`：由到达时间推导（早到 / 午到 / 晚到）
- `departure_day_shape`：由离开时间推导（早走 / 午走 / 晚走）
- `celebration_flags`：从 free text 抽取（纪念日 / 生日 / 求婚 / 带父母）
- `mobility_notes`：由老人 / 小孩 / 特别需求推导
- 将“决策层要用的稳定字段”作为显式字段输出，不只塞 JSON

---

### 5.2 eligibility_gate

**文件**：`app/domains/planning/eligibility_gate.py`

**职责**：pass/fail 过滤，不做排序。

#### 它应该过滤什么

- 永久关闭 / 长期停业
- 明显不在本次城市圈范围
- 明显超预算
- 季节不对
- 不符合同行条件
- 已知不可达
- 与用户硬性 avoid 冲突

#### 输出

```python
EligibilityResult(
  passed_entity_ids=[],
  rejected_entity_ids=[],
  rejected_reason_codes=[]
)
```

#### 实现原则

- 这是 **gate**，不是扣分器
- 被过滤掉的对象后续不再进入 major / secondary / meal pool
- reason code 必须可追踪，方便 explain 与调试

---

### 5.3 precheck_gate

**文件**：`app/domains/planning/precheck_gate.py`

**职责**：消费已知运营事实，把“提前可规避的风险”在生成前处理掉。

#### 与 eligibility_gate 的区别

- eligibility：实体层硬过滤
- precheck：结合时间、运营日历、票务、营业快照做**本次行程特定时间点**的过滤

#### 应消费的数据

- `PoiOpeningSnapshot`
- `EntityOperatingFact`
- 预约窗口 / 售罄状态
- 已知维护 / 已知闭园 / 固定休馆

#### 输出

```python
PrecheckResult(
  valid_major_candidates=[],
  invalid_candidates=[],
  warnings=[],
  fallback_hints=[]
)
```

#### 关键建议

- 一定要在 `select_circle / rank_major` 前跑
- 这里处理的是 **前置可规避风险**，不是 live risk
- 结果应进入 explain：比如“这次未选择 A，因为本周闭馆 / 已售罄”

---

### 5.4 city_circle_selector

**文件**：`app/domains/planning/city_circle_selector.py`

**职责**：在候选圈中选择本次主圈 / 扩展圈。

#### 输入

- `NormalizedTripProfile`
- `PrecheckResult`
- `city_circles`

#### 建议评分维度

至少 8 维：

1. `must_go_fit`
2. `airport_fit`
3. `season_fit`
4. `pace_fit`
5. `daytrip_tolerance_fit`
6. `hotel_switch_tolerance_fit`
7. `transfer_penalty`
8. `hotel_instability_penalty`

#### 输出

```python
CircleSelectionDecision(
  selected_circles=[],
  rejected_circles=[],
  reason_codes=[],
  confidence_score=0.0
)
```

#### 规则建议

- `< 7` 天：默认只允许 1 个完整圈
- `7-9` 天：1 个主圈 + 0~1 个轻扩展圈
- `10+` 天：开放 2 个完整圈

#### 当前建议

如果现在线上版本还是 6 维打分，建议扩成 8 维，把 `daytrip_tolerance` 和 `hotel_switch_tolerance` 显式纳入，不要全混进 pace。

---

### 5.5 major_activity_ranker

**文件**：`app/domains/planning/major_activity_ranker.py`

**职责**：从圈内 major pool 里选本次值得占半天 / 一天 / 改酒店的核心活动。

#### 输入

- `NormalizedTripProfile`
- `CircleSelectionDecision`
- `activity_clusters`
- base quality / context fit scoring

#### 不建议的做法

不要把 risk 继续混成统一总分。

#### 推荐公式

```python
major_score = 0.55 * base_quality_score + 0.45 * context_fit_score
```

风险改为独立字段：

- `precheck_status`
- `live_disruption_risk_level`

#### 输出

```python
MajorActivityPlan(
  selected_major_ids=[],
  rejected_major_ids=[],
  why_selected=[],
  why_not_selected=[],
  capacity_units=[],
)
```

#### 关键建议

- major 不是单个点，而是活动簇 / corridor driver
- 到达日 / 离开日容量按 0.5，中间日按 1.0
- 同一 major 必须带 `why_selected`，后面报告直接复用

---

### 5.6 hotel_base_builder

**文件**：`app/domains/planning/hotel_base_builder.py`

**职责**：确定住几个基点、每个基点住几晚、最后一晚是否安全。

#### 输入

- `NormalizedTripProfile`
- `MajorActivityPlan`
- `hotel_strategy_presets`

#### 规则建议

- 默认一个基点撑 3–4 晚
- 只有“节省显著通勤时间”或“酒店本身是主要活动”才换酒店
- 最后一晚要计算 `last_night_safe`

#### 输出

```python
HotelBaseStrategy(
  bases=[],
  nights_per_base=[],
  switch_reason_codes=[],
  last_night_safe=True,
  airport_margin_minutes=0,
)
```

#### 当前建议

这一步不只输出“选了哪个预设”，还要输出：

- 覆盖了哪些 major
- 如果不换酒店会损失什么
- 是否允许人工 override

---

### 5.7 route_skeleton_builder

**文件**：`app/domains/planning/route_skeleton_builder.py`

**职责**：先排“每天的主线和容量”，不先填满具体实体。

这是 Layer 2 最重要的模块。

#### DayFrame 不应只有 5 个字段

建议定成 11 个字段以上：

```python
DayFrame(
  day_index,
  sleep_base,
  primary_corridor,
  main_driver,
  secondary_capacity,
  transfer_budget_minutes,
  first_slot_type,
  last_slot_type,
  reservation_windows,
  meal_windows,
  cut_order,
)
```

还可以继续补：

- `weather_mode`
- `fallback_corridor`
- `must_keep_ids`
- `energy_level`

#### 原则

- 这一步“排天”，不决定所有 POI
- 每天先锁 1 个 main_driver
- 再给 secondary / meal 留容量
- `cut_order` 在这里就要先定，不要等报告时才编

#### 输出

`day_frames[]`

#### 当前建议

你现在提的“11 字段约束”方向是对的，建议把 `transfer_budget_minutes / reservation_windows / meal_windows / fallback_corridor` 明确写进 schema，不然 secondary / meal 两层会反过来决定日骨架。

---

### 5.8 secondary_filler

**文件**：`app/domains/planning/secondary_filler.py`

**职责**：在已锁定的日骨架里，往合适的 corridor 里补次要活动。

#### 输入

- `day_frames[]`
- `circle_entity_roles`
- `secondary activity pool`

#### 原则

- 只能在 `day_frame` 给的 corridor / capacity 内补
- 不能为了补一个次要活动推翻 main_driver
- `detour_cost` 动态计算，不建议做实体静态字段

#### 输出

```python
SecondaryFillResult(
  day_secondary_items=[],
  skipped_items=[],
  cut_candidates=[]
)
```

#### 当前建议

- `same_corridor_bonus`
- `backtrack_penalty`
- `weather_flexibility`
- `can_be_cut_first`

这些都应作为 secondary rerank 的显式因子。

---

### 5.9 meal_flex_filler

**文件**：`app/domains/planning/meal_flex_filler.py`

**职责**：按餐窗和当天动线填餐厅。

#### 餐厅建议分层

- `destination_meal`
- `route_meal`
- `backup_meal`

#### 输入

- `day_frames[]`
- `secondary fill result`
- restaurant score / tags / booking hints

#### 原则

- 先满足主驱动的节奏
- 再满足用餐时间窗
- route_meal 不要让用户专门绕大路
- backup_meal 必须真实可替代

#### 输出

```python
MealFillResult(
  day_meals=[],
  backup_meals=[],
  meal_conflicts=[]
)
```

---

### 5.10 itinerary_fit_scorer

**文件**：`app/domains/planning/itinerary_fit_scorer.py`

**职责**：在日骨架已成形后，对 day 内对象做最终重排。

#### 这一步为什么不能放前面

因为它评估的是：

- 绕路成本
- 前后衔接
- 时间窗兼容
- 是否回头路
- 单日节奏平衡

这些都必须在 skeleton 已出来之后才能算。

#### 推荐因子

- `corridor_fit`
- `sequence_fit`
- `time_window_fit`
- `backtrack_penalty`
- `rhythm_balance`

#### 输出

- 最终 day item 排序
- 调整后的 cut order
- 低置信度提醒

#### 当前建议

这一步不应只是“最后打一遍分”，而应允许做小范围替换：

- 用同 corridor 候选替换一个回头路严重的次要活动
- 用 backup_meal 替换一个时间窗冲突的 route_meal

---

## 6. 与现有系统的兼容方式

当前项目不是重写，而是“在 assembler 上游加一层城市圈决策层”，这个方向是对的。

### 兼容原则

Layer 2 最终仍然要落到现有下游能消费的形态：

- `itinerary_days`
- `itinerary_items`
- `report_payload_vNext`

### 具体桥接建议

- `route_skeleton_builder` 输出的 `day_frames[]` 转成 `ItineraryDay`
- `secondary_filler + meal_flex_filler` 产出 `ItineraryItem`
- 原有 `assembler._fill_slot()` 逻辑可抽取复用为次级排序器
- `report_generator` 不再决定结构，只消费 Layer 2 结果和 explain 字段

---

## 7. 一定要补的落库层：generation_decisions

你贴的当前状态里，**唯一明确还没做但又非常关键的，是 `generation_decisions` 表**。

这是 Layer 2 能不能复盘、调试、复用的关键。

### 建议表结构

```sql
id UUID PK
plan_id UUID
stage TEXT
payload JSONB
version TEXT
input_hash TEXT
is_current BOOLEAN DEFAULT TRUE
created_at TIMESTAMP
```

### 至少落 8 类快照

1. `normalized_profile`
2. `eligibility`
3. `precheck`
4. `circle_selection`
5. `major_activity_plan`
6. `hotel_strategy`
7. `day_frame`
8. `secondary_fill`
9. `meal_fill`
10. `itinerary_fit`

### 为什么必须做

- 方便 debug：知道是选圈错了还是骨架错了
- 方便 explain：把“为什么这样排”从事实快照里拿，不靠 AI 瞎补
- 方便 partial rerun：只重跑某阶段
- 方便后续评测和模板复用

---

## 8. fallback_router 怎么做才对

你现在的方向是对的：做**分阶段降级**，不要整条链一出问题就回旧模板。

### 建议降级粒度

- 没有圈数据 → 回旧模板
- 圈数据有，但 major pool 不够 → 仅降级 major selection
- skeleton 能排，但 secondary 不足 → 仅降级 secondary filler
- meals 不足 → 仅降级餐厅 filler
- report payload 不足 → 使用简化版报告模板

### 原则

降级一定要留下 reason code，且写进 `generation_decisions`。

---

## 9. 当前清单里我认为还缺的 3 件事

### 9.1 normalize 推导增强

你自己的状态表里也已经标出来了，这个确实还没闭合。

这是 P0/P1 的真实关键项，不补的话：

- select_circle 会太粗
- major ranking 的 context_fit 不够准
- explain 页的“你的偏好如何被兑现”不好写

### 9.2 explain 字段与 Layer 2 同步生成

不要等报告时才临时写“为什么这样安排”。

建议 Layer 2 每个核心阶段同步产出 explain：

- `why_selected`
- `why_not_selected`
- `expected_tradeoff`
- `fallback_hint`

### 9.3 trace 与评测

Layer 2 没有 trace，就很难做对比评测。

至少要能回答：

- 为什么选了东京圈不是关西圈
- 为什么选了镰仓没选箱根
- 为什么最后一晚切到机场友好酒店
- 为什么 Day 3 不给第二个 main driver

---

## 10. 推荐开发顺序

### 第一批：让主链真正可复盘

1. `normalize_profile` 推导增强
2. `generation_decisions` 表
3. `generate_trip.py` 按阶段写快照
4. `fallback_router` 接入 reason code

### 第二批：让骨架稳

5. `route_skeleton_builder` 扩成完整 `DayFrame`
6. `secondary_filler` 严格受 `day_frame` 约束
7. `meal_flex_filler` 接 `meal_windows`
8. `itinerary_fit_scorer` 支持小范围替换

### 第三批：让解释和报告直接受益

9. 每阶段增加 explain 字段
10. report payload 直接消费 Layer 2 explain
11. 让前端页面显示 circle / major / hotel / day_frame 的决策证据

---

## 11. 一句话版实施原则

**Layer 2 不要做成“大函数拼逻辑”，而要做成“阶段化、可落库、可回放、可局部降级”的轻量工作流”。**

更具体一点：

- `normalize / gate / select / rank / build / fill / rerank` 各司其职
- 每阶段输出结构化对象
- 每阶段都能写 `generation_decisions`
- 最终兼容现有 `itinerary_days + itinerary_items + report_payload_vNext`
- 先不上重型工作流平台，先把当前 Python 主流程做成可持久化编排器

---

## 12. 最终判断

你现在贴出来的 Layer 2 清单，**主骨架已经成立**，而且方向是对的：从模板驱动转向城市圈驱动，把 AI 收缩到解释层。

真正还没闭合的只有两类：

1. **阶段持久化与回放**：`generation_decisions` 还没做
2. **画像推导增强**：normalize 还没把 arrival/daytrip/celebration/mobility 等推导补齐

只要这两块补上，Layer 2 就不再只是“代码文件存在”，而会变成一条真正可上线、可复盘、可继续扩圈的行程引擎。
