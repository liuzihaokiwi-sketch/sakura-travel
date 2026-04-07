# 系统设计 V2 — 完整方案

> 这是所有架构讨论的最终整合。之前的文档（DATA_LIFECYCLE、PRECOMPUTE_AND_REUSE、
> AI_MODEL_ALLOCATION 等）的精华都在这里，加上后续审视发现的问题和修正。

---

## 第一章：产品本质

**我们卖的是什么：** 纸质旅行手账本 + 贴纸 DIY 包，298/348 元。

**用户付费的核心价值：**
1. **确定性** — 不用做攻略，照着走就行
2. **信息准确** — 营业时间、交通、价格都对，不会扑空
3. **节奏感** — 时间分配合理，不赶不闲
4. **惊喜感** — 有一些"攻略上找不到"的本地推荐
5. **仪式感** — 纸质手账 + 贴纸，旅行变得有仪式感

**用户最怕什么：**
1. 信息过时 — 到了发现店关门了（最致命）
2. 路线不合理 — 来回折腾浪费时间
3. 千篇一律 — 和小红书攻略一模一样，没有付费感
4. 内容太空 — 只有地名没有实用信息

**贴纸机制的意义：** 容错。用户可以用贴纸覆盖修改，所以手账本不是"印错就废了"。
这降低了我们对"完美准确"的焦虑，但不能成为偷懒的借口。

---

## 第二章：数据系统

### 2.1 应该收集什么数据

从手账本那一页倒推，每个元素需要什么数据：

**实体级数据（每个景点/餐厅/酒店/店铺都需要）：**

| 数据 | 用途 | 必要性 | 来源 |
|------|------|--------|------|
| 名称（中/日/英） | 手账本标题 + 用户到现场认出来 | 必须 | 权威源原文 |
| 精确坐标 | 路线编排 + 导航二维码 | 必须 | Google Places |
| 营业时间 | 避免扑空 | 必须 | Google Places |
| 定休日 | 避免撞上定休 | 必须 | Google Places + Tabelog |
| 权威评分 | 决定推不推荐 | 必须 | Tabelog/大众点评/Japan Guide |
| 价格/费用 | 预算估算 | 必须 | Tabelog/Google/攻略 |
| 推荐理由（一句话） | 手账本上印的描述 | 必须 | 攻略原文提取 |
| 实用提醒 | "只收现金"/"需预约" | 必须 | 评论提取 |
| 招牌菜/核心体验 | 到了知道点什么/看什么 | 重要 | 评论提取 |
| 照片 | 手账本配图 | 重要 | 收集后改画风 |
| 最佳时段 | 编排时间顺序 | 重要 | 攻略/评论 |
| 排队/预约信息 | 时间规划 | 重要 | 评论提取 |
| 支付方式 | 实用提醒 | 有则更好 | 评论提取 |
| 语言友好度 | 实用提醒 | 有则更好 | 评论提取 |
| 替代方案 | Plan B | 有则更好 | 同区域同类型实体 |
| 标签 | 筛选匹配 | 后续迭代 | AI 从评论提取 |

**城市级数据（每个城市需要）：**

| 数据 | 用途 | 来源 |
|------|------|------|
| 城市间交通 | 行程骨架 | 乗換案内 / Google Directions |
| 月度气候 | 穿衣建议 + 活动可行性 | 气象厅历史数据 |
| 日出日落时间 | 户外活动时间窗 | 天文数据 |
| 特色菜系列表 | 餐厅采集重点 | 攻略网站提取 |
| 节假日/祭典日历 | 避开/利用特殊日期 | 官方旅游网站 |
| 季节性开放信息 | 景点可行性约束 | Japan Guide / 官方 |
| 签证/入境政策 | 行前准备页 | 官方 |
| 免税/退税政策 | 购物提示 | 官方 |

### 2.2 从哪里收集

> **注意：** 数据采集方法论已演进为"品类内相对排名"体系（不再使用固定分数阈值做入围判断）。
> 具体执行标准以 [data-engineering/MASTER_GUIDE.md](data-engineering/MASTER_GUIDE.md) 为准。
> 以下"决策源"框架仍然有效，但阈值数字仅适用于发现池粗筛。

**数据源分两种角色：**

**决策源（决定"推不推荐"）：**
- Tabelog（日本餐厅）→ 发现池粗筛 3.5+，入围/终选按品类内相对排名
- Japan Guide（日本景点）→ 2-3 星才推荐
- 大众点评（中国餐厅）→ 4.0+ 才推荐
- 攻略交叉验证 → 3+ 个独立源提及才进候选池

**补充源（提供结构化数据）：**
- Google Places API → 坐标、营业时间、place_id
- 攻略网站文本 → 描述、实用提醒、推荐理由
- 评论文本 → 维度评价、标签

**两者关系：决策源说"这个值得去"，补充源说"具体在哪、几点开门"。不反过来。**

### 2.3 数据源注册与城市覆盖

每个数据源在 `data_source_registry` 中注册，记录：
- 覆盖哪些国家/城市
- 覆盖哪些品类
- 采集方式（API/HTML 爬虫/手动）
- 速率限制
- 当前状态（active/pending_api/broken）

每个城市×品类的覆盖进度在 `city_data_coverage` 中追踪：
- 目标数量 vs 当前数量 vs 已验证数量
- 哪些源已拉过、哪些还没
- 覆盖百分比

### 2.4 如何收集

**发现阶段（双向）：**
```
方向1：攻略扫描 → 提取地点名 → 交叉验证
  Japan Guide 的 Sapporo 页提到了 30 个地方
  乐吃购的北海道页提到了 50 个地方
  GOOD LUCK TRIP 提到了 40 个地方
  → 交集中被 3+ 源提及的 = 高置信候选
  → 只被 1 源提及的 = 低置信候选（可能是小众好去处或不值得去）

方向2：权威源直接筛选 → 按评分全拉
  Tabelog 札幌 3.5+ 的餐厅 → 全部拉进来（这些一定值得推荐）
  Google Places 评分 4.3+ 的景点 → 全部拉进来
  → 不依赖攻略提没提到
```

**采集阶段（按优先级）：**
```
P0 必须有：坐标 + 名称 + 营业时间（没有这些无法编排行程）
P1 核心价值：权威评分 + 价格 + 推荐理由（没有这些手账本没内容）
P2 丰富度：评价维度 + 实用提醒 + 照片（让手账本更实用）
P3 个性化：标签 + 匹配度（让推荐更精准）
```

P0 和 P1 必须在出第一版手账本之前完成。P2 和 P3 可以迭代补充。

### 2.5 数据整合与清洗

**去重：** dedup engine（名称规范化 + 坐标 500m + Levenshtein），同一地点只保留一条 entity_base 记录，各源评分分别存在 entity_source_scores。

**信任标记：**
- verified — 人工确认过
- unverified — 真实数据源拉的，未人工确认
- ai_generated — AI 生成的兜底数据
- suspicious — 坐标异常/名称疑似重复
- rejected — 确认不用

**综合评分：** 多源加权。权威源权重最高，Google 次之，攻略提及度作为补充信号。

**评价维度提取：** AI 从评论文本中提取结构化维度（queue_risk、payment_method 等）+ 一句话摘要。AI 只做搬运不做创作——输入是真实评论，输出是结构化提取。

### 2.6 权重如何使用

评分不是一个数字排序那么简单。三层机制：

```
第一层：标签硬过滤
  用户不吃生的 → 排除 sushi 标签的餐厅
  用户带幼儿 → 排除 child_friendly=no 的景点
  → 候选池从 200 缩到 80

第二层：综合评分排序
  同品类内按多源加权评分排序
  Tabelog 3.8 的拉面店排在 3.5 的前面
  → 80 个候选按质量排好序

第三层：用户匹配（每单微调时）
  把 top 20 候选的维度信息 + 用户画像发给 AI
  AI 判断哪个更适合这个具体用户
  → 最终选出 5-8 个写进行程
```

---

## 第三章：行程编排

### 3.1 前置约束（编排之前必须确定）

不是"生成完了检查"，而是"一开始就知道哪些不能排"：

**时间约束：**
```
输入：用户出发日期 2026-05-10 ~ 2026-05-14

查询并确定：
  - 每天日出日落时间 → 户外活动时间窗
  - 每天星期几 → 定休日约束
  - 是否撞上节假日 → 拥挤度/特殊营业
  - 是否有祭典/活动 → 可以加入行程或需要避开
  - 季节 → 哪些景点当季开放
```

**天气约束：**
```
查询 5 月中旬北海道历史天气：
  - 平均气温 10-18°C → 穿衣建议
  - 降水概率 ~30% → 每天准备一个室内 Plan B
  - 日照时长 14+ 小时 → 户外活动时间充裕
```

**交通约束：**
```
  - JR 北海道时刻表 → 城市间移动时间
  - 末班车时间 → 晚上活动截止时间
  - 冬季是否有减班/停运
```

**预订约束：**
```
  - 哪些餐厅必须提前预约 → 提前几天
  - 哪些活动有名额限制 → 是否还有位置
  - 酒店旺季是否订满
```

这些约束数据可以预计算（气候、日出日落、定休日模式）或查表（节假日日历），不需要每单现算。

### 3.2 编排流程

```
前置约束确定
    │
    ▼
骨架构建（城市×天数×节奏）
  Day 1: 到达·札幌 [light]
  Day 2: 札幌→小樽 [balanced]
  Day 3: 定山溪温泉 [balanced]
  Day 4: 富良野/美瑛 [balanced]
  Day 5: 札幌·出发 [light]
    │
    ▼
片段填充（从预制 day_fragments 中选）
  Day 2 → "小樽港町漫步" 片段
  Day 3 → "定山溪温泉日归" 片段
    │
    ▼
定休日/约束检查
  Day 2 是周一 → 政寿司周一定休 → 换成旭寿司（同区域替代）
    │
    ▼
餐食补充
  每天确保有午餐和晚餐 → 从同区域高评分餐厅中选
    │
    ▼
交通串联
  每个移动点之间插入交通信息 → JR/巴士/步行
    │
    ▼
预算核算
  累加所有费用 → 对照用户预算级别
    │
    ▼
Plan B 准备
  每个户外活动 → 准备一个室内替代
  每个需预约餐厅 → 准备一个 walk-in 替代
    │
    ▼
质量审核
  Haiku: 格式/时间连续性
  Sonnet: 逻辑/路线合理性/定休日检查
  Opus: 整体体验/信息准确性/是否值 298 元
```

### 3.3 预计算 & 复用

**核心洞察：行程是"模板 + 微调"，不是每单从零生成。**

**三层计算：**

```
一次性预计算（做一次永久用）：
  - 实体画像（评分/维度/标签/摘要）
  - 实体间距离矩阵
  - 城市气候表/日出日落表/定休日模式
  - 节假日日历

模板层（按城市圈预制 20-30 个）：
  - day_fragments：半天/全天的预编排片段，含文案/图片/实用提示
  - itinerary_templates：完整行程骨架，引用 fragments

每单微调（工作量很小）：
  - 模板匹配（规则匹配，不用 AI）
  - 替换不合适的实体（标签过滤，不用 AI）
  - 定休日检查 + 自动换替代（规则，不用 AI）
  - 微调后检查（Haiku 快检，仅改动大时用 Sonnet）
```

**片段变体：**
同一个"小樽半日游"可能有多个变体：
- 周一版：跳过周一定休的店
- 冬季版：加运河冰雕灯光
- 带小孩版：去掉坡道多的路线，加水族馆
- 雨天版：减少室外，加音乐盒堂和 LeTAO 室内时间

变体不需要全部预制——骨架一样，只是某些实体被标签匹配自动替换。

---

## 第四章：AI 模型分配

### 4.1 五个层级

| 层级 | 模型 | 用在哪 | 成本 |
|------|------|--------|------|
| Creative | GPT-5.3/5.4/4o | 文案创意、翻译、每日主题 | 中 |
| Analytical | Sonnet | 评论提取、标签、Plan B、逻辑审核 | 中 |
| Judge | Opus | 最终质量审核、复杂决策 | 高 |
| Fast | Haiku | 分类、格式校验、简单判断 | 低 |
| Cheap | DeepSeek/Qwen | 大量中文处理 | 极低 |

### 4.2 什么不用 AI

大部分工作不需要 AI：
- 去重 → 代码逻辑（Levenshtein + 坐标）
- 评分归一化 → 数学公式
- 标签过滤 → 规则引擎
- 骨架构建 → 算法
- 模板匹配 → 规则匹配
- 距离计算 → API
- 定休日检查 → 日历查表
- PDF 渲染 → 代码

**AI 只用在四个地方：**
1. 从评论文本提取结构化信息（Sonnet，一次性）
2. 生成文案（GPT，一次性）
3. 用户-实体个性化匹配（Sonnet，每单 0-1 次）
4. 质量审核（Opus，模板级一次 + 每单 Haiku 快检）

### 4.3 异步慢速生成

预计算的工作不紧急，可以后台慢慢跑：
- 评论维度提取 → 队列，每分钟 1 个实体
- 文案生成 → 每天处理 10-20 个片段
- 质量审核 → 每天审 5-10 个模板
- 翻译 → 攒一批一起翻

中转站压低 token 成本，反正是异步的不需要低延迟。

---

## 第五章：渲染与展示

### 5.1 手账本页面类型

| 页面类型 | 内容 | 数据来源 |
|----------|------|---------|
| 封面 | 目的地名 + 日期 + 主视觉图 | 用户信息 + 编辑设计 |
| 行程总览 | 5 天路线鸟瞰图 | 骨架数据 |
| 每日详情页 | 时间轴 + 活动卡片 + 实用提示 | fragment + 实体数据 |
| 城市美食图鉴 | 当地特色菜系介绍 + 推荐 | 预制页（每城市一次） |
| 行前准备页 | checklist + 签证 + 行李 | 预制页（每国一次） |
| 交通指南页 | JR Pass + 交通卡 + 常用线路 | 预制页 |
| 实用信息页 | 紧急联系 + 退税 + Wi-Fi | 预制页 |
| 天气穿衣页 | 按月份建议 | 预制页（每城市每月） |
| 预算追踪页 | 空白表格供用户填写 | 模板 |
| 贴纸页 | 每个景点/城市的贴纸 | 设计资产 |

### 5.2 加分展示项

让用户觉得"值 298 元"的细节：
- 手写风格字体（不是印刷体）
- 水彩风格地图（不是 Google Maps 截图）
- 每日主题命名（"港町漫步日"而不是"Day 2"）
- 当地人才知道的小贴士（从评论中提取的实用信息）
- 季节限定内容（樱花前线、红叶时间、雪祭信息）
- QR 码链接到 Google Maps 导航
- 空白贴纸区让用户自由发挥

### 5.3 出发前动态更新

手账本印完无法修改，但可以给用户发补充提醒：
- 出发前 3 天：检查行程中所有餐厅的当周营业状态
- 如有临时休业/改时间 → 发消息给用户，附替代方案
- 极端天气预警 → 发消息建议调整行程
- 这不需要改手账本，用贴纸覆盖就行

---

## 第六章：验证策略

### 6.1 分步验证（每步独立可验）

| 步骤 | 验证标准 | 验证方法 | 快速验证 |
|------|---------|---------|---------|
| 数据采集 | 实体有坐标+名称+评分 | DB 查询统计 | `SELECT city_code, COUNT(*), AVG(google_rating) FROM entity_base GROUP BY city_code` |
| 数据清洗 | 无重复、无异常坐标 | dedup 报告 + bbox 检查 | `SELECT COUNT(*) FROM entity_base WHERE trust_status='suspicious'` |
| 评价提取 | 维度有值、摘要通顺 | 抽样 10 个人工看 | 管理后台看 entity 详情 |
| 片段编排 | 时间不冲突、距离合理 | 自动校验脚本 | `python scripts/validate_fragment.py --fragment-id 1` |
| 模板组装 | 5天路线连贯、无死角 | Opus 审核 + 人工看 | 在管理后台预览模板 |
| 定休日检查 | 不安排定休日的店 | 自动校验 | 对照 Google 营业信息 |
| PDF 输出 | 有图有文有地图 | 打开 PDF 看 | `python scripts/export_plan_pdf.py` |
| 最终验证 | **自己假装是用户走一遍** | 人工 | 拿着手账本模拟一天行程 |

### 6.2 快速验证（端到端冒烟测试）

**不需要等所有数据就绪。** 可以用最小数据集快速验证全链路：

```
最小验证集：
  - 1 个城市（札幌）
  - 5 个景点 + 5 个餐厅 + 2 个酒店（全部真实数据）
  - 1 个 day_fragment（"札幌市区半日"）
  - 1 个 2 天模板
  → 能生成一个 2 天行程的 PDF
  → PDF 里有真实地名、真实评分、真实照片
  → 这就证明全链路通了
```

**然后逐步扩展：**
- 2 天 → 5 天（加更多 fragments）
- 1 城市 → 3 城市（加小樽、函馆）
- 12 个实体 → 200 个实体（批量采集）
- 无评价维度 → 有评价维度（评论提取）

### 6.3 后续迭代方向

**V1.0（先活下来）：**
- 北海道 5 天 × 3 个模板（couple/family/solo）
- 真实数据，有评分有描述
- PDF 可输出
- 人工质量审核

**V1.1（数据丰富化）：**
- 评价维度提取
- 标签系统
- 更多 fragments 和模板变体

**V1.2（个性化）：**
- 用户画像匹配
- AI 微调
- 感知层数据（小红书标签）

**V1.3（多城市圈）：**
- 广府圈上线
- 关西圈上线（已有部分数据）
- 数据源注册中心正式运行

**V2.0（规模化）：**
- 全自动化采集 + 刷新
- 模板自动生成 + 审核
- 出发前动态更新
- 正规 API 合作替换爬虫

---

## 第七章：当前现实 vs 目标差距

| 方面 | 现在有什么 | 需要什么 | 差距 |
|------|-----------|---------|------|
| 实体数据 | 481 个（北海道），208 个是 AI 编的 | ~1500 个真实数据 | 清掉 AI 数据，用权威源重新拉 |
| 数据质量 | 有坐标有评分，但无评价维度/标签/摘要 | 核心实体有完整画像 | 需要评论提取流程 |
| 行程生成 | generate_trip 能跑通，但只有 3-4 个活动 | 每天 4-6 个活动 + 餐食 + 交通 | 需要更多 entity_roles 绑定 + meal_filler 修复 |
| 片段/模板 | 无 | 北海道 40-50 个片段 + 20 个模板 | 全部要新建 |
| PDF 输出 | 能生成 12 页 PDF，但无图片 | 有图有文案有地图 | 需要图片关联 + 文案填充 |
| 前置约束 | planning_defaults.json 有部分 | 定休日/气候/节假日/交通全套 | 需要数据表 + 查询接口 |
| 管理后台 | 基本 CRUD + trust_status | 片段编辑器 + 模板预览 + 数据覆盖看板 | 大量前端工作 |
| 数据源 | Google Places + Tabelog 列表页 | 10+ 个源按城市圈配置 | 爬虫开发 + 注册中心 |

---

## 第八章：设计取舍决策

> 2026-03-30 审视后的精简决策。每个去掉的设计都记录原因，避免后续重复讨论。

### 保留的设计

| 设计 | 理由 |
|------|------|
| data_source_registry | 数据源会越来越多，需要注册中心统一管理 |
| city_data_coverage | 追踪每个城市的数据覆盖进度 |
| entity_source_scores | **展示给用户**（"Tabelog 3.65 / 米其林一星 / Google 4.4"），不做加权综合分 |
| entity_review_signals + 维度 | 核心内容价值——让手账本有实用信息而不是只有地名 |
| entity_tags | 标签过滤是推荐的第一层（不吃生的→排除寿司） |
| day_fragments + 方案A条件替代 | 片段预编排，保存时写死替代方案（定休日/雨天），调用时简单查表替换 |
| itinerary_templates | 模板复用，90% 订单不需要从零生成 |
| trust_status | 区分真实/AI/存疑数据 |
| dedup engine | 防止同一地点存两条 |
| BaseCrawler 统一接口 | 新爬虫遵循统一格式，方便扩展 |
| 模板级质量审核（Opus 审一次） | 模板创建时 Opus 审核，后续复用不再审 |

### 去掉的设计

| 设计 | 原因 |
|------|------|
| discovery_candidates 表 | 直接写 entity_base，用 trust_status 区分。少一个中间表少一层复杂度 |
| CrawlScheduler 调度器 | 用 data_source_registry.crawl_frequency + cron 脚本替代。现阶段爬虫少不需要调度系统 |
| entity_distance_cache | 同城市用 Haversine 实时算，跨城市交通时间写配置。后续可用乘换案内 API |
| 多源加权综合分计算 | entity_source_scores 只存各源独立评分供展示，不算加权。推荐排序直接用权威源评分 |
| fragment 变体多版本方案 | 改用方案 A：片段内每个活动保存 alternatives，运行时按条件替换 |
| 每单三层质量门控 | 模板已审核，每单只需 Haiku 格式快检 + 定休日规则检查 |
| AI 个性化匹配第三层 | V1.0 用标签过滤 + 评分排序够用，推迟到 V1.5 |

### 片段替代方案数据结构（方案 A）

片段 items 中每个活动可以带替代信息，编排片段时一次性填好：

```json
{
  "entity_id": "xxx",
  "type": "restaurant",
  "start": "11:30",
  "duration": 60,
  "note": "招牌时令五贯盛 ¥2,200",
  "closed_days": ["monday"],
  "alternatives": [
    {
      "entity_id": "yyy",
      "reason": "周一定休时替代",
      "note": "旭寿司，同在寿司屋通，握寿司套餐 ¥1,800"
    }
  ],
  "rain_alternative": {
    "entity_id": "zzz",
    "reason": "雨天室内替代",
    "note": "小樽音乐盒堂二楼咖啡厅"
  }
}
```

调用时判断逻辑极简：
```python
if day_of_week in item.get("closed_days", []):
    item = item["alternatives"][0]
if weather == "rain" and "rain_alternative" in item:
    item = item["rain_alternative"]
```

### 数据源采集频率（替代 CrawlScheduler）

直接在 data_source_registry 中配置，cron 按频率执行：

| 频率 | 数据源 | 说明 |
|------|--------|------|
| quarterly（每季度） | Tabelog / Google Places / 大众点评 | 核心评分源，季度更新够用 |
| yearly（每年） | Japan Guide / 官方旅游网站 / 攻略网站 | 内容变化慢 |
| manual（手动） | 新发现的攻略网站 | 你手动触发 |

不需要 weekly——手账本不是实时产品，季度更新已经够用。

---

## 附录 A：数据源层级 & 信任标记规则

### 四层数据源层级

```
第1层 权威评分源（决定推不推荐）
  → Japan Guide 2-3星景点 → data_tier='S', trust_status='unverified'
  → Tabelog 3.5+ 餐厅 → data_tier='A', trust_status='unverified'
  → Tabelog 3.0-3.5 → data_tier='B', trust_status='unverified'
  → 大众点评必吃榜 → data_tier='S', trust_status='unverified'
  → Jalan/携程酒店 → data_tier='A', trust_status='unverified'

第2层 基础设施源（补坐标/营业时间，不做推荐决策）
  → Google Places API → 只补字段，不改 data_tier
  → 高德 API → 同上

第3层 感知层（调分+打标签）
  → 小红书/马蜂窝/TripAdvisor → 只影响 entity_tags 和 soft_scores
  → 不改 data_tier 和 trust_status

第4层 兜底（极偏远地区）
  → AI 生成 → data_tier='C', trust_status='ai_generated'
  → 手账本上注明"建议出发前确认"
```

### trust_status 自动标记规则

| 数据来源 | trust_status | data_tier |
|----------|-------------|-----------|
| Japan Guide / 官方旅游网站 | unverified | S |
| Tabelog 3.5+ / 大众点评必吃榜 | unverified | A |
| Google Places / Jalan / 携程 | unverified | A |
| Tabelog 3.0-3.5 / 普通攻略提及 | unverified | B |
| 小红书/马蜂窝提取 | unverified | B |
| AI 生成 | ai_generated | C |
| 坐标异常/名称疑似重复 | suspicious | 不变 |
| 人工审核通过 | verified | 不变 |
| 人工拒绝 | rejected | 不变 |

### 多源评分归一化

```
Tabelog 3.0-5.0 → 0-100:  score = (tabelog - 2.5) * 40  (3.0→20, 3.5→40, 4.0→60, 4.5→80)
Google  1.0-5.0 → 0-100:  score = (google - 1.0) * 25   (3.0→50, 4.0→75, 4.5→87.5)
Japan Guide 1-3 → 0-100:  1星→50, 2星→75, 3星→95
大众点评 1-5    → 0-100:  score = (dp - 2.0) * 33       (3.5→50, 4.0→66, 4.5→83)

综合评分加权（日本餐厅）：
  Tabelog × 0.5 + Google × 0.2 + 攻略提及度 × 0.3

综合评分加权（日本景点）：
  Japan Guide × 0.4 + Google × 0.2 + 攻略提及度 × 0.4
```

---

## 附录 B：评价维度完整定义

### 餐厅 6 维度

| 维度 | 字段名 | 类型 | 说明 |
|------|--------|------|------|
| 招牌菜明确度 | signature_dish_clarity | clear/vague/none | 有没有"来了必点"的菜 |
| 排队风险 | queue_risk | none/low/medium/high | 是否经常排队 |
| 预约难度 | reservation_difficulty | walk_in/easy/hard/impossible | 能否直接去 |
| 语言友好度 | language_friendliness | japanese_only/menu_ok/english_ok | 有没有图片菜单 |
| 支付方式 | payment_method | cash_only/card_ok | 很多日本小店只收现金 |
| 性价比感知 | value_perception | below/fair/above | 值不值 |

### 景点 8 维度

| 维度 | 字段名 | 类型 |
|------|--------|------|
| 最佳时段 | best_timing | 字符串 "早上8-9点" |
| 天气敏感度 | weather_sensitivity | any/prefer_clear/rain_ruins |
| 体力要求 | physical_demand | easy/moderate/demanding |
| 拍照价值 | photo_value | low/medium/high/iconic |
| 人群密度模式 | crowd_pattern | 字符串 "旅行团10-14点集中" |
| 停留弹性 | duration_flexibility | fixed/flexible |
| 儿童适合度 | child_friendly | not_suitable/ok/great |
| 季节依赖 | season_dependency | any_season/specific_season |

### 酒店 7 维度

| 维度 | 字段名 | 类型 |
|------|--------|------|
| 位置便利度 | location_convenience | remote/ok/convenient/excellent |
| 房间状况 | room_condition | dated/acceptable/good/excellent |
| 温泉/浴场 | bath_quality | none/basic/good/exceptional |
| 早餐评价 | breakfast_quality | none/basic/good/highlight |
| 隔音情况 | soundproofing | poor/acceptable/good |
| 性价比 | value_perception | below/fair/above |
| 适合人群 | best_for | 字符串[] ["couple","family"] |

### 一句话摘要类型

```
review_why_go          — "二条市场最老的海鲜盖饭店，三色丼是招牌"
review_practical_tip   — "只收现金，11点前去不用排队"
review_skip_if         — "不吃生鲜的话可以跳过"
review_best_experience — "沿木栈道走一圈约30分钟，到大汤沼可以泡免费足汤"
review_heads_up        — "靠马路的房间有噪音，订房时备注要湖景侧"
```

### 评论过滤规则

```
跳过：少于 5 字、纯表情/星级、纯情绪（"太棒了！"/"垃圾！"）
采信负面评价：3+ 人重复提到同一问题才算客观
采信正面评价：必须有具体细节（"味噌汤底浓郁"而不是"好吃"）
维度无信号：留空，不猜测
```

### 维度 → 标签自动推断

```
queue_risk=high → tag: long_queue
payment_method=cash_only → tag: cash_only
child_friendly=great → tag: family_friendly
weather_sensitivity=rain_ruins → tag: outdoor_only
physical_demand=demanding → tag: not_for_elderly
reservation_difficulty=impossible → tag: reservation_required
photo_value=iconic → tag: photo_spot
```

### DB 存储

```
维度评分 → entity_review_signals.dimension_scores (JSONB)
一句话摘要 → entity_descriptions (description_type='review_why_go' 等)
标签 → entity_tags (tag_namespace='practical'/'audience'/'experience')
```

---

## 附录 C：片段 & 模板表结构

### day_fragments 表

```sql
CREATE TABLE day_fragments (
    fragment_id     SERIAL PRIMARY KEY,
    city_code       VARCHAR(50) NOT NULL,
    corridor        VARCHAR(100),
    fragment_type   VARCHAR(20) NOT NULL,        -- 'half_day' / 'full_day'
    theme           VARCHAR(100),

    items           JSONB NOT NULL,              -- 排好序的活动列表
    total_duration  SMALLINT,
    estimated_cost  INTEGER,                     -- 日元/人

    -- 适配条件
    best_season     VARCHAR(20)[],
    weather_ok      VARCHAR(20)[] DEFAULT '{any}',
    suitable_for    VARCHAR(20)[] DEFAULT '{any}',
    pace            VARCHAR(20) DEFAULT 'moderate',
    energy_level    VARCHAR(20) DEFAULT 'medium',

    -- 交通
    start_station   VARCHAR(100),
    end_station     VARCHAR(100),
    transit_from_prev VARCHAR(200),

    -- 文案
    title_zh        VARCHAR(200),
    summary_zh      TEXT,
    practical_notes TEXT,

    -- 质量
    quality_score   NUMERIC(4,2),                -- Opus 审核打分
    is_verified     BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 片段变体

同一路线不同条件的变体，不新建片段，通过 items 中的条件标记实现：

```json
{
  "entity_id": "xxx",
  "type": "restaurant",
  "start": "11:30",
  "duration": 60,
  "conditions": {
    "skip_if_day_of_week": ["monday"],
    "alternative_entity_id": "yyy",
    "alternative_reason": "周一定休，改去旁边的旭寿司"
  }
}
```

编排时自动检查 conditions，触发替换。

### itinerary_templates 表

```sql
CREATE TABLE itinerary_templates (
    template_id     SERIAL PRIMARY KEY,
    template_code   VARCHAR(100) UNIQUE NOT NULL,
    circle_id       VARCHAR(50) NOT NULL,
    duration_days   SMALLINT NOT NULL,

    party_types     VARCHAR(20)[] NOT NULL,
    pace            VARCHAR(20) NOT NULL,
    seasons         VARCHAR(20)[] NOT NULL,
    budget_levels   VARCHAR(20)[] DEFAULT '{mid}',

    day_plan        JSONB NOT NULL,              -- 引用 fragment_ids + 酒店 + 交通

    total_estimated_cost INTEGER,
    highlights      VARCHAR(200)[],
    title_zh        VARCHAR(200),
    description_zh  TEXT,

    opus_review_score NUMERIC(4,2),
    is_published    BOOLEAN DEFAULT FALSE,
    usage_count     INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

（entity_distance_cache 和 discovery_candidates 已在第八章中决定去掉。
距离用 Haversine 实时算；攻略扫描结果直接写 entity_base。）

---

## 附录 D：AI 模型路由 & 质量门控

### 模型路由器 (ai_router.py)

```python
class ModelTier(str, Enum):
    CREATIVE = "creative"       # GPT-5.3/4o
    ANALYTICAL = "analytical"   # Sonnet
    JUDGE = "judge"             # Opus
    FAST = "fast"               # Haiku
    CHEAP_CN = "cheap_cn"       # DeepSeek/Qwen

async def ai_call(prompt: str, tier: ModelTier, ...) -> str:
    config = MODEL_CONFIG[tier]
    # 自动选 provider + model + 参数
```

### 降级链

```
CREATIVE:   GPT-5.3 → GPT-4o → Sonnet → DeepSeek
ANALYTICAL: Sonnet → DeepSeek → GPT-4o
JUDGE:      Opus → Sonnet（降级时标记需人工复核）→ 绝不降到 Haiku
FAST:       Haiku → Qwen → DeepSeek
CHEAP_CN:   DeepSeek → Qwen → Haiku
```

### 三层质量门控

```
Haiku 快检（0.5秒 $0.001）：
  - 时间是否连续（09:00→10:30→12:00 不能跳到 09:00）
  - 营业时间是否对（不安排凌晨去景点）
  - 格式是否正确
  → 不过 → 自动修复后重跑

Sonnet 逻辑检查（2秒 $0.01）：
  - 路线是否合理（不来回折腾）
  - 同类型是否太密集（连续 3 个寺庙不行）
  - 预算是否超标
  - 餐食间隔是否合理（午餐12:00 晚餐18:00）
  - 交通衔接是否可行
  → 不过 → 重新编排后重跑

Opus 深度审核（5秒 $0.05）：
  - 整体体验是否好（有节奏感、有惊喜）
  - 推荐理由是否令人信服
  - 有没有明显遗漏（去札幌没安排拉面？）
  - 这本手账本值不值 298 元
  → 不过 → 给出具体修改建议 → 人工介入或重新生成
```

**只有三层都 pass 才发布。**

### 每单 AI 成本明细

```
一次性预计算（摊销到每单接近 0）：
  评论维度提取 50实体 × Sonnet ¥0.07 = ¥3.5（总计，不是每单）
  一句话摘要 50实体 × Sonnet ¥0.035 = ¥1.75
  标签提取 50实体 × Haiku ¥0.007 = ¥0.35
  片段文案 10片段 × GPT ¥0.14 = ¥1.4
  模板审核 1模板 × Opus ¥0.7 = ¥0.7
  ——总计一次性 ¥7.7，摊到 100 单 = ¥0.077/单

每单运行时：
  模板匹配 → 规则，¥0
  微调替换 → 规则或 Haiku ¥0.007
  定休日检查 → 规则，¥0
  质量快检 → Haiku ¥0.007
  逻辑检查 → Sonnet ¥0.07（仅改动大时）
  ——每单运行时 ¥0.01-0.08

极端情况（无匹配模板，从零生成）：
  匹配 + 编排 + 文案 + 3层审核 ≈ ¥5
```

---

## 附录 E：爬虫统一接口

### BaseCrawler

```python
class CrawlerResult:
    entities: list[dict]       # upsert_entity 兼容格式
    raw_snapshots: list[dict]  # 原始数据存 source_snapshots
    errors: list[str]
    source_name: str

class BaseCrawler:
    source_name: str

    async def fetch(self, city_code: str, entity_type: str,
                    limit: int = 50, **kwargs) -> CrawlerResult:
        raise NotImplementedError

    async def fetch_reviews(self, entity_id: str,
                            source_entity_id: str,
                            limit: int = 50) -> list[dict]:
        raise NotImplementedError
```

（CrawlScheduler 已在第八章中决定去掉。用 cron + crawl_frequency 替代。）

### 新数据源接入流程

```
1. data_source_registry 插一条记录（指定 crawl_frequency）
2. 写 crawler 文件（实现 BaseCrawler.fetch）
3. 在 cron 脚本中按 frequency 调用
→ 简单直接，不需要调度器
```
