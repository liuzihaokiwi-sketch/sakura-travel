# 旅行数据 Schema 规范

> 版本: 2.0
> 更新: 2026-04-01
> 适用: 所有城市圈数据采集

本文档定义三类数据（景点、餐厅、酒店）的**完整字段规范**，包括字段名、类型、枚举值、校验规则。
新城市圈采集必须严格遵守此规范。

---

## 〇、数据可信度标记（最高优先级规则）

### 核心原则

**没有真实数据源验证的数据，不能直接用于生产。**

每条数据必须携带 `data_confidence` 字段，标记其可信度：

```json
"data_confidence": {
  "level": "verified | cross_checked | single_source | ai_generated",
  "sources": ["tabelog", "google_maps", "ikyu", "booking", "trip_com", "xiaohongshu"],
  "axes_verified": {
    "quality": true,
    "traveler_fit": true,
    "execution": false
  },
  "verified_fields": ["grade", "pricing", "review_signals"],
  "unverified_fields": ["coord", "when.open_hours"],
  "last_verified_at": "2026-04",
  "notes": "Tabelog评分已验证(quality)，携程评论已确认(traveler_fit)，坐标待Google API确认(execution)"
}
```

### 可信度等级

| 等级 | 含义 | 可否用于生产 | 条件 |
|------|------|-------------|------|
| **verified** | 三轴均有真实来源覆盖 | 可直接使用 | quality+traveler_fit+execution均有至少1个真实来源 |
| **cross_checked** | 至少2个轴有真实来源 | 可使用，标记来源 | 如quality+execution已验证，traveler_fit待补 |
| **single_source** | 仅1个轴有真实来源 | 可使用但需标注 | 如仅有quality轴的Tabelog数据 |
| **ai_generated** | 无任何轴有真实来源 | 不可用于生产 | 无任何真实数据源 |

注: P0/P1/P2分级保留在源注册表(MASTER_GUIDE第四章)中，用于源管理和抓取优先级。
data_confidence的判定现在基于三轴覆盖度，不再简单按"几个P0确认"决定。

### 数据源注册表(源管理用)

| 级别 | 数据源 | 说明 |
|------|--------|------|
| **P0** | Tabelog / 米其林 / MICHELIN Keys / 一休 / 楽天 / 携程 / Google Maps / japan-guide / JNTO | 抓取优先级最高，维护频率最高 |
| **P1** | Booking / じゃらん / Agoda / TripAdvisor / Retty / GURUNAVI / SAVOR JAPAN / Relux | 交叉确认用，抓取优先级次之 |
| **P2** | 小红书 / 马蜂窝 / 独立攻略站 / 知乎 | 参考用，按需抓取 |
| **P3** | AI知识库 | 必须标记 ai_generated，不可用于生产 |

各来源在三轴中的具体角色见 MASTER_GUIDE 第四章"三轴判断模型"。

### 现有关西数据的可信度状态

当前关西数据（景点171+餐厅380+酒店300）**全部为 `ai_generated`**，因为：
- 未使用Tabelog API验证餐厅评分
- 未使用一休/楽天/携程验证酒店价格和评分
- 未使用Google Maps API验证坐标和营业时间
- 价格是AI估算，不是OTA真实价格

**这些数据在真实数据源验证之前，标记为存疑，不可用于生产环境。**

### 升级路径

```
ai_generated → 用真实数据源验证关键字段 → cross_checked/verified → 可用于生产
```

关键字段验证优先级：
1. **评分/评级**: Tabelog分/Google分/一休分 — 决定推荐排序
2. **价格**: OTA真实价格 — 决定预算规划
3. **营业状态**: Google Maps确认是否还在营业 — 避免推荐已关店
4. **坐标**: Google Maps API — 避免地图定位错误
5. **营业时间**: 官网/Google Maps — 避免行程安排出错

---

## 一、通用规则

### 1.1 ID 格式

```
{city_prefix}_{type}_{seq}
```

| 数据类型 | type标识 | 示例 |
|----------|---------|------|
| 景点 | (无type段) | `kyo_fushimi_inari` |
| 餐厅 | `r` | `kyo_r_001` |
| 酒店 | `h` | `kyo_h_001` |

城市前缀表：

| 前缀 | 城市 | 前缀 | 城市 |
|------|------|------|------|
| kyo | 京都 | nar | 奈良 |
| osa | 大阪 | kob | 神户 |
| ons | 温泉地 | oth | 其他地区 |
| tok | 东京 | hok | 北海道 |
| fuk | 福冈 | oki | 冲绳 |

### 1.2 坐标格式

```json
"coord": [latitude, longitude]
```

**必须是 `[纬度, 经度]` 顺序。** 日本范围校验：
- 纬度: 24.0 ~ 46.0
- 经度: 122.0 ~ 154.0

如果 coord[0] > 100，说明经纬度写反了。

### 1.3 时间格式

所有时间字段统一为 `"HH:MM-HH:MM"` 格式：
- 正确: `"09:00-17:00"`
- 错误: `"09:00-17:00(最終入場16:30)"` — 括号注释移到 `closed_notes` 或 `notes`
- 错误: `"18:00-(一斗席)"` — 必须有结束时间
- 错误: `"终日开放"` — 改为 `"00:00-24:00"` 并在notes标注"终日开放"

特殊值：`null` 表示不适用（如景点无晚间营业）。

### 1.4 Grade 评级

统一使用 **S/A/B/C** 四级制，不使用 A+、B+ 等变体。

| 等级 | 景点含义 | 餐厅含义 | 酒店含义 |
|------|---------|---------|---------|
| S | 城市圈名片，不去等于没来 | 城市美食名片 | 住宿本身是此行目的 |
| A | 值得专程安排半天 | 必吃推荐 | 住宿明显加分 |
| B | 行程增色 | 优质选择 | 有小惊喜 |
| C | 顺路收录 | 顺路可选 | 纯功能性住宿 |

**不允许 null**。酒店无体验特色的标 C。
**grade由品类内相对排名+编辑判断决定，不由固定分数阈值决定。** 详见 SELECTION_PHILOSOPHY.md。

### 1.4b 精选标签 (selection_tags)

每条数据标记其入选逻辑(可多选):

| 标签 | 含义 | 判断来源 |
|------|------|---------|
| city_icon | 城市身份/文化名片 | 编辑判断+权威源 |
| traveler_hot | 游客高热度 | 携程/小红书/Google评论量 |
| local_benchmark | 本地口碑标杆 | Tabelog高分/Retty/日文来源 |

```json
"selection_tags": ["city_icon", "local_benchmark"]
```

### 1.4c 景点双S制

景点的S级拆分为:
- heritage_s: 文化/历史/自然名片(JNTO/japan-guide/世界遗产判定)
- popular_s: 大众热门/体验名片(Google评论量/携程/小红书判定)

```json
"s_type": "heritage_s"  // 或 "popular_s" 或 "both" 或 null(非S级)
```

### 1.4d 负向编辑记录

入围池中被编辑淘汰的条目保留记录:
```json
"editorial_exclusion": {
  "excluded": true,
  "reason": "排队平均2小时，同区域有3家同品质免排队替代",
  "better_alternatives": ["xxx_id", "yyy_id"]
}
```

### 1.4e 性价比信号 (value_signal)

所有品类通用:

```json
"value_signal": {
  "tier_value": "high/medium/low",
  "surprise_factor": "12000日元含天然温泉+免费夜宵拉面",
  "best_deal_tip": "午餐比晚餐便宜60%，体验几乎一样",
  "avoid_trap": "旺季价格翻3倍，不如换区域"
}
```

- tier_value: 同预算层内的性价比(high=超值, medium=合理, low=偏贵)
- surprise_factor: 超预期的体验(如果有)
- best_deal_tip: 怎么获得最佳性价比
- avoid_trap: 性价比陷阱提醒

### 1.4f 酒店 MICHELIN Keys

```json
"michelin_keys": 3  // 0/1/2/3, 0=无Key
```
替代旧的 michelin_stars(仅餐厅保留)。

### 1.5 价格字段

- 日元字段名以 `_jpy` 结尾，类型为 `number`
- 人民币字段名以 `_cny` 结尾，类型为 `number`
- 汇率: 1 JPY = 0.05 CNY（采集时注明汇率，后续可批量更新）
- 价格范围用数组: `[min, max]`，不用字符串

### 1.6 画像维度（profile）

9个标准维度，用于 `best_for`、`not_suitable_for`、`profile_boosts`：

| 维度码 | 中文 | 说明 |
|--------|------|------|
| first_{city} | 首次XX | 第一次来，3-5天 |
| revisit | 深度复访 | 第二次以上 |
| family_kids | 亲子 | 带小孩 |
| couple | 情侣 | 约会/蜜月 |
| culture_deep | 文化深度 | 历史宗教特别感兴趣 |
| nature_outdoor | 自然户外 | 徒步、自然景观 |
| foodie | 美食控 | 以吃为核心 |
| photo | 拍照党 | 出片优先 |
| time_tight | 时间紧 | 3天以内快节奏 |
| solo | 独行 | 一个人旅行 |
| budget | 预算有限 | 省钱优先 |
| senior | 长辈 | 带老人 |

---

## 二、景点 Schema

### 2.1 完整字段定义

```json
{
  "id": "string — 唯一标识",
  "name_zh": "string — 中文名",
  "name_ja": "string — 日文名",
  "name_en": "string — 英文名",

  "main_type": "enum: fixed_spot | area_dest | experience",
  "sub_type": "enum: 见下表",

  "grade": "enum: S | A | B | C",
  "grade_reason": "string — 评级理由",
  "profile_boosts": { "维度码": "+1 或 -1" },

  "tags": ["string — 标签数组"],

  "city_code": "string — 城市码",
  "prefecture": "string — 府县名",
  "address_ja": "string — 日文地址",
  "nearest_station": "string — 最近车站+步行时间",
  "corridor_tags": ["string — 所属走廊标签"],
  "coord": [latitude, longitude],

  "when": {
    "open_days": "string — 营业日（如'周二至周日'）",
    "open_hours": "string — 'HH:MM-HH:MM' 格式",
    "last_entry": "string — 'HH:MM' 或 null",
    "closed_notes": "string — 定休日说明 + 时间附注",
    "reservation_required": "boolean — 是否需要预约"
  },

  "cost": {
    "admission_jpy": "number — 门票日元，0=免费",
    "typical_spend_jpy": "number — 典型消费（含周边）",
    "budget_tier": "enum: free | budget | moderate | expensive"
  },

  "visit_minutes": "number — 建议游览时间（分钟）",
  "queue_wait_minutes": "number — 平均排队时间",
  "best_time": "string — 最佳游览时段",

  "seasonality": {
    "open_seasons": "string — 物理上可去的季节(硬约束，系统筛选用): 'all' 或 'spring,summer,autumn,winter'",
    "best_season": "string | null — 体验最佳季节(软推荐，不做筛选): 'spring'/'autumn'/null",
    "avoid_season": "string | null — 不建议去的季节",
    "avoid_reason": "string | null — 不建议的原因",
    "seasonal_notes": "string | null — 季节性特殊说明"
  },

  "review_signals": {
    "google_rating": "number — Google评分 1.0-5.0",
    "google_review_count": "number — Google评价数",
    "dimension_scores": {
      "scenery": "number 1-10",
      "cultural_depth": "number 1-10",
      "accessibility": "number 1-10",
      "crowd_comfort": "number 1-10",
      "uniqueness": "number 1-10",
      "value_for_money": "number 1-10"
    },
    "positive_tags": ["string"],
    "negative_tags": ["string"]
  },

  "risk_flags": ["string — 风险标签"],

  "descriptions": {
    "why_selected": "string — 推荐理由",
    "what_to_expect": "string — 体验描述",
    "skip_if": "string — 不适合的情况"
  },

  "tips": "string — 实用贴士",

  "optional_addons": [
    {
      "id": "string",
      "name_zh": "string — 附加体验名称",
      "extra_minutes": "number — 额外时间",
      "extra_cost_jpy": "number",
      "extra_cost_cny": "number",
      "recommended_shops": [{ "name": "string", "booking_url": "string" }],
      "effect": "string — 对行程的影响",
      "best_for": ["string"],
      "skip_if_rain": "boolean"
    }
  ]
}
```

### 2.2 sub_type 枚举

**fixed_spot（固定地点）：**

| 值 | 中文 | 示例 |
|----|------|------|
| culture_art | 文化艺术 | 美术馆、博物馆 |
| history_religion | 历史宗教 | 神社、寺庙、古城 |
| landmark_view | 地标观景 | 展望台、标志性建筑 |
| animal_science | 动物海洋科普 | 水族馆、动物园 |
| nature_scenery | 自然景观 | 公园、山、湖 |
| amusement | 游乐休闲 | 主题乐园 |
| shopping_specialty | 购物特色 | 商场、市场、特色街 |

**area_dest（区域目的地）：**

| 值 | 中文 |
|----|------|
| historic_district | 老城历史区 |
| shopping_district | 商圈购物区 |
| onsen_resort | 温泉/度假区 |

**experience（体验活动）：**

| 值 | 中文 |
|----|------|
| day_trip | 半日/一日游 |
| cultural_exp | 文化体验 |
| outdoor_sport | 户外运动 |
| night_show | 演出夜游 |
| seasonal_event | 节庆限定 |

### 2.3 校验规则

| 规则 | 说明 |
|------|------|
| coord[0] 在 24-46 之间 | 纬度范围（日本） |
| coord[1] 在 122-154 之间 | 经度范围（日本） |
| grade 必须是 S/A/B/C | 不允许 null 或 A+ |
| when.open_hours 匹配 `^\d{2}:\d{2}-\d{2}:\d{2}$` 或 null | 格式校验 |
| when.reservation_required 是 boolean | 不允许缺失 |
| cost.admission_jpy >= 0 | 非负 |
| visit_minutes > 0 | 正数 |

---

## 三、餐厅 Schema

### 3.1 完整字段定义

```json
{
  "id": "string",
  "name_zh": "string",
  "name_ja": "string",
  "name_en": "string",
  "type": "restaurant",

  "cuisine": "string — 菜系码（见枚举表）",
  "cuisine_zh": "string — 中文菜系名",
  "cuisine_sub": "string | null — 子菜系",
  "meal_type": ["lunch", "dinner"],

  "budget_tier": "enum: luxury | premium | mid | budget | street",
  "is_city_must_eat": "boolean",
  "must_eat_reason": "string | null",

  "grade": "enum: S | A | B | C",
  "grade_reason": "string",
  "profile_boosts": { "维度码": "+1 或 -1" },

  "city_code": "string",
  "prefecture": "string",
  "corridor_tags": ["string"],
  "best_pairing_corridors": ["string"],
  "address_ja": "string",
  "nearest_station": "string",
  "coord": [latitude, longitude],

  "when": {
    "open_days": "string",
    "lunch_hours": "string — 'HH:MM-HH:MM' 或 null",
    "dinner_hours": "string — 'HH:MM-HH:MM' 或 null",
    "closed_notes": "string — 定休日 + 时间附注（如'入店截止时间'）"
  },

  "cost": {
    "lunch_min_jpy": "number", "lunch_max_jpy": "number",
    "lunch_min_cny": "number", "lunch_max_cny": "number",
    "dinner_min_jpy": "number | null", "dinner_max_jpy": "number | null",
    "dinner_min_cny": "number | null", "dinner_max_cny": "number | null"
  },

  "review_signals": {
    "tabelog_score": "number | null — Tabelog评分（小吃类可为null）",
    "google_rating": "number — Google评分",
    "michelin_stars": "number — 0/1/2/3",
    "tabelog_award": "string | null — 如'百名店2024'",
    "positive_tags": ["string"],
    "negative_tags": ["string"]
  },

  "wagyu_grade": "enum: kobe_a5 | tajima | omi | matsusaka | a4_wagyu | domestic | null",

  "queue_wait_minutes": "number",
  "requires_reservation": "boolean",
  "reservation_difficulty": "enum: none | easy | medium | hard",
  "reservation_method": "string | null",
  "has_english_menu": "boolean",

  "risk_flags": ["string"],

  "descriptions": {
    "signature_dishes": "string — 招牌菜",
    "why_selected": "string",
    "ordering_hint": "string — 点餐建议",
    "skip_if": "string"
  },

  "tags": ["string"]
}
```

### 3.2 cuisine 菜系码枚举

#### 和食系
| 码 | 日文 | 中文 |
|----|------|------|
| nihon_ryori | 日本料理 | 日本料理/怀石 |
| sushi | 寿司 | 寿司 |
| kaiten_sushi | 回転寿司 | 回转寿司 |
| kaisendon | 海鮮丼 | 海鲜丼 |
| unagi | うなぎ | 鳗鱼 |
| tempura | 天ぷら | 天妇罗 |
| tonkatsu | とんかつ | 炸猪排 |
| kushiage | 串揚げ | 串炸 |
| yakitori | 焼き鳥 | 烤鸡串 |
| sukiyaki | すき焼き | 寿喜烧 |
| shabu | しゃぶしゃぶ | 涮锅 |
| soba | そば | 荞麦面 |
| udon | うどん | 乌冬面 |
| okonomiyaki | お好み焼き | 大阪烧 |
| takoyaki | たこ焼き | 章鱼烧 |
| oden | おでん | 关东煮 |
| tofu | 豆腐料理 | 豆腐料理 |
| kamameshi | 釜飯 | 釜饭 |
| donburi | 丼 | 丼饭 |
| kappo | 割烹 | 割烹 |

#### 肉类系
| 码 | 中文 |
|----|------|
| yakiniku | 烧肉 |
| wagyu_steak | 和牛牛排/铁板烧 |
| kani | 螃蟹料理 |

#### 拉面系
| 码 | 中文 |
|----|------|
| ramen | 拉面 |
| tsukemen | 蘸面 |

#### 洋食系
| 码 | 中文 |
|----|------|
| yoshoku | 日式洋食 |
| french | 法餐 |
| italian | 意餐 |

#### 甜品/咖啡系
| 码 | 中文 |
|----|------|
| matcha_sweets | 抹茶甜品 |
| wagashi | 和果子 |
| cafe | 咖啡/喫茶 |
| kakigori | 刨冰 |
| pan | 面包 |

#### 酒类
| 码 | 中文 |
|----|------|
| izakaya | 居酒屋 |
| sake_bar | 清酒吧 |

#### 特殊
| 码 | 中文 |
|----|------|
| shojin | 精进料理 |
| kawadoko | 川床料理 |
| ryokan_meal | 旅馆料理 |
| korean | 韩国料理 |

### 3.3 budget_tier 定义

| 层级 | 人均(JPY) | 定位 |
|------|-----------|------|
| luxury | 8000+ | 米其林/高端怀石 |
| premium | 3000-8000 | 优质正餐 |
| mid | 1000-3000 | 主力用餐 |
| budget | 500-1000 | 快速解决 |
| street | <500 | 边走边吃 |

### 3.4 校验规则

| 规则 | 说明 |
|------|------|
| grade 只允许 S/A/B/C | 不允许 A+/B+/null |
| lunch_hours 匹配 HH:MM-HH:MM 或 null | 无括号注释 |
| dinner_hours 同上 | 括号内容移到 closed_notes |
| cost._cny = cost._jpy * 0.05 | 汇率一致性 |
| wagyu_grade 只在肉类餐厅使用 | 其他为 null |

---

## 四、酒店 Schema

### 4.1 完整字段定义

```json
{
  "id": "string",
  "name_zh": "string",
  "name_ja": "string",
  "name_en": "string",

  "hotel_type": "enum: 见下表",
  "style_zh": "string — 中文风格描述",

  "area": {
    "city_code": "string",
    "district_zh": "string",
    "district_ja": "string",
    "price_level": "enum: luxury | expensive | moderate | budget | backpacker",
    "corridor_tags": ["string"],
    "best_for_visiting": ["string — 住这里最方便游览的走廊"]
  },

  "pricing": {
    "basis_note": "string — '2人1晚含税参考，是否含餐见price_note'",
    "off_season_jpy": [min, max],
    "regular_season_jpy": [min, max],
    "peak_season_jpy": [min, max],
    "price_level": "enum — 同 area.price_level",
    "last_checked_at": "string — 'YYYY-MM'",
    "price_note": "string — 含餐情况、季节性加价等"
  },

  "experience": {
    "grade": "enum: S | A | B | C — 不允许 null",
    "types": ["enum: onsen | view | heritage | shukubo | machiya | design | meal"],
    "reason": "string | null",
    "highlight": "string | null"
  },

  "access_friction": {
    "level": "enum: low | medium | high",
    "summary": "string — 交通摩擦描述",
    "luggage_friendly": "boolean"
  },

  "best_for": ["string — 画像维度码"],
  "not_suitable_for": ["string"],

  "address_ja": "string",
  "nearest_station": "string",
  "coord": [latitude, longitude],

  "check_in": "string — 'HH:MM'",
  "check_out": "string — 'HH:MM'",
  "meals_included": {
    "breakfast": "boolean",
    "dinner": "boolean"
  },

  "review_impression": {
    "score_range": "string — '4.0-4.5' 格式",
    "vibe": "string — 一句话口碑印象",
    "updated_at": "string — 'YYYY-MM'"
  },

  "occupancy_note": "string — 入住人数/儿童政策简述",
  "booking_tip": "string — 预订建议",
  "risk_flags": ["string"],

  "descriptions": {
    "why_selected": "string",
    "what_to_expect": "string",
    "best_season": "string",
    "skip_if": "string",
    "insider_tip": "string"
  },

  "tags": ["string"]
}
```

### 4.2 hotel_type 枚举

| 码 | 中文 | 说明 |
|----|------|------|
| luxury_ryokan | 顶级旅馆 | 虹夕诺雅、俵屋 |
| ryokan | 温泉/传统旅馆 | 中高档旅馆 |
| business_hotel | 商务酒店 | 东横INN、APA、Dormy Inn |
| city_hotel | 城市酒店 | 万豪、希尔顿 |
| boutique | 精品酒店 | 设计酒店、町屋改造 |
| hostel | 青旅/胶囊 | 背包客 |
| minshuku | 民宿 | 家庭经营 |
| shukubo | 宿坊 | 寺院住宿 |
| guesthouse | 民宿/旅馆 | 小型经营 |

### 4.3 price_level 定义

| 等级 | 2人1晚参考(JPY) | 定位 |
|------|-----------------|------|
| luxury | 50000+ | 顶级体验 |
| expensive | 25000-50000 | 高档 |
| moderate | 12000-25000 | 中档舒适 |
| budget | 6000-12000 | 经济实惠 |
| backpacker | <6000 | 背包客 |

### 4.4 experience.types 枚举

| 类型 | 说明 | 对行程的影响 |
|------|------|-------------|
| onsen | 温泉 | 建议预留泡汤时间 |
| view | 美景 | 建议选景观房 |
| heritage | 历史建筑 | 建筑本身值得参观 |
| shukubo | 宿坊体验 | 含早课+精进料理 |
| machiya | 町屋 | 传统建筑体验 |
| design | 设计酒店 | 建筑/室内设计亮点 |
| meal | 料理旅馆 | 晚餐本身是体验 |

### 4.5 校验规则

| 规则 | 说明 |
|------|------|
| coord[0] 在 24-46 | 纬度（日本） |
| coord[1] 在 122-154 | 经度（日本） |
| experience.grade 必须是 S/A/B/C | 不允许 null |
| check_in 匹配 HH:MM | 如 "15:00" |
| check_out 匹配 HH:MM | 如 "11:00" |
| pricing.*_jpy 是长度2的数组 | [min, max], min <= max |

---

## 五、走廊定义 Schema

走廊是地理上的步行可达区域，用于行程编排的最小单位。

```json
{
  "id": "string — 走廊标签",
  "name_zh": "string",
  "name_ja": "string",
  "city_code": "string",
  "center_coord": [latitude, longitude],
  "radius_km": "number — 步行半径",
  "typical_visit_hours": "number",
  "connects_to": ["string — 相邻走廊"],
  "transit_minutes": { "走廊id": number },
  "cuisine_types": ["string — 该走廊常见菜系"]
}
```

---

## 六、季节活动 Schema

```json
{
  "name_zh": "string",
  "name_ja": "string",
  "location": "string",
  "city_code": "string",
  "event_type": "enum: sakura | autumn_leaves | festival | illumination | fireworks | matsuri | food_event | other",
  "date_range": "string — 如 '3月下旬-4月上旬'",
  "recurring": "enum: annual | one_time",
  "grade": "enum: S | A | B | C",
  "description": "string",
  "tips": "string"
}
```

---

## 七、编辑精选字段（跨品类通用）

以下字段在 MASTER_GUIDE 和 GUIDE_*.md 中被大量引用，适用于所有品类。

### 7.1 selection_tags — 三条标签线

```json
"selection_tags": ["city_icon", "traveler_hot", "local_benchmark"]
```

| 标签 | 含义 | 判断来源 |
|------|------|---------|
| city_icon | 城市身份/文化名片 | 编辑判断 + 权威来源(JNTO/japan-guide/百名店) |
| traveler_hot | 游客高热度 | 携程/小红书/Google评论量 |
| local_benchmark | 本地口碑标杆 | Tabelog高分/Retty/日文博客 |

可多选。如菊乃井 = city_icon + local_benchmark。

### 7.2 value_signal — 性价比信号

```json
"value_signal": {
  "tier_value": "high | medium | low",
  "surprise_factor": "string | null",
  "best_deal_tip": "string | null",
  "avoid_trap": "string | null"
}
```

- `tier_value`: 同预算层内的性价比（不跨层比较）
- `surprise_factor`: 超预期体验（如"12000日元含天然温泉+免费夜宵"）
- `best_deal_tip`: 获取最佳性价比的方法（如"午餐比晚餐便宜60%"）
- `avoid_trap`: 性价比陷阱提醒（如"旺季价格翻3倍"）

### 7.3 indie_quotes — 独立站精选评价

来自独立攻略站博主的原创体验摘录，最多3条。详见 MASTER_GUIDE 第八章。

```json
"indie_quotes": [
  {
    "source": "string — 站名",
    "url": "string — 文章URL",
    "quote": "string — 精选原文摘录",
    "aspect": "string — 评价角度(味道/氛围/排队/性价比/交通等)"
  }
]
```

同时记录独立站加分（前2条满权重，第3条起乘0.5，封顶0.5）:
```json
"indie_boost": {
  "total_score": 0.35,
  "breakdown": [
    {"source": "Inside Kyoto", "level": "strong", "weight": 0.15, "decay": 1.0},
    {"source": "Mimi韩", "level": "normal", "weight": 0.10, "decay": 1.0},
    {"source": "lazyjapan", "level": "normal", "weight": 0.10, "decay": 0.5}
  ]
}
```

### 7.4 house_score — 内部排序分

只在同一决策位内排序用，不跨组比较，不展示给用户。
详见 MASTER_GUIDE 第四b章"评分解释系统"。

```json
"house_score": {
  "base_quality": 4.0,
  "traveler_fit": 0.25,
  "indie_support": 0.35,
  "risk_penalty": -0.25,
  "total": 4.35,
  "notes": "Tabelog品类前10%, 携程评价正面, 2个独立站强推, 预约有一定难度"
}
```

### 7.5 risk_watch — 避雷标记

仅在触发条件下生成（S/A候选、边界升级、高热条目、反差信号）。
详见 MASTER_GUIDE 第四b章"避雷触发机制"。

```json
"risk_watch": {
  "level": "none | mild | medium | high",
  "triggers": ["string — 风险类型: queue/value_gap/language_barrier/booking_hard/unstable/tourist_trap"],
  "evidence": "string — 证据摘要",
  "action": "string — 建议应对"
}
```

风险类型枚举:

| 类型 | 中文 | 说明 |
|------|------|------|
| queue | 排队 | 排队成本高 |
| booking_hard | 预约难 | 需提前很久/经常约满 |
| value_gap | 性价比落差 | 价格与体验不匹配 |
| language_barrier | 语言障碍 | 日文only/沟通困难 |
| unstable | 营业不稳定 | 临时休业/时间不固定 |
| tourist_trap | 游客陷阱 | 过度商业化 |
| access_hard | 交通摩擦 | 位置偏远/换乘复杂 |
| photo_gap | 照骗 | 实际与照片/宣传差距大 |
| single_gimmick | 单一爆品 | 只靠一道菜/一个看点 |

### 7.6 editorial_exclusion — 负向编辑记录

仅在入围池中被淘汰的条目上使用，不出现在终选池中。

```json
"editorial_exclusion": {
  "excluded": true,
  "reason": "string — 淘汰理由",
  "better_alternatives": ["string — 更优替代的entity_id"]
}
```

---

## 七b、Selection Ledger Schema（Phase 2 输出）

> Phase 2 的主输出文件。每个品类一份 JSON，包含所有入选+排除的候选及其证据。
> 详见 PHASE2_PLAN.md v2.0

### 7b.1 Ledger 文件结构

```json
{
  "version": "2.0",
  "generated_at": "ISO 8601 datetime",
  "city_circle": "string — 城市圈码",
  "summary": {
    "total_candidates": "number — 发现池总数",
    "selected": "number — 入选数",
    "excluded": "number — 排除数",
    "by_grade": {"S": 12, "A": 45, "B": 120, "C": 173},
    "by_city": {"kyoto": 130, "osaka": 100}
  },
  "entries": ["array — LedgerEntry 对象"]
}
```

### 7b.2 LedgerEntry 字段

```json
{
  // 基础标识
  "name_ja": "string",
  "city_code": "string",
  "corridor": "string | null — 走廊码(归一化后)",

  // 品类特有（餐厅/酒店/景点各不同）
  "cuisine_type": "string — 标准菜系码（仅餐厅）",
  "budget_tier": "string — luxury/premium/mid/budget/street（仅餐厅）",
  "hotel_type": "string（仅酒店）",
  "price_level": "string（仅酒店）",
  "main_type": "string（仅景点）",
  "sub_type": "string（仅景点）",

  // 选择模型字段
  "selection_slot": "string — slot 键",
  "base_quality_score": "number 2.5-5.0 — 组内 percentile 映射",
  "quality_evidence": "string 50-100字 — quality 轴证据摘要",
  "traveler_fit_modifier": "number -0.5~+0.5",
  "traveler_fit_evidence": "string 30-80字",
  "execution_penalty": "number -1.0~0",
  "execution_evidence": "string 30-80字",
  "risk_watch": "enum: none/mild/medium/high",
  "risk_detail": "string | null — 风险具体说明",
  "indie_support_score": "number 0~0.5",
  "house_score": "number — BaseQuality + TravelerFit + Indie + Risk",

  // 编辑判断
  "grade": "enum: S/A/B/C",
  "selection_tags": ["city_icon", "traveler_hot", "local_benchmark"],
  "editorial_exclusion": "boolean",
  "editorial_exclusion_reason": "string | null",
  "one_line_editorial_note": "string — 一句话选品理由",

  // 元数据
  "score_basis": "enum: tabelog_percentile/ota_rating/michelin_keys/guide_level/group_median",
  "opus_reviewed": "boolean — 是否经过 Opus 审核",
  "data_confidence": "enum: verified/cross_checked/single_source/ai_generated",

  // 原始数据保留（供回溯）
  "raw_tabelog_score": "number | null",
  "raw_michelin": "string | null",
  "raw_ota_rating": "number | null",
  "raw_nightly_jpy": "number | null",
  "raw_source": "string — 原始来源"
}
```

### 7b.3 score_basis 枚举说明

| 值 | 含义 | 使用场景 |
|----|------|---------|
| tabelog_percentile | Tabelog 在组内 percentile | 有 tabelog_score 的餐厅 |
| ota_rating | OTA 星级归一化 | 有 OTA 评分的酒店 |
| michelin_keys | Michelin Keys 直接映射 | 有 Keys 的酒店 |
| guide_level | japan-guide 等级映射 | 景点 |
| group_median | 同组中位数（无直接评分） | 缺少主评分源的条目 |

### 7b.4 Ledger 文件命名

```
data/{city_circle}_spots/
├── restaurants_selection_ledger.json
├── hotels_selection_ledger.json
├── spots_selection_ledger.json
└── selection_excluded.json          # 被排除的候选 + 排除理由
```

---

## 八、文件命名规范

```
data/{city_circle}_spots/
├── taxonomy.json                 # 分类体系定义
├── corridor_definitions.json     # 走廊定义
├── data_sources_registry.json    # 数据源注册
├── {city}_city.json              # 城市景点（如 kyoto_city.json）
├── {city}_extended.json          # 城市周边景点
├── restaurants_{city}_high.json  # 餐厅 luxury+premium
├── restaurants_{city}_mid.json   # 餐厅 mid
├── restaurants_{city}_budget.json # 餐厅 budget
├── restaurants_{city}_street.json # 餐厅 street
├── hotels_{city}.json            # 酒店（可分 _p2, _p3）
├── hotels_onsen.json             # 温泉地酒店
└── hotels_others.json            # 其他地区酒店
```
