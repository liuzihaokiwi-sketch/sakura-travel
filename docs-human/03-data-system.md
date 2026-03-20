# 数据体系

## 实体类型

系统管理三类核心实体，统一存储在 `entity_base` 表中（CTI 模式）：

| 实体类型 | 扩展表 | 关键字段 |
|---|---|---|
| POI（景点） | `pois` | 类别、游览时长、门票、最佳季节、拥挤度 |
| Hotel（酒店） | `hotels` | 类型（商务/旅馆/胶囊）、星级、设施、价格层级 |
| Restaurant（餐厅） | `restaurants` | 料理类型、Tabelog 评分、米其林星级、预约难度、人均价格 |

每个实体具有多语言名称（中/日/英）、地理坐标、Google Place ID、数据层级（S/A/B）。

## 数据采集来源

| 来源 | 采集方式 | 数据类型 |
|---|---|---|
| OpenStreetMap (OSM) | Overpass API | POI 基础信息 |
| Tabelog | 爬虫 | 餐厅评分/价格 |
| Google Places | API | 评分/评论数/营业时间 |
| JNTO 官方 | 爬虫 | 景点官方信息 |
| 小红书 | Playwright 爬虫 | 用户真实体验 |
| Claude AI | API 生成 | 离线模式下的实体补全 |
| 人工编辑 | 后台操作 | Editorial Boost 标注 |

## GPT 标签系统（9 维主题亲和度）

每个实体通过 GPT-4o-mini 生成 9 个维度的亲和度评分（0-100）：

```
shopping / food / culture_history / onsen_relaxation / nature_outdoors
anime_pop_culture / family_kids / nightlife_entertainment / photography_scenic
```

标签存储在 `entity_tags` 表中，支持种子 JSON 人工覆盖（`data/entity_affinity_seed_v1.json`）。

## 评分引擎

三阶段评分机制：

1. **系统基础分 (0-100)**：平台评分 × 评论数量 × 数据新鲜度 × 实体类型特有信号
2. **上下文分**：根据用户画像（party_type, budget_level, must_have_tags）动态调整
3. **编辑 Boost (-8 ~ +8)**：人工标注的权重调整，覆盖算法盲区

最终得分 = `clamp(base_score + editorial_boost, 0, 100)`

## 数据新鲜度

- 酒店报价快照 TTL: 1 天
- 航班价格快照 TTL: 1 天
- 景点开放状态 TTL: 7 天
- 天气数据 TTL: 1 天
- AI 文案缓存 TTL: 7 天

## 数据层级

| 层级 | 含义 | 标准 |
|---|---|---|
| S | 精品 | Google 评分 ≥ 4.5 + 评论 ≥ 500 + 编辑审核 |
| A | 优质 | Google 评分 ≥ 4.0 + 评论 ≥ 100 |
| B | 基础 | 有基本信息但未人工审核 |