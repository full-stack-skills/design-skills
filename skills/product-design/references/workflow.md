# Product Design Orchestration Workflow

For multi-stage or resumable execution, `design-harness` owns persistent run state, evidence, approval gates, reconciliation, and correction invalidation. This document defines design routing and stage responsibilities; it is not a second run engine.

## Harness profile routing

Choose the narrowest built-in profile before starting a new multi-stage run:

| Task | Profile |
|---|---|
| New product/feature to UI | `product-to-ui` |
| Continue one approved page family | `existing-product-next-page` |
| Batch sibling pages with one shell | `page-family-batch` |
| Scoped correction | `design-correction` |
| Stitch-centric high-fidelity delivery | `stitch-high-fidelity-delivery` |
| Approved design to implementation handoff | `design-to-implementation` |

Profile stage plans belong to `design-harness`; this router only selects the task class.

## Stage 0 — Recover state

Collect:
- product/version identity;
- approved terminology and IA;
- current feature/page ID;
- approved shell or visual master, if any;
- open decisions;
- latest completed gate;
- downstream artifacts already generated.

Never infer approval from file recency alone.

## Stage 1 — Product behavior

If actions, states, permissions, evidence, or acceptance are incomplete, use `feature-design`.

Output: behavior contract.

## Stage 2 — Navigation

If scope, menu/tab hierarchy, routes, activation, context propagation, deep links, or return behavior are incomplete, use `navigation-design`.

Output: navigation contract.

## Stage 3 — Documentation

Use the repository’s documentation conventions/skills to persist confirmed behavior and navigation. Documentation is a persistence layer, not a substitute for the design decisions themselves.

## Stage 4 — Page task preparation

Create one design task contract per page/state using `design-task-contract.md`.

## Stage 5 — Continuity decision

If an approved UI baseline exists, use `ui-continuity` before rendering.

If no baseline exists and visual direction is intentionally open, use an exploration/design skill instead.

## Stage 6 — Visual execution

Select the narrowest executor:
- Stitch for Stitch-native generation/workflows;
- Pencil for editable `.pen` work;
- `huashu-design` for HTML-based high-fidelity prototypes/visual exploration;
- another explicit tool when the project requires it.

Executors consume upstream contracts; they do not redefine them silently.

## Stage 7 — Review and promotion

Run:
1. structural/semantic consistency checks;
2. visual review;
3. user approval where required;
4. implementation/runtime verification separately when implementation exists.

Use `design-guard` for cross-artifact consistency.

## Stage 8 — Continue

Record the next unfinished item. When `design-harness` is active, persist it as the run's `next_action` with required input/evidence references. “Continue” resumes there instead of returning to Stage 0 discovery unless the baseline changed.
