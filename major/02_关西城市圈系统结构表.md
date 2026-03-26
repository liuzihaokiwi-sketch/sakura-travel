> 对齐说明：本文件属于 major 草案目录。边界与优先级冲突时，请以 architecture 真相源为准：
> `docs/architecture/00_scope_and_truth.md`
> `docs/architecture/01_current_state.md`
> `docs/architecture/02_target_architecture.md`
> `docs/architecture/03_gap_and_priorities.md`
> `docs/architecture/04_execution_staging.md`
> 本文件可继续参考，但不单独作为当前阶段最高决策依据。
# 02｜关西城市圈系统结构表

面向：程序 AI / 城市圈建模 / 前端配置层  
目标：把“关西城市圈”固化成可排程、可编辑、可扩展的数据结构。  
默认版本：`kansai_classic_circle_v1`

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
| `circle_id` | `kansai_classic_circle_v1` |
| `name` | 关西经典城市圈 |
| `region` | Kansai |
| `core_bases` | 京都 / 大阪 |
| `daytrip_nodes` | 奈良 / 宇治 / 神户 / 有马温泉 / 姬路 |
| `optional_expansion_nodes` | 高野山 / 琵琶湖西岸 / 贵船鞍马 / 吉野山 |
| `recommended_day_range` | `5~9` 天 |
| `hard_cap_without_expansion` | `8` 天 |

### 1.2 默认策略

| 天数 | 默认住法 | 默认核心 |
|---|---|---|
| 4 天 | 单基点（大阪或京都） | 只跑核心三角：京都 / 奈良 or 大阪 |
| 5–6 天 | 双基点（京都 + 大阪）或单基点强日归 | 京都 + 大阪 + 奈良，择优插入宇治/神户 |
| 7–8 天 | 双基点 | 京都深玩 + 大阪深玩 + 奈良 + 1 个扩展节点 |
| 9 天 | 双基点 + 1 个体验住法可选 | 可纳入有马温泉过夜 / 姬路 / 高野山 |

---

## 2. 基点层

| base_id | 城市 | 角色 | 适合承接 | 不适合承接 | 默认夜数 |
|---|---|---|---|---|---:|
| `kyoto_base` | 京都 | 文化主基点 | 东山、祇园、岚山、伏见稻荷、宇治、贵船鞍马 | 深夜夜生活主线、USJ 全天 | 2–4 |
| `osaka_base` | 大阪 | 都市/交通主基点 | 梅田、难波、USJ、神户、奈良、机场缓冲 | 清晨型京都主线长期承接 | 2–4 |
| `arima_experience_base` | 有马温泉 | 体验型基点 | 温泉酒店、六甲山、神户联动 | 多天城市通勤 | 1 |

### 住法 preset

| preset_id | 说明 | 适用 |
|---|---|---|
| `kansai_1base_osaka` | 全程住大阪 | 4–5 天、首次关西、重交通便利 |
| `kansai_1base_kyoto` | 全程住京都 | 4–5 天、重文化寺社、轻夜生活 |
| `kansai_2base_kyoto_osaka` | 京都 2–3 晚 + 大阪 2–3 晚 | 5–8 天默认方案 |
| `kansai_2base_kyoto_arima` | 京都 + 有马温泉 | 纪念日、疗愈型 |
| `kansai_3base_kyoto_osaka_arima` | 京都 + 大阪 + 有马 | 8–9 天，且温泉酒店本身是主活动 |

---

## 3. 主要活动簇（major activity clusters）

> 主要活动簇是排程主驱动，不等于单个景点。

| cluster_id | 活动簇 | 基点建议 | 时长 | 代表节点 | 默认季节 | 预检风险 | 实时扰动风险 | 默认优先级 |
|---|---|---|---|---|---|---|---|---:|
| `kyoto_higashiyama_gion` | 京都东山祇园线 | 京都 | 半天~1天 | 清水寺、二年坂三年坂、八坂神社、祇园 | 四季 | 低 | 低 | 10 |
| `kyoto_arashiyama_sagano` | 岚山嵯峨野线 | 京都 | 半天~1天 | 天龙寺、竹林、小火车、渡月桥 | 四季 / 秋强 | 中 | 中 | 9 |
| `kyoto_fushimi_inari` | 伏见稻荷时间窗线 | 京都 / 大阪 | 半天 | 伏见稻荷大社 | 四季 | 低 | 低 | 8 |
| `uji_tea_culture` | 宇治茶文化线 | 京都 | 半天~1天 | 平等院、宇治桥、茶店街区 | 四季 / 春秋优 | 低 | 低 | 7 |
| `nara_park_heritage` | 奈良公园古都线 | 京都 / 大阪 | 半天~1天 | 奈良公园、东大寺、春日大社、鹿互动 | 四季 | 低 | 低 | 9 |
| `osaka_urban_food_night` | 大阪都市美食夜游线 | 大阪 | 半天~1天 | 梅田、心斋桥、道顿堀、难波 | 四季 | 低 | 低 | 8 |
| `usj_full_day` | USJ 全天主题公园线 | 大阪 | 1天 | USJ | 四季 / 节假日波动大 | 高 | 中 | 8 |
| `kobe_port_city` | 神户港城异国线 | 大阪 | 半天~1天 | 北野异人馆、港未来、缆车/香草园 | 四季 | 低 | 中 | 6 |
| `arima_onsen_retreat` | 有马温泉疗愈线 | 大阪 / 有马 | 半天~1天 / 过夜 | 金汤银汤、温泉酒店街区 | 四季 / 冬强 | 中 | 低 | 7 |
| `himeji_castle_daytrip` | 姬路城世界遗产线 | 大阪 | 半天~1天 | 姬路城、好古园 | 四季 | 低 | 低 | 6 |
| `kifune_kurama_escape` | 贵船鞍马山林线 | 京都 | 半天~1天 | 贵船神社、鞍马区域 | 夏秋强 | 低 | 中 | 5 |
| `koyasan_retreat` | 高野山宿坊/山寺线 | 大阪 | 1天 / 过夜 | 宿坊、奥之院、高野山 | 四季 | 中 | 中 | 4 |

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
| `gion_evening_walk` | 祇园/先斗町夜走 | 东山祇园 / 京都晚餐 | 20–40 分钟 | 夜景氛围补强 | 是 |
| `kyoto_cafe_matcha` | 京都抹茶甜品/茶屋 | 东山 / 宇治 / 京都市区 | 15–30 分钟 | 休息 + 吃 | 是 |
| `fushimi_sake_area` | 伏见酒街区 | 伏见稻荷 | 20–40 分钟 | 体验差异化 | 是 |
| `osaka_observatory` | 大阪城市夜景点 | 大阪都市夜游 | 20–40 分钟 | 夜景补强 | 是 |
| `shinsaibashi_shopping` | 心斋桥购物段 | 大阪都市夜游 | 20–60 分钟 | 购物 | 是 |
| `nara_mochi_snack` | 奈良小吃甜点 | 奈良公园 | 10–20 分钟 | 快速补能量 | 是 |
| `kobe_beef_meal` | 神户牛目的地餐 | 神户港城 / 有马 | 30–90 分钟 | 高价值正餐 | 否 |
| `onsen_street_walk` | 温泉街散步 | 有马温泉 | 15–30 分钟 | 松弛收尾 | 是 |
| `kyoto_photo_spot` | 单点拍摄位 | 京都各主线 | 10–25 分钟 | 出片 | 是 |
| `station_backup_meal` | 车站附近备胎餐 | 任意主线 | 5–15 分钟 | 执行兜底 | 是 |

---

## 5. 关西圈的活动兼容矩阵

| 主活动 | 最适配次要活动 | 不建议强拼 |
|---|---|---|
| 东山祇园线 | 祇园夜走、茶屋甜品、和服拍摄、轻量会席 | USJ、神户全天 |
| 岚山嵯峨野线 | 河边咖啡、小火车、轻徒步、甜点 | 奈良全天、深夜大阪 |
| 伏见稻荷线 | 伏见酒街区、京都站周边、宇治轻拼 | 神户港城 |
| 宇治茶文化线 | 茶屋、河边慢逛、京都南线 | 大阪夜生活强拼 |
| 奈良古都线 | 小吃、鹿互动、博物馆轻补 | 岚山、USJ |
| 大阪都市美食夜游线 | 购物、夜景、宵夜、短停拍照 | 清晨型京都主线 |
| USJ | CityWalk 补餐、酒店缓冲 | 晚上再跨城跑深活动 |
| 神户港城线 | 神户牛、港区夜景、有马温泉 | 清晨京都高强度 |
| 有马温泉线 | 温泉街散步、轻食、六甲山视天气 | 大量购物/强排队 |

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
| `known_schedule_dependency` | 依赖可提前查到的时间表/营业/维护/预约情况 | USJ、展馆特别展、小火车旺季座位 |
| `day_of_disruption_possible` | 当天可能因天气/交通/限流失效 | 山地、缆车、强户外、铁路依赖高的日归 |
| `backup_same_corridor_required` | 必须绑定同走廊备选 | USJ、贵船鞍马、神户缆车类 |

### 6.3 分类原则

- `known_schedule_dependency=true` 不等于突发风险。  
- 只有“临近或当天才会发生且不能完全提前确认”的情况，才计入 `day_of_disruption_possible=true`。  
- 程序先跑 `precheck_gate` 处理已知风险，再给高 `day_of_disruption_possible` 活动挂 fallback。

---

## 7. 前端编辑所需字段

| 字段 | 用途 |
|---|---|
| `cluster_locked` | 锁定活动簇 |
| `manual_priority` | 前端人工改主次优先级 |
| `manual_base_override` | 强制指定活动归属基点 |
| `manual_duration_override` | 改半天/全天/过夜 |
| `hide_from_user` | 后台保留、前端不展示 |
| `show_as_optional` | 展示为可变活动 |
| `operator_note` | 人工说明 |
| `risk_badge_override` | 人工覆盖风险角标 |

---

## 8. 关西圈默认生成模板

### 4–5 天

- 必选主活动：`东山祇园 / 奈良 or 大阪 / 另一个京都主线`
- 不默认加入：`姬路 / 高野山 / 贵船鞍马`
- USJ 只有在画像命中时加入

### 6–7 天

- 默认 4–5 个主活动簇
- 京都与大阪都应有承接日
- 奈良优先于姬路/高野山
- 宇治、有马、神户三者择一或择二

### 8–9 天

- 可加入体验住法：`有马温泉过夜`
- 可开放 `姬路 / 高野山 / 贵船鞍马` 中的 1 个
- 不建议把所有扩展节点全塞入同一版本

---

## 9. 关西圈落库建议

### 9.1 主表

```ts
interface KansaiCircleRegistry {
  circle_id: string;
  version: string;
  bases: BaseNode[];
  major_clusters: MajorActivityCluster[];
  secondary_clusters: SecondaryActivityCluster[];
  hotel_presets: HotelStrategyPreset[];
  validation_rules: string[];
}
```

### 9.2 最少校验

| 校验 ID | 规则 |
|---|---|
| `KANSAI_001` | 4–5 天版本不允许默认塞入 2 个远扩展节点 |
| `KANSAI_002` | 若 `kyoto_base` 夜数为 0，则东山/岚山主活动总量不应过高 |
| `KANSAI_003` | 若排 `USJ`，当天不得再跨城深玩 |
| `KANSAI_004` | 若排 `arima_onsen_retreat` 为过夜，则次日强度默认下调一级 |
| `KANSAI_005` | 神户/姬路/高野山同时出现时，必须触发圈内过载告警 |
| `KANSAI_006` | 高 `day_of_disruption_possible` 活动至少要有 1 个同走廊 fallback |

---

## 10. 官方建模依据（简记）

- 关西官方经典线路长期以京都、奈良、大阪作为核心三角。  
- 宇治是京都近郊稳定日归点。  
- 神户与有马温泉适合作为大阪/京都辐射的港城/温泉扩展。  
- JR 西日本的关西区域产品与线路信息也支持把京都、大阪、神户、奈良视为可联动建模的一组交通圈。


