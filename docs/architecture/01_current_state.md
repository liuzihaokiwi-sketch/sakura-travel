# 01 Current State

## File Role

This file records the current repository reality.

It does not define the final target. It explains:

1. which old assumptions are still lingering in the repo
2. which layers are affected by the new boundary
3. which earlier gap findings remain valid
4. why the current phase is document consolidation before broad code change

## Current Code Reality

The repository already contains a working multi-layer system, not only planning documents.

Current code reality includes:

- FastAPI backend with intake, preview, order, form, generation, and review APIs
- worker jobs for generation, guardrails, and export
- old assembly-based planning path
- new staged planning modules around city-circle decisions
- old rendering path centered on the legacy renderer and long-template flow
- new rendering modules for chapter, page, page view model, and magazine renderers
- frontend pages for sample, preview, detail form, plan, pricing, and admin flows

This means the project is beyond concept stage, but not yet fully converged.

## Deprecated Assumptions Still Present In The Repo

Several deprecated assumptions still appear in the existing file set and code-facing planning:

### Japan-Only Framing

Many current documents still describe the system as Japan-first or Japan-only.

This was valid for the earlier phase, but it is no longer the current planning boundary.

### Standalone-Site-First Framing

Some growth and delivery documents still imply a standalone site as the primary front door.

Current phase priority is now form intake through Douyin traffic, not site-system completeness.

### Long-Report Framing

Part of the code and older rendering descriptions still operate in report vocabulary:

- long overview
- daily blocks
- long HTML template flow

The current target boundary is already a 60-page handbook with visual slots.

### Refactor-First Framing

Older execution thinking often slides toward "replace old code first".

That is not the current phase. Current phase is planning consolidation first.

## New Boundary Impact On Current State

### Product Delivery Layer

Current documents already include the 60-page handbook definition, but actual plan display and some renderer usage still reflect older report-style structures.

So delivery truth has moved ahead of some live presentation paths.

### Acquisition And Order Layer

Current code has workable quiz, submission, order, detail-form, and preview flows.

However, planning language is still mixed between:

- website page system
- sample preview
- backend form intake

The new boundary requires these to be interpreted with form intake as the present priority.

### Decision Layer

The code already has both:

- old `assemble_trip` template assembly
- newer staged planning modules

But the planning language around them is still mixed with earlier Japan-centered scope assumptions.

### Rendering Layer

The repo already includes chapter/page/view-model modules, so the rendering migration is not merely conceptual.

At the same time, legacy renderer paths remain active in the system.

### Quality And Operations Layer

Validation, guardrails, quality gate, review, and export checks exist, but they are still attached through multiple entry points rather than described and governed as one unified truth-source layer.

### Data And Config Layer

There is still no single consolidated truth-source file for:

- city-circle scope
- handbook delivery rules
- intake priority
- deprecated assumptions

That is precisely why this document set is needed.

## Still-Valid Gap Findings

The following previous findings remain valid and should be preserved:

### 1. Old And New Decision Chains Coexist

The repo still contains:

- old decision chain: `assemble_trip` and template-oriented assembly
- new decision chain: city-circle-based staged orchestration

This is a real current-state fact, not an outdated observation.

### 2. Old And New Rendering Chains Coexist

The repo still contains:

- legacy renderer and long-template flow
- newer `chapter_plan -> page_plan -> page_view_model -> render adapters` path

This coexistence is still active and still matters.

### 3. Truth Sources Are Distributed

Current planning truth is scattered across:

- older system documents
- layer-specific design documents
- handbook files
- code-facing maps

No single file previously expressed the latest boundary cleanly.

### 4. Quality And Operations Are Still Distributed

Validation, review, guardrails, export checks, and operational logic are present, but not yet described or governed under one unified current truth-source boundary.

## Which Earlier Gaps Need Reinterpretation Under The New Boundary

Some earlier gaps still exist, but they must now be read differently:

- Japan scope gaps must be rewritten as city-circle scope and configuration gaps
- rendering gaps must now be judged against handbook and visual-slot requirements
- acquisition gaps must now be judged against form-intake priority, not standalone-site completeness

## Why Current Phase Starts With File Consolidation

This phase starts with file and planning cleanup because the current mismatch is mostly at the level of:

- boundary definition
- scope definition
- truth-source location
- obsolete assumptions still being treated as current

If broad code changes started now, they would likely implement a mixed planning state:

- part Japan-only
- part six-city-circle
- part report-style
- part handbook-style
- part standalone-site-first
- part Douyin-form-first

That would increase code churn without reducing architectural ambiguity.

So current-state cleanup comes first:

- consolidate files
- stabilize the top-level truth source
- explicitly mark deprecated assumptions
- preserve still-valid gap findings under the new boundary

## Source Basis For This File

This file absorbs and reframes current-state evidence from:

- `docs/13_ai_codebase_map.md`
- `docs/11_api_dependency_map.md`
- `docs/01_system_core.md`
- `docs/Layer_2_决策与编排层实现方案_v1.md`
- `docs/Layer_3_报告与渲染层补充设计方案_v1.md`
- `docs/Layer_4_评测校验运营层修改建议_v1.md`
- `docs/travel_handbook_60p_for_engineer (1).md`
- current code structure under `app/` and `web/`
