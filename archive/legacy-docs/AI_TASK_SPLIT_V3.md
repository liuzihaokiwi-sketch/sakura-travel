# 任务再分工 V3 (AI-本体 + AI-C 并行)
> 更新时间: 2026-03-19 23:30
> 项目路径: /Users/yanghailin/projects/travel-ai

## 背景

V2 已将 30 项任务分给 AI-A 和 AI-B 两个 AI。
本文档在 V2 基础上，将 AI-A 和 AI-B 的任务**再各拆一半**，
难度高的归 **AI-本体 (我)**，简单/模板化的归 **AI-C (另一个AI)**。

---

## 难度评级标准

| 难度 | 定义 |
|---|---|
| ⭐⭐⭐ | 需要逆向站点结构、调试反爬、设计新架构 |
| ⭐⭐ | 需要理解已有代码 + 编写集成逻辑 |
| ⭐ | 模板化、验证性、文档性工作 |

---

## AI-本体 (我): 15 项高难度任务

> 核心原则: 逆向工程 + 架构设计 + 复杂集成

### 🔧 M1. 爬虫修复 — 站点逆向 (3项) ⭐⭐⭐

```
❌ M1.1 修复 letsgojp.py — 站点改版适配
    问题: URL 从 /archives/category/area/tokyo/ → /category?a=3&c=1
    工作:
      1) 逆向新 URL 参数: a=地区ID, c=分类ID
      2) 建立地区 ID 映射 (tokyo=3, osaka=7, kyoto=141 ...)
      3) 解析新页面 HTML 结构 (文章卡片选择器)
      4) 分页机制 (?page=2)
      5) 验证: python scripts/guide_crawl.py --source letsgojp --city tokyo --limit 10

❌ M1.2 修复 matcha.py — API 下线适配
    问题: /api/v1/articles 返回 404, /zh-Hant/list 301 到首页
    工作:
      1) 探测 matcha-jp.com 当前可用 URL 结构
      2) 尝试 sitemap.xml / RSS / 新 API 端点
      3) 重写解析逻辑
      4) 验证: python scripts/guide_crawl.py --source matcha --city tokyo --limit 10

❌ M1.3 修复 experiences.py — KKday/Klook Playwright 化
    问题: KKday Captcha, Klook JS 渲染
    工作:
      1) 继承 PlaywrightCrawler 重写 KKday 采集
      2) 处理 Captcha 检测 + 重试逻辑
      3) Klook 搜索结果 JS 渲染等待策略
      4) 验证: python scripts/experience_crawl.py --city tokyo --source kkday --limit 5
```

### 🏗️ M2. 交通矩阵 — 核心架构 (4项) ⭐⭐⭐

```
❌ M2.1 创建 app/domains/planning/route_matrix.py
    设计:
      - get_travel_time(origin_id, dest_id, mode, session, redis_client)
      - 支持 mode: transit / walk / drive
      - 返回: {duration_min, distance_km, route_summary, cached}
    
❌ M2.2 Google Routes API 集成
    工作:
      1) 调用 Routes API (computeRoutes) 获取公共交通时间
      2) 处理多交通方式 (JR/地铁/巴士)
      3) 解析 legs / steps 中的换乘信息
      4) 错误处理 + 限额管理 (每日请求数上限)

❌ M2.3 Redis / DB 双层缓存
    设计:
      - L1: Redis (TTL 24h) — 热数据
      - L2: route_matrix_cache 表 (TTL 7d) — 持久化
      - 写入策略: API 返回后同时写 Redis + DB
      - 读取策略: Redis miss → DB → API call → 回填两层

❌ M2.4 Fallback 估算 + entity_card 注入
    工作:
      1) 当 API 不可用时按 haversine 估算
         步行: 距离(km) / 4.5 * 60 (分钟)
         公交: max(距离/30*60, 15)
      2) entity_card.html.j2 注入 "🚶 12分钟" / "🚇 25分钟" 信息
```

### 🔗 M3. 数据集成 — 复杂管道 (4项) ⭐⭐

```
❌ M3.1 Google Flights 爬虫 → flight_offer_snapshots 写入
    工作:
      1) 在 price_monitor.py 中增加 save_crawler_snapshot()
         接收 GoogleFlightsCrawler 输出格式 → 转换为表字段
      2) 字段映射:
         crawler.airline → raw_payload.airline
         crawler.price   → min_price (转 CNY)
         crawler.dep/arr → departure_date + 时间提取
      3) source_name = 'google_flights_crawler' (区分 amadeus)
      4) 去重: 同航线+同日期+同来源 24h 内不重复写入

❌ M3.2 JNTO/GO TOKYO 景点 → entity_base 写入
    工作:
      1) 在 pipeline.py 中增加 ingest_jnto_spots()
      2) 字段映射:
         spot.name_zh → entity_base.name_zh
         spot.name_en → entity_base.name_en
         spot.lat/lng → entity_base.lat/lng
         spot.area    → entity_base.area_name
         spot.tags    → entity_tags (namespace=feature)
      3) entity_type = 'poi', data_tier = 'A' (官方数据)
      4) 去重: 按 name_zh + city_code 判断是否已存在

❌ M3.3 活动/体验 → entity_base 复用方案
    设计决策:
      - events (樱花/红叶/节日) → entity_base(type='event') + JSONB扩展
      - experiences (VELTRA) → entity_base(type='experience') + JSONB扩展
      - 不新建表，用 entity_base 的 JSONB 扩展字段存特有属性
    工作:
      1) entity_type 枚举扩展: 'event' / 'experience'
      2) migration 加 check constraint 或注释
      3) pipeline.py 增加 ingest_events() / ingest_experiences()

❌ M3.4 统一采集调度器 crawl_all.py
    设计:
      1) 串联所有爬虫: flights → hotels → tabelog → jnto → events → veltra
      2) 每个爬虫独立 try/except，失败不阻断后续
      3) 结果汇总日志: "采集完成: 9航班 + 25酒店 + 20餐厅 + 62景点 + 12活动 + 23体验"
      4) --dry-run 模式: 只跑爬虫不写 DB
      5) 可选 cron 定时: 每天凌晨 3:00 执行
```

### 🎯 M4. 端到端验证 — 核心链路 (4项) ⭐⭐

```
❌ M4.1 运行完整生成流程
    POST /trips → 提交问卷 → POST /trips/{id}/generate → GET /trips/{id}/plan
    验证: plan 包含 5 天行程, 每天有景点+餐厅+酒店

❌ M4.2 验证 PDF 输出质量
    GET /trips/{id}/export?fmt=pdf
    检查: 中文渲染正常, 图片加载, 排版不溢出

❌ M4.3 生成 tokyo_classic_5d/couple 攻略
    完整人工检查: 景点合理性 + 路线连贯性 + 预算准确性

❌ M4.4 生成 kansai_classic_6d/family 攻略
    完整人工检查: 跨城市切换 + 亲子景点覆盖 + 交通时间合理
```

**AI-本体 总计: 15 项**

---

## AI-C (另一个AI): 15 项简单/模板化任务

> 核心原则: 验证 + 配置 + 文档 + 已有代码的微调

### 📋 C1. 爬虫验证 — 仅测试 (2项) ⭐

```
❌ C1.1 测试 xiaohongshu.py
    → 安装 Playwright: pip install playwright && playwright install chromium
    → python scripts/guide_crawl.py --source xiaohongshu --keyword "东京攻略" --limit 10
    → 记录结果 (成功/失败/需修复什么)
    → 如果有简单 bug (选择器变了、URL 错了) 直接修

❌ C1.2 验证已修复的 VELTRA 爬虫仍然工作
    → python scripts/experience_crawl.py --city tokyo --source veltra --limit 5
    → 确认 ≥3 条结果, 价格/标题/评分都有值
```

### ✅ C2. Phase 0 收尾 (2项) ⭐

```
❌ C2.1 GPT 标签生成
    前置: 设置 OPENAI_API_KEY 环境变量
    → python scripts/generate_tags.py --city tokyo
    → python scripts/generate_tags.py --city osaka
    → python scripts/generate_tags.py --city kyoto
    → 检查 entity_tags 表中新增记录数

❌ C2.2 验证模板加载
    → python scripts/load_route_templates.py
    → SELECT count(*) FROM route_templates;  -- 应有 ≥5 条
    → SELECT count(*) FROM route_template_slots;  -- 应有 ≥20 条
```

### 🔌 C3. API 验证 + 微调 (5项) ⭐

> 注: B2 代码已存在 (products.py + trips_generate.py), 只需验证和微调

```
❌ C3.1 验证 GET /products 返回正确 SKU
    → curl http://localhost:8000/products
    → 确认包含 19.9 基础版 SKU
    → 如有问题修改 products.py 中的硬编码数据

❌ C3.2 验证 POST /trips/{id}/generate 流程
    → 创建 trip_request
    → POST /trips/{id}/generate
    → 确认返回 202 + job_id
    → 检查队列是否入队

❌ C3.3 验证 GET /trips/{id}/preview 返回 URL
    → 生成完成后调用
    → 确认返回 preview_url 字段

❌ C3.4 验证 GET /trips/{id}/exports 返回 PDF 列表
    → 生成完成后调用
    → 确认返回 assets 数组, 包含 html + pdf 链接

❌ C3.5 确认所有路由已注册在 main.py
    → 检查 app/main.py 中的 include_router 是否完整
    → curl http://localhost:8000/docs 查看 Swagger 是否全部显示
```

### 📊 C4. 数据集成 — 简单管道 (2项) ⭐⭐

```
❌ C4.1 酒店爬虫 → hotels + entity_base 写入
    工作:
      1) 在 pipeline.py 中增加 ingest_hotel_crawl()
      2) 读取 data/hotels_raw/*.json
      3) 字段映射 (比 flights 简单, 直接 map):
         name → entity_base.name_zh
         star_rating → hotels.star_rating
         price → hotels.typical_price_min_jpy
         booking_score → hotels.booking_score
      4) upsert 去重 by name + city_code

❌ C4.2 Tabelog 餐厅 → restaurants + entity_base 写入
    工作:
      1) 在 pipeline.py 中增加 ingest_tabelog_crawl()
      2) 读取 data/tabelog_raw/*.json
      3) 字段映射:
         name → entity_base.name_ja / name_zh
         score → restaurants.tabelog_score
         budget → restaurants.budget_dinner_jpy
         lat/lng → entity_base.lat/lng
      4) upsert 去重 by tabelog_id
```

### 📝 C5. 验证 + 文档 (4项) ⭐

```
❌ C5.1 验证 planner_runs 追溯记录
    → 生成行程后查 DB:
    → SELECT * FROM planner_runs WHERE trip_request_id = '{id}';
    → 确认 started_at, finished_at, status, error_message 都有

❌ C5.2 验证 trip_requests.status 状态流转
    → 创建 → draft
    → 提交问卷 → profiled
    → generate → generating → completed / failed
    → 检查每个节点的 updated_at 时间戳

❌ C5.3 验证 H5 预览手机端可访问
    → 用 Chrome DevTools 手机模拟器打开 preview URL
    → 检查: 响应式布局, 图片加载, 文字可读

❌ C5.4 更新 README.md
    → 补充 Phase 1 使用说明
    → 所有 CLI 命令列表
    → API 端点列表 (从 Swagger 截取)
    → 环境变量说明 (OPENAI_API_KEY, GOOGLE_ROUTES_KEY 等)
```

**AI-C 总计: 15 项**

---

## 分工对照表

| 原编号 | 任务 | 难度 | 分配 |
|---|---|---|---|
| A1.1 (KKday/Klook) | experiences Playwright化 | ⭐⭐⭐ | **AI-本体 M1.3** |
| A1.2 | letsgojp 修复 | ⭐⭐⭐ | **AI-本体 M1.1** |
| A1.3 | matcha 修复 | ⭐⭐⭐ | **AI-本体 M1.2** |
| A1.4 | xiaohongshu 测试 | ⭐ | AI-C C1.1 |
| A1.1 (VELTRA) | VELTRA 回归测试 | ⭐ | AI-C C1.2 |
| A2.1 | Flights → DB | ⭐⭐ | **AI-本体 M3.1** |
| A2.2 | Hotels → DB | ⭐⭐ | AI-C C4.1 |
| A2.3 | JNTO → DB | ⭐⭐ | **AI-本体 M3.2** |
| A2.4 | Events/Exp → DB | ⭐⭐ | **AI-本体 M3.3** |
| A2.5 | crawl_all.py | ⭐⭐ | **AI-本体 M3.4** |
| A3.1 | route_matrix.py | ⭐⭐⭐ | **AI-本体 M2.1** |
| A3.2 | Google Routes API | ⭐⭐⭐ | **AI-本体 M2.2** |
| A3.3 | 双层缓存 | ⭐⭐⭐ | **AI-本体 M2.3** |
| A3.4 | Fallback 估算 | ⭐⭐ | **AI-本体 M2.4** |
| A3.5 | prebuild 脚本 | ⭐⭐ | **AI-本体 M2.4** (合并) |
| A3.6 | entity_card 注入 | ⭐ | **AI-本体 M2.4** (合并) |
| B1.1 | GPT 标签 | ⭐ | AI-C C2.1 |
| B1.2 | 模板验证 | ⭐ | AI-C C2.2 |
| B2.1-B2.5 | API 层 (已有代码) | ⭐ | AI-C C3.1-C3.5 |
| B3.1 | 全流程验证 | ⭐⭐ | **AI-本体 M4.1** |
| B3.2 | PDF 质量验证 | ⭐⭐ | **AI-本体 M4.2** |
| B3.3 | H5 手机端验证 | ⭐ | AI-C C5.3 |
| B3.4 | planner_runs 验证 | ⭐ | AI-C C5.1 |
| B3.5 | status 流转验证 | ⭐ | AI-C C5.2 |
| B3.6 | tokyo 攻略人工检查 | ⭐⭐ | **AI-本体 M4.3** |
| B3.7 | kansai 攻略人工检查 | ⭐⭐ | **AI-本体 M4.4** |
| B3.8 | README 更新 | ⭐ | AI-C C5.4 |
| — | Tabelog → DB | ⭐⭐ | AI-C C4.2 (新增) |

---

## 依赖关系

```
AI-本体:                          AI-C:
M1 (爬虫修复) ─────┐              C1 (爬虫验证)
                    ↓              C2 (Phase 0 收尾) ──┐
M3 (数据集成) ◄────┘                                   ↓
      ↓                           C3 (API 验证) ──────→ 需要服务器启动
M2 (交通矩阵)                    C4 (简单数据管道) ──→ 需要 M3 的 pipeline.py 框架
      ↓                                  ↓
M4 (端到端验证) ◄────────────────── C5 (验证+文档)
```

### 并行策略
- **第一阶段** (可完全并行):
  - AI-本体: M1 爬虫修复 + M2 交通矩阵
  - AI-C: C1 爬虫验证 + C2 Phase 0 收尾 + C3 API 验证
- **第二阶段** (AI-本体先完成 M3 框架后):
  - AI-本体: M3 数据集成
  - AI-C: C4 简单数据管道 (复用 M3 的 pipeline 框架)
- **第三阶段** (收尾):
  - AI-本体: M4 端到端验证
  - AI-C: C5 验证 + 文档

---

## 快速启动 Prompt

### 给 AI-C 的 prompt:
```
看 scripts/crawlers/AI_TASK_SPLIT_V3.md 的 AI-C 部分。
同时参考 scripts/crawlers/CRAWLERS_GUIDE.md 了解项目背景和接口规范。

你负责 15 项简单/验证性任务:
1. C1: 测试小红书爬虫 + VELTRA 回归测试
2. C2: GPT 标签生成 + 模板加载验证 (需 OPENAI_API_KEY)
3. C3: 验证 API 端点 (products/generate/preview/exports, 代码已存在)
4. C4: 酒店和餐厅数据写入 DB (简单字段映射)
5. C5: 状态验证 + README 更新

先从 C2 Phase 0 收尾开始 (不依赖其他任务)，然后 C3 验证 API。
C4 需要等 AI-本体完成 M3 的 pipeline 框架后再做。

⚠️ 注意:
- C2.1 需要配置 OPENAI_API_KEY
- C3 需要先 uvicorn app.main:app 启动服务
- C4 参考 data/hotels_raw/ 和 data/tabelog_raw/ 中的 JSON 格式
```
