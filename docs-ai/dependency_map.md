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