/opt/travel-ai/docker-compose.prod.yml  /opt/travel-ai/docker-compose.yml
services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: japan_ai_postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-japan_ai}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-japan_ai_dev}
      POSTGRES_DB: ${POSTGRES_DB:-japan_ai}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-japan_ai} -d ${POSTGRES_DB:-japan_ai}"]
      interval: 5s
      timeout: 5s
      retries: 10

  redis:
    image: redis:7-alpine
    container_name: japan_ai_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 10
[root@iZj6chkex6u9xz7wdqlly2Z travel-ai]# cat /opt/travel-ai/docker-compose.yml
services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: japan_ai_postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-japan_ai}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-japan_ai_dev}
      POSTGRES_DB: ${POSTGRES_DB:-japan_ai}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-japan_ai} -d ${POSTGRES_DB:-japan_ai}"]
      interval: 5s
      timeout: 5s
      retries: 10

  redis:
    image: redis:7-alpine
    container_name: japan_ai_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 10

  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: japan_ai_api
    env_file:
      - .env
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./app:/app/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  worker:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: japan_ai_worker
    env_file:
      - .env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./app:/app/app
      - exports_data:/app/exports
    command: python -m app.workers

volumes:
  postgres_data:
  redis_data:
  exports_data:
[root@iZj6chkex6u9xz7wdqlly2Z travel-ai]# 