# Do Not Break — 高风险文件清单

> 修改以下文件前必须格外小心，理解上下游依赖后再动手。

## 🔴 Critical（修改可能导致系统不可用）

| 文件 | 风险原因 | 影响范围 |
|---|---|---|
| `app/main.py` | FastAPI 入口，所有路由注册在此 | 整个 API 不可用 |
| `app/core/config.py` | 全局配置，所有模块引用 `settings` | 全系统 |
| `app/db/session.py` | 数据库会话工厂，所有 DB 操作依赖 | 全系统 |
| `app/db/models/catalog.py` | 8 张核心表的 ORM，CTI 模式基础 | catalog, ranking, planning |
| `app/db/models/business.py` | 订单/用户/行程请求 ORM | api层, workers |
| `app/db/models/derived.py` | 行程方案/评分/导出 ORM（13 张表） | planning, rendering, export |
| `app/workers/__main__.py` | Worker 入口 + normalize job | 异步任务全部失效 |
| `docker-compose.yml` | 基础设施编排 | 开发/部署环境 |

## 🟡 High（修改可能导致核心流程异常）

| 文件 | 风险原因 | 影响范围 |
|---|---|---|
| `app/domains/planning/assembler.py` | 行程装配核心逻辑 | 行程生成失败 |
| `app/domains/planning/copywriter.py` | AI 文案生成 + Redis 缓存 | 文案质量/生成速度 |
| `app/domains/ranking/scorer.py` | 评分算法核心 | 推荐质量 |
| `app/domains/catalog/tagger.py` | GPT 标签生成 | 标签数据 |
| `app/domains/catalog/pipeline.py` | 数据采集管线入口 | 数据入库 |
| `app/domains/geography/region_router.py` | 区域推荐 + 种子数据加载 | 路线选择 |
| `app/domains/rendering/renderer.py` | HTML/PDF 渲染 | 交付物生成 |
| `app/api/quiz.py` | 问卷提交（含企业微信通知） | 用户转化链路 |
| `app/api/orders.py` | 订单状态机 | 订单流程 |
| `web/app/page.tsx` | 首页（营销漏斗入口） | 用户转化率 |
| `web/app/plan/[id]/page.tsx` | 行程交付页（核心交付物） | 用户体验 |

## 🟢 Moderate（修改前确认测试覆盖）

| 文件 | 风险原因 |
|---|---|
| `app/domains/catalog/upsert.py` | 实体写入，多模块调用 |
| `app/domains/ranking/affinity.py` | 亲和度查询，评分依赖 |
| `app/domains/ranking/theme_weights.py` | 问卷答案 → 权重映射 |
| `app/workers/jobs/*.py` | 各 Worker job |
| `data/route_templates/*.json` | 路线模板数据，格式变化影响装配器 |
| `data/entity_affinity_seed_v1.json` | 种子标签数据 |
| `data/questionnaire_to_theme_weights_rules_v1.json` | 问卷权重规则 |

## ⚠️ 数据文件（不可随意删改）

| 文件 | 说明 |
|---|---|
| `data/route_templates/*.json` | 8 条路线模板，装配器直接读取 |
| `data/entity_affinity_seed_v1.json` | 人工标注的种子亲和度 |
| `data/japan_region_usertype_matrix_v1.json` | 区域-用户类型匹配矩阵 |
| `data/route_region_binding_v1.json` | 路线-区域绑定 |
| `data/questionnaire_to_theme_weights_rules_v1.json` | 问卷答案→主题权重规则 |
| `data/p0_route_skeleton_templates_v1.json` | 路线骨架模板 |
| `data/context_score_design.json` | 上下文评分设计 |
| `alembic.ini` | 迁移配置 |
| `.env.example` | 环境变量模板（新人参考） |