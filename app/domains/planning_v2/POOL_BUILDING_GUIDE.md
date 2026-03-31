# 候选池构建指南（Step 4 & 6）

## 概述

`step04_poi_pool.py` 和 `step06_hotel_pool.py` 实现了 planning_v2 工作流中的候选池缩减逻辑，将所有可用实体过滤为符合用户约束的候选集合。

## Step 4：POI 候选池构建（step04_poi_pool.py）

### 功能
从 entity_base 读取 POI 数据，按 10 条规则顺序执行过滤，最终输出符合条件的景点候选池。

### 过滤规则（顺序执行）

| 序号 | 规则 | 说明 | 数据源 |
|-----|------|------|--------|
| 1 | 城市范围 | 必须在 circle 的城市范围内 | RegionSummary.cities |
| 2 | 激活状态 | 必须 is_active=true | entity_base.is_active |
| 3 | 数据等级 | 必须 data_tier in [S, A] | entity_base.data_tier |
| 4 | 同行条件 | 过滤小孩不宜/老人不宜 | EntityTag, UserConstraints.party_type |
| 5 | 预算等级 | 高端体验 vs 用户预算 | entity_base.budget_tier, EntityTag |
| 6 | 季节 | best_season 与旅行月份匹配 | Poi.best_season |
| 7 | 禁去地 | 排除 do_not_go_places | UserConstraints.constraints |
| 8 | 已访问 | 排除 visited_places | UserConstraints.constraints |
| 9 | 定休日 | 永久关闭、长期停业 | EntityOperatingFact |
| 10 | 风险标志 | 排除施工、不稳定等 | entity_base.risk_flags |

### 接口定义

```python
async def build_poi_pool(
    session: AsyncSession,
    user_constraints: UserConstraints,
    region_summary: RegionSummary,
    travel_dates: list[str],  # [YYYY-MM-DD, ...]
) -> list[CandidatePool]:
    """
    构建 POI 候选池。

    Args:
        session: SQLAlchemy 异步数据库会话
        user_constraints: 用户约束（trip_window, user_profile, constraints）
        region_summary: 地区摘要（circle_name, cities）
        travel_dates: 旅行日期列表，YYYY-MM-DD 格式

    Returns:
        CandidatePool 列表，每个包含：
          - entity_id: UUID 字符串
          - name_zh: 中文名称
          - entity_type: "poi"
          - grade: "S" 或 "A"
          - latitude, longitude: 地理坐标
          - tags: 语义标签列表
          - visit_minutes: 推荐游览时间（分钟）
          - cost_jpy: 门票价格（日元）
          - open_hours: 营业时间字典
          - review_signals: 评分信号（rating, review_count 等）
    """
```

### 使用示例

```python
from app.domains.planning_v2 import build_poi_pool, UserConstraints, RegionSummary

# 构建用户约束
user_constraints = UserConstraints(
    trip_window={
        "start_date": "2026-04-01",
        "end_date": "2026-04-05",
        "total_days": 5,
    },
    user_profile={
        "party_type": "family_young",  # 带小孩
        "budget_tier": "mid",
        "children_ages": [5, 8],
        "avoid_tags": ["nightclub", "bar"],
    },
    constraints={
        "do_not_go": ["entity_id_1", "entity_id_2"],
        "visited": ["entity_id_3"],
        "must_visit": [],
    },
)

# 构建地区摘要
region_summary = RegionSummary(
    circle_name="kansai_classic_circle",
    cities=["kyoto", "osaka", "nara"],
    entity_count=150,
    entities_by_type={"poi": 100, "restaurant": 30, "hotel": 20},
    grade_distribution={"S": 10, "A": 40, "B": 100},
)

# 构建候选池
poi_pools = await build_poi_pool(
    session=db_session,
    user_constraints=user_constraints,
    region_summary=region_summary,
    travel_dates=["2026-04-01", "2026-04-02", "2026-04-03", "2026-04-04", "2026-04-05"],
)

# 输出例子
print(f"POI 候选池: {len(poi_pools)} 个景点")
for pool in poi_pools[:3]:
    print(f"  {pool.name_zh} ({pool.grade}) - {pool.visit_minutes}分 - ¥{pool.cost_jpy}")
```

### 关键设计点

1. **顺序过滤**：规则按顺序执行，每条规则独立决定是否排除实体
2. **权重计算**：visit_minutes 用作权重（仅在酒店池中使用）
3. **季节处理**：支持 "all"、"spring,summer" 等多种格式
4. **错误容忍**：缺失字段（如 lat/lng）降级为 0，不中断流程
5. **日志跟踪**：每步过滤的数量和失败原因都被记录

---

## Step 6：酒店候选池构建（step06_hotel_pool.py）

### 功能
从 entity_base 读取酒店数据，计算 POI 池的地理中心，按距离和预算过滤，输出酒店候选池。

### 逻辑流程

```
1. 计算 POI 池地理中心
   ├─ 加权平均：权重 = visit_minutes
   ├─ 若无有效坐标，降级为简单平均
   └─ 若池为空，使用全圈范围

2. 查询圈内所有酒店
   ├─ WHERE entity_type='hotel' AND city_code IN circle_cities
   └─ WHERE is_active=true

3. 执行过滤规则
   ├─ 排除 do_not_go_places 中的酒店
   ├─ 排除有风险标志的酒店（施工、关闭等）
   └─ 按预算过滤（用户预算 >= 酒店等级）

4. 按距离排序并截取
   ├─ 使用 Haversine 公式计算距离
   ├─ 按距离升序排序
   └─ 保留前 N 个（默认 50）

5. 转换为 CandidatePool
   └─ 添加距离信息到 review_signals
```

### 接口定义

```python
async def build_hotel_pool(
    session: AsyncSession,
    user_constraints: UserConstraints,
    circle_name: str,
    circle_cities: list[str],
    candidate_poi_pool: list[CandidatePool],
    max_candidates: int = 50,
) -> list[CandidatePool]:
    """
    构建酒店候选池。

    Args:
        session: SQLAlchemy 异步数据库会话
        user_constraints: 用户约束
        circle_name: 城市圈名称（用于日志）
        circle_cities: 圈内城市列表
        candidate_poi_pool: POI 候选池（用于计算地理中心）
        max_candidates: 最多保留的酒店数（默认 50）

    Returns:
        CandidatePool 列表，每个包含：
          - entity_id: UUID 字符串
          - name_zh: 中文名称
          - entity_type: "hotel"
          - grade: 数据等级
          - latitude, longitude: 地理坐标
          - tags: 语义标签列表
          - visit_minutes: 0（酒店无访问时长）
          - cost_jpy: 每晚参考价
          - open_hours: {"check_in_time": "HH:MM", "check_out_time": "HH:MM"}
          - review_signals: 距离、星级、评分、设施等
    """
```

### 使用示例

```python
from app.domains.planning_v2 import build_poi_pool, build_hotel_pool

# 先构建 POI 池（见上例）
poi_pools = await build_poi_pool(
    session=db_session,
    user_constraints=user_constraints,
    region_summary=region_summary,
    travel_dates=["2026-04-01", "2026-04-02", "2026-04-03", "2026-04-04", "2026-04-05"],
)

# 再构建酒店池
hotel_pools = await build_hotel_pool(
    session=db_session,
    user_constraints=user_constraints,
    circle_name="kansai_classic_circle",
    circle_cities=["kyoto", "osaka", "nara"],
    candidate_poi_pool=poi_pools,
    max_candidates=50,
)

# 输出例子
print(f"酒店候选池: {len(hotel_pools)} 家酒店")
for pool in hotel_pools[:3]:
    distance = pool.review_signals.get("distance_from_poi_center_km", "?")
    star = pool.review_signals.get("star_rating", "?")
    print(f"  {pool.name_zh} - {star}★ - 距离中心{distance}km - ¥{pool.cost_jpy}/晚")
```

### 关键设计点

1. **地理中心计算**：
   - 使用 Haversine 公式，精度 ±10m
   - 权重 = POI 访问时长（反映重要性）
   - 若无坐标，距离设为 inf，自动排在后面

2. **距离排序**：
   - 按距离升序排列
   - 距离越近越优先（通常意味着交通便利）
   - 默认保留前 50 家，可调整 max_candidates

3. **预算约束**：
   - 用户预算为"中等"，可选"中等"和"廉价"的酒店
   - 用户预算为"豪华"，可选所有等级的酒店
   - 用户预算为"廉价"，仅可选"廉价"酒店

4. **设施信息**：
   - amenities（温泉、早餐、停车等）存储在 review_signals
   - 用于后续的酒店选择和展示

---

## 集成测试案例

### 场景：关西 5 日游家庭游

```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.domains.planning_v2 import (
    build_poi_pool,
    build_hotel_pool,
    UserConstraints,
    RegionSummary,
)

async def test_kansai_family_trip():
    # 连接数据库
    engine = create_async_engine("postgresql+asyncpg://...")
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # 用户约束
        user_constraints = UserConstraints(
            trip_window={
                "start_date": "2026-04-15",
                "end_date": "2026-04-19",
                "total_days": 5,
            },
            user_profile={
                "party_type": "family_young",
                "budget_tier": "mid",
                "children_ages": [5, 8],
                "has_elderly": False,
                "avoid_tags": ["nightlife", "extreme_sports"],
            },
            constraints={
                "do_not_go": [],
                "visited": [],
                "must_visit": ["shrine_a", "castle_b"],
                "booked_items": [],
            },
        )

        # 地区摘要
        region_summary = RegionSummary(
            circle_name="kansai_classic_circle",
            cities=["kyoto", "osaka", "nara"],
            entity_count=0,  # 实际值由 build_poi_pool 确定
            entities_by_type={},
            grade_distribution={},
        )

        # Step 4: 构建 POI 池
        poi_pools = await build_poi_pool(
            session=session,
            user_constraints=user_constraints,
            region_summary=region_summary,
            travel_dates=[
                "2026-04-15", "2026-04-16", "2026-04-17",
                "2026-04-18", "2026-04-19"
            ],
        )

        print(f"✓ POI 候选池: {len(poi_pools)} 个景点")

        # Step 6: 构建酒店池
        hotel_pools = await build_hotel_pool(
            session=session,
            user_constraints=user_constraints,
            circle_name="kansai_classic_circle",
            circle_cities=["kyoto", "osaka", "nara"],
            candidate_poi_pool=poi_pools,
            max_candidates=40,
        )

        print(f"✓ 酒店候选池: {len(hotel_pools)} 家酒店")

        # 验证数据质量
        for pool in poi_pools[:5]:
            assert pool.entity_id, "entity_id 缺失"
            assert pool.name_zh, "name_zh 缺失"
            assert pool.visit_minutes > 0, "visit_minutes 应 > 0"

        for pool in hotel_pools[:5]:
            assert pool.entity_id, "entity_id 缺失"
            assert pool.name_zh, "name_zh 缺失"
            assert "distance_from_poi_center_km" in pool.review_signals

        print("✓ 数据质量验证通过")

asyncio.run(test_kansai_family_trip())
```

---

## 性能与优化

### 数据库查询性能

- **批量查询**：所有数据通过 3-4 次批量 SQL 查询完成，而非逐实体查询
- **索引使用**：利用 entity_base(city_code, entity_type) 和 entity_base(data_tier) 索引
- **预期耗时**：
  - POI 池：100-200 个实体 → 50-100ms
  - 酒店池：50 个实体 → 20-30ms

### 内存占用

- POI 池：~1-2MB（1000 个实体）
- 酒店池：~500KB（50 个实体）

---

## 常见问题

### Q: 为什么某个景点被过滤了？

A: 检查日志中的 trace_log，它列出了每步过滤的数量变化：
```
Step 1 (base filter): 150 POI
Step 2-10 (all filters): 45 POI
```

可逐步启用过滤规则，找出哪条规则导致排除。

### Q: 地理中心计算不准确？

A:
- 确认 poi_pools 的坐标有效（不为 0,0）
- Haversine 公式精度为 ±10m，足够规划使用
- 若 POI 分布极端不均，可使用 geometry 中位数替代平均

### Q: 酒店距离为什么是 inf？

A: 表示该酒店缺少有效坐标（lat=0 或 lng=0）。应检查数据质量。

### Q: 如何调整酒店数量上限？

A:
```python
hotel_pools = await build_hotel_pool(
    ...
    max_candidates=100,  # 改为 100
)
```

---

## 依赖和导入

```python
# 必需的数据库表/模型
from app.db.models.catalog import EntityBase, Poi, Hotel, EntityTag
from app.db.models.soft_rules import EntityOperatingFact

# 数据结构
from app.domains.planning_v2 import (
    UserConstraints,
    RegionSummary,
    CandidatePool,
)

# 池构建函数
from app.domains.planning_v2 import (
    build_poi_pool,
    build_hotel_pool,
)
```

---

## 下一步

在 planning_v2 工作流中，候选池之后的步骤：
- **Step 5**: 计算可行性（feasibility checking）
- **Step 7**: 主活动排名（major activity ranking）
- **Step 8**: 日程规划（itinerary scheduling）
