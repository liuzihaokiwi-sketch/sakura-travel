# R5. 仓库治理文件

> 基于 R3 新目录结构，为项目编写 README.md / CONTRIBUTING.md / CODEOWNERS / .gitignore / .env.example 的建议内容。
> 每个文件给出完整可用的内容，复制即可替换。

---

## 1. README.md

> 替换当前 README.md。保留技术深度，同时让新人 5 分钟能跑起来。

```markdown
# 🇯🇵 Travel AI — 日本旅行定制规划引擎

为用户生成 30-40 页杂志级日本旅行行程手册的全栈系统。

用户填写问卷 → 系统装配路线 → AI 润色文案 → 渲染杂志 PDF/H5 → 微信交付。

---

## 技术栈

| 层 | 技术 |
|---|---|
| 后端框架 | FastAPI 0.115+（Python 3.12） |
| 数据库 | PostgreSQL 16 + SQLAlchemy 2.0 async |
| 异步任务 | arq（Redis） |
| 迁移 | Alembic |
| 前端 | Next.js 14（App Router） + Tailwind CSS |
| 模板渲染 | Jinja2 杂志模板 + WeasyPrint PDF |
| 爬虫 | httpx + BeautifulSoup + Playwright |

## 项目结构

```
travel-ai/
├── app/                    # Python 后端（FastAPI）
│   ├── api/                #   API 路由（用户侧 + 运营侧 /ops）
│   ├── core/               #   配置 / 队列 / 快照
│   ├── db/                 #   ORM 模型（35张表）/ Alembic 迁移
│   ├── domains/            #   业务领域（catalog / planning / rendering / ranking）
│   └── workers/            #   arq 后台任务
│
├── web/                    # Next.js 前端
│   ├── app/                #   页面（问卷 / 价格 / 交付页 / 后台）
│   ├── components/         #   UI 组件
│   └── lib/                #   工具函数
│
├── scripts/                # 爬虫 + 数据工具脚本
│   └── crawlers/           #   爬虫模块（Tabelog / Hotels / Events / Flights）
│
├── templates/magazine/     # Jinja2 杂志风格渲染模板
├── tests/                  # Python 测试
├── data/                   # 种子数据 + 爬虫输出
│   ├── seed/               #   配置 JSON（评分权重/路由规则/区域矩阵）
│   ├── route_templates/    #   路线骨架模板
│   ├── crawled/            #   爬虫抓取原始数据
│   └── sakura/             #   樱花专题数据
│
├── openspec/               # 产品规格 + 变更管理
├── docs-human/             # 给人看的文档（架构/流程/运维）
└── docs-ai/                # 给 AI 看的结构化文档
```

## 快速启动

### 前置条件

- Python 3.12+
- Node.js 18+
- Docker & Docker Compose
- （可选）Playwright（爬虫需要）

### 1. 克隆 & 配置环境变量

```bash
git clone <repo-url> && cd travel-ai
cp .env.example .env
# 编辑 .env，填入真实的 API Key（至少 GOOGLE_PLACES_API_KEY + OPENAI_API_KEY）
```

### 2. 启动基础服务

```bash
docker compose up -d postgres redis
docker compose ps   # 确认 healthy
```

### 3. 后端

```bash
# 安装依赖
python3 -m pip install -e ".[dev]"

# 数据库迁移
alembic upgrade head

# 启动 API（开发模式）
uvicorn app.main:app --reload
# → http://localhost:8000/docs

# 启动 Worker（新终端）
python -m app.workers
```

### 4. 前端

```bash
cd web
npm install
npm run dev
# → http://localhost:3000
```

### 5. 数据灌入（首次）

```bash
# 采集三城市基础数据
python3 scripts/crawl.py --city tokyo
python3 scripts/crawl.py --city osaka
python3 scripts/crawl.py --city kyoto

# 标记数据层级
python3 scripts/mark_data_tier.py --city all

# 生成标签
python3 scripts/generate_tags.py --seed-only
python3 scripts/generate_tags.py --city tokyo

# 写入路线模板
python3 scripts/load_route_templates.py

# 预计算交通时间矩阵
python3 scripts/prebuild_route_matrix.py --cities tokyo osaka kyoto --top 50
```

## API 端点速查

### 用户侧

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/health` | 健康检查（DB + Redis） |
| `POST` | `/trips` | 创建行程请求 |
| `POST` | `/trips/{id}/questionnaire` | 提交问卷 |
| `POST` | `/trips/{id}/generate` | 触发异步生成（202） |
| `GET` | `/trips/{id}/plan` | 查询行程状态与内容 |
| `GET` | `/trips/{id}/preview` | H5 预览 |
| `GET` | `/trips/{id}/export/pdf` | 下载 PDF |

### 运营侧（`/ops`）

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/ops/entities/search` | 搜索实体 |
| `GET` | `/ops/entities/ranked` | 按评分排行 |
| `POST` | `/ops/entities/{type}/{id}/editorial-score` | 人工评分（-8~+8） |

## 测试

```bash
# 单元测试（无需 Docker）
pytest tests/test_snapshots.py tests/test_scorer.py -v

# 集成测试（需 Docker + DB）
pytest tests/test_trip_api.py -v

# 全量
pytest -v
```

## 脚本索引

| 脚本 | 说明 |
|---|---|
| `scripts/crawl.py` | 城市数据采集（`--city tokyo`） |
| `scripts/mark_data_tier.py` | 批量标记数据层级 |
| `scripts/generate_tags.py` | GPT 标签生成 / 种子导入 |
| `scripts/load_route_templates.py` | 写入路线模板 |
| `scripts/prebuild_route_matrix.py` | 预计算交通时间矩阵 |
| `scripts/seed_product_skus.py` | 产品 SKU 种子 |
| `scripts/ingest_all.py` | 全量数据导入 |

## 异步任务流

```
POST /trips → trip_requests(pending)
  ↓ normalize_trip_profile
  ↓ assemble_trip        ← 路线模板 + 评分召回
  ↓ enrich_copy          ← GPT 文案润色
  ↓ run_guardrails       ← 质量守卫
  ↓ export_pdf           ← WeasyPrint 渲染
  → 交付（微信 H5 链接）
```

## 许可证

私有项目，未经授权不得分发。
```

---

## 2. CONTRIBUTING.md

```markdown
# Contributing 贡献指南

## 开发环境

1. 按 README.md「快速启动」配置本地环境
2. 确保 `pytest -v` 全部通过后再提交

## 分支规范

| 分支 | 用途 |
|---|---|
| `main` | 生产稳定分支，只通过 PR 合入 |
| `dev` | 开发主分支，日常合入 |
| `feat/<name>` | 功能分支 |
| `fix/<name>` | 修复分支 |
| `refactor/<name>` | 重构分支 |
| `chore/<name>` | 杂务（依赖更新、文档、CI） |

## 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/)：

```
<type>(<scope>): <description>

feat(planner): add seasonal route weighting
fix(renderer): handle missing entity image gracefully
docs(readme): update quick start section
chore(deps): bump fastapi to 0.115.5
refactor(crawler): extract base class for all crawlers
```

常用 type：`feat` `fix` `docs` `chore` `refactor` `test` `style` `perf`

常用 scope：`api` `db` `planner` `renderer` `crawler` `web` `worker` `ops` `docs`

## 代码风格

### Python（后端）

- Python 3.12+，使用 type hints
- 格式化/检查：`ruff check . && ruff format .`
- 类型检查：`mypy app/`
- 行宽上限 100 字符
- 异步优先（async/await），数据库操作全部走 AsyncSession

### TypeScript（前端）

- Next.js App Router，TypeScript strict
- 格式化：Prettier（`.prettierrc` 配置跟随项目）
- 组件目录：`web/components/`，按功能分目录

### Jinja2 模板

- 模板文件：`templates/magazine/*.html.j2`
- 变量命名：`snake_case`
- 包含一个 `{# 变量说明注释 #}` 头部

## 测试要求

- 新增后端功能必须附带测试（`tests/` 目录）
- 测试命名：`test_<module>_<scenario>.py`
- 单元测试使用 SQLite in-memory，集成测试使用 PostgreSQL
- PR 前跑 `pytest -v` 确认全部通过

## Pull Request 流程

1. 从 `dev` 拉分支
2. 开发 + 测试
3. `ruff check . && pytest -v`
4. 提交 PR 到 `dev`，描述写清楚：
   - **做了什么**（What）
   - **为什么**（Why）
   - **怎么验证**（How to test）
5. 至少 1 人 review 后合入

## 目录约定

| 如果你要… | 放到… |
|---|---|
| 新增 API 路由 | `app/api/` 或 `app/api/ops/` |
| 新增业务逻辑 | `app/domains/<domain>/` |
| 新增后台任务 | `app/workers/jobs/` |
| 新增爬虫 | `scripts/crawlers/<source>.py` |
| 新增模板 | `templates/magazine/<name>.html.j2` |
| 新增前端页面 | `web/app/<route>/page.tsx` |
| 新增组件 | `web/components/<category>/` |
| 新增种子数据 | `data/seed/` |
| 新增/修改 Spec | `openspec/specs/` 或 `openspec/changes/` |
| 写给人看的文档 | `docs-human/` |
| 写给 AI 看的结构文档 | `docs-ai/` |

## 敏感信息

- **绝对不提交** `.env` 文件、API Key、密码、token
- 新增环境变量时同步更新 `.env.example`
- 提交前检查 `git diff --cached` 不包含敏感内容

## 数据文件

- `data/crawled/` 下的爬虫输出**不入 Git**（已在 .gitignore）
- `data/seed/` 下的配置 JSON **入 Git**
- 大于 10MB 的文件**不入 Git**
```

---

## 3. CODEOWNERS

```
# ===================================================
# CODEOWNERS — Travel AI
# 定义代码区域的负责人，PR 自动 assign reviewer
# 语法：<pattern> <@owner>
# ===================================================

# ── 全局兜底 ──
*                           @yanghailin

# ── 后端核心 ──
/app/                       @yanghailin
/app/api/                   @yanghailin
/app/db/                    @yanghailin
/app/domains/               @yanghailin
/app/workers/               @yanghailin

# ── 前端 ──
/web/                       @yanghailin

# ── 爬虫与数据 ──
/scripts/                   @yanghailin
/data/seed/                 @yanghailin
/data/route_templates/      @yanghailin

# ── 渲染模板 ──
/templates/                 @yanghailin

# ── 测试 ──
/tests/                     @yanghailin

# ── 基础设施 & 配置 ──
Dockerfile                  @yanghailin
docker-compose.yml          @yanghailin
pyproject.toml              @yanghailin
alembic.ini                 @yanghailin
.env.example                @yanghailin
.gitignore                  @yanghailin

# ── 文档 ──
/docs-human/                @yanghailin
/docs-ai/                   @yanghailin
/openspec/                  @yanghailin
README.md                   @yanghailin
CONTRIBUTING.md             @yanghailin
```

> **说明**：当前为单人/小团队阶段，所有区域指向同一 owner。团队扩大后按职责拆分（如前端 `@frontend-dev`、数据 `@data-eng`）。

---

## 4. .gitignore

> 替换当前 `.gitignore`（目前只有 4 行）。按类别分组，覆盖 Python / Node.js / IDE / 系统 / 项目特有文件。

```gitignore
# ===================================================
# .gitignore — Travel AI
# ===================================================

# ── 环境变量（绝对不入库） ──
.env
.env.local
.env.*.local

# ── Python ──
__pycache__/
*.py[cod]
*$py.class
*.so
*.egg-info/
*.egg
dist/
build/
.eggs/
.mypy_cache/
.ruff_cache/
.pytest_cache/
htmlcov/
.coverage
.coverage.*
*.cover

# ── Node.js / Next.js ──
web/node_modules/
web/.next/
web/out/
web/.turbo/
web/.vercel/

# ── 数据文件（爬虫输出不入库） ──
data/crawled/
data/events_raw/
data/experiences_raw/
data/flights_raw/
data/hotels_raw/
data/tabelog_raw/

# ── 导出产物（生成的 HTML/PDF） ──
exports/
web/output/

# ── 日志 ──
logs/
*.log

# ── IDE ──
.idea/
.vscode/
*.swp
*.swo
*~
.project
.classpath
.settings/

# ── 系统文件 ──
.DS_Store
Thumbs.db
Desktop.ini

# ── Docker 挂载卷 ──
postgres_data/
redis_data/

# ── 归档区（可选：不入主分支） ──
# archive/

# ── 临时调试文件 ──
data/gf_*.png
data/sakura/screenshots/
*.tmp
*.bak

# ── Playwright ──
web/test-results/
web/playwright-report/

# ── WeasyPrint 缓存 ──
.weasyprint-cache/
```

---

## 5. .env.example

> 当前 `.env.example` 已经比较完整，以下是建议的更新版本，补充了分组注释和新增字段。

```bash
# ===================================================
# Travel AI — 环境变量模板
# 复制为 .env 并填入真实值。绝对不提交 .env 到 Git。
# ===================================================

# ── 数据库 ──────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://japan_ai:japan_ai_dev@localhost:5432/japan_ai
POSTGRES_USER=japan_ai
POSTGRES_PASSWORD=japan_ai_dev
POSTGRES_DB=japan_ai

# ── Redis / arq Worker ──────────────────────────────
REDIS_URL=redis://localhost:6379/0

# ── 外部 API ────────────────────────────────────────
GOOGLE_PLACES_API_KEY=your_google_places_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# ── Amadeus 机票监控（可选） ────────────────────────
AMADEUS_CLIENT_ID=your_amadeus_client_id
AMADEUS_CLIENT_SECRET=your_amadeus_client_secret

# ── 应用配置 ────────────────────────────────────────
APP_ENV=development          # development | staging | production
APP_DEBUG=true
SECRET_KEY=change_me_to_a_random_secret_key_in_production
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# ── 快照 TTL（天） ──────────────────────────────────
SNAPSHOT_TTL_HOTEL_OFFER=1
SNAPSHOT_TTL_FLIGHT_OFFER=1
SNAPSHOT_TTL_POI_OPENING=7
SNAPSHOT_TTL_WEATHER=1

# ── Worker 配置 ─────────────────────────────────────
WORKER_MAX_JOBS=10
JOB_RETRY_MAX=3
JOB_RETRY_DELAY_SECS=10

# ── 通知渠道 ────────────────────────────────────────
# 企业微信机器人 Webhook（推荐）
WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx

# 邮件通知（备用）
SMTP_HOST=smtp.qq.com
SMTP_USER=your@qq.com
SMTP_PASSWORD=your_smtp_token
ALERT_EMAIL=notify@yourteam.com

# ── 前端（Next.js 公开变量用 NEXT_PUBLIC_ 前缀）────
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

---

## 6. 实施说明

| 文件 | 操作 | 备注 |
|---|---|---|
| `README.md` | 替换 | 当前 README 内容大部分保留，重新组织结构 |
| `CONTRIBUTING.md` | 新建 | 项目根目录 |
| `CODEOWNERS` | 新建 | 项目根目录（需 GitHub 仓库启用 CODEOWNERS） |
| `.gitignore` | 替换 | 从 4 行扩展到完整覆盖 |
| `.env.example` | 更新 | 补充 `NEXT_PUBLIC_*` 前端变量 |

### 替换顺序建议

```bash
# 1. 先更新 .gitignore（最重要，防止脏文件入库）
# 2. 新建 CODEOWNERS + CONTRIBUTING.md
# 3. 替换 README.md
# 4. 更新 .env.example
# 5. git add -A && git commit -m "chore: add repo governance files (R5)"
```
