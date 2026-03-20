# 部署与环境

## 本地开发

```bash
# 后端
cp .env.example .env     # 填入 API Keys
pip install -e ".[dev]"  # Python 依赖
uvicorn app.main:app --reload --port 8000

# 前端
cd web && pnpm install && pnpm dev  # http://localhost:3000

# Worker
python -m app.workers  # arq 异步任务

# 数据库
docker compose up -d postgres redis
alembic upgrade head
```

## 环境变量（完整清单）

| 变量 | 必填 | 说明 |
|------|------|------|
| `DATABASE_URL` | ✅ | PostgreSQL 连接串 |
| `REDIS_URL` | ✅ | Redis 连接串 |
| `OPENAI_API_KEY` | ✅ | GPT-4o / GPT-4o-mini |
| `ANTHROPIC_API_KEY` | 推荐 | Claude（行程编排） |
| `DEEPL_API_KEY` | 推荐 | 翻译（免费版即可） |
| `GOOGLE_PLACES_API_KEY` | 可选 | POI 数据采集 |
| `SERPAPI_KEY` | 可选 | 搜索引擎数据 |
| `ADMIN_PASSWORD` | ✅ | 管理后台密码 |
| `WECOM_WEBHOOK_URL` | 推荐 | 企微通知 |
| `AI_BASE_URL` | 可选 | OpenAI API 中转站 |

## Docker Compose

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: japan_ai
      POSTGRES_PASSWORD: japan_ai_dev
      POSTGRES_DB: japan_ai
    ports: ["5432:5432"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
```

## 数据库迁移

```bash
# 生成迁移
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head

# 回退
alembic downgrade -1
```

## 备份

```bash
# 数据库备份
docker exec -t <postgres_container_id> pg_dump -U japan_ai -F tar japan_ai > japan_ai_backup.tar

# 备份恢复
docker exec -t <postgres_container_id> pg_restore -U japan_ai -d japan_ai japan_ai_backup.tar
```