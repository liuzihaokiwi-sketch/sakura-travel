# AGENTS

## Project Definition

AI 旅行手账生成系统：用户填表 → 候选池硬筛 → Opus 装配 → 用户确认 → 预算选择 → 60页手账本 → PDF 交付。

Not a one-shot LLM itinerary writer. Not Japan-only. Not a standalone site.

## Truth Source Order

1. `content/kansai/brief.md` -- 产品原则（唯一原则文档）
2. `content/kansai/policy.json` -- 硬约束（程序检查用）
3. `docs/intake/` -- 表单与确认页设计
4. `docs/SCHEMA.md` -- **字段唯一权威源**(任何字段变动先改这里)
5. `docs/DECISIONS.md` -- 关键决策记录
6. `docs/templates/` -- 模板系统(模板/内容池/季节)
7. `docs/data-engineering/` -- 数据工程文档(方法论/数据源/采集流程/工具),入口见 `docs/data-engineering/README.md`
8. `docs/page_system/` -- 页面系统规范
9. `docs/ops/` -- 运营手册 + 服务流程

## Current Boundary

- Six city circles: Kansai, Kanto, Hokkaido, Guangfu, Northern Xinjiang, Guangdong
- Delivery: 60-page travel handbook (paper + sticker DIY pack)
- Intake: 4-screen form → plan preview → budget confirm
- Pricing: ¥198 domestic / ¥228 international (前期优惠), 后期 +¥70
- No flight service: users book flights themselves
- No deep price comparison

## Main Chain (v2 — 模板 + Opus 装配)

```
4屏表单 → 候选池硬筛(规则) → Opus 装配(最终决策) → plan_preview → 用户纠偏 → plan_confirm → BudgetCalculator → budget_confirm → 手账本渲染
```

决策主体：**Opus 是最终决策者**。规则只做候选池硬筛（`when` 触发、vibe/人群匹配、`core_entities` 去重），"一天里走哪几个景点、配哪家餐厅、住哪家酒店、story 怎么写"由 Opus 读模板 + 内容池自然语言字段判断。详见 [docs/DECISIONS.md](docs/DECISIONS.md) D28/D31。

Key files:
- `app/api/trips_v2.py` -- 7 API endpoints `/v2/trips`
- `app/domains/planning_v2/opus_assembler.py` -- Opus 两步装配（路线+酒店 / 配餐）
- `app/domains/planning_v2/budget_calculator.py` -- 预算计算
- `app/domains/templates/loader.py` -- 模板数据读取
- `app/workers/jobs/generate_plan_preview.py` -- Job: Opus 第一步
- `app/workers/jobs/generate_handbook_final.py` -- Job: Opus 第二步
- `content/kansai/` -- 模板数据目录

## Legacy Chain

16步管线已废弃，代码在 `_deprecated/planning_v2_scaffold/`。

## Deleted Modules (do not reference)

- `app/domains/planning/report_generator.py` -- replaced by planning_output.py
- `app/domains/rendering/layer2_handoff.py` -- eliminated
- `app/domains/planning/assembler.py` -- replaced by city-circle pipeline
- `app/domains/rendering/renderer.py` -- replaced by magazine/
- `app/domains/flights/` -- removed (no flight service)

## Communication Default

- Keep progress updates minimal
- Content for end users defaults to Chinese
- Internal technical docs may use English

## Task Handling

- Handle fast tasks directly
- For complex tasks: classify difficulty, plan, then execute
- Prefer direct replacement over compatibility layering
- Let runtime paths fail explicitly when appropriate
