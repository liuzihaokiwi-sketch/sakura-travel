# 后台运行流程

> 请求进 API 到 PDF 出来之间,代码真实的调用顺序。

## 主链路

```
POST /v2/trips
  ↓
创建 TripRequest → 入队 generate_trip job
  ↓
─── 装配阶段 ───
读表单约束 → 硬筛候选池(模板+实体) → Opus 装配 → 输出方案草稿
  ↓
GET /v2/trips/{id}/plan-preview
  ↓
─── 用户纠偏(可选多轮) ───
POST /v2/trips/{id}/plan-actions
  ↓
应用 action → 局部/全量重装配
  ↓
POST /v2/trips/{id}/plan-confirm
  ↓
─── 预算阶段 ───
GET /v2/trips/{id}/budget-options → 吐三档
POST /v2/trips/{id}/budget-confirm → 选定档位
  ↓
─── 渲染阶段 ───
装配输出 → 页型映射 → magazine 排版 → PDF
  ↓
job 完成,通知客服发货
```

## 每一步对应什么

| 运行步 | 代码入口 | 文档 |
|---|---|---|
| 入队 | [app/api/trips_v2.py](../app/api/trips_v2.py) | — |
| 装配（第一步）| [app/workers/jobs/generate_plan_preview.py](../app/workers/jobs/generate_plan_preview.py) | [SCHEMA.md](SCHEMA.md) §1.3 `when` 字段 |
| 装配（第二步）| [app/workers/jobs/generate_handbook_final.py](../app/workers/jobs/generate_handbook_final.py) | — |
| 候选池硬筛 | [app/domains/planning_v2/opus_assembler.py](../app/domains/planning_v2/opus_assembler.py) | [SCHEMA.md](SCHEMA.md) §1.3 `when` 字段 |
| 纠偏 | trips_v2.py `plan-actions` 端点 | [intake/plan_confirm_spec.md](intake/plan_confirm_spec.md) |
| 预算 | [app/domains/planning_v2/budget_calculator.py](../app/domains/planning_v2/budget_calculator.py) | [../content/kansai/policy.json](../content/kansai/policy.json) |
| 渲染 | [app/domains/rendering/](../app/domains/rendering/) | [page_system/](page_system/) |
| Worker 入口 | [app/workers/jobs/generate_trip.py](../app/workers/jobs/generate_trip.py) | — |

## 事实源的位置

运行期读取的"活数据",不是代码也不是文档:

| 事实源 | 位置 | 谁读 |
|---|---|---|
| L0 事件(樱花/红叶/祭典) | [../data/events/](../data/events/) | 装配(判断 `when.event_ref`) |
| 票价/营业时间/预约 | [../content/kansai/live_facts/](../content/kansai/live_facts/) | 渲染(填进手账本) |
| 模板库 | `content/<circle>/<city>/days/` 目录 | 装配 |
| 内容池(景点/餐厅/酒店/店铺) | `content/<circle>/<city>/*.json` | 装配 |
