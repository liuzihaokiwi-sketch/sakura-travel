# Phase 2: 锁主活动 + 住宿 (Step 5-7.5)

> 代码位置：`app/domains/planning_v2/step05~step07_5`
> 执行方：Opus AI + Sonnet AI + 系统(DB/API)
> 目的：从候选池中选出每天做什么、住哪里

---

## 本阶段的核心目标

Phase 1 给了一个 50-100 个 POI 的候选池和城市分配方案。Phase 2 的任务是：
- AI 从池中为每天选主活动（Step 5）
- 系统校验有没有定休日/冲突（Step 5.5）
- 系统按地理和通勤筛酒店（Step 6 + 7.5）
- AI 从酒店池中选最终住宿（Step 7）

Phase 2 结束时，"每天去哪、住哪"已经确定。

---

## Step 5: plan_daily_activities (Opus AI)

### 职责
用 Opus 深度思考，从 POI 候选池中为每天选择主活动、确定走廊、标记强度。

### 输入
- `cities_by_day` — Step 3 输出的每日城市安排
- `poi_pool` — Step 4 输出的候选池
- `UserConstraints` — 用户约束（must_visit 等）
- `CircleProfile` — 提示词注入

### 输出
```python
{
    "daily_activities": [
        {
            "day": 1,
            "city": "osaka",
            "theme": "大阪都市美食",
            "main_activities": [
                {"entity_id": "xxx", "name": "道顿堀", "visit_minutes": 90, "why": "关西第一站的经典体验"}
            ],
            "time_anchors": [],
            "main_corridor": "namba_dotonbori",
            "secondary_corridors": ["shinsaibashi"],
            "intensity": "light"
        }
    ],
    "unassigned_must_visit": [],
    "thinking_tokens_used": 9200
}
```

### AI 调用规格
| 参数 | 值 |
|------|-----|
| 模型 | claude-opus-4-6 |
| max_tokens | 6000 |
| thinking_budget | 12000 |

### 提示词 6 条决策原则
1. must_visit 必须安排，放最合适的天
2. 同走廊景点安排同一天（减少通勤）
3. 考虑最佳游览时间（寺庙清晨、夜景傍晚）
4. 到达日/离开日只安排 1 个轻量活动
5. heavy 天可 2 个主活动，light 天最多 1 个
6. 同一天不要 2 个同类型景点

### Fallback
- 按 city_code 匹配分配 must_visit
- 不足时按 grade 排序补充 top-1 POI
- 从选中活动 tag 提取 main_corridor（排除通用标签）

### 关键设计决策
**为什么 main_corridor 很重要？**
corridor 是后续所有步骤的地理锚点：Step 6 用它算酒店地理中心，Step 13 用它选走廊内餐厅，Step 15 用它限定 Plan B 范围。一个好的 corridor 意味着当天活动地理集中，通勤少。

### 测试要点
- must_visit 全部出现在某一天的 main_activities 中
- unassigned_must_visit 应为空（除非池中没有对应实体）
- light 天活动数 ≤ 1
- 同一天不出现 2 个 entity_type 完全一样的景点

---

## Step 5.5: validate_and_substitute (Sonnet AI)

### 职责
检查 Step 5 选出的活动是否在旅行日期内存在 5 种冲突，有冲突时从候选池找替代。

### 5 种冲突检测

| # | 冲突类型 | 检测方式 | 示例 |
|---|---------|---------|------|
| 1 | 定休日 | entity_id in closed_entities | "周二定休" |
| 2 | 营业时间不足 | arrival + visit_mins > close_time | "预计10:00到，需90分钟，但18:00闭馆" |
| 3 | 最后入场超时 | arrival > last_admission | "预计17:00到，最后入场16:00" |
| 4 | 预约制/场次制 | 检查 hard_to_book 标签 + time_slot 匹配 | "场次10:00/14:00，预计15:30不匹配" |
| 5 | 季节性闭馆 | 检查 special_closure 日期范围 | "年度检修 01-15~02-28" |

### 替代候选评分（score 越小越优先）
```
score = grade_weight * 10
  同主走廊+同类型:  score -= 50  (最优)
  同走廊组+同类型:  score -= 30
  同主走廊不同类型: score -= 20
  不在走廊:        score += 50  (最低)
  tag 交集越多:    score -= (交集数 * 3)
```

### 输出
```python
{
    "validated_activities": {...},  # 修改后的 daily_activities
    "substitutions": [{"day": 2, "original": "金阁寺", "replacement": "龙安寺", "reason": "周二定休"}],
    "no_substitute_found": [...]
}
```

### 关键设计决策
**为什么 5.5 在 Step 8 之后执行（编排顺序）？**
虽然编号是 5.5，但 orchestrator 中实际执行顺序是 5 → 8 → 5.5。因为 5.5 需要 Step 8 的 `daily_constraints`（含 closed_entities）才能做定休日检测。

**为什么用 Sonnet 而不是 Opus？**
候选已经按 score 排好了，AI 只需要从 top-5 中选一个。轻量决策，不需要深度推理。

### 测试要点
- 定休日实体被替代
- 替代活动在同走廊
- 无替代可用时记录在 no_substitute_found

---

## Step 6: build_hotel_pool (系统两阶段筛选)

### 职责
从 DB 读取酒店，经过预算过滤 + Haversine 粗筛 + 通勤精排，输出排序后的酒店候选池。

### 两阶段筛选

**Phase 1: Haversine 粗筛**
1. 计算 POI 池的加权地理中心（权重=visit_minutes）
   ```
   center_lat = Σ(lat_i × visit_mins_i) / Σ(visit_mins_i)
   ```
2. 对每家酒店算 Haversine 距离（球面距离）
3. 排序取 top 100

**Phase 2: 通勤精排**（需要 daily_main_corridors）
1. 对每个 top-100 酒店，查询到每天主走廊代表 POI 的通勤时间
2. 累加所有天的通勤分钟数
3. 按 avg_commute 升序排列，取 top N

### 预算过滤规则
```
用户 budget → 只能选 budget 酒店
用户 mid    → 可选 budget/mid
用户 premium → 可选 budget/mid/premium
用户 luxury → 可选任何
```

### 输出
`list[CandidatePool]`，review_signals 包含：
```python
{
    "distance_from_poi_center_km": 2.3,
    "star_rating": 4.0,
    "google_rating": 4.5,
    "booking_score": 8.7,
    "amenities": ["wifi", "breakfast", ...]
}
```

### 关键设计决策
**为什么不直接用通勤时间？为什么要 Haversine 粗筛？**
Google Routes API 的 transit 模式有 100 elements 上限。如果有 500 家酒店 × 5 天 = 2500 次查询，超限。Haversine 粗筛把范围缩到 100 家，再精排。

**加权地理中心为什么用 visit_minutes 做权重？**
停留时间长的景点对酒店位置的影响更大。如果花 3 小时逛东山，30 分钟看大阪城，酒店应该更靠近东山。

### 测试要点
- budget 用户不出现 luxury 酒店
- do_not_go 的酒店不在池中
- risk_flags 含 renovation 的酒店被过滤
- 池为空时返回空列表而非报错

---

## Step 7.5: check_commute_feasibility (系统/API)

### 职责
对 Step 6 输出的酒店候选，逐一查询到每天主走廊的公交通勤时间，判定可行性。

### 判定规则（阈值=45 分钟）
| 状态 | 条件 | 含义 |
|------|------|------|
| pass | 所有天 ≤ 45min | 推荐 |
| warning | 部分天 > 45min | 可接受，需提示 |
| fail | 所有天 > 45min | 不可用 |

### 输出
```python
[
    {
        "hotel_id": "xxx",
        "status": "pass",
        "avg_commute_minutes": 22,
        "max_commute_minutes": 35,
        "commute_details": [
            {"day": 1, "corridor": "namba", "minutes": 20, "mode": "transit"},
            {"day": 2, "corridor": "higashiyama", "minutes": 35, "mode": "transit"}
        ]
    }
]
```

### 错误处理（分级）
| 异常类型 | 日志级别 | Fallback | mode 标记 |
|---------|---------|----------|----------|
| ValueError/KeyError | error | 30min | fallback_data_error |
| ConnectionError/Timeout | warning | 30min | fallback_network_error |
| 其他 Exception | error | 30min | fallback_unknown_error |

### 关键设计决策
**为什么串行查询不并发？**
Google Routes API transit 模式 100 elements 上限。串行查询保证不超限。

**Fallback 30 分钟是否合理？**
30 分钟是日本城市公交的典型通勤时间。过高会漏掉好酒店，过低会放进远酒店。保守选择中间值。mode 标记让后续 step 知道这是估算值。

---

## Step 7: select_hotels (Sonnet AI)

### 职责
从通勤检查后的酒店候选中，选出最终住宿方案（1-2 家酒店）。

### 输入
- `hotel_pool` — Step 6 输出
- `commute_results` — Step 7.5 输出
- `daily_activities` — Step 5/5.5 输出
- `UserConstraints` — 预算、画像

### 输出
```python
{
    "hotel_plan": {
        "primary": {
            "hotel_id": "xxx",
            "name": "京都格兰维亚",
            "nights": 4,
            "cost_per_night_jpy": 15000,
            "meals_included": {"breakfast": true, "dinner": false},
            "check_in": "15:00",
            "check_out": "11:00",
            "avg_commute_minutes": 22,
            "why_selected": "位置最优，覆盖4天主走廊"
        },
        "secondary": null
    },
    "hotel_switch_day": null
}
```

### Sonnet 提示词 7 条决策原则
1. **通勤优先** — avg < 30min 理想
2. **走廊覆盖** — 覆盖尽可能多天的主走廊
3. **预算匹配** — 不超 budget_tier
4. **含餐加分** — 含早餐省时间
5. **评分优先** — google_rating + booking_score
6. **换酒店条件** — 只在明显区域切换（如大阪→京都）时换
7. **不需要换就只选 1 家**

### Fallback 评分函数
```
score = (-avg_commute * 2)
      + (google_rating * 10)
      + booking_score
      + (grade_bonus * 5)     # S=4, A=3, B=2, C=1
      + (breakfast_bonus * 5)  # 含早餐+5
```

### 含餐判断
从 amenities + tags 中检测关键词：
- 早餐：breakfast / 朝食 / 朝食付き / breakfast_included
- 晚餐：dinner / 夕食 / 夕食付き / half_board

### 测试要点
- primary.hotel_id 必须在候选池中
- nights = total_days - 1（或更少如果有 switch）
- 含餐标记正确传递到 Step 8

---

## Phase 2 整体原则

1. **AI 做选择，系统做校验** — Step 5 选活动（AI），5.5 校验冲突（AI+规则）；Step 6 筛酒店（系统），7 选酒店（AI）
2. **走廊是核心概念** — main_corridor 串联活动选择、酒店选址、后续餐厅筛选
3. **通勤时间是硬约束** — 45 分钟阈值，超限则 warning/fail，不是建议
4. **Opus vs Sonnet 分工** — 活动选择是多维取舍（Opus）；酒店选择是排序决策（Sonnet）

## Phase 2 数据流

```
Step 3 cities_by_day + Step 4 poi_pool
    │
    ▼
Step 5: plan_daily_activities (Opus)
    │ → daily_activities {main_activities[], main_corridor, intensity}
    │
    ├──▶ Step 8: build_daily_constraints (先执行)
    │       │ → daily_constraints {closed_entities[], sunrise, sunset}
    │       │
    │       ▼
    │   Step 5.5: validate_and_substitute (Sonnet)
    │       → validated_activities {替代冲突活动}
    │
    ├──▶ Step 6: build_hotel_pool (系统)
    │       │ → hotel_pool (Haversine粗筛 → 通勤精排)
    │       │
    │       ▼
    │   Step 7.5: check_commute_feasibility (API)
    │       │ → commute_results {status, avg/max_commute}
    │       │
    │       ▼
    │   Step 7: select_hotels (Sonnet)
    │       → hotel_plan {primary, secondary?, meals_included}
    │
    └──▶ Phase 3...
```
