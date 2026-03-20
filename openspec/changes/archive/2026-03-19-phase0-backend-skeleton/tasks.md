## 1. 项目初始化与环境

- [x] 1.1 创建 `app/` 目录结构（domains/api/workers/db/core 按设计文档建好空目录和 `__init__.py`）
- [x] 1.2 创建 `pyproject.toml`，添加依赖：fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, alembic, pydantic-settings, arq, redis, pgvector
- [x] 1.3 创建 `docker-compose.yml`：PostgreSQL 16 (pgvector/pgvector:pg16) + Redis 7 + FastAPI 服务
- [x] 1.4 创建 `.env.example`，列出所有必填环境变量（DATABASE_URL、REDIS_URL、GOOGLE_PLACES_API_KEY 等）
- [x] 1.5 创建 `app/core/config.py`，用 pydantic-settings 定义 `Settings` 类，验证必填变量

## 2. 数据库 Schema（Layer A：Catalog）

*依赖：1.1、1.2、1.3*

- [x] 2.1 创建 `app/db/session.py`：async_session factory + `get_db` 依赖注入
- [x] 2.2 创建 `app/db/models/catalog.py`：`entity_base`、`pois`、`hotels`、`restaurants`、`entity_tags`、`entity_media`、`entity_editor_notes`、`hotel_area_guide`（共 8 张表）
- [x] 2.3 验证 entity_base 与扩展表的外键关系可正常 JOIN

## 3. 数据库 Schema（Layer B：Snapshots）

*依赖：2.1*

- [x] 3.1 创建 `app/db/models/snapshots.py`：`source_snapshots`、`hotel_offer_snapshots`、`hotel_offer_lines`、`flight_offer_snapshots`、`poi_opening_snapshots`、`weather_snapshots`（共 6 张表）

## 4. 数据库 Schema（Layer C：Derived + 业务表）

*依赖：2.2、3.1*

- [x] 4.1 创建 `app/db/models/derived.py`：`entity_scores`、`itinerary_scores`、`candidate_sets`、`route_matrix_cache`、`planner_runs`、`itinerary_plans`、`itinerary_days`、`itinerary_items`、`route_templates`、`render_templates`、`export_jobs`、`export_assets`、`plan_artifacts`（共 13 张表）
- [x] 4.2 创建 `app/db/models/business.py`：`users`、`orders`、`product_sku`、`trip_requests`、`trip_profiles`、`trip_versions`、`review_jobs`、`review_actions`（共 8 张表）

## 5. Alembic 初始化与首次迁移

*依赖：2.2、3.1、4.1、4.2*

- [x] 5.1 初始化 Alembic（`alembic init app/db/migrations`），配置 `env.py` 使用 async SQLAlchemy engine
- [x] 5.2 在迁移脚本中添加 `CREATE EXTENSION IF NOT EXISTS vector` 和 `CREATE EXTENSION IF NOT EXISTS "uuid-ossp"`
- [x] 5.3 运行 `alembic revision --autogenerate -m "initial_schema"`，检查生成的 migration 无遗漏（手动生成，bypass Docker；文件：`app/db/migrations/versions/a1b2c3d4e5f6_initial_schema.py`）
- [x] 5.4 运行 `alembic upgrade head` 验证全部 35 张表创建成功，无错误（本地 Docker 验证通过，36 rows含alembic_version）

## 6. FastAPI 应用骨架

*依赖：1.5、2.1*

- [x] 6.1 创建 `app/main.py`：初始化 FastAPI app，注册 router，配置 CORS、startup/shutdown 钩子
- [x] 6.2 实现 `GET /health`：检查 DB 连接、Redis 连接，返回 `{"status": "ok/degraded", "db": "...", "redis": "..."}`
- [x] 6.3 创建 `app/api/trips.py` router，挂载到 `/trips` 前缀

## 7. Trip Core API

*依赖：4.2、6.3*

- [x] 7.1 实现 `POST /trips`：Pydantic schema 验证输入 → 写 `trip_requests` → 入队 `normalize_trip_profile` job → 返回 202 + trip_id
- [x] 7.2 实现 `GET /trips/{id}`：读取 `trip_requests` + `trip_profiles`（如已生成）返回完整信息
- [x] 7.3 实现 `GET /trips/{id}/status`：读取 `trip_requests.status`，失败时附带 `error_summary`
- [x] 7.4 创建 `app/api/ops/entities.py`：实现 `GET /ops/entities/search`（按 city/entity_type/data_tier 过滤）

## 8. arq Worker 框架

*依赖：1.2、2.1*

- [x] 8.1 创建 `app/core/queue.py`：arq Redis pool 初始化，封装 `enqueue_job` 工具函数
- [x] 8.2 创建 `app/workers/__main__.py`：`WorkerSettings`，注册所有 job 函数，可用 `python -m app.workers` 启动
- [x] 8.3 实现 `normalize_trip_profile` job：读取 `trip_requests` → 生成 `trip_profiles` JSON → 写库 → 更新状态
- [x] 8.4 实现自动推导规则（`party_type=family_child` → 自动加 `family_friendly` 到 must_have_tags 等）
- [x] 8.5 实现 job 失败处理：重试 3 次，耗尽后更新 `trip_requests.status=failed`，写 `last_job_error`

## 9. source_snapshots 工具

*依赖：3.1、2.1*

- [x] 9.1 创建 `app/core/snapshots.py`：`record_snapshot(source_name, object_type, object_id, raw_payload, expires_in_days)` 工具函数，写入 `source_snapshots` 表
- [x] 9.2 编写单元测试：调用 `record_snapshot` 后可在 `source_snapshots` 查到记录，`expires_at` 计算正确

## 10. 端到端验证

*依赖：7.x、8.x、9.1*

- [x] 10.1 编写集成测试：`POST /trips` → Worker 消费 → `GET /trips/{id}/status` 返回 `profiled`
- [x] 10.2 验证 `GET /health` 在 DB/Redis 均正常时返回 `{"status": "ok"}`
- [x] 10.3 验证 `POST /trips` 缺少必填字段时返回 HTTP 422
- [x] 10.4 更新 `README.md`：记录本地开发启动步骤（`docker compose up`、`alembic upgrade head`、`python -m app.workers`）
