# Repo Index

```
travel-ai/
├── app/                          # Python 后端（FastAPI）
│   ├── api/                      #   路由层（HTTP handlers）
│   │   ├── orders.py             #     订单 CRUD + 状态机
│   │   ├── modifications.py      #     用户修改请求 API
│   │   ├── review.py             #     管理员审核操作 API
│   │   ├── quiz.py               #     问卷提交
│   │   ├── trips.py              #     行程 CRUD
│   │   ├── trips_generate.py     #     行程生成触发
│   │   ├── chat.py               #     对话接口
│   │   ├── pois.py               #     POI 查询
│   │   ├── products.py           #     产品/SKU
│   │   └── ops/                  #     运营 API（editorial/entities/ranked）
│   ├── core/                     #   基础设施
│   │   ├── config.py             #     pydantic-settings 配置
│   │   ├── queue.py              #     Redis 连接池 + arq
│   │   └── ai_cache.py           #     AI 调用 Redis 缓存中间件
│   ├── db/                       #   数据库层
│   │   ├── models/               #     ORM 模型（catalog/business/derived/snapshots）
│   │   ├── migrations/           #     Alembic 迁移
│   │   └── session.py            #     async session factory
│   ├── domains/                  #   领域逻辑（DDD）
│   │   ├── catalog/              #     实体管理 + 数据采集 + GPT 标签
│   │   ├── ranking/              #     三层评分引擎
│   │   ├── planning/             #     行程装配 + AI 文案 + 路线矩阵
│   │   ├── rendering/            #     Jinja2 → HTML/PDF
│   │   ├── geography/            #     区域路由 + 路线选择
│   │   └── flights/              #     机票监控
│   ├── workers/                  #   arq 异步任务定义
│   └── main.py                   #   FastAPI 应用入口
├── web/                          # Next.js 14 前端
│   ├── app/                      #   App Router 页面
│   │   ├── page.tsx              #     首页（10 模块转化漏斗）
│   │   ├── quiz/                 #     5 步问卷
│   │   ├── pricing/              #     三档价格对比
│   │   ├── plan/[id]/            #     杂志级行程交付
│   │   ├── submitted/            #     提交成功 + 微信引导
│   │   ├── admin/                #     管理后台（看板 + 审核）
│   │   └── api/admin/            #     admin 登录/登出 API route
│   ├── components/               #   共享组件
│   ├── lib/                      #   工具函数（admin-api.ts）
│   └── middleware.ts             #   /admin 路由密码保护
├── scripts/                      # 运维脚本
│   ├── crawl.py                  #   数据采集
│   ├── generate_tags.py          #   GPT 9维标签批量生成
│   ├── batch_translate.py        #   DeepL 批量翻译
│   ├── mark_data_tier.py         #   数据层级标记
│   ├── load_route_templates.py   #   路线模板导入
│   └── prebuild_route_matrix.py  #   路线矩阵预计算
├── templates/                    # Jinja2 杂志风模板
│   └── magazine/                 #   杂志版渲染模板集
├── data/                         # 数据目录
│   ├── seed/                     #   永久种子数据（JSON + 路线模板）
│   ├── crawled/                  #   临时爬取（gitignore 排除）
│   └── city_defaults/            #   城市默认图片
├── tests/                        # pytest 测试
├── openspec/                     # OpenSpec 变更管理
├── docs-human/                   # 人类可读文档（10 篇）
├── docs-ai/                      # AI 结构化文档（10 篇）
├── archive/                      # 归档的遗留代码
├── hooks/                        # Git hooks（pre-commit）
├── .env.example                  # 环境变量模板
├── README.md
├── CONTRIBUTING.md
├── CODEOWNERS
├── pyproject.toml
├── alembic.ini
└── docker-compose.yml
```