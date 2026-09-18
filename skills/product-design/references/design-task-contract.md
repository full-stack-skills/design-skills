# Design Task Contract

Use one task contract per page, major state, or design unit.

## Identity

- `task_id`
- `page_id`
- `feature_id`
- `product_version`
- `target_surface`
- `status`

## Upstream sources

- feature contract + version
- navigation contract + version
- visual/design-system baseline
- approved reference assets
- scenario fixture/data version

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
