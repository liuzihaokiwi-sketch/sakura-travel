# Runtime Entrypoints（AI 版）

## 基础依赖
- Docker：Postgres + Redis
- Python 3.12+
- Node 20+
- `.env` 基于 `.env.example`

## 后端启动
```bash
uvicorn app.main:app --reload --port 8000
```

## Worker 启动
```bash
python -m app.workers
```

## 前端启动
```bash
cd web && npm run dev
```

## 从零启动最小顺序
```bash
docker compose up -d postgres redis
python scripts/init_db.py
python scripts/fix_and_init.py
uvicorn app.main:app --reload --port 8000
cd web && npm ci && npm run dev
python -m app.workers
```

## 当前最有价值的验证顺序
1. 首页是否正常
2. `/rush` 是否正常
3. `/quiz` 是否能提交
4. 生成链路能否跑到 plan
5. PDF 是否能导出

## AI 注意
- 不要把所有脚本都当成当前必须入口
- 当前重点是主站、/rush、问卷、生成、导出闭环
