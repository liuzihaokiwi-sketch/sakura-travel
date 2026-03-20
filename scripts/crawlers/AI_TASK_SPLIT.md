# 爬虫并行开发任务分工
> 生成时间: 2026-03-19  
> 项目路径: /Users/yanghailin/projects/travel-ai

## 背景

我们在为日本 AI 旅行引擎构建数据采集层。信息源按 4 层组织：

| 层级 | 用途 | 目标数据源 |
|---|---|---|
| 第一层：官方真相 | 区域、活动日期、季节亮点、官方线路 | JNTO, GO TOKYO, Kyoto Travel, OSAKA-INFO |
| 第二层：活动体验 | 活动库存、体验类型、价格区间、热度 | VELTRA, KKday, Klook, Rakuten Experiences |
| 第三层：餐厅路由 | 餐厅候选、路线现实性、营业信息 | Tabelog ✅, NAVITIME |
| 第四层：中文灵感 | 中文写法、用户视角、选题、热门玩法 | 小红书, 樂吃購, MATCHA, Japaholic |

### 已完成模块 (AI-1 已搞定)

- `scripts/crawlers/base.py` — 异步 HTTP 基类 (httpx, UA轮换, 限速, 重试)
- `scripts/crawlers/playwright_base.py` — Playwright 浏览器基类
- `scripts/crawlers/tabelog.py` — Tabelog 餐厅 ✅ 已验证
- `scripts/crawlers/google_flights.py` — Google Flights 机票 ✅ 已验证 (Lite + Full/Playwright + Calendar 三模式)
- `scripts/crawlers/hotels.py` — Booking/Ctrip/Agoda/Jalan 酒店 ✅ 已验证
- `scripts/crawlers/events.py` — japan-guide 活动/樱花/红叶 ✅ 已验证
- `scripts/crawlers/xiaohongshu.py` — 小红书 UGC ⚠️ 已写未测试
- `scripts/crawlers/tianxun.py` — 天巡 ❌ 被 Captcha 封杀，已废弃
- `scripts/crawlers/skyscanner.py` — Skyscanner API ❌ 需 API Key

### 代码规范

1. **继承 `BaseCrawler`**（纯 HTTP 站）或 **`PlaywrightCrawler`**（JS 重度站）
2. **异步**: 所有方法用 `async def`
3. **价格统一人民币 (CNY)**: 非人民币价格需转换，用 `_CURRENCY_TO_CNY` 映射
4. **输出**: JSON 保存到 `data/raw/{source}/`，同时 `print` 摘要
5. **容错**: 单条解析失败不能崩整个爬虫，用 `try/except` + `logger.warning`
6. **CLI 入口**: 每个爬虫配一个 `scripts/{name}_crawl.py` 命令行脚本

---

## AI-2 任务：第二层 — 活动体验爬虫

### 目标文件
- `scripts/crawlers/experiences.py` — 主爬虫
- `scripts/experience_crawl.py` — CLI 入口

### 要爬的平台 (按优先级)

#### 1. KKday (优先 — 中文友好, 结构化好)
- URL: `https://www.kkday.com/zh-cn/country/japan`
- 数据: 体验名称, 价格(CNY), 评分, 评论数, 城市, 类型, 时长, 是否可退
- 方法: HTTP 抓取，KKday 有 `/api/` 接口可以直接拿 JSON
- 城市页: `https://www.kkday.com/zh-cn/city/tokyo`, `/city/osaka`, `/city/kyoto`

#### 2. Klook (备选 — 类似 KKday)
- URL: `https://www.klook.com/zh-CN/city/1-tokyo-things-to-do/`
- 数据: 同上
- 方法: SSR 页面 + `__NEXT_DATA__` JSON 提取（Next.js 站）

#### 3. VELTRA (日本本地体验强)
- URL: `https://www.veltra.com/en/asia/japan/`
- 数据: 体验名, 价格(JPY→CNY), 评分, 时长, 类别
- 方法: HTTP 抓取 HTML

#### 4. Rakuten Travel Experiences
- URL: `https://experiences.travel.rakuten.co.jp/`
- 数据: 体验名, 价格(JPY→CNY), 类别, 地区
- 方法: HTTP

### 输出 schema

```python
{
    "id": "kkday_12345",
    "source": "kkday",           # kkday / klook / veltra / rakuten
    "name": "东京晴空塔门票",
    "name_en": "Tokyo Skytree Ticket",
    "city": "tokyo",
    "category": "attraction",     # attraction / tour / food / transport / culture
    "price_cny": 120.0,
    "original_price": 2400,       # 原币种价格
    "original_currency": "JPY",
    "rating": 4.7,
    "review_count": 3200,
    "duration_hours": None,       # 体验时长(小时), 门票类为 None
    "is_refundable": True,
    "url": "https://www.kkday.com/...",
    "image_url": "https://...",
    "tags": ["门票", "观光"],
    "crawled_at": "2026-03-19T22:00:00"
}
```

### 参考代码

看 `scripts/crawlers/base.py` 了解 BaseCrawler 接口:
```python
class ExperienceCrawler(BaseCrawler):
    async def crawl_kkday(self, city: str, pages: int = 3) -> List[Dict]:
        ...
    async def crawl_klook(self, city: str, pages: int = 3) -> List[Dict]:
        ...
    async def crawl_all(self, cities=["tokyo","osaka","kyoto"]) -> List[Dict]:
        ...
```

### 注意事项
- KKday 中文站价格已经是 CNY，不需要转换
- Klook 可能需要 Playwright（有反爬），先试 HTTP，不行再切
- VELTRA 价格是 JPY，需要转换 (1 JPY ≈ 0.048 CNY)
- 去重逻辑：同一个体验可能在多个平台出现，用 `name + city` 做粗去重

---

## AI-3 任务：第四层 — 台湾攻略站爬虫 + 修复小红书

### 目标文件
- `scripts/crawlers/letsgojp.py` — 樂吃購！日本
- `scripts/crawlers/matcha.py` — MATCHA 繁中站
- `scripts/crawlers/xiaohongshu.py` — 修复已有小红书爬虫
- `scripts/guide_crawl.py` — 统一 CLI 入口

### 要爬的平台

#### 1. 樂吃購！日本 (优先 — 台湾最大日本旅游站)
- URL: `https://www.letsgojp.com/`
- 分类页: `/archives/category/area/tokyo/`, `/area/osaka/`, `/area/kyoto/`
- 数据: 文章标题, 摘要, 城市, 标签, 发布日期, 图片, URL
- 方法: HTTP 抓取 HTML (WordPress 站, 结构规律)
- 重点抓: 攻略文章、景点推荐、美食推荐、交通教学、季节限定

#### 2. MATCHA 繁中站 (日本出品, 多语言)
- URL: `https://matcha-jp.com/zh-Hant`
- 城市页: `https://matcha-jp.com/zh-Hant/list?pref=tokyo`
- 数据: 文章标题, 摘要, 城市, 标签, 文章类型, URL
- 方法: HTTP 抓取 (有 API: `https://matcha-jp.com/api/v1/articles`)
- 优势: 分类细(景点/美食/购物/住宿/交通), 有地区筛选

#### 3. 小红书修复
- 文件: `scripts/crawlers/xiaohongshu.py` (已有代码)
- 问题: 实现完成但从未测试过
- 任务: 运行测试, 修复选择器/等待时间问题, 确认能抓到数据

### 输出 schema

```python
{
    "id": "letsgojp_12345",
    "source": "letsgojp",        # letsgojp / matcha / xiaohongshu
    "title": "2026东京赏樱全攻略！10大必去景点＋花期预测",
    "summary": "每年三月底四月初...",
    "city": "tokyo",
    "category": "guide",          # guide / food / attraction / transport / shopping / seasonal
    "tags": ["赏樱", "东京", "景点推荐"],
    "publish_date": "2026-03-01",
    "url": "https://www.letsgojp.com/...",
    "image_url": "https://...",
    "language": "zh-TW",          # zh-TW / zh-CN
    "engagement": {               # 仅小红书有
        "likes": 5200,
        "collects": 3100,
        "comments": 420
    },
    "crawled_at": "2026-03-19T22:00:00"
}
```

### 参考代码

```python
# 樂吃購 — WordPress 站, 用 BaseCrawler
class LetsGoJPCrawler(BaseCrawler):
    BASE = "https://www.letsgojp.com"
    
    async def crawl_category(self, area: str, pages: int = 5) -> List[Dict]:
        """抓取某个地区的攻略文章列表"""
        ...
    
    async def crawl_article(self, url: str) -> Dict:
        """抓取单篇文章详情"""
        ...

# MATCHA — 优先试 API
class MATCHACrawler(BaseCrawler):
    BASE = "https://matcha-jp.com"
    API = "https://matcha-jp.com/api/v1"
    
    async def crawl_by_city(self, city: str, limit: int = 50) -> List[Dict]:
        ...
```

### 注意事项
- 樂吃購是 WordPress，列表页有 `class="post-card"` 类似的卡片结构
- MATCHA 优先试 `/api/v1/articles` 接口，如果有的话效率远高于 HTML 解析
- 小红书用的是 PlaywrightCrawler（需要浏览器），看 `playwright_base.py`
- 台湾站内容是繁体中文，`language` 字段标记为 `"zh-TW"`
- 文章去重: 用 URL 做唯一键

---

## 通用提示

### 如何查看已有爬虫写法

```bash
# 看 BaseCrawler 基类
cat scripts/crawlers/base.py

# 看 PlaywrightCrawler 基类
cat scripts/crawlers/playwright_base.py

# 看最完整的参考: Tabelog 爬虫
cat scripts/crawlers/tabelog.py

# 看酒店爬虫(多平台整合参考)
cat scripts/crawlers/hotels.py
```

### 汇率参考 (用于价格转 CNY)

```python
_CURRENCY_TO_CNY = {
    "JPY": 0.048, "¥": 0.048,     # 日元
    "USD": 7.25, "$": 7.25,       # 美元
    "TWD": 0.22, "NT$": 0.22,     # 台币
    "HKD": 0.93, "HK$": 0.93,    # 港币
    "KRW": 0.0053,                 # 韩元
    "CNY": 1.0, "￥": 1.0,        # 人民币
}
```

### 完成后的验证

每个爬虫完成后跑一次验证:
```bash
# AI-2
python scripts/experience_crawl.py --city tokyo --limit 10

# AI-3  
python scripts/guide_crawl.py --source letsgojp --city tokyo --limit 10
python scripts/guide_crawl.py --source matcha --city tokyo --limit 10
python scripts/guide_crawl.py --source xiaohongshu --keyword "东京攻略" --limit 10
```
