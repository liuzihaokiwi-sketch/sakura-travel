# AGENTS

## Project Definition

AI 旅行手账生成系统：用户填表 → 模板规则拼装 → 用户确认 → 预算选择 → 60页手账本 → PDF 交付。

Not a one-shot LLM itinerary writer. Not Japan-only. Not a standalone site.

## Truth Source Order

1. `content/kansai/brief.md` -- 产品原则（唯一原则文档）
2. `content/kansai/policy.json` -- 硬约束（程序检查用）
3. `content/kansai/form_design.md` -- 表单与确认页设计
4. `docs/DECISIONS.md` -- 关键决策记录
5. `docs/data-engineering/MASTER_GUIDE.md` -- 数据采集唯一执行文档
6. `docs/page_system/` -- 页面系统规范

## Current Boundary

- Six city circles: Kansai, Kanto, Hokkaido, Guangfu, Northern Xinjiang, Guangdong
- Delivery: 60-page travel handbook (paper + sticker DIY pack)
- Intake: 4-screen form → plan preview → budget confirm
- Pricing: ¥298 domestic / ¥348 international
- No flight service: users book flights themselves
- No deep price comparison

## Main Chain (v2 — 模板引擎)

```
4屏表单 → TemplatePlanner(规则拼装) → plan_preview → 用户纠偏 → plan_confirm → BudgetCalculator → budget_confirm → 手账本渲染
```

Key files:
- `app/api/trips_v2.py` -- 7 API endpoints `/v2/trips`
- `app/domains/planning_v2/template_planner.py` -- 纯规则方案生成
- `app/domains/planning_v2/budget_calculator.py` -- 预算计算
- `app/domains/templates/loader.py` -- 模板数据读取
- `content/kansai/` -- 模板数据目录

## Legacy Chain (16步管线，代码仍存在)

```
表单输入 → 归一化 → 16步行程规划管线 → 页面生成 → PDF渲染 → 交付
```

Key files:
- `app/workers/jobs/generate_trip.py` -- main entry, USE_PLANNING_V2 flag
- `app/domains/planning_v2/orchestrator.py` -- 16-step orchestrator
- `app/domains/rendering/planning_output.py` -- decision chain → page data
- `app/domains/rendering/page_planner.py` -- 17 page types + budget trim

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
