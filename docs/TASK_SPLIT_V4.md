# 功能开发任务分配 V4
> 更新时间: 2026-03-20 00:47
> 基于: docs/FEATURE_GAP_ANALYSIS.md (功能差距分析)
> 分配原则: 复杂任务 → AI-本体(我), 简单任务 → AI-C + AI-D 各一半
> 优先级: 樱花季数据优先采集

---

## 角色分工

| 角色 | 负责方向 | 特点 |
|---|---|---|
| **AI-本体 (我)** | 架构设计 + 复杂引擎 + 逆向爬虫 | 需要理解全局、调试、设计新模块 |
| **AI-C** | 内容撰写 + 渲染模板 | 偏文案和前端模板，不涉及复杂后端 |
| **AI-D** | 数据管道 + 验证 + 配置 | 偏后端但模板化，照着已有模式做 |

---

## AI-本体 (我) — 14 项复杂任务

### 🌸 S0. 樱花季数据优先 (1项) ⭐⭐⭐

```
✅ S0.1 樱花季数据采集 + 入库
   前置: events.py 中 crawl_sakura_forecast() 已实现
   工作:
     1) 运行 python scripts/event_crawl.py --type sakura 验证采集
     2) 在 pipeline.py 增加 ingest_sakura_events()
        → entity_base(type='event', subtype='sakura')
        → 字段: name/city_code/start_date/end_date/lat/lng/image_url
     3) 确保樱花数据能被 assembler.py 的 tags_required=["sakura"] 召回
     4) 新建 7 天模板 tokyo_sakura_7d.json (樱花专属路线)
        D1 新宿御苑 → D2 上野公园/隅田川 → D3 千鸟ヶ淵/靖国神社 → ...
     5) 验证: 生成一份樱花季行程 PDF
```

### 🏗️ S1. 核心引擎 (5项) ⭐⭐⭐

```
❌ S1.1 7天通用路线模板
   工作:
     1) 新建 data/route_templates/tokyo_classic_7d.json
        在 5d 基础上扩展: D6 镰仓日归, D7 台场/丰洲/自由活动
     2) 新建 data/route_templates/kansai_classic_7d.json
        在 6d 基础上扩展: D7 神户半日+购物
     3) 为所有 7d 模板补充 senior 场景变体
     4) 验证: assembler.py 能正确加载并装配

❌ S1.2 天数裁剪/扩展逻辑
   工作:
     1) assembler.py 增加 trim_to_days(template, n) 方法
        - n < 模板天数: 取前 n 天
        - n > 模板天数: 复用部分天程 or 加"自由活动日"
     2) 在 generate_trip.py 中调用，根据 trip_request.duration 裁剪
     3) 验证: 用 7d 模板生成 4 天和 10 天行程

❌ S1.3 交通矩阵 route_matrix.py
   (同 V3 的 M2.1-M2.4，合并)
   工作:
     1) 创建 app/domains/planning/route_matrix.py
     2) Google Routes API 集成 (computeRoutes)
     3) Redis + DB 双层缓存
     4) Fallback: haversine 估算
     5) entity_card 注入交通时间

❌ S1.4 多平台比价聚合引擎
   工作:
     1) 创建 app/domains/flights/compare_engine.py
        - 聚合 Google Flights + Skyscanner + 携程 数据
        - 按 航线+日期+舱位 对齐
        - 输出: 最优价格 + 各平台价格对比 + 节省金额
     2) 创建 app/domains/hotels/compare_engine.py
        - 聚合 Booking + 携程 + Agoda + Jalan
        - 按 酒店名+房型+日期 对齐
        - 输出: 最优价格 + 各平台链接
     3) 创建 app/domains/planning/combo_optimizer.py
        - 机票+酒店+交通卡 组合优化
        - 输出: savings_report

❌ S1.5 多版本方案生成
   工作:
     1) 在 assembler.py 增加 generate_variants(trip_request, n=2)
        - 版本A: 经典路线 (评分最高)
        - 版本B: 小众路线 (去掉 S/A 级热门，用 B/C 级替代)
     2) trip_versions 表写入逻辑
     3) 对比渲染模板 comparison.html.j2
```

### 🔧 S2. 爬虫修复 (3项) ⭐⭐⭐

```
❌ S2.1 修复 letsgojp.py
   (同 V3 的 M1.1)
   
❌ S2.2 修复 matcha.py
   (同 V3 的 M1.2)

❌ S2.3 KKday/Klook Playwright 化
   (同 V3 的 M1.3)
```

### 🔗 S3. 数据集成 — 复杂管道 (3项) ⭐⭐

```
❌ S3.1 Google Flights → flight_offer_snapshots
   (同 V3 的 M3.1)

❌ S3.2 统一采集调度器 crawl_all.py
   (同 V3 的 M3.4，增加樱花季优先)

❌ S3.3 按天加价 + 订单计价逻辑
   工作:
     1) products.py 增加 calculate_price(sku_id, days)
        - 读取 workflow_config.base_days / extra_day_price
        - 返回 base_price + extra_days * extra_day_price
     2) orders 表写入时带上 extra_days 和 total_price
     3) 验证: ¥68 选 10 天 → 68 + 3×10 = ¥98
```

### 🎯 S4. 端到端验证 (2项) ⭐⭐

```
❌ S4.1 全流程 E2E — 🌸 樱花季行程
   POST /trips → 问卷 → generate(tokyo_sakura_7d/couple) → PDF
   验证: 7天行程含樱花景点、路线合理、PDF排版正确

❌ S4.2 全流程 E2E — 通用行程
   POST /trips → generate(tokyo_classic_7d/family) → PDF
   验证: 7天标准行程、景点信息完整
```

**AI-本体 总计: 14 项**

---

## AI-C — 8 项内容 + 模板任务

> 核心: 内容撰写 + Jinja2 渲染模板，不涉及复杂后端逻辑

### 📝 C1. 出行准备攻略 (1项，但内容量大) ⭐

```
✅ C1.1 撰写出行前准备攻略 + 渲染模板
   内容 (8 大模块，总计约 5000 字):
     1) 📋 证件与签证 — 护照/签证类型/材料清单/时间线/电子签
     2) ✈️ 机票须知 — 廉航vs全服务/行李额/值机/转机
     3) 💴 货币与支付 — 现金建议/换汇渠道/IC卡/移动支付
     4) 📱 通讯与网络 — SIM vs WiFi vs eSIM/购买渠道
     5) 🧳 行李打包清单 — 必带/季节性/不用带/限重
     6) 🚃 交通卡与通票 — Suica/JR Pass/一日券/机场交通
     7) 🏥 医疗与保险 — 旅行险/看病流程/常备药/紧急电话
     8) 📲 必备APP — 地图/翻译/预约/退税

   渲染:
     1) 新建 templates/magazine/pre_trip_guide.html.j2
     2) 杂志级排版，分模块卡片式布局
     3) 每模块有图标 + 要点列表 + 小贴士框
     4) 在 html_renderer.py 中增加 render_pre_trip_guide() 方法
     5) component_config 中 standard_128+ 包含此 section
```

### 📝 C2. 安全须知 (1项) ⭐

```
✅ C2.1 撰写安全须知 + 渲染模板
   内容 (4 模块，约 2000 字):
     1) 🔒 人身安全 — 治安概况/夜间注意/贵重物品
     2) 🌋 自然灾害 — 地震应对/台风/避难所/预警APP
     3) ⚖️ 法律与礼仪 — 法律红线/公共礼仪/拍照禁区/吸烟
     4) 📞 紧急联系 — 报警急救/大使馆/保险报案

   渲染:
     1) 新建 templates/magazine/safety_guide.html.j2
     2) 醒目的警告色框 + 图标
     3) 在 html_renderer.py 中增加 render_safety_guide()
```

### 📝 C3. 拍照 + 出片攻略 (1项) ⭐

```
✅ C3.1 撰写拍照攻略 + 出片攻略 + 渲染模板
   拍照攻略内容 (约 3000 字):
     - 20个热门景点的最佳拍摄点位 (具体站位描述)
     - 每个点的最佳时间 (几点光线好/避开人流)
     - 经典构图参考 (三分法/引导线/框架...)
     - 5个隐藏机位

   出片攻略内容 (约 2000 字):
     - 日本街拍穿搭 (春/夏/秋/冬 各一套建议)
     - 配色方案 (和服/街拍/咖啡馆)
     - 手机修图参数 (VSCO/Lightroom 预设推荐)
     - 小红书爆款构图模板 (5种)
     - 短视频拍摄建议

   渲染:
     1) 新建 templates/magazine/photo_guide.html.j2
     2) 新建 templates/magazine/instagrammable_guide.html.j2
     3) 图文并茂，配示意图占位
```

### 📝 C4. 避坑指南 (1项) ⭐

```
✅ C4.1 撰写避坑指南 + 渲染模板
   基础版内容 (¥128, 约 1500 字):
     - 交通坑: JR Pass 别买贵了 / 末班车时间 / 地铁vs JR 区别
     - 餐饮坑: 旅游区价格虚高 / 排队名店不一定值 / 居酒屋套路
     - 购物坑: 免税规则 / 药妆店比价 / 别在机场买
     - 住宿坑: "车站旁"可能很远 / 大小房型注意 / 退房时间
     - 景点坑: 周一闭馆多 / 预约制景点 / 门票组合券

   深度版内容 (¥298+, 额外 1500 字):
     - 各城市特有坑 (东京/京都/大阪 分别)
     - 季节特有坑 (樱花季/红叶季/盂兰盆节)
     - 编辑亲历踩坑故事

   渲染:
     1) 新建 templates/magazine/avoid_traps.html.j2
     2) ⚠️ 警告框 + ✅ 正确做法 对比排版
```

### 🎨 C5. 报告类渲染模板 (3项) ⭐

```
✅ C5.1 餐厅推荐报告模板
   新建 templates/magazine/restaurant_report.html.j2
   设计:
     - 每日午/晚各推荐 1-2 家
     - 卡片式: 店名 + Tabelog评分 + 人均 + 菜系 + 一句话推荐
     - 地图标注 (预留占位)
     - 参考 entity_card.html.j2 的样式

✅ C5.2 酒店推荐报告模板 (两个版本)
   简单版: templates/magazine/hotel_list_simple.html.j2 (¥68)
     - 3-5 家列表: 名称 + 价位 + 区域 + 一行说明
   详细版: templates/magazine/hotel_report.html.j2 (¥128+)
     - 卡片式: 名称 + 星级 + 价格范围 + 评分 + 区域优劣分析
     - 对比表格
     - "为什么推荐这家"文案

✅ C5.3 比价报告模板
   新建 templates/magazine/compare_report.html.j2 (¥888+)
   设计:
     - 机票对比表: 航司 × 平台 × 价格 矩阵
     - 酒店对比表: 酒店名 × 平台 × 价格 矩阵
     - 最优方案高亮 (绿色)
     - 省钱汇总: "总计为您节省 ¥6,230" 大字突出
   新建 templates/magazine/savings_summary.html.j2
     - 一页汇总: 原价 vs 优化后价格 + 节省金额 + 节省比例
```

### 📝 C6. 交通卡攻略扩充 (1项) ⭐

```
✅ C6.1 扩充 tips_page.html.j2 交通卡内容
   当前: 只有简单签证信息
   扩充:
     - Suica/PASMO: 购买方式 + 充值 + 使用范围
     - JR Pass: 各类型对比 + 是否值得买计算器说明
     - 东京地铁一日券/二日券/三日券
     - 关西周游卡
     - 机场→市区: 成田Express vs 京成Skyliner vs 利木津巴士
```

**AI-C 总计: 8 项** (但内容量大，约 15000+ 字撰写 + 8 个模板)

---

## AI-D — 8 项数据 + 验证任务

> 核心: 数据入库管道 + 配置 + 验证，照着已有模式做

### 📊 D1. 数据入库 (4项) ⭐⭐

```
❌ D1.1 酒店爬虫 → hotels + entity_base
   工作:
     1) pipeline.py 增加 ingest_hotel_crawl()
     2) 读取 data/hotels_raw/*.json
     3) 字段映射:
        name → entity_base.name_zh
        star_rating → hotels.star_rating
        price → hotels.typical_price_min_jpy
        booking_score → hotels.booking_score
        lat/lng → entity_base.lat/lng
     4) upsert by name + city_code
   参考: pipeline.py 中已有的 ingest 模式

❌ D1.2 Tabelog 餐厅 → restaurants + entity_base
   工作:
     1) pipeline.py 增加 ingest_tabelog_crawl()
     2) 读取 data/tabelog_raw/*.json
     3) 字段映射:
        name → entity_base.name_ja / name_zh
        score → restaurants.tabelog_score
        budget → restaurants.budget_dinner_jpy
        lat/lng → entity_base.lat/lng
        genre → entity_tags
     4) upsert by tabelog_id

❌ D1.3 JNTO/GO TOKYO → entity_base(type='poi')
   工作:
     1) pipeline.py 增加 ingest_jnto_spots()
     2) 读取 data/raw/official/*.json
     3) 字段映射:
        name_zh → entity_base.name_zh
        name_en → entity_base.name_en
        lat/lng → entity_base.lat/lng
        area → entity_base.area_name
        tags → entity_tags(namespace='feature')
     4) data_tier = 'A' (官方数据)
     5) upsert by name_zh + city_code

❌ D1.4 Events/Experiences → entity_base
   工作:
     1) pipeline.py 增加 ingest_events() + ingest_experiences()
     2) events → entity_base(type='event')
        - 樱花数据 ← S0.1 已入库，这里补其余(节日/红叶/花火)
     3) experiences → entity_base(type='experience')
        - VELTRA 数据
     4) 扩展 entity_type 枚举: 'event' / 'experience'
```

### ⚙️ D2. SKU 种子数据 + 配置 (2项) ⭐

```
❌ D2.1 product_sku 种子数据写入
   工作:
     1) 新建 scripts/seed_product_skus.py
     2) 写入 6 个 SKU 记录:
        basic_20:     ¥19.9, template, fixed_days=7
        flex_68:      ¥68,   flexible, base_days=7, extra_day_price=10
        standard_128: ¥128,  personalized, base_days=9, extra_day_price=10
        deep_298:     ¥298,  personalized, base_days=9, extra_day_price=20
        compare_888:  ¥888,  premium, base_days=10, extra_day_price=30
        honeymoon_1999: ¥1999, premium, base_days=14, extra_day_price=50
     3) 每个 SKU 写入 workflow_config + component_config (JSON)
        参考: docs/PRODUCT_TIERS_V2.md 第十节
     4) 幂等: 按 sku_id upsert

❌ D2.2 更新 products.py API 返回所有 SKU
   工作:
     1) 删除 hardcoded 的 basic_v1
     2) 改为从 DB 读取 product_sku 表
     3) GET /products → 返回所有 is_active=True 的 SKU
     4) GET /products/{sku_id} → 返回单个 SKU 详情 + features
     5) 增加 calculate_price(sku_id, days) 接口 (给 S3.3 调用)
```

### ✅ D3. 验证 + 辅助 (2项) ⭐

```
❌ D3.1 Phase 0 收尾验证
   工作:
     1) GPT 标签生成: python scripts/generate_tags.py --city tokyo
     2) 模板加载: python scripts/load_route_templates.py
     3) 验证 entity_tags / route_templates 表有数据
     4) 记录结果

❌ D3.2 API 端点全面验证
   工作:
     1) uvicorn app.main:app 启动
     2) 验证:
        GET /products → 返回 6 个 SKU (D2 完成后)
        POST /trips → 创建成功
        GET /trips/{id}/profile-questions → 返回问卷
        POST /trips/{id}/questionnaire → 提交成功
        POST /trips/{id}/generate → 返回 202
        GET /trips/{id}/plan → 返回行程
        GET /trips/{id}/preview → 返回 URL
     3) 记录每个端点的响应状态和异常
```

**AI-D 总计: 8 项**

---

## 依赖关系图

```
                   AI-本体                      AI-C                    AI-D
                   ======                      ====                    ====
Phase 0 (并行):
  S0.1 樱花数据采集+入库              C1.1 出行准备攻略         D1.1 酒店入库
  S1.1 7天通用模板                    C2.1 安全须知             D1.2 餐厅入库
  S2.1-2.3 爬虫修复                   C3.1 拍照出片攻略         D1.3 JNTO入库
                                      C4.1 避坑指南             D2.1 SKU种子数据
                                                                D3.1 Phase0收尾
                    ↓
Phase 1 (半并行):
  S1.2 天数裁剪逻辑                   C5.1 餐厅报告模板    ←──  D1.2 餐厅入库完成后
  S1.3 交通矩阵                       C5.2 酒店报告模板    ←──  D1.1 酒店入库完成后
  S3.1 Flights→DB                     C6.1 交通卡扩充          D1.4 Events入库
  S3.3 按天加价逻辑                                            D2.2 products.py 改造
                    ↓                                                 ↓
Phase 2 (依赖上游):
  S1.4 比价聚合引擎                   C5.3 比价报告模板         D3.2 API全面验证
  S1.5 多版本生成
  S3.2 crawl_all.py
                    ↓
Phase 3 (收尾):
  S4.1 E2E 樱花行程验证
  S4.2 E2E 通用行程验证
```

---

## 启动顺序

### 立即启动 (Phase 0，三方完全并行)

**AI-本体**: 先做 S0.1 (樱花采集+入库+模板) → S1.1 (7天模板)
**AI-C**: 先做 C1.1 (出行准备攻略，内容量最大)
**AI-D**: 先做 D1.1-D1.3 (数据入库，阻塞最多下游)

### 预计时间线

```
Week 1: Phase 0 — 樱花数据+7天模板+内容撰写+数据入库 → ¥19.9 可试跑
Week 2: Phase 1 — 天数裁剪+交通+报告模板+SKU → ¥68 可试跑
Week 3: Phase 1 续 — 餐厅酒店报告+加价逻辑 → ¥128 可试跑
Week 4: Phase 2 — 比价引擎+多版本 → ¥298 可试跑
Week 5-6: Phase 2 续 + Phase 3 → ¥888/¥1999 + E2E
```

---

## 给 AI-C 的启动 Prompt

```
你负责 Japan Travel AI 项目的内容撰写和渲染模板工作。

背景:
- 项目路径: /Users/yanghailin/projects/travel-ai
- 模板引擎: Jinja2, 文件在 templates/magazine/ 目录
- 参考样式: templates/magazine/entity_card.html.j2 和 tips_page.html.j2
- CSS: templates/magazine/css/ 目录
- 渲染器: app/domains/rendering/magazine/html_renderer.py

你的 8 项任务 (见 docs/TASK_SPLIT_V4.md AI-C 部分):
1. C1.1 出行前准备攻略 (8模块, ~5000字) + pre_trip_guide.html.j2
2. C2.1 安全须知 (4模块, ~2000字) + safety_guide.html.j2
3. C3.1 拍照+出片攻略 (~5000字) + photo_guide.html.j2 + instagrammable_guide.html.j2
4. C4.1 避坑指南 (基础+深度, ~3000字) + avoid_traps.html.j2
5. C5.1 餐厅报告模板 restaurant_report.html.j2
6. C5.2 酒店报告模板 hotel_list_simple.html.j2 + hotel_report.html.j2
7. C5.3 比价报告模板 compare_report.html.j2 + savings_summary.html.j2
8. C6.1 交通卡攻略扩充 tips_page.html.j2

优先顺序: C1 → C2 → C4 → C3 → C5 → C6
C5 需要等 AI-D 完成数据入库后才能做真实数据渲染测试。

要求:
- 内容用中文撰写，面向中国赴日自由行用户
- 语调: 实用、友好、不啰嗦，像朋友在给你建议
- 渲染模板保持杂志级排版风格，参考现有模板的 CSS 类名
- 每个模板都要在 html_renderer.py 中注册渲染方法
```

## 给 AI-D 的启动 Prompt

```
你负责 Japan Travel AI 项目的数据入库管道、SKU 配置和验证工作。

背景:
- 项目路径: /Users/yanghailin/projects/travel-ai
- 数据管道: app/domains/catalog/pipeline.py (已有 ingest 模式可参考)
- DB 模型: app/db/models/catalog.py (entity_base, hotels, restaurants, entity_tags)
- DB 模型: app/db/models/business.py (product_sku, orders)
- 爬虫输出: data/hotels_raw/, data/tabelog_raw/, data/raw/official/
- 参考文档: scripts/crawlers/CRAWLERS_GUIDE.md

你的 8 项任务 (见 docs/TASK_SPLIT_V4.md AI-D 部分):
1. D1.1 酒店数据入库 → hotels + entity_base
2. D1.2 Tabelog 餐厅入库 → restaurants + entity_base
3. D1.3 JNTO/GO TOKYO 入库 → entity_base(type='poi')
4. D1.4 Events/Experiences 入库 → entity_base(type='event'/'experience')
5. D2.1 product_sku 种子数据 (6个SKU)
6. D2.2 products.py 从 DB 读取 SKU
7. D3.1 Phase 0 收尾验证 (GPT 标签 + 模板加载)
8. D3.2 API 端点全面验证

优先顺序: D1.1 → D1.2 → D1.3 → D2.1 → D2.2 → D1.4 → D3.1 → D3.2
D3.2 需要等 D2 完成后才能完整验证。

要求:
- 入库逻辑用 upsert (有则更新，无则插入)
- 每条记录必须有 source + crawled_at
- 价格统一转 CNY (汇率见 CRAWLERS_GUIDE.md)
- 参考 pipeline.py 已有的代码风格和模式
```
