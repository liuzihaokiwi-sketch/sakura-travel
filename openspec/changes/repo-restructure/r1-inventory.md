# R1. 全项目体检报告

> 扫描时间：2026-03-21
> 项目根：/Users/yanghailin/projects/travel-ai

---

## 一、项目顶层结构

| 目录 | 用途 | 状态 |
|---|---|---|
| `app/` | Python 后端（FastAPI） | ✅ 核心，活跃 |
| `web/` | Next.js 前端 | ✅ 核心，活跃 |
| `scripts/` | 爬虫+数据脚本 | ✅ 活跃 |
| `data/` | 原始数据+模板 | ⚠️ 混杂，需整理 |
| `templates/` | Jinja2 杂志模板 | ✅ 活跃 |
| `tests/` | 单元测试 | ✅ 保留 |
| `docs/` | 文档（混杂） | ⚠️ 需要重组 |
| `openspec/` | OpenSpec 规格文档 | ✅ 活跃 |
| `exports/` | 生成的 HTML/PDF 产物 | 🔴 构建产物，不入库 |
| `logs/` | 日志 | 🔴 不入库 |
| `sakura-rush-2026/` | 早期樱花攻略 HTML | ⚠️ 可能废弃 |

---

## 二、文件分类盘点

### 2.1 后端代码 `app/`

| 路径 | 类型 | 作用 | 动作 |
|---|---|---|---|
| `app/main.py` | 入口 | FastAPI 应用入口 | **keep** |
| `app/core/config.py` | 配置 | 环境变量加载（含 API key 引用） | **keep** ⚠️安全检查 |
| `app/core/queue.py` | 核心 | 异步任务队列 | **keep** |
| `app/core/snapshots.py` | 核心 | 数据快照 | **keep** |
| `app/db/session.py` | 数据库 | SQLAlchemy 会话 | **keep** |
| `app/db/models/__init__.py` | 数据库 | 数据模型 | **keep** |
| `app/db/migrations/` | 数据库 | Alembic 迁移 | **keep** |
| `app/api/chat.py` | API | 聊天接口 | **keep** |
| `app/api/pois.py` | API | POI 接口 | **keep** |
| `app/api/products.py` | API | 产品SKU接口 | **keep** |
| `app/api/quiz.py` | API | 问卷接口 | **keep** |
| `app/api/trips.py` | API | 行程接口 | **keep** |
| `app/api/trips_generate.py` | API | 行程生成 | **keep** |
| `app/api/ops/editorial.py` | API | 运营编辑接口 | **keep** |
| `app/api/ops/entities.py` | API | 实体管理接口 | **keep** |
| `app/api/ops/ranked.py` | API | 排名接口 | **keep** |
| `app/domains/catalog/` | 领域 | 实体目录（爬虫同步/打标/AI生成） | **keep** |
| `app/domains/flights/` | 领域 | 机票（Amadeus/通知） | **keep** |
| `app/domains/geography/` | 领域 | 地理路由 | **keep** |
| `app/domains/intake/` | 领域 | 用户需求解析 | **keep** |
| `app/domains/live_inventory/` | 领域 | 实时库存 | **keep** |
| `app/domains/planning/` | 领域 | 行程规划核心 | **keep** |
| `app/domains/ranking/` | 领域 | 评分排名 | **keep** |
| `app/domains/rendering/` | 领域 | 方案渲染 | **keep** |
| `app/domains/trip_core/` | 领域 | 行程核心模型 | **keep** |
| `app/workers/` | 后台任务 | Worker 进程 | **keep** |

### 2.2 前端代码 `web/`

| 路径 | 类型 | 作用 | 动作 |
|---|---|---|---|
| `web/app/page.tsx` | 页面 | 首页 | **keep** |
| `web/app/quiz/` | 页面 | 轻问卷 | **keep** |
| `web/app/submitted/` | 页面 | 提交成功页 | **keep**（新页面） |
| `web/app/pricing/` | 页面 | 价格页 | **keep** |
| `web/app/plan/[id]/` | 页面 | 交付页 | **keep** |
| `web/app/rush/` | 页面 | 樱花追踪页 | ⚠️ **archive** — 早期功能 |
| `web/app/city/` | 页面 | 城市页 | ⚠️ 需确认是否在用 |
| `web/app/custom/` | 页面 | 定制页 | ⚠️ 需确认是否在用 |
| `web/app/generating/[id]/` | 页面 | 生成等待页 | 🔴 **archive** — 流程已改为微信交付 |
| `web/app/preview/[id]/` | 页面 | 免费预览页 | 🔴 **archive** — 流程已改为微信交付 |
| `web/app/checkout/[id]/` | 页面 | 付款页 | 🔴 **archive** — 流程已改为微信转账 |
| `web/app/questionnaire/[id]/` | 页面 | 正式问卷 | 🔴 **archive** — 流程已改为微信追问 |
| `web/components/rush/` | 组件 | 樱花追踪组件 | ⚠️ **archive** |
| `web/components/social/` | 组件 | 小红书封面组件 | ⚠️ 需确认 |
| `web/components/landing/` | 组件 | 首页组件 | **keep** |
| `web/components/custom/` | 组件 | 定制页组件 | ⚠️ 需确认 |
| `web/components/shared/` | 组件 | 共享组件 | **keep** |
| `web/components/ui/` | 组件 | UI基础组件 | **keep** |
| `web/lib/` | 库 | 工具函数/常量/动画 | **keep** |
| `web/scripts/` | 脚本 | 导出脚本（Playwright/Satori） | **keep** |
| `web/.next/` | 构建产物 | Next.js 编译缓存 | 🔴 **不入库**，加 .gitignore |
| `web/output/` | 构建产物 | 导出产物 | 🔴 **不入库** |
| `web/public/fonts/NotoSansSC-Regular.ttf` | 静态资源 | 字体（17MB） | ⚠️ 大文件，考虑CDN或Git LFS |

### 2.3 数据文件 `data/`

| 路径 | 类型 | 作用 | 动作 |
|---|---|---|---|
| `data/route_templates/*.json` | 数据 | 路线模板（8个） | **keep** — 核心业务数据 |
| `data/events_raw/*.json` | 数据 | 活动爬虫原始数据 | **keep** 但不入库（太大） |
| `data/experiences_raw/*.json` | 数据 | 体验爬虫数据 | **keep** 但不入库 |
| `data/flights_raw/*.json` | 数据 | 机票爬虫数据 | **keep** 但不入库 |
| `data/hotels_raw/*.json` | 数据 | 酒店爬虫数据 | **keep** 但不入库 |
| `data/tabelog_raw/*.json` | 数据 | 餐厅爬虫数据 | **keep** 但不入库 |
| `data/sakura/*.html` | 静态页面 | 早期樱花展示页 | 🔴 **archive** — 已被web/替代 |
| `data/sakura/*.json` | 数据 | 樱花数据 | **keep** |
| `data/sakura/screenshots/` | 截图 | 调试截图 | 🔴 **delete_candidate** |
| `data/gf_*.png` | 截图 | Google Flights 调试截图 | 🔴 **delete_candidate** |
| `data/flights_raw/gf_error.png` | 截图 | 错误截图 | 🔴 **delete_candidate** |
| `data/*.json`（根级） | 配置数据 | 评分/路由/权重配置 | **keep** |
| `data/*.xlsx` | 数据 | 区域种子数据 | **keep** |
| `data/raw/official/` | 数据 | 官方数据 | **keep** |

### 2.4 文档 `docs/`

| 路径 | 类型 | 作用 | 动作 |
|---|---|---|---|
| `docs/日本旅行AI后端完整方案_第一性原理版.md` | 文档 | 后端架构方案（外部AI产出） | **keep** → 移入 docs-human |
| `docs/PLATFORM_OVERVIEW.md` | 文档 | 平台概览 | **keep** → 移入 docs-human |
| `docs/FEATURE_GAP_ANALYSIS.md` | 文档 | 功能差距分析 | **keep** → 移入 docs-human |
| `docs/AI_WORK_GUIDE.md` | 文档 | AI工作指南 | **keep** → 移入 docs-ai |
| `docs/DELIVERY_PAGE_DESIGN.md` | 文档 | 交付页设计 | **refactor** → 已被openspec替代 |
| `docs/PRICING_AND_FEATURES.md` | 文档 | 定价功能 | **refactor** → 已被openspec替代 |
| `docs/PRICING.md` | 文档 | 定价 | **refactor** → 与上面重复 |
| `docs/PRODUCT_TIERS_V2.md` | 文档 | 产品层级 | **refactor** → 已被openspec替代 |
| `docs/PROJECT_PLAN.md` | 文档 | 项目计划 | **archive** → 旧版 |
| `docs/SAKURA_DISPLAY_PLAN.md` | 文档 | 樱花展示计划 | **archive** → 旧版 |
| `docs/SAKURA_SYSTEM_PLAN.md` | 文档 | 樱花系统计划 | **archive** → 旧版 |
| `docs/TASK_SPLIT_V4.md` | 文档 | 任务拆分 | **archive** → 旧版 |
| `docs/A19-A27_DELIVERY_PREVIEW_QUESTIONNAIRE.md` | 文档 | 交付/预览/问卷设计 | **refactor** → 已被openspec替代 |
| `docs/*.html` | 静态 | 早期HTML展示页 | 🔴 **archive** |
| `docs/screenshots/*.png` | 截图 | 系统截图 | **keep** → 移入 docs-human |
| `docs/weathernews_all_spots.json` | 数据 | 数据文件误放在docs | 🔴 **移到data/** |

### 2.5 脚本 `scripts/`

| 路径 | 类型 | 动作 |
|---|---|---|
| `scripts/crawl.py` | 入口 | **keep** |
| `scripts/crawlers/*.py` | 爬虫 | **keep** |
| `scripts/crawlers/AI_TASK_SPLIT*.md` | 文档 | **archive** — 历史任务拆分 |
| `scripts/crawlers/CRAWLERS_GUIDE.md` | 文档 | **keep** → 移入 docs-human |
| `scripts/*_crawl.py` | 爬虫入口 | **keep** |
| `scripts/generate_tags.py` | 工具 | **keep** |
| `scripts/ingest_all.py` | 工具 | **keep** |
| `scripts/load_route_templates.py` | 工具 | **keep** |
| `scripts/mark_data_tier.py` | 工具 | **keep** |
| `scripts/prebuild_route_matrix.py` | 工具 | **keep** |
| `scripts/scan_flights.py` | 工具 | **keep** |
| `scripts/seed_product_skus.py` | 工具 | **keep** |
| `scripts/verify_api.py` | 工具 | **keep** |

### 2.6 其他

| 路径 | 类型 | 动作 |
|---|---|---|
| `sakura-rush-2026/*.html` | 静态 | 🔴 **archive** — 早期樱花攻略 HTML，已被 web/ 和 templates/ 替代 |
| `exports/*.html` `exports/*.pdf` | 构建产物 | 🔴 **不入库** |
| `logs/` | 日志 | 🔴 **不入库** |
| `docker-compose.yml` | 配置 | **keep** |
| `Dockerfile` | 配置 | **keep** |
| `pyproject.toml` | 配置 | **keep** |
| `alembic.ini` | 配置 | **keep** |
| `README.md` | 文档 | **refactor** — 需要重写 |
| `.env` | 配置 | 🔴 **绝不入库** — 含真实密钥 |
| `.env.example` | 模板 | **keep** |
| `.gitignore` | 配置 | **refactor** — 需要补全 |
| `openspec/` | Spec文档 | **keep** — 项目核心 |

---

## 三、安全风险标记

| 风险 | 文件 | 严重度 | 处理 |
|---|---|---|---|
| 🔴 真实密钥 | `.env` | **P0** | 绝不入库，.gitignore 必须覆盖 |
| 🔴 API key 引用 | `app/core/config.py` | 中 | 确认只读环境变量，不硬编码 |
| 🔴 API key 引用 | `app/domains/flights/amadeus_client.py` | 中 | 同上 |
| 🔴 API key 引用 | `app/domains/catalog/google_places.py` | 中 | 同上 |
| 🔴 API key 引用 | `app/domains/catalog/serp_sync.py` | 中 | 同上 |
| 🔴 API key 引用 | `scripts/crawlers/google_flights.py` | 中 | 同上 |
| ⚠️ 大文件 | `web/public/fonts/NotoSansSC-Regular.ttf`（17MB） | 中 | 考虑 CDN 或 Git LFS |
| ⚠️ 构建产物 | `web/.next/`（~100MB+） | 高 | .gitignore 必须覆盖 |
| ⚠️ 构建产物 | `exports/` | 中 | .gitignore 必须覆盖 |

---

## 四、统计摘要

| 分类 | 数量 | 动作 |
|---|---|---|
| **keep** | ~80 个文件 | 保留不动 |
| **refactor** | ~10 个文件 | 需要重写或合并 |
| **archive** | ~25 个文件 | 移入 archive/ |
| **delete_candidate** | ~15 个文件 | 调试截图/临时文件 |
| **不入库** | ~5 个目录 | .gitignore 覆盖 |