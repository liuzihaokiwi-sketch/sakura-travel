# 工具链审计与升级建议

> 基于 pyproject.toml + package.json + 代码扫描的工具链评估
> 原则：免费优先，实在不行再付费

---

## 当前工具链（✅ 不用换）

| 工具 | 用途 |
|---|---|
| FastAPI | 后端框架 |
| SQLAlchemy 2.x + asyncpg | 数据库 ORM |
| Alembic | 数据库迁移 |
| httpx | HTTP 客户端/爬虫 |
| Pydantic v2 | 数据校验 |
| arq + Redis | 异步任务队列 |
| Next.js 14 | 前端框架 |
| Tailwind CSS 4 | 样式 |
| Framer Motion | 动画 |
| Playwright | 截图/导出 |
| Satori + resvg-js | OG图/卡片 |
| Ruff | Python linter |
| orjson | JSON 序列化 |
| BeautifulSoup4 | HTML 解析 |
| WeasyPrint | PDF 导出 |
| Jinja2 | 模板渲染 |

## 需要新增/替换的工具

### P0 — 翻译（DeepL 免费 API + Redis 缓存）

- **问题**：景点名/餐厅名日→中翻译全靠 GPT，浪费 token
- **方案**：DeepL 免费 API（50万字符/月）+ Redis 缓存
- **估算**：景点~500 + 餐厅~1000 + 车站~200 = ~2000 条，一天跑完
- **用完就停**：翻译一次缓存永久，不需要持续调用
- **TODO**：写批量翻译脚本 `scripts/batch_translate.py`

### P0 — AI 模型分层

- **问题**：主模型 claude-opus（贵），轻任务也用贵模型
- **方案**：

| 层级 | 用途 | 模型 |
|---|---|---|
| Tier 0 | 固定文案/清单/交通 | 不用 AI，模板填充 |
| Tier 1 | 标签/分类/简单翻译 | gpt-4o-mini |
| Tier 2 | 推荐理由/润色/避坑 | gpt-4o |
| Tier 3 | 完整行程编排/复杂决策 | claude-opus |

- **TODO**：在 config.py 加 ai_model_light / ai_model_standard / ai_model_strong

### P1 — 结构化日志（structlog）

- **问题**：只写本地文件，生产环境看不到
- **方案**：`structlog`（免费）
- **TODO**：后续部署前加

### P1 — AI 调用缓存 ✅ DONE

- **问题**：相同输入重复调 AI 浪费 token
- **方案**：Redis 缓存 AI 响应（key = hash(prompt+model)）
- **实现**：
  - `app/core/ai_cache.py` — `cached_ai_call()` 统一入口（已存在并完善）
  - `app/domains/catalog/tagger.py` — 已改为走 `cached_ai_call`（移除直接 OpenAI 调用）
  - `app/domains/planning/copywriter.py` — `_call_gpt()` 已改为走 `cached_ai_call`
  - 缓存 TTL = 7 天，Redis key = `ai_cache:{model}:{sha256(prompt)}`

### P2 — AI 调用追踪（langfuse）✅ DONE

- **问题**：不知道 token 花在哪
- **方案**：`langfuse`（免费 self-host 或免费云额度）
- **实现**：
  - `app/core/ai_cache.py` — `cached_ai_call()` 内置 langfuse 追踪
  - 环境变量 `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` 未配置时自动降级
  - `.env.example` 已添加 Langfuse 配置项
  - `pyproject.toml` 已添加 `langfuse>=2.0.0` 依赖

### P2 — Python 端 Playwright

- **问题**：JS 渲染页面爬不到（如 Google Flights）
- **方案**：Python `playwright`（免费）
- **TODO**：已有 google_flights.py 但可能需要补 playwright 支持

### P2 — 重试策略（tenacity）✅ DONE

- **问题**：手写 retry 不够稳
- **方案**：`tenacity`（免费）
- **实现**：
  - `scripts/crawlers/base.py` — `BaseCrawler.fetch()` 中的手写 `for attempt` 重试循环已替换为 `AsyncRetrying` + `wait_exponential`
  - `scripts/crawlers/sakura_pipeline/utils.py` — 已有 tenacity 装饰器（无需改动）
  - `pyproject.toml` 已添加 `tenacity>=9.0.0` 依赖
  - 重试策略：指数退避（min=2s, max=30s），429/503 自动重试，403 直接失败
