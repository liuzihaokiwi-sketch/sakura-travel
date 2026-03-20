# Japan Travel AI — Backend

> 第一性原理架构的日本旅行 AI 规划与交付引擎。

## 技术栈

| 层级 | 技术 |
|------|------|
| Web Framework | FastAPI 0.115+ (Python 3.12) |
| ORM | SQLAlchemy 2.0 async + asyncpg |
| Database | PostgreSQL 16 + pgvector |
| 异步任务 | arq (Redis-based) |
| 迁移管理 | Alembic |
| 配置管理 | pydantic-settings |

## 数据架构（三层）

```
Layer A – Catalog     : 静态事实（景点/酒店/餐厅基础信息）      8 张表
Layer B – Snapshots   : 动态快照（实时价格/开放状态/天气）       6 张表
Layer C – Derived     : 计算结果（评分/行程/渲染/交付物）       13 张表
Business              : 用户/订单/行程请求/审核工作流            8 张表
───────────────────────────────────────────────────────────────────
Total                                                            35 张表
```

## 本地开发快速启动

### 1. 环境准备

```bash
# 复制环境变量模板
cp .env.example .env
# 编辑 .env，填入真实 API Keys（如 GOOGLE_PLACES_API_KEY）
```

### 2. 启动 Docker 服务（PostgreSQL + Redis）

```bash
docker compose up -d postgres redis
# 等待 healthy（约 10s）
docker compose ps
```

### 3. 安装 Python 依赖

```bash
python3 -m pip install -e ".[dev]"
```

### 4. 执行数据库迁移（建全量 35 张表）

```bash
# 生成 autogenerate migration（首次）
alembic revision --autogenerate -m "initial_schema"

# 应用迁移
alembic upgrade head
```

### 5. 启动 API 服务

```bash
uvicorn app.main:app --reload
# API 文档：http://localhost:8000/docs
# 健康检查：http://localhost:8000/health
```

### 6. 启动 arq Worker

```bash
# 新开一个终端
python -m app.workers
```

### 7. 运行测试

```bash
# 单元测试（无需 Docker / PostgreSQL）
pytest tests/test_snapshots.py -v
pytest tests/test_score_entities_e2e.py -v   # 评分引擎端到端（SQLite in-memory）

# 集成测试（需 Docker + DB）
pytest tests/test_trip_api.py -v

# 全量测试
pytest -v
```

### 8. 数据灌入（Phase 0）

> 前置：`.env` 中已配置 `OPENAI_API_KEY`（用于 GPT 标签生成）

```bash
# 8-1. 采集三城市基础数据
python3 scripts/crawl.py --city tokyo
python3 scripts/crawl.py --city osaka
python3 scripts/crawl.py --city kyoto

# 8-2. 自动标记 data_tier（有 Google Place ID → A，否则 → B）
python3 scripts/mark_data_tier.py --city all

# 8-3. 导入人工种子标签（人工优先，覆盖 GPT）
python3 scripts/generate_tags.py --seed-only

# 8-4. GPT-4o-mini 批量生成 9 维主题亲和度标签
python3 scripts/generate_tags.py --city tokyo
python3 scripts/generate_tags.py --city osaka
python3 scripts/generate_tags.py --city kyoto

# 8-5. 手动触发评分任务（通常 crawl.py 结束后自动入队）
python3 -c "
import asyncio
from app.core.queue import enqueue_job
for city in ['tokyo', 'osaka', 'kyoto']:
    asyncio.run(enqueue_job('score_entities', city_code=city))
"
```

## API 端点概览

### 用户侧

| Method | Path | 描述 |
|--------|------|------|
| `GET`  | `/health` | 服务健康检查（DB + Redis） |
| `POST` | `/trips` | 提交行程请求，返回 202 |
| `GET`  | `/trips/{id}` | 获取行程详情（含 profile） |
| `GET`  | `/trips/{id}/status` | 轻量状态轮询 |

### 运营侧（`/ops`）

| Method | Path | 描述 |
|--------|------|------|
| `GET`  | `/ops/entities/search` | 按城市/类型/层级搜索实体 |
| `GET`  | `/ops/entities/ranked` | 按 final_score 降序返回实体 |
| `POST` | `/ops/entities/{entity_type}/{entity_id}/editorial-score` | 录入 Editorial Boost（-8 ~ +8） |
| `GET`  | `/ops/entities/{entity_type}/{entity_id}/editorial-history` | 查看 boost 变更历史 |
| `PATCH`| `/ops/entities/{entity_id}/data-tier` | 手动设置数据层级（S/A/B） |

**`GET /ops/entities/ranked` 参数示例：**

```
GET /ops/entities/ranked?city_code=tokyo&entity_type=poi&score_profile=general&limit=20
```

**`POST /ops/entities/poi/{id}/editorial-score` Body 示例：**

```json
{
  "boost_value": 3,
  "note": "编辑推荐：春季樱花期特别上榜",
  "operator": "editor_alice"
}
```

## 异步工作流

```
POST /trips
    │
    ▼
trip_requests (status=pending)
    │
    ▼  [arq job: normalize_trip_profile]
    │
    ├── 推导标签规则（family_child → family_friendly 等）
    ├── 写入 trip_profiles
    └── trip_requests.status = "profiled"
```

## 项目结构

```
travel-ai/
├── app/                # 应用主体
│   ├── api/            #   FastAPI routers（用户侧 + 运营侧）
│   │   └── ops/        #     运营端 API（entities / editorial / ranked）
│   ├── workers/        #   arq Job handlers（score_entities / normalize 等）
│   ├── domains/        #   领域逻辑（catalog / ranking / geography / rendering）
│   ├── db/
│   │   ├── models/     #     SQLAlchemy ORM（4 个文件，35 张表）
│   │   ├── migrations/ #     Alembic 迁移脚本
│   │   └── session.py  #     async session factory
│   ├── core/           #   基础设施（config / queue / snapshots）
│   └── main.py
├── scripts/            # 运维脚本（crawl / generate_tags / mark_data_tier）
├── data/               # 种子数据 JSON（region matrix / route binding / affinity seed）
├── templates/          # Jinja2 模板（邮件/渲染）
├── tests/              # 测试（单元 + 端到端）
├── docs/               # 设计文档 & 规划文档
│   ├── 日本旅行AI后端完整方案_第一性原理版.md   # 底层架构方案
│   ├── PROJECT_PLAN.md                          # 项目计划 v2.0（分周里程碑）
│   └── AI_WORK_GUIDE.md                         # AI 协作开发指南
├── openspec/           # OpenSpec 变更管理
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── alembic.ini
└── README.md
```

## 评分架构（三分量）

```
候选实体
    │
    ▼ [1] Base Score / System Score（0-100）
    │   platform_rating   × 0.25  ← Google Rating（归一化）
    │   review_confidence × 0.15  ← 评价数量置信度
    │   recency           × 0.15  ← 数据新鲜度
    │   data_tier_bonus   × 0.20  ← 数据层级（S/A/B）
    │   has_opening_hours × 0.10  ← 营业时间完整性
    │   photo_richness    × 0.10  ← 图片丰富度
    │   homogeneity_penalty       ← 过度同质化惩罚
    │
    ▼ [2] Context Score（0-100，可选）
    │   9 维主题亲和度（由 GPT-4o-mini 生成）× 用户偏好权重
    │   主题：shopping / food / culture_history / onsen_relaxation /
    │         nature_outdoors / anime_pop_culture / family_kids /
    │         nightlife_entertainment / photography_scenic
    │
    ▼ [3] Editorial Boost（-8 ~ +8）
    │   运营人工标注，来自 entity_editor_notes（note_type="editorial_boost"）
    │
    └──▶ final_score = base_score + editorial_boost（clamped 0-100）
         score_breakdown 包含所有分量明细，透明可审计
```

## Phase 1：攻略生成（行程 PDF）

Phase 1 在 Phase 0 的数据基础上，新增了完整的行程装配 → 文案润色 → 杂志级 PDF 渲染能力。

### 行程生成命令

```bash
# 生成东京经典 5 日攻略（标准版）
curl -X POST http://localhost:8000/trips \
  -H "Content-Type: application/json" \
  -d '{"sku_id": "standard_128", "city_codes": ["tokyo"]}'

# 提交问卷（场景 couple）
curl -X POST http://localhost:8000/trips/{trip_id}/questionnaire \
  -H "Content-Type: application/json" \
  -d '{"scene": "couple", "duration_days": 5}'

# 触发异步生成
curl -X POST http://localhost:8000/trips/{trip_id}/generate

# 查询生成状态
curl http://localhost:8000/trips/{trip_id}/plan

# 预览 HTML
curl http://localhost:8000/trips/{trip_id}/preview

# 下载 PDF
curl http://localhost:8000/trips/{trip_id}/export/pdf -o itinerary.pdf
```

### 路线模板加载

```bash
# 首次部署：写入 5 条经典路线模板
python3 scripts/load_route_templates.py

# 预计算三城市 Top50 景点对的交通时间（Google Routes API / Haversine fallback）
python3 scripts/prebuild_route_matrix.py --cities tokyo osaka kyoto --top 50
# 仅东京，步行模式
python3 scripts/prebuild_route_matrix.py --cities tokyo --top 30 --mode walking
```

### Phase 1 新增 API 端点

#### 行程规划（`/trips`）

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/trips` | 创建行程（传入 sku_id + city_codes） |
| `GET`  | `/trips/{id}/profile-questions` | 获取问卷题目 |
| `POST` | `/trips/{id}/questionnaire` | 提交问卷（scene / duration_days / preferences） |
| `POST` | `/trips/{id}/generate` | 触发异步行程生成（返回 202） |
| `GET`  | `/trips/{id}/plan` | 查询行程状态和内容 |
| `GET`  | `/trips/{id}/preview` | 获取 H5 预览 URL |
| `GET`  | `/trips/{id}/export/pdf` | 下载 PDF 文件 |

#### 运营侧新增（`/ops`）

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/ops/entities/ranked` | 按城市 + 类型查询评分排行 |
| `POST` | `/ops/entities/{type}/{id}/editorial-score` | 设置人工分（-8~+8） |
| `GET` | `/ops/entities/{type}/{id}/editorial-history` | 查看编辑历史 |

### 异步 Worker Job 列表（Phase 1 新增）

| Job 名称 | 触发方 | 说明 |
|----------|--------|------|
| `assemble_trip` | POST /trips/{id}/generate | 装配行程（路线模板 + 评分召回） |
| `enrich_copy` | assemble_trip 完成后 | AI 文案润色（GPT 批量） |
| `run_guardrails` | enrich_copy 完成后 | 行程质量守卫 |
| `export_pdf` | POST /trips/{id}/export/pdf | WeasyPrint 异步渲染 PDF |
| `score_entities` | 数据入库 / 手动触发 | 重新计算评分 |

---

## 脚本索引（scripts/）

| 脚本 | 说明 |
|------|------|
| `crawl.py` | 城市数据采集（`--city tokyo` / `--all-cities`） |
| `mark_data_tier.py` | 批量标记 data_tier（`--city all`） |
| `generate_tags.py` | GPT 标签生成 / 种子数据导入（`--seed-only`） |
| `load_route_templates.py` | 写入路线模板种子数据（5 条经典路线） |
| `prebuild_route_matrix.py` | 预计算城市 TopN 实体对交通时间（Google Routes API + fallback） |
