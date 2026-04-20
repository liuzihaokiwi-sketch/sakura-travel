# 新架构：知识与数据分离，规则合成文案

> 2026-04-17 晚深度架构讨论后的最终共识。
> 本文档是当前有效架构，**替代 05 文档**（05 保留作为字段清单的历史参考）。
> 06（fun_fact 素材库）和 07（SOP）文档继续有效，作为辅助规范。

---

## 0. 核心洞察

今晚写 21 个早春京都模板时暴露出根本性问题：**每个模板同时在做 4 件事**——
1. 给用户看的手账本内容（文案/氛围/拍照建议）
2. 给装配系统的指令（时间/entity 引用/priority）
3. 事实数据库（票价/开放时间/店铺详情）
4. 策展专家的设计思路（为什么这样排/如果只能保留三个）

**这 4 件事本质上是 4 种不同的东西，混一个 JSON = 所有混乱的根源。**

---

## 1. 四层架构

```
┌───────────────────────────────────────────────────┐
│ Layer 1: 真实数据层（冷数据）                      │
│ ├── entities/kyoto.json     景点/餐厅/酒店静态信息 │
│ ├── live_facts/kyoto.json   票价/开放时间/闭馆日   │
│ ├── restaurant_pools/       按区域的餐厅池         │
│ └── hotel_pools/            按档位的酒店池         │
│                                                   │
│ 职责：真实数据，不带观点                           │
│ 双角色：display（文案注入）+ availability（硬筛选）│
│ 维护者：数据工程 + 爬虫 + 人工校对                  │
└───────────────────────────────────────────────────┘
                    ↓ 引用
┌───────────────────────────────────────────────────┐
│ Layer 2: 策展知识层（热知识）                      │
│ └── templates/                                    │
│     只写设计思路：                                 │
│     - 为什么 8 点前去竹林                          │
│     - 动线逻辑                                     │
│     - 峰值在哪、收尾在哪                           │
│     - 氛围 / day_mood                              │
│                                                   │
│ 规则：                                             │
│ - entity 必须在 Layer 1 已注册                     │
│ - 不写任何票价、时间、电话                         │
│ - 不让用户做选择（禁止 N 选 1）                    │
│                                                   │
│ 维护者：产品/策展                                   │
└───────────────────────────────────────────────────┘
                    ↓ 按用户输入装配
┌───────────────────────────────────────────────────┐
│ Layer 3: 装配层                                   │
│                                                   │
│ 3a) 规则装配（主路径）                            │
│ - 按 applies_when + excludes_when 硬过滤候选      │
│ - 按 live_facts.availability 检查 entity 可用性   │
│ - 不可用则从同池自动替补                           │
│ - 每个 slot 规则拼接 entity + facts + design       │
│ - Markdown/文本渲染                                │
│                                                   │
│ 3b) Opus 判断（关键节点）                         │
│ - 选哪些模板组成 N 天行程                          │
│ - 餐厅池内选具体 A/B 家店                          │
│ - 酒店池内选最匹配                                 │
│ - 夜间活动挑不重复的                               │
│ - 行程完整装配后最终审查（发现节奏失衡、加料）      │
│                                                   │
│ 维护者：工程                                       │
└───────────────────────────────────────────────────┘
                    ↓ 输出
┌───────────────────────────────────────────────────┐
│ Layer 4: 手账本输出                               │
│ 单一最终方案，不让用户选                           │
└───────────────────────────────────────────────────┘
```

---

## 2. Opus 的正确角色

**Opus 不负责每个 slot 的文案合成——那是规则的事。**

| 节点 | Opus 做 | 规则做 |
|------|--------|-------|
| 选模板组成行程 | ✓ | |
| 餐厅 A/B 选哪家 | ✓ | |
| 酒店选哪家 | ✓ | |
| 夜间活动选哪个 | ✓ | |
| 最终整体审查 | ✓ | |
| 每 slot 文案合成 | | ✓ |
| 事实注入（票价/时间）| | ✓ |
| 筛选 entity 可用性 | | ✓ |
| 自动替补 | | ✓ |
| Markdown 渲染 | | ✓ |

**为什么这样分**：
- 规则产出确定性（同样输入同样输出，版式统一）
- Opus 成本可控（只在判断节点，不在每 slot）
- 调试容易（错了知道在哪一层）
- 质量稳定（规则不漂移）

---

## 3. 核心设计原则

### 3.1 按分从高到低、递进锁定景点

写模板的顺序不是"每个主题/人群独立设计"，而是：

1. **先写分数最高的模板**（比如东山精华日，默认人群）
2. **锁定它占用的 critical_entities**（清水寺/三年坂/花见小路/白川/八坂）
3. **写下一个模板时，必须避开已锁定的景点**
4. **情侣日 / 闺蜜日是另一条动线的独立模板**，不是东山精华日的"人群变种"
5. 分数低到一定程度（< 30）就停 —— 不是所有体验都需要独立模板

**例子**：
- `kyo_higashiyama__default`（默认王牌）→ 锁定清水/花见/白川
- `kyo_philosophers__couple`（情侣走哲学之道+南禅寺+鸭川）→ 完全不同动线
- `kyo_nishiki_kawaramachi__friends`（闺蜜走锦市场+河原町+和服）→ 又一条不同动线

**这样做的好处**：
- 跨模板去重天然解决（设计阶段就避开）
- 每个模板都有独特性
- 模板总数有自然上限

### 3.2 人群专属型 ≠ 同一地点不同人群文案版本

audience_bonus 拉满到 20 不代表模板和基础模板重叠。专属型模板必须**动线本身就是为这个人群设计的**。

### 3.3 变种 vs 独立判断

- critical entity 高度重合 → 是**同一模板的变种**（用 `_variants` 字段覆盖个别 slot）
- critical entity 基本不同 → **独立模板**

默认选**独立模板方案**（字段简单、逻辑清晰）。

---

## 4. 模板池分层

```
templates/
├── full_day/
│   ├── main/        广谱主推（东山、岚山、金阁、任天堂等）
│   └── deep/        深度/小众（大原、奥嵯峨、随心院等）
├── half_day/
│   ├── morning/     上午型半日（伏见稻荷、二条城半日）
│   └── afternoon/   下午型半日（三十三間堂、宇治、工艺）
├── multi_day/       多日模板（岚山温泉一泊）
├── night_module/    夜间插件（GEAR 夜 2-3h）
└── special_date/    特定日期触发（3/14 伏见酒祭、2/25 梅花祭）
```

**池的语义**：
- `main` = 不勾选也进候选池
- `deep` = 已经刷过主线或明确勾选才给
- `modules`（selectable）= 用户必须勾选对应标签才进候选池

---

## 5. 模板字段结构

### 5.1 单日模板（full_day）

```json
{
  "template_id": "kyo_arashiyama__early_spring",
  "name": "岚山日（早春静美版）",
  "duration_days": 1,
  "pool": "main",

  "applies_when": {
    "party_types": ["couple", "default", "friends"],
    "budget_tier_min": null
  },

  "excludes_when": {
    "adults_only": false,          // 成年限定（默认 false；true = 未成年不推荐）
    "requires_reservation": false, // 需提前预约/抽票（默认 false）
    "not_first_visit": false       // 第一次来京都不推荐（默认 false）
  },

  "selectable_tag": null,          // 用户主动勾选的偏好标签；没勾仍入池，勾了加分（软加分，非硬过滤）

  "audience_bonus": {
    "couple": 3,
    "friends": 1,
    "family": 0
  },

  "score": {
    "core_experience": 46,
    "execution_risk": -1,
    "access_convenience": 3,
    "base_score": 48
  },

  "critical_entities": ["kyo_arashiyama_bamboo", "kyo_tenryuji"],

  "theme": {
    "mood": "沉浸与留白",
    "hook": "樱花高峰前的空窗期，一年里独享竹林的机会",
    "rationale": "如果只能保留三个：清晨竹林 + 天龙寺曹源池 + 渡月桥黄昏。顺序关键：竹林 9 点后明显拥挤必须最前；天龙寺 8:30 开门，北门接竹林北端形成闭环",
    "peak_end": "渡月桥畔黄昏——桂川水声和远山变成剪影的 10 分钟"
  },

  "flow": [
    {"slot": "morning_early", "entity": "kyo_arashiyama_bamboo", "design": "..."},
    {"slot": "morning", "entity": "kyo_tenryuji", "design": "..."},
    {"slot": "lunch", "meal_area": "arashiyama_central", "cuisine_hint": "tofu_ryori", "design": "..."},
    {"slot": "peak_end", "entity": "kyo_togetsukyo", "design": "..."},
    {"slot": "dinner", "meal_area": "default_city_center", "cuisine_hint": "avoid_tofu", "design": "..."}
  ],

  "strategy": {
    "rain_light": "...",
    "rain_heavy": "...",
    "crowd_dense": "..."
  },

  "night_options": ["kyo_gear_night"]
}
```

### 5.2 半日模板（half_day）

```json
{
  "template_id": "kyo_sanjusangendo__half_pm",
  "name": "三十三間堂下午半日",
  "template_kind": "half_day",
  "time_slot": "afternoon",              // ← 关键：morning / afternoon
  "duration_hours": 4,
  "pool": "main",

  "applies_when": {...},
  "critical_entities": ["kyo_sanjusangendo"],

  "meal_included": {                     // ← 餐配位置
    "breakfast": false,
    "lunch": "before_entry",             // 需前置午餐 / "included" / false
    "dinner": false
  },

  "can_attach_after": [                  // ← 可挂在哪些上下文后
    "transfer_day",
    "multi_day_checkout",
    "half_day_morning_*"
  ],

  "theme": {...},
  "flow": [...],
  "strategy": {...}
}
```

### 5.3 多日模板（multi_day）

```json
{
  "template_id": "kyo_arashiyama_onsen__1n_stay",
  "name": "岚山温泉一泊",
  "template_kind": "multi_day",
  "duration_days": 2,
  "nights_consumed": 1,
  "pool": "deep",

  "applies_when": {...},
  "excludes_when": {"min_budget_tier": "premium_ryokan"},

  "hotel_tier_variants": {               // ← 替代 core_entities.酒店
    "luxury_high": {...},
    "luxury_core": {...},
    "premium_ryokan": {...}
  },

  "days": [
    {
      "day_index": 1,
      "time_slot_coverage": "afternoon_onwards",  // D1 下午切入
      "flow": [...]
    },
    {
      "day_index": 2,
      "time_slot_coverage": "until_noon",          // D2 上午结束
      "flow": [...],
      "d2_afternoon_policy": "attach_half_day_pm"  // 装配时接一个下午半日
    }
  ]
}
```

### 5.4 夜间模块（night_module）

```json
{
  "template_id": "kyo_gear__night",
  "name": "GEAR 齿轮秀",
  "template_kind": "night_module",
  "duration_hours": 2.5,
  "pool": "modules",

  "applies_when": {
    "selectable_tag": "traditional_performance"
  },

  "can_attach_after": ["full_day_kyoto_center_*", "half_day_afternoon_*"],

  "flow": [
    {"slot": "pre_dinner", "meal_area": "karasuma_oike"},
    {"slot": "show", "entity": "kyo_gear_theatre"}
  ]
}
```

---

## 6. 字段语义规则

### 6.1 禁止规则（校验脚本强制）

| 字段 | 禁止 |
|------|------|
| `design` / `note` | "三个方向任选"、"两个方向"、"都不会错"、"(1)…(2)…(3)" |
| `design` | 具体票价、开放时间、店铺年份（属 live_facts） |
| `entity` | 必须在 entities 层注册，禁止占位符 |
| `meal_area` | 单值，多方向用 `_variants` |

### 6.2 必填字段

所有模板：`template_id / name / template_kind / pool / applies_when / audience_bonus / score / theme / flow（或 days）`

### 6.3 候选筛选四字段的分工

装配前系统依次过这四个字段。前两个决定"能不能进候选池",后两个决定"进了之后加几分"。

| 字段 | 语义 | 不符合的后果 |
|------|------|------------|
| `applies_when`（适用条件） | 这模板是为哪类人群/预算写的 | 不是目标人群 → 不进候选池 |
| `excludes_when`（硬排除） | 有什么硬门槛必须满足 | 不满足 → 不进候选池 |
| `audience_bonus`（人群加分） | 特别适合某类人群 | 不是这类人群 → 少几分,仍在池中 |
| `selectable_tag`（偏好加分） | 用户主动勾选的兴趣标签 | 没勾 → 少几分,仍在池中 |

**核心原则:系统只做非黑即白的硬判断,细节留给文案。**

`excludes_when` 只保留三个开关(布尔值):

```json
"excludes_when": {
  "adults_only": true,           // 成年限定(含酒精/赌场/成人秀等)
  "requires_reservation": true,  // 需要提前预约/抽票(任天堂博物馆、某些会席)
  "not_first_visit": true        // 第一次来京都不推荐(深度线/小众线)
}
```

**不做细粒度判断**——具体年龄门槛(20 岁饮酒)、身高限制、签证要求等写进 entity 的 `display` 字段或模板 `flow.design` 的文字说明里,由手账本原样呈现给用户,让用户自己判断。

例:伏见酒蔵模板标 `adults_only: true`,entity 的 display 里写 "法律规定 20 岁以上可试饮,未成年仅参观"。

### 6.4 变种机制

真需要按人群差异时用 `_variants`，不在 note 列多选：

```json
{
  "slot": "afternoon_extend",
  "entity": "kyo_kimono_forest",
  "design": "和服森林+足湯，下午能量重置",
  "_variants": {
    "couple": {"entity": "kyo_okochi_sanso", "design": "..."}
  }
}
```

---

## 7. 事实层（live_facts）

### 7.1 双角色结构

```json
{
  "kyo_tenryuji": {
    "display": {
      "admission": "庭园 ¥500 / 庭园+本堂 ¥800",
      "hours": "08:30-17:00（最晚入场 16:50）",
      "payment_methods": "仅现金"
    },
    "availability": {
      "base_hours": {"open": "08:30", "close": "17:00"},
      "closed_weekdays": [],
      "closed_dates_2026": [],
      "seasonal_period": null,
      "temp_closures": []
    }
  },
  "kyo_kitano_ume_garden": {
    "display": {
      "admission": "¥1200（含茶点）",
      "hours": "09:00-16:00"
    },
    "availability": {
      "seasonal_period": {
        "open_from": "2026-02-01",
        "open_to": "2026-03-22",
        "peak": "2026-02-20 to 2026-03-15"
      }
    }
  },
  "kyo_sagano_torokko": {
    "availability": {
      "seasonal_period": {
        "open_from": "2026-03-01",
        "open_to": "2026-12-29"
      },
      "closed_weekdays": [3]
    }
  }
}
```

### 7.2 装配前筛选

```
Step 1: 按 applies_when + excludes_when 硬过滤候选（不符合直接淘汰）
Step 2: 检查 critical_entities 在用户日期是否可用（availability）
        - 周几休馆 → 跳过或挪日
        - 季节窗口不对 → 排除
        - 临时闭馆 → 排除
Step 3: critical 任一不可用 → 模板淘汰
Step 4: 可用模板按 score 排序
        - base_score + audience_bonus[当前人群] + (用户勾了 selectable_tag 则加分)
Step 5: 不够 N 个 → 自动替补（同池/同季节/同人群）
Step 6: Opus 关键节点判断
Step 7: 规则合成最终文案
```

### 7.3 自动替补

**替代手写 swap_candidates**（那是静态硬编码，违反配置驱动原则）：

```python
def find_replacement(failed_template, user_input, used_entities):
    candidates = all_templates.filter(
        pool == failed_template.pool,
        applies_when_matches(user_input),
        critical_entities_available(user_dates),
        critical_entities_not_in(used_entities)
    )
    return candidates.sorted_by_score().first()
```

---

## 8. 餐厅池

### 8.1 区域池结构

```
content/kansai_v2/restaurant_pools/
  kyoto.json
```

每家餐厅：
```json
{
  "id": "kyo_gion_izuju",
  "name_ja": "いづう",
  "name_zh": "いづう鲭寿司",
  "area": "gion_pontocho",
  "cuisine": "sushi",
  "budget_tier": "mid",
  "ab_role": "A",
  "vibe_tags": ["nostalgic", "cultural"],          // ← 氛围
  "experience_tags": ["local_life", "signature_dish"], // ← 体验
  "meal_time": ["lunch", "dinner"],
  "audience_bonus": {"couple": 3, "friends": 0, "family": -2},
  "seasonal_availability": null,
  "editor_note": "..."
}
```

### 8.2 装配时的选择

模板只标 `meal_area + cuisine_hint`：
1. 按 meal_area 过滤餐厅池
2. 按用户预算档位过滤
3. 按 cuisine_hint 匹配（可选）
4. **Opus** 按当前模板氛围 + 用户人群选具体 A + B
5. 跨天菜系/档位去重（行程级）

---

## 9. 酒店池

### 9.1 普通模板
**不关心酒店**。装配时按行程城市段统一选酒店（连续几天同一酒店，换城时换）。

### 9.2 特殊模板（温泉一泊等）
`hotel_tier_variants` 绑定特定酒店类型，装配时从对应池选。

---

## 10. 用户标签季节配置

`form_config/{season}.json` 定义当季可选标签：

```json
// form_config/early_spring.json
{
  "time_occupying": [
    {"tag": "usj", "label": "USJ"},
    {"tag": "nintendo_museum", "label": "任天堂博物馆"},
    {"tag": "teamlab", "label": "teamLab 京都"},
    {"tag": "traditional_performance", "label": "传统表演"}
  ],
  "non_time_occupying": [
    {"tag": "cultural_experience", "label": "文化体验（茶道/工艺/酒藏）"},
    {"tag": "kimono", "label": "和服体验"}
  ],
  "constraints": [
    {"tag": "no_early_morning", "label": "不接受 7-8 点前早起"},
    {"tag": "no_late_night", "label": "不接受 19 点后活动"}
  ]
}
```

---

## 11. 跨季节规则

用户行程跨越两个季节：按**覆盖天数最多的季节**作为主季节。
例：3/20-3/28（早春 5 天 + 樱花 4 天）→ 按早春主导装配。
罕见平分情况下按固定规则（优先前一个季节）。

---

## 12. 产品边界

以下情况**不走模板装配，直接客服定制**：
- 第二次来关西的用户
- 奢华游（酒店 ¥3000+/晚）
- 已预订酒店的用户
- 预约失败的场景（任天堂没抽中等）—— 客服流程，非模板问题

---

## 13. 恢复日特殊处理

恢复日系统设计**暂缓**（过于特殊，强行套一般模板架构会把系统搞复杂）。
- 保留现有模板文件
- 标记 `_design_deferred: "assembly logic TBD"`
- 等其他模板全部按新架构稳定后再单独想

---

## 14. 实施路径

### 第 1 步：文档落定（本文档）
- 本文档作为权威架构共识

### 第 2 步：事实采集清单
- 扫 21 个模板抽出所有 entity 的 live_facts 需求
- 产出 `facts_to_collect.md`

### 第 3 步：样板验证（Arashiyama）
- 按新架构重写 Arashiyama 样板
- 建对应的 entities 和 live_facts 子集
- 写最简规则渲染脚本跑通
- 验证 flow → 文案的合成效果

### 第 4 步：21 模板机械迁移
- 样板通过后，其他 20 个按同样规则改写
- 抽事实到 live_facts
- 删 N 选 1 内容
- 景点避让（按分从高到低重审）

### 第 5 步：校验脚本
- entity 必须在 entities 层
- 禁用词扫描
- 模板池分类正确性

### 第 6 步：overlay 机制（跨季节时再做）
- 写樱花/红叶季模板时需要 core + overlay 机制
- 不是早春单季就做

---

## 15. 今晚架构反思沉淀

### 所有问题的根源：**模板同时在做 4 件事**

| 今晚踩过的坑 | 新架构怎么不再踩 |
|-------------|----------------|
| 模板里塞事实（票价/时间）| Layer 1 分离，模板不写事实 |
| 票价变了改 21 个模板 | 只改 live_facts 一处 |
| core_entities 语义双重 | 重命名 critical_entities，只做去重和筛选 |
| 占位符混入（kyo_craft_studio）| entity 必须在 entities 层 |
| 2 天模板用 full_day | 独立 multi_day 结构 + days[] |
| 37 处 N 选 1 | 字段规则禁止，_variants 表达变种 |
| 晚餐两方向 | meal_area 单值 |
| 独立 vs overlay 混乱 | 目录分层 + overlay 机制（后续） |
| 酒店塞模板 | 独立酒店池 |
| 文案质量不稳 | 规则合成代替 Opus 合成 |
| 让用户做决策 | 模板只呈现单一最终方案 |

---

## 16. 下次 session 从哪里开始

1. 读本文档（08）建立架构理解
2. 读 `facts_to_collect.md` 知道要采集什么
3. 读 `21_template_migration_plan.md` 知道怎么迁移
4. 启动实际数据层搭建 + 样板验证

---
