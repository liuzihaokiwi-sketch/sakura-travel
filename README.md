# 🗾 Japan Travel AI

> 日本旅行 AI 定制服务 — 从问卷到杂志级行程攻略的全自动交付引擎。

## ✨ 项目简介

Travel AI 是一个面向中国出境游客的日本旅行定制服务平台。用户通过 3 分钟问卷描述偏好，AI 系统自动生成个性化行程攻略并渲染为杂志级 PDF / H5 交付物。

**核心价值**：用 AI 替代传统旅行社的人工定制流程，将交付周期从 3-5 天缩短到 30 分钟。

## 🛠 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | Next.js 14 (App Router) + TypeScript + Tailwind CSS 4 + Framer Motion |
| **后端** | FastAPI 0.115+ (Python 3.12) |
| **ORM** | SQLAlchemy 2.0 async + asyncpg |
| **数据库** | PostgreSQL 16 + pgvector |
| **异步任务** | arq (Redis-based) |
| **迁移管理** | Alembic |
| **配置管理** | pydantic-settings |
| **AI** | OpenAI GPT-4o / GPT-4o-mini + Anthropic Claude |
| **渲染** | Jinja2 模板 + WeasyPrint PDF |
| **翻译** | DeepL API |
| **包管理** | hatch (pyproject.toml) / pnpm (web/) |

## 🏗 系统架构

```
用户端（Next.js）          管理后台（Next.js /admin）
     │                           │
     ▼                           ▼
FastAPI API Gateway ────── PostgreSQL + Redis
     │
     ├── domains/catalog    → 实体数据管理（POI/酒店/餐厅）
     ├── domains/ranking    → 评分引擎（Base + Context + Editorial）
     ├── domains/planning   → 行程装配 + AI 文案润色
     ├── domains/rendering  → 杂志级 HTML/PDF 渲染
     └── workers/           → arq 异步任务（生成/评分/导出）
```

## 💰 三档定价

| 套餐 | 价格 | 交付物 |
|------|------|--------|
| **免费试用** | ¥0 | 3 日粗略行程 + 预览 |
| **标准版** | ¥248 | 完整行程 PDF + 1 次精调 |
| **尊享版** | ¥888 | 完整行程 + 3 次精调 + 人工审核 + 专属客服 |

## 🚀 本地开发环境搭建

### 前置要求

- Python 3.12+
- Node.js 18+ / pnpm
- Docker & Docker Compose（PostgreSQL + Redis）
- API Keys: OpenAI、Google Places（可选）

### 1. 克隆仓库 & 配置环境变量

```bash
git clone https://github.com/your-org/travel-ai.git
cd travel-ai
cp .env.example .env
# 编辑 .env，填入真实 API Keys
```

### 2. 启动 Docker 服务

```bash
docker compose up -d postgres redis
docker compose ps  # 确认 healthy
```

### 3. 安装后端依赖

```bash
python3 -m pip install -e ".[dev]"
```

### 4. 数据库迁移

```bash
alembic upgrade head
```

### 5. 安装前端依赖

```bash
cd web && pnpm install && cd ..
```

### 6. 启动服务

```bash
# 终端 1：后端 API
uvicorn app.main:app --reload

# 终端 2：arq Worker
python -m app.workers

# 终端 3：前端
cd web && pnpm dev
```

- 后端 API 文档：http://localhost:8000/docs
- 前端：http://localhost:3000
- 健康检查：http://localhost:8000/health

## 📋 常用命令

```bash
# ── 数据采集 ──────────────────────────────────
python3 scripts/crawl.py --city tokyo          # 采集东京数据
python3 scripts/mark_data_tier.py --city all   # 标记数据层级

# ── AI 标签生成 ───────────────────────────────
python3 scripts/generate_tags.py --seed-only   # 导入种子标签
python3 scripts/generate_tags.py --city tokyo  # GPT 批量打标

# ── 翻译 ─────────────────────────────────────
python3 scripts/batch_translate.py --city tokyo --dry-run  # 预览
python3 scripts/batch_translate.py --city tokyo            # 执行翻译

# ── 路线模板 ──────────────────────────────────
python3 scripts/load_route_templates.py
python3 scripts/prebuild_route_matrix.py --cities tokyo osaka kyoto --top 50

# ── 测试 ─────────────────────────────────────
pytest tests/ -v                               # 全量测试
pytest tests/test_snapshots.py -v              # 单元测试
ruff check app/ scripts/                       # Lint
```

## 📂 目录结构

```
travel-ai/
├── app/                     # Python 后端
│   ├── api/                 #   FastAPI routers
│   │   └── ops/             #     运营端 API
│   ├── core/                #   基础设施（config / queue / ai_cache）
│   ├── db/
│   │   ├── models/          #     SQLAlchemy ORM（35 张表）
│   │   ├── migrations/      #     Alembic 迁移
│   │   └── session.py       #     async session factory
│   ├── domains/             #   领域逻辑
│   │   ├── catalog/         #     实体管理 + GPT 标签
│   │   ├── ranking/         #     评分引擎
│   │   ├── planning/        #     行程装配 + 文案润色
│   │   ├── rendering/       #     杂志级 HTML/PDF 渲染
│   │   ├── geography/       #     区域路由 + 路线选择
│   │   └── flights/         #     机票监控
│   ├── workers/             #   arq 异步 Worker
│   └── main.py
├── web/                     # Next.js 前端
│   ├── app/                 #   App Router 页面
│   │   ├── page.tsx         #     首页
│   │   ├── quiz/            #     问卷页
│   │   ├── pricing/         #     价格页
│   │   ├── plan/[id]/       #     交付页
│   │   └── admin/           #     管理后台
│   └── components/          #   共享组件
├── scripts/                 # 运维脚本
│   ├── crawl.py             #   数据采集
│   ├── generate_tags.py     #   GPT 标签生成
│   ├── batch_translate.py   #   批量翻译
│   └── hooks/               #   Git hooks
├── data/                    # 数据目录
│   ├── seed/                #   永久配置（种子数据 JSON / 路线模板）
│   ├── crawled/             #   临时爬取数据（gitignore 排除）
│   └── city_defaults/       #   城市默认图片
├── templates/               # Jinja2 模板（杂志渲染）
├── tests/                   # 测试
├── openspec/                # OpenSpec 变更管理
├── docker-compose.yml
├── pyproject.toml
├── alembic.ini
└── README.md
```

## 🔌 API 端点概览

### 用户侧

| Method | Path | 描述 |
|--------|------|------|
| `GET` | `/health` | 服务健康检查 |
| `POST` | `/trips` | 创建行程请求 |
| `GET` | `/trips/{id}` | 获取行程详情 |
| `POST` | `/trips/{id}/generate` | 触发行程生成 |
| `GET` | `/trips/{id}/plan` | 查询行程状态和内容 |
| `GET` | `/trips/{id}/export/pdf` | 下载 PDF |

### 运营侧 (`/ops`)

| Method | Path | 描述 |
|--------|------|------|
| `GET` | `/ops/entities/search` | 搜索实体 |
| `GET` | `/ops/entities/ranked` | 评分排行 |
| `POST` | `/ops/entities/{type}/{id}/editorial-score` | 设置人工分 |

### 订单管理 (`/orders`)

| Method | Path | 描述 |
|--------|------|------|
| `POST` | `/orders` | 创建订单 |
| `GET` | `/orders` | 订单列表（支持 status 过滤） |
| `GET` | `/orders/{id}` | 订单详情 |

## 🤖 AI 模型分层

| Tier | 模型 | 用途 | 环境变量 |
|------|------|------|----------|
| Light | `gpt-4o-mini` | 标签分类 / 翻译 | `AI_MODEL_LIGHT` |
| Standard | `gpt-4o` | 文案润色 / 推荐理由 | `AI_MODEL_STANDARD` |
| Strong | `claude-sonnet` | 完整行程编排 | `AI_MODEL_STRONG` |

## 📄 License

Private — All rights reserved.