# Plan B 备用方案设计

> 最后更新: 2026-03-28

## 设计目标

用户拿到手账后，可能遇到三种意外：下雨、体力不够、预约失败。
系统在生成行程时为每天的关键 slot 预生成替代方案，写入 `DaySection.plan_b`，PDF 渲染时展示。

**原则：替代方案不是"随便换一个"，而是"同区域、同时段、能立刻去"。**

---

## 三种触发场景

### 1. 下雨（weather）

| 维度 | 规则 |
|------|------|
| 触发条件 | `poi_category` 属于户外类（park/garden/shrine/temple/castle/waterfall/lake/scenic_spot/beach）**或** `risk_flags` 含 `weather_sensitive` / `outdoor_only` |
| 替代策略 | 同区域 → 同城市，优先室内类（museum/art_gallery/aquarium/shopping_mall/indoor_market/theater/hot_spring） |
| 排序 | 同区域优先 > quality_tier 高优先 |
| 文案模板 | "X受天气影响，推荐改去Y（室内，同区域）" |

### 2. 体力不足（low_energy）

| 维度 | 规则 |
|------|------|
| 触发条件 | `poi_category` 属于高强度类（mountain/hiking/theme_park/cycling/water_sport）**或** `risk_flags` 含 `high_physical_demand` **或** `typical_duration_min > 180` |
| 替代策略 | 同区域 → 同城市，排除高强度类，`typical_duration_min <= 120` |
| 排序 | 同区域优先 > quality_tier 高优先 |
| 文案模板 | "改为Y（节奏轻松，同区域步行可达）" |

### 3. 预约失败（booking_fail）

| 维度 | 规则 |
|------|------|
| 触发条件 | `booking_method` 为 `online_advance` / `phone` / `impossible` **或** `risk_flags` 含 `requires_reservation` **或** POI 子表 `requires_advance_booking = true` |
| 替代策略 | 同类型（POI→POI，餐厅→餐厅）、同区域 → 同城市、`booking_method` 为 `walk_in` 或 NULL、同 `poi_category` 优先 |
| 排序 | 同区域 > 同类别 > quality_tier |
| 文案模板 | "X约不到，改去Y（同类型，无需预约或更易约）" |

---

## 数据流

```
generate_trip.py
  └→ build_planning_output()
       └→ 对每天的 slots 调用 build_plan_b_for_day()
            ├→ 遍历 slot，判断触发条件
            ├→ 查 DB 找替代实体（SQL 查询，同区域优先）
            └→ 返回 list[PlanBOption] → DaySection.plan_b
```

## 输出格式

```python
{
    "trigger": "下雨" | "体力不足" | "预约失败",
    "alternative": "人类可读的替代说明",
    "entity_ids": ["原实体ID", "替代实体ID"],
    "original_entity_id": "原实体ID",
    "replacement_entity_id": "替代实体ID",
}
```

## 边界情况

- 同区域找不到替代 → 扩大到同城市
- 同城市也找不到 → 不生成该触发器的 Plan B（允许为空）
- 一个 slot 可能同时触发多种 Plan B（如户外+需预约 → 同时有雨天和预约失败方案）
- 餐厅类只触发预约失败（不触发雨天/体力）
- 酒店类不生成 Plan B

## 后续优化（D3 实现时）

- [ ] 替代实体去重（同一天内不重复推荐同一个替代）
- [ ] 替代实体的营业时间校验（替代品在该时段是否营业）
- [ ] 季节性过滤（替代品在出行月份是否适合）
- [ ] 距离约束（替代品距原地点步行/地铁 < 15分钟）
