> 对齐说明：本文件属于 major 草案目录。边界与优先级冲突时，请以 architecture 真相源为准：
> `docs/architecture/00_scope_and_truth.md`
> `docs/architecture/01_current_state.md`
> `docs/architecture/02_target_architecture.md`
> `docs/architecture/03_gap_and_priorities.md`
> `docs/architecture/04_execution_staging.md`
> 本文件可继续参考，但不单独作为当前阶段最高决策依据。
# 05｜广佛顺珠广府圈系统结构表

面向：程序 AI / 城市圈建模 / 前端配置层  
目标：把“广佛顺珠广府圈”固化成可排程、可编辑、可扩展的数据结构。  
默认版本：`guangfu_gz_fs_sd_zh_circle_v1`

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
| `circle_id` | `guangfu_gz_fs_sd_zh_circle_v1` |
| `name` | 广佛顺珠广府圈 |
| `region` | Greater Bay / Guangfu |
| `core_bases` | 广州 / 佛山 / 珠海 |
| `daytrip_nodes` | 顺德 / 南海 / 横琴 |
| `optional_expansion_nodes` | 长隆 / 中山 / 开平（后续） |
| `recommended_day_range` | `5~7` 天 |
| `hard_cap_without_expansion` | `6` 天 |

### 1.2 默认策略

| 天数 | 默认住法 | 默认核心 |
|---|---|---|
| 4 天 | 单基点（广州） | 广州 2 天 + 顺德 / 佛山择一 |
| 5–6 天 | 双基点（广州 + 珠海 or 广州 + 佛山） | 广州 + 顺德 + 佛山 / 珠海 |
| 7 天 | 双基点 | 广州 + 顺德 + 佛山 + 珠海 / 长隆 |

---

## 2. 基点层

| base_id | 城市 / 片区 | 角色 | 适合承接 | 不适合承接 | 默认夜数 |
|---|---|---|---|---|---:|
| `gz_oldcity_base` | 广州老城 / 越秀荔湾 | 广府生活核心基点 | 老城、早茶、珠江夜景 | 海滨度假 | 2–4 |
| `gz_tianhe_base` | 广州天河 / 珠江新城 | 都市现代基点 | 广州塔、夜景、现代商圈 | 老城深步行全天 | 1–3 |
| `fs_shunde_food_base` | 顺德 / 佛山 | 美食与岭南文化基点 | 顺德美食、祖庙、岭南天地 | 珠海海边日出型 | 1–2 |
| `zh_coast_base` | 珠海海滨 / 横琴 | 松弛度假基点 | 海边、珠海夜景、横琴 | 广州老城高频往返 | 1–2 |

### 住法 preset

| preset_id | 说明 | 适用 |
|---|---|---|
| `gfz_1base_guangzhou` | 全程住广州 | 首次广府圈、交通最稳 |
| `gfz_2base_gz_zh` | 广州 + 珠海 | 情侣、松弛 + 都市双体验 |
| `gfz_2base_gz_fs` | 广州 + 顺德 / 佛山 | 美食 / 岭南文化重度 |
| `gfz_3base_gz_fs_zh` | 广州 + 顺德 / 佛山 + 珠海 | 6–7 天，且重视节奏切换 |

---

## 3. 主要活动簇（major activity clusters）

| cluster_id | 活动簇 | 基点建议 | 时长 | 代表节点 | 默认季节 | 预检风险 | 实时扰动风险 | 默认优先级 |
|---|---|---|---|---|---|---|---|---:|
| `gzs_old_canton_life` | 广州老城广府生活线 | 广州老城 | 半天~1天 | 永庆坊、上下九、沙面、北京路 | 四季 | 低 | 低 | 10 |
| `gzs_pearl_river_night` | 广州塔—珠江夜景线 | 天河 / 珠江新城 | 半天~0.75天 | 广州塔、珠江、珠江新城 | 四季 | 中 | 低 | 9 |
| `shunde_food_journey` | 顺德世界美食线 | 顺德 / 广州 | 1天 | 清晖园、华盖路、金榜、餐厅节点 | 四季 | 中 | 低 | 10 |
| `foshan_lingnan_kungfu` | 佛山岭南文化功夫线 | 佛山 / 广州 | 0.75~1天 | 祖庙、岭南天地、南风古灶 | 四季 | 低 | 低 | 8 |
| `zhuhai_coast_relax` | 珠海海滨松弛线 | 珠海 | 0.5~1天 | 情侣路、日月贝、海滨公园 | 四季 | 低 | 中 | 7 |
| `gz_chimelong_full_day` | 长隆主题乐园线 | 广州 / 番禺 | 1天 | 长隆园区 | 四季 / 节假日波动大 | 高 | 中 | 8 |
| `zhuhai_hengqin_resort` | 横琴度假扩展线 | 珠海 | 1天 / 过夜 | 横琴 / 海洋王国（条件） | 四季 | 中 | 中 | 6 |
| `shunde_garden_water_town` | 顺德园林水乡慢游线 | 顺德 / 佛山 | 半天 | 清晖园、逢简（择优） | 四季 | 低 | 低 | 5 |

---

## 4. 次要活动簇（secondary activity clusters）

| cluster_id | 名称 | 适配主活动 | 绕路预算 | 作用 | 可先砍 |
|---|---|---|---:|---|---|
| `gfz_dimsum_breakfast` | 老字号早茶 | 广州 / 顺德 | 30–90 分钟 | 仪式感早餐 | 否 |
| `gfz_riverside_walk` | 江边 / 海边散步 | 夜景线 / 珠海线 | 20–40 分钟 | 氛围补强 | 是 |
| `gfz_design_shop` | 买手店 / 文创店 | 老城线 / 佛山线 | 15–40 分钟 | 年轻化补充 | 是 |
| `gfz_cafe_rest` | 咖啡甜品休息 | 任意主线 | 15–30 分钟 | 松弛收尾 | 是 |
| `gfz_food_backup` | 备胎餐 / 备胎茶楼 | 任意主线 | 5–15 分钟 | 执行兜底 | 是 |
| `gfz_family_photo_spot` | 拍照位 | 珠海 / 广州塔 / 老城 | 10–20 分钟 | 出片 | 是 |

---

## 5. 风险标签系统

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

### 语义
- `known_schedule_dependency`：依赖放票 / 开园 / 预约 / 茶楼时段
- `day_of_disruption_possible`：当天可能因天气 / 排队 / 客流失效
- `backup_same_corridor_required`：必须绑定同走廊备选

---

## 6. 广府圈默认生成模板

### 5 天
- 必选主活动：`广州老城 / 顺德美食 / 夜景线`
- 佛山与珠海默认二选一
- 长隆只有画像命中时加入

### 6 天
- 默认 4–5 个主活动簇
- 广州至少承接 2 天
- 顺德优先于横琴 / 中山等进一步扩展

### 7 天
- 可加入珠海过夜或顺德 / 佛山深玩
- 不建议把长隆、珠海、顺德三个高消耗节点全塞满

---

## 7. 广府圈落库建议

### 7.1 主表

```ts
interface GuangfuCircleRegistry {
  circle_id: string;
  version: string;
  bases: BaseNode[];
  major_clusters: MajorActivityCluster[];
  secondary_clusters: SecondaryActivityCluster[];
  hotel_presets: HotelStrategyPreset[];
  validation_rules: string[];
}
```

### 7.2 最少校验

| 校验 ID | 规则 |
|---|---|
| `GFZ_001` | 5 天版本不允许默认同时塞入顺德深吃 + 珠海过夜 + 长隆全天 |
| `GFZ_002` | 若排 `chimelong_full_day`，当天不得再跨城深玩 |
| `GFZ_003` | 若热门餐厅排队风险高，必须挂同走廊备选餐 |
| `GFZ_004` | 若 `zhuhai_coast_relax` 作为降强度日，前一日与后一日不应连续高强度 |
| `GFZ_005` | 若用户画像是“重美食”，顺德优先级应高于珠海 |
| `GFZ_006` | 长辈 / 亲子同行时，跨城频率不得过密，默认最多 1 次跨城大切换 / 天 |

