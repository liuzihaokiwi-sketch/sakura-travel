# Data Collection · 真实范例

> 全部取自仓库真实记录与真实 validator 白名单（2026-07-09 核）。字段以各 `scripts/validate_*.py` 为准，本文过期时以脚本为准。

## 权威字段白名单（照抄真实 validator·别凭记忆造字段）

**餐厅**（`restaurants/{city}/{area}.json`·顶层 list）
- 必填：`id, area, near_attractions, tier, cuisine, recommended_meals, closed_days`
- 可选：`reservation_difficulty, queue_level, season_months, depth, choice_role, note, images, handbook`
- 枚举：`tier ∈ {showcase, high, mid, economy}`·`reservation_difficulty ∈ {none, recommended, must}`·`queue_level ∈ {none, mild, high}`·`choice_role ∈ {safe_pick, discovery_pick}`
- `note` full 必填：`店名, 简介, 亮点, 招牌菜, 地址, 营业, 预约`；可选 `到店提醒, Tabelog 分数`
- ⚠️ **餐厅记录没有 `可信度` / `数据来源` / `recommend_reason` / `credibility` 字段**。这些是幻觉。sourcing 追在 `research/` 散文里，不是 per-record 数据字段。

**entity**（`entities/{city}.json`·顶层 **dict**，key=entity_id，首个 key 是 `_meta`）
- 必填：`entity_id, city, area, category, depth, 可信度`
- 可选：`season_months, reservation`；另有 `note, templates_meta`
- 枚举：`depth ∈ {full, verified, skeleton}`·`可信度 ∈ {verified, cross_checked, single_source, ai_generated}`·`reservation ∈ {none, recommended, required, hard}`
- `note` 必填 `店名, 简介`；可选 `票价, 营业, 怎么去`

**酒店**（`hotels/{city}.json`·顶层 list）
- 必填：`id, city, area, near_attractions, tier, type, price_cny_per_night` + 元数据 `可信度, 数据来源, 最后核实`
- 枚举：`tier ∈ {b1..b6}`·`type ∈ {city, experience}`
- `type=experience` 时 `note.亮点[0]` **必须**是 6 组之一：`温泉旅馆 / 老铺旅馆 / 宿坊 / 町家 / 温泉度假 / 设计精品`（validator FAIL 强约束）

---

## 范例 1：一条合格的餐厅记录（真实·`kyo_kawaramachi_kikunoi_roan`）

```json
{
  "id": "kyo_kawaramachi_kikunoi_roan",
  "area": "pontocho_kawaramachi",
  "near_attractions": [{"entity_id": "kyo_pontocho", "walk_min": 4}],
  "tier": "showcase",
  "cuisine": ["怀石"],
  "recommended_meals": [
    {"meal": "lunch",  "price_cny": [470, 705]},
    {"meal": "dinner", "price_cny": [940, 1410]}
  ],
  "reservation_difficulty": "must",
  "queue_level": "none",
  "closed_days": [3],
  "season_months": null,
  "depth": "full",
  "note": {
    "店名": "菊乃井 露庵（きくのい ろあん）",
    "简介": "…柜台割烹形式，昼怀石 ¥10,000 起是集团门槛最友好的入口…",
    "亮点": ["米其林二星", "高瀬川畔町家暖帘", "柜台割烹形式", "夏季纳凉床", "集团最易约入口"],
    "招牌菜": ["昼怀石套餐（¥10,000 起·全 8 品）", "夏季纳凉床怀石（5-9 月·需单独预约）"],
    "地址": "京都市下京区木屋町通四条下る斉藤町 118",
    "营业": "午市 11:30-15:30（LO 13:30）/ 晚市 17:00-22:00；水曜定休",
    "预约": "必须，电话 075-361-5580 / 一休 / TableCheck；旺季提前 1 个月+",
    "Tabelog 分数": 3.99
  }
}
```

取用要点：`closed_days:[3]` = 周三定休（数字周几）；`Tabelog 分数` 是可选质量信号，来自官方 tabelog；`米其林二星` 写在 `note.亮点` 里而非独立字段（能描述的写描述，不加字段）。

## 范例 2：entity 是 dict 不是 list（真实·`kyo_arashiyama_bamboo`）

```json
{
  "kyo_arashiyama_bamboo": {
    "entity_id": "kyo_arashiyama_bamboo",
    "city": "kyoto", "area": "arashiyama", "category": "自然", "depth": "full",
    "note": {"店名": "嵯峨野竹林小径…", "简介": "…约 400 米青竹通廊…", "票价": "免费", "营业": "24h", "怎么去": "JR「嵯峨嵐山」步行 9 分…"},
    "templates_meta": {"拍照位置": "…", "冷知识": "…声景百選…", "顺路小店": "…", "衔接": "…"}
  }
}
```

取用要点：整文件顶层是 `{entity_id: record}`，首键 `_meta` 不是记录（遍历时跳过）。`templates_meta` 里的 冷知识/顺路小店 是**外化素材金矿**——挖到即沉淀 `marketing/japan/kansai/素材库.md`。

## 范例 3：validator FAIL → 修根因（真实修复·2026-07-09）

`kyo_shijo_kawaramachi_soraniwa_terrace_bettei`（type=experience 温泉旅馆型酒店）报错：

```
kyoto.json::kyo_shijo_kawaramachi_soraniwa_terrace_bettei
  type=experience 但 note.亮点[0]='全室天然温泉露天风吕' 不在 6 组
```

- **错误做法**：改 validator 白名单 / 把 6 组约束放水（红线：`feedback_never_modify_validator`——检查器说错时，错的是我）。
- **根因修**：该店真实是「温泉旅馆型」，全池所有温泉旅馆的 `亮点[0]` 都是组标签。补 `"温泉旅馆"` 为 `亮点[0]`，原描述性亮点顺延：

```json
"亮点": ["温泉旅馆", "全室天然温泉露天风吕", "四条河原町温泉（自家源泉）", …]
```

- **验证**：`python scripts/validate_hotels.py japan/kansai/hotels` → `217 hotels, 0 errors`。改数据前先 grep 同类记录对齐约定（`亮点[0]` 全是 6 组之一），不硬塞。
