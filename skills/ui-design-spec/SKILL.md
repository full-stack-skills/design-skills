---
name: ui-design-spec
description: Use for complete functional design specifications or coordinated ui-design-spec execution. Spec mode organizes feature catalogs, per-page contracts, navigation, layout, user flows and task plans using Agent Browser and Evently examples; execution mode hands a selected workflow to specialists and ui-design-harness. 产品设计统一入口：功能清单、界面结构、交互流程、实施计划与后续设计交接。
license: Apache-2.0
---

# UI Design Spec / 界面设计规格

## Overview

Own the ui-design-spec entrypoint and the complete design package. **Spec mode** organizes requirements into clear feature, page, interaction and task contracts. **Execution mode** selects the next design workflow and hands its progress to `ui-design-harness`. Behavior, navigation, rendering and review keep their specialist ownership; all consume the same versioned facts.

## When to use this skill

- 整理详细功能设计计划：功能清单、逐页结构、完整交互流程、任务依赖与验收。
- 参考 Agent Browser / Evently 的成果整理一个完整产品，或补齐现有文档。
- 将规格推进到视觉设计，或继续已有设计工作。

Do not start rendering, implementation, installation or publishing merely because this skill is selected. Explanation/review requests stay read-only unless edits are requested.

## How to use this skill

Apply the following precedence before any routing:

1. **Harness dispatch present:** handle only the named stage and scope. For `baseline`, recover and bind existing authority; for `task`, assemble the scoped design task from the canonical plan. Return artifacts/evidence for the packet's `evidence_stage`. Do not select a new mode/profile, create a run or recursively invoke Harness. Other stages require an explicit matching scope; do not guess a broader task.
2. **Explicit specification/planning request:** use **spec mode**, even if it involves multiple files or the user says “continue the documents”. It does not require a Harness run.
3. **Resume an existing execution:** use its run identity and recorded next action through Harness. Do not restart specification discovery or create a second run.
4. **New visual/design execution:** use **execution mode**. If scope is unclear, inspect current artifacts and ask only about a material missing decision.

Read [responsibility and handoff contract](references/responsibility-contract.md). Missing optional specialist skills do not authorize installing them; for spec work use the bundled contracts and mark any unavailable specialist review honestly.

## Spec mode

Read [spec mode workflow](references/spec-mode.md), [delivery contract](references/delivery-contract.md), [template](assets/specification-template.md) and the [example guide](examples/READING_GUIDE.md). The complete Agent Browser example teaches full-product organization; Evently teaches detailed module/action/task decomposition. Preserve their Draft and historical evidence boundaries.

Fixed sequence: **scope/sources → feature detail → navigation/page structure → user journeys → Surface Registry → tasks → review**.

Default output under `docs/functional-design/`:

- `README.md`: scope, authority, coverage and reading order.
- `FUNCTION-CATALOG.md` + `pages/*.md`: full inventory and detailed contracts.
- `NAVIGATION.md` + `UI-STRUCTURE.md`: navigation, shell and page structure.
- `USER-FLOWS.md` + `GLOBAL-SURFACES.md`: journeys and shared interactions.
- `SCREEN-REGISTRY.md` + `registry.json`: stable views, actions, states and results.
- `MASTER-PLAN.md`: dependencies, deliverables, task briefs and acceptance.
- `task-coverage.json`: derived feature/Surface-to-task mapping, dependencies and exact canonical task locations; no duplicated execution status.
- `DESIGN-EXECUTION.md` + `STATUS.md`: handoff rules and separate delivery states.

Existing files/IDs/task sources remain canonical; map duties rather than force renaming or create a second requirements/task system. `ui-design-feature` refines behavior sections and `ui-design-nav` refines navigation sections only when needed. An already sufficient section is verified and reused, not regenerated. The same agent may apply these responsibilities without spawning other agents.

For newly authored full-product packages, validate structure and declared task coverage with `python3 <skill>/scripts/validate_functional_design.py <package> --require-task-coverage`. Historical source snapshots remain unmodified and may be checked without that flag. Read [task coverage contract](references/task-coverage.md). Perform the semantic review separately using [review checklist](references/review-checklist.md). Structure is not proof of content depth, task coverage, approval or runtime behavior. Do not finish a whole-product request with a few sample pages.

## Execution mode

1. Recover user authorization, product scope, current authority versions, existing task and visual baseline. Record whether the continuity mode is initial, inherit or correction; do not invent an approved visual baseline for a first page.
2. Resolve actual gaps with the relevant specialist; do not reopen confirmed requirements or navigation merely to run a workflow.
3. Resolve theme selection through ui-design-theme when needed; reuse an existing theme contract and carry its identity/version/maturity. Prepare the [design task contract](references/design-task-contract.md), including exact canonical paths/versions and acceptance. Spec completion alone does not authorize visual generation or implementation.
4. Select a fitting profile once and hand it to `ui-design-harness`: `product-to-ui`, `existing-product-next-page`, `page-family-batch`, `design-correction`, `stitch-high-fidelity-delivery` or `design-to-implementation`. Profile semantics stay in Harness; do not duplicate its state machine here.
5. Existing runs are resumed by Harness. Specialists return bounded results to the active dispatch; this entrypoint is not re-entered to choose the same workflow again.
6. Use `ui-design-continuity` for pre-render constraints in initial/inherit/correction mode, a selected renderer such as `ui-design-visual` for assets, and `ui-design-review` for independent consistency findings. None may rewrite upstream facts silently.

For bounded one-shot work without persistent workflow needs, hand the prepared contract directly to the selected specialist. Avoid creating a ledger solely because several documents were read. Detailed stage routing: [workflow](references/workflow.md).

## Best Practices

- One requirements authority and one task execution source; the design package is their detailed projection.
- Feature/page/Surface/task identity remains stable across specification, execution and review.
- Preserve user decisions, context and unfinished work; complete only the requested scope.
- Author self-checks improve the draft; `ui-design-review` findings are separate review evidence, not self-granted approval.
- Report spec, visual, approval, implementation and runtime status separately.
- `functional-design` and `product-interface-spec` are retired draft names, not additional skills to install.

## Output contract

Return the selected mode or dispatch stage, scope, authority and task source, completed artifacts, unresolved decisions, actual verification, and the next action. A Harness worker returns stage evidence rather than a new routing plan. Installation, remote CI and model/runtime validation are separate evidence boundaries.

## Keywords

product design, design spec, functional design, feature catalog, user flow, page structure, design handoff, 产品设计, 功能清单, 交互流程, 界面结构, 实施计划, Evently, Agent Browser
