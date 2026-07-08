---
name: handbook-image-assets
description: Generate, validate, and wire travel handbook image assets for this repository. Use when working on Japan travel handbook route images, watercolor/cutout/sticker assets, route-specific prompts, saiai image generation, handbook-assets public paths, or avoiding 413 payload errors in the project's image workflow.
---

# Handbook Image Assets

## Core Rule

Use the repository's saiai Responses API wrapper, not raw image API calls.

Known-good setup:

- Endpoint: `https://api.saiai.top/v1/responses`
- Wrapper: `scripts/generate_handbook_image_saiai.py`
- Host model: `gpt-5.4`
- Tool: `image_generation`
- Do not use `/v1/images/generations`
- Do not use `gpt-5` as the default host model on saiai; it can 502 even when the key and endpoint are valid.

Small assets such as food cutouts, stickers, stamps, texture details, and tiny storefront accents should usually be saved at max edge `1024` for restaurant-page print/layout use.

```powershell
.\.venv\Scripts\python.exe .\scripts\generate_handbook_image_saiai.py `
  --model gpt-5.4 `
  --prompt-file <route>\prompts\<asset>.txt `
  --size 1024x1024 `
  --quality medium `
  --max-payload-mb 1.0 `
  --max-output-mb 1.0 `
  --max-output-edge 1024 `
  --out <route>\generated\<asset>.png
```

Large spread or half-page images should stay around `1024` on the long side.

```powershell
.\.venv\Scripts\python.exe .\scripts\generate_handbook_image_saiai.py `
  --model gpt-5.4 `
  --prompt-file <route>\prompts\<asset>.txt `
  --size 1024x1536 `
  --quality medium `
  --max-payload-mb 1.0 `
  --max-output-mb 1.0 `
  --max-output-edge 1024 `
  --out <route>\generated\<asset>.png
```

Do not call `/v1/images/generations`. Do not hand-roll Responses API JSON. The script reads `SAIAI_BASE_URL` and `SAIAI_API_KEY` from environment or project `.env`; never write keys into docs, prompts, commands, or chat.

Use `gpt-5.4` as the default host model for saiai image-generation tool calls. On this provider, `gpt-5` can return upstream 502 even when the same key and Responses endpoint are valid.

`gpt-5.5` may be tried only if `/v1/models` lists it or the user explicitly asks to test it. If it is not listed, prefer `gpt-5.4`.

## 413 Avoidance

Treat 413 as two separate risks:

- API 413: request body is too large, usually from reference images after base64 expansion.
- Chat/window 413: too many large images were embedded or opened in the conversation preview.

For visual browsing, build a thumbnail review board before opening or attaching images:

```powershell
.\.venv\Scripts\python.exe .\scripts\build_image_review_board.py `
  <image-dir-or-files> `
  --out-dir _tmp\<task>-image-review `
  --recursive `
  --max-edge 420 `
  --quality 72 `
  --cols 3 `
  --cell 320
```

Review `_tmp\<task>-image-review\contact_sheet.jpg` or `index.html` first. Do not embed many full-size PNGs in chat. Open a full-size image only after narrowing to one specific candidate.

Prefer this order:

1. Use `--max-payload-mb 1.0` for normal small handbook assets. Use `0.75` when a proxy/window is flaky.
2. Send no reference images for simple food/cutout assets unless identity must be preserved.
3. Send at most one scene reference `A` plus one style reference `B`.
4. Keep prompt files short; do not paste an entire brief into a prompt.
5. Generate stickers/cutouts at `1024x1024`, then save with `--max-output-edge 1024`. Generate vertical page art at `1024x1536`, then save with `--max-output-edge 1024`. Generate horizontal page art at `1536x1024`, then save with `--max-output-edge 1024`.
6. If 413 still happens, rerun with fewer `--image` arguments before changing artistic prompt or output size.

Output `--size` controls the generated image dimensions. It can affect generation cost, but it is not the main cause of upload 413; uploaded reference images and prompt length dominate request size.

Use `--max-output-edge 1024 --max-output-mb 1.0` for restaurant cutouts, stickers, large spread, and half-page artwork unless the asset is truly icon-sized. Only use `256` for smoke tests or tiny UI thumbnails.

The project script already downscales reference images and measures JSON payload locally. A healthy run prints a line like:

```text
payload=... MB, ref_max_edge=..., ref_jpeg_quality=...
```

Successful image generation prints:

```text
status=200
saved=... bytes=... raw_bytes=... output_optimization=...
```

For API smoke tests, do not open the image unless visual quality matters. It is enough to verify:

- `status=200`
- the saved file exists
- PIL can open it
- dimensions and mode match the requested asset class

If a request returns 502 while `/v1/models` works, switch/check the host model first. `gpt-5.4` is known-good; `gpt-5` may fail with upstream 502.

## Asset Workflow

For each route, read the local route docs first:

- `image_generation_brief.md` for the route's visual plan.
- `generate_images.md` for known-good commands.
- `prompts/*.txt` for the actual prompt files.
- `reference_index.md` when choosing reference images.

For general policy, load `references/handbook-image-sop.md` only when needed. For the Osaka Castle to Namba route, load `references/osakajo-namba-generate-images.md`. For the restaurant page cutout task, load `references/restaurant-page-image-prompts.md`.

Final project assets should exist under both appropriate locations when the frontend needs public access:

```text
japan/kansai/assets/routes/{city}/{route_id}/generated/
web/public/handbook-assets/{city}/{route-slug}/...
```

Do not leave final project assets only in temp folders.

## Prompt Discipline

Generate standalone image assets, not a finished journal page.

Prompts should say the image is "for placement into a printed travel journal layout as an image asset." Avoid asking for a book, open journal, page mockup, multi-panel sheet, captions, readable fake text, logos, or watermark.

Keep prompt files short and operational. For gpt-image-2 / saiai image-generation tool calls, prefer a compact asset spec over a long creative brief:

- 1 line for asset purpose.
- 1-2 lines for subject and composition.
- 2-4 bullets for style constraints.
- 1 short avoid line.

Do not paste the whole page brief, product rationale, or long reference analysis into the prompt. Long prompts tend to dilute the main visual instruction, increase payload risk, and make iterations harder to diagnose. Put research notes and rationale in `source_notes.md`; put only the final visual instruction in `prompts/*.txt`.

When iterating, change one thing at a time and keep the rest of the prompt stable. If the result is wrong, write a targeted follow-up prompt instead of rewriting the whole prompt from scratch.

For transparent/cutout-like assets in this repo, prefer actual transparent PNGs when available. If the generator cannot produce true alpha, create a clean flat-background source, remove the background locally, validate alpha, then copy the final PNG into the public asset path.

## Wiring

After generating assets:

1. Inspect that files open and have nonzero dimensions.
2. For transparent PNGs, verify alpha channel and transparent corners.
3. Open/view the image only when doing visual quality review; API smoke tests can stay headless.
4. Copy selected assets into `web/public/handbook-assets/...`.
5. Replace temporary raw/fallback paths in the frontend.
6. Run the relevant build or render check.
