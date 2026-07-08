---
name: handbook-system-rendering
description: Frontend/system rendering workflow for Travel AI handbook pages. Use when Codex works on web/app/render pages, page-type prototypes, fixed layout rendering, Chinese text overlays, public handbook-assets paths, page export previews, build checks, or wiring simple AI assets into handbook pages.
---

# Handbook System Rendering

Use this skill after `travel-ai-workflow` classifies the task as system rendering: fixed frontend layout plus simple image assets plus system-rendered Chinese text.

## Boundary

This line owns page composition, not complex visual production.

Do:

- Render Chinese titles, labels, body text, lists, and route details in frontend/system code.
- Use AI images only as simple assets: cutouts, background details, blank bubbles, stickers, paper textures, small objects.
- Preview pages under `web/app/render/*`.
- Read final frontend assets from `web/public/handbook-assets/...`.

Do not:

- Ask image models to generate a finished Chinese handbook page.
- Solve brand style, map accuracy, or character design by CSS patching.
- Put prompts, source notes, reference images, or failed experiments in `web/public`.
- Change plan/template JSON just to satisfy a page layout issue.

## Minimal Reading

Default:

```text
_tmp/handoff/CURRENT_2_system_rendering.md
```

Then read only what the page requires:

- Page composition boundary: handbook rendering work layering.
- Asset path/publishing issue: asset directory spec.
- Typography/layout issue: layout system and typography system.
- Copy/visible Chinese issue: handbook copy spec.
- Daily page design: daily page type design.

For a specific page type, read only:

```text
render/page-types/{page_type}/README.md
web/app/render/{page}/page.tsx
```

Do not read all rendering SOPs by default.

## Asset Wiring

Source assets stay with their owner:

- Page-type assets: `render/page-types/{page_type}/...`
- Shared brand/texture assets: `render/shared/...`
- Route-owned assets: `japan/kansai/assets/routes/{city}/{route_id}/...`

Published frontend copies go under:

```text
web/public/handbook-assets/
```

Use source notes to record selected source, published copy, and consuming page. If an asset is missing, switch to `handbook-visual-production` or `handbook-image-assets` instead of inventing a fake path.

## Template Production (making or reworking a render template)

Follow `docs/操作SOP/上线前/手账/渲染模板生产流程.md`: 4 fixed communication checkpoints (align -> pick direction -> A/B converge -> final sign-off), AI closes the loop between checkpoints with screenshot self-check.

Hard rules:

- Every draft must pass the self-check list in `docs/操作SOP/上线前/手账/版式基线.md` before showing the user.
- A template is done only after content stress-test (3-5 extreme variants, no overflow/overlap) and golden baseline capture. One good-looking instance is not done.
- Never ask the user to describe design requirements; offer references, graded info tables, and A/B choices instead.

## Implementation Workflow

1. Identify the page and page type.
2. Confirm which content comes from data and which is static prototype copy.
3. Wire only lightweight public assets into the page.
4. Keep layout stable: fixed page dimensions, safe text wrapping, no overlapping text, no cards inside cards.
5. Keep Chinese text live/system-rendered unless the task explicitly concerns a raster-only image.
6. If the page needs new complex art, write the asset requirement and hand it to the visual production line.

## Verification

For frontend changes, run:

```powershell
cd web
npm run build
```

When visual correctness matters, also run a local preview and capture screenshots for the target viewport/page. Do not embed many full-size images in chat; use review boards for image comparison.

## Handoff

Record current page status, asset source/public paths, verification, and the next concrete page task in `_tmp/handoff/CURRENT_2_system_rendering.md`.
