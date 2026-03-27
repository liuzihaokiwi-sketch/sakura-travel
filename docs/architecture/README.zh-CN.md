# 当前架构文档入口

这份 README 只做一件事：给团队提供一个稳定入口，避免把多个文件误读成并列真相源。

## 先看哪里

唯一的总入口是：

1. `docs/architecture/00_scope_and_truth.md`

当需要继续往下读时，严格按下面顺序：

1. `docs/architecture/00_scope_and_truth.md`
2. `docs/architecture/02_target_architecture.md`
3. `docs/architecture/01_current_state.md`
4. `docs/architecture/03_gap_and_priorities.md`
5. `docs/architecture/04_execution_staging.md`
6. `docs/architecture/09_layer2_city_circle_policy_modules.md`
7. `docs/architecture/10_l2_l3_closure_definition_package.md`

## 这套文档现在回答什么

当前文档集用于统一四类问题：

- 当前系统边界到底是什么
- 新旧链路各自处于什么状态
- 什么能算主证明路径，什么只是兼容路径
- blocker green、L2 收口、L3 收口分别代表什么

它不是：

- 旧文档的索引汇编
- 多个并列真相源的导航页
- 大规模重构任务看板

## 当前阶段的默认口径

- 系统不是 Japan-only，也不是一次性 itinerary writer
- 当前获取优先级是 Douyin 表单接入，不是 standalone site 完整度
- 交付物默认是 60 页 handbook，不是长报告
- 当前主要工作是定义收口、边界收紧、真相源统一，不是继续在旧前提上打 patch

## 与旧文档的关系

旧文档仍可作为历史输入，但不能覆盖当前真相源顺序。

尤其不要把下面这些历史说法继续当当前口径：

- Japan-only 默认成立
- standalone site 是当前主入口
- 只要还能导出报告，就等于交付链已统一
- 只要 blocker 绿灯，就等于 architecture unification complete

## 两份最容易被误读的补充文档

- `docs/architecture/09_layer2_city_circle_policy_modules.md`
  只负责定义 Layer 2 policy bundle 的主合同、来源层次和归属，不代表六城市圈实现已经完全统一。
- `docs/architecture/10_l2_l3_closure_definition_package.md`
  只负责定义 L2/L3 收口标准、入口分级、evidence surface 和 blocker 语义，不代表整仓迁移完成。

## 一句话原则

如果团队要先判断“什么是真的、什么算完成、什么只是兼容保留”，先回到 `00_scope_and_truth.md`；如果团队要判断“L2/L3 到底收口到哪一步”，再看 `10_l2_l3_closure_definition_package.md`。
