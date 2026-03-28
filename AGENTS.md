# AGENTS

## Project Definition

AI 旅行手账生成系统：用户填表 → 结构化决策 → 60页手账本 → PDF 交付。

Not a one-shot LLM itinerary writer. Not Japan-only. Not a standalone site.

## Truth Source Order

1. `docs/ARCHITECTURE.md` — 系统全景
2. `docs/DECISIONS.md` — 关键决策记录
3. `docs/STATUS.md` — 当前状态 + 剩余工作
4. `docs/city_circles/` — 城市圈结构定义
5. `docs/page_system/` — 页面系统规范

## Current Boundary

- Six city circles: Kansai, Kanto, Hokkaido, Guangfu (广府), Northern Xinjiang, Guangdong
- Delivery: 60-page travel handbook (paper + sticker DIY pack)
- Intake priority: Douyin form, not standalone site
- Pricing: ¥298 domestic / ¥348 international
- No flight service: users book flights themselves, system only takes landing/departure times
- No deep price comparison: only entity-level value-for-money in hotel/restaurant selection, no cross-day route optimization

## Main Chain

```
表单输入 → 归一化 → 城市圈决策链 → 页面生成 → PDF渲染 → 交付
```

Key files:
- `app/workers/jobs/generate_trip.py` — main orchestrator
- `app/domains/rendering/planning_output.py` — decision chain → page data (no report intermediate)
- `app/domains/rendering/page_planner.py` — 17 page types + budget trim
- `app/domains/rendering/copy_enrichment.py` — optional AI copy

## Deleted Modules (do not reference)

- `app/domains/planning/report_generator.py` — replaced by planning_output.py
- `app/domains/rendering/layer2_handoff.py` — eliminated
- `app/domains/planning/assembler.py` — replaced by city-circle pipeline
- `app/domains/rendering/renderer.py` — replaced by magazine/
- `app/domains/flights/` — removed (no flight service)

## Communication Default

- Keep progress updates minimal
- Content for end users defaults to Chinese
- Internal technical docs may use English

## Task Handling

- Handle fast tasks directly
- For complex tasks: classify difficulty, plan, then execute
- Prefer direct replacement over compatibility layering
- Let runtime paths fail explicitly when appropriate
