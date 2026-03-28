> 对齐说明：本文件属于 major 草案目录。边界与优先级冲突时，请以 architecture 真相源为准：
> `docs/architecture/00_scope_and_truth.md`
> `docs/architecture/01_current_state.md`
> `docs/architecture/02_target_architecture.md`
> `docs/architecture/03_gap_and_priorities.md`
> `docs/architecture/04_execution_staging.md`
> 本文件可继续参考，但不单独作为当前阶段最高决策依据。
# 07｜北疆伊犁赛里木湖圈系统结构表

面向：程序 AI / 城市圈建模 / 前端配置层  
目标：把“北疆伊犁赛里木湖圈”固化成可排程、可编辑、可扩展的数据结构。  
默认版本：`xj_yili_sayram_circle_v1`

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
| `circle_id` | `xj_yili_sayram_circle_v1` |
| `name` | 北疆伊犁赛里木湖圈 |
| `region` | Northern Xinjiang / Ili |
| `core_bases` | 伊宁 / 赛里木湖沿线 / 特克斯 |
| `daytrip_nodes` | 喀拉峻 / 那拉提 |
| `optional_expansion_nodes` | 独库北段 / 伊昭 / 琼库什台 |
| `recommended_day_range` | `6~9` 天 |
| `hard_cap_without_expansion` | `8` 天 |

### 1.2 默认策略

| 天数 | 默认住法 | 默认核心 |
|---|---|---|
| 5 天 | 双基点（伊宁 + 赛湖 or 草原） | 不默认双草原 + 公路线全开 |
| 6–7 天 | 3 基点 | 赛湖 + 1 个草原核心 + 伊宁承接 |
| 8–9 天 | 3–4 基点 | 可开放独库 / 伊昭 / 深草原扩展 |

---

## 2. 基点层

| base_id | 城市 / 片区 | 角色 | 适合承接 | 不适合承接 | 默认夜数 |
|---|---|---|---|---|---:|
| `xj_yining_base` | 伊宁 | 线路承接核心基点 | 首末日、城市缓冲、河谷中转 | 长驻看海量景观 | 1–2 |
| `xj_sayram_base` | 赛湖沿线 | 情绪高点基点 | 日落、环湖、星空 | 高频跨城通勤 | 1 |
| `xj_tekes_base` | 特克斯 / 喀拉峻承接 | 草原核心基点 | 喀拉峻 / 琼库什台 / 伊犁腹地 | 赛里木湖 | 1–2 |
| `xj_nalati_base` | 那拉提 | 草原扩展基点 | 那拉提 / 独库承接 | 伊宁城市线 | 1–2 |

### 住法 preset

| preset_id | 说明 | 适用 |
|---|---|---|
| `xj_2base_yining_sayram` | 伊宁 + 赛湖 | 5–6 天精简版 |
| `xj_3base_yining_sayram_tekes` | 伊宁 + 赛湖 + 特克斯 | 6–7 天默认 |
| `xj_3base_yining_tekes_nalati` | 伊宁 + 特克斯 + 那拉提 | 不重赛湖日落、重草原 |
| `xj_4base_full_ili` | 伊宁 + 赛湖 + 特克斯 + 那拉提 | 8–9 天完整版 |

---

## 3. 主要活动簇（major activity clusters）

| cluster_id | 活动簇 | 基点建议 | 时长 | 代表节点 | 默认季节 | 预检风险 | 实时扰动风险 | 默认优先级 |
|---|---|---|---|---|---|---|---|---:|
| `xj_sayram_ring_lake` | 赛里木湖环湖核心线 | 赛湖 / 博乐 | 0.75~1天 | 赛湖环线、湖岸观景点 | 5–10 月 | 中 | 中 | 10 |
| `xj_yining_valley_buffer` | 伊宁承接线 | 伊宁 | 0.5~0.75天 | 伊宁城市承接 / 河谷休息 | 四季 | 低 | 低 | 6 |
| `xj_kalajun_grassland` | 喀拉峻草原核心线 | 特克斯 | 1天 / 过夜 | 喀拉峻草原 | 夏秋强 | 中 | 中 | 9 |
| `xj_nalati_grassland` | 那拉提草原线 | 那拉提 | 1天 / 过夜 | 那拉提 | 夏秋强 | 中 | 中 | 8 |
| `xj_duku_north_drive` | 独库北段公路线 | 那拉提 / 奎屯向 | 1天 | 独库北段沿线 | 通车季 | 高 | 高 | 8 |
| `xj_yizhao_road` | 伊昭公路线 | 伊宁 / 昭苏向 | 半天~1天 | 伊昭沿线 | 通车季 | 高 | 高 | 7 |
| `xj_qiongkushitai` | 琼库什台深度自然线 | 特克斯 / 琼库什台 | 1天 / 过夜 | 琼库什台 | 夏秋强 | 中 | 中 | 6 |
| `xj_lake_sunset_stargaze` | 湖边日落星空线 | 赛湖 | 半晚 | 赛湖日落 / 星空 | 晴天强 | 中 | 高 | 5 |

---

## 4. 次要活动簇（secondary activity clusters）

| cluster_id | 名称 | 适配主活动 | 绕路预算 | 作用 | 可先砍 |
|---|---|---|---:|---|---|
| `xj_photo_stop` | 沿路拍照停靠位 | 任意景观主线 | 10–25 分钟 | 出片 | 是 |
| `xj_picnic_meal` | 草原 / 湖边轻野餐 | 赛湖 / 草原 | 30–60 分钟 | 氛围补强 | 是 |
| `xj_horse_riding_experience` | 骑马体验 | 草原主线 | 30–120 分钟 | 情绪价值 | 是 |
| `xj_station_backup_meal` | 服务区 / 县城备胎餐 | 任意主线 | 5–15 分钟 | 执行兜底 | 是 |
| `xj_hotel_view_rest` | 景观酒店停留 | 赛湖 / 草原 | 30–120 分钟 | 松弛承接 | 是 |

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
- `known_schedule_dependency`：依赖通车、路况、景区开放状态
- `day_of_disruption_possible`：当天可能因天气 / 风雨 / 限流失效
- `backup_same_corridor_required`：必须挂同走廊备选

---

## 6. 北疆圈默认生成模板

### 6 天
- 必选主活动：`赛里木湖 / 1 个草原核心 / 伊宁承接`
- 独库与伊昭都不默认双开
- 琼库什台不默认加入

### 7 天
- 默认 4–5 个主活动簇
- 可在 `喀拉峻 / 那拉提` 中稳选 1–2 个
- 公路线活动最多放 1 条强线

### 8–9 天
- 可开放 `独库 or 伊昭` + 深草原
- 不建议把 `独库 + 伊昭 + 两大草原` 全塞入同一版本

---

## 7. 北疆圈落库建议

### 7.1 主表

```ts
interface XinjiangYiliRegistry {
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
| `XJ_001` | 6 天版本不允许默认同时塞入喀拉峻、那拉提、独库三强活动 |
| `XJ_002` | 若 `duku_north_drive` 入选，当天不得再叠加深草原重活动 |
| `XJ_003` | 若 `yizhao_road` 或 `duku_north_drive` 失败，必须挂同走廊 fallback |
| `XJ_004` | 若 `sayram_ring_lake` 以日落 / 星空为目标，需检查天气与住宿位置是否匹配 |
| `XJ_005` | 若用户晕车 / 低强度画像，长车程日不得连续排两天 |
| `XJ_006` | 伊宁承接日不能被压缩到纯零价值通勤日，至少保留一个城市缓冲动作 |

