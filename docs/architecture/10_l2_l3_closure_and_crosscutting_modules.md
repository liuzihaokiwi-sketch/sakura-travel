> Superseded（已吸收进收口定义包）：
> 当前请优先使用 `docs/architecture/10_l2_l3_closure_definition_package.md`。
> 本文件保留为“任务归位草案 / 历史讨论输入”，不再作为当前任务状态、完成度或任务分配的主依据。

# 10 L2/L3 收口与横切模块任务文档

## 文档职责

本文档用于把两类任务放到同一套当前真源口径下：

- `L2` / `L3` 尚未收口的剩余任务
- 超出 `L1` - `L4` 四层边界、但已经在系统中真实存在的横切模块

它不是详细排期，不直接拆成 sprint，也不把所有事项都升级成新的主层。

本文档回答四个问题：

1. 哪些旧前提在这批任务里已经失效
2. 新边界改变了哪些层与共享能力的表达方式
3. 哪些历史 gap 仍然有效，必须继续保留
4. 为什么当前阶段仍先做文档收口与任务归位，而不是直接大规模改代码

## 边界对齐

### 已失效的旧前提

以下前提不再适合作为 `L2` / `L3` 与横切模块任务的默认假设：

- 任务重点只是“把日本行程逻辑做得更聪明”
- 当前主入口是独立站完整漏斗
- 输出物仍主要是长报告或普通 HTML/PDF
- 四层之外的能力可以继续散落在各文件里
- 只要 `L2` / `L3` blocker 通过，就等于迁移已经完成

### 新边界带来的影响

当前边界已经明确为：

- 六城市圈
- Douyin form intake 优先
- 60 页 travel handbook
- page semantics 与 image / illustration slots
- 新旧链并存但尚未收口

这会直接改变两类任务的表达方式。

#### 对 `L2` 的影响

`L2` 不再只是“更好的 itinerary planner”。

它现在必须承接：

- intake contract 的主入口对齐
- city-circle-aware policy 的统一注入
- explain / evidence / decision snapshot 的稳定产出
- 面向 `L3` 的稳定 handoff

#### 对 `L3` 的影响

`L3` 不再只是“把 report 渲染得更好看”。

它现在必须承接：

- handbook page semantics
- `chapter_plan -> page_plan -> page_view_model`
- shared PDF/H5 delivery contract
- 资产槽位与无图兜底
- 编辑态与正式导出的同源性

#### 对横切能力的影响

有些能力已经不适合继续被视为“零散附属逻辑”。

它们需要被明确归位为：

- 正式横切模块
- 某层内部必须单独命名的子平面 / 子系统

### 仍然有效的历史 gap

以下 gap 仍然有效，不能因为新增了任务文档就被覆盖掉：

- old and new decision chains coexist
- old and new rendering chains coexist
- truth sources are distributed
- quality and operations are still distributed

在本文档里，它们体现为：

- `L2` 收口不是“继续加模块”，而是减少主链歧义
- `L3` 收口不是“继续加页型”，而是减少交付语义歧义
- 横切模块归位不是“新造大层”，而是减少分散 ownership

### 为什么当前阶段仍先做文档收口

这批任务虽然已经触达实现层，但当前阶段仍不能默认直接进入大规模代码迁移。

原因不是工作不重要，而是现在最容易发生的错误是：

- 一边按新边界推进 `L2` / `L3`
- 一边让入口、配置、素材、导出、运营继续沿用旧口径

这样会形成新的混合状态：

- 主链偏新
- 入口偏旧
- 页面系统偏新
- 导出与运营表达偏散

所以当前阶段仍应先做：

- 把 `L2` / `L3` 的剩余任务写清楚
- 把横切模块写清楚
- 把“独立主层”和“层内子系统”区分清楚
- 再进入后续代码收口

### 当前阶段同时禁止什么

当前阶段同时禁止补丁式治理：

- 不允许在旧前提上继续叠加 patch、补桥、临时胶水
- 不允许把 compatibility bridge 包装成主链完成
- 不允许靠 patch 掩盖 truth source、contract、source-of-truth object、main path 没修好的事实
- 遇到结构问题，优先改 truth source、contract、source-of-truth object、main path

## 模块归位结论

本文档采用三类结构，而不是把所有能力都抬成同级主层。

### A. 主层

- `L1` Data / Foundation
- `L2` Decision / Orchestration
- `L3` Page Semantics / Rendering
- `L4` Quality / Review / Operations

### B. 正式横切模块

这些能力跨越多层，且已经成为当前系统稳定性与可扩展性的硬约束：

- Intake Contract
- Knowledge And Policy Ops
- Observability And Replay

### C. 层内必须单独命名的子平面 / 子系统

这些能力非常重要，但更适合归属在某一层内部：

- `L3` 内：Asset And Media
- `L3` 内：Delivery Channel
- `L4` 内：Operator Console

### D. 关于 `L0`

`L0` 可以作为工作中的辅助提法，表示 truth-source / architecture / taskboard / reading order。

但在当前文档集里，`L0` 更像治理入口，不建议替代 `L1` - `L4` 成为新的业务主层命名。

## L2 剩余收口任务

### L2-C1 入口 contract 冻结

目标：

- 确认当前正式 Layer 2 输入 contract
- 标出已接入字段、缺失字段、透传字段、兼容字段

当前问题：

- worker 主链已经开始读取新 contract
- 但不同入口、不同测试、不同 API 的 contract 仍有漂移

完成标准：

- 有单一 contract truth source
- `requested_city_circle`、arrival / departure local datetime、visited / do-not-go、booked_items、special_requirements 等字段状态清楚
- 新旧入口的兼容逻辑明确

### L2-C2 入口分层与新旧链边界固定

目标：

- 明确哪些入口强制走新链
- 哪些入口只是兼容旧链
- 哪些场景允许 fallback

当前问题：

- worker 主路径偏新
- API / 模板模式仍可能直接调用旧 `assemble_trip`

完成标准：

- 每个入口有明确 generation path
- fallback 触发条件可解释
- 不再出现“默认走哪条链说不清”的状态

### L2-C3 city-circle 从候选推断转向用户目标圈校验

目标：

- 把 `L2` 的默认心智固定为“用户先选圈，系统校验与圈内编排”

当前问题：

- 当前 selector 已经支持 `requested_city_circle`
- 但整体表达还容易滑回“自动选最优圈”

完成标准：

- 目标城市圈成为强信号
- selector、constraint、hotel/base、skeleton 都能解释“为什么在这个圈内这样排”

### L2-C4 explain / evidence / decision snapshot 补齐

目标：

- 稳定输出可被 `L3`、评测、review、回放共同消费的 decision artifacts

当前问题：

- `generation_decisions`、`evidence_bundle` 已存在
- 但字段完整性与下游消费边界还不够稳定

完成标准：

- selected / not-selected / fallback / policy 来源都有结构化表达
- `L3` handoff 不再依赖隐式推断

### L2-C5 policy bundle 正式运营化

目标：

- 把城市圈 policy、规则包、override、版本来源从“实现细节”提升为正式运营对象

当前问题：

- 已有 `policy_resolver`、`config_resolver`、seed、admin config
- 但 ownership、版本化、更新流程仍偏分散

完成标准：

- one pipeline + many policy packs + one evidence format 被写成正式运行原则

## L3 剩余收口任务

### L3-C1 页面链成为默认交付主路径

目标：

- 让 `chapter_plan -> page_plan -> page_view_model` 成为 handbook 默认主路径

当前问题：

- 新链已存在
- 旧 renderer / 长模板仍在并行工作

完成标准：

- 新链是默认交付语义
- 旧链只保留明确兼容边界

### L3-C2 shared delivery contract 固定

目标：

- 固定 Web / PDF / H5 / export bridge 共用的 page contract

当前问题：

- `page_plan`、`page_models`、`shared export contract` 已有
- 但不同渠道仍可能出现局部重组或隐式转换

完成标准：

- 所有渠道优先消费同一份 page semantics
- 不再让某个渠道偷偷走旧 report 语义

### L3-C3 编辑态与正式导出同源

目标：

- 确认 page edit、preview、formal export 基于同一组 page models 与 asset manifest

当前问题：

- 编辑 API 和 render payload 已出现
- 但它们还没有被正式写成 handbook delivery 的固定边界

完成标准：

- 用户编辑的页面内容在预览与正式导出中保持一致
- 不再出现“编辑看得到，导出不一定吃到”的路径分叉

### L3-C4 handbook 语义优先于 report 语义

目标：

- 后续新增内容优先进入 page semantics，而不是先堆进 report 字段

当前问题：

- 代码与历史文档里仍保留不少 report framing

完成标准：

- 新需求默认落在 chapter / page / view model / slot contract
- report 只作为中间载荷或兼容表示

### L3-C5 资产槽位与无图兜底规范化

目标：

- 明确 hero、slot、版权来源、fallback、placeholder 的统一规则

当前问题：

- 资产相关能力已经开始出现
- 但仍更像局部实现，不像完整共享底座

完成标准：

- 页面系统不再把素材解析散落在各页型组件里

## 横切模块任务

### X1 Intake Contract

定位：

- 正式横切模块

职责：

- 统一原始表单、标准化输入、缺省策略、版本兼容、form-to-backend handoff

为什么优先：

- 当前入口优先级已经改成 Douyin 表单 intake
- 这决定 `L2` 能否稳定收口

近期任务：

- 冻结 contract schema
- 建立字段状态清单
- 建立入口映射清单
- 明确兼容版本策略

### X2 Knowledge And Policy Ops

定位：

- 正式横切模块

职责：

- 管理城市圈 policy、rule pack、override、seed、版本来源、运营调口

为什么优先：

- 六城市圈扩展的第一风险不是页面不够华丽
- 而是同一主链被不同圈层规则慢慢打散

近期任务：

- 统一 policy 来源表达
- 统一运营 override 表达
- 建立 policy version / source / owner 视图

### X3 Observability And Replay

定位：

- 正式横切模块

职责：

- 统一 run_id、trace、decision snapshots、offline eval、diff、replay、regression evidence

为什么优先：

- 当前系统已经多阶段、多入口、多链路并存
- 没有统一观测与回放，就无法稳定判断“哪里跑偏”

近期任务：

- 固定 run-level 观测边界
- 固定 decision / evidence / eval 的关联方式
- 固定 replay 与 regression case 的输入来源

### X4 Asset And Media

定位：

- `L3` 内共享基础设施

职责：

- 管理 hero、asset manifest、slot contract、版权来源、placeholder、无图兜底

近期任务：

- 把 asset source / fallback 规则从页型实现里抽出来
- 建立 handbook 交付所需的最小素材协议

### X5 Delivery Channel

定位：

- `L3` 内 channel-adapter 平面

职责：

- 管理同一份 page semantics 如何输出到 PDF / H5 / preview / export

近期任务：

- 固定共享 delivery contract
- 明确 render adapter 边界
- 避免渠道侧重新发明 report 组装逻辑

### X6 Operator Console

定位：

- `L4` 内 operator surface / operator console 子系统

职责：

- 管理 review、锁字段、人工修订、补素材、发布控制、运营操作面

近期任务：

- 把分散的 review / page edit / admin config / publish control 归并成统一 operator 视图

## 当前优先级

如按当前真源和代码现实给出优先级，建议如下：

### P0

- `L2-C1` 入口 contract 冻结
- `X1` Intake Contract
- `X2` Knowledge And Policy Ops
- `X3` Observability And Replay

### P1

- `L2-C2` 入口分层与新旧链边界固定
- `L2-C4` explain / evidence / decision snapshot 补齐
- `L3-C1` 页面链成为默认交付主路径
- `L3-C2` shared delivery contract 固定

### P2

- `L2-C3` 目标圈校验心智收口
- `L2-C5` policy bundle 正式运营化
- `L3-C3` 编辑态与正式导出同源
- `L3-C5` 资产槽位与无图兜底规范化
- `X4` Asset And Media
- `X5` Delivery Channel

### P3

- `L3-C4` handbook 语义完全压过 report 语义
- `X6` Operator Console 统一操作面收口

## 本文档不做的事

本文档不直接做下面这些事情：

- 不把所有模块都提升成新的主层
- 不直接制定详细 sprint 排期
- 不假设旧链已可立即整体删除
- 不假设六城市圈能力已经全面完工
- 不把文档中的优先级直接等同于立刻大规模改代码

## 使用方式

这份文档适合用于：

- 判断 `L2` / `L3` 剩余工作是不是继续跑偏
- 判断四层之外哪些能力应升级为正式模块
- 给后续实现计划、审计、收口 review 提供统一口径

应与以下文件一起阅读：

1. `00_scope_and_truth.md`
2. `01_current_state.md`
3. `02_target_architecture.md`
4. `03_gap_and_priorities.md`
5. `04_execution_staging.md`
6. `05_direction_taskboard.md`
7. `09_layer2_city_circle_policy_modules.md`
8. `10_l2_l3_closure_definition_package.md`
