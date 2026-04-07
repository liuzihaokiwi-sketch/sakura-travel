# 景点精选指南

> 版本: 2.0
> 更新: 2026-04-01
> 上位文档: SELECTION_PHILOSOPHY.md
> 核心改动: 双S制(heritage_s / popular_s)，JNTO/japan-guide是主骨架

---

## 一、双S制

景点有两种"顶级"，不应混为一类:

| 类型 | 含义 | 判断来源 | 示例 |
|------|------|---------|------|
| **heritage_s** | 文化/历史/自然名片 | JNTO/japan-guide/世界遗产/国宝 | 金阁寺、姬路城、高野山、熊野古道 |
| **popular_s** | 大众热门/体验名片 | Google评论量/携程/小红书热度 | 伏见稻荷、USJ、道顿堀 |

一个景点可以同时是两种S(如伏见稻荷 = heritage_s + popular_s)。

### JNTO/japan-guide是S/A的主骨架

这两个是编辑型指南，经过专家筛选，不是算法排序。
它们的推荐等级直接映射到我们的grade:

| japan-guide等级 | 我们的grade |
|-----------------|-----------|
| Top Attraction | heritage_s 或 A |
| Recommended | A 或 B |
| More Attractions | B 或 C |

**Google评论量是补充信号，不是主骨架。** 很多文化名片评论量不过万但绝对值得去。

---

## 二、数据源

| 顺序 | 数据源 | 级别 | 得到什么 |
|------|--------|------|---------|
| 1 | japan-guide.com | P0 | 编辑推荐等级、描述 |
| 2 | JNTO | P0 | 官方推荐景点 |
| 3 | Google Maps | P0 | 评分、评论数、坐标、营业时间 |
| 4 | 携程Trip.com | P1 | 中国游客评分、门票价格(CNY) |
| 5 | TripAdvisor | P1 | 国际游客排名 |
| 6 | 小红书 | P2 | 中国游客热门+避坑 |
| 7 | 独立攻略站 | P2 | 深度体验描述 |

---

## 三、三层池执行

### 发现池

```
Step 1: japan-guide + JNTO
  - WebFetch该城市页面，提取全部推荐景点
  - 这是骨架，直接进发现池

Step 2: Google Maps
  - 按走廊搜索 tourist attraction / shrine / temple / museum / park
  - 取评分>3.5且评论>100

Step 3: 携程 + TripAdvisor
  - 该城市景点排名前30-50
  - 补充遗漏

Step 4: 小红书 + 独立站
  - "{城市}必去" "{城市}景点"
  - 记录高频+避坑
```

### 入围池

```
进入条件:
- japan-guide "Top" 或 "Recommended" -> 直接入围
- JNTO 重点推荐 -> 直接入围
- Google > 4.0 且该城市评论量前30% -> 入围
- 携程 > 4.0 且 "必去" 标签 -> 入围
- 世界遗产/国宝 -> 直接入围
- 3+个独立原创推荐 -> 入围

不入围(噪音过滤底线，非选择标准):
- Google < 3.0
- 已关闭
- 仅AI知识
```

### 终选池

```
分组: 按 city x main_type(固定景点/区域目的地/体验活动) x sub_type

样本量门槛(见MASTER_GUIDE第六章):
  >= 15: 取前10-20%
  6-14: 取best N + 编辑判断
  < 6: 仅收明确代表项，否则留空

同一决策位(corridor x sub_type)最多保留3家:
  首推 / 稳妥替代 / 机动备选

编辑判断:
  heritage_s候选:
    - 世界遗产? 国宝建筑?
    - japan-guide "Top"?
    - 不可替代性高?
    -> 即使热度不高，只要文化价值确认就可以标S

  popular_s候选:
    - 该城市该类型Google评论前10%(不用绝对阈值)
    - 携程/小红书在该城市同类目中排名靠前
    - 体验独特且大众可参与
    -> 同时满足多条则标S

  A/B/C:
    - 品类内相对位置
    - 是否值得专程去(A) vs 顺路去(B/C)
    - 某个sub_type如果没有好的就空着
```

---

## 四、季节性模型(三层语义)

### 问题根因

旧设计用单一字段 best_season 同时表达"最佳体验季节"和"能不能去"两个语义，
导致系统把"秋天去最美"理解为"只能秋天去"，造成4个测试失败。

### 系统设计: seasonality 对象

```json
"seasonality": {
  "open_seasons": "all",
  "best_season": "autumn",
  "avoid_season": null,
  "avoid_reason": null,
  "seasonal_notes": "11月红叶最美，5月藤花也值得"
}
```

三层语义，各自独立，不互相耦合:

| 字段 | 语义 | 系统用途 | 类型 |
|------|------|---------|------|
| open_seasons | 物理上能去的季节 | **硬约束，系统筛选用** | "all" 或 "spring,summer,autumn,winter" |
| best_season | 体验最佳季节 | 软推荐，排序加分 | string 或 null |
| avoid_season | 不建议去的季节 | 软警告，可覆盖 | string 或 null |
| avoid_reason | 不建议的具体原因 | 展示给用户 | string 或 null |
| seasonal_notes | 季节性补充说明 | 展示给用户 | string 或 null |

### 分类示例

| 景点 | open_seasons | best_season | avoid_season | 说明 |
|------|-------------|-------------|--------------|------|
| 姬路城 | all | spring | null | 全年开放，春天樱花最美 |
| 平等院 | all | autumn | null | 全年开放，秋天红叶+5月藤花 |
| 比叡山 | all | autumn | winter | 冬季积雪路况差(非不可去) |
| 和服体验 | all | spring | null | 全年可穿，春天出片最好 |
| 祇园祭 | summer_only | summer | null | 7月限定 |
| 吉野山樱花 | all | spring | null | 春天赏樱名所，其他季节风景也好 |
| 嵯峨野竹林 | all | null | null | 全年体验差异不大 |

### 系统筛选逻辑

```python
# 旧逻辑(有bug):
if spot.best_season != user_travel_season:
    exclude(spot)  # 错! 把"秋天最美"理解为"只能秋天去"

# 新逻辑:
if user_travel_season not in spot.seasonality.open_seasons:
    exclude(spot)  # 硬约束: 该季节确实不开放

# 排序加分(不排除):
if spot.seasonality.best_season == user_travel_season:
    score_boost(spot, +10)  # 恰好是最佳季节，加分

# 软警告(不排除，但提示):
if spot.seasonality.avoid_season == user_travel_season:
    add_warning(spot, spot.seasonality.avoid_reason)
```

### 数据修复清单(关西xfail)

| 景点 | 旧 best_season | 新 seasonality |
|------|---------------|----------------|
| 姬路城 | spring | open:all, best:spring, avoid:null |
| 和服体验 | spring | open:all, best:spring, avoid:null |
| 平等院 | autumn | open:all, best:autumn, avoid:null, notes:"5月藤花也值得" |
| 比叡山 | autumn | open:all, best:autumn, avoid:winter, reason:"积雪路况差" |

---

## 四b、景点纳入决策模型(边际成本模型)

### 问题根因

旧设计用 `trip_duration x grade` 硬编码:
- 3天: 只纳入S+A
- 5天: 纳入S+A+B
这导致走廊内顺路的B级景点(如哲学之道在银阁寺动线上)被排除。

### 系统设计: 边际成本纳入模型

**不按 duration x grade 硬编码，而是按"纳入这个景点的边际成本"决定。**

```
纳入决策 = f(grade, 边际时间成本, 走廊位置)

规则:
1. S级: 始终纳入(它是行程骨架)
2. A级: 时间允许即纳入
3. B级: 仅当边际时间成本 <= 15分钟时纳入
4. C级: 仅当边际时间成本 = 0(字面上就在路上)时纳入
```

### 边际时间成本定义

```
边际时间成本 = 为了去这个景点，行程多花的时间

= 0: 景点在走廊动线上，走过路过不需要绕路
     (如: 哲学之道在银阁寺->南禅寺步行路线上)
     (如: 蹴上铁道在南禅寺旁边，步行2分钟)

<= 15min: 需要轻微绕路但不影响整体节奏
     (如: 从主路线步行5分钟到一个神社)

> 15min: 需要专程安排
     (如: 需要坐电车去另一个区域)
```

### 数据层支持

每个景点增加字段(在corridor_definitions或景点数据中):

```json
"corridor_adjacency": {
  "primary_corridor": "philosopher_path",
  "on_main_route": true,
  "detour_minutes": 0,
  "pairs_well_with": ["ginkakuji", "nanzenji"]
}
```

系统筛选时:
```python
def should_include(spot, trip_tier, current_corridor):
    if spot.grade in ['S', 'A']:
        return True
    if spot.grade == 'B':
        detour = spot.corridor_adjacency.detour_minutes
        return detour <= 15
    if spot.grade == 'C':
        return spot.corridor_adjacency.on_main_route
    return False
```

### 对测试xfail的修复

- 哲学之道(B级): on_main_route=true, detour_minutes=0 -> 3天行程中纳入(在银阁寺动线上)
- 蹴上铁道(B级): on_main_route=false, detour_minutes=2 -> 3天行程中纳入(边际成本极低)

---

## 五、三条标签(景点版)

| 标签 | 含义 | 示例 |
|------|------|------|
| city_icon | 城市文化名片 | 金阁寺(京都)、大阪城(大阪) |
| traveler_hot | 游客必打卡 | 伏见稻荷(千本鸟居)、道顿堀 |
| local_benchmark | 本地人也推荐 | 哲学之道散步、中崎町街区 |

---

## 六、负向编辑规则(景点)

| 信号 | 处理 |
|------|------|
| 严重过度商业化(游客陷阱) | 降级或不收 |
| 需要特定背景知识才能欣赏 | 不降级但标注 "建议有XX背景再去" |
| 体验高度依赖天气/季节 | 必须在available_seasons标清 |
| 排队2小时+但体验15分钟 | 标注排队风险+建议替代时段 |
| 维护关闭中 | 标注，暂不收录 |

---

## 七、taxonomy配置修正

**测试发现的问题**: 有马温泉属于的库(hyogo)，但跨圈关联未建立。

需要在taxonomy.json中增加跨圈可达性:

```json
"cross_region_access": {
  "arima": {
    "reachable_from": ["osaka", "kobe"],
    "transit_minutes": {"osaka": 50, "kobe": 30},
    "note": "从大阪/神户均可当日往返"
  }
}
```

这不是arima属于哪个region的问题，而是"从哪里能方便到达"的问题。

---

## 八、评价维度(从真实评论提取)

| 维度 | 字段名 | 类型 |
|------|--------|------|
| 最佳时段 | best_timing | string |
| 天气敏感度 | weather_sensitivity | any/prefer_clear/rain_ruins |
| 体力要求 | physical_demand | easy/moderate/demanding |
| 拍照价值 | photo_value | low/medium/high/iconic |
| 人群密度 | crowd_pattern | string |
| 停留弹性 | duration_flexibility | fixed/flexible |
| 儿童适合度 | child_friendly | not_suitable/ok/great |
| 季节依赖 | season_dependency | any_season/specific_season |

**从Google/携程/小红书评论提取。没提到的不填。**
