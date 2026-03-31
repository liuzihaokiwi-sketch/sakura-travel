# 行程规划最终工作流 v4（16步）

> 最后更新: 2026-03-31
> 状态: 最终定稿，可用于工程开发

---

## 核心设计原则

1. **系统缩圈 → AI 判断** — 系统做资格筛选和可行性检查，AI 做取舍和排序
2. **硬规则优先** — 营业时间、定休日、交通时刻表、时间窗约束由系统检查，不让 AI 猜
3. **容错链清晰** — 冲突发生时有确定性的处理顺序，不让系统和 AI 互相甩锅
4. **每日时间线独立成层** — 时间线不能散在各步骤里，必须有专门的排程和检查层
5. **候选 vs 唯一的显式分工** — 宏观决策输出候选，排程决策输出唯一

---

## 第一阶段：收集约束 + 宏观方案（Step 1-4）

### Step 1：收集用户约束

**输入**：用户的所有先决条件

* 出发日期、返程日期、航班时间
* 总天数
* 预算档（economy / standard / premium）
* 人群构成（情侣 / 亲子 / 单人 / 老人 / 小孩）
* 用户画像标签（first_visit / culture_deep / foodie / photo / nature_outdoor / time_tight 等）
* 已锁定项目（必须去某景点 / 必须住某酒店等）
* 明确禁忌（不吃生的 / 不能爬坡 / 拒绝夜间活动等）

**系统动作**：整理成结构化数据，不做任何判断

**输出**：用户约束包

```json
{
  "trip_window": {
    "departure_date": "2026-05-10",
    "arrival_date": "2026-05-14",
    "total_days": 5
  },
  "user_profile": {
    "party_type": "couple",
    "budget_tier": "standard",
    "first_visit": true,
    "tags": ["photo", "foodie", "time_tight"]
  },
  "constraints": {
    "must_visit": ["伏见稻荷", "清水寺"],
    "must_avoid": ["steep_climb"],
    "must_stay": null
  }
}
```

---

### Step 2：喂"区域级摘要"给 AI

**系统动作**：从候选库里提取每个城市/区域的高层摘要

不喂具体景点、具体餐厅，只喂：

* 区域风格和代表性内容
* 3 星 / 2 星 / 1 星玩法的数量和风格
* 是否适合做基地 / 中转 / 一日游
* 季节相关玩法
* 大致交通角色（起点 / 中点 / 终点）

**输出示例**：

```json
{
  "region_summary": {
    "kyoto": {
      "style": "古都、传统、寺庙、和服体验",
      "star3_count": 13,  // 伏见稻荷、清水寺、金阁寺等
      "base_suitability": "high",
      "seasonal_highlights": "樱花(3月下-4月上) / 红叶(11月中-12月初)",
      "transport_role": "hub"
    },
    "osaka": {...},
    "nara": {...}
  }
}
```

---

### Step 3：AI 输出城市组合候选

**AI Prompt 输入**：用户约束包 + 区域级摘要

**AI 决策**：
* 哪些城市值得去（结合用户偏好、季节、时间、已锁定项）
* 每城停留几天
* 大致访问顺序（考虑机场进出、季节事件时序）
* 每天主题建议（文化日 / 自然日 / 城市漫游日 / 美食日 / 恢复日）
* 每天强度建议（light / medium / heavy）

**输出策略**：**Top 2-3 的城市组合候选**，不输唯一

```json
{
  "candidates": [
    {
      "rank": 1,
      "cities": ["kyoto", "osaka"],
      "days_per_city": [3, 2],
      "route_order": ["kyoto_first"],
      "daily_themes": ["arrival_light", "kyoto_culture_heavy", "kyoto_nature_medium", ...],
      "daily_intensity": ["light", "heavy", "medium", "heavy", "light"],
      "rationale": "樱花季京都优先，交通最优"
    },
    {
      "rank": 2,
      "cities": ["kyoto", "osaka", "nara"],
      "days_per_city": [2, 2, 1],
      ...
    }
  ]
}
```

**用户 / 运营选择**：选 Rank 1 还是备选，继续走 Step 4

---

### Step 4：系统按主方案缩"玩的候选池"

**输入**：选定的城市组合方案

**系统动作**：从完整候选池里切出一小块

保留条件：
* 城市在选定的城市列表里
* 星级是 3 星 + 强 2 星 + 少量精选 1 星（不是全部 1 星）
* 当季 relevant（樱花季保留春季景点，冬季排除）
* 与 Step 3 的每日主题匹配

**输出**：

```json
{
  "curated_poi_pool": [
    {
      "id": "kyo_fushimi_inari",
      "name_zh": "伏见稻荷大社",
      "grade": "S",
      "city": "kyoto",
      "matching_themes": ["culture", "photo"],
      ...
    },
    ...  // 总共 50-80 个而不是全部 400+ 个
  ]
}
```

---

## 第二阶段：锁主活动 + 主片区（Step 5-7.5）

### Step 5：AI 选主活动、锚点、每日片区

**输入**：缩过的候选池 + Step 3 的主题和强度建议

**AI 决策**：
* 每天的主活动（真正值得专程去的 3 星点）
* 每个锚点（演出、日落、定时入场、季节活动）
* 每天的主片区 / 走廊（上午 / 下午 / 晚上各在哪片区）
* 可插拔模块池（1 星点和补充点）

**输出**：

```json
{
  "daily_plan": {
    "day1": {
      "theme": "arrival_light",
      "intensity": "light",
      "main_activity": "kyo_fushimi_inari",
      "main_corridors": ["fushimi"],
      "anchors": [],
      "optional_modules": ["kyo_xxx_1star", "kyo_yyy_1star"]
    },
    "day2": {
      "theme": "kyoto_culture_heavy",
      "intensity": "heavy",
      "main_activities": ["kyo_kiyomizu", "kyo_gion"],
      "main_corridors": ["higashiyama", "gion"],
      "anchors": [{"name": "日落于清水寺舞台", "time_window": "17:30-18:30"}],
      "optional_modules": [...]
    }
  }
}
```

---

### Step 5.5：主活动初筛校验

**系统动作**：对 Step 5 选出的主活动立刻做定休日检查

检查内容：
* 用户选定的每个主活动，在分配给它的那天是否营业？
* 开放时间是否太短（比如 16:00 就关门）？
* 是否与固定班次交通时段天然冲突？

**检查失败的处理**：直接标记为"改期或换备选"，不等到后面

**输出**：

```json
{
  "validation_result": "pass" | "fail_with_suggestions",
  "issues": [
    {
      "activity": "kyo_xxx",
      "issue": "closed_on_monday",
      "day_assigned": 2,  // 是周几？
      "suggestion": "改期到 day3 或换成 kyo_yyy"
    }
  ]
}
```

---

### Step 6：系统缩住宿区域和酒店候选

**输入**：Step 5 的主活动和主片区

**系统动作**：
* 根据主活动密度，找出 2-3 个最合适的住宿区域
* 从这些区域里提取酒店候选（预算匹配 + 评分 + 评论量）

**输出**：

```json
{
  "hotel_options": [
    {
      "region": "higashiyama",
      "suitability_score": 0.95,
      "candidates": [
        {
          "id": "hotel_a",
          "name": "京都东山町屋旅馆",
          "experience_grade": "A",
          "price_tier": "premium",
          "distance_to_main_activity": "500m",
          "candidates_rank": 1
        },
        ...  // Top 3-5
      ]
    },
    {
      "region": "gion",
      "suitability_score": 0.88,
      "candidates": [...]
    }
  ]
}
```

---

### Step 7：AI 选住宿区域与酒店

**输入**：Step 6 的住宿区域和酒店候选

**AI 决策**：
* 主住宿区域方案
* 备选区域（以防主方案与后续日程冲突）
* 对应的具体酒店

**输出策略**：**唯一方案 + 1-2 个备选**

```json
{
  "hotel_plan": {
    "primary": {
      "region": "higashiyama",
      "hotels": [
        {
          "dates": ["day1", "day2"],
          "hotel_id": "hotel_a",
          "check_in": "15:00",
          "check_out": "11:00"
        }
      ]
    },
    "backup_options": [
      {
        "region": "gion",
        "reason": "如果 higashiyama 与某日片区冲突"
      }
    ]
  }
}
```

---

### Step 7.5：住宿区与每日片区通勤检查

**系统动作**：生成"住宿区→各日主片区"的通勤矩阵

用 Google Routes API 的 `computeRouteMatrix` 快速算出：
* 住宿区 → Day1 主片区 travel time
* 住宿区 → Day2 主片区 travel time
* ... 以此类推

**检查规则**：
* 如果某日通勤超过 30 分钟，标黄（可接受但需注意）
* 如果某日通勤超过 45 分钟，标红（建议换住宿区或改日程）

**输出**：

```json
{
  "commute_matrix": [
    {
      "from_region": "higashiyama",
      "routes": [
        {"day": 1, "to_corridor": "fushimi", "travel_min": 25, "status": "yellow"},
        {"day": 2, "to_corridor": "higashiyama", "travel_min": 2, "status": "green"},
        {"day": 3, "to_corridor": "arashiyama", "travel_min": 50, "status": "red"}
      ]
    }
  ],
  "recommendation": "如果 day3 通勤过远，建议改备选住宿区"
}
```

如果标红较多，回到 Step 7 调整住宿区。

---

## 第三阶段：每日时间线排程（Step 8-12）

### Step 8：系统整理每日约束包

**系统动作**：为每一天单独编制约束数据

包含：
* 当天开放时间（sunrise / sunset）
* 当天是周几（因此哪些实体定休）
* 低频 / 固定班次交通的时刻
* 锚点时间（演出 / 日落 / 定时讲解）
* 该天有效游玩时长（arrival_time 到 return_time）

**数据来源**：
* 日出日落：天文数据
* 定休日：实体的 `regularOpeningHours` 或人工标注
* 低频交通：各地交通部门的 timetable
* 锚点：Step 5 里选出的

**输出示例**：

```json
{
  "daily_constraints": {
    "day2": {
      "date": "2026-05-11",
      "day_of_week": "Monday",
      "sunrise": "05:30",
      "sunset": "18:45",
      "available_hours": 13,  // 从 05:30 到 18:45
      "closed_entities": ["museum_x", "restaurant_y"],  // 周一定休
      "low_freq_transits": [
        {"route": "cable_car_1", "departures": ["09:00", "10:00", "14:00", "16:00"]}
      ],
      "anchors": [
        {
          "name": "日落于清水舞台",
          "time_window": ["17:30", "18:30"],
          "location": "kyo_kiyomizu",
          "flexibility": "hard"  // 不能动
        }
      ]
    }
  }
}
```

---

### Step 9：AI 选每日最优顺序

**输入**：
* Step 5 的主活动、片区、可插拔模块
* Step 8 的每日约束包

**AI 决策**（核心是平衡两个目标）：
1. **满足时间窗** — 锚点、低频交通必须接上
2. **地理最优** — 在满足时间窗的前提下，选择地理上更优的顺序

这里**不是死板按时间顺序**，而是先考虑约束，再优化地理。

**输出**（重要！输出必须包含三项）：

```json
{
  "daily_sequence": {
    "day2": {
      "order": [
        {"entity": "kyo_kiyomizu", "position": 1, "reason": "morning 最佳体验"},
        {"entity": "kyo_gion", "position": 2, "reason": "下一个片区，步行接驳"},
        {"entity": "anchor_sunset", "position": 3, "time_locked": "17:30-18:30"}
      ]
    }
  },
  "remaining_slack_minutes": {
    "day2": 90  // 当天还剩 90 分钟余量
  },
  "insertion_slots": {
    "day2": [
      {"position": "between_1_and_2", "available_min": 30},
      {"position": "after_anchor", "available_min": 60}
    ]
  },
  "drop_order": [
    "kyo_optional_1star_a",
    "kyo_optional_1star_b"
  ]
}
```

关键点：
* **remaining_slack_minutes** — 告诉后续步骤还能塞多少内容
* **insertion_slots** — 告诉后续步骤哪里能插补充项
* **drop_order** — 如果超载，先删哪些

---

### Step 10：系统做每日时间线可行性检查

**检查项**（红黄绿灯）：

1. **时间窗冲突** — 锚点、低频交通是否与主活动冲突
2. **交通时间是否赶得上** — 活动间的 travel time 是否在预期内
3. **容量是否超载**：
   - light：占用不超过 80%
   - medium：不超过 85%
   - heavy：不超过 90%
4. **动线是否反常** — 是否有明显折返

**输出**：

```json
{
  "feasibility_check": {
    "day2": {
      "status": "fail",
      "violations": [
        {
          "type": "capacity_exceeded",
          "current_usage": 92,
          "limit": 90,
          "severity": "high"
        },
        {
          "type": "travel_time_tight",
          "from": "kyo_kiyomizu",
          "to": "restaurant_gion",
          "planned_min": 15,
          "required_min": 20,
          "severity": "medium"
        }
      ]
    }
  }
}
```

如果 status 是 fail，进入 Step 11。

---

### Step 11：冲突处理链

**这是系统和 AI 的责任分界最清楚的一步。**

当 Step 10 检查失败时，**固定走这个链条**：

```
检查失败 →

1️⃣ 系统自动删可插拔模块
   规则：按 drop_order 依次删，直到满足容量

2️⃣ 如果还不行，系统自动压缩非核心停留
   规则：把 2 星点的停留时间从 45min 压到 30min，以此类推

3️⃣ 如果还不行，系统自动降强度
   规则：heavy → medium（重新计算余量）

4️⃣ 如果还是不行，回退 AI
   信息：告诉 AI
     - 当前冲突的具体项
     - 已删除了哪些可插拔项
     - 哪些锚点是死的不能动
     - 哪些主活动组合在一天内物理上不可行
   AI 任务：重新选主活动或者改日期分配
```

**关键规则**：
* 每一步都要记录"改了什么、为什么改"
* 只有链条都走完仍不可行，才回退 AI
* AI 回退时，**不是让 AI 猜，而是给 AI 明确的反馈**

**输出**：

```json
{
  "conflict_resolution": {
    "day2": {
      "step1_drop_modules": ["kyo_optional_1star_a"],
      "step1_status": "still_fail",
      "step2_compress_poi": ["kyo_xxx_2star"],  // 压缩时间
      "step2_status": "still_fail",
      "step3_downgrade_intensity": "medium",
      "step3_status": "pass",
      "final_resolution": "day2 强度从 heavy 降到 medium"
    }
  }
}
```

---

### Step 12：AI 输出最终每日时间线骨架

**输入**：Step 11 处理后的可行方案

**AI 输出**（精确到分钟）：

```json
{
  "final_daily_schedule": {
    "day2": [
      {
        "time_slot": "06:00-06:30",
        "activity": "早起准备",
        "type": "prep"
      },
      {
        "time_start": "06:45",
        "time_end": "08:15",
        "entity_id": "kyo_kiyomizu",
        "entity_name": "清水寺",
        "duration_planned_min": 90,
        "notes": "开门即到，清晨人少"
      },
      {
        "time_start": "08:15",
        "time_end": "08:40",
        "type": "transit",
        "from": "kyo_kiyomizu",
        "to": "kyo_gion_district",
        "mode": "walk",
        "duration_min": 25
      },
      {
        "time_start": "09:00",
        "time_end": "11:30",
        "activity_type": "area_exploration",
        "corridor": "gion",
        "description": "祇园散步、购物"
      },
      {
        "time_start": "12:00",
        "time_end": "13:00",
        "type": "meal",
        "meal_type": "lunch",
        "placeholder": true,
        "notes": "待定，见 Step 13"
      },
      {
        "time_start": "17:30",
        "time_end": "18:30",
        "entity_id": "anchor_sunset",
        "entity_name": "清水舞台日落",
        "type": "anchor",
        "flexibility": "hard"
      },
      {
        "time_start": "19:00",
        "time_end": "20:00",
        "type": "meal",
        "meal_type": "dinner",
        "placeholder": true,
        "notes": "待定，见 Step 13"
      },
      {
        "time_start": "20:30",
        "time_end": "21:00",
        "type": "return",
        "from": "gion",
        "to": "hotel_higashiyama",
        "mode": "transit",
        "notes": "地铁或巴士"
      }
    ]
  }
}
```

此时输出的是**可执行的日程骨架**，但餐厅和一些细节还是 placeholder。

---

## 第四阶段：餐厅 + 预算 + Plan B（Step 13-15）

### Step 13：系统按"每日路线"切餐厅候选

**系统动作**：按当天的片区和活动时段切餐厅

不是一次喂全城 400 家，而是：
* Day2 上午在 higashiyama → 保留该区域午餐候选（20 家）
* Day2 下午在 gion → 保留该区域晚餐候选（30 家）

**输出**：

```json
{
  "daily_restaurant_options": {
    "day2_lunch": {
      "corridor": "higashiyama",
      "candidates": [
        {
          "id": "rest_a",
          "name": "清水豆腐料理",
          "cuisine": "tofu",
          "price_range": "2000-3000",
          "requires_reservation": false,
          "candidates_rank": 1
        },
        ...  // Top 5
      ]
    },
    "day2_dinner": {
      "corridor": "gion",
      "candidates": [...]
    }
  }
}
```

---

### Step 13.5：AI 选餐厅与备选

**AI 决策**：
* 主餐厅（考虑位置、菜系、价格、用户口味）
* 备选餐厅（预约失败时用）
* 菜系分布（不重复两天都吃同一菜式）

**规则**：预约失败直接切备选，**不回推改主骨架**

**输出**：

```json
{
  "meals": {
    "day2_lunch": {
      "restaurant": "rest_a",
      "time_window": "12:00-13:00",
      "reservation_required": false,
      "backup": "rest_b"
    },
    "day2_dinner": {...}
  }
}
```

---

### Step 14：预算核算

**累加**：
* 酒店 × 晚数
* 门票 × 人数
* 交通（城市间 + 市内）
* 餐饮 × 餐数
* 可选购物预留

**输出**：

```json
{
  "budget_summary": {
    "total_jpy": 85000,
    "by_category": {
      "hotel": 36000,
      "activities": 15000,
      "meals": 25000,
      "transport": 9000
    },
    "by_day": [
      {"day": 1, "total": 12000, "breakdown": {...}},
      ...
    ],
    "within_budget": true,
    "budget_tier_limit": 87500
  }
}
```

---

### Step 15：Plan B 准备

**准备以下替代方案**：

1. **下雨替代** — 每个户外活动对应室内替代
2. **预约失败替代** — 由 Step 13.5 的 backup 承接
3. **起晚 / 晚点缩短版** — 如果某天推迟 1-2 小时，怎么调整
4. **恶劣天气低强度版** — 如果天气太糟糕，简化整天方案

**输出**：

```json
{
  "plan_b": {
    "rainy_alternatives": [
      {
        "original_day": 2,
        "original_activity": "kyo_gion_district",
        "alternative": "goto_museum_x"
      }
    ],
    "late_start_contingency": [
      {
        "day": 2,
        "if_delayed_min": 60,
        "drop_activities": ["kyo_optional_1star"],
        "revised_schedule": [...]
      }
    ],
    "bad_weather_light_version": {...}
  }
}
```

---

### Step 16：手账本加分内容填充

**不参与主骨架，只做增强**：

* 街景插画和渲染指导
* 拍照机位和技巧
* 顺路小商店推荐
* 地区小故事 / 历史故事
* 散步时的实用提示
* 仪式感文案

**规则**：
* 不反向改主行程
* 可以没有（预算紧张时删掉）
* 历史故事需要轻量核对（避免常见谣言）

**输出**：最终手账本的装饰内容层

---

## 各步骤输出策略

| 步骤 | 输出类型 | 输出数量 | 备注 |
|------|---------|---------|------|
| Step 3 | 城市组合候选 | Top 2-3 | 用户选一个继续 |
| Step 5 | 主活动组合 | 唯一 | 给定城市方案后确定 |
| Step 7 | 住宿区域 + 酒店 | 唯一 + 1-2 备选 | 主备选 |
| Step 9 | 每日顺序 | 唯一 | 已是最优 |
| Step 12 | 每日时间线骨架 | 唯一 | 已可执行 |
| Step 13.5 | 餐厅 | 唯一 + backup | 预约失败用 backup |
| Step 16 | 手账本装饰 | 唯一 | 最终文案 |

---

## 关键数据结构定义（工程参考）

### 用户约束包
```typescript
interface UserConstraints {
  trip_window: {
    departure_date: string;  // ISO 8601
    arrival_date: string;
    total_days: number;
  };
  user_profile: {
    party_type: 'couple' | 'family' | 'solo' | 'group';
    budget_tier: 'economy' | 'standard' | 'premium';
    tags: string[];  // first_visit, photo, foodie, ...
  };
  constraints: {
    must_visit: string[];
    must_avoid: string[];
    must_stay?: string;
  };
}
```

### 每日时间线
```typescript
interface DailySchedule {
  date: string;
  day_of_week: number;
  events: Array<{
    time_start: string;  // HH:MM
    time_end: string;
    activity_type: 'main' | 'optional' | 'meal' | 'transit' | 'anchor';
    entity_id?: string;
    duration_planned_min: number;
    notes?: string;
  }>;
  remaining_slack_min: number;
}
```

### 冲突检查结果
```typescript
interface FeasibilityCheck {
  status: 'pass' | 'fail';
  violations?: Array<{
    type: 'capacity_exceeded' | 'travel_time_tight' | 'time_window_conflict';
    severity: 'low' | 'medium' | 'high';
    details: string;
  }>;
}
```

---

## 执行顺序建议

### 可并行开发
- Step 1（收集约束）
- Step 2（区域摘要）
- Step 4（缩候选池）
- Step 6（缩住宿池）
- Step 8（编制约束包）
- Step 13（缩餐厅池）

### 必须串行
- Step 3 → Step 4（选城市后才能缩池）
- Step 5 → Step 5.5（选活动后才能校验）
- Step 5 → Step 6（知道活动才能选住宿）
- Step 9 → Step 10 → Step 11（顺序排程→检查→修复）
- Step 12 → Step 13.5（时间线确定后才能填餐厅）

---

## 注意事项

### 时间窗约束
* 京都市交通局明确提示：不同公交线路运营时间和班次数不同，必须查 timetable
* 低频交通（≤3班/天）必须硬锚定
* 高频交通（≥6班/小时）可灵活处理

### 定休日处理
* 使用 Google Places 的 `regularOpeningHours`
* 如果没有 API 数据，使用人工标注或官方网站数据
* Step 5.5 必须做定休日初筛，不能等到 Step 10

### 预算精度
* 门票和交通可精确到 100 日元
* 餐厅按菜系给出价格范围，不求每家精确
* 酒店按选定的具体酒店来确定

### Plan B 优先级
* 必须有 Plan B（不能完全依赖理想场景）
* Plan B 可以比主方案的体验降低一档，但不能无法执行

---
