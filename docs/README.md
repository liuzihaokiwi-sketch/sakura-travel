# Travel AI — 文档索引

## 核心文档

| 文件 | 内容 |
|------|------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 系统架构：主链6步、6大子系统、评分机制、关键边界 |
| [DECISIONS.md](DECISIONS.md) | 关键决策记录（14条）：每个重大选择的背景、理由、后果 |
| [STATUS.md](STATUS.md) | 当前状态：系统成熟度、MVP定义、剩余工作 |
| [DATA_STRATEGY.md](DATA_STRATEGY.md) | 数据策略：采集渠道、质量档位、避雷机制、多样性、更新频率 |
| [DATA_FIRST_PRINCIPLES.md](DATA_FIRST_PRINCIPLES.md) | 数据第一性原理：从手账体验倒推数据需求、6层结构、统一口径 |
| [API_PROVIDERS.md](API_PROVIDERS.md) | AI API 供应商配置：DashScope / saiai / Claude 切换方法 |

## 前端

| 文件 | 内容 |
|------|------|
| [FRONTEND_DESIGN_SPEC.md](FRONTEND_DESIGN_SPEC.md) | 前端完整设计规范：重构背景、设计参考、站点地图、每页详细设计、色彩方案 |
| [TASKS_FRONTEND.md](TASKS_FRONTEND.md) | 前端重构任务清单：4批次、Sonnet 可直接执行 |

## 增长与运营

| 文件 | 内容 |
|------|------|
| [GROWTH.md](GROWTH.md) | 增长模块设计+任务清单：营销内容生成、工具页、UTM追踪（Sonnet 可直接执行） |
| [OPS_GUIDE.md](OPS_GUIDE.md) | 运营手册：后台操作 + 异常处理 SOP + 日常巡检 |

## 活动系统

| 文件 | 内容 |
|------|------|
| [TASKS_ACTIVITY_SYSTEM.md](TASKS_ACTIVITY_SYSTEM.md) | 活动簇系统：待办任务 + 新城市圈自动化流程 |
| [TASKS_DATA_PIPELINE.md](TASKS_DATA_PIPELINE.md) | 数据管线待办：结构层 / 采集层 / 消费层三层审计 |

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

`assets/` — 手账本插画/图片素材，按城市圈 → 类型组织。目前仅北海道有素材。

## 归档

`_archive/` — 历史文档，不作为当前决策依据。含旧架构文档、旧系统文档、设计讨论、已实现的设计文档（Plan B、节奏编排、旧前端重构背景等）。
