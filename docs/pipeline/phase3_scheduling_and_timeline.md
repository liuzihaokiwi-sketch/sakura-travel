# Phase 3: 每日排程 + 时间线 (Step 8-12)

> 代码位置：`app/domains/planning_v2/step08~step12`
> 执行方：系统(DB+astral) + Opus AI + 纯 Python + Sonnet AI
> 目的：从"每天做什么"到"每分钟做什么"

---

## 本阶段的核心目标

Phase 2 确定了"每天去哪些地方、住哪家酒店"。Phase 3 的任务是：
- 构建每天的物理约束（日出日落、定休日、酒店含餐）→ Step 8
- AI 排出分钟级的活动顺序 → Step 9
- 系统检查排序结果是否可行 → Step 10
- 自动修复不可行的部分 → Step 11
- AI 生成完整时间线骨架 → Step 12

Phase 3 结束时，每天有精确到分钟的 slot 列表。

---

## Step 8: build_daily_constraints_list (系统)

### 职责
为旅行期间每天构建物理约束包：日出日落、关闭实体、低频班次、锚点、酒店含餐信息。

### 输入
- `trip_window` — 日期范围
- `selected_hotel_id` — Step 7 选出的酒店（可选，用于含餐判断）
- `CircleProfile` — 用于日出日落计算的坐标和时区

### 输出
```python
[
    DailyConstraints(
        date = "2026-04-01",
        day_of_week = "Tue",
        sunrise = "05:42",
        sunset = "18:15",
        closed_entities = ["kyo_kinkaku", ...],
        low_freq_transits = [],       # 预留
        anchors = [],                  # 预留
        hotel_breakfast_included = True,
        hotel_dinner_included = False
    ),
    ...
]
```

### 日出日落计算
- **主路径**：astral 库 + CircleProfile 的坐标和时区（不再硬编码东京）
- **Fallback**：三角函数近似（无 astral 时）

### 定休日查询
- `EntityOperatingFact.day_of_week` 匹配当天星期 + `open_time=NULL`
- `PoiOpeningSnapshot.is_open=False` 匹配具体日期

### 酒店含餐判断
从 Hotel.amenities 中检测 breakfast/dinner 关键词。

### 关键设计决策
**Step 8 被调用两次**
1. 第一次：Step 5 之后（无酒店信息，用于 5.5 的冲突检测）
2. 第二次：Step 7 之后（有酒店信息，更新含餐字段）

**日出日落为什么需要精确？**
户外活动必须在日出后开始、日落前（+buffer）结束。冬季日照短（日落 16:45），直接影响能排几个景点。

### 测试要点
- 不同城市圈的日出日落时间合理（广州 vs 札幌）
- 定休日实体正确出现在 closed_entities 中
- 酒店含餐信息正确传递

---

## Step 9: plan_daily_sequences (Opus AI)

### 职责
用 Opus 深度思考，为每天的活动排出分钟级最优顺序。这是管线中**最核心的 AI 步骤**。

### 输入
- `daily_activities` — Step 5.5 校验后的活动
- `daily_constraints` — Step 8 的约束包
- `commute_matrix` — Step 7.5 的通勤数据

### 输出
```python
{
    "daily_sequences": [
        {
            "day": 1,
            "date": "2026-04-01",
            "activities": [
                {
                    "entity_id": "xxx",
                    "name": "伏见稻荷大社",
                    "start_time": "07:00",
                    "end_time": "09:00",
                    "type": "poi",
                    "commute_from_prev_mins": 0,
                    "notes": "清晨人少"
                },
                ...
            ]
        }
    ],
    "thinking_tokens_used": 12000
}
```

### AI 调用规格
| 参数 | 值 |
|------|-----|
| 模型 | claude-opus-4-6 |
| max_tokens | 16000 |
| thinking_budget | 15000 |

### 编排 7 条原则
1. **时间窗约束** — 营业时间内安排，定休日跳过
2. **通勤效率** — 相邻活动通勤 < 30min
3. **体力曲线** — 上午高强度，下午递减，傍晚轻松
4. **锚点优先** — 飞行、预约等不可移动
5. **弹性午餐** — 11:30-13:30 之间插入
6. **酒店含餐** — 含早餐则 08:00 前回酒店，含晚餐则 18:30 前
7. **日出/日落** — 日出后开始，sunset+60min 前结束

### 校验（_validate_day_sequence）
- 必须字段：entity_id, start_time, end_time
- 时间格式：HH:MM
- 时间顺序：start_time < end_time，且后一活动 start >= 前一活动 end

### Fallback
- 按 grade 排序 + 粗略时间分配（09:00 开始，每活动间隔 30min）
- 自动插入 flex_meal（12:00-13:00）

### 关键设计决策
**为什么用 Opus 而不是 Sonnet？**
排序需要同时考虑时间窗、通勤、体力、含餐、锚点等多维约束。这不是简单的排列组合，是真正的规划推理。

**每天独立调用 vs 一次性排所有天？**
当前每天独立调用 `_plan_single_day()`。好处是单次 prompt 更短、更精确；代价是跨天优化能力弱。

### 测试要点
- 活动时间窗在日出日落之间
- 相邻活动不时间重叠
- flex_meal 出现在 11:30-13:30
- 定休日实体不出现在序列中

---

## Step 10: check_feasibility (纯 Python)

### 职责
硬规则检查 Step 9 的排序结果是否物理可行。不依赖 AI，不做网络调用。

### 7 条检查规则（优先级递减）

| # | 规则 | 严重度 | 说明 |
|---|------|--------|------|
| 1 | 时间重叠 | FAIL | 两个真实活动时间交叉（buffer 块豁免） |
| 2 | 定休日 | FAIL | 活动实体在当天关闭 |
| 3 | 通勤不足 | WARNING | 间隔 < commute_from_prev_mins |
| 4 | 日出前 | WARNING | 户外活动在日出前开始 |
| 5 | 日落后 | WARNING | 户外活动在 sunset+30min 后进行 |
| 6 | 餐食冲突 | WARNING | 酒店含早餐但安排了外部早餐 |
| 7 | 超载 | WARNING | 当日活动总时长 > 10 小时 |

### Buffer 块处理
**定义**：type 属于 `{buffer, slack, free_time, flex_meal, rest, commute}` 或 `is_buffer=True`

**规则**：
- 不参与时间重叠检查（有意留白）
- 不计入总活动时长（不算超载）
- 其他检查仍适用（如户外活动日出日落）

### 输出
```python
FeasibilityResult(
    status = "pass" | "warning" | "fail",
    violations = [
        {"severity": "fail", "type": "time_overlap", "day": 2, "entity_id": "xxx", "reason": "..."},
        {"severity": "warning", "type": "overloaded_day", "day": 3, "reason": "活动总时长660分钟"}
    ],
    suggestions = ["Day 2: 移除低等级活动以消除重叠"]
)
```

### 关键设计决策
**为什么 Step 10 是纯 Python 不用 AI？**
可行性检查是确定性的物理规则（时间是否重叠、实体是否关闭）。用 AI 会引入不确定性，而这里需要 100% 精确。

**为什么 buffer 块不参与重叠检查？**
buffer/slack/rest 是 Step 9/12 有意插入的留白时间，允许与其他活动"重叠"（实际上是被其他活动替代的候选时段）。

### 测试要点
- buffer 块不触发 time_overlap
- 定休日实体触发 FAIL
- 活动总时长刚好 10h 不触发 warning，10h01min 触发

---

## Step 11: resolve_conflicts (系统 + Opus AI)

### 职责
4 步链式处理 Step 10 发现的冲突。逐步升级：规则优先，AI 兜底。

### 4 步冲突处理链

**Step 11.1 — 删除（纯规则）**
- 处理：closed_entity → 删除实体；time_overlap → 删除 grade 更低的
- 保护：anchor / flight / hotel_checkin / hotel_checkout 不可删
- 删完后重新跑 Step 10；通过则返回

**Step 11.2 — 压缩时间（纯规则）**
- 处理：commute_infeasible
- 方法：缩减前一活动 end_time，最多 20%（MAX_COMPRESS_RATIO）
- 压缩后重新跑 Step 10；通过则返回

**Step 11.3 — 降级强度（纯规则，仅 capacity_overload）**
- 处理：overloaded_day
- 方法：缩减 grade 最低的 heavy 活动到 70%，或直接移除
- 降级后重新跑 Step 10；通过则返回

**Step 11.4 — AI 回退（仅 hard_infeasible 未解决时）**
- 调用 Opus 重排整天活动
- thinking_budget: 8000, max_output: 16000

### hard_infeasible vs capacity_overload

| 类型 | 包含 | 处理方式 |
|------|------|---------|
| hard_infeasible | time_overlap, closed_entity, commute_infeasible | 物理不可行，只能删除/重排 |
| capacity_overload | overloaded_day, before_sunrise, after_sunset, meal_conflict | 体验层超载，可缩减/降级 |

**关键区分**：hard_infeasible 意味着"时间/空间上不可能"，降低强度标签无效。capacity_overload 意味着"能做但体验差"，可以通过减量解决。

### 输出
```python
{
    "resolved_sequences": [...],  # 修改后的序列
    "resolution_log": [
        {"step": "11.1", "action": "删除", "day": 2, "reason": "周二定休"}
    ],
    "final_status": "resolved" | "partially_resolved" | "unresolved",
    "ai_fallback_used": false,
    "thinking_tokens_used": 0
}
```

### 测试要点
- 11.1 删除后 closed_entity 不再出现
- 11.2 压缩不超过 20%
- 11.3 只处理 capacity_overload，跳过 hard_infeasible
- 11.4 只在前三步都无法解决时触发

---

## Step 12: build_timeline (Sonnet AI)

### 职责
把冲突修复后的活动序列转化为完整的时间线骨架，补充通勤段、餐食段、buffer 段。

### 输入
- `resolved_sequences` — Step 11 输出
- `daily_constraints` — Step 8 输出
- `hotel_plan` — Step 7 输出
- `CircleProfile` — 提示词注入

### Slot 类型
| type | 说明 | 示例 |
|------|------|------|
| hotel_breakfast | 酒店早餐 | 07:00-08:00 |
| poi | 景点/活动 | 09:00-11:00 |
| commute | 通勤段 | 11:00-11:30, mode=JR |
| flex_meal | 弹性午餐 | 12:00-13:00, optional=true |
| dinner | 晚餐 | 18:00-20:00 |
| hotel_checkin | 入住 | 15:00 |
| hotel_checkout | 退房 | 11:00 |

### Sonnet 规则
1. 第一个活动 ≥ max(sunrise, 07:00)
2. 最后活动 ≤ min(sunset+2h, 21:00)
3. 通勤 slot ≥ commute_from_prev_mins
4. 午餐 11:30-13:30，optional=true
5. 晚餐 18:00-20:00（酒店含晚餐则不插入）
6. 无时间重叠
7. 允许 15-30min buffer

### Fallback
直接用活动序列的 start/end_time 构建 slot，补充：
- 酒店早餐（07:00-08:00，如 included）
- 弹性午餐（12:00-13:00）
- 晚餐（19:00-20:00）

### 测试要点
- 每天 slot 无时间重叠
- 酒店含早餐时有 hotel_breakfast slot
- 通勤 slot 的 mode 字段有值

---

## Phase 3 整体原则

1. **检查-修复闭环** — Step 9 排序 → Step 10 检查 → Step 11 修复 → 再检查。最多 4 轮自动修复。
2. **确定性优先** — Step 10/11.1/11.2/11.3 都是纯规则，只有 11.4 才用 AI。
3. **Buffer 块是一等公民** — 有意义的留白（休息、弹性午餐），不是无效填充。Step 10 知道它们不是真实活动。
4. **日出日落不是建议** — 是硬约束。冬季日照短会实质减少可排景点数。

## Phase 3 数据流

```
Step 5.5 validated_activities + Step 8 daily_constraints + Step 7.5 commute_matrix
    │
    ▼
Step 9: plan_daily_sequences (Opus)
    │ → daily_sequences {activities[{start_time, end_time, commute}]}
    │
    ▼
Step 10: check_feasibility (纯Python)
    │ → FeasibilityResult {status, violations[]}
    │
    ├─ status == "pass" ──▶ Step 12
    │
    └─ status != "pass" ──▶ Step 11: resolve_conflicts (规则链 + Opus fallback)
                               │ → resolved_sequences
                               │
                               ▼
                          Step 12: build_timeline (Sonnet)
                               → timeline {days[{slots[{time, type, entity_id}]}]}
```
