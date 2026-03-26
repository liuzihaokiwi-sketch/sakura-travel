# Same-Source Lockdown — 同源锁死 + 硬失败护栏

## 问题

回归报告 67/67 PASS，但最终 PDF 可能来自另一次运行的 plan_id。
链路中 run_id 不存在，plan_id 仅在片段中传递，回归/导出/护栏三阶段之间无强一致校验。
hard constraint 在 trace 中可能停留在 `pending` 状态直接落库。

## 目标

1. 单次运行唯一标识 `run_id` 贯穿全链路
2. 每次生成产出结构化"证据包"（evidence bundle）
3. 回归报告与 PDF 强制同源：plan_id / run_id 不一致 → fail
4. 护栏真拦截：hard constraint unconsumed → fail
5. constraint_trace finalize：不允许 pending 落库
6. 新增同源核对回归项
7. 精选 10 个黄金 case 做端到端验证

## 不做

- 不碰 UI / renderer 样式
- 不重写排序权重
- 不大量新增文案断言
- 不做大重构
