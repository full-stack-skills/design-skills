# UI Continuity Contract

## Baseline identity

- `mode`: initial / inherit / correction
- `baseline_id`: null for initial; otherwise exact source identity
- `baseline_version`: null for initial; otherwise bound version
- `theme_ref`: identity, version, source and maturity
- `baseline_type`: candidate / preferred-direction / approved-visual-master / approved-product-contract / implementation-screenshot
- `authority_sources`
- `target_page_id`
- `target_spec_version`

Do not collapse visual approval and product-contract approval into one status.

## Region map

| Region | Class | Authority | Allowed change |
|---|---|---|---|
| Example: global shell | immutable | approved shell/design system | none except contract-variable values |
| Example: active navigation | contract-variable | navigation contract | active state only |
| Example: content workspace | page-local | target page spec | target-page design |

The examples are categories, not fixed product structure.

## Change budget

State in plain language:
- **May change**
- **Must preserve**
- **May vary from live/runtime data**
- **Needs decision before change**

A candidate that exceeds the budget is a continuity failure even if it looks good.

## Post-render comparison (ui-design-review)

| Area | Baseline | Candidate | Allowed? | Evidence/decision |
|---|---|---|---|---|

Before rendering, return these comparison criteria only. Initial mode compares the candidate to product/theme constraints; no baseline diff is claimed until a baseline exists.

Compare:
- navigation inventory/order;
- shell geometry and hierarchy;
- design tokens/component language;
- context identity;
- page-local information architecture;
- active states;
- incidental copy/data that should not become product truth.

## Regression checklist

Examples:
- immutable region inventory unchanged;
- target active state correct;
- page-local content matches current feature contract;
- no accidental menu or route additions;
- visual language remains in the approved family;
- unresolved product conflicts are visible, not silently resolved.
