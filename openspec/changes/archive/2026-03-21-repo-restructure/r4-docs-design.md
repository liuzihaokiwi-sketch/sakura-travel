# R4. 双文档体系设计

> docs-human/（给人看）+ docs-ai/（给 AI 看），两套文档各司其职。

---

## A. docs-human/ — 给人看的文档

### 设计原则
- 每个文件只讲一个主题，不做大而全
- 写"关键路径"不写"所有细节"
- 新人 30 分钟内能理解项目全貌
- 用自然语言，可以有图表但不是必须

### 文档清单

| 文件 | 目标读者 | 写什么 | 不写什么 | 结构建议 |
|---|---|---|---|---|
| `00-overview.md` | 所有人 | 项目是什么、解决什么问题、核心流程一句话、技术栈概览 | 不写细节 | 1页，bullet points |
| `01-product-scope.md` | 产品/运营 | 三个档位定义、前台页面清单、用户旅程、微信交付流程 | 不写代码 | 流程图 + 表格 |
| `02-system-architecture.md` | 后端/架构 | 后端模块划分、领域模型、数据流、API 清单、关键依赖 | 不写逐行代码 | 架构图 + 模块表 |
| `03-data-system.md` | 后端/数据 | 数据库 schema 概览、爬虫数据源、种子数据说明、数据更新策略 | 不写 SQL | 表格 + 数据流图 |
| `04-generation-workflow.md` | 后端 | 方案生成全流程（需求解析→召回→评分→编排→渲染→审核）| 不写 prompt 原文 | 流程图 + 步骤说明 |
| `05-delivery-workflow.md` | 运营/前端 | 交付页结构、H5 模块、精调流程、升级流程 | 不写组件代码 | 模块表 + 截图 |
| `06-ops-and-customer-service.md` | 运营 | 微信客服流程、AI分流规则、话术库指引（指向 openspec） | 不写技术实现 | SOP 表 |
| `07-content-engine.md` | 运营/内容 | 内容支柱、类型、排期、生成工作流概览（指向 openspec） | 不写模板代码 | 排期表 + 流程图 |
| `08-deployment-and-env.md` | 运维/后端 | 如何本地跑起来、Docker部署、环境变量清单、数据库迁移 | 不写业务逻辑 | 步骤清单 |
| `09-risk-and-known-issues.md` | 所有人 | 已知问题、待解决缺口、风险点、临时方案 | 不写已解决的历史问题 | 表格 |
| `crawlers-guide.md` | 后端/数据 | 爬虫怎么跑、输出到哪、注意事项 | 不写爬虫内部逻辑 | 命令清单 |
| `screenshots/` | — | 系统截图（架构图、交付页截图等） | — | PNG 文件 |

---

## B. docs-ai/ — 给 AI 看的文档

### 设计原则
- 结构化优先（表格 > 列表 > 散文）
- 机器可扫描（有固定格式、有分隔符）
- 每个文件是一个"查询入口"
- AI 读一个文件就能回答一类问题
- 用 YAML-like / 表格 / pseudo-schema，不用纯散文

### 文档清单

| 文件 | 目标 | 格式建议 | 必须保持最新 |
|---|---|---|---|
| `repo_index.md` | 项目目录结构 + 每个目录一句话职责 | 树状结构 + 表格 | ✅ 每次重构后更新 |
| `module_registry.md` | 所有 Python 模块/域的职责、入口、依赖 | 表格：模块名 / 路径 / 职责 / 依赖 / 入口函数 | ✅ 每次新增模块后 |
| `dependency_map.md` | 模块间依赖关系 | 邻接表或 Mermaid 图 | ✅ 重构后 |
| `runtime_entrypoints.md` | 所有可运行入口（API server / Worker / 脚本 / 前端） | 表格：入口 / 命令 / 用途 / 环境要求 | ✅ |
| `config_inventory.md` | 所有配置文件、环境变量、功能开关 | 表格：变量名 / 来源 / 默认值 / 必须/可选 | ✅ |
| `data_models.md` | 数据库表结构摘要 | pseudo-schema：表名 / 字段 / 类型 / 关系 | ✅ 迁移后 |
| `pipeline_catalog.md` | 所有管线/工作流（爬虫/生成/渲染/导出） | 表格：名称 / 触发方式 / 输入 / 输出 / 依赖 | ✅ |
| `prompt_catalog.md` | 所有 AI prompt 的位置和用途 | 表格：名称 / 文件路径 / 输入 / 输出 / token估算 | ✅ 改 prompt 后 |
| `naming_conventions.md` | 命名规范（文件/函数/变量/数据库/API） | 规则列表 | 低频 |
| `do_not_break.md` | 绝对不能改动/删除的文件清单及原因 | 表格：路径 / 原因 / 风险 | ✅ |

### 各文件格式示例

**repo_index.md 示例**：
```
# Repo Index

| 目录 | 职责 |
|---|---|
| app/ | Python 后端（FastAPI） |
| app/api/ | HTTP API 路由 |
| app/core/ | 全局配置、队列、快照 |
| app/db/ | 数据库模型、迁移 |
| app/domains/catalog/ | 实体目录管理（POI/酒店/餐厅） |
| app/domains/planning/ | 行程规划引擎 |
| ... | ... |
```

**module_registry.md 示例**：
```
# Module Registry

| 模块 | 路径 | 职责 | 核心入口 | 依赖 |
|---|---|---|---|---|
| catalog | app/domains/catalog/ | 实体CRUD+标签+AI生成 | tagger.py, ai_generator.py | db, openai |
| planning | app/domains/planning/ | 行程编排+路线矩阵 | planner.py, route_matrix.py | catalog, ranking |
| ranking | app/domains/ranking/ | 实体评分排名 | scorer.py | db, catalog |
| rendering | app/domains/rendering/ | 方案渲染为HTML/PDF | html_renderer.py | templates/, planning |
```

**do_not_break.md 示例**：
```
# Do Not Break

| 路径 | 原因 | 删除风险 |
|---|---|---|
| app/db/migrations/ | Alembic迁移链，删除导致数据库无法迁移 | 🔴 致命 |
| app/core/config.py | 全局配置入口，所有模块依赖 | 🔴 致命 |
| data/route_templates/ | 路线模板，规划引擎核心数据 | 🔴 生成不出方案 |
| templates/magazine/ | 渲染模板，交付页依赖 | 🔴 交付页打不开 |
| web/app/plan/ | H5交付页，微信链接指向此 | 🔴 用户看不到方案 |
```

---

## C. docs-human 和 docs-ai 的关系

```
docs-human/  ← 人读这个理解项目
    ↕ 互相引用但不重复
docs-ai/     ← AI 读这个理解代码
    ↕
openspec/    ← 产品spec和变更记录（两套文档都指向这里的细节）
```

- docs-human 可以写"行程生成的大致流程"
- docs-ai 写"行程生成涉及哪些模块、哪些函数、输入输出是什么"
- openspec 写"行程应该包含哪些模块、文案怎么写、修改次数几次"
- **三者不重复，通过链接互指**