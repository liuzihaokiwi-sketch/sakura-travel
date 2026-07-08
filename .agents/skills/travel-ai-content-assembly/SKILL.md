---
name: travel-ai-content-assembly
description: Content assembly workflow for the D:/projects/projects/travel-ai repository. Use when Codex works on Kansai plans, templates, route conclusions, resources.json, transport.json, entities, restaurants, hotels, stops, plan contracts, template validation, or user-visible itinerary content that feeds the handbook rendering layer.
---

# Travel AI Content Assembly

Use this skill after `travel-ai-workflow` classifies the task as content assembly, plan work, template work, transport/resource wiring, or fact-layer changes.

## Layer Boundaries

Keep each decision in its proper layer:

- `japan/kansai/plans/`: cross-day city order, stay pattern, form contract, route choice, optional tweaks.
- `japan/kansai/plans/catalog/`: candidate pools, seasonal pools, half-day pools.
- `japan/kansai/templates/{city}/{route}/N.json`: one day or half day of execution.
- `动线说明.md`: when to use the route, when not to use it, and why it exists.
- `entities/`, `restaurants/`, `hotels/`, `stops/`: facts and reusable resource data.
- `resources.json`: local resource linkage for a route.
- `transport.json`: machine-readable movement and display text for transport.

Do not put rendering logic, page styling, image paths, or CSS concerns into plan/template JSON.

## Minimal Reading

Default:

```text
_tmp/handoff/CURRENT_1_content_assembly.md
```

Then read only the target object and the one matching rule document (real paths):

- Plan/form work: `japan/kansai/plans/plan_layer_handoff.md` + `docs/项目核心/表单设计.md`.
- Template work: `docs/操作SOP/上线前/模板写作速查.md` (full: `docs/操作SOP/上线前/模板写作.md`).
- Field/schema change: `docs/项目核心/字段权威.md` + `docs/项目核心/当前生效决策.md`.
- Route judgment or current facts: switch to `travel-ai-research` and read only the target route research.

Read the full template SOP only when the quick reference is not enough. Do not read all content docs for every task. **Worked layer-routing + template-schema examples are in `examples.md`.**

## Workflow

1. Identify the target object: plan file, template file, route directory, data pool item, `resources.json`, or `transport.json`.
2. Check the current route conclusion and research before changing user-visible itinerary logic.
3. Make the smallest layer-correct change.
4. If a new field or enum is needed, update `docs/项目核心/字段权威.md` first.
5. If the work changes rendering needs, describe the need for the rendering line instead of encoding it into template JSON.

## Template Rules

Use current template shape:

- Required top-level fields: `template_id`, `applicable_dates`, `note`, `slots`.
- Optional only when needed: `variant_label`, `contingencies`.
- Half-day only when needed: `default_duration_option`, `duration_options`, `copy_variants`, `nearby_food`.
- Slots must be time-ordered; each `main` must contain at least one item.
- Use `free_time` for real open time; do not leave empty slots.
- `meal` uses `meal_type` and `meal_area`, not a fixed restaurant.
- `hotel` does not point to a fixed hotel entity.
- Template notes explain route-specific execution, not point encyclopedias.

Do not reintroduce deprecated fields listed in `模板写作速查.md`.

## Validation

Run when templates, plans, transport validation, or plan contract behavior changes:

```powershell
.\.venv\Scripts\python.exe scripts\validate_template.py japan\kansai\templates
.\.venv\Scripts\python.exe -m pytest app\tests\test_plan_contract.py -q
```

If only a data-pool file changes, run the matching validator when available:

```powershell
.\.venv\Scripts\python.exe scripts\validate_entity.py
.\.venv\Scripts\python.exe scripts\validate_restaurants.py
.\.venv\Scripts\python.exe scripts\validate_hotels.py
```

## Handoff

Record only current status, next step, key paths, validation run, and blockers in `_tmp/handoff/CURRENT_1_content_assembly.md`.
