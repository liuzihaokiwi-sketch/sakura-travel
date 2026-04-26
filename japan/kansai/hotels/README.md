# 关西酒店数据池

> 跟 `japan/kansai/restaurants/` `japan/kansai/stops/` 平级。
> 字段规范权威 → [`docs/操作SOP/上线前/数据池构建/酒店规范.md`](../../../docs/操作SOP/上线前/数据池构建/酒店规范.md)
> 字段总闸 → [`docs/项目核心/字段权威.md §2.4`](../../../docs/项目核心/字段权威.md)
> tier 阈值表 → [城市档位.md](城市档位.md)

## 现状（2026-04-26·D48 skeleton 全清零完成）

- **总数：206 家**·全部通过 [validate_hotels.py](../../../scripts/validate_hotels.py)·**0 errors**
- **深度**：84 家 full / 122 家 verified·**0 家 skeleton**·全部 cross_checked 或 single_source（无套话占位）
- **基线**：D40 旧池 387 家 → D46 三道筛 201 家 → D47 重构 214 家 → D48 拆分+verify·删 8 家闭店/数据污染/重复 = 206
- **结构**：拆为 28 个 city/area json·与 `restaurants/`、`stops/` 对齐

## D47 重构核心变更

| 维度 | D46（之前） | D47（现在） |
|---|---|---|
| tier 枚举 | `comfort` / `quality` / `luxury` / `top`（4 档·一套阈值） | `b1`-`b6`（6 档·京都 + 关西其他两套阈值）|
| 边界 | 凭手感 300/600/1700/4000 | trip.com 关西/京都站筛选区间·1:1 对齐 |
| 对外用户 | 4 档 | 5 档可选（b1-b5）+ b6 顶奢仅定制启用 |
| 占位 id | 104 家（51%）h*** 占位 | 0 ✅ 全部改 slug |
| 套话简介 | 149 家（5 类批量套话）| 0 ✅ 已全部清扫为「待充实」占位 OR 真实重写 |
| area 错配 | 5 家（高雄/贵船/鹰峯等）| 0 ✅ 全部修正 |

## 6 档对外名

| band | 对外名 | 京都 RMB（平季中位） | 关西其他 RMB | 用户可选 |
|---|---|---|---|---|
| `b1` | 经济 | 0–500 | 0–400 | ✅ |
| `b2` | 舒适 | 500–950 | 400–600 | ✅ |
| `b3` | 品质 | 950–1,200 | 600–850 | ✅ |
| `b4` | 高端 | 1,200–2,000 | 850–1,250 | ✅ |
| `b5` | 奢华 | 2,000–3,500 | 1,250–2,050 | ✅ |
| `b6` | 顶奢 | ≥3,500 | ≥2,050 | ❌·客服定制启用 |

## 城市 × tier 分布

| city | b1 经济 | b2 舒适 | b3 品质 | b4 高端 | b5 奢华 | b6 顶奢 | 合计 |
|---|---|---|---|---|---|---|---|
| 京都 | 0 | 30 | 11 | 33 | 7 | 15 | 96 |
| 大阪 | 0 | 0 | 18 | 1 | 20 | 11 | 50 |
| 神户 | 0 | 0 | 14 | 6 | 8 | 0 | 28 |
| 奈良 | 0 | 0 | 5 | 0 | 6 | 0 | 11 |
| 城崎 | 0 | 0 | 5 | 0 | 2 | 1 | 8 |
| 高野山 | 0 | 10 | 0 | 0 | 0 | 0 | 10 |
| 白浜 | 0 | 0 | 2 | 1 | 0 | 0 | 3 |

**b1 经济档 0 家**——关西真四星地板基本都 ¥400+·b1（关西其他 ¥0-400 / 京都 ¥0-500）只能容纳极少数。trip.com 关西样本里有 Elite Inn 京都站 / Sotetsu Fresa Inn / Smile Hotel·待逐家核实后补。

## type × experience 6 组

| 维度 | 数量 |
|---|---|
| city（便利型）| 79 |
| experience（体验型）| 135 |

**experience 6 组分布**：
- 设计精品 41
- 温泉旅馆 39
- 宿坊 17
- 温泉度假 14
- 町家 12
- 老铺旅馆 12

## D47 重写 / 补收明细

### 套话条目逐家用真数据重写（27 家·full + cross_checked）

第一批（8 家·首批宝藏）：
- 空庭テラス京都 本馆+別邸（trip 9.4/10·994 评论）
- 高雄もみぢ家本館（創業 100 余年·川床發祥）
- 貴船ふじや（川床发祥老舗）
- 料理旅館 右源太（貴船川上流）
- 京都嵐山温泉 花伝抄（共立リゾート·5 个无料贷切风吕）
- FUFU Kyoto / FUFU Nara

第二批（19 家）：
- 京都温泉旅館：京湯元ハトヤ瑞鳳閣·京都梅小路花伝抄·御室花伝抄
- 祇园老铺：柚子屋旅館·料理旅館花楽·純和風料理旅館き乃ゑ·松井本館·天ぷら吉川
- 神户：神戸みなと温泉 蓮（温泉宿総選挙 4 连冠）
- 奈良 5 家：飛鳥荘·古都の宿むさし野·四季亭·遊景の宿平城·春日ホテル
- 白浜 3 家：INFINITO·白良荘·KEY TERRACE Seamore
- 大阪 LIBER（USJ 旁·MUJI room 12 室）

### 补收 15 家应收未收宝藏（全 full + cross_checked）

- **顶奢 b6**：Aman 京都·星のや 京都
- **奢华 b5**：Nazuna 京都 御所·二条城·東本願寺·奈良ホテル·界 城崎·界 有馬
- **高端 b4**：Caption by Hyatt Namba（2025 新）·京の温所 丸太町·葵 KYOTO STAY
- **品质 b3**：Nazuna 京都 椿通
- **舒适 b2**：OMO5 京都祇園·OMO3 京都東寺·Daiwa Roynet 京都四条乌丸（2026.3 重开）

## 待补充工作（next 窗口）

按优先级：

1. **122 verified 升 full**（D48 一轮已用公式源补全 5-7 项 note·下轮可针对性补 cover 图/真实 price 三时段/特定客室 detail）
2. **b1 经济档专项穷举**（trip.com 关西 ¥0-400 4-5 星全榜筛·补 5-15 家）
3. **near_attractions 物理位置精修**（很多家是 area 兜底挂 entity·应按真实物理位置精确挂）
4. **新酒店补漏**（2024-2026 新开业·特别是大阪世博会前后开业的）

## 文件结构

```
japan/kansai/hotels/
├── README.md                         ← 本文（数据池现状+下一步）
├── 城市档位.md                        ← tier 阈值唯一权威源（京都/关西其他两套）
├── _seed_table.md                    ← 6 类种子穷举（D47）
├── _d47_audit.md                     ← D47 重构 audit log
├── _d47_audit_table.md               ← 现池 audit dump
├── kyoto/                            ← 京都 10 个 area json（D48 拆分）
│   ├── arashiyama.json / gion_higashiyama.json / higashiyama.json
│   ├── kibune.json / kita.json / kyoto_station.json / nakagyo.json
│   └── nijo_central.json / shijo_kawaramachi.json / takao.json
├── osaka/                            ← 大阪 6 个 area json
│   └── bay_area / honmachi / namba_dotonbori / shinsaibashi / tennoji_shinsekai / umeda_kita
├── kobe_area/                        ← 神户/有马/姬路（与餐厅 kobe_area 对齐）
│   └── arima / arima_onsen / bay_area / harborland_meriken / kitano_shinkobe / motomachi_nankinmachi / sannomiya
└── other/                            ← 关西其他城市
    ├── nara/nara_park_area.json
    ├── kinosaki/kinosaki_onsen.json + kinosaki.json
    ├── koyasan/koyasan_temple.json
    └── shirahama/shirahama.json
```

D48（2026-04-26）：从单一 `data/hotels__kansai.json` 拆为 28 个按 area 切的 json·与 `japan/kansai/restaurants/`、`japan/kansai/stops/` 结构对齐。

## 历史

- 2026-04-26 **D48 verify 全清零**：118 skeleton 全部用公式源升 verified·删 8 家闭店/数据污染/重复·总 206 家·0 errors（删除 8 家：三井淀屋桥闭店/Vista Premio 闭店/京セラ鹿児島污染/根岸屋/新泉/月明かり/艷郷 3 家城崎污染/la_suite 重复）
- 2026-04-26 **D48 拆分**：单 json → 28 个 city/area.json·对齐餐厅/stops 结构
- 2026-04-26 **D47 重构**：tier 4 档→6 档·trip.com 阈值对齐·套话逐家重写·补收 15 家宝藏·总 214 家·validate 0 errors
- 2026-04-26 D46 首轮迁移：D40 旧池 387 家 → 三道筛 201 家 → 转 D46 schema → 0 errors → 54 家精修 full
- 2026-04-22 D40 ~ D43：旧 5 档 budget_tier·旧池 387 家·已归档到 `_archive/assembly_hotels_legacy_d46/`
