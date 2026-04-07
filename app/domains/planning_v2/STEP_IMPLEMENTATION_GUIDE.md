# Planning V2 步骤实现指南

## 概述

实现了 planning_v2 的三个核心步骤：

1. **Step 01: 用户约束解析** (`step01_constraints.py`)
2. **Step 02: 地区摘要汇总** (`step02_region_summary.py`)
3. **Step 08: 每日约束包** (`step08_daily_constraints.py`)

## 详细说明

### Step 01: resolve_user_constraints()

**目的**: 从 TripProfile/DetailForm 规范化用户约束

**输入**:
- `session`: AsyncSession
- `trip_request_id`: UUID 字符串

**输出**: `UserConstraints`
```python
UserConstraints(
    trip_window={
        'start_date': '2026-04-01',
        'end_date': '2026-04-05',
        'total_days': 5
    },
    user_profile={
        'party_type': 'couple',
        'budget_tier': 'premium',
        'must_have_tags': ['shrine', 'garden'],
        'nice_to_have_tags': ['photo_spot', 'cafe'],
        'companion_breakdown': {...},
        'special_requirements': {...}
    },
    constraints={
        'must_visit': ['fushimi_inari', 'arashiyama'],
        'do_not_go': ['crowded_area'],
        'visited': ['tokyo_tower'],
        'booked_items': [...]
    }
)
```

**关键特性**:
- 自动计算 total_days（从 start_date 到 end_date）
- 规范化列表字段（None → []，str → [str]）
- 提取 TripProfile 的所有相关字段
- 包含 special_requirements 和 companion_breakdown（用于高级规划）

**使用示例**:
```python
from app.domains.planning_v2 import resolve_user_constraints

user_constraints = await resolve_user_constraints(
    session=session,
    trip_request_id='550e8400-e29b-41d4-a716-446655440000'
)

print(f"旅行天数: {user_constraints.trip_window['total_days']}")
print(f"同行人类型: {user_constraints.user_profile['party_type']}")
print(f"必去景点: {user_constraints.constraints['must_visit']}")
```

---

### Step 02: build_region_summary()

**目的**: 统计地区内实体分布，为后续池构建提供背景信息

**输入**:
- `session`: AsyncSession
- `circle_id`: str — 从 CircleProfile.circle_id 获取（如 'kansai', 'kanto', 'hokkaido'）
- `circle_cities`: list[str] — 从 CircleProfile.cities 获取（如 ['kyoto', 'osaka', 'kobe']）

**输出**: `RegionSummary`
```python
RegionSummary(
    circle_name='Kansai',
    cities=['kyoto', 'osaka', 'kobe'],
    entity_count=1259,
    entities_by_type={
        'poi': 847,
        'restaurant': 298,
        'hotel': 114,
        'event': 0
    },
    grade_distribution={
        'S': 42,
        'A': 285,
        'B': 732,
        'C': 200
    }
)
```

**SQL查询特点**:
- 批量查询：避免 N+1 问题
- 按 entity_type 和 data_tier 分组聚合
- 自动补充缺失的类型（设为0）
- 精确统计 is_active=true 的实体

**使用示例**:
```python
from app.domains.planning_v2 import build_region_summary

circle = CircleProfile.from_registry("kansai")
region = await build_region_summary(
    session=session,
    circle_id=circle.circle_id,
    circle_cities=circle.cities,
)

print(f"关西圈共 {region.entity_count} 个实体")
print(f"景点(POI): {region.entities_by_type['poi']}")
print(f"S级实体: {region.grade_distribution['S']}")
```

**集成点**:
- 用于验证 circle_cities 配置是否正确
- 为 Step 4 (POI 池) 和 Step 6 (酒店池) 提供背景
- 支持查询语句的优化（如果某城市无实体，可提前跳过）

---

### Step 08: build_daily_constraints_list()

**目的**: 为旅行期间每一天构建时间、营业、班次等约束

**输入**:
- `session`: AsyncSession
- `trip_window`: dict with `{start_date, end_date, total_days}`
- `circle`: CircleProfile — 用于日出日落坐标、时区
- `selected_hotel_id`: Optional[str] (Step 7 输出)
- `user_party_type`: Optional[str]

**输出**: `list[DailyConstraints]`
```python
[
    DailyConstraints(
        date='2026-04-01',
        day_of_week='Wed',
        sunrise='06:15',
        sunset='18:32',
        closed_entities=['entity_id_1', 'entity_id_2'],
        low_freq_transits=[
            {
                'start_time': '09:00',
                'end_time': '17:00',
                'frequency_mins': 60,
                'route': 'JR嵯峨嵐山線',
                'constraint': 'must_be_at_station_by'
            }
        ],
        anchors=[
            {
                'type': 'hotel_checkin',
                'time': '15:00',
                'name': 'Check-in at Kyoto Hotel',
                'constraint': 'hard'
            }
        ],
        hotel_breakfast_included=True,
        hotel_dinner_included=False
    ),
    # ... 后续每一天 ...
]
```

**数据源**:
| 数据 | 来源 | 说明 |
|------|------|------|
| sunrise/sunset | astral 库 + 地理坐标 | 日出日落时间，影响行程规划 |
| closed_entities | EntityOperatingFact + PoiOpeningSnapshot | 该天关闭的实体 |
| low_freq_transits | entity_temporal_profiles (future: transit_frequency) | 班次稀疏的交通方式 |
| anchors | TripProfile + Hotel check-in/out | 固定时间点约束 |
| hotel_breakfast_included | Hotel.amenities / pricing | 酒店是否包含早餐 |

**关键特性**:

1. **Sunrise/Sunset 计算**:
   - 优先使用 `astral` 库（精确计算）
   - Fallback: 基于日期序号的简单正弦波近似
   - 返回格式: 'HH:MM'

2. **关闭实体查询**:
   - 按星期几查询 EntityOperatingFact（定休日）
   - 按日期查询 PoiOpeningSnapshot（临时关闭）
   - 合并两者，返回关闭 entity_id 列表

3. **低频班次** (未来实现):
   - 从 entity_temporal_profiles.availability_notes 解析
   - 或专门的 transit_frequency 表
   - 当前返回空列表

4. **酒店餐饮信息**:
   - 从 Hotel.amenities 推断 ('breakfast', 'dinner', ...)
   - 或从 pricing.includes_meal 读取 (新字段)
   - 返回布尔值 (True/False)

**使用示例**:
```python
from app.domains.planning_v2 import build_daily_constraints_list
from datetime import datetime

circle = CircleProfile.from_registry("kansai")
daily_list = await build_daily_constraints_list(
    session=session,
    trip_window={
        'start_date': '2026-04-01',
        'end_date': '2026-04-05',
        'total_days': 5
    },
    circle=circle,
    selected_hotel_id='550e8400-e29b-41d4-a716-446655440000',
    user_party_type='family_with_kids'
)

for day_constraint in daily_list:
    print(f"{day_constraint.date} ({day_constraint.day_of_week})")
    print(f"  日出: {day_constraint.sunrise}, 日落: {day_constraint.sunset}")
    print(f"  关闭景点: {len(day_constraint.closed_entities)}")
    print(f"  早餐包含: {day_constraint.hotel_breakfast_included}")
    print()
```

**集成点**:
- Step 9 会使用 DailyConstraints 进行可行性检查
- Step 10 会使用 closed_entities 过滤候选实体
- 餐饮信息 (breakfast_included/dinner_included) 用于灵活的餐饮规划

---

## 新字段与扩展

### Hotel 的 pricing 字段扩展

在 hotel_plan.md 中，提议为 Hotel 表添加 pricing 字段：

```python
# app/db/models/catalog.py - Hotel 类

pricing: Mapped[Optional[dict]] = mapped_column(
    JSONB,
    comment='{"per_night_jpy": 8000, "includes_meal": "含早晚", "deposit_required": true}'
)
```

**关键子字段**:
- `per_night_jpy`: int - 每晚基准价格（日元）
- `includes_meal`: str - '不含餐' / '含早' / '含晚' / '含早晚'
- `deposit_required`: bool - 是否需要定金
- `cancellation_policy`: str - '免费取消' / '7天前取消' 等

**Step 8 的处理**:
```python
if selected_hotel:
    hotel_meals = selected_hotel.get('pricing', {}).get('includes_meal', '不含餐')
    daily_constraints.hotel_breakfast_included = '含早' in hotel_meals
    daily_constraints.hotel_dinner_included = '含晚' in hotel_meals
```

---

## 错误处理与 Fallback

### Step 01
- **缺少 TripProfile**: ValueError
- **日期解析失败**: ValueError（带具体错误信息）
- **缺少必需字段**: 使用默认值 (如 party_type='couple')

### Step 02
- **circle_cities 为空**: ValueError
- **数据库查询失败**: 日志警告 + 返回 0 计数
- **缺失实体类型**: 自动补充为 0

### Step 08
- **Sunrise/Sunset 计算失败**: 使用 Fallback（简单正弦波近似）
- **Astral 库不可用**: 自动使用 Fallback（日志警告）
- **酒店不存在**: 返回 (False, False) 用于餐饮包含
- **关闭实体查询失败**: 返回空列表（行程规划会相对宽松）

---

## 性能注意事项

### 批量查询优化

**Step 02** 使用分组聚合：
```sql
-- 不用 N+1 的方式遍历 city 查询
-- 而是一次查询统计：
SELECT entity_type, COUNT(*) FROM entity_base
WHERE city_code IN (?, ?, ...)
GROUP BY entity_type;
```

**Step 08** 使用批量查询：
```sql
-- 一次查询获取整个旅行期间的关闭实体
-- 而不是逐天查询
SELECT * FROM entity_operating_facts
WHERE day_of_week IN (?, ?, ...) AND entity_id IN (SELECT ... FROM candidate_pool)
```

### 时间复杂度
- Step 01: O(1) - 单条记录查询
- Step 02: O(n) - n = circle_cities 数量（通常 < 10）
- Step 08: O(d * e) - d = 旅行天数（通常 < 20），e = 实体数量（查询优化可降至 O(d))

---

## 测试清单

- [ ] Step 01 可以正确解析 TripProfile 的所有字段
- [ ] Step 01 正确计算 total_days（包括边界情况）
- [ ] Step 02 按 city_code 正确分组统计
- [ ] Step 02 自动补充缺失的等级 (S/A/B/C)
- [ ] Step 08 为每一天创建 DailyConstraints
- [ ] Step 08 sunrise/sunset 时间在合理范围内
- [ ] Step 08 能够检索关闭实体
- [ ] Step 08 正确读取酒店早晚餐信息
- [ ] 错误处理：缺少 TripProfile 时抛出 ValueError
- [ ] 错误处理：circle_cities 为空时抛出 ValueError
- [ ] 错误处理：Astral 库不可用时使用 Fallback
- [ ] 日志记录关键操作（INFO 级别）和调试信息（DEBUG 级别）

---

## 未来扩展

### Step 08 的后续改进

1. **低频班次详细化**:
   - 创建 `transit_frequency` 表，存储各条线路的班次间隔
   - 按日期查询并返回详细的班次信息

2. **天文数据本地化**（已完成）:
   - 日出日落坐标和时区从 CircleProfile 获取，不再硬编码东京
   - 各圈使用自己的 default_location + timezone

3. **天气和特殊事件**:
   - 集成 WeatherSnapshot 查询
   - 添加季节活动 (seasonal_events) 和假期标记

4. **高级约束**:
   - 温泉营业时间（hotel amenities 中提取）
   - 餐厅营业时间（restaurant operating_hours_json）
   - 季节限定活动 (seasonal_events)

---

## 相关文档

- [planning_v2 模型定义](models.py)
- [Step 04 POI 池构建](step04_poi_pool.py)
- [Step 06 酒店池构建](step06_hotel_pool.py)
- [数据库架构](../../../db/models/)
- [Hotel Plan 设计](../../../docs/ITINERARY_PLANNING_FINAL_WORKFLOW.md)
