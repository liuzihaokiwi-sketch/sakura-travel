# R3. 项目结构优化方案

> 基于 R1 体检 + R2 废弃识别结论，设计新目录结构。
> 原则：最小迁移量，不改后端代码结构（app/已经很好），主要整理 data/docs/前端/归档。

---

## 一、建议的新目录结构

```
travel-ai/
├── app/                          # 🔒 不动 — Python 后端（FastAPI）
│   ├── api/                      #   API 路由
│   ├── core/                     #   全局配置/队列/快照
│   ├── db/                       #   数据库模型/迁移
│   ├── domains/                  #   业务领域模块
│   └── workers/                  #   后台任务
│
├── web/                          # 🔒 基本不动 — Next.js 前端
│   ├── app/                      #   页面路由（清理后）
│   │   ├── page.tsx              #     首页
│   │   ├── quiz/                 #     轻问卷
│   │   ├── submitted/            #     提交成功页
│   │   ├── pricing/              #     价格页
│   │   ├── plan/[id]/            #     交付页+精调+升级
│   │   ├── admin/                #     后台（未来）
│   │   ├── api/                  #     API路由
│   │   ├── custom/               #     ⚠️ 保留观察
│   │   └── city/                 #     ⚠️ 保留观察（暂不归档）
│   ├── components/               #   组件
│   ├── lib/                      #   工具
│   ├── public/                   #   静态资源
│   └── scripts/                  #   导出脚本
│
├── scripts/                      # 🔒 不动 — 爬虫+数据工具
│   ├── crawlers/                 #   爬虫模块（清理文档后）
│   └── *.py                      #   入口脚本
│
├── templates/                    # 🔒 不动 — Jinja2 杂志模板
│   └── magazine/
│
├── tests/                        # 🔒 不动 — 测试
│
├── data/                         # ⚠️ 需整理 — 数据文件
│   ├── seed/                     #   🆕 种子数据（配置JSON/XLSX）
│   ├── route_templates/          #   路线模板（已有）
│   ├── sakura/                   #   樱花数据（清理HTML后）
│   ├── raw/                      #   官方原始数据（已有）
│   └── crawled/                  #   🆕 爬虫输出（合并 *_raw/）
│       ├── events/
│       ├── experiences/
│       ├── flights/
│       ├── hotels/
│       └── tabelog/
│
├── openspec/                     # 🔒 不动 — Spec 文档
│   ├── specs/                    #   主规格
│   └── changes/                  #   变更（含当前重构）
│
├── docs-human/                   # 🆕 给人看的文档
│   ├── 00-overview.md
│   ├── 01-product-scope.md
│   ├── 02-system-architecture.md
│   ├── 03-data-system.md
│   ├── 04-generation-workflow.md
│   ├── 05-delivery-workflow.md
│   ├── 06-ops-and-customer-service.md
│   ├── 07-content-engine.md
│   ├── 08-deployment-and-env.md
│   ├── 09-risk-and-known-issues.md
│   ├── crawlers-guide.md         #   从 scripts/crawlers/ 迁入
│   └── screenshots/              #   从 docs/screenshots/ 迁入
│
├── docs-ai/                      # 🆕 给 AI 看的文档
│   ├── repo_index.md
│   ├── module_registry.md
│   ├── dependency_map.md
│   ├── runtime_entrypoints.md
│   ├── config_inventory.md
│   ├── data_models.md
│   ├── pipeline_catalog.md
│   ├── prompt_catalog.md
│   ├── naming_conventions.md
│   └── do_not_break.md
│
├── archive/                      # 🆕 归档区（不入主分支，或加 .gitignore）
│   ├── legacy-html/              #   早期HTML展示页
│   ├── legacy-docs/              #   旧版文档
│   └── legacy-web-pages/         #   废弃前端页面
│
├── .env                          # 🔴 不入库
├── .env.example                  # ✅ 入库
├── .gitignore                    # ✅ 需更新
├── README.md                     # ✅ 需重写
├── CONTRIBUTING.md               # 🆕 新建
├── CODEOWNERS                    # 🆕 新建
├── Dockerfile                    # ✅ 不动
├── docker-compose.yml            # ✅ 不动
├── pyproject.toml                # ✅ 不动
└── alembic.ini                   # ✅ 不动
```

---

## 二、每个目录职责说明

| 目录 | 职责 | 谁维护 |
|---|---|---|
| `app/` | 后端业务逻辑、API、数据库、领域模块 | 后端开发 |
| `web/` | 前端页面、组件、样式 | 前端开发 |
| `scripts/` | 爬虫、数据导入、标签生成等一次性/定期脚本 | 后端/数据 |
| `templates/` | Jinja2 杂志风格渲染模板 | 后端/设计 |
| `tests/` | Python 单元/集成测试 | 后端 |
| `data/seed/` | 种子配置数据（评分权重/路由规则/区域矩阵） | 产品/后端 |
| `data/route_templates/` | 路线骨架模板 | 产品/后端 |
| `data/crawled/` | 爬虫抓取的原始数据（不入库） | 自动生成 |
| `data/sakura/` | 樱花专题数据 | 数据 |
| `openspec/` | 产品规格、变更管理、审计报告 | 产品/AI |
| `docs-human/` | 给人看的文档（架构/流程/运维） | 团队共同 |
| `docs-ai/` | 给 AI 看的结构化文档（索引/注册/约束） | AI/后端 |
| `archive/` | 归档区，不活跃代码/文档暂存 | — |

---

## 三、迁移映射（当前 → 新结构）

### 3.1 需要移动的文件

| 当前位置 | 目标位置 | 操作 |
|---|---|---|
| `data/events_raw/` | `data/crawled/events/` | 重命名 |
| `data/experiences_raw/` | `data/crawled/experiences/` | 重命名 |
| `data/flights_raw/` | `data/crawled/flights/` | 重命名（先删 gf_error.png） |
| `data/hotels_raw/` | `data/crawled/hotels/` | 重命名 |
| `data/tabelog_raw/` | `data/crawled/tabelog/` | 重命名 |
| `data/context_score_design.json` | `data/seed/context_score_design.json` | 移动 |
| `data/entity_affinity_seed_v1.json` | `data/seed/entity_affinity_seed_v1.json` | 移动 |
| `data/japan_region_usertype_matrix_v1.json` | `data/seed/japan_region_usertype_matrix_v1.json` | 移动 |
| `data/p0_route_skeleton_templates_v1.json` | `data/seed/p0_route_skeleton_templates_v1.json` | 移动 |
| `data/questionnaire_to_theme_weights_rules_v1.json` | `data/seed/questionnaire_to_theme_weights_rules_v1.json` | 移动 |
| `data/route_region_binding_v1.json` | `data/seed/route_region_binding_v1.json` | 移动 |
| `data/日本_日本区域与线路_SeedData_v1.xlsx` | `data/seed/日本_区域与线路_SeedData_v1.xlsx` | 移动 |
| `docs/日本旅行AI后端完整方案_第一性原理版.md` | `docs-human/02-system-architecture.md`（作为参考） | 移动 |
| `docs/PLATFORM_OVERVIEW.md` | `docs-human/00-overview.md`（合并） | 移动 |
| `docs/FEATURE_GAP_ANALYSIS.md` | `docs-human/09-risk-and-known-issues.md`（合并） | 移动 |
| `docs/AI_WORK_GUIDE.md` | `docs-ai/change_playbook.md` | 移动 |
| `docs/screenshots/` | `docs-human/screenshots/` | 移动 |
| `docs/weathernews_all_spots.json` | `data/sakura/` | 移动（去重） |
| `scripts/crawlers/CRAWLERS_GUIDE.md` | `docs-human/crawlers-guide.md` | 移动 |

### 3.2 需要归档的文件（→ archive/）

见 R2 表2，共 31 项。

### 3.3 需要删除的文件

见 R2 表1，共 20 项。

### 3.4 完全不动的目录

| 目录 | 原因 |
|---|---|
| `app/` 全部 | 后端核心，结构已经很好 |
| `web/app/plan/` `web/app/quiz/` `web/app/submitted/` `web/app/pricing/` | 核心页面 |
| `web/components/ui/` `web/components/shared/` `web/components/landing/` | 活跃组件 |
| `web/lib/` | 工具库 |
| `templates/magazine/` | 渲染模板 |
| `tests/` | 测试 |
| `openspec/` | Spec 文档 |
| 根级配置文件 | `Dockerfile` `docker-compose.yml` `pyproject.toml` `alembic.ini` |

---

## 四、迁移后需更新的引用

移动 `data/*_raw/` 到 `data/crawled/` 后，需要更新以下文件中的路径引用：

| 文件 | 引用内容 | 需改为 |
|---|---|---|
| `scripts/*_crawl.py` | `data/events_raw/` 等 | `data/crawled/events/` 等 |
| `scripts/crawlers/*.py` | 输出路径 | 同上 |
| `scripts/ingest_all.py` | 读取路径 | 同上 |
| `app/domains/catalog/` | 如果有读取 raw 数据 | 同上 |

> ⚠️ 这些引用更新是迁移的**关键风险点**。如果不想改代码，可以只建 `data/crawled/` 目录但用软链接保持旧路径兼容。

### 软链接兼容方案（推荐）

```bash
# 先移动
mv data/events_raw data/crawled/events
# 再建软链接保持兼容
ln -s crawled/events data/events_raw
```

这样旧代码不需要改，新代码用新路径即可，后续逐步清理软链接。

---

## 五、迁移风险评估

| 操作 | 风险 | 缓解 |
|---|---|---|
| 归档前端页面 | 低 — 已确认无引用 | 归档不删除，可回滚 |
| 归档旧文档 | 无 — 不影响代码 | — |
| 删除调试截图 | 无 | — |
| 移动 data/*_raw/ | **中** — 代码路径引用 | 用软链接保持兼容 |
| 移动 data/*.json 到 seed/ | **中** — 代码路径引用 | 同上 |
| 新建 docs-human/ docs-ai/ | 无 — 纯新增 | — |
| 旧 docs/ 目录处理 | 低 | 先移完再删空目录 |