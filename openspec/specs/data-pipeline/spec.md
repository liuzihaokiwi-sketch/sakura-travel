# 数据采集管道 + 动态快照层 (Data Pipeline & Live Snapshots)

## 概述
属于三层数据架构中的 **Layer B：动态快照层**。
从第三方 API 采集高时效信息，每个快照必须有 source / fetched_at / expires_at / parse_version，确保可追溯。

## 核心原则（第一性原理）
- **静态与动态必须分离**：主档在 Catalog，快照在这里
- **每条快照必须可追溯**：source + fetched_at + expires_at
- **派生结果必须绑定快照版本**：plan_artifacts 记录用了哪些快照
- **不把高频价格存在主档里**

---

## 数据源

### 自动采集源
| 数据源 | 用途 | 阶段 |
|---|---|---|
| Google Places API | POI/酒店/餐厅基础信息 → 写入 Catalog | Phase 0 |
| Google Routes API | 路线耗时矩阵 → route_matrix_cache | Phase 1 |
| Tabelog | 日本餐厅评分/排名 → 补充 Catalog | Phase 1 |
| Booking Demand API | 酒店报价/库存 → hotel_offer_snapshots | Phase 2+ |
| JNTO Safety Tips | 安全提醒 → source_snapshots | Phase 0 |
| JMA | 天气/灾害 → source_snapshots | Phase 1 |
| MOFA | 签证/eVISA → source_snapshots | Phase 0 |

### 人工录入
| 内容 | 工具 | 阶段 |
|---|---|---|
| 实体中文名/介绍/提示 | 后台 CMS 或 CSV → entity_base | Phase 0 |
| 标签强度 | 给 GPT 的打分表 → entity_tags | Phase 0 |
| 编辑修正 | 后台 → entity_editor_notes | Phase 0 |
| 区域住宿指南 | 后台 → hotel_area_guide | Phase 1 |

### Google Places 工程规则
- 必须使用 field mask 控制成本
- 必须存 raw snapshot（source_snapshots）
- 不把 photo name 当长期主键
- 主档更新不应每次都重抓全字段

### Google Routes 工程规则
- 只在 shortlist 候选之间打矩阵，不全量算
- 优先命中缓存
- 必须绑定 time bucket

### Booking Demand API 工程规则
- 酒店主档和报价快照严格分离
- 不能直接依赖返回顺序代表"最优价格"
- 必须自己做归一化和排序

---

## 动态快照表结构

### source_snapshots（通用快照表）
| 字段 | 类型 | 说明 |
|---|---|---|
| snapshot_id | UUID | 主键 |
| source_name | VARCHAR | google_places / jnto / jma / mofa |
| source_object_type | VARCHAR | poi_opening / weather / visa_rule / safety |
| source_object_id | VARCHAR | 关联对象 ID |
| raw_payload | JSONB | 原始返回数据 |
| normalized_payload | JSONB | 归一化后的数据 |
| fetched_at | TIMESTAMP | 抓取时间 |
| expires_at | TIMESTAMP | 过期时间 |
| parse_version | VARCHAR | 解析版本号 |

### hotel_offer_snapshots（酒店报价快照头表）
| 字段 | 类型 | 说明 |
|---|---|---|
| snapshot_id | UUID | 主键 |
| trip_id | UUID | 关联行程（按需抓取时） |
| source | VARCHAR | booking / expedia / agoda |
| currency | VARCHAR | JPY / CNY |
| checkin_date | DATE | 入住日期 |
| checkout_date | DATE | 离店日期 |
| occupancy | INT | 入住人数 |
| fetched_at | TIMESTAMP | 抓取时间 |
| expires_at | TIMESTAMP | 过期时间 |
| request_hash | VARCHAR | 请求去重 hash |

### hotel_offer_lines（酒店报价快照行表）
| 字段 | 类型 | 说明 |
|---|---|---|
| offer_line_id | UUID | 主键 |
| snapshot_id | UUID | 关联头表 |
| hotel_entity_id | UUID | 关联酒店 entity_id |
| room_type | VARCHAR | 房型 |
| breakfast_included | BOOLEAN | 含早 |
| cancellation_policy | VARCHAR | 取消政策 |
| total_price | INT | 含税总价 |
| taxes_included | BOOLEAN | 是否含税 |
| availability | BOOLEAN | 是否可订 |
| score_inputs | JSONB | 用于评分的提取字段 |

### flight_offer_snapshots（航班快照，Phase 2+）
| 字段 | 类型 | 说明 |
|---|---|---|
| snapshot_id | UUID | 主键 |
| origin | VARCHAR | 出发城市 |
| destination | VARCHAR | 目的地 |
| depart_date_range | VARCHAR | 出发日期范围 |
| return_date_range | VARCHAR | 返回日期范围 |
| passenger_mix | JSONB | 乘客组合 |
| offer_list | JSONB | 航班报价列表 |
| fetched_at | TIMESTAMP | 抓取时间 |
| expires_at | TIMESTAMP | 过期时间 |

### poi_opening_snapshots（营业时间变更快照）
| 字段 | 类型 | 说明 |
|---|---|---|
| snapshot_id | UUID | 主键 |
| entity_id | UUID | 关联 POI |
| status | VARCHAR | normal / closed_temp / hours_changed |
| detail | JSONB | 变更详情 |
| source | VARCHAR | google_places / official |
| fetched_at | TIMESTAMP | 抓取时间 |
| expires_at | TIMESTAMP | 过期时间 |

### weather_snapshots（天气快照）
| 字段 | 类型 | 说明 |
|---|---|---|
| snapshot_id | UUID | 主键 |
| city | VARCHAR | 城市 |
| forecast_date | DATE | 预报日期 |
| weather_summary | JSONB | 天气摘要 |
| alerts | JSONB | 预警信息 |
| source | VARCHAR | jma |
| fetched_at | TIMESTAMP | 抓取时间 |
| expires_at | TIMESTAMP | 过期时间 |

---

## 路线矩阵缓存

### route_matrix_cache
| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 主键 |
| origin_entity_id | UUID | 起点 |
| dest_entity_id | UUID | 终点 |
| origin_geohash | VARCHAR | 起点 geohash |
| dest_geohash | VARCHAR | 终点 geohash |
| travel_mode | VARCHAR | transit / walking |
| depart_time_bucket | VARCHAR | 时段（morning/midday/evening） |
| duration_min | INT | 耗时分钟 |
| distance_m | INT | 距离米 |
| route_summary | TEXT | 路线摘要 |
| source | VARCHAR | google_routes |
| calculated_at | TIMESTAMP | 计算时间 |
| expires_at | TIMESTAMP | 过期时间 |

### 缓存键
```text
route_matrix_key = hash(origin_geohash, dest_geohash, depart_time_bucket, travel_mode)
```

---

## 采集流程

### Catalog 主档采集
```
1. 按城市+类型调用 Google Places Nearby Search（用 field mask）
2. 获取 place_id 列表
3. 批量调用 Place Details 获取详情
4. 写入 entity_base + pois/hotels/restaurants
5. 原始返回写入 source_snapshots（可追溯）
6. GPT 辅助打标签 → entity_tags
7. 人工筛选 S/A 级 → data_tier 标记
```

### 动态快照采集
```
1. 按需触发（用户提交行程）或定时触发
2. 调用对应 API
3. 原始返回写入对应 snapshot 表
4. 标记 fetched_at + expires_at
5. 过期快照不参与评分，标记 stale
```

## 刷新策略
| 数据类型 | 刷新周期 | 触发方式 |
|---|---|---|
| Catalog 主档 | 90 天 | 定时 |
| 酒店动态报价 | 7 天 | 按需+定时 |
| 营业时间快照 | 30 天 | 定时 |
| 天气快照 | 1 天 | 定时 |
| 路线矩阵缓存 | 180 天 | 定时 |
| 签证/安全 | 7 天 | 定时 |

## API 成本控制
- Google Places：field mask + 缓存已查询的 place_id
- Google Routes：只在 shortlist 之间打矩阵 + geohash 缓存
- Booking API：按需抓取，不全量扫
- 按数据分级控制：S 级全量刷新，B 级按需