# 05 Direction Taskboard

## 文件职责

本文件用于汇总当前阶段的大方向任务线。

它面向人阅读，不展开为详细开发排期，也不直接拆成工程任务。

## 当前阶段总方向任务总表

| 任务线名称 | 目标 | 当前状态 | 是否当前阶段优先 | 依赖哪些真相源文档 |
|---|---|---|---|---|
| 真相源统一与文档收口 | 把当前边界、目标形态、缺口与阶段顺序统一到一套文件中，降低旧前提继续混入的风险 | `docs/architecture/` 已建立，但旧文档仍未系统补充适用范围和历史阶段说明 | 是 | `00_scope_and_truth.md` / `01_current_state.md` / `02_target_architecture.md` / `03_gap_and_priorities.md` / `04_execution_staging.md` |
| 六城市圈范围重写 | 把范围从“日本核心城市”升级为“六城市圈”统一表达，并区分规划边界与代码现实 | 新边界已写入 architecture 文件，但旧文档和既有叙述仍大量沿用日本-only表述 | 是 | `00_scope_and_truth.md` / `01_current_state.md` / `02_target_architecture.md` |
| 60页手册交付定义统一 | 把最终交付物统一定义为“60页旅行手册”，并把插画/图片素材位纳入正式架构表达 | 手册文档已存在，但旧“长攻略/普通报告”表述仍未完全退出 | 是 | `00_scope_and_truth.md` / `02_target_architecture.md` / `travel_handbook_60p_for_engineer (1).md` / `travel_handbook_60p_for_owner.md` |
| 抖音表单优先的入口边界整理 | 明确当前主入口优先级是“抖音表单采集 -> 后端”，而不是先做完整独立站体系 | architecture 已定调，但旧增长与前端表述仍可能默认独立站优先 | 是 | `00_scope_and_truth.md` / `02_target_architecture.md` / `04_execution_staging.md` |
| 当前系统现状表达统一 | 固定“代码不是纯概念阶段，而是新旧链路并存”的统一判断 | 当前现状已写入 architecture，但还未成为全部文档的默认口径 | 是 | `01_current_state.md` / `03_gap_and_priorities.md` |
| 新旧决策链边界整理 | 统一旧 `assemble_trip` 链路与新阶段化决策链的定位和边界表达 | 缺口仍有效，但当前阶段只做边界整理，不做全面迁移 | 否 | `01_current_state.md` / `02_target_architecture.md` / `03_gap_and_priorities.md` |
| 新旧渲染链边界整理 | 统一旧 renderer/长模板与新页面系统链路的定位和边界表达 | 缺口仍有效，但当前阶段以表述收束为主 | 否 | `01_current_state.md` / `02_target_architecture.md` / `03_gap_and_priorities.md` |
| 质量与运营闭环表达收束 | 把校验、guardrails、review、回流这些分散表达整理成统一架构认知 | 相关能力已存在，但文档表达仍分散 | 否 | `01_current_state.md` / `02_target_architecture.md` / `03_gap_and_priorities.md` |
| 旧文档适用范围标注 | 不删除旧文档，但明确哪些仍有效、哪些属于历史阶段、哪些已被 architecture 覆盖 | 还未系统处理 | 是 | `00_scope_and_truth.md` / `04_execution_staging.md` |
| 中文对人文档规范 | 给人看的文档和给最终用户生成的内容默认使用中文 | 规则已确认，需要在后续文档更新中持续执行 | 是 | `AGENTS.md` |

## 本阶段先做

- 统一 architecture 真相源文件
- 把六城市圈、60页手册、插画/图片素材位、抖音表单优先写成统一边界
- 把旧前提作废项和仍保留缺口系统化写清
- 逐步给旧文档补充适用范围和历史阶段说明
- 固化中文为默认对人输出语言

## 本阶段暂不做

- 不先全面改业务代码
- 不先做大规模链路迁移
- 不先围绕独立站搭完整页面体系
- 不先拆成详细开发排期
- 不假设六城市圈能力已经在代码里全面实现

## 说明

这份总表服务于当前阶段方向判断。

当以下内容变化时，应更新本文件：

- 真相源边界变化
- 当前阶段优先级变化
- 文档整理阶段完成并进入执行设计阶段
