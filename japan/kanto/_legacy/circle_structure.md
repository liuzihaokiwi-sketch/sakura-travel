> 对齐说明：本文件属于 major 草案目录。边界与优先级冲突时，请以 architecture 真相源为准：
> `docs/architecture/00_scope_and_truth.md`
> `docs/architecture/01_current_state.md`
> `docs/architecture/02_target_architecture.md`
> `docs/architecture/03_gap_and_priorities.md`
> `docs/architecture/04_execution_staging.md`
> 本文件可继续参考，但不单独作为当前阶段最高决策依据。

# 03｜东京城市圈系统结构表

面向：程序 AI / 城市圈建模 / 前端配置层  
目标：把“东京城市圈”固化成可排程、可编辑、可扩展的数据结构。  
默认版本：`tokyo_extended_circle_v1`

---

## 1. 圈定义

```ts
interface CityCircle {
  circle_id: string;
  name: string;
  region: string;
  core_bases: BaseNode[];
  daytrip_nodes: DaytripNode[];
  major_activity_clusters: MajorActivityCluster[];
  secondary_activity_clusters: SecondaryActivityCluster[];
  default_hotel_strategies: HotelStrategyPreset[];
  recommended_day_range: [number, number];
  expansion_rules: ExpansionRule[];
}
```

### 1.1 建议圈边界

| 字段 | 值 |
|---|---|
| `circle_id` | `tokyo_extended_circle_v1` |
| `name` | 东京扩展城市圈 |
| `region` | Kanto |
| `core_bases` | 东京站/银座基点 / 新宿-涩谷基点 / 东京迪士尼基点(条件型) |
| `daytrip_nodes` | 镰仓江之岛 / 横滨 / 箱根 / 河口湖 / 日光 |
| `optional_expansion_nodes` | 轻井泽 / 伊豆热海 / 川越 |
| `recommended_day_range` | `4~9` 天 |
| `hard_cap_without_expansion` | `8` 天 |

### 1.2 默认策略

| 天数 | 默认住法 | 默认核心 |
|---|---|---|
| 3–4 天 | 单基点（东京市区） | 只跑东京核心，不默认塞箱根/河口湖/日光 |
| 5–6 天 | 单基点 + 1 个日归 | 东京核心 + 镰仓/横滨/迪士尼三选一 |
| 7–8 天 | 单基点 + 1~2 个日归，或双基点条件开放 | 东京核心 + 迪士尼 + 镰仓/箱根/河口湖择优 |
| 9 天 | 单基点强扩展或双基点 | 可开放 2 个重日归，或东京+温泉体验住法 |

---

## 2. 基点层

| base_id | 城市/区域 | 角色 | 适合承接 | 不适合承接 | 默认夜数 |
|---|---|---|---|---|---:|
| `tokyo_central_base` | 东京站/银座/日本桥 | 交通+商务主基点 | 银座、浅草、上野、东京站、皇居外苑、机场进出 | 深夜涩谷/新宿连续夜生活 | 2–5 |
| `tokyo_west_base` | 新宿/涩谷 | 都市生活主基点 | 新宿、涩谷、原宿、表参道、下北泽、夜景/夜生活 | 迪士尼清晨、京叶线早出 | 2–5 |
| `maihama_theme_base` | 舞滨 | 条件型体验基点 | 东京迪士尼度假区、极早入园、亲子慢节奏 | 多天跨城通勤 | 1–2 |
| `hakone_experience_base` | 箱根 | 体验型基点 | 温泉酒店、箱根环线、休息收尾 | 连续东京市区通勤 | 1 |

### 住法 preset

| preset_id | 说明 | 适用 |
|---|---|---|
| `tokyo_1base_central` | 全程住东京中部 | 首次东京、重交通效率 |
| `tokyo_1base_west` | 全程住新宿/涩谷 | 重都市氛围、夜生活、年轻化体验 |
| `tokyo_2base_city_maihama` | 东京市区 + 舞滨 | 迪士尼是主活动 |
| `tokyo_2base_city_hakone` | 东京市区 + 箱根 | 温泉酒店是主活动 |
| `tokyo_2base_central_west` | 东京中部 + 西东京 | 8–9 天且东京市内主线很重时开放 |

---

## 3. 主要活动簇（major activity clusters）

| cluster_id | 活动簇 | 基点建议 | 时长 | 代表节点 | 默认季节 | 预检风险 | 实时扰动风险 | 默认优先级 |
|---|---|---|---|---|---|---|---|---:|
| `tokyo_east_classic` | 东京东侧经典线 | 东京中部 | 半天~1天 | 浅草、上野、东京站、银座 | 四季 | 低 | 低 | 10 |
| `tokyo_west_urban` | 东京西侧都市线 | 东京西部 | 半天~1天 | 新宿、涩谷、原宿、表参道 | 四季 | 低 | 低 | 10 |
| `tokyo_disney_full_day` | 东京迪士尼全天线 | 舞滨 / 东京中部 | 1天 | 东京迪士尼乐园/海洋 | 四季 | 高 | 中 | 9 |
| `kamakura_enoshima_daytrip` | 镰仓江之岛海岸古都线 | 东京中部 / 西部 | 1天 | 镰仓大佛、长谷、江之电、江之岛 | 四季 / 春夏强 | 低 | 中 | 9 |
| `yokohama_port_city` | 横滨港城都市线 | 东京中部 / 西部 | 半天~1天 | 红砖仓库、山下公园、中华街、港未来 | 四季 | 低 | 低 | 7 |
| `hakone_onsen_loop` | 箱根温泉山景线 | 箱根 / 东京中部 | 1天 / 过夜 | 箱根汤本、强罗、芦之湖、登山铁道 | 四季 / 秋冬强 | 中 | 中 | 8 |
| `kawaguchiko_fuji_view` | 河口湖富士观景线 | 东京西部 / 东京中部 | 1天 / 过夜 | 河口湖、富士景观点、湖区散步 | 秋冬春强 | 中 | 高 | 8 |
| `nikko_heritage_daytrip` | 日光世界遗产线 | 东京中部 | 1天 | 东照宫、神桥、自然景观 | 四季 / 秋强 | 中 | 中 | 7 |
| `tokyo_seasonal_blossom` | 东京季节花景线 | 东京中部 / 西部 | 半天~1天 | 樱花/银杏/红叶主题公园与河岸 | 春秋强 | 中 | 中 | 6 |
| `luxury_onsen_retreat` | 贵价温泉酒店线 | 箱根 / 河口湖 | 过夜 | 目的地温泉酒店 | 四季 | 中 | 低 | 7 |

### 主要活动簇字段

```ts
interface MajorActivityCluster {
  cluster_id: string;
  title: string;
  base_candidates: string[];
  duration_band: "half_day" | "full_day" | "overnight";
  representative_nodes: string[];
  season_tags: string[];
  reservation_need: "none" | "recommended" | "required";
  precheck_risk: RiskLevel;
  live_disruption_risk: RiskLevel;
  execution_friction: RiskLevel;
  user_condition_risk: RiskLevel;
  secondary_cluster_ids: string[];
}
```

---

## 4. 次要活动簇（secondary activity clusters）

| cluster_id | 名称 | 适配主活动 | 绕路预算 | 作用 | 可先砍 |
|---|---|---|---:|---|---|
| `tokyo_observatory_night` | 都市夜景点 | 东京西侧都市线 / 横滨 | 20–40 分钟 | 夜景补强 | 是 |
| `asakusa_sensoji_evening` | 浅草寺夜走 | 东京东侧经典线 | 15–30 分钟 | 夜景氛围 | 是 |
| `ginza_department_store` | 银座百货/商场 | 东京东侧经典线 | 20–60 分钟 | 购物 | 是 |
| `harajuku_cafe_snack` | 原宿甜品咖啡 | 东京西侧都市线 | 15–30 分钟 | 休息+拍照 | 是 |
| `tokyo_photo_spot` | 单点拍摄位 | 任意东京主线 | 10–25 分钟 | 出片 | 是 |
| `station_backup_meal` | 车站备胎餐 | 任意主线 | 5–15 分钟 | 执行兜底 | 是 |
| `mall_quick_shop` | 车站商场快逛 | 东京/横滨 | 15–30 分钟 | 购物补位 | 是 |
| `onsen_town_walk` | 温泉街散步 | 箱根 / 目的地温泉酒店 | 15–30 分钟 | 松弛收尾 | 是 |
| `beach_cafe_break` | 海边咖啡/甜点 | 镰仓江之岛 | 20–40 分钟 | 氛围与补能量 | 是 |
| `fuji_viewpoint_extra` | 富士单点观景位 | 河口湖富士线 | 20–40 分钟 | 观景补强 | 是 |

---

## 5. 东京圈活动兼容矩阵

| 主活动 | 最适配次要活动 | 不建议强拼 |
|---|---|---|
| 东京东侧经典线 | 浅草夜走、银座购物、备胎餐、单点拍摄 | 迪士尼全天、箱根全天 |
| 东京西侧都市线 | 咖啡甜点、夜景、潮流购物 | 日光全天 |
| 东京迪士尼全天线 | 园区补餐、酒店缓冲、轻量舞滨补位 | 晚上再跨东京强主线 |
| 镰仓江之岛线 | 海边咖啡、江之电拍摄、轻徒步 | 当晚再拼新宿深夜 |
| 横滨港城线 | 中华街目的地餐、夜景、港区慢走 | 清晨日光/箱根 |
| 箱根温泉山景线 | 温泉街散步、轻食、旅馆休息 | 东京市区强购物 |
| 河口湖富士线 | 单点观景、湖边咖啡 | 大量购物、晚间回市区强夜生活 |
| 日光世界遗产线 | 轻量甜点、车站补餐 | 东京夜生活强拼 |

---

## 6. 风险标签系统（给活动簇）

### 6.1 字段

```ts
interface ActivityRiskTags {
  precheck_risk: RiskLevel;
  live_disruption_risk: RiskLevel;
  execution_friction: RiskLevel;
  user_condition_risk: RiskLevel;
  known_schedule_dependency: boolean;
  day_of_disruption_possible: boolean;
  backup_same_corridor_required: boolean;
}
```

### 6.2 语义

| 字段 | 含义 | 例子 |
|---|---|---|
| `known_schedule_dependency` | 依赖可提前查到的运营日历/预约/维护/门票 | 迪士尼、特展、美术馆时间窗 |
| `day_of_disruption_possible` | 当天可能因天气/能见度/交通影响体验或失效 | 河口湖富士观景、箱根强户外、海边日归 |
| `backup_same_corridor_required` | 必须绑定同走廊备选 | 迪士尼、河口湖、箱根 |

### 6.3 分类原则

- `known_schedule_dependency=true` 不等于突发风险。  
- 园区闭园、官方维护、已公布停运、已售罄门票，属于前置可规避风险。  
- 只有“临近或当天才会发生且不能完全提前确认”的情况，才计入 `day_of_disruption_possible=true`。  
- 程序先跑 `precheck_gate`，再给高 `day_of_disruption_possible` 活动挂 fallback。

---

## 7. 前端编辑所需字段

| 字段 | 用途 |
|---|---|
| `cluster_locked` | 锁定活动簇 |
| `manual_priority` | 人工改主次优先级 |
| `manual_base_override` | 强制指定活动归属基点 |
| `manual_duration_override` | 改半天/全天/过夜 |
| `hide_from_user` | 后台保留、前端不展示 |
| `show_as_optional` | 展示为可变活动 |
| `operator_note` | 人工说明 |
| `risk_badge_override` | 人工覆盖风险角标 |

---

## 8. 东京圈默认生成模板

### 4–5 天

- 必选主活动：`东京东侧经典 / 东京西侧都市`
- 画像命中后再加入：`迪士尼 / 镰仓江之岛 / 横滨`
- 不默认加入：`箱根 / 河口湖 / 日光三选二`

### 6–7 天

- 默认 4–5 个主活动簇
- 东京市内应有 2–3 天承接
- 迪士尼与镰仓/箱根/河口湖一般择一或择二
- 河口湖与箱根不默认同版同时开放

### 8–9 天

- 可加入体验住法：`箱根或河口湖过夜`
- 可开放 `日光 / 轻井泽 / 伊豆热海` 中的 1 个
- 不建议把 3 个重日归全部塞入同一版本

---

## 9. 落库建议

```ts
interface TokyoCircleRegistry {
  circle_id: string;
  version: string;
  bases: BaseNode[];
  major_clusters: MajorActivityCluster[];
  secondary_clusters: SecondaryActivityCluster[];
  hotel_presets: HotelStrategyPreset[];
  rules: {
    short_trip_single_circle_only: boolean;
    disney_requires_precheck: boolean;
    fuji_view_requires_weather_fallback: boolean;
    one_heavy_daytrip_per_day_max: boolean;
  };
}
```

---

## 10. 来源锚点（供程序维护）

- JNTO / JR East 口径支持东京为基点辐射镰仓、横滨、箱根、河口湖、日光。
- 镰仓可视为东京日归节点；Hakone 为东京近郊温泉/住宿节点；JR TOKYO Wide Pass 面向东京周边出行。


