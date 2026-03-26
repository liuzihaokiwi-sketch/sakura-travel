# AGENTS

## Project Definition

This repository is a travel decision and handbook delivery system, not a one-shot LLM itinerary writer.

Its stable end-to-end shape is:

- lead capture / sample preview / paid detail form intake
- decision and orchestration
- page-based rendering
- PDF/H5 handbook delivery
- evaluation, review, feedback, and operational loop

## Truth Source Order

When documents disagree, use the following order:

1. `docs/architecture/00_scope_and_truth.md`
2. `docs/architecture/02_target_architecture.md`
3. `docs/architecture/01_current_state.md`
4. `docs/architecture/03_gap_and_priorities.md`
5. `docs/architecture/04_execution_staging.md`
6. older topic documents under `docs/`

Older documents are still useful as historical design input, but they are no longer the top-level source of truth once the `docs/architecture/` set exists.

## Deprecated Assumptions

The following old assumptions are no longer valid as default premises:

- the system only targets Japan
- the current primary entry point is a standalone website
- the final output is just a long-form travel report
- the current task is to fully refactor the codebase
- the codebase is still only at concept stage

If older files use these assumptions, treat them as historical-phase statements, not current truth.

## New Boundary Changes

The current planning boundary changes multiple layers at once:

- scope layer: destination scope is now six city circles, not Japan-only
- intake layer: current acquisition priority is Douyin form intake, not standalone site completeness
- delivery layer: output is a 60-page travel handbook with image / illustration slots
- rendering layer: rendering must serve page semantics and visual slots, not only long report flow
- configuration layer: rules must become city-circle-aware rather than Japan-core-city-only

The six city circles are:

- Kansai city circle
- Kanto city circle
- Hokkaido city circle
- South China five-city circle
- Northern Xinjiang city circle
- Guangdong city circle

## Persistent Gaps

The following gap inventory remains valid and must not be lost:

- old and new decision chains coexist
- old and new rendering chains coexist
- truth sources are distributed across files
- quality and operations are still attached in a distributed way

These are architecture facts, not short-term task items.

## Current-Stage Rule

The current stage is documentation consolidation and truth-source unification first.

Do not default to:

- large-scale code refactor
- deep implementation scheduling
- standalone-site-first planning
- Japan-only framing

The reason is simple: the current risk is not just missing code, but conflicting boundaries, mixed planning assumptions, and scattered truth sources. Changing code before stabilizing these files would harden obsolete assumptions into implementation.

## Handling Old and New Chains

When describing the system, always acknowledge coexistence:

- old decision chain: `assemble_trip` and template-driven assembly
- new decision chain: city-circle-based staged orchestration
- old rendering chain: old renderer and long-template flow
- new rendering chain: `chapter_plan -> page_plan -> page_view_model -> render adapters`

Do not describe either migration as already complete unless code and truth-source files are explicitly aligned.

## Communication Default

- keep progress updates minimal
- report only at key milestones, before high-risk modifications, when blocked, and in final summary
- do not repeat background or already-confirmed constraints

## Language Default

- content shown to users defaults to Chinese
- content generated for end users defaults to Chinese
- internal technical documentation may remain in English only when it is more practical for agent maintenance

## Task Handling Default

- handle fast tasks directly
- for complex tasks, classify by difficulty first, record the task shape, then route to a more suitable AI / model path
- do not enter large-scale code modification before truth-source documents and planning are aligned

## Document Update Rules

When adding or updating planning documents:

- state which old assumptions are deprecated
- state which layers changed under the new boundary
- state which previous gaps remain valid
- state why the current phase still prioritizes file and planning cleanup before broad code change

If a file cannot answer these four questions, it is not complete enough to serve as current planning documentation.
