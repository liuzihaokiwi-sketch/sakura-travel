# 代码审计报告：约束真源与消费链路

> **审计模式**：只读 Explore，不改代码  
> **审计日期**：2026-03-23  
> **审计范围**：`app/workers/`, `app/domains/planning/`, `app/domains/ranking/`, `app/domains/rendering/`  
> **关注问题**：用户约束是否有单一真源(Single Source of Truth)?

---

## A. 主链路调用顺序

```
normalize_trip_profile()         ← workers/__main__.py:281
  ├→ derive_profile_tags()       ← workers/__main__.py:64   (推导 must_have/avoid/nice_to_have)
  ├→ _derive_circle_signals()    ← workers/__main__.py:113  (推导 arrival_shape/departure_day_shape/tolerance)
  └→ TripProfile 写库            ← workers/__main__.py:313

generate_trip()                  ← workers/jobs/generate_trip.py:821
  └→ _try_city_circle_pipeline()   ← :197
      ├─ EligibilityContext(avoid_tags=profile.avoid_tags)  ← :337   ← 直接读 profile 字段
      ├─ run_eligibility_gate(session, eg_ctx)              ← :343
      ├─ rank_major_activities(session, profile, ...)       ← :381   ⚠️ 无 constraints 参数
      ├─ build_hotel_strategy(session, profile, ...)        ← :449
      ├─ build_route_skeleton(pace=profile.pace)            ← :481   ⚠️ 无 constraints 参数
      ├─ fill_secondary_activities(profile_dict, ...)       ← :559   ⚠️ 用 dict 传 3 个字段
      ├─ fill_meals(profile_dict, ...)                      ← :604   ⚠️ 无 constraints 参数
      ├─ assemble_trip / build_itinerary_records            ← :722/750
      ├─ generate_report_v2(user_ctx, ...)                  ← :944
      └─ render_export(plan_id)                             ← 由 guardrails 入队

run_guardrails()                 ← workers/jobs/run_guardrails.py:156
  └→ _check_plan()               ← :36   (纯结构检查，不读 profile 约束)

render_export()                  ← workers/jobs/render_export.py:21
  └→ render_html / render_pdf    ← :66/:83  (纯渲染，不读 profile 约束)
```

**关键发现**：`constraint_compiler.py` 已编写完成并具备完整能力，但 `generate_trip.py` 中**从未调用** `compile_constraints()`。所有下游模块在生产管线中**仍然直接读取 `profile.*` 原始字段**。

---

## B. 约束的"写—编译—消费"全景表

| # | 约束名 | 写入来源 | constraint_compiler 是否编译 | 实际消费文件 | 消费方式 | 断裂描述 |
|---|--------|---------|-----|------|------|----------|
| 1 | `avoid_tags` | `__main__.py:71` → `TripProfile.avoid_tags` | ✅ → `blocked_tags` | `eligibility_gate.py:337` | EG-006 标签过滤 | **gate 直接读 profile，未经 compiler**；ranker/skeleton/filler 的 `constraints` 参数在 `generate_trip` 中**未传** |
| 2 | `must_have_tags` | `__main__.py:69` → `TripProfile.must_have_tags` | ✅ → `preferred_tags_boost` | `major_activity_ranker.py:198,331` 直读 profile | 软加分 (+8 context_fit) | **ranker 直读 profile.must_have_tags，未使用 compiler 的 boost dict** |
| 3 | `pace` | `__main__.py:335` → `TripProfile.pace` | ✅ → `max_intensity` | `generate_trip.py:485` → skeleton(pace=str) / `generate_trip.py:555` → profile_dict | 字符串透传 | **skeleton 接收原始 pace 字符串再自行映射，compiler 的 `max_intensity` int 未被使用** |
| 4 | `party_type` | `__main__.py:335` 写库 | ✅ → `party_block_tags`, `party_fit_penalty` | `eligibility_gate.py:338`, `assembler.py:82`, `generate_trip.py:554` | 各模块自行解读 | **三处独立映射：`__main__` 有 `PARTY_TYPE_TAG_RULES`，compiler 有 `_PARTY_RULES`，assembler 有 `_PARTY_TO_SEGMENT`——逻辑可能不一致** |
| 5 | `has_elderly` / `has_children` | `__main__.py:157-159` 推导 | ✅ → `max_intensity_override`, `departure_day_no_poi` | `eligibility_gate.py:339-340` | gate 用 bool 做 EG-004 | **compiler 额外推导了 `max_intensity` 上限和 `departure_day_no_poi`——但 gate 不用这些字段，骨架也不用** |
| 6 | `departure_day_no_poi` | — | ✅ compiler 推导 | **无人消费** | — | **⛔ Dead Constraint：compiler 编译了，但 `build_route_skeleton` 没有读取此字段** |
| 7 | `departure_meal_window` | — | ✅ compiler 推导 (基于 `last_flight_time`) | `route_skeleton_builder.py:_set_meal_windows` 签名支持，但 `generate_trip.py` **未传 constraints** | — | **⛔ 断裂：skeleton 的函数签名已就绪，但调用方没传——生产中永远走 `constraints=None` 默认分支** |
| 8 | `arrival_evening_only` | — | ✅ compiler 推导 | 同上 | — | **⛔ 同 #7** |
| 9 | `avoid_cuisines` | — | ✅ compiler 推导 | `meal_flex_filler.py:282` 签名支持 | — | **⛔ 同 #7——filler 有参数但 generate_trip 未传** |
| 10 | `must_stay_cities` | — | ✅ compiler 推导 | **无人消费** | — | **⛔ hotel_base_builder 不读此字段** |
| 11 | `budget_level` | `__main__.py:82` → 推导 avoid/nice_to_have tags | ❌ compiler 不处理 | `assembler.py:_build_user_weights` (不用)；`generate_trip.py:554` → profile_dict | 透传给 secondary_filler | 无编译层 |
| 12 | `arrival_airport` / `departure_airport` | `__main__.py:132-133` 推导 | ❌ compiler 不处理 | `hotel_strategy_builder` 内部自读 profile | 直读 | 无编译层 |

---

## C. 重复推导（Double Source of Truth）

以下逻辑在两处以上独立实现，彼此可能不一致：

### C1. party_type → 标签规则

| 位置 | 映射方式 | 产物 |
|------|---------|------|
| `__main__.py:25-60` `PARTY_TYPE_TAG_RULES` | party → must_have / nice_to_have / avoid | 写入 `TripProfile.avoid_tags` 等 |
| `constraint_compiler.py:167-183` `_PARTY_RULES` | party → block_unless_must_go / penalty / max_intensity_override | `PlanningConstraints.party_block_tags` 等 |
| `assembler.py:46-57` `_PARTY_TO_SEGMENT` | party → segment_pack_id (权重包) | 用于 context_score 计算 |

**风险**：`__main__` 可能将 `theme_park` 放入 avoid，而 compiler 的 `_PARTY_RULES` 只将其 "block_unless_must_go"（允许用户显式指定去）。两个逻辑的语义冲突：**一个是无条件 avoid，一个是有条件 block**。

### C2. pace → 强度上限

| 位置 | 映射 |
|------|------|
| `constraint_compiler.py:153-158` `_PACE_TO_MAX_INTENSITY` | `"relaxed"→0, "moderate"→1, "packed"→2` |
| `route_skeleton_builder.py:627` `max_allowed_intensity_name()` | 调用 compiler 的函数（✅ 一致） |
| `generate_trip.py:485` | 传 `pace=profile.pace` 字符串给 skeleton，skeleton 内部再做一次映射 | 

**风险**：如果 skeleton 内部映射和 compiler 映射不同步，结果就会不一致。

### C3. arrival/departure 日形态

| 位置 | 推导 |
|------|------|
| `__main__.py:146-152` `_infer_day_shape_arrival/departure` | 写入 `TripProfile.arrival_day_shape` / `departure_day_shape` |
| `constraint_compiler.py:~280` | 从 profile 读取后再转换成 `arrival_evening_only`, `departure_meal_window` |

**风险**：两层转换，如果 `__main__` 的 `_infer_day_shape_*` 输出了 compiler 不认识的值，compiler 就会 fallback 到默认值。

---

## D. Dead Constraints（编译了但无人消费）

| 约束 | compiler 字段 | 原因 |
|------|--------------|------|
| `departure_day_no_poi` | `PlanningConstraints.departure_day_no_poi` | `build_route_skeleton` 签名中无此参数，skeleton 内部自行判断 |
| `must_stay_cities` | `PlanningConstraints.must_stay_cities` | hotel_strategy_builder 直读 profile |
| `must_stay_area` | `PlanningConstraints.must_stay_area` | 同上 |
| `blocked_clusters` | `PlanningConstraints.blocked_clusters` | ranker 的 `constraints.blocked_clusters` 签名已支持，但 generate_trip 未传 constraints |
| `party_fit_penalty` | `PlanningConstraints.party_fit_penalty` | ranker 签名已支持，但 generate_trip 未传 |

---

## E. 语义泄漏点

### E1. Renderer 不读约束——但可能该读

`renderer.py` 的 `_build_render_context()` 纯粹从 `ItineraryPlan` → `ItineraryDay` → `ItineraryItem` 组装数据。它：

- 不读 `TripProfile`
- 不读 `PlanningConstraints`
- 日标题(`day_theme`) 来自 `ItineraryDay.day_theme` 字段

**问题**：`day_theme` 是谁写入的？追溯到 `generate_trip.py:~750` 的 `build_itinerary_records`，它从 skeleton frame 的 `main_driver` 或 cluster name 拼接生成。如果 cluster name 含有"紅葉"而用户 3 月出行，这个季节性标题就会泄漏到 PDF——**renderer 无法防御，因为它不知道旅行季节**。

### E2. Assembler 的 _PARTY_TO_SEGMENT 没走 compiler

`assembler.py:46-57` 定义了自己的 party → segment 映射。它用于构建评分权重包(weight packs)。这和 compiler 的 `_PARTY_RULES` 、`__main__` 的 `PARTY_TYPE_TAG_RULES` 形成**三套独立的 party 解读逻辑**。

### E3. Scorer 是约束无感的

`scorer.py` 的 `compute_base_score()` 和 `compute_context_score()` 均为纯函数，不接收任何 `PlanningConstraints` 参数。这本身是好的设计（评分不该被约束左右），但 `compute_candidate_score()` 在 assembler 中被调用时，用户的 `must_have_tags` 加分是 assembler 自行 +8 实现的——**这和 compiler 的 `preferred_tags_boost` 逻辑重复**。

---

## F. 诊断结论与 Severity 分级

### 🔴 Critical（会产生错误行程）

| ID | 问题 | 影响 |
|----|------|------|
| **F1** | `generate_trip.py` 从未调用 `compile_constraints()`，所有 `constraints=` 参数传 None | compiler 编译的 departure_meal_window / arrival_evening_only / blocked_clusters **全部失效**；返程日照排午餐、到达日深夜照排午餐 |
| **F2** | `party_type` 三处独立映射，语义不一致 | `family_multi_gen`(三代同堂) 在 `__main__` 可能不在映射表中(缺失该 key)，compiler 有 block 规则，assembler 映射到 `"parents"` 包——三者行为不同 |
| **F3** | `day_theme` 直接使用 cluster name，未做季节过滤 | 3月行程出现"紅葉名所"标题 |

### 🟡 High（会降低行程质量）

| ID | 问题 | 影响 |
|----|------|------|
| **F4** | `avoid_cuisines` 编译了但 `fill_meals` 未收到 | 用户说"不吃生鱼"但行程照排寿司/刺身 |
| **F5** | `must_have_tags` 的加分在 ranker 和 assembler 各做一次(+8) | 可能双倍加分，或如果只走其中一条路径则效果不稳定 |
| **F6** | Dead Constraints (`must_stay_cities`, `must_stay_area`) 给用户"已处理"的假象 | 用户指定住京都站附近，实际不生效 |

### 🟢 Medium（架构债务，不直接出错）

| ID | 问题 | 影响 |
|----|------|------|
| **F7** | pace 映射在 compiler 和 skeleton 内部各做一次 | 目前值恰好一致，但无同步保证 |
| **F8** | eligibility_gate 有自己的 `EligibilityContext` dataclass，和 `PlanningConstraints` 字段高度重叠 | 维护两套 dataclass 增加出错概率 |
| **F9** | scorer 是约束无感的（纯函数），但 assembler 手动给 must_have 加分 | 加分逻辑散落在调用方 |

---

## G. 修复路线图建议

> ⚠️ 以下为审计建议，不在 Explore 阶段实施。

### Phase 1: 接通 Compiler（消除 F1/F4/F6，最高优先级）

```
generate_trip.py:_try_city_circle_pipeline() 顶部加入:

    from app.domains.planning.constraint_compiler import compile_constraints
    constraints = compile_constraints(profile)

然后把 constraints 透传给:
    ├─ rank_major_activities(..., constraints=constraints)
    ├─ build_route_skeleton(..., constraints=constraints)
    ├─ fill_secondary_activities(..., constraints=constraints)
    └─ fill_meals(..., constraints=constraints)
```

预计改动：**1 个文件，~10 行**。

### Phase 2: 合并 EligibilityContext（消除 F8）

让 `run_eligibility_gate` 接受 `PlanningConstraints` 而非自建 `EligibilityContext`，或者让 compiler 输出一个 `to_eligibility_context()` 方法。

预计改动：**2 个文件，~30 行**。

### Phase 3: party_type 统一（消除 F2）

将 `__main__.py` 的 `PARTY_TYPE_TAG_RULES`、compiler 的 `_PARTY_RULES`、assembler 的 `_PARTY_TO_SEGMENT` 合并到一个 `party_rules.py` registry，由 compiler 统一读取。

预计改动：**新建 1 文件，改 3 文件**。

### Phase 4: day_theme 季节防御（消除 F3）

在 `build_itinerary_records` 生成 `day_theme` 时注入 `travel_month`，对含季节关键词的 cluster name 做验证/替换。

预计改动：**1-2 个文件**。

---

## H. 约束流向可视化

```
                          ┌────────────────────────────────┐
                          │     normalize_trip_profile()    │
                          │   ┌─────────────────────────┐  │
  raw_input ─────────────▶│   │ derive_profile_tags()   │  │
                          │   │ _derive_circle_signals() │  │
                          │   └──────────┬──────────────┘  │
                          │              ▼                  │
                          │     TripProfile (DB)           │
                          └──────────────┬─────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
         ┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
         │  Eligibility │    │ generate_trip.py  │    │ constraint   │
         │  Gate        │    │ (orchestrator)    │    │ _compiler.py │
         │              │    │                   │    │              │
         │ 直接读       │    │ 直接读 profile.*  │    │ 编译 profile │
         │ profile.*    │    │ 透传给各模块      │    │ → Planning   │
         │              │    │                   │    │   Constraints│
         └──────┬───────┘    └───┬───┬───┬──────┘    └──────┬───────┘
                │                │   │   │                   │
                ▼                ▼   ▼   ▼                   ▼
           pass/fail        ranker skeleton filler    ⛔ 无人调用
                            (constraints=None)        (Dead Code)
                            ↓ 各模块 fallback 到默认值

        ════════════════════════════════════════════════════
        理想状态（Phase 1 修复后）：
        ════════════════════════════════════════════════════

                          ┌────────────────────────────────┐
                          │     normalize_trip_profile()    │
                          └──────────────┬─────────────────┘
                                         │
                                         ▼
                                  TripProfile (DB)
                                         │
                          ┌──────────────┴─────────────────┐
                          │     compile_constraints()       │
                          │     (Single Source of Truth)     │
                          └──────────────┬─────────────────┘
                                         │
              ┌──────────┬───────────┬───┴────┬──────────┐
              ▼          ▼           ▼        ▼          ▼
          Eligibility  Ranker    Skeleton   Filler   Assembler
          Gate         (blocked  (meal      (avoid   (weight
          (avoid_tags  clusters, windows,   cuisine, packs)
           party)      boost)    intensity) city
                                            strict)
```

---

*审计完成。以下为基于审计结论的最小实施方案。*

---
---

# 最小实施方案："统一约束来源 + constraint_trace"

> **目标**：消除约束分散、消费不一致、无法追踪三个核心问题  
> **硬限制**：最多新增 1 文件，最多改 4 个已有文件，不做大重构，不碰 UI，不扩断言  
> **第一轮范围**：只接通已有的 compiler → 已有的下游签名，不新增约束字段

---

## A. 新增文件职责

**无需新增文件。**

`constraint_compiler.py` 已经存在且功能完备——它已实现：

| 已有能力 | 对应用户要求的字段 | 现状 |
|---------|-------------------|------|
| `blocked_clusters` | `blocked_clusters` | ✅ 已编译，ranker 签名已支持 |
| `must_stay_area` / `must_stay_cities` | `must_stay_area` | ✅ 已编译，无消费方 |
| `avoid_cuisines` | `avoid_cuisines` | ✅ 已编译，filler 签名已支持 |
| `max_intensity` | `max_intensity_level` | ✅ 已编译，skeleton 有 `max_allowed_intensity_name()` |
| `city_strict_day_types` | `city_strict_day_types` | ✅ 已有默认值 `{"theme_park","arrival","departure"}` |
| `preferred_tags_boost` | `preferred_tags_boost` | ✅ 已编译，ranker `_score_cluster` 签名已支持 |
| `constraint_trace` | `constraint_trace` | ✅ `ConstraintTraceItem` dataclass + `record_consumption()` 已实现 |

**缺的不是 compiler，而是 `generate_trip.py` 从未调用它。**

> 关于 `must_go_clusters`：当前 compiler 没有此字段，但用户要求的意图已被 `preferred_tags_boost` (must_have_tags → boost=10) + ranker 的 `default_selected` 逻辑覆盖。第一轮不新增字段，用现有机制。

---

## B. 每个修改文件要改哪一个函数

### 文件 1: `app/workers/jobs/generate_trip.py`（编排层接通）

| 函数 | 改动内容 |
|------|---------|
| `_try_city_circle_pipeline()` | 在 Step 4 (major_ranking) 之前新增 2 行：`from constraint_compiler import compile_constraints` + `constraints = compile_constraints(profile)` |
| `_try_city_circle_pipeline()` | Step 4: `rank_major_activities(..., constraints=constraints)` — 补传 constraints 参数 |
| `_try_city_circle_pipeline()` | Step 6: `build_route_skeleton(..., constraints=constraints)` — 补传 constraints 参数 |
| `_try_city_circle_pipeline()` | Step 8: `fill_meals(..., constraints=constraints)` — 补传 constraints 参数 (注意：需给 `fill_meals` 调用加 `constraints=` kwarg) |
| `_try_city_circle_pipeline()` | Step 9 之后(assembler 之前): 把 `constraints.constraint_trace` 序列化写入 `PlannerRun.trace` 或 `plan_metadata["constraint_trace"]` |

**预计改动**：~15 行新增，0 行删除。

### 文件 2: `app/domains/planning/major_activity_ranker.py`（ranker 补 trace 记录）

| 函数 | 改动内容 |
|------|---------|
| `_score_cluster()` | 在现有 `constraints.record_consumption("blocked_clusters", ...)` 之后（:340行），为 `blocked_tags` 命中、`preferred_tags_boost` 命中也各加一次 `record_consumption` 调用 |

**预计改动**：~8 行新增。

当前 `_score_cluster` 已有的 constraints 消费逻辑（:332-343行）：
```python
avoid_tags = constraints.blocked_tags if constraints else set(...)
if constraints and constraints.blocked_clusters:
    if cluster.cluster_id in constraints.blocked_clusters:
        constraints.record_consumption("blocked_clusters", "ranker", ...)
```

需要补充的 trace 记录：
```python
# blocked_tags 命中时
if constraints and avoid_tags & profile_fit_tags:
    constraints.record_consumption("blocked_tags", "ranker", "tag_penalty", ...)

# preferred_tags_boost 消费时
if constraints and constraints.preferred_tags_boost:
    constraints.record_consumption("preferred_tags_boost", "ranker", "soft_boost", ...)
```

### 文件 3: `app/domains/planning/route_skeleton_builder.py`（skeleton 补 trace 记录）

| 函数 | 改动内容 |
|------|---------|
| `_set_meal_windows()` | 当 `constraints` 非 None 时，在应用 `departure_meal_window` 和 `arrival_evening_only` 后调用 `constraints.record_consumption(...)` |
| `_mark_intensity()` | 当 constraints 限制了 max_intensity 时调用 `constraints.record_consumption("max_intensity", "skeleton", ...)` |

**预计改动**：~10 行新增。

当前 `_set_meal_windows` 已有条件判断（读取 `constraints.departure_meal_window` 等），只差 trace 记录。

### 文件 4: `app/domains/planning/meal_flex_filler.py`（filler 补 trace 记录）

| 函数 | 改动内容 |
|------|---------|
| `fill_meals()` | 在现有 `:289-291` 行（已读取 `constraints.avoid_cuisines`）之后，加 `constraints.record_consumption("avoid_cuisines", "filler", ...)` |
| `fill_meals()` | 在 city_strict 过滤处，加 `constraints.record_consumption("city_strict_day_types", "filler", ...)` |

**预计改动**：~6 行新增。

---

## C. 每个函数新增什么参数

| 函数 | 现有签名 | 变更 |
|------|---------|------|
| `generate_trip._try_city_circle_pipeline` | 内部函数，无签名变更 | **不变**——constraints 在函数体内创建 |
| `rank_major_activities(...)` | 已有 `constraints: PlanningConstraints \| None = None` | **不变** |
| `_score_cluster(...)` | 已有 `constraints: PlanningConstraints \| None = None` | **不变** |
| `build_route_skeleton(...)` | 已有 `constraints: PlanningConstraints \| None = None` | **不变** |
| `_set_meal_windows(frames, wake_up, constraints=None)` | 已有 `constraints` | **不变** |
| `fill_meals(...)` | 已有 `constraints` 参数 (:282) | **不变** |

> **核心结论**：所有下游函数的签名已经在之前的 Round 2 中完成了。第一轮实施**不需要改任何签名**，只需要在调用方传入实参。

---

## D. constraint_trace 的字段设计

`ConstraintTraceItem` **已存在**于 `constraint_compiler.py`，字段如下：

```python
@dataclass
class ConstraintTraceItem:
    constraint_name: str          # e.g. "blocked_tags", "max_intensity"
    source_inputs: str            # e.g. "profile.avoid_tags=['raw','crowd']"
    compiled_value: str           # e.g. "{'raw','sushi','sashimi','crowd'}"
    strength: str = "hard"        # "hard" | "soft"
    intended_consumers: list[str] # e.g. ["ranker","skeleton"]
    consumption_events: list[dict] = []  # 下游调用 record_consumption() 追加
    final_status: str = "pending" # "pending" → "partially_consumed" → "fully_consumed"
    ignored_reason: str = ""      # 如果 unconsumed，记录原因
```

**consumption_events 的每条记录**：

```python
{
    "module": "ranker",           # 消费方模块名
    "action": "hard_block",       # 消费动作：hard_block / tag_penalty / soft_boost / meal_filter / intensity_cap
    "effect_summary": "cluster fushimi_inari zeroed",  # 人可读效果描述
    "reason": ""                  # 可选的补充原因
}
```

**新增的落库设计**（在 `generate_trip.py` 的 Step 9 之后）：

```python
# 序列化 trace 到 plan_metadata
plan_meta["constraint_trace"] = [
    {
        "name": t.constraint_name,
        "strength": t.strength,
        "value": t.compiled_value,
        "consumers": t.intended_consumers,
        "events": t.consumption_events,
        "status": t.final_status,
    }
    for t in constraints.constraint_trace
]
plan_meta["constraint_compiler_version"] = constraints.compiler_version
plan_meta["constraint_run_id"] = constraints.run_id
```

---

## E. 怎么验证约束真的被消费了

### E1. constraint_trace 自验证（零成本）

在 `generate_trip.py` 落库前自动检查：

```python
unconsumed = [
    t.constraint_name for t in constraints.constraint_trace
    if t.strength == "hard" and t.final_status == "pending"
]
if unconsumed:
    logger.warning(
        "⚠️ unconsumed hard constraints: %s (run_id=%s)",
        unconsumed, constraints.run_id,
    )
```

这段代码作为 **被动告警**，不阻断流程，但会在日志中暴露任何未被消费的硬约束。

### E2. 回归测试断言（已有框架，加 1 条）

在 `scripts/run_regression.py` 的 `score_plan()` 中加一条检查：

```python
# 验证 constraint_trace 存在且无 pending 硬约束
trace = plan_meta.get("constraint_trace", [])
hard_pending = [t for t in trace if t["strength"] == "hard" and t["status"] == "pending"]
if hard_pending:
    result.add_issue("constraint_unconsumed", f"{len(hard_pending)} hard constraints never consumed")
```

### E3. 人工抽查路径

查看任意行程的 `plan_metadata.constraint_trace`：

```sql
SELECT plan_metadata->'constraint_trace' 
FROM itinerary_plans 
WHERE plan_id = '<id>';
```

每条 trace 的 `events` 数组可以回答："这个约束被谁、在什么场景下、以什么方式消费了？"

### E4. 验证矩阵（第一轮覆盖的 7 个约束）

| 约束 | 消费模块 | 验证方式 | 期望 trace status |
|------|---------|---------|------------------|
| `blocked_tags` | ranker._score_cluster | 给一个 avoid_tags=["crowd"] 的 profile，检查含 "crowd" 的 cluster context_fit 是否为 0 | `partially_consumed` |
| `blocked_clusters` | ranker._score_cluster | 给一个 blocked_clusters=["xxx"] 的 profile，检查 xxx 不在 selected_majors | `partially_consumed` |
| `avoid_cuisines` | filler.fill_meals | 给 avoid_tags=["raw"]，检查行程无寿司/刺身 | `partially_consumed` |
| `max_intensity` | skeleton._mark_intensity | 给 pace="relaxed" + has_elderly=true，检查无 dense 日 | `partially_consumed` |
| `city_strict_day_types` | filler.fill_meals | 检查 arrival/departure 日无跨城餐厅 | `partially_consumed` |
| `preferred_tags_boost` | ranker._score_cluster | 给 must_have_tags=["sakura"]，检查 sakura cluster 分数有 boost | `partially_consumed` |
| `must_stay_area` | **本轮不接消费方** | trace 会显示 status="pending" | `pending` (已知) |

---

## F. 本轮明确不做什么

| 不做的事 | 原因 |
|---------|------|
| ❌ 新建 `party_rules.py` 统一 party_type 三套映射 | 属于 Phase 3 重构，影响面大 |
| ❌ 合并 `EligibilityContext` 和 `PlanningConstraints` | gate 在 constraints 之前执行（过滤 → 编译 → 排序），合并会改变执行顺序 |
| ❌ 让 hotel_base_builder 消费 `must_stay_area` / `must_stay_cities` | 需要改 hotel 策略模块内部逻辑，第一轮不碰 |
| ❌ 修复 day_theme 季节泄漏 | 涉及 cluster name 映射和渲染模块，属于独立 change |
| ❌ 碰 UI / 前端 | 不在范围内 |
| ❌ 新增大量回归断言 | 只加 E2 中的 1 条 constraint_unconsumed 检查 |
| ❌ 修改 scorer.py | scorer 应保持约束无感的纯函数设计 |
| ❌ 修改 renderer.py | 渲染层不应直接读约束，约束应在生成阶段生效 |
| ❌ 新增 `must_go_clusters` 字段 | 当前 `preferred_tags_boost` (must_have→10) + `default_selected` 已覆盖此需求 |
| ❌ 修改 `__main__.py` 的 `derive_profile_tags` | 入库逻辑不变，compiler 读库后的 profile 做二次编译 |

---

## 改动汇总

```
修改文件数：4
新增文件数：0
总新增行数：~39 行
总删除行数：0 行

┌──────────────────────────────────────────┬──────────┬──────────────────────────────────────┐
│ 文件                                      │ 新增行数 │ 改动点                                 │
├──────────────────────────────────────────┼──────────┼──────────────────────────────────────┤
│ workers/jobs/generate_trip.py            │ ~15      │ 编译 constraints + 传参 + 落库 trace   │
│ domains/planning/major_activity_ranker.py│ ~8       │ record_consumption × 2 处              │
│ domains/planning/route_skeleton_builder.py│ ~10     │ record_consumption × 2 处              │
│ domains/planning/meal_flex_filler.py     │ ~6       │ record_consumption × 2 处              │
└──────────────────────────────────────────┴──────────┴──────────────────────────────────────┘
```

**执行顺序建议**：

```
1. generate_trip.py  (接通 compiler — 一切的前提)
2. major_activity_ranker.py  (补 trace — 最多约束消费在这里)
3. route_skeleton_builder.py (补 trace)
4. meal_flex_filler.py       (补 trace)
5. 跑回归测试验证 constraint_trace 落库 + 无 pending 硬约束告警
```
