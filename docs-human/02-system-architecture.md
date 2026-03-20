# 系统架构

## 总体架构

```
用户浏览器 (Next.js 14 前端)
       │
       │  REST API
       ▼
FastAPI 后端 (app/main.py)
  ├── api/ ─── 路由层（quiz, orders, trips, trips_generate, pois, products, chat, ops/）
  ├── domains/ ─── 业务领域层
  │     ├── intake/      → 意图解析（自然语言 → 结构化行程需求）
  │     ├── geography/   → 区域路由（用户画像 → 推荐地区 + 路线选择）
  │     ├── catalog/     → 数据目录（实体采集、GPT 标签、SERP 同步、AI 生成）
  │     ├── ranking/     → 评分引擎（实体评分 + 上下文评分 + 编辑 Boost）
  │     ├── planning/    → 行程装配（模板加载 → 候选填充 → 文案润色 → 路线矩阵）
  │     ├── rendering/   → 渲染引擎（Jinja2 → HTML → WeasyPrint PDF）
  │     ├── flights/     → 机票监控（Amadeus API）
  │     └── live_inventory/ → 实时库存
  ├── workers/ ─── 异步任务（arq + Redis）
  │     └── jobs/ → normalize_trip_profile, generate_plan, generate_trip,
  │                 render_export, run_guardrails, score_entities, scan_flight_prices
  └── db/ ─── 数据层
        ├── models/ → catalog.py(8表), business.py(8表), derived.py(13表), snapshots.py(6表)
        └── session.py → SQLAlchemy 2 async session

       │
       │  arq 任务队列
       ▼
Redis 6379 ─── 缓存 + 任务队列 + 翻译缓存 + AI 调用缓存
       │
       ▼
PostgreSQL 5432 (pgvector) ─── 35 张表，4 层架构
```

## 四层数据库架构

| 层 | 文件 | 表数 | 职责 |
|---|---|---|---|
| Layer A: Catalog | catalog.py | 8 | 静态事实：实体、景点、酒店、餐厅、标签、媒体、编辑标注 |
| Layer B: Snapshots | snapshots.py | 6 | 动态事实：酒店报价、航班价格、景点开放状态、天气 |
| Layer C: Derived | derived.py | 13 | 计算结果：评分、行程方案、天/条目、路线模板、渲染、导出 |
| Layer D: Business | business.py | 8 | 业务流程：用户、SKU、订单、行程请求、画像、版本、审核 |

## 前端架构

Next.js 14 App Router + TypeScript + Tailwind CSS 4 + Framer Motion：

- `/` — 营销首页（10 个模块的转化漏斗）
- `/quiz` — 5 步问卷（目的地→天数→同行人→风格→微信号）
- `/submitted` — 提交成功 + 微信引导
- `/plan/[id]` — 行程交付页（支持 `?mode=preview` 免费预览模式）
- `/pricing` — 三档定价对比页
- `/admin` — 内部管理后台（密码保护）

## 关键数据流

1. **问卷提交**: quiz/page.tsx → POST /quiz → 创建 TripRequest → 企业微信通知
2. **行程生成**: Worker normalize_trip_profile → generate_plan → generate_trip → render_export → run_guardrails
3. **交付查看**: plan/[id]/page.tsx → GET /trips/{id}/plan → 渲染行程内容