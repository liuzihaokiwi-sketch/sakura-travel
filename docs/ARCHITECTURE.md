# 系统架构

> 最后更新: 2026-03-28

## 一句话定义

AI 旅行手账生成系统：用户填表 → 结构化决策 → 60页手账本 → PDF 交付。

---

## 系统全景

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户前端漏斗                              │
│  首页 → 问卷 → 样本 → 定价 → 详细表单 → 提交 → 查看计划        │
│  (前期不上线，抖音表单为主入口)                                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                      主链（6步）                                 │
│  表单输入 → 归一化 → 城市圈决策链 → 页面生成 → PDF渲染 → 交付   │
└──────────┬───────────────────────────────────┬──────────────────┘
           │                                   │
┌──────────▼──────────┐          ┌─────────────▼─────────────────┐
│   数据供给            │          │   质量门控                     │
│   爬虫 → 实体入库     │          │   规则检查 → 离线评测          │
│   → 打标 → 评分      │          │   → 多模型评审                 │
│   → 城市圈绑定       │          │   → publish / rewrite / human  │
└─────────────────────┘          └───────────────────────────────┘
           │                                   │
┌──────────▼───────────────────────────────────▼─────────────────┐
│                      运营后台                                    │
│  订单管理 · 实体 CRUD · 城市圈管理 · 配置中心 · Review 审核     │
└────────────────────────────────────────────────────────────────┘
```

---

## 一、主链（6步）

```
表单输入 → 归一化 → 城市圈决策链 → 手账页面生成 → PDF渲染 → 交付
```

### Step 1: 表单输入
- 入口: 抖音表单 / DetailForm
- 产出: `DetailForm` 行（raw_input JSON）
- 关键文件: `app/api/detail_forms.py`, `app/api/submissions.py`

### Step 2: 归一化
- 入口: arq job `normalize_trip_profile`
- 产出: `TripProfile` + `layer2_canonical_input`
- 关键文件: `app/workers/__main__.py`, `app/domains/intake/layer2_contract.py`
- 逻辑: 解析日期、推断标签、构建 canonical contract

### Step 3: 城市圈决策链
- 入口: `_try_city_circle_pipeline()` in `generate_trip.py`
- 子步骤（串行）:
  1. `select_city_circle` → 选圈
  2. `run_eligibility_gate` → 实体资格过滤
  3. `run_precheck_gate` → 运营事实预检
  4. `compile_constraints` → 约束编译
  5. `rank_major_activities` → 主活动排序
  6. `build_hotel_strategy` → 酒店策略
  7. `build_route_skeleton` → 骨架构建（DayFrame[]）
  8. `fill_secondary_activities` → 次要活动填充
  9. `fill_meals` → 餐厅填充
  10. `build_itinerary_records` → 写入 DB
- 产出: `plan_id`, `day_frames`, `design_brief`, `evidence_bundle`
- 关键文件: `app/workers/jobs/generate_trip.py`, `app/domains/planning/` 下各模块

### Step 4: 手账页面生成
- 入口: `build_planning_output()` → `plan_chapters()` → `plan_pages_and_persist()`
- 产出: `PageModel[]` 持久化到 `plan_metadata`
- 关键文件:
  - `app/domains/rendering/planning_output.py` — 从 DB + pipeline 直接构建页面数据
  - `app/domains/rendering/chapter_planner.py` — 章节规划
  - `app/domains/rendering/page_planner.py` — 页面规划（17种页型 + 预算裁剪）
  - `app/domains/rendering/page_view_model.py` — ViewModel 构建
  - `app/domains/rendering/copy_enrichment.py` — AI 文案填充（可选）

### Step 5: PDF 渲染
- 入口: arq job `render_export`
- 产出: PDF 文件 + `ExportAsset` 记录
- 关键文件: `app/workers/jobs/render_export.py`, `app/domains/rendering/magazine/`

### Step 6: 交付
- `shared_export_contract.py` → 统一导出合约
- PDF 通过 `ExportAsset.storage_url` 分发

---

## 二、数据供给（Catalog Pipeline）

给决策链喂实体数据。没有这个，决策链选不出东西。

```
爬虫采集 → 实体入库/去重 → AI打标 → 评分计算 → 城市圈绑定
```

| 环节 | 模块 | 说明 |
|------|------|------|
| 爬虫采集 | `scripts/` 下各 crawl 脚本 | tabelog/hotel/jnto/xhs/guide/experience，一次性脚本 |
| 实体入库 | `catalog/pipeline` + `upsert` | 清洗、去重、标准化字段写入 EntityBase |
| AI 补充 | `catalog/ai_generator` + `tagger` | AI 生成描述、自动打标签 |
| 评分计算 | `ranking/scorer` + `soft_rules` | base_score + editorial_boost(-8~+8) → final_score |
| 城市圈绑定 | `scripts/seed_kansai_*` | 实体 → 走廊 → 城市圈的角色关系 |

**当前状态**: 爬虫是手动脚本，无自动化 pipeline。Kansai 圈数据部分完成，其余5圈待补。

---

## 三、质量门控

主链生成完成后、交付前的质量关卡。

```
quality_gate → offline_eval → multi_model_review → publish/rewrite/human
```

| 环节 | 模块 | 说明 |
|------|------|------|
| 规则检查 | `core/quality_gate.py` | 硬规则：天数完整、实体存在、无空日 |
| 离线评测 | `evaluation/offline_eval.py` | 打分：完整性/可行性/多样性，0-1 分 |
| 多模型评审 | `review_ops/pipeline.py` | 6角色 AI 评审：QA/用户代理/运营代理/微调守卫/终审 |
| 评审回写 | `review_ops/review_writeback.py` | 评审意见回写到数据层 |
| 回归测试 | `scripts/run_regression.py` | 自动化回归，对比历史 case |

**裁决三路分流**:
- `publish` → 进入渲染交付
- `rewrite` → 自动重写（最多2轮）
- `human` → 进人工 review 队列

---

## 四、运营后台（Ops Console）

运营人员日常操作界面。

### 已实现

| 功能 | 前端页面 | 后端 API | 说明 |
|------|---------|---------|------|
| 订单看板 | `admin/page.tsx` | `api/submissions` | 7列看板，11状态流转 |
| 订单详情 | `admin/order/[id]` | `api/submissions/{id}` | 状态推进、表单创建、计划预览 |
| 实体 CRUD | `admin/catalog` | `api/ops/catalog` | 酒店/餐厅/POI 增删改查 |
| 编辑加权 | `admin/catalog` | `api/ops/editorial` | editorial_boost -8~+8，带时间窗 |
| 配置管理 | `admin/config` | `api/admin/config` | 权重包/阈值/开关，版本+发布流 |
| Review 审核 | `admin/` | `api/review` | 发布/打回/编辑 |
| Trace 查看 | `admin/trace` | `api/admin/trace` | 生成链路 debug |
| 评测结果 | `admin/evals` | `api/admin/evals` | 离线评测分数查看 |

### 待实现

| 功能 | 重要度 | 说明 |
|------|--------|------|
| 城市圈结构管理 | **高** | 圈/走廊/实体角色关系 CRUD，目前只能跑 seed 脚本 |
| 活动集群管理 | **高** | 主活动 cluster 增删改查，决策链从这里选活动 |
| 酒店预设管理 | **中** | 住法策略配置（单点/双点/三点） |
| Operator Override | **中** | 推荐干预（boost/block/pin），DB 表在但无前端 |
| 素材审核 | **低** | entity_media 的 needs_review 审核流 |
| 数据质量仪表盘 | **低** | 实体覆盖率、层级分布、评分分布 |

---

## 五、产品/SKU 体系

```
ProductSku (¥298国内 / ¥348国外) → Order → TripRequest
```

- 模块: `domains/product/model.py` + `scripts/seed_product_skus.py`
- 前端: `web/app/pricing/` 展示
- 很轻，当前够用

---

## 六、用户前端漏斗

**前期不上线**，抖音表单为主入口。设计已有，代码骨架已有。

```
首页 → 问卷 → 样本预览 → 定价 → 详细表单 → 提交 → 等待 → 查看计划
```

| 页面 | 路径 | 状态 |
|------|------|------|
| 首页 | `web/app/page.tsx` | 骨架 |
| 问卷 | `web/app/quiz/` | 骨架 |
| 样本预览 | `web/app/sample/` | 骨架 |
| 定价 | `web/app/pricing/` | 骨架 |
| 详细表单 | `web/app/detail-form/` | 旧版，V3 设计稿见 `docs/product/` |
| 提交确认 | `web/app/submitted/` | 骨架 |
| 计划查看 | `web/app/plan/` | 骨架 |

---

## 实体评分与推荐机制

### 质量档（取代精细评分）

| 档位 | 含义 | 进入条件 |
|------|------|---------|
| 5 极好 | 值得专程去 | 编辑认定+多源高分 |
| 4 很好 | 推荐给大多数人 | 评分+评论达标 |
| 3 不错 | 主流稳定选择 | 数据充分无负面 |
| 2 凑合 | 不主动推荐 | 有瑕疵或数据不足 |
| 1 避开 | 有负面信号 | 风险标签命中 |

同档内完全平权，选择由上下文决定（菜式/距离/轮转/画像匹配）。默认只推荐 3 档及以上。

### 避雷三层过滤

```
硬黑名单（永不推荐）→ 风险标签（默认过滤，用户可放开）→ 正常池
```

风险标签：environment_basic / service_rough / queue_extreme / cash_only / hygiene_concern 等。
用户表单中"我可以接受"选项默认不勾 = 帮你避开。

### 推荐多样性

- 推荐计数器（近30天被推荐次数）→ 高频降权
- 同档软随机 → 不总选 Top 1
- 菜式不重复 → 连续两餐不同菜式
- discovery_gem 标记 → 隐藏好店额外曝光

详见 `docs/DATA_STRATEGY.md`。

---

## 关键边界

| 边界 | 规则 |
|------|------|
| 表单 → 归一化 | 归一化后系统不再读原始表单数据 |
| 决策 → 页面 | 页面直接消费结构化数据，无文本中间层 |
| 页面模型 → 渲染 | 渲染器只做数据→视觉映射，无业务逻辑 |
| 主链失败 | 显式失败进人工队列，无隐式回退到老链 |
| 比价边界 | 不提供跨天/跨方案比价；仅当天酒店/餐厅选择时考虑性价比 |
| 机票边界 | 系统不管机票，用户自行预订并提供落地/返程时间 |
| 避雷优先 | 宁可少推荐不能推差的，一次糟糕体验毁掉整本手账价值 |

---

## 技术栈

| 层 | 技术 |
|----|------|
| API | FastAPI (async) |
| 任务队列 | arq (Redis) |
| 数据库 | PostgreSQL (asyncpg) |
| AI 模型 | gpt-4o-mini (轻量) / gpt-4o (标准) / claude-sonnet (强推理) |
| PDF | WeasyPrint |
| 前端 | Next.js 14 (TypeScript) |

## 数据库分层

| 层 | 模型 | 用途 |
|----|------|------|
| Business | User, Order, TripRequest, TripProfile, ReviewJob | 业务实体 |
| Catalog | EntityBase, EntityTag, EntityEditorNote | POI/餐厅/酒店数据 |
| Derived | ItineraryPlan, ItineraryDay, ItineraryItem, EntityScore, ExportAsset | 计算结果 |
| Config | SoftRuleSchema, SegmentWeightPack, OperatorOverride | 运营配置 |
| CityCircle | CityCircle, CircleEntityRole, Corridor | 城市圈地理结构 |

## 目录结构

```
app/
  api/              # REST 路由
    ops/            # 运营 API（实体 CRUD、编辑加权、排名）
  core/             # 基础设施（config, queue, ai_client, quality_gate）
  db/               # 模型 + 迁移
  domains/
    intake/         # 表单归一化
    planning/       # 决策链（城市圈选择 → 骨架构建）
    rendering/      # 页面生成 + 渲染
    ranking/        # 实体评分
    evaluation/     # 离线评测
    review_ops/     # 多模型评审
    catalog/        # 实体采集管理
    product/        # SKU 体系
    validation/     # 表单校验引擎
    feedback/       # 反馈蒸馏（骨架）
    scoring/        # 软规则维度
    tracking/       # 事件追踪（骨架）
  workers/          # arq 后台任务
web/
  app/
    admin/          # 运营后台
    api/admin/      # 后台 API 代理
    quiz/sample/... # 用户前端漏斗（前期不上线）
  lib/admin-api.ts  # 后台 API 客户端
scripts/            # 爬虫 + 种子数据 + 运维工具
tests/              # 测试
docs/               # 文档（3篇核心 + 产品规范）
```

---

## 已删除的模块

| 模块 | 原因 |
|------|------|
| `domains/planning/report_generator.py` | Report-First 胶水层，被 planning_output.py 替代 |
| `domains/rendering/layer2_handoff.py` | 同上 |
| `domains/planning/assembler.py` | v1 模板引擎，被城市圈决策链替代 |
| `domains/rendering/renderer.py` | Jinja2 老渲染器，被 magazine/ 替代 |
| `domains/flights/` | 航班监控，系统不管机票（待删除） |
