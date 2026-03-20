# 需求采集与用户画像模块

## 概述
将用户的自然语言需求或表单输入转换成统一结构化画像，驱动后续所有模块的筛选和评分。

## 产品价位关系
| 价位 | 需求采集方式 |
|---|---|
| 引流款（19.9~29.9） | 不采集用户信息，直接选择预制路线模板 |
| 利润款（69~199） | 表单采集（出行时间/人数/预算/偏好等） |
| 高客单 | 表单 + 自然语言对话 + 人工沟通 |

## 采集字段

### trip_profile 表
| 字段 | 类型 | 说明 | 引流款 | 利润款 | 高客单 |
|---|---|---|---|---|---|
| profile_id | UUID | 主键 | - | ✅ | ✅ |
| user_id | UUID | 用户 ID | - | ✅ | ✅ |
| departure_city | VARCHAR | 出发城市 | - | ✅ | ✅ |
| destination_country | VARCHAR | 目的地国家 | - | ✅ | ✅ |
| destination_cities | VARCHAR[] | 目的地城市（可空，空则由区域匹配推导） | - | ✅ | ✅ |
| travel_month | VARCHAR | 出行月份 | - | ✅ | ✅ |
| travel_start_date | DATE | 出行起始日 | - | 可选 | ✅ |
| travel_days | INT | 出行天数 | - | ✅ | ✅ |
| party_size | INT | 人数 | - | ✅ | ✅ |
| party_type | VARCHAR | 同行关系 | - | ✅ | ✅ |
| budget_level | VARCHAR | 预算区间 | - | ✅ | ✅ |
| budget_total_cny | INT | 总预算（人民币） | - | 可选 | ✅ |
| visit_count | INT | 第几次去 | - | ✅ | ✅ |
| trip_experience | VARCHAR | first_time / repeat（由 visit_count 推导） | - | ✅ | ✅ |
| preferences | JSONB | 偏好标签 | - | ✅ | ✅ |
| theme_weights | JSONB | 主题偏好权重（由 preferences 推导或用户直接设置） | - | ✅ | ✅ |
| pace | VARCHAR | 节奏 | - | ✅ | ✅ |
| accept_frequent_transfer | BOOLEAN | 是否接受频繁换乘 | - | ✅ | ✅ |
| need_hotel_rec | BOOLEAN | 是否需要酒店推荐 | - | ✅ | ✅ |
| need_restaurant_rec | BOOLEAN | 是否需要餐饮推荐 | - | ✅ | ✅ |
| need_rainy_backup | BOOLEAN | 是否需要雨天方案 | - | 可选 | ✅ |
| flight_preferences | JSONB | 航班偏好 `{"depart_after":"09:00","return_before":"21:00"}` | - | 可选 | ✅ |
| special_requirements | TEXT | 特殊需求 | - | - | ✅ |
| matched_region_ids | JSONB | 匹配到的区域 ID 列表（系统填充） | - | ✅ | ✅ |
| matched_route_id | VARCHAR | 最终选定的线路 ID（系统填充） | - | ✅ | ✅ |
| created_at | TIMESTAMP | 创建时间 | - | ✅ | ✅ |

### 同行关系枚举
solo / couple / friends / family_child / family_elder / pet / group

### 预算区间枚举
budget / mid_range / comfortable / luxury / ultra_luxury

### 节奏枚举
relaxed / balanced / intensive

### 偏好标签枚举
anime / shopping / onsen / food / nature / photo / museum / theme_park / culture / nightlife / skiing

## 用户画像输出结构
```json
{
  "trip_type": "自由行",
  "party_type": "亲子",
  "days": 5,
  "budget_level": "mid_range",
  "pace": "relaxed",
  "must_have_tags": ["family_friendly", "transport_convenient", "rainy_day_friendly"],
  "avoid_tags": ["late_night", "intensive_walking", "frequent_transfer"],
  "theme_weights": {
    "anime": 0.1,
    "shopping": 0.2,
    "food": 0.2,
    "attraction": 0.15,
    "family": 0.35
  }
}
```

## 画像转换规则
- party_type=family_child → 自动添加 must_have: family_friendly, avoid: late_night
- party_type=family_elder → 自动添加 must_have: low_physical, avoid: intensive_walking
- pace=relaxed → 每日 POI 上限 3 个
- pace=balanced → 每日 POI 上限 4 个
- pace=intensive → 每日 POI 上限 5-6 个
- budget_level=budget → 自动添加 theme_weight: budget_friendly +0.3
