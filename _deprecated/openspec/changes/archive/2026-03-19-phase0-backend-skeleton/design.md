## Context

这是全新项目，没有历史包袱。需要在第一次动手写代码前，确定好项目目录结构、数据库建表策略、异步任务架构、以及各层之间的依赖注入方式，避免后续重构成本。

核心约束：
- 复杂度来自业务编排，不来自并发 → 模块化单体，不拆微服务
- 数据强一致性要求（trip/score/snapshot/export 需要强一致）→ 单一 PostgreSQL
- MVP 阶段需要快速迭代和可调试 → 不引入不必要的抽象

## Goals / Non-Goals

**Goals:**
- 建立清晰的目录结构，按六大领域（trip_core/catalog/live_inventory/ranking/rendering/review_ops）划分模块
- 全量 DDL 一次建好，后续用 Alembic 管理迁移，不反复重建表
- Trip 提交到状态查询的完整异步工作流可以跑通（哪怕 normalize 逻辑先是 mock）
- 本地一条命令（`docker compose up`）启动全套服务
- source_snapshots 机制从一开始就内置，确保外部 API 调用可追溯

**Non-Goals:**
- 完整的业务逻辑（评分/编排/渲染 等后续 Phase 的内容）
- 前端页面（Next.js 是独立项目，本阶段不涉及）
- 生产环境部署配置
- 认证系统（Phase 2 再做）

## Decisions

### 决策 1：目录结构按领域划分，而非按技术层划分

**选择：**
```
app/
├── api/            # FastAPI routers（用户侧 + 运营侧）
├── workers/        # 异步 Queue Job handlers
├── domains/
│   ├── trip_core/         # 行程请求、画像标准化、订单
│   ├── catalog/           # entity_base、pois、hotels、restaurants
│   ├── live_inventory/    # snapshots 写入与读取
│   ├── ranking/           # 评分引擎（Phase 0 建框架）
│   ├── rendering/         # 渲染（Phase 1 填充）
│   └── review_ops/        # 审核与编辑修正
├── db/
│   ├── models/            # SQLAlchemy ORM models
│   ├── migrations/        # Alembic migration files
│   └── session.py         # async session factory
├── core/
│   ├── config.py          # pydantic-settings
│   ├── queue.py           # Queue Worker 接口
│   └── snapshots.py       # source_snapshots 写入工具
└── main.py
```

**备选方案：** 按技术层划分（models/schemas/services/routers）
**选择理由：** 领域划分让每个 Phase 的工作范围清晰，同一个领域的 model/service/router 在一起，不需要跨文件夹查找。技术层划分在功能多了之后会造成 models/ 和 services/ 文件夹爆炸。

---

### 决策 2：ORM 选 SQLAlchemy 2.0 async，不用 raw SQL 或 Tortoise

**选择：** SQLAlchemy 2.0 async (`asyncpg` driver)

**备选：**
- Raw SQL + asyncpg：太底层，大量重复代码
- Tortoise ORM：生态小，pgvector 支持弱
- SQLModel：底层是 SQLAlchemy，但额外抽象在复杂查询时会受限

**选择理由：** SQLAlchemy 2.0 async 是 FastAPI 生态的事实标准，支持 pgvector，Alembic 迁移成熟。

---

### 决策 3：异步任务用 Queue Worker（基于 Redis），不用 Celery

**选择：** 轻量 Worker（`arq` 库，基于 Redis）

**备选：**
- Celery：重，配置复杂，序列化有坑，`app/config.yaml` 里写的是 Celery 但第一性原理版说"队列 worker"
- arq：轻量，原生 asyncio，与 FastAPI async 生态无缝
- Dramatiq：也可以，但生态相对小

**选择理由：** MVP 阶段任务量不大，arq 够用且运维简单。如果后续确实需要 Celery 的特性（任务链、chord），迁移代价也不大。

**注意：** `app/config.yaml` 里写的是 Celery，这里改为 arq，原因记录在此。

---

### 决策 4：全量 35 张表一次建好，不分批

**选择：** Phase 0 全量建表

**备选：** 按 Phase 分批建表

**选择理由：** 三层数据架构（Catalog/Snapshots/Derived）之间有外键和 JOIN 关系，分批建表会导致后续迁移时需要处理已有数据的外键补充。DDL 是纯结构，一次建好没有副作用，反而减少后续 Alembic 迁移的复杂度。

---

### 决策 5：trip_profile 标准化第一版用结构化表单，不用 LLM

**选择：** 表单字段直接映射到 trip_profile JSON

**备选：** 接入 LLM 做自然语言解析

**选择理由：** Phase 0 目标是跑通工作流框架，LLM 解析逻辑在 Phase 2 利润款时才真正用到。先用简单映射让整条链路可以端到端测试，LLM 逻辑作为后续插拔的模块替换进来。

## Risks / Trade-offs

| 风险 | 缓解 |
|---|---|
| arq 在高并发场景有瓶颈 | MVP 阶段并发极低，若需要可换 Celery，接口抽象不变 |
| 35 张表一次建好维护压力大 | 用 Alembic autogenerate，每次只生成 delta；测试环境用 `--drop-all` 重建 |
| SQLAlchemy async 学习曲线 | 只用 2.0 的 `async_session`，不用 legacy session；写好 session factory 模板 |
| Docker Compose 在 M1/M2 Mac 的 pgvector 镜像兼容 | 使用 `pgvector/pgvector:pg16` 官方镜像，原生支持 arm64 |

## Migration Plan

1. 创建项目目录结构（`app/`）
2. 配置 `docker-compose.yml`（PostgreSQL + pgvector + Redis + FastAPI）
3. 配置 `pydantic-settings`（`core/config.py`）
4. 编写全量 SQLAlchemy models（35 张表）
5. 初始化 Alembic，生成第一个 migration
6. 实现 Trip Core API（提交/查询/状态）
7. 实现 arq Worker 框架 + `normalize_trip_profile` job
8. 实现 `source_snapshots` 写入工具
9. 端到端测试：`POST /trips` → Worker 消费 → `GET /trips/{id}/status` 返回状态

回滚：删除 `app/` 目录即可，无生产数据影响。

## Open Questions

- `trip_versions` 表的版本号格式：UUID 还是自增整数？（建议 UUID，便于分布式）
- `arq` 的 Job 失败重试策略：最大重试 3 次，退避 10s？
- `source_snapshots` 的 `expires_at` 默认 TTL 如何配置？建议走 `config.py` 统一管理
