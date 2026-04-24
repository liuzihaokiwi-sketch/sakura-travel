# 日模板字段结构与打分体系

> 2026-04-17 讨论产出。承接 [04_city_plugin_rating_v1.md](04_city_plugin_rating_v1.md) 的城市插件评级（决定写哪些城市的模板），本文档定义日模板本身的字段结构和评分方法。
>
> 本文档是**设计共识记录**，不是实施清单。未触及旧文件。

---

## 1. 架构回顾（5 层）

```
第 1 层 路线骨架（5 条）          → 京都/大阪主住宿链
第 2 层 城市插件（04 文档）       → 可挂外出城市，★★★/★★/★ 三档
第 3 层 day template（本文档）    → 住在某城市时的当天内容
第 4 层 seasonal overlay          → 轻量季节微调（只用于"主体稳定+季节加成"类型）
第 5 层 实体填充 + Opus 解释
```

**城市插件评级** 是辅助我们决定"每个季节要写哪些城市的模板"，不是给系统装配用。

---

## 2. 公共池 vs 季节特化

**不是所有模板都按季节拆分。按季节敏感度分三类处理。**

| 类型 | 处理方式 | 典型模板 |
|------|---------|---------|
| A. 季节无关（室内型） | 单个公共模板，全年通用 | 任天堂博物馆、teamLab、USJ、铁道博物馆、水族馆、GEAR 秀、工艺日 |
| B. 主体稳定 + 季节加成 | 公共模板 + 季节 note（轻 overlay） | 金阁寺、二条城、酒蔵巡礼、伏见稻荷、大阪城 |
| C. 强季节依赖（花/叶/祭典主导） | 每季独立完整模板 | 岚山樱花季、岚山红叶季、哲学之道樱花、梅苑日、祇園祭宵山 |

**岚山例子**：
- `arashiyama_day.json`（公共，用于早春/初夏/梅雨/盛夏淡季/初冬/深冬，共 6 季节）
- `arashiyama_sakura_day.json`（樱花季专属）
- `arashiyama_koyo_day.json`（红叶季专属）

---

## 3. 模板字段结构（新版本）

### 3.1 外层字段（完整版）

```json
{
  // 基础元信息
  "template_id": "kyo_kiyomizudera__higashiyama_core",
  "label": "东山精华日",
  "template_kind": "full_day",
  "core_entities": ["kyo_kiyomizudera", "kyo_yasaka_shrine"],
  "weather_sensitive": true,
  "selectable_tag": null,
  "night_options": ["kyo_gear_night", "kyo_pontocho_bar_night"],

  // 打分
  "score": {
    "core_experience": 53,
    "audience_bonus": {"couple": 3, "friends": 2, "family": -3},
    "execution_risk": -2,
    "access_convenience": 5,
    "base_score": 56
  },

  // 内容核心
  "description": "...一段话氛围/day_mood...",
  "design_rationale": "为什么这样排序+为什么选这些点+如果只能保留三个是哪三个",
  "hotel_area_note": "酒店区域到当天关键点的交通(后期对接 3 酒店区域设计)",
  "slots": [ ... ],

  // 峰值与情绪
  "day_peak": {
    "type": "small_peak",            // big_peak / small_peak / null
    "moment": "曹源池方丈前坐下 5 分钟",
    "peak_end_line": "渡月桥畔黄昏, 看水面和远山, 什么都不做"
  },

  // 拍照与逛街(选填,按模板性格判断)
  "photo_spots": [ ... ],
  "nearby_shops": [ ... ],

  // 应急预案(合并了 plan_b_rain + minimum_viable_day + if-then)
  "contingencies": {
    "rain_light": "小雨反而加分, ...",
    "rain_heavy": "大雨天优先调换, 或改去...",
    "crowd": "如果 8:30 到达发现人多, 先进...",
    "minimum_viable": {
      "condition": "身体/时间/天气极端不允许",
      "must_do": "只做渡月桥畔 1 小时",
      "why": "岚山的核心不是竹林也不是天龙寺, 是桂川和远山"
    },
    "swap_candidates": ["nintendo_museum_day", "teamlab_kyoto_day"]
  },

  // 季节特有
  "early_spring_notes": {
    "seasonal_advantage": "...",
    "weather_tip": "...",
    "other_season_specific_info": "..."
  }
}
```

### 3.1.1 新增字段的设计理由

| 字段 | 设计理由 |
|------|---------|
| `design_rationale` | 把"策展思路"独立出来——为什么这样排、如果只能保留三个是哪三个。体现"十个日本专家"的价值 |
| `day_peak` | brief.md §3.5 peak-end rule 要求。大峰值/小峰值+收尾画面 |
| `photo_spots` | 给爱拍照用户。不是每个模板必填——静美型/禅意型模板可以不给机位 |
| `nearby_shops` | brief.md §7 附录信息。按自由时间数量（3h+→5 家，1-2h→3 家，<1h→1-2 家，无→0） |
| `contingencies` | 合并了 plan_b_rain / minimum_viable / if-then crowd。一个字段处理"意外/保底" |
| slot 内可选 `fun_fact` | 合适时才加（有历史典故/影视取景/趣闻传说/冷门礼仪/建筑冷知识）。不是每个 slot 都有。素材库见 [06_fun_facts_library.md](06_fun_facts_library.md) |

### 3.1.2 明确删除的字段（讨论过但最终不加）

| 字段 | 删除理由 |
|------|---------|
| `sensory_moments` | 尬，容易变成"教用户做事"。感官体验应融在 slot note 和 fun_fact 里 |
| `scalable_versions` (半日/全日版本) | 真正需要半日版的模板极少, 到时候拆成独立半日模板即可, 不在通用字段里处理 |

### 3.2 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `template_id` | string | 格式：`{核心实体ID}__{变种名}`。多 core_entities 时取最代表的 |
| `label` | string | 中文模板名 |
| `template_kind` | enum | `full_day` / `night_day` / `night_module` |
| `core_entities` | list | 当天核心实体 ID。用于打分、去重 |
| `weather_sensitive` | bool | 是否受雨天影响 |
| `selectable_tag` | string / null | 只对"能筛"模板有值。对应用户表单勾选项（`usj` / `nintendo` / `teamlab` / `kimono` 等）。用户勾选后人群加分拉满 20 |
| `night_options` | list / 不存在 | 这天结束后顺路可挂的夜间活动模块 ID 列表。为空或无此字段 = 不挂夜活 |
| `score` | object | 评分体系，见 §4 |
| `description` | string | 氛围、day_mood、动线逻辑。**不写结构化字段能表达的信息** |
| `hotel_area_note` | string | 交通说明（后期会改为"住宿 3 个推荐区域 × 到景点路线"） |
| `slots` | list | 当天时间段，见 §3.3 |

### 3.3 slot 结构（精简后）

```json
// 景点(有实体)
{
  "entity": "kyo_kiyomizudera",
  "time": "08:00-10:00",
  "type": "poi",
  "note": "..."
}

// 餐饮(只标区域)
{
  "time": "11:30-12:30",
  "type": "meal",
  "meal_area": "higashiyama_south",
  "featured_meals": [
    {"restaurant_id": "kyo_sakura_kaiseki", "min_budget_tier": "good_enjoy", "reason": "樱花季限定庭院会席"}
  ],
  "note": "..."
}

// 街区散步(可删)
{
  "time": "14:00-15:00",
  "type": "walk",
  "priority": "P2",
  "note": "..."
}

// 自由活动
{
  "time": "20:00-21:30",
  "type": "free",
  "priority": "P2",
  "note": "..."
}
```

### 3.4 slot 字段规则

| 字段 | 说明 |
|------|------|
| `entity` | 有具体实体时填（景点）。同模板内同一天不能重复（防重复的唯一性标识） |
| `time` | `"HH:MM-HH:MM"` |
| `type` | `poi` / `meal` / `walk` / `free` / `info`（原 7 类收敛为 5 类） |
| `priority` | **只在可删减时填**。`P1` = 优先保留，`P2` = 压缩时首选删除。**无此字段 = 必排、不能删**（核心活动、三餐） |
| `meal_area` | 仅 `type=meal` 时有。值对齐细粒度区域代码（见 §5） |
| `featured_meals` | 仅 `type=meal` 时有，可选。特殊餐厅绑定，优先于区域池。`min_budget_tier` 控制触发档位 |
| `note` | 核心文字内容 |

### 3.5 删除的字段

从旧模板中删除：

- `tags`（合并到打分体系）
- `fit_audience`（合并到 audience_bonus）
- `condition`（无实际作用）
- `assembly.phase / assembly.best_pace`（值单一，无分辨力）
- slot 内的 `slot_id`（与 entity 合并）
- slot 内的 `area`（模板层级已有区域概念）
- slot 内的 `duration_min`（与 time 重复）
- slot 内的 `entity_hint`（改名为 entity）

### 3.6 模板类型（`template_kind`）

| 类型 | 含义 |
|------|------|
| `full_day` | 整日模板，绝大多数模板都是这种 |
| `night_day` | 整日模板，白天轻松/空闲、晚上是高光（如舞妓お座敷、GEAR 扩展成一天） |
| `night_module` | 2-3 小时夜间插件，不能独立成一天。挂在其他 full_day 的 night_options 里 |

---

## 4. 打分体系

### 4.1 打分框架

| 维度 | 权重 | 说明 |
|------|------|------|
| 核心体验价值 | 60 | 模板本身的吸引力强度（与季节/人群无关） |
| 人群适配度 | 20 | 用户标签勾选=20（拉满）；否则按人群类型加分 |
| 执行风险 | 5 | 只扣"未对冲"的风险；模板内已预警的风险不扣 |
| 动线/性价比 | 5 | 主要评"离市中心远近"（因为模板本身动线已设计好） |

**默认人群（default）不参与 audience_bonus 计算**——否则默认人群会天生有优势。

### 4.2 核心体验价值（0-60）

拆成 4 个小维度：

| 子维度 | 满分 | 说明 |
|-------|-----|-----|
| 代表性 | 20 | 是不是这个区域/季节最值得专门来一次的体验 |
| 沉浸性 | 20 | 参与感、多感官触发、时间消失感 |
| 记忆性 | 12 | 高光时刻、发朋友圈冲动 |
| 独特性 | 8 | 别处不易替代 |

**打分尺度（总分分布）：**

| 分数 | 定位 | 例子 |
|------|------|------|
| 55-60 | 殿堂级（极少） | 伏见稻荷千本鸟居、东山清水寺（樱花/红叶）、USJ 满员日 |
| 48-54 | 王牌 | 金阁寺日、岚山核心日、任天堂博物馆、teamLab |
| 40-47 | 稳妥优秀 | 二条城+御所、铁道博物馆+水族馆、京都工艺日 |
| 30-39 | 中等良好 | 嵯峨野小火车、伏见酒藏、恢复日 |
| 20-29 | 深度/小众 | 大原深度、奥嵯峨深度、冈崎 |
| 10-19 | 主题/补位 | 特定标签触发才用 |
| < 10 | 异常信号 | 不应存在，需重新审视或删除 |

**每个精选模板应落在 10-60 区间。常见分布在 25-54。低于 10 分表示模板有问题。**

### 4.3 人群适配度（0-20）

**核心理念修正：人群加分反映"人群差异"，不是"模板强度"。**

如果一个模板对所有人群都打高分 → 说明"对谁都好" → 这个属性已在核心体验里体现，不应在人群加分里重复计算。

**正确的人群加分分布：**

| 模板定位 | couple | friends | family | 说明 |
|---------|--------|---------|--------|------|
| 王道经典型（金阁、清水寺） | 0-3 | 0-3 | 0-3 | 大部分 0，普适性已在核心体验 |
| 情侣专属型（情侣东山版） | 18-20 | 0-5 | -3~0 | couple 拉满 |
| 亲子专属型（铁道+水族馆） | 0 | 0-3 | 18-20 | family 拉满 |
| 闺蜜专属型（和服+锦市场） | 0-5 | 18-20 | -3~0 | friends 拉满 |
| 小众深度型（大原、奥嵯峨） | 0-5 | 0-5 | -5~-3 | 普遍低，不硬塞给普通用户 |

**特殊规则：** 当模板有 `selectable_tag` 且用户勾选了对应标签 → 人群加分直接 = 20（覆盖上述规则）。

### 4.4 执行风险（-5 到 0）

**不扣满 5。只扣"未对冲的风险"。**

- 模板 slot note 已写"9 点准时到避开人流" → 拥挤风险已对冲，不扣
- 季节/天气风险无法 100% 规避（雪景靠运气、梅花窗口窄） → 扣 -1 到 -2
- 真正的失败风险（预约制不保证能进） → 扣 -2 到 -3

**原则：好模板应通过内部设计对冲大部分风险，扣分只反映"设计也无法消除的风险"。**

### 4.5 动线/性价比（0-5）

**实际上只评"离市中心远近"**（模板本身换乘/景点聚集已由设计保证）。

| 分 | 范围 |
|----|------|
| 5 | 市中心（东山、四条、二条、祇园） |
| 3-4 | 近郊（岚山、宇治、伏见） |
| 1-2 | 远郊（大原、高雄、鞍马贵船） |

### 4.6 base_score

```
base_score = core_experience + execution_risk + access_convenience
```

**不含人群加分。装配时按用户人群实时加上对应 audience_bonus。**

用户为默认人群 → 总分 = base_score。
用户为情侣 → 总分 = base_score + audience_bonus.couple。
用户勾选了 selectable_tag → 人群加分 = 20（覆盖）。

---

## 5. 餐厅设计

### 5.1 模板只标区域

模板的 meal slot 不直接绑具体餐厅，只标区域（`meal_area`）+ 提示（`note`）。

```json
{
  "time": "11:30-12:30",
  "type": "meal",
  "meal_area": "higashiyama_south",
  "note": "不要在清水参道上吃,往下走到高台寺..."
}
```

### 5.2 区域餐厅池

独立维护**区域池**（`content/kansai/restaurants/{city}.json`）。餐厅自带 `area` 字段，匹配模板 `meal_area`。

### 5.3 细粒度 area 标签

**文件组织粗（按城市）**，**area 字段细（按步行圈 800m-1km）**。

京都细粒度 area 草案（~15 个）：

| area 代码 | 覆盖范围 |
|----------|---------|
| `kyoto_station` | 京都站周边 |
| `higashiyama_south` | 清水寺-高台寺-八坂神社 |
| `gion_pontocho` | 祇园-花见小路-先斗町-木屋町 |
| `kawaramachi_shijo` | 河原町-锦市场-新京极 |
| `karasuma_oike` | 乌丸御池-二条城 |
| `demachiyanagi` | 出町柳-下鸭神社-鸭川三角洲 |
| `okazaki_kyoudai` | 冈崎-平安神宫-京大 |
| `northwest_kinkaku` | 金阁-龙安-仁和-北野 |
| `arashiyama_central` | 渡月桥-天龙寺-竹林 |
| `sagano_north` | 奥嵯峨-祇王寺-大觉寺 |
| `ohara` | 大原 |
| `fushimi` | 伏见稻荷-伏见酒蔵 |
| `uji` | 宇治-平等院 |
| `kurama_kibune` | 鞍马-贵船 |
| `takao` | 高雄 |

### 5.4 餐厅字段结构（精简到 12 个）

```json
{
  "id": "kyo_gion_izuju",
  "name_ja": "いづう",
  "name_zh": "いづう鲭寿司",
  "area": "gion_pontocho",
  "cuisine_tag": "sushi",
  "budget_tier": "mid",
  "price_cny": 250,
  "score": "tabelog:3.68",
  "ab_role": "A_safe",
  "meal_time": ["lunch", "dinner"],
  "seasonal_availability": null,
  "audience_bonus": {
    "couple": 0,
    "friends": 0,
    "family": 0
  },
  "editor_note": "tabelog 3.68 + Michelin Bib Gourmand..."
}
```

### 5.5 餐厅字段说明

| 字段 | 说明 |
|------|------|
| `id` | 唯一 ID |
| `name_ja` / `name_zh` | 日文名（用于在日本找店）+ 中文名 |
| `area` | 细粒度区域代码，匹配模板 meal_area |
| `cuisine_tag` | 菜系（ramen / sushi / kaiseki / katsu / tofu / wagyu / ...） |
| `budget_tier` | **四档**：`economy` / `mid` / `premium` / `luxury`（虽然表单三档，但系统内四档，因为"好好享受"会穿插升级到 ¥500+） |
| `price_cny` | 人均价（CNY） |
| `score` | `tabelog:3.68` 这种格式，数据可信度来源 |
| `ab_role` | `A_safe`（安全牌）/ `B_surprise`（惊喜牌） |
| `meal_time` | `["breakfast", "lunch", "dinner"]` 开放时段。晚上才开的店不能排进午餐 |
| `seasonal_availability` | `["late_autumn", "winter", "early_spring"]` 季节限定。`null` = 全年 |
| `audience_bonus` | 类比景点。大部分店打 0（中立），只给明显适配/不适配的打分 |
| `editor_note` | 推荐理由 + 数据来源（tabelog 评分、米其林标注） |

### 5.6 删掉的旧字段

相比旧餐厅数据：

- `day_refs`（把餐厅硬绑到模板，破坏解耦）
- `meal_role`（混乱：时段+定位+与 ab_role 重复）→ 改为 `meal_time`
- `vibe_tags`（改为 audience_bonus）
- `facility_tags`（全空）
- `review`（全空）
- `fallback_for_dedup`（全空）
- `upgrade_experience`（等价于 budget_tier=luxury）

### 5.7 季节特供放哪

**原则：区域池为主，模板 featured_meals 为补充。**

| 场景 | 放哪 |
|------|------|
| 常规餐厅（全年或长季节） | 区域池（无 seasonal_availability） |
| 区域性季节特色（螃蟹/川床/啤酒花园），多模板共用 | 区域池 + seasonal_availability 标记 |
| 一次性限定（1-3 周窗口，只绑定一个模板） | 模板 featured_meals |

**典型判断：**
- 城崎冬天螃蟹宴 → 区域池 + seasonal（城崎所有冬季模板共用）
- 梅田"かに道楽"螃蟹店 → 区域池 + seasonal
- 岚山樱花季"樱花树下私房会席" → 模板 featured_meals（只为这一个模板服务）

### 5.8 featured_meals 触发规则

```
if 用户预算档位 ≥ featured_meal.min_budget_tier:
    优先用 featured_meals
else:
    回落到区域池匹配
```

---

## 5.9 模板正文的语言规范

**模板正文全中文写作**。专有名词（景区名、寺庙名、店铺名、车站名、日本特有文化词）保留日文原文 + 中文注释。

- 正确："曹源池庭园（曹源池庭园）" / "嵯峨野小火车（トロッコ列車）" / "嵐電嵐山站（岚山电车嵐山站）"
- 正确："北野天満宮（北野天满宫）梅苑"
- 错误：全文混日文（"庭園奥に進むと"这种）
- 错误：强行音译（"Togetsu-kyo"）

**原因：** 用户是中国年轻人，全中文降低阅读门槛；但专有名词保留日文原名是为了用户到日本能在路牌、Google Maps 上对得上。

---

## 6. 产品边界（不在模板池设计范围内）

以下用户场景**不走模板装配**，直接转客服定制：

1. 第二次去关西的用户
2. 奢华游（酒店 ¥3000+/晚、整体预算对应"顶级体验 + 顶级住宿"）
3. 已预定酒店的用户

这些情况下模板池作为"素材库"供客服参考，但不参与自动装配。

**影响：** 旧模板中带 `condition: "budget in ['premium', 'luxury']"` 的应从标准池移除（如舞妓お座敷）。

---

## 7. 装配逻辑摘要

```
用户表单
  → 季节 + 天数
  → 【城市插件评级】决定骨架城市（04 文档）
  → 【日模板评分】在激活的城市×季节池里选（本文档）

装配流程:
  1. 按季节+城市打开模板池(如 early_spring/kyoto 的 22 个模板)
  2. 按用户人群 / 勾选标签 算出每个模板的总分
  3. 按天数需要的 day 数选 top-N 模板
  4. 如用户需要夜生活: 从所选模板的 night_options 挑夜间模块(不重复)
  5. meal slot: featured_meals 优先 → 回落到区域池 按 area/budget/ab_role 匹配
  6. Opus 读模板 description + slot note 做最终自然语言装配和微调
```

---

## 8. 下一步

1. 按本文档字段结构迁移早春京都 22 个模板（新目录，不改旧文件）
2. 逐模板打分（打分本身会反向验证字段结构）
3. 设计 1-2 个区域餐厅池作为样板（如 `higashiyama_south` 或 `gion_pontocho`）
4. 打完早春京都发现的任何设计缺陷，回改本文档
5. 推广到其他季节 × 城市
