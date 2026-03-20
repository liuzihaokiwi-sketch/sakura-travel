# Naming Conventions

## Python 后端

| 类别 | 约定 | 示例 |
|---|---|---|
| 文件名 | snake_case | `intent_parser.py`, `route_matrix.py` |
| 类名 | PascalCase | `EntityBase`, `TripProfile`, `ScoreResult` |
| 函数名 | snake_case | `compute_base_score()`, `generate_tags_for_city()` |
| 异步函数 | async + snake_case | `async def assemble_trip()` |
| 常量 | UPPER_SNAKE_CASE | `SCORE_MIN`, `_REDIS_TTL`, `_GPT_TIMEOUT` |
| 私有函数 | _前缀 | `_normalize_scores()`, `_call_gpt()` |
| 数据库表名 | 复数 snake_case | `entity_base`, `itinerary_plans`, `review_jobs` |
| 数据库列名 | snake_case | `trip_request_id`, `name_zh`, `created_at` |
| API 路由 | 复数名词 | `/orders`, `/trips`, `/pois`, `/quiz` |
| Worker job | snake_case 动词+名词 | `normalize_trip_profile`, `generate_trip` |

## TypeScript 前端

| 类别 | 约定 | 示例 |
|---|---|---|
| 文件名(组件) | PascalCase.tsx | `BloomTimeline.tsx`, `Button.tsx` |
| 文件名(工具) | camelCase.ts | `animations.ts`, `utils.ts` |
| 文件名(页面) | page.tsx (Next.js 约定) | `app/quiz/page.tsx` |
| 组件名 | PascalCase | `Hero`, `PainPoints`, `QuizPage` |
| 函数名 | camelCase | `handleSelect()`, `canProceed()` |
| 常量 | UPPER_SNAKE_CASE | `QUESTIONS`, `TIERS`, `API_BASE` |
| CSS 类 | Tailwind utility classes | `bg-warm-50 text-stone-900` |
| 颜色命名空间 | sakura-*, warm-* | `sakura-300`, `warm-400` |

## 目录结构

| 约定 | 说明 |
|---|---|
| `app/domains/{domain}/` | 后端领域按功能分目录 |
| `app/api/{resource}.py` | API 路由按资源分文件 |
| `app/api/ops/{feature}.py` | 运营后台 API 在 ops/ 子目录 |
| `app/workers/jobs/{job_name}.py` | Worker job 一个文件一个 job |
| `app/db/models/{layer}.py` | ORM 模型按数据层分文件 |
| `web/app/{route}/page.tsx` | 前端页面按路由分目录 |
| `web/components/{category}/` | 前端组件按功能分类 |
| `data/route_templates/` | 路线模板 JSON |
| `scripts/crawlers/` | 爬虫模块 |
| `templates/magazine/` | Jinja2 渲染模板 |

## 数据库 ID 命名

| 表 | 主键命名 | 类型 |
|---|---|---|
| 核心业务表 | `{entity}_id` | UUID |
| 派生/缓存表 | `{entity}_id` 或 `id` | BigInteger auto |
| 外键 | 与目标主键同名 | 同目标类型 |