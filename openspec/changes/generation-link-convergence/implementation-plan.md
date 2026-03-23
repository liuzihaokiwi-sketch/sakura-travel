# 修改方案：Generation Link Convergence — 统一约束接通

> **状态**：待评审  
> **日期**：2026-03-23  
> **基于文档**：  
> - `audit-constraint-truth.md`（我方审计：约束真源 + 消费链路）  
> - `代码审计结论_约束真源与假绿根因.md`（评审方结论：P0-P2 分层 + 修复顺序）  
> - `false-green-root-cause.md`（假绿根因：RC-1 到 RC-6）  
> - `trace-and-failure-case.md`（日志 + 失败 case 对照）  

---

## 双方共识

经过对照 4 份审计文档，**双方对以下结论完全一致**：

| # | 共识 | 我方依据 | 评审方依据 |
|---|------|---------|-----------|
| 1 | `constraint_compiler.py` 已完备，缺的是生产管线未调用 | audit B 表 12 项全断裂 | §1.1 "写好了但没接通" |
| 2 | 回归脚本和生产管线分叉——回归 GREEN 不代表生产行为 | trace-and-failure §3 对照图 | §1.2 "回归链路和生产链路真的分叉了" |
| 3 | renderer 不是根因 | RC-6 Medium | §1.3 "renderer 不会自己重新规划路线" |
| 4 | guardrails 零约束意识 | RC-4 High | §1.4 "拦结构问题，不拦硬约束没被消费" |
| 5 | party_type 三处独立映射有冲突风险 | audit C1 | §1.5 "同一语义被三处各自解释" |
| 6 | 先接通 compiler 是 ROI 最高的第一步 | audit G Phase 1 | §5 Step 1 |
| 7 | 排序 is_must_go 碾压是第二优先级 | RC-2 Critical | §5 Step 3 "P1" |
| 8 | 文案同源是最后碰的 | RC-3 在 RC-2 之后 | §5 Step 4 |
| 9 | 不该继续加零散字段 validator | audit F 明确不做 | §4 "不该这么做" |

---

## 修改方案

### 原则

1. **只做一件事**：接通 compiler → 生产管线，让约束真正生效
2. **不改架构**：不动签名，不合并模块，不碰 renderer/UI
3. **顺手加 trace**：既然动了 generate_trip.py，一并把 trace 落库
4. **不碰排序**：is_must_go 碾压是下一轮的事，本轮不动 ranker 内部逻辑
5. **不碰文案**：design_brief 同源是下下轮的事

### 修改范围

| # | 文件 | 改动 | 新增行数 | 删除行数 |
|---|------|------|---------|---------|
| 1 | `app/workers/jobs/generate_trip.py` | 接通 compiler + 透传 constraints（含 secondary_filler）+ trace finalize + 落库 | ~25 | 0 |
| 2 | `app/domains/planning/major_activity_ranker.py` | 补 4 处 `record_consumption` 调用 | ~8 | 0 |
| 3 | `app/domains/planning/route_skeleton_builder.py` | 补 3 处 `record_consumption` 调用 | ~8 | 0 |
| 4 | `app/domains/planning/meal_flex_filler.py` | 补 2 处 `record_consumption` 调用 | ~6 | 0 |

**新增文件：0 个**  
**总行数：~47 行新增，0 行删除**

### 评审修正（3 项）

**修正 1**：`fill_secondary_activities` 也需要补传 `constraints=constraints`。审计路线图 Phase 1 已列入，主链路中二级活动填充（Step 7）如果漏掉，secondary 仍走旧逻辑。

**修正 2**：trace 落库前先做 finalize——遍历所有 trace item，将仍为 `pending` 的硬约束显式标记为 `unconsumed` 并写 `ignored_reason`。`ConstraintTraceItem` 的数据模型本来就区分了 `pending / partially_consumed / fully_consumed / unconsumed`，直接把 `pending` 落库等于落"半成品"。

**修正 3**：本轮不对外声称 `must_stay_area` / `must_stay_cities` 已修复。审计已标为 dead constraint，hotel_base_builder 本轮不动。预期效果表中需如实标注。

---

### 文件 1: `generate_trip.py`（核心接通）

#### 改动点 A：import + 编译（在 Step 4 之前，约 :378 行附近）

```python
# ── Step 3b: 编译统一约束 ──
from app.domains.planning.constraint_compiler import compile_constraints
constraints = compile_constraints(profile)
```

#### 改动点 B：ranker 传参（:381 行）

现在:
```python
ranking_result = await rank_major_activities(
    session=session,
    circle_id=circle_id,
    profile=profile,
    passed_cluster_ids=eg_result.passed_cluster_ids,
    precheck_failed_entity_ids=pc_result.failed_ids,
    override_resolver=override_resolver,
)
```

改为:
```python
ranking_result = await rank_major_activities(
    session=session,
    circle_id=circle_id,
    profile=profile,
    passed_cluster_ids=eg_result.passed_cluster_ids,
    precheck_failed_entity_ids=pc_result.failed_ids,
    override_resolver=override_resolver,
    constraints=constraints,
)
```

#### 改动点 C：skeleton 传参（:481 行）

现在:
```python
skeleton = build_route_skeleton(
    duration_days=days_count,
    selected_majors=ranking_result.selected_majors,
    hotel_bases=hotel_result.bases,
    pace=profile.pace or "moderate",
    wake_up_time=profile.wake_up_time or "normal",
)
```

改为:
```python
skeleton = build_route_skeleton(
    duration_days=days_count,
    selected_majors=ranking_result.selected_majors,
    hotel_bases=hotel_result.bases,
    pace=profile.pace or "moderate",
    wake_up_time=profile.wake_up_time or "normal",
    constraints=constraints,
)
```

#### 改动点 D：filler 传参（:604 行）

现在:
```python
meal_fills = fill_meals(
    frames=skeleton.frames,
    restaurant_pool=restaurant_pool,
    trip_profile=profile_dict,
    corridor_resolver=corridor_resolver,
)
```

改为:
```python
meal_fills = fill_meals(
    frames=skeleton.frames,
    restaurant_pool=restaurant_pool,
    trip_profile=profile_dict,
    corridor_resolver=corridor_resolver,
    constraints=constraints,
)
```

#### 改动点 E：trace 落库 + unconsumed 告警（在 Step 9 之后，assembler 之前）

```python
# ── constraint_trace 落库 ──
_ct_data = [
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
plan_metadata["constraint_trace"] = _ct_data
plan_metadata["constraint_compiler_version"] = constraints.compiler_version
plan_metadata["constraint_run_id"] = constraints.run_id

# 被动告警：硬约束未被消费
_unconsumed = [t.constraint_name for t in constraints.constraint_trace
               if t.strength == "hard" and t.final_status == "pending"]
if _unconsumed:
    logger.warning("⚠️ unconsumed hard constraints: %s (run_id=%s)",
                   _unconsumed, constraints.run_id)
```

---

### 文件 2: `major_activity_ranker.py`（补 trace 记录）

在 `_score_cluster` 函数内，**现有的 constraints 消费逻辑处**补 `record_consumption` 调用。

#### 改动点 A：blocked_tags 命中时

```python
# 在 blocked_tags 扣分逻辑后
if constraints and hit_blocked:
    constraints.record_consumption(
        "blocked_tags", "ranker", "tag_penalty",
        f"cluster {cluster.cluster_id} penalized: hit tags {sorted(hit_blocked)}")
```

#### 改动点 B：blocked_clusters 命中时

```python
# 在 blocked_clusters 过滤逻辑后
if constraints and cluster.cluster_id in constraints.blocked_clusters:
    constraints.record_consumption(
        "blocked_clusters", "ranker", "hard_block",
        f"cluster {cluster.cluster_id} zeroed")
```

#### 改动点 C：preferred_tags_boost 应用时

```python
# 在 preferred_tags_boost 加分逻辑后
if constraints and constraints.preferred_tags_boost and boost_total > 0:
    constraints.record_consumption(
        "preferred_tags_boost", "ranker", "soft_boost",
        f"cluster {cluster.cluster_id} boosted +{boost_total:.0f}")
```

#### 改动点 D：party_block_tags / party_fit_penalty 应用时

```python
if constraints and constraints.party_block_tags and party_hit:
    constraints.record_consumption(
        "party_block_tags", "ranker", "hard_block",
        f"cluster {cluster.cluster_id} blocked by party tags {sorted(party_hit)}")

if constraints and constraints.party_fit_penalty and penalty_applied:
    constraints.record_consumption(
        "party_fit_penalty", "ranker", "soft_penalty",
        f"cluster {cluster.cluster_id} penalized -{constraints.party_fit_penalty}")
```

---

### 文件 3: `route_skeleton_builder.py`（补 trace 记录）

#### 改动点 A：`_set_meal_windows` 应用 departure/arrival 约束时

```python
# 在 departure_meal_window 应用后
if constraints and dep_meal_window != "breakfast_only":
    constraints.record_consumption(
        "departure_constraints", "skeleton", "meal_window_set",
        f"departure day meals={dep_meal_window}")

# 在 arrival_evening_only 应用后
if constraints and constraints.arrival_evening_only:
    constraints.record_consumption(
        "arrival_constraints", "skeleton", "evening_only_set",
        f"arrival day restricted to evening only")
```

#### 改动点 B：`_mark_intensity` 应用 max_intensity 约束时

```python
if constraints and constraints.max_intensity < 2:
    constraints.record_consumption(
        "max_intensity", "skeleton", "intensity_cap",
        f"capped at level {constraints.max_intensity}")
```

---

### 文件 4: `meal_flex_filler.py`（补 trace 记录）

#### 改动点 A：avoid_cuisines 过滤时

```python
# 在 avoid_cuisines 过滤逻辑处
if constraints and constraints.avoid_cuisines and filtered_count > 0:
    constraints.record_consumption(
        "avoid_cuisines", "filler", "cuisine_filter",
        f"filtered {filtered_count} restaurants by cuisine avoids {sorted(constraints.avoid_cuisines)}")
```

#### 改动点 B：city_strict_day_types 过滤时

```python
if constraints and frame.day_type in constraints.city_strict_day_types:
    constraints.record_consumption(
        "city_strict_day_types", "filler", "city_strict",
        f"day {frame.day_index} ({frame.day_type}) enforced city match")
```

---

## 不做什么（本轮明确排除）

| 排除项 | 原因 | 何时做 |
|--------|------|--------|
| 修改 ranker `_sort_key` / is_must_go | 评审方 P1，需要先看接通后的排序数据 | Round 2 |
| 修改 design_brief 同源 | 评审方 P2 Step 4，需要先让 planner 输出稳定 | Round 3 |
| 合并 party_type 三套映射 | 风险大，需要独立 change | 独立 change |
| 合并 EligibilityContext + PlanningConstraints | gate 在 compiler 之前执行，合并改执行顺序 | 不做 |
| 碰 renderer / UI | 评审方确认 renderer 不是根因 | 不做 |
| 碰 scorer.py | 应保持约束无感的纯函数设计 | 不做 |
| guardrails 加约束检查 | 需要先有 trace 数据积累，本轮先落库 | Round 2 |
| 扩大量回归断言 | 双方共识：不该继续加零散 validator | 不做 |
| 让 hotel_base_builder 消费 must_stay_area | 需改 hotel 内部逻辑 | 独立 change |

---

## 验证计划

### V1: 接通验证（本轮核心）

```bash
# 跑回归测试
python scripts/run_regression.py

# 检查日志中是否有 constraint_compiler 输出
grep "constraint_compiler" scripts/_reg_p0.log

# 检查是否有 unconsumed hard constraints 告警
grep "unconsumed hard" scripts/_reg_p0.log
```

### V2: trace 落库验证

回归跑完后检查 plan_metadata：
```sql
SELECT plan_metadata->'constraint_trace' FROM itinerary_plans WHERE plan_id = '<最新>';
SELECT plan_metadata->>'constraint_compiler_version' FROM itinerary_plans WHERE plan_id = '<最新>';
```

预期：
- `constraint_trace` 数组非空
- 每条硬约束的 `status` 不是 `pending`
- `compiler_version` = `"2.1.0"`

### V3: 三代同堂 case 语义验证

跑回归后检查用例 2（约束型·三代同堂）：
- ✅ 餐厅无 sushi/sashimi（`avoid_cuisines` 生效）
- ✅ 节奏 ≤ balanced（`max_intensity` 生效）
- ✅ 无 USJ（`party_block_tags` 生效）
- ⚠️ 仍然可能出现伏见/岚山/东山（`is_must_go` 碾压——**本轮已知不解决**）

---

## 执行顺序

```
Step 1: generate_trip.py（改动点 A-E）
    ↓ 这是一切的前提——不接通则其他全白做
Step 2: major_activity_ranker.py（改动点 A-D）
    ↓ ranker 是约束消费最多的模块
Step 3: route_skeleton_builder.py（改动点 A-B）
    ↓ skeleton 消费 departure/arrival/intensity
Step 4: meal_flex_filler.py（改动点 A-B）
    ↓ filler 消费 avoid_cuisines/city_strict
Step 5: 跑回归测试 + 检查 trace
```

---

## 预期效果

### 本轮修复后

| 问题 | 修复前 | 修复后 |
|------|--------|--------|
| 生产管线 avoid_cuisines | ⛔ 不生效 | ✅ 生效 |
| 生产管线 max_intensity | ⛔ 不生效 | ✅ 生效 |
| 生产管线 party_block_tags | ⛔ 不生效 | ✅ 生效 |
| 生产管线 departure/arrival day | ⛔ 不生效 | ✅ 生效 |
| 生产管线 preferred_tags_boost | ⛔ 不生效 | ✅ 生效（但可能被 is_must_go 碾压） |
| constraint_trace 落库 | ⛔ 无数据 | ✅ plan_metadata 有完整 trace |
| unconsumed 硬约束告警 | ⛔ 无告警 | ✅ 自动 logger.warning |
| 回归 vs 生产分叉 | ⛔ 两条路径 | ✅ 统一走 compiler |

### 本轮不解决

| 问题 | 原因 | 计划 |
|------|------|------|
| S 级经典线碾压个性化 | 需要先看接通后的分数数据再定阈值 | Round 2 |
| 摘要 ≠ 行程语义 | 需要先让行程正确 | Round 3 |
| guardrails 约束检查 | 需要先积累 trace 数据 | Round 2 |

---

## 风险评估

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| constraints 参数传入但被下游 `if constraints:` 跳过 | 低 | 约束部分失效 | 已确认下游三个模块的 constraints 分支逻辑正确 |
| party_type 不在 `_PARTY_RULES` 映射表中 | 中 | party_block_tags 不生效 | compiler 已有 fallback（:314-323 行写 `unconsumed` trace） |
| profile 对象缺少某些字段（如 `arrival_time`） | 低 | compiler 用 `getattr` 安全 fallback | 已确认 compiler 全部用 `getattr(profile, ..., None)` |
| 回归测试因新约束生效导致结果变化 | 高 | 部分 case 可能 FAIL | **预期行为**——说明约束真的生效了，需更新断言 |
