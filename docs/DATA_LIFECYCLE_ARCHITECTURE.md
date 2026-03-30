# 数据全生命周期架构

> 从第一性原理出发：用户拿到手账本那一刻，他需要什么？
> 然后从终点倒推，每一步需要什么数据，数据从哪来，怎么变成最终的手账本内容。

---

## 一、终点倒推：用户看到的是什么

用户拿到的是一本纸质手账本。翻开来，每一页都是一个"时间块"——

```
┌─────────────────────────────────────────────────┐
│  Day 2 · 5月11日（周一）                         │
│  札幌 → 小樽 · 港町漫步日                        │
│                                                 │
│  ☀ 天气预报：晴 12-18°C                         │
│                                                 │
│  09:00  🚃 札幌 → 小樽（JR 快速，32分钟，¥770） │
│                                                 │
│  09:40  小樽运河散步                             │
│         ▸ 沿运河走 15 分钟到浅草桥拍经典角度      │
│         ▸ 早上光线最好，游客少                    │
│         [照片：运河+仓库群的经典构图]              │
│                                                 │
│  10:30  小樽音乐盒堂 ♪                           │
│         ▸ 二楼可以定制刻字音乐盒（约¥3000）       │
│         ▸ 推荐预留 30 分钟                        │
│                                                 │
│  11:30  🍣 政寿司（本店）                         │
│         ▸ Tabelog 3.65 · 小樽最老的寿司店         │
│         ▸ 招牌：时令五贯盛（¥2,200）              │
│         ▸ 💡 周一定休，请确认营业                  │
│         ▸ 只收现金                                │
│                                                 │
│  13:00  北一硝子（玻璃工艺品）                    │
│         ▸ 三号馆的油灯咖啡厅值得坐一坐            │
│         ▸ 顺路买手信，预算 ¥1000-3000             │
│                                                 │
│  14:30  LeTAO 本店                               │
│         ▸ 二楼可堂食双层芝士蛋糕（¥800）          │
│         ▸ 买伴手礼排队约 10 分钟                  │
│                                                 │
│  15:30  🚃 返回札幌（JR 快速）                    │
│                                                 │
│  💰 今日预算：约 ¥8,500/人                       │
│  🏨 住宿：JR Inn 札幌站南口（check-in 15:00）    │
│                                                 │
│  📝 贴纸区：[    ] [    ] [    ]                 │
└─────────────────────────────────────────────────┘
```

**从这一页反推，需要哪些数据：**

| 展示内容 | 需要的数据 | 数据来源 |
|----------|-----------|---------|
| 日期+星期 | 用户出发日期 | 用户表单 |
| 城市间交通 | 起止站、车次、时间、票价 | Google Maps Directions / 乘换案内 |
| 天气预报 | 历史同期天气 | weather API / 气象厅数据 |
| 景点名+描述 | name_zh, 一句话描述 | 攻略网站 + 编辑 |
| 实用提示 | practical_tip | 攻略评论提取 |
| 最佳体验方式 | best_experience | 攻略评论提取 |
| 照片 | entity_media | Google Places Photo / 手动收集 |
| 餐厅名+评分 | name, tabelog_score | Tabelog |
| 招牌菜+价格 | signature_dish, price | Tabelog 评论提取 |
| 注意事项 | heads_up (定休日/现金) | Tabelog/Google 营业信息 |
| 特色店推荐理由 | why_go | 攻略网站 |
| 顺路手信建议 | 附近 specialty_shop | Google Places + 攻略 |
| 今日预算 | 各项费用累加 | 门票+餐费+交通+购物 |
| 酒店信息 | name, check_in_time | Jalan / Booking / Google |
| 贴纸区 | 空白 | 产品设计 |

---

## 二、数据的七个阶段

```
发现 → 采集 → 清洗 → 整合 → 加工 → 编排 → 渲染
```

### 阶段 1：发现（Discovery）

**目标**：知道一个城市有哪些值得去的地方。

**输入**：城市代码
**输出**：候选实体名单（还不是数据，只是"名字+来源"）

**做什么**：
- 扫描攻略网站的城市页面（Japan Guide 的 Sapporo 页、乐吃购的北海道页）
- 提取所有被提及的地点名称
- 记录每个名字在多少个攻略源中出现过（被提及次数 = 初始重要度信号）
- 结果存入 `discovery_candidates` 表

**关键指标**：
- 多源交叉验证：一个地点被 3+ 个独立攻略源提及 → 大概率值得去
- 单源独有的地点 → 可能是小众好去处，也可能不值得，标记待验证

**数据结构**：
```sql
CREATE TABLE discovery_candidates (
    id              SERIAL PRIMARY KEY,
    name_original   VARCHAR(200) NOT NULL,     -- 原文名称
    name_normalized VARCHAR(200),              -- 规范化后的名称
    city_code       VARCHAR(50) NOT NULL,
    entity_type     VARCHAR(20),               -- poi/restaurant/hotel/unknown
    sub_category    VARCHAR(50),               -- 菜系/景点类型

    -- 来源追踪
    source_count    SMALLINT DEFAULT 1,         -- 被多少个源提及
    sources         JSONB NOT NULL,             -- [{"source": "japan_guide", "url": "...", "context": "推荐3星景点"}]
    first_seen_at   TIMESTAMPTZ DEFAULT NOW(),

    -- 状态
    status          VARCHAR(20) DEFAULT 'new',  -- new/enriching/enriched/rejected
    entity_id       UUID,                       -- 关联到 entity_base（enriched 后）

    UNIQUE(name_normalized, city_code, entity_type)
);
```

### 阶段 2：采集（Collection）

**目标**：把候选名单变成有坐标、有评分、有详情的结构化数据。

**输入**：discovery_candidates 中 status='new' 的记录
**输出**：entity_base + 子表的完整记录

**做什么（按优先级）**：

```
第一步：基础设施数据（必须有）
  → Google Places API：按名字搜索，拿到 place_id、坐标、评分、营业时间
  → 没有坐标的实体无法用于路线编排，必须先拿到

第二步：权威评分（核心价值）
  → Tabelog：按名字或 place_id 关联，拿到 tabelog_score
  → Japan Guide：景点评级（1-3星）
  → Jalan/携程：酒店评分和价格

第三步：详细信息（丰富度）
  → 攻略网站原文：景点描述、餐厅推荐理由
  → Google Places 详情：电话、网站、营业时间详情
  → 照片：Google Places Photo API / 攻略网站图片
```

**速率控制**：
- 不是所有候选都要立刻采集完
- 按 source_count 排序——被多次提及的优先采集
- 每个数据源有独立的速率限制
- 采集失败的标记后跳过，不阻塞其他

**数据来源优先级**（同一字段多源时取哪个）：
```
坐标      → Google Places（精度最高）
营业时间  → Google Places（最实时）
评分      → 权威源优先（Tabelog > Google > 攻略网站描述推断）
名称      → 权威源原文（Tabelog 的日文名、大众点评的中文名）
描述      → 攻略网站原文（不是 AI 编的）
照片      → 多源收集，人工选最好的
价格      → Tabelog/大众点评（用户真实消费数据）
```

### 阶段 3：清洗（Cleaning）

**目标**：确保每条数据准确、不重复、不过时。

**做什么**：

```
3a. 去重合并
  → 同一个地点可能从 Japan Guide、Tabelog、Google 各拉了一条
  → 用 dedup engine（名称规范化 + 坐标 500m + Levenshtein）识别
  → 合并为一条 entity_base 记录，保留各源的独立评分（entity_source_scores）

3b. 异常检测
  → 坐标在海里 / 在城市 bbox 外 → 标记 suspicious
  → 评分异常（Tabelog 5.0 / Google 1.0）→ 标记 suspicious
  → 名称疑似非旅游实体（XX医院、XX加油站）→ 标记 rejected
  → 营业状态为"永久关闭" → 标记 rejected

3c. 时效性检查
  → 评分数据超过 3 个月 → 标记需刷新
  → 营业时间超过 1 个月 → 标记需刷新
  → 景点描述超过 6 个月 → 可接受（景点变化慢）

3d. 人工审核
  → trust_status = suspicious 的实体 → 管理后台人工审核
  → 高优先级（被选入行程的）→ 优先审核
  → 低优先级（候选池中的）→ 慢慢审核
```

### 阶段 4：整合（Integration）

**目标**：多源数据合并为单一实体画像，包含所有维度信息。

**做什么**：

```
4a. 多源评分归一化
  → Tabelog 3.0-5.0 → 归一化到 0-100（3.0=40, 3.5=60, 4.0=80, 4.5=95）
  → Google  1.0-5.0 → 归一化到 0-100（3.0=30, 4.0=60, 4.5=80, 5.0=95）
  → Japan Guide 1-3星 → 1星=50, 2星=75, 3星=95
  → 存入 entity_source_scores 表

4b. 综合评分计算
  → 加权平均：权威源权重高，大众源权重低
  → 日本餐厅：Tabelog × 0.5 + Google × 0.2 + 攻略提及度 × 0.3
  → 日本景点：Japan Guide × 0.4 + Google × 0.2 + 攻略提及度 × 0.4
  → 中国餐厅：大众点评 × 0.5 + 攻略提及度 × 0.3 + Google × 0.2

4c. 评价维度提取
  → 输入：该实体在各平台的评论原文（top 50 条）
  → 处理：AI 读评论，按维度提取（queue_risk, payment_method 等）
  → 输出：dimension_scores (JSONB) + 一句话摘要
  → 过滤规则：
    - 跳过少于 5 字的评论
    - 跳过纯表情/纯星级的评论
    - 负面评价需 3+ 人提到才采信
    - 正面评价需有具体细节才采信

4d. 标签生成
  → 从评论维度自动推断标签：
    queue_risk=high → tag: long_queue
    payment_method=cash_only → tag: cash_only
    child_friendly=great → tag: family_friendly
  → 从攻略原文提取标签：
    "雨天也能玩" → tag: rainy_day_ok
    "拍照出片" → tag: photo_spot
    "当地人都去" → tag: local_favorite
  → 标签分类：
    audience: family_friendly, couple, solo, senior, group
    practical: cash_only, reservation_required, long_queue, english_ok
    experience: photo_spot, rainy_day_ok, local_favorite, seasonal
    dietary: vegetarian_ok, halal, no_raw_fish_alternative
```

### 阶段 5：加工（Processing）

**目标**：把整合后的实体数据变成可以被行程编排引擎消费的输入。

**做什么**：

```
5a. 活动簇绑定
  → 每条活动线路（如"小樽港町漫步线"）需要绑定具体实体
  → 绑定逻辑：
    - 从该线路的城市 + 走廊 + 主题筛选候选实体
    - 按综合评分排序
    - anchor_poi 取评分最高的 2-3 个景点
    - meal_destination 取该区域评分最高的 2-3 个餐厅
    - hotel_anchor 取该区域各档位各 1 个酒店
  → 不是 AI 推测名字然后去找，而是从已有真实数据中选

5b. 实体间关系计算
  → 距离矩阵：每对实体之间的步行/交通时间
  → 顺路关系：A → B 路上会经过 C（用于"顺路推荐"）
  → 替代关系：A 关门了可以改去 B（同类型同区域）
  → 存入 route_matrix_cache 或实时计算

5c. 行程适配性预计算
  → 每个实体标记适合的时间段（早上/下午/晚上/全天）
  → 每个实体标记适合的天气条件
  → 每个实体标记适合的人群类型
  → 基于标签 + 维度评分自动推断，人工可覆盖

5d. 用户-实体匹配
  → 输入：用户画像（party_type, interests, budget, pace 等）
         实体画像（维度评分 + 标签 + 一句话摘要）
  → 处理：
    第一层：标签硬过滤（不吃生的 → 排除 sushi）
    第二层：评分排序（综合分高的排前面）
    第三层：AI 个性化匹配（把 top 20 候选 + 用户画像发给 AI）
  → AI 返回：match_score + match_reason + booking_note
  → 输出：该用户的个性化排序候选池
```

### 阶段 6：编排（Orchestration）

**目标**：把候选实体按时间线编排成一个完整的多日行程。

**做什么**：

```
6a. 骨架构建（route_skeleton_builder）
  → 输入：天数、城市列表、用户 pace、已选活动簇
  → 输出：每天的框架（城市、强度、主题、酒店基地）

6b. 主活动填充（major_activity_ranker）
  → 从匹配后的候选池中选 top N 个主活动
  → 按天分配，考虑地理距离和节奏感

6c. 次要活动填充（secondary_filler）
  → 填充"顺路可以去"的景点和店铺
  → 考虑时间余量和体力消耗

6d. 餐食填充（meal_filler）
  → 每天 2-3 餐分配餐厅
  → 考虑位置（在当天活动区域内）、菜系多样性、价格匹配
  → 早餐可以在酒店或附近

6e. 交通填充
  → 每个地点间的交通方式和时间
  → JR/地铁/巴士/步行/出租车
  → 需要交通 API 或预计算的距离矩阵

6f. 酒店分配
  → 按酒店策略（单base/多base）分配每晚住宿
  → 考虑 check-in/check-out 时间约束

6g. 预算计算
  → 累加：门票 + 餐费 + 交通 + 住宿 + 购物预估
  → 对照用户预算级别，超预算时调整

6h. Plan B 准备
  → 每个户外活动准备一个雨天替代方案
  → 每个需预约的餐厅准备一个 walk-in 替代
  → 核心景点关门时的替代路线
```

### 阶段 7：渲染（Rendering）

**目标**：把编排好的行程变成用户实际拿到的手账本内容。

**做什么**：

```
7a. 文案生成
  → 每个活动的一句话描述：从攻略原文或 AI 从评论总结
  → 实用提示：从 practical_tip 字段
  → 不用 AI 从零写，用真实数据拼接

7b. 图片选择
  → 每页 1-2 张高质量图片
  → 优先：编辑精选 > Google Places Photo > 攻略网站
  → 版权检查：Google Photos 需标注 attribution

7c. 地图/路线图
  → 每天一张简化路线图
  → 标注关键交通换乘点

7d. 信息卡片
  → 每个实体一张小卡片：名字、地址、营业时间、电话
  → 生成 QR code 链接到 Google Maps

7e. 贴纸设计
  → 每个景点/城市一张贴纸
  → 用户自己贴到手账本上

7f. 加分展示项
  → 当地特色菜系介绍页（"北海道必吃 10 种美食"）
  → 实用日语/粤语小卡片（"すみません"/"唔该"）
  → 紧急联系方式页（大使馆、报警、急救）
  → 行前准备 checklist
  → 预算追踪表（空白，用户自己填）
  → 天气穿衣建议（按月份）
  → JR Pass 使用指南（如果适用）
  → 退税流程说明
  → Wi-Fi/SIM 卡建议
  → 城市特色美食图鉴（带图）
```

---

## 三、数据实体之间的关系图

```
discovery_candidates
    │ （发现阶段：名字 + 来源）
    ▼
entity_base ◄──── entity_source_scores（多源评分）
    │              entity_descriptions（一句话摘要）
    │              entity_review_signals（维度评分）
    │              entity_tags（标签）
    │              entity_media（图片）
    │              entity_operating_facts（营业事实）
    │
    ├── pois（景点子表）
    ├── restaurants（餐厅子表）
    ├── hotels（酒店子表）
    │
    ▼
circle_entity_roles ◄──── activity_clusters
    │ （哪个实体在哪条线路中扮演什么角色）
    │
    ▼
itinerary_plan
    ├── itinerary_days
    │       ├── itinerary_items（每个时间块）
    │       │       └── entity_id → entity_base
    │       └── hotel_entity_id → entity_base
    │
    ▼
page_view_model → PDF / 手账本内容
```

---

## 四、数据采集应该收集的完整字段清单

### 不管从哪个源，最终要收集到的字段：

**基础信息（所有实体）**：
- 名称：name_zh, name_ja, name_en（至少有一个）
- 坐标：lat, lng（必须有，否则无法编排路线）
- 地址：address_ja 或 address_zh
- 城市：city_code
- 区域：area_name（用于走廊匹配和"同区域"判断）
- 最近车站：nearest_station（日本很重要）
- 营业时间：opening_hours_json
- 电话：phone（手账本上要印）
- 网站/预约链接：website_url
- 照片：至少 1 张高质量图
- 数据来源：source + source_url

**评分信息**：
- 各平台原始评分：tabelog_score, google_rating 等
- 各平台评论数：review_count
- 综合归一化评分：normalized_score (0-100)

**评价维度**（阶段 4 生成）：
- 餐厅：signature_dish_clarity, queue_risk, reservation_difficulty, language_friendliness, payment_method, value_perception
- 景点：best_timing, weather_sensitivity, physical_demand, photo_value, crowd_pattern, duration_flexibility, child_friendly, season_dependency
- 酒店：location_convenience, room_condition, bath_quality, breakfast_quality, soundproofing, value_perception, best_for

**一句话摘要**（阶段 4 生成）：
- why_go / why_stay — 推荐理由
- practical_tip — 实用提醒
- skip_if — 如果不去的替代建议
- best_experience — 最佳体验方式（景点）
- heads_up — 注意事项（酒店）

**标签**（阶段 4 生成）：
- audience 类：family_friendly, couple, solo, senior
- practical 类：cash_only, reservation_required, english_ok
- experience 类：photo_spot, rainy_day_ok, local_favorite
- seasonal 类：cherry_blossom, autumn_leaves, snow_festival

**价格信息**：
- 餐厅：budget_lunch_jpy, budget_dinner_jpy
- 景点：admission_fee_jpy, admission_free
- 酒店：price_per_night_jpy, price_tier

**时间信息**：
- typical_duration_min — 建议停留时长
- best_time_window — 最佳时段
- reservation_advance_days — 提前预约天数

### 每个字段的理想数据源

| 字段 | 最佳数据源 | 备选 |
|------|-----------|------|
| 坐标 | Google Places API | 高德 API（中国） |
| 营业时间 | Google Places API | 各平台详情页 |
| 餐厅评分 | Tabelog（日本）/ 大众点评（中国）/ OpenRice（香港） | Google Rating |
| 景点评级 | Japan Guide / 官方旅游网站 | TripAdvisor / 攻略提及度 |
| 酒店评分+价格 | Jalan（日本）/ 携程（中国） | Booking / Google |
| 餐厅招牌菜 | Tabelog 评论 / 攻略网站 | Google 评论 |
| 实用提醒 | 攻略网站原文 / 评论提取 | — |
| 照片 | Google Places Photo / 攻略网站 / 手动收集 | — |
| 交通信息 | Google Directions API / 乗換案内 | — |
| 天气 | 气象厅历史数据 | weather API |

---

## 五、城市特色菜系数据

每个城市的特色菜系决定了餐厅采集的重点方向。

### 数据结构

```sql
-- 加到 city_circles 表的 JSONB 字段
ALTER TABLE city_circles ADD COLUMN IF NOT EXISTS
    local_specialties JSONB DEFAULT '[]';

-- 或者独立表（更灵活，支持按城市维护）
CREATE TABLE city_food_specialties (
    id          SERIAL PRIMARY KEY,
    city_code   VARCHAR(50) NOT NULL,
    cuisine     VARCHAR(50) NOT NULL,         -- 菜系代码
    cuisine_zh  VARCHAR(100) NOT NULL,        -- 中文名
    importance  VARCHAR(10) DEFAULT 'normal', -- 'signature'（城市名片）/ 'popular'（热门）/ 'normal'
    description VARCHAR(500),                 -- "札幌味噌拉面是北海道三大拉面之一"
    search_keywords VARCHAR(500)[],           -- 采集时用的搜索关键词
    target_count INTEGER DEFAULT 10,          -- 这个菜系要拉多少家
    notes       TEXT,
    UNIQUE(city_code, cuisine)
);
```

### 数据来源

城市特色菜系不应该凭记忆列——应该从攻略网站的"XX市必吃美食"类文章中提取，然后人工确认。

采集流程：
1. 爬取 Japan Guide / 乐吃购 / GOOD LUCK TRIP 的城市美食页
2. AI 提取提到的菜系名称和频次
3. 按频次排序，前 3-5 个标记为 signature
4. 人工审核确认
5. 存入 city_food_specialties 表
6. 后续采集餐厅时，signature 菜系的 target_count 设最高

---

## 六、系统边界 & 不做什么

### 明确不做的事

1. **不做实时数据** — 手账本是出发前印好的，不需要实时更新。数据新鲜度按周/月维护即可
2. **不做 UGC** — 不让用户上传评价。我们是内容生产者，不是平台
3. **不做全品类覆盖** — 不是大众点评。只收"游客值得去的地方"，一个城市 200-350 个实体就够
4. **不做价格比较** — 不是 booking.com。酒店给参考价和档位就行
5. **不自己生产内容** — 所有文案从真实攻略/评论提取，AI 只做搬运工不做创作者

### 可以慢慢做的事

1. 数据源扩展 — 注册中心设计好，后续接新源只需要写爬虫 + 插一条配置
2. 评论维度提取 — 需要评论原文，慢慢拿慢慢处理
3. 照片收集 — Google Photo API + 手动，每天处理一点
4. 正规 API 合作 — 有机会了再接入，架构已经预留

### 必须现在做好的事

1. **entity_base 数据准确** — 坐标对、名字对、营业状态对
2. **去重不重复** — dedup engine 保证同一个地点只有一条记录
3. **trust_status 标记清晰** — 哪些是真实数据、哪些待验证
4. **数据源可追溯** — 每条数据知道从哪来的（entity_field_provenance）
5. **管理后台可审核** — 你能看到数据状态并操作
