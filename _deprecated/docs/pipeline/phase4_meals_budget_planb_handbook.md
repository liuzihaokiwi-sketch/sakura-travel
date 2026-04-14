# Phase 4: 餐饮 + 预算 + Plan B + 手账本 (Step 13-16)

> 代码位置：`app/domains/planning_v2/step13~step16`
> 执行方：系统(DB) + Sonnet AI + 纯 Python
> 目的：补齐餐饮、算清预算、准备备案、生成手账内容

---

## 本阶段的核心目标

Phase 3 给出了精确到分钟的时间线骨架。Phase 4 的任务是：
- 为每天每餐选择具体餐厅 → Step 13 + 13.5
- 计算全程预算明细 → Step 14
- 为每天准备雨天/疲劳/预约失败的 Plan B → Step 15
- 生成手账本的文案和贴士 → Step 16

Phase 4 结束后，行程产物完整，可以交付渲染。

---

## Step 13: build_restaurant_pool (系统过滤)

### 职责
按走廊、菜系、营业时段构建分餐候选池（早/午/晚分开），供 Step 13.5 的 AI 选择。

### 输入
- `UserConstraints` — 预算、黑名单
- `circle_cities` — 圈内城市
- `daily_constraints` — 酒店含餐信息
- `main_corridors` — Step 5 的主走廊列表
- `CircleProfile` — 价格上限配置

### 输出
```python
{
    "breakfast_pool": [CandidatePool, ...],   # 如酒店不含早餐
    "lunch_pool": {
        "restaurants": [CandidatePool, ...],  # 正餐
        "cafes": [CandidatePool, ...]         # 咖啡/甜品
    },
    "dinner_pool": [CandidatePool, ...],      # 如酒店不含晚餐
    "pool_stats": {
        "total_restaurants": 85,
        "breakfast_available": true,
        "dinner_available": true,
        "lunch_flex": true
    }
}
```

### 过滤规则
1. entity_type = 'restaurant'，city_code in circle_cities
2. is_active = true
3. 排除 do_not_go
4. 价格 ≤ restaurant_price_cap[budget_tier]（从 circle.budget_config 读取）
5. 走廊内标记 in_main_corridor（不排除，用于排序）
6. 菜系分类：cafe/sweets vs restaurant
7. **营业时段校验**

### 营业时段校验逻辑
```python
_MEAL_TIME_WINDOWS = {
    "breakfast": ("06:30", "09:30"),
    "lunch": ("11:00", "14:00"),
    "dinner": ("17:00", "21:00"),
}
```
优先检查分段格式（`lunch_start/lunch_end`），fallback 到通用格式（`open_time/close_time`），无数据时宽容通过。

### 酒店含餐逻辑
```
所有天都含早餐 → breakfast_pool = []（跳过早餐池构建）
所有天都含晚餐 → dinner_pool = []（跳过晚餐池构建）
```
这与 Step 7 的 meals_included → Step 8 的 hotel_breakfast_included → Step 13 的跳过逻辑形成完整链路。

### 关键设计决策
**为什么按餐食时段分三个池？**
早餐候选（cafe/bakery）和晚餐候选（正餐）完全不同。分开后 Step 13.5 的 AI 选择空间更精准，不会给晚餐推咖啡厅。

**走廊内餐厅为什么不排除走廊外的？**
走廊优先但不排除——万一走廊内只有 2 家符合的，需要走廊外的补充。通过 `in_main_corridor` 标记让 AI 知道优先级。

### 测试要点
- 酒店全含早餐时 breakfast_pool 为空
- budget 用户的餐厅价格 ≤ cap
- 走廊内餐厅的 in_main_corridor 标记为 true
- 早上不营业的餐厅不在 breakfast_pool

---

## Step 13.5: select_meals (Sonnet AI)

### 职责
从餐厅池中为每天每餐选择具体餐厅，确保菜系多样性。

### 输入
- `restaurant_pool` — Step 13 输出
- `timeline` — Step 12 输出
- `daily_constraints` — Step 8 输出
- `UserConstraints` — 预算

### 输出
```python
{
    "meal_selections": [
        {
            "day": 1,
            "breakfast": null,         # 酒店含早餐
            "lunch": {
                "entity_id": "xxx",
                "name": "某拉面店",
                "cuisine": "ramen",
                "type": "restaurant",
                "why": "在东山走廊，步行5分钟"
            },
            "dinner": {
                "entity_id": "yyy",
                "name": "某居酒屋",
                "cuisine": "izakaya",
                "type": "restaurant",
                "why": "距酒店近，评分高"
            }
        }
    ],
    "cuisine_variety_check": true
}
```

### 选择规则（8 条）
1. 酒店含早餐 → breakfast = null
2. 酒店含晚餐 → dinner = null
3. 午餐优先从 restaurants 池选正餐，紧凑时可选 cafes
4. **不同天不重复同一菜系**
5. **寿司/拉面全程最多各 2 次**（CUISINE_FREQUENCY_CAP）
6. 优先 in_main_corridor=true 的餐厅
7. 考虑 budget_tier
8. 晚餐考虑距酒店距离

### 菜系频率控制
```python
CUISINE_FREQUENCY_CAP = {"sushi": 2, "ramen": 2, "寿司": 2, "拉面": 2}
```
超标时 `cuisine_variety_check=false`，记录 warning。

### 关键设计决策
**为什么菜系多样性是硬规则？**
"连续三天吃拉面"是差评的典型原因。菜系多样性直接影响用户体验和手账本的内容丰富度。

### 测试要点
- 酒店含餐时对应餐为 null
- 同一菜系不连续出现
- 寿司/拉面全程不超过 2 次
- 选择的餐厅在池中有对应 entity_id

---

## Step 14: estimate_budget (纯 Python)

### 职责
基于 CircleProfile.budget_config 计算全程预算明细。不调用 DB，不调用 AI。

### 输入
- `daily_sequences` — Step 9 输出
- `hotel_plan` — Step 7 输出
- `restaurant_selections` — Step 13.5 输出
- `budget_tier` — 用户预算档位
- `CircleProfile` — 预算常量来源

### 从 circle.budget_config 读取的字段
| 字段 | 说明 | 示例（关西/JPY） | 示例（广府/CNY） |
|------|------|-----------------|-----------------|
| hotel_per_night | 各档位每晚酒店费 | mid: 10000 | mid: 350 |
| transport_per_day | 各档位日交通费 | mid: 1200 | mid: 35 |
| food_floor_per_day | 各档位日餐费保底 | mid: 3500 | mid: 200 |
| default_admission | 各类别默认门票 | museum: 1000 | museum: 50 |
| misc_buffer_rate | 杂费比例 | 0.10 | 0.10 |

### 计算公式
```
每日 = 酒店 + 门票 + 餐费 + 交通 + 杂项
     = hotel_nightly
     + Σ(POI 门票)
     + (breakfast + lunch + dinner)
     + transport_daily
     + (上述合计 × misc_rate)

全程 = Σ(每日)
CNY  = 全程 × circle.cny_rate
```

### 餐费默认值分配
```
food_floor 按比例拆分：早餐 20% / 午餐 30% / 晚餐 50%
```

### 门票费获取优先级
1. `cost_local`（明确值，本地货币）— 兼容旧字段 `admission_fee_jpy` / `cost_jpy`
2. `admission_free` 标记 → 0
3. `poi_category` → `circle.budget_config.default_admission[category]`
4. 兜底：无（budget_config 必须配齐，由 CircleProfile.validate() 保证）

### 输出
```python
{
    "daily_breakdown": [
        {"date": "2026-04-01", "hotel": 10000, "activities": 1500, "meals": 3500, "transport": 1200, "misc": 960, "total": 17160}
    ],
    "trip_total_local": 68640,
    "currency": "JPY",
    "trip_total_cny": 3226,
    "budget_tier": "mid",
    "within_budget": true,
    "breakdown_by_category": {"hotel": 40000, "activities": 3000, "meals": 14000, "transport": 4800, "misc": 6840}
}
```

### 关键设计决策
**为什么不在 Step 14 用 AI？**
预算是纯数学计算。用 AI 会引入"幻觉数字"——AI 可能编造门票价格。必须从数据源获取真实价格。

**配置驱动**：所有预算常量从 `CircleProfile.budget_config` 读取（circle_registry.json 配置）。CircleProfile 是必传参数，不允许 None。

### 测试要点
- 最后一天无酒店费用
- CNY 换算正确（JPY 圈用 0.047，CNY 圈用 1.0）
- within_budget 判断合理
- 酒店含餐时对应餐费为 0

---

## Step 15: build_plan_b (Sonnet AI)

### 职责
为每天准备 1-2 个备选活动，应对三种场景：下雨、疲劳、预约失败。

### 三种触发场景

| 触发 | 替代条件 | 示例 |
|------|---------|------|
| rain | 原活动 outdoor → 替代为 indoor | 伏见稻荷（户外）→ 京都国立博物馆（室内） |
| fatigue | 原活动 heavy → 替代为 light | 岚山全天徒步 → 河边咖啡厅慢逛 |
| reservation_fail | 原活动需预约 → 替代为无需预约 | 某预约制餐厅 → 免预约同类型店 |

### 替代规则
1. 必须在同天主走廊范围内（不额外增加通勤）
2. 不与当天其他活动重复
3. 每天最多 2 个 Plan B
4. 优先 grade 较高的替代

### 标签分类
```python
OUTDOOR_TAGS = {outdoor, garden, park, hiking, beach, ...}
INDOOR_TAGS = {indoor, museum, gallery, shopping, ...}
RESERVATION_TAGS = {reservation_required, booking_required, ...}
HEAVY_TAGS = {hiking, mountain, long_walk, ...}
```

### 输出
```python
{
    "plan_b": [
        {
            "day": 2,
            "alternatives": [
                {
                    "trigger": "rain",
                    "replace_entity": "kyo_fushimi",
                    "replace_name": "伏见稻荷大社",
                    "alternative_entity": "kyo_museum",
                    "alternative_name": "京都国立博物馆",
                    "reason": "室内替代，同东山走廊"
                }
            ]
        }
    ]
}
```

### 关键设计决策
**为什么 Plan B 限制在同走廊？**
换活动不应该增加通勤——用户已经在那个区域了。如果 Plan B 在城市另一端，执行时反而更乱。

**为什么每天最多 2 个？**
手账本印刷空间有限。3 个以上 Plan B 信息过载，用户反而不知道怎么选。

### 测试要点
- rain 替代活动的 tags 含 indoor
- fatigue 替代活动不含 heavy 标签
- 每天 alternatives ≤ 2
- 替代活动不与当天已有活动重复

---

## Step 16: generate_handbook_content (Sonnet AI)

### 职责
为手账本生成三类装饰内容：活动卡片文案、每日小贴士、休息站推荐。

### 注意：Step 16 失败不阻塞管线
在 orchestrator 中用 try/except 包裹，失败时 `state.handbook = {}`。

### 三类输出

**1. activity_cards — 每个活动的文案**
```python
{
    "entity_id": "kyo_fushimi",
    "copy_zh": "千本鸟居的朱红色隧道...",      # 30-50字，生动有趣
    "insider_tip": "清晨6点前到几乎没人",       # 内行贴士
    "photo_spot": "四ツ辻展望台"                # 最佳拍照点
}
```

**2. daily_tip — 每日小贴士**
- 到达日：时差适应
- 离开日：打包退税
- 高强度日：体力分配
- 普通日：天气着装、文化礼仪

**3. rest_stops — 仅高强度日（最多 3 个）**
```python
{
    "name": "% Arabica 京都东山",
    "type": "cafe",
    "why": "走累了来杯咖啡，看八坂塔",
    "near_activity": "清水寺"
}
```

### 高强度日判断
POI 数量 ≥ 5 或总活动时长 ≥ 420 分钟（7h）或含高强度标签

### Rest Stop 候选规则
1. 排除当天已安排的实体
2. 标签含 cafe/coffee/sweets/tea/rest
3. 主走廊内优先
4. 按 grade 排序，最多 3 个

### Fallback
- copy_zh: "{name} — 值得一去的好地方"
- insider_tip: "建议提前查看官网确认开放时间"
- photo_spot: "入口处"

### 关键设计决策
**为什么 Step 16 不阻塞？**
手账本文案是锦上添花，不是行程必要组成。如果 Sonnet 调用失败或超时，行程仍然完整可用。

**insider_tip 的质量标准？**
这是产品差异化的关键——"攻略上找不到的本地推荐"。AI 生成的 tip 需要后续人工审核。数据层面，优先从 review_signals 提取真实评论信息，而不是 AI 编造。

### 测试要点
- 每个 POI slot 有对应的 activity_card
- copy_zh 长度 30-50 字
- 高强度日有 rest_stops（≤ 3 个）
- 非高强度日 rest_stops 为空

---

## Phase 4 整体原则

1. **数据契约链路** — Step 7 meals_included → Step 8 hotel_breakfast_included → Step 13 跳过早餐池 → Step 13.5 breakfast=null → Step 14 早餐费=0。任何一环断裂都会导致错误。
2. **预算数字来自真实数据** — Step 14 从 DB 字段和 circle.budget_config 获取，不用 AI 估算价格。
3. **手账本不阻塞** — Step 16 是唯一允许静默失败的步骤。其他步骤失败都必须上报。
4. **菜系多样性是体验底线** — 连续重复菜系 = 差评。CUISINE_FREQUENCY_CAP 是硬限制。

## Phase 4 数据流

```
Step 12 timeline
    │
    ├──▶ Step 13: build_restaurant_pool (系统)
    │       │ → {breakfast_pool, lunch_pool, dinner_pool}
    │       │
    │       ▼
    │   Step 13.5: select_meals (Sonnet)
    │       │ → meal_selections {day, breakfast, lunch, dinner}
    │       │
    │       ▼
    │   Step 14: estimate_budget (纯Python)
    │       → {trip_total_local, currency, trip_total_cny, daily_breakdown}
    │
    ├──▶ Step 15: build_plan_b (Sonnet)
    │       → plan_b {day, alternatives[{trigger, replacement}]}
    │
    └──▶ Step 16: generate_handbook_content (Sonnet, 非阻塞)
            → handbook {activity_cards, daily_tip, rest_stops}
```

---

## 管线整体产出

所有 Phase 完成后，orchestrator 组装最终输出：

```python
day_frames = [
    {
        "day": 1,
        "date": "2026-04-01",
        "timeline": [...slots...],      # Step 12
        "meals": {...},                  # Step 13.5
        "plan_b": {...},                 # Step 15
        "handbook": {...},               # Step 16
        "budget": {...}                  # Step 14
    }
]
```

与 v1 管线返回签名完全对齐：`(success, plan_id, day_frames, design_brief, runtime_context)`
