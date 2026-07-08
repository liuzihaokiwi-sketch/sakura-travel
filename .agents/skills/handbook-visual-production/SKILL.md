---
name: handbook-visual-production
description: Complex visual production workflow for Travel AI handbook assets. Use when Codex works on maps, S-level spread pages, Kiwi or Logo style, watercolor/cutout/sticker systems, visual references, source_notes, review boards, render/ assets, or preparing final assets for web/public/handbook-assets.
---

# Handbook Visual Production

Use this skill after `travel-ai-workflow` classifies the task as complex visual rendering. Use `handbook-image-assets` alongside it when actually generating or processing images.

## Boundary

This line produces visual assets for the handbook. It does not implement frontend page layout and does not create finished Chinese pages as raster images.

Owns:

- Maps and map layers.
- S-level route spread pages.
- Kiwi, Logo, brand marks, actions, watercolor and paper style systems.
- Reference image curation, review boards, prompts, generated candidates, selected sources.
- Asset source notes and public copy handoff.

Does not own:

- Live Chinese text rendering in pages.
- Plan/template route logic.
- Long-term research conclusions unrelated to visual production.

## Minimal Reading

Default:

```text
_tmp/handoff/CURRENT_3_visual_rendering.md
```

Then read only the matching asset docs:

- Asset ownership/public copy: asset directory spec.
- Image generation/prompting: handbook image generation guide.
- Render workspace uncertainty: `render/README.md`.

For maps, read only:

```text
render/maps/map_generation_workflow.md
```

For S-level spreads, read only:

```text
japan/docs/旅行手账装帧与大通页设计.md
japan/kansai/assets/s_spot_spread_asset_list.md
japan/kansai/assets/s_spot_spread_collection_plan.md
```

Do not read all visual docs or all reference groups by default.

## Directory Rules

Put source assets with the object:

- Maps: `render/maps/{map_id}/`
- Page-type visual systems: `render/page-types/{page_type}/`
- Shared brand assets: `render/shared/brand/`, `render/shared/logos/`, `render/shared/textures/`
- Visual references: `render/references/{reference_group}/`
- Route spread pages: `japan/kansai/assets/routes/{city}/{route_id}/spread_pages/{spot_slug}/`

Inside object directories, prefer:

```text
references/
prompts/
generated/
public/
_tmp/
source_notes.md
```

`web/public/handbook-assets/` contains only lightweight files the frontend reads. Never put prompts, `source_notes.md`, reference images, or failed experiments there.

## Image Review

Before browsing many images, build a review board:

```powershell
.\.venv\Scripts\python.exe .\scripts\build_image_review_board.py `
  <image-dir-or-files> `
  --out-dir <object-dir>\_tmp\review `
  --recursive `
  --max-edge 420 `
  --quality 72 `
  --cols 3 `
  --cell 320
```

Review `contact_sheet.jpg`, `index.html`, and `manifest.json` first. Open a full-size image only after narrowing to a specific candidate.

## Production Workflow

1. Identify the asset owner and create/inspect the object directory.
2. Collect 1-3 relevant references; use cropped/small references when possible.
3. Write or update `source_notes.md` with source, selected version, public path, and consuming page.
4. Keep prompts short and asset-focused: standalone image asset, no finished page mockup, no readable text.
5. Use `handbook-image-assets` for saiai generation, 413 control, alpha validation, and cutout processing.
6. Select, compress/copy, and publish only final lightweight assets to `web/public/handbook-assets/...`.
7. If a frontend page consumes the asset, hand off exact public path to `handbook-system-rendering`.

## Map Rule

For accurate transport maps, prefer bottom map/art layer plus SVG line/label/legend layers. For sasi-style atmosphere maps, generated art can be used only with structure references and a checklist against real geography.

## Handoff

Record selected asset, source directory, public path, verification, and next visual decision in `_tmp/handoff/CURRENT_3_visual_rendering.md`.
