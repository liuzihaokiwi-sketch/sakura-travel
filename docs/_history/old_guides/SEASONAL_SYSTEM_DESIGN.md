# 季节系统设计

> 版本：2026-04-12
> 状态：已共识，待实施
> 关联：
> - [../SCHEMA.md](../SCHEMA.md) — 字段唯一权威源（when / seasonal_notes / L0 事件字段定义）
> - [TEMPLATE_CREATION_GUIDE.md](TEMPLATE_CREATION_GUIDE.md) — 造模板 SOP
> - [../../data/events/](../../data/events/) — 事实层数据

---

## 1. 总原则：事实与编排分离

### 1.1 L0 事实层（data/events/）

只存"什么时候有什么活动"，不含任何 slot_id 或编排规则。

保持现有 9 字段结构，236 条现有数据不动：

```
data/events/kansai/
  sakura.json       — 24 个 event_def（清水寺/円山公园/醍醐寺...）
  koyo.json         — 20 个
  festivals.json    — 14 个（祇园祭/天神祭...）
  illumination.json — 14 个（清水寺春季夜间拝观...）
  special_open.json — 10 个（京都春秋特别拝観）
```

**L0 的职责边界**：维护事件的时间窗口（usual_window + current_year_window）。编排规则不放在这里。

### 1.2 L1 编排层

通过**独立完整模板 + 景点池 seasonal_notes** 两个机制承接。

不做运行期合并，不做 overlay patch。运行期没有"把普通模板和季节数据合并"的动作——季节模板和普通模板在候选池里平等竞争，由装配引擎通过硬筛（`when` 触发条件）+ `core_entities` 去重自然处理。

### 1.3 两个机制的分工

| 情况 | 机制 |
|---|---|
| 够格成为整天主题（平时不存在，季节才成立） | 独立完整模板（见第 2 节） |
| 附注级的季节信息（现有景点的季节加成） | 景点池 seasonal_notes（见第 3 节） |

判断标准：**"如果这个季节活动不存在，整天的行程主题还成立吗？"** 不成立 → 独立模板；成立但有附加信息 → seasonal_notes。

---

## 2. 机制一：独立完整模板

### 2.1 什么情况下写独立模板

- **平时不存在、只有特定季节才成立的整天主题**：醍醐寺樱花日、永观堂红叶夜间拝観、高雄三尾红叶日
- **祭典日**：祇园祭山鉾巡行（7/17）、五山送火（8/16）、葵祭（5/15）
- **季节性料理/体验**：贵船川床、鸭川纳凉床（季节内每天都成立，但非季节期间完全不存在）

这些模板在数据库里和普通模板平等存在，遵循 [SCHEMA.md](../SCHEMA.md) 的全部数据结构约定，唯一的区别是有 `when` 触发条件字段。

### 2.2 触发条件字段 when

`when` 字段定义见 [../SCHEMA.md §1.3](../SCHEMA.md#13-when-触发条件字段)。两种触发方式（`event_ref` 引用 L0 事件 / `period_md` 月日区间）二选一,没有 `when` 字段的模板常年有效。

示例（引用 L0 事件,L0 每年更新窗口后所有引用该事件的模板自动更新）：

```json
{
  "when": {
    "event_ref": "kansai_sakura_daigoji"
  }
}
```

示例（月日区间,适用于"夏季限定的每天都可去"等无对应 L0 事件的情况）：

```json
{
  "when": {
    "period_md": {"start": "05-01", "end": "09-30"}
  }
}
```

### 2.3 装配时如何被选中

装配流程：

```
1. 查 when 字段：
   - 有 event_ref → 查 L0 的 current_year_window，用户行程日期 ∩ 窗口 命中则通过
   - 有 period_md → 用户行程日期 ∩ 月日区间 命中则通过
   - 无 when → 直接通过（常年有效）
2. 进入候选池（和普通模板平等参与后续筛选）
3. 按 vibe / 人群硬筛
4. core_entities 去重（与已选模板有核心景点重叠则淘汰）
5. 按清单优先级截取前 N 个
```

**运行期没有"塞入"动作**。季节模板和普通模板在候选池里平等竞争，依靠 `when` 命中 + `core_entities` 去重自然处理，不需要专门的"季节塞入步骤"。

### 2.4 京都季节模板清单

以下为京都季节模板清单：

**樱花池（8 个）**

| id | 主题 | L0 event_ref |
|---|---|---|
| daigoji_sakura_day | 醍醐寺一日 | kansai_sakura_daigoji |
| ninnaji_omuro_sakura_day | 仁和寺御室樱 | kansai_sakura_ninnaji |
| hirano_jinja_sakura_day | 平野神社樱花祭 | kansai_sakura_hirano |
| haradanien_sakura_day | 原谷苑私家樱园 | kansai_sakura_haradanien |
| maruyama_yozakura_day | 圆山夜樱 | kansai_sakura_maruyama |
| nijo_yozakura_day | 二条城夜樱 | kansai_sakura_nijo |
| keage_sakura_day | 蹴上倾斜铁道 + 平安神宫神苑 | kansai_sakura_keage |
| kyoto_botanical_sakura_day | 京都府立植物园 | kansai_sakura_botanical |

**红叶池（6 个）**

| id | 主题 | L0 event_ref |
|---|---|---|
| tofukuji_koyo_day | 东福寺红叶 | kansai_koyo_tofukuji |
| eikando_koyo_day | 永观堂夜间拝観 | kansai_koyo_eikando |
| rurikoin_koyo_day | 琉璃光院 | kansai_koyo_rurikoin |
| takao_koyo_day | 高雄三尾 | kansai_koyo_takao |
| ohara_koyo_day | 大原红叶 | kansai_koyo_ohara |
| shugakuin_koyo_day | 修学院離宮秋季公开 | kansai_koyo_shugakuin |

**非樱红季节池（12 个）**

| id | 主题 | 触发条件 |
|---|---|---|
| gion_matsuri_yoiyama_day | 祇园祭宵山 | 7/14-16 |
| gion_matsuri_yamaboko_day | 山鉾巡行 | 7/17 |
| kyoto_gozan_okuribi_day | 五山送り火 | 8/16 |
| kibune_kawadoko_day | 贵船川床料理 | 5-9 月 |
| kamogawa_noryoyuka_day | 鸭川纳凉床 | 5-9 月 |
| aoi_matsuri_day | 葵祭 | 5/15 |
| jidai_matsuri_day | 时代祭 | 10/22 |
| kyoto_shunki_tokubetsu_day | 春季非公开特别公开 | 春季 |
| kyoto_shuki_tokubetsu_day | 秋季非公开特别公开 | 秋季 |
| kyoto_hatsumoude_day | 元旦初詣 | 1/1-3 |
| kyoto_yuki_day | 雪景日 | 天气触发 |
| arashiyama_hanatouro_day | 岚山花灯路 | 12 月中旬 |

---

## 3. 机制二：景点池 seasonal_notes

### 3.1 设计意图

适用于"景点本身常年存在，但在特定季节有附加价值"的情况。不新建独立模板，而是在景点池实体上标注季节附注，装配时自动触发。

例如：清水寺在东山日模板里是常规 slot，但樱花期"子安塔背后的舞台全景樱花"是附加信息——不值得为此写一个"东山樱花日"模板（因为清水寺本身常年都在），但值得在装配时追加一条提示。

### 3.2 数据结构

所有池实体（餐厅/酒店/咖啡馆/景点/拍照点）加一个可选对象 `seasonal_notes`。key 是季节名，value 是自然语言说明。key 数量自由，没有受控词表，常用的有 "樱花期" / "红叶期" / "夏季" / "冬季" / "祭典期" 等。只有"有季节故事"的实体才填，不是每条都填。

```json
{
  "id": "pontocho_robin",
  "seasonal_notes": {
    "樱花期": "傍晚临河座位，鸭川两岸樱花 + 黄昏灯光，最值得来的时段",
    "秋季": "秋季限定松茸土瓶蒸 ¥2000，必点",
    "夏季": "5-9 月开纳凉床，川面正上方位置要提前 1 个月预约"
  }
}
```

### 3.3 字段约定

`seasonal_notes` 字段定义见 [../SCHEMA.md §0.3](../SCHEMA.md#03-通用字段约定)。所有四类实体共享这一字段。

**为什么是 key/value 而不是带 trigger/bonus 的结构化数组**：
- 实体只描述"这个季节有什么看点"，**不写具体日期**——日期由 L0 事实层（`data/events/`）维护
- 装配引擎是 Opus（D28），不需要数值 bonus 排序，Opus 读 note 文字自己判断要不要追加到推荐里
- 樱花期窗口推迟一周这种事不需要逐条改实体，L0 当年窗口更新一次，所有实体自动跟随

### 3.4 装配引擎如何消费

装配引擎是 Opus（D28），系统不做"塞入/匹配"动作。装配 prompt 里塞三样东西：

1. 用户行程日期
2. L0 当年事件窗口（`data/events/<circle>/*.json` 的 `current_year_window`，约 50 行 JSON）
3. 候选实体（含各自的 `seasonal_notes` 对象）

Opus 自己读这三样判断：用户日期是否落入某个事件窗口、命中后哪些实体的 seasonal_notes key 应该被激活、激活后的 note 文字怎么自然地融进推荐叙述。**没有打分、没有加权、没有排序公式**，全部是自然语言判断。

季节名到 L0 事件的对应关系是约定俗成的（"樱花期" → sakura.json，"红叶期" → koyo.json，"祭典期" → festivals.json 等），不需要在每条实体里写明引用关系，装配 prompt 里告诉 Opus 这套对应即可。

### 3.5 什么情况下用 seasonal_notes 而不是独立模板

用 seasonal_notes 的判断标准：

- 景点常年存在，只是季节期间有额外看点（清水寺樱花期早开门 + 樱花背景）
- 餐厅有季节限定菜品（松茸土瓶蒸、冬日暖锅）
- 景点在特定季节氛围更好，但没好到值得"专门为此安排整天"
- 附注文字在 1-2 句内说完

不适合用 seasonal_notes（应写独立模板）的情况：

- 景点平时根本不开或不值得去，只有季节才成立（醍醐寺樱花）
- 季节活动本身就是整天的主题（祭典日、川床料理）
- 季节变化导致路线、时间、餐饮全部需要调整

---

## 4. 年度更新机制

### 4.1 usual_window vs current_year_window

L0 事件字段定义见 [../SCHEMA.md §3](../SCHEMA.md#3-l0-事实层events)。每条 event_def 有两层时间：

- `usual_window`：历史规律窗口，月日格式，人工维护，变化不大
- `current_year_window`：当年预测窗口，完整日期，由年度更新脚本写入

装配引擎优先使用 `current_year_window`，无当年数据时回退到 `usual_window`（作为约值区间）。

示例：

```json
{
  "event_def_id": "kansai_sakura_daigoji",
  "usual_window": {
    "start_md": "03-25",
    "end_md": "04-04"
  },
  "current_year_window": {
    "year": 2026,
    "start": "2026-03-29",
    "end": "2026-04-08",
    "updated_at": "2026-03-15",
    "source": "weathernews"
  }
}
```

### 4.2 年度更新脚本

```
scripts/update_sakura_year_windows.py
  读 data/sakura/weathernews_all_spots.json
  读 data/sakura/jma/
  对 data/events/kansai/sakura.json 的每条 event_def
    找对应预测 → 更新 current_year_window（year / start / end / updated_at / source）
```

原始数据已有，每年 2-3 月跑一次。红叶池类似，待建对应脚本。

---

## 5. 旧架构废弃

### 5.1 本次废弃的文件

| 文件 | 废弃原因 |
|---|---|
| `content/kansai/kyoto/seasonal_overlay.json` | 运行期合并方案，和"独立完整模板"新共识冲突 |
| `content/kansai/osaka/seasonal_events.json` | 事实和规则混在一起，和 L0/L1 分层原则冲突；含 slot_id bug（d2_osaka_castle → core_osaka_castle） |
| `_deprecated/docs/tasks/TASK_seasonal_system.md`（原内容） | 过时的任务文档，结论被本文档替代 |

**迁移顺序**：先建新结构并验证，再删旧文件。不要在迁移完成前删除旧文件。

### 5.2 已废弃的方案

以下方案经过完整讨论后明确否决：

| 方案 | 废弃原因 |
|---|---|
| 方案 A：slot 级 `seasonal_variants` 数组（运行期合并） | 调试复杂；每个 slot 的变体数据散落各处 |
| 方案 B：events 文件带 `default_overlay` + Resolver（300 行 patch 引擎） | 工程复杂度高；L0 事实层不该承载编排规则 |
| 方案 C：只做 banner（在预览页展示季节提示） | 违反产品承诺；用户预期的是行程本身包含季节活动 |
| `overlay_patch_types` / `confidence_permissions` / `precedence` 机制 | 属于方案 B 的复杂度，一并废弃 |
| 独立候选池 + 装配时"塞入/替换"动作 | 和"季节模板在候选池里平等竞争"的新共识冲突 |

### 5.3 最终方案：独立完整模板 + seasonal_notes 附注

最终选择"方案 D"的理由：
- **概念最少**：季节模板就是普通模板，只是多了 `when` 字段
- **运行期逻辑最简**：装配引擎的季节处理逻辑只是"when 命中 → 进候选池"，和普通模板的差异只在这一步
- **数据调试最直观**：每条模板完整独立，出错时直接看那条记录，不需要追踪 patch 链路
- **编辑体验好**：专家直接写一个完整模板，不需要理解 overlay 语法

---

## 6. 迁移步骤

### 6.1 一次性迁移清单

1. 把 `data/events/kansai/*.json`（236 条）加入 git 追踪（当前 untracked，存在丢失风险）
2. 读 `content/kansai/kyoto/seasonal_overlay.json`，对照 `data/events/` 找 `event_def_id`，把内容改写成独立完整模板，存入 `content/kansai/kyoto/days/` 目录
3. 读 `content/kansai/osaka/seasonal_events.json`，同上处理，顺便修 slot_id bug（`d2_osaka_castle` → `core_osaka_castle`）
4. 删除两个旧 seasonal 文件
5. 景点池实体扫一遍，把明显的季节附注补成 `seasonal_notes` 对象（key 是季节名，value 是自然语言说明，详见第 3 节）
6. 更新 `data/events/schema.json`：删除旧的 `applies_to` / `default_overlay` / `precedence` 字段（这些是方案 B 的残留）
7. 确认 `_deprecated/docs/tasks/TASK_seasonal_system.md` 顶部的废弃声明已添加

### 6.2 持续性工作

- 京都季节模板内容生产（见本文 §2.4 清单）
- 大阪、奈良、神户季节模板类推
- 每年 2-3 月跑一次 `current_year_window` 更新脚本

---

## 7. 与其他模块的边界

- **模板系统**：所有模板遵循 [SCHEMA.md](../SCHEMA.md) 数据结构约定。
- **L0 事实层 schema**：见 `data/events/schema.json`（需要更新，删除旧的 `applies_to` / `default_overlay` / `precedence` 字段）
- **装配引擎**：seasonal_notes 由 Opus 在装配 prompt 里直接读取判断（见第 3.4 节），不做加权排序，本文档只定义数据结构。
- **呈现层**：见 [../page_system/](../page_system/)。季节附注的 `note` 文字由呈现层决定如何展示（行内展示、角标、弹出框等）。
