# Repo Index

```
travel-ai/
├── app/                          # Python 后端（FastAPI）
│   ├── api/                      # API 路由层
│   │   ├── ops/                  # 运营/编辑后台 API
│   │   ├── chat.py               # 自然语言对话接口
│   │   ├── orders.py             # 订单 CRUD + 状态管理
│   │   ├── pois.py               # 景点搜索/详情
│   │   ├── products.py           # 产品 SKU 查询/价格计算
│   │   ├── quiz.py               # 问卷提交
│   │   ├── trips.py              # 行程创建/查询
│   │   └── trips_generate.py     # 行程生成/导出/预览
│   ├── core/                     # 核心配置
│   │   ├── config.py             # Pydantic Settings（环境变量）
│   │   ├── queue.py              # Redis 连接池管理
│   │   └── snapshots.py          # 快照管理
│   ├── db/                       # 数据层
│   │   ├── models/               # SQLAlchemy ORM 模型（4 个文件，35 张表）
│   │   ├── migrations/           # Alembic 迁移
│   │   └── session.py            # 数据库会话工厂
│   ├── domains/                  # 业务领域层（DDD 风格）
│   │   ├── catalog/              # 数据目录：采集、标签、同步、AI 生成
│   │   ├── flights/              # 机票监控
│   │   ├── geography/            # 区域路由 + 路线选择
│   │   ├── intake/               # 意图解析（NLP → 结构化）
│   │   ├── live_inventory/       # 实时库存
│   │   ├── planning/             # 行程装配 + 文案润色 + 路线矩阵
│   │   ├── ranking/              # 评分引擎
│   │   ├── rendering/            # HTML/PDF 渲染
│   │   └── trip_core/            # 行程核心逻辑
│   ├── workers/                  # arq 异步任务
│   │   ├── jobs/                 # 各类 Worker job
│   │   └── __main__.py           # Worker 启动入口
│   └── main.py                   # FastAPI 应用入口
├── web/                          # Next.js 14 前端
│   ├── app/                      # App Router 页面
│   │   ├── page.tsx              # 首行（营销漏斗）
│   │   ├── quiz/                 # 问卷页
│   │   ├── submitted/            # 提交成功页
│   │   ├── plan/[id]/            # 行程交付页
│   │   ├── pricing/              # 价格对比页
│   │   ├── city/                 # 城市页
│   │   └── custom/               # 定制页
│   ├── components/               # React 组件
│   │   ├── landing/              # 首页组件
│   │   ├── shared/               # 共享组件
│   │   ├── social/               # 社交分享组件
│   │   └── ui/                   # 基础 UI 组件（Button, Badge 等）
│   ├── lib/                      # 工具函数和常量
│   └── scripts/                  # 导出脚本（Playwright, Satori）
├── templates/magazine/           # Jinja2 杂志风渲染模板（16 个模板）
├── data/                         # 种子数据 + 爬取数据
│   ├── route_templates/          # 路线模板 JSON（8 条线路）
│   ├── sakura/                   # 樱花数据
│   └── *_raw/                    # 各类爬取原始数据
├── scripts/                      # Python 工具脚本
│   └── crawlers/                 # 爬虫模块（12 个爬虫）
├── tests/                        # 测试文件
├── docs-human/                   # 面向人类的文档
├── docs-ai/                      # 面向 AI 的结构化文档
├── openspec/                     # OpenSpec 需求管理
├── docker-compose.yml            # Docker 编排
├── Dockerfile                    # API/Worker 镜像
├── pyproject.toml                # Python 包管理
└── alembic.ini                   # 数据库迁移配置
```
