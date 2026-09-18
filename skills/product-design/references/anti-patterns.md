# Product Design Orchestration Anti-patterns

## Monolithic reimplementation

**Failure:** The orchestrator rewrites feature, navigation, rendering, and testing logic inside itself.

**Fix:** Route to the narrowest existing skill and pass explicit contracts.

## Restarting on “continue”

**Failure:** Re-ask product positioning, IA, or style questions that were already approved.

**Fix:** Recover state and continue from the next unfinished gate.

## Visual-first gap filling

**Failure:** Missing permissions/routes are invented inside a render prompt.

**Fix:** Resolve them upstream with `feature-design` / `navigation-design` or mark them `needs-decision`.

## Tool-success completion

**Failure:** A generated screen is called final.

**Fix:** Keep candidate, preferred direction, approved visual master, product-contract approval, runtime verification, and archival distinct.

## Competing facts

**Failure:** Every skill maintains its own menu/page truth.

**Fix:** Share stable IDs and versioned contracts; use `design-guard` before promotion.
