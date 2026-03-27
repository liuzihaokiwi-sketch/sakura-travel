# 00 Scope And Truth

## File Role

This file is the top-level boundary and truth-source definition for the current project phase.

It answers four questions:

1. which old assumptions are no longer valid
2. which layers changed under the new boundary
3. which previous gap findings still remain valid
4. why the current phase is document and planning consolidation first

## Current System Definition

The system is defined as a complete travel handbook system:

- acquisition sample and intake
- form-based structured collection
- decision and orchestration
- page-based rendering
- PDF/H5 delivery
- evaluation, review, and feedback loop

It is not defined as a single LLM directly writing a travel guide from scratch.

## Deprecated Assumptions

The following old assumptions are now deprecated:

- "the product is Japan-only"
- "the current main line is building the standalone site"
- "the output is a normal long report or simple strategy deck"
- "the current phase should start from broad code refactor"
- "the project is still mainly conceptual and not yet structurally implemented"

These assumptions may still appear in older documents. When they do, treat them as phase-history statements.

## New Boundary

### Destination Scope

The destination boundary now expands from Japan-centric planning to six city circles:

- Kansai city circle
- Kanto city circle
- Hokkaido city circle
- South China five-city circle
- Northern Xinjiang city circle
- Guangdong city circle

This means "city circle" becomes the target planning abstraction, replacing the old default of "Japan core cities".

### Delivery Definition

The delivery target is now a 60-page travel handbook with image / illustration slots.

This replaces the old default framing of:

- long-form report
- simple itinerary deck
- plain HTML/PDF export without visual slot semantics

### Acquisition Priority

The current entry priority is:

- Douyin traffic
- form submission
- backend intake and generation

The standalone site is not the current primary strategic line.

This does not mean the web code is useless. It means current truth-source planning should prioritize form intake over site-system completeness.

## New Boundary Impact By Layer

### Product Delivery Layer

Changed from long-report framing to handbook framing.

The system must now describe:

- fixed page semantics
- page families
- image / illustration slots
- PDF/H5 as handbook outputs

### Acquisition And Order Layer

Changed from standalone-site-first to form-intake-first.

Current planning should prioritize:

- intake structure
- order and form flow
- handoff into backend generation

### Decision Layer

Changed from Japan-core-city framing to city-circle framing.

This affects:

- planning abstractions
- rule packs
- scope definitions
- future config truth sources

### Rendering Layer

Changed from "report output" to "page system for handbook output".

Rendering now needs to serve:

- chapter semantics
- page semantics
- view-model semantics
- visual slot semantics

### Quality And Operations Layer

The boundary expansion means quality and operational logic must eventually become:

- city-circle aware
- handbook aware
- asset-slot aware

### Data And Config Layer

The system can no longer rely on Japan-only defaults spread across old documents and code assumptions.

Truth sources must move toward:

- city-circle-scoped rules
- handbook delivery rules
- intake-priority rules

## Persistent Gap Inventory

The following earlier gap findings remain valid:

- old and new decision chains coexist
- old and new rendering chains coexist
- truth sources are still scattered
- quality and operations are still connected in a distributed way

These gaps remain valid under the new boundary. They should not be discarded just because the destination scope has widened.

## Why Current Phase Starts With File Consolidation

The current phase starts with files and total-planning cleanup first because the main risk is not only missing implementation.

The main risk is that:

- old assumptions still exist in active documents
- code reality and planning reality are not expressed under one boundary
- new scope, new delivery form, and new acquisition priority are not yet written into a single truth-source set

If broad code changes start before these files are stabilized, obsolete assumptions are likely to be reintroduced into:

- configs
- API design
- rendering contracts
- execution priorities

So the current phase is:

- unify truth sources
- mark deprecated assumptions
- rewrite planning boundary
- carry forward still-valid gaps

Only after that should broader execution planning begin.

## No Patch Governance

The current phase must not be advanced by patch-style governance.

That means:

- do not keep layering patches, bridges, and temporary glue on top of obsolete assumptions
- do not describe compatibility fixes as if they prove main-path completion
- do not use patch logic to hide unresolved truth-source, contract, or main-path problems
- when structure is wrong, fix the truth source, contract, source-of-truth object, or main path directly

In short, current-phase stabilization means reducing ambiguity at the source, not extending the life of broken boundaries through more patching.

## Truth Source Set

The current truth-source file set is:

1. `docs/architecture/00_scope_and_truth.md`
2. `docs/architecture/01_current_state.md`
3. `docs/architecture/02_target_architecture.md`
4. `docs/architecture/03_gap_and_priorities.md`
5. `docs/architecture/04_execution_staging.md`

Supporting historical inputs that remain useful:

- `docs/01_system_core.md`
- `docs/02_fragment_system.md`
- `docs/03_report_delivery_rules.md`
- `docs/Layer_2_决策与编排层实现方案_v1.md`
- `docs/Layer_3_报告与渲染层补充设计方案_v1.md`
- `docs/Layer_4_评测校验运营层修改建议_v1.md`
- `docs/travel_handbook_60p_for_engineer (1).md`
- `docs/travel_handbook_60p_for_owner.md`

These older files should now be read through the boundary established in this file.
