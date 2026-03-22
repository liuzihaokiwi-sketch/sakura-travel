# 数据层补充任务拆解

> 创建：2026-03-22
> 依据：ARCHITECTURE.md Layer 1 缺口 + 数据侧审核意见 8 条
> 原则：P0 = 跑通且跑稳，P1 = 效果好且可维护，P2 = 飞轮闭环

---

## 任务依赖图

```
P0 (跑通)
├── T1 entity_aliases 表                    [L1][低级]
├── T2 entity_temporal_profiles 表           [L1][低级]
├── T3 entity_field_provenance 表            [L1][低级]
├── T4 entity_base 补静态字段 + 去掉 detour   [L1][低级]
│     (lat/lng/nearest_station/corridor_tags)
├── T5 TripProfile 补 arrival/departure_day_shape [L2][低级]
├── T6 seed_all_circles.py (6 圈)            [L1][低级]  依赖 T1
├── T7 auto_map_entities_to_clusters.py       [L1][高级]  依赖 T1,T4,T6
│     (可反复跑的管线，消费 entity_aliases)
├── T8 normalize 推导增强                    [L2][高级]  依赖 T5
│     (arrival_day_shape / celebration / mobility)
└── T9 trace 输出到 generation_step_runs      [L4][高级]

P1 (效果好)
├── T10 entity_mapping_reviews 表 + 审核流   [L1][高级]  依赖 T7
├── T11 generation_decisions 补 input_hash    [L2][低级]
├── T12 页面资产层 (hero/gallery/photo_reason) [L1][低级]
├── T13 circle_entity_roles 补 why_selected 等 [L3][低级]
├── T14 corridor 标准化 (area_name → corridor_id) [L1][高级]
└── T15 refresh SLA / stale policy            [L4][高级]
```

---

## P0 任务详细

### T1 — 新建 `entity_aliases` 表
**级别：低级 AI**
**依赖：无**
**文件：`app/db/models/catalog.py` + migration**

```python
class EntityAlias(Base):
    __tablename__ = "entity_aliases"
    alias_id      BIGINT PK AUTO
    entity_id     UUID FK → entity_base  NOT NULL
    alias_text    TEXT NOT NULL
    alias_lang    VARCHAR(10)  # ja / en / zh / romaji
    alias_type    VARCHAR(20)  # official / common / romaji / short / deprecated
    normalized_text TEXT       # 小写+去音标+去空格的标准化文本
    
    INDEX (normalized_text) USING gin (pg_trgm)
    UNIQUE (entity_id, alias_text)
```

**关键：** 建表后立即从现有 entity_base.name_local / name_en 批量灌初始别名。

---

### T2 — 新建 `entity_temporal_profiles` 表
**级别：低级 AI**
**依赖：无**
**文件：新建 `app/db/models/temporal.py` + migration**

```python
class EntityTemporalProfile(Base):
    __tablename__ = "entity_temporal_profiles"
    profile_id        BIGINT PK AUTO
    entity_id         UUID FK → entity_base  NOT NULL
    season_code       VARCHAR(20)   # spring / summer / autumn / winter / all_year
    month_range       VARCHAR(20)   # "03-04" / "07-08"
    daypart           VARCHAR(20)   # morning / afternoon / evening / night / all_day
    best_time_window  VARCHAR(50)   # "06:00-09:00"
    queue_risk_level  VARCHAR(10)   # low / medium / high / extreme
    weather_sensitivity VARCHAR(10) # none / low / medium / high
    crowd_level       VARCHAR(10)   # low / medium / high / extreme
    availability_notes TEXT
    source_type       VARCHAR(20)   # official / platform / ai_estimated / manual
    
    UNIQUE (entity_id, season_code, daypart)
```

---

### T3 — 新建 `entity_field_provenance` 表
**级别：低级 AI**
**依赖：无**
**文件：新建或加入 `app/db/models/catalog.py` + migration**

```python
class EntityFieldProvenance(Base):
    __tablename__ = "entity_field_provenance"
    provenance_id   BIGINT PK AUTO
    entity_id       UUID FK → entity_base  NOT NULL
    field_name      VARCHAR(100) NOT NULL   # "typical_duration_minutes" / "price_band" / ...
    source_type     VARCHAR(20)  NOT NULL   # official / platform / ai_estimated / manual / rule_derived
    source_ref      TEXT                    # URL 或来源标识
    confidence_score NUMERIC(3,2)           # 0.00-1.00
    review_status   VARCHAR(20) DEFAULT 'unreviewed'  # unreviewed / approved / rejected / stale
    reviewed_by     VARCHAR(100)
    updated_at      TIMESTAMP DEFAULT NOW()
    
    UNIQUE (entity_id, field_name, source_type)
```

---

### T4 — entity_base 补静态字段 + 移除 detour
**级别：低级 AI**
**依赖：无**
**文件：`app/db/models/catalog.py` + migration**

**新增字段：**
- `latitude` NUMERIC(9,6) — 纬度
- `longitude` NUMERIC(9,6) — 经度
- `nearest_station` VARCHAR(100)
- `corridor_tags` JSONB DEFAULT '[]' — 所属走廊标签
- `typical_duration_baseline` SMALLINT — 基准游览时长（分钟），非时态值
- `price_band` VARCHAR(10) — free / budget / mid / premium / luxury
- `operating_stability_level` VARCHAR(10) — stable / moderate / volatile

**不加的字段（对比原方案）：**
- ~~`detour_cost_minutes`~~ → 改为 itinerary_fit 动态计算
- ~~`best_time_window`~~ → 移到 entity_temporal_profiles
- ~~`weather_sensitivity`~~ → 移到 entity_temporal_profiles
- ~~`queue_risk_level`~~ → 移到 entity_temporal_profiles

---

### T5 — TripProfile 补 2 个字段
**级别：低级 AI**
**依赖：无**
**文件：`app/db/models/business.py` + migration**

```python
arrival_day_shape   VARCHAR(20)  # full_day / half_day_afternoon / evening_only / red_eye
departure_day_shape VARCHAR(20)  # full_day / half_day_morning / early_morning
```

---

### T6 — seed_all_circles.py（6 圈种子数据）
**级别：低级 AI**
**依赖：T1（别名表要同步灌）**
**文件：`scripts/seed_all_circles.py`**

**每个圈灌入：**
- 1 条 city_circles
- 7-10 条 activity_clusters
- 5 条 hotel_strategy_presets
- 同时灌入活动簇代表节点的 entity_aliases（日文名/英文名/罗马音）

**必须带的元数据：**
```python
SEED_META = {
    "schema_version": "v1",
    "seed_version": "2026-03-22",
    "source_doc_refs": [
        "major/02_关西城市圈系统结构表.md",
        "major/03_东京城市圈系统结构表.md",
        ...
    ],
}
```

---

### T7 — auto_map_entities_to_clusters.py（实体映射管线）
**级别：高级 AI**
**依赖：T1, T4, T6**
**文件：`scripts/auto_map_entities_to_clusters.py`**

**不是一次性脚本，是可反复跑的管线。**

**匹配策略（4 层）：**
1. **exact_match**: cluster 代表节点名 == entity_alias.normalized_text
2. **alias_match**: pg_trgm similarity ≥ 0.7 且同 city_code
3. **fuzzy_match**: similarity ≥ 0.5 且同 corridor_tags 有交集
4. **rejected**: similarity < 0.5 或 city_code 不匹配

**输出：**
- 写入 `circle_entity_roles`（exact + alias match 自动写入）
- fuzzy match 标记 `needs_review=true`
- rejected 输出到 `entity_mapping_reviews` 表（如果 P1 T10 已建，否则输出日志）
- 打印覆盖率报告：每圈每簇匹配了几个实体

**锚点标记规则：**
- 活动簇 level=S 的第一个 exact_match 实体 → is_cluster_anchor=True
- 其余实体 → role 按 entity_type 推导（poi→anchor_poi/secondary_poi, restaurant→meal_*, hotel→hotel_anchor）

---

### T8 — normalize 推导增强
**级别：高级 AI**
**依赖：T5**
**文件：修改 normalize_profile job**

**推导规则：**

| 输出字段 | 推导来源 |
|----------|---------|
| `arrival_day_shape` | flight_info.outbound.arrive 时间：<12点→full_day, 12-17→half_day_afternoon, 17-22→evening_only, >22→red_eye |
| `departure_day_shape` | flight_info.return.depart 时间：>18→full_day, 12-18→half_day_morning, <12→early_morning |
| `celebration_flags` | 从 free_text_wishes 用关键词提取（生日/纪念日/求婚/蜜月） |
| `mobility_notes` | has_elderly→slow_pace, has_children+age<5→stroller, wheelchair→accessible_only |
| `queue_tolerance` | pace=packed→high, pace=relaxed+has_elderly→low, default→medium |
| `weather_risk_tolerance` | travel_month∈[6,7,8,9]+has_children→low, solo+packed→high |
| `food/photo/shopping/hotel_priority` | 从 must_have_tags 计数：含 food/ramen/sushi→food_priority=high |

**推导结果分两块写入：**
- 高频决策字段 → TripProfile 一等列（arrival_day_shape 等）
- 低频/复杂字段 → special_requirements JSONB 内

---

### T9 — trace 输出到 generation_step_runs
**级别：高级 AI**
**依赖：无（修改已有各模块返回值）**
**文件：修改 `generate_trip.py` + 各决策模块**

**改造方式：**
每个决策模块已经返回 `trace: list[str]`，只需在 `_try_city_circle_pipeline()` 中把每步的 trace 写入 `generation_step_runs` 表。

```python
async def _save_trace(session, plan_id, step_name, trace_data):
    await session.execute(
        text("""
            INSERT INTO generation_step_runs 
            (plan_id, step_name, trace_payload, created_at)
            VALUES (:pid, :step, :payload, NOW())
        """),
        {"pid": str(plan_id), "step": step_name, 
         "payload": json.dumps(trace_data, ensure_ascii=False)},
    )
```

**写入的 step_name：**
- `eligibility_gate`
- `precheck_gate`
- `circle_selection`
- `major_ranking`
- `hotel_strategy`
- `skeleton_build`
- `secondary_fill`
- `meal_fill`
- `report_generation`

---

## P1 任务详细

### T10 — entity_mapping_reviews 表 + 审核流
**级别：高级 AI**
**依赖：T7**

审核队列表，取代 CSV 工作流。支持重跑映射、统计覆盖率、AI 二次学习。

### T11 — generation_decisions 补字段
**级别：低级 AI**
**依赖：无**

补 `input_hash`（画像哈希，用于判断是否需要重跑）+ `is_current`（当前有效版本标记）。

### T12 — 页面资产层
**级别：低级 AI**
**依赖：无**

新建 `page_hero_registry` 表：hero_id / page_type / object_id / render_mode / visual_priority / crop_safe_area。

### T13 — circle_entity_roles 补决策解释字段
**级别：低级 AI**
**依赖：无**

在 `circle_entity_roles` 上补：why_selected / what_to_expect / booking_or_arrival_hint。**不挂 entity_base**，因为同实体不同角色的解释口径不同。

### T14 — corridor 标准化
**级别：高级 AI**
**依赖：T4, T6**

标准化 area_name → corridor_id 的映射逻辑，让 corridor_alignment 评分有准确输入。

### T15 — refresh SLA / stale policy
**级别：高级 AI**
**依赖：T3**

基于 entity_field_provenance 的 updated_at，定义每类字段的 refresh SLA，到期自动标记 stale。

---

## 执行顺序

```
第一批（纯建表，无依赖，低级 AI 并行做）:
  T1 + T2 + T3 + T4 + T5

第二批（种子数据，依赖 T1）:
  T6

第三批（核心管线，依赖 T1+T4+T6）:
  T7（高级 AI — 实体映射管线）

第四批（推导 + trace，依赖 T5）:
  T8（高级 AI — normalize 增强）
  T9（高级 AI — trace 输出）

第五批 P1（效果打磨）:
  T10~T15
```

---

## 任务总结

| ID | 任务 | 层 | 级别 | 依赖 | 优先级 |
|----|------|---|------|------|--------|
| T1 | entity_aliases 表 | L1 | 低级 | 无 | P0 |
| T2 | entity_temporal_profiles 表 | L1 | 低级 | 无 | P0 |
| T3 | entity_field_provenance 表 | L1 | 低级 | 无 | P0 |
| T4 | entity_base 补静态字段 | L1 | 低级 | 无 | P0 |
| T5 | TripProfile 补 2 字段 | L2 | 低级 | 无 | P0 |
| T6 | 6 圈种子数据 | L1 | 低级 | T1 | P0 |
| T7 | 实体映射管线 | L1 | **高级** | T1,T4,T6 | P0 |
| T8 | normalize 推导增强 | L2 | **高级** | T5 | P0 |
| T9 | trace 输出 | L4 | **高级** | 无 | P0 |
| T10 | 映射审核表+流 | L1 | **高级** | T7 | P1 | ✅ 完成 |
| T11 | decisions 补字段 | L2 | 低级 | 无 | P1 | ✅ 完成 |
| T12 | 页面资产层 | L1 | 低级 | 无 | P1 | ✅ 完成 |
| T13 | roles 补解释字段 | L3 | 低级 | 无 | P1 | ✅ 完成 |
| T14 | corridor 标准化 | L1 | **高级** | T4,T6 | P1 | ✅ 完成 |
| T15 | refresh SLA | L4 | **高级** | T3 | P1 | ✅ 完成 |
