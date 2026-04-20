# SCHEMA — 字段唯一权威源

> 最后更新:2026-04-20(从 architecture/SCHEMA.md 搬入并加第一性原理)
> 关联:[DECISIONS.md](../02_历史决策/DECISIONS.md) D28(Opus 装配)/ D29(字段两分法)/ D30(score 0-5 统一)

## ⚠️ 重要:当前是过渡状态,字段会继续演化

2026-04-20 版本的 schema **不是最终版本**,仍在演化中。已知待变动方向:

- **餐厅字段**:当前是按区域(`meal_area`)的简化版本,未来会变得更复杂——可能加菜系维度、场景维度(日常/招待/约会)、季节限定菜、A/B 角色分级等。**当前写的关西模板只用 `meal_area + cuisine_hint` 对齐**,别的字段等真需要再加
- **装配层代码**还没完全实现,很多字段定义仍可能随装配策略调整
- **v1 → v2 过渡中**:文档里提到的旧字段(`role`/`priority`/`fatigue` 等)已废弃,但仍可能在 `_legacy/v1_content/` 的历史模板里出现

**字段变更原则**(D31):
1. 改字段前先在本文件登记
2. 加字段必须有"消费方"——代码真读或表单真填
3. 去字段要扫全仓库 import,避免孤儿字段
4. 过渡期允许字段多版本共存,但必须清晰标注哪个版本活跃

## 文档第一性原理

这份文档回答"**所有结构化字段长什么样、怎么命名、取什么值**"。
- 不回答"字段怎么填好"(看 `04_操作SOP/模板写作.md` / `数据采集.md`)
- 不回答"为什么要这些字段"(看 `02_历史决策/DECISIONS.md`)
- 不回答"代码怎么消费这些字段"(看 `数据流.md` / `业务流.md`)

**字段变动硬规**:任何字段变动**必须先改本文件,再改其他文档**。其他文档(写作指引、地区层文档)只引用本文,不复述定义。

## 契约的精髓(唯一判断锚)

> **字段是"机器和人共读的最小语言"——任何读到这个字段的人或 AI,对它的理解必须完全一致。**

判断一个字段设计得好不好:
- 不同的人/AI 读到同一个字段,会不会产生不同理解?→ 会 = 字段没定义清
- 字段值的取值范围是否明确?(枚举 / 范围 / 正则 / 自然语言)
- 有没有"既可以这样也可以那样"的灰色?→ 灰色 = 字段要重拆
- 字段变了,下游哪些消费方会断?→ 清楚 = 字段有契约;不清楚 = 危险

---

## 0. 通用约定

### 0.1 字段两分法（D29）

所有结构化字段只有两类，其余一律自然语言：

- **客观事实字段**：世界的属性（id / 坐标 / 营业时间 / 价格等），机器和人都精确读
- **表单对应字段**：表单会按它过滤、或用户看得到的展示分类（人群 / 预算档 / 氛围标签等）

不属于这两类的全部写进 `editor_note` / `review` / `story` / `flow detail` 等自然语言字段。

### 0.2 硬字段保留 5 条标准（D29）

一个字段进入硬字段表，必须满足以下至少一条：

1. 表单按它过滤
2. 用户看得到的展示分类
3. 客观事实
4. 硬约束机械判定需要
5. 系统运维需要

### 0.3 通用字段约定

| 字段 | 类型 | 取值 / 格式 | 一句话语义 |
|---|---|---|---|
| `id` | string | snake_case，带城市/圈前缀 | 全局唯一标识，如 `kyo_kiyomizudera` |
| `score` | float | 0.0-5.0，一档对应一分 | 编辑综合评分（D30）：4.0+ S 级 / 3.0-3.9 A / 2.0-2.9 B / 1.0-1.9 C |
| `risk_flags` | string[] | 自由词表 | 风险标签（观光化严重 / 价格陷阱 / 服务差等），表单可放开 |
| `last_verified` | string | YYYY-MM-DD | 最后核验日期 |
| `coordinates` | object | `{lat: float, lng: float}` | 经纬度，必须 Google Maps 验证 |
| `opening_hours` | object | 自定义结构（含定休日） | 营业时间 |
| `seasonal_notes` | object（可选） | `{季节名: 自然语言说明}` | key 自由命名（樱花期/红叶期/夏季等），只有"有季节故事"的实体才填 |

### 0.4 命名规范

- `name_ja` / `name_zh`：日文 / 中文名称双字段。日文汉字不要写成简体。
- `area`：所在区域（对齐模板 area 枚举），用于装配反查

---

## 1. 日模板候选池（day_templates）

> 对应文件：`content/<circle>/<city>/days/` 目录（`_meta.json` + 每个模板一个 `.json`）
> 消费方：`opus_assembler.py` 硬筛 + Opus 最终选择
> 模板里的自然语言内容（description、slot note、editor_note 等）不在本文件定义格式，由写作指引管内容完整性。

### 1.1 模板级硬字段

| 字段 | 类型 | 必填 | 取值 | 一句话语义 |
|---|---|---|---|---|
| `template_id` | string | ✓ | snake_case | 全局唯一标识，如 `arrival_day`、`higashiyama_day` |
| `label` | string | ✓ | - | 人可读的模板名称 |
| `tags` | string[] | ✓ | 受控词表 | 体验标签，用于 skip_tags 过滤（如 `["temple", "walking"]`） |
| `core_entities` | string[] | ✓ | 实体 ID | 核心景点 1-2 个，用于装配跨天去重 |
| `fit_audience` | string \| string[] | ✓ | `"all"` / `["couple", "friends"]` | 适合人群（默认 `"all"`） |
| `weather_sensitive` | bool | ✓ | true/false | 是否依赖晴天（true = 雨天需 Plan B） |
| `condition` | string \| null | - | 自然语言 | 触发条件描述，Opus 读取判断是否适用。常年模板为 null |

### 1.2 assembly 装配元数据

嵌在每个模板内的 `assembly` 对象。`phase` 供 Python 分组，`best_pace` 供 Opus 决策。

| 字段 | 类型 | 必填 | 取值 | 一句话语义 |
|---|---|---|---|---|
| `phase` | string | ✓ | `arrival` / `departure` / `transfer` / `sightseeing` | Python 按此分组候选池，告诉 Opus "这几天从这些里挑" |
| `best_pace` | string | ✓ | `compact` / `standard` / `relaxed` / `locked` | 这个模板在哪种节奏下体验最佳。`locked` = 强度固定无法降级（如 USJ），Opus 会自动让下一天降级补偿 |
| `span_days` | int | 仅多日 | 2+ | 多日模板占几天，Python 检查剩余天数是否足够 |

> **已废弃字段**：`role`（被 `phase` 替代）、`priority`（Opus 从 description 判断）、`fatigue`（被 `best_pace` + P1/P2/P3 slot 体系替代）

### 1.3 slot 时间槽硬字段

模板内 `slots` 数组的每个元素。

| 字段 | 类型 | 必填 | 取值 | 一句话语义 |
|---|---|---|---|---|
| `slot_id` | string | ✓ | snake_case | 槽位标识 |
| `type` | string | ✓ | `poi` / `meal` / `snack` / `transport` / `rest` / `walk` / `shopping` / `cafe` / `evening_auto` / `optional_poi` / `shop_info` / `cafe_info` / `photo_spots` | 槽位类型 |
| `area` | string | 仅 poi/meal | 对齐城市 area 枚举 | 所在区域，用于匹配餐厅/酒店池 |
| `priority` | string | 仅内容槽 | `P1` / `P2` / `P3` | P1=灵魂景点必去，P2=顺路推荐，P3=顺路加项让紧凑节奏饱满。shop_info 槽可用 P5 |
| `duration_min` | int | 仅内容槽 | 分钟 | 建议时长 |

### 1.4 when 触发条件（季节模板用）

| 字段 | 类型 | 必填 | 一句话语义 |
|---|---|---|---|
| `event_ref` | string | 二选一 | 引用 L0 `event_def_id`，由 L0 维护当年窗口 |
| `period_md` | object | 二选一 | `{start: "MM-DD", end: "MM-DD"}`，月日区间，无对应 L0 事件时用 |

---

## 2. 实体（entities）

四类实体共享 §0.3 的通用字段。本节只列各类型独有的硬字段。

### 2.1 景点 attractions（14 字段）

| 字段 | 类型 | 必填 | 取值 | 一句话语义 |
|---|---|---|---|---|
| `id` | string | ✓ | - | 见 §0.3 |
| `name_ja` | string | ✓ | - | 日文名称 |
| `name_zh` | string | ✓ | - | 中文名称 |
| `area` | string | ✓ | 对齐模板 area 枚举 | 所在区域 |
| `score` | float | ✓ | 0-5 | 见 §0.3 |
| `coordinates` | object | ✓ | - | 见 §0.3 |
| `visit_duration_min` | int | ✓ | 分钟 | 建议游览时长，必须搜索验证 |
| `opening_hours` | object | ✓ | - | 见 §0.3 |
| `admission_fee` | object \| null | ✓ | `{adult: int, child: int}`（人民币），搜不到 null | 票价 |
| `booking_required` | bool | ✓ | - | 是否需要预约（参拜预约 / 宿坊预约等） |
| `weather_sensitive` | bool | ✓ | - | 是否怕下雨（户外且雨天体验大幅下降 → true） |
| `fit_audience` | string \| string[] | ✓ | 默认 `"all"` | 适合人群 |
| `risk_flags` | string[] | ✓ | - | 见 §0.3 |
| `last_verified` | string | ✓ | - | 见 §0.3 |

**自然语言字段**：`editor_note`（一句话编辑点评，永远成立）、`review`（三段：亮点 / 怎么玩 / 缺点）、`seasonal_notes`（见 §0.3）

### 2.2 餐厅 restaurants（17 字段）

| 字段 | 类型 | 必填 | 取值 | 一句话语义 |
|---|---|---|---|---|
| `id` | string | ✓ | - | 见 §0.3 |
| `name_ja` | string | ✓ | - | 日文名称 |
| `name_zh` | string | ✓ | - | 中文名称 |
| `area` | string | ✓ | - | 所在区域 |
| `cuisine_tag` | string | ✓ | 受控词表 | 菜系（用于跨城去重 + 表单过滤） |
| `meal_type_fit` | string[] | ✓ | `[breakfast, lunch, dinner, snack]` 子集 | 适合餐次 |
| `budget_tier` | string | ✓ | `economy` / `mid` / `mid_high` / `premium` / `top` | 预算档 |
| `price_cny` | int | ✓ | 人民币 | 人均价 |
| `vibe_tags` | string[] | ✓ | 浪漫 / 热闹 / 安静 / 小众 等 | 氛围标签（表单过滤 + 展示） |
| `facility_tags` | string[] | ✓ | 包间 / 儿童椅 / 无障碍 / 英文菜单 等 | 设施标签（表单过滤） |
| `score` | float | ✓ | 0-5 | 见 §0.3 |
| `ab_role` | string | ✓ | `A_safe` / `B_surprise` | A/B 角色（D29 明确保留，每天展示一对） |
| `meal_role` | string | ✓ | 见 §2.2.1 | 餐次角色（Opus 装配语义提示） |
| `reservation_difficulty` | string | ✓ | `walk_in` / `1week` / `1month` / `2month+` | 预约难度（`2month+` 默认不进推荐池） |
| `opening_hours` | object | ✓ | - | 见 §0.3 |
| `risk_flags` | string[] | ✓ | - | 见 §0.3 |
| `last_verified` | string | ✓ | - | 见 §0.3 |

**自然语言字段**：`editor_note`、`review`（三段：亮点 / 必点必知 / 缺点）

#### 2.2.1 meal_role 取值

| 值 | 含义 |
|---|---|
| `arrival_recovery` | 到达恢复餐，轻松简单 |
| `core_local_experience` | 城市核心名物体验 |
| `showcase` | 全程高光餐（每城最多 1，全程最多 2） |
| `everyday_good` | 日常好餐，稳定输出 |
| `local_life_experience` | 本地生活体验（路边摊/站着吃） |
| `theme_park_recovery` | 主题公园后恢复餐 |

### 2.3 酒店 hotels（14 字段）

| 字段 | 类型 | 必填 | 取值 | 一句话语义 |
|---|---|---|---|---|
| `id` | string | ✓ | - | 见 §0.3 |
| `name_ja` | string | ✓ | - | 日文名称 |
| `name_zh` | string | ✓ | - | 中文名称 |
| `area` | string | ✓ | - | 酒店所在区域（模板 hotel_area 反查这个） |
| `budget_tier` | string | ✓ | `economy` / `mid` / `mid_high` / `premium` / `luxury` | 预算档 |
| `price_range_cny` | object | ✓ | `{min: int, max: int}` | 每晚人均价格区间（人民币） |
| `vibe_tags` | string[] | ✓ | 浪漫 / 传统 / 设计感 / 商务 等 | 氛围标签 |
| `facility_tags` | string[] | ✓ | 温泉 / 早餐 / 儿童友好 / 无障碍 等 | 设施标签 |
| `practical_tags` | string[] | ✓ | 地铁步行 5 分钟 / 免费停车 / 24h 前台 等 | 实用标签 |
| `score` | float | ✓ | 0-5 | 见 §0.3 |
| `checkin` | string | ✓ | `HH:MM` | 标准入住时间 |
| `checkout` | string | ✓ | `HH:MM` | 标准退房时间 |
| `risk_flags` | string[] | ✓ | - | 见 §0.3 |
| `last_verified` | string | ✓ | - | 见 §0.3 |

**自然语言字段**：`editor_note`、`review`（三段：亮点 / 位置房间 / 缺点）

> **2026-04-12 砍掉的字段**：`quality_bias`（性价比/均衡/高品质）、`experience_bias`（普通/强体验）。理由：不是表单过滤维度（用户只问预算档）、不是客观事实、不是展示分类，可完全用 editor_note 表达。装配引擎是 Opus，读 editor_note 比读粗粒度标签更准确。

### 2.4 店铺 shops（10 字段）

| 字段 | 类型 | 必填 | 取值 | 一句话语义 |
|---|---|---|---|---|
| `id` | string | ✓ | - | 见 §0.3 |
| `name_ja` | string | ✓ | - | 日文名称 |
| `name_zh` | string | ✓ | - | 中文名称 |
| `area` | string | ✓ | - | 所在区域 |
| `shop_type_tag` | string | ✓ | 传统工艺 / 二次元 / 服饰 / 古着 / 生活杂货 / 伴手礼 等 | 店铺类型 |
| `vibe_tags` | string[] | ✓ | 小众 / 网红 / 老牌 / 设计感 等 | 氛围标签 |
| `score` | float | ✓ | 0-5 | 见 §0.3 |
| `opening_hours` | object | ✓ | - | 见 §0.3 |
| `risk_flags` | string[] | ✓ | - | 见 §0.3 |
| `last_verified` | string | ✓ | - | 见 §0.3 |

**自然语言字段**：`editor_note`（一段话 2-4 句，店铺不做多段 review）

---

## 3. L0 事实层（events）

### 3.1 event_def 字段

| 字段 | 类型 | 必填 | 一句话语义 |
|---|---|---|---|
| `event_def_id` | string | ✓ | 事件唯一标识，如 `kansai_sakura_daigoji` |
| `usual_window` | object | ✓ | 历史规律窗口，月日格式 |
| `current_year_window` | object | - | 当年预测窗口，由年度更新脚本写入 |

### 3.2 usual_window

| 字段 | 类型 | 一句话语义 |
|---|---|---|
| `start_md` | string | `MM-DD` 起始月日 |
| `end_md` | string | `MM-DD` 结束月日 |

### 3.3 current_year_window

| 字段 | 类型 | 一句话语义 |
|---|---|---|
| `year` | int | 年份 |
| `start` | string | `YYYY-MM-DD` 当年起始 |
| `end` | string | `YYYY-MM-DD` 当年结束 |
| `updated_at` | string | `YYYY-MM-DD` 更新时间 |
| `source` | string | 数据来源（`weathernews` / `jma` 等） |

装配引擎优先用 `current_year_window`，无当年数据时回退 `usual_window`。

---

## 4. 受控词表（enums）

### 4.1 budget_tier

| 餐厅 | 酒店 |
|---|---|
| `economy` | `economy` |
| `mid` | `mid` |
| `mid_high` | `mid_high` |
| `premium` | `premium` |
| `top` | `luxury` |

### 4.2 cuisine_tag（餐厅）

受控词表见 [content/kansai/tag_vocab.json](../content/kansai/tag_vocab.json)。常用值：怀石 / 寿司 / 天妇罗 / 拉面 / 乌冬 / 烧鸟 / 串炸 / 大阪烧 / 居酒屋 / 西餐 / 咖啡 / 和菓子 等。

### 4.3 meal_type_fit / meal_type

`breakfast` / `lunch` / `dinner` / `snack`

### 4.4 reservation_difficulty

| 值 | 说明 |
|---|---|
| `walk_in` | 随时去，无需预约 |
| `1week` | 提前 1 周内可预约 |
| `1month` | 提前 1 个月 |
| `2month+` | 提前 2 个月以上或介绍/会员制（默认不进推荐池） |

### 4.5 fit_audience

`all` / `couple` / `friends` / `family` / `solo` / `elderly` / 自定义子集

### 4.6 ab_role

`A_safe` / `B_surprise`

---

## 5. 字段变更流程（硬规则）

任何字段变动必须按以下顺序执行：

1. **先改本文件 SCHEMA.md**（这是唯一权威源）
2. 再改受影响的写作指引（[templates/CONTENT_POOL_WRITING_GUIDE.md](templates/CONTENT_POOL_WRITING_GUIDE.md)、[templates/TEMPLATE_CREATION_GUIDE.md](templates/TEMPLATE_CREATION_GUIDE.md)）
3. 如有架构层影响，在 [DECISIONS.md](DECISIONS.md) 加新决策号

**禁止反向操作**：不许"先在写作指引里加字段，回头再改 SCHEMA"。这会导致字段定义不一致。

---

## 6. 历史砍掉的字段（D29 + 2026-04-12）

以下字段在装配引擎转 Opus 驱动（D28）后被砍：

**模板**：旧版定义了 `story` / `flow` / `flow.detail` 等自然语言字段的结构。2026-04-12 起不再定义自然语言字段的格式，由写作指引管内容完整性。

**餐厅**：`day_refs` / `season_affinity` / `fallback_for_dedup`

**酒店**：`quality_bias` / `experience_bias` / 多维 ratings

**店铺**：`day_refs`

**全局**：`grade`（被 score 0-5 取代，D30）/ `tag_vocab.json` 强制约束（降级为风格指南）
