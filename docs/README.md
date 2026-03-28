# Travel AI — 文档索引

## 核心文档（5篇，必读）

| 文件 | 内容 |
|------|------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 系统架构：主链6步、6大子系统、评分机制、关键边界 |
| [DECISIONS.md](DECISIONS.md) | 关键决策记录（14条）：每个重大选择的背景、理由、后果 |
| [STATUS.md](STATUS.md) | 当前状态：上线路线图、并行任务排列、验收里程碑 |
| [DATA_STRATEGY.md](DATA_STRATEGY.md) | 数据策略：采集渠道、质量档位、避雷机制、多样性、更新频率 |
| [GROWTH_MODULES.md](GROWTH_MODULES.md) | 增长模块设计：营销内容生成 + 独立工具页（流量磁铁） |
| [FRONTEND_REDESIGN.md](FRONTEND_REDESIGN.md) | 前端重构设计：页面结构、UI参考、色彩体系、核心页面wireframe |
| [TASKS_GROWTH.md](TASKS_GROWTH.md) | 增长模块任务清单：Sonnet 可直接执行 |
| [TASKS_FRONTEND.md](TASKS_FRONTEND.md) | 前端重构任务清单：4批次、含 Sonnet 配置和并行计划 |

## 城市圈数据（编辑实体数据时参考）

| 文件 | 内容 |
|------|------|
| [city_circles/kansai.md](city_circles/kansai.md) | 关西圈结构：核心基地、日游节点、12主活动cluster、10次要cluster |
| [city_circles/kansai_activities.md](city_circles/kansai_activities.md) | 关西圈活动S/A/B分级定义 |
| [city_circles/kanto.md](city_circles/kanto.md) | 关东圈结构 |
| [city_circles/hokkaido.md](city_circles/hokkaido.md) | 北海道圈结构（含季节切换逻辑） |
| [city_circles/guangfu.md](city_circles/guangfu.md) | 广府圈结构 |
| [city_circles/guangfu_activities.md](city_circles/guangfu_activities.md) | 广府圈活动分级 |
| [city_circles/xinjiang.md](city_circles/xinjiang.md) | 北疆圈结构 |
| [city_circles/xinjiang_activities.md](city_circles/xinjiang_activities.md) | 北疆圈活动分级 |

## 页面系统规范（开发渲染层时参考）

| 文件 | 内容 |
|------|------|
| [page_system/01_page_types.md](page_system/01_page_types.md) | 17种页型总表与整本框架 |
| [page_system/02_intro_pages.md](page_system/02_intro_pages.md) | 前置页与总纲页详细说明 |
| [page_system/03_daily_pages.md](page_system/03_daily_pages.md) | 章节/每日/专题页详细说明 |
| [page_system/04_data_contracts.md](page_system/04_data_contracts.md) | 页面数据协议与实现顺序 |
| [page_system/05_design_checklist.md](page_system/05_design_checklist.md) | 设计感与验收清单 |

## 产品规范

| 文件 | 内容 |
|------|------|
| [product/SERVICE_FLOW.md](product/SERVICE_FLOW.md) | 服务完整流程：获客→表单→生成→预览→修改→交付→回访 |
| [product/travel_handbook_60p_for_engineer.md](product/travel_handbook_60p_for_engineer.md) | 60页手账本工程规范 |
| [product/travel_handbook_60p_for_owner.md](product/travel_handbook_60p_for_owner.md) | 60页手账本产品规范 |
| [product/travel_form_multistep_frontend_v3.md](product/travel_form_multistep_frontend_v3.md) | V3多步表单设计（8屏+1确认） |

## 素材目录

`assets/` — 手账本插画/图片素材，按城市圈 → 类型（成品/素材）组织。目前仅北海道有素材。

## 归档

`_archive/` — 历史文档，不作为当前决策依据。
- `architecture/` — 旧14篇架构文档集
- `legacy/` — 旧13篇系统文档 + Layer设计方案
- `design_notes/` — 生成流程设计、旅行前指引模块、软硬规则说明等设计讨论
