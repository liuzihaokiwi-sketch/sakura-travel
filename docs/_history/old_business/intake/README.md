# intake — 表单与确认页系统

> 付费后填写。4 屏轻表单 → 方案确认页 → 预算确认页。
> 核心原则:用户付费买的是"专家替你决策",不是旅行编辑器。

## 完整流程

```
屏1:什么时候去
屏2:旅行感觉 + 几位出行
屏3:节奏
屏4:特殊情况(可跳过)
→ 系统生成方案
→ 方案确认页(行程 + 可加体验 + 纠偏)
→ 预算确认页(吃住档位 + 加购 + 总费用)
→ 确认下单,开始制作手账本
```

## 本模块文档

| 文件 | 内容 |
|---|---|
| [form_spec.md](form_spec.md) | 4 屏表单字段与交互 |
| [plan_confirm_spec.md](plan_confirm_spec.md) | 方案确认页 5 个区域 + 纠偏抽屉 |
| [budget_confirm_spec.md](budget_confirm_spec.md) | 预算确认页 UI(吃/住/加购/费用示例) |

## 相关但不在本模块

| 话题 | 去哪 | 原因 |
|---|---|---|
| 预算升降档混搭比例(内部计算逻辑) | [../templates/CONTENT_POOL_WRITING_GUIDE.md](../templates/CONTENT_POOL_WRITING_GUIDE.md) 餐厅预算档一节 | 是 BudgetCalculator 的规则,不是表单 UI |
| 客服根据表单字段发什么消息 | [../ops/SERVICE_FLOW.md](../ops/SERVICE_FLOW.md) | 客服的活,不是填表的活 |
| 默认方案生成规则(风格×条件表) | [../DEFERRED.md](../DEFERRED.md) 推迟项#1 | 装配引擎 Prompt 工程待落地 |
| 城市天数消耗表 | [../../content/kansai/policy.json](../../content/kansai/policy.json) | 硬约束文件 |

## 代码入口

- [app/api/trips_v2.py](../../app/api/trips_v2.py) — 7 个 `/v2/trips` 端点
