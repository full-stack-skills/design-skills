# Product Design Orchestration Workflow

For multi-stage or resumable execution, `ui-design-harness` owns persistent run state, evidence, approval gates, reconciliation, and correction invalidation. This document defines design routing and stage responsibilities; it is not a second run engine.

Before selecting a profile, classify specification-only requests. Complete functional design planning stays in **ui-design-spec spec mode**; read [spec-mode.md](spec-mode.md) and [responsibility-contract.md](responsibility-contract.md). No Harness, rendering or implementation is started merely to organize documents. An active Harness dispatch takes precedence over entrypoint routing and is handled only within its named stage.

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

Profile stage plans belong to `ui-design-harness`; this router only selects the task class.

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

If actions, states, permissions, evidence, or acceptance are incomplete, use `ui-design-feature` to refine the canonical section. If sufficient, inspect and reuse it with appropriate evidence; do not regenerate a parallel behavior contract.

Output: behavior contract.

## Stage 2 — Navigation

If scope, menu/tab hierarchy, routes, activation, context propagation, deep links, or return behavior are incomplete, use `ui-design-nav` to refine the canonical section. Otherwise verify and reuse its existing version.

Output: navigation contract.

## Stage 3 — Documentation

Use the repository’s documentation conventions/skills to persist confirmed behavior and navigation. Documentation is a persistence layer, not a substitute for the design decisions themselves.

For full functional design packages, use this skill’s spec mode, detailed workflow and delivery contracts. Retain one requirements/task source; the package is the detailed design projection, not a competing PRD or task state.

## Stage 4 — Page task preparation

Assemble the existing scoped task using `design-task-contract.md`, preserving its canonical task ID and source. A Harness task dispatch returns this stage’s evidence without selecting another profile or starting a run.

## Stage 5 — Continuity decision

If an approved UI baseline exists, use `ui-design-continuity` before rendering.

If no baseline exists and visual direction is intentionally open, use an exploration/design skill instead.

## Stage 6 — Visual execution

Select the narrowest executor:
- Stitch for Stitch-native generation/workflows;
- Pencil for editable `.pen` work;
- `ui-design-visual` for HTML-based high-fidelity prototypes/visual exploration;
- another explicit tool when the project requires it.

Executors consume upstream contracts; they do not redefine them silently.

## Stage 7 — Review and promotion

Run:
1. structural/semantic consistency checks;
2. visual review;
3. user approval where required;
4. implementation/runtime verification separately when implementation exists.

Use `ui-design-review` for cross-artifact consistency.

## Stage 8 — Continue

Record the next unfinished item. When `ui-design-harness` is active, persist it as the run's `next_action` with required input/evidence references. “Continue” resumes there instead of returning to Stage 0 discovery unless the baseline changed.
