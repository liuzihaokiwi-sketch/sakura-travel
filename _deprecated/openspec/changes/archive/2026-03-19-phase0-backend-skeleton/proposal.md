## Why

所有产品功能（引流款模板、利润款定制、高客单主题攻略）都依赖同一套数据底座和业务骨架。在任何产品层工作开始之前，必须先建好 FastAPI 项目结构、PostgreSQL 全量数据库 Schema、以及基础业务工作流框架（Trip 提交/状态查询/画像标准化）。没有这个地基，后续所有模块的开发都无法并行推进。

## What Changes

- **新建** FastAPI 模块化单体项目骨架（`app/` 目录结构，按六大领域划分模块）
- **新建** PostgreSQL DDL：Layer A Catalog（8 张表）+ Layer B Snapshots（6 张表）+ Layer C Derived（13 张表）+ 业务表（8 张表），共 35 张表
- **新建** Trip Core 基础 API：`POST /trips`、`GET /trips/{id}`、`GET /trips/{id}/status`
- **新建** trip_profile 标准化逻辑（表单/自然语言 → 结构化画像 JSON）
- **新建** 异步任务队列框架（Queue Worker，`normalize_trip_profile` 为第一个 job）
- **新建** source_snapshots 基础机制（记录每次外部 API 抓取的原始返回）
- **新建** 本地开发环境配置（Docker Compose：PostgreSQL + Redis + FastAPI）
- **新建** 基础运营侧 API：`GET /ops/entities/search`

## Capabilities

### New Capabilities
- `backend-skeleton`: FastAPI 项目结构、配置管理、依赖注入、健康检查
- `database-schema`: 全量 35 张表的 DDL，按三层数据架构组织，含索引设计
- `trip-core-api`: Trip 提交/查询/状态 API + trip_profile 标准化逻辑
- `async-worker`: 异步任务队列框架，支持 normalize_trip_profile job

### Modified Capabilities
（无，这是全新项目）

## Impact

- **新建项目**：`app/` 目录，Python 3.12 + FastAPI 0.110+
- **数据库**：PostgreSQL 16，需要 pgvector 扩展
- **缓存**：Redis 7
- **依赖**：FastAPI, SQLAlchemy 2.0 (async), Alembic, pydantic-settings, redis-py, pgvector
- **本地开发**：Docker Compose 启动全套服务
- **MVP 优先级**：P0 — 所有后续模块的前置依赖
- **产品价位关系**：所有价位（¥20 引流款 / ¥69~199 利润款 / ¥299+ 高客单）都构建在这套骨架之上
