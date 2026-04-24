# 早春京都 — 事实采集清单

> 从 21 个早春京都模板里抽出的所有 entity + 待采集事实字段。
> 这个清单是 live_facts 层的初始 schema，后续扩展到其他季节会补充。
> 采集机制（人工/爬虫/混合）后续讨论，本文档只定**采集什么**。

---

## 一、Entity 总清单（按模板引用频率）

### A. 高频 entity（被多模板引用或是 critical）

| entity_id | 中文名 | 用途 | 优先级 |
|-----------|-------|------|--------|
| `kyo_arashiyama_bamboo` | 嵯峨野竹林小径 | 岚山 critical | P0 |
| `kyo_tenryuji` | 天龙寺 | 岚山 critical | P0 |
| `kyo_togetsukyo` | 渡月桥 | 岚山 peak-end | P0 |
| `kyo_kiyomizudera` | 清水寺 | 东山 critical | P0 |
| `kyo_yasaka_shrine` | 八坂神社 | 东山 flow | P0 |
| `kyo_gion_hanamikoji` | 祇园花见小路 | 东山/情侣/闺蜜 critical | P0 |
| `kyo_kinkakuji` | 金阁寺 | 北山 critical | P0 |
| `kyo_ryoanji` | 龙安寺 | 北山 flow | P0 |
| `kyo_kitano_tenmangu` | 北野天满宫 | 北山/梅苑 critical | P0 |

### B. 主体景点（modules/selectable）

| entity_id | 中文名 | 用途 | 优先级 |
|-----------|-------|------|--------|
| `kyo_nintendo_museum` | 任天堂博物馆 | 任天堂日 critical | P0 |
| `kyo_teamlab_biovortex` | teamLab Biovortex 京都 | teamLab 日 critical | P0 |
| `kyo_gekkeikan_okura_museum` | 月桂冠大仓纪念馆 | 伏见酒蔵 critical | P0 |
| `kyo_teradaya` | 寺田屋 | 伏见酒蔵 critical | P0 |
| `kyo_gear_theatre` | GEAR 剧场（1928 Building） | GEAR 夜 critical | P0 |
| `kyo_railway_museum` | 京都铁道博物馆 | 亲子日 critical | P0 |
| `kyo_aquarium` | 京都水族馆 | 亲子日 critical | P0 |
| `kyo_nijo_castle` | 二条城 | 二条城日 critical | P0 |
| `kyo_gyoen` | 京都御苑 | 二条城日 flow | P0 |

### C. 次级/扩展景点

| entity_id | 中文名 | 用途 | 优先级 |
|-----------|-------|------|--------|
| `kyo_kodaiji` | 高台寺 | 东山扩展 | P1 |
| `kyo_kenninji` | 建仁寺 | 情侣日 critical | P1 |
| `kyo_ninnaji` | 仁和寺 | 北山扩展 | P1 |
| `kyo_hirano_jinja` | 平野神社 | 梅苑日 flow | P1 |
| `kyo_ginkakuji` | 银阁寺 | 哲学之道日 critical | P1 |
| `kyo_nanzenji` | 南禅寺 | 哲学之道日 flow | P1 |
| `kyo_philosophers_path` | 哲学之道 | 哲学日 critical | P1 |
| `kyo_jonangu` | 城南宫 | 城南宫日 critical | P1 |
| `kyo_fushimi_inari` | 伏见稻荷大社 | 城南宫/半日 | P1 |
| `kyo_zuishinin` | 随心院 | 随心院日 critical | P1 |
| `kyo_daigoji` | 醍醐寺 | 随心院日扩展 | P1 |
| `kyo_byodoin_uji` | 平等院（宇治） | 任天堂日扩展 | P1 |
| `kyo_sagano_torokko` | 嵯峨野小火车 | 小火车日 critical | P1 |
| `kyo_kameyama_park` | 龟山公园 | 岚山扩展 | P1 |
| `kyo_jojakkoji` | 常寂光寺 | 岚山扩展 | P1 |
| `kyo_giouji` | 祇王寺 | 奥嵯峨 critical | P1 |
| `kyo_adashino_nenbutsuji` | 化野念佛寺 | 奥嵯峨 critical | P1 |
| `kyo_sanzenin` | 三千院 | 大原 critical | P1 |
| `kyo_jakkoin` | 寂光院 | 大原 critical | P1 |
| `kyo_shimogamo_shrine` | 下鸭神社 | 恢复日 flow | P1 |
| `kyo_kamogawa` | 鸭川 | 恢复/情侣 flow | P1 |
| `kyo_nishiki_market` | 锦市场 | 闺蜜日 critical | P1 |
| `kyo_kyoto_tower` | 京都塔 | teamLab 日 flow | P1 |

### D. 伴生/补强景点（文档里出现但非 slot 引用）

| 待补 entity | 出现场景 |
|------------|---------|
| `kyo_kitano_ume_garden` | 北野梅苑（独立于 kitano_tenmangu 的季节性开放区） |
| `kyo_kameyama_okochi_sanso` | 大河内山荘 |
| `kyo_kimono_forest` | 和服森林 |
| `kyo_kodaiji_nene_no_michi` | 宁宁之道（可能合并到高台寺） |
| `kyo_hozen_inari` | 愛宕念仏寺（奥嵯峨扩展） |
| `kyo_hokanji_pagoda` | 八坂之塔（法觀寺五重塔） |
| `kyo_shirakawa_minamidori` | 白川南通 |
| `kyo_tojji` | 东寺（teamLab 日扩展） |
| `kyo_fukuda_art_museum` | 福田美术馆（岚山雨天替代） |

**总计：约 40-45 个 entity**

---

## 二、entity 层需要采集的字段

### 静态字段（entities/kyoto.json）

```json
{
  "entity_id": "kyo_kinkakuji",
  "name_zh": "金阁寺",
  "name_ja": "金閣寺",
  "name_en": "Kinkaku-ji",
  "area": "northwest_kinkaku",          // 对应餐厅池 area
  "category": "unesco_temple",           // unesco_temple / shrine / museum / park / bridge / market / natural_path / street / castle / bath_house / theatre / etc.
  "coordinates": {"lat": 35.03937, "lng": 135.72932},
  "official_url": "https://www.shokoku-ji.jp/kinkakuji/",
  "access": "市バス 205号→金阁寺道站步行 3 分钟 / 从京都站约 40 分钟",
  "short_desc": "金箔三层阁楼倒映在镜湖池，京都 icon 级景点",
  "photo_ok": true,
  "tripod_allowed": false
}
```

---

## 三、live_facts 需要采集的字段（双角色）

### 3.1 角色 A：display（装配时注入文案）

```json
{
  "kyo_kinkakuji": {
    "display": {
      "admission_adult": "¥500",
      "admission_child": "¥300",
      "admission_note": "含纸质护身符",
      "hours": "09:00-17:00",
      "last_entry": "16:30",
      "payment_methods": "仅现金",
      "updated_at": "2026-01-15",
      "source_url": "shokoku-ji.jp/kinkakuji/"
    }
  }
}
```

### 3.2 角色 B：availability（装配前硬筛选）

```json
{
  "kyo_kinkakuji": {
    "availability": {
      "base_weekly_hours": {
        "mon-sun": {"open": "09:00", "close": "17:00"}
      },
      "closed_weekdays": [],
      "closed_dates_2026": [],
      "seasonal_period": null,
      "temp_closures": [],
      "requires_reservation": false
    }
  }
}
```

---

## 四、按 entity 分类的采集表

### 4.1 全年稳定型（seasonal_period = null）

只需采集 display + 基础 availability。

| entity | 特殊说明 |
|--------|---------|
| kyo_kinkakuji | 不太休，基础稳定 |
| kyo_ryoanji | |
| kyo_kiyomizudera | 6:00 开门，晚闭因季节不同 |
| kyo_yasaka_shrine | 24 小时开放，免费 |
| kyo_gion_hanamikoji | 街道本身无闭，但舞妓出勤时段禁拍 |
| kyo_arashiyama_bamboo | 24 小时开放，免费 |
| kyo_togetsukyo | 24 小时开放，免费 |
| kyo_tenryuji | 8:30-17:00（最晚入场 16:50），云龙图仅特定日 |
| kyo_ginkakuji | |
| kyo_kodaiji | |
| kyo_kenninji | |
| kyo_nanzenji | 水道閣 24 小时，三门登入收费 |
| kyo_nishiki_market | 多数店 10:00-18:00，各家不同 |
| kyo_shimogamo_shrine | 24 小时开放 |
| kyo_kamogawa | 河岸 24 小时 |
| kyo_gyoen | 24 小时开放 |

### 4.2 周期性休（closed_weekdays 非空）

| entity | 休日 | 注意 |
|--------|------|------|
| `kyo_nintendo_museum` | **周二休（不定期）** | 需采集 2026 全年闭馆表 |
| `kyo_teamlab_biovortex` | **周二休（不定期）** | 需采集 2026 全年闭馆表 |
| `kyo_railway_museum` | **周三休** | 节假日例外 |
| `kyo_aquarium` | 基本无休 | 临时维护另议 |
| `kyo_gear_theatre` | 周一/周二休（以官方为准）| 演出日程随月变 |
| `kyo_fukuda_art_museum` | **展期更换临时闭** | 2026/4 有长闭馆公告，需跟踪 |
| `kyo_nijo_castle` | 年末和 1/8-10 等特定日 | |
| `kyo_gekkeikan_okura_museum` | 周一休（盂兰盆和年末年始） | 2026/7 起无现金支付 |

### 4.3 季节性开放（seasonal_period 关键字段）

| entity | 开放期 | 采集重点 |
|--------|-------|---------|
| `kyo_kitano_ume_garden` | 2 月初-3 月下旬 | 2026 具体开放日、票价、是否有花之庭装置 |
| `kyo_jonangu_shidare_ume_garden` | 2/18-3/22（2026 春之山茶花祭典） | |
| `kyo_zuishinin_ono_plum_garden` | 3 月上旬-3 月下旬 | 2026 はねず踊り 日期（通常 3 月最后周末） |
| `kyo_sagano_torokko` | **2026/3/1 开航**，运营到 12 月下旬 | 冬季停运、夏季 8/12-8/31 休航 |
| `kyo_hozugawa_kudari`（保津川漂流） | 全年，暴雨停运 | 早春水冷 |
| `kyo_hirano_jinja_sakura_en` | 3 月底-4 月下旬 | 早春只有魁桜零星开 |
| `kyo_ninnaji_omuro_sakura` | 3/27-5/6（2026 御室花祭） | |

### 4.4 特殊限定日

| 日期 | entity | 事件 | 备注 |
|------|--------|------|------|
| 2026/2/25 | kyo_kitano_tenmangu | 梅花祭 + 野点大茶汤（上七軒舞妓奉茶）| 900 年传统 |
| 每月 25 日 | kyo_kitano_tenmangu | 天神市（上千摊位） | 京都最大露天市集 |
| 2026/3/14 | 伏见酒蔵区多家 | 伏见酒祭 + 12 家酒蔵开放日 | 5 部制 5000 名 |
| 2026/3/20 | kyo_fushimi_jikkokubune | 十石舟开航 | 早春 3/20 前无法乘船 |
| 2026/3/27-4/5 | kyo_kiyomizudera | 夜间特别参拜（夜樱） | 18:00-21:30 |

### 4.5 预约制硬门槛

| entity | 预约规则 |
|--------|---------|
| `kyo_nintendo_museum` | **提前 3 月抽选**，只接受任天堂账号 |
| `kyo_teamlab_biovortex` | 官网/Klook 购票，时段制 |
| `kyo_gear_theatre` | 提前 1-2 周官网/Klook 订票 |
| `kyo_arashiyama_onsen_inn`（各旅馆）| 高档旅馆旺季提前 2-3 月 |
| 花札工作坊（任天堂内）| 当日馆内预约（抽票） |

---

## 五、餐厅池字段（restaurant_pools/kyoto.json）

与 entities 分离。每家餐厅字段：
```json
{
  "id": "kyo_gion_izuju",
  "name_ja": "いづう",
  "name_zh": "いづう鲭寿司",
  "area": "gion_pontocho",
  "cuisine": "sushi",
  "budget_tier": "mid",
  "ab_role": "A",
  "vibe_tags": ["nostalgic", "cultural"],
  "experience_tags": ["local_life", "signature_dish"],
  "meal_time": ["lunch", "dinner"],
  "audience_bonus": {"couple": 3, "friends": 0, "family": -2},
  "seasonal_availability": null,
  "tabelog_score": 3.68,
  "michelin": "bib_gourmand",
  "editor_note": "1781 年起经营鲭鱼押寿司..."
}
```

**现有资产**：`content/kansai/kyoto/restaurants.json`（旧版 50+ 家）可作为采集基础。

---

## 六、酒店池字段（hotel_pools/kyoto.json）

```json
{
  "id": "hoshinoya_kyoto",
  "name_ja": "星のや京都",
  "name_zh": "星野屋京都",
  "area": "arashiyama",
  "tier": "ultra_luxury",
  "budget_range": "¥50000-80000/人/一泊二食",
  "signature_features": ["乘船入内", "保津川景观", "露天风吕"],
  "room_types": ["四季房", "宙之房"],
  "audience_bonus": {"couple": 10, "family": 5},
  "booking_lead_time_days": 90,
  "access": "渡月桥附近专用船入内"
}
```

**初步清单**（从温泉一泊模板的 hotel_tier_variants 抽出）：
- 星のや京都 / 翠嵐 / 花伝抄 / 嵐山辨慶 / 翠岚（旧 ランザン）

后续补充市区酒店（京都站/四条/祇园周边）。

---

## 七、采集优先级

### P0 —— 必须先有（样板验证用）
岚山线 3 个：`kyo_arashiyama_bamboo / kyo_tenryuji / kyo_togetsukyo`
事实采集完整（display + availability），这样才能跑通 Arashiyama 样板的规则装配验证。

### P1 —— 21 模板全覆盖
上面 §1 A+B 的 ~20 个 entity。够 21 个模板迁移用。

### P2 —— 扩展
§1 C+D 的扩展景点（伴生型、分支型）。

---

## 八、采集流程建议（后续讨论）

候选：
1. **纯人工**：客服或产品手动填。质量高但慢。
2. **爬虫+人工校对**：官网爬基础字段，人工核对+补充上下文。
3. **Agent 辅助**：给 Agent 官网 URL 让它抽字段，人工审核。

**建议混合**：
- 静态字段（名称、地址、坐标）→ 爬虫一次性
- display 字段（票价、开放时间）→ 爬虫 + 月度刷新
- availability 字段（周几休、季节期）→ 人工校对 + 月度更新
- seasonal_period / 特殊限定日 → **必须人工**（官方经常改，爬虫难抓对）

---

## 九、本清单的下一步动作

1. **产品/数据 同步**：这个清单达成共识
2. **采集工具选型**：决定爬虫/Agent/人工的混合比例
3. **P0 采集启动**：先完成岚山 3 个 entity + teamLab + 任天堂 + 清水 这 5-6 个最高优先级 entity，跑通样板验证
4. **P1 批量采集**：其他 15 个 P0-P1 entity
5. **校验脚本**：`scripts/validate_live_facts.py` 扫所有模板的 critical_entities 是否在 live_facts 里
