# 04 Execution Staging

## File Role

This file defines stage boundaries only.

It does not create detailed engineering schedules.

It explains:

1. which old assumptions are no longer valid for staging
2. which layers are affected by the new boundary
3. which earlier gaps still remain active inputs
4. why current stage starts with files and total planning cleanup

## Deprecated Assumptions For Execution Staging

The current staging should not be built on these assumptions:

- "start with broad refactor"
- "finish the standalone site first"
- "the product is still mainly a Japan report generator"
- "the old planning docs can continue to act as the top truth source"

These assumptions would produce the wrong stage order.

## New Boundary Impact On Staging

The new boundary changes stage order because:

- six city circles require top-level scope rewrite before implementation decisions
- 60-page handbook delivery requires page-system truth before render migration
- Douyin form priority requires intake truth before site-system expansion

So staging must now start from truth-source alignment rather than code-first migration.

## Still-Active Inputs From Earlier Gap Work

The following still remain valid inputs for staging:

- decision-chain coexistence
- rendering-chain coexistence
- distributed truth sources
- distributed quality and operations expression

They remain valid, but they are not yet an execution checklist.

## Why Current Stage Starts With File Consolidation

Current stage starts with file consolidation because the system currently has:

- real code
- real partial migrations
- real planning documents
- mixed assumptions across them

If broad code execution starts first, the team risks migrating implementation without a stable answer to:

- what the scope now is
- what the delivery unit now is
- what the intake priority now is
- which file is the current truth source

So this stage is intentionally documentation-first.

## Stage 0: Truth-Source Consolidation

Goal:

- establish the new architecture file set
- declare current boundary
- mark obsolete assumptions

Output:

- stable scope and truth-source files
- stable reading order for old and new documents

## Stage 1: Planning Alignment

Goal:

- align current-state description with actual repo reality
- align target-state description with latest boundary
- rewrite gap language under new scope

Output:

- current-state file
- target-architecture file
- rewritten gap inventory

## Stage 2: Execution Boundary Preparation

Goal:

- define what is current-phase priority
- define what is deferred
- prevent premature code-first migration

Output:

- stage-based execution framing
- clearer future implementation entry point

## Stage 3: Post-Consolidation Execution Design

Goal:

- only after truth-source stabilization, enter implementation-level planning

This future stage may include:

- migration design
- implementation sequencing
- code-level change plans

But that is not part of the current stage.

## Explicitly Deferred For Now

- business-code modification
- broad refactor across old and new chains
- detailed sprint scheduling
- standalone-site-first redesign
- pretending six-city-circle support is already fully implemented

## Source Basis For This File

This file absorbs execution-order intent from older architecture and delivery documents, but rewrites the stage order under the latest boundary:

- six city circles
- 60-page handbook with visual slots
- Douyin form priority
- truth-source cleanup before implementation
