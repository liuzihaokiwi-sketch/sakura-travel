# 实施任务分配表

> 按 V1.0 → V1.5 → V2.0 三版迭代。每个任务标注：执行模型、思考强度、验证方式。

---

## V1.0 — 北海道全量真实数据 + 完整行程 + PDF 输出

> 目标：札幌一个城市做透验证，然后扩展到北海道 10 城。
> 产出：能生成内容饱满的北海道 5 天手账本 PDF，每天 5-6 个活动 + 餐厅 + 交通 + 图片。

### 阶段 A：数据基础设施

#### A1. 数据源注册中心 + 城市覆盖表 [Sonnet · 普通]
```
新建：data_source_registry 表 + city_data_coverage 表 + city_food_specialties 表
初始数据：录入当前所有已知数据源（Google Places/Tabelog/Japan Guide 等）
录入北海道 10 城市的覆盖目标（每城市各品类目标数量）
文件：新 migration + app/db/models/data_sources.py
验证：SELECT * FROM data_source_registry WHERE countries @> '{JP}' 能列出所有日本源
```

#### A2. 清除 AI 数据 + 标记现有数据 [Sonnet · 普通]
```
把 entity_base 中 trust_status='ai_generated' 的 208 条标记为 rejected（不删，留审计）
确认剩余 258 条 unverified 数据的质量（坐标在 bbox 内、有名称）
文件：一次性脚本 scripts/clean_ai_data.py
验证：SELECT trust_status, COUNT(*) FROM entity_base GROUP BY trust_status
      → ai_generated=0（active 的），rejected=208
```

#### A3. 前置约束数据表 [Sonnet · 普通]
```
新建：city_climate_monthly（月度气温/降水/日照）
新建：holiday_calendar（日本节假日 + 祭典）
新建：定休日模式存入 entity_operating_facts（已有表，补数据）
数据来源：气象厅历史数据（JSON/CSV 手动录入）、日本假日 API
文件：新 migration + data/seed/climate_hokkaido.json + data/seed/holidays_jp.json
验证：SELECT city_code, month, avg_temp_high FROM city_climate_monthly WHERE city_code='sapporo'
```

#### A4. 实体间距离矩阵 [Sonnet · 普通]
```
新建：entity_distance_cache 表
批量计算：同城市内实体两两距离（Google Directions API 或 Haversine 近似）
近似策略：同 area_name 的实体默认步行 5-10 分钟，跨区域的调 Google Directions
文件：新 migration + scripts/compute_distances.py
验证：SELECT COUNT(*) FROM entity_distance_cache WHERE from_entity_id != to_entity_id
```

### 阶段 B：札幌数据做透

#### B1. Tabelog 餐厅全量拉取 — 札幌 [Opus · 深度思考]
```
目标：札幌 Tabelog 3.0+ 的餐厅全部拉取
按菜系分别搜索（12 个菜系 × 每个拉 20-50 条）
提取：名字、评分、价格区间、菜系、地址
然后用 Google Places 补坐标
写入 entity_base + restaurants 表，trust_status='unverified', data_tier='A'
文件：改进 app/domains/catalog/crawlers/tabelog_scraper.py（从现有 web_crawler.py 拆出）
验证：SELECT cuisine_type, COUNT(*) FROM restaurants r
      JOIN entity_base e ON r.entity_id = e.entity_id
      WHERE e.city_code='sapporo' GROUP BY cuisine_type
      → 12+ 个菜系，每个至少 10 家
```

#### B2. Google Places 景点/酒店/特色店 — 札幌 [Sonnet · 普通]
```
目标：
  景点：按子分类搜索（shrine/temple/museum/park/landmark/onsen 各 20 条）
  酒店：按价位搜索（budget/mid/premium/luxury 各 15 条）
  特色店：按关键词搜索（お土産/工芸品/地元特産 各 10 条）
改进现有 google_places.py：按子分类循环搜索，不是一个 type 搜完
验证：SELECT entity_type, COUNT(*) FROM entity_base WHERE city_code='sapporo'
      → poi 100+, hotel 50+, restaurant 200+ (含 Tabelog)
```

#### B3. Japan Guide 景点评级 — 札幌+北海道 [Sonnet · 普通]
```
新建 Japan Guide 爬虫：解析 japan-guide.com/e/e2164.html (Sapporo) 等页面
提取：景点名、评级（1-3星）、描述文本、地址
与 entity_base 通过名字+坐标匹配关联
存入 entity_source_scores（source='japan_guide'）
文件：app/domains/catalog/crawlers/japan_guide.py
验证：SELECT COUNT(*) FROM entity_source_scores WHERE source_name='japan_guide'
```

#### B4. 攻略网站扫描 — 札幌 [Sonnet · 普通]
```
爬取 3-5 个攻略网站的札幌页面：
  - letsgojp.cn 的北海道美食/景点页
  - gltjp.com 的 Sapporo Food Guide
  - uu-hokkaido.in 的札幌页
提取被提及的地点名称列表
存入 discovery_candidates，标记 source_count
与 entity_base 关联（已有的标记，没有的作为新候选）
文件：app/domains/catalog/crawlers/guide_scraper.py（通用攻略爬虫）
验证：SELECT source_count, COUNT(*) FROM discovery_candidates
      WHERE city_code='sapporo' GROUP BY source_count
      → source_count=3+ 的有 50+ 个（高置信候选）
```

#### B5. 城市特色菜系确定 — 北海道 [Sonnet · 普通]
```
从 B4 爬取的攻略文本中提取各城市被反复提及的美食关键词
AI（DeepSeek）提取频次排序
人工确认后存入 city_food_specialties
验证：SELECT city_code, cuisine, importance FROM city_food_specialties
      WHERE city_code='sapporo' ORDER BY importance
      → signature: 味噌拉面/成吉思汗/汤咖喱/海鲜丼
```

### 阶段 C：评价维度 + 文案

#### C1. 评论采集 — 札幌核心实体 [Opus · 深度思考]
```
目标：为 top 100 实体（评分最高的景点+餐厅+酒店）采集评论原文
来源：
  - Google Places Reviews（通过 Place Details API，每实体 5 条最新评论）
  - Tabelog 评论页（如果可以爬到）
  - TripAdvisor 评论页
  - 攻略网站中提到该实体的段落
存入 source_snapshots（type='review_batch'）
文件：app/domains/catalog/crawlers/review_collector.py
验证：SELECT COUNT(DISTINCT object_id) FROM source_snapshots
      WHERE object_type='review_batch' → 100+
```

#### C2. 维度提取 + 摘要生成 [Sonnet · 普通]
```
读取 C1 采集的评论原文
AI（Sonnet）按维度提取结构化评分
AI（Sonnet）生成一句话摘要（why_go/practical_tip/skip_if）
过滤规则：跳过 < 5 字评论、纯表情、无具体细节的
存入 entity_review_signals.dimension_scores + entity_descriptions
文件：app/domains/catalog/review_extractor.py
验证：抽样 10 个实体，人工看维度和摘要是否准确
      管理后台 entity 详情页能看到维度和摘要
```

#### C3. 标签生成 [Haiku/DeepSeek · 普通]
```
从 C2 的维度评分自动推断标签：
  queue_risk=high → tag: long_queue
  payment_method=cash_only → tag: cash_only
从攻略原文提取额外标签：
  "雨天也能玩" → tag: rainy_day_ok
存入 entity_tags
文件：app/domains/catalog/tag_generator.py
验证：SELECT tag_namespace, tag_value, COUNT(*) FROM entity_tags
      GROUP BY tag_namespace, tag_value ORDER BY count DESC LIMIT 20
```

### 阶段 D：片段 + 模板

#### D1. day_fragment 表设计 + 札幌片段编排 [Opus · 深度思考]
```
新建 day_fragments 表（含变体支持）
为札幌编排 8-10 个片段：
  - 札幌市区经典半日（大通公园→时计台→电视塔→狸小路）
  - 札幌美食巡游（二条市场→拉面横丁→汤咖喱）
  - 白色恋人+圆山动物园（亲子半日）
  - 藻岩山夜景（晚间半日）
  - 定山溪温泉日归
  - 等等
每个片段：选实体（从 B 阶段真实数据中选）、排时间、配文案、标注约束
文件：新 migration + scripts/seed_fragments_sapporo.py
验证：SELECT fragment_id, theme, city_code FROM day_fragments WHERE city_code='sapporo'
      → 8-10 个片段
      每个片段 items 中的 entity_id 都在 entity_base 中存在且 trust_status != 'rejected'
```

#### D2. 小樽/函馆/其他城市片段 [Sonnet · 普通]
```
复制 D1 的模式，为其他城市编排片段：
  小樽：港町漫步半日、寿司屋通美食
  函馆：港城夜景全日、五棱郭+西部半日、朝市
  富良野/美瑛：花田自驾全日（夏）、滑雪全日（冬）
  旭川：旭山动物园半日、拉面村
  登别：温泉一日
  洞爷湖：火山温泉一日
  等等
总共约 30-40 个片段
验证：SELECT city_code, COUNT(*) FROM day_fragments GROUP BY city_code
      → 每个城市至少 2-3 个片段
```

#### D3. 片段文案生成 [GPT Creative · 普通]
```
每个片段生成：
  - title_zh（"小樽 · 港町漫步半日"）
  - summary_zh（一段话描述）
  - 每个活动项的过渡文案（"从运河步行 5 分钟就到音乐盒堂"）
GPT-5.3/4o 生成，人工审核修改
验证：每个片段都有 title_zh 和 summary_zh，不为空
```

#### D4. 行程模板组装 — 北海道 [Opus · 深度思考]
```
组装 6-8 个完整模板：
  - 北海道经典5天（couple/moderate/summer）
  - 北海道经典5天（family/moderate/summer）
  - 北海道经典5天（couple/moderate/winter）
  - 北海道深度7天（couple/relaxed/summer）
  - 北海道紧凑4天（couple/packed/any）
  - 北海道温泉6天（senior/relaxed/autumn）
  等等
每个模板引用 day_fragments + 指定酒店 + 城市间交通
Opus 做整体审核：路线连贯性、节奏感、是否值 298 元
文件：scripts/seed_templates_hokkaido.py + itinerary_templates 表
验证：Opus 审核每个模板打分 > 80/100
      人工看每个模板的 5 天路线是否合理
```

#### D5. 定休日约束引擎 [Sonnet · 普通]
```
模板生成用户行程时，自动检查：
  - 行程中某天是周一 → 检查所有周一定休的餐厅/景点 → 自动替换为同区域替代
  - 行程中撞上节假日 → 标记拥挤提示
  - 季节性关闭的景点 → 自动替换
文件：app/domains/planning/constraint_checker.py
验证：构造一个周一出发的行程 → 确认周一定休的店被自动换掉
```

### 阶段 E：渲染 + PDF

#### E1. 图片关联到实体 [Sonnet · 普通]
```
assets/hokkaido/ 有 195 张真实图片
按文件名/目录名匹配到 entity_base（如 otaru_canal.jpg → 小樽运河）
Google Places Photo API 补充缺少图片的实体
存入 entity_media，标记 is_cover=True 的主图
文件：scripts/link_photos.py
验证：SELECT COUNT(*) FROM entity_media WHERE is_cover=TRUE
      → 核心实体（top 100）至少 80% 有封面图
```

#### E2. PDF 渲染完善 [Sonnet · 普通]
```
改进 export_plan_pdf.py：
  - 每天显示 5-6 个活动（不再只有 1 个）
  - 每个活动显示实用提醒和价格
  - 插入实体图片
  - 显示交通信息（JR/步行/巴士）
  - 每日预算汇总
  - 酒店信息
验证：生成一个 5 天北海道 PDF，人工检查：
  - 每天有 5+ 个活动 ✓
  - 有图片 ✓
  - 有交通信息 ✓
  - 有实用提醒 ✓
  - 无 AI 编造的内容 ✓
```

#### E3. 预制页面 [Sonnet · 普通]
```
制作固定页面模板：
  - 北海道美食图鉴页（特色菜系介绍 + 推荐）
  - 行前准备 checklist（签证/行李/APP/交通卡）
  - 交通指南（JR Pass/IC 卡/常用线路）
  - 实用信息（紧急电话/退税/Wi-Fi）
  - 天气穿衣建议（按月份）
数据来源：官方信息 + 预制内容，不用 AI
验证：PDF 包含这些页面
```

### 阶段 F：端到端验证

#### F1. 札幌 3 天冒烟测试 [人工 + Opus 审核]
```
用札幌一个城市的完整数据（B 阶段完成后）
生成一个 3 天札幌行程
PDF 输出
人工检查所有内容准确性：
  - 每个地名在 Google Maps 上能找到 ✓
  - 营业时间和定休日对不对 ✓
  - 价格大致准确 ✓
  - 交通时间合理 ✓
  - 评分来自权威源 ✓
  - 无 AI 编造的内容 ✓
```

#### F2. 北海道 5 天完整验证 [人工 + Opus 审核]
```
用北海道全部数据（A-E 阶段完成后）
使用预制模板生成一个 5 天行程
PDF 输出完整版（含图片、美食图鉴、行前准备等）
Opus 做质量审核
人工做最终验证
→ 这就是可以卖给用户的版本
```

---

## V1.5 — 个性化 + 多城市圈

#### V1.5-1. 用户-实体匹配引擎 [Opus · 深度思考]
```
标签硬过滤 + 评分排序 + AI 个性化匹配（top 20 → Sonnet 判断）
```

#### V1.5-2. 感知层数据接入 [Sonnet · 普通]
```
小红书/马蜂窝/TripAdvisor 标签提取 → soft_scores 调分
```

#### V1.5-3. 广府圈数据 + 模板 [复制 V1.0 流程]
```
广深港澳顺德 → 同样的 A-F 阶段
数据源换成大众点评/OpenRice/携程
```

#### V1.5-4. 关西圈数据 + 模板 [复制 V1.0 流程]
```
已有部分关西数据，补充完善
```

---

## V2.0 — 规模化

#### V2.0-1. 全自动采集调度器 [Opus · 深度思考]
#### V2.0-2. 出发前动态更新推送
#### V2.0-3. 正规 API 合作替换爬虫
#### V2.0-4. 模板自动生成 + 审核流水线

---

## 任务汇总 — V1.0

### Opus 任务（需要深度思考的设计 + 质量把控）

| ID | 任务 | Thinking | 验证方式 |
|----|------|----------|---------|
| B1 | Tabelog 餐厅全量拉取架构 | 开 | 12 菜系各 10+ 家 |
| C1 | 评论采集系统设计 | 开 | 100+ 实体有评论原文 |
| D1 | day_fragment 表设计 + 札幌片段 | 开 | 8-10 个可用片段 |
| D4 | 行程模板组装 + 质量审核 | 开 | Opus 打分 >80 |
| F1 | 札幌 3 天冒烟测试 | 否 | 人工逐项验证 |
| F2 | 北海道 5 天完整验证 | 否 | 可以卖给用户 |

### Sonnet 任务（明确的实现工作）

| ID | 任务 | Thinking | 验证方式 |
|----|------|----------|---------|
| A1 | 数据源注册中心 + 覆盖表 | 否 | DB 查询 |
| A2 | 清除 AI 数据 | 否 | COUNT 统计 |
| A3 | 前置约束数据表 | 否 | 气候/假日数据可查 |
| A4 | 距离矩阵 | 否 | 同城市实体有距离数据 |
| B2 | Google Places 批量拉取 | 否 | 每品类数量达标 |
| B3 | Japan Guide 爬虫 | 否 | 有评级数据 |
| B4 | 攻略网站扫描 | 否 | discovery_candidates 有数据 |
| B5 | 城市特色菜系 | 否 | 每城市 3-5 个 signature |
| C2 | 维度提取 + 摘要 | 否 | 抽样 10 个人工看 |
| C3 | 标签生成 | 否 | entity_tags 有数据 |
| D2 | 其他城市片段 | 否 | 每城市 2-3 个片段 |
| D3 | 片段文案（调 GPT） | 否 | 每个片段有标题和摘要 |
| D5 | 定休日约束引擎 | 否 | 周一行程无定休店 |
| E1 | 图片关联 | 否 | 核心实体 80% 有图 |
| E2 | PDF 渲染完善 | 否 | PDF 每天 5+ 活动 |
| E3 | 预制页面 | 否 | PDF 含固定页面 |

### 执行顺序（依赖关系）

```
第一批（无依赖，可并行）：
  A1 数据源注册中心
  A2 清除 AI 数据
  A3 前置约束数据
  B5 城市特色菜系（不依赖 DB 改动，可人工先做）

第二批（依赖第一批）：
  B1 Tabelog 全量拉取（依赖 A2 清理后的干净 DB）
  B2 Google Places 批量拉取（同上）
  B3 Japan Guide 爬虫（同上）
  B4 攻略扫描（同上）

第三批（依赖第二批的数据）：
  A4 距离矩阵（需要实体坐标）
  C1 评论采集（需要知道哪些是 top 100 实体）

第四批（依赖评论数据）：
  C2 维度提取
  C3 标签生成
  E1 图片关联

第五批（依赖实体画像完整）：
  D1 片段编排 — 札幌
  D2 片段编排 — 其他城市
  D3 片段文案
  D5 定休日引擎

第六批（依赖片段）：
  D4 模板组装
  E2 PDF 完善
  E3 预制页面

第七批（验证）：
  F1 札幌 3 天冒烟
  F2 北海道 5 天完整
```

---

## 分阶段执行策略

**不要一次全做。分三个检查点，每个做完审视调整再继续。**

### 检查点 1：数据地基（A1-A3 + B1-B5）
```
做什么：建基础设施 + 札幌数据做透
产出：札幌 300+ 真实实体（景点 100+/餐厅 200+/酒店 50+）
验证：管理后台能看到札幌的完整数据，每个品类数量达标

Opus 做：B1（Tabelog 架构设计）
Sonnet 做：A1+A2+A3 → B2+B3+B4+B5

检查点 1 完成后审视：
  - 数据质量够不够？需不需要调采集策略？
  - 哪些数据源实际上爬不了？要换方案吗？
  - 实体去重效果好不好？
  → 根据实际情况调整检查点 2 的任务
```

### 检查点 2：内容加工 + 片段编排（C1-C3 + D1-D3 + A4）
```
做什么：评价提取 + 片段编排 + 距离计算
产出：札幌 8-10 个 day_fragments，核心实体有维度评分和摘要
验证：每个片段内容饱满、时间连贯、实体都是真实数据

Opus 做：C1（评论采集设计）+ D1（片段设计 + 札幌编排）
Sonnet 做：A4 + C2+C3 + D2+D3

检查点 2 完成后审视：
  - 片段内容质量怎么样？值不值得给用户看？
  - 评价维度准不准？需要调 prompt 吗？
  - 片段变体（定休日/季节）的逻辑对不对？
  → 根据实际情况调整检查点 3 的任务
```

### 检查点 3：模板 + PDF + 端到端验证（D4-D5 + E1-E3 + F1-F2）
```
做什么：组装完整模板 + PDF 渲染 + 验证
产出：一本可以卖的北海道 5 天手账本 PDF
验证：人工走一遍行程，确认每条信息准确

Opus 做：D4（模板组装 + 审核）+ F1+F2（验证）
Sonnet 做：D5 + E1+E2+E3

检查点 3 完成后审视：
  - PDF 拿在手上像不像值 298 元的东西？
  - 哪些地方需要改进？
  - 可以进入 V1.5 了吗？还是 V1.0 要继续打磨？
```

**每个检查点之间可能需要回头修前一阶段的问题——这是正常的。**
不要假设任务一次就做对，预留回头修的时间。
