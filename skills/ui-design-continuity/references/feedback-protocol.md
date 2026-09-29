# Scoped Feedback Protocol

Convert feedback into a patch before redesigning.

## Patch fields

- **feedback**: exact user intent in concise form;
- **target**: region/component/behavior being corrected;
- **change**: what should be different;
- **preserve**: confirmed decisions that remain valid;
- **non-inference**: tempting conclusions that are *not* authorized;
- **affected_artifacts**: specs, prompts, pages, tests, manifests;
- **regression_checks**: how to prove the correction did not cause drift.

## Example

Feedback:

> Do not turn internal page tabs into sidebar items.

Patch:

- **change:** forbid dynamic injection from page-local navigation into the sidebar;
- **preserve:** already-approved fixed sidebar items;
- **non-inference:** do not conclude that the sidebar must have no second-level items;
- **regression:** compare sidebar item IDs before/after switching page-local views.

## Approval language

Treat feedback phrases carefully:
- “better / I like this” → preference or direction unless the user explicitly approves structure/behavior;
- “lock this / use this as the baseline” → promote the named scope;
- “only change X” → explicit change budget;
- “continue” → resume from the latest approved state, not from every incidental detail of the latest candidate.

If the approval scope is ambiguous and materially changes downstream work, ask or mark it `needs-decision`.
