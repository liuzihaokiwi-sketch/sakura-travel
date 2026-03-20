# 部署与环境

## 本地开发环境搭建

### 前置依赖
- Python 3.11+
- Node.js 18+
- PostgreSQL 16（pgvector 扩展）
- Redis 7

### 快速启动（Docker 方式）

```bash
# 1. 克隆仓库
git clone <repo_url> && cd travel-ai

# 2. 复制环境变量
cp .env.example .env
# 编辑 .env，填入 OPENAI_API_KEY 等

# 3. 启动基础设施
docker compose up -d postgres redis

# 4. 启动后端
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000

# 5. 启动前端
cd web && npm install && npm run dev

# 6. 启动 Worker（可选）
python -m app.workers
```

### 全 Docker 方式

```bash
docker compose up -d
# API: http://localhost:8000
# 前端: http://localhost:3000
```

## 环境变量清单

| 变量 | 必填 | 说明 |
|---|---|---|
| `DATABASE_URL` | ✅ | PostgreSQL 连接串（asyncpg） |
| `REDIS_URL` | ✅ | Redis 连接串 |
| `OPENAI_API_KEY` | ✅ | OpenAI API Key（标签/文案/意图解析） |
| `AI_BASE_URL` | ⚪ | AI API 中转站地址（默认 OpenAI 官方） |
| `AI_MODEL` | ⚪ | 默认 AI 模型（默认 claude-opus-4-6） |
| `GOOGLE_PLACES_API_KEY` | ⚪ | Google Places API（实体采集） |
| `SERPAPI_KEY` | ⚪ | SerpAPI Key（搜索采集） |
| `AMADEUS_CLIENT_ID` | ⚪ | Amadeus 机票 API |
| `WECOM_WEBHOOK_URL` | ⚪ | 企业微信机器人通知 |
| `APP_ENV` | ⚪ | development / staging / production |
| `SECRET_KEY` | ⚪ | 应用密钥（生产环境必改） |
| `ALLOWED_ORIGINS` | ⚪ | CORS 允许的来源 |

## 数据库迁移

```bash
# 使用 Alembic
alembic revision --autogenerate -m "描述"
alembic upgrade head

# 开发模式自动建表（启动时 create_all）
APP_ENV=development uvicorn app.main:app --reload
```

## Docker Compose 架构

| 服务 | 镜像 | 端口 |
|---|---|---|
| postgres | pgvector/pgvector:pg16 | 5432 |
| redis | redis:7-alpine | 6379 |
| api | 自定义 Dockerfile | 8000 |
| worker | 同 api 镜像 | — |

数据持久化使用 Docker volumes：`postgres_data`, `redis_data`, `exports_data`。