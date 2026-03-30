# 数据管线待办任务

> 最后更新: 2026-03-29
>
> 分三层审计：数据结构、数据采集、数据消费。每层按优先级排列。

---

## 一、数据结构层

### P0：必须修的结构问题

#### 1.1 轮换惩罚双重扣分
- **文件**: `app/domains/ranking/scorer.py:421` + `app/domains/ranking/rotation.py`
- **问题**: `compute_rotation_penalty()` 先做绝对扣分（log2 公式），然后 `apply_rotation_penalty()` 又做百分比扣分。同一个 `recommendation_count_30d` 被惩罚两次。
- **影响**: 推荐过 20 次的实体被过度压制，轮换机制矫枉过正
- **修复**: 去掉其中一个，保留 log2 绝对扣分即可

#### 1.2 缺少关键索引
- **文件**: `app/db/models/catalog.py`
- **问题**: 以下高频查询字段缺索引
  - `entity_base.recommendation_count_30d` — rotation.py 全表扫描
  - `entity_base.is_active` — 几乎所有查询都过滤此字段
- **修复**: 写 migration 加两个索引

#### 1.3 soft_rules 层表归属错误
- **文件**: `app/db/models/soft_rules.py`
- **问题**: 以下表不是"软规则"，放错了位置
  - `entity_operating_facts` → 应归 catalog 层（营业事实是硬数据）
  - `area_profiles` → 应归 city_circles 层（区域画像）
  - `transport_links` → 应归 corridors 层（交通连接）
  - `timeslot_rules` → 应合并到 `entity_temporal_profiles`
  - `seasonal_events` → 应独立为 temporal 层
- **影响**: 开发者找不到表、职责混乱
- **修复**: 移动模型定义到正确的文件，保持表名不变（无需 migration）

### P1：应该修的结构问题

#### 1.4 死表清理
以下表无任何代码读写，建议归档或标记 deprecated：
- `preview_trigger_scores` — 零读写
- `swap_candidate_soft_scores` — 零读写
- `user_events` — 零读写
- `product_config`（soft_rules 里的） — 被 config_center 层取代
- `feature_flags`（soft_rules 里的） — 零读写

#### 1.5 重复字段整理
| 重复 | 位置 | 建议 |
|------|------|------|
| `opening_hours_json` | Poi + Restaurant 各有一份 | 保持各自子表（CTI 模式正确） |
| `best_time_of_day` (entity_base) vs `best_time_window` (temporal_profiles) | 两种表示 | 废弃 entity_base 上的，统一用 temporal_profiles |
| `queue_risk_level` | entity_base.risk_flags + temporal_profiles + activity_clusters | 三处 | 活动簇级别用 activity_clusters 的，实体级别用 temporal_profiles 的 |
| `price_band` (entity_base) vs `price_tier` (Hotel) vs `budget_tier` (entity_base) | 三个价格字段 | 统一用 `budget_tier`，其余废弃 |

---

## 二、数据采集层

### P0：采集可靠性

#### 2.1 数据校验不足
- **文件**: `app/domains/catalog/ai_generator.py:80-112`
- **问题**: 只校验了 name_zh 非空和坐标范围。以下未校验：
  - `poi_category` / `cuisine_type` / `hotel_type` 无枚举校验
  - 价格无范围校验（可能为负数或天价）
  - URL 无格式校验
  - `star_rating` 无范围检查
- **修复**: 在 `validate_entity()` 中增加字段级校验

#### 2.2 去重逻辑薄弱
- **文件**: `app/domains/catalog/pipeline.py:51-65`, `upsert.py:82-131`
- **问题**:
  - pipeline 只按 `name_zh + city_code + entity_type` 去重
  - upsert 按 `google_place_id` 或 `tabelog_id` 匹配
  - OSM 的 `osm_id` 没有用于去重
  - Hotel 的 `booking_hotel_id` / `agoda_hotel_id` 没有用于去重
  - 同一地点不同写法（"浅草寺" vs "Senso-ji"）会创建重复实体
- **修复**: upsert 逻辑增加 osm_id / booking_id 匹配；考虑名称模糊匹配

#### 2.3 data_tier 不区分来源
- **文件**: `app/domains/catalog/pipeline.py:92,154,228`
- **问题**:
  - OSM 爬取的 POI 标 "A"
  - Tabelog 爬取的餐厅标 "B"（应该是 A，因为是权威来源）
  - AI 生成的也标 "B"（跟真实爬取混在一起）
- **修复**: 增加 `source_type` 字段或调整 data_tier 赋值逻辑

### P1：采集健壮性

#### 2.4 汇率硬编码
- **文件**: `app/domains/catalog/pipeline.py:421,505-507`
- **问题**: `1 CNY = 21 JPY` 硬编码，从未更新
- **修复**: 移到配置文件或环境变量

#### 2.5 刷新机制粗糙
- **文件**: `app/workers/jobs/refresh_entities.py`
- **问题**:
  - 只用 AI 刷新（不回到原始数据源）
  - 刷新阈值 30 天硬编码
  - 批量大小 20 硬编码
  - S/A 级数据刷新后可能降级为 B 级（AI 生成质量不稳定）
- **修复**: 高 tier 数据不用 AI 刷新；阈值/批量移到环境变量

---

## 三、数据消费层

### P0：直接影响手账质量的逻辑问题

#### 3.1 时间分配忽略实体时长
- **文件**: `app/domains/planning/itinerary_builder.py:45-57,213`
- **问题**: 所有活动统一分配 75 分钟，不管 `major.default_duration` 或 `poi.typical_duration_min`
  - 博物馆需要 3 小时但只给 75 分钟
  - 快速景点 30 分钟但也给 75 分钟
- **修复**: 从 skeleton frame 读 `activity_load_minutes`，用实际时长分配

#### 3.2 copy_enrichment 硬编码模型名
- **文件**: `app/domains/rendering/copy_enrichment.py:163,209`
- **问题**: 写死 `model="gpt-4o-mini"`，不走 settings 的模型配置
- **修复**: 改为 `from app.core.config import settings; model=settings.ai_model_light`

#### 3.3 预算估算全靠默认值
- **文件**: `app/domains/planning/budget_estimator.py:26-62`
- **问题**: 以下全部硬编码：
  - `JPY_TO_CNY = 0.047`
  - `TRANSPORT_BUDGET_BY_TIER`（800-3000 日元/天）
  - `HOTEL_BUDGET_BY_TIER`（5000-40000 日元/晚）
  - `FOOD_FLOOR_BY_TIER`（2000-10000 日元/天）
  - `DEFAULT_ADMISSION_BY_POI_CATEGORY`（13 个品类的门票默认值）
  - `MISC_BUFFER_RATE = 0.10`
- **影响**: 用户看到的预算数字跟实际偏差大
- **修复**: 移到配置表（config_packs 或环境变量），优先读实体真实数据

#### 3.4 Plan B budget_level 参数传了但从没用
- **文件**: `app/domains/planning/plan_b_builder.py:49,85,99,114,164,234,272`
- **问题**: `budget_level` 作为参数传入了 7 个函数，但在查询替代方案时完全没用来过滤
- **影响**: 经济型用户可能被推荐奢华替代方案
- **修复**: 查询替代实体时增加 `budget_tier` 过滤条件

### P1：可以改善手册质量的逻辑问题

#### 3.5 itinerary_fit_scorer 结果被丢弃
- **文件**: `app/workers/jobs/generate_trip.py:734-794`
- **问题**: fit scoring 跑完了，swap suggestions 也生成了，但结果既没写 DB 也没反馈给排序
- **影响**: 次要活动的路线适配度优化白做了
- **修复**: 将 fit results 写入 `plan_metadata["fit_scores"]`，swap suggestions 写入 `plan_metadata["swap_suggestions"]`

#### 3.6 route_skeleton 不用 best_time_window
- **文件**: `app/domains/planning/route_skeleton_builder.py`
- **问题**: `activity_clusters.best_time_window` 字段存在但骨架编排完全不读
- **影响**: 可能把"最佳上午去"的活动排到下午
- **修复**: 在 `_assign_major_drivers()` 中增加时段偏好匹配

#### 3.7 page_view_model 不检查 null
- **文件**: `app/domains/rendering/page_view_model.py:266-268,375-405`
- **问题**:
  - `payload.days` 可能为 None，直接迭代会崩
  - `booking_alerts` 按 `deadline_date` 排序，但 deadline_date 可能为 None
- **修复**: 加 null 检查和排序 fallback

#### 3.8 骨架编排的 pace 表全部硬编码
- **文件**: `app/domains/planning/route_skeleton_builder.py:87-122`
- **问题**: 5 个 pace 相关的常量表（每日容量、交通时间、缓冲时间等）全部硬编码在代码里
- **影响**: 运营无法调参，只能改代码
- **修复**: 移到 config_packs 或 JSON 配置文件

### P2：锦上添花

#### 3.9 entity_temporal_profiles 从未被查询
- **问题**: 表结构完整（season_code/daypart/best_time_window/queue_risk_level/weather_sensitivity），但 planning 代码从未 JOIN 这张表
- **影响**: 季节/时段约束形同虚设
- **修复**: 在 route_skeleton_builder 中查询 temporal profiles 做时段约束

#### 3.10 weather_snapshots / poi_opening_snapshots 从未被查询
- **问题**: 表存在且有 schema，但 plan_b_builder 只用 `poi_category` 判断室内外
- **影响**: Plan B 无法基于真实天气/营业状态触发
- **修复**: 未来接入天气 API 后启用

#### 3.11 page_hero_registry 从未被使用
- **问题**: 表存在但 page_view_model 直接用 selection_evidence 里的 hero_image_url
- **影响**: 无法按页面类型管理封面图
- **修复**: 在渲染层查询 page_hero_registry 作为图片源

---

---

## 优先级总览

| 级别 | 编号 | 任务 | 类型 | 预估工时 |
|------|------|------|------|---------|
| ~~P0~~ | ~~3.1~~ | ~~时间分配用实际时长~~ | ~~消费~~ | ✅ 已完成 |
| ~~P0~~ | ~~1.1~~ | ~~修复轮换双重扣分~~ | ~~结构~~ | ✅ 已完成 |
| ~~P0~~ | ~~3.2~~ | ~~copy_enrichment 用 settings 模型~~ | ~~消费~~ | ✅ 已完成 |
| ~~P0~~ | ~~3.3~~ | ~~预算常量移到配置~~ | ~~消费~~ | ✅ 已完成 |
| ~~P0~~ | ~~3.4~~ | ~~Plan B 用 budget_level 过滤~~ | ~~消费~~ | ✅ 已完成 |
| ~~P0~~ | ~~1.2~~ | ~~加缺失索引~~ | ~~结构~~ | ✅ 已完成 |
| ~~P0~~ | ~~2.1~~ | ~~增强实体校验~~ | ~~采集~~ | ✅ 已完成 |
| ~~P1~~ | ~~3.5~~ | ~~fit scorer 结果写入 metadata~~ | ~~消费~~ | ✅ 已完成 |
| ~~P1~~ | ~~3.6~~ | ~~骨架编排用 best_time_window~~ | ~~消费~~ | ✅ 已完成 |
| ~~P1~~ | ~~3.7~~ | ~~page_view_model null 安全~~ | ~~消费~~ | ✅ 已完成 |
| ~~P1~~ | ~~3.8~~ | ~~pace 表移到配置~~ | ~~消费~~ | ✅ 已完成 |
| ~~P1~~ | ~~1.3~~ | ~~soft_rules 表归属整理~~ | ~~结构~~ | ✅ 已完成 |
| ~~P1~~ | ~~1.4~~ | ~~死表标记 deprecated~~ | ~~结构~~ | ✅ 已完成 |
| ~~P1~~ | ~~2.2~~ | ~~增强去重逻辑~~ | ~~采集~~ | ✅ 已完成 |
| ~~P1~~ | ~~2.3~~ | ~~data_tier 区分来源~~ | ~~采集~~ | ✅ 已完成 |
| ~~P1~~ | ~~2.4~~ | ~~汇率移到配置~~ | ~~采集~~ | ✅ 已完成 |
| ~~P1~~ | ~~2.5~~ | ~~刷新机制改善~~ | ~~采集~~ | ✅ 已完成 |
| ~~P2~~ | ~~1.5~~ | ~~重复字段整理~~ | ~~结构~~ | ✅ 已完成 |
| ~~P2~~ | ~~3.9~~ | ~~启用 temporal_profiles~~ | ~~消费~~ | ✅ 已完成 |
| ~~P2~~ | ~~3.10~~ | ~~接入天气/营业快照~~ | ~~消费~~ | ✅ 已完成 |
| ~~P2~~ | ~~3.11~~ | ~~启用 page_hero_registry~~ | ~~消费~~ | ✅ 已完成 |
