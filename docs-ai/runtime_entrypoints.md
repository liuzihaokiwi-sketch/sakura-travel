# Runtime Entrypoints

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

## 脚本

| 脚本 | 命令 | 说明 |
|---|---|---|
| `scripts/crawl.py` | `python scripts/crawl.py` | 爬虫调度 |
| `scripts/generate_tags.py` | `python scripts/generate_tags.py --city tokyo` | GPT 标签生成 |
| `scripts/mark_data_tier.py` | `python scripts/mark_data_tier.py` | 数据分层标记 |
| `scripts/ingest_all.py` | `python scripts/ingest_all.py` | 批量数据入库 |
| `scripts/load_route_templates.py` | `python scripts/load_route_templates.py` | 路线模板入库 |
| `scripts/seed_product_skus.py` | `python scripts/seed_product_skus.py` | SKU 种子数据 |
| `scripts/verify_api.py` | `python scripts/verify_api.py` | API 端点验证 |
| `web/scripts/export-playwright.ts` | `cd web && npm run export:screenshot` | Playwright 截图导出 |
| `web/scripts/export-satori.ts` | `cd web && npm run export:cards` | Satori 卡片导出 |

## Docker

| 命令 | 说明 |
|---|---|
| `docker compose up -d` | 启动所有服务 |
| `docker compose up -d postgres redis` | 仅启动基础设施 |
| `docker compose logs -f api` | 查看 API 日志 |
| `docker compose logs -f worker` | 查看 Worker 日志 |