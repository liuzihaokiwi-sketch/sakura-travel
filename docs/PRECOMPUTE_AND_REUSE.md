# 预计算 & 复用架构

> 核心洞察：去札幌 5 天的情侣 A 和情侣 B，行程 80% 一样。
> 不该每单从零生成，而是"预制模板 + 用户微调"。

---

## 一、三层计算模型

```
┌───────────────────────────────────────────────────────┐
│  一次性预计算层（做一次，永久复用）                      │
│  → 与用户无关的客观事实                                 │
│  → 数据变了才重算                                      │
│  存储位置：DB 表 / JSON 文件                            │
└───────────────────────────────────────────────────────┘
                        │
┌───────────────────────────────────────────────────────┐
│  模板层（按城市圈×天数×人群 预制）                       │
│  → 同类用户共享的行程骨架                               │
│  → 比如"北海道5天情侣线" 做一次，卖100次                │
│  存储位置：itinerary_templates 表                       │
└───────────────────────────────────────────────────────┘
                        │
┌───────────────────────────────────────────────────────┐
│  用户定制层（每单现算，但工作量很小）                     │
│  → 根据用户特殊需求微调模板                             │
│  → 换餐厅、调酒店、去掉不适合的景点                     │
│  存储位置：itinerary_plans 表                           │
└───────────────────────────────────────────────────────┘
```

---

## 二、一次性预计算（做一次，永久用）

这些数据与用户完全无关，只跟城市和实体本身有关。

### 2.1 实体画像（已有，持续更新）

| 内容 | 频率 | 说明 |
|------|------|------|
| 实体基础数据（名称/坐标/评分） | 采集时一次 | entity_base |
| 评价维度提取 | 采集评论后一次 | entity_review_signals |
| 一句话摘要 | 提取后一次 | entity_descriptions |
| 标签 | 提取后一次 | entity_tags |
| 多源评分归一化 | 评分更新时重算 | entity_source_scores |

### 2.2 实体间关系（新增预计算）

| 内容 | 存储 | 说明 |
|------|------|------|
| 距离矩阵 | `entity_distance_matrix` | 每对实体的步行/公交/JR时间 |
| 顺路关系 | `entity_nearby` | A→B 路上经过的 C |
| 替代关系 | `entity_alternatives` | A 关门时的替代 B |
| 同区域实体 | 从 area_name 查询 | 同一区域的其他选择 |

```sql
CREATE TABLE entity_distance_cache (
    from_entity_id  UUID NOT NULL,
    to_entity_id    UUID NOT NULL,
    walk_minutes    SMALLINT,          -- 步行时间
    transit_minutes SMALLINT,          -- 公共交通时间
    drive_minutes   SMALLINT,          -- 开车时间
    transit_summary VARCHAR(200),      -- "JR快速32分钟+步行5分钟"
    computed_at     TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (from_entity_id, to_entity_id)
);
```

**这张表一次算好后，所有行程编排直接查，不用每次调 Google Directions。**

### 2.3 城市日模板片段（新概念）

一个城市某个区域的"半天"或"一天"可以预先编排好：

```sql
CREATE TABLE day_fragments (
    fragment_id     SERIAL PRIMARY KEY,
    city_code       VARCHAR(50) NOT NULL,
    corridor        VARCHAR(100),               -- 走廊/区域
    fragment_type   VARCHAR(20) NOT NULL,        -- 'half_day' / 'full_day'
    theme           VARCHAR(100),               -- "小樽港町漫步" / "定山溪温泉日归"

    -- 内容
    items           JSONB NOT NULL,             -- 排好序的活动列表
    /*
    [
        {"entity_id": "xxx", "type": "poi", "start": "09:40", "duration": 50, "notes": "沿运河走到浅草桥"},
        {"entity_id": "xxx", "type": "restaurant", "start": "11:30", "duration": 60, "notes": "招牌时令五贯盛"},
        {"entity_id": "xxx", "type": "poi", "start": "13:00", "duration": 40, "notes": "三号馆油灯咖啡厅"},
    ]
    */
    total_duration  SMALLINT,                   -- 总时长（分钟）
    estimated_cost  INTEGER,                    -- 预估费用（日元/人）

    -- 适配条件
    best_season     VARCHAR(20)[],              -- ['spring', 'summer', 'autumn']
    weather_ok      VARCHAR(20)[] DEFAULT '{any}', -- ['any'] / ['clear'] / ['rain_ok']
    suitable_for    VARCHAR(20)[] DEFAULT '{any}', -- ['couple', 'family', 'solo']
    pace            VARCHAR(20) DEFAULT 'moderate',
    energy_level    VARCHAR(20) DEFAULT 'medium',

    -- 交通
    start_station   VARCHAR(100),               -- 建议出发车站
    end_station     VARCHAR(100),               -- 结束车站
    transit_from_prev VARCHAR(200),             -- "从札幌站JR快速32分钟"

    -- 文案（预生成，不用每次调 AI）
    title_zh        VARCHAR(200),               -- "小樽 · 港町漫步半日"
    summary_zh      TEXT,                       -- 一段话描述
    practical_notes TEXT,                       -- 实用提醒合集

    -- 状态
    quality_score   NUMERIC(4,2),               -- 质量分（Opus 审核后打分）
    is_verified     BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

**关键：这些片段是预先编排好、经过质量审核的。**
- 小樽半日游 → 编排一次，审核一次，所有含小樽的行程复用
- 定山溪温泉日归 → 编排一次，所有想泡温泉的行程复用
- 札幌美食巡游 → 编排一次，所有吃货行程复用

### 2.4 每日文案和图片（预生成）

| 内容 | 何时生成 | 复用范围 |
|------|---------|---------|
| 实体描述文案 | 实体入库时 | 所有包含该实体的行程 |
| 实体照片选择 | 图片入库时 | 所有包含该实体的行程 |
| 城市特色美食图鉴页 | 做一次 | 所有该城市的行程 |
| 行前准备 checklist | 做一次 | 所有同国家的行程 |
| 退税指南/交通指南 | 做一次 | 所有同国家的行程 |
| 天气穿衣建议 | 按月份做一次 | 同月份同城市的行程 |

---

## 三、模板层（按维度组合预制）

### 3.1 行程模板维度

一个完整行程模板由这几个维度确定：

```
城市圈 × 天数 × 人群类型 × 节奏 × 季节
```

实际有效组合没那么多：

| 城市圈 | 天数 | 人群 | 节奏 | 季节 | 组合数 |
|--------|------|------|------|------|--------|
| 北海道 | 4/5/6/7 | couple/family/solo | relaxed/moderate/packed | summer/winter/spring/autumn | 4×3×3×4=144 |

但实际上很多组合可以共享骨架：
- couple + moderate 和 solo + moderate 的景点安排几乎一样，只是餐厅和酒店不同
- 5 天 moderate 和 6 天 relaxed 可能只差一天自由活动日

**所以模板不需要 144 个，大约 20-30 个骨架模板就够覆盖：**

```
北海道经典5天（couple/moderate/summer）     ← 最高频
北海道经典5天（family/moderate/summer）     ← 换酒店+去掉酒吧
北海道经典5天（couple/moderate/winter）     ← 加滑雪+雪祭
北海道深度7天（couple/relaxed/summer）      ← 加道东
北海道紧凑4天（couple/packed/any）          ← 精简版
...
```

### 3.2 模板数据结构

```sql
CREATE TABLE itinerary_templates (
    template_id     SERIAL PRIMARY KEY,
    template_code   VARCHAR(100) UNIQUE NOT NULL,  -- "hokkaido_5d_couple_moderate_summer"
    circle_id       VARCHAR(50) NOT NULL,
    duration_days   SMALLINT NOT NULL,

    -- 适配条件
    party_types     VARCHAR(20)[] NOT NULL,         -- ['couple', 'solo']
    pace            VARCHAR(20) NOT NULL,
    seasons         VARCHAR(20)[] NOT NULL,          -- ['summer', 'autumn']
    budget_levels   VARCHAR(20)[] DEFAULT '{mid}',

    -- 内容（引用 day_fragments）
    day_plan        JSONB NOT NULL,
    /*
    [
        {
            "day_number": 1,
            "type": "arrival",
            "city": "sapporo",
            "fragment_ids": [12],        -- 半天片段
            "hotel_entity_id": "xxx",
            "theme": "到达·狸小路初探"
        },
        {
            "day_number": 2,
            "type": "full",
            "city": "otaru",
            "fragment_ids": [34, 35],    -- 上午+下午两个片段
            "hotel_entity_id": "xxx",
            "theme": "小樽·港町漫步日"
        },
        ...
    ]
    */

    -- 元信息
    total_estimated_cost INTEGER,          -- 总预估费用
    highlights          VARCHAR(200)[],    -- ["函馆百万夜景", "小樽运河漫步", "定山溪温泉"]
    title_zh            VARCHAR(200),
    description_zh      TEXT,

    -- 质量
    opus_review_score   NUMERIC(4,2),      -- Opus 审核评分
    is_published        BOOLEAN DEFAULT FALSE,
    usage_count         INTEGER DEFAULT 0, -- 被使用次数
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.3 模板生成流程

```
1. 人工定义骨架（哪几天去哪个城市，什么主题）
2. 系统自动填充 day_fragments（按评分选最佳片段）
3. 系统自动填充餐厅和酒店（按评分+区域匹配）
4. GPT-4o 生成每日主题文案
5. Opus 做整体质量审核
6. 人工最终确认 → is_published = true
7. 后续所有匹配该模板条件的用户订单直接复用
```

---

## 四、用户定制层（每单的工作）

### 4.1 微调而不是重新生成

用户下单后，系统做的事：

```
1. 匹配模板
   → 根据 city_circle + days + party_type + pace + season
   → 找到最匹配的 published 模板
   → 如果完全匹配 → 直接用，AI 成本 = 0

2. 微调（只在有特殊需求时）
   → 用户说"不吃生的" → 把寿司店换成拉面店（从同区域餐厅中选替代）
   → 用户说"预算高" → 把中档酒店换成高档（从同城市 premium 酒店中选）
   → 用户说"带 3 岁小孩" → 去掉体力要求高的景点，加动物园/水族馆
   → 用户说"想去薰衣草" → 确认是否夏季，是就加富良野片段

3. 微调后的检查
   → Haiku 快速检查格式和时间连续性
   → 如果改动超过 30% → Sonnet 做逻辑检查
   → 如果几乎没改 → 跳过检查，直接用模板（已经 Opus 审过了）
```

### 4.2 AI 成本对比

| 方式 | AI 调用 | 成本 | 时间 |
|------|---------|------|------|
| 从零生成（现在） | 10+ 次 AI 调用 | ¥5-10 | 30-60 秒 |
| 模板微调（目标） | 0-2 次 AI 调用 | ¥0-2 | 1-5 秒 |

**大部分订单 AI 成本接近 0**——模板已经预审核过，只需要简单替换。

### 4.3 什么时候需要从零生成

极少数情况无法用模板：
- 用户要求完全自定义路线（"我要第一天去函馆第二天去知床"）
- 用户的特殊需求太多导致模板改了 50% 以上
- 没有匹配的模板（新城市圈刚上线还没做模板）

这些走现有的 generate_trip 全链路。

---

## 五、存储复用的完整行程

### 5.1 已生成行程的复用

```sql
-- 每个成功生成的行程标记为可复用候选
ALTER TABLE itinerary_plans ADD COLUMN IF NOT EXISTS
    reuse_fingerprint VARCHAR(200);  -- "hokkaido_5d_couple_mid_moderate_summer_v1"

ALTER TABLE itinerary_plans ADD COLUMN IF NOT EXISTS
    reuse_count INTEGER DEFAULT 0;

ALTER TABLE itinerary_plans ADD COLUMN IF NOT EXISTS
    opus_quality_score NUMERIC(4,2);
```

当一个行程被 Opus 审核为高质量（>85分）时，它自动成为该 fingerprint 的"标准模板"。后续同类用户直接复用。

### 5.2 片段级复用

不只是整个行程可以复用，**每一天、每半天都可以独立复用**：

```
"小樽半日游" 这个片段：
  → 北海道5天行程的 Day 2 上午用到了
  → 北海道7天行程的 Day 3 全天用到了
  → 北海道4天紧凑行程的 Day 2 下午用到了
```

片段的文案、图片、实用提示都只生成一次。

### 5.3 复用率预估

```
北海道圈：
  → 大约 20 个模板覆盖 90% 用户
  → 每个模板由 8-15 个 day_fragments 组成
  → 总共大约 40-50 个独立 day_fragments
  → 片段做好后，新模板只是重新组合

广府圈：类似，20 个模板 + 40 个片段
关西圈：类似

总计：60 个模板 + 150 个片段 = 覆盖 90% 订单
```

---

## 六、哪些步骤需要什么时候计算

| 步骤 | 何时计算 | 频率 | AI 模型 |
|------|---------|------|---------|
| 实体数据采集 | 系统初始化/每周刷新 | 一次 | 无 |
| 评论维度提取 | 实体入库后 | 一次 | Sonnet |
| 一句话摘要 | 实体入库后 | 一次 | Sonnet |
| 标签生成 | 实体入库后 | 一次 | Haiku |
| 实体间距离 | 实体入库后 | 一次 | 无（API） |
| 日文→中文翻译 | 实体入库后 | 一次 | GPT-4o |
| day_fragment 编排 | 手动触发 | 一次 | Sonnet + 人工 |
| day_fragment 文案 | 片段确认后 | 一次 | GPT-4o |
| day_fragment 审核 | 文案后 | 一次 | Opus |
| 行程模板组装 | 手动触发 | 一次 | Sonnet + 人工 |
| 模板整体审核 | 模板完成后 | 一次 | Opus |
| 城市美食图鉴页 | 每城市一次 | 一次 | GPT-4o |
| 行前指南页 | 每国一次 | 一次 | 无（模板） |
| **用户匹配模板** | **每单** | 每单 | **无（规则匹配）** |
| **微调替换** | **每单（如需）** | 每单 | **Haiku** |
| **微调后检查** | **每单（如需）** | 每单 | **Haiku/Sonnet** |
| PDF 渲染 | 每单 | 每单 | 无（代码） |

**结论：每单的 AI 成本从 ¥5-10 降到 ¥0-2。**
