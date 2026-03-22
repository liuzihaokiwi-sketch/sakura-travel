# Travel-AI 项目架构全景图

> 本文件是整个项目的工程架构真相源。所有模块设计、任务拆分、优先级判断以此为准。
> 最后更新：2026-03-22

---

## 核心架构：4 层

```
┌─────────────────────────────────────────────────────────────┐
│                    Layer 4: 评测、校验与运营层                │
│  precheck · quality_gate · fallback · live_risk · eval      │
├─────────────────────────────────────────────────────────────┤
│                    Layer 3: 报告与渲染层                     │
│  report_schema · page_plan · page_type · 文案 · 渲染 · PDF  │
├─────────────────────────────────────────────────────────────┤
│                    Layer 2: 决策与编排层                     │
│  select_circle · rank_major · build_hotel · skeleton ·      │
│  fill_secondary · fill_meals · eligibility · scoring        │
├─────────────────────────────────────────────────────────────┤
│                    Layer 1: 数据与知识层                     │
│  city_circles · entity_base · activity_clusters · hotel_    │
│  presets · snapshots · 采集 · 清洗 · 风险事实 · 新鲜度       │
└─────────────────────────────────────────────────────────────┘
```

**每层回答的核心问题：**
- **Layer 1**：有什么可用素材？
- **Layer 2**：这次旅行怎么排？（行程引擎）
- **Layer 3**：怎么把结果变成一份有价值感、好阅读、可导出的攻略？
- **Layer 4**：结果对不对？出了问题怎么办？怎么持续变好？

---

## Layer 1: 数据与知识层

> 回答：有什么可用素材

### 模块清单

| 模块 | 文件 | 职责 | 状态 |
|------|------|------|------|
| **城市圈真相源** | `app/db/models/city_circles.py` | CityCircle 表定义 | ✅ 已建 |
| **活动簇** | `app/db/models/city_circles.py` | ActivityCluster 表定义 | ✅ 已建 |
| **角色映射** | `app/db/models/city_circles.py` | CircleEntityRole 表定义 | ✅ 已建 |
| **酒店策略预设** | `app/db/models/city_circles.py` | HotelStrategyPreset 表定义 | ✅ 已建 |
| **实体库** | `app/db/models/catalog.py` | EntityBase / EntityTag / EntityMedia | ✅ 已有 |
| **实体评分** | `app/db/models/derived.py` | EntityScore（base_quality 层） | ✅ 已有 |
| **软规则评分** | `app/db/models/soft_rules.py` | EntitySoftScore（12 维度） | ✅ 已有 |
| **运营事实** | `app/db/models/soft_rules.py` | EntityOperatingFact | ✅ 已有 |
| **营业快照** | `app/db/models/snapshots.py` | PoiOpeningSnapshot / HotelOfferSnapshot | ✅ 已有 |
| **关西圈种子数据** | `scripts/seed_kansai_circle.py` | 关西圈 circle + cluster + hotel preset | ✅ 已建 |
| **实体别名库** | `app/db/models/catalog.py` | EntityAlias — 多语别名+pg_trgm 匹配基础 | ❌ 未做(P0) |
| **时态画像** | `app/db/models/temporal.py` | EntityTemporalProfile — 季节/时段变化属性 | ❌ 未做(P0) |
| **字段溯源** | `app/db/models/catalog.py` | EntityFieldProvenance — 来源/置信度/审核 | ❌ 未做(P0) |
| **6 圈种子数据** | `scripts/seed_all_circles.py` | 东京/北海道/北九州/冲绳/中部北陆 | ❌ 未做(P0) |
| **实体→活动簇映射** | `scripts/auto_map_entities_to_clusters.py` | 可反复跑的 4 层匹配管线 | ❌ 未做(P0) |
| **实体静态字段补充** | entity_base migration | lat/lng/station/corridor_tags/duration/price_band | ❌ 未做(P0) |
| **走廊/子区域标准化** | corridors 标准化逻辑 | area_name → corridor_id 标准化 | ❌ 未做(P1) |
| **映射审核队列** | entity_mapping_reviews 表 | 取代 CSV 的长期审核工作流 | ❌ 未做(P1) |
| **采集管线** | data pipeline | Google Maps / Tabelog / 官方爬取 | ⚠️ 部分已有 |
| **事实新鲜度管理** | refresh SLA + stale policy | 定期检查实体数据过期 | ❌ 未做(P1) |
| **媒体资产层** | page_hero_registry | hero 图/gallery/地图/分享图 | ❌ 未做(P1) |

---

## Layer 2: 决策与编排层

> 回答：这次旅行怎么排（行程引擎）

### 核心链路

```
normalize_profile
  → eligibility_gate（资格过滤，pass/fail）
  → precheck_gate（前置可规避风险）
  → select_circle（城市圈选择，8 维评分）
  → rank_major（主要活动排序，base_quality × context_fit）
  → build_hotel（酒店基点策略）
  → build_skeleton（日骨架，11 字段约束）
  → fill_secondary（次要活动填充）
  → fill_meals（餐厅填充）
  → itinerary_fit_scoring（日内适配重排）
```

### 模块清单

| 模块 | 文件 | 职责 | 状态 |
|------|------|------|------|
| **画像标准化** | `app/workers/jobs/normalize_profile.py`? | DetailForm → TripProfile 标准化 | ⚠️ 已有基础版，缺推导逻辑 |
| **TripProfile 补字段** | `app/db/models/business.py` | arrival_shape / daytrip_tolerance 等 12 字段 | ✅ 已补 |
| **资格过滤** | `app/domains/planning/eligibility_gate.py` | EG-001~007 pass/fail 门控 | ✅ 已建 |
| **前置风险检查** | `app/domains/planning/precheck_gate.py` | PC-001~005 消费快照+运营事实 | ✅ 已建 |
| **城市圈选择** | `app/domains/planning/city_circle_selector.py` | 8 维评分选圈 | ✅ 已建 |
| **主要活动排序** | `app/domains/planning/major_activity_ranker.py` | score = base×0.55 + context×0.45 | ✅ 已建 |
| **酒店基点策略** | `app/domains/planning/hotel_base_builder.py` | 选住法 + last_night_safe 检查 | ✅ 已建 |
| **日骨架生成** | `app/domains/planning/route_skeleton_builder.py` | DayFrame 11 字段 | ✅ 已建 |
| **次要活动填充** | `app/domains/planning/secondary_filler.py` | 受 capacity + transfer 约束 | ✅ 已建 |
| **餐厅填充** | `app/domains/planning/meal_flex_filler.py` | 受 meal_windows 约束 | ✅ 已建 |
| **分阶段降级** | `app/domains/planning/fallback_router.py` | F-01~04 精确降级 | ✅ 已建 |
| **旧装配引擎** | `app/domains/planning/assembler.py` | 模板驱动装配（保留为 fallback） | ✅ 已有 |
| **评分规则（base_quality）** | `app/domains/ranking/rules.py` | POI 5 维（已拆出 theme_match/area_eff） | ✅ 已改 |
| **评分引擎** | `app/domains/ranking/scorer.py` | 计算 system_score | ✅ 已改 |
| **日内适配评分** | `app/domains/planning/itinerary_fit_scorer.py` | Layer 4 评分：corridor/sequence/time/backtrack/rhythm | ✅ 已建 |
| **主流程集成** | `app/workers/jobs/generate_trip.py` | 城市圈优先 + fallback 旧模板 | ✅ 已改 |
| **阶段决策落库** | `generation_decisions` 表 | circle/major/hotel/skeleton 决策快照 | ❌ 未做 |
| **normalize 推导增强** | normalize job | arrival_day_shape / celebration_flags / mobility 等推导 | ❌ 未做 |

---

## Layer 3: 报告与渲染层

> 回答：怎么把结果变成一份有价值感、好阅读、可导出的攻略

### 模块清单

| 模块 | 文件 | 职责 | 状态 |
|------|------|------|------|
| **报告 Schema** | `app/domains/planning/report_schema.py` | ReportPayloadV2 Pydantic 模型 | ✅ 已建 |
| **报告生成 v1** | `app/domains/planning/report_generator.py` | 旧链路（保留） | ✅ 已有 |
| **报告生成 v2** | `app/domains/planning/report_generator.py` | 城市圈链路入口 generate_report_v2 | ✅ 已建 |
| **AI prompt（v2）** | `report_generator.py` 内 | _P_OVERVIEW / _P_DAILY 约束型 prompt | ✅ 已改 |
| **条件页触发** | `report_generator.py` 内 | _trigger_conditional 规则引擎 | ✅ 已改 |
| **文案润色** | `app/domains/planning/copywriter.py` | 实体一句话描述 + tips | ✅ 已有 |
| **片段复用** | `app/domains/planning/fragment_pipeline.py` | route/decision/experience 片段 | ✅ 已有 |
| **渲染引擎 v1** | `app/domains/rendering/renderer.py` | Jinja2 HTML 渲染 | ✅ 已有 |
| **渲染引擎 v2** | `app/domains/rendering/renderer.py` | v2 分支 | ✅ 已建 |
| **模板 v1** | `templates/itinerary_default.html` | 旧模板（保留） | ✅ 已有 |
| **模板 v2** | `templates/itinerary_v2.html` | 新模板（design_brief/must_keep/reasoning） | ✅ 已建 |
| **PDF 导出** | `scripts/export-playwright.ts` | Playwright 截图导出 | ✅ 已有 |
| **页型系统** | 待建 | page_plan / page_type / page_blueprint | ❌ 未做 |
| **page_plan 落库** | 待建 | 页序 + 页型 + 对象占页规则 | ❌ 未做 |
| **page_type 模板** | 待建 | 酒店页/餐厅页/拍摄页/预约页/风险页等 | ❌ 未做 |
| **page_view_model** | 待建 | 每页的渲染数据模型 | ❌ 未做 |
| **chapter 系统** | 待建 | chapter_id / goal / mood / covered_days | ❌ 未做 |
| **payload 扩充** | report_schema.py | preference_fulfillment / skipped_options / emotional_goal | ❌ 未做 |
| **决策解释文案** | 待建 | why_selected / why_here / what_to_expect 模板 | ❌ 未做 |
| **Satori 社交卡片** | `web/` 内 | OG image / share image | ⚠️ 已有基础版 |
| **前端 Next.js** | `web/` | 攻略阅读页 | ✅ 已有 |

---

## Layer 4: 评测、校验与运营层

> 回答：结果对不对？出了问题怎么办？怎么持续变好？

### 模块清单

| 模块 | 文件 | 职责 | 状态 |
|------|------|------|------|
| **结构校验 QTY** | `app/core/quality_gate.py` | QTY-01~11 现有检查 | ✅ 已有 |
| **结构校验 STR** | `app/core/quality_gate.py` | STR-01~05 v2 payload 结构检查 | ✅ 已建 |
| **多模型评审** | `app/workers/jobs/review_pipeline.py`? | 4 agent + judge | ✅ 已有 |
| **fallback 兼容** | `app/domains/planning/fallback_router.py` | 4 级精确降级 | ✅ 已建 |
| **版本兼容** | report_content.schema_version | v1/v2 双路径 renderer | ✅ 已建 |
| **实时风险监控** | `app/domains/planning/live_risk_monitor.py` | T-72h/T-24h 检查 + fallback 触发 | ❌ 未做 |
| **trace 输出** | generation_step_runs 表 | 每阶段 (result, trace) 写入 | ❌ 未做 |
| **离线评测 cases** | `evals/cases/` | 关西/东京等回归 case | ❌ 未做 |
| **grader 评测** | 待建 | 自动评分 + 人工评分对比 | ❌ 未做 |
| **运营修正规则** | 待建 | 人工覆盖 cluster_locked / priority / risk_badge 等 | ❌ 未做 |
| **反馈闭环** | 待建 | 用户反馈 → 评分调整 → 片段回库 | ❌ 未做 |
| **版本号管理** | 待建 | profile_version / circle_version / scorer_version 等 | ❌ 未做 |

---

## 未完成清单汇总

### P0 — 缺了就跑不通

| # | 层 | 任务 | 阻塞什么 |
|---|---|---|---|
| 1 | L1 | 6 圈种子数据入库 | 东京等城市圈链路无法运行 |
| 2 | L1 | 实体→活动簇自动映射 | major_activity_ranker 拿不到锚点实体分数 |
| 3 | L1 | entity_base 补字段 | 骨架容量/时间窗/价格过滤缺数据 |
| 4 | L2 | normalize 推导增强 | arrival_day_shape / celebration 等信号丢失 |
| 5 | L4 | trace 输出到 generation_step_runs | 排查问题无据可查 |

### P1 — 缺了效果打折

| # | 层 | 任务 | 影响什么 |
|---|---|---|---|
| 6 | L1 | 走廊/子区域标准化 | corridor_alignment 评分不准 |
| 7 | L1 | 媒体资产层 | 报告缺 hero 图，定制感弱 |
| 8 | L2 | 阶段决策落库 | 无法复用、回溯、部分重跑 |
| 9 | L3 | 页型系统 (page_plan + page_type) | 报告仍然是长 section 流 |
| 10 | L3 | payload 扩充 (fulfillment/skipped/emotional) | 定制感和决策解释弱 |
| 11 | L3 | 决策解释文案模板 | why_selected 等空洞 |
| 12 | L3 | chapter 系统 | 无法按章节组织多天 |
| 13 | L4 | live_risk_monitor | 天气/海况等当天风险无应对 |
| 14 | L4 | 离线评测 cases | 无法量化改进效果 |

### P2 — 缺了不能形成飞轮

| # | 层 | 任务 | 影响什么 |
|---|---|---|---|
| 15 | L1 | 事实新鲜度管理 | 过期数据污染评分 |
| 16 | L3 | page_blueprint 模板库 | 页序不能按 trip shape 自动适配 |
| 17 | L4 | grader 评测体系 | 无法自动化质量检测 |
| 18 | L4 | 运营修正规则 | 人工无法精细干预 |
| 19 | L4 | 反馈闭环 | 用户反馈不能回流 |
| 20 | L4 | 版本号管理 | 无法精确回溯哪个版本出了问题 |

---

## 技术栈

| 层 | 后端 | 前端 | 存储 |
|---|---|---|---|
| L1 数据与知识 | Python / SQLAlchemy / Alembic | — | PostgreSQL (JSONB) |
| L2 决策与编排 | Python async / 纯规则+评分 | — | PostgreSQL |
| L3 报告与渲染 | Jinja2 / GPT-4o | Next.js / Tailwind / shadcn/ui | PostgreSQL + 对象存储 |
| L4 评测与运营 | Python / arq workers | — | PostgreSQL + Redis (cache) |

**部署：** Vercel (前端) + 自有后端 + PostgreSQL + Redis

---

## 当前版本

```
schema_version: v2
circle_registry_version: v1 (关西已有，其余 5 圈待灌)
scorer_version: v2 (已拆 theme_match/area_efficiency)
planner_version: circle-v1
renderer_version: v2
```
