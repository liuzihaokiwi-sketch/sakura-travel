## Why

Phase 0 已完成数据底座：三城市 ~800 实体入库、GPT 9 维标签、评分引擎、Editorial Boost 运营接口。但系统当前**只能输出排序列表，不能输出用户可用的攻略产品**。

定价方案已确定（19.9 基础版 → 1999 超级定制版），19.9 基础版是核心引流款——用户拿到手必须觉得"这个质量值一两百"。要实现这个，需要：**行程编排引擎 + 杂志级模板渲染 + 路线模板 + 导出管线**。

Phase 1 的目标是：**让系统能生成 19.9 基础版攻略，质量达到杂志级，H5 + PDF 双格式交付。**

## What Changes

### 新增能力

- **路线模板系统**：设计 3-5 条经典日本路线模板（东京经典 5 日、关西经典 6 日、东京+关西 7 日等），每条模板定义每日时间块、实体槽位、交通衔接
- **行程编排引擎 v1**：基于模板 + 评分排序，自动装配实体到时间槽位，生成结构化行程 JSON（itinerary_plans → itinerary_days → itinerary_items）
- **杂志级模板渲染**：HTML/CSS 排版系统，支持封面、每日行程卡片、地图标注、餐厅/景点卡片、交通指引、实用信息页
- **PDF 导出管线**：WeasyPrint 将 HTML 渲染为高质量 PDF，支持 export_jobs 异步队列
- **H5 预览页面**：移动端友好的在线预览，可分享链接
- **AI 文案润色层**：LLM 只做表达层（景点一句话描述、过渡语、小 Tips），不做事实判断
- **区域住宿指南**：hotel_area_guide 内容，引流款只推区域不推具体酒店
- **Google Routes 交通矩阵**：获取实体间步行/公交/地铁时间，写入 route_matrix_cache
- **自动审核规则 v1**：hard_fail（时间冲突/交通不可达/实体已关闭）+ soft_fail（节奏过紧/餐厅缺失）
- **plan_artifacts 追溯链路**：每次生成记录完整版本链（profile_version → score_version → template_version）

### 接入层变更

- 新增 `POST /trips/{id}/generate`：触发 19.9 基础版行程生成（选场景 → 匹配模板 → 装配 → 渲染 → 交付）
- 新增 `GET /trips/{id}/preview`：H5 预览
- 新增 `GET /trips/{id}/exports`：获取 PDF 下载链接
- 新增 `GET /products`：产品列表（先只上 19.9 基础版 SKU）
- 新增 `POST /orders`：创建订单（先对接简单支付）

## Capabilities

### New Capabilities

- `route-templates`: 路线模板定义（模板结构、时间块、实体槽位、场景变体、经典路线种子数据）
- `trip-assembler`: 行程装配引擎（模板 + 评分 → 结构化行程 JSON，约束校验，备选替换逻辑）
- `magazine-renderer`: 杂志级渲染系统（HTML/CSS 模板架构、组件库、封面/日卡片/实体卡片、PDF 导出、H5 预览）
- `route-matrix`: Google Routes 交通矩阵（步行/公交时间获取、缓存策略、fallback）
- `ai-copywriter`: AI 文案润色（景点描述、过渡语、Tips 生成，LLM prompt 模板，只做表达不做事实）
- `export-pipeline`: 导出管线（export_jobs 队列、WeasyPrint 渲染、export_assets 存储、下载链接生成）

### Modified Capabilities

- `itinerary-planner`: 从"规格定义"推进到"v1 实现规格"——定义基于模板装配的具体编排算法、时间块填充规则、约束检查
- `template-renderer`: 从"三层模板架构定义"推进到"杂志级 CSS 实现规格"——定义具体组件、配色方案、排版规范
- `review-gate`: 增加 v1 自动审核规则（hard_fail/soft_fail 具体条件列表）
- `product-tiers`: 增加 19.9 基础版的具体 workflow_config（触发条件、模板选择、渲染参数）
- `scoring-engine`: 增加候选召回逻辑（从"全量排序"到"按模板槽位类型召回 + 排序"）

## Impact

### 代码变更

- 新增 `app/domains/planning/` — 行程装配引擎
- 新增 `app/domains/rendering/magazine/` — 杂志级渲染组件
- 新增 `app/workers/jobs/generate_trip.py` — 行程生成 job
- 新增 `app/workers/jobs/render_export.py` — 渲染导出 job
- 新增 `app/api/products.py` — 产品/订单 API
- 修改 `app/domains/ranking/` — 增加候选召回
- 修改 `app/domains/rendering/renderer.py` — 集成杂志级模板
- 新增 `templates/magazine/` — HTML/CSS 模板文件
- 新增 `data/route_templates/` — 路线模板 JSON

### 数据库

- 写入：itinerary_plans / itinerary_days / itinerary_items / planner_runs
- 写入：route_matrix_cache
- 写入：export_jobs / export_assets / plan_artifacts
- 写入：route_templates / render_templates
- 写入：product_sku / orders
- 读取：entity_base + entity_scores + entity_tags + entity_media

### 外部依赖

- Google Routes API（交通时间矩阵）
- OpenAI GPT-4o-mini（文案润色）
- WeasyPrint（PDF 渲染，需要系统级依赖：cairo + pango）
- 对象存储（PDF/H5 静态文件，初期可用本地 + nginx）

### 产品价位作用

Phase 1 直接支撑 **19.9 基础版**（引流款）的完整交付链路。这是用户第一次付费触点，质量直接决定后续升级转化率。

### MVP 优先级

| 优先级 | 能力 | 理由 |
|--------|------|------|
| P0 必须 | route-templates + trip-assembler | 没有编排就没有产品 |
| P0 必须 | magazine-renderer + export-pipeline | 没有渲染就无法交付 |
| P1 重要 | route-matrix | 交通时间让行程可信，但 v1 可先用估算 |
| P1 重要 | ai-copywriter | 文案让攻略有温度，但 v1 可先用固定模板文案 |
| P2 可延后 | 支付接入 | 初期可手动收款+发货 |
