# 02 Target Architecture

## File Role

This file defines what the system is intended to become under the latest boundary.

It explains:

1. which old assumptions are replaced
2. which layers are changed by the new boundary
3. which earlier gaps still map into the target system
4. why current phase still starts from planning and truth-source consolidation

## Target System Overview

The target system is a city-circle-based travel handbook system:

- form-based intake
- normalized planning profile
- staged decision orchestration
- page-based handbook rendering
- PDF/H5 handbook delivery
- evaluation, operational review, and feedback loop

The target system is not:

- a Japan-only itinerary writer
- a standalone-site-first content project
- a plain long-report generator

## Replaced Assumptions

### Japan Core Cities -> Six City Circles

The target planning abstraction is no longer "Japan core city templates".

It becomes "city-circle-based planning scope", currently covering:

- Kansai city circle
- Kanto city circle
- Hokkaido city circle
- South China five-city circle
- Northern Xinjiang city circle
- Guangdong city circle

### Long Report -> 60-Page Handbook

The target delivery abstraction is no longer a plain report flow.

It becomes a 60-page travel handbook with:

- fixed page semantics
- chapter semantics
- image / illustration slots
- PDF/H5 delivery

### Standalone Site First -> Douyin Form Intake First

The target intake strategy for the current phase is not "complete the standalone site first".

It is:

- prioritize traffic capture
- prioritize structured form intake
- feed backend planning and delivery pipeline

The backend target architecture still remains entry-point-neutral, but current planning priority is no longer site-first.

## New Boundary Impact By Layer

### Product Delivery Layer

Target state:

- handbook is the default product form
- page system is the delivery unit
- visual slots are explicit, not incidental

This replaces the old report-oriented delivery mental model.

### Acquisition And Order Layer

Target state:

- intake starts from a structured form path that can be fed by Douyin or future channels
- acquisition logic and backend intake logic are decoupled
- current planning priority is form capture, not full standalone-site completion

### Decision And Orchestration Layer

Target state:

- planning is city-circle-aware
- planning runs through staged decision logic
- profile normalization and constraint handling are explicit
- old template assembly no longer defines the long-term main path

### Rendering And Delivery Layer

Target state:

- `chapter_plan` defines chapter structure
- `page_plan` defines page structure
- `page_view_model` defines renderable page data
- render adapters output PDF/H5 from shared semantics

This layer must also serve:

- handbook page stability
- image / illustration slot semantics
- cross-channel consistency

### Quality And Operations Layer

Target state:

- intake validation
- post-generation review
- operator controls
- feedback loop

These should behave like one architecture layer, not a scattered set of checks.

### Data And Config Layer

Target state:

- city-circle-aware rule packs
- handbook delivery contracts
- visual slot contracts
- acquisition-priority-aware truth sources

This replaces older distributed assumptions embedded in many documents.

## Target Decision Chain

The long-term target decision chain is staged and explicit.

At the architecture level it should be understood as:

- normalized profile
- eligibility and precheck gates
- city-circle selection
- major activity selection
- hotel/base strategy
- route skeleton
- secondary fill
- meal fill
- fit scoring and review

The target system does not assume one large prompt writes the trip from scratch.

## Target Page System

The long-term target rendering chain is:

- `ReportPayload`
- `chapter_plan`
- `page_plan`
- `page_view_model`
- render adapters
- PDF / H5 handbook outputs

This chain must be able to support the 60-page handbook definition and visual slot logic.

## Persistent Gaps Still Relevant To The Target

The following earlier gaps still map directly into the target architecture:

- decision-chain coexistence still blocks clear main-path definition
- rendering-chain coexistence still blocks unified delivery semantics
- distributed truth sources still block stable city-circle and handbook planning
- distributed quality/ops entry points still block a clear operations architecture

These gaps are still valid even after the boundary expands.

## Why Current Phase Still Starts With File Consolidation

The target architecture cannot be implemented cleanly until the current truth-source boundary is stabilized.

Without that, implementation would still be answering conflicting questions such as:

- are we Japan-only or city-circle-based?
- are we delivering reports or handbook pages?
- are we optimizing for standalone site completeness or Douyin form capture?
- are old chains temporary compatibility or still design-default?

That is why the current phase still starts from:

- unifying files
- rewriting obsolete assumptions
- aligning target descriptions
- preserving still-valid gap inventory

Implementation planning should start after these files make the target state unambiguous.

## Source Basis For This File

This file absorbs and reframes target-state material from:

- `docs/Layer_2_决策与编排层实现方案_v1.md`
- `docs/Layer_3_报告与渲染层补充设计方案_v1.md`
- `docs/Layer_4_评测校验运营层修改建议_v1.md`
- `docs/travel_handbook_60p_for_engineer (1).md`
- `docs/travel_handbook_60p_for_owner.md`
- prior current-vs-target gap analysis now rewritten under the new boundary
