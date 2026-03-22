# AI Codebase Map

> AI agent 工作手册：代码地图、模型、管线、风险文件


---

# Config Inventory（AI 版）

## 原则
只记录对当前主链路重要的配置，不重复罗列所有低优先级变量。

## 核心后端配置
- `APP_ENV`
- `APP_DEBUG`
- `SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`
- `AI_BASE_URL`
- `AI_MODEL`
- `AI_MODEL_STRONG`
- `OPENAI_API_KEY`
- `GOOGLE_PLACES_API_KEY`

## 运维/告警配置
- `WECOM_WEBHOOK_URL`
- `SMTP_HOST`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `ALERT_EMAIL`

## Worker/TTL 配置
- `SNAPSHOT_TTL_HOTEL_OFFER`
- `SNAPSHOT_TTL_FLIGHT_OFFER`
- `SNAPSHOT_TTL_POI_OPENING`
- `SNAPSHOT_TTL_WEATHER`
- `WORKER_MAX_JOBS`
- `JOB_RETRY_MAX`
- `JOB_RETRY_DELAY_SECS`

## 前端关键配置
- `NEXT_PUBLIC_API_URL`

## 当前配置问题
1. 微信号存在前端硬编码
2. 一些价格和产品逻辑不应该继续分散在配置/种子/文案里
3. 当前项目缺少独立的 single source of truth 配置文件

## 建议
后续新增：
- `single_source_of_truth.yaml`
用于统一：
- 价格参考价
- 免费体验边界
- 自助微调规则
- 正式修改次数
- 页面职责

---

# Data Models（AI 版）

## 目标
让 AI 快速知道“当前库里有什么”，并知道哪些模型是旧结构，哪些是可延续基础。

## 当前四层
1. Catalog：实体、标签、媒体、编辑备注
2. Snapshots：外部时效数据快照
3. Derived：评分、行程、导出、产物
4. Business：用户、订单、请求、画像、版本、审核

## 仍然有效的核心模型
### Catalog
- `entity_base`
- `pois`
- `hotels`
- `restaurants`
- `entity_tags`
- `entity_media`
- `entity_editor_notes`
- `hotel_area_guide`

### Derived
- `entity_scores`
- `itinerary_plans`
- `itinerary_days`
- `itinerary_items`
- `itinerary_scores`
- `route_templates`
- `export_jobs`
- `export_assets`
- `plan_artifacts`
- `route_matrix_cache`

### Business
- `users`
- `orders`
- `trip_requests`
- `trip_profiles`
- `trip_versions`
- `review_jobs`
- `review_actions`

## 旧结构但仍可能被调用的模型
### `product_sku`
这是现有代码事实，但不是最终产品模型。  
当前新方向是：
- 前台少套餐
- 后台多维映射

因此后续不要继续把 `product_sku` 当成完整产品真相源，尤其不要从它反推前台产品定义。

## 反馈与增长相关模型（需特别记住）
代码和旧文档里还涉及：
- `user_entity_feedback`
- 可能存在的 `entity_time_window_scores` / crowd 类派生分层
- 订单、反馈、复购意向的业务扩展字段

AI 在改动反馈/复购相关功能时，不要只盯 `orders` 和 `trip_profiles`。

## 当前缺少但新方向需要的概念层
这些不一定都要立刻变成表，但 AI 应知道后续会需要：
- 主题家族
- 时间扩展包
- 预算偏向
- 免费体验边界
- 自助微调配置
- 条件页触发规则
- 预览钩子配置

## 真相源边界
- 数据模型文档描述的是“当前代码现实”
- 产品定义真相源在 `product-scope.md` 和人类产品文档中
- 如果 DB 结构和产品定义冲突，先标冲突，不要假装数据库已经迁移完成

## 结论
当前数据库仍可继续用，但 AI 在做设计时要把“旧 SKU 结构”和“新产品结构”分开理解；涉及反馈、复购、体验版、主题层时，不能只盯旧表名推断产品逻辑。

---

# Dependency Map（AI 版）

## 核心主链路
### 问卷提交 → 画像 → 方案 → 详情 → 导出
- `app/api/quiz.py`
- `workers/__main__.py::normalize_trip_profile`
- `workers/jobs/generate_plan.py`
- `workers/jobs/generate_trip.py`
- `workers/jobs/run_guardrails.py`
- `workers/jobs/render_export.py`

## 排序主链路
- `ranking/scorer.py`
- `ranking/affinity.py`
- `ranking/queries.py`
- `planning/assembler.py`

## 内容与专题页主链路
### `/rush`
- `web/app/rush/page.tsx`
- `web/lib/data.ts`
- `data/sakura/*.json`
- `web/app/rush/RushClient.tsx`

## 现阶段最不该忽略的依赖
1. `/rush` 依赖的数据文件是强耦合的
2. assembler 强依赖 ranking 结果
3. PDF 导出强依赖模板和渲染器
4. 旧产品 SKU 仍可能被订单/产品 API 调用

## AI 修改顺序建议
1. 先理解主链路
2. 再理解具体模块
3. 最后才动高风险模块

---

# Do Not Break（AI 版）

## 最高风险文件
这些文件一旦修改，会直接影响全局输出或系统可用性。

- `app/domains/ranking/scorer.py`：三层评分核心
- `app/domains/planning/assembler.py`：行程装配核心
- `app/db/models/business.py`：订单、请求、画像等核心业务表
- `app/db/models/catalog.py`：实体主表和扩展表
- `app/main.py`：应用入口
- `app/db/session.py`：数据库连接
- `web/lib/data.ts`：/rush 实时数据加载器

## 修改前必须做的事
1. 先读依赖关系
2. 先确认是否已有测试或验证脚本
3. 先确认是不是“产品文档要改”而不是“代码先改”
4. 改 ORM 字段前先想迁移

## 当前最常见误改风险
- 把旧 SKU 逻辑硬删，导致订单和产品接口坏掉
- 改 scorer 但没重新验证排序质量
- 改 assembler 但没验证 PDF/H5 结构
- 改 `/rush` 数据字段导致页面白屏
- 改首页首屏结构却不验证移动端

## 数据文件不可删除
- `data/seed/entity_affinity_seed_v1.json`
- `data/seed/p0_route_skeleton_templates_v1.json`
- `data/seed/japan_region_usertype_matrix_v1.json`
- `data/seed/context_score_design.json`
- `data/seed/questionnaire_to_theme_weights_rules_v1.json`
- `data/sakura/sakura_rush_scores.json`
- `data/sakura/weathernews_all_spots.json`
- `data/sakura/jma/jma_city_truth_2026.json`
- `data/route_templates/*.json`

## 修改后最少验证
- API 能启动
- 前端首页可打开
- `/rush` 不白屏
- 一条行程生成链路能跑通
- PDF 导出不报错

---

# Module Registry（AI 版）

## 只保留 AI 最需要知道的模块

### 入口层
- `app/main.py`：FastAPI 应用入口
- `app/api/quiz.py`：问卷提交
- `app/api/trips_generate.py`：生成与导出触发
- `app/api/products.py`：产品与价格接口
- `app/api/orders.py`：订单状态流转

### 领域层
- `app/domains/intake/intent_parser.py`：意图解析
- `app/domains/geography/region_router.py`：区域推荐
- `app/domains/geography/route_selector.py`：路线模板匹配
- `app/domains/ranking/scorer.py`：评分核心
- `app/domains/ranking/queries.py`：候选查询
- `app/domains/planning/assembler.py`：行程装配
- `app/domains/planning/copywriter.py`：AI 文案润色
- `app/domains/planning/route_matrix.py`：交通矩阵
- `app/domains/rendering/renderer.py`：HTML/PDF 渲染

### Worker
- `generate_itinerary_plan`
- `generate_trip`
- `run_guardrails`
- `render_export`
- `score_entities`

### 前端核心
- `web/app/page.tsx`：首页
- `web/app/quiz/page.tsx`：问卷
- `web/app/pricing/page.tsx`：价格页
- `web/app/rush/page.tsx`：樱花页
- `web/app/plan/[id]/page.tsx`：交付页（当前仍有 mock 风险）
- `web/lib/data.ts`：樱花数据加载

## AI 注意
如果只是做产品和文档对齐，不要从所有模块开始读；只需先读以上模块。

---

# Naming Conventions（AI 版）

## 保持现有约定
- Python：snake_case / PascalCase / UPPER_SNAKE_CASE
- TypeScript：组件 PascalCase，工具 camelCase
- DB：表和列 snake_case

## 新文档与新配置建议命名
- 人类文档：数字前缀 + snake_case
- AI 文档：功能直名，如 `single_source_of_truth.yaml`
- 规则文件：`*_rules_v1.json`
- 方案树文件：`*_families_v1.json`
- 时间扩展包：`time_expansion_pack_*.json`

## 命名原则
- 产品前台名称不要等于后台字段名
- 后台维度名称要可组合、可映射、可扩展

---

# Pipeline Catalog（AI 版）

## 当前最重要的 5 条管线

### 1. 问卷画像管线
输入：问卷 raw_input  
输出：`trip_profiles`

### 2. 行程骨架生成管线
输入：`trip_request_id`  
输出：`itinerary_plans` + `itinerary_days`

### 3. 行程详情填充管线
输入：`trip_request_id`  
输出：`itinerary_items`

### 4. 护栏检查管线
输入：`plan_id`  
输出：检查结果 + 状态

### 5. 导出交付管线
输入：`plan_id`  
输出：PDF / H5 资产

## 数据采集管线
- `catalog/pipeline.py`
- `scripts/crawl_orchestrator.py`
- `scripts/crawlers/sakura_pipeline/*`

## 当前产品新方向尚未完全入管线的部分
- 免费体验版钩子生成
- 自助微调闭环
- 条件页触发系统
- 预算偏向影响逻辑

## AI 使用原则
- 先在现有主链路上改，少发明新链路
- 新方向优先做“插入式增强”，不要先推翻所有旧 pipeline

---

# Prompt Catalog（AI 版）

## 当前仍在使用的 prompt 场景
1. `catalog/tagger.py`：标签生成
2. `planning/copywriter.py`：一句话描述 + tips
3. `intake/intent_parser.py`：自然语言意图解析
4. `catalog/ai_generator.py`：离线生成实体

## 当前 prompt 使用原则
- Prompt 只负责少量高价值解释
- 不要用 prompt 代替结构、规则和配置
- 能模板化的不要交给 AI 从头写

## 新方向下 prompt 的角色
最值得交给 AI 的：
- 总设计思路
- 每日亮点解释
- 复杂取舍说明
- 少量个性化润色

不值得继续重写的：
- 通用出发前准备
- 通用安全提示
- 重复性酒店/餐厅理由
- 可以由规则直接给出的判断

---

# Repo Index（AI 版）

> 作用：帮助 AI 和开发者快速理解仓库结构。它描述的是当前代码现实，不等于最终产品真相源。

## 一、仓库结构

### 后端
- `app/api/`：HTTP 路由入口
- `app/core/`：配置、队列、缓存、日志
- `app/db/models/`：ORM 模型，按 catalog / business / derived / snapshots 分层
- `app/domains/`：领域逻辑，主要包括 catalog / ranking / planning / rendering / geography
- `app/workers/`：异步任务
- `app/main.py`：FastAPI 入口

### 前端
- `web/app/`：Next.js App Router 页面
- `web/components/`：共享组件
- `web/lib/`：前端工具函数与数据加载器
- `web/scripts/`：前端导出、验证脚本

### 脚本与数据
- `scripts/`：数据采集、初始化、维护脚本
- `data/`：seed / sakura / route_templates / crawled 等数据
- `templates/`：Jinja2 渲染模板

### 文档
- `docs-human/`：人类文档
- `docs-ai/`：当前旧版 AI 文档
- `docs-ai-v2/`：新的 AI 指引文档
- `openspec/`：变更管理

## 二、当前代码事实
- 代码仍保留 `product_sku`、旧产品档位和旧生成链路
- 前端已有首页、问卷、价格页、/rush、提交成功页、plan 页面
- `/rush` 已有真实数据加载器和交互组件
- 行程生成主要依赖 ranking + assembler + copywriter + render

## 三、已知与新方向的偏差
1. 产品新方向强调“前台少套餐、后台多维映射”，代码里仍保留旧 SKU 设计
2. 新方向强调“总纲 + 每日固定骨架 + 条件页”，代码里还没有完整落地
3. 新方向强调“免费体验版 = 一天完整样片 + 后续钩子”，现有代码未必完全实现
4. 新方向强调“自助微调优先”，代码中该闭环仍需补全

## 四、AI 读取顺序
1. 看本文件
2. 看 `do_not_break.md`
3. 看 `runtime_entrypoints.md`
4. 看 `data_models.md`
5. 看 `dependency_map.md`
6. 再去读具体模块

## 五、不要做的事
- 不要把旧代码中的产品结构自动当成最终产品真相源
- 不要先改高风险文件再理解依赖
- 不要忽略 `/rush`、预览页、问卷和 PDF 交付这些现阶段核心链路

---

# Runtime Entrypoints（AI 版）

## 基础依赖
- Docker：Postgres + Redis
- Python 3.12+
- Node 20+
- `.env` 基于 `.env.example`

## 后端启动
```bash
uvicorn app.main:app --reload --port 8000
```

## Worker 启动
```bash
python -m app.workers
```

## 前端启动
```bash
cd web && npm run dev
```

## 从零启动最小顺序
```bash
docker compose up -d postgres redis
python scripts/init_db.py
python scripts/fix_and_init.py
uvicorn app.main:app --reload --port 8000
cd web && npm ci && npm run dev
python -m app.workers
```

## 当前最有价值的验证顺序
1. 首页是否正常
2. `/rush` 是否正常
3. `/quiz` 是否能提交
4. 生成链路能否跑到 plan
5. PDF 是否能导出

## AI 注意
- 不要把所有脚本都当成当前必须入口
- 当前重点是主站、/rush、问卷、生成、导出闭环
