# 16 步行程规划管线

> 版本: 1.0
> 基于: ITINERARY_PLANNING_FINAL_WORKFLOW v4 + TASK_ALLOCATION_16STEPS
> 权威代码: `app/domains/planning_v2/orchestrator.py`
> Feature flag: `USE_PLANNING_V2=true`

---

## 设计原则

1. **系统缩圈 + AI 判断** -- 系统做资格筛选和可行性检查，AI 做取舍和排序
2. **硬规则优先** -- 营业时间、定休日、交通时刻表由系统检查，不让 AI 猜
3. **容错链清晰** -- 冲突发生时有确定性处理顺序，不让系统和 AI 互相甩锅
4. **每日时间线独立成层** -- 时间线有专门的排程和检查层
5. **候选 vs 唯一的显式分工** -- 宏观决策输出候选，排程决策输出唯一

---

## 管线总览

```
阶段一: 收集约束 + 宏观方案 (Step 1-4)
阶段二: 锁主活动 + 住宿 (Step 5-7.5)
阶段三: 每日时间线排程 (Step 8-12)
阶段四: 餐厅 + 预算 + Plan B (Step 13-16)
```

| Step | 名称 | 执行方 | 模型 | 输出 |
|------|------|--------|------|------|
| 1 | resolve_user_constraints | 系统(DB) | -- | UserConstraints |
| 2 | build_region_summary | 系统(DB) | -- | RegionSummary |
| 3 | plan_city_combination | AI | Opus | Top 2-3 城市组合候选 |
| 4 | build_poi_pool | 系统(DB) | -- | 缩减后 POI 池 (50-100) |
| 5 | plan_daily_activities | AI | Opus | 每日主活动+走廊+可插拔模块 |
| 5.5 | validate_and_substitute | AI | Sonnet | 定休日/冲突初筛 |
| 6 | build_hotel_pool | 系统(DB) | -- | 住宿区域+酒店候选 |
| 7 | select_hotels | AI | Sonnet | 唯一酒店方案+备选 |
| 7.5 | check_commute_feasibility | 系统(API) | -- | 通勤矩阵 |
| 8 | build_daily_constraints_list | 系统(DB+astral) | -- | 每日约束包 |
| 9 | plan_daily_sequences | AI | Opus | 每日最优顺序+余量 |
| 10 | check_feasibility | 系统(纯Python) | -- | 红黄绿灯可行性检查 |
| 11 | resolve_conflicts | 系统+AI | Opus | 冲突处理链(4级) |
| 12 | build_timeline | AI | Sonnet | 精确到分钟的时间线骨架 |
| 13 | build_restaurant_pool | 系统(DB) | -- | 按当日走廊切餐厅候选 |
| 13.5 | select_meals | AI | Sonnet | 餐厅选择+备选 |
| 14 | estimate_budget | 系统(纯Python) | -- | 预算累加 |
| 15 | build_plan_b | AI | Sonnet | 下雨/迟到/恶劣天气替代方案 |
| 16 | generate_handbook_content | AI | Sonnet | 手账本装饰内容(非阻塞) |

---

## 阶段一: 收集约束 + 宏观方案

### Step 1: 收集用户约束
- 纯数据映射，无AI
- 从 TripProfile 提取日期、预算、人群、画像标签、锁定项、禁忌

### Step 2: 区域级摘要
- SQL聚合，按 entity_type/grade/city 统计
- 输出各城市风格、S/A/B数量、基地适配度、季节亮点

### Step 3: AI城市组合 (Opus, 深度决策)
- 输入: 用户约束 + 区域摘要 + 季节数据
- 输出: Top 2-3 城市组合候选，含每天主题和强度建议
- token: ~2-3K input, ~1-2K output

### Step 4: 系统缩候选池 (PoolConfig驱动)
- 按选定城市 + grade过滤 + 季节相关性 + 用户禁忌
- 从 400+ 缩到 50-100 个

---

## 阶段二: 锁主活动 + 住宿

### Step 5: AI选主活动 (Opus, 深度决策)
- 每天的主活动(S/A级) + 锚点(演出/日落) + 主走廊
- 输出可插拔模块池(B/C级)和优先丢弃顺序

### Step 5.5: 初筛校验 (Sonnet)
- 5种冲突检测: 定休日、开放时间过短、交通班次冲突、季节限制、预约冲突
- 失败则标记"改期或换备选"

### Step 6: 系统缩住宿池
- 两阶段: Haversine粗筛(按主活动密度找住宿区) + 通勤精排
- 每区域 Top 3-5 候选

### Step 7: AI选酒店 (Sonnet)
- 唯一方案 + 1-2 备选
- 考虑 experience.grade、access_friction、meals_included

### Step 7.5: 通勤可行性检查
- Google Routes API `computeRouteMatrix` (上限100 elements)
- 黄灯>30min, 红灯>45min, 红灯过多回 Step 7 调整

---

## 阶段三: 每日时间线排程

### Step 8: 系统编制每日约束包
- sunrise/sunset(astral)、定休日、低频交通时刻、锚点时间
- 计算每天有效游玩时长

### Step 9: AI排每日顺序 (Opus, 深度决策)
- 平衡时间窗满足 + 地理最优
- 必须输出: daily_sequence + remaining_slack_minutes + insertion_slots + drop_order

### Step 10: 系统可行性检查
- 时间窗冲突 / 交通时间 / 容量(light<80%, medium<85%, heavy<90%) / 动线折返
- buffer块不参与检查

### Step 11: 冲突处理链 (4级递进)
1. 系统自动删可插拔模块(按drop_order)
2. 系统压缩非核心停留时间
3. 系统降强度(heavy->medium)
4. 回退AI(给明确反馈，不是让AI猜)

### Step 12: AI输出时间线骨架 (Sonnet)
- 精确到分钟: 活动+交通+餐占位+回酒店
- 此时餐厅仍是 placeholder

---

## 阶段四: 餐厅 + 预算 + Plan B

### Step 13: 系统切餐厅候选
- 按当日走廊+时段切出候选(不喂全城400家)
- 校验营业时段是否匹配用餐窗口
- 考虑 hotel breakfast/dinner_included 跳过已含餐

### Step 13.5: AI选餐厅 (Sonnet)
- 主餐厅 + 备选(预约失败切备选，不改主骨架)
- 控制菜系不重复
- 输出 {meal_selections: [{day, breakfast, lunch, dinner}]}

### Step 14: 预算核算 (纯Python)
- 累加: 酒店x晚数 + 门票x人数 + 交通 + 餐饮
- Step 13.5 输出格式必须被 Step 14 理解

### Step 15: Plan B (Sonnet)
- 下雨替代(户外->室内)
- 预约失败替代(已由13.5的backup承接)
- 晚起缩短版
- 恶劣天气低强度版

### Step 16: 手账本内容 (Sonnet, 非阻塞)
- 街景指导/拍照机位/顺路小店/地区故事/仪式感文案
- 失败不阻塞主管线

---

## 关键数据契约

上下游字段必须对齐，已知关键数据流:
- Step 7 `meals_included` -> Step 8 `hotel_breakfast/dinner_included` -> Step 13 跳过已含餐
- Step 13.5 输出 `{meal_selections}` -> Step 14 必须理解此格式
- CandidatePool.city_code -> Step 5 按城市分组(不用tag匹配)

---

## 并行开发指引

可并行(纯系统步骤，相互独立):
- Step 1, 2, 4, 6, 8, 13

必须串行:
- Step 3 -> Step 4 (选城市后才能缩池)
- Step 5 -> Step 5.5 -> Step 6 (选活动->校验->选住宿)
- Step 9 -> Step 10 -> Step 11 (排程->检查->修复)
- Step 12 -> Step 13.5 (时间线确定后才能填餐厅)

---

## 代码入口

| 文件 | 用途 |
|------|------|
| `app/domains/planning_v2/orchestrator.py` | 16步编排器 |
| `app/workers/jobs/generate_trip.py` | 主入口，含 USE_PLANNING_V2 flag |
| `app/domains/planning_v2/step*.py` | 各步骤实现 |
| `app/domains/planning_v2/models.py` | 数据模型定义 |
