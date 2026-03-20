# 行程串联模块 (Itinerary Planner)

## 概述
将景点、酒店、餐饮组合成可执行路线。只负责组合、排序、装配、修正，不直接拥有底层实体资料。

## 产品价位关系
| 价位 | 串联方式 |
|---|---|
| 引流款（19.9~29.9） | 预制区域模板，AI 辅助润色文案 |
| 利润款（69~199） | 基于用户画像的自动编排 + 餐厅酒店穿插 |
| 高客单 | 自动编排 + 人工审核调优 |

## 串联子流程
1. **候选召回** — 按城市/区域从实体模块获取候选
2. **打分排序** — 调用评分引擎获取 FinalScore
3. **区域聚类** — 将候选按区域分组（浅草组/新宿组/银座组…）
4. **日程装配** — 按天分配区域组，考虑节奏约束
5. **餐饮插入** — 在午餐/晚餐时段插入附近餐厅（仅利润款+）
6. **酒店关联** — 根据每天活动区域推荐住宿（引流款只推区域）
7. **交通计算** — 计算每日步行时长 + 换乘次数
8. **预算校验** — 汇总每日预估花费
9. **风险校验** — 营业时间冲突/暴走/跨区检测
10. **备用方案** — 为天气敏感 POI 生成替代

## 数据结构

### itinerary_plan 行程计划
| 字段 | 类型 | 说明 |
|---|---|---|
| plan_id | UUID | 主键 |
| trip_profile_id | UUID | 关联用户画像（利润款+） |
| template_id | VARCHAR | 关联模板 ID（引流款） |
| product_tier | VARCHAR | standard / premium / vip |
| title | VARCHAR | 行程标题 |
| destination_country | VARCHAR | 国家 |
| destination_cities | VARCHAR[] | 城市列表 |
| total_days | INT | 总天数 |
| total_budget_estimate_cny | INT | 预估总花费 |
| status | VARCHAR | draft / reviewed / published |
| created_at | TIMESTAMP | 创建时间 |

### itinerary_day 每日行程
| 字段 | 类型 | 说明 |
|---|---|---|
| day_id | UUID | 主键 |
| plan_id | UUID | 关联行程 |
| day_number | INT | 第几天 |
| theme | VARCHAR | 当日主题（"浅草-上野亲子轻松日"） |
| city | VARCHAR | 当日所在城市 |
| area_cluster | VARCHAR[] | 当日涉及区域 |
| walking_minutes | INT | 预估步行总时长 |
| transfer_count | INT | 换乘次数 |
| day_budget_estimate_cny | INT | 当日预估花费 |
| cross_city | BOOLEAN | 是否跨城 |
| weather_note | TEXT | 天气相关提示 |

### itinerary_item 行程项
| 字段 | 类型 | 说明 |
|---|---|---|
| item_id | UUID | 主键 |
| day_id | UUID | 关联当日行程 |
| sort_order | INT | 排序序号 |
| item_type | VARCHAR | attraction / restaurant / hotel / transport / free_time |
| entity_id | UUID | 关联实体 ID |
| timeslot | VARCHAR | AM / LUNCH / PM / DINNER / EVENING |
| start_time | VARCHAR | 建议开始时间 |
| duration_min | INT | 建议时长 |
| note_zh | TEXT | 中文备注/提示 |
| is_backup | BOOLEAN | 是否为备用方案 |
| backup_for_item_id | UUID | 替代哪个 item |

## 区域模板结构（引流款用）

### route_template 路线模板
| 字段 | 类型 | 说明 |
|---|---|---|
| template_id | VARCHAR | 模板 ID（如 "tokyo_5d_classic"） |
| title | VARCHAR | 模板标题 |
| country | VARCHAR | 国家 |
| cities | VARCHAR[] | 涉及城市 |
| days | INT | 天数 |
| suitable_for | VARCHAR[] | 适合人群 |
| difficulty | VARCHAR | easy / moderate / hard |
| season_best | VARCHAR[] | 最佳季节 |
| description_zh | TEXT | 模板简介 |

## 日程装配约束规则
- 每日第一个 POI 距酒店 ≤ 30 分钟车程
- 同日 POI 必须在同一区域聚类内（允许相邻区域）
- 午餐时段 11:30-13:30 必须安排用餐或自由时间
- 晚餐时段 17:30-19:30 必须安排用餐或自由时间
- 不得安排在营业时间外到达
- 跨城日 POI 数量减半

### intensity 约束映射（来自 geography-routing/spec.md）
| intensity | 每日 POI 上限 | 每日步行上限 | 每日换乘上限 | 对应 pace |
|---|---|---|---|---|
| RELAX | 2 | 40 min | 1 | relaxed |
| EASY | 3 | 60 min | 2 | relaxed |
| BALANCED | 4 | 90 min | 3 | balanced |
| CITY_RUSH | 5 | 120 min | 4 | intensive |
| SPRINT | 6 | 150 min | 5 | intensive |

planner 应从 route.intensity 或 trip_profile.pace 获取约束参数，不再硬编码。

## 输出示例
```json
{
  "day": 2,
  "theme": "浅草-上野亲子轻松日",
  "items": [
    {"type": "attraction", "id": "poi_101", "timeslot": "AM", "start": "09:30", "duration": 90},
    {"type": "restaurant", "id": "res_302", "timeslot": "LUNCH", "start": "12:00", "duration": 60},
    {"type": "attraction", "id": "poi_155", "timeslot": "PM", "start": "13:30", "duration": 120},
    {"type": "restaurant", "id": "res_411", "timeslot": "DINNER", "start": "18:00", "duration": 75}
  ],
  "walking_minutes": 42,
  "transfer_count": 1,
  "cross_city": false,
  "backup_plan": ["poi_188", "mall_22"]
}
```
