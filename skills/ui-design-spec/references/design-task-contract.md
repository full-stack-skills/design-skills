# Design Task Contract

Use one task contract per page, major state, or design unit.

Reference the canonical specification and task rather than creating a second execution checklist. This contract is shared by spec mode, specialists, Harness and renderers; see [responsibility-contract.md](responsibility-contract.md).

## Identity

- `task_id`
- `page_id`
- `feature_id`
- `product_version`
- `target_surface`
- `status`

`status` is a projection of the named canonical task source, not an independently editable execution status.

## Upstream sources

- feature contract + version
- navigation contract + version
- visual/design-system baseline (explicitly absent for initial mode)
- theme identity/version/source/maturity, colors/fonts, permitted overrides and actual check evidence
- approved reference assets
- scenario fixture/data version
- canonical requirement and task source + exact section/marker
- page/Surface registry version and unresolved decisions affecting this task

## Handoff boundary

- requested mode/stage, exact scope and expected deliverable
- editable sections/regions and immutable authority
- return evidence and limitations
- when issued by Harness: retain the existing run/dispatch identity, handler, scope and expected evidence stage from its packet; do not invent a new payload schema or restart routing

## Required behavior

- page goal
- actors
- visible states
- actions
- permissions
- evidence/acceptance cues
- empty/error/blocked/conflict behavior

## Navigation contract

- entry route
- active navigation levels
- context IDs
- local views
- return/deep-link behavior

## Continuity contract

- mode: initial / inherit / correction
- baseline identity/version or explicit absence
- post-render comparison criteria; actual diff is produced by review after rendering

- immutable regions
- contract-variable regions
- page-local regions
- explicit change budget

## Scenario fixture

Use synthetic or approved demonstration data. The same fixture should feed prompt, prototype, screenshots, and tests when possible.

## Output targets

- text/UI description if needed
- renderer prompt/plan
- candidate asset path
- editable source path
- screenshot/render path
- verification evidence

## Acceptance

- structural checks
- semantic checks
- visual review scope
- interaction checks
- user approval gate
- implementation verification gate, if applicable

Do not mark the task complete merely because a render file exists.
