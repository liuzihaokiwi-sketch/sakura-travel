# 09 第二层城市圈差异模块设计补充

## 文档定位

本文件是《第二层改造计划》的补充件，专门回答第二层如何在“统一主链”之上，显式承载“城市圈差异模块”。

这里强调的不是把 planner 拆成 6 套，而是把原本会散落在 `if/else`、seed、权重包、临时规则里的城市圈差异，收束成可维护、可组合、可审计的 policy 模块。

本文件讨论的差异模块，服务于当前新边界：

- 范围不是 Japan-only，而是六城市圈
- 入口优先是抖音表单收单
- 交付重点是 60 页旅行手册
- 第二层必须接受新表单 contract
- 行程按飞机落地后的在地时间计算
- 机票由用户自行预订，我们只做落地后的旅行规划

当前代码里已经存在一些“差异承载雏形”，例如 `city_circles`、`config_resolver`、`seed_all_circles`。但这些能力还没有被组织成完整的“城市圈差异模块体系”。

---

## A. 第二层应该如何设计“统一主链 + 城市圈差异模块”

### 1. 保持统一的部分

这些部分必须继续是一条统一主链，不能按城市圈分叉实现：

- 输入 contract 形状
- 主链阶段顺序
- 决策产物结构
- evidence / explain / decisions 写回方式
- 第三层 handoff 结构

统一主链仍然应是：

`normalize -> circle selection -> constraint compile -> hotel/base strategy -> skeleton building -> secondary fill -> scoring -> explanation`

也就是说，不同城市圈只能改变“参数、阈值、候选过滤、偏好权重、默认组织方式”，不能改变“第二层的基本执行协议”。

### 2. 允许差异化的部分

这些部分允许按城市圈 policy 差异化：

- mobility 假设
- routing 组织方式
- 气候与季节风险
- 预约压力与 booking 习惯
- hotel/base 组织逻辑
- day frame 容量和通勤预算
- 例外处理与 fallback 触发条件

### 3. 如何避免发展成 6 套分叉 planner

核心原则是“统一接口，不统一内容”。

具体做法：

- 不做 `planner_tokyo.py / planner_hokkaido.py / planner_xinjiang.py`
- 只保留一套 `selector / compiler / hotel / skeleton / filler / scorer`
- 每个阶段只读取同一种 `ResolvedPolicySet`
- 城市圈差异以数据模块和策略模块注入，不以代码分叉注入
- 所有模块都返回同样的标准输出结构
- 差异只体现在阈值、候选过滤、模式偏置、风险解释上

第二层真正需要的是：

- `one pipeline`
- `many policy packs`
- `one evidence format`

而不是：

- `many pipelines`

---

## B. 建议新增哪些差异模块

下面这些模块都建议存在，其中前 4 个是必须项。

### 1. `city_circle_profile`

建议存在，且是根模块。

职责：

- 定义一个城市圈的基础画像
- 描述这个圈的核心组织方式
- 指明默认 mobility / routing / season / booking / hotel 偏置
- 作为其他 policy 的装配入口

### 2. `mobility_policy`

建议存在，且必须优先落地。

职责：

- 定义该圈默认交通组织方式
- 定义 transit / driving / charter / walking 的优先级
- 定义可接受通勤时长、跨城频率、最后一晚到机场安全边界

### 3. `climate_and_season_policy`

建议存在，且必须优先落地。

职责：

- 定义季节适配
- 定义天气风险与关闭风险
- 定义雪季、雨季、极端温差、景区关闭等约束
- 定义季节性活动触发与禁入条件

### 4. `routing_style_policy`

建议存在，且必须优先落地。

职责：

- 定义该圈行程更适合“单城深挖 / 放射型日归 / 多基地串联 / 线性公路段”
- 定义 route skeleton 的默认组织方式
- 定义跨日换基地、长距离路段、回头路容忍度

### 5. `booking_and_reservation_policy`

建议存在。

职责：

- 定义该圈 booking pressure 的默认假设
- 定义高预约压力项目的提前量
- 定义哪些内容若未预约只可降级、不应硬排
- 定义 booking alert 生成口径

### 6. `hotel_base_policy`

建议存在。

职责：

- 定义该圈 hotel/base strategy 的默认模式
- 定义“单基地优先 / 多基地可接受 / 最后一晚必须近机场 / 自驾优先住交通节点外”
- 定义住宿点与 main corridor 的耦合方式

### 7. `day_frame_policy`

建议存在。

职责：

- 定义不同 day type 的容量和通勤预算
- 定义 arrival / departure / theme_park / road_trip / snow_day 的日框架
- 定义该圈“满一天”到底意味着多少有效活动分钟

### 8. `exception_policy`

建议存在，但可后上。

职责：

- 定义例外触发器
- 定义何时 needs_review
- 定义何时 fallback 到兼容层
- 定义城市圈特有异常的处理方式，例如封山、停运、雪关闭、长途段断裂

---

## C. 每个模块分别承载什么差异

### 1. 东京 / 关东：公共交通优先

建议差异：

- `mobility_policy`
  默认 `primary_mode = public_transit`
  `walking + rail` 为主
  对跨城通勤可容忍，但应压低长距离地面转移
- `routing_style_policy`
  更适合“单城核心 + 个别日归”
  日内换区可多，但不应频繁跨远郊
- `booking_and_reservation_policy`
  热门展览、餐厅、观景台、主题项目预约压力高
- `day_frame_policy`
  可以接受较高的日内公共交通切换，但总步行预算应可控

### 2. 北海道：雪季、冬季路况、道路关闭、季节性活动

建议差异：

- `climate_and_season_policy`
  冬季必须显式影响可行性，不只是 season score
  需要支持 `snow_season`, `road_closure_risk`, `short_daylight`, `weather_buffer`
- `mobility_policy`
  冬季公共交通 / 自驾可用性不能按常规圈假设
  需要区分“札幌城市内”和“富良野/美瑛/二世谷”这种跨区段
- `routing_style_policy`
  低密度景点之间不能沿用东京式碎片排法
  更偏“块状组织 + 长段转移”
- `exception_policy`
  雪关闭、道路不可通行、冬季设施停开时，必须触发 review 或替代路线

### 3. 北疆：自驾 / 包车、长距离路段、低密度景点组织

建议差异：

- `mobility_policy`
  默认不应假设 public transit first
  应支持 `self_drive` / `charter` 为主模式
- `routing_style_policy`
  应显式支持“长距离路段日”“景点低密度串联”“住宿点跟随路段推进”
- `hotel_base_policy`
  酒店基地应更多服从路段分段，而不是热门核心区住宿偏好
- `day_frame_policy`
  需要把大段驾驶时间计入 day frame，而不是只算景点游玩时间
- `exception_policy`
  对封路、天气、季节性开放窗口更敏感

### 4. 日本城市圈 vs 中国城市圈：基础交通与组织方式差异

建议差异：

- 日本城市圈
  更常见 `public_transit + walking`
  精细到站点和时窗的组织价值更高
  景点和餐饮预约压力结构更稳定
- 中国城市圈
  更可能 `taxi/网约车/自驾/包车` 混合
  城市间转移和城市内通行的时间分布不同
  “核心城市圈 + 郊野长段”组合更常见
- 这类差异不应直接写死在 `if circle_id in japan_circles`
  应通过 `mobility_policy.region_family` 和 `routing_style_policy.pattern_family` 注入

---

## D. 这些差异模块应该在第二层主链的哪个阶段被读取

### 1. `normalize`

读取：

- `city_circle_profile`
- `mobility_policy`
- `climate_and_season_policy`

作用：

- 把原始表单输入标准化成统一 Layer 2 input
- 生成初始 `travel_mode_assumption`
- 生成 `season_context`
- 生成 `routing_family_hint`

### 2. `circle selection`

读取：

- `city_circle_profile`
- `mobility_policy`
- `climate_and_season_policy`

作用：

- 决定用户指定圈是否合法
- 若用户目标圈与真实时间/机场/模式冲突，给出 explain
- 不是重新自由选圈，而是“校验目标圈 + 补差异信号”

### 3. `constraint compile`

读取：

- `mobility_policy`
- `climate_and_season_policy`
- `booking_and_reservation_policy`
- `exception_policy`

作用：

- 产出 hard/soft constraints
- 产出 season block
- 产出 road/closure risk constraint
- 产出 booking required / booking preferred constraint
- 产出长距离路段限制

### 4. `hotel/base strategy`

读取：

- `hotel_base_policy`
- `mobility_policy`
- `routing_style_policy`

作用：

- 决定单基地还是多基地
- 决定最后一晚是否必须贴机场/交通枢纽
- 决定自驾圈是否优先住“路段节点”而非传统热门区

### 5. `skeleton building`

读取：

- `day_frame_policy`
- `routing_style_policy`
- `mobility_policy`

作用：

- 决定 day type 容量
- 决定 transit budget
- 决定 road trip day / snow day / urban transit day 的骨架差异
- 决定 main driver 的分布方式

### 6. `secondary fill`

读取：

- `day_frame_policy`
- `routing_style_policy`
- `booking_and_reservation_policy`

作用：

- 决定一个主活动周围还能挂多少 secondary
- 决定低密度圈是否减少碎片化补点
- 决定高预约压力内容不应临时硬塞

### 7. `scoring`

读取：

- `mobility_policy`
- `climate_and_season_policy`
- `routing_style_policy`
- `booking_and_reservation_policy`

作用：

- 调整 transit / detour / queue / weather / closure / booking penalties
- 同样的候选项在不同圈不应使用同一套罚分函数

### 8. `explanation`

读取：

- 全部 policy 的摘要版

作用：

- 给第三层的 explain/evidence 提供“为什么这样排”
- 让解释不是通用空话，而是“因为该城市圈在冬季/自驾/预约/低密度组织上有特定策略”

---

## E. 建议的数据结构

建议不要把每个 policy 拆成完全独立的数据库表再互相 join。第一阶段更适合：

- 一个默认策略集 `default_policy_bundle`
- 多个城市圈覆盖项 `circle_policy_overrides`
- 季节覆盖项 `season_policy_overrides`
- 运行时合并成一个 `ResolvedPolicySet`

### 1. 建议的运行时结构

```yaml
ResolvedPolicySet:
  policy_version: "v1"
  circle_id: "hokkaido_city_circle"
  season_key: "winter"
  region_family: "japan"
  modules:
    city_circle_profile: {}
    mobility_policy: {}
    climate_and_season_policy: {}
    routing_style_policy: {}
    booking_and_reservation_policy: {}
    hotel_base_policy: {}
    day_frame_policy: {}
    exception_policy: {}
  sources:
    - default
    - circle:hokkaido_city_circle
    - season:winter
```

### 2. `city_circle_profile`

核心字段：

```yaml
city_circle_profile:
  circle_id: ""
  region_family: "japan"
  destination_family: "urban_multi_base"
  primary_planning_unit: "city_circle"
  default_user_selected_scope: true
  default_transport_mode_hint: "public_transit"
  default_route_pattern: "hub_and_spoke"
  default_hotel_pattern: "single_or_dual_base"
```

默认值：

- `region_family = general`
- `default_transport_mode_hint = mixed`
- `default_route_pattern = compact_multi_day`
- `default_hotel_pattern = single_base`

城市圈覆盖项：

- 东京可覆盖为 `urban_transit_dense`
- 北海道可覆盖为 `regional_sparse`
- 北疆可覆盖为 `road_trip_sparse`

### 3. `mobility_policy`

核心字段：

```yaml
mobility_policy:
  primary_mode: "public_transit"
  allowed_modes: ["public_transit", "walk", "taxi"]
  transit_budget_minutes_normal_day: 120
  transit_budget_minutes_arrival_day: 60
  max_cross_city_transfer_minutes: 150
  last_night_airport_safe_buffer_minutes: 180
  long_distance_segment_threshold_minutes: 180
  self_drive_supported: false
  charter_supported: false
```

默认值：

- `primary_mode = mixed`
- `allowed_modes = [walk, public_transit, taxi]`
- `self_drive_supported = false`
- `charter_supported = false`

城市圈覆盖项：

- 关东：`primary_mode = public_transit`
- 北海道：冬季可把 `max_cross_city_transfer_minutes` 下调，`self_drive_supported = conditional`
- 北疆：`primary_mode = self_drive_or_charter`，`allowed_modes = [self_drive, charter]`

### 4. `climate_and_season_policy`

核心字段：

```yaml
climate_and_season_policy:
  season_sensitivity: "medium"
  weather_buffer_minutes: 30
  closure_risk_enabled: true
  road_closure_risk_enabled: false
  daylight_adjustment_enabled: false
  winter_mode_enabled: false
  seasonal_activity_required: false
  blocked_months: []
  high_risk_months: []
  trigger_tags_by_month: {}
```

默认值：

- `season_sensitivity = low`
- `weather_buffer_minutes = 20`
- `closure_risk_enabled = true`
- `road_closure_risk_enabled = false`

城市圈覆盖项：

- 北海道冬季：`winter_mode_enabled = true`
- 北海道冬季：`road_closure_risk_enabled = true`
- 北海道冬季：`daylight_adjustment_enabled = true`
- 北疆肩季/冬季：同样提高 `road_closure_risk_enabled`

季节覆盖项：

```yaml
season_override:
  winter:
    weather_buffer_minutes: 60
    road_closure_risk_enabled: true
    daylight_adjustment_enabled: true
```

### 5. `routing_style_policy`

核心字段：

```yaml
routing_style_policy:
  route_pattern: "hub_and_spoke"
  prefer_single_city_depth: false
  prefer_linear_progression: false
  allow_multi_base: true
  allow_daytrip_expansion: true
  max_daytrip_frequency: 2
  max_backtrack_penalty: 1.0
  sparse_poi_mode: false
```

默认值：

- `route_pattern = compact_multi_day`
- `allow_multi_base = false`
- `allow_daytrip_expansion = true`
- `sparse_poi_mode = false`

城市圈覆盖项：

- 东京/关东：`route_pattern = hub_and_spoke`
- 北海道：`route_pattern = regional_block`
- 北疆：`route_pattern = linear_road_trip`
- 北疆：`prefer_linear_progression = true`
- 北疆：`sparse_poi_mode = true`

### 6. `booking_and_reservation_policy`

核心字段：

```yaml
booking_and_reservation_policy:
  reservation_pressure_default: "medium"
  booking_alert_enabled: true
  hard_block_if_unreserved_types: []
  advance_booking_days_default: 7
  queue_penalty_multiplier: 1.0
  reservation_penalty_multiplier: 1.0
  walk_in_fallback_allowed: true
```

默认值：

- `reservation_pressure_default = low`
- `advance_booking_days_default = 3`
- `walk_in_fallback_allowed = true`

城市圈覆盖项：

- 东京热门项目可提高 `reservation_penalty_multiplier`
- 北海道冬季活动可提高 `advance_booking_days_default`
- 北疆包车 / 自驾资源可设 `hard_block_if_unreserved_types = [charter, permit_required]`

### 7. `hotel_base_policy`

核心字段：

```yaml
hotel_base_policy:
  hotel_pattern: "single_base"
  max_switches_default: 1
  require_last_night_transport_safety: true
  prefer_transport_hub_area: true
  prefer_scenic_stay: false
  drive_trip_lodging_bias: false
  lock_hotel_to_route_progression: false
```

默认值：

- `hotel_pattern = single_base`
- `max_switches_default = 1`
- `prefer_transport_hub_area = true`

城市圈覆盖项：

- 东京：更偏 `single_base`
- 北海道：可为 `dual_base_or_route_based`
- 北疆：`drive_trip_lodging_bias = true`
- 北疆：`lock_hotel_to_route_progression = true`

### 8. `day_frame_policy`

核心字段：

```yaml
day_frame_policy:
  normal_day_capacity_minutes: 480
  arrival_day_capacity_minutes: 240
  departure_day_capacity_minutes: 180
  long_distance_day_capacity_minutes: 240
  snow_day_capacity_minutes: 300
  normal_day_transit_minutes: 120
  long_distance_day_transit_minutes: 240
  sparse_area_secondary_limit: 1
```

默认值：

- 保持当前 skeleton 的一般值
- `long_distance_day_capacity_minutes` 可以默认等于 `normal_day_capacity_minutes`

城市圈覆盖项：

- 东京：normal day 可接受较高 transit budget
- 北海道冬季：`snow_day_capacity_minutes` 下调
- 北疆：`long_distance_day_transit_minutes` 上调，`sparse_area_secondary_limit` 下调

### 9. `exception_policy`

核心字段：

```yaml
exception_policy:
  review_on_road_closure_risk: true
  review_on_weather_uncertainty: false
  review_on_missing_booking_for_high_pressure: true
  fallback_on_low_density_match: false
  fallback_on_transport_conflict: true
  block_generation_on_hard_conflict: true
```

默认值：

- `review_on_road_closure_risk = false`
- `fallback_on_transport_conflict = true`
- `block_generation_on_hard_conflict = true`

城市圈覆盖项：

- 北海道冬季提高 review 触发
- 北疆长距离段提高 transport conflict review 触发

### 10. 运行时如何合并

建议合并顺序固定为：

`default -> region_family -> circle -> season -> plan_override`

合并规则：

- 标量字段：后者覆盖前者
- 数值字段：后者覆盖前者，不做平均
- 列表字段：默认用“覆盖”而不是“拼接”
- 风险开关：以后者为准
- explain 中要保留 `sources`

这样可以继续复用现有配置解析器的思路，但把目前偏“weights/thresholds/switches”的配置中心扩展为 policy bundle 解析。

---

## F. 实施顺序

### Phase 1：必须先上

- `city_circle_profile`
- `mobility_policy`
- `climate_and_season_policy`
- `routing_style_policy`

原因：

- 这四个模块直接决定第二层是否还在用 Japan-only 的通用 mobility/routing 假设
- 不先上它们，北海道和北疆都会被错误地塞进“城市公共交通 + 紧凑排程”模型

### Phase 2：紧接着上

- `hotel_base_policy`
- `day_frame_policy`
- `booking_and_reservation_policy`

原因：

- 这三者会直接影响 `hotel/base strategy`、`skeleton`、`secondary fill`
- 但它们依赖 Phase 1 已经提供的 route pattern 和 mobility 假设

### Phase 3：可以后上

- `exception_policy`

原因：

- 它很重要，但前提是前面几个 policy 已经能稳定产出“风险语义”
- 否则 exception 只会变成新的散乱 if/else

### 未来增强项

- region_family 级别的中日差异包
- 季节分区 policy，不只 winter/summer，而是圈内季节子区
- 组织方式切换 policy，例如同一城市圈下 `public_transit_mode` 与 `self_drive_mode`
- 可解释性模板，让第三层直接消费 policy explain

---

## 最先该落地的 3 个差异模块

1. `mobility_policy`
原因：它决定东京/北海道/北疆会不会被误用同一套交通组织假设。

2. `climate_and_season_policy`
原因：北海道冬季、北疆长段、季节活动窗口，都不能继续只靠弱 season score 处理。

3. `routing_style_policy`
原因：这是避免“所有城市圈都被排成同一种紧凑城市游”的关键模块，也是避免分叉成 6 套 planner 的核心抽象。
