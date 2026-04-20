# 西班牙模板 Schema v3

> 本文档是西班牙 day 模板/restaurants/hotels JSON 的字段规范。
> 参考关西 v2 教训:避免"一个主题日 4-6 份重复文件"+"事实硬编码在 slot note"+"缺结构化 day_peak"三个老坑。
> 反哺关西:关西 v3 应按本 schema 对齐。

---

## 1. 设计原则

### 1.1 一份文件 = 一个"主题日"的所有可能性

不是一份文件 = 一天。是一份文件 = **一组紧密相关的变体**(同景点主线,不同季节/人群/天气版本)。

**反例(关西 v1 老坑)**:
```
arashiyama_day.json            # base
arashiyama_sakura_day.json     # 春季版(重复 70%)
arashiyama_koyo_day.json       # 红叶版(重复 70%)
arashiyama_onsen_stay.json     # 加温泉版(重复 60%)
```
4 份文件维护成 4 倍工作量,差异散落看不见。

**正例(西班牙 v3)**:
```
santa_cruz_flamenco_day.json   # 一份文件,内含 variants 字段
    variants:
      default:          # 常规版
      summer_heat:      # 夏季避暑改版(siesta 延长,paseo 移到 20h 后)
      semana_santa:     # 圣周专属(凌晨游行替代 flamenco)
      couple:           # 情侣版(加上 Betis 夜酒)
```

一份文件一眼看清 4 个版本的差异。

### 1.2 事实与叙事分离

**事实**(会变,爬虫维护):价格/营业时间/官网链接/预约窗口/地址/电话 → 用 `{{entity:xxx.field}}` 占位符
**叙事**(不变,人工维护):历史年份/建筑风格/文化意涵/动线建议/氛围描述 → 直接写入

### 1.3 结构化峰值

关西 v2 反馈:`day_peak` 必须结构化,装配层读得到,砍 slot 时保护。加 `design_rationale` 让 Opus 理解"为什么这样排"。

---

## 2. Day 模板 Schema

### 2.1 顶层字段

```json
{
  "template_id": "santa_cruz_flamenco_day",
  "label": "Santa Cruz + Flamenco 开场日",
  "tags": ["moorish", "cathedral", "flamenco", "santa_cruz"],
  "core_entities": ["sev_alcazar", "sev_catedral_giralda", "sev_flamenco_anchor"],
  "region": "andalucia",
  "city": "sevilla",
  "fit_audience": "all",

  "assembly": {
    "phase": "anchor|sightseeing|rest|transfer|arrival|departure",
    "best_pace": "compact|standard|leisurely"
  },

  "day_peak": {
    "slot_id": "sc_flamenco",
    "type": "bigPeak",
    "description": "Flamenco 心灵相通时刻——塞维利亚骨子里的劲道,当晚的情绪最高点。",
    "never_cut": true
  },

  "peak_end_line": "看完那一刻你会懂为什么这城市是 flamenco 的圣地。",

  "design_rationale": {
    "why_this_sequence": "Alcázar→大教堂→Santa Cruz 是'世界遗产三连'地理最紧凑动线(1 分钟步行);午餐 sobremesa 让体力回血;siesta 避 40°C;paseo 是傍晚仪式不是景点过场;Flamenco 放 22:00 是当天峰值,需要前面 8 小时的慢热铺垫才打得中。",
    "what_to_cut_first": ["sc_night_option (P5)", "sc_shops (P5)", "sc_santa_cruz_walk 缩短 30min (P2)"],
    "what_never_cut": ["sc_alcazar", "sc_catedral", "sc_flamenco", "sc_lunch sobremesa 时长"],
    "alternative_orderings": [
      {
        "condition": "用户 Day 1 累(倒时差)",
        "swap": "Alcázar + 大教堂 → Day 2,本 Day 只做 Santa Cruz 漫步 + Flamenco"
      }
    ]
  },

  "weather_sensitive": false,
  "summer_heat_sensitive": true,

  "hotel_area_note": "...",
  "booking_requirements": { ... },

  "variants": {
    "default": { ... },
    "summer_heat": { ... },
    "semana_santa": { ... },
    "couple": { ... }
  },

  "slots": [ ... ]   // base slots, variants 只列 diff
}
```

### 2.2 variants 机制

**装配层合并规则**:
1. 读 `slots`(base)
2. 根据当前上下文(月份/用户选择/人群)选一个 variant key
3. 将 variant 的 `slot_overrides / slot_inserts / slot_removes / top_level_overrides` 应用到 base

```json
"variants": {
  "default": {
    "applies_when": "always",
    "description": "常规版,春秋适中气候"
  },
  "summer_heat": {
    "applies_when": "month in [6,7,8,9]",
    "description": "夏季 40°C+ 版本,siesta 延长,paseo 后移",
    "top_level_overrides": {
      "best_pace": "leisurely"
    },
    "slot_overrides": {
      "sc_siesta_indoor": {
        "time_range": "15:00-18:30",
        "duration_min": 210,
        "priority": "P1",
        "note": "夏季必须回酒店空调房 2-3 小时,不是可选。出门前看温度,超过 38°C 绝对不在街上。"
      },
      "sc_paseo": {
        "time_range": "20:30-21:30"
      },
      "sc_dinner": {
        "time_range": "21:45-22:45"
      },
      "sc_flamenco": {
        "time_range": "23:00-00:30",
        "note": "夏季场次普遍推迟 1 小时"
      }
    }
  },
  "semana_santa": {
    "applies_when": "date in [2026-03-29, 2026-04-05]",
    "description": "圣周期间,flamenco 让位给凌晨 cofradías 游行",
    "slot_removes": ["sc_flamenco", "sc_night_option"],
    "slot_inserts": [
      {
        "after": "sc_dinner",
        "slot_id": "sc_madrugada_cofradia",
        "time_range": "01:00-04:00",
        "type": "festival",
        "priority": "P1",
        "note": "'La Madrugá'(圣周凌晨)是 Sevilla 一年中最震撼的夜——Macarena/Esperanza de Triana/El Silencio 三大 hermandades 凌晨出队游行。**提前查路线图**(官方 semanasanta.sevilla.org),占位要 4 小时前。不要拍照闪光,不要说话——这是 Sevillanos 的宗教时刻。"
      }
    ],
    "booking_note": "圣周住宿价翻 2-3 倍,提前 4-6 月订。"
  },
  "couple": {
    "applies_when": "party_type == 'couple'",
    "description": "情侣版,收尾加河岸夜酒",
    "slot_overrides": {
      "sc_night_option": {
        "priority": "P2",
        "note": "Flamenco 散场后走回 Santa Cruz 西侧的 Puente Isabel II 河岸——Torre del Oro 打灯倒影在水面,这是情侣版的安静收尾。一杯 digestivo 再回。"
      }
    }
  }
}
```

**variants 选择优先级**:
- 同时匹配多个 → 合并(semana_santa + couple 都匹配,先应用季节 overlay,再叠人群 overlay)
- 冲突时人群 variant 覆盖季节 variant(除非季节 variant 标 `override_priority: "strict"`)

### 2.3 slot 字段(不变)

slot 内部字段继承原设计,但 `note` 内部的事实走占位符(见第 3 节)。

---

## 3. 事实占位符机制

### 3.1 语法

```
{{entity:<entity_id>.<field>}}
{{entity:<entity_id>.<field>|fallback:<默认值>}}
```

### 3.2 只对 5 类字段强制占位符化

| 字段 | 来源 | 例子 |
|------|------|------|
| `price_eur` | live_facts | `€{{entity:sev_alcazar.price_eur\|fallback:14.5}}` |
| `booking_url` | live_facts | `官网 {{entity:sev_alcazar.booking_url\|fallback:alcazarsevilla.org}}` |
| `opening_hours` | live_facts | `{{entity:sev_alcazar.hours_today}}` |
| `address` | live_facts | `{{entity:sev_alcazar.address}}` |
| `phone` | live_facts | `{{entity:sev_alcazar.phone}}` |

### 3.3 不走占位符(直接硬写)

- 历史叙事("1670 年开业""穆迪札尔风格")
- 文化背景("Mudéjar 是穆斯林工匠为天主教国王做的装饰")
- 动线建议("从北门出来接竹林南端")
- 氛围文案("茉莉香是这里的早餐")

这些**不是事实,是知识**,不会变,硬写进模板。

### 3.4 渲染规则

- 占位符解析失败(live_facts 里无此 entity/field)→ 使用 `|fallback:xxx` 后的默认值
- 无 fallback 且解析失败 → 整句话降级,不露 `{{}}` 给用户(例如 "官网:{{entity:x.url}}" 降级为"详见官网")
- 手账本渲染阶段完成替换,不在 Opus 装配阶段展开(Opus 不需要看具体价格,只需要知道"有个订票信息 slot")

---

## 4. live_facts/ 目录

```
content/spain/live_facts/
  poi/
    sev_alcazar.json           # 订票窗口/价格/hours/url 等
    sev_catedral.json
    sev_alhambra.json
  restaurants/
    sev_taberna_coloniales.json  # 地址/电话/hours/price_range
  hotels/
    parador_granada.json
  flamenco_venues/
    sev_casa_memoria.json
  _update_policy.md            # 爬虫节奏(月度/季度/年度)
```

每个 entity 一份 JSON,字段定义见第 5 节(entity schema)。

---

## 5. Entity Schema(live_facts 里的对象)

```json
{
  "entity_id": "sev_alcazar",
  "name_es": "Real Alcázar de Sevilla",
  "name_zh": "塞维利亚王宫",
  "type": "poi",
  "city": "sevilla",
  "address": "Patio de Banderas, s/n, 41004 Sevilla",
  "coordinates": {"lat": 37.3830, "lng": -5.9903},
  "phone": "+34 954 50 23 24",
  "booking_url": "https://www.alcazarsevilla.org",
  "official_url": "https://www.alcazarsevilla.org",
  "price_eur": 14.5,
  "price_updated_at": "2026-04-18",
  "hours": {
    "mon-sun": "09:30-17:00",
    "seasonal_notes": "4-9 月延长至 19:00"
  },
  "booking_window": {
    "level": "L3",
    "weeks_ahead_recommended": 2,
    "days_ahead_minimum": 3,
    "named_ticket": true,
    "passport_required": true
  },
  "data_confidence": "verified",
  "sources": [
    {"url": "https://www.alcazarsevilla.org/tarifas", "accessed": "2026-04-18", "by": "manual_verified"}
  ],
  "update_policy": "quarterly"
}
```

**data_confidence** 沿用 CLAUDE.md 定义(verified / cross_checked / single_source / ai_generated)。

---

## 6. 迁移策略(已写的 2 份 day 模板)

1. 抽出 5 类事实字段 → live_facts/poi/*.json(本次生成骨架,爬虫后续验证)
2. slot note 里的事实替换为占位符
3. 顶层新增 day_peak / peak_end_line / design_rationale
4. 顶层 variants 字段暂时只填 `default`(无季节变体),后续需要时再扩

---

## 7. 与关西 v2 差异(反哺路径)

| 维度 | 关西 v2 | 西班牙 v3 |
|------|---------|----------|
| 变体管理 | 文件拆分(4 份 arashiyama) | 单文件 variants(1 份内含 4 variant) |
| 事实字段 | 硬编码在 slot note | 占位符 + live_facts |
| day_peak | 描述里提 | 结构化字段 |
| design_rationale | 无 | 显式字段 |
| data_confidence | 无 | 三级标注 |
| 订票窗口 | 部分 slot note | 顶层 booking_requirements + entity level |

**反哺计划**(提案,等关西窗口决策):
- arashiyama_day + sakura + koyo + onsen_stay 4 合 1 → `arashiyama_day.json` with variants
- 所有 ¥ 价格和 URL 抽出到 `content/kansai/live_facts/`
- 顶层补 day_peak / peak_end_line / design_rationale

---

## 8. 变更规则

字段新增/修改必须:
1. 先改本文档(_SCHEMA.md)
2. 再改已有模板
3. 如影响装配层,同步改 Opus assembler / live_facts 渲染器
