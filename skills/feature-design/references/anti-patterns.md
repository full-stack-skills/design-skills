# Feature Design Anti-patterns

## Drawing before defining behavior

**Failure:** Jump directly from a feature name to KPI cards, tables, and buttons.

**Correction:** Define actors, actions, states, permissions, evidence, and acceptance first.

## Invented product authority

**Failure:** Assume who may approve, override, delete, or run automation because the page needs an action.

**Correction:** Mark missing authority as `needs-decision`.

## Status theater

**Failure:** Treat “Done”, “Approved”, or a progress percentage as proof.

**Correction:** Define the evidence that makes the claim trustworthy.

## Hidden recovery semantics

**Failure:** Specify only the happy path.

**Correction:** Include blocking, conflict, retry, resume, rollback, cancellation, and human takeover where they change the experience.

## Feature design mutates IA

**Failure:** Reorganize menus or page hierarchy while specifying a feature.

**Correction:** Preserve approved IA and hand navigation changes to `navigation-design`.

## Proposal presented as fact

**Failure:** Fill missing business rules with plausible defaults.

**Correction:** Keep `confirmed`, `proposed`, and `needs-decision` distinct.
