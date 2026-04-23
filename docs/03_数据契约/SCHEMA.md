# SCHEMA — 字段唯一权威源

> 最后更新：2026-04-22（D37 修订：slots 改时间段+main+optional、模板目录按动线重组）
> 关联：[DECISIONS.md](../02_历史决策/DECISIONS.md) D36（字段大瘦身）+ D37（目录重组 + slots 重构）

## ⚠️ 设计宪法（最高原则，永久有效）

### 第一条：能用自然语言文字的，绝不用字段

**字段的唯一意义**：
1. **给系统看**（代码/装配 AI 要按它做硬判断、硬筛、硬分组）
2. **确定的等级或标签**（P1/P2/P3、budget_tier、selectable_tag、category 等枚举值）

任何"看起来像信息但本质是描述/解释/判断说明"的内容 → **写自然语言段落，不要做字段**。

→ 推论：宁可写一段长文字（甚至带子标题），也不为每种小信息单独立字段。AI 读自然语言比读嵌套字段更自然。

### 第二条：内容归属对象，谁的事谁解决

| 问题层级 | 解决在哪 |
|---|---|
| 跟具体景点相关（拍照/冷知识/周边小店/动线衔接 tip/避坑） | **景点对象本身**（事实层 entity 的 notes） |
| 跟具体餐厅相关（菜系/A-B 角色/价格/avoid） | **餐厅对象本身** |
| 跟具体酒店相关（位置/特色/适配） | **酒店对象本身** |
| 装配规则（打分/天数门槛/A-B 双推/跨城去重/人群升降/酒店升档） | **对应的装配 markdown** |
| 真正需要"模板设计"才能解决的（动线顺序/peak-end 编排/三档怎么砍/整天思路） | **模板自己** |

→ 推论：模板瘦身的判断标准不是"字段越少越好"，而是"**这件事是不是只能在模板这一层解决**？"

### 字段扩展硬规

**禁止随意扩展字段。**任何想加字段，先回答这 3 个问题：

1. **消费方是谁？** —— 渲染代码 / AI 装配 / 写作者本人。说不出消费方 = 不要加。
2. **能不能用现有字段或自然语言段落表达？** —— 能用 `note` / `description` / `notes` 等承载的，不要加新字段。
3. **是不是装配层的事？** —— 跟"用户档位/天数/人群/A-B 餐厅/酒店升档"相关的全部不进模板和事实层，去 [assembly/](../../japan/kansai/assembly/) markdown 写。

**触发任何字段变更必须先改本文件再改其他文档。**

### 三层文件格式分工

| 层 | 文件 | 格式 | 消费方 |
|---|---|---|---|
| 模板 | `templates/**/*.json` | JSON | 渲染代码（生成手账本布局）+ AI 装配读 slot |
| 景点（事实层） | `entities/{kyoto,osaka,other}.json` | JSON | 渲染代码（取门票/坐标/开门）+ AI 装配硬筛 |
| 装配规则 | `assembly/{templates,restaurants,hotels}/*.md` | **Markdown** | AI 装配读（不是机械查表） |
| 装配数据 | `assembly/{templates,restaurants,hotels}/data/*.json` | JSON | 装配 AI 按规则消费（餐厅池/酒店池/季节窗口） |

**为什么装配/事件用 markdown**：消费方主要是 AI，markdown 让 AI 像读 SOP 一样读，比 JSON 嵌套自然。

---

## 文档第一性原理

这份文档回答"**所有结构化字段长什么样、怎么命名、取什么值**"。
- 不回答"字段怎么填好"（看 [模板写作.md](../04_操作SOP/模板写作.md) / [数据采集.md](../04_操作SOP/数据采集.md)）
- 不回答"为什么要这些字段"（看 [DECISIONS.md](../02_历史决策/DECISIONS.md) D36）
- 不回答"装配怎么挑餐厅/酒店"（看 [assembly/](../../japan/kansai/assembly/) markdown）

## 契约的精髓

> **字段是"机器和人共读的最小语言"——任何读到这个字段的人或 AI，对它的理解必须完全一致。**

判断字段设计好坏：
- 不同的人/AI 读到同一个字段，会不会产生不同理解？→ 会 = 字段没定义清
- 字段值的取值范围是否明确？（枚举 / 范围 / 正则 / 自然语言）
- 有没有"既可以这样也可以那样"的灰色？→ 灰色 = 字段要重拆
- 字段变了，下游哪些消费方会断？→ 清楚 = 字段有契约

---

## 1. 模板字段（templates/**/*.json）

### 1.0 目录组织（D37）

模板按城市/动线重组：

```
japan/kansai/templates/
├── kyoto/
│   ├── arashiyama/            动线（一日和两日变体统一编号，不分子层）
│   │   ├── index.md           变体清单，标明每个编号是几日+主题
│   │   ├── transport.md       该动线交通清单
│   │   ├── 1.json             一日核心
│   │   ├── 2.json             两日温泉
│   │   ├── 3.json             两日红叶深度
│   │   └── night.json         可选夜晚模块（一文件含多选项）
│   ├── higashiyama/           清水+东山+祇园
│   ├── kitayama/              金阁+龙安寺+北野+平野（合并）
│   ├── okazaki_tetsugaku/     南禅寺+哲学之道+瑠璃光院（合并）
│   ├── kurama_kibune/         鞍马+贵船（合并）
│   ├── fushimi/
│   ├── takao/                 高雄（一日+两日统一编号）
│   ├── nijo/
│   ├── uji/                   宇治+任天堂博物馆
│   └── half_day/              京都半日池
├── osaka/{expo, kaiyukan, nakazakicho, namba, osakajo, tennoji, usj, half_day}/
├── other/{arima, kinosaki, kobe, koyasan, nara, yoshino, half_day}/
├── arrivals/                  到达日
├── departures/                离开日
├── special_dates/             时间敏感型（大文字/节分/祇园祭/天神祭/琵琶湖花火/通し矢/初诣/特别公开 等）
│                               里面每个文件是独立模板，不做变体互斥；装配按当年日期匹配才能装
└── niche_spots/               孤立小众景点（铁道博物馆/醍醐寺/三千院/深冬雪景 等）
                               里面每个文件是独立模板，不做变体互斥；全年/季节窗口可装
```

**硬规**：
- 文件命名 `1.json` / `2.json`（数字编号连续）/ `night.json`（夜晚单文件）
- 动线文件夹不带城市前缀（父目录已表达）
- **同动线文件夹内变体互斥**：装配每个动线文件夹最多选 1 个变体
- **一日和两日统一编号，不分子层**。index.md 标明每个编号是几日
- **special_events/ 例外**：里面每个 JSON 是独立模板，不在变体互斥范围内

### 1.1 顶层必填（7 个）

| 字段 | 类型 | 取值 | 一句话语义 |
|---|---|---|---|
| `template_id` | string | snake_case | 全局唯一标识，如 `kyoto_arashiyama_1` |
| `label` | string | - | 人可读名称，如 "岚山核心一日" |
| `variant_label` | string | - | 变体自描述（如 "红叶版+情侣" / "核心一日" / "温泉一泊"），与文件名数字编号互补 |
| `applicable_dates` | array | 见 §1.2 | 适用时间列表；常年模板默认 `[]` |
| `note` | string | 自然语言 | **设计 note（不展示）**：整天为什么这样排——路线/体验/情绪/旺季应对 |
| `description` | string | 自然语言 | 用户总览（含钩子）：对 note 的面向用户提炼 |
| `slots` | array | 见 §1.4 | 时间段+main+optional 结构 |

> **`selectable_tag` 已挪装配层**（D36）：用户勾选入口由 [assembly/templates/index.md](../../japan/kansai/assembly/templates/index.md) 维护。
> **`template_kind` 已砍**（D37）：类型由文件夹位置表达（`half_day/` 下的是半日、`arrivals/` 下是到达日）。
> **`night_options` 已砍**（D37）：夜晚模块跟动线文件夹绑定（同文件夹有 `night.json` 才能挂）。

### 1.2 applicable_dates 元素

**格式**：一个时间区间对象，`MM-DD` 月日，**不写年**。

| 字段 | 类型 | 必填 | 一句话语义 |
|---|---|---|---|
| `start` | string | ✓ | `MM-DD` 起始月日 |
| `end` | string | ✓ | `MM-DD` 结束月日（单日祭典 start = end） |
| `label` | string | ✓ | 人可读说明，如 "山鉾巡行" / "红叶最佳期" / "梅花季" |

**取值示例**：
- 单日祭典（祇园祭山鉾巡行 7/17）：`[{"start": "07-17", "end": "07-17", "label": "山鉾巡行"}]`
- 窗口期（红叶 11/15-12/5）：`[{"start": "11-15", "end": "12-05", "label": "红叶最佳期"}]`
- 跨年窗口（深冬 12/20-02/28）：`[{"start": "12-20", "end": "02-28", "label": "深冬"}]` —— 代码识别 `start > end` 表示跨年
- 常年通用模板：`[]`（空数组）

### 1.3 顶层可选字段（**有就写，没有不写**）

| 字段 | 类型 | 写的判断标准 |
|---|---|---|
| `pace_type` | string | `"adaptive"`（默认，可省略）/ `"fixed_early"`。见 §1.3.1 |
| `hotel_area_note` | string | 偏远 / 起点对酒店区敏感的模板才写（岚山要算交通、有马一泊要算路线）。市区核心模板不写 |
| `curators_notes` | string[] | 1-4 条策展小巧思，每条 30-50 字。**懂当地朋友才知道的小决定**（"早到是岚山日成立的关键"）。"以官方为准" 类废话不写 |
| `contingencies` | object | 应急预案；**4 子项有内容才写，不硬填**。见 §1.5 |

### 1.3.1 pace_type 字段（D38）

标记动线是否接受出门时间档位平移。

| 取值 | 含义 | 适用动线 |
|---|---|---|
| `"adaptive"` | 普通动线，跟随用户出门档（8/9/10）整体平移；**省略字段时默认此值** | 绝大多数动线 |
| `"fixed_early"` | 早起强动线，整天 6:30 出门写绝对时间，不平移；仅装给勾"早起加成"用户 | 清水寺独享舞台 / 伏见无人千鸟居 / 高雄 / 高野山 / 吉野山等 |

**本期暂不做 `fixed_early` 模板**（D38），但字段保留供未来扩展。所有动线先按 `adaptive` + 9 点档基准写。

### 1.4 slots 结构（D37 修订）

`slots` 是**按时间段分组**的数组，每段包含 `main`（必做）+ `optional`（推荐）：

```json
"slots": [
  {
    "time": "08:00-10:00",
    "main": [
      {"type": "poi", "entity": "kyo_arashiyama_bamboo"},
      {"type": "poi", "entity": "kyo_tenryuji"}
    ],
    "optional": [
      {"type": "poi", "entity": "kyo_kameyama_park", "note": "体力好/早到的用户加项"}
    ]
  },
  {
    "time": "12:00-13:30",
    "main": [
      {"type": "meal", "meal_type": "lunch", "meal_area": "arashiyama"}
    ]
  }
]
```

**关键设计**：
- **外层按时间段分组**（一天 5-8 个时段）
- **main** 数组：该时段必做，**必须 ≥1 个 slot，不能为空数组**
- **optional** 数组：顺路推荐，装配按用户密度决定用不用（可以为空或省略）
- **装配规则**：
  - packed 密度 → optional 全用
  - balanced → optional 用 1 个（写作者排序前的那个）
  - relaxed → optional 不用（+ 独立 `relaxed.json` 变体文件仅核心动线做）
- **slots 数组必须按 time 时间正序排列**

**硬规：main 不能为空**
- 如果某时段没有必做内容（如下午自由漫游），使用 `free_time` slot 类型填充 main（见 §1.4.1），**不要留空 main 把所有内容塞 optional**
- 空 main + 满 optional 会让装配不知道"这段是干什么的"

**为什么不再是三档 `{packed, balanced, relaxed}` 字段**：D36 定的三档强迫写作者为每模板写三套完整序列，工作量翻倍但多数档位差异只是"加不加顺路景点"。D37 改用"默认 main + 可选 optional"，节奏差异通过 optional 表达即可。

**放松版**：只有高强度动线（如东山）才在动线文件夹里单独做一个 `relaxed.json` 变体（里面再写一套完整 slots），多数动线不需要。

### 1.4.0 slot.time 缓冲时间规则（D37）

`slot.time` 时长 = 景点最佳游玩时间 + **缓冲**。缓冲给用户"不一定掐点到、不一定准点结束" 的稳态：

| 最佳游玩时间 | 缓冲 |
|---|---|
| < 1h | +30 分钟 |
| 1-2h | +30-45 分钟 |
| 2-3h | +45-60 分钟 |
| > 3h | +60 分钟 |

缓冲不是浪费，是体验稳态。

#### 1.4.1 slot 元素字段（按 type 区分）

**slot 没有 `time` 字段**（时间在外层时段对象上）。slot 是 main/optional 数组里的元素。

**通用字段**：

| 字段 | 类型 | 必填 | 取值 | 一句话语义 |
|---|---|---|---|---|
| `type` | string | ✓ | `poi` / `meal` / `hotel` / `transport` / `free_time` | slot 类型 |
| `note` | string | 部分必填 | 自然语言 | 该 slot 的动线判断 tip（见下方硬规） |

**note 硬规**：
- **同一 entity 在同一天的 slots 里出现 ≥2 次时**（如渡月桥下午漫步 + 黄昏 peak-end），**每次 slot 必须写 note 区分用途**（该时段做什么、为什么这时间来），否则装配/渲染无法区分两次停留
- optional slot 建议写 note 说明"什么情况下用"（如"体力好/早到的用户加项"）
- 普通单次 slot 可不写 note

**poi 类专属**：
- `entity` 必填：景点 ID（含商业街/河岸/区域型 entity）

**meal 类专属**：
- `meal_type` 必填：`breakfast` / `lunch` / `dinner`
- `meal_area` 必填：餐厅区域
- **不允许写 `entity`** 指定具体餐厅——即便灵魂餐厅也由餐厅装配按规则从池里挑

**hotel 类专属**：
- `hotel_area` 必填
- **不允许写 `entity`** 指定具体酒店——由酒店装配挑

**transport 类专属**：无额外字段，只 `type`。

**free_time 类专属**（D37 新增）：
- `theme` 必填：自由时段主题（如"下午自由漫游"/"午后茶歇"）
- `options_note` 必填：自然语言列"几个不会错的方向"（多选一的专家决策）
- 不挂 entity——因为自由时段是"在某个区域里，用户三选一做什么"，不绑单一景点
- 示例：

```json
{
  "type": "free_time",
  "theme": "下午自由漫游",
  "options_note": "三方向任选：(A) 渡月桥南岸 % ARABICA 买咖啡河堤坐；(B) 嵐電嵐山站足湯 ¥200-300 泡 15 分钟重置体力；(C) 嵯峨鳥居本传统建筑物群保护区漫步（江户街道风貌）"
}
```

**为什么需要 free_time**：按产品原则"有些天要有自由漫游段——专家决定在这里留白+给 2-3 个不会错的方向"，自由时段是付费价值之一。`free_time` 不挂 entity 避免为咖啡店/足湯这类小型设施单独建 entity。

#### 1.4.2 slot 字段彻底清掉的（不要再加回来）

- ~~`priority`~~（P1/P2/P3 被三档 slots 取代）
- ~~`note`~~（slot 内 note 取消，整天思路写在模板顶层 `note`）
- ~~`fun_fact`~~（挪事实层 entity）
- ~~`cuisine_hint`~~（餐厅装配按 area + 用户偏好挑，模板不指挥菜系）
- ~~`max_wait_min`~~（time 范围已含排队）
- ~~`stay_nights`~~（hotel 几晚由酒店装配算）
- ~~`kind`~~（保留 `type` 字段名）

### 1.4.3 动线内交通（transport.md）

每个动线文件夹**可选**一份 `transport.md`——列该动线涉及的景点对之间的交通方式。模板 slot 过渡时装配读此文件。

```markdown
# {动线名} 交通

## 动线起点（从市区到动线起始点）
- {酒店区} → {起始点}：约 N 分钟（交通方式大类）

## 景点间过渡
- {A} → {B}：N 分钟（步行/地铁/JR/公交/组合）
- {A} → {C}：...

## 跨动线连接（如适用）
- 动线 → 市区晚餐/下一动线：...
```

**硬规**：
- 优先公共交通（地铁/JR/公交/私铁），不写具体线路编号，只写**大类**和**总时长**
- 交通复杂时可加"推荐打车"作为补充，但公共交通也要写
- 只有没公共交通的情况才只写打车
- 每个动线景点对的交通**在这份文件维护一次**，模板不重复写交通细节

**边界（什么不写进 transport.md）**：
- 动线内**紧密相连、纯步行 citywalk 型**的景点路径（二年坂→三年坂→八坂塔、岚山竹林→天龙寺→渡月桥、祇园→先斗町这类）**不写**——这些就是模板 slot 顺序表达，slot 排序本身就是最佳 citywalk 路线
- 凡是"步行 3-10 分钟" 这种紧密相邻的不用列条目
- 只列真需要交通信息的段（换乘/跨区域/需要坐车）

### 1.4.2 night.json 结构（D37）

动线文件夹内可选的夜晚模块文件。**一个文件装多个夜晚选项**，装配按用户人群/预算挑一个。

```json
{
  "label": "东山夜晚模块",
  "time": "19:30-21:30",
  "options": [
    {
      "option_id": "gion_bar",
      "label": "祇园威士忌吧",
      "type": "bar",
      "meal_area": "gion",
      "fit_audience": "couple",
      "note": "花见小路附近，情侣向"
    },
    {
      "option_id": "gion_yozashiki",
      "label": "お茶屋体验",
      "type": "experience",
      "meal_area": "gion",
      "fit_audience": "couple",
      "reservation_required": true,
      "note": "舞妓/艺伎座敷，需预约"
    }
  ]
}
```

**每个 option 字段**：
- `option_id` 必填：option 唯一标识
- `label` 必填：人可读
- `type` 必填：`bar` / `experience` / `show` / `snack` 等
- 按 option 类型加 `meal_area` / `entity` / `fit_audience` / `reservation_required` / `note`

**硬规**：
- `night.json` 不在 index.md 里作为独立变体计数（它是**白天模板的可选附加**）
- 同一动线只有一份 `night.json`
- 岚山/USJ/有马/温泉一泊等默认无 night.json
- **夜间参拜不做 night.json**：延时参拜是白天模板的延伸（红叶夜间/樱花夜间），直接写在对应白天模板的 slots 末尾

### 1.5 contingencies 子项（4 个，有内容才写）

| 子项 | 写的条件 |
|---|---|
| `rain_light` | 小雨真有特别玩法时（雨后苔藓更深）；普通模板不写 |
| `rain_heavy` | 大雨需要改路线时（户外重的模板）。推荐用户躲进本地室内景点/咖啡馆。不另造模板 |
| `crowd` | 旺季有特殊应对（不是"人多时早点去" 这种废话） |
| `indoor_backup` | 本地雨天躲进的室内景点/咖啡馆清单（一段文字，户外重模板有时写） |
| ~~`minimum_viable`~~ | **彻底砍掉**——半天用半天模板，不在全天模板里搞兜底 |
| ~~`swap_candidates`~~ | **彻底砍掉**——不一天都下雨，用户雨时躲进 `indoor_backup` 即可，不需要换整个模板 |

### 1.6 模板字段彻底清掉的（不要再加回来）

跟"用户档位/天数/人群/A-B/酒店升档"相关的字段全部不进模板，挪到 [assembly/](../../japan/kansai/assembly/) markdown。

- ~~`tier`~~（A/B/C 投入精力分级，被 score.min_days 取代，且 score 已挪装配层）
- ~~`status`~~（开发状态没意义）
- ~~`weather_sensitive`~~（写模板时判断，contingencies 表达）
- ~~`day_peak`~~（写模板时判断，slot 顺序+note 表达）
- ~~`design_rationale`~~（合并进顶层 note）
- ~~`pace_variants`~~（三档 slots 取代）
- ~~`season_notes`~~（季节用文件夹表达）
- ~~`negative_peak_guard`~~（写模板时考虑）
- ~~`season_trigger`~~（季节用文件夹表达）
- ~~`time_of_day`~~（写进 template_id） 
- ~~`fit_audience`~~（装配层 audience_bonus 已有）
- ~~`tags`~~（砍）
- ~~`special_dates`~~（applicable_dates 取代）
- ~~`condition`~~（无明确消费方）
- ~~`variant_of` / `variant_type` / `trigger_condition`~~（template_id 已表达，如 `_atmosphere_full` `_photo_full`）
- ~~`early_spring_notes`~~（季节用文件夹表达）
- ~~`assembly_hints` / `assembly` / `season_window`~~（装配层 markdown 表达）
- ~~`core_entities`~~（slots 里 entity 字段汇总即可）
- ~~`photo_spots` / `nearby_shops` / `fun_facts`~~（**全挪事实层 entity**）
- ~~`score`~~（含 audience_bonus / execution_risk **挪装配层 markdown**）
- ~~`min_days`~~（**挪装配层 markdown**）
- ~~`day_type`~~（USJ日/人群日/到达日 **挪装配层 markdown**）
- ~~`exclusive_with`~~（互斥模板 **挪装配层 markdown**）
- ~~`night_options`~~（**挪装配层 markdown**——装配层维护"白天模板可接哪些夜模块"）
- ~~`selectable_tag`~~（**挪装配层 markdown**——用户表单勾选入口由装配层维护）
- ~~`_xxx` 临时注释字段~~（_season_restriction / _architecture_todo / _meta 等全清）

---

## 2. 景点层字段（entities/）

**entities/ 是景点完整信息层**——3 个文件按城市归属：
- `entities/kyoto.json` 京都景点（含 live facts 已并入对应景点）
- `entities/osaka.json` 大阪景点
- `entities/other.json` 其他城市（奈良/兵库/神户·有马 等合并）

模板 slot.entity 直接引用，渲染代码读这层取门票/坐标/开门时间，景点附属内容（拍照/冷知识/小店/避坑）全在 `notes` 自由文本。

**餐厅池和酒店池在装配层**：
- 餐厅池 → `assembly/restaurants/data/restaurants__{city}.json`
- 酒店池 → `assembly/hotels/data/hotels__kansai.json`

**季节窗口（樱花/红叶/祭典）在装配数据**：
- `assembly/templates/data/{sakura,koyo,festivals,illumination,special_open}.json`

### 2.1 entities（景点）

#### 2.1.1 必填（8 个）

| 字段 | 类型 | 一句话语义 |
|---|---|---|
| `entity_id` | string | 唯一标识，如 `kyo_kiyomizudera` |
| `name_zh` | string | 中文名（手账本印） |
| `name_ja` | string | 日文名（手账本印 / 现场找路） |
| `area` | string | 所在区域（装配匹配餐厅/酒店池） |
| `category` | string | 类别（去重用），见 §2.1.3 |
| `coordinates` | object | `{lat, lng}` 经纬度 |
| `short_desc` | string | 一句话介绍（手账本印） |
| `opening_hours` | object | `{regular: "06:00-18:00", closed: "无休"}` |

#### 2.1.2 可选（**有"比较好的"才写，不凑数**）

| 字段 | 写的判断标准 |
|---|---|
| `official_url` | 有就写 |
| `admission` | 收费才写：`{adult: 500, child: 200, unit: "JPY"}`。免费景点不写 |
| `reservation_required` | 需要预约才写 `true`（默认 false 不存字段） |
| `notes` | **自由文本大字段**（按宪法第一条），装跟这景点相关的所有零碎信息——拍照机位、冷知识、顺路小店、避坑、票价指引、当年临时变更等。**全部用中文子标题分段**，见下方 §2.1.4 |

**注意**：原 `photo_spots[]` / `fun_facts[]` / `nearby_shops[]` 三个结构化数组**已全部砍掉**，所有内容合并到 `notes` 自由文本（D36 决定，按宪法第一条"能用文字就用文字"）。

#### 2.1.3 category 枚举（约 12 个）

| 值 | 中文 | 例子 |
|---|---|---|
| `temple` | 寺 | 清水寺/金阁/天龙寺 |
| `shrine` | 神社 | 伏见稻荷/八坂 |
| `castle` | 城 | 大阪城/姬路城/二条城 |
| `bridge` | 桥 | 渡月桥 |
| `park` | 公园 | 奈良公园/圆山 |
| `garden` | 庭园 | 曹源池 |
| `market` | 市场 | 锦市场/黑门市场 |
| `commercial_street` | 商业街 | 道顿堀/心斋桥/先斗町 |
| `department_store` | 百货 | 阪急梅田 |
| `museum` | 博物馆 | 任天堂/铁博 |
| `onsen` | 温泉 | 有马/城崎 |
| `view_spot` | 展望台 | 龟山公园/摩耶山 |
| `natural_path` | 自然步道 | 竹林/哲学之道 |
| `riverside` | 河岸 | 鸭川/桂川 |
| `theme_park` | 主题乐园 | USJ/海游馆 |
| `district` | 散步区域 | 嵯峨鸟居本/岚山区域 |

### 2.1.4 notes 字段子标题规范

`notes` 用 markdown 子标题分段，**用统一中文标题词汇**（保持一致 AI/渲染才好处理）：

| 子标题 | 装什么 | 写的判断 |
|---|---|---|
| `## 拍照位置` | 出片机位 | 这景点真有"游客通常不走的角度"才写。每条 = 机位+时段+构图，一行一条 |
| `## 冷知识` | 朋友会忍不住讲的故事 | 不是百科摘要。"金阁 1950 年纵火三岛由纪夫" 算，"始建于 xx 年" 不算 |
| `## 顺路小店` | 懂当地朋友会指给你看的小店 | 不是伴手礼 TOP10 |
| `## 衔接` | 跨景点动线 tip | 跟具体动线相关的衔接说明（"北门接竹林南端，北门 16:50 关门"） |
| `## 票价指引` | 票价细分/购票建议 | 票价基础已在 admission 字段，这里写"加诸堂 +¥300，建议先买基础再决定" 这种判断 |
| `## 避坑` | 常见踩坑/误解 | "8 点后人爆炸" / "禁穿和服入内" 等 |
| `## 当年临时` | 当年特殊变更 | 票价涨/临时闭馆/活动停。明确写年份 |
| `## 季节` | 春/夏/秋/冬 各有什么不同 | 有差异才写 |

**示例**：

```markdown
## 拍照位置
- 子安塔背后小径：7:30 光线斜打，俯瞰本堂舞台
- 音羽の滝下方：仰拍舞台木柱结构，禁三脚架

## 冷知识
舞台 12 米高、139 根榉木立柱榫卯无钉。"清水の舞台から飛び降りる" 是日语谚语，意思"豁出去做件大事"。

## 衔接
出庭园走北门接竹林南端，北门 16:50 关门注意。

## 票价指引
庭园 ¥500，加诸堂 +¥300，加云龙图 +¥500（周末和春秋特别公开期间每天）。建议先买基础再现场决定要不要加。

## 当年临时
2026 年起夜间特别参拜票价涨至 ¥600。
```

### 2.1.5 砍掉的字段（不要再加回来）

- ~~`name_en`~~（手账本不印英文）
- ~~`address_ja`~~（coordinates 够定位）
- ~~`phone`~~（临时查官网）
- ~~`access`~~（用户用不到，模板 hotel_area_note 表达交通）
- ~~`unesco`~~（写进 short_desc 一句话）
- ~~`photo_ok` / `tripod_allowed`~~（合并进 photo_spots 的 tip）
- ~~`is_public_path`~~（opening_hours 表达 24h）
- ~~`seasonal_notes`~~（季节用模板文件夹表达）
- ~~`dwell_time_min`~~（slot.time 已定）
- ~~`kimono_policy`~~（写模板时 WebSearch）
- ~~`weather_sensitive`~~（写模板时判断）
- ~~`negative_peak_cautions`~~（写模板时考虑，写在模板 note）
- ~~`last_verified`~~（无效设计）
- ~~`data_confidence` / `data_sources[]`~~（内部管控放别处，不进生产数据）
- ~~`access_difficulty`~~（**砍掉**——偏远是装配层考虑"要不要给这用户推该模板"的事，不在事实层。装配花名册中标注模板"偏远 / 需 X 天以上"即可）
- ~~`photo_spots[]` / `fun_facts[]` / `nearby_shops[]`~~（**全砍**——内容合并到 `notes` 自由文本，按宪法第一条。子标题分段见 §2.1.4）

### 2.2 restaurants（餐厅）— 已挪装配层

**文件位置**：`japan/kansai/assembly/restaurants/data/restaurants__{city}.json`

字段保持原定义（17 字段）+ 新增 `notes` 自由文本字段（按宪法第一条，装该餐厅的零碎说明：避坑/历史背景/必点必知/季节限定）。

字段：`id / name_ja / name_zh / area / cuisine_tag / meal_type_fit / budget_tier / price_cny / vibe_tags / facility_tags / score / ab_role / meal_role / reservation_difficulty / opening_hours / risk_flags / last_verified / notes`

**当前模板 meal slot 永远不指定 entity**，由餐厅装配按规则从池里挑。装配规则见 [assembly/restaurants/index.md](../../japan/kansai/assembly/restaurants/index.md)。

### 2.3 hotels（酒店）— 已挪装配层

**文件位置**：`japan/kansai/assembly/hotels/data/hotels__kansai.json`

字段保持原定义（14 字段）+ 新增 `notes` 自由文本字段（按宪法第一条，装该酒店的零碎说明：位置细节/特色/适配/淡旺季差异）。

字段：`id / name / area / budget_tier / price_range_cny / vibe_tags / facility_tags / practical_tags / score / checkin / checkout / risk_flags / last_verified / notes`

**当前模板 hotel slot 永远不指定 entity**，由酒店装配按规则从池里挑。装配规则见 [assembly/hotels/index.md](../../japan/kansai/assembly/hotels/index.md)。

---

## 3. 装配层（assembly/）— **Markdown 不是 JSON**

装配层维护的是"装配规则 + 模板元数据"，消费方主要是 AI，**用 markdown 不是 JSON**。

### 3.1 文件组织

```
japan/kansai/assembly/
├── templates/
│   ├── index.md                 ← 模板花名册 + 打分 + min_days + day_type + 互斥 + 关西7条化学反应
│   └── data/                    ← 季节窗口 JSON（sakura/koyo/festivals/illumination/special_open）
├── restaurants/
│   ├── index.md                 ← 总规则（A/B 策略 / meal_role / 跨城去重 / 日类型升降）
│   ├── kyoto/{先斗町_河原町,祇园,京都站,...}.md
│   ├── osaka/{梅田_新地,难波_道顿堀,心斋桥,...}.md
│   ├── other/{神户,奈良,有马,城崎,高野山}.md    ← 每个文件内按区域分章节
│   └── data/                    ← 餐厅池 JSON
└── hotels/
    ├── index.md                 ← 总规则（升档比例表 / 修饰器 / 区域偏好 / 人群预算冲突）
    ├── kyoto/{四条河原町,京都站,祇园,...}.md
    ├── osaka/{难波_道顿堀,梅田,心斋桥,...}.md
    ├── other/{神户,奈良,有马,城崎,高野山}.md
    └── data/                    ← 酒店池 JSON
```

**路径命名硬规**：顶层和子目录**全英文**（避免 Windows/Python/Node 脚本对中文路径的兼容坑）；装配入口 md 文件名**统一 `index.md`**（跟 `templates/kyoto/arashiyama/index.md` 的动线入口一致）。区域 md 文件名用中文（写作者直接读，不进代码 import）。

**装配 markdown 正文全部用中文书写**。消费方是 Opus，中文比英文键名自然。

**热门 vs 补充**：京都/大阪 各热门区域单独一份 md（数量多、引用频率高）；其他城市在"其他/"下每个城市一份 md，文件内按区域分章节。

**每份区域 md 内部结构**：区域说明（氛围/适合场景/A 主推/B 惊喜/避坑/价格/跨城角色/景点关联）+ 该区域餐厅或酒店列表。

**产品原则的装配策略已挪走**：原 [产品原则.md](../../japan/kansai/产品原则.md) §4 餐饮 / §5 酒店 / §12 关西 7 条化学反应整章已迁到装配 markdown，产品原则中删除（避免两份并存冲突）。

### 3.2 assembly/templates/index.md = 顶层模板花名册（核心规范）

**所有模板的元属性集中在一份顶层 markdown 里维护**，不分散到各个模板 JSON。

**为什么这样**：
- 模板 JSON 干净，只管动线
- 元属性可以横向对比（一眼看完所有模板的打分/季节/人群偏好/互斥关系）
- 修改装配规则只改一个文件
- AI 装配读一份花名册就知道全局，不用扫 98 个 JSON

**花名册每个模板一段 markdown，含**：

| 字段 | 内容 |
|---|---|
| 季节 | early_spring / sakura / tsuyu / matsuri_peak_summer / summer_low / koyo / deep_winter / common（与模板所在文件夹一致，作为元数据冗余便于查询） |
| 人群偏好 | 情侣 / 朋友 / 家庭 / 默认 各档加成（实际就是 audience_bonus） |
| 打分 | core_experience（0-60）+ audience_bonus（情侣/朋友/家庭，-15~+20）+ execution_risk（0~-3） |
| min_days | 推荐总天数门槛（默认 0=任何天数） |
| day_type | regular / arrival / departure / theme_park / audience_day |
| exclusive_with | 互斥模板 ID 数组（关西 §12 化学反应规则） |
| no_pace_downgrade | bool，true 表示任何密度都不降档（USJ 日/人群日） |
| night_options | 这模板结束后可接哪些 night_module（template_id 数组） |
| selectable_tag | 用户表单勾选入口（onsen / usj / kimono / craft 等）；null 表示装配自动判断 |

### 3.3 events/ 也是 markdown（待迁移）

现有 `events/{sakura,koyo,festivals,illumination,special_open}.json` 5 个文件实质是给 AI 装配读的"窗口+判断上下文"，应迁移为 markdown。`live_facts__kyoto.json` 同样。

---

## 4. 通用字段约定

### 4.1 字段两分法（D29，仍适用）

所有结构化字段只有两类，其余一律自然语言：

- **客观事实字段**：世界的属性（id / 坐标 / 营业时间 / 价格等），机器和人都精确读
- **表单对应字段**：表单会按它过滤、或用户看得到的展示分类（人群 / 预算档 / 氛围标签等）

不属于这两类的全部写进 `note` / `description` / `curators_notes` 等自然语言字段。

### 4.2 命名规范

- 字段名：snake_case
- ID：snake_case，带城市/圈前缀（`kyo_arashiyama_bamboo`）
- 双语字段：`name_zh` / `name_ja`，日文汉字不要写成简体
- 时间格式：`HH:MM-HH:MM`（slot.time）/ `MM-DD`（applicable_dates）/ `YYYY-MM-DD`（具体日期）

### 4.3 通用结构

| 字段 | 类型 | 取值 / 格式 | 一句话语义 |
|---|---|---|---|
| `coordinates` | object | `{lat: float, lng: float}` | 经纬度，必须 Google Maps 验证 |
| `opening_hours` | object | `{regular: string, closed: string}` | 营业时间含定休日 |
| `admission` | object | `{adult: int, child: int, unit: "JPY"}` | 门票 |

---

## 4.4 校验脚本

`scripts/validate_template.py` 实现下面所有硬规的机械校验。每次改造模板后跑一次，违规才能提交审核。

规则清单：
1. 顶层 7 必填字段齐
2. template_id 全局唯一
3. slots 数组按 time 时间正序
4. 每个时段对象 main 数组 ≥1 个 slot（不能空）
5. 同一 entity 在同一天多次出现时每次 slot 必填 note
6. meal slot 不写 entity
7. hotel slot 不写 entity
8. free_time slot 必有 theme + options_note，不写 entity
9. poi slot 的 entity 在 entities/{city}.json 存在
10. applicable_dates 元素含 start/end/label，格式 MM-DD
11. contingencies 子项合法（rain_light/rain_heavy/crowd/indoor_backup，不含 swap_candidates/minimum_viable）
12. 动线文件夹内 1.json/2.json 编号连续无缺
13. 动线文件夹有 index.md（必）+ transport.md（必）

---

## 5. 字段变更流程（硬规）

任何字段变动**必须按以下顺序**：

1. **先改本文件 SCHEMA.md**（这是唯一权威源）
2. 再改受影响的写作指引（[模板写作.md](../04_操作SOP/模板写作.md)）
3. 在 [DECISIONS.md](../02_历史决策/DECISIONS.md) 加新决策号
4. 批量改现有数据/模板文件

**禁止反向操作**：不许"先在写作指引里加字段，回头再改 SCHEMA"。这会导致字段定义不一致。

**禁止随意扩展字段**：触发任何"新加字段"想法，先回答 §⚠️ 核心规范的 3 个问题。

---

## 6. 历史砍掉的字段（D36 大瘦身 2026-04-22）

模板字段从 30+ 砍到 12（必填 8 + 可选 4），事实层从 25+ 砍到最多 15。详见 §1.6 / §2.1.5 砍单。

砍的核心逻辑：
- **景点相关的内容（介绍/拍照/冷知识/小店/门票/开门）→ 全在事实层 entity**
- **跟用户档位/天数/人群相关的（打分/min_days/A-B/升档/互斥）→ 全在装配层 markdown**
- **模板只剩动线判断（顺序/时段/区域/类型）+ 设计 note + 用户 description**

---

## 7. 历史决策链

- D28 Opus 装配（2026-03-15）
- D29 字段两分法（2026-03-22）
- D30 score 0-5 统一（2026-04-08）
- D31 字段变更流程（2026-04-12）
- D32 关西 v2 四层架构（2026-04-17）
- D33 季节目录 10→7 档（2026-04-20）
- D34 仓库聚合重构（2026-04-20）
- D35 docs 5 类重构（2026-04-20）
- **D36 字段大瘦身 + 装配层 markdown 化**（2026-04-22）← 本次
