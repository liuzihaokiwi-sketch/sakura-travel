# Travel AI — 旅行手账生成系统

AI 驱动的付费旅行手账本系统。专家策展 + 本地人视角 → 中国游客"照着走就对了"。

## 对用户的口号

> **一本为你写好的旅行手账·旅行时带着走·旅行后留作回忆。**

## 产品定位

- **交付物**：60 页纸质旅行手账本 + 贴纸 DIY 包
- **定价**：国内 ¥298 / 国外 ¥348
- **入口**：抖音表单采集（前期）·独立站（后期）
- **覆盖**：日本（关西样板间已铺·关东/北海道/中部/九州 待开圈）+ 未来扩中国/欧洲

**我们卖的不是信息·是「品质」+「确定性」+「独立」**——不和任何商家合作·不收恰饭·不接返佣。

## 核心文档（按需查）

| 你想做什么 | 读哪份 |
|---|---|
| 第一次进项目·想理解整体 | [CLAUDE.md](CLAUDE.md) |
| 理解产品哲学 | [docs/项目核心/项目定位.md](docs/项目核心/项目定位.md) |
| 看字段长什么样 | [docs/项目核心/字段权威.md](docs/项目核心/字段权威.md) |
| 看历史决策 | [docs/项目核心/历史决策.md](docs/项目核心/历史决策.md) |
| 开新城市圈 | [docs/操作SOP/总流程.md](docs/操作SOP/总流程.md) |
| 做关西模板 | [docs/操作SOP/上线前/模板写作.md](docs/操作SOP/上线前/模板写作.md) |
| 采集数据（餐厅/景点/酒店/停留点） | [docs/操作SOP/上线前/数据池构建/](docs/操作SOP/上线前/数据池构建/) |
| 关西定位+装配硬规 | [japan/kansai/这是什么.md](japan/kansai/这是什么.md) |

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | FastAPI（Python 3.12·async） |
| 前端 | Next.js 14（TypeScript） |
| 数据库 | PostgreSQL + Redis |
| 任务队列 | arq |
| AI | Claude Opus / Sonnet（Anthropic）+ qwen-max（阿里云·高并发场景） |
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
uvicorn app.main:app --reload      # API（端口 8000）
python -m app.workers              # Worker
cd web && pnpm install && pnpm dev # 前端（端口 3000）
```

> ⚠️ 当前 app/ 代码部分待修（路径未跟仓库重构同步）·数据池建设是当前主线。

## 目录结构

```
travel-ai/
├── CLAUDE.md                    ← AI 进项目第一份读
├── japan/                       ← 日本数据（关西已铺）
│   ├── kansai/                  ← 关西工作区
│   │   ├── entities/ restaurants/ stops/ hotels/ templates/
│   │   ├── assembly/            ← 装配规则
│   │   └── 这是什么.md           ← 关西定位+装配硬规
│   └── docs/                    ← 日本特化（独立站清单等）
├── docs/
│   ├── 项目核心/                ← 项目定位/字段权威/数据流/业务流/历史决策
│   └── 操作SOP/
│       ├── 总流程.md             ← 12 步骨架
│       ├── 数据采集.md           ← 跨 Phase 理论
│       ├── 上线前/              ← 研究/模板/装配/数据池构建
│       └── 上线后/              ← pilot/运营/客服
├── marketing/                   ← 运营素材库
├── scripts/                     ← validator + 数据脚本
├── app/ web/                    ← 代码
└── _archive/                    ← 历史归档
```

## 校验工具

每类数据有对应 validator·跑通才算完：

```bash
python scripts/validate_entity.py
python scripts/validate_restaurants.py    # 同时校验 restaurants + stops
python scripts/validate_hotels.py
python scripts/validate_template.py
```
