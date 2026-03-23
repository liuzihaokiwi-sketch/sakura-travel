# "假绿"根因分析：摘要懂用户，但 PDF 回到经典线

> **问题定义**：回归测试 Green，摘要/总纲文案读起来"懂用户"（写了三代同堂、写了relaxed pace），但最终 PDF 里的实际行程是伏见稻荷→岚山→东山清水寺——标准首刷游客线。  
> **分析方法**：逐层代码追踪，从 profile 入口到 PDF 出口，找出约束在哪一层"丢失"或"被覆盖"。

---

## 问题 1：约束是否只存在于 profile/summary/copywriter，但没进入 assembler？

### 结论：✅ 是。这是最严重的根因。

**证据链**：

```
profile.must_have_tags = ["family_child", "elderly"]
profile.avoid_tags = ["crowd", "steep_stairs"]
profile.pace = "relaxed"
        │
        ▼
_build_design_brief(profile, days)          ← report_generator.py:178
  → route_strategy: ["轻松深玩，减少城际移动"]
  → tradeoffs: ["主动放弃步行量大的区域"]
  → execution_principles: ["整体节奏：轻松"]
        │
        ▼
_P_OVERVIEW prompt (AI)                     ← report_generator.py:484
  → "为三代同堂家庭设计的轻松节奏..." ← AI 读到 profile 写出漂亮文案
        │
        ▼  ✅ 到这里，文案完美地"理解"了用户
========================================
        │  ⛔ 但以下是行程实体的真实来源：
        ▼
rank_major_activities(constraints=None)     ← generate_trip.py:381
  → _sort_key: (precheck_pass, is_must_go, major_score)
  → is_must_go = S级 + default_selected → 无条件排第一
  → 容量贪心选取 → S级经典线吃光容量
  → constraints=None → P5b/P5c/P5d 全部跳过
        │
        ▼
build_route_skeleton(constraints=None)      ← generate_trip.py:481
  → 骨架按经典线排布
  → _set_meal_windows(constraints=None) → 默认分支
        │
        ▼
fill_meals(constraints=None)                ← generate_trip.py:604
  → avoid_cuisines = set() → 不过滤任何菜系
```

**关键代码位置**：

| 文件 | 行号 | 问题 |
|------|------|------|
| `generate_trip.py` | :381 | `rank_major_activities(...)` 无 `constraints=constraints` |
| `generate_trip.py` | :481 | `build_route_skeleton(...)` 无 `constraints=constraints` |
| `generate_trip.py` | :604 | `fill_meals(...)` 无 `constraints=constraints` |
| `report_generator.py` | :178 | `_build_design_brief(profile, days)` 读 profile 写文案——**文案源 ≠ 行程源** |
| `report_generator.py` | :484 | AI prompt 注入了 design_brief——所以摘要写的是 profile 的理想状态 |

**结论**：摘要读的是 `profile`（用户告诉我们的），行程读的是 `default_selected + base_quality_score`（系统自己算的）。两者从未在同一条约束链上。

---

## 问题 2：排序结果是否覆盖了个性化偏好，回退成安全经典线？

### 结论：✅ 是。`_sort_key` 的 `is_must_go` 二元优先级导致 S 级经典线**无条件压制**个性化结果。

**根因代码** — `major_activity_ranker.py:201-213`：

```python
def _sort_key(r: RankedMajor):
    c = cluster_map.get(r.cluster_id)
    is_must_go = bool(c and c.default_selected and (c.level or "") == "S")
    return (
        r.precheck_status == "pass",  # ① pass 优先
        is_must_go,                   # ② S+default 必去——二元 True/False
        r.major_score,                # ③ 分高优先
    )
```

**问题拆解**：

1. **`is_must_go` 是布尔值，排在 `major_score` 前面**  
   → 只要 cluster 是 `level="S"` + `default_selected=True`，它就排在所有 A/B 级 cluster 前面，**无论 context_fit 分数多低**

2. **P4 的 `GENERIC_CLUSTERS` 惩罚太弱**（:399-406）  
   → 小众用户对经典线扣 `len(user_niche_tags) * 5`，最多 20 分  
   → 但 P1 给 S+default 加了 25 分（:363），净效果 = +5  
   → 然后 `_sort_key` 的 `is_must_go=True` 又把它拉到最前——**分数惩罚被排序优先级碾压**

3. **MMR 走廊去重对 S+default 豁免**（:243-247）  
   ```python
   is_must = bool(c_obj and c_obj.default_selected and (c_obj.level or "") == "S")
   if not is_must and corridor_count.get(corr, 0) >= max_per_corridor:
   ```
   → S 级不受走廊去重限制 → 如果 higashiyama、fushimi、arashiyama 都是 S+default，全部进入

4. **constraints=None 导致 P5b/P5c/P5d 全跳过**  
   → `party_block_tags` 不生效（三代同堂不 block 陡坡线）  
   → `party_fit_penalty` 不生效（party 不匹配也不扣分）  
   → `preferred_tags_boost` 不生效（用户的 family_child 偏好不加分）

**数值模拟**（以"三代同堂·轻松"用户 + 京都 5 日为例）：

| Cluster | level | default_selected | base_quality | context_fit (无 constraints) | is_must_go | 排序结果 |
|---------|-------|-----------------|-------------|------|-----------|---------|
| kyo_higashiyama_gion_classic | S | ✅ | 85 | 50+25=75 | **True** | **#1** |
| kyo_fushimi_inari | S | ✅ | 82 | 50+25=75 | **True** | **#2** |
| kyo_arashiyama_sagano | S | ✅ | 80 | 50+25=75 | **True** | **#3** |
| kyo_philosophers_walk (适合老人) | A | ❌ | 72 | 50+6=56 | False | **#7** ← 被挤出容量 |
| kyo_nishiki_market (适合家庭) | A | ❌ | 68 | 50+6=56 | False | **#8** ← 被挤出容量 |

→ 容量 = (5-2)×1.0 + 0.5 + 0.5 = 4.0，S 级吃掉 3.0，只剩 1.0 给个性化  
→ 哲学之道和锦市场等适合家庭的 A/B 级被 S 级碾压

---

## 问题 3：day_type/airport_day/arrival_day 约束是否只在局部模块生效？

### 结论：✅ 是。约束在 compiler 中推导，但 skeleton 和 filler 的调用链上断裂。

**约束流向追踪**：

```
__main__.py:146-152
  _infer_day_shape_arrival(arrive_time) → profile.arrival_day_shape = "evening_only"
  _infer_day_shape_departure(depart_time) → profile.departure_day_shape = "airport_only"
        │
        ▼
constraint_compiler.py:343-383
  arrival_day_shape → arrival_evening_only = True
  departure_day_shape → departure_day_no_poi = True, departure_meal_window = "none"
        │
        ▼  ✅ 编译完成
        ⛔ 但 generate_trip.py 从未调用 compile_constraints()
        │
        ▼
build_route_skeleton(constraints=None)    ← generate_trip.py:481
  → _set_meal_windows(frames, wake_up, constraints=None)
       → dep_meal_window = "breakfast_only"  ← 默认值，不是编译值
       → arrival_evening_only = False        ← 默认值
  → _assign_major_drivers(frames, ..., constraints=None)
       → departure_day 仍然可能分配 major activity
        │
        ▼
fill_meals(constraints=None)              ← generate_trip.py:604
  → constraints.city_strict_day_types 不生效
  → 到达日、离开日的餐厅不受约束
```

**具体泄漏场景**：

| 场景 | 预期行为 | 实际行为 | 代码位置 |
|------|---------|---------|---------|
| 20:00 到达关西机场 | arrival_evening_only=True，不排午餐和下午景点 | 照常排 12:00 午餐 + 14:00 景点 | `skeleton._set_meal_windows` 走 `constraints=None` 默认分支 |
| 10:00 航班离开 | departure_meal_window="none"，不排任何餐 | 排了早餐 + 午餐 | 同上 |
| 返程日 | departure_day_no_poi=True | 照常排 1-2 个景点 | `skeleton._assign_major_drivers` 走 `constraints=None` 默认分支 |

---

## 问题 4：render_export/renderer 是否重新取数，导致与 planner 不同源？

### 结论：⚠️ 部分是。renderer 从 DB 重新查询，但数据源本身是 planner 写入的，不会"另造"数据。真正的问题在于 **文案源和行程源分离**。

**数据流图**：

```
generate_trip.py
  ├─ build_itinerary_records() → 写入 ItineraryDay + ItineraryItem (DB)  ← 行程实体
  ├─ generate_report_v2()     → 写入 plan_metadata.report_v2 (DB)       ← 文案数据
  └─ enqueue run_guardrails → enqueue render_export

render_export.py:66
  └→ render_html(plan_id, render_session)           ← 新开 AsyncSession
      └→ _build_magazine_context(session, plan)
          ├─ 从 DB 查 ItineraryDay + ItineraryItem  ← ✅ 与 planner 写入一致
          ├─ 从 DB 查 EntityBase                     ← ✅ 实体数据一致
          └─ 从 plan_metadata 读 report_v2           ← ✅ 文案数据一致
```

**renderer 不会"另造"行程**，但有两个隐患：

| 隐患 | 代码位置 | 说明 |
|------|---------|------|
| `render_export.py:65` 新开独立 session | `async_session_factory()` | 如果 `generate_trip` 的 session 尚未 commit 就被 enqueue，理论上可能读到旧数据。但实际上 guardrails 在中间，有 commit 点，所以**目前安全** |
| `html_renderer.py:227` 逐实体 `session.get(EntityBase, entity_id)` | N+1 查询 | 不影响正确性，但如果 entity 在 planner 完成后被编辑（罕见），可能出现不一致。**不是假绿根因** |

**真正的问题**：renderer 忠实渲染了 `ItineraryDay.day_theme` 和 `ItineraryItem` 列表——而这些数据是由 `constraints=None` 的 planner 生成的经典线。renderer 本身没有错，**错在上游**。

---

## 问题 5：guardrails 是否只检结构，不检约束消费？

### 结论：✅ 完全是。guardrails 零约束意识。

**`run_guardrails.py:_check_plan()` 的 8 项检查**：

| # | 检查项 | 类型 | 是否涉及约束？ |
|---|--------|------|--------------|
| 1 | 行程有 ≥1 天 | 结构 | ❌ |
| 2 | 实体总数 ≥ 3 | 结构 | ❌ |
| 3 | 重复实体 ≤ 20% | 结构 | ❌ |
| 4 | swap_safety: 实体营业时间冲突 | 运营 | ❌ |
| 5 | swap_safety: 区域通勤合理性 | 运营 | ❌ |
| 6 | swap_safety: 同质化检查 | 质量 | ❌ |
| 7 | swap_safety: 开放时间匹配星期几 | 运营 | ❌ |
| 8 | swap_safety: 高风险实体预警 | 运营 | ❌ |

**guardrails 完全不检查的内容**：

- ❌ `avoid_tags` 是否在行程中出现
- ❌ `must_have_tags` 是否被满足
- ❌ `pace` 是否与实际 intensity 一致
- ❌ `party_type` 是否与行程内容匹配
- ❌ 返程日是否有 POI
- ❌ 到达日是否排了不该有的餐
- ❌ `constraint_trace` 是否有 pending 硬约束

**这就是为什么假绿能通过**：guardrails 说"结构 OK"，行程就被标记为 pass，直接进入 render_export。

---

## 根因列表（按严重度排序）

### 🔴 RC-1：compiler 断路——约束编译了但从未注入管线（Critical）

| 项 | 值 |
|----|-----|
| **代码位置** | `generate_trip.py:381` (ranker), `:481` (skeleton), `:604` (filler) |
| **机制** | `compile_constraints()` 从未被调用；三个下游模块的 `constraints` 参数永远是 `None` |
| **影响** | `blocked_tags`, `blocked_clusters`, `avoid_cuisines`, `max_intensity`, `departure_meal_window`, `arrival_evening_only`, `party_block_tags`, `party_fit_penalty`, `preferred_tags_boost` — **9 个约束全部失效** |
| **最小修复** | `generate_trip.py` `_try_city_circle_pipeline()` 顶部加 2 行编译 + 3 行传参 |
| **补 trace** | 修复后 `constraints.constraint_trace` 自动记录所有消费事件；落库到 `plan_metadata["constraint_trace"]` |

### 🔴 RC-2：_sort_key 的 is_must_go 碾压 context_fit（Critical）

| 项 | 值 |
|----|-----|
| **代码位置** | `major_activity_ranker.py:201-213` `_sort_key()`, `:243-247` MMR 豁免 |
| **机制** | `is_must_go` 是布尔值排在 `major_score` 前面；S+default_selected 无条件排第一且不受 MMR 走廊去重限制 |
| **影响** | 即使 constraints 接通后 context_fit 被正确计算，**S 级经典线仍然因排序优先级碾压个性化 A/B 级** |
| **最小修复** | 将 `is_must_go` 从排序优先级降为加分项：`_sort_key` 改为 `(precheck_pass, major_score + (20 if is_must_go else 0))`；同时取消 S 级的 MMR 豁免 |
| **补 trace** | 新增 trace: `"must_go_override"` → 记录哪些 cluster 因 S+default 被强制提升，以及提升了多少分 |

### 🔴 RC-3：摘要源 ≠ 行程源（Critical）

| 项 | 值 |
|----|-----|
| **代码位置** | `report_generator.py:178` `_build_design_brief(profile, days)`, `:484` `_P_OVERVIEW` prompt |
| **机制** | design_brief 从 `profile` dict 推导文案策略（节奏、party、风格），但行程实体来自 ranker + skeleton（完全不读 profile 的这些字段） |
| **影响** | 摘要写"为三代同堂设计的轻松节奏"，但实际行程是 3 条 S 级经典线（伏见稻荷 1000 级台阶），文案和行程**语义撕裂** |
| **最小修复** | 在 `_build_design_brief` 中注入 `selected_majors` 列表，让文案基于**实际选中的活动**而非 profile 的理想期望。或更彻底：让 design_brief 在 skeleton 之后生成 |
| **补 trace** | `plan_metadata["design_brief_source"]` = `"profile_only"` (当前) → `"profile+execution"` (修复后) |

### 🟡 RC-4：guardrails 零约束意识（High）

| 项 | 值 |
|----|-----|
| **代码位置** | `run_guardrails.py:36-153` `_check_plan()` |
| **机制** | 8 项检查全部是结构/运营检查，不检查约束是否被消费 |
| **影响** | 假绿顺利通过 guardrails 进入 render_export |
| **最小修复** | 在 `_check_plan` 尾部加 1 个检查：读 `plan_metadata["constraint_trace"]`，如有 `strength="hard"` + `status="pending"` 的条目 → 加入 soft_fail 警告 |
| **补 trace** | 无需额外 trace——复用 RC-1 落库的 `constraint_trace` |

### 🟡 RC-5：arrival/departure day 约束断路（High）

| 项 | 值 |
|----|-----|
| **代码位置** | `route_skeleton_builder.py:_set_meal_windows()` 的 `constraints=None` 分支; `generate_trip.py:481` 未传 constraints |
| **机制** | compiler 编译了 `departure_meal_window` 和 `arrival_evening_only`，但 skeleton 收到 `constraints=None`，走默认分支 |
| **影响** | 20:00 到达照排午餐；10:00 航班离开照排午餐+景点 |
| **最小修复** | **同 RC-1**——接通 compiler 后此问题自动解决（skeleton 的 `_set_meal_windows` 已有正确的 constraints 判断逻辑） |
| **补 trace** | `constraints.record_consumption("departure_constraints", "skeleton", "meal_window_set", ...)` |

### 🟢 RC-6：renderer 不验证语义一致性（Medium）

| 项 | 值 |
|----|-----|
| **代码位置** | `html_renderer.py:168-298` `_build_magazine_context()` |
| **机制** | renderer 忠实渲染 DB 数据，不检查 `day_theme` 与旅行季节是否匹配，不检查行程实体与 profile 约束是否一致 |
| **影响** | 如果上游（planner）出错，renderer 忠实放大错误到 PDF |
| **最小修复** | **第一轮不修**——renderer 不该做约束检查，应在 planner 层和 guardrails 层解决。但可以在 `_build_magazine_context` 中加 1 行 warning log：如果 `plan_metadata` 中有 `constraint_trace` 且有 pending 硬约束，打日志 |
| **补 trace** | 无 |

---

## 总结：假绿的形成机制

```
┌──────────────┐    ┌─────────────────┐    ┌────────────────┐    ┌──────────────┐
│  TripProfile  │    │  constraint     │    │  ranker +      │    │  renderer    │
│  (用户意图)    │───▶│  compiler       │    │  skeleton +    │    │  (PDF)       │
│               │    │  (已断路 ⛔)     │    │  filler        │    │              │
└──────┬───────┘    └─────────────────┘    │  (constraints  │    │  忠实渲染    │
       │                                    │   = None)      │    │  经典线行程  │
       │                                    └───────┬────────┘    └──────────────┘
       │                                            │
       │    ┌─────────────────┐                     │
       └───▶│  report_generator│                     │
            │  _build_design  │                     │
            │  _brief(profile)│                     │
            │                 │                     │
            │  → "轻松节奏"   │                     │
            │  → "三代同堂"   │                     │
            │  → "无障碍优先" │                     │
            └────────┬────────┘                     │
                     │                              │
                     ▼                              ▼
              摘要文案（漂亮）              行程实体（经典线）
                     │                              │
                     └──────────┬───────────────────┘
                                │
                         ┌──────▼──────┐
                         │  guardrails  │
                         │  (只查结构)  │
                         │  → PASS ✅   │ ← 假绿就在这里产生
                         └─────────────┘
```

**一句话根因**：摘要从 `profile` 生成（懂用户），行程从 `default_selected + base_quality` 生成（不懂用户），guardrails 只查结构不查语义一致性——三者合力制造了"假绿"。

---

## 修复优先级与依赖关系

```
RC-1 (接通 compiler)
  │
  ├──▶ RC-5 自动解决 (arrival/departure day)
  │
  └──▶ RC-2 (改 _sort_key) ← 必须在 RC-1 之后，否则 context_fit 无效
         │
         └──▶ RC-3 (design_brief 注入 selected_majors) ← 在 RC-2 之后行程才正确
                │
                └──▶ RC-4 (guardrails 加约束检查) ← 在 RC-1 之后有 trace 可查
```

**第一轮只做 RC-1**（~15 行），验证 constraint_trace 落库。  
**第二轮做 RC-2**（~10 行），验证个性化 cluster 能战胜经典线。  
**第三轮做 RC-3 + RC-4**（~20 行），验证摘要与行程语义一致。
