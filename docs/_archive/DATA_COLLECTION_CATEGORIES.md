# 数据采集分类体系 & 推荐匹配架构

---

## 一、城市数据覆盖管理

### 新表：city_data_coverage

不是按"数据源"维护，而是按"城市×品类"维护采集进度：

```sql
CREATE TABLE city_data_coverage (
    id              SERIAL PRIMARY KEY,
    city_code       VARCHAR(50) NOT NULL,
    entity_type     VARCHAR(20) NOT NULL,     -- 'poi' / 'restaurant' / 'hotel'
    sub_category    VARCHAR(50),              -- 'ramen' / 'budget_hotel' / 'shrine' 等

    -- 目标 & 进度
    target_count    INTEGER NOT NULL,          -- 这个城市这个品类应该有多少个
    current_count   INTEGER DEFAULT 0,         -- 当前有多少个
    verified_count  INTEGER DEFAULT 0,         -- 其中已验证的

    -- 数据源覆盖
    sources_used    VARCHAR(50)[],             -- 已经从哪些源拉过 ['tabelog', 'google_places']
    sources_pending VARCHAR(50)[],             -- 还没拉的 ['jalan', 'retty']

    -- 状态
    coverage_pct    NUMERIC(5,2) GENERATED ALWAYS AS
                    (CASE WHEN target_count > 0
                     THEN LEAST(100.0, current_count * 100.0 / target_count)
                     ELSE 0 END) STORED,
    last_updated    TIMESTAMPTZ DEFAULT NOW(),
    notes           TEXT,

    UNIQUE(city_code, entity_type, sub_category)
);
```

### 各城市目标数量

**大城市**（札幌、东京、大阪、广州、深圳、香港）：

| 品类 | 子分类 | 目标数量 | 说明 |
|------|--------|----------|------|
| 景点 | 神社寺庙 | 15-20 | — |
| 景点 | 博物馆美术馆 | 10-15 | — |
| 景点 | 公园自然 | 10-15 | — |
| 景点 | 商业街区 | 5-10 | — |
| 景点 | 展望台地标 | 5-8 | — |
| 景点 | 温泉 | 5-10 | 视城市而定 |
| 景点 | 特色体验 | 5-10 | 手工艺/茶道等 |
| 餐厅 | 拉面 | 15-20 | 日本城市 |
| 餐厅 | 寿司海鲜 | 15-20 | — |
| 餐厅 | 居酒屋 | 10-15 | — |
| 餐厅 | 烤肉/成吉思汗 | 10 | 北海道特色 |
| 餐厅 | 汤咖喱 | 5-8 | 北海道特色 |
| 餐厅 | 甜品咖啡 | 10-15 | — |
| 餐厅 | 早餐/朝食 | 5-8 | 行程需要 |
| 餐厅 | 高档和食/怀石 | 5-8 | premium客户 |
| 酒店 | budget 经济 | 10-15 | 商务酒店/胶囊/青旅 |
| 酒店 | mid 中档 | 15-20 | 城市酒店/连锁 |
| 酒店 | premium 高档 | 10-15 | 温泉旅馆/度假 |
| 酒店 | luxury 豪华 | 5-8 | 五星/高端ryokan |
| 特色店 | 手信特产 | 10-15 | — |
| 特色店 | 手工艺品 | 5-8 | — |
| **合计** | — | **200-350** | — |

**中型城市**（函馆、小樽、旭川、佛山、顺德）：

| 品类 | 目标 |
|------|------|
| 景点（全分类） | 30-50 |
| 餐厅（全分类） | 40-80 |
| 酒店（全档位） | 20-40 |
| 特色店 | 5-10 |
| **合计** | **100-180** |

**小城市**（美瑛、登别、布尔津、禾木）：

| 品类 | 目标 |
|------|------|
| 景点 | 10-20 |
| 餐厅 | 10-20 |
| 酒店 | 5-15 |
| 特色店 | 2-5 |
| **合计** | **30-60** |

**北海道总计**（10 个城市）：**约 1500-2000 个实体**

---

## 二、酒店采集分类

Google Places 搜酒店时，按子分类分别搜索，确保各档位覆盖：

```python
HOTEL_SEARCH_CATEGORIES = {
    "JP": [
        # (keyword, price_tier, hotel_type)
        ("ビジネスホテル", "budget", "business"),           # 商务酒店
        ("カプセルホテル", "budget", "capsule"),             # 胶囊旅馆
        ("ゲストハウス ホステル", "budget", "hostel"),       # 青旅
        ("シティホテル", "mid", "city_hotel"),               # 城市酒店
        ("東横イン ルートイン アパホテル", "mid", "chain"),   # 连锁酒店
        ("温泉旅館", "premium", "ryokan"),                   # 温泉旅馆
        ("リゾートホテル", "premium", "resort"),              # 度假酒店
        ("ラグジュアリーホテル 高級旅館", "luxury", "luxury"),# 高档
    ],
    "CN": [
        ("快捷酒店 如家 汉庭", "budget", "budget"),
        ("酒店", "mid", "city_hotel"),
        ("度假酒店 温泉酒店", "premium", "resort"),
        ("五星级酒店 奢华酒店", "luxury", "luxury"),
        ("民宿 精品酒店", "mid", "boutique"),
    ],
}
```

### Tabelog 搜酒店 → 不搜

Tabelog 是餐厅平台，不搜酒店。酒店用：
- 日本：Google Places + Jalan（后续） + Rakuten Travel（后续）
- 中国：携程 + Google Places（港澳）

---

## 三、餐厅采集分类

### 日本城市

```python
RESTAURANT_SEARCH_CATEGORIES_JP = {
    # Tabelog 按菜系分类搜索
    "tabelog": [
        ("RC020101", "sushi", "寿司"),
        ("RC040201", "ramen", "ラーメン"),
        ("RC010101", "kaiseki", "懐石/会席料理"),
        ("RC010401", "tempura", "天ぷら"),
        ("RC010301", "yakitori", "焼き鳥"),
        ("RC010601", "udon", "うどん/蕎麦"),
        ("RC040101", "izakaya", "居酒屋"),
        ("RC020201", "seafood", "海鮮"),
        ("RC120301", "curry", "カレー"),        # 汤咖喱
        ("RC990101", "cafe", "カフェ"),
        ("RC011201", "yakiniku", "焼肉"),
        ("RC011101", "sukiyaki", "すき焼き/しゃぶしゃぶ"),
    ],
    # Google Places 按关键词补充 Tabelog 缺的
    "google_places": [
        ("朝食 モーニング", "breakfast", "早餐"),
        ("スイーツ パフェ", "sweets", "甜品"),
        ("ジンギスカン", "genghis_khan", "成吉思汗烤肉"),  # 北海道特色
        ("スープカレー", "soup_curry", "汤咖喱"),            # 北海道特色
    ],
}
```

### 中国城市

```python
RESTAURANT_SEARCH_CATEGORIES_CN = {
    # 大众点评按菜系搜索
    "dianping": [
        ("粤菜", "cantonese"),
        ("早茶 茶餐厅", "dimsum"),
        ("潮汕菜", "teochew"),
        ("客家菜", "hakka"),
        ("火锅", "hotpot"),
        ("烧烤 烤肉", "bbq"),
        ("海鲜", "seafood"),
        ("面食 粉面", "noodles"),
        ("小吃 街头美食", "snack"),
        ("西餐", "western"),
        ("日料", "japanese"),
        ("咖啡 甜品", "cafe"),
    ],
    # 香港用 OpenRice 分类
    "openrice_hk": [
        ("中菜", "chinese"),
        ("日本菜", "japanese"),
        ("西式", "western"),
        ("茶餐廳", "cha_chaan_teng"),
        ("甜品", "dessert"),
        ("火鍋", "hotpot"),
    ],
}
```

---

## 四、推荐匹配三层架构

```
用户请求进来
    │
    ▼
┌─────────────────────────────┐
│  第一层：标签筛选（硬过滤）    │
│                             │
│  用户说"不吃生的"             │
│  → 排除 sushi, sashimi 标签  │
│                             │
│  用户带 3 岁小孩              │
│  → 排除 child_friendly=no    │
│                             │
│  用户预算经济                  │
│  → 排除 price_tier=luxury    │
│                             │
│  产出：候选池（可能 200→80）  │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  第二层：评分排序（软排序）    │
│                             │
│  Tabelog 3.8 > 3.5           │
│  Google 4.5 > 4.0            │
│  多源评分加权综合              │
│                             │
│  A 餐厅 综合 85 分            │
│  B 餐厅 综合 78 分            │
│                             │
│  产出：排序后候选（80→80）    │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  第三层：AI 个性化匹配        │
│                             │
│  输入给 AI：                  │
│  - 用户画像：couple, 蜜月旅行,│
│    喜欢安静, 预算中档,         │
│    第一次来北海道              │
│  - 候选实体的维度信息：        │
│    A 餐厅：招牌味噌拉面,      │
│    排队20分钟, 氛围热闹嘈杂    │
│    B 餐厅：创意法日融合,       │
│    需预约, 氛围安静浪漫         │
│                             │
│  AI 判断：                    │
│  - B 更适合（蜜月+安静偏好）  │
│  - 生成推荐理由：              │
│    "适合二人世界的法日融合餐厅，│
│     需提前 2 天预约"           │
│                             │
│  产出：最终推荐 + 理由         │
└─────────────────────────────┘
```

### AI 匹配的输入格式

```json
{
  "user_profile": {
    "party_type": "couple",
    "trip_purpose": "honeymoon",
    "preferences": ["quiet", "romantic", "local_experience"],
    "avoid": ["crowded", "tourist_trap"],
    "budget_level": "mid",
    "first_visit": true,
    "dietary": ["no_raw_fish"],
    "mobility": "normal",
    "children": []
  },
  "candidate_entity": {
    "name": "XXX餐厅",
    "type": "restaurant",
    "cuisine": "french_japanese_fusion",
    "review_dimensions": {
      "signature_dish_clarity": "clear",
      "queue_risk": "none",
      "reservation_difficulty": "hard",
      "language_friendliness": "english_ok",
      "value_perception": "above"
    },
    "review_summaries": {
      "why_go": "法日融合创意料理，北海道食材为主，摆盘精致",
      "practical_tip": "需提前2天电话预约，可用英语沟通",
      "skip_if": "预算有限的话性价比不高，人均8000日元"
    },
    "tags": ["romantic", "quiet", "reservation_required", "local_ingredients"],
    "tabelog_score": 3.72,
    "google_rating": 4.4,
    "price_range": "6000-10000 JPY"
  }
}
```

AI 返回：

```json
{
  "match_score": 92,
  "match_reason": "蜜月旅行首选，环境安静浪漫，北海道本地食材体验感强",
  "booking_note": "建议出发前2天预约晚餐18:30时段",
  "alternative_if_full": "同区域的XXX也适合，无需预约"
}
```

### 为什么不全交给 AI

- 标签筛选用规则比 AI 快 1000 倍（毫秒 vs 秒），而且确定性——"不吃生的"就是不吃，不需要 AI 判断
- 评分排序用算法比 AI 一致性好——每次跑结果一样，AI 可能每次给不同排序
- AI 只处理最终的 10-20 个候选，成本可控（不是对 200 个都调 AI）

---

## 五、与现有系统的对接

### soft_scores 12 维度 → 标签 + AI 匹配的关系

现有的 `entity_soft_scores` 表有 12 个维度：
```
emotional_value, shareability, relaxation_feel, memory_point,
localness, smoothness, food_certainty, night_completion,
recovery_friendliness, weather_resilience_soft,
professional_judgement_feel, preview_conversion_power
```

这些维度可以继续保留作为评分排序的参考，但**不作为 AI 匹配的输入**——AI 匹配的输入应该是更直观的维度描述（review_dimensions）和标签，而不是 0-100 的抽象分数。

### scorer.py 的调整

```
当前：base_score × editorial_boost × rotation_penalty
改为：
  1. 标签硬过滤 → 候选池
  2. 多源评分加权 → 排序分
     tabelog_score × 0.4 + google_rating × 0.2 + soft_score × 0.2 + editorial_boost × 0.2
  3. trust_status 调权 → verified ×1.0, unverified ×0.9, ai_generated ×0.5
  4. rotation_penalty → 避免重复推荐
  5. AI 匹配 → 最终个性化排序
```
