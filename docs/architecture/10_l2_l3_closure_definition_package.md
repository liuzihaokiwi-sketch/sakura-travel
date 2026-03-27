# 10 L2/L3 Closure Definition Package

## 文档定位

本文档只做四件事：

1. 定义什么算 L2 收口
2. 定义什么算 L3 收口
3. 固定主证明入口与兼容入口的边界
4. 解释 blocker green 代表什么、不代表什么

本文档不是：

- “当前包里做过一些实现” 的宣传页
- “测试过了几条链路” 的完成公告
- “architecture unification complete” 的替代表述

如果代码现实与旧文档表述冲突，优先收紧这里的定义，不先把兼容链包装成主链完成。

## 先固定三层状态语义

后文只允许使用以下三层语义，不能混写：

### 已完成

仅表示某一项定义内的主合同、主证明入口和最小验收口径已经明确且可验证。

它不自动推出：

- 兼容链已移除
- 所有入口都统一
- 架构统一完成

### 已完成但兼容链保留

仅表示主证明路径已经可以单独成立，但兼容链仍明确保留。

它不允许被写成：

- 已完成迁移
- 已完成架构统一
- 旧链已不再影响解释口径

### 架构统一未完成

只要下面任一事实仍成立，就必须保留这层表述：

- old/new decision chain coexist
- old/new rendering chain coexist
- report-first 与 page-model-first 并存
- truth sources 与 ops surface 仍分散

## 当前最可能继续造成误判的 5 个边界问题

### 1. `requested_city_circle` 已入合同，但还不是“只允许用户显式指定”的纯主来源

代码现实：

- `layer2_contract.py` 会优先读取 `requested_city_circle`
- 仍会从 `city_circle_intent.circle_id` 和 `destination` 推断

因此当前正确口径是：

- L2 主合同已经有该字段
- 入口来源还不是完全收紧到“显式用户字段优先、系统只校验不推断”

### 2. 新链主证明入口存在，但生成入口仍允许回退旧链

代码现实：

- `generate_trip.py::_try_city_circle_pipeline` 是当前内部主证明入口
- `generate_trip.py` 仍可能进入 `FULL_LEGACY`、`MAJOR_LEGACY`
- `FILLER_LEGACY`、`SECTION_ADAPTER` 也仍存在

因此当前正确口径是：

- 有主证明链
- 没有“对外强制新链生成入口”

### 3. `evidence_bundle` 已成为主 evidence surface，但 explain / handoff / eval 仍未完全去重为单一对象

代码现实：

- `constraint_compiler.py` 会产出 `evidence_bundle`
- `layer2_handoff.py` 会读取它并形成交付边界
- `report_generator.py` 仍持续消费 `generation_decisions`
- `offline_eval.py` 仍基于 plan/eval case 运行，不等于单一 evidence object 已彻底统一

因此当前正确口径是：

- 主 evidence surface 已形成
- evidence unification 仍未完成

### 4. L3 已建立 page-model-first 主证明面，但生成链仍是 report-first 再适配 page

代码现实：

- `page_models`、`page_overrides`、`page_render`、`shared_export_contract` 已形成主证明支路
- `generate_trip.py` 仍先 `generate_report_v2`，再 `build_layer2_delivery_handoff`，再进入 page pipeline

因此当前正确口径是：

- L3 proof path 可按 page-model-first 验收
- handbook page semantics 还不能被写成“唯一上游语义”

### 5. blocker green 只代表 blocker 所定义的主验收通过，不代表 architecture unification complete

代码现实：

- `docs/testing_layers.md` 已把 blocker 与 legacy compatibility 分层
- 但兼容链、旧入口、旧展示与旧导出仍存在

因此当前正确口径是：

- blocker green 是主证明口径绿灯
- 不是兼容链退出证明
- 不是整体架构统一证明

## L2 收口定义

### L2 收口的判断对象

L2 收口只判断以下四件事是否同时成立：

1. Layer 2 canonical input 字段集已冻结
2. 主证明入口可明确指向 city-circle staged pipeline
3. evidence surface 能从 contract 追到 constraint / policy / fallback
4. compatibility path 不再被误写成 main-proof path

### 当前 L2 主证明入口

当前主证明入口固定为：

- `app/workers/__main__.py::normalize_trip_profile`
- `app/workers/jobs/generate_trip.py::_try_city_circle_pipeline`

对外业务入口如果只是“优先尝试新链但仍可回退”，不能单独拿来证明 L2 收口完成。

### L2 收口必须能回答的字段问题

团队必须能稳定回答以下字段分别属于哪一类：

- integrated
- pass-through
- partially consumed
- legacy fallback

当前最关键字段是：

- `requested_city_circle`
- `arrival_local_datetime`
- `departure_local_datetime`
- `visited_places`
- `do_not_go_places`
- `booked_items`
- `special_requirements`

### 当前保守状态判断

- `do_not_go_places`：已进入主约束消费
- `requested_city_circle`：已进入主合同，但来源仍含推断
- `arrival_local_datetime` / `departure_local_datetime`：已进合同，消费强度不对称
- `booked_items`：已进合同并被部分消费，仍不能写成硬锁位完全完成
- `visited_places`：仍更接近 pass-through / weak-consumption
- `special_requirements`：仍是 legacy/side-channel 容器，不能写成主合同已完全替代

### L2 收口不要求什么

L2 收口不要求：

- 所有 legacy 入口删除
- 所有兼容字段下线
- 所有 circle policy 完全运营化

但 L2 收口要求：

- 这些保留必须被明确标成 compatibility 或 side-channel

## L3 收口定义

### L3 收口的判断对象

L3 收口只判断以下四件事是否同时成立：

1. page-model-first 主证明面存在且可单独失败
2. 编辑、预览、导出使用同一 page-model 源
3. handbook delivery blocker 不再依赖 legacy report/day-first 页面
4. compatibility 页面和导出入口不会被误写成主交付证明

### 当前 L3 主证明入口

当前主证明入口固定为：

- `GET /trips/{id}/page-models`
- `POST /trips/{id}/page-overrides`
- `GET /trips/{id}/page-render`
- `shared_export_contract.py` 驱动的正式导出支路

### 当前明确不是主证明入口的路径

以下路径仍应明示为 compatibility 或只读聚合，不作 L3 主证明：

- `POST /trips/{id}/generate`
- `GET /trips/{id}/export`
- `web/app/api/report/[planId]/route.ts`
- 任何仍以 `report_content` / `day-first` 语义解释自身完成度的旧展示口

### 当前保守状态判断

- 编辑链、预览链、shared export contract：可作为 L3 主证明面
- 主生成链：仍是 report-first 再 page-adapt
- 因此可以说“L3 主证明支路已建立”
- 不能说“L3 架构统一完成”

## 主证明入口与兼容入口边界

### A. 主证明入口

只可用于证明当前定义包里的主收口：

- `normalize_trip_profile`
- `_try_city_circle_pipeline`
- `GET /trips/{id}/page-models`
- `POST /trips/{id}/page-overrides`
- `GET /trips/{id}/page-render`
- `shared_export_contract`

### B. 新链优先但兼容保留

这类入口可以证明“业务已优先接入新链”，不能证明“纯新链已完成”：

- `POST /submissions/{id}/generate`
- 任何内部先尝试 city-circle pipeline、失败再 fallback 的生成入口

owner-facing 固定表述：

- “当前对外生成入口是新链优先，不是强制纯新链”
- “当前对外生成入口仍允许显式或隐式落到兼容链”
- “在出现 fallback 时，成功产物不自动等于主证明路径成功”

### C. 显式 legacy compatibility

这类入口只能证明兼容保留还在，不能证明收口完成：

- `POST /trips/{id}/generate?template_code=...`
- 不带强制 page-model contract 的旧 report/export 路径
- 任何直接以旧模板、旧 report、旧 renderer 为主的入口

### D. 必须显式失败而不是静默 fallback 的入口

以下能力缺失时，必须失败而不是临时补 page / 补 render：

- `page_models` 缺失时的 page-model 读取、编辑、预览
- shared export contract 所依赖的 page-model 数据缺失

当前这一点已是主口径的一部分，不能再回退成“从 report_content 临时拼一下也算成功”。

## 对外生成入口的统一定义

当前统一定义固定如下：

### 当前状态

- 当前没有“对外强制新链、失败即显式失败”的统一生成入口
- 当前只有“内部主证明入口”与“对外新链优先入口”
- 任何对外生成成功，都必须能区分：
  - 新链主证明成功
  - 兼容链成功
  - 新链部分执行后兼容降级成功

### owner-facing 禁止说法

以下表述现在都不允许对外使用：

- “生成入口已经统一到纯新链”
- “所有对外生成成功都可视为主路径成功”
- “兼容入口只是技术细节，无需在状态口径中出现”

### 后续何时才可改写为强制新链

只有当下面三件事同时成立，文档才允许把对外生成入口改写为强制新链：

1. 存在单一对外生成入口，且默认不再回退旧链
2. 新链失败时返回显式失败状态，而不是兼容成功
3. regression / blocker / owner-facing 汇报都能区分主链失败与兼容链成功

在这之前，实现侧不得自行把入口文案、状态文案或测试汇报改写成“已强制新链”。

## report-first 与 page-model-first 的长期边界

### 当前固定边界

- `report-first` 仍是现有主生成链中的事实上游语义
- `page-model-first` 已经是 L3 主证明面和正式交付证明面
- 两者并存时，必须写成“主证明面已建立，长期统一未完成”

### 当前不允许的实现侧改写

实现侧现在不能擅自把以下任一说法写进代码注释、PR 说明、测试汇报或 owner-facing 文档：

- “report-first 已经退出主系统”
- “page-model-first 已经成为唯一上游语义”
- “兼容 report path 现在只算历史遗留，不再影响交付解释”

### 长期收敛的触发条件

只有当下面条件同时成立，定义文档才可以宣布开始改写长期边界：

1. 生成链不再以 `generate_report_v2 -> handoff -> page pipeline` 作为默认结构
2. page semantics 在生成阶段即成为正式上游语义，而不是后适配结果
3. 旧 report-first 页面、聚合接口、导出接口不再承担任何主证明职责

在这之前，长期边界的解释权属于定义文档，不属于实现侧。

## Main Evidence Surface 定义

当前主 evidence surface 固定为三层分工，不得再混写：

### `generation_decisions`

职责：

- 记录阶段选择与 explain trace

不应被写成：

- L2 到 L3 的唯一正式 handoff

### `plan_metadata.evidence_bundle`

职责：

- 作为 contract / constraint / resolved policy / fallback reason 的主追踪对象

它是当前最接近主 evidence surface 的对象。

### `layer2_delivery_handoff`

职责：

- 把 L2 交付边界转成 L3 可消费的稳定 handoff 边界

它不等于：

- 已完成“单一上游语义统一”

## blocker green 的正式解释

`blocker green` 只代表：

- 当前 blocker 所定义的主证明路径验收通过

它不代表：

- 兼容链已经退出
- 所有业务入口都已纯新链
- 所有页面都已 page-model-first
- architecture unification complete

如果需要表达更高层状态，必须另外写：

- “兼容链保留”
- “架构统一未完成”

不能让 blocker green 替代这两层语义。

## 哪些工作现在可以安全交给 `gpt-5.3-codex`

前提是不得改变本文档中的定义口径。

可以安全下放的事项：

- route / serializer 对齐
- tests 与 regression source 对齐
- page-model API glue 修补
- edit / preview / export 同源实现细化
- asset slot 与 no-image fallback 的实现跟进
- 在既有入口分级下补齐失败语义和兼容标识

## 哪些工作仍应保留在定义层

以下事项仍属于定义层主任务，不宜直接按实现任务下放：

- 重新定义 L2/L3 closure criteria
- 改写 truth-source wording
- 改写 entry classification
- 改写 owner-facing architecture interpretation
- 把“已接入一部分”改写成“已完成迁移”的文档行为

## 当前不能宣称“已完成”的事项

以下说法现在都不能成立：

- Layer 2 已完成迁移
- Layer 3 已完成迁移
- 对外已经存在强制纯新链生成入口
- handbook page semantics 已成为唯一上游语义
- blocker green 等于架构统一完成
- policy ops 已完全统一
- compatibility path 已退出主系统

## 最终口径

团队现在应能稳定回答：

1. 什么算 L2 收口
   以冻结的 canonical input、主证明入口、evidence surface、兼容入口分级为准。
2. 什么算 L3 收口
   以 page-model-first 主证明面、同源编辑预览导出、兼容入口不混证明为准。
3. 哪些入口只是兼容入口
   任何旧模板、旧 report、旧导出、或新链优先但仍可回退旧链的入口。
4. blocker green 到底代表什么
   只代表 blocker 定义的主证明路径通过。
5. 哪些任务能直接交给 `gpt-5.3-codex`
   在不改定义口径前提下的实现型、对齐型、测试型工作。

只要这些问题仍会得到两套答案，就不能宣称当前文档包已经完成定义收口。
## 旧链清退后的剩余工作分配

本节只安排当前仍未完成的工作，并明确哪些定义层工作已在本文件内冻结完成。

### 当前仍未完成的 5 类工作

1. 旧链退出
2. 输入字段彻底规范
3. 生成语义彻底统一
4. 观测与回放彻底统一
5. 旧展示与旧导出退出主交付

### `gpt-5.4` 已在本轮完成的定义层清退工作

以下事项在本文件内视为已完成定稿，不再继续以“待定义任务”形式挂起。

#### A1 真相源口径已切换到“旧链清退阶段”

已冻结口径：

- 不再把“兼容链保留”写成长期稳定终态
- 当前口径应写为“仍有兼容链存在，但系统已进入旧链清退阶段”
- 旧入口、旧 fallback、旧导出、旧展示都属于清退对象，不再写成可长期保留结构

在本文件中的直接体现：

- 主证明入口与兼容入口被明确分开
- compatibility path 被界定为不得混写为主证明路径
- blocker green 被明确排除出“旧链已退出”的解释范围

#### A2 旧入口分级已改写为“待清退入口”视角

已冻结口径：

- 主证明入口只承担当前收口证明职责
- 新链优先但允许 fallback 的入口，属于过渡入口，不属于完成态入口
- 显式 legacy compatibility 入口属于待清退入口，不属于长期并存入口

在本文件中的直接体现：

- `POST /submissions/{id}/generate` 被归为“新链优先但兼容保留”
- 模板化生成、旧 report/export、旧 renderer 入口被归为显式 legacy compatibility
- page-model 缺失时必须显式失败，不能再借旧 report 语义静默补齐

#### A3 三个关键输入字段语义已定稿

已冻结口径：

- `requested_city_circle` 是主合同字段，目标状态是显式主输入，不再长期依赖推断
- `visited_places` 不能继续停留在无消费归属的模糊字段状态，后续实现必须给出明确消费点
- `special_requirements` 不再允许被表述成主合同核心字段，当前只应视为兼容兜底/side-channel 容器

在本文件中的直接体现：

- L2 字段分类已要求回答 integrated / pass-through / partially consumed / legacy fallback
- 当前保守状态判断已把三个字段分别放入明确语义位置

#### A4 生成语义统一目标已定稿

已冻结口径：

- 当前现实仍是 `report-first -> handoff -> page pipeline`
- 长期目标是 `page-model-first / handbook-first`
- 在生成链默认结构未改写前，不允许把 page-model-first 写成唯一上游语义

在本文件中的直接体现：

- L3 主证明面与主生成链被明确拆开
- 长期边界改写的触发条件已固定
- 旧 report-first 页面、聚合接口、导出接口被定义为后续需退出主证明职责的对象

### 分配给 `gpt-5.3-codex`

以下事项仍属于实现层待执行清退项，必须以后续实现对齐上述已冻结口径。

#### B1 清退旧生成入口与旧 fallback

主要文件：

- `app/workers/jobs/generate_trip.py`
- `app/api/trips_generate.py`
- `app/domains/planning/fallback_router.py`

目标：

- 对外默认生成入口不再回退旧链
- 新链失败返回显式失败

#### B2 收正输入字段实现

主要文件：

- `app/domains/intake/layer2_contract.py`
- `app/api/detail_forms.py`
- `app/api/submissions.py`
- `app/db/models/business.py`
- `app/domains/planning/constraint_compiler.py`

目标：

- `requested_city_circle` 作为显式主输入
- `visited_places` 具备明确消费点
- `special_requirements` 回收到兼容兜底

#### B3 推进生成链去 report-first

主要文件：

- `app/domains/planning/report_generator.py`
- `app/domains/rendering/layer2_handoff.py`
- `app/domains/rendering/page_planner.py`
- `app/domains/rendering/page_view_model.py`

目标：

- handbook/page 语义前移进入主链
- 对旧 report payload 的耦合继续下降

#### B4 统一观测与回放实现

主要文件：

- `app/domains/planning/decision_writer.py`
- `app/domains/evaluation/offline_eval.py`
- `scripts/test_cases.py`
- `scripts/run_regression.py`
- `scripts/run_regression_md.py`

目标：

- run、decision、handoff、eval、regression 已形成连续观测链路

#### B5 清退旧展示与旧导出

主要文件：

- `web/app/plan/[id]/page.tsx`
- `web/app/api/report/[planId]/route.ts`
- `web/app/api/report/[planId]/pages/route.ts`
- `app/api/trips_generate.py`
- `app/domains/rendering/magazine/html_renderer.py`

目标：

- 旧展示页退出主系统
- 旧导出入口退出主交付
### 执行顺序

当前执行顺序固定为直接进入 `gpt-5.3-codex` 实现清退：

1. `B1`
2. `B2`
3. `B3`
4. `B4`
5. `B5`

### 约束

- `gpt-5.4` 已完成本文件内定义冻结，不再重复承接同一轮定义改写
- `gpt-5.3-codex` 不负责重写真相源口径
- `gpt-5.3-codex` 必须以 `gpt-5.4` 已冻结的新口径为准执行

