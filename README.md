# Travel AI -- 旅行手账生成系统

AI 驱动的旅行手账本生成系统。用户填写表单 -> 系统自动规划行程 -> 生成60页手账本 PDF。

## 产品定位

- **交付物**: 纸质旅行手账本 + 贴纸DIY包
- **定价**: 国内 Y298 / 国外 Y348
- **入口**: 抖音表单采集（前期），独立站（后期）
- **覆盖**: 六城市圈（关西、关东、北海道、广府、北疆、广东）

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | FastAPI (Python 3.12, async) |
| 前端 | Next.js 14 (TypeScript) |
| 数据库 | PostgreSQL + Redis |
| 任务队列 | arq |
| AI | Claude Opus / Sonnet (Anthropic) + qwen-max (阿里云, 高并发场景) |
| PDF | WeasyPrint |

## 快速启动

```bash
# 1. 环境配置
cp .env.example .env  # 填入 API Keys

# 2. 启动服务
docker compose up -d postgres redis
pip install -e ".[dev]"
alembic upgrade head

# 3. 运行
uvicorn app.main:app --reload      # API (端口 8000)
python -m app.workers              # Worker
cd web && pnpm install && pnpm dev # 前端 (端口 3000)
```

## 目录结构

```
app/
  api/              # REST 路由 + ops API
  core/             # 基础设施
  db/               # ORM 模型 + 迁移
  domains/
    intake/         # 表单归一化
    planning_v2/    # 16步行程规划管线
    rendering/      # 页面生成 + PDF 渲染
    ranking/        # 实体评分
    evaluation/     # 离线评测
    review_ops/     # 多模型评审
    catalog/        # 实体采集管理
  workers/          # arq 后台任务
web/                # Next.js 前端 + 管理后台
scripts/            # 爬虫 + 种子数据 + 运维
assets/             # 手账本素材（按城市圈分）
docs/               # 文档（见 docs/README.md）
```

## 文档

- [docs/SYSTEM_DESIGN_V2.md](docs/SYSTEM_DESIGN_V2.md) -- 系统设计总纲
- [docs/pipeline/README.md](docs/pipeline/README.md) -- 16步行程规划管线
- [docs/DECISIONS.md](docs/DECISIONS.md) -- 关键决策记录
