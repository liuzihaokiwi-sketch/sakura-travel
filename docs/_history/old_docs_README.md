# Travel AI -- 文档索引

> 2026-04-12 更新。文档目录按系统模块组织,字段定义集中到 SCHEMA.md(单一权威源)。

## 先看这三份流程图(迷路时从这里开始)

| 流程 | 视角 | 作用 |
|------|------|------|
| [FLOW_DATA.md](FLOW_DATA.md) | 端到端 | 用户从填表到拿到手账本整个走了什么 |
| [FLOW_RUNTIME.md](FLOW_RUNTIME.md) | 后台 | API 请求 → PDF 之间代码的调用顺序 |
| [templates/FLOW_TEMPLATE_BUILD.md](templates/FLOW_TEMPLATE_BUILD.md) | 生产 | 从零构建一个可用 day 模板的步骤 |

## 全局根目录

| 文件 | 内容 |
|------|------|
| [SCHEMA.md](SCHEMA.md) | **字段唯一权威源** -- 所有模板/实体/事件字段定义,任何字段变动必须先改这里 |
| [DECISIONS.md](DECISIONS.md) | 决策记录 -- 31 条关键决策的背景与理由 |
| [DEFERRED.md](DEFERRED.md) | 推迟项索引 -- 已达成共识但暂不做的模块 |

## 核心系统模块

### templates/ -- 模板系统(含模板/内容池/季节)

| 文件 | 内容 |
|------|------|
| [templates/TEMPLATE_CREATION_GUIDE.md](templates/TEMPLATE_CREATION_GUIDE.md) | **造模板 SOP**(给 AI 看) -- 8 步流程 + 8 条体验原则 + 11 类体验类型覆盖 |
| [templates/CONTENT_POOL_WRITING_GUIDE.md](templates/CONTENT_POOL_WRITING_GUIDE.md) | **内容池编写指引**(给 AI 看) -- 景点/餐厅/酒店/店铺写作标准 + 业务规则 |
| [templates/SEASONAL_SYSTEM_DESIGN.md](templates/SEASONAL_SYSTEM_DESIGN.md) | 季节系统 -- 独立模板 + seasonal_notes 双机制 + L0 年度更新 |

### data-engineering/ -- 数据采集系统

入口: [data-engineering/README.md](data-engineering/README.md)

| 目录 | 内容 |
|------|------|
| [data-engineering/methodology/](data-engineering/methodology/) | 方法论(master-guide) |
| [data-engineering/sources/](data-engineering/sources/) | 数据源目录(按地域+品类分) |
| [data-engineering/guides/](data-engineering/guides/) | 采集工作流(餐厅/酒店/景点/店铺) |
| [data-engineering/ops/](data-engineering/ops/) | 工具配置、开城模板、踩坑记录 |

### ops/ -- 运营

| 文件 | 内容 |
|------|------|
| [ops/OPS_GUIDE.md](ops/OPS_GUIDE.md) | 运营手册 -- 后台操作 SOP、日常巡检 |
| [ops/SERVICE_FLOW.md](ops/SERVICE_FLOW.md) | 服务完整流程 -- 获客→交付→售后 |

### page_system/ -- 渲染系统(60 页手账本页型)

| 文件 | 内容 |
|------|------|
| [page_system/01_page_types.md](page_system/01_page_types.md) | 17 种页型总表 |
| [page_system/02-05](page_system/) | 前置页、每日页、数据协议、设计清单 |

### product/ -- 产品规范

| 文件 | 内容 |
|------|------|
| [product/travel_handbook_60p_for_engineer.md](product/travel_handbook_60p_for_engineer.md) | 60 页手账本工程规范 |
| [product/travel_handbook_60p_for_owner.md](product/travel_handbook_60p_for_owner.md) | 60 页手账本产品规范 |

## 已确定存在但待文档化的模块

以下模块已经达成架构共识,但还没有专属文档。建了空目录占位,内容待填:

| 目录 | 模块 | 设计来源 |
|------|------|---------|
| [facts/](facts/) | 事实源(天气 / 大交通 / L0 事件年度更新) | [DECISIONS.md](DECISIONS.md) D15,推迟项见 [DEFERRED.md](DEFERRED.md) |
| [intake/](intake/) | 表单系统(4 屏轻表单 → 方案/预算确认页) | 已迁移完成,见 [intake/README.md](intake/README.md) |
| [rendering/](rendering/) | 渲染系统(把数据渲染成 60 页 PDF) | 现有素材在 [page_system/](page_system/) 和 [product/](product/) |

## 城市圈数据(已挪到 data/)

城市圈结构数据(关西/关东/北海道/广府/北疆)已挪到 [../data/city_circles/](../data/city_circles/),作为模板构建的参考素材。后续大概率会进一步整合或废弃。

## 归档

过期文档已移至 [_deprecated/](../_deprecated/),可从 git 历史查看。包括:
- `_deprecated/openspec/` -- 旧架构 spec
- `_deprecated/templates_v1/` -- 旧模板目录
- `_deprecated/docs/` -- 旧管线文档、旧表单设计、旧任务文档
