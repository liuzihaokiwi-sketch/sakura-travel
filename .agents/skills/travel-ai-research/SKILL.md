---
name: travel-ai-research
description: Research workflow for the D:/projects/projects/travel-ai repository. Use when Codex needs to research destinations, routes, seasons, transport, restaurants, hotels, traveler feedback, competitor examples, Xiaohongshu/opencli notes, recommendations, current facts, or evidence that must be saved into research/ and turned into product conclusions.
---

# Travel AI Research

Use this skill after `travel-ai-workflow` classifies the task as research, data-backed route judgment, current fact checking, Xiaohongshu review, or source collection.

## Core Rule

Separate evidence from conclusions:

- Evidence, source notes, conflicts, and process go under `research/`.
- Product conclusions go back to the formal object, such as `japan/kansai/templates/**/动线说明.md`, data pools, `render/**/source_notes.md`, or `marketing/**`.
- Do not write inferred facts as confirmed facts. Search or mark them unverified.

## Minimal Reading

Default to the handoff route, then read only the object files named by that handoff or by the user:

```text
_tmp/handoff/CURRENT_1_content_assembly.md
```

Read formal docs only when they are directly needed (real paths):

- Research method: `docs/操作SOP/上线前/研究方法.md` — when starting a new research object or changing standard.
- `research/README.md` / `research/japan/kansai/README.md`: when unsure where evidence belongs.
- `opencli` SOP: `docs/操作SOP/opencli使用.md` — only when using Xiaohongshu/opencli.
- Target route/template files: only for the current route.

Do not read all route files, historical handoffs, or archived handoff files by default. **Worked deposits (Kansai scoring rubric, Italy hard-reservation action calendar) + evidence-location conventions are in `examples.md`.**

## Research Workflow

1. Define the object and decision: route, season, restaurant, hotel, map, page type, marketing topic, or user pain point.
2. Search at least the source classes required by the object:
   - Official or factual source for hours, tickets, closures, prices, access, rules.
   - Curated/deep source for route logic and experience quality.
   - Real traveler feedback for queues, disappointment points, confusion, and Chinese-user fit.
3. Record evidence in the narrowest reusable location:
   - `research/global/` for project-wide behavior.
   - `research/japan/kansai/region/`, `seasonal/`, or `transport/` for shared Kansai findings.
   - `research/japan/kansai/routes/{route_id}/` for route decisions.
   - `research/render/` for visual, page-type, and map research.
4. Write a conclusion that states keep/delete/admit/trigger/downgrade/fact ownership.
5. Move only the final conclusion into the formal object directory.

## Xiaohongshu / opencli

Use `opencli` for Xiaohongshu evidence and marketing examples. Run from:

```powershell
cd D:/projects/projects/travel-ai/opencli-main
node dist/main.js xiaohongshu search "关键词" --limit 10 --format md
node dist/main.js xiaohongshu note "完整URL" --format md
node dist/main.js xiaohongshu download "完整URL" --output "D:/tmp/xhs_refs/..."
```

Hard rules:

- `note`, `download`, and `dump-state` run serially. Parallel calls can mix outputs.
- Use full URLs with `xsec_token`; note IDs alone are unreliable.
- Treat `collects` as stronger long-term intent than likes.
- Xiaohongshu is traveler feedback and trend evidence, not an authoritative fact source.
- Downloaded reference media must be sorted into `research/`, `render/references/`, or object `references/`; never directly into `web/public`.

## Marketing Link

During research, save reusable operating material:

- Viral note structures and topic angles: `marketing/{region}/爆款参考.md`
- Local insights, pain points, hidden details, and story hooks: `marketing/{region}/素材库.md`

Do this only when the material can support product trust or content distribution.

## Verification

Before finishing, confirm:

- Evidence file path exists and is named for the researched object.
- Current facts have source attribution or are marked unverified.
- Final conclusion was written to the formal object, not only to `research/`.
- Any follow-up task is short enough for `_tmp/handoff/CURRENT_*`.
