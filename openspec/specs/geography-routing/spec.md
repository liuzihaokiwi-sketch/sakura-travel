# 区域与线路匹配模块 (Geography & Route Matching)

## 概述
管理日本旅行区域划分和推荐线路，是"用户画像 → 实体召回"之间的**中间决策层**。
没有这一层，系统只能硬编码城市，无法做智能区域推荐和线路匹配。

## 在系统中的位置
```
用户画像 (trip_profile)
    ↓ 匹配
区域 (regions)  ← 本 spec
    ↓ 筛选
线路 (routes)   ← 本 spec
    ↓ 圈定城市组合
候选实体召回 (entity_base 按 city_code + tags)
    ↓ 评分
candidate_score → shortlist → 编排
```

## 产品价位关系
| 价位 | 区域/线路使用方式 |
|---|---|
| 引流款（19.9~29.9） | 直接选择 P0 线路模板，不做动态匹配 |
| 利润款（69~199） | 根据画像自动匹配区域 → 筛选线路 → 动态召回实体 |
| 高客单 | 自动匹配 + 人工审核线路选择 + 支持 P2 小众区域 |

---

## 数据结构

### regions（区域表）
| 字段 | 类型 | 说明 |
|---|---|---|
| region_id | VARCHAR(10) PK | 区域 ID（R01, R02...） |
| region_name_cn | VARCHAR(100) | 中文名（东京都市圈） |
| region_name_en | VARCHAR(100) | 英文名（Tokyo Metro） |
| region_scope | TEXT | 区域范围描述 |
| core_cities | JSONB | 核心城市列表 `["tokyo"]` |
| extended_cities | JSONB | 扩展城市（日游/短途可达）`["yokohama", "kamakura"]` |
| min_days | INT | 建议最少天数 |
| max_days | INT | 建议最多天数 |
| core_tags | JSONB | 区域核心标签 `["城市","购物","美食","文化"]` |
| default_intensity | VARCHAR(20) | 默认节奏 RELAX/EASY/BALANCED/CITY_RUSH/SPRINT |
| suitable_users | JSONB | 适合用户类型描述列表 |
| first_trip_friendly | VARCHAR(1) | Y / M / N（首次去日本是否友好） |
| repeat_trip_friendly | VARCHAR(1) | Y / M / N（二刷是否友好） |
| launch_priority | VARCHAR(2) | P0 / P1 / P2 |
| highlight_cn | TEXT | 亮点一句话（用于推荐理由） |
| notes | TEXT | 补充说明 |
| is_active | BOOLEAN | 是否启用，默认 true |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### routes（线路表）
| 字段 | 类型 | 说明 |
|---|---|---|
| route_id | VARCHAR(10) PK | 线路 ID（T01, F01, KS01...） |
| region_id | VARCHAR(10) FK | 所属区域 |
| route_name_cn | VARCHAR(200) | 中文名（东京经典 5 日） |
| route_name_en | VARCHAR(200) | 英文名 |
| cities_combo | JSONB | 城市组合 `["tokyo", "hakone"]` |
| days_min | INT | 最少天数 |
| days_max | INT | 最多天数 |
| intensity | VARCHAR(20) | 节奏 RELAX/EASY/BALANCED/CITY_RUSH/SPRINT |
| vacation_mode | VARCHAR(20) | 度假模式 CITY/CLASSIC/SLOW/RESORT/NATURE/ART |
| suitable_users | JSONB | 适合用户列表 |
| first_or_repeat | VARCHAR(10) | first / repeat / both |
| core_features | TEXT | 线路核心特色描述 |
| core_tags | JSONB | 标签列表 |
| sprint_friendly | VARCHAR(1) | Y / M / N |
| launch_priority | VARCHAR(2) | P0 / P1 / P2 |
| template_data | JSONB | 行程骨架模板（每天的区域/主题分配，引流款核心数据） |
| is_active | BOOLEAN | 是否启用，默认 true |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### template_data 结构示例
```json
{
  "recommended_days": 5,
  "day_plan": [
    {
      "day_number": 1,
      "city_code": "tokyo",
      "area_focus": "新宿/涉谷",
      "morning_theme": "到达+入住",
      "afternoon_theme": "城市探索",
      "evening_theme": "夜景/购物",
      "hotel_area": "新宿"
    },
    {
      "day_number": 2,
      "city_code": "tokyo",
      "area_focus": "浅草/上野",
      "morning_theme": "寺庙/传统文化",
      "afternoon_theme": "博物馆/公园",
      "evening_theme": "下町美食",
      "hotel_area": "新宿"
    }
  ]
}
```

---

## 枚举定义

### intensity（旅行节奏）
| 值 | 含义 | 每日 POI 上限 | 每日步行上限 | 每日换乘上限 |
|---|---|---|---|---|
| RELAX | 休息度假 | 2 | 40 min | 1 |
| EASY | 轻松慢玩 | 3 | 60 min | 2 |
| BALANCED | 均衡通用 | 4 | 90 min | 3 |
| CITY_RUSH | 城市暴走 | 5 | 120 min | 4 |
| SPRINT | 短期冲刺 | 6 | 150 min | 5 |

### vacation_mode（度假模式）
| 值 | 含义 | 影响 |
|---|---|---|
| CITY | 城市体验 | 偏重购物/美食/夜生活 |
| CLASSIC | 经典观光 | 均衡分配文化/景点/美食 |
| SLOW | 慢旅行 | 单区域深度，减少换乘 |
| RESORT | 休息度假 | 温泉/酒店体验为主 |
| NATURE | 自然户外 | 偏重公园/徒步/自然景观 |
| ART | 文化艺术 | 偏重美术馆/手工艺/传统文化 |

---

## 区域匹配逻辑

### 输入
trip_profile 的关键字段：
- `trip_experience`: first_time / repeat
- `travel_days`: 总天数
- `party_type`: solo / couple / family_child / family_elder / friends
- `pace`: relaxed / balanced / intensive
- `theme_weights`: 主题偏好权重
- `destination_cities`: 用户指定城市（可能为空）

### 匹配流程

#### Step 1：硬过滤
```
candidates = regions.where(
    is_active = true
    AND min_days <= user.travel_days <= max_days + 2  (允许溢出 2 天)
    AND launch_priority IN user_allowed_priorities      (根据产品价位)
)
```
- 引流款：只匹配 P0
- 利润款：匹配 P0 + P1
- 高客单：匹配 P0 + P1 + P2

#### Step 2：适配度打分
```python
region_score = (
    0.30 * first_trip_match(user, region)     # 首次/二刷匹配
  + 0.25 * tag_overlap(user.theme_weights, region.core_tags)  # 标签重合度
  + 0.20 * party_type_match(user, region)     # 人群适配
  + 0.15 * days_fit(user.travel_days, region.min_days, region.max_days)  # 天数适合度
  + 0.10 * intensity_match(user.pace, region.default_intensity)  # 节奏匹配
)
```

#### Step 3：组合推荐
- 如果用户 `travel_days >= 7`，允许推荐 2 个区域组合（如 R01 + R03）
- 如果用户指定了 `destination_cities`，优先匹配包含这些城市的区域
- 返回 Top 3 区域（或区域组合），每个附带匹配理由

### 线路筛选
在匹配到区域后，从该区域的线路中筛选：
```
routes = region.routes.where(
    is_active = true
    AND days_min <= user.travel_days <= days_max + 1
    AND (first_or_repeat = 'both' OR first_or_repeat = user.trip_experience)
    AND intensity_compatible(route.intensity, user.pace)
)
ORDER BY tag_overlap(user, route) DESC
LIMIT 3
```

---

## 种子数据

### 来源
`data/日本_日本区域与线路_SeedData_v1.xlsx`

### 内容
- **Regions sheet**：12 个区域（R01-R12），5 个 P0，4 个 P1，3 个 P2
- **Routes sheet**：29 条线路，10 条 P0
- **Enums sheet**：intensity 和 vacation_mode 枚举定义
- **Sources sheet**：参考来源（JNTO）

### P0 区域（MVP 必做）
| ID | 名称 | 核心城市 |
|---|---|---|
| R01 | 东京都市圈 | 东京 |
| R03 | 富士箱根伊豆圈 | 箱根/河口湖/伊豆 |
| R05 | 关西经典圈 | 京都/大阪/奈良 |
| R06 | 北海道圈 | 札幌/小樽/登别/富良野 |
| R08 | 北陆深度圈 | 金泽/加贺温泉 |

### P0 线路（优先上线）
T01, T02（东京）、F01, F02（箱根/富士）、KS01, KS02, KS03（关西）、H01（北海道）、HK01, HK02（北陆金泽）

---

## 导入脚本需求
- 脚本路径：`scripts/seed_regions_routes.py`
- 读取 Excel → 解析 → 写入 regions + routes 表
- 幂等执行：按 region_id / route_id 做 upsert
- 标签字段（逗号分隔文本）→ JSONB 数组
- suitable_users（顿号分隔文本）→ JSONB 数组
- first_trip_friendly 列：Y→true, N→false, M→null（保留模糊）

---

## 与其他模块的关系

| 模块 | 关系 |
|---|---|
| user-intake | trip_profile → 区域匹配的输入 |
| catalog-entities | entity_base.city_code ∈ route.cities_combo → 候选召回 |
| scoring-engine | 匹配到的 route 确定城市范围后，评分引擎对候选排序 |
| itinerary-planner | route.template_data 提供骨架，planner 按骨架召回实体装配 |
| route_templates | 引流款直接使用 route.template_data 作为 route_template 数据源 |

---

## 实现状态

| 组件 | 状态 | 说明 |
|---|---|---|
| regions 表 ORM | ❌ 待建 | 需新建 app/db/models/geography.py |
| routes 表 ORM | ❌ 待建 | 同上 |
| 种子数据导入脚本 | ❌ 待建 | scripts/seed_regions_routes.py |
| 区域匹配逻辑 | ❌ 待建 | app/domains/ranking/region_matcher.py |
| 线路筛选逻辑 | ❌ 待建 | 同上 |
| planner 集成 | ❌ 待建 | planner.py 需读取 route.template_data 作为骨架 |

---

## 约束
- region_id / route_id 使用 Excel 中定义的短码，不用 UUID（人类可读）
- cities_combo 中的城市名必须与 entity_base.city_code 对齐（统一用英文小写）
- 引流款只使用 launch_priority = P0 的区域和线路
- 区域匹配返回结果必须包含匹配理由（可解释性）
- template_data 是骨架不是成品——后续由 planner 按骨架召回实体填充
