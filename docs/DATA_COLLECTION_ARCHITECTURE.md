# 数据采集架构设计

> 从第一性原理出发：我们卖的是"确定性"——用户拿着手账本照着走不会出错。
> 所以数据采集的核心目标不是"量大"，而是"每一条都可靠、可执行"。

---

## 一、整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    数据源注册中心                             │
│         data_source_registry 表                              │
│    记录每个数据源的：URL、覆盖城市、品类、采集频率、          │
│    认证方式、速率限制、当前状态                               │
│    → 所有爬虫从这里读配置，不硬编码                          │
└───────────────┬─────────────────────────────────────────────┘
                │
    ┌───────────┼───────────────┐
    ▼           ▼               ▼
┌────────┐ ┌────────┐   ┌────────────┐
│ 即时层 │ │ 定时层 │   │ 手动/API层 │
│(秒级)  │ │(日/周) │   │(按需)      │
└────┬───┘ └────┬───┘   └─────┬──────┘
     │          │              │
     ▼          ▼              ▼
┌──────────────────────────────────────┐
│          采集调度器                    │
│   CrawlScheduler                     │
│   - 读 data_source_registry          │
│   - 按城市×品类×数据源 分发任务       │
│   - 尊重速率限制                      │
│   - 失败重试 + 熔断                   │
└───────────────┬──────────────────────┘
                │
                ▼
┌──────────────────────────────────────┐
│          原始数据存储                  │
│   source_snapshots 表                │
│   - 保存爬虫原始响应                  │
│   - 带 TTL，过期自动清理              │
│   - 所有后续处理从这里读，不重复爬     │
└───────────────┬──────────────────────┘
                │
                ▼
┌──────────────────────────────────────┐
│          数据加工管线                  │
│   1. 解析 → 结构化字段               │
│   2. 去重 → dedup engine             │
│   3. 合并 → 多源同一实体合并          │
│   4. 评价提取 → AI 从评论中提取维度   │
│   5. 写入 → upsert_entity            │
└──────────────────────────────────────┘
```

---

## 二、数据源注册中心

### 表结构

```sql
CREATE TABLE data_source_registry (
    source_id       SERIAL PRIMARY KEY,
    source_name     VARCHAR(50) UNIQUE NOT NULL,
    display_name    VARCHAR(100) NOT NULL,
    source_type     VARCHAR(20) NOT NULL,        -- 'rating' / 'infrastructure' / 'perception'
    source_layer    SMALLINT NOT NULL DEFAULT 1,  -- 1=权威评分 2=基础设施 3=感知层 4=兜底

    -- 覆盖范围
    countries       VARCHAR(10)[] NOT NULL,       -- ['JP', 'CN', 'HK']
    city_codes      VARCHAR(50)[],                -- NULL=该国全部城市，否则指定
    entity_types    VARCHAR(20)[] NOT NULL,        -- ['restaurant', 'poi', 'hotel']

    -- 采集配置
    crawler_module  VARCHAR(200),                 -- 'app.domains.catalog.crawlers.tabelog'
    crawler_func    VARCHAR(100),                 -- 'fetch_tabelog_restaurants'
    auth_type       VARCHAR(20) DEFAULT 'none',   -- 'none' / 'api_key' / 'cookie' / 'oauth'
    auth_config     JSONB,                        -- {"env_var": "TABELOG_API_KEY"}
    rate_limit      JSONB NOT NULL DEFAULT '{"rpm": 10, "daily": 500}',
    base_url        VARCHAR(500),

    -- 调度
    crawl_frequency VARCHAR(20) DEFAULT 'weekly', -- 'realtime' / 'daily' / 'weekly' / 'monthly' / 'manual'
    priority        SMALLINT DEFAULT 50,          -- 同品类多源时的优先级，1=最高
    last_crawl_at   TIMESTAMPTZ,
    next_crawl_at   TIMESTAMPTZ,

    -- 状态
    status          VARCHAR(20) DEFAULT 'active', -- 'active' / 'paused' / 'broken' / 'pending_api'
    error_count     INTEGER DEFAULT 0,
    last_error      TEXT,
    notes           TEXT,

    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 初始数据

```sql
-- ═══ 第一层：权威评分源 ═══

-- 日本景点
INSERT INTO data_source_registry (source_name, display_name, source_type, source_layer,
    countries, entity_types, crawl_frequency, priority, status, notes)
VALUES
('japan_guide', 'Japan Guide', 'rating', 1,
    '{JP}', '{poi}', 'monthly', 10, 'active',
    '最权威英文日本旅游指南，1-3星评级体系，HTML爬取'),

('visit_hokkaido', 'Visit Hokkaido 官方', 'rating', 1,
    '{JP}', '{poi}', 'monthly', 5,  'active',
    '北海道官方旅游网站'),

-- 日本餐厅
('tabelog', 'Tabelog 食べログ', 'rating', 1,
    '{JP}', '{restaurant}', 'weekly', 10, 'active',
    '日本餐厅评价最权威，3.5+才算好店，已有爬虫'),

('retty', 'Retty', 'rating', 1,
    '{JP}', '{restaurant}', 'monthly', 30, 'pending_api',
    '实名评价系统，可信度高，需要研究采集方式'),

-- 日本酒店
('jalan', 'Jalan じゃらん', 'rating', 1,
    '{JP}', '{hotel}', 'weekly', 10, 'pending_api',
    '日本本土第一订房平台，温泉旅馆覆盖最全'),

('rakuten_travel', 'Rakuten Travel', 'rating', 1,
    '{JP}', '{hotel}', 'monthly', 20, 'pending_api',
    '小旅馆/民宿覆盖强，需研究采集方式'),

-- 中国餐厅
('dianping', '大众点评', 'rating', 1,
    '{CN}', '{restaurant,poi}', 'weekly', 10, 'active',
    '3.63亿条评价，国内最权威，已有爬虫框架'),

('dianping_bichilist', '大众点评·必吃榜', 'rating', 1,
    '{CN}', '{restaurant}', 'monthly', 5, 'pending_api',
    '万里挑一的必吃餐厅，权威性最高'),

-- 香港餐厅
('openrice', 'OpenRice 开饭喇', 'rating', 1,
    '{HK}', '{restaurant}', 'weekly', 10, 'pending_api',
    '香港美食第一平台，需建爬虫'),

-- 中国景点/酒店
('ctrip', '携程', 'rating', 1,
    '{CN}', '{poi,hotel}', 'weekly', 10, 'active',
    '内地景点酒店最全，已有爬虫框架'),

('mafengwo', '马蜂窝', 'rating', 1,
    '{CN}', '{poi}', 'monthly', 20, 'pending_api',
    '游记型攻略，深度信息多，需研究采集方式'),

-- ═══ 第二层：基础设施 ═══

('google_places', 'Google Places API', 'infrastructure', 2,
    '{JP,HK,MO}', '{poi,restaurant,hotel}', 'weekly', 10, 'active',
    '坐标/营业时间/place_id，已有爬虫，$200/月免费额度'),

('amap', '高德地图 API', 'infrastructure', 2,
    '{CN}', '{poi,restaurant,hotel}', 'weekly', 10, 'pending_api',
    '中国城市坐标/营业时间，需申请API key'),

-- ═══ 第三层：感知层 ═══

('xiaohongshu', '小红书', 'perception', 3,
    '{CN,JP}', '{poi,restaurant,hotel}', 'monthly', 30, 'pending_api',
    '博主攻略提取标签和推荐理由，中文游客视角'),

('tripadvisor', 'TripAdvisor', 'perception', 3,
    '{JP}', '{poi,restaurant,hotel}', 'monthly', 40, 'pending_api',
    '国际游客评价，英文评论多');
```

---

## 三、城市数据源配置

每个城市不需要单独配置——通过 `data_source_registry` 的 `countries` 和 `city_codes` 字段自动匹配。

但有些数据源只覆盖特定城市，用 `city_codes` 限定：

```sql
-- Visit Hokkaido 只覆盖北海道城市
UPDATE data_source_registry SET city_codes =
    '{sapporo,otaru,hakodate,asahikawa,furano,biei,noboribetsu,niseko,abashiri,kushiro,toya}'
WHERE source_name = 'visit_hokkaido';

-- OpenRice 只覆盖香港（澳门用大众点评）
UPDATE data_source_registry SET city_codes = '{hongkong}'
WHERE source_name = 'openrice';
```

### 查询某城市可用的数据源

```sql
SELECT source_name, display_name, entity_types, priority, status
FROM data_source_registry
WHERE is_active = TRUE
  AND 'JP' = ANY(countries)
  AND (city_codes IS NULL OR 'sapporo' = ANY(city_codes))
  AND 'restaurant' = ANY(entity_types)
ORDER BY source_layer, priority;

-- 结果：
-- tabelog     | Tabelog    | {restaurant} | 10 | active
-- retty      | Retty      | {restaurant} | 30 | pending_api
-- google_places | Google  | {poi,restaurant,hotel} | 10 | active
```

---

## 四、采集调度器设计

### 核心逻辑

```python
class CrawlScheduler:
    """
    数据采集调度器

    职责：
    1. 从 data_source_registry 读取活跃数据源
    2. 按城市×品类×数据源生成采集任务
    3. 尊重速率限制和采集频率
    4. 失败重试 + 熔断（连续失败 5 次暂停该源）
    """

    async def get_pending_tasks(self, city_code: str = None) -> list[CrawlTask]:
        """获取待执行的采集任务"""
        # 查 data_source_registry 中 next_crawl_at < now() 的活跃源
        # 按 priority 排序
        # 返回 CrawlTask 列表

    async def execute_task(self, task: CrawlTask) -> CrawlResult:
        """执行单个采集任务"""
        # 1. 检查速率限制
        # 2. 调用对应的 crawler_module.crawler_func
        # 3. 保存原始数据到 source_snapshots
        # 4. 更新 last_crawl_at, next_crawl_at
        # 5. 失败时更新 error_count, last_error
        # 6. 连续失败 5 次 → status = 'broken'

    async def run_city(self, city_code: str):
        """采集一个城市的所有数据"""
        tasks = await self.get_pending_tasks(city_code)
        for task in tasks:
            await self.execute_task(task)
            await asyncio.sleep(task.rate_limit_interval)
```

### 采集频率策略

| 频率 | 适用场景 | 说明 |
|------|----------|------|
| realtime | 无 | 我们不需要实时数据 |
| daily | 无 | 目前没有日更需求 |
| weekly | Tabelog/Google/携程/大众点评 | 核心数据源，一周更新一次评分和营业状态 |
| monthly | Japan Guide/Jalan/小红书/马蜂窝 | 内容变化慢，一月一次够了 |
| manual | 官方旅游网站/特殊数据 | 你手动触发或我帮你跑 |

### 速率限制

不同数据源的限制差异很大：

| 数据源 | 限制 | 策略 |
|--------|------|------|
| Google Places API | $200/月免费 ≈ 6000次 | 每日 200 次硬上限 |
| Tabelog | 无 API，HTML 爬取 | 3-5 秒/次，User-Agent 轮换 |
| 大众点评 | 反爬强，有验证码 | 5-10 秒/次，遇验证码停止 |
| 携程 | 移动端 API 相对宽松 | 2-3 秒/次 |
| Japan Guide | 静态页面 | 1 秒/次，月更就行 |

---

## 五、渐进式采集策略

核心思想：**先建骨架，再填肉，不追求一步到位。**

### Phase 0：骨架（现在就做）

**目标**：每个城市有最基本的可用数据，generate_trip 能跑通。

```
做什么：
  - Google Places 拉每个城市的 POI/餐厅/酒店（坐标+评分）
  - Tabelog 拉北海道餐厅（已有爬虫，扩展覆盖）
  - 手动确认 anchor_entities 的核心实体（你在管理后台审核）

数据量：每城市 30-50 个实体
数据质量：坐标准确，评分来自权威源，trust_status = unverified
耗时：1-2 天
```

### Phase 1：权威评分（本周）

**目标**：核心实体有权威源评分，可以支撑推荐决策。

```
做什么：
  - Japan Guide 爬虫建好，拉北海道+关西景点（带评级）
  - Tabelog 全量拉北海道（3.0+ 的餐厅）
  - Jalan 爬虫建好，拉北海道酒店（带评分和价格）
  - 大众点评拉广深港核心餐厅

数据量：每城市 100-200 个实体
数据质量：有权威源评分，有坐标，trust_status 按规则标记
耗时：1 周
```

### Phase 2：评价维度（本月）

**目标**：核心实体有结构化维度评分和一句话摘要。

```
做什么：
  - 从 Tabelog/大众点评 拉评论原文（每个实体 top 50 条）
  - AI 提取维度评分和摘要
  - 写入 entity_descriptions 和 entity_review_signals
  - 你在管理后台抽查审核

数据量：核心实体约 500 个有完整评价维度
耗时：2-3 周（大部分时间是 AI 处理评论）
```

### Phase 3：感知层（下月）

**目标**：标签系统丰富，推荐更精准。

```
做什么：
  - 小红书/马蜂窝攻略爬取
  - AI 提取标签（family_friendly, photo_spot, rainy_day_ok 等）
  - 调整 soft_scores 各维度
  - 如果有正规 API 合作，接入替换爬虫

数据量：标签覆盖 80% 核心实体
耗时：持续迭代
```

### Phase ∞：持续维护

```
每周：
  - Tabelog/大众点评/Google 自动刷新评分
  - 检测歇业/搬迁（Google Places 状态变化）
  - 新开店检测（评论数从 0 开始增长的实体）

每月：
  - Japan Guide/Jalan 评分更新
  - 评论增量爬取 → 更新维度评分
  - 清理过期 snapshot

你手动：
  - 管理后台审核 trust_status
  - 标记编辑精选（data_tier = 'S'）
  - 接入新的正规 API → 在 data_source_registry 中注册
```

---

## 六、正规 API 接入预留

你提到后面可能找正规 API 合作。架构已经预留了：

### data_source_registry 的 auth_type 支持

```
auth_type = 'none'     → 公开数据，直接爬
auth_type = 'api_key'  → 简单 API key（Google Places 这种）
auth_type = 'oauth'    → OAuth 认证（正规合作伙伴 API）
auth_type = 'cookie'   → 需要登录态（爬虫用）
auth_type = 'partner'  → 合作伙伴专属接口
```

### 接入新 API 的流程

```
1. 在 data_source_registry 插入一条记录
   - 指定 crawler_module 和 crawler_func
   - 设置 auth_type 和 auth_config
   - 设置 rate_limit 和 crawl_frequency

2. 写一个 crawler 文件（统一接口）
   async def fetch_xxx(city_code: str, limit: int) -> list[dict]:
       # 返回 upsert_entity 兼容格式

3. pipeline 自动发现并使用（通过 registry 的 priority 排序）
```

不需要改 pipeline 代码——调度器从 registry 读配置，自动选择该城市该品类优先级最高的活跃数据源。

---

## 七、爬虫模块统一接口

所有爬虫遵循统一接口，方便替换和扩展：

```python
# app/domains/catalog/crawlers/base.py

class CrawlerResult:
    entities: list[dict]       # upsert_entity 兼容格式
    raw_snapshots: list[dict]  # 原始数据，存 source_snapshots
    errors: list[str]
    source_name: str
    city_code: str
    entity_type: str

class BaseCrawler:
    source_name: str           # 对应 data_source_registry.source_name

    async def fetch(
        self,
        city_code: str,
        entity_type: str,
        limit: int = 50,
        **kwargs,
    ) -> CrawlerResult:
        raise NotImplementedError

    async def fetch_reviews(
        self,
        entity_id: str,
        source_entity_id: str,  # Tabelog ID / 大众点评 ID 等
        limit: int = 50,
    ) -> list[dict]:
        """拉取评论原文（用于 Phase 2 评价提取）"""
        raise NotImplementedError
```

现有的 google_places.py、ctrip_scraper.py、dianping_scraper.py 都可以重构成这个接口。
新加数据源只需要实现 `BaseCrawler.fetch()`。

---

## 八、与现有代码的关系

### 不动的部分
- `upsert_entity()` — 统一写入入口，不变
- `dedup.py` — 去重逻辑，不变
- `entity_base` 表结构 — 已有 trust_status，不变

### 要改的部分
- `pipeline.py` 的 `run_city_pipeline()` — 从 registry 读数据源配置，而不是硬编码优先级
- 现有爬虫 — 重构为 BaseCrawler 接口
- 新增 `CrawlScheduler` — 调度器
- 新增 `data_source_registry` 表 — migration

### 要新建的部分
- `app/domains/catalog/crawlers/base.py` — 统一接口
- `app/domains/catalog/crawlers/japan_guide.py` — Japan Guide 爬虫
- `app/domains/catalog/crawlers/jalan.py` — Jalan 酒店爬虫
- `app/domains/catalog/crawlers/openrice.py` — OpenRice 爬虫
- `app/domains/catalog/scheduler.py` — 采集调度器
- `app/domains/catalog/review_extractor.py` — 评论 → 维度提取
