# 数据体系

## 实体类型

| 类型 | 表 | 数据源 | 示例 |
|------|------|--------|------|
| POI（景点） | `entity_base` (type=poi) | OSM + AI 生成 | 浅草寺、新宿御苑 |
| 餐厅 | `entity_base` (type=restaurant) | Tabelog + AI 生成 | 一兰拉面、叙叙苑 |
| 酒店 | `entity_base` (type=hotel) | Hotels API + AI 生成 | 星野リゾート |

## 数据采集流程

```
POST /admin/sync/{city}
  → pipeline.py
    → 优先使用爬虫（OSM/Tabelog/Google Places）
    → 网络不通时自动降级到 Claude AI 生成
    → 写入 entity_base + entity_scores
```

## GPT 标签（9 维主题亲和度）

每个实体有 9 个维度的 0-5 评分：
`shopping / food / culture_history / onsen_relaxation / nature_outdoors / anime_pop_culture / family_kids / nightlife_entertainment / photography_scenic`

- **生成方式**：GPT-4o-mini 批量打标（`scripts/generate_tags.py`）
- **人工覆盖**：`data/seed/entity_affinity_seed_v1.json` 中的种子数据优先于 GPT
- **存储**：`entity_tags` 表，`tag_namespace=affinity`，`tag_value={theme}:{score}`

## 三层评分引擎

| 层 | 权重 | 说明 |
|----|------|------|
| Base Score | 40% | 平台评分 + 评论数 + 数据新鲜度 + 风险惩罚 |
| Context Score | 40% | 用户偏好标签 × 实体亲和度标签的加权点积 |
| Editorial Score | 20% | 人工编辑加分（-3 到 +5） |

## 数据新鲜度

- `entity_scores.updated_at` 距今超过 30 天 → 新鲜度衰减
- POI 开放时间 TTL: 7 天
- 酒店报价 TTL: 1 天
- 航班报价 TTL: 1 天

## 翻译

- 工具：DeepL Free API（`scripts/batch_translate.py`）
- 翻译范围：实体 `name_ja` → `name_zh`
- 缓存：Redis 永久缓存，key = `translate:ja:zh:{text}`