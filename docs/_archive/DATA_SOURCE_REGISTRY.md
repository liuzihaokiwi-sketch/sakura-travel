# 数据源注册表（Data Source Registry）

> 每个城市圈的数据采集策略。核心原则：**每个品类用该地区最权威的评价平台，Google Places 只做基础设施层（坐标/营业时间）。**

---

## 一、数据源分层架构

```
┌──────────────────────────────────────────────────┐
│  第一层：权威评分源（决定"推不推荐"）              │
│  → 该品类在该地区最权威的评价平台                  │
│  → 产出：评分、是否值得去、品类标签                │
├──────────────────────────────────────────────────┤
│  第二层：基础设施层（补充结构化数据）              │
│  → Google Places API                             │
│  → 产出：精确坐标、营业时间、place_id、照片引用    │
├──────────────────────────────────────────────────┤
│  第三层：感知层（调分+打标签）                    │
│  → 小红书、马蜂窝、博主攻略                      │
│  → AI 提取标签和推荐理由（不生成数据）            │
│  → 产出：audience_fit 标签、soft_score 调分       │
├──────────────────────────────────────────────────┤
│  第四层：兜底（仅极偏远地区）                     │
│  → AI 生成，必须标记 trust_status='ai_generated'  │
│  → 手账本上注明"建议出发前确认"                   │
└──────────────────────────────────────────────────┘
```

## 二、各城市圈数据源配置

### 北海道圈（sapporo/otaru/hakodate/asahikawa/furano/biei/noboribetsu/niseko/abashiri/kushiro/toya）

| 品类 | 权威源（第一层） | 基础设施（第二层） | 备注 |
|------|-----------------|-------------------|------|
| 景点 | [Japan Guide](https://www.japan-guide.com/list/e1101.html) (1-3星评级) | Google Places API | Japan Guide 对北海道覆盖非常全 |
| 景点 | [Visit Hokkaido 官方](https://www.visit-hokkaido.jp/en/) | — | 北海道官方旅游网站，权威性最高 |
| 景点 | [UU-Hokkaido](https://uu-hokkaido.in/) | — | 北海道专业旅游指南，季节性信息强 |
| 餐厅 | [Tabelog](https://tabelog.com/) (3.5+评分) | Google Places API | 日本餐厅评价最权威，3.5+才算好 |
| 餐厅 | [Retty](https://retty.me/) | — | 实名评价，可信度高，补充 Tabelog |
| 酒店 | [Jalan](https://www.jalan.net/) | Google Places API | 日本本土第一，温泉旅馆覆盖最全 |
| 酒店 | [Rakuten Travel](https://travel.rakuten.com/) | — | 小旅馆/民宿覆盖比 Booking 强 |
| 特色店 | Google Places (keyword搜索) | — | 筛选 type=store + 旅游关键词 |

### 关西圈（tokyo/osaka/kyoto/nara/kobe/hakone/kamakura 等）

| 品类 | 权威源（第一层） | 基础设施（第二层） | 备注 |
|------|-----------------|-------------------|------|
| 景点 | [Japan Guide](https://www.japan-guide.com/) | Google Places API | 关西是 Japan Guide 覆盖最密的区域 |
| 景点 | [GO TOKYO](https://www.gotokyo.org/cn/) / 各市官方旅游网 | — | 东京/京都/大阪各有官方旅游网 |
| 餐厅 | [Tabelog](https://tabelog.com/) | Google Places API | 关西是 Tabelog 数据最密的区域 |
| 餐厅 | [Gurunavi](https://www.gnavi.co.jp/) | — | 预约功能强，补充高端餐厅 |
| 酒店 | [Jalan](https://www.jalan.net/) | Google Places API | 京都町屋/温泉旅馆首选 Jalan |
| 酒店 | [Booking.com](https://www.booking.com/) | — | 城市商务酒店 Booking 价格更优 |
| 特色店 | Google Places + [Hitosara](https://hitosara.com/) | — | Hitosara 高端/手工艺品类强 |

### 广府圈（guangzhou/shenzhen/hongkong/macau/zhuhai/foshan/shunde）

| 品类 | 权威源（第一层） | 基础设施（第二层） | 备注 |
|------|-----------------|-------------------|------|
| 景点 | [携程攻略](https://you.ctrip.com/) | Google Places API (港澳) / 高德 (内地) | 内地景点携程覆盖最全 |
| 景点 | [马蜂窝](https://www.mafengwo.cn/) | — | 游记型攻略，深度信息多 |
| 餐厅(广深) | [大众点评·必吃榜](https://www.dianping.com/) | 高德 API | 3.63亿条评价，国内最权威 |
| 餐厅(香港) | [OpenRice 开饭喇](https://www.openrice.com/zh/hongkong) | Google Places API | 香港美食第一平台 |
| 餐厅(澳门) | [大众点评](https://www.dianping.com/) + OpenRice | — | 两者互补 |
| 餐厅(顺德) | [大众点评](https://www.dianping.com/) | — | 顺德美食全国闻名，点评数据密 |
| 酒店(广深) | [携程](https://hotels.ctrip.com/) | — | 内地酒店携程最全最准 |
| 酒店(港澳) | [Booking.com](https://www.booking.com/) | Google Places API | 国际平台港澳覆盖好 |
| 特色店 | [大众点评](https://www.dianping.com/) 搜"手信/特产/文创" | — | 点评有"购物"分类 |

### 北疆圈（urumqi/yili/altay/burqin/kanas/hemu/nalati/sailimu）

| 品类 | 权威源（第一层） | 基础设施（第二层） | 备注 |
|------|-----------------|-------------------|------|
| 景点 | [携程攻略](https://you.ctrip.com/) | 高德 API | 北疆景点携程覆盖最全 |
| 景点 | [马蜂窝](https://www.mafengwo.cn/) | — | 北疆自驾/徒步游记非常丰富 |
| 餐厅 | [大众点评](https://www.dianping.com/) | 高德 API | 乌鲁木齐覆盖尚可，小城市数据少 |
| 餐厅 | [小红书](https://www.xiaohongshu.com/) | — | 北疆美食推荐小红书反而更活跃 |
| 酒店 | [携程](https://hotels.ctrip.com/) | — | 北疆偏远地区携程是唯一选择 |
| 特色店 | 小红书搜"新疆手信/特产" | — | 北疆特色店信息来源有限 |

### 潮汕圈（chaozhou/shantou/meizhou）

| 品类 | 权威源（第一层） | 基础设施（第二层） | 备注 |
|------|-----------------|-------------------|------|
| 景点 | [携程攻略](https://you.ctrip.com/) + [马蜂窝](https://www.mafengwo.cn/) | 高德 API | — |
| 餐厅 | [大众点评](https://www.dianping.com/) | — | 潮汕美食是核心卖点，点评数据关键 |
| 酒店 | [携程](https://hotels.ctrip.com/) | — | — |

### 华东圈（shanghai/hangzhou/suzhou/nanjing/wuxi/wuzhen 等）

| 品类 | 权威源（第一层） | 基础设施（第二层） | 备注 |
|------|-----------------|-------------------|------|
| 景点 | [携程攻略](https://you.ctrip.com/) | 高德 API | — |
| 餐厅 | [大众点评·必吃榜](https://www.dianping.com/) | — | 上海/杭州是点评必吃榜重镇 |
| 餐厅 | [携程美食林](https://you.ctrip.com/foodrank/) | — | 携程美食林对高端餐厅覆盖好 |
| 酒店 | [携程](https://hotels.ctrip.com/) | — | — |

---

## 三、数据源优先级 & 合并规则

### 同一实体多数据源时的合并策略

```
评分取权威源：
  日本餐厅 → Tabelog 评分优先（3.0-5.0），Google 评分仅参考
  日本酒店 → Jalan/Rakuten 评分优先
  中国餐厅 → 大众点评评分优先
  中国酒店 → 携程评分优先
  香港餐厅 → OpenRice 评分优先

坐标取 Google/高德：
  精度最高，且有 place_id 防重复

名称取权威源：
  日本用 name_ja（Tabelog/Jalan 原文）
  中国用 name_zh（大众点评/携程原文）
  name_en 从 Google Places 补充

营业时间取 Google Places：
  Google 的营业时间最实时

照片取多源：
  Google Places Photo API（有版权）
  权威源官网图片（需注意版权）
  assets/ 目录手动收集的图片
```

### trust_status 自动标记规则

| 数据来源 | trust_status | data_tier |
|----------|-------------|-----------|
| Japan Guide / Visit Hokkaido 官方 | unverified | S |
| Tabelog 3.5+ / 大众点评必吃榜 | unverified | A |
| Google Places / Jalan / 携程 | unverified | A |
| Tabelog 3.0-3.5 / 普通大众点评 | unverified | B |
| 小红书/马蜂窝 攻略提取 | unverified | B |
| AI 生成（兜底） | ai_generated | C |
| 坐标异常/名称疑似重复 | suspicious | — |

---

## 四、爬虫开发优先级

### 立即（北海道验证必须）
1. **Japan Guide 景点爬虫** — HTML 解析，提取景点名、评级、描述
2. **Tabelog 餐厅爬虫** — 已有，扩展覆盖北海道全部城市
3. **Jalan 酒店爬虫** — 搜索结果页 HTML 解析
4. **Google Places 基础设施补充** — 已有，用于补坐标/营业时间

### 短期（广府圈上线）
5. **大众点评餐厅爬虫** — 已有框架，完善反爬
6. **OpenRice 香港餐厅爬虫** — 新建
7. **携程酒店/景点爬虫** — 已有框架，完善

### 中期（感知层）
8. **小红书标签提取** — AI 读攻略文本 → 提取标签
9. **马蜂窝游记解析** — 提取推荐理由

---

## 五、数据库设计扩展

### entity_base 新增字段（已有的 trust_status 基础上）
```sql
-- 记录每个字段的数据来源
-- 已有 entity_field_provenance 表可以复用
```

### 新表：data_source_registry（数据源注册）
```sql
CREATE TABLE data_source_registry (
  source_id    SERIAL PRIMARY KEY,
  source_name  VARCHAR(50) UNIQUE NOT NULL,  -- 'tabelog', 'japan_guide', 'dianping', ...
  source_type  VARCHAR(20) NOT NULL,          -- 'rating', 'infrastructure', 'perception'
  base_url     VARCHAR(500),
  coverage     JSONB,                         -- {"countries": ["JP"], "cities": ["sapporo",...]}
  entity_types VARCHAR(100)[],                -- ['restaurant', 'poi', 'hotel']
  priority     SMALLINT DEFAULT 50,           -- 权威度排序，1=最高
  is_active    BOOLEAN DEFAULT TRUE,
  rate_limit   JSONB,                         -- {"requests_per_minute": 10, "daily_limit": 500}
  auth_config  JSONB,                         -- {"api_key_env": "TABELOG_API_KEY"}
  notes        TEXT
);
```

### 新表：entity_source_scores（多源评分）
```sql
CREATE TABLE entity_source_scores (
  id          SERIAL PRIMARY KEY,
  entity_id   UUID REFERENCES entity_base(entity_id),
  source_name VARCHAR(50) NOT NULL,           -- 'tabelog', 'jalan', 'dianping', ...
  raw_score   NUMERIC(4,2),                   -- 原始评分（各平台量纲不同）
  normalized_score NUMERIC(4,2),              -- 归一化到 0-100
  review_count INTEGER,
  fetched_at  TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(entity_id, source_name)
);
```

这样每个实体可以有多个平台的评分，推荐引擎综合多源评分做决策，而不是只看一个数。
