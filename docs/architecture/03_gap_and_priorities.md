# 03 Gap And Priorities

## File Role

This file reorganizes the gap inventory under the latest boundary.

It does not break work into engineering tasks. It explains:

1. which old assumptions have invalidated older gap wording
2. which layer impacts now require rewritten gaps
3. which earlier gaps still remain valid
4. why current priority is file consolidation before broad code execution

## Gaps That Are No Longer Valid In Their Old Wording

Some older gap wording should no longer be carried forward as-is.

### "The system is only missing better Japan itinerary logic"

Outdated because scope is no longer defined only by Japan.

The gap must now be framed as:

- city-circle abstraction gap
- city-circle rule-pack gap
- city-circle truth-source gap

### "The main missing thing is the standalone site system"

Outdated because the current acquisition priority is form intake through Douyin, not site completeness.

The gap must now be framed as:

- intake contract alignment gap
- form-to-backend handoff gap

### "The output report structure is incomplete"

Too old and too weak.

The gap must now be framed as:

- handbook page semantics gap
- handbook visual-slot truth-source gap
- unified delivery contract gap

## Still-Valid Gaps

The following previous findings remain valid and should be preserved.

### 1. Old And New Decision Chains Coexist

This remains valid.

Current consequence:

- unclear long-term planning main path
- compatibility burden on downstream layers
- repeated ambiguity in planning truth sources

### 2. Old And New Rendering Chains Coexist

This remains valid.

Current consequence:

- duplicated delivery semantics
- mixed report and page-system assumptions
- unstable render truth source

### 3. Truth Sources Are Distributed

This remains valid.

Current consequence:

- latest boundary is not expressed in one file set
- old assumptions remain easy to reintroduce

### 4. Quality And Operations Are Still Distributed

This remains valid.

Current consequence:

- checks exist, but operational architecture is still fragmented in expression and ownership

## Gaps That Must Be Rewritten Under The New Boundary

### A. Scope Gap

Old wording:

- "Japan destination coverage gap"

Rewrite under new boundary:

- city-circle abstraction gap
- city-circle-specific rule/source/config gap

### B. Delivery Gap

Old wording:

- "report output quality gap"

Rewrite under new boundary:

- 60-page handbook semantics gap
- image / illustration slot rule gap
- shared PDF/H5 handbook delivery contract gap

### C. Acquisition Gap

Old wording:

- "website funnel completeness gap"

Rewrite under new boundary:

- Douyin form intake priority gap
- intake truth-source and order handoff gap

### D. Planning Expression Gap

Old wording:

- "Layer 2 / Layer 3 docs incomplete"

Rewrite under new boundary:

- current architecture truth-source gap
- mismatch between existing code reality and latest planning boundary

## Current Deferred Items

The following are intentionally deferred for the current phase:

- broad code refactor
- full standalone-site system redesign
- detailed engineering scheduling
- mass migration of all old paths in one step
- pretending the six-city-circle scope is already implemented in code

These are not rejected forever. They are simply not current-phase priorities.

## Why Current Priority Is File Consolidation First

Current priority starts with files because the most dangerous failure mode right now is false alignment.

That would look like:

- code changes based on old Japan-only assumptions
- render work based on old report assumptions
- intake work based on standalone-site-first assumptions
- operational planning based on fragmented truth sources

File consolidation reduces that risk by doing four things first:

- marking obsolete assumptions explicitly
- rewriting boundary changes layer by layer
- preserving still-valid gap inventory
- establishing a stable truth-source set

## Priority Logic

### P0

Planning truth-source stabilization:

- unify latest boundary
- identify deprecated assumptions
- preserve still-valid gaps
- rewrite outdated gap wording

### P1

Architecture-level convergence planning:

- current state expression
- target architecture expression
- stage framing for future execution

### P2

Implementation and migration planning after truth-source stabilization.

## Source Basis For This File

This file absorbs:

- earlier current-vs-target gap analysis
- the still-valid gap inventory
- latest boundary changes around six city circles, handbook delivery, and Douyin form priority

It replaces older gap framing that still assumed:

- Japan-only scope
- standalone-site-first priority
- long-report delivery default
