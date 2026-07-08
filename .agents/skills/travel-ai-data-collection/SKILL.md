---
name: travel-ai-data-collection
description: Data collection workflow for the D:/projects/projects/travel-ai repository. Use when Codex collects, verifies, edits, or validates factual pools for entities, restaurants, hotels, stops, shops, opening hours, prices, coordinates, ratings, reservations, data source evidence, or production-ready JSON data.
---

# Travel AI Data Collection

Use this skill for factual data pools. Use `travel-ai-research` when the task is mainly route judgment, destination insight, or evidence synthesis.

## Core Rule

AI may make judgments from evidence, but must not invent facts. If a value can be checked in a real source, search or leave it null/unverified.

## Minimal Reading

Read only the current pool and its matching spec (real paths):

- entity task: `docs/操作SOP/上线前/数据池构建/entity规范.md` + target `japan/kansai/entities/{city}.json`.
- stops task: `docs/操作SOP/上线前/数据池构建/stops规范.md` + target `japan/kansai/stops/*`.
- restaurant task: `docs/操作SOP/上线前/数据池构建/餐厅规范.md` + target `japan/kansai/restaurants/{city}/{area}.json`.
- hotel task: `docs/操作SOP/上线前/数据池构建/酒店规范.md` + target `japan/kansai/hotels/{city}.json`.
- new field/schema task: `docs/项目核心/字段权威.md` (edit this FIRST, before any pool file).
- search-method task: `docs/操作SOP/上线前/数据池构建/搜索方法.md`; demand-driven adds: `需求验证.md`.

Do not read every data-pool spec by default. **Worked records + the authoritative field whitelists are in `examples.md` — read it before adding fields, to avoid inventing non-existent ones (e.g. restaurant records have NO `可信度`/`recommend_reason`).**

## Data Locations

```text
japan/kansai/entities/
japan/kansai/restaurants/
japan/kansai/hotels/
japan/kansai/stops/
japan/kansai/area_registry.json
research/japan/kansai/
marketing/japan/kansai/素材库.md
```

Use `research/` for evidence/process that should not become production fields. Add marketing hooks only when a finding has real传播价值.

## Workflow

1. Identify the pool and target area.
2. Read the matching schema/spec and existing nearby records.
3. Gather real evidence from the right source class:
   - Official/Google Maps/site data for hours, address, closure, reservation, access.
   - Tabelog/official/Michelin/Rakuten/booking sources as appropriate for quality signals.
   - Xiaohongshu/Ctrip/real traveler feedback for Chinese traveler fit.
4. Write production fields only when the source supports them.
5. Keep editorial judgment concise and durable; do not fill weak records with generic praise.
6. Run the matching validator.

## Validation

Validators take a target path (file or pool dir). Run against the whole pool dir before finishing:

```powershell
.\.venv\Scripts\python.exe scripts\validate_entity.py       japan\kansai\entities
.\.venv\Scripts\python.exe scripts\validate_restaurants.py  japan\kansai\restaurants
.\.venv\Scripts\python.exe scripts\validate_hotels.py       japan\kansai\hotels
```

Paste the full output (the `合计: N … , M errors` line) — do not claim it passed without it. A `pre-commit` hook (`scripts/git-hooks/pre-commit`, enabled via `core.hooksPath`) also runs these on commit and blocks schema errors. For template-linked changes, also use `travel-ai-content-assembly` validation.

## Red Lines

- Do not fabricate scores, coordinates, hours, price bands, closures, or reservation rules.
- Do not use `ai_generated` facts in production.
- Do not add fields before checking `docs/项目核心/字段权威.md`.
- Do not promote a record only because it is famous; traveler fit and execution risk matter.
