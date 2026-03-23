# 生成链路日志 + 失败 Case 对照分析

> **数据来源**：`scripts/_reg_p0.log`（2026-03-23 13:35:29 运行）  
> **聚焦 Case**：用例 2 — 约束型 · 三代同堂家庭 [BLOCKER]

---

## 1. 真实生成链路日志（用例 2：三代同堂）

### 1.1 运行标识

| 字段 | 值 |
|------|-----|
| **trip_request_id** | 回归脚本生成的临时 UUID（每次不同，非持久化） |
| **plan_id** | 回归脚本不写 DB，无 plan_id |
| **run_id** | `constraints.run_id`（日志中有 trace items 计数但 SQL 日志未单独记录 run_id） |
| **circle_id** | `kansai_classic_circle` |
| **日志时间** | `13:35:29`（与用例 1 同秒完成，总耗时 <1s） |

### 1.2 Profile 原始输入

```python
# 来自 scripts/test_cases.py CASE_CONSTRAINED
{
    "case_id": "constrained",
    "duration_days": 5,
    "cities": [{"city_code": "kyoto", "nights": 3}, {"city_code": "osaka", "nights": 1}],
    "party_type": "family_multi_gen",
    "budget_level": "premium",
    "pace": "relaxed",
    "must_have_tags": ["culture", "nature"],
    "avoid_tags": ["sushi", "sashimi", "raw"],
    "daytrip_tolerance": "low",
    "hotel_switch_tolerance": "low",
    "travel_dates": {"start": "2026-04-12", "end": "2026-04-16"},
}
```

### 1.3 中间结果路径（从日志提取）

| 步骤 | 日志行 | 结果 |
|------|--------|------|
| 城市圈选择 | :123 | `kansai_classic_circle` |
| 活动簇通过 | :132 | 39 个通过（eligibility gate fallback，未真正过滤） |
| 主要活动排序 | :165 | **6 个入选** |
| 酒店策略 | :174 | `全程住京都（河原町/祇园）` 4 晚 |
| 骨架天数 | :175 | 5 天 |
| 餐厅填充 | :184-189 | 城市过滤 338→112，Day1-5 各有餐厅 |

### 1.4 constraint_trace 记录

> ⚠️ **关键发现**：回归脚本（`run_regression.py`）**已接通 compiler**（:73 行 `constraints = compile_constraints(profile)`），并传给了 ranker/skeleton/filler。  
> 但生产管线（`generate_trip.py`）**未接通**。  
> 这意味着回归测试的结果**不代表生产行为**——回归测试可能 pass，但生产出的行程仍然是经典线。

回归脚本中的约束编译调用：
```python
# run_regression.py:73
constraints = compile_constraints(profile)
# run_regression.py:102-104
ranking = await rank_major_activities(..., constraints=constraints)
# run_regression.py:118-123
skeleton = build_route_skeleton(..., constraints=constraints)
# run_regression.py:148-156
meal_fills = fill_meals(..., constraints=constraints)
```

生产管线中的调用（generate_trip.py）：
```python
# generate_trip.py:381 — 无 constraints
ranking = await rank_major_activities(session, circle_id, profile, passed_ids)
# generate_trip.py:481 — 无 constraints
skeleton = build_route_skeleton(duration_days=..., pace=profile.pace)
# generate_trip.py:604 — 无 constraints
meal_fills = fill_meals(frames=..., restaurant_pool=..., trip_profile=...)
```

### 1.5 骨架输出（从日志推断）

| Day | 走廊 | 主活动 | day_type | intensity | 餐厅 |
|-----|------|--------|----------|-----------|------|
| 1 | fushimi | 伏见稻荷 | arrival | balanced | 祢ざめ家, 黄桜酒场 |
| 2 | arashiyama | 岚山·嵯峨野 | normal | balanced | イノダ, よしむら, 篩月 |
| 3 | higashiyama | 东山·祇园经典 | normal | balanced | う桶や, 奥丹清水 |
| 4 | namba | 道顿堀 | normal | balanced | 章鱼烧くくる, 美津の |
| 5 | osakajo | 大阪城·中之岛 | departure | light | ラ・シェット |

### 1.6 断言结果

```
断言: 13/13 PASS ✅
```

| # | 断言 | 结果 | 细节 |
|---|------|------|------|
| 1 | 天数>=5 | ✅ | 5天 |
| 2 | 天数<=5 | ✅ | 5天 |
| 3 | departure 类型 | ✅ | departure |
| 4 | 返程日节奏 ∈ [light] | ✅ | light |
| 5 | 返程日 item<=2 | ✅ | 2个 |
| 6 | 禁忌餐饮 [sushi,sashimi] | ✅ | 通过 |
| 7 | 节奏不超过 balanced | ✅ | 通过 |
| 8 | 无东京餐厅 | ✅ | 通过 |
| 9 | 走廊一致性 | ✅ | 通过 |
| 10 | 无 USJ/环球影城 | ✅ | 通过 |
| 11 | 无 raw key 泄露 | ✅ | 通过 |
| 12 | 返程日标题 | ✅ | "返程日 · 大阪·中之岛+天满桥文化线 · 轻松收尾" |
| 13 | 关键决策一致性 | ✅ | 通过 |

---

## 2. 失败 Case 对照：回归 vs 生产

### 2.1 用户输入（相同）

```
party_type = "family_multi_gen"（三代同堂：70岁老人+5岁小孩）
pace = "relaxed"
avoid_tags = ["sushi", "sashimi", "raw"]
must_have_tags = ["culture", "nature"]
budget_level = "premium"
```

### 2.2 摘要（来自 profile_summary — 两条管线相同）

```
travel_portrait: "三代同堂 · 带70岁老人+5岁小孩 · 偏轻松 · 高预算 · 不吃生食"

hard_constraints:
  - 5天4晚 · 关西经典圈
  - 老人腿脚不便，每天步行控制在1万步以内
  - 不吃生鱼片/寿司等生食
  - 返程航班14:00，最后一天需提前到机场

care_about:
  - 老人想看寺庙和日式庭园
  - 小孩想喂鹿（奈良）
  - 不要太多台阶和爬坡
  - 每天午休时间留够
```

### 2.3 总览 / design_brief（来自 _build_design_brief — 两条管线相同）

```
route_strategy: ["单城深玩，减少城际移动时间"]
tradeoffs: ["主动放弃步行量大、换乘复杂的区域"]
execution_principles: ["整体节奏：轻松，每天避免超过2个主要区域",
                       "景点间步行距离控制在15分钟以内，安排午休缓冲"]
stay_strategy: ["根据路线重心选择住宿区域，减少不必要的通勤时间"]
budget_strategy: ["品质优先：高价餐和体验集中安排，不做过度压缩"]
```

> ✅ 以上文案完美理解了用户需求——"三代同堂"、"轻松"、"无障碍"、"不吃生食"。

### 2.4 日页对比

#### 回归测试管线（constraints 已接通）

| Day | 走廊 | 主活动 | 问题？ |
|-----|------|--------|--------|
| 1 | fushimi | 伏见稻荷 | ⚠️ 伏见稻荷有 1000+ 级台阶，不适合 70 岁老人。**但 S+default 强制入选** |
| 2 | arashiyama | 岚山·嵯峨野 | ⚠️ 岚山有较多坡路。**S+default 强制入选** |
| 3 | higashiyama | 东山·祇园经典 | ⚠️ 清水寺坂道+二年坂陡坡。**S+default 强制入选** |
| 4 | namba | 道顿堀 | ✅ 平坦，适合家庭 |
| 5 | osakajo | 大阪城·中之岛 | ⚠️ 返程日去大阪城（有天守阁台阶）|

> **即使 constraints 接通，由于 RC-2（_sort_key is_must_go 碾压），伏见/岚山/东山仍然入选。**  
> constraints 帮助的是：避食生鱼 ✅、节奏≤balanced ✅、返程日轻量 ✅  
> constraints 帮不了的是：S 级经典线不适合老人但仍排第一 ❌

#### 生产管线（constraints=None，假设行为）

| Day | 走廊 | 主活动 | 与回归相比 |
|-----|------|--------|-----------|
| 1 | fushimi | 伏见稻荷 | 相同（S+default） |
| 2 | arashiyama | 岚山 | 相同（S+default） |
| 3 | higashiyama | 东山 | 相同（S+default） |
| 4 | namba/sakurajima | 道顿堀 或 **USJ** | ⛔ 可能出现 USJ（constraints=None → party_block_tags 不生效）|
| 5 | ? | ? | ⛔ 返程日可能 intensity=dense（constraints=None → max_intensity 不生效）|

额外生产问题：
- 餐厅可能包含寿司/刺身（avoid_cuisines 不生效）
- 返程日可能排 3+ 个景点（departure_day_no_poi 不生效）
- 到达日可能排午餐（arrival_evening_only 不生效）

### 2.5 Grader 结果对比

| 断言 | 回归（constraints=有）| 生产（constraints=None）|
|------|---------------------|----------------------|
| 禁忌餐饮 [sushi,sashimi] | ✅ PASS | ❌ 可能 FAIL（avoid_cuisines 不传）|
| 节奏不超过 balanced | ✅ PASS | ❌ 可能 FAIL（max_intensity 不传）|
| 无 USJ/环球影城 | ✅ PASS | ❌ 可能 FAIL（party_block_tags 不传）|
| 返程日 item<=2 | ✅ PASS | ❌ 可能 FAIL（departure_day_no_poi 不传）|
| 其余结构断言 | ✅ PASS | ✅ PASS（结构不依赖 constraints）|

---

## 3. 核心发现：回归脚本和生产管线的分裂

```
┌──────────────────────┐          ┌──────────────────────┐
│  run_regression.py   │          │  generate_trip.py    │
│  (回归测试)           │          │  (生产管线)           │
├──────────────────────┤          ├──────────────────────┤
│                      │          │                      │
│  ✅ compile_constraints()  │    │  ⛔ 从未调用           │
│  ✅ constraints=constraints│    │  ⛔ constraints=None   │
│  ✅ 13/13 PASS       │          │  ❓ 可能 9/13 FAIL    │
│                      │          │                      │
│  → 回归 GREEN        │          │  → 生产出经典线       │
└──────────────────────┘          └──────────────────────┘
         │                                  │
         └──────────┬───────────────────────┘
                    │
             ⛔ 回归测试的 GREEN
                不代表生产行为
```

**这就是"假绿"的最终证据**：

1. 回归脚本自己接通了 compiler（`run_regression.py:73`），所以约束生效，测试通过
2. 生产管线没有接通 compiler（`generate_trip.py:381/481/604`），约束全部失效
3. 回归的 13/13 PASS 给了"一切正常"的假象
4. 但用户真正收到的 PDF 是生产管线生成的——经典线、可能有生鱼、可能有 USJ

---

## 4. 缺失的 Trace 字段

当前回归日志**缺少以下关键追踪信息**（项目文档要求但未实现）：

| 缺失字段 | 应该在哪里 | 当前状态 |
|---------|-----------|---------|
| `constraint_compiler_version` | plan_metadata | ❌ 未落库（回归脚本只打日志不写 DB）|
| `constraint_run_id` | plan_metadata | ❌ 同上 |
| `constraint_trace[]` | plan_metadata | ❌ 回归脚本打了 trace_summary 日志，但未序列化到输出 |
| `被挡片段` (blocked_clusters/tags 命中记录) | constraint_trace.consumption_events | ❌ ranker 有 logger.debug 但未写 trace |
| `软规则排序结果` (全部 ranked clusters + 分数) | ranking.all_ranked | ❌ 日志只记了 "主要活动: 6 个"，未记录完整排名 |
| `质量门控结果` (guardrails) | plan_metadata.guardrail_warnings | ❌ 回归脚本不走 guardrails |

### 4.1 修复建议：回归脚本补全 trace 输出

在 `run_regression.py` 的 `_build_case_data()` 返回值中补充：

```python
return {
    # ... 现有字段 ...
    "trace": {
        "compiler_version": constraints.compiler_version,
        "run_id": constraints.run_id,
        "constraint_trace": [
            {
                "name": t.constraint_name,
                "strength": t.strength,
                "value": t.compiled_value,
                "events": t.consumption_events,
                "status": t.final_status,
            }
            for t in constraints.constraint_trace
        ],
        "ranking_full": [
            {
                "cluster_id": r.cluster_id,
                "name": r.name_zh,
                "base_quality": r.base_quality_score,
                "context_fit": r.context_fit_score,
                "major_score": r.major_score,
                "selection_reason": r.selection_reason,
            }
            for r in ranking.all_ranked
        ],
    },
}
```

---

## 5. 约束流向对照表（回归 vs 生产）

| 约束 | 回归脚本 | 生产管线 | 结论 |
|------|---------|---------|------|
| `blocked_tags` → ranker | ✅ 传了 constraints | ⛔ constraints=None | 回归 pass ≠ 生产 pass |
| `blocked_clusters` → ranker | ✅ | ⛔ | 同上 |
| `preferred_tags_boost` → ranker | ✅ | ⛔ | 同上 |
| `party_block_tags` → ranker | ✅ | ⛔ | 同上 |
| `max_intensity` → skeleton | ✅ | ⛔ | 同上 |
| `departure_meal_window` → skeleton | ✅ | ⛔ | 同上 |
| `arrival_evening_only` → skeleton | ✅ | ⛔ | 同上 |
| `avoid_cuisines` → filler | ✅ | ⛔ | 同上 |
| `city_strict_day_types` → filler | ✅ | ⛔ | 同上 |
| `design_brief` → report | ✅ 读 profile | ✅ 读 profile | **两者一致但都不读 execution 结果** |
| `guardrails` → 约束检查 | ⛔ 不走 | ⛔ 只查结构 | **两者都不检查约束消费** |
