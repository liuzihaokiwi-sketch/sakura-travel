# Dependency Map

## 核心依赖链

```
app/main.py
  ├── app/api/chat.py          → app/domains/intake/intent_parser.py
  ├── app/api/quiz.py          → app/db/models/business.py, app/core/queue.py
  ├── app/api/orders.py        → app/db/models/business.py
  ├── app/api/trips.py         → app/db/models/business.py, app/db/models/derived.py
  ├── app/api/trips_generate.py → app/domains/planning/*, app/domains/rendering/*
  ├── app/api/pois.py          → app/db/models/catalog.py
  ├── app/api/products.py      → app/db/models/business.py
  └── app/api/ops/*            → app/db/models/catalog.py, app/domains/ranking/*
```

## Worker 依赖

```
app/workers/__main__.py (normalize_trip_profile)
  → app/db/models/business.py

app/workers/jobs/generate_plan.py
  → app/domains/geography/region_router.py
  → app/domains/geography/route_selector.py
  → app/db/models/derived.py

app/workers/jobs/generate_trip.py
  → app/domains/planning/assembler.py
    → app/domains/ranking/queries.py
    → app/domains/planning/copywriter.py
    → app/domains/planning/route_matrix.py

app/workers/jobs/render_export.py
  → app/domains/rendering/renderer.py
    → templates/magazine/*.html.j2

app/workers/jobs/run_guardrails.py
  → app/db/models/derived.py

app/workers/jobs/score_entities.py
  → app/domains/ranking/scorer.py
    → app/domains/ranking/affinity.py
```

## 领域层内部依赖

```
catalog/tagger.py      → openai (AsyncOpenAI), db/models/catalog.py
catalog/pipeline.py    → catalog/ai_generator.py, catalog/web_crawler.py, catalog/serp_sync.py, catalog/upsert.py
catalog/serp_sync.py   → serpapi, db/models/catalog.py
planning/assembler.py  → ranking/queries.py, planning/copywriter.py
planning/copywriter.py → openai (AsyncOpenAI), redis
ranking/scorer.py      → ranking/affinity.py (纯计算，无外部IO)
geography/region_router.py → data/*.json (种子文件)
geography/route_selector.py → data/route_templates/*.json
```

## 爬虫依赖

```
scripts/crawl_orchestrator.py
  → scripts/crawlers/*.py          # 各站点爬虫
    → scripts/crawlers/base.py     # 爬虫基类（自适应限速）
    → scripts/crawlers/playwright_base.py  # JS 渲染爬虫基类
  → data/crawl_progress.json       # 爬取进度（断点续传）
  → data/crawl_status.json         # 实时状态仪表板

scripts/crawlers/sakura_pipeline/cli.py
  → scripts/crawlers/sakura_pipeline/providers/*.py  # JMA/Weathernews/etc
  → scripts/crawlers/sakura_pipeline/fusion.py       # 多源融合
  → data/sakura/*.json                               # 输出数据
```

## 前端依赖

```
web/app/rush/page.tsx (Server Component)
  → web/lib/data.ts                # 数据加载器
    → data/sakura/sakura_rush_scores.json  # ★ 实际数据文件
    → data/sakura/weathernews_all_spots.json
    → data/sakura/jma/jma_city_truth_2026.json
  → web/app/rush/RushClient.tsx    # 客户端交互组件
    → web/components/rush/BloomTimeline.tsx

web/app/page.tsx (首页)
  → web/lib/constants.ts           # 文案/统计常量
  → web/lib/animations.ts          # 动画预设

web/app/admin/* (管理后台)
  → web/lib/admin-api.ts           # 后端 API 客户端
  → web/middleware.ts              # 密码保护
```

## 外部依赖

| 包 | 用于 |
|---|---|
| `fastapi` | Web 框架 |
| `sqlalchemy[asyncio]` | ORM + async DB |
| `asyncpg` | PostgreSQL async driver |
| `pgvector` | 向量搜索扩展 |
| `redis.asyncio` | Redis 客户端 |
| `arq` | 异步任务队列 |
| `openai` | GPT API 调用 |
| `pydantic-settings` | 环境变量配置 |
| `jinja2` | 模板渲染 |
| `weasyprint` | HTML → PDF |
| `httpx` | HTTP 客户端 |
| `structlog` | 结构化日志 |
| `playwright` | JS 渲染爬虫 + 截图导出 |
| `beautifulsoup4` | HTML 解析（爬虫） |
| `aiofiles` | 异步文件操作 |
