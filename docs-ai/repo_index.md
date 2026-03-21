# Repo Index

> 最后更新：2026-03-21 · 这是整个代码库的目录索引，任何 AI 或开发者接手项目时应首先阅读此文件。

```
travel-ai/
├── app/                              # Python 后端（FastAPI）
│   ├── api/                          #   路由层（HTTP handlers）
│   │   ├── orders.py                 #     订单 CRUD + 状态机
│   │   ├── modifications.py          #     用户修改请求 API
│   │   ├── review.py                 #     管理员审核操作 API
│   │   ├── quiz.py                   #     问卷提交
│   │   ├── trips.py                  #     行程 CRUD
│   │   ├── trips_generate.py         #     行程生成触发
│   │   ├── chat.py                   #     对话接口
│   │   ├── pois.py                   #     POI 查询
│   │   ├── products.py               #     产品/SKU
│   │   └── ops/                      #     运营 API（editorial/entities/ranked）
│   ├── core/                         #   基础设施
│   │   ├── config.py                 #     pydantic-settings 配置
│   │   ├── queue.py                  #     Redis 连接池 + arq
│   │   ├── ai_cache.py               #     AI 调用 Redis 缓存中间件
│   │   └── logging_config.py         #     structlog JSON/Console 双模日志
│   ├── db/                           #   数据库层
│   │   ├── models/                   #     ORM 模型（catalog/business/derived/snapshots）
│   │   ├── migrations/               #     Alembic 迁移
│   │   └── session.py                #     async session factory
│   ├── domains/                      #   领域逻辑（DDD）
│   │   ├── catalog/                  #     实体管理 + 数据采集 + GPT 标签
│   │   ├── ranking/                  #     三层评分引擎
│   │   ├── planning/                 #     行程装配 + AI 文案 + 路线矩阵
│   │   ├── rendering/                #     Jinja2 → HTML/PDF
│   │   ├── geography/                #     区域路由 + 路线选择
│   │   └── flights/                  #     机票监控
│   ├── workers/                      #   arq 异步任务定义
│   └── main.py                       #   FastAPI 应用入口
│
├── web/                              # Next.js 14 前端
│   ├── app/                          #   App Router 页面
│   │   ├── page.tsx                  #     首页（10 模块转化漏斗）
│   │   ├── quiz/                     #     5 步问卷
│   │   ├── pricing/                  #     三档价格对比
│   │   ├── plan/[id]/                #     杂志级行程交付（⚠️ 当前仍为 mock 数据）
│   │   ├── rush/                     #     🌸 樱花冲刺排行榜（实时花期追踪）
│   │   ├── submitted/                #     提交成功 + 微信引导
│   │   ├── admin/                    #     管理后台（看板 + 审核）
│   │   └── api/                      #     Next.js API Routes
│   │       ├── admin/login/          #       admin 登录
│   │       ├── admin/logout/         #       admin 登出
│   │       └── export/plan-image/    #       Playwright 截图导出 API
│   ├── components/                   #   共享组件
│   │   ├── rush/                     #     樱花排行榜组件（BloomTimeline 等）
│   │   └── ui/                       #     基础 UI 组件（Badge 等）
│   ├── lib/                          #   工具函数
│   │   ├── data.ts                   #     樱花数据加载器（读 data/sakura/*.json）
│   │   ├── admin-api.ts              #     管理后台 API 客户端
│   │   ├── animations.ts             #     Framer Motion 动画预设
│   │   ├── constants.ts              #     硬编码常量（微信号/统计/文案）
│   │   ├── satori.ts                 #     Satori SVG/PNG 渲染
│   │   └── utils.ts                  #     cn() 等工具
│   ├── scripts/                      #   前端运维脚本
│   │   ├── export-playwright.ts      #     Playwright 页面截图
│   │   ├── export-satori.ts          #     Satori 卡片导出
│   │   ├── export-social-images.ts   #     社交媒体图片批量导出
│   │   ├── e2e-funnel-verify.ts      #     E2E 转化漏斗验证
│   │   ├── mobile-responsive-verify.ts  #  移动端响应式验证
│   │   └── visual-walkthrough.ts     #     视觉走查
│   ├── middleware.ts                 #   /admin 路由密码保护
│   ├── next.config.mjs               #   Next.js 配置
│   └── package.json                  #   前端依赖
│
├── scripts/                          # 运维与数据脚本
│   ├── crawlers/                     #   爬虫模块集合
│   │   ├── base.py                   #     爬虫基类（自适应限速）
│   │   ├── playwright_base.py        #     Playwright 爬虫基类
│   │   ├── CRAWLERS_GUIDE.md         #     爬虫开发指南
│   │   ├── tabelog.py                #     Tabelog 餐厅爬虫
│   │   ├── hotels.py                 #     Booking/Jalan 酒店爬虫
│   │   ├── jnto.py                   #     JNTO 官方景点爬虫
│   │   ├── events.py                 #     活动/祭典爬虫
│   │   ├── experiences.py            #     体验活动爬虫
│   │   ├── google_flights.py         #     Google Flights 爬虫
│   │   ├── skyscanner.py             #     Skyscanner 爬虫
│   │   ├── tianxun.py                #     天巡爬虫
│   │   ├── xiaohongshu.py            #     小红书攻略爬虫
│   │   ├── letsgojp.py               #     letsgojp 爬虫（⚠️ 待修复）
│   │   ├── matcha.py                 #     Matcha 爬虫（⚠️ 待修复）
│   │   └── sakura_pipeline/          #     🌸 樱花数据管线
│   │       ├── cli.py                #       命令行入口
│   │       ├── models.py             #       数据模型
│   │       ├── fusion.py             #       多源数据融合
│   │       ├── normalize.py          #       数据归一化
│   │       ├── lexicon.py            #       地名词典
│   │       ├── utils.py              #       工具函数
│   │       ├── configs/              #       本地站点配置
│   │       └── providers/            #       数据提供者
│   │           ├── jma.py            #         气象厅（JMA）
│   │           ├── jmc.py            #         JMC 数据
│   │           ├── weathernews.py    #         Weathernews
│   │           └── local_official.py #         各地官方网站
│   ├── crawl_orchestrator.py         #   全日本并行爬取调度器（独立运行）
│   ├── crawl.py                      #   爬虫简易入口
│   ├── sync_remote_to_local.py       #   Supabase → 本地 PG 数据同步
│   ├── fix_and_init.py               #   数据库修复与初始化（评分归一化/标签/模板）
│   ├── smart_commit.py               #   自动语义化 commit
│   ├── maintain.py                   #   一键维护脚本（deploy/status/restart）
│   ├── generate_tags.py              #   GPT 9 维标签批量生成
│   ├── batch_translate.py            #   DeepL 批量翻译（Redis 缓存）
│   ├── mark_data_tier.py             #   数据分层标记（P0-P3 城市）
│   ├── load_route_templates.py       #   路线模板导入
│   ├── prebuild_route_matrix.py      #   路线矩阵预计算
│   ├── seed_product_skus.py          #   SKU 种子数据
│   ├── init_db.py                    #   数据库初始化
│   ├── ingest_all.py                 #   批量数据入库
│   ├── generate_one_day.py           #   单日行程生成测试
│   ├── verify_api.py                 #   API 端点验证
│   ├── test_db_conn.py               #   数据库连接测试
│   ├── test_remote_db.py             #   远程数据库测试
│   ├── test_api_keys.py              #   API Key 有效性测试
│   ├── hotel_crawl.py                #   酒店爬取入口
│   ├── tabelog_crawl.py              #   Tabelog 爬取入口
│   ├── event_crawl.py                #   活动爬取入口
│   ├── experience_crawl.py           #   体验爬取入口
│   ├── flight_crawl.py               #   机票爬取入口
│   ├── guide_crawl.py                #   攻略爬取入口
│   ├── jnto_crawl.py                 #   JNTO 爬取入口
│   └── xhs_crawl.py                  #   小红书爬取入口
│
├── templates/                        # Jinja2 杂志风模板
│   └── magazine/                     #   杂志版渲染模板集
│
├── data/                             # 数据目录
│   ├── seed/                         #   永久种子数据（JSON + 路线模板）
│   ├── sakura/                       #   🌸 樱花数据（rush_scores + 各源原始数据）
│   │   └── jma/                      #     气象厅开花数据
│   ├── route_templates/              #   路线模板 JSON
│   ├── crawled/                      #   临时爬取（gitignore 排除）
│   └── city_defaults/                #   城市默认图片
│
├── tests/                            # pytest 测试
├── openspec/                         # OpenSpec 变更管理
│   ├── config.yaml                   #   OpenSpec 配置
│   └── changes/                      #   变更记录
│       ├── strategic-upgrade/        #     项目升级总方案（当前活跃）
│       └── product-conversion-redesign/ # 产品转化重设计
│
├── docs-human/                       # 人类可读文档（12 篇）
│   ├── 00-overview.md                #   项目总览
│   ├── 01-product-scope.md           #   产品范围
│   ├── 02-system-architecture.md     #   系统架构
│   ├── 03-data-system.md             #   数据体系
│   ├── 04-generation-workflow.md     #   生成工作流
│   ├── 05-delivery-workflow.md       #   交付工作流
│   ├── 06-ops-and-customer-service.md #  运营与客服
│   ├── 07-content-engine.md          #   内容引擎
│   ├── 08-deployment-and-env.md      #   部署与环境
│   ├── 09-risk-and-known-issues.md   #   风险与已知问题
│   ├── copywriting-audit-report.md   #   文案审查报告
│   └── crawlers-guide.md             #   爬虫指南
│
├── docs-ai/                          # AI 结构化文档（10 篇）
│   ├── repo_index.md                 #   ★ 仓库目录索引（本文件）
│   ├── module_registry.md            #   模块注册表
│   ├── dependency_map.md             #   依赖关系图
│   ├── do_not_break.md               #   高风险文件清单
│   ├── config_inventory.md           #   配置变量清单
│   ├── runtime_entrypoints.md        #   运行入口清单
│   ├── data_models.md                #   数据模型
│   ├── naming_conventions.md         #   命名规范
│   ├── pipeline_catalog.md           #   管线目录
│   └── prompt_catalog.md             #   Prompt 目录
│
├── .github/                          # GitHub 配置
│   └── workflows/
│       └── deploy-pages.yml          #   GitHub Pages 部署（待配置）
│
├── hooks/                            # Git hooks（pre-commit）
├── archive/                          # 归档的遗留代码
├── .env.example                      # 环境变量模板
├── README.md
├── CONTRIBUTING.md
├── CODEOWNERS
├── pyproject.toml                    # Python 项目配置（Hatchling 构建）
├── alembic.ini                       # Alembic 迁移配置
└── docker-compose.yml                # Docker 服务编排（PG + Redis）
```

## ⚠️ 当前已知问题（2026-03-21）

| 问题 | 影响 | 状态 |
|------|------|------|
| `web/app/plan/[id]/page.tsx` 使用 mock 数据 | 交付页无法显示真实行程 | 待修复 |
| `scripts/crawlers/letsgojp.py` 解析失败 | letsgojp 爬虫不可用 | 待修复 |
| `scripts/crawlers/matcha.py` 解析失败 | matcha 爬虫不可用 | 待修复 |
| `web/` 的 node_modules 是 Mac 安装的 | Windows 本地 build 需先 `npm ci` | 每次换平台需重装 |
| 线上部署方式未确定 | 网站未上线 | 需决定 Vercel/VPS |

## 📌 新 AI 接手必读顺序

1. **本文件**（`docs-ai/repo_index.md`）— 了解目录结构
2. **`docs-ai/do_not_break.md`** — 知道哪些文件不能乱改
3. **`docs-ai/runtime_entrypoints.md`** — 知道怎么启动系统
4. **`docs-ai/config_inventory.md`** — 知道需要哪些环境变量
5. **`docs-human/00-overview.md`** — 理解业务背景
6. **`docs-human/09-risk-and-known-issues.md`** — 知道已知风险
7. **`openspec/changes/strategic-upgrade/`** — 看当前活跃的升级计划