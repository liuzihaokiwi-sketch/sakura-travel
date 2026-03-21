# Runtime Entrypoints

> 最后更新：2026-03-21 · 所有启动命令和入口点的完整清单。

## 先决条件

| 依赖 | 命令 | 说明 |
|---|---|---|
| Docker（PG + Redis） | `docker compose up -d postgres redis` | PostgreSQL 15 (pgvector) + Redis 7 |
| Python venv | `.venv\Scripts\activate`（Windows）/ `source .venv/bin/activate`（Mac/Linux） | Python 3.12+ |
| Node.js | `cd web && npm ci` | Node 20+，每次换平台需重装 |
| 环境变量 | 复制 `.env.example` → `.env` 并填写 | 必填项见 `config_inventory.md` |

## FastAPI 应用

| 入口 | 命令 | 说明 |
|---|---|---|
| `app/main.py` | `uvicorn app.main:app --reload --port 8000` | FastAPI Web 服务器 |

**启动时 lifespan 自动执行**：
1. 开发模式下自动建表（`Base.metadata.create_all`）
2. 加载区域种子数据（`geography/region_router.load_seed_data()`）
3. 初始化 Redis 连接池

## Worker

| 入口 | 命令 | 说明 |
|---|---|---|
| `app/workers/__main__.py` | `python -m app.workers` | arq 异步任务 Worker |

**注册的 Job 函数**：
- `normalize_trip_profile`
- `generate_itinerary_plan`
- `generate_trip`
- `render_export`
- `run_guardrails`
- `score_entities`
- `scan_flight_prices`

## 前端

| 入口 | 命令 | 说明 |
|---|---|---|
| `web/` | `cd web && npm run dev` | Next.js 开发服务器（端口 3000） |
| `web/` | `cd web && npm run build && npm run start` | 生产构建 |

**⚠️ Windows 注意**：如果 `npm run dev` 提示 `'next' 不是内部或外部命令`，使用：
```bash
cd web && node node_modules\next\dist\bin\next dev
```

**⚠️ 首次在新平台运行**：如果 `node_modules` 是其他平台安装的，先运行：
```bash
cd web && npm ci
```

## 脚本

### 日常运维

| 脚本 | 命令 | 说明 |
|---|---|---|
| `scripts/maintain.py` | `python scripts/maintain.py deploy` | 一键部署（commit → push → update → build → restart） |
| `scripts/maintain.py` | `python scripts/maintain.py status` | 查看系统状态 |
| `scripts/smart_commit.py` | `python scripts/smart_commit.py` | 自动语义化 commit |

### 数据管理

| 脚本 | 命令 | 说明 |
|---|---|---|
| `scripts/fix_and_init.py` | `python scripts/fix_and_init.py` | 数据库修复与初始化（评分归一化/标签/模板） |
| `scripts/sync_remote_to_local.py` | `python scripts/sync_remote_to_local.py` | Supabase → 本地 PG 数据同步 |
| `scripts/generate_tags.py` | `python scripts/generate_tags.py --city tokyo` | GPT 标签生成 |
| `scripts/batch_translate.py` | `python scripts/batch_translate.py` | DeepL 批量翻译 |
| `scripts/mark_data_tier.py` | `python scripts/mark_data_tier.py` | 数据分层标记 |
| `scripts/ingest_all.py` | `python scripts/ingest_all.py` | 批量数据入库 |
| `scripts/load_route_templates.py` | `python scripts/load_route_templates.py` | 路线模板入库 |
| `scripts/seed_product_skus.py` | `python scripts/seed_product_skus.py` | SKU 种子数据 |
| `scripts/init_db.py` | `python scripts/init_db.py` | 数据库初始化 |

### 爬虫

| 脚本 | 命令 | 说明 |
|---|---|---|
| `scripts/crawl_orchestrator.py` | `python scripts/crawl_orchestrator.py` | **全日本并行爬取调度器**（独立运行，断连后继续） |
| `scripts/crawl.py` | `python scripts/crawl.py` | 爬虫简易入口 |
| `scripts/hotel_crawl.py` | `python scripts/hotel_crawl.py` | 酒店爬取 |
| `scripts/tabelog_crawl.py` | `python scripts/tabelog_crawl.py` | Tabelog 餐厅爬取 |
| `scripts/event_crawl.py` | `python scripts/event_crawl.py` | 活动爬取 |
| `scripts/jnto_crawl.py` | `python scripts/jnto_crawl.py` | JNTO 景点爬取 |
| `scripts/xhs_crawl.py` | `python scripts/xhs_crawl.py` | 小红书攻略爬取 |
| `scripts/flight_crawl.py` | `python scripts/flight_crawl.py` | 机票爬取 |

### 樱花数据管线

| 命令 | 说明 |
|---|---|
| `python -m scripts.crawlers.sakura_pipeline.cli fetch` | 抓取所有樱花数据源 |
| `python -m scripts.crawlers.sakura_pipeline.cli fuse` | 多源数据融合 |
| `python -m scripts.crawlers.sakura_pipeline.cli all` | 全流程（fetch + fuse + score） |

### 测试与验证

| 脚本 | 命令 | 说明 |
|---|---|---|
| `scripts/verify_api.py` | `python scripts/verify_api.py` | API 端点验证 |
| `scripts/test_db_conn.py` | `python scripts/test_db_conn.py` | 数据库连接测试 |
| `scripts/test_api_keys.py` | `python scripts/test_api_keys.py` | API Key 有效性测试 |
| `scripts/generate_one_day.py` | `python scripts/generate_one_day.py` | 单日行程生成测试 |

### 前端脚本

| 脚本 | 命令 | 说明 |
|---|---|---|
| `web/scripts/export-playwright.ts` | `cd web && npm run export:screenshot` | Playwright 截图导出 |
| `web/scripts/export-satori.ts` | `cd web && npm run export:cards` | Satori 卡片导出 |
| `web/scripts/export-social-images.ts` | `cd web && npm run export:social` | 社交媒体图片导出 |
| `web/scripts/e2e-funnel-verify.ts` | `cd web && npm run verify:funnel` | E2E 漏斗验证 |
| `web/scripts/mobile-responsive-verify.ts` | `cd web && npm run verify:mobile` | 移动端响应式验证 |

## Docker

| 命令 | 说明 |
|---|---|
| `docker compose up -d` | 启动所有服务 |
| `docker compose up -d postgres redis` | 仅启动基础设施 |
| `docker compose logs -f api` | 查看 API 日志 |
| `docker compose logs -f worker` | 查看 Worker 日志 |

## 完整启动流程（从零到运行）

```bash
# 1. 启动基础设施
docker compose up -d postgres redis

# 2. 激活 Python 环境
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# 3. 初始化数据库（仅首次）
python scripts/init_db.py
python scripts/fix_and_init.py

# 4. 启动后端
uvicorn app.main:app --reload --port 8000

# 5. 启动前端（新终端）
cd web && npm run dev

# 6. 启动 Worker（新终端）
python -m app.workers

# 7. 验证
python scripts/verify_api.py
# 浏览器打开 http://localhost:3000
```