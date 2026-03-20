# 爬虫模块开发指引
> 最后更新: 2026-03-19 23:25
> 项目路径: /Users/yanghailin/projects/travel-ai/scripts/crawlers/

## 一、架构概览

```
scripts/crawlers/
├── base.py              ← 异步 HTTP 基类 (httpx + UA轮换 + 限速 + 重试)
├── playwright_base.py   ← Playwright 浏览器基类 (用于 JS 重度站)
├── tabelog.py           ← 第三层: 餐厅 [已验证 ✅]
├── google_flights.py    ← 核心: 机票 [已验证 ✅] (Lite + Full/Playwright + Calendar)
├── hotels.py            ← 核心: 酒店 [已验证 ✅] (Booking/Ctrip/Agoda/Jalan)
├── events.py            ← 第一层: 活动/樱花/红叶 [已验证 ✅] (japan-guide)
├── jnto.py              ← 第一层: 官方站 [已验证 ✅] (JNTO + GO TOKYO)
├── experiences.py       ← 第二层: 活动体验 [VELTRA ✅, KKday/Klook 需Playwright]
├── letsgojp.py          ← 第四层: 樂吃購 [需修复 ⚠️ URL结构已变]
├── matcha.py            ← 第四层: MATCHA [需修复 ⚠️ API 404 + 重定向]
├── xiaohongshu.py       ← 第四层: 小红书 [未测试 ⚠️ 需Playwright]
├── skyscanner.py        ← 备用: Skyscanner API [需API Key]
└── tianxun.py           ← 废弃: 天巡 [Captcha封杀]
```

## 二、各模块详细状态

### ✅ 已验证通过 (5个)

| 模块 | 命令 | 结果 | 关键细节 |
|---|---|---|---|
| tabelog.py | `python scripts/tabelog_crawl.py --city tokyo --pages 1` | 20家餐厅 | 评分/预算/地址/坐标全有 |
| google_flights.py | `python scripts/flight_crawl.py --mode full --origin PVG --dest NRT` | 9条航班 | Playwright自动化交互，需翻日历页 |
| hotels.py | `python scripts/hotel_crawl.py --city tokyo` | 25家酒店 | Booking星级用SVG计数，价格需货币转换 |
| events.py | `python scripts/event_crawl.py` | 12节日+43樱花 | japan-guide 的日期在文本块中 |
| jnto.py | `python scripts/jnto_crawl.py` | 143目的地+62景点+15指南 | GO TOKYO 景点用数字ID: /spot/6/ |

### ⚠️ 部分可用 (1个)

| 模块 | 可用平台 | 不可用平台 | 修复建议 |
|---|---|---|---|
| experiences.py | **VELTRA** (33条/页, `[data-package-id]` 选择器) | KKday (Captcha), Klook (JS渲染) | KKday/Klook 需改用 PlaywrightCrawler |

### ❌ 需修复 (2个)

| 模块 | 问题 | 根因 | 修复方向 |
|---|---|---|---|
| letsgojp.py | 所有分类 URL 301 重定向到 `/articles` | 站点改版，URL 从 `/archives/category/area/tokyo/` 变成了 `/category?a=3&c=1` | 1) 改用新 URL `/category?a={areaId}&c={catId}` 2) 地区 ID 映射: tokyo=3, osaka=7, kyoto=141 3) 首页已有文章卡片 `a[href*="/archives/"]` 可直接解析 |
| matcha.py | API 404, HTML 301 到首页 | `/api/v1/articles` 接口已下线, `/zh-Hant/list` 页面也重定向 | 1) 检查 matcha-jp.com 当前 URL 结构 2) 可能改用 `matcha-jp.com/zh-Hant` 首页解析 3) 或改用 sitemap.xml |

### ❓ 未测试 (1个)

| 模块 | 依赖 | 预期风险 |
|---|---|---|
| xiaohongshu.py | Playwright + 小红书登录/反爬 | 反爬较强，可能需要cookie注入或登录态 |

## 三、BaseCrawler 关键接口

```python
class BaseCrawler:
    def __init__(
        delay_range=(1.0, 3.0),  # 请求间随机延迟(秒)
        max_retries=3,            # 失败重试次数
        timeout=20.0,             # 单次请求超时(秒)
        max_concurrent=3,         # 最大并发数
    )

    async def fetch(url, **kwargs) -> Optional[httpx.Response]  # 带重试的请求
    async def fetch_text(url, **kwargs) -> Optional[str]        # 直接返回文本
    async def _random_delay() -> None                           # 随机等待
```

### 继承模式

```python
# HTTP 站点用 BaseCrawler
class MyNewCrawler(BaseCrawler):
    def __init__(self, **kwargs):
        kwargs.setdefault("delay_range", (1.5, 3.0))  # ⚠️ 必须用 setdefault
        super().__init__(**kwargs)

# JS 重度站点用 PlaywrightCrawler
class MyJSCrawler(PlaywrightCrawler):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
```

### ⚠️ 常见坑

1. **不要在 `__init__` 中硬编码 `delay_range` 再传 `**kwargs`**
   - 错误: `super().__init__(delay_range=(1,2), **kwargs)` → kwargs 里如果也有 delay_range 就报错
   - 正确: `kwargs.setdefault("delay_range", (1,2)); super().__init__(**kwargs)`

2. **`fetch_text()` 会自动跟随重定向**，但重定向后的 URL 可能和预期不同

3. **价格统一用人民币 (CNY)**，汇率映射：
   ```python
   _CURRENCY_TO_CNY = {
       "JPY": 0.048, "¥": 0.048,
       "USD": 7.25, "$": 7.25,
       "TWD": 0.22, "NT$": 0.22,
       "HKD": 0.93, "HK$": 0.93,
       "CNY": 1.0, "￥": 1.0,
   }
   ```

## 四、Google Flights 特殊说明

### 三种模式

| 模式 | 依赖 | 速度 | 数据量 | 适用场景 |
|---|---|---|---|---|
| Lite (SSR) | httpx | 快 | 少 | 快速价格检查 |
| **Full (Playwright)** | playwright | 慢(~30s) | **最全** | 正式数据采集 |
| Calendar | playwright | 中 | 每日最低价 | 价格趋势分析 |

### Full 模式交互流程

```
首页 → 点击出发地输入框 → 输入城市名 → 选择下拉建议
     → 点击目的地输入框 → 输入城市名 → 选择下拉建议
     → 点击出发时间 → 翻日历到目标月 → 点击出发日 → 点击返程日
     → 点击"完成" → 点击"搜索" → 等待结果加载 → 解析文本
```

### 关键技术点

1. **城市名映射**: `_CITY_NAMES = {"SHA": "上海", "TYO": "东京", ...}`
2. **日历翻页**: 坐标点击 `page.mouse.click(1130, 625)` (1280x900 viewport)
3. **时间解析**: `innerText` 中时间分三行 (`19:10` / `–` / `23:00`)，解析器支持同行和分行两种模式
4. **结果等待**: 3s 轮询，检测到 ≥3 条航班时间对就提前返回

## 五、数据输出规范

### 文件路径

```
data/raw/official/     ← JNTO/GO TOKYO (jnto.py)
data/tabelog_raw/      ← Tabelog (tabelog.py)
data/flights_raw/      ← 机票 (google_flights.py)
data/hotels_raw/       ← 酒店 (hotels.py)
data/events_raw/       ← 活动 (events.py)
data/experiences_raw/  ← 体验 (experiences.py)
data/raw/letsgojp/     ← 樂吃購 (letsgojp.py)
data/raw/matcha/       ← MATCHA (matcha.py)
data/xhs_raw/          ← 小红书 (xiaohongshu.py)
```

### JSON 格式要求

- 每条记录必须有 `source` (数据来源标识) 和 `crawled_at` (ISO 时间戳)
- 价格字段统一为 `price_cny` (人民币)，同时保留 `original_price` + `original_currency`
- 坐标用 `latitude` / `longitude` (float)
- 标签/分类用 `tags: List[str]`

## 六、CLI 入口汇总

```bash
# 餐厅
python scripts/tabelog_crawl.py --city tokyo --pages 2

# 机票
python scripts/flight_crawl.py --mode full --origin PVG --dest NRT --dep 2026-07-20 --ret 2026-07-26

# 酒店
python scripts/hotel_crawl.py --city tokyo

# 活动/樱花
python scripts/event_crawl.py

# 官方站 (JNTO + GO TOKYO)
python scripts/jnto_crawl.py                          # 全量
python scripts/jnto_crawl.py --only spots --limit 10  # 只抓景点

# 体验 (目前只有 VELTRA 可用)
python scripts/experience_crawl.py --city tokyo --source veltra --limit 10

# 攻略站 (letsgojp/matcha 需修复)
python scripts/guide_crawl.py --source letsgojp --city tokyo --limit 10

# 小红书 (需 Playwright)
python scripts/guide_crawl.py --source xiaohongshu --keyword "东京攻略" --limit 10
```

## 七、新增爬虫 Checklist

- [ ] 继承 `BaseCrawler` 或 `PlaywrightCrawler`
- [ ] `__init__` 用 `kwargs.setdefault()` 设默认值
- [ ] 实现 `crawl_xxx()` 异步方法
- [ ] 价格转换为 CNY
- [ ] 每条记录包含 `source` + `crawled_at`
- [ ] 创建 CLI 入口 `scripts/xxx_crawl.py`
- [ ] 添加 `sys.path.insert(0, ...)` 到 CLI 入口
- [ ] 运行验证并记录结果到本文档
